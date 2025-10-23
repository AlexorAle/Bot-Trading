#!/usr/bin/env python3
"""
Production Validation Script - Validación completa para producción
"""

import asyncio
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backtrader_engine.test_suite import global_test_suite
from backtrader_engine.backup_manager import global_backup_manager
from backtrader_engine.disaster_recovery import global_disaster_recovery
from backtrader_engine.metrics_collector import global_metrics_collector
from backtrader_engine.alerting_system import global_alerting_system

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_validation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ProductionValidator:
    """Validador de producción para el bot de trading"""
    
    def __init__(self):
        self.logger = logging.getLogger("ProductionValidator")
        self.validation_results = []
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """Ejecutar validación completa de producción"""
        self.logger.info("Starting production validation...")
        
        try:
            # 1. Validación de seguridad
            await self._validate_security()
            
            # 2. Validación de configuración
            await self._validate_configuration()
            
            # 3. Validación de dependencias
            await self._validate_dependencies()
            
            # 4. Validación de recursos del sistema
            await self._validate_system_resources()
            
            # 5. Validación de conectividad
            await self._validate_connectivity()
            
            # 6. Validación de backup y recovery
            await self._validate_backup_recovery()
            
            # 7. Validación de monitoreo
            await self._validate_monitoring()
            
            # 8. Validación de alertas
            await self._validate_alerting()
            
            # 9. Validación de performance
            await self._validate_performance()
            
            # 10. Validación de disaster recovery
            await self._validate_disaster_recovery()
            
            # Generar reporte final
            report = self._generate_validation_report()
            
            self.logger.info(f"Production validation completed: {report['summary']}")
            return report
            
        except Exception as e:
            self.logger.error(f"Production validation failed: {e}")
            raise
    
    async def _validate_security(self):
        """Validar aspectos de seguridad"""
        self.logger.info("Validating security...")
        
        # Verificar archivos de configuración
        config_files = ['.env', 'configs/alert_config.json', 'configs/bybit_x_config.json']
        
        for config_file in config_files:
            if Path(config_file).exists():
                # Verificar permisos
                stat = Path(config_file).stat()
                permissions = oct(stat.st_mode)[-3:]
                
                if permissions in ['777', '666', '755']:
                    self.critical_issues.append(f"CRITICAL: {config_file} has insecure permissions: {permissions}")
                elif permissions in ['600', '640']:
                    self.validation_results.append(f"✅ {config_file} has secure permissions: {permissions}")
                else:
                    self.warnings.append(f"⚠️ {config_file} has moderate permissions: {permissions}")
        
        # Verificar que secrets no están en git
        import subprocess
        try:
            result = subprocess.run(['git', 'ls-files', '.env'], capture_output=True, text=True)
            if '.env' in result.stdout:
                self.critical_issues.append("CRITICAL: .env file is tracked in git")
            else:
                self.validation_results.append("✅ .env file is not tracked in git")
        except Exception as e:
            self.warnings.append(f"⚠️ Could not verify git tracking: {e}")
        
        # Verificar API keys no hardcodeadas
        code_files = list(Path("backtrader_engine").rglob("*.py"))
        hardcoded_keys = []
        
        for file_path in code_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'RGsF3mGYBxloK5k2P8' in content:
                        hardcoded_keys.append(str(file_path))
            except Exception:
                continue
        
        if hardcoded_keys:
            self.critical_issues.append(f"CRITICAL: API keys hardcoded in files: {hardcoded_keys}")
        else:
            self.validation_results.append("✅ No hardcoded API keys found in code")
    
    async def _validate_configuration(self):
        """Validar configuración del sistema"""
        self.logger.info("Validating configuration...")
        
        # Verificar archivos de configuración críticos
        critical_configs = [
            'configs/alert_config.json',
            'configs/bybit_x_config.json',
            '.env'
        ]
        
        for config_file in critical_configs:
            if Path(config_file).exists():
                try:
                    with open(config_file, 'r') as f:
                        if config_file.endswith('.json'):
                            json.load(f)
                    self.validation_results.append(f"✅ {config_file} is valid JSON")
                except json.JSONDecodeError as e:
                    self.critical_issues.append(f"CRITICAL: {config_file} has invalid JSON: {e}")
                except Exception as e:
                    self.warnings.append(f"⚠️ Could not validate {config_file}: {e}")
            else:
                self.critical_issues.append(f"CRITICAL: {config_file} not found")
        
        # Verificar variables de entorno críticas
        import os
        required_env_vars = ['EXCHANGE', 'API_KEY', 'SECRET', 'SYMBOL']
        
        for env_var in required_env_vars:
            if os.getenv(env_var):
                self.validation_results.append(f"✅ Environment variable {env_var} is set")
            else:
                self.critical_issues.append(f"CRITICAL: Environment variable {env_var} not set")
    
    async def _validate_dependencies(self):
        """Validar dependencias del sistema"""
        self.logger.info("Validating dependencies...")
        
        # Verificar dependencias de Python
        required_packages = [
            'pandas', 'numpy', 'requests', 'psutil', 'asyncio',
            'streamlit', 'fastapi', 'pydantic', 'ccxt'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.validation_results.append(f"✅ Package {package} is available")
            except ImportError:
                self.critical_issues.append(f"CRITICAL: Package {package} not installed")
        
        # Verificar dependencias del sistema
        import subprocess
        
        system_deps = ['python3', 'git', 'cron']
        for dep in system_deps:
            try:
                subprocess.run([dep, '--version'], capture_output=True, check=True)
                self.validation_results.append(f"✅ System dependency {dep} is available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.warnings.append(f"⚠️ System dependency {dep} not found or not working")
    
    async def _validate_system_resources(self):
        """Validar recursos del sistema"""
        self.logger.info("Validating system resources...")
        
        import psutil
        
        # Verificar memoria
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        if memory_available_gb < 0.5:
            self.critical_issues.append(f"CRITICAL: Low memory available: {memory_available_gb:.1f} GB")
        elif memory_available_gb < 1.0:
            self.warnings.append(f"⚠️ Moderate memory available: {memory_available_gb:.1f} GB")
        else:
            self.validation_results.append(f"✅ Sufficient memory available: {memory_available_gb:.1f} GB")
        
        # Verificar espacio en disco
        disk = psutil.disk_usage('/')
        disk_free_gb = disk.free / (1024**3)
        disk_usage_percent = (disk.used / disk.total) * 100
        
        if disk_free_gb < 1.0:
            self.critical_issues.append(f"CRITICAL: Low disk space: {disk_free_gb:.1f} GB free")
        elif disk_free_gb < 5.0:
            self.warnings.append(f"⚠️ Moderate disk space: {disk_free_gb:.1f} GB free")
        else:
            self.validation_results.append(f"✅ Sufficient disk space: {disk_free_gb:.1f} GB free")
        
        if disk_usage_percent > 90:
            self.critical_issues.append(f"CRITICAL: High disk usage: {disk_usage_percent:.1f}%")
        elif disk_usage_percent > 80:
            self.warnings.append(f"⚠️ Moderate disk usage: {disk_usage_percent:.1f}%")
        else:
            self.validation_results.append(f"✅ Acceptable disk usage: {disk_usage_percent:.1f}%")
        
        # Verificar CPU
        cpu_count = psutil.cpu_count()
        if cpu_count < 2:
            self.warnings.append(f"⚠️ Low CPU cores: {cpu_count}")
        else:
            self.validation_results.append(f"✅ Adequate CPU cores: {cpu_count}")
    
    async def _validate_connectivity(self):
        """Validar conectividad de red"""
        self.logger.info("Validating connectivity...")
        
        # Verificar conectividad DNS
        import socket
        try:
            socket.gethostbyname('google.com')
            self.validation_results.append("✅ DNS resolution working")
        except Exception as e:
            self.critical_issues.append(f"CRITICAL: DNS resolution failed: {e}")
        
        # Verificar conectividad HTTP
        import requests
        try:
            response = requests.get('https://httpbin.org/status/200', timeout=10)
            if response.status_code == 200:
                self.validation_results.append("✅ HTTP connectivity working")
            else:
                self.warnings.append(f"⚠️ HTTP connectivity issues: {response.status_code}")
        except Exception as e:
            self.critical_issues.append(f"CRITICAL: HTTP connectivity failed: {e}")
        
        # Verificar conectividad a exchanges
        try:
            import ccxt
            exchange = ccxt.bybit()
            markets = exchange.load_markets()
            if markets:
                self.validation_results.append("✅ Exchange connectivity working")
            else:
                self.warnings.append("⚠️ Exchange connectivity issues")
        except Exception as e:
            self.warnings.append(f"⚠️ Exchange connectivity test failed: {e}")
    
    async def _validate_backup_recovery(self):
        """Validar sistema de backup y recovery"""
        self.logger.info("Validating backup and recovery...")
        
        # Verificar que el backup manager está funcionando
        try:
            backup_manager = global_backup_manager
            if backup_manager:
                self.validation_results.append("✅ Backup manager initialized")
            else:
                self.critical_issues.append("CRITICAL: Backup manager not initialized")
        except Exception as e:
            self.critical_issues.append(f"CRITICAL: Backup manager initialization failed: {e}")
        
        # Verificar directorio de backups
        backup_dir = Path("backups")
        if backup_dir.exists():
            self.validation_results.append("✅ Backup directory exists")
        else:
            self.warnings.append("⚠️ Backup directory does not exist")
        
        # Verificar disaster recovery
        try:
            disaster_recovery = global_disaster_recovery
            if disaster_recovery and len(disaster_recovery.recovery_plans) == 5:
                self.validation_results.append("✅ Disaster recovery plans configured")
            else:
                self.critical_issues.append("CRITICAL: Disaster recovery not properly configured")
        except Exception as e:
            self.critical_issues.append(f"CRITICAL: Disaster recovery initialization failed: {e}")
    
    async def _validate_monitoring(self):
        """Validar sistema de monitoreo"""
        self.logger.info("Validating monitoring...")
        
        # Verificar metrics collector
        try:
            metrics_collector = global_metrics_collector
            if metrics_collector:
                self.validation_results.append("✅ Metrics collector initialized")
            else:
                self.critical_issues.append("CRITICAL: Metrics collector not initialized")
        except Exception as e:
            self.critical_issues.append(f"CRITICAL: Metrics collector initialization failed: {e}")
        
        # Verificar health checker
        try:
            from backtrader_engine.health_checker import TradingBotHealthChecker
            health_checker = TradingBotHealthChecker()
            if health_checker:
                self.validation_results.append("✅ Health checker initialized")
            else:
                self.warnings.append("⚠️ Health checker not properly initialized")
        except Exception as e:
            self.warnings.append(f"⚠️ Health checker initialization failed: {e}")
    
    async def _validate_alerting(self):
        """Validar sistema de alertas"""
        self.logger.info("Validating alerting...")
        
        # Verificar alerting system
        try:
            alerting_system = global_alerting_system
            if alerting_system and len(alerting_system.rules) > 0:
                self.validation_results.append("✅ Alerting system configured")
            else:
                self.critical_issues.append("CRITICAL: Alerting system not properly configured")
        except Exception as e:
            self.critical_issues.append(f"CRITICAL: Alerting system initialization failed: {e}")
        
        # Verificar configuración de Telegram
        try:
            with open('configs/alert_config.json', 'r') as f:
                alert_config = json.load(f)
                if alert_config.get('telegram', {}).get('enabled'):
                    self.validation_results.append("✅ Telegram alerts configured")
                else:
                    self.warnings.append("⚠️ Telegram alerts not enabled")
        except Exception as e:
            self.warnings.append(f"⚠️ Could not validate Telegram configuration: {e}")
    
    async def _validate_performance(self):
        """Validar rendimiento del sistema"""
        self.logger.info("Validating performance...")
        
        import time
        
        # Test de rendimiento de backup
        try:
            start_time = time.time()
            backup_id = await global_backup_manager.create_backup(
                BackupType.STATE_ONLY,
                "Performance validation backup"
            )
            duration = time.time() - start_time
            
            if duration < 30:
                self.validation_results.append(f"✅ Backup performance acceptable: {duration:.1f}s")
            else:
                self.warnings.append(f"⚠️ Slow backup performance: {duration:.1f}s")
        except Exception as e:
            self.warnings.append(f"⚠️ Backup performance test failed: {e}")
        
        # Test de rendimiento de métricas
        try:
            start_time = time.time()
            for i in range(100):
                global_metrics_collector.set_gauge(f"test_metric_{i}", i)
            duration = time.time() - start_time
            
            if duration < 1.0:
                self.validation_results.append(f"✅ Metrics performance acceptable: {duration:.3f}s")
            else:
                self.warnings.append(f"⚠️ Slow metrics performance: {duration:.3f}s")
        except Exception as e:
            self.warnings.append(f"⚠️ Metrics performance test failed: {e}")
    
    async def _validate_disaster_recovery(self):
        """Validar disaster recovery"""
        self.logger.info("Validating disaster recovery...")
        
        # Verificar detección de desastres
        try:
            disaster = await global_disaster_recovery.detect_disaster()
            if disaster is None:
                self.validation_results.append("✅ No disasters detected")
            else:
                self.warnings.append(f"⚠️ Disaster detected: {disaster.value}")
        except Exception as e:
            self.warnings.append(f"⚠️ Disaster detection test failed: {e}")
        
        # Verificar planes de recuperación
        try:
            plans = global_disaster_recovery.recovery_plans
            if len(plans) == 5:
                self.validation_results.append("✅ All disaster recovery plans configured")
            else:
                self.critical_issues.append(f"CRITICAL: Missing disaster recovery plans: {len(plans)}/5")
        except Exception as e:
            self.critical_issues.append(f"CRITICAL: Disaster recovery plans validation failed: {e}")
    
    def _generate_validation_report(self) -> Dict[str, Any]:
        """Generar reporte de validación"""
        total_checks = len(self.validation_results) + len(self.warnings) + len(self.critical_issues)
        passed_checks = len(self.validation_results)
        warning_checks = len(self.warnings)
        critical_checks = len(self.critical_issues)
        
        # Determinar estado general
        if critical_checks > 0:
            overall_status = "CRITICAL"
        elif warning_checks > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"
        
        return {
            'overall_status': overall_status,
            'summary': {
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'warning_checks': warning_checks,
                'critical_checks': critical_checks,
                'pass_rate': (passed_checks / total_checks * 100) if total_checks > 0 else 0
            },
            'results': {
                'passed': self.validation_results,
                'warnings': self.warnings,
                'critical_issues': self.critical_issues
            },
            'recommendations': self.recommendations,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Trading Bot Production Validation")
    parser.add_argument("--output", help="Output file for validation report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        validator = ProductionValidator()
        report = await validator.run_full_validation()
        
        # Mostrar resumen
        print(f"\n{'='*60}")
        print(f"PRODUCTION VALIDATION REPORT")
        print(f"{'='*60}")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Total Checks: {report['summary']['total_checks']}")
        print(f"Passed: {report['summary']['passed_checks']}")
        print(f"Warnings: {report['summary']['warning_checks']}")
        print(f"Critical Issues: {report['summary']['critical_checks']}")
        print(f"Pass Rate: {report['summary']['pass_rate']:.1f}%")
        
        # Mostrar issues críticos
        if report['results']['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in report['results']['critical_issues']:
                print(f"  ❌ {issue}")
        
        # Mostrar warnings
        if report['results']['warnings']:
            print(f"\n⚠️ WARNINGS:")
            for warning in report['results']['warnings']:
                print(f"  ⚠️ {warning}")
        
        # Mostrar resultados exitosos
        if report['results']['passed']:
            print(f"\n✅ PASSED CHECKS:")
            for result in report['results']['passed']:
                print(f"  ✅ {result}")
        
        # Guardar reporte si se especifica archivo
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Report saved to: {args.output}")
        
        # Determinar código de salida
        if report['overall_status'] == "CRITICAL":
            sys.exit(1)
        elif report['overall_status'] == "WARNING":
            sys.exit(2)
        else:
            sys.exit(0)
    
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
