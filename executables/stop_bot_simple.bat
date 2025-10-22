@echo off
chcp 65001 >nul
title Trading Bot - Deteniendo
color 0C

echo +---------------------------------------------+
echo ^|         TRADING BOT - DETENIENDO           ^|
echo +---------------------------------------------+
echo.

echo 🔍 Buscando procesos del bot...
for /f "tokens=2" %%i in ('tasklist /v /fi "imagename eq python.exe" ^| findstr "paper_trading_main.py"') do (
    echo Terminando proceso %%i...
    taskkill /f /pid %%i >nul 2>&1
)

echo ⏳ Esperando 2 segundos...
timeout /t 2 /nobreak >nul

echo 🔍 Verificando que no hay procesos activos...
tasklist /fi "imagename eq python.exe" | findstr "paper_trading_main.py" >nul
if %errorlevel% == 0 (
    color 0C
    echo ❌ Aún hay procesos activos
) else (
    color 0A
    echo ✅ Bot detenido correctamente
)
color 07

echo.
echo +---------------------------------------------+
echo ^|         BOT DETENIDO                       ^|
echo +---------------------------------------------+
echo.
echo Para reiniciar: executables\start_bot.bat
echo.
pause
