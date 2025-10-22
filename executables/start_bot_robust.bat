@echo off
chcp 65001 >nul
title Trading Bot - Inicio Robusto
color 07

REM Variables
set PROJECT_DIR=%~dp0..
set BOT_DIR=%PROJECT_DIR%\backtrader_engine
set LOG_FILE=%BOT_DIR%\logs\system_init.log
set PID_MANAGER=%PROJECT_DIR%\executables\bot_pid_manager.py

echo +---------------------------------------------+
echo ^|         TRADING BOT - INICIO ROBUSTO       ^|
echo +---------------------------------------------+
echo.

REM Función para logging
:LOG
echo [%date% %time%] %~1 >> "%LOG_FILE%"
echo %~1
goto :eof

REM Función para mostrar estado
:SHOW_STATUS
if "%2"=="OK" (
    color 0A
    echo %1: ✓ OK
) else (
    color 0C
    echo %1: ✗ ERROR
)
color 07
call :LOG "%1: %2"
goto :eof

call :LOG "=== INICIANDO BOT - INICIO ROBUSTO ==="

REM Verificar si el bot ya está ejecutándose
echo Verificando estado actual del bot...
python "%PID_MANAGER%" status >nul 2>&1
if %errorlevel% == 0 (
    echo Bot ya está ejecutándose. Verificando estado...
    python "%PID_MANAGER%" status | findstr "is_running.*true" >nul
    if %errorlevel% == 0 (
        call :SHOW_STATUS "Bot Status" "YA_EJECUTANDOSE"
        echo.
        echo El bot ya está ejecutándose. ¿Deseas reiniciarlo?
        echo [S] Sí, reiniciar
        echo [N] No, salir
        set /p choice="Selecciona una opción (S/N): "
        if /i "%choice%"=="S" (
            call :LOG "Usuario eligió reiniciar el bot"
            echo Deteniendo bot actual...
            python "%PID_MANAGER%" force-stop
            timeout /t 3 /nobreak >nul
        ) else (
            call :LOG "Usuario eligió no reiniciar, saliendo"
            echo Saliendo...
            pause
            exit /b 0
        )
    )
)

REM Verificar Docker
echo.
echo Verificando Docker...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    call :SHOW_STATUS "Docker" "ERROR"
    echo Docker no está ejecutándose. Inicia Docker Desktop y reintenta.
    pause
    exit /b 1
) else (
    call :SHOW_STATUS "Docker" "OK"
)

REM Verificar archivos necesarios
echo.
echo Verificando archivos necesarios...
if not exist "%BOT_DIR%" (
    call :SHOW_STATUS "Directorio Bot" "ERROR"
    pause
    exit /b 1
) else (
    call :SHOW_STATUS "Directorio Bot" "OK"
)

if not exist "%BOT_DIR%\configs\bybit_x_config.json" (
    call :SHOW_STATUS "Config Bybit" "ERROR"
    pause
    exit /b 1
) else (
    call :SHOW_STATUS "Config Bybit" "OK"
)

if not exist "%BOT_DIR%\configs\alert_config.json" (
    call :SHOW_STATUS "Config Alertas" "ERROR"
    pause
    exit /b 1
) else (
    call :SHOW_STATUS "Config Alertas" "OK"
)

REM Verificar servicios
echo.
echo Verificando servicios...
set RETRY=0
:CHECK_SERVICES
if %RETRY% geq 3 (
    call :SHOW_STATUS "Servicios" "ERROR"
    echo Timeout verificando servicios. Continuando...
    goto :START_BOT
)

netstat -an | findstr "9090" >nul
if %errorlevel% neq 0 (
    docker-compose -f "%PROJECT_DIR%\docker-compose.yml" up -d prometheus >>"%LOG_FILE%" 2>&1
)

netstat -an | findstr "3000" >nul
if %errorlevel% neq 0 (
    docker-compose -f "%PROJECT_DIR%\docker-compose.yml" up -d grafana >>"%LOG_FILE%" 2>&1
)

timeout /t 5 /nobreak >nul

netstat -an | findstr "9090" >nul
if %errorlevel% neq 0 (
    set /a RETRY+=1
    goto :CHECK_SERVICES
)

netstat -an | findstr "3000" >nul
if %errorlevel% neq 0 (
    set /a RETRY+=1
    goto :CHECK_SERVICES
)

call :SHOW_STATUS "Prometheus" "OK"
call :SHOW_STATUS "Grafana" "OK"

REM Limpiar puerto 8080 si está ocupado
echo.
echo Verificando puerto 8080...
netstat -an | findstr "8080" >nul
if %errorlevel% == 0 (
    call :LOG "Puerto 8080 ocupado, limpiando..."
    python "%PID_MANAGER%" force-stop >nul 2>&1
    timeout /t 3 /nobreak >nul
)

REM Enviar alerta inicial a Telegram
echo.
echo Enviando alerta inicial a Telegram...
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('[START] Bot de Trading iniciando...')" 2>>"%LOG_FILE%"
if %errorlevel% == 0 (
    call :SHOW_STATUS "Telegram" "OK"
) else (
    call :SHOW_STATUS "Telegram" "ERROR"
)

REM Iniciar bot usando PID Manager
echo.
echo Iniciando bot con PID Manager...
cd /d "%PROJECT_DIR%"
python "%PID_MANAGER%" start
if %errorlevel% == 0 (
    call :SHOW_STATUS "Bot" "OK"
    
    REM Enviar confirmación a Telegram
    cd /d "%BOT_DIR%"
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('[READY] Bot de Trading iniciado correctamente')" 2>>"%LOG_FILE%"
    
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
    echo Para detener el bot:
    echo   executables\stop_bot_robust.bat
    echo.
    echo Logs: %LOG_FILE%
    
) else (
    call :SHOW_STATUS "Bot" "ERROR"
    
    REM Enviar error a Telegram
    cd /d "%BOT_DIR%"
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('[ERROR] No se pudo iniciar el Bot de Trading')" 2>>"%LOG_FILE%"
    
    echo.
    echo +---------------------------------------------+
    echo ^|         ERROR INICIANDO BOT               ^|
    echo +---------------------------------------------+
    echo.
    echo Revisa los logs en: %LOG_FILE%
    echo.
    echo Últimas líneas del log:
    Get-Content "%LOG_FILE%" -Tail 10
)

echo.
pause
