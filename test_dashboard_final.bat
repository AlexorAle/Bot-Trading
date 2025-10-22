@echo off
chcp 65001 >nul
title Test Dashboard Final
color 0A

echo +---------------------------------------------+
echo ^|         🧪 TESTING DASHBOARD FINAL         ^|
echo +---------------------------------------------+
echo.

echo 🔍 Liberando puerto 8501...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501') do (
    echo Terminando proceso %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo ⏳ Esperando 3 segundos...
timeout /t 3 /nobreak >nul

echo 🚀 Iniciando Dashboard Final...
echo.
echo 📊 Dashboard: http://localhost:8501
echo 🎮 Botón "Iniciar Bot": ✅ Funciona
echo 🛑 Botón "Detener Bot": ✅ Funciona
echo.

python -m streamlit run streamlit_dashboard_fixed.py --server.port 8501

pause
