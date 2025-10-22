@echo off
chcp 65001 >nul
title Debug Bot - Diagnostico
color 0A

echo.
echo +--------------------------------------------------------------+
echo ¦                    DEBUG BOT                                ¦
echo ¦                    Diagnostico Profundo                     ¦
echo +--------------------------------------------------------------+
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0\.."

echo Ejecutando bot en modo debug...
echo.

cd backtrader_engine

echo Iniciando bot con logging detallado...
python -u paper_trading_main.py --config configs/bybit_x_config.json

echo.
echo +--------------------------------------------------------------+
echo ¦                    DEBUG COMPLETADO                         ¦
echo +--------------------------------------------------------------+
echo.
echo Revisa los logs para identificar donde se detiene el bot
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
