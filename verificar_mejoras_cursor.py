#!/usr/bin/env python3
"""
verificar_mejoras_cursor.py - Verificación de Mejoras de Cursor
==============================================================

Script para verificar que las mejoras implementadas en Cursor
están funcionando correctamente y midiendo las mejoras de rendimiento.
"""

import os
import time
import subprocess
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

class CursorImprovementsVerifier:
    """Verificador de mejoras de Cursor implementadas."""
    
    def __init__(self):
        """Inicializa el verificador."""
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment_json": {},
            "cursorrules_json": {},
            "mcp_json": {},
            "performance_tests": {},
            "recommendations": []
        }
    
    def verify_environment_json(self) -> Dict[str, any]:
        """Verifica la configuración de environment.json."""
        print("🔍 Verificando .cursor/environment.json...")
        
        env_path = ".cursor/environment.json"
        if not os.path.exists(env_path):
            return {"status": "error", "message": "Archivo no encontrado"}
        
        try:
            with open(env_path, 'r') as f:
                config = json.load(f)
            
            checks = {
                "agentCanUpdateSnapshot": config.get("agentCanUpdateSnapshot", False),
                "has_real_install_script": "pip install" in config.get("install", ""),
                "has_real_start_script": "python" in config.get("start", ""),
                "has_base_image": "baseImage" in config,
                "has_terminals": "terminals" in config and len(config["terminals"]) > 0,
                "has_env_vars": "env" in config and len(config["env"]) > 0,
                "has_persisted_dirs": "persistedDirectories" in config and len(config["persistedDirectories"]) > 0
            }
            
            score = sum(checks.values()) / len(checks) * 100
            
            return {
                "status": "success",
                "score": score,
                "checks": checks,
                "config": config
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def verify_cursorrules_json(self) -> Dict[str, any]:
        """Verifica la configuración de .cursorrules.json."""
        print("🔍 Verificando .cursorrules.json...")
        
        rules_path = ".cursorrules.json"
        if not os.path.exists(rules_path):
            return {"status": "error", "message": "Archivo no encontrado"}
        
        try:
            with open(rules_path, 'r') as f:
                rules = json.load(f)
            
            checks = {
                "has_description": "description" in rules,
                "has_rules": "rules" in rules and len(rules["rules"]) > 0,
                "has_edit_handling": any("Edit Handling" in rule.get("category", "") for rule in rules["rules"]),
                "has_performance": any("Performance" in rule.get("category", "") for rule in rules["rules"]),
                "has_constraints": any("Constraints" in rule.get("category", "") for rule in rules["rules"]),
                "has_trading_specific": any("Trading Bot" in rule.get("category", "") for rule in rules["rules"]),
                "has_error_prevention": any("Error Prevention" in rule.get("category", "") for rule in rules["rules"])
            }
            
            score = sum(checks.values()) / len(checks) * 100
            
            return {
                "status": "success", 
                "score": score,
                "checks": checks,
                "rules_count": len(rules["rules"])
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def verify_mcp_json(self) -> Dict[str, any]:
        """Verifica la configuración de mcp.json."""
        print("🔍 Verificando mcp.json...")
        
        mcp_path = "mcp.json"
        if not os.path.exists(mcp_path):
            return {"status": "error", "message": "Archivo no encontrado"}
        
        try:
            with open(mcp_path, 'r') as f:
                mcp = json.load(f)
            
            checks = {
                "has_mcp_servers": "mcpServers" in mcp,
                "has_filesystem": "filesystem" in mcp.get("mcpServers", {}),
                "has_github": "github" in mcp.get("mcpServers", {}),
                "has_sqlite": "sqlite" in mcp.get("mcpServers", {}),
                "has_global_settings": "globalSettings" in mcp,
                "has_caching": mcp.get("globalSettings", {}).get("enableCaching", False)
            }
            
            score = sum(checks.values()) / len(checks) * 100
            
            return {
                "status": "success",
                "score": score, 
                "checks": checks,
                "servers_count": len(mcp.get("mcpServers", {}))
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_performance_improvements(self) -> Dict[str, any]:
        """Prueba las mejoras de rendimiento."""
        print("🚀 Probando mejoras de rendimiento...")
        
        tests = {}
        
        # Test 1: Tiempo de importación de dependencias
        start_time = time.time()
        try:
            import ccxt
            import pandas
            import backtrader
            import numpy
            import_time = time.time() - start_time
            tests["import_time"] = {"status": "success", "time": import_time}
        except Exception as e:
            tests["import_time"] = {"status": "error", "message": str(e)}
        
        # Test 2: Tiempo de ejecución de GitOps_Watcher_Agent
        start_time = time.time()
        try:
            result = subprocess.run(
                ["python", "run_git_watcher.py", "--branch", "main", "--commits", "1"],
                capture_output=True,
                text=True,
                timeout=30
            )
            gitops_time = time.time() - start_time
            tests["gitops_time"] = {
                "status": "success" if result.returncode == 0 else "error",
                "time": gitops_time,
                "returncode": result.returncode
            }
        except Exception as e:
            tests["gitops_time"] = {"status": "error", "message": str(e)}
        
        # Test 3: Verificar que los directorios persisten
        persisted_dirs = ["logs", "reports", "data", "models"]
        dir_tests = {}
        for dir_name in persisted_dirs:
            dir_tests[dir_name] = os.path.exists(dir_name)
        tests["persisted_directories"] = dir_tests
        
        return tests
    
    def generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en los resultados."""
        recommendations = []
        
        # Verificar environment.json
        env_result = self.results["environment_json"]
        if env_result.get("status") == "success":
            score = env_result.get("score", 0)
            if score < 80:
                recommendations.append("🔧 Mejorar configuración de environment.json - score actual: {:.1f}%".format(score))
            else:
                recommendations.append("✅ environment.json configurado correctamente")
        else:
            recommendations.append("❌ Corregir errores en environment.json")
        
        # Verificar cursorrules.json
        rules_result = self.results["cursorrules_json"]
        if rules_result.get("status") == "success":
            score = rules_result.get("score", 0)
            if score < 80:
                recommendations.append("🔧 Mejorar configuración de .cursorrules.json - score actual: {:.1f}%".format(score))
            else:
                recommendations.append("✅ .cursorrules.json configurado correctamente")
        else:
            recommendations.append("❌ Corregir errores en .cursorrules.json")
        
        # Verificar mcp.json
        mcp_result = self.results["mcp_json"]
        if mcp_result.get("status") == "success":
            score = mcp_result.get("score", 0)
            if score < 80:
                recommendations.append("🔧 Mejorar configuración de mcp.json - score actual: {:.1f}%".format(score))
            else:
                recommendations.append("✅ mcp.json configurado correctamente")
        else:
            recommendations.append("❌ Corregir errores en mcp.json")
        
        # Verificar rendimiento
        perf_tests = self.results["performance_tests"]
        if perf_tests.get("import_time", {}).get("status") == "success":
            import_time = perf_tests["import_time"]["time"]
            if import_time > 5:
                recommendations.append("⚠️ Tiempo de importación lento: {:.2f}s (objetivo: <5s)".format(import_time))
            else:
                recommendations.append("✅ Tiempo de importación óptimo: {:.2f}s".format(import_time))
        
        if perf_tests.get("gitops_time", {}).get("status") == "success":
            gitops_time = perf_tests["gitops_time"]["time"]
            if gitops_time > 10:
                recommendations.append("⚠️ GitOps_Watcher lento: {:.2f}s (objetivo: <10s)".format(gitops_time))
            else:
                recommendations.append("✅ GitOps_Watcher rápido: {:.2f}s".format(gitops_time))
        
        return recommendations
    
    def run_verification(self) -> Dict[str, any]:
        """Ejecuta la verificación completa."""
        print("=" * 60)
        print("🔍 VERIFICACIÓN DE MEJORAS DE CURSOR")
        print("=" * 60)
        
        # Verificar archivos de configuración
        self.results["environment_json"] = self.verify_environment_json()
        self.results["cursorrules_json"] = self.verify_cursorrules_json()
        self.results["mcp_json"] = self.verify_mcp_json()
        
        # Probar rendimiento
        self.results["performance_tests"] = self.test_performance_improvements()
        
        # Generar recomendaciones
        self.results["recommendations"] = self.generate_recommendations()
        
        return self.results
    
    def print_results(self):
        """Imprime los resultados de la verificación."""
        print("\n" + "=" * 60)
        print("📊 RESULTADOS DE VERIFICACIÓN")
        print("=" * 60)
        
        # Environment.json
        env_result = self.results["environment_json"]
        if env_result.get("status") == "success":
            score = env_result.get("score", 0)
            print(f"📁 environment.json: {score:.1f}% - {'✅' if score >= 80 else '⚠️'}")
        else:
            print(f"📁 environment.json: ❌ - {env_result.get('message', 'Error')}")
        
        # Cursorrules.json
        rules_result = self.results["cursorrules_json"]
        if rules_result.get("status") == "success":
            score = rules_result.get("score", 0)
            print(f"📋 .cursorrules.json: {score:.1f}% - {'✅' if score >= 80 else '⚠️'}")
        else:
            print(f"📋 .cursorrules.json: ❌ - {rules_result.get('message', 'Error')}")
        
        # MCP.json
        mcp_result = self.results["mcp_json"]
        if mcp_result.get("status") == "success":
            score = mcp_result.get("score", 0)
            print(f"🔗 mcp.json: {score:.1f}% - {'✅' if score >= 80 else '⚠️'}")
        else:
            print(f"🔗 mcp.json: ❌ - {mcp_result.get('message', 'Error')}")
        
        # Rendimiento
        perf_tests = self.results["performance_tests"]
        if perf_tests.get("import_time", {}).get("status") == "success":
            import_time = perf_tests["import_time"]["time"]
            print(f"⚡ Tiempo de importación: {import_time:.2f}s - {'✅' if import_time < 5 else '⚠️'}")
        
        if perf_tests.get("gitops_time", {}).get("status") == "success":
            gitops_time = perf_tests["gitops_time"]["time"]
            print(f"🤖 GitOps_Watcher: {gitops_time:.2f}s - {'✅' if gitops_time < 10 else '⚠️'}")
        
        # Recomendaciones
        print("\n" + "=" * 60)
        print("💡 RECOMENDACIONES")
        print("=" * 60)
        
        for recommendation in self.results["recommendations"]:
            print(f"  {recommendation}")
        
        # Resumen final
        print("\n" + "=" * 60)
        print("🏁 RESUMEN FINAL")
        print("=" * 60)
        
        total_score = 0
        count = 0
        
        for result in [env_result, rules_result, mcp_result]:
            if result.get("status") == "success":
                total_score += result.get("score", 0)
                count += 1
        
        if count > 0:
            average_score = total_score / count
            print(f"Puntuación promedio: {average_score:.1f}%")
            
            if average_score >= 90:
                print("🎉 ¡EXCELENTE! Todas las mejoras implementadas correctamente")
            elif average_score >= 80:
                print("✅ ¡BUENO! Mejoras implementadas con éxito")
            elif average_score >= 60:
                print("⚠️ REGULAR - Algunas mejoras necesitan ajustes")
            else:
                print("❌ NECESITA MEJORAS - Revisar configuración")
        else:
            print("❌ No se pudieron verificar las mejoras")

def main():
    """Función principal."""
    verifier = CursorImprovementsVerifier()
    results = verifier.run_verification()
    verifier.print_results()
    
    # Guardar resultados
    with open("cursor_improvements_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Reporte guardado en: cursor_improvements_report.json")

if __name__ == "__main__":
    main()

