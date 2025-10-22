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
    """Verifica si el bot está ejecutándose"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'paper_trading_main.py' in cmdline:
                    return True, proc.info['pid']
        return False, None
    except Exception as e:
        return False, None

def get_metrics():
    """Obtiene métricas del bot desde Prometheus"""
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
    except Exception as e:
        return {}

def read_logs():
    """Lee las últimas líneas del log"""
    try:
        log_paths = [
            "backtrader_engine/logs/vstru_trading.log",
            "backtrader_engine/logs/paper_trading.log"
        ]
        for log_file in log_paths:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    return lines[-20:] if len(lines) > 20 else lines
        return []
    except Exception as e:
        return []

def start_bot():
    """Inicia el bot usando el script corregido"""
    try:
        # Usar ruta absoluta para Windows
        script_path = os.path.join(os.getcwd(), "executables", "start_bot_fixed.bat")
        result = subprocess.Popen(
            [script_path], 
            shell=True,
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Esperar a que termine el script
        result.wait(timeout=45)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        st.error("Timeout: El script tardó demasiado en ejecutarse")
        return False
    except Exception as e:
        st.error(f"Error iniciando bot: {e}")
        return False

def stop_bot():
    """Detiene el bot usando el script corregido"""
    try:
        # Usar ruta absoluta para Windows
        script_path = os.path.join(os.getcwd(), "executables", "stop_bot_fixed.bat")
        result = subprocess.Popen(
            [script_path], 
            shell=True,
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Esperar a que termine el script
        result.wait(timeout=45)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        st.error("Timeout: El script tardó demasiado en ejecutarse")
        return False
    except Exception as e:
        st.error(f"Error deteniendo bot: {e}")
        return False

# Verificar estado del bot
bot_running, bot_pid = is_bot_running()

# Layout principal
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📊 Estado del Bot")
    
    if bot_running:
        st.success("🟢 **BOT ACTIVO**")
        st.info(f"**PID:** {bot_pid}")
        st.info("**Estrategias activas:** 5 estrategias")
        st.info(f"**Última actualización:** {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.error("🔴 **BOT DETENIDO**")
        st.info("**Estrategias:** No activas")
        st.info(f"**Última verificación:** {datetime.now().strftime('%H:%M:%S')}")
    
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
        st.success(f"✅ Bot ejecutándose (PID: {bot_pid})")
        if st.button("🛑 Detener Bot", type="primary"):
            with st.spinner("Deteniendo bot..."):
                if stop_bot():
                    st.success("✅ Bot detenido correctamente")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("❌ Error deteniendo bot")
    else:
        st.error("❌ Bot detenido")
        if st.button("🚀 Iniciar Bot", type="primary"):
            with st.spinner("Iniciando bot..."):
                if start_bot():
                    st.success("✅ Bot iniciado correctamente")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("❌ Error iniciando bot")
    
    st.markdown("### 🔄 Modo Demo / Live Toggle")
    
    mode = st.radio("Modo de Trading", ["📄 Paper Trading (Demo)", "🚀 Live Trading (Real)"], index=0)
    
    if "Paper Trading" in mode:
        st.success("📄 **MODO DEMO ACTIVO**")
        st.info("• Datos reales de Bybit")
        st.info("• Sin ejecución real")
        st.info("• Balance simulado: $10,000")
    else:
        st.warning("🚀 **MODO LIVE ACTIVO**")
        st.error("⚠️ **ATENCIÓN:** Trading real activado")
    
    st.markdown("### ℹ️ Información del Sistema")
    
    # Estado de servicios
    try:
        response = requests.get("http://localhost:9090", timeout=3)
        if response.status_code == 200:
            st.success("✅ Prometheus")
        else:
            st.error("❌ Prometheus")
    except:
        st.error("❌ Prometheus")
    
    try:
        response = requests.get("http://localhost:3000", timeout=3)
        if response.status_code == 200:
            st.success("✅ Grafana")
        else:
            st.error("❌ Grafana")
    except:
        st.error("❌ Grafana")
    
    try:
        response = requests.get("http://localhost:8080/metrics", timeout=3)
        if response.status_code == 200:
            st.success("✅ Métricas Bot")
        else:
            st.error("❌ Métricas Bot")
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

# Auto-refresh
if st.checkbox("🔄 Auto-refresh (10s)", value=True):
    time.sleep(10)
    st.rerun()

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    🤖 Trading Bot Dashboard | Desarrollado con Streamlit
</div>
""", unsafe_allow_html=True)
