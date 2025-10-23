"""
Metrics Collector - Sistema de métricas para Prometheus
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Tipos de métricas"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class Metric:
    """Métrica individual"""
    name: str
    value: float
    labels: Dict[str, str]
    metric_type: MetricType
    timestamp: float
    help_text: str = ""

class MetricsCollector:
    """Recolector de métricas para el bot de trading"""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.Lock()
        self.logger = logging.getLogger("MetricsCollector")
        
        # Métricas del bot
        self._init_bot_metrics()
    
    def _init_bot_metrics(self):
        """Inicializar métricas del bot"""
        # Métricas de trading
        self._create_metric("trading_signals_total", 0, {"strategy": "vstru"}, MetricType.COUNTER, "Total trading signals generated")
        self._create_metric("trading_trades_total", 0, {}, MetricType.COUNTER, "Total trades executed")
        self._create_metric("trading_trades_wins", 0, {}, MetricType.COUNTER, "Total winning trades")
        self._create_metric("trading_trades_losses", 0, {}, MetricType.COUNTER, "Total losing trades")
        self._create_metric("trading_pnl_total", 0.0, {}, MetricType.GAUGE, "Total PnL")
        self._create_metric("trading_balance", 10000.0, {}, MetricType.GAUGE, "Current balance")
        
        # Métricas de sistema
        self._create_metric("bot_uptime_seconds", 0, {}, MetricType.GAUGE, "Bot uptime in seconds")
        self._create_metric("bot_status", 1, {}, MetricType.GAUGE, "Bot status (1=running, 0=stopped)")
        self._create_metric("bot_memory_usage_bytes", 0, {}, MetricType.GAUGE, "Bot memory usage in bytes")
        self._create_metric("bot_cpu_usage_percent", 0, {}, MetricType.GAUGE, "Bot CPU usage percentage")
        
        # Métricas de conectividad
        self._create_metric("websocket_connected", 0, {}, MetricType.GAUGE, "WebSocket connection status")
        self._create_metric("api_requests_total", 0, {"endpoint": "bybit"}, MetricType.COUNTER, "Total API requests")
        self._create_metric("api_requests_failed", 0, {"endpoint": "bybit"}, MetricType.COUNTER, "Failed API requests")
        self._create_metric("api_response_time_seconds", 0, {"endpoint": "bybit"}, MetricType.HISTOGRAM, "API response time")
        
        # Métricas de errores
        self._create_metric("errors_total", 0, {"type": "system"}, MetricType.COUNTER, "Total errors")
        self._create_metric("circuit_breaker_open", 0, {"name": "default"}, MetricType.GAUGE, "Circuit breaker status")
        
        # Métricas de health
        self._create_metric("health_check_status", 1, {"check": "overall"}, MetricType.GAUGE, "Health check status")
        self._create_metric("health_check_duration_seconds", 0, {"check": "overall"}, MetricType.HISTOGRAM, "Health check duration")
        
        self.logger.info("Metrics collector initialized")
    
    def _create_metric(self, name: str, value: float, labels: Dict[str, str], metric_type: MetricType, help_text: str = ""):
        """Crear una nueva métrica"""
        with self.lock:
            self.metrics[name] = Metric(
                name=name,
                value=value,
                labels=labels,
                metric_type=metric_type,
                timestamp=time.time(),
                help_text=help_text
            )
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Incrementar contador"""
        with self.lock:
            key = f"{name}_{self._labels_to_key(labels or {})}"
            self.counters[key] += value
            self._update_metric(name, self.counters[key], labels or {})
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Establecer valor de gauge"""
        with self.lock:
            key = f"{name}_{self._labels_to_key(labels or {})}"
            self.gauges[key] = value
            self._update_metric(name, value, labels or {})
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observar valor en histograma"""
        with self.lock:
            key = f"{name}_{self._labels_to_key(labels or {})}"
            self.histograms[key].append(value)
            self._update_metric(name, value, labels or {})
    
    def _update_metric(self, name: str, value: float, labels: Dict[str, str]):
        """Actualizar métrica existente"""
        if name in self.metrics:
            self.metrics[name].value = value
            self.metrics[name].labels.update(labels)
            self.metrics[name].timestamp = time.time()
    
    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """Convertir labels a clave"""
        if not labels:
            return ""
        return "_".join([f"{k}={v}" for k, v in sorted(labels.items())])
    
    def get_metric(self, name: str, labels: Dict[str, str] = None) -> Optional[Metric]:
        """Obtener métrica específica"""
        with self.lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if labels:
                    metric.labels.update(labels)
                return metric
            return None
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Obtener todas las métricas"""
        with self.lock:
            return self.metrics.copy()
    
    def export_prometheus_format(self) -> str:
        """Exportar métricas en formato Prometheus"""
        with self.lock:
            lines = []
            
            # Agregar comentarios de ayuda
            for name, metric in self.metrics.items():
                if metric.help_text:
                    lines.append(f"# HELP {name} {metric.help_text}")
                lines.append(f"# TYPE {name} {metric.metric_type.value}")
            
            # Agregar métricas
            for name, metric in self.metrics.items():
                labels_str = ""
                if metric.labels:
                    labels_str = "{" + ",".join([f'{k}="{v}"' for k, v in metric.labels.items()]) + "}"
                
                lines.append(f"{name}{labels_str} {metric.value} {int(metric.timestamp * 1000)}")
            
            return "\n".join(lines)
    
    # Métodos específicos para el bot de trading
    def record_signal(self, strategy: str = "vstru"):
        """Registrar señal generada"""
        self.increment_counter("trading_signals_total", labels={"strategy": strategy})
        self.logger.debug(f"Signal recorded for strategy: {strategy}")
    
    def record_trade(self, pnl: float, is_win: bool = None):
        """Registrar trade ejecutado"""
        self.increment_counter("trading_trades_total")
        
        if is_win is not None:
            if is_win:
                self.increment_counter("trading_trades_wins")
            else:
                self.increment_counter("trading_trades_losses")
        
        # Actualizar PnL total
        current_pnl = self.get_metric("trading_pnl_total")
        if current_pnl:
            new_pnl = current_pnl.value + pnl
            self.set_gauge("trading_pnl_total", new_pnl)
        
        self.logger.debug(f"Trade recorded: PnL={pnl}, is_win={is_win}")
    
    def update_balance(self, balance: float):
        """Actualizar balance"""
        self.set_gauge("trading_balance", balance)
        self.logger.debug(f"Balance updated: {balance}")
    
    def record_api_request(self, endpoint: str, success: bool, response_time: float):
        """Registrar request de API"""
        self.increment_counter("api_requests_total", labels={"endpoint": endpoint})
        if not success:
            self.increment_counter("api_requests_failed", labels={"endpoint": endpoint})
        
        self.observe_histogram("api_response_time_seconds", response_time, labels={"endpoint": endpoint})
        self.logger.debug(f"API request recorded: {endpoint}, success={success}, time={response_time:.3f}s")
    
    def record_error(self, error_type: str):
        """Registrar error"""
        self.increment_counter("errors_total", labels={"type": error_type})
        self.logger.warning(f"Error recorded: {error_type}")
    
    def update_bot_status(self, running: bool, uptime: float = None):
        """Actualizar estado del bot"""
        self.set_gauge("bot_status", 1 if running else 0)
        if uptime is not None:
            self.set_gauge("bot_uptime_seconds", uptime)
        self.logger.debug(f"Bot status updated: running={running}, uptime={uptime}")
    
    def update_websocket_status(self, connected: bool):
        """Actualizar estado de WebSocket"""
        self.set_gauge("websocket_connected", 1 if connected else 0)
        self.logger.debug(f"WebSocket status updated: connected={connected}")
    
    def update_system_metrics(self, memory_bytes: int, cpu_percent: float):
        """Actualizar métricas del sistema"""
        self.set_gauge("bot_memory_usage_bytes", memory_bytes)
        self.set_gauge("bot_cpu_usage_percent", cpu_percent)
        self.logger.debug(f"System metrics updated: memory={memory_bytes} bytes, cpu={cpu_percent}%")
    
    def update_health_status(self, check_name: str, status: int, duration: float):
        """Actualizar estado de health check"""
        self.set_gauge("health_check_status", status, labels={"check": check_name})
        self.observe_histogram("health_check_duration_seconds", duration, labels={"check": check_name})
        self.logger.debug(f"Health check updated: {check_name}, status={status}, duration={duration:.3f}s")
    
    def update_circuit_breaker(self, name: str, is_open: bool):
        """Actualizar estado de circuit breaker"""
        self.set_gauge("circuit_breaker_open", 1 if is_open else 0, labels={"name": name})
        self.logger.debug(f"Circuit breaker updated: {name}, open={is_open}")

# Instancia global del collector
global_metrics_collector = MetricsCollector()
