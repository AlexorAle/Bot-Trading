import streamlit as st
import requests
import subprocess
import os
import time
from datetime import datetime
import psutil

st.set_page_config(page_title="Trading Bot Dashboard", page_icon="🤖", layout="wide")
st.title("🤖 Dashboard de Trading Bot")

def is_bot_running():
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'paper_trading_main.py' in cmdline:
                    return True, proc.info['pid']
        return False, None
    except:
        return False, None

def get_metrics():
    try:
        response = requests.get("http://localhost:8080/metrics", timeout=5)
        if response.status_code == 200:
            metrics = {}
            for line in response.text.split('\n'):
                if line.startswith('paper_') and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        metrics[parts[0]] = parts[1]
            return metrics
        return {}
    except:
        return {}

def read_logs():
    try:
        log_file = "backtrader_engine/logs/paper_trading.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-20:] if len(lines) > 20 else lines
        return []
    except:
        return []

def start_bot():
    try:
        subprocess.Popen(["./executables/start_bot.bat"], shell=True)
        return True
    except:
        return False

def stop_bot():
    try:
        subprocess.Popen(["./executables/stop_bot.bat"], shell=True)
        return True
    except:
        return False

bot_running, bot_pid = is_bot_running()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📊 Estado del Bot")
    
    if bot_running:
        st.success("🟢 **BOT ACTIVO**")
        st.info("**Estrategias activas:** 5 estrategias")
    else:
        st.error("🔴 **BOT DETENIDO**")
        st.info("**Estrategias:** No activas")
    
    st.markdown("### 📝 Logs en Tiempo Real")
    
    if st.button("🔄 Refrescar Logs"):
        st.rerun()
    
    logs = read_logs()
    if logs:
        for log_line in logs:
            if "ERROR" in log_line:
                st.error(log_line.strip())
            elif "WARNING" in log_line:
                st.warning(log_line.strip())
            elif "INFO" in log_line:
                st.info(log_line.strip())
            else:
                st.text(log_line.strip())
    else:
        st.info("No hay logs disponibles")

with col2:
    st.markdown("### 🎮 Controles del Bot")
    
    if bot_running:
        st.success("✅ Bot ejecutándose")
        if st.button("🛑 Detener Bot", type="primary"):
            if stop_bot():
                st.success("Comando de detención enviado")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Error enviando comando")
    else:
        st.error("❌ Bot detenido")
        if st.button("🚀 Iniciar Bot", type="primary"):
            if start_bot():
                st.success("Comando de inicio enviado")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Error enviando comando")
    
    st.markdown("### 🔄 Modo Demo / Live Toggle")
    
    mode = st.radio("Modo de Trading", ["📄 Paper Trading (Demo)", "🚀 Live Trading (Real)"], index=0)
    
    if "Paper Trading" in mode:
        st.success("📄 **MODO DEMO ACTIVO**")
        st.info("• Datos reales de Bybit\n• Sin ejecución real\n• Balance simulado: $10,000")
    else:
        st.warning("🚀 **MODO LIVE ACTIVO**")
        st.error("⚠️ **ATENCIÓN:** Trading real activado")
    
    st.markdown("### ℹ️ Información del Sistema")
    
    try:
        response = requests.get("http://localhost:9090", timeout=3)
        st.success("✅ Prometheus") if response.status_code == 200 else st.error("❌ Prometheus")
    except:
        st.error("❌ Prometheus")
    
    try:
        response = requests.get("http://localhost:3000", timeout=3)
        st.success("✅ Grafana") if response.status_code == 200 else st.error("❌ Grafana")
    except:
        st.error("❌ Grafana")
    
    try:
        response = requests.get("http://localhost:8080/metrics", timeout=3)
        st.success("✅ Métricas Bot") if response.status_code == 200 else st.error("❌ Métricas Bot")
    except:
        st.error("❌ Métricas Bot")
    
    st.markdown("### 📈 Métricas Rápidas")
    
    metrics = get_metrics()
    if metrics:
        st.metric("Señales Generadas", metrics.get('paper_signals_generated_total', '0'))
        st.metric("Precio ETH", f"${metrics.get('paper_current_price_ethusdt', '0')}")
        st.metric("Balance", f"${metrics.get('paper_balance_usd', '10000')}")
    else:
        st.warning("⚠️ No se pueden obtener métricas")

if st.checkbox("🔄 Auto-refresh (10s)", value=True):
    time.sleep(10)
    st.rerun()

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    🤖 Trading Bot Dashboard | Desarrollado con Streamlit
</div>
""", unsafe_allow_html=True)