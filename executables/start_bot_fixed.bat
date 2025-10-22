@echo off
chcp 65001 >nul
title Trading Bot - Inicio
color 07

REM Variables
set PROJECT_DIR=%~dp0..
set BOT_DIR=%PROJECT_DIR%\backtrader_engine
set LOG_FILE=%BOT_DIR%\logs\system_init.log
set PID_MANAGER=%PROJECT_DIR%\executables\bot_pid_manager.py

echo +---------------------------------------------+
echo ^|         TRADING BOT - INICIANDO            ^|
echo +---------------------------------------------+
echo.

echo [%date% %time%] === INICIANDO BOT === >> "%LOG_FILE%"

REM Verificar si el bot ya está ejecutándose
echo Verificando estado actual del bot...
python "%PID_MANAGER%" status | findstr "is_running.*true" >nul
if %errorlevel% == 0 (
    echo Bot ya está ejecutándose. ¿Deseas reiniciarlo?
    echo [S] Sí, reiniciar
    echo [N] No, salir
    set /p choice="Selecciona una opción (S/N): "
    if /i "%choice%"=="S" (
        echo Deteniendo bot actual...
        python "%PID_MANAGER%" force-stop
        timeout /t 3 /nobreak >nul
    ) else (
        echo Saliendo...
        pause
        exit /b 0
    )
)

REM Verificar Docker
echo Verificando Docker...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker: ✗ ERROR - Inicia Docker Desktop y reintenta
    pause
    exit /b 1
) else (
    echo Docker: ✓ OK
)

REM Verificar archivos necesarios
echo Verificando archivos necesarios...
if not exist "%BOT_DIR%" (
    echo Directorio Bot: ✗ ERROR
    pause
    exit /b 1
) else (
    echo Directorio Bot: ✓ OK
)

if not exist "%BOT_DIR%\configs\bybit_x_config.json" (
    echo Config Bybit: ✗ ERROR
    pause
    exit /b 1
) else (
    echo Config Bybit: ✓ OK
)

if not exist "%BOT_DIR%\configs\alert_config.json" (
    echo Config Alertas: ✗ ERROR
    pause
    exit /b 1
) else (
    echo Config Alertas: ✓ OK
)

REM Verificar servicios
echo Verificando servicios...
netstat -an | findstr "9090" >nul
if %errorlevel% neq 0 (
    docker-compose -f "%PROJECT_DIR%\docker-compose.yml" up -d prometheus >>"%LOG_FILE%" 2>&1
    timeout /t 3 /nobreak >nul
)

netstat -an | findstr "3000" >nul
if %errorlevel% neq 0 (
    docker-compose -f "%PROJECT_DIR%\docker-compose.yml" up -d grafana >>"%LOG_FILE%" 2>&1
    timeout /t 3 /nobreak >nul
)

netstat -an | findstr "9090" >nul
if %errorlevel% == 0 (
    echo Prometheus: ✓ OK
) else (
    echo Prometheus: ✗ ERROR
)

netstat -an | findstr "3000" >nul
if %errorlevel% == 0 (
    echo Grafana: ✓ OK
) else (
    echo Grafana: ✗ ERROR
)

REM Limpiar puerto 8080 si está ocupado
echo Verificando puerto 8080...
netstat -an | findstr "8080" >nul
if %errorlevel% == 0 (
    echo Puerto 8080 ocupado, limpiando...
    python "%PID_MANAGER%" force-stop >nul 2>&1
    timeout /t 3 /nobreak >nul
)

REM Enviar alerta inicial a Telegram
echo Enviando alerta inicial a Telegram...
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('🚀 Bot de Trading iniciando...')" 2>>"%LOG_FILE%"
if %errorlevel% == 0 (
    echo Telegram: ✓ OK
) else (
    echo Telegram: ✗ ERROR
)

REM Iniciar bot usando PID Manager
echo Iniciando bot con PID Manager...
cd /d "%PROJECT_DIR%"
python "%PID_MANAGER%" start
if %errorlevel% == 0 (
    echo Bot: ✓ OK - Iniciado correctamente
    
    REM Enviar confirmación a Telegram
    cd /d "%BOT_DIR%"
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('✅ Bot de Trading iniciado correctamente')" 2>>"%LOG_FILE%"
    
    echo.
    echo +---------------------------------------------+
    echo ^|         BOT INICIADO CORRECTAMENTE        ^|
    echo +---------------------------------------------+
    echo.
    echo URLs importantes:
    echo   Grafana: http://localhost:3000
    echo   Prometheus: http://localhost:9090
    echo   Métricas: http://localhost:8080/metrics
    echo.
    echo Para detener: executables\stop_bot_fixed.bat
    echo Logs: %LOG_FILE%
    
) else (
    echo Bot: ✗ ERROR - No se pudo iniciar
    
    REM Enviar error a Telegram
    cd /d "%BOT_DIR%"
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('❌ Error iniciando Bot de Trading')" 2>>"%LOG_FILE%"
    
    echo.
    echo +---------------------------------------------+
    echo ^|         ERROR INICIANDO BOT               ^|
    echo +---------------------------------------------+
    echo Revisa los logs en: %LOG_FILE%
)

echo.
pause
