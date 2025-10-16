#!/usr/bin/env python3
"""
GitOps_Watcher_Agent - Agente Supervisor de GitOps
==================================================

Este agente autónomo audita y reporta las actividades de control de versiones (Git)
en el repositorio del bot de trading. Previene conflictos y mantiene la integridad
de la rama main requiriendo consulta del usuario para operaciones críticas.

Funciones Core:
- compare_and_report_diff: Compara dos ramas y genera reportes
- audit_last_commits: Audita los últimos commits y identifica responsables
- send_audit_alert: Envía alertas críticas por Slack
"""

import os
import json
import datetime
from typing import List, Dict, Tuple, Optional
import subprocess
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitOpsWatcher:
    """
    Clase principal del Agente Supervisor de GitOps.
    Encapsula todas las operaciones de auditoría y notificación.
    """
    
    def __init__(self, reports_dir: str = "reports"):
        """
        Inicializa el GitOps Watcher.
        
        Args:
            reports_dir: Directorio donde se guardarán los reportes
        """
        self.reports_dir = reports_dir
        self.ensure_reports_dir()
        
        # Archivos críticos que requieren consulta obligatoria
        self.critical_files = [
            "risk_parity_allocator.py",
            "broker_handler.py", 
            "portfolio_engine.py",
            "main.py",
            "config.py"
        ]
        
        logger.info(f"GitOps Watcher inicializado. Directorio de reportes: {self.reports_dir}")
    
    def ensure_reports_dir(self):
        """Asegura que el directorio de reportes existe."""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            logger.info(f"Directorio de reportes creado: {self.reports_dir}")
    
    def execute_git_command(self, command: str) -> Tuple[bool, str]:
        """
        Ejecuta un comando de Git y retorna el resultado.
        Configurado para evitar problemas de pager.
        
        Args:
            command: Comando de Git a ejecutar
            
        Returns:
            Tuple[bool, str]: (éxito, output)
        """
        try:
            # Configurar variables de entorno para evitar pager
            env = os.environ.copy()
            env['GIT_PAGER'] = 'cat'
            env['PAGER'] = 'cat'
            
            # Agregar --no-pager a comandos Git si no está presente
            if command.startswith('git ') and '--no-pager' not in command:
                command = command.replace('git ', 'git --no-pager ', 1)
            
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                env=env,
                timeout=30  # Timeout de 30 segundos
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                logger.error(f"Error ejecutando comando Git: {command}")
                logger.error(f"Stderr: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ejecutando comando Git: {command}")
            return False, "Timeout - comando tardó más de 30 segundos"
        except Exception as e:
            logger.error(f"Excepción ejecutando comando Git: {e}")
            return False, str(e)
    
    def compare_and_report_diff(self, base_branch: str, target_branch: str, output_file: str) -> Tuple[str, str]:
        """
        Compara dos ramas de Git y genera un reporte detallado.
        
        Args:
            base_branch: Rama base para la comparación
            target_branch: Rama objetivo para la comparación
            output_file: Nombre del archivo de salida (sin extensión)
            
        Returns:
            Tuple[str, str]: (ruta_del_archivo, contenido_del_diff)
        """
        logger.info(f"Comparando ramas: {base_branch} vs {target_branch}")
        
        # Ejecutar git diff
        diff_command = f"git diff {base_branch}..{target_branch}"
        success, diff_content = self.execute_git_command(diff_command)
        
        if not success:
            logger.error(f"Error obteniendo diff entre {base_branch} y {target_branch}")
            return "", ""
        
        # Generar reporte en Markdown
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{output_file}_{timestamp}.md"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        # Crear contenido del reporte
        report_content = self._generate_diff_report(
            base_branch, target_branch, diff_content, timestamp
        )
        
        # Escribir archivo
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Reporte de diff generado: {report_path}")
        except Exception as e:
            logger.error(f"Error escribiendo reporte: {e}")
            return "", diff_content
        
        return report_path, diff_content
    
    def _generate_diff_report(self, base_branch: str, target_branch: str, 
                            diff_content: str, timestamp: str) -> str:
        """
        Genera el contenido del reporte de diff en formato Markdown.
        
        Args:
            base_branch: Rama base
            target_branch: Rama objetivo
            diff_content: Contenido del diff
            timestamp: Timestamp del reporte
            
        Returns:
            str: Contenido del reporte en Markdown
        """
        # Analizar archivos críticos afectados
        critical_files_affected = []
        if diff_content:
            for critical_file in self.critical_files:
                if critical_file in diff_content:
                    critical_files_affected.append(critical_file)
        
        # Generar reporte
        report = f"""# Reporte de Diferencias Git - {timestamp}

## Información General
- **Rama Base:** `{base_branch}`
- **Rama Objetivo:** `{target_branch}`
- **Fecha de Generación:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Generado por:** GitOps_Watcher_Agent

## Resumen de Cambios
"""
        
        if critical_files_affected:
            report += f"""
### ⚠️ ARCHIVOS CRÍTICOS AFECTADOS
Los siguientes archivos críticos han sido modificados:
"""
            for file in critical_files_affected:
                report += f"- `{file}`\n"
            report += f"""
**ACCIÓN REQUERIDA:** Estos cambios requieren consulta obligatoria antes de merge.
"""
        else:
            report += "No se detectaron cambios en archivos críticos.\n"
        
        report += f"""
## Diferencias Detalladas

```diff
{diff_content}
```

## Análisis de Riesgo
- **Nivel de Riesgo:** {'🔴 ALTO' if critical_files_affected else '🟢 BAJO'}
- **Archivos Críticos Afectados:** {len(critical_files_affected)}
- **Recomendación:** {'Consultar antes de proceder' if critical_files_affected else 'Proceder con precaución'}

---
*Reporte generado automáticamente por GitOps_Watcher_Agent*
"""
        
        return report
    
    def audit_last_commits(self, branch: str, file_path: Optional[str] = None, 
                          num_commits: int = 5) -> List[Dict[str, str]]:
        """
        Audita los últimos commits de una rama y identifica responsables.
        
        Args:
            branch: Rama a auditar
            file_path: Archivo específico a auditar (opcional)
            num_commits: Número de commits a revisar
            
        Returns:
            List[Dict[str, str]]: Lista de commits con información del autor
        """
        logger.info(f"Auditando últimos {num_commits} commits en rama: {branch}")
        
        # Construir comando git log
        log_command = f"git log --oneline -n {num_commits}"
        if file_path:
            log_command += f" -- {file_path}"
        
        # Obtener commits
        success, log_output = self.execute_git_command(log_command)
        if not success:
            logger.error(f"Error obteniendo log de la rama {branch}")
            return []
        
        # Procesar commits
        commits = []
        for line in log_output.strip().split('\n'):
            if not line:
                continue
                
            # Formato: hash mensaje
            parts = line.split(' ', 1)
            if len(parts) >= 2:
                commit_hash = parts[0]
                commit_msg = parts[1]
                
                # Determinar autor basado en el mensaje
                author = self._determine_author(commit_msg)
                
                commits.append({
                    'hash': commit_hash,
                    'commit_msg': commit_msg,
                    'author': author,
                    'branch': branch,
                    'file_path': file_path
                })
        
        logger.info(f"Encontrados {len(commits)} commits para auditar")
        return commits
    
    def _determine_author(self, commit_msg: str) -> str:
        """
        Determina el autor del commit basado en el mensaje.
        
        Args:
            commit_msg: Mensaje del commit
            
        Returns:
            str: Autor identificado
        """
        # Buscar prefijos de autor en el mensaje
        if '[AGENTE:' in commit_msg.upper():
            # Extraer nombre del agente
            start = commit_msg.upper().find('[AGENTE:')
            end = commit_msg.find(']', start)
            if end > start:
                agent_name = commit_msg[start+8:end].strip()
                return f"AGENTE: {agent_name}"
        
        elif '[HUMANO:' in commit_msg.upper():
            # Extraer nombre del humano
            start = commit_msg.upper().find('[HUMANO:')
            end = commit_msg.find(']', start)
            if end > start:
                human_name = commit_msg[start+8:end].strip()
                return f"HUMANO: {human_name}"
        
        # Si no hay prefijo, asumir que es humano
        return "HUMANO: Desconocido"
    
    def send_audit_alert(self, report_data: str, channel: str) -> bool:
        """
        Envía una alerta de auditoría por Slack.
        
        Args:
            report_data: Datos del reporte a enviar
            channel: Canal de Slack donde enviar la alerta
            
        Returns:
            bool: True si la alerta se envió correctamente
        """
        logger.info(f"Enviando alerta de auditoría al canal: {channel}")
        
        # Simular envío de alerta (en implementación real, usaría SLACK_TOOL.post_message)
        # Por ahora, guardamos la alerta en un archivo para simulación
        alert_filename = f"alert_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        alert_path = os.path.join(self.reports_dir, alert_filename)
        
        try:
            with open(alert_path, 'w', encoding='utf-8') as f:
                f.write(f"ALERTA GITOPS - {datetime.datetime.now()}\n")
                f.write(f"Canal: {channel}\n")
                f.write(f"Mensaje:\n{report_data}\n")
            
            logger.info(f"Alerta guardada en: {alert_path}")
            logger.info(f"Contenido de la alerta:\n{report_data}")
            
            # En implementación real, aquí se llamaría a SLACK_TOOL.post_message
            # return SLACK_TOOL.post_message(channel, report_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")
            return False
    
    def check_critical_files_changed(self, diff_content: str) -> List[str]:
        """
        Verifica si algún archivo crítico ha sido modificado en el diff.
        
        Args:
            diff_content: Contenido del diff a analizar
            
        Returns:
            List[str]: Lista de archivos críticos modificados
        """
        critical_changed = []
        
        for critical_file in self.critical_files:
            if critical_file in diff_content:
                critical_changed.append(critical_file)
        
        return critical_changed
    
    def generate_audit_summary(self, commits: List[Dict[str, str]]) -> str:
        """
        Genera un resumen de la auditoría de commits.
        
        Args:
            commits: Lista de commits auditados
            
        Returns:
            str: Resumen formateado
        """
        if not commits:
            return "No se encontraron commits para auditar."
        
        summary = f"📊 RESUMEN DE AUDITORÍA - {len(commits)} commits analizados\n\n"
        
        # Contar por tipo de autor
        agent_commits = [c for c in commits if c['author'].startswith('AGENTE:')]
        human_commits = [c for c in commits if c['author'].startswith('HUMANO:')]
        
        summary += f"🤖 Commits de Agentes: {len(agent_commits)}\n"
        summary += f"👤 Commits de Humanos: {len(human_commits)}\n\n"
        
        # Último commit
        if commits:
            last_commit = commits[0]
            summary += f"📝 Último commit:\n"
            summary += f"   Autor: {last_commit['author']}\n"
            summary += f"   Mensaje: {last_commit['commit_msg']}\n"
            summary += f"   Hash: {last_commit['hash']}\n"
        
        return summary


# Funciones de conveniencia para uso directo
def compare_and_report_diff(base_branch: str, target_branch: str, output_file: str) -> Tuple[str, str]:
    """
    Función de conveniencia para comparar ramas y generar reporte.
    
    Args:
        base_branch: Rama base
        target_branch: Rama objetivo  
        output_file: Nombre del archivo de salida
        
    Returns:
        Tuple[str, str]: (ruta_del_archivo, contenido_del_diff)
    """
    watcher = GitOpsWatcher()
    return watcher.compare_and_report_diff(base_branch, target_branch, output_file)


def audit_last_commits(branch: str, file_path: Optional[str] = None, 
                      num_commits: int = 5) -> List[Dict[str, str]]:
    """
    Función de conveniencia para auditar commits.
    
    Args:
        branch: Rama a auditar
        file_path: Archivo específico (opcional)
        num_commits: Número de commits a revisar
        
    Returns:
        List[Dict[str, str]]: Lista de commits auditados
    """
    watcher = GitOpsWatcher()
    return watcher.audit_last_commits(branch, file_path, num_commits)


def send_audit_alert(report_data: str, channel: str) -> bool:
    """
    Función de conveniencia para enviar alertas.
    
    Args:
        report_data: Datos del reporte
        channel: Canal de destino
        
    Returns:
        bool: True si se envió correctamente
    """
    watcher = GitOpsWatcher()
    return watcher.send_audit_alert(report_data, channel)


if __name__ == "__main__":
    # Ejemplo de uso
    watcher = GitOpsWatcher()
    
    # Auditar commits recientes
    commits = watcher.audit_last_commits("main", num_commits=3)
    print("Commits auditados:")
    for commit in commits:
        print(f"  {commit['author']}: {commit['commit_msg']}")
    
    # Generar resumen
    summary = watcher.generate_audit_summary(commits)
    print(f"\nResumen:\n{summary}")
