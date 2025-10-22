@echo off
chcp 65001 >nul
title Trading Bot - Iniciando
color 0A

echo.
echo +--------------------------------------------------------------+
echo ¦                    TRADING BOT 72H                          ¦
echo ¦                    Iniciando Sistema                         ¦
echo +--------------------------------------------------------------+
echo.
echo Configuracion:
echo    - 5 estrategias activas
echo    - Bybit X (datos reales)
echo    - Paper Trading
echo    - Alertas Telegram
echo    - Monitoreo Grafana
echo.
echo Simbolos: ETHUSDT, BTCUSDT, SOLUSDT
echo.
echo Alertas: Telegram habilitadas
echo Monitoreo: Grafana + Prometheus
echo.
echo Duracion: 72 horas continuas
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0\.."

REM Verificar si estamos en el directorio correcto
if not exist "backtrader_engine" (
    echo ERROR: No se encuentra el directorio backtrader_engine
    echo    Asegurate de ejecutar este archivo desde la carpeta scripts
    echo.
    pause
    exit /b 1
)

echo OK: Directorio del proyecto encontrado
echo.

REM Cambiar al directorio backtrader_engine
cd backtrader_engine

echo Verificando archivos necesarios...
if not exist "paper_trading_main.py" (
    echo ERROR: No se encuentra paper_trading_main.py
    pause
    exit /b 1
)

if not exist "configs\bybit_x_config.json" (
    echo ERROR: No se encuentra configs\bybit_x_config.json
    pause
    exit /b 1
)

echo OK: Archivos de configuracion encontrados
echo.

echo Verificando directorio de logs...
if not exist "logs" (
    echo Creando directorio de logs...
    mkdir logs
    echo OK: Directorio de logs creado
)

echo.
echo +--------------------------------------------------------------+
echo ¦                    INICIANDO BOT                            ¦
echo +--------------------------------------------------------------+
echo.
echo Revisa tu Telegram para alertas
echo Grafana: http://localhost:3000
echo Prometheus: http://localhost:9090
echo.
echo Para detener el bot, presiona Ctrl+C
echo.

python paper_trading_main.py --config configs/bybit_x_config.json

echo.
echo +--------------------------------------------------------------+
echo ¦                    BOT DETENIDO                             ¦
echo +--------------------------------------------------------------+
echo.
echo El bot ha sido detenido
echo Revisa los logs en: backtrader_engine\logs\paper_trading.log
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
