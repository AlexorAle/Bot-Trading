# GitOps_Watcher_Agent - Documentación Completa

## 🎯 Objetivo

El **GitOps_Watcher_Agent** es un agente autónomo que audita y reporta las actividades de control de versiones (Git) en el repositorio del bot de trading. Su función principal es prevenir conflictos y **mantener la integridad de la rama `main` requiriendo siempre la consulta del usuario** para operaciones críticas.

## 🏗️ Arquitectura Implementada

### Arquitectura de Dos Capas

1. **Agente Principal (Meta-Agente / "El Constructor")**
   - **Ubicación:** Ventana de prompt del IDE (Ctrl+L)
   - **Función:** Interpreta instrucciones complejas, genera código, invoca el servidor MCP, y modifica la base de código
   - **Uso:** Para generar o modificar el GitOps_Watcher_Agent

2. **Agente Supervisor (GitOps_Watcher_Agent)**
   - **Ubicación:** Scripts Python independientes (`git_watcher.py`, `run_git_watcher.py`)
   - **Función:** Ejecuta tareas de auditoría de forma autónoma o programada
   - **Uso:** Auditoría continua y prevención de operaciones críticas

## 📁 Archivos Creados

### 1. `git_watcher.py` - Núcleo del Agente
**Funciones Core Implementadas:**

- **`compare_and_report_diff(base_branch, target_branch, output_file)`**
  - Compara dos ramas de Git
  - Genera reportes detallados en Markdown
  - Detecta archivos críticos modificados
  - Retorna ruta del archivo y contenido del diff

- **`audit_last_commits(branch, file_path=None, num_commits=5)`**
  - Audita los últimos commits de una rama
  - Identifica responsables (AGENTE vs HUMANO)
  - Busca prefijos en mensajes de commit
  - Retorna lista estructurada de commits

- **`send_audit_alert(report_data, channel)`**
  - Envía alertas críticas por Slack
  - Genera notificaciones estructuradas
  - Guarda alertas en archivos para auditoría

### 2. `run_git_watcher.py` - Punto de Entrada
**Políticas de Supervisión Configuradas:**

```python
MAIN_BRANCH = "main"
BRANCHES_TO_MONITOR = [
    "live_trading_monitor",
    "agent/ml_opt/",
    "develop",
    "feature/*"
]
ALERTS_CHANNEL = "trading-gitops"
```

**Funcionalidades:**
- Ejecución periódica de auditorías
- Monitoreo de múltiples ramas
- Generación de reportes consolidados
- Sistema de alertas automáticas

### 3. `gitops_blocking_logic.py` - Lógica de Bloqueo
**Integración con Agente Principal:**

- **Detección automática** de cambios en archivos críticos
- **Bloqueo preventivo** de operaciones peligrosas
- **Consulta obligatoria** al usuario
- **Validación de confirmaciones** del usuario

**Archivos Críticos Monitoreados:**
- `risk_parity_allocator.py`
- `broker_handler.py`
- `portfolio_engine.py`
- `main.py`
- `config.py`
- `execution/trader.py`
- `strategy/liquidation_hunter.py`

### 4. `reports/` - Directorio de Reportes
- Reportes de diferencias entre ramas
- Alertas y notificaciones
- Resúmenes de auditoría
- Logs de actividad

## 🚀 Uso del Sistema

### Ejecución Manual
```bash
# Auditoría completa
python run_git_watcher.py

# Auditoría de rama específica
python run_git_watcher.py --branch feature/new-strategy

# Modo verbose
python run_git_watcher.py --verbose
```

### Ejecución Programada (Cron)
```bash
# Ejecutar cada 30 minutos
*/30 * * * * cd /path/to/project && python run_git_watcher.py

# Ejecutar cada hora
0 * * * * cd /path/to/project && python run_git_watcher.py
```

### Integración con Cursor
El Agente Principal de Cursor ahora incluye lógica de bloqueo automático:

```python
# En el Agente Principal, antes de cualquier operación Git:
from gitops_blocking_logic import check_git_operation_safety

is_safe, message, critical_files = check_git_operation_safety(
    "merge", 
    target_branch="main", 
    source_branch="feature/risky-changes"
)

if not is_safe:
    # BLOQUEAR OPERACIÓN y mostrar mensaje al usuario
    print(message)
    # Esperar confirmación explícita del usuario
```

## 🔧 Configuración

### Variables de Entorno
```bash
# Canal de Slack para alertas
export SLACK_CHANNEL="trading-gitops"

# Token de Slack (si se implementa integración real)
export SLACK_TOKEN="xoxb-your-token"

# Directorio de reportes
export GITOPS_REPORTS_DIR="reports"
```

### Configuración de Slack
1. Crear canal `#trading-gitops` en Slack
2. Configurar webhook o bot token
3. Actualizar `ALERTS_CHANNEL` en `run_git_watcher.py`

## 📊 Tipos de Alertas

### 1. Alertas de Actividad Reciente
```
🚨 ALERTA GITOPS: Actividad reciente en la rama `feature/new-strategy`
📊 RESUMEN DE AUDITORÍA - 3 commits analizados
🤖 Commits de Agentes: 1
👤 Commits de Humanos: 2
```

### 2. Alertas Críticas
```
🚨 ALERTA CRÍTICA GITOPS 🚨
Se detectaron cambios en archivos críticos en la rama `feature/risky-changes`:
• risk_parity_allocator.py
• portfolio_engine.py
⚠️ ACCIÓN REQUERIDA: Estos cambios requieren consulta obligatoria antes de merge.
```

### 3. Alertas de Bloqueo
```
🚨 OPERACIÓN BLOQUEADA - ARCHIVOS CRÍTICOS DETECTADOS 🚨
Se encontraron cambios en archivos críticos en el merge:
main <- feature/risky-changes
⚠️ ACCIÓN REQUERIDA: Confirma explícitamente que deseas continuar.
Para proceder, responde con: "CONFIRMO MERGE CRÍTICO"
```

## 🛡️ Lógica de Bloqueo

### Operaciones Bloqueadas
- **Merge** a ramas críticas (`main`, `master`)
- **Push** a ramas críticas con archivos críticos modificados
- **Rebase** de ramas críticas
- **Reset** de ramas críticas
- **Force Push** a cualquier rama

### Confirmaciones Válidas
- `CONFIRMO MERGE CRÍTICO`
- `CONFIRMO PUSH CRÍTICO A MAIN`
- `CONFIRMO REBASE`
- `CONFIRMO RESET`
- `CONFIRMO FORCE PUSH`

## 📈 Reportes Generados

### 1. Reportes de Diferencias
- **Ubicación:** `reports/diff_branch_name_timestamp.md`
- **Contenido:** Diferencias detalladas entre ramas
- **Análisis:** Archivos críticos afectados
- **Recomendaciones:** Nivel de riesgo y acciones requeridas

### 2. Reportes de Auditoría
- **Ubicación:** `reports/audit_summary_timestamp.md`
- **Contenido:** Resumen de auditoría completa
- **Métricas:** Commits auditados, alertas enviadas
- **Estado:** Archivos críticos detectados

### 3. Alertas
- **Ubicación:** `reports/alert_timestamp.txt`
- **Contenido:** Alertas enviadas por Slack
- **Propósito:** Auditoría de notificaciones

## 🔄 Flujo de Trabajo

### 1. Auditoría Periódica
```
run_git_watcher.py ejecuta cada X minutos
    ↓
Obtiene lista de ramas disponibles
    ↓
Para cada rama monitoreada:
    - Audita commits recientes
    - Compara con rama main
    - Verifica archivos críticos
    - Envía alertas si es necesario
    ↓
Genera reporte final consolidado
```

### 2. Bloqueo de Operaciones
```
Usuario intenta operación Git en Cursor
    ↓
Agente Principal verifica seguridad
    ↓
Si archivos críticos afectados:
    - BLOQUEA operación
    - Muestra mensaje de alerta
    - Espera confirmación explícita
    ↓
Si confirmación válida:
    - Ejecuta operación
    - Registra en logs
```

## 🧪 Pruebas

### Prueba Básica
```bash
# Ejecutar auditoría de prueba
python run_git_watcher.py --branch main --commits 3

# Verificar reportes generados
ls -la reports/

# Revisar logs
tail -f logs/gitops_watcher.log
```

### Prueba de Bloqueo
```python
# En Python o Cursor
from gitops_blocking_logic import check_git_operation_safety

# Simular merge peligroso
is_safe, message, critical_files = check_git_operation_safety(
    "merge", 
    target_branch="main", 
    source_branch="feature/test"
)

print(f"Es seguro: {is_safe}")
print(f"Mensaje: {message}")
```

## 🚨 Solución de Problemas

### Error: "No se encontraron ramas para monitorear"
- Verificar que las ramas existen en el repositorio
- Ejecutar `git branch -r` para ver ramas remotas
- Actualizar `BRANCHES_TO_MONITOR` en `run_git_watcher.py`

### Error: "Error ejecutando comando Git"
- Verificar que Git está instalado y configurado
- Verificar permisos de escritura en el directorio
- Revisar logs para detalles del error

### Alertas no se envían
- Verificar configuración de Slack
- Revisar tokens y webhooks
- Comprobar conectividad de red

## 🔮 Próximos Pasos

### Fase 1: Integración Real con MCP
- Implementar llamadas reales a `SLACK_TOOL.post_message`
- Conectar con `GIT_TOOL.execute_command`
- Configurar tokens y webhooks

### Fase 2: Mejoras de Funcionalidad
- Dashboard web para visualizar reportes
- Notificaciones por email
- Integración con sistemas de CI/CD

### Fase 3: Automatización Avanzada
- Auto-merge para cambios seguros
- Rollback automático en caso de problemas
- Métricas y analytics de actividad

## ✅ Estado Actual

**IMPLEMENTACIÓN COMPLETADA:**
- ✅ `git_watcher.py` - Funciones core
- ✅ `run_git_watcher.py` - Punto de entrada
- ✅ `gitops_blocking_logic.py` - Lógica de bloqueo
- ✅ `reports/` - Directorio de reportes
- ✅ Documentación completa

**LISTO PARA USO:**
El GitOps_Watcher_Agent está completamente implementado y listo para ser utilizado. Puede ejecutarse inmediatamente con `python run_git_watcher.py` y se integrará automáticamente con el Agente Principal de Cursor para prevenir operaciones críticas.

---

*Documentación generada automáticamente por GitOps_Watcher_Agent*
