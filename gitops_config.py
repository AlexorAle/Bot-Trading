#!/usr/bin/env python3
"""
gitops_config.py - Configuración del GitOps_Watcher_Agent
=========================================================

Archivo de configuración centralizado para el GitOps_Watcher_Agent.
Contiene todas las configuraciones, constantes y parámetros del sistema.
"""

import os
from typing import List, Dict

# =============================================================================
# CONFIGURACIÓN PRINCIPAL
# =============================================================================

# Ramas principales
MAIN_BRANCH = "main"
MASTER_BRANCH = "master"  # Alternativa a main

# Ramas a monitorear
BRANCHES_TO_MONITOR = [
    "live_trading_monitor",
    "agent/ml_opt/",
    "develop",
    "feature/*",
    "hotfix/*"
]

# Canal de alertas
ALERTS_CHANNEL = "trading-gitops"

# Directorios
REPORTS_DIR = "reports"
LOGS_DIR = "logs"

# =============================================================================
# ARCHIVOS CRÍTICOS
# =============================================================================

# Archivos que requieren consulta obligatoria antes de merge
CRITICAL_FILES = [
    # Core del sistema
    "main.py",
    "config.py",
    "bot_controller.py",
    
    # Gestión de riesgo
    "risk_parity_allocator.py",
    "portfolio_engine.py",
    
    # Ejecución y trading
    "broker_handler.py",
    "execution/trader.py",
    
    # Estrategias principales
    "strategy/liquidation_hunter.py",
    "strategy/Liquidation_hunter_AI-Coded.py",
    "strategy/Liquidation_hunter_Self_Generating_Algo.py",
    
    # Configuraciones críticas
    "config_final.json",
    "config_eth.json",
    "config_test.json",
    
    # Backtrader engine
    "backtrader_engine/main.py",
    "backtrader_engine/portfolio_engine.py",
    "backtrader_engine/risk_parity_allocator.py"
]

# =============================================================================
# OPERACIONES CRÍTICAS
# =============================================================================

# Operaciones que requieren validación
CRITICAL_OPERATIONS = [
    "merge",
    "push", 
    "rebase",
    "force_push",
    "reset",
    "cherry_pick"
]

# =============================================================================
# CONFIGURACIÓN DE AUDITORÍA
# =============================================================================

# Número de commits a auditar por defecto
DEFAULT_COMMITS_TO_AUDIT = 5

# Número máximo de commits a auditar
MAX_COMMITS_TO_AUDIT = 50

# Intervalo mínimo entre auditorías (en segundos)
MIN_AUDIT_INTERVAL = 300  # 5 minutos

# =============================================================================
# CONFIGURACIÓN DE NOTIFICACIONES
# =============================================================================

# Tipos de alertas
ALERT_TYPES = {
    "ACTIVITY": "🚨 ALERTA GITOPS",
    "CRITICAL": "🚨 ALERTA CRÍTICA GITOPS 🚨",
    "BLOCKED": "🚨 OPERACIÓN BLOQUEADA",
    "INFO": "📊 INFORMACIÓN GITOPS"
}

# Patrones de confirmación válidos
CONFIRMATION_PATTERNS = {
    "merge": [
        "CONFIRMO MERGE CRÍTICO",
        "CONFIRMO MERGE",
        "YES MERGE"
    ],
    "push": [
        "CONFIRMO PUSH CRÍTICO",
        "CONFIRMO PUSH",
        "YES PUSH"
    ],
    "rebase": [
        "CONFIRMO REBASE",
        "YES REBASE"
    ],
    "reset": [
        "CONFIRMO RESET",
        "YES RESET"
    ],
    "force_push": [
        "CONFIRMO FORCE PUSH",
        "YES FORCE PUSH"
    ]
}

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================

# Niveles de logging
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

# Formato de logs
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Archivos de log
LOG_FILES = {
    "MAIN": "logs/gitops_watcher.log",
    "AUDIT": "logs/gitops_audit.log",
    "ALERTS": "logs/gitops_alerts.log",
    "ERRORS": "logs/gitops_errors.log"
}

# =============================================================================
# CONFIGURACIÓN DE REPORTES
# =============================================================================

# Formatos de reporte
REPORT_FORMATS = {
    "MARKDOWN": ".md",
    "TEXT": ".txt",
    "JSON": ".json"
}

# Plantillas de reporte
REPORT_TEMPLATES = {
    "DIFF": "diff_{branch}_{timestamp}.md",
    "AUDIT": "audit_{branch}_{timestamp}.md", 
    "SUMMARY": "audit_summary_{timestamp}.md",
    "ALERT": "alert_{timestamp}.txt"
}

# =============================================================================
# CONFIGURACIÓN DE INTEGRACIÓN MCP
# =============================================================================

# Herramientas MCP disponibles
MCP_TOOLS = {
    "GIT": "GIT_TOOL.execute_command",
    "SLACK": "SLACK_TOOL.post_message",
    "TELEGRAM": "TELEGRAM_TOOL.send_message",
    "EMAIL": "EMAIL_TOOL.send_email"
}

# Configuración de Slack
SLACK_CONFIG = {
    "CHANNEL": ALERTS_CHANNEL,
    "USERNAME": "GitOps-Watcher",
    "ICON_EMOJI": ":robot_face:",
    "WEBHOOK_URL": os.getenv("SLACK_WEBHOOK_URL", ""),
    "TOKEN": os.getenv("SLACK_TOKEN", "")
}

# Configuración de Telegram
TELEGRAM_CONFIG = {
    "CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
    "BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "PARSE_MODE": "Markdown"
}

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =============================================================================

# Patrones de autor en commits
AUTHOR_PATTERNS = {
    "AGENT": "[AGENTE:",
    "HUMAN": "[HUMANO:",
    "BOT": "[BOT:",
    "AUTO": "[AUTO:"
}

# Niveles de riesgo
RISK_LEVELS = {
    "LOW": "🟢 BAJO",
    "MEDIUM": "🟡 MEDIO", 
    "HIGH": "🔴 ALTO",
    "CRITICAL": "🚨 CRÍTICO"
}

# =============================================================================
# CONFIGURACIÓN DE EJECUCIÓN
# =============================================================================

# Modos de ejecución
EXECUTION_MODES = {
    "MANUAL": "manual",
    "SCHEDULED": "scheduled",
    "CONTINUOUS": "continuous",
    "TRIGGERED": "triggered"
}

# Configuración de scheduler
SCHEDULER_CONFIG = {
    "INTERVAL_MINUTES": 30,
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 60,  # segundos
    "TIMEOUT": 300  # segundos
}

# =============================================================================
# FUNCIONES DE CONFIGURACIÓN
# =============================================================================

def get_critical_files() -> List[str]:
    """Retorna la lista de archivos críticos."""
    return CRITICAL_FILES.copy()

def get_branches_to_monitor() -> List[str]:
    """Retorna la lista de ramas a monitorear."""
    return BRANCHES_TO_MONITOR.copy()

def get_confirmation_patterns(operation: str) -> List[str]:
    """Retorna los patrones de confirmación para una operación."""
    return CONFIRMATION_PATTERNS.get(operation, [])

def is_critical_file(file_path: str) -> bool:
    """Verifica si un archivo es crítico."""
    return file_path in CRITICAL_FILES

def is_critical_operation(operation: str) -> bool:
    """Verifica si una operación es crítica."""
    return operation in CRITICAL_OPERATIONS

def get_alert_type(alert_type: str) -> str:
    """Retorna el emoji y texto para un tipo de alerta."""
    return ALERT_TYPES.get(alert_type, "📊 ALERTA GITOPS")

def get_risk_level(level: str) -> str:
    """Retorna el emoji y texto para un nivel de riesgo."""
    return RISK_LEVELS.get(level, "🟡 MEDIO")

# =============================================================================
# VALIDACIÓN DE CONFIGURACIÓN
# =============================================================================

def validate_config() -> Dict[str, bool]:
    """
    Valida la configuración del sistema.
    
    Returns:
        Dict[str, bool]: Resultados de validación
    """
    validation_results = {
        "reports_dir_exists": os.path.exists(REPORTS_DIR),
        "logs_dir_exists": os.path.exists(LOGS_DIR),
        "critical_files_defined": len(CRITICAL_FILES) > 0,
        "branches_defined": len(BRANCHES_TO_MONITOR) > 0,
        "confirmation_patterns_defined": len(CONFIRMATION_PATTERNS) > 0
    }
    
    return validation_results

def ensure_directories():
    """Asegura que todos los directorios necesarios existen."""
    directories = [REPORTS_DIR, LOGS_DIR]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Directorio creado: {directory}")

# =============================================================================
# CONFIGURACIÓN DE ENTORNO
# =============================================================================

def load_environment_config():
    """Carga configuración desde variables de entorno."""
    global ALERTS_CHANNEL, REPORTS_DIR, LOGS_DIR
    
    ALERTS_CHANNEL = os.getenv("GITOPS_ALERTS_CHANNEL", ALERTS_CHANNEL)
    REPORTS_DIR = os.getenv("GITOPS_REPORTS_DIR", REPORTS_DIR)
    LOGS_DIR = os.getenv("GITOPS_LOGS_DIR", LOGS_DIR)

# Cargar configuración de entorno al importar
load_environment_config()

# =============================================================================
# INFORMACIÓN DE VERSIÓN
# =============================================================================

VERSION = "1.0.0"
BUILD_DATE = "2025-10-14"
AUTHOR = "GitOps_Watcher_Agent"
DESCRIPTION = "Agente Supervisor de GitOps para Bot de Trading"

def get_version_info() -> Dict[str, str]:
    """Retorna información de versión del sistema."""
    return {
        "version": VERSION,
        "build_date": BUILD_DATE,
        "author": AUTHOR,
        "description": DESCRIPTION
    }

if __name__ == "__main__":
    # Mostrar configuración actual
    print("=== CONFIGURACIÓN GITOPS_WATCHER_AGENT ===")
    print(f"Versión: {VERSION}")
    print(f"Fecha de Build: {BUILD_DATE}")
    print(f"Autor: {AUTHOR}")
    print()
    
    print("=== CONFIGURACIÓN PRINCIPAL ===")
    print(f"Rama Principal: {MAIN_BRANCH}")
    print(f"Ramas a Monitorear: {BRANCHES_TO_MONITOR}")
    print(f"Canal de Alertas: {ALERTS_CHANNEL}")
    print(f"Directorio de Reportes: {REPORTS_DIR}")
    print(f"Directorio de Logs: {LOGS_DIR}")
    print()
    
    print("=== ARCHIVOS CRÍTICOS ===")
    print(f"Total de archivos críticos: {len(CRITICAL_FILES)}")
    for file in CRITICAL_FILES[:5]:  # Mostrar solo los primeros 5
        print(f"  - {file}")
    if len(CRITICAL_FILES) > 5:
        print(f"  ... y {len(CRITICAL_FILES) - 5} más")
    print()
    
    print("=== VALIDACIÓN ===")
    validation = validate_config()
    for key, value in validation.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value}")
    
    print()
    print("=== ASEGURAR DIRECTORIOS ===")
    ensure_directories()
    print("✅ Directorios verificados/creados")
