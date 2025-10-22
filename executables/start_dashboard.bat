@echo off
chcp 65001 >nul
title Trading Bot Dashboard - Streamlit
color 0A

echo +---------------------------------------------+
echo ^|         🤖 TRADING BOT DASHBOARD           ^|
echo ^|         Iniciando Streamlit                ^|
echo +---------------------------------------------+
echo.

echo 📊 Dashboard: http://localhost:8501
echo 🤖 Bot Status: Verificando...
echo 📝 Logs: En tiempo real
echo 🎮 Controles: Disponibles
echo.

cd /d "%~dp0.."

REM Verificar si el archivo del dashboard existe
if not exist "streamlit_dashboard.py" (
    echo Creando dashboard...
    echo import streamlit as st > streamlit_dashboard.py
    echo import requests >> streamlit_dashboard.py
    echo import subprocess >> streamlit_dashboard.py
    echo import os >> streamlit_dashboard.py
    echo import time >> streamlit_dashboard.py
    echo from datetime import datetime >> streamlit_dashboard.py
    echo import psutil >> streamlit_dashboard.py
    echo. >> streamlit_dashboard.py
    echo st.set_page_config(page_title="Trading Bot Dashboard", page_icon="🤖", layout="wide") >> streamlit_dashboard.py
    echo st.title("🤖 Dashboard de Trading Bot") >> streamlit_dashboard.py
    echo. >> streamlit_dashboard.py
    echo def is_bot_running(): >> streamlit_dashboard.py
    echo     try: >> streamlit_dashboard.py
    echo         for proc in psutil.process_iter(["pid", "name", "cmdline"]): >> streamlit_dashboard.py
    echo             if proc.info["name"] == "python.exe": >> streamlit_dashboard.py
    echo                 cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else "" >> streamlit_dashboard.py
    echo                 if "paper_trading_main.py" in cmdline: >> streamlit_dashboard.py
    echo                     return True, proc.info["pid"] >> streamlit_dashboard.py
    echo         return False, None >> streamlit_dashboard.py
    echo     except: >> streamlit_dashboard.py
    echo         return False, None >> streamlit_dashboard.py
    echo. >> streamlit_dashboard.py
    echo def start_bot(): >> streamlit_dashboard.py
    echo     try: >> streamlit_dashboard.py
    echo         subprocess.Popen(["./executables/start_bot.bat"], shell=True) >> streamlit_dashboard.py
    echo         return True >> streamlit_dashboard.py
    echo     except: >> streamlit_dashboard.py
    echo         return False >> streamlit_dashboard.py
    echo. >> streamlit_dashboard.py
    echo def stop_bot(): >> streamlit_dashboard.py
    echo     try: >> streamlit_dashboard.py
    echo         subprocess.Popen(["./executables/stop_bot.bat"], shell=True) >> streamlit_dashboard.py
    echo         return True >> streamlit_dashboard.py
    echo     except: >> streamlit_dashboard.py
    echo         return False >> streamlit_dashboard.py
    echo. >> streamlit_dashboard.py
    echo bot_running, bot_pid = is_bot_running() >> streamlit_dashboard.py
    echo. >> streamlit_dashboard.py
    echo col1, col2 = st.columns([2, 1]) >> streamlit_dashboard.py
    echo. >> streamlit_dashboard.py
    echo with col1: >> streamlit_dashboard.py
    echo     st.markdown("### Estado del Bot") >> streamlit_dashboard.py
    echo     if bot_running: >> streamlit_dashboard.py
    echo         st.success("BOT ACTIVO") >> streamlit_dashboard.py
    echo         st.info("Estrategias activas: 5 estrategias") >> streamlit_dashboard.py
    echo     else: >> streamlit_dashboard.py
    echo         st.error("BOT DETENIDO") >> streamlit_dashboard.py
    echo         st.info("Estrategias: No activas") >> streamlit_dashboard.py
    echo. >> streamlit_dashboard.py
    echo with col2: >> streamlit_dashboard.py
    echo     st.markdown("### Controles del Bot") >> streamlit_dashboard.py
    echo     if bot_running: >> streamlit_dashboard.py
    echo         st.success("Bot ejecutandose") >> streamlit_dashboard.py
    echo         if st.button("Detener Bot", type="primary"): >> streamlit_dashboard.py
    echo             if stop_bot(): >> streamlit_dashboard.py
    echo                 st.success("Comando de detencion enviado") >> streamlit_dashboard.py
    echo                 time.sleep(2) >> streamlit_dashboard.py
    echo                 st.rerun() >> streamlit_dashboard.py
    echo             else: >> streamlit_dashboard.py
    echo                 st.error("Error enviando comando") >> streamlit_dashboard.py
    echo     else: >> streamlit_dashboard.py
    echo         st.error("Bot detenido") >> streamlit_dashboard.py
    echo         if st.button("Iniciar Bot", type="primary"): >> streamlit_dashboard.py
    echo             if start_bot(): >> streamlit_dashboard.py
    echo                 st.success("Comando de inicio enviado") >> streamlit_dashboard.py
    echo                 time.sleep(2) >> streamlit_dashboard.py
    echo                 st.rerun() >> streamlit_dashboard.py
    echo             else: >> streamlit_dashboard.py
    echo                 st.error("Error enviando comando") >> streamlit_dashboard.py
    echo. >> streamlit_dashboard.py
    echo st.markdown("---") >> streamlit_dashboard.py
    echo st.markdown("Trading Bot Dashboard") >> streamlit_dashboard.py
)

streamlit run streamlit_dashboard.py --server.port 8501 --server.address localhost

pause
