#!/usr/bin/env python3
"""
run_git_watcher.py - Punto de Entrada del GitOps_Watcher_Agent
==============================================================

Script principal para la ejecución periódica del Agente Supervisor de GitOps.
Define las políticas de supervisión y ejecuta las auditorías programadas.

Uso:
    python run_git_watcher.py

Este script debe ejecutarse periódicamente (cron, scheduler, etc.) para mantener
la supervisión continua del repositorio.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict

# Importar las funciones del GitOps Watcher
from git_watcher import GitOpsWatcher, compare_and_report_diff, audit_last_commits, send_audit_alert

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gitops_watcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class GitOpsSupervisor:
    """
    Clase principal del Supervisor de GitOps.
    Coordina las políticas de supervisión y ejecuta las auditorías.
    """
    
    def __init__(self):
        """Inicializa el supervisor con las políticas de supervisión."""
        
        # --- Políticas de Supervisión ---
        self.MAIN_BRANCH = "main"
        self.BRANCHES_TO_MONITOR = [
            "live_trading_monitor",
            "agent/ml_opt/",
            "develop",
            "feature/*"
        ]
        
        self.ALERTS_CHANNEL = "trading-gitops"
        self.REPORTS_DIR = "reports"
        
        # Configuración de auditoría
        self.COMMITS_TO_AUDIT = 5
        self.CRITICAL_FILES = [
            "risk_parity_allocator.py",
            "broker_handler.py", 
            "portfolio_engine.py",
            "main.py",
            "config.py",
            "execution/trader.py"
        ]
        
        # Inicializar el watcher
        self.watcher = GitOpsWatcher(self.REPORTS_DIR)
        
        logger.info("GitOps Supervisor inicializado")
        logger.info(f"Ramas a monitorear: {self.BRANCHES_TO_MONITOR}")
        logger.info(f"Canal de alertas: {self.ALERTS_CHANNEL}")
    
    def ensure_logs_dir(self):
        """Asegura que el directorio de logs existe."""
        if not os.path.exists("logs"):
            os.makedirs("logs")
            logger.info("Directorio de logs creado")
    
    def get_available_branches(self) -> List[str]:
        """
        Obtiene la lista de ramas disponibles en el repositorio.
        
        Returns:
            List[str]: Lista de ramas disponibles
        """
        try:
            success, output = self.watcher.execute_git_command("git branch -r")
            if not success:
                logger.error("Error obteniendo ramas remotas")
                return []
            
            branches = []
            for line in output.strip().split('\n'):
                if 'origin/' in line and not 'HEAD' in line:
                    branch_name = line.strip().replace('origin/', '')
                    branches.append(branch_name)
            
            return branches
            
        except Exception as e:
            logger.error(f"Error obteniendo ramas: {e}")
            return []
    
    def filter_existing_branches(self, branches_to_check: List[str]) -> List[str]:
        """
        Filtra las ramas que realmente existen en el repositorio.
        
        Args:
            branches_to_check: Lista de ramas a verificar
            
        Returns:
            List[str]: Lista de ramas que existen
        """
        available_branches = self.get_available_branches()
        existing_branches = []
        
        for branch in branches_to_check:
            # Verificar ramas exactas
            if branch in available_branches:
                existing_branches.append(branch)
            # Verificar patrones (para feature/*, etc.)
            elif '*' in branch:
                pattern = branch.replace('*', '')
                matching_branches = [b for b in available_branches if pattern in b]
                existing_branches.extend(matching_branches)
        
        return list(set(existing_branches))  # Eliminar duplicados
    
    def execute_branch_audit(self, target_branch: str) -> Dict[str, any]:
        """
        Ejecuta una auditoría completa de una rama específica.
        
        Args:
            target_branch: Rama a auditar
            
        Returns:
            Dict[str, any]: Resultados de la auditoría
        """
        logger.info(f"🔍 Iniciando auditoría de rama: {target_branch}")
        
        audit_results = {
            'branch': target_branch,
            'timestamp': datetime.now().isoformat(),
            'commits_audited': [],
            'diff_report_path': '',
            'critical_files_changed': [],
            'alerts_sent': 0,
            'status': 'success'
        }
        
        try:
            # 1. Auditar commits recientes
            commits = audit_last_commits(target_branch, num_commits=self.COMMITS_TO_AUDIT)
            audit_results['commits_audited'] = commits
            
            if commits:
                # Generar resumen de auditoría
                summary = self.watcher.generate_audit_summary(commits)
                logger.info(f"Resumen de auditoría para {target_branch}:\n{summary}")
                
                # Enviar alerta si hay actividad reciente
                alert_message = f"🚨 ALERTA GITOPS: Actividad reciente en la rama `{target_branch}`\n\n{summary}"
                if send_audit_alert(alert_message, self.ALERTS_CHANNEL):
                    audit_results['alerts_sent'] += 1
            
            # 2. Comparar con rama main
            report_path, diff_content = compare_and_report_diff(
                self.MAIN_BRANCH, 
                target_branch, 
                f"diff_{target_branch.replace('/', '_')}"
            )
            
            audit_results['diff_report_path'] = report_path
            
            # 3. Verificar archivos críticos
            if diff_content:
                critical_changed = self.watcher.check_critical_files_changed(diff_content)
                audit_results['critical_files_changed'] = critical_changed
                
                if critical_changed:
                    # Enviar alerta crítica
                    critical_alert = f"""
🚨 ALERTA CRÍTICA GITOPS 🚨

Se detectaron cambios en archivos críticos en la rama `{target_branch}`:

Archivos críticos modificados:
{chr(10).join([f"• {file}" for file in critical_changed])}

⚠️ ACCIÓN REQUERIDA: Estos cambios requieren consulta obligatoria antes de merge.

Reporte completo: {report_path}
"""
                    
                    if send_audit_alert(critical_alert, self.ALERTS_CHANNEL):
                        audit_results['alerts_sent'] += 1
                    
                    logger.warning(f"Archivos críticos modificados en {target_branch}: {critical_changed}")
                else:
                    # Notificar generación de reporte normal
                    normal_alert = f"📊 Informe de diferencias entre `{self.MAIN_BRANCH}` y `{target_branch}` generado: {report_path}"
                    if send_audit_alert(normal_alert, self.ALERTS_CHANNEL):
                        audit_results['alerts_sent'] += 1
            
            logger.info(f"✅ Auditoría completada para {target_branch}")
            
        except Exception as e:
            logger.error(f"Error en auditoría de {target_branch}: {e}")
            audit_results['status'] = 'error'
            audit_results['error'] = str(e)
        
        return audit_results
    
    def execute_full_audit(self) -> Dict[str, any]:
        """
        Ejecuta una auditoría completa de todas las ramas monitoreadas.
        
        Returns:
            Dict[str, any]: Resultados de la auditoría completa
        """
        logger.info("🚀 Iniciando auditoría completa de GitOps")
        
        # Asegurar directorios necesarios
        self.ensure_logs_dir()
        
        # Filtrar ramas existentes
        existing_branches = self.filter_existing_branches(self.BRANCHES_TO_MONITOR)
        
        if not existing_branches:
            logger.warning("No se encontraron ramas para monitorear")
            return {'status': 'no_branches', 'branches_found': 0}
        
        logger.info(f"Ramas encontradas para auditar: {existing_branches}")
        
        # Ejecutar auditorías
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'main_branch': self.MAIN_BRANCH,
            'branches_audited': existing_branches,
            'branch_results': [],
            'total_alerts_sent': 0,
            'critical_files_detected': False,
            'status': 'completed'
        }
        
        for branch in existing_branches:
            branch_result = self.execute_branch_audit(branch)
            audit_results['branch_results'].append(branch_result)
            audit_results['total_alerts_sent'] += branch_result.get('alerts_sent', 0)
            
            if branch_result.get('critical_files_changed'):
                audit_results['critical_files_detected'] = True
        
        # Generar reporte final
        self._generate_final_report(audit_results)
        
        logger.info(f"✅ Auditoría completa finalizada. Alertas enviadas: {audit_results['total_alerts_sent']}")
        
        return audit_results
    
    def _generate_final_report(self, audit_results: Dict[str, any]):
        """
        Genera un reporte final de la auditoría completa.
        
        Args:
            audit_results: Resultados de la auditoría
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"audit_summary_{timestamp}.md"
        report_path = os.path.join(self.REPORTS_DIR, report_filename)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"""# Reporte de Auditoría GitOps - {timestamp}

## Resumen Ejecutivo
- **Fecha:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Ramas Auditadas:** {len(audit_results['branches_audited'])}
- **Alertas Enviadas:** {audit_results['total_alerts_sent']}
- **Archivos Críticos Detectados:** {'Sí' if audit_results['critical_files_detected'] else 'No'}

## Ramas Monitoreadas
""")
                
                for branch in audit_results['branches_audited']:
                    f.write(f"- `{branch}`\n")
                
                f.write(f"""
## Resultados por Rama

""")
                
                for result in audit_results['branch_results']:
                    f.write(f"""### Rama: `{result['branch']}`
- **Estado:** {result['status']}
- **Commits Auditados:** {len(result['commits_audited'])}
- **Alertas Enviadas:** {result['alerts_sent']}
- **Archivos Críticos:** {len(result['critical_files_changed'])}
""")
                    
                    if result['critical_files_changed']:
                        f.write(f"- **Archivos Críticos Modificados:**\n")
                        for file in result['critical_files_changed']:
                            f.write(f"  - `{file}`\n")
                    
                    f.write(f"- **Reporte de Diff:** {result['diff_report_path']}\n\n")
                
                f.write(f"""
## Recomendaciones

""")
                
                if audit_results['critical_files_detected']:
                    f.write("""
⚠️ **ACCIÓN INMEDIATA REQUERIDA**
- Se detectaron cambios en archivos críticos
- Revisar todos los reportes de diff generados
- Consultar antes de proceder con cualquier merge
""")
                else:
                    f.write("""
✅ **ESTADO NORMAL**
- No se detectaron cambios en archivos críticos
- Continuar con el monitoreo regular
""")
                
                f.write(f"""

---
*Reporte generado automáticamente por GitOps_Watcher_Agent*
""")
            
            logger.info(f"Reporte final generado: {report_path}")
            
        except Exception as e:
            logger.error(f"Error generando reporte final: {e}")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description='GitOps Watcher Agent - Supervisor de GitOps')
    parser.add_argument('--branch', type=str, help='Auditar una rama específica')
    parser.add_argument('--commits', type=int, default=5, help='Número de commits a auditar')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verbose')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Inicializar supervisor
    supervisor = GitOpsSupervisor()
    
    try:
        if args.branch:
            # Auditar rama específica
            logger.info(f"Auditando rama específica: {args.branch}")
            result = supervisor.execute_branch_audit(args.branch)
            print(f"Resultado de auditoría: {result}")
        else:
            # Ejecutar auditoría completa
            result = supervisor.execute_full_audit()
            print(f"Auditoría completa finalizada: {result['status']}")
            print(f"Alertas enviadas: {result['total_alerts_sent']}")
            print(f"Archivos críticos detectados: {result['critical_files_detected']}")
    
    except KeyboardInterrupt:
        logger.info("Auditoría interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error en la ejecución: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
