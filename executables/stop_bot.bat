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
echo ^|         TRADING BOT - DETENIENDO           ^|
echo +---------------------------------------------+
echo.

REM Alerta Telegram
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('El bot se esta deteniendo...')" 2>>"%LOG_FILE%"
if %errorlevel% == 0 (
    color 0A
    echo Telegram: ✓ OK
) else (
    color 0C
    echo Telegram: ✗ ERROR
)
color 07

REM Detener Bot
for /f "tokens=2" %%i in ('tasklist /v /fi "imagename eq python.exe" ^| findstr "paper_trading_main.py"') do taskkill /f /pid %%i >>"%LOG_FILE%" 2>&1
if %errorlevel% == 0 (
    color 0A
    echo Bot: ✓ OK
    cd /d "%BOT_DIR%"
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('Bot detenido correctamente.')" 2>>"%LOG_FILE%"
) else (
    color 0C
    echo Bot: ✗ ERROR
)
color 07

REM Detener Services
docker-compose -f "%COMPOSE_FILE%" down >>"%LOG_FILE%" 2>&1
if %errorlevel% == 0 (
    color 0A
    echo Servicios: ✓ OK
) else (
    color 0C
    echo Servicios: ✗ ERROR
)
color 07

timeout /t 2 /nobreak >nul

REM Verificar
tasklist /fi "imagename eq python.exe" | findstr "python" >nul
if %errorlevel% == 0 (
    color 0C
    echo Cleanup: ✗ ERROR
) else (
    color 0A
    echo Cleanup: ✓ OK
)
color 07

echo.
echo +---------------------------------------------+
echo ^|         SISTEMA DETENIDO                   ^|
echo +---------------------------------------------+
echo.
echo Estado:
echo   Bot: Detenido
echo   Servicios: Detenidos
echo   Logs: Disponibles en %LOG_FILE%
echo.
echo Para reiniciar:
echo   Ejecuta: executables\start_bot.bat
echo.
pause >nul