#!/usr/bin/env python3
"""
Automated Testing Script - Script para ejecutar tests automatizados
"""

import asyncio
import sys
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backtrader_engine.test_suite import global_test_suite

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automated_tests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def run_comprehensive_tests():
    """Ejecutar tests comprehensivos"""
    logger.info("Starting comprehensive test suite...")
    
    try:
        # Ejecutar todos los tests
        report = await global_test_suite.run_all_tests()
        
        # Mostrar resumen
        summary = report['summary']
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE TEST SUITE REPORT")
        print(f"{'='*60}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Skipped: {summary['skipped_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration_seconds']:.1f}s")
        print(f"Average Duration: {summary['average_duration_ms']:.1f}ms")
        
        # Mostrar resultados por categoría
        print(f"\n📊 RESULTS BY CATEGORY:")
        for category, stats in report['by_category'].items():
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {category.upper()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Mostrar tests fallidos
        failed_tests = [r for r in report['results'] if r['status'] == 'failed']
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  ❌ {test['test_name']} ({test['category']}): {test['message']}")
        
        # Mostrar tests exitosos
        passed_tests = [r for r in report['results'] if r['status'] == 'passed']
        if passed_tests:
            print(f"\n✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"  ✅ {test['test_name']} ({test['category']}): {test['message']}")
        
        return report
        
    except Exception as e:
        logger.error(f"Test suite execution failed: {e}")
        raise

async def run_unit_tests():
    """Ejecutar solo tests unitarios"""
    logger.info("Running unit tests...")
    
    try:
        # Ejecutar tests unitarios
        await global_test_suite._run_unit_tests()
        
        # Generar reporte
        report = global_test_suite._generate_report()
        
        # Filtrar solo tests unitarios
        unit_results = [r for r in report['results'] if r['category'] == 'unit']
        
        print(f"\n{'='*40}")
        print(f"UNIT TESTS REPORT")
        print(f"{'='*40}")
        print(f"Total Unit Tests: {len(unit_results)}")
        
        passed = len([r for r in unit_results if r['status'] == 'passed'])
        failed = len([r for r in unit_results if r['status'] == 'failed'])
        
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / len(unit_results) * 100) if unit_results else 0:.1f}%")
        
        return report
        
    except Exception as e:
        logger.error(f"Unit tests execution failed: {e}")
        raise

async def run_integration_tests():
    """Ejecutar solo tests de integración"""
    logger.info("Running integration tests...")
    
    try:
        # Ejecutar tests de integración
        await global_test_suite._run_integration_tests()
        
        # Generar reporte
        report = global_test_suite._generate_report()
        
        # Filtrar solo tests de integración
        integration_results = [r for r in report['results'] if r['category'] == 'integration']
        
        print(f"\n{'='*40}")
        print(f"INTEGRATION TESTS REPORT")
        print(f"{'='*40}")
        print(f"Total Integration Tests: {len(integration_results)}")
        
        passed = len([r for r in integration_results if r['status'] == 'passed'])
        failed = len([r for r in integration_results if r['status'] == 'failed'])
        
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / len(integration_results) * 100) if integration_results else 0:.1f}%")
        
        return report
        
    except Exception as e:
        logger.error(f"Integration tests execution failed: {e}")
        raise

async def run_system_tests():
    """Ejecutar solo tests de sistema"""
    logger.info("Running system tests...")
    
    try:
        # Ejecutar tests de sistema
        await global_test_suite._run_system_tests()
        
        # Generar reporte
        report = global_test_suite._generate_report()
        
        # Filtrar solo tests de sistema
        system_results = [r for r in report['results'] if r['category'] == 'system']
        
        print(f"\n{'='*40}")
        print(f"SYSTEM TESTS REPORT")
        print(f"{'='*40}")
        print(f"Total System Tests: {len(system_results)}")
        
        passed = len([r for r in system_results if r['status'] == 'passed'])
        failed = len([r for r in system_results if r['status'] == 'failed'])
        
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / len(system_results) * 100) if system_results else 0:.1f}%")
        
        return report
        
    except Exception as e:
        logger.error(f"System tests execution failed: {e}")
        raise

async def run_performance_tests():
    """Ejecutar solo tests de rendimiento"""
    logger.info("Running performance tests...")
    
    try:
        # Ejecutar tests de rendimiento
        await global_test_suite._run_performance_tests()
        
        # Generar reporte
        report = global_test_suite._generate_report()
        
        # Filtrar solo tests de rendimiento
        performance_results = [r for r in report['results'] if r['category'] == 'performance']
        
        print(f"\n{'='*40}")
        print(f"PERFORMANCE TESTS REPORT")
        print(f"{'='*40}")
        print(f"Total Performance Tests: {len(performance_results)}")
        
        passed = len([r for r in performance_results if r['status'] == 'passed'])
        failed = len([r for r in performance_results if r['status'] == 'failed'])
        
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / len(performance_results) * 100) if performance_results else 0:.1f}%")
        
        return report
        
    except Exception as e:
        logger.error(f"Performance tests execution failed: {e}")
        raise

async def run_security_tests():
    """Ejecutar solo tests de seguridad"""
    logger.info("Running security tests...")
    
    try:
        # Ejecutar tests de seguridad
        await global_test_suite._run_security_tests()
        
        # Generar reporte
        report = global_test_suite._generate_report()
        
        # Filtrar solo tests de seguridad
        security_results = [r for r in report['results'] if r['category'] == 'security']
        
        print(f"\n{'='*40}")
        print(f"SECURITY TESTS REPORT")
        print(f"{'='*40}")
        print(f"Total Security Tests: {len(security_results)}")
        
        passed = len([r for r in security_results if r['status'] == 'passed'])
        failed = len([r for r in security_results if r['status'] == 'failed'])
        
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / len(security_results) * 100) if security_results else 0:.1f}%")
        
        return report
        
    except Exception as e:
        logger.error(f"Security tests execution failed: {e}")
        raise

async def run_disaster_recovery_tests():
    """Ejecutar solo tests de disaster recovery"""
    logger.info("Running disaster recovery tests...")
    
    try:
        # Ejecutar tests de disaster recovery
        await global_test_suite._run_disaster_recovery_tests()
        
        # Generar reporte
        report = global_test_suite._generate_report()
        
        # Filtrar solo tests de disaster recovery
        dr_results = [r for r in report['results'] if r['category'] == 'disaster_recovery']
        
        print(f"\n{'='*40}")
        print(f"DISASTER RECOVERY TESTS REPORT")
        print(f"{'='*40}")
        print(f"Total Disaster Recovery Tests: {len(dr_results)}")
        
        passed = len([r for r in dr_results if r['status'] == 'passed'])
        failed = len([r for r in dr_results if r['status'] == 'failed'])
        
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / len(dr_results) * 100) if dr_results else 0:.1f}%")
        
        return report
        
    except Exception as e:
        logger.error(f"Disaster recovery tests execution failed: {e}")
        raise

async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Trading Bot Automated Testing")
    parser.add_argument("test_type", choices=[
        "all", "unit", "integration", "system", "performance", "security", "disaster-recovery"
    ], help="Type of tests to run")
    parser.add_argument("--output", help="Output file for test report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        if args.test_type == "all":
            report = await run_comprehensive_tests()
        elif args.test_type == "unit":
            report = await run_unit_tests()
        elif args.test_type == "integration":
            report = await run_integration_tests()
        elif args.test_type == "system":
            report = await run_system_tests()
        elif args.test_type == "performance":
            report = await run_performance_tests()
        elif args.test_type == "security":
            report = await run_security_tests()
        elif args.test_type == "disaster-recovery":
            report = await run_disaster_recovery_tests()
        
        # Guardar reporte si se especifica archivo
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Test report saved to: {args.output}")
        
        # Determinar código de salida
        if report['summary']['failed_tests'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except KeyboardInterrupt:
        logger.info("Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
