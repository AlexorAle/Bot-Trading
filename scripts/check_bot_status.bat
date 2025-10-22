@echo off
chcp 65001 >nul
title Trading Bot - Estado del Sistema
color 0A

echo.
echo +--------------------------------------------------------------+
echo ¦                    TRADING BOT                               ¦
echo ¦                    Verificando Estado                       ¦
echo +--------------------------------------------------------------+
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0\.."

echo Verificando procesos de Python...
tasklist /fi "imagename eq python.exe" | findstr "python" >nul
if %errorlevel% == 0 (
    echo OK: Procesos de Python encontrados:
    tasklist /fi "imagename eq python.exe"
) else (
    echo ERROR: No hay procesos de Python ejecutandose
)

echo.
echo Verificando puerto 8080 (metricas del bot)...
netstat -an | findstr ":8080" >nul
if %errorlevel% == 0 (
    echo OK: Puerto 8080 en uso - Bot probablemente ejecutandose
    echo Metricas disponibles en: http://localhost:8080/metrics
) else (
    echo ERROR: Puerto 8080 libre - Bot no ejecutandose
)

echo.
echo Verificando puerto 9090 (Prometheus)...
netstat -an | findstr ":9090" >nul
if %errorlevel% == 0 (
    echo OK: Prometheus ejecutandose en puerto 9090
    echo Prometheus disponible en: http://localhost:9090
) else (
    echo ERROR: Prometheus no esta ejecutandose
)

echo.
echo Verificando puerto 3000 (Grafana)...
netstat -an | findstr ":3000" >nul
if %errorlevel% == 0 (
    echo OK: Grafana ejecutandose en puerto 3000
    echo Grafana disponible en: http://localhost:3000
) else (
    echo ERROR: Grafana no esta ejecutandose
)

echo.
echo Verificando logs...
if exist "backtrader_engine\logs\paper_trading.log" (
    echo OK: Archivo de log encontrado
    echo Tamano del log:
    dir "backtrader_engine\logs\paper_trading.log" | findstr "paper_trading.log"
    echo.
    echo Ultimas 5 lineas del log:
    echo +--------------------------------------------------------------+
    powershell "Get-Content 'backtrader_engine\logs\paper_trading.log' | Select-Object -Last 5"
    echo +--------------------------------------------------------------+
) else (
    echo ERROR: No se encuentra archivo de log
)

echo.
echo Verificando configuracion...
if exist "backtrader_engine\configs\bybit_x_config.json" (
    echo OK: Configuracion Bybit X encontrada
) else (
    echo ERROR: Configuracion Bybit X no encontrada
)

if exist "backtrader_engine\configs\strategies_config_72h.json" (
    echo OK: Configuracion de estrategias encontrada
) else (
    echo ERROR: Configuracion de estrategias no encontrada
)

echo.
echo +--------------------------------------------------------------+
echo ¦                    RESUMEN DEL ESTADO                        ¦
echo +--------------------------------------------------------------+
echo.
echo Para iniciar el bot: scripts\start_bot.bat
echo Para detener el bot: scripts\stop_bot.bat
echo Para verificar estado: scripts\check_bot_status.bat
echo Para probar Telegram: scripts\test_telegram.bat
echo.
echo Telegram: Revisa alertas en tu chat
echo Grafana: http://localhost:3000
echo Prometheus: http://localhost:9090
echo Metricas: http://localhost:8080/metrics
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
