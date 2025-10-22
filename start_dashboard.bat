@echo off
chcp 65001 >nul
title Trading Bot Dashboard
color 0A

echo +---------------------------------------------+
echo ^|         🤖 TRADING BOT DASHBOARD           ^|
echo +---------------------------------------------+
echo.

echo 🔍 Liberando puerto 8501...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501') do (
    echo Terminando proceso %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo ⏳ Esperando 3 segundos...
timeout /t 3 /nobreak >nul

echo 🚀 Iniciando Dashboard...
echo.
echo 📊 Dashboard: http://localhost:8501
echo 🎮 Controles: Iniciar/Detener Bot
echo 📝 Logs: En tiempo real
echo.

python -m streamlit run streamlit_dashboard_fixed.py --server.port 8501 --server.address localhost

pause
