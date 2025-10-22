@echo off
chcp 65001 >nul
title Trading Bot - Detención Robusta
color 07

REM Variables
set PROJECT_DIR=%~dp0..
set BOT_DIR=%PROJECT_DIR%\backtrader_engine
set LOG_FILE=%BOT_DIR%\logs\system_init.log
set PID_MANAGER=%PROJECT_DIR%\executables\bot_pid_manager.py

echo +---------------------------------------------+
echo ^|         TRADING BOT - DETENCION ROBUSTA     ^|
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

call :LOG "=== DETENIENDO BOT - DETENCION ROBUSTA ==="

REM Verificar estado actual del bot
echo Verificando estado actual del bot...
python "%PID_MANAGER%" status >nul 2>&1
if %errorlevel% neq 0 (
    call :SHOW_STATUS "PID Manager" "ERROR"
    echo Error accediendo al PID Manager. Intentando detención manual...
    goto :MANUAL_STOP
)

REM Obtener estado del bot
for /f "tokens=*" %%i in ('python "%PID_MANAGER%" status ^| findstr "is_running"') do set BOT_STATUS=%%i
echo %BOT_STATUS% | findstr "true" >nul
if %errorlevel% neq 0 (
    call :SHOW_STATUS "Bot Status" "YA_DETENIDO"
    echo El bot ya está detenido.
    goto :CLEANUP
)

REM Enviar alerta de detención a Telegram
echo.
echo Enviando alerta de detención a Telegram...
cd /d "%BOT_DIR%"
python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('🛑 Bot de Trading deteniendo...')" 2>>"%LOG_FILE%"
if %errorlevel% == 0 (
    call :SHOW_STATUS "Telegram" "OK"
) else (
    call :SHOW_STATUS "Telegram" "ERROR"
)

REM Intentar detención graceful
echo.
echo Intentando detención graceful...
python "%PID_MANAGER%" stop
if %errorlevel% == 0 (
    call :SHOW_STATUS "Detención Graceful" "OK"
    goto :VERIFY_STOP
) else (
    call :SHOW_STATUS "Detención Graceful" "ERROR"
    echo Detención graceful falló. Intentando detención forzada...
)

REM Intentar detención forzada
echo.
echo Intentando detención forzada...
python "%PID_MANAGER%" force-stop
if %errorlevel% == 0 (
    call :SHOW_STATUS "Detención Forzada" "OK"
    goto :VERIFY_STOP
) else (
    call :SHOW_STATUS "Detención Forzada" "ERROR"
    echo Detención forzada falló. Intentando métodos manuales...
    goto :MANUAL_STOP
)

:VERIFY_STOP
echo.
echo Verificando que el bot se haya detenido...
timeout /t 3 /nobreak >nul

python "%PID_MANAGER%" status | findstr "is_running.*false" >nul
if %errorlevel% == 0 (
    call :SHOW_STATUS "Verificación" "OK"
    goto :SUCCESS
) else (
    call :SHOW_STATUS "Verificación" "ERROR"
    echo El bot aún está ejecutándose. Intentando métodos manuales...
    goto :MANUAL_STOP
)

:MANUAL_STOP
echo.
echo === METODOS MANUALES DE DETENCION ===

REM Método 1: Buscar por nombre de proceso
echo Método 1: Buscando procesos por nombre...
for /f "tokens=2" %%i in ('tasklist /v /fi "imagename eq python.exe" ^| findstr "paper_trading_main.py"') do (
    echo Terminando proceso %%i...
    taskkill /f /pid %%i >>"%LOG_FILE%" 2>&1
    if %errorlevel% == 0 (
        call :SHOW_STATUS "Proceso %%i" "TERMINADO"
    ) else (
        call :SHOW_STATUS "Proceso %%i" "ERROR"
    )
)

REM Método 2: Terminar por puerto 8080
echo.
echo Método 2: Buscando proceso por puerto 8080...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
    echo Terminando proceso en puerto 8080: %%i...
    taskkill /f /pid %%i >>"%LOG_FILE%" 2>&1
    if %errorlevel% == 0 (
        call :SHOW_STATUS "Puerto 8080" "LIBERADO"
    ) else (
        call :SHOW_STATUS "Puerto 8080" "ERROR"
    )
)

REM Método 3: Terminar todos los procesos Python (último recurso)
echo.
echo Método 3: Terminando todos los procesos Python...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr /v "PID"') do (
    set PID=%%i
    set PID=!PID:"=!
    echo Terminando proceso Python !PID!...
    taskkill /f /pid !PID! >>"%LOG_FILE%" 2>&1
    if %errorlevel% == 0 (
        call :SHOW_STATUS "Python !PID!" "TERMINADO"
    ) else (
        call :SHOW_STATUS "Python !PID!" "ERROR"
    )
)

REM Verificar detención final
echo.
echo Verificando detención final...
timeout /t 5 /nobreak >nul

tasklist /fi "imagename eq python.exe" | findstr "python" >nul
if %errorlevel% == 0 (
    call :SHOW_STATUS "Verificación Final" "ERROR"
    echo Aún hay procesos Python ejecutándose. Revisa manualmente.
    goto :FAILURE
) else (
    call :SHOW_STATUS "Verificación Final" "OK"
    goto :SUCCESS
)

:SUCCESS
echo.
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
echo Para reiniciar: executables\start_bot_robust.bat
goto :CLEANUP

:FAILURE
echo.
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
echo.
echo Últimas líneas del log:
Get-Content "%LOG_FILE%" -Tail 10
goto :CLEANUP

:CLEANUP
echo.
echo Limpiando archivos temporales...
python "%PID_MANAGER%" status >nul 2>&1
if %errorlevel% == 0 (
    call :SHOW_STATUS "Limpieza" "OK"
) else (
    call :SHOW_STATUS "Limpieza" "ERROR"
)

echo.
pause
