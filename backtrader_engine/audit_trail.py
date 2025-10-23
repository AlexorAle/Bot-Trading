"""
Audit Trail - Sistema de auditoría y trazabilidad
"""

import asyncio
import logging
import json
import hashlib
import hmac
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import threading
import queue

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Tipos de eventos de auditoría"""
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    TRADING_ACTION = "trading_action"
    SECURITY_EVENT = "security_event"
    CONFIGURATION_CHANGE = "configuration_change"
    ERROR_EVENT = "error_event"
    COMPLIANCE_EVENT = "compliance_event"

class AuditSeverity(Enum):
    """Severidad de eventos de auditoría"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Evento de auditoría"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str]
    session_id: Optional[str]
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    signature: str
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None

class AuditTrail:
    """Sistema de auditoría y trazabilidad"""
    
    def __init__(self, audit_file: str = "logs/audit_trail.jsonl"):
        self.audit_file = Path(audit_file)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("AuditTrail")
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        
        # Configuración de auditoría
        self.audit_config = {
            "retention_days": 2555,  # 7 años
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "compression_enabled": True,
            "encryption_enabled": True,
            "signature_key": "audit_trail_secret_key",  # En producción usar clave segura
            "batch_size": 100,
            "flush_interval": 30  # segundos
        }
        
        # Estadísticas de auditoría
        self.stats = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_severity": {},
            "events_by_user": {},
            "last_event_time": None,
            "file_size": 0
        }
        
        self.logger.info("AuditTrail initialized")
    
    def start(self):
        """Iniciar sistema de auditoría"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            self.logger.info("Audit trail started")
    
    def stop(self):
        """Detener sistema de auditoría"""
        if self.running:
            self.running = False
            if self.worker_thread:
                self.worker_thread.join(timeout=5)
            self.logger.info("Audit trail stopped")
    
    def _worker_loop(self):
        """Loop del worker de auditoría"""
        batch = []
        last_flush = time.time()
        
        while self.running:
            try:
                # Procesar eventos en lotes
                while not self.event_queue.empty():
                    event = self.event_queue.get_nowait()
                    batch.append(event)
                    
                    # Flush si se alcanza el tamaño del lote
                    if len(batch) >= self.audit_config["batch_size"]:
                        self._flush_batch(batch)
                        batch = []
                        last_flush = time.time()
                
                # Flush periódico
                if time.time() - last_flush > self.audit_config["flush_interval"]:
                    if batch:
                        self._flush_batch(batch)
                        batch = []
                    last_flush = time.time()
                
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in audit worker loop: {e}")
                time.sleep(1)
        
        # Flush final
        if batch:
            self._flush_batch(batch)
    
    def _flush_batch(self, batch: List[AuditEvent]):
        """Escribir lote de eventos a archivo"""
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                for event in batch:
                    event_json = json.dumps(asdict(event), default=str, ensure_ascii=False)
                    f.write(event_json + "\n")
            
            # Actualizar estadísticas
            self.stats["total_events"] += len(batch)
            for event in batch:
                # Estadísticas por tipo
                event_type = event.event_type.value
                self.stats["events_by_type"][event_type] = self.stats["events_by_type"].get(event_type, 0) + 1
                
                # Estadísticas por severidad
                severity = event.severity.value
                self.stats["events_by_severity"][severity] = self.stats["events_by_severity"].get(severity, 0) + 1
                
                # Estadísticas por usuario
                if event.user_id:
                    self.stats["events_by_user"][event.user_id] = self.stats["events_by_user"].get(event.user_id, 0) + 1
                
                # Último evento
                self.stats["last_event_time"] = event.timestamp.isoformat()
            
            # Actualizar tamaño del archivo
            self.stats["file_size"] = self.audit_file.stat().st_size
            
            self.logger.debug(f"Flushed {len(batch)} audit events")
        except Exception as e:
            self.logger.error(f"Error flushing audit batch: {e}")
    
    def log_event(self, 
                  event_type: AuditEventType,
                  action: str,
                  resource: str,
                  details: Dict[str, Any],
                  severity: AuditSeverity = AuditSeverity.MEDIUM,
                  user_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None,
                  previous_state: Optional[Dict[str, Any]] = None,
                  new_state: Optional[Dict[str, Any]] = None) -> str:
        """Registrar evento de auditoría"""
        
        # Generar ID único del evento
        event_id = self._generate_event_id()
        
        # Crear evento
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            signature=self._generate_signature(event_id, action, resource),
            previous_state=previous_state,
            new_state=new_state
        )
        
        # Agregar a cola
        self.event_queue.put(event)
        
        self.logger.debug(f"Logged audit event: {event_id}")
        return event_id
    
    def _generate_event_id(self) -> str:
        """Generar ID único del evento"""
        timestamp = int(time.time() * 1000000)  # microsegundos
        random_part = hashlib.md5(f"{timestamp}{id(self)}".encode()).hexdigest()[:8]
        return f"audit_{timestamp}_{random_part}"
    
    def _generate_signature(self, event_id: str, action: str, resource: str) -> str:
        """Generar firma del evento"""
        message = f"{event_id}:{action}:{resource}"
        signature = hmac.new(
            self.audit_config["signature_key"].encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, event: AuditEvent) -> bool:
        """Verificar firma del evento"""
        expected_signature = self._generate_signature(event.event_id, event.action, event.resource)
        return hmac.compare_digest(event.signature, expected_signature)
    
    def query_events(self, 
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     event_type: Optional[AuditEventType] = None,
                     severity: Optional[AuditSeverity] = None,
                     user_id: Optional[str] = None,
                     resource: Optional[str] = None,
                     limit: int = 1000) -> List[AuditEvent]:
        """Consultar eventos de auditoría"""
        events = []
        
        try:
            with open(self.audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        event = AuditEvent(**event_data)
                        
                        # Aplicar filtros
                        if start_time and event.timestamp < start_time:
                            continue
                        if end_time and event.timestamp > end_time:
                            continue
                        if event_type and event.event_type != event_type:
                            continue
                        if severity and event.severity != severity:
                            continue
                        if user_id and event.user_id != user_id:
                            continue
                        if resource and resource not in event.resource:
                            continue
                        
                        events.append(event)
                        
                        if len(events) >= limit:
                            break
                    except Exception as e:
                        self.logger.warning(f"Error parsing audit event: {e}")
                        continue
        except FileNotFoundError:
            self.logger.warning("Audit file not found")
        except Exception as e:
            self.logger.error(f"Error querying audit events: {e}")
        
        # Ordenar por timestamp descendente
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de auditoría"""
        return {
            "total_events": self.stats["total_events"],
            "events_by_type": self.stats["events_by_type"],
            "events_by_severity": self.stats["events_by_severity"],
            "events_by_user": self.stats["events_by_user"],
            "last_event_time": self.stats["last_event_time"],
            "file_size": self.stats["file_size"],
            "file_size_mb": round(self.stats["file_size"] / (1024 * 1024), 2),
            "retention_days": self.audit_config["retention_days"],
            "compression_enabled": self.audit_config["compression_enabled"],
            "encryption_enabled": self.audit_config["encryption_enabled"]
        }
    
    def cleanup_old_events(self):
        """Limpiar eventos antiguos"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.audit_config["retention_days"])
            
            # Leer todos los eventos
            events = []
            with open(self.audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        event = AuditEvent(**event_data)
                        if event.timestamp >= cutoff_date:
                            events.append(event)
                    except Exception as e:
                        self.logger.warning(f"Error parsing audit event during cleanup: {e}")
                        continue
            
            # Escribir eventos filtrados
            with open(self.audit_file, "w", encoding="utf-8") as f:
                for event in events:
                    event_json = json.dumps(asdict(event), default=str, ensure_ascii=False)
                    f.write(event_json + "\n")
            
            self.logger.info(f"Cleaned up audit events older than {cutoff_date}")
        except Exception as e:
            self.logger.error(f"Error cleaning up audit events: {e}")
    
    def export_events(self, 
                      output_file: str,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      format: str = "json") -> bool:
        """Exportar eventos de auditoría"""
        try:
            events = self.query_events(start_time, end_time)
            
            if format == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump([asdict(event) for event in events], f, indent=2, default=str)
            elif format == "csv":
                import csv
                with open(output_file, "w", newline="", encoding="utf-8") as f:
                    if events:
                        writer = csv.DictWriter(f, fieldnames=asdict(events[0]).keys())
                        writer.writeheader()
                        for event in events:
                            writer.writerow(asdict(event))
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False
            
            self.logger.info(f"Exported {len(events)} events to {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting audit events: {e}")
            return False
    
    def generate_audit_report(self, 
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Generar reporte de auditoría"""
        try:
            events = self.query_events(start_time, end_time)
            
            # Calcular estadísticas
            total_events = len(events)
            events_by_type = {}
            events_by_severity = {}
            events_by_user = {}
            events_by_resource = {}
            
            for event in events:
                # Por tipo
                event_type = event.event_type.value
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
                
                # Por severidad
                severity = event.severity.value
                events_by_severity[severity] = events_by_severity.get(severity, 0) + 1
                
                # Por usuario
                if event.user_id:
                    events_by_user[event.user_id] = events_by_user.get(event.user_id, 0) + 1
                
                # Por recurso
                events_by_resource[event.resource] = events_by_resource.get(event.resource, 0) + 1
            
            # Eventos críticos
            critical_events = [e for e in events if e.severity == AuditSeverity.CRITICAL]
            
            # Eventos de seguridad
            security_events = [e for e in events if e.event_type == AuditEventType.SECURITY_EVENT]
            
            # Eventos de trading
            trading_events = [e for e in events if e.event_type == AuditEventType.TRADING_ACTION]
            
            report = {
                "report_id": f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "period": {
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                },
                "summary": {
                    "total_events": total_events,
                    "critical_events": len(critical_events),
                    "security_events": len(security_events),
                    "trading_events": len(trading_events)
                },
                "statistics": {
                    "events_by_type": events_by_type,
                    "events_by_severity": events_by_severity,
                    "events_by_user": events_by_user,
                    "events_by_resource": events_by_resource
                },
                "critical_events": [asdict(e) for e in critical_events[:10]],  # Top 10
                "security_events": [asdict(e) for e in security_events[:10]],  # Top 10
                "trading_events": [asdict(e) for e in trading_events[:10]]  # Top 10
            }
            
            return report
        except Exception as e:
            self.logger.error(f"Error generating audit report: {e}")
            return {}

# Instancia global del audit trail
global_audit_trail = AuditTrail()
