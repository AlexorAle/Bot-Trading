@echo off
chcp 65001 >nul
title Trading Bot - Iniciando Sistema
color 07

REM Variables
set PROJECT_DIR=%~dp0..
set BOT_DIR=%PROJECT_DIR%\backtrader_engine
set LOG_FILE=%BOT_DIR%\logs\system_init.log
set CONFIG_BYBIT=%BOT_DIR%\configs\bybit_x_config.json
set CONFIG_ALERT=%BOT_DIR%\configs\alert_config.json
set COMPOSE_FILE=%PROJECT_DIR%\docker-compose.yml

echo +---------------------------------------------+
echo ¦         TRADING BOT - INICIANDO            ¦
echo +---------------------------------------------+
echo.

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

REM Verificar configs/dirs
echo.
echo Verificando Archivos...
if not exist "%BOT_DIR%" (
    echo Directorio backtrader_engine: ✗ ERROR - No encontrado
    pause
    exit /b 1
) else (
    echo Directorio backtrader_engine: ✓ OK
)

if not exist "%CONFIG_BYBIT%" (
    echo Configuracion Bybit: ✗ ERROR - No encontrada
    pause
    exit /b 1
) else (
    echo Configuracion Bybit: ✓ OK
)

if not exist "%CONFIG_ALERT%" (
    echo Configuracion Alertas: ✗ ERROR - No encontrada
    pause
    exit /b 1
) else (
    echo Configuracion Alertas: ✓ OK
)

REM Verificar servicios
echo.
echo Verificando Servicios...
netstat -an | findstr "9090" >nul
if %errorlevel% neq 0 (
    echo Prometheus: ✗ ERROR - No ejecutandose
    echo Iniciando Prometheus...
    docker-compose -f "%COMPOSE_FILE%" up -d prometheus
    timeout /t 5 /nobreak >nul
) else (
    echo Prometheus: ✓ OK
)

netstat -an | findstr "3000" >nul
if %errorlevel% neq 0 (
    echo Grafana: ✗ ERROR - No ejecutandose
    echo Iniciando Grafana...
    docker-compose -f "%COMPOSE_FILE%" up -d grafana
    timeout /t 5 /nobreak >nul
) else (
    echo Grafana: ✓ OK
)

REM Alerta Telegram inicial
echo.
echo Enviando alerta inicial Telegram...
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('El bot se esta inicializando...')" 2>>"%LOG_FILE%"
if %errorlevel% == 0 (
    echo Telegram: ✓ OK - Alerta enviada
) else (
    echo Telegram: ✗ ERROR - Continuando sin alerta
)

REM Iniciar Bot
echo.
echo Iniciando Bot...
cd /d "%BOT_DIR%"
echo [%date% %time%] Iniciando bot... >> "%LOG_FILE%"
start /B python paper_trading_main.py --config configs/bybit_x_config.json >>"%LOG_FILE%" 2>&1
echo [%date% %time%] Comando start ejecutado, esperando 5 segundos... >> "%LOG_FILE%"
timeout /t 5 /nobreak >nul
echo [%date% %time%] Verificando procesos Python... >> "%LOG_FILE%"
tasklist /fi "imagename eq python.exe" | findstr "python" >nul
if %errorlevel% == 0 (
    echo Bot: ✓ OK - Iniciado correctamente
    echo [%date% %time%] Bot iniciado correctamente >> "%LOG_FILE%"
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('Bot inicializado correctamente.')" 2>>"%LOG_FILE%"
) else (
    echo Bot: ✗ ERROR - Error al iniciar
    echo [%date% %time%] ERROR: Bot no se pudo iniciar >> "%LOG_FILE%"
    echo [%date% %time%] Verificando logs de error... >> "%LOG_FILE%"
    Get-Content "%LOG_FILE%" -Tail 10 >> "%LOG_FILE%"
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('Error inicializando bot.')" 2>>"%LOG_FILE%"
)

echo.
echo +---------------------------------------------+
echo ¦         SISTEMA INICIADO                   ¦
echo +---------------------------------------------+
echo URLs: Grafana http://localhost:3000, Prometheus http://localhost:9090, Metricas http://localhost:8080/metrics            
echo Logs: %LOG_FILE%
pause