@echo off
chcp 65001 >nul
title Trading Bot - Estado del Sistema
color 07

echo +---------------------------------------------+
echo ¦         TRADING BOT - ESTADO               ¦
echo +---------------------------------------------+
echo.

echo Verificando Bot...
tasklist /fi "imagename eq python.exe" | findstr "paper_trading_main.py" >nul
if %errorlevel% == 0 (
    echo Bot: ✓ OK - Ejecutandose
) else (
    echo Bot: ✗ ERROR - No ejecutandose
)

echo.
echo Verificando Puertos...

netstat -an | findstr "8080" >nul
if %errorlevel% == 0 (
    echo Puerto 8080: ✓ OK - Metricas activas
) else (
    echo Puerto 8080: ✗ ERROR - No disponible
)

netstat -an | findstr "9090" >nul
if %errorlevel% == 0 (
    echo Puerto 9090: ✓ OK - Prometheus activo
) else (
    echo Puerto 9090: ✗ ERROR - No disponible
)

netstat -an | findstr "3000" >nul
if %errorlevel% == 0 (
    echo Puerto 3000: ✓ OK - Grafana activo
) else (
    echo Puerto 3000: ✗ ERROR - No disponible
)

echo.
echo Verificando Archivos...
if exist "backtrader_engine\logs\paper_trading.log" (
    echo Logs: ✓ OK - Archivo encontrado
) else (
    echo Logs: ✗ ERROR - Archivo no encontrado
)

if exist "backtrader_engine\configs\bybit_x_config.json" (
    echo Config Bybit: ✓ OK
) else (
    echo Config Bybit: ✗ ERROR
)

if exist "backtrader_engine\configs\strategies_config_72h.json" (
    echo Config Estrategias: ✓ OK
) else (
    echo Config Estrategias: ✗ ERROR
)

echo.
echo +---------------------------------------------+
echo ¦         RESUMEN COMPLETO                   ¦
echo +---------------------------------------------+
echo.
echo URLs:
echo   Grafana: http://localhost:3000
echo   Prometheus: http://localhost:9090
echo   Metricas: http://localhost:8080/metrics
echo.
echo Scripts:
echo   Iniciar: executables\start_bot.bat
echo   Detener: executables\stop_bot.bat
echo   Estado: executables\check_bot_status.bat
echo.
pause