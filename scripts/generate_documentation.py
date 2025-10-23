#!/usr/bin/env python3
"""
Script para generar documentación completa del sistema
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Agregar el directorio del proyecto al path
sys.path.append(str(Path(__file__).parent.parent))

from backtrader_engine.documentation_generator import global_documentation_generator
from backtrader_engine.compliance_manager import global_compliance_manager
from backtrader_engine.audit_trail import global_audit_trail
from backtrader_engine.regulatory_reporter import global_regulatory_reporter

async def generate_all_documentation():
    """Generar toda la documentación"""
    print("🚀 Generando documentación completa del sistema...")
    
    try:
        # Generar documentación técnica
        print("📚 Generando documentación técnica...")
        tech_docs = await global_documentation_generator.generate_all_documentation()
        
        # Generar reporte de compliance
        print("📋 Generando reporte de compliance...")
        compliance_report = await global_compliance_manager.generate_compliance_report()
        
        # Generar reporte de auditoría
        print("🔍 Generando reporte de auditoría...")
        audit_report = global_audit_trail.generate_audit_report()
        
        # Generar reportes regulatorios
        print("📊 Generando reportes regulatorios...")
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        # Reporte de trades
        trade_report = await global_regulatory_reporter.generate_trade_report(
            framework=global_regulatory_reporter.RegulatoryFramework.MIFID_II,
            start_time=start_time,
            end_time=end_time
        )
        
        # Reporte de transacciones
        transaction_report = await global_regulatory_reporter.generate_transaction_report(
            framework=global_regulatory_reporter.RegulatoryFramework.MIFID_II,
            start_time=start_time,
            end_time=end_time
        )
        
        # Reporte de posiciones
        position_report = await global_regulatory_reporter.generate_position_report(
            framework=global_regulatory_reporter.RegulatoryFramework.MIFID_II,
            as_of_date=end_time
        )
        
        # Reporte de riesgo
        risk_report = await global_regulatory_reporter.generate_risk_report(
            framework=global_regulatory_reporter.RegulatoryFramework.BASEL_III,
            start_time=start_time,
            end_time=end_time
        )
        
        # Reporte de compliance
        compliance_regulatory_report = await global_regulatory_reporter.generate_compliance_report(
            framework=global_regulatory_reporter.RegulatoryFramework.SOX,
            start_time=start_time,
            end_time=end_time
        )
        
        # Crear resumen de documentación generada
        summary = {
            "generated_at": datetime.now().isoformat(),
            "technical_documentation": tech_docs,
            "compliance_report": {
                "report_id": compliance_report.report_id,
                "overall_status": compliance_report.overall_status.value,
                "compliance_score": compliance_report.compliance_score,
                "total_rules": compliance_report.total_rules,
                "compliant_rules": compliance_report.compliant_rules
            },
            "audit_report": {
                "report_id": audit_report.get("report_id", "N/A"),
                "total_events": audit_report.get("summary", {}).get("total_events", 0),
                "critical_events": audit_report.get("summary", {}).get("critical_events", 0)
            },
            "regulatory_reports": {
                "trade_report": trade_report.report_id,
                "transaction_report": transaction_report.report_id,
                "position_report": position_report.report_id,
                "risk_report": risk_report.report_id,
                "compliance_report": compliance_regulatory_report.report_id
            }
        }
        
        # Guardar resumen
        with open("docs/documentation_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print("✅ Documentación generada exitosamente!")
        print(f"📁 Archivos generados en: docs/")
        print(f"📊 Resumen guardado en: docs/documentation_summary.json")
        
        return summary
        
    except Exception as e:
        print(f"❌ Error generando documentación: {e}")
        return None

async def generate_compliance_documentation():
    """Generar documentación de compliance"""
    print("📋 Generando documentación de compliance...")
    
    try:
        # Ejecutar verificaciones de compliance
        compliance_checks = await global_compliance_manager.run_compliance_check()
        
        # Generar reporte de compliance
        compliance_report = await global_compliance_manager.generate_compliance_report()
        
        # Generar documentación de compliance
        compliance_docs = await global_documentation_generator.generate_compliance_documentation()
        
        print("✅ Documentación de compliance generada!")
        return compliance_docs
        
    except Exception as e:
        print(f"❌ Error generando documentación de compliance: {e}")
        return None

async def generate_regulatory_reports():
    """Generar reportes regulatorios"""
    print("📊 Generando reportes regulatorios...")
    
    try:
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        reports = {}
        
        # Reporte de trades (MiFID II)
        reports["trade_report"] = await global_regulatory_reporter.generate_trade_report(
            framework=global_regulatory_reporter.RegulatoryFramework.MIFID_II,
            start_time=start_time,
            end_time=end_time
        )
        
        # Reporte de transacciones (MiFID II)
        reports["transaction_report"] = await global_regulatory_reporter.generate_transaction_report(
            framework=global_regulatory_reporter.RegulatoryFramework.MIFID_II,
            start_time=start_time,
            end_time=end_time
        )
        
        # Reporte de posiciones (MiFID II)
        reports["position_report"] = await global_regulatory_reporter.generate_position_report(
            framework=global_regulatory_reporter.RegulatoryFramework.MIFID_II,
            as_of_date=end_time
        )
        
        # Reporte de riesgo (Basel III)
        reports["risk_report"] = await global_regulatory_reporter.generate_risk_report(
            framework=global_regulatory_reporter.RegulatoryFramework.BASEL_III,
            start_time=start_time,
            end_time=end_time
        )
        
        # Reporte de compliance (SOX)
        reports["compliance_report"] = await global_regulatory_reporter.generate_compliance_report(
            framework=global_regulatory_reporter.RegulatoryFramework.SOX,
            start_time=start_time,
            end_time=end_time
        )
        
        print("✅ Reportes regulatorios generados!")
        return reports
        
    except Exception as e:
        print(f"❌ Error generando reportes regulatorios: {e}")
        return None

async def generate_audit_report():
    """Generar reporte de auditoría"""
    print("🔍 Generando reporte de auditoría...")
    
    try:
        # Generar reporte de auditoría
        audit_report = global_audit_trail.generate_audit_report()
        
        # Obtener estadísticas de auditoría
        audit_stats = global_audit_trail.get_audit_statistics()
        
        print("✅ Reporte de auditoría generado!")
        return {
            "audit_report": audit_report,
            "audit_stats": audit_stats
        }
        
    except Exception as e:
        print(f"❌ Error generando reporte de auditoría: {e}")
        return None

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Generar documentación del sistema")
    parser.add_argument("--type", choices=["all", "compliance", "regulatory", "audit"], 
                       default="all", help="Tipo de documentación a generar")
    parser.add_argument("--output", default="docs/", help="Directorio de salida")
    parser.add_argument("--format", choices=["json", "markdown", "html"], 
                       default="markdown", help="Formato de salida")
    parser.add_argument("--verbose", action="store_true", help="Modo verbose")
    
    args = parser.parse_args()
    
    print(f"🚀 Iniciando generación de documentación...")
    print(f"📁 Directorio de salida: {args.output}")
    print(f"📄 Formato: {args.format}")
    
    if args.verbose:
        print("🔍 Modo verbose activado")
    
    # Ejecutar según el tipo
    if args.type == "all":
        result = asyncio.run(generate_all_documentation())
    elif args.type == "compliance":
        result = asyncio.run(generate_compliance_documentation())
    elif args.type == "regulatory":
        result = asyncio.run(generate_regulatory_reports())
    elif args.type == "audit":
        result = asyncio.run(generate_audit_report())
    else:
        print(f"❌ Tipo de documentación no válido: {args.type}")
        return 1
    
    if result:
        print("✅ Documentación generada exitosamente!")
        return 0
    else:
        print("❌ Error generando documentación")
        return 1

if __name__ == "__main__":
    sys.exit(main())
