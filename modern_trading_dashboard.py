import streamlit as st
import requests
import subprocess
import os
import time
from datetime import datetime
import psutil
import pandas as pd

# Configuración de página con tema oscuro
st.set_page_config(
    page_title="Trading Bot Dashboard", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para diseño moderno
st.markdown("""
<style>
    /* Tema oscuro principal */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Tarjetas de métricas personalizadas */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Botones modernos */
    .stButton > button {
        border-radius: 10px;
        border: none;
        padding: 12px 30px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(0, 0, 0, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(0, 0, 0, 0.3);
    }
    
    /* Status indicators */
    .status-active {
        display: inline-block;
        width: 12px;
        height: 12px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
        margin-right: 8px;
    }
    
    .status-inactive {
        display: inline-block;
        width: 12px;
        height: 12px;
        background: #ef4444;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Títulos con estilo */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 30px;
    }
    
    /* Ocultar elementos de streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Contenedor de logs minimalista */
    .log-container {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
        padding: 15px;
        max-height: 200px;
        overflow-y: auto;
        font-family: 'Monaco', monospace;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

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
                return lines[-5:] if len(lines) > 5 else lines  # Solo últimas 5 líneas
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

def check_service_status(url, timeout=3):
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

# Header principal
st.markdown("# 🤖 Trading Bot Command Center")
st.markdown("---")

# Estado del bot y métricas principales
bot_running, bot_pid = is_bot_running()
metrics = get_metrics()

# Fila superior: Estado y controles principales
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if bot_running:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">⚡ Bot Status</div>
            <div style="display: flex; align-items: center; margin-top: 15px;">
                <span class="status-active"></span>
                <span style="color: #10b981; font-size: 1.5rem; font-weight: 600;">ONLINE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">⚡ Bot Status</div>
            <div style="display: flex; align-items: center; margin-top: 15px;">
                <span class="status-inactive"></span>
                <span style="color: #ef4444; font-size: 1.5rem; font-weight: 600;">OFFLINE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    signals = metrics.get('paper_signals_generated_total', '0')
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">📊 Señales</div>
        <div class="metric-value">{signals}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    eth_price = float(metrics.get('paper_current_price_ethusdt', '0'))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">💎 ETH/USDT</div>
        <div class="metric-value">${eth_price:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    balance = float(metrics.get('paper_balance_usd', '10000'))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">💰 Balance</div>
        <div class="metric-value">${balance:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Sección de controles y configuración
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### 🎮 Control Panel")
    
    control_col1, control_col2, control_col3 = st.columns(3)
    
    with control_col1:
        if bot_running:
            if st.button("🛑 STOP BOT", type="secondary", use_container_width=True):
                if stop_bot():
                    st.success("✅ Comando enviado")
                    time.sleep(2)
                    st.rerun()
        else:
            if st.button("🚀 START BOT", type="primary", use_container_width=True):
                if start_bot():
                    st.success("✅ Bot iniciando...")
                    time.sleep(2)
                    st.rerun()
    
    with control_col2:
        if st.button("🔄 REFRESH", use_container_width=True):
            st.rerun()
    
    with control_col3:
        auto_refresh = st.toggle("⚡ Auto-refresh", value=False)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Modo de trading
    st.markdown("### 🎯 Trading Mode")
    mode_col1, mode_col2 = st.columns(2)
    
    with mode_col1:
        demo_selected = st.button("📄 PAPER TRADING", use_container_width=True, type="primary")
    with mode_col2:
        live_selected = st.button("🚀 LIVE TRADING", use_container_width=True)
    
    if demo_selected or not live_selected:
        st.success("📄 **MODO DEMO ACTIVO** | Sin riesgo real | Balance simulado: $10,000")
    else:
        st.error("⚠️ **MODO LIVE** | Trading real con dinero real")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Estrategias activas
    st.markdown("### 📈 Active Strategies")
    
    strategies = [
        {"name": "Volatility Breakout", "status": "active", "signals": 12},
        {"name": "RSI EMA Momentum", "status": "active", "signals": 8},
        {"name": "MACD Crossover", "status": "active", "signals": 5},
        {"name": "Bollinger Bands", "status": "active", "signals": 3},
        {"name": "Support/Resistance", "status": "active", "signals": 2}
    ]
    
    for strategy in strategies:
        col_name, col_status, col_signals = st.columns([3, 1, 1])
        with col_name:
            st.markdown(f"**{strategy['name']}**")
        with col_status:
            st.markdown("🟢 Active" if bot_running else "⚪ Paused")
        with col_signals:
            st.markdown(f"📊 {strategy['signals']}")

with col_right:
    st.markdown("### 🔧 System Health")
    
    # Servicios
    services = {
        "Prometheus": ("http://localhost:9090", "📊"),
        "Grafana": ("http://localhost:3000", "📈"),
        "Metrics API": ("http://localhost:8080/metrics", "🔌")
    }
    
    for service_name, (url, icon) in services.items():
        status = check_service_status(url)
        if status:
            st.success(f"{icon} {service_name}")
        else:
            st.error(f"{icon} {service_name}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Información del sistema
    st.markdown("### 💻 System Info")
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        st.metric("CPU Usage", f"{cpu_percent}%", delta=None)
        st.metric("RAM Usage", f"{memory.percent}%", delta=None)
        st.metric("Uptime", f"{bot_pid if bot_pid else 'N/A'}")
    except:
        st.info("System info not available")

# Logs minimalistas al final
st.markdown("---")
with st.expander("📜 Recent Logs (Last 5 entries)", expanded=False):
    logs = read_logs()
    if logs:
        log_text = "".join(logs)
        st.code(log_text, language=None)
    else:
        st.info("No logs available")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: rgba(255,255,255,0.4); font-size: 0.85rem;'>
    🤖 Trading Bot Dashboard v2.0 | Built with Streamlit | Last update: """ + datetime.now().strftime("%H:%M:%S") + """
</div>
""", unsafe_allow_html=True)

# Auto-refresh
if auto_refresh:
    time.sleep(10)
    st.rerun()
