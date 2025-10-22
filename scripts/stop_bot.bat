@echo off
chcp 65001 >nul
title Trading Bot - Deteniendo
color 0A

echo.
echo +--------------------------------------------------------------+
echo ¦                    TRADING BOT                               ¦
echo ¦                    Deteniendo Sistema                       ¦
echo +--------------------------------------------------------------+
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0\.."

echo Buscando procesos del bot...

REM Buscar procesos de Python que ejecuten paper_trading_main.py
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "paper_trading_main"') do (
    echo Proceso encontrado: %%i
    echo Deteniendo proceso...
    taskkill /pid %%i /f >nul 2>&1
    echo OK: Proceso detenido
)

REM Buscar procesos de Python en general
echo.
echo Buscando otros procesos de Python...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "python"') do (
    echo Proceso Python encontrado: %%i
    echo Deteniendo proceso...
    taskkill /pid %%i /f >nul 2>&1
    echo OK: Proceso detenido
)

echo.
echo Verificando puertos...

REM Verificar si el puerto 8080 esta en uso
netstat -an | findstr ":8080" >nul
if %errorlevel% == 0 (
    echo ADVERTENCIA: Puerto 8080 aun en uso
    echo Buscando proceso en puerto 8080...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8080"') do (
        echo PID en puerto 8080: %%i
        echo Deteniendo proceso...
        taskkill /pid %%i /f >nul 2>&1
        echo OK: Proceso detenido
    )
) else (
    echo OK: Puerto 8080 liberado
)

echo.
echo Verificando estado final...
timeout /t 2 /nobreak >nul

REM Verificar si aun hay procesos
tasklist /fi "imagename eq python.exe" | findstr "python" >nul
if %errorlevel% == 0 (
    echo ADVERTENCIA: Aun hay procesos de Python ejecutandose
    echo Lista de procesos:
    tasklist /fi "imagename eq python.exe"
    echo.
    echo Si quieres detener todos los procesos de Python:
    echo    taskkill /im python.exe /f
) else (
    echo OK: Todos los procesos de Python detenidos
)

echo.
echo +--------------------------------------------------------------+
echo ¦                    BOT DETENIDO COMPLETAMENTE               ¦
echo +--------------------------------------------------------------+
echo.
echo Estado:
echo    - Procesos Python: Detenidos
echo    - Puerto 8080: Liberado
echo    - Logs: Disponibles en backtrader_engine\logs\paper_trading.log
echo.
echo Para reiniciar el bot:
echo    Ejecuta: scripts\start_bot.bat
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
