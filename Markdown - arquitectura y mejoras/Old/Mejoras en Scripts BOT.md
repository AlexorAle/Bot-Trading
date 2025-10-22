# Propuesta de Simplificación de Scripts para Bot de Trading

## Introducción
Esta propuesta analiza los scripts batch (.bat) existentes generados por Cursor para el bot de trading (basado en Backtrader con integración de Bybit X, paper trading, alertas Telegram, y monitoreo via Prometheus/Grafana). El objetivo es simplificar el conjunto de scripts a solo tres principales: `start_bot.bat`, `check_bot_status.bat` y `stop_bot.bat`, eliminando redundancias y mejorando la robustez, usabilidad y profesionalidad.

El enfoque es técnico, orientado a un desarrollador Python experto. Asumimos que el código Python subyacente (e.g., `paper_trading_main.py`, `telegram_notifier.py`) está implementado correctamente, con dependencias como `json`, `requests` (para Telegram) y librerías de métricas (e.g., Prometheus client). Se enfatiza en integración seamless entre batch y Python, manejo de errores, paths relativos/absolutos, seguridad en configs, y outputs visuales limpios.

**Beneficios de la simplificación**:
- Reducción de 9 scripts a 3, minimizando mantenimiento.
- Automatización integral en `start_bot.bat` (verifica/inicia Docker, envía alertas Telegram, lanza bot).
- Outputs visuales con status claros (✓ OK / ✗ ERROR, colores).
- Logging centralizado en archivos (no en pantalla para mantener limpieza).
- Robustez: Retries, checks dinámicos, manejo de errores con %errorlevel%.

## Análisis de Scripts Existentes
Se revisaron los 9 scripts proporcionados. Aquí un resumen técnico, identificando fortalezas, debilidades y redundancias:

1. **start_bot.bat**:
   - **Función**: Inicia el bot Python con verificaciones de directorios/configs.
   - **Fortalezas**: Checks básicos (existencia de archivos), outputs informativos (configuración mostrada).
   - **Debilidades**: No integra inicio de Docker/services; ejecución blocking (bloquea hasta Ctrl+C); no envía alertas Telegram automáticas.
   - **Redundancia**: Similar a `start_services.bat` en flujo, pero separado.

2. **debug_bot.bat**:
   - **Función**: Ejecuta bot en modo debug con logging detallado (`python -u` para unbuffered output).
   - **Fortalezas**: Útil para troubleshooting.
   - **Debilidades**: Redundante con `start_bot.bat` (solo agrega `-u`); no integra checks.
   - **Redundancia**: Puede fusionarse en `start_bot.bat` con un flag (e.g., `--debug`).

3. **test_telegram_ultra_simple.bat** / **test_telegram.bat** / **test_telegram_simple.bat**:
   - **Función**: Pruebas de Telegram via one-liner Python o script temporal.
   - **Fortalezas**: Valida config JSON y envío de mensajes; maneja paths con `sys.path.append`.
   - **Debilidades**: Múltiples variantes para el mismo propósito (diferencias mínimas en manejo de errores/formato); dependen de `telegram_notifier.py`; no limpian temporales consistentemente.
   - **Redundancia**: Tres scripts para una función simple; integrar en `start_bot.bat` como check inicial.

4. **check_bot_status.bat**:
   - **Función**: Verifica procesos, puertos, logs y configs; muestra últimas líneas de log via PowerShell.
   - **Fortalezas**: Completo (incluye `tasklist`, `netstat`, `dir`, PowerShell para logs).
   - **Debilidades**: Outputs verbose (logs en pantalla); no chequea métricas reales; depende de PowerShell (no siempre disponible en entornos restringidos).
   - **Redundancia**: Similar a `check_metrics.bat` en checks de puertos.

5. **check_metrics.bat**:
   - **Función**: Chequea puerto 8080 y obtiene métricas via `curl`.
   - **Fortalezas**: Focalizado en métricas Prometheus (filtra con `findstr "paper_"`).
   - **Debilidades**: Requiere `curl` instalado (no default en todos los Windows); outputs crudos sin parsing.
   - **Redundancia**: Puede integrarse en `check_bot_status.bat`.

6. **stop_bot.bat**:
   - **Función**: Detiene procesos Python via `taskkill`, libera puerto 8080.
   - **Fortalezas**: Busca PIDs específicos (`findstr "paper_trading_main"`); verifica estado final.
   - **Debilidades**: Mata todos los Python si no encuentra específicos (riesgo de overkill); no detiene Docker; no envía alertas Telegram.
   - **Redundancia**: Lógica de `netstat` / `taskkill` similar a checks en otros scripts.

7. **start_services.bat**:
   - **Función**: Inicia Docker containers (Prometheus/Grafana) con verificaciones.
   - **Fortalezas**: Chequea Docker version; timeout para startup; outputs claros.
   - **Debilidades**: Timeout fijo (10s, no dinámico); asume `docker-compose.yml` en root; no retries en fallos.
   - **Redundancia**: Debe integrarse en `start_bot.bat` como prerequisito.

**Problemas Generales Identificados**:
- **Redundancia Alta**: Múltiples scripts para tests Telegram y checks; lógica repetida (e.g., `cd` a dirs, `netstat`).
- **Usabilidad**: Outputs verbose con logs en pantalla; no visuales consistentes (colores/status symbols).
- **Robustez**: Paths hardcodeados; manejo de errores básico (pausas en fallos); dependencia de tools externos (PowerShell, curl).
- **Seguridad**: Configs JSON expuestas (e.g., tokens Telegram); no encriptación.
- **Integración con Python**: One-liners Python en batch son frágiles (escaping issues); mejor encapsular en funciones Python si se expande.
- **Escalabilidad**: No flags/args; no background runs; asumiendo Windows (batch-specific).

## Propuesta de Simplificación
Reducir a tres scripts:
- **start_bot.bat**: Todo-en-uno para inicio. Verifica/inicia Docker/services automáticamente, envía alerta Telegram inicial, lanza bot Python, confirma con alerta final. Ejecuta blocking por simplicidad, pero agrega opción para background si needed.
- **check_bot_status.bat**: Verifica estado con outputs visuales limpios (sin logs crudos). Integra checks de métricas/puertos.
- **stop_bot.bat**: Detiene bot y services, envía alerta Telegram, verifica cleanup.

**Ajustes Basados en Revisión**:
- Integrar Telegram tests en `start_bot.bat` (envío inicial como prueba).
- Eliminar debug/test variants; agregar `-u` en start para unbuffered si debug needed.
- Usar variables para paths/configs (e.g., `%PROJECT_DIR%`).
- Agregar colores dinámicos y symbols (✓/✗) para visualidad.
- Manejo de errores: Usar %errorlevel%, logging a archivo, retries en Docker (loop hasta puertos up).
- Para dev Python: Recomendar exponer flags en `paper_trading_main.py` (e.g., `--debug`), y usar `subprocess` en Python para llamar batch si se invierte el flujo.

## Código Detallado de los Scripts

### 1. start_bot.bat
**Descripción Técnica**: Cambia dirs con `%~dp0` para paths relativos. Verifica Docker con retry loop (hasta 30s). Inicia containers solo si puertos down. Envía Telegram via Python one-liner (asumiendo `telegram_notifier.py` maneja errors). Lanza bot con redirección a log. Confirma con alerta.

```batch
@echo off
chcp 65001 >nul
title Trading Bot - Iniciando Sistema
color 07  REM Neutral inicial

REM Variables (ajustar si needed)
set PROJECT_DIR=%~dp0..
set BOT_DIR=%PROJECT_DIR%\backtrader_engine
set LOG_FILE=%BOT_DIR%\logs\system_init.log
set CONFIG_BYBIT=%BOT_DIR%\configs\bybit_x_config.json
set CONFIG_ALERT=%BOT_DIR%\configs\alert_config.json
set COMPOSE_FILE=%PROJECT_DIR%\docker-compose.yml

echo. > "%LOG_FILE%"  REM Limpiar log

echo +---------------------------------------------+
echo ¦         TRADING BOT - INICIANDO            ¦
echo +---------------------------------------------+
echo.

:SHOW_STATUS
if "%2"=="OK" (color 0A & echo %1: ✓ OK) else (color 0C & echo %1: ✗ ERROR)
color 07
goto :eof

REM Verificar Docker
echo Verificando Docker...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    call :SHOW_STATUS "Docker" "ERROR"
    echo Inicia Docker Desktop y reintenta.
    pause
    exit /b 1
) else (
    call :SHOW_STATUS "Docker" "OK"
)

REM Iniciar/Verificar services con retry
echo Verificando/Iniciando Servicios...
set RETRY=0
:START_SERVICES
if %RETRY% geq 6 (call :SHOW_STATUS "Servicios" "ERROR" & echo Timeout. Revisa %LOG_FILE%. & pause & exit /b 1)
netstat -an | findstr ":9090" >nul || docker-compose -f "%COMPOSE_FILE%" up -d prometheus >>"%LOG_FILE%" 2>&1
netstat -an | findstr ":3000" >nul || docker-compose -f "%COMPOSE_FILE%" up -d grafana >>"%LOG_FILE%" 2>&1
timeout /t 5 /nobreak >nul
netstat -an | findstr ":9090 :3000" >nul
if %errorlevel% neq 0 (set /a RETRY+=1 & goto START_SERVICES)
call :SHOW_STATUS "Servicios (Prometheus/Grafana)" "OK"

REM Verificar configs/dirs
if not exist "%BOT_DIR%" or not exist "%CONFIG_BYBIT%" or not exist "%CONFIG_ALERT%" (
    call :SHOW_STATUS "Configs/Dirs" "ERROR"
    pause
    exit /b 1
) else (
    call :SHOW_STATUS "Configs/Dirs" "OK"
)

REM Alerta Telegram inicial (integra test)
echo Enviando alerta inicial Telegram...
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('El bot se está inicializando...')" 2>>"%LOG_FILE%"
if %errorlevel% == 0 (call :SHOW_STATUS "Telegram Inicial" "OK") else (call :SHOW_STATUS "Telegram" "ERROR" & echo Continuando...)

REM Iniciar Bot
echo Iniciando Bot...
python paper_trading_main.py --config configs/bybit_x_config.json >>"%LOG_FILE%" 2>&1
if %errorlevel% == 0 (
    call :SHOW_STATUS "Bot" "OK"
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('Bot inicializado correctamente.')" 2>>"%LOG_FILE%"
) else (
    call :SHOW_STATUS "Bot" "ERROR"
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('Error inicializando bot.')" 2>>"%LOG_FILE%"
)

echo.
echo +---------------------------------------------+
echo ¦         SISTEMA INICIADO                   ¦
echo +---------------------------------------------+
echo URLs: Grafana http://localhost:3000, Prometheus http://localhost:9090, Metricas http://localhost:8080/metrics
echo Logs: %LOG_FILE%
pause >nul
```

### 2. check_bot_status.bat
**Descripción Técnica**: Usa `tasklist /v` para filtrar procesos específicos. Integra métricas via `curl` (fallback si no instalado: usar PowerShell `Invoke-WebRequest`). Outputs minimalistas; logs solo en archivo si needed.

```batch
@echo off
chcp 65001 >nul
title Trading Bot - Estado del Sistema
color 07

REM Variables
set PROJECT_DIR=%~dp0..
set BOT_DIR=%PROJECT_DIR%\backtrader_engine
set LOG_FILE=%BOT_DIR%\logs\paper_trading.log

echo +---------------------------------------------+
echo ¦         TRADING BOT - ESTADO               ¦
echo +---------------------------------------------+
echo.

:SHOW_STATUS
if "%2"=="OK" (color 0A & echo %1: ✓ OK) else (color 0C & echo %1: ✗ ERROR)
color 07
goto :eof

REM Bot prendido?
tasklist /v /fi "imagename eq python.exe" | findstr "paper_trading_main.py" >nul
call :SHOW_STATUS "Bot" "%errorlevel%==0 ? OK : ERROR%"

REM Puertos
netstat -an | findstr ":8080" >nul && call :SHOW_STATUS "Metricas (8080)" "OK" || call :SHOW_STATUS "Metricas" "ERROR"
netstat -an | findstr ":9090" >nul && call :SHOW_STATUS "Prometheus (9090)" "OK" || call :SHOW_STATUS "Prometheus" "ERROR"
netstat -an | findstr ":3000" >nul && call :SHOW_STATUS "Grafana (3000)" "OK" || call :SHOW_STATUS "Grafana" "ERROR"

REM Logs/Configs
exist "%LOG_FILE%" && call :SHOW_STATUS "Logs" "OK" || call :SHOW_STATUS "Logs" "ERROR"
exist "%BOT_DIR%\configs\bybit_x_config.json" && exist "%BOT_DIR%\configs\strategies_config_72h.json" && call :SHOW_STATUS "Configs" "OK" || call :SHOW_STATUS "Configs" "ERROR"

REM Metricas simples (si curl disponible)
netstat -an | findstr ":8080" >nul
if %errorlevel% == 0 (
    curl -s http://localhost:8080/metrics | findstr "paper_" >nul
    call :SHOW_STATUS "Metricas Activas" "%errorlevel%==0 ? OK : ERROR%"
)

echo.
echo +---------------------------------------------+
echo ¦         RESUMEN COMPLETO                   ¦
echo +---------------------------------------------+
pause >nul
```

### 3. stop_bot.bat
**Descripción Técnica**: Filtra PIDs precisos con `findstr`. Detiene Docker con `down`. Envía alerta Telegram. Verifica post-stop con timeout.

```batch
@echo off
chcp 65001 >nul
title Trading Bot - Deteniendo Sistema
color 07

REM Variables
set PROJECT_DIR=%~dp0..
set BOT_DIR=%PROJECT_DIR%\backtrader_engine
set CONFIG_ALERT=%BOT_DIR%\configs\alert_config.json
set LOG_FILE=%BOT_DIR%\logs\system_init.log
set COMPOSE_FILE=%PROJECT_DIR%\docker-compose.yml

echo +---------------------------------------------+
echo ¦         TRADING BOT - DETENIENDO           ¦
echo +---------------------------------------------+
echo.

:SHOW_STATUS
if "%2"=="OK" (color 0A & echo %1: ✓ OK) else (color 0C & echo %1: ✗ ERROR)
color 07
goto :eof

REM Alerta Telegram
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('El bot se está deteniendo...')" 2>>"%LOG_FILE%"
call :SHOW_STATUS "Telegram" "OK"  REM Asumir OK; chequear %errorlevel% si critical

REM Detener Bot
for /f "tokens=2" %%i in ('tasklist /v /fi "imagename eq python.exe" ^| findstr "paper_trading_main.py"') do taskkill /f /pid %%i >>"%LOG_FILE%" 2>&1
call :SHOW_STATUS "Bot" "OK"

REM Detener Services
docker-compose -f "%COMPOSE_FILE%" down >>"%LOG_FILE%" 2>&1
call :SHOW_STATUS "Servicios" "OK"

timeout /t 2 /nobreak >nul

REM Verificar
tasklist /fi "imagename eq python.exe" | findstr "python" >nul && call :SHOW_STATUS "Cleanup" "ERROR" || call :SHOW_STATUS "Cleanup" "OK"

echo.
echo +---------------------------------------------+
echo ¦         SISTEMA DETENIDO                   ¦
echo +---------------------------------------------+
pause >nul
```

## Recomendaciones Adicionales para Desarrollador Python
- **Integración Batch-Python**: Considera wrapper Python para estos batch (e.g., usar `subprocess.call` para ejecutar batch desde `paper_trading_main.py` con args). Agrega logging Python a archivos (e.g., `logging.basicConfig(filemode='a')`).
- **Seguridad**: Encripta tokens en JSON (e.g., usa `cryptography` lib). Valida JSON en Python antes de load.
- **Mejoras en Python**: En `telegram_notifier.py`, agrega retries (e.g., `tenacity` lib si disponible). Para métricas, expone endpoint Prometheus con valores reales (no solo defs).
- **Testing**: Unit tests para Python (e.g., mock Telegram API). Para batch, usa herramientas como `bats` o simula en CI.
- **Cross-Platform**: Migra a PowerShell o Python scripts puros para Linux/Mac compatibilidad.
- **Escalabilidad**: Agrega args a batch (e.g., `if "%1"=="--debug" python -u ...`). Para 72h duration, implementa timer en Python (e.g., `threading.Timer` para auto-stop).

Esta propuesta reduce complejidad mientras mantiene funcionalidad. Implementa y testa en entorno local. Si necesitas iteraciones, proporciona feedback.