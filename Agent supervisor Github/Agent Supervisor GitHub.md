📄 Manifiesto COMPLETO: Creación del Agente Supervisor de GitOps
Markdown

# [MANIFIESTO] Creación y Configuración del Agente Supervisor de GitOps

## OBJETIVO PRINCIPAL
Crear y activar un agente Python autónomo llamado `GitOps_Watcher_Agent` cuyo único rol es auditar y reportar las actividades de control de versiones (Git) en el repositorio del bot de trading. Este agente debe prevenir conflictos y **mantener la integridad de la rama `main` requiriendo siempre la consulta del usuario** para operaciones críticas.

## CONTEXTO Y DEPENDENCIAS (MCP TOOLING)
Este agente debe usar las siguientes herramientas del Servidor MCP Unificado ya conectado:
1.  **`GIT_TOOL` (Mandatorio):** Para acceder a funciones de `diff`, `log` y `status`.
2.  **`SLACK_TOOL` o `TELEGRAM_TOOL` (Mandatorio):** Para enviar notificaciones críticas y reportes de auditoría.
3.  **Ambiente:** El agente debe poder ejecutarse en el entorno local (Windows/Linux) o en el ambiente de CI/CD (Docker).
Distinción de Agentes
Su sistema ahora tendrá una Arquitectura de Agentes de Dos Capas:

1. Agente Principal (Meta-Agente / "El Constructor")
Donde Vive: La ventana de prompt del IDE (donde escribe Ctrl+L).

Función: Interpreta sus instrucciones complejas (como el Manifiesto), genera el código, invoca el servidor MCP, y modifica su base de código.

Uso: Lo usa para generar o modificar el GitOps_Watcher_Agent.

2. Agente Supervisor (GitOps_Watcher_Agent)
Donde Vive: Dentro de su código, como un script de Python (git_watcher.py y run_git_watcher.py).

Función: Ejecuta tareas de auditoría de forma autónoma o programada (fuera del IDE) o cuando es invocado por otros Agentes Principales/Humanos.

Uso: Su objetivo es ejecutar las funciones audit_last_commits o compare_and_report_diff y enviar alertas por Slack.

Al darle el Manifiesto a su Agente Principal, usted le está pidiendo que construya el Agente Supervisor y lo incorpore a la lógica de su bot de trading.
El Manifiesto se Entrega como una Tarea (Prompt)
El documento Markdown que le proporcioné (el "Manifiesto") debe entregarse a Cursor como una tarea única y detallada en una ventana de Agente de Cursor (Ctrl+L o Cmd+L en macOS).

Flujo Recomendado:
Copiar el Manifiesto: Copie el contenido completo del documento Markdown que generé anteriormente.

Abrir el Agente: Abra la ventana de diálogo del Agente (la nueva ventana de prompt del IDE).

Instrucción Inicial: Comience el prompt con una instrucción clara, luego pegue el manifiesto:

"Utiliza el siguiente Manifiesto para crear el nuevo Agente Supervisor de GitOps. Debes crear los archivos git_watcher.py y run_git_watcher.py e implementar las funciones de Git y Slack/Telegram usando las herramientas MCP que ya están conectadas. Confirma los cambios antes de grabarlos y explica cómo queda configurada la nueva arquitectura de supervisión."

El Agente Principal Actúa como "Constructor": El Agente de Cursor (su agente principal, el que está conversando conmigo) analizará el Manifiesto y lo interpretará como una serie de pasos de construcción y configuración de código (la "tarea").

Paso 1: Razonamiento: El agente decide que necesita invocar las funciones de su servidor MCP para simular las operaciones de Git y Slack/Telegram.

Paso 2: Generación de Código: El agente escribe el código Python (git_watcher.py, run_git_watcher.py) que utiliza las meta-funciones del MCP para llamar a las herramientas reales.

Paso 3: Modificación del Proyecto: El agente modificará su repositorio local al crear estos dos nuevos archivos.
---
## PASO 1: Creación del Agente Supervisor (`git_watcher.py`)

Crea un archivo Python llamado `git_watcher.py` con una clase o conjunto de funciones que encapsulen las siguientes capacidades:

### 1.1 Función Core: `compare_and_report_diff(base_branch, target_branch, output_file)`
- **Propósito:** Comparar dos ramas de Git.
- **Implementación:** Debe invocar la meta-función del MCP para **`GIT_TOOL.compare_branches(base_branch, target_branch)`**.
- **Output:** Escribir el resultado detallado del `diff` en un archivo Markdown dentro del directorio `reports/` (e.g., `reports/git_diff_report.md`).
- **Retorno:** Devolver la ruta del archivo generado y el contenido del *diff* para análisis interno.

### 1.2 Función Core: `audit_last_commits(branch, file_path=None, num_commits=5)`
- **Propósito:** Identificar al responsable de los últimos cambios.
- **Implementación:** Debe invocar la meta-función del MCP para **`GIT_TOOL.fetch_log(branch, num_commits, file_path)`**.
    - Si se provee `file_path`, solo debe auditar ese archivo.
- **Lógica de Auditoría:** Buscar el prefijo del autor en el mensaje del *commit* (`[AGENTE: Nombre]` o `[HUMANO: Nombre]`) y registrar el mensaje de *commit* completo.
- **Retorno:** Devolver una lista estructurada (JSON) con `[{'author': '...', 'commit_msg': '...', 'hash': '...'}]`.

### 1.3 Función de Alerta: `send_audit_alert(report_data, channel)`
- **Propósito:** Notificar al usuario sobre actividades de riesgo o nuevas modificaciones.
- **Implementación:** Debe invocar la meta-función del MCP para **`SLACK_TOOL.post_message(channel, message)`** o similar.
- **Mensaje:** El cuerpo del mensaje debe incluir un resumen claro del `report_data`, destacando si se encontraron *commits* de **agentes** o si la rama `main` fue modificada.
- **Uso:** Esta función debe ser llamada después de cada ejecución de auditoría.

---
## PASO 2: Creación del Script de Ejecución (Punto de Control)

Crea un script llamado `run_git_watcher.py` que sirva como punto de entrada para la ejecución periódica y defina las políticas de supervisión:

```python
# run_git_watcher.py
from git_watcher import compare_and_report_diff, audit_last_commits, send_audit_alert
import os

# --- Políticas de Supervisión ---
MAIN_BRANCH = "main"
BRANCHES_TO_MONITOR = ["live_trading_monitor", "agent/ml_opt/"]
ALERTS_CHANNEL = "trading-gitops"  # ID de Slack o chat de Telegram

if not os.path.exists("reports"):
    os.makedirs("reports")

# 1. Ejecutar Auditoría de Commits
for target_branch in BRANCHES_TO_MONITOR:
    # Obtener el log y buscar actividad reciente
    commit_log = audit_last_commits(target_branch, num_commits=3)

    # 2. Generar Alerta (si se encuentran commits recientes)
    if commit_log:
        message = (f"🚨 ALERTA GITOPS: Actividad reciente en la rama `{target_branch}`.\n"
                   f"Último commit por: {commit_log[0]['author']} - {commit_log[0]['commit_msg']}")
        send_audit_alert(message, ALERTS_CHANNEL)

    # 3. Ejecutar Comparación con Main
    report_path, diff_content = compare_and_report_diff(MAIN_BRANCH, target_branch, f"reports/diff_{target_branch}.md")
    
    # Notificar la generación del reporte
    send_audit_alert(f"Informe de diferencias entre `{MAIN_BRANCH}` y `{target_branch}` generado: {report_path}", ALERTS_CHANNEL)


print("✅ Auditoría de GitOps completada. Revise los reportes y alertas.")
PASO 3: Requerimiento de Consulta Obligatoria (Configuración de Bloqueo)
Este paso es crítico para asegurar la consulta del usuario antes de la fusión.

Instrucción para el Agente Principal:

Configura la lógica del Agente Principal de Cursor para que, ante cualquier prompt que implique modificar o fusionar ramas clave (main o live_trading_monitor), primero se auto-invoque al GitOps_Watcher_Agent para una validación:

Lógica de Bloqueo: El Agente Principal debe ejecutar un GIT_TOOL.compare_branches() internamente.

Condición de Freno: Si el diff muestra cambios en archivos clave como risk_parity_allocator.py, broker_handler.py, o portfolio_engine.py, el Agente Principal debe DETENER LA OPERACIÓN (bloqueo).

Acción de Consulta: En lugar de ejecutar el merge/push, el Agente debe enviar una ALERTA CRÍTICA por Slack/Telegram (usando send_audit_alert) y responder al usuario en el prompt de Cursor con: "Operación bloqueada. Se encontraron cambios en archivos críticos de riesgo. Confirma explícitamente que deseas continuar, o revisa el informe en reports/."

🚀 Finalización
Una vez que git_watcher.py y run_git_watcher.py estén creados y la lógica de bloqueo del PASO 3 esté integrada en el runtime del Agente Principal de Cursor, notifica al usuario que el GitOps_Watcher_Agent está activo. Indica que ahora pueden ejecutar la supervisión periódica con:


python run_git_watcher.py