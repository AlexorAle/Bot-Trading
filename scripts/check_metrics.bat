@echo off
chcp 65001 >nul
title Verificar Metricas del Bot
color 0A

echo.
echo +--------------------------------------------------------------+
echo ¦                    VERIFICAR METRICAS                        ¦
echo +--------------------------------------------------------------+
echo.

echo Verificando si el bot esta ejecutandose...
netstat -an | findstr ":8080" >nul
if %errorlevel% == 0 (
    echo OK: Bot ejecutandose en puerto 8080
    echo.
    echo Obteniendo metricas del bot...
    echo.
    curl -s http://localhost:8080/metrics | findstr "paper_"
    echo.
    echo +--------------------------------------------------------------+
    echo ¦                    METRICAS OBTENIDAS                       ¦
    echo +--------------------------------------------------------------+
    echo.
    echo Si ves metricas con valores numericos, el bot esta funcionando
    echo Si solo ves definiciones sin valores, el bot no esta generando señales
    echo.
) else (
    echo ERROR: Bot no esta ejecutandose
    echo Puerto 8080 no esta en uso
    echo.
    echo Ejecuta primero: scripts\start_bot.bat
)

echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
