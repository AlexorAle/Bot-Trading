"""
Health Checker - Sistema de monitoreo de salud del bot
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Estados de salud"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """Resultado de health check"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None
    response_time_ms: float = 0.0

class HealthChecker:
    """Sistema de health checks"""
    
    def __init__(self):
        self.checks: List[callable] = []
        self.last_results: Dict[str, HealthCheck] = {}
        self.logger = logging.getLogger("HealthChecker")
        
        # Registrar checks básicos
        self.register_check(self._check_system_resources)
        self.register_check(self._check_memory_usage)
        self.register_check(self._check_disk_space)
        self.register_check(self._check_network_connectivity)
    
    def register_check(self, check_func: callable):
        """Registrar un health check"""
        self.checks.append(check_func)
        self.logger.info(f"Registered health check: {check_func.__name__}")
    
    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Ejecutar todos los health checks"""
        results = {}
        
        for check_func in self.checks:
            try:
                start_time = time.time()
                result = await check_func()
                response_time = (time.time() - start_time) * 1000
                result.response_time_ms = response_time
                results[result.name] = result
                self.last_results[result.name] = result
            except Exception as e:
                self.logger.error(f"Health check {check_func.__name__} failed: {e}")
                result = HealthCheck(
                    name=check_func.__name__,
                    status=HealthStatus.UNKNOWN,
                    message=f"Check failed: {e}",
                    timestamp=datetime.now(timezone.utc)
                )
                results[result.name] = result
                self.last_results[result.name] = result
        
        return results
    
    async def _check_system_resources(self) -> HealthCheck:
        """Check system CPU and memory usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            status = HealthStatus.HEALTHY
            message = f"CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%"
            
            if cpu_percent > 90 or memory.percent > 90:
                status = HealthStatus.CRITICAL
                message = f"HIGH USAGE - CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%"
            elif cpu_percent > 70 or memory.percent > 70:
                status = HealthStatus.WARNING
                message = f"ELEVATED USAGE - CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%"
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                timestamp=datetime.now(timezone.utc),
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "memory_total_gb": memory.total / (1024**3)
                }
            )
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system resources: {e}",
                timestamp=datetime.now(timezone.utc)
            )
    
    async def _check_memory_usage(self) -> HealthCheck:
        """Check memory usage specifically"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            status = HealthStatus.HEALTHY
            message = f"Process memory: {memory_mb:.1f} MB"
            
            if memory_mb > 1000:  # 1GB
                status = HealthStatus.CRITICAL
                message = f"HIGH MEMORY USAGE: {memory_mb:.1f} MB"
            elif memory_mb > 500:  # 500MB
                status = HealthStatus.WARNING
                message = f"ELEVATED MEMORY: {memory_mb:.1f} MB"
            
            return HealthCheck(
                name="memory_usage",
                status=status,
                message=message,
                timestamp=datetime.now(timezone.utc),
                details={
                    "memory_mb": memory_mb,
                    "memory_percent": process.memory_percent()
                }
            )
        except Exception as e:
            return HealthCheck(
                name="memory_usage",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check memory: {e}",
                timestamp=datetime.now(timezone.utc)
            )
    
    async def _check_disk_space(self) -> HealthCheck:
        """Check disk space"""
        try:
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            status = HealthStatus.HEALTHY
            message = f"Disk: {used_percent:.1f}% used, {free_gb:.1f} GB free"
            
            if used_percent > 95:
                status = HealthStatus.CRITICAL
                message = f"CRITICAL DISK SPACE: {used_percent:.1f}% used, {free_gb:.1f} GB free"
            elif used_percent > 85:
                status = HealthStatus.WARNING
                message = f"LOW DISK SPACE: {used_percent:.1f}% used, {free_gb:.1f} GB free"
            
            return HealthCheck(
                name="disk_space",
                status=status,
                message=message,
                timestamp=datetime.now(timezone.utc),
                details={
                    "used_percent": used_percent,
                    "free_gb": free_gb,
                    "total_gb": total_gb
                }
            )
        except Exception as e:
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk space: {e}",
                timestamp=datetime.now(timezone.utc)
            )
    
    async def _check_network_connectivity(self) -> HealthCheck:
        """Check network connectivity"""
        try:
            import socket
            
            # Test DNS resolution
            start_time = time.time()
            socket.gethostbyname('google.com')
            dns_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY
            message = f"Network OK, DNS: {dns_time:.1f}ms"
            
            if dns_time > 5000:  # 5 seconds
                status = HealthStatus.CRITICAL
                message = f"SLOW DNS: {dns_time:.1f}ms"
            elif dns_time > 2000:  # 2 seconds
                status = HealthStatus.WARNING
                message = f"SLOW NETWORK: {dns_time:.1f}ms"
            
            return HealthCheck(
                name="network_connectivity",
                status=status,
                message=message,
                timestamp=datetime.now(timezone.utc),
                details={
                    "dns_response_ms": dns_time
                }
            )
        except Exception as e:
            return HealthCheck(
                name="network_connectivity",
                status=HealthStatus.UNKNOWN,
                message=f"Network check failed: {e}",
                timestamp=datetime.now(timezone.utc)
            )
    
    def get_overall_status(self) -> HealthStatus:
        """Obtener estado general de salud"""
        if not self.last_results:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in self.last_results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Obtener resumen del estado de salud"""
        overall_status = self.get_overall_status()
        
        return {
            "overall_status": overall_status.value,
            "total_checks": len(self.last_results),
            "healthy_checks": len([c for c in self.last_results.values() if c.status == HealthStatus.HEALTHY]),
            "warning_checks": len([c for c in self.last_results.values() if c.status == HealthStatus.WARNING]),
            "critical_checks": len([c for c in self.last_results.values() if c.status == HealthStatus.CRITICAL]),
            "unknown_checks": len([c for c in self.last_results.values() if c.status == HealthStatus.UNKNOWN]),
            "last_check": max([c.timestamp for c in self.last_results.values()]) if self.last_results else None,
            "checks": {name: {
                "status": check.status.value,
                "message": check.message,
                "response_time_ms": check.response_time_ms,
                "timestamp": check.timestamp.isoformat()
            } for name, check in self.last_results.items()}
        }

# Health check específico para el bot de trading
class TradingBotHealthChecker(HealthChecker):
    """Health checker específico para el bot de trading"""
    
    def __init__(self, bot_instance=None):
        super().__init__()
        self.bot_instance = bot_instance
        
        # Registrar checks específicos del bot
        self.register_check(self._check_bot_running)
        self.register_check(self._check_websocket_connection)
        self.register_check(self._check_recent_signals)
        self.register_check(self._check_state_persistence)
    
    async def _check_bot_running(self) -> HealthCheck:
        """Check if bot is running"""
        try:
            if not self.bot_instance:
                return HealthCheck(
                    name="bot_running",
                    status=HealthStatus.UNKNOWN,
                    message="Bot instance not available",
                    timestamp=datetime.now(timezone.utc)
                )
            
            if hasattr(self.bot_instance, 'running') and self.bot_instance.running:
                uptime = time.time() - self.bot_instance.start_time if hasattr(self.bot_instance, 'start_time') and self.bot_instance.start_time else 0
                uptime_hours = uptime / 3600
                
                return HealthCheck(
                    name="bot_running",
                    status=HealthStatus.HEALTHY,
                    message=f"Bot running for {uptime_hours:.1f} hours",
                    timestamp=datetime.now(timezone.utc),
                    details={
                        "uptime_hours": uptime_hours,
                        "start_time": self.bot_instance.start_time
                    }
                )
            else:
                return HealthCheck(
                    name="bot_running",
                    status=HealthStatus.CRITICAL,
                    message="Bot is not running",
                    timestamp=datetime.now(timezone.utc)
                )
        except Exception as e:
            return HealthCheck(
                name="bot_running",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check bot status: {e}",
                timestamp=datetime.now(timezone.utc)
            )
    
    async def _check_websocket_connection(self) -> HealthCheck:
        """Check WebSocket connection status"""
        try:
            if not self.bot_instance or not hasattr(self.bot_instance, 'paper_trader'):
                return HealthCheck(
                    name="websocket_connection",
                    status=HealthStatus.UNKNOWN,
                    message="Paper trader not available",
                    timestamp=datetime.now(timezone.utc)
                )
            
            paper_trader = self.bot_instance.paper_trader
            if hasattr(paper_trader, 'websocket') and paper_trader.websocket:
                if paper_trader.websocket.connected:
                    return HealthCheck(
                        name="websocket_connection",
                        status=HealthStatus.HEALTHY,
                        message="WebSocket connected",
                        timestamp=datetime.now(timezone.utc)
                    )
                else:
                    return HealthCheck(
                        name="websocket_connection",
                        status=HealthStatus.CRITICAL,
                        message="WebSocket disconnected",
                        timestamp=datetime.now(timezone.utc)
                    )
            else:
                return HealthCheck(
                    name="websocket_connection",
                    status=HealthStatus.WARNING,
                    message="WebSocket not initialized",
                    timestamp=datetime.now(timezone.utc)
                )
        except Exception as e:
            return HealthCheck(
                name="websocket_connection",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check WebSocket: {e}",
                timestamp=datetime.now(timezone.utc)
            )
    
    async def _check_recent_signals(self) -> HealthCheck:
        """Check if bot is generating signals recently"""
        try:
            if not self.bot_instance:
                return HealthCheck(
                    name="recent_signals",
                    status=HealthStatus.UNKNOWN,
                    message="Bot instance not available",
                    timestamp=datetime.now(timezone.utc)
                )
            
            if hasattr(self.bot_instance, 'signal_counter'):
                signal_count = self.bot_instance.signal_counter
                uptime_hours = (time.time() - self.bot_instance.start_time) / 3600 if hasattr(self.bot_instance, 'start_time') and self.bot_instance.start_time else 1
                signals_per_hour = signal_count / uptime_hours if uptime_hours > 0 else 0
                
                status = HealthStatus.HEALTHY
                message = f"Generated {signal_count} signals ({signals_per_hour:.1f}/hour)"
                
                if signals_per_hour < 0.5:  # Menos de 1 señal cada 2 horas
                    status = HealthStatus.WARNING
                    message = f"LOW SIGNAL RATE: {signal_count} signals ({signals_per_hour:.1f}/hour)"
                elif signal_count == 0 and uptime_hours > 1:
                    status = HealthStatus.CRITICAL
                    message = f"NO SIGNALS GENERATED in {uptime_hours:.1f} hours"
                
                return HealthCheck(
                    name="recent_signals",
                    status=status,
                    message=message,
                    timestamp=datetime.now(timezone.utc),
                    details={
                        "signal_count": signal_count,
                        "signals_per_hour": signals_per_hour,
                        "uptime_hours": uptime_hours
                    }
                )
            else:
                return HealthCheck(
                    name="recent_signals",
                    status=HealthStatus.UNKNOWN,
                    message="Signal counter not available",
                    timestamp=datetime.now(timezone.utc)
                )
        except Exception as e:
            return HealthCheck(
                name="recent_signals",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check signals: {e}",
                timestamp=datetime.now(timezone.utc)
            )
    
    async def _check_state_persistence(self) -> HealthCheck:
        """Check state persistence system"""
        try:
            if not self.bot_instance or not hasattr(self.bot_instance, 'state_manager'):
                return HealthCheck(
                    name="state_persistence",
                    status=HealthStatus.UNKNOWN,
                    message="State manager not available",
                    timestamp=datetime.now(timezone.utc)
                )
            
            state_manager = self.bot_instance.state_manager
            state_file = state_manager.state_file
            
            if state_file.exists():
                # Check file age
                file_age = time.time() - state_file.stat().st_mtime
                file_age_minutes = file_age / 60
                
                status = HealthStatus.HEALTHY
                message = f"State file exists, last update: {file_age_minutes:.1f} min ago"
                
                if file_age_minutes > 60:  # 1 hour
                    status = HealthStatus.WARNING
                    message = f"STALE STATE: Last update {file_age_minutes:.1f} min ago"
                elif file_age_minutes > 180:  # 3 hours
                    status = HealthStatus.CRITICAL
                    message = f"VERY STALE STATE: Last update {file_age_minutes:.1f} min ago"
                
                return HealthCheck(
                    name="state_persistence",
                    status=status,
                    message=message,
                    timestamp=datetime.now(timezone.utc),
                    details={
                        "file_age_minutes": file_age_minutes,
                        "file_size_bytes": state_file.stat().st_size
                    }
                )
            else:
                return HealthCheck(
                    name="state_persistence",
                    status=HealthStatus.WARNING,
                    message="State file does not exist",
                    timestamp=datetime.now(timezone.utc)
                )
        except Exception as e:
            return HealthCheck(
                name="state_persistence",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check state persistence: {e}",
                timestamp=datetime.now(timezone.utc)
            )
