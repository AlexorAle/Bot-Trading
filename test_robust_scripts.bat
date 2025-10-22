@echo off
chcp 65001 >nul
title Test Scripts Robustos
color 0A

echo +---------------------------------------------+
echo ^|         🧪 TESTING SCRIPTS ROBUSTOS        ^|
echo +---------------------------------------------+
echo.

echo 🔍 Verificando archivos necesarios...
if not exist "executables\bot_pid_manager.py" (
    echo ❌ bot_pid_manager.py no encontrado
    pause
    exit /b 1
) else (
    echo ✅ bot_pid_manager.py encontrado
)

if not exist "executables\start_bot_robust.bat" (
    echo ❌ start_bot_robust.bat no encontrado
    pause
    exit /b 1
) else (
    echo ✅ start_bot_robust.bat encontrado
)

if not exist "executables\stop_bot_robust.bat" (
    echo ❌ stop_bot_robust.bat no encontrado
    pause
    exit /b 1
) else (
    echo ✅ stop_bot_robust.bat encontrado
)

echo.
echo 🧪 Iniciando pruebas...
echo.

echo === PRUEBA 1: Estado inicial ===
python executables\bot_pid_manager.py status
echo.

echo === PRUEBA 2: Iniciar bot ===
echo Presiona cualquier tecla para iniciar el bot...
pause >nul
executables\start_bot_robust.bat
echo.

echo === PRUEBA 3: Verificar estado ===
python executables\bot_pid_manager.py status
echo.

echo === PRUEBA 4: Detener bot ===
echo Presiona cualquier tecla para detener el bot...
pause >nul
executables\stop_bot_robust.bat
echo.

echo === PRUEBA 5: Verificar detención ===
python executables\bot_pid_manager.py status
echo.

echo +---------------------------------------------+
echo ^|         🎯 PRUEBAS COMPLETADAS             ^|
echo +---------------------------------------------+
echo.
echo Revisa los logs en: backtrader_engine\logs\system_init.log
echo.
pause
