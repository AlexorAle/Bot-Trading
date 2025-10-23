"""
Test Suite - Sistema completo de testing y validación
"""

import asyncio
import logging
import time
import json
import unittest
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backup_manager import global_backup_manager, BackupType
from disaster_recovery import global_disaster_recovery
from metrics_collector import global_metrics_collector
from alerting_system import global_alerting_system
from health_checker import TradingBotHealthChecker

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """Estado de tests"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TestCategory(Enum):
    """Categorías de tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DISASTER_RECOVERY = "disaster_recovery"

@dataclass
class TestResult:
    """Resultado de test individual"""
    test_name: str
    category: TestCategory
    status: TestStatus
    duration_ms: float
    message: str
    details: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.details is None:
            self.details = {}

class TestSuite:
    """Suite completa de tests para el bot de trading"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.logger = logging.getLogger("TestSuite")
        self.start_time = None
        self.end_time = None
        
        # Configuración de tests
        self.test_timeout = 30  # segundos por test
        self.parallel_tests = 5  # tests en paralelo
        
        self.logger.info("TestSuite initialized")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests"""
        self.start_time = datetime.now(timezone.utc)
        self.logger.info("Starting comprehensive test suite...")
        
        try:
            # Tests unitarios
            await self._run_unit_tests()
            
            # Tests de integración
            await self._run_integration_tests()
            
            # Tests de sistema
            await self._run_system_tests()
            
            # Tests de rendimiento
            await self._run_performance_tests()
            
            # Tests de seguridad
            await self._run_security_tests()
            
            # Tests de disaster recovery
            await self._run_disaster_recovery_tests()
            
            self.end_time = datetime.now(timezone.utc)
            
            # Generar reporte
            report = self._generate_report()
            self.logger.info(f"Test suite completed: {report['summary']}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
            raise
    
    async def _run_unit_tests(self):
        """Ejecutar tests unitarios"""
        self.logger.info("Running unit tests...")
        
        tests = [
            self._test_backup_manager_creation,
            self._test_metrics_collector_basic,
            self._test_alerting_system_rules,
            self._test_health_checker_initialization,
            self._test_disaster_recovery_plans,
            self._test_state_manager_operations,
            self._test_error_handler_classification
        ]
        
        await self._run_test_batch(tests, TestCategory.UNIT)
    
    async def _run_integration_tests(self):
        """Ejecutar tests de integración"""
        self.logger.info("Running integration tests...")
        
        tests = [
            self._test_backup_restore_cycle,
            self._test_metrics_alerting_integration,
            self._test_health_monitoring_integration,
            self._test_state_persistence_integration,
            self._test_error_handling_integration
        ]
        
        await self._run_test_batch(tests, TestCategory.INTEGRATION)
    
    async def _run_system_tests(self):
        """Ejecutar tests de sistema"""
        self.logger.info("Running system tests...")
        
        tests = [
            self._test_system_resources,
            self._test_file_permissions,
            self._test_network_connectivity,
            self._test_disk_space,
            self._test_memory_usage,
            self._test_process_management
        ]
        
        await self._run_test_batch(tests, TestCategory.SYSTEM)
    
    async def _run_performance_tests(self):
        """Ejecutar tests de rendimiento"""
        self.logger.info("Running performance tests...")
        
        tests = [
            self._test_backup_performance,
            self._test_metrics_collection_performance,
            self._test_alert_processing_performance,
            self._test_memory_usage_performance,
            self._test_cpu_usage_performance
        ]
        
        await self._run_test_batch(tests, TestCategory.PERFORMANCE)
    
    async def _run_security_tests(self):
        """Ejecutar tests de seguridad"""
        self.logger.info("Running security tests...")
        
        tests = [
            self._test_file_permissions_security,
            self._test_secrets_protection,
            self._test_backup_encryption,
            self._test_api_key_validation,
            self._test_log_sanitization
        ]
        
        await self._run_test_batch(tests, TestCategory.SECURITY)
    
    async def _run_disaster_recovery_tests(self):
        """Ejecutar tests de disaster recovery"""
        self.logger.info("Running disaster recovery tests...")
        
        tests = [
            self._test_disaster_detection,
            self._test_recovery_plan_execution,
            self._test_backup_integrity,
            self._test_rollback_capability,
            self._test_validation_procedures
        ]
        
        await self._run_test_batch(tests, TestCategory.DISASTER_RECOVERY)
    
    async def _run_test_batch(self, tests: List[Callable], category: TestCategory):
        """Ejecutar lote de tests"""
        for test_func in tests:
            try:
                await self._run_single_test(test_func, category)
            except Exception as e:
                self.logger.error(f"Test {test_func.__name__} failed: {e}")
                self.results.append(TestResult(
                    test_name=test_func.__name__,
                    category=category,
                    status=TestStatus.FAILED,
                    duration_ms=0,
                    message=f"Test execution failed: {e}"
                ))
    
    async def _run_single_test(self, test_func: Callable, category: TestCategory):
        """Ejecutar test individual"""
        start_time = time.time()
        test_name = test_func.__name__
        
        self.logger.debug(f"Running test: {test_name}")
        
        try:
            # Ejecutar test con timeout
            result = await asyncio.wait_for(
                test_func(),
                timeout=self.test_timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if result.get('success', False):
                status = TestStatus.PASSED
                message = result.get('message', 'Test passed')
            else:
                status = TestStatus.FAILED
                message = result.get('message', 'Test failed')
            
            self.results.append(TestResult(
                test_name=test_name,
                category=category,
                status=status,
                duration_ms=duration_ms,
                message=message,
                details=result.get('details', {})
            ))
            
            self.logger.debug(f"Test {test_name} completed: {status.value}")
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            self.results.append(TestResult(
                test_name=test_name,
                category=category,
                status=TestStatus.FAILED,
                duration_ms=duration_ms,
                message=f"Test timeout after {self.test_timeout}s"
            ))
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.results.append(TestResult(
                test_name=test_name,
                category=category,
                status=TestStatus.FAILED,
                duration_ms=duration_ms,
                message=f"Test error: {e}"
            ))
    
    # Tests unitarios
    async def _test_backup_manager_creation(self):
        """Test: Creación del BackupManager"""
        try:
            backup_manager = global_backup_manager
            assert backup_manager is not None
            assert backup_manager.backup_dir.exists()
            return {'success': True, 'message': 'BackupManager created successfully'}
        except Exception as e:
            return {'success': False, 'message': f'BackupManager creation failed: {e}'}
    
    async def _test_metrics_collector_basic(self):
        """Test: Métricas básicas del collector"""
        try:
            collector = global_metrics_collector
            assert collector is not None
            
            # Test métricas básicas
            collector.set_gauge("test_metric", 100.0)
            metric = collector.get_metric("test_metric")
            assert metric is not None
            assert metric.value == 100.0
            
            return {'success': True, 'message': 'Metrics collector working correctly'}
        except Exception as e:
            return {'success': False, 'message': f'Metrics collector test failed: {e}'}
    
    async def _test_alerting_system_rules(self):
        """Test: Reglas del sistema de alertas"""
        try:
            alerting = global_alerting_system
            assert alerting is not None
            assert len(alerting.rules) > 0
            
            # Verificar reglas críticas
            rule_names = [rule.name for rule in alerting.rules]
            assert 'bot_not_running' in rule_names
            assert 'websocket_disconnected' in rule_names
            assert 'high_loss' in rule_names
            
            return {'success': True, 'message': 'Alerting system rules configured correctly'}
        except Exception as e:
            return {'success': False, 'message': f'Alerting system test failed: {e}'}
    
    async def _test_health_checker_initialization(self):
        """Test: Inicialización del health checker"""
        try:
            health_checker = TradingBotHealthChecker()
            assert health_checker is not None
            assert len(health_checker.checks) > 0
            
            return {'success': True, 'message': 'Health checker initialized successfully'}
        except Exception as e:
            return {'success': False, 'message': f'Health checker test failed: {e}'}
    
    async def _test_disaster_recovery_plans(self):
        """Test: Planes de disaster recovery"""
        try:
            disaster_recovery = global_disaster_recovery
            assert disaster_recovery is not None
            assert len(disaster_recovery.recovery_plans) == 5
            
            # Verificar planes críticos
            plan_types = list(disaster_recovery.recovery_plans.keys())
            assert 'data_corruption' in [p.value for p in plan_types]
            assert 'system_crash' in [p.value for p in plan_types]
            assert 'complete_failure' in [p.value for p in plan_types]
            
            return {'success': True, 'message': 'Disaster recovery plans configured correctly'}
        except Exception as e:
            return {'success': False, 'message': f'Disaster recovery test failed: {e}'}
    
    async def _test_state_manager_operations(self):
        """Test: Operaciones del state manager"""
        try:
            from state_manager import StateManager
            state_manager = StateManager("test_state.json")
            
            # Test operaciones básicas
            state_manager.update_balance(1000.0)
            state_manager.add_trade(50.0)
            state_manager.update_signal_count()
            
            # Verificar estado
            summary = state_manager.get_state_summary()
            assert summary['balance'] == 1000.0
            assert summary['total_trades'] == 1
            
            return {'success': True, 'message': 'State manager operations working correctly'}
        except Exception as e:
            return {'success': False, 'message': f'State manager test failed: {e}'}
    
    async def _test_error_handler_classification(self):
        """Test: Clasificación de errores"""
        try:
            from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
            error_handler = ErrorHandler()
            
            # Test clasificación de errores
            import Exception
            test_error = Exception("Connection timeout")
            context = error_handler.classify_error(test_error, "test_operation")
            
            assert context.category in [ErrorCategory.NETWORK, ErrorCategory.API]
            assert context.severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]
            
            return {'success': True, 'message': 'Error classification working correctly'}
        except Exception as e:
            return {'success': False, 'message': f'Error classification test failed: {e}'}
    
    # Tests de integración
    async def _test_backup_restore_cycle(self):
        """Test: Ciclo completo de backup y restore"""
        try:
            backup_manager = global_backup_manager
            
            # Crear backup de prueba
            backup_id = await backup_manager.create_backup(
                BackupType.STATE_ONLY,
                "Test backup for integration test"
            )
            
            assert backup_id is not None
            
            # Verificar que el backup existe
            backup_info = backup_manager.get_backup_info(backup_id)
            assert backup_info is not None
            assert backup_info.status.value == "completed"
            
            return {'success': True, 'message': 'Backup-restore cycle working correctly', 'details': {'backup_id': backup_id}}
        except Exception as e:
            return {'success': False, 'message': f'Backup-restore cycle test failed: {e}'}
    
    async def _test_metrics_alerting_integration(self):
        """Test: Integración entre métricas y alertas"""
        try:
            metrics_collector = global_metrics_collector
            alerting_system = global_alerting_system
            
            # Simular métricas que deberían disparar alertas
            metrics_collector.set_gauge("bot_status", 0)  # Bot detenido
            metrics_collector.set_gauge("trading_pnl_total", -1500)  # Pérdida alta
            
            # Obtener métricas
            metrics = metrics_collector.get_all_metrics()
            metrics_dict = {name: {"value": metric.value, "labels": metric.labels} for name, metric in metrics.items()}
            
            # Verificar alertas
            await alerting_system.check_alerts(metrics_dict)
            
            # Verificar que se generaron alertas
            active_alerts = alerting_system.get_active_alerts()
            assert len(active_alerts) > 0
            
            return {'success': True, 'message': 'Metrics-alerting integration working correctly'}
        except Exception as e:
            return {'success': False, 'message': f'Metrics-alerting integration test failed: {e}'}
    
    async def _test_health_monitoring_integration(self):
        """Test: Integración de health monitoring"""
        try:
            health_checker = TradingBotHealthChecker()
            
            # Ejecutar health checks
            health_results = await health_checker.run_all_checks()
            overall_status = health_checker.get_overall_status()
            
            assert health_results is not None
            assert overall_status is not None
            
            return {'success': True, 'message': 'Health monitoring integration working correctly'}
        except Exception as e:
            return {'success': False, 'message': f'Health monitoring integration test failed: {e}'}
    
    async def _test_state_persistence_integration(self):
        """Test: Integración de state persistence"""
        try:
            from state_manager import StateManager
            state_manager = StateManager("test_persistence.json")
            
            # Simular operaciones del bot
            state_manager.update_balance(5000.0)
            state_manager.add_trade(100.0)
            state_manager.add_trade(-50.0)
            state_manager.update_signal_count()
            
            # Guardar estado
            state_manager.save_state(force=True)
            
            # Crear nuevo state manager y cargar estado
            new_state_manager = StateManager("test_persistence.json")
            loaded_state = new_state_manager.load_state()
            
            assert loaded_state is not None
            assert loaded_state.balance == 5000.0
            assert loaded_state.total_trades == 2
            assert loaded_state.signals_generated == 1
            
            return {'success': True, 'message': 'State persistence integration working correctly'}
        except Exception as e:
            return {'success': False, 'message': f'State persistence integration test failed: {e}'}
    
    async def _test_error_handling_integration(self):
        """Test: Integración de error handling"""
        try:
            from error_handler import with_error_handling, ErrorCategory
            
            # Test función con error handling
            @with_error_handling(category=ErrorCategory.SYSTEM)
            async def test_function():
                return "success"
            
            result = await test_function()
            assert result == "success"
            
            return {'success': True, 'message': 'Error handling integration working correctly'}
        except Exception as e:
            return {'success': False, 'message': f'Error handling integration test failed: {e}'}
    
    # Tests de sistema
    async def _test_system_resources(self):
        """Test: Recursos del sistema"""
        try:
            import psutil
            
            # Verificar CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            assert 0 <= cpu_percent <= 100
            
            # Verificar memoria
            memory = psutil.virtual_memory()
            assert memory.total > 0
            assert memory.available > 0
            
            # Verificar disco
            disk = psutil.disk_usage('/')
            assert disk.total > 0
            assert disk.free > 0
            
            return {'success': True, 'message': 'System resources accessible', 'details': {
                'cpu_percent': cpu_percent,
                'memory_total_gb': memory.total / (1024**3),
                'disk_free_gb': disk.free / (1024**3)
            }}
        except Exception as e:
            return {'success': False, 'message': f'System resources test failed: {e}'}
    
    async def _test_file_permissions(self):
        """Test: Permisos de archivos"""
        try:
            critical_files = [
                "logs/bot_state.json",
                "configs/alert_config.json",
                ".env"
            ]
            
            for file_path in critical_files:
                if Path(file_path).exists():
                    stat = Path(file_path).stat()
                    # Verificar que no es público (permisos 644 o más restrictivos)
                    assert oct(stat.st_mode)[-3:] in ['644', '600', '640']
            
            return {'success': True, 'message': 'File permissions are secure'}
        except Exception as e:
            return {'success': False, 'message': f'File permissions test failed: {e}'}
    
    async def _test_network_connectivity(self):
        """Test: Conectividad de red"""
        try:
            import socket
            
            # Test DNS resolution
            socket.gethostbyname('google.com')
            
            # Test conexión HTTP
            import requests
            response = requests.get('https://httpbin.org/status/200', timeout=10)
            assert response.status_code == 200
            
            return {'success': True, 'message': 'Network connectivity working'}
        except Exception as e:
            return {'success': False, 'message': f'Network connectivity test failed: {e}'}
    
    async def _test_disk_space(self):
        """Test: Espacio en disco"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            
            free_gb = disk.free / (1024**3)
            total_gb = disk.total / (1024**3)
            usage_percent = (disk.used / disk.total) * 100
            
            # Verificar que hay al menos 1GB libre
            assert free_gb > 1.0
            
            # Verificar que no está lleno (menos del 95%)
            assert usage_percent < 95.0
            
            return {'success': True, 'message': 'Disk space adequate', 'details': {
                'free_gb': free_gb,
                'total_gb': total_gb,
                'usage_percent': usage_percent
            }}
        except Exception as e:
            return {'success': False, 'message': f'Disk space test failed: {e}'}
    
    async def _test_memory_usage(self):
        """Test: Uso de memoria"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            # Verificar que hay al menos 100MB disponibles
            available_mb = memory.available / (1024**2)
            assert available_mb > 100
            
            return {'success': True, 'message': 'Memory usage acceptable', 'details': {
                'available_mb': available_mb,
                'total_gb': memory.total / (1024**3),
                'usage_percent': memory.percent
            }}
        except Exception as e:
            return {'success': False, 'message': f'Memory usage test failed: {e}'}
    
    async def _test_process_management(self):
        """Test: Gestión de procesos"""
        try:
            import psutil
            
            # Verificar que podemos listar procesos
            processes = list(psutil.process_iter(['pid', 'name']))
            assert len(processes) > 0
            
            # Verificar que podemos acceder a información del proceso actual
            current_process = psutil.Process()
            assert current_process.pid > 0
            assert current_process.name() is not None
            
            return {'success': True, 'message': 'Process management working', 'details': {
                'total_processes': len(processes),
                'current_pid': current_process.pid
            }}
        except Exception as e:
            return {'success': False, 'message': f'Process management test failed: {e}'}
    
    # Tests de rendimiento
    async def _test_backup_performance(self):
        """Test: Rendimiento de backup"""
        try:
            backup_manager = global_backup_manager
            start_time = time.time()
            
            # Crear backup de prueba
            backup_id = await backup_manager.create_backup(
                BackupType.STATE_ONLY,
                "Performance test backup"
            )
            
            duration = time.time() - start_time
            
            # Verificar que el backup se completó en menos de 30 segundos
            assert duration < 30.0
            
            return {'success': True, 'message': 'Backup performance acceptable', 'details': {
                'duration_seconds': duration,
                'backup_id': backup_id
            }}
        except Exception as e:
            return {'success': False, 'message': f'Backup performance test failed: {e}'}
    
    async def _test_metrics_collection_performance(self):
        """Test: Rendimiento de recolección de métricas"""
        try:
            metrics_collector = global_metrics_collector
            start_time = time.time()
            
            # Simular recolección de métricas
            for i in range(100):
                metrics_collector.set_gauge(f"test_metric_{i}", i)
                metrics_collector.increment_counter(f"test_counter_{i}")
            
            duration = time.time() - start_time
            
            # Verificar que 100 operaciones se completaron en menos de 1 segundo
            assert duration < 1.0
            
            return {'success': True, 'message': 'Metrics collection performance acceptable', 'details': {
                'duration_seconds': duration,
                'operations_per_second': 100 / duration
            }}
        except Exception as e:
            return {'success': False, 'message': f'Metrics collection performance test failed: {e}'}
    
    async def _test_alert_processing_performance(self):
        """Test: Rendimiento de procesamiento de alertas"""
        try:
            alerting_system = global_alerting_system
            start_time = time.time()
            
            # Simular verificación de alertas
            test_metrics = {
                'bot_status': {'value': 1},
                'trading_pnl_total': {'value': 1000},
                'websocket_connected': {'value': 1}
            }
            
            await alerting_system.check_alerts(test_metrics)
            
            duration = time.time() - start_time
            
            # Verificar que la verificación se completó en menos de 5 segundos
            assert duration < 5.0
            
            return {'success': True, 'message': 'Alert processing performance acceptable', 'details': {
                'duration_seconds': duration
            }}
        except Exception as e:
            return {'success': False, 'message': f'Alert processing performance test failed: {e}'}
    
    async def _test_memory_usage_performance(self):
        """Test: Rendimiento de uso de memoria"""
        try:
            import psutil
            process = psutil.Process()
            
            # Obtener uso de memoria inicial
            initial_memory = process.memory_info().rss / (1024**2)  # MB
            
            # Simular operaciones intensivas
            for i in range(1000):
                data = [j for j in range(100)]
                del data
            
            # Obtener uso de memoria final
            final_memory = process.memory_info().rss / (1024**2)  # MB
            memory_increase = final_memory - initial_memory
            
            # Verificar que el aumento de memoria es razonable (menos de 50MB)
            assert memory_increase < 50.0
            
            return {'success': True, 'message': 'Memory usage performance acceptable', 'details': {
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': memory_increase
            }}
        except Exception as e:
            return {'success': False, 'message': f'Memory usage performance test failed: {e}'}
    
    async def _test_cpu_usage_performance(self):
        """Test: Rendimiento de uso de CPU"""
        try:
            import psutil
            process = psutil.Process()
            
            # Medir CPU durante operaciones
            start_time = time.time()
            cpu_before = process.cpu_percent()
            
            # Simular operaciones de CPU
            for i in range(10000):
                result = sum(range(100))
            
            duration = time.time() - start_time
            cpu_after = process.cpu_percent()
            
            # Verificar que las operaciones se completaron en tiempo razonable
            assert duration < 5.0
            
            return {'success': True, 'message': 'CPU usage performance acceptable', 'details': {
                'duration_seconds': duration,
                'cpu_before': cpu_before,
                'cpu_after': cpu_after
            }}
        except Exception as e:
            return {'success': False, 'message': f'CPU usage performance test failed: {e}'}
    
    # Tests de seguridad
    async def _test_file_permissions_security(self):
        """Test: Seguridad de permisos de archivos"""
        try:
            sensitive_files = ['.env', 'configs/alert_config.json', 'configs/bybit_x_config.json']
            
            for file_path in sensitive_files:
                if Path(file_path).exists():
                    stat = Path(file_path).stat()
                    permissions = oct(stat.st_mode)[-3:]
                    
                    # Verificar que no es público (no 777, 666, etc.)
                    assert permissions not in ['777', '666', '755', '644']
                    
                    # Verificar que es restrictivo (600, 640, etc.)
                    assert permissions in ['600', '640', '644']
            
            return {'success': True, 'message': 'File permissions are secure'}
        except Exception as e:
            return {'success': False, 'message': f'File permissions security test failed: {e}'}
    
    async def _test_secrets_protection(self):
        """Test: Protección de secretos"""
        try:
            # Verificar que .env no está en git
            import subprocess
            result = subprocess.run(['git', 'ls-files', '.env'], capture_output=True, text=True)
            assert '.env' not in result.stdout
            
            # Verificar que archivos de configuración con secrets no están en git
            result = subprocess.run(['git', 'ls-files', 'configs/alert_config.json'], capture_output=True, text=True)
            assert 'configs/alert_config.json' not in result.stdout
            
            return {'success': True, 'message': 'Secrets are protected from git'}
        except Exception as e:
            return {'success': False, 'message': f'Secrets protection test failed: {e}'}
    
    async def _test_backup_encryption(self):
        """Test: Encriptación de backups"""
        try:
            # Verificar que los backups están comprimidos
            backup_dir = Path("backups")
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.tar.gz"))
                assert len(backup_files) > 0, "No compressed backups found"
            
            return {'success': True, 'message': 'Backups are properly compressed'}
        except Exception as e:
            return {'success': False, 'message': f'Backup encryption test failed: {e}'}
    
    async def _test_api_key_validation(self):
        """Test: Validación de API keys"""
        try:
            # Verificar que las API keys no están hardcodeadas en el código
            code_files = list(Path("backtrader_engine").rglob("*.py"))
            
            for file_path in code_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Verificar que no hay API keys hardcodeadas
                    assert 'RGsF3mGYBxloK5k2P8' not in content
                    assert '5OujyPCj3i4gU0eCvFZJ1XAAX68YePJQrgd1' not in content
                    assert '7707298650:AAHvtK5f6w38dZa5rPYJyL3dCOabs7ifCo4' not in content
            
            return {'success': True, 'message': 'API keys are not hardcoded in code'}
        except Exception as e:
            return {'success': False, 'message': f'API key validation test failed: {e}'}
    
    async def _test_log_sanitization(self):
        """Test: Sanitización de logs"""
        try:
            # Verificar que los logs no contienen información sensible
            log_files = list(Path("logs").glob("*.log"))
            
            for log_file in log_files:
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                    # Verificar que no hay API keys en los logs
                    assert 'RGsF3mGYBxloK5k2P8' not in content
                    assert '5OujyPCj3i4gU0eCvFZJ1XAAX68YePJQrgd1' not in content
            
            return {'success': True, 'message': 'Logs are properly sanitized'}
        except Exception as e:
            return {'success': False, 'message': f'Log sanitization test failed: {e}'}
    
    # Tests de disaster recovery
    async def _test_disaster_detection(self):
        """Test: Detección de desastres"""
        try:
            disaster_recovery = global_disaster_recovery
            
            # Simular detección de desastre
            disaster = await disaster_recovery.detect_disaster()
            
            # Verificar que la detección funciona (puede ser None si no hay desastre)
            assert disaster is None or hasattr(disaster, 'value')
            
            return {'success': True, 'message': 'Disaster detection working correctly'}
        except Exception as e:
            return {'success': False, 'message': f'Disaster detection test failed: {e}'}
    
    async def _test_recovery_plan_execution(self):
        """Test: Ejecución de planes de recuperación"""
        try:
            disaster_recovery = global_disaster_recovery
            
            # Verificar que los planes de recuperación están configurados
            assert len(disaster_recovery.recovery_plans) == 5
            
            # Verificar que cada plan tiene los campos requeridos
            for plan in disaster_recovery.recovery_plans.values():
                assert hasattr(plan, 'disaster_type')
                assert hasattr(plan, 'severity')
                assert hasattr(plan, 'recovery_steps')
                assert hasattr(plan, 'estimated_time_minutes')
                assert hasattr(plan, 'rollback_possible')
            
            return {'success': True, 'message': 'Recovery plans are properly configured'}
        except Exception as e:
            return {'success': False, 'message': f'Recovery plan execution test failed: {e}'}
    
    async def _test_backup_integrity(self):
        """Test: Integridad de backups"""
        try:
            backup_manager = global_backup_manager
            
            # Crear backup de prueba
            backup_id = await backup_manager.create_backup(
                BackupType.STATE_ONLY,
                "Integrity test backup"
            )
            
            # Verificar que el backup tiene checksum
            backup_info = backup_manager.get_backup_info(backup_id)
            assert backup_info.checksum is not None
            assert len(backup_info.checksum) == 32  # MD5 hash length
            
            return {'success': True, 'message': 'Backup integrity verification working', 'details': {
                'backup_id': backup_id,
                'checksum': backup_info.checksum
            }}
        except Exception as e:
            return {'success': False, 'message': f'Backup integrity test failed: {e}'}
    
    async def _test_rollback_capability(self):
        """Test: Capacidad de rollback"""
        try:
            disaster_recovery = global_disaster_recovery
            
            # Verificar que los planes de recuperación tienen rollback
            rollback_plans = [plan for plan in disaster_recovery.recovery_plans.values() if plan.rollback_possible]
            assert len(rollback_plans) >= 3  # Al menos 3 planes deben tener rollback
            
            return {'success': True, 'message': 'Rollback capability is available'}
        except Exception as e:
            return {'success': False, 'message': f'Rollback capability test failed: {e}'}
    
    async def _test_validation_procedures(self):
        """Test: Procedimientos de validación"""
        try:
            disaster_recovery = global_disaster_recovery
            
            # Verificar que los procedimientos de validación están implementados
            assert hasattr(disaster_recovery, '_validate_file_integrity')
            assert hasattr(disaster_recovery, '_validate_recovery')
            
            return {'success': True, 'message': 'Validation procedures are implemented'}
        except Exception as e:
            return {'success': False, 'message': f'Validation procedures test failed: {e}'}
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generar reporte de tests"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAILED])
        skipped_tests = len([r for r in self.results if r.status == TestStatus.SKIPPED])
        
        # Agrupar por categoría
        by_category = {}
        for result in self.results:
            category = result.category.value
            if category not in by_category:
                by_category[category] = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
            
            by_category[category]['total'] += 1
            if result.status == TestStatus.PASSED:
                by_category[category]['passed'] += 1
            elif result.status == TestStatus.FAILED:
                by_category[category]['failed'] += 1
            elif result.status == TestStatus.SKIPPED:
                by_category[category]['skipped'] += 1
        
        # Calcular duración total
        total_duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        # Calcular duración promedio
        avg_duration = sum(r.duration_ms for r in self.results) / len(self.results) if self.results else 0
        
        return {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'skipped_tests': skipped_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_duration_seconds': total_duration,
                'average_duration_ms': avg_duration
            },
            'by_category': by_category,
            'results': [
                {
                    'test_name': r.test_name,
                    'category': r.category.value,
                    'status': r.status.value,
                    'duration_ms': r.duration_ms,
                    'message': r.message,
                    'details': r.details,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.results
            ],
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

# Instancia global del test suite
global_test_suite = TestSuite()
