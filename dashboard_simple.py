import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time

st.set_page_config(page_title="Liquidation Hunter Dashboard", layout="wide")

# Header con título y controles
col_title, col_status, col_control = st.columns([3, 1, 1])

# Función para verificar estado del bot
def check_bot_status():
    """Verificar si el bot está ejecutándose"""
    try:
        if os.path.exists('logs/bot.log'):
            with open('logs/bot.log', 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if "Starting trading bot" in last_line or "Starting trading cycle" in last_line:
                        return "🟢 Ejecutándose"
                    elif "shutting down" in last_line:
                        return "🔴 Detenido"
                    else:
                        return "🟡 Procesando"
        return "❌ Sin logs"
    except:
        return "❌ Error"

with col_title:
    st.title("📊 LiquidationHunter - Panel de Monitoreo")

with col_status:
    # LED dinámico de estado
    bot_status = check_bot_status()
    if "Ejecutándose" in bot_status or "Procesando" in bot_status:
        st.markdown("""
        <div style="text-align: center;">
            <div style="width: 20px; height: 20px; background-color: #00ff00; border-radius: 50%; 
                        box-shadow: 0 0 10px #00ff00; animation: pulse 2s infinite; margin: 0 auto;"></div>
            <p style="margin: 5px 0; font-size: 12px; color: #00ff00;">ACTIVO</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center;">
            <div style="width: 20px; height: 20px; background-color: #ff0000; border-radius: 50%; 
                        margin: 0 auto;"></div>
            <p style="margin: 5px 0; font-size: 12px; color: #ff0000;">INACTIVO</p>
        </div>
        """, unsafe_allow_html=True)

with col_control:
    st.markdown("<br>", unsafe_allow_html=True)  # Espaciado
    if "Ejecutándose" in bot_status or "Procesando" in bot_status:
        if st.button("🛑 Detener", key="stop_bot"):
            st.warning("Función de detención no implementada aún")
    else:
        if st.button("▶️ Iniciar", key="start_bot"):
            st.info("Función de inicio no implementada aún")

# CSS para animación de pulso
st.markdown("""
<style>
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# Auto-refresh cada 30 segundos
if st.button("🔄 Actualizar Datos"):
    st.rerun()

# Obtener métricas básicas
def get_basic_metrics():
    """Obtener métricas básicas del bot"""
    try:
        if not os.path.exists('logs/bot.log'):
            return {'cycles': 0, 'signals': 0, 'trades': 0, 'errors': 0}
        
        with open('logs/bot.log', 'r') as f:
            lines = f.readlines()
        
        cycles = len([l for l in lines if 'Starting trading cycle' in l])
        signals = len([l for l in lines if 'Generated signal' in l])
        trades = len([l for l in lines if 'Trade executed successfully' in l])
        errors = len([l for l in lines if 'ERROR' in l])
        
        return {'cycles': cycles, 'signals': signals, 'trades': trades, 'errors': errors}
    except:
        return {'cycles': 0, 'signals': 0, 'trades': 0, 'errors': 0}

# Obtener datos del bot
def get_bot_data():
    """Obtener datos básicos del bot"""
    try:
        from config import Config
        config = Config()
        return {
            'mode': config.MODE,
            'symbol': config.SYMBOL,
            'timeframe': config.TIMEFRAME,
            'exchange': config.EXCHANGE,
            'update_interval': config.UPDATE_INTERVAL
        }
    except:
        return None

# Obtener últimos logs
def get_recent_logs(n=10):
    """Obtener los últimos n logs"""
    try:
        if os.path.exists('logs/bot.log'):
            with open('logs/bot.log', 'r') as f:
                lines = f.readlines()
                return lines[-n:] if len(lines) >= n else lines
        return []
    except:
        return []

# Métricas principales
metrics = get_basic_metrics()
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🟢 Estado", bot_status)
with col2:
    st.metric("📊 Ciclos", f"{metrics['cycles']}", "0")
with col3:
    st.metric("⚡ Señales", f"{metrics['signals']}", "0")
with col4:
    st.metric("💰 Trades", f"{metrics['trades']}", "0")

# Información de configuración y logs
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("⚙️ Configuración del Bot")
    bot_data = get_bot_data()
    if bot_data:
        st.write(f"**Modo:** {bot_data['mode'].upper()}")
        st.write(f"**Exchange:** {bot_data['exchange']}")
        st.write(f"**Símbolo:** {bot_data['symbol']}")
        st.write(f"**Timeframe:** {bot_data['timeframe']}")
        st.write(f"**Intervalo:** {bot_data['update_interval']}s")
    else:
        st.warning("No se pudo cargar la configuración")

with col2:
    st.subheader("📋 Logs Recientes")
    logs = get_recent_logs(10)
    if logs:
        for log in logs[-5:]:  # Mostrar solo los últimos 5
            if "ERROR" in log:
                st.error(log.strip())
            elif "WARNING" in log:
                st.warning(log.strip())
            elif "INFO" in log:
                st.info(log.strip())
            else:
                st.text(log.strip())
    else:
        st.warning("No hay logs disponibles")

# Auto-refresh
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(f"⏰ **Última actualización:** {datetime.now().strftime('%H:%M:%S')}")

with col2:
    if st.checkbox("🔄 Auto-actualizar (30s)"):
        time.sleep(30)
        st.rerun()




