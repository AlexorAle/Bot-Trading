"""
Error Handler - Sistema robusto de manejo de errores
Incluye circuit breakers, retry logic, y graceful degradation
"""

import asyncio
import logging
import time
import functools
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import traceback

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Severidad de errores"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categorías de errores"""
    NETWORK = "network"
    API = "api"
    DATA = "data"
    TRADING = "trading"
    SYSTEM = "system"
    CONFIG = "config"

@dataclass
class ErrorContext:
    """Contexto de error para logging y recovery"""
    error: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    operation: str
    retry_count: int = 0
    max_retries: int = 3
    last_attempt: Optional[datetime] = None
    recovery_action: Optional[str] = None

class CircuitBreakerState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3
    timeout: int = 30  # seconds

class CircuitBreaker:
    """Circuit breaker para proteger contra fallos en cascada"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.logger = logging.getLogger(f"CircuitBreaker.{name}")
    
    def can_execute(self) -> bool:
        """Verificar si se puede ejecutar la operación"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")
                return True
            return False
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def _should_attempt_reset(self) -> bool:
        """Verificar si se debe intentar resetear el circuit breaker"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now(timezone.utc) - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def record_success(self):
        """Registrar éxito"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.logger.info(f"Circuit breaker {self.name} reset to CLOSED state")
    
    def record_failure(self):
        """Registrar fallo"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker {self.name} opened due to {self.failure_count} failures")

class RetryConfig:
    """Configuración de retry"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

class ErrorHandler:
    """Manejador principal de errores"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_history: List[ErrorContext] = []
        self.max_history = 1000
        self.logger = logging.getLogger("ErrorHandler")
        
        # Configuraciones por categoría
        self.retry_configs = {
            ErrorCategory.NETWORK: RetryConfig(max_retries=5, base_delay=2.0),
            ErrorCategory.API: RetryConfig(max_retries=3, base_delay=1.0),
            ErrorCategory.DATA: RetryConfig(max_retries=2, base_delay=0.5),
            ErrorCategory.TRADING: RetryConfig(max_retries=1, base_delay=0.1),
            ErrorCategory.SYSTEM: RetryConfig(max_retries=0, base_delay=0.0),
            ErrorCategory.CONFIG: RetryConfig(max_retries=0, base_delay=0.0),
        }
    
    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Obtener o crear circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]
    
    def classify_error(self, error: Exception, operation: str) -> ErrorContext:
        """Clasificar error por tipo y severidad"""
        error_str = str(error).lower()
        
        # Clasificar por tipo
        if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'socket']):
            category = ErrorCategory.NETWORK
            severity = ErrorSeverity.MEDIUM
        elif any(keyword in error_str for keyword in ['api', 'http', 'unauthorized', 'forbidden']):
            category = ErrorCategory.API
            severity = ErrorSeverity.HIGH
        elif any(keyword in error_str for keyword in ['data', 'parse', 'format', 'validation']):
            category = ErrorCategory.DATA
            severity = ErrorSeverity.MEDIUM
        elif any(keyword in error_str for keyword in ['trade', 'order', 'position', 'balance']):
            category = ErrorCategory.TRADING
            severity = ErrorSeverity.HIGH
        elif any(keyword in error_str for keyword in ['config', 'file', 'path', 'permission']):
            category = ErrorCategory.CONFIG
            severity = ErrorSeverity.CRITICAL
        else:
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.MEDIUM
        
        return ErrorContext(
            error=error,
            severity=severity,
            category=category,
            operation=operation
        )
    
    def log_error(self, context: ErrorContext):
        """Log error con contexto completo"""
        self.error_history.append(context)
        
        # Limpiar historial antiguo
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
        
        # Log según severidad
        log_msg = f"Error in {context.operation}: {context.error}"
        log_data = {
            'severity': context.severity.value,
            'category': context.category.value,
            'retry_count': context.retry_count,
            'operation': context.operation
        }
        
        if context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_msg, extra=log_data)
        elif context.severity == ErrorSeverity.HIGH:
            self.logger.error(log_msg, extra=log_data)
        elif context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_msg, extra=log_data)
        else:
            self.logger.info(log_msg, extra=log_data)
    
    def should_retry(self, context: ErrorContext) -> bool:
        """Determinar si se debe reintentar"""
        if context.retry_count >= context.max_retries:
            return False
        
        # No retry para errores críticos o de configuración
        if context.severity == ErrorSeverity.CRITICAL or context.category == ErrorCategory.CONFIG:
            return False
        
        return True
    
    def calculate_delay(self, context: ErrorContext) -> float:
        """Calcular delay para retry"""
        config = self.retry_configs.get(context.category, RetryConfig())
        
        # Exponential backoff
        delay = config.base_delay * (config.exponential_base ** context.retry_count)
        delay = min(delay, config.max_delay)
        
        # Jitter para evitar thundering herd
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecutar función con retry automático"""
        operation = f"{func.__name__}"
        context = None
        
        for attempt in range(10):  # Max 10 attempts
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Éxito - resetear circuit breaker si existe
                if context and hasattr(context, 'circuit_breaker'):
                    context.circuit_breaker.record_success()
                
                return result
                
            except Exception as e:
                # Clasificar error
                context = self.classify_error(e, operation)
                context.retry_count = attempt
                context.last_attempt = datetime.now(timezone.utc)
                
                # Log error
                self.log_error(context)
                
                # Verificar circuit breaker
                cb_name = f"{context.category.value}_{operation}"
                circuit_breaker = self.get_circuit_breaker(cb_name)
                context.circuit_breaker = circuit_breaker
                
                if not circuit_breaker.can_execute():
                    raise Exception(f"Circuit breaker {cb_name} is OPEN - operation blocked")
                
                # Determinar si reintentar
                if not self.should_retry(context):
                    circuit_breaker.record_failure()
                    raise e
                
                # Calcular delay y esperar
                delay = self.calculate_delay(context)
                self.logger.info(f"Retrying {operation} in {delay:.2f}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)
        
        # Si llegamos aquí, todos los intentos fallaron
        if context:
            context.circuit_breaker.record_failure()
        raise Exception(f"All retry attempts failed for {operation}")

def with_error_handling(
    error_handler: ErrorHandler = None,
    circuit_breaker_name: str = None,
    max_retries: int = None,
    category: ErrorCategory = None
):
    """Decorator para manejo automático de errores"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()
            
            # Configurar context si se especifica
            if circuit_breaker_name:
                cb = handler.get_circuit_breaker(circuit_breaker_name)
                if not cb.can_execute():
                    raise Exception(f"Circuit breaker {circuit_breaker_name} is OPEN")
            
            return await handler.execute_with_retry(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()
            
            # Configurar context si se especifica
            if circuit_breaker_name:
                cb = handler.get_circuit_breaker(circuit_breaker_name)
                if not cb.can_execute():
                    raise Exception(f"Circuit breaker {circuit_breaker_name} is OPEN")
            
            # Para funciones síncronas, ejecutar en loop
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(handler.execute_with_retry(func, *args, **kwargs))
            except RuntimeError:
                # Si no hay loop, crear uno nuevo
                return asyncio.run(handler.execute_with_retry(func, *args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

class GracefulDegradation:
    """Sistema de degradación graceful"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.fallback_functions: Dict[str, Callable] = {}
        self.logger = logging.getLogger("GracefulDegradation")
    
    def register_fallback(self, operation: str, fallback_func: Callable):
        """Registrar función de fallback"""
        self.fallback_functions[operation] = fallback_func
        self.logger.info(f"Registered fallback for {operation}")
    
    async def execute_with_fallback(self, operation: str, primary_func: Callable, *args, **kwargs):
        """Ejecutar con fallback automático"""
        try:
            return await self.error_handler.execute_with_retry(primary_func, *args, **kwargs)
        except Exception as e:
            if operation in self.fallback_functions:
                self.logger.warning(f"Primary operation {operation} failed, using fallback: {e}")
                fallback_func = self.fallback_functions[operation]
                return await self.error_handler.execute_with_retry(fallback_func, *args, **kwargs)
            else:
                raise e

# Instancia global del error handler
global_error_handler = ErrorHandler()
global_graceful_degradation = GracefulDegradation(global_error_handler)
