@echo off
chcp 65001 >nul
title Trading Bot - Detención
color 07

REM Variables
set PROJECT_DIR=%~dp0..
set BOT_DIR=%PROJECT_DIR%\backtrader_engine
set LOG_FILE=%BOT_DIR%\logs\system_init.log
set PID_MANAGER=%PROJECT_DIR%\executables\bot_pid_manager.py

echo +---------------------------------------------+
echo ^|         TRADING BOT - DETENIENDO           ^|
echo +---------------------------------------------+
echo.

echo [%date% %time%] === DETENIENDO BOT === >> "%LOG_FILE%"

REM Verificar estado actual del bot
echo Verificando estado actual del bot...
python "%PID_MANAGER%" status | findstr "is_running.*false" >nul
if %errorlevel% == 0 (
    echo El bot ya está detenido.
    goto :CLEANUP
)

REM Enviar alerta de detención a Telegram
echo Enviando alerta de detención a Telegram...
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('🛑 Bot de Trading deteniendo...')" 2>>"%LOG_FILE%"
if %errorlevel% == 0 (
    echo Telegram: ✓ OK
) else (
    echo Telegram: ✗ ERROR
)

REM Intentar detención graceful
echo Intentando detención graceful...
python "%PID_MANAGER%" stop
if %errorlevel% == 0 (
    echo Detención Graceful: ✓ OK
    goto :VERIFY_STOP
) else (
    echo Detención Graceful: ✗ ERROR
    echo Intentando detención forzada...
)

REM Intentar detención forzada
echo Intentando detención forzada...
python "%PID_MANAGER%" force-stop
if %errorlevel% == 0 (
    echo Detención Forzada: ✓ OK
    goto :VERIFY_STOP
) else (
    echo Detención Forzada: ✗ ERROR
    echo Intentando métodos manuales...
    goto :MANUAL_STOP
)

:VERIFY_STOP
echo Verificando que el bot se haya detenido...
timeout /t 3 /nobreak >nul

python "%PID_MANAGER%" status | findstr "is_running.*false" >nul
if %errorlevel% == 0 (
    echo Verificación: ✓ OK
    goto :SUCCESS
) else (
    echo Verificación: ✗ ERROR
    echo El bot aún está ejecutándose. Intentando métodos manuales...
    goto :MANUAL_STOP
)

:MANUAL_STOP
echo === METODOS MANUALES DE DETENCION ===

REM Método 1: Buscar por nombre de proceso
echo Método 1: Buscando procesos por nombre...
for /f "tokens=2" %%i in ('tasklist /v /fi "imagename eq python.exe" ^| findstr "paper_trading_main.py"') do (
    echo Terminando proceso %%i...
    taskkill /f /pid %%i >>"%LOG_FILE%" 2>&1
    if %errorlevel% == 0 (
        echo Proceso %%i: ✓ TERMINADO
    ) else (
        echo Proceso %%i: ✗ ERROR
    )
)

REM Método 2: Terminar por puerto 8080
echo Método 2: Buscando proceso por puerto 8080...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
    echo Terminando proceso en puerto 8080: %%i...
    taskkill /f /pid %%i >>"%LOG_FILE%" 2>&1
    if %errorlevel% == 0 (
        echo Puerto 8080: ✓ LIBERADO
    ) else (
        echo Puerto 8080: ✗ ERROR
    )
)

REM Verificar detención final
echo Verificando detención final...
timeout /t 5 /nobreak >nul

tasklist /fi "imagename eq python.exe" | findstr "python" >nul
if %errorlevel% == 0 (
    echo Verificación Final: ✗ ERROR
    echo Aún hay procesos Python ejecutándose. Revisa manualmente.
    goto :FAILURE
) else (
    echo Verificación Final: ✓ OK
    goto :SUCCESS
)

:SUCCESS
echo Enviando confirmación a Telegram...
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('✅ Bot de Trading detenido correctamente')" 2>>"%LOG_FILE%"

echo.
echo +---------------------------------------------+
echo ^|         BOT DETENIDO CORRECTAMENTE         ^|
echo +---------------------------------------------+
echo.
echo Estado: Bot detenido
echo Logs: %LOG_FILE%
echo.
echo Para reiniciar: executables\start_bot_fixed.bat
goto :CLEANUP

:FAILURE
echo Enviando error a Telegram...
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('❌ Error deteniendo Bot de Trading')" 2>>"%LOG_FILE%"

echo.
echo +---------------------------------------------+
echo ^|         ERROR DETENIENDO BOT               ^|
echo +---------------------------------------------+
echo.
echo El bot no se pudo detener completamente.
echo Revisa los logs en: %LOG_FILE%

:CLEANUP
echo.
echo Limpieza completada.
echo.
pause
