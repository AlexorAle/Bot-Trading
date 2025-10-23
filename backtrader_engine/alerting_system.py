"""
Alerting System - Sistema de alertas inteligentes
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Severidad de alertas"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    """Estado de alertas"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class Alert:
    """Alerta individual"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    labels: Dict[str, str] = None
    annotations: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.annotations is None:
            self.annotations = {}

@dataclass
class AlertRule:
    """Regla de alerta"""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    title: str
    message_template: str
    cooldown_seconds: int = 300  # 5 minutos
    enabled: bool = True
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}

class AlertingSystem:
    """Sistema de alertas inteligentes"""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_rule_check: Dict[str, datetime] = {}
        self.notifiers: List[Callable] = []
        self.logger = logging.getLogger("AlertingSystem")
        
        # Inicializar reglas por defecto
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Inicializar reglas de alerta por defecto"""
        
        # Regla: Bot no está corriendo
        self.add_rule(AlertRule(
            name="bot_not_running",
            condition=lambda metrics: not metrics.get("bot_status", {}).get("value", 0),
            severity=AlertSeverity.CRITICAL,
            title="🚨 Bot Stopped",
            message_template="Trading bot has stopped running",
            cooldown_seconds=60
        ))
        
        # Regla: WebSocket desconectado
        self.add_rule(AlertRule(
            name="websocket_disconnected",
            condition=lambda metrics: not metrics.get("websocket_connected", {}).get("value", 0),
            severity=AlertSeverity.WARNING,
            title="⚠️ WebSocket Disconnected",
            message_template="WebSocket connection lost",
            cooldown_seconds=300
        ))
        
        # Regla: Alta pérdida de dinero
        self.add_rule(AlertRule(
            name="high_loss",
            condition=lambda metrics: metrics.get("trading_pnl_total", {}).get("value", 0) < -1000,
            severity=AlertSeverity.CRITICAL,
            title="💰 High Loss Alert",
            message_template="Trading PnL is ${pnl:.2f} (below -$1000 threshold)",
            cooldown_seconds=600
        ))
        
        # Regla: Muchos errores de API
        self.add_rule(AlertRule(
            name="high_api_errors",
            condition=lambda metrics: self._get_error_rate(metrics) > 0.1,  # 10% error rate
            severity=AlertSeverity.WARNING,
            title="🔌 High API Error Rate",
            message_template="API error rate is {error_rate:.1%} (above 10% threshold)",
            cooldown_seconds=300
        ))
        
        # Regla: Sin señales por mucho tiempo
        self.add_rule(AlertRule(
            name="no_signals",
            condition=lambda metrics: self._get_signal_age(metrics) > 1800,  # 30 minutos
            severity=AlertSeverity.WARNING,
            title="📊 No Signals Generated",
            message_template="No trading signals generated for {age_minutes:.1f} minutes",
            cooldown_seconds=600
        ))
        
        # Regla: Uso alto de memoria
        self.add_rule(AlertRule(
            name="high_memory_usage",
            condition=lambda metrics: metrics.get("bot_memory_usage_bytes", {}).get("value", 0) > 500 * 1024 * 1024,  # 500MB
            severity=AlertSeverity.WARNING,
            title="💾 High Memory Usage",
            message_template="Bot memory usage is {memory_mb:.1f} MB (above 500MB threshold)",
            cooldown_seconds=300
        ))
        
        # Regla: Uso alto de CPU
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            condition=lambda metrics: metrics.get("bot_cpu_usage_percent", {}).get("value", 0) > 80,
            severity=AlertSeverity.WARNING,
            title="⚡ High CPU Usage",
            message_template="Bot CPU usage is {cpu_percent:.1f}% (above 80% threshold)",
            cooldown_seconds=300
        ))
        
        # Regla: Circuit breaker abierto
        self.add_rule(AlertRule(
            name="circuit_breaker_open",
            condition=lambda metrics: any(
                metrics.get(f"circuit_breaker_open_{name}", {}).get("value", 0) 
                for name in ["bot_startup", "signal_generation", "paper_trader_startup"]
            ),
            severity=AlertSeverity.CRITICAL,
            title="🔒 Circuit Breaker Open",
            message_template="Circuit breaker is open, blocking operations",
            cooldown_seconds=60
        ))
        
        self.logger.info(f"Initialized {len(self.rules)} alert rules")
    
    def _get_error_rate(self, metrics: Dict[str, Any]) -> float:
        """Calcular tasa de errores de API"""
        try:
            total_requests = metrics.get("api_requests_total", {}).get("value", 0)
            failed_requests = metrics.get("api_requests_failed", {}).get("value", 0)
            
            if total_requests == 0:
                return 0.0
            
            return failed_requests / total_requests
        except:
            return 0.0
    
    def _get_signal_age(self, metrics: Dict[str, Any]) -> float:
        """Obtener edad de la última señal en segundos"""
        try:
            # Simular edad basada en uptime y número de señales
            uptime = metrics.get("bot_uptime_seconds", {}).get("value", 0)
            signal_count = metrics.get("trading_signals_total", {}).get("value", 0)
            
            if signal_count == 0:
                return uptime  # Si no hay señales, usar uptime completo
            
            # Estimar edad basada en frecuencia esperada (cada 15 minutos)
            expected_signals = uptime / 900  # 900 segundos = 15 minutos
            if signal_count >= expected_signals:
                return 0  # Señales al día
            else:
                return uptime - (signal_count * 900)  # Tiempo desde última señal esperada
        except:
            return 0.0
    
    def add_rule(self, rule: AlertRule):
        """Agregar regla de alerta"""
        self.rules.append(rule)
        self.logger.info(f"Added alert rule: {rule.name}")
    
    def add_notifier(self, notifier: Callable):
        """Agregar notificador"""
        self.notifiers.append(notifier)
        self.logger.info("Added alert notifier")
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Verificar reglas de alerta"""
        current_time = datetime.now(timezone.utc)
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Verificar cooldown
            last_check = self.last_rule_check.get(rule.name)
            if last_check and (current_time - last_check).total_seconds() < rule.cooldown_seconds:
                continue
            
            try:
                # Evaluar condición
                if rule.condition(metrics):
                    await self._trigger_alert(rule, metrics, current_time)
                else:
                    await self._resolve_alert(rule.name, current_time)
                
                self.last_rule_check[rule.name] = current_time
                
            except Exception as e:
                self.logger.error(f"Error checking rule {rule.name}: {e}")
    
    async def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any], current_time: datetime):
        """Disparar alerta"""
        alert_id = f"{rule.name}_{int(current_time.timestamp())}"
        
        # Verificar si ya existe alerta activa
        if rule.name in self.active_alerts:
            return  # Ya hay una alerta activa
        
        # Crear mensaje personalizado
        message = rule.message_template
        try:
            # Reemplazar variables en el mensaje
            if "{pnl}" in message:
                pnl = metrics.get("trading_pnl_total", {}).get("value", 0)
                message = message.replace("{pnl}", f"{pnl:.2f}")
            
            if "{error_rate}" in message:
                error_rate = self._get_error_rate(metrics)
                message = message.replace("{error_rate}", f"{error_rate:.1%}")
            
            if "{age_minutes}" in message:
                age_seconds = self._get_signal_age(metrics)
                message = message.replace("{age_minutes}", f"{age_seconds / 60:.1f}")
            
            if "{memory_mb}" in message:
                memory_bytes = metrics.get("bot_memory_usage_bytes", {}).get("value", 0)
                memory_mb = memory_bytes / (1024 * 1024)
                message = message.replace("{memory_mb}", f"{memory_mb:.1f}")
            
            if "{cpu_percent}" in message:
                cpu_percent = metrics.get("bot_cpu_usage_percent", {}).get("value", 0)
                message = message.replace("{cpu_percent}", f"{cpu_percent:.1f}")
                
        except Exception as e:
            self.logger.error(f"Error formatting alert message: {e}")
            message = rule.message_template
        
        # Crear alerta
        alert = Alert(
            id=alert_id,
            title=rule.title,
            message=message,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            created_at=current_time,
            labels=rule.labels.copy(),
            annotations={
                "rule_name": rule.name,
                "triggered_at": current_time.isoformat()
            }
        )
        
        # Guardar alerta
        self.active_alerts[rule.name] = alert
        self.alert_history.append(alert)
        
        # Enviar notificaciones
        await self._send_notifications(alert)
        
        self.logger.warning(f"Alert triggered: {rule.name} - {alert.title}")
    
    async def _resolve_alert(self, rule_name: str, current_time: datetime):
        """Resolver alerta"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = current_time
            
            # Enviar notificación de resolución
            resolution_alert = Alert(
                id=f"{rule_name}_resolved_{int(current_time.timestamp())}",
                title=f"✅ {alert.title} - RESOLVED",
                message=f"Alert resolved: {alert.message}",
                severity=AlertSeverity.INFO,
                status=AlertStatus.RESOLVED,
                created_at=current_time,
                labels=alert.labels.copy(),
                annotations={
                    "rule_name": rule_name,
                    "resolved_at": current_time.isoformat(),
                    "original_alert_id": alert.id
                }
            )
            
            await self._send_notifications(resolution_alert)
            
            # Remover de alertas activas
            del self.active_alerts[rule_name]
            
            self.logger.info(f"Alert resolved: {rule_name}")
    
    async def _send_notifications(self, alert: Alert):
        """Enviar notificaciones"""
        for notifier in self.notifiers:
            try:
                await notifier(alert)
            except Exception as e:
                self.logger.error(f"Error sending notification: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Obtener alertas activas"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Obtener historial de alertas"""
        return self.alert_history[-limit:]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Obtener resumen de alertas"""
        active_count = len(self.active_alerts)
        critical_count = len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.CRITICAL])
        warning_count = len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.WARNING])
        
        return {
            "active_alerts": active_count,
            "critical_alerts": critical_count,
            "warning_alerts": warning_count,
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules if r.enabled])
        }

# Instancia global del sistema de alertas
global_alerting_system = AlertingSystem()
