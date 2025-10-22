import streamlit as st
import requests
import subprocess
import os
import time
from datetime import datetime
import psutil
import pandas as pd
from investment_manager import investment_manager

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
    """Verifica si el bot está ejecutándose (soporta Windows y Linux)"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_name = proc.info.get('name', '')
                # Soportar tanto Windows (python.exe) como Linux (python, python3)
                if proc_name in ['python.exe', 'python', 'python3']:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'paper_trading_main.py' in cmdline:
                        return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None
    except Exception as e:
        return False, None

def get_metrics():
    """Obtiene métricas del bot desde Prometheus"""
    try:
        response = requests.get("http://127.0.0.1:8080/metrics", timeout=5)
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
    """Lee las últimas 5 líneas del log"""
    try:
        log_file = "backtrader_engine/logs/paper_trading.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-5:] if len(lines) > 5 else lines
        return []
    except Exception as e:
        return []

def start_bot():
    """Inicia el bot de trading"""
    try:
        # Buscar proceso de paper_trading_main.py
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'paper_trading_main.py' in ' '.join(cmdline):
                    return False  # Ya está corriendo
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Usar el entorno virtual del bot
        venv_python = os.path.join(os.getcwd(), "venv", "bin", "python")
        bot_script = os.path.join(os.getcwd(), "backtrader_engine", "paper_trading_main.py")
        bot_dir = os.path.join(os.getcwd(), "backtrader_engine")
        
        if not os.path.exists(bot_script):
            st.error(f"Script no encontrado: {bot_script}")
            return False
        
        if not os.path.exists(venv_python):
            # Si no hay venv, usar python3 del sistema
            venv_python = "python3"
        
        # Iniciar proceso en background
        subprocess.Popen(
            [venv_python, bot_script],
            cwd=bot_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        time.sleep(2)  # Esperar a que inicie
        return True
    except Exception as e:
        st.error(f"Error iniciando bot: {e}")
        return False

def stop_bot():
    """Detiene el bot de trading"""
    try:
        # Buscar y detener proceso de paper_trading_main.py
        found = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'paper_trading_main.py' in ' '.join(cmdline):
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        proc.kill()
                    found = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return found
    except Exception as e:
        st.error(f"Error deteniendo bot: {e}")
        return False

def check_service_status(url, timeout=3):
    """Verifica el estado de un servicio"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

# Header principal
st.markdown("<h1 style='text-align: center;'>🤖 COMMAND CENTER</h1>", unsafe_allow_html=True)
st.markdown("---")

# ========================================
# PANEL SUPERIOR: ESTADO DE TODOS LOS SERVICIOS
# ========================================
st.markdown("## 📊 System Status Overview")

# Obtener estados
bot_running, bot_pid = is_bot_running()
investment_status = investment_manager.get_status()
prometheus_status = check_service_status("http://127.0.0.1:9090")
grafana_status = check_service_status("http://127.0.0.1:3000")
metrics_api_status = check_service_status("http://127.0.0.1:8080/metrics")

# Grid de servicios (6 columnas)
service_cols = st.columns(6)

services_data = [
    {"name": "Trading Bot", "status": bot_running, "icon": "🤖", "port": "-"},
    {"name": "Investment Backend", "status": investment_status['backend']['status'] == 'running', "icon": "🔧", "port": "8000"},
    {"name": "Investment Frontend", "status": investment_status['frontend']['status'] == 'running', "icon": "🌐", "port": "3000"},
    {"name": "Prometheus", "status": prometheus_status, "icon": "📊", "port": "9090"},
    {"name": "Grafana", "status": grafana_status, "icon": "📈", "port": "3000"},
    {"name": "Metrics API", "status": metrics_api_status, "icon": "🔌", "port": "8080"},
]

for idx, (col, service) in enumerate(zip(service_cols, services_data)):
    with col:
        status_emoji = "🟢" if service["status"] else "🔴"
        status_color = "#10b981" if service["status"] else "#ef4444"
        status_text = "ONLINE" if service["status"] else "OFFLINE"
        
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div style="font-size: 2rem;">{service["icon"]}</div>
            <div style="font-size: 0.75rem; color: rgba(255, 255, 255, 0.7); margin: 5px 0;">
                {service["name"]}
            </div>
            <div style="font-size: 1.5rem;">{status_emoji}</div>
            <div style="color: {status_color}; font-size: 0.7rem; font-weight: 600;">
                {status_text}
            </div>
            {f'<div style="font-size: 0.65rem; color: rgba(255, 255, 255, 0.5);">:{service["port"]}</div>' if service["port"] != "-" else ''}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ========================================
# PANEL INFERIOR: BOT DE TRADING (izq) | LOGS (der)
# ========================================
main_col_left, main_col_right = st.columns([1, 1])

# ========================================
# COLUMNA IZQUIERDA: BOT DE TRADING
# ========================================
with main_col_left:
    st.markdown("## 🤖 Trading Bot Control")
    
    # Estado del bot y métricas principales
    bot_running, bot_pid = is_bot_running()
    metrics = get_metrics()
    
    # Fila superior: Estado y métricas principales
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if bot_running:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">⚡ Bot Status</div>
                <div style="display: flex; align-items: center; margin-top: 15px;">
                    <span class="status-active"></span>
                    <span style="color: #10b981; font-size: 1.5rem; font-weight: 600;">ONLINE</span>
                </div>
                <div style="color: rgba(255,255,255,0.6); font-size: 0.8rem; margin-top: 5px;">
                    PID: """ + str(bot_pid) + """
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
    
    # Segunda fila de métricas
    col3, col4 = st.columns([1, 1])
    
    with col3:
        eth_price = float(metrics.get('paper_current_price_ethusdt', '4000'))
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
    
    # Control Panel
    st.markdown("### 🎮 Control Panel")
    
    control_col1, control_col2, control_col3 = st.columns(3)
    
    with control_col1:
        if bot_running:
            if st.button("🛑 STOP BOT", type="secondary", use_container_width=True, key="stop_trading"):
                with st.spinner("Deteniendo bot..."):
                    if stop_bot():
                        st.success("✅ Bot detenido")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Error deteniendo bot")
        else:
            if st.button("🚀 START BOT", type="primary", use_container_width=True, key="start_trading"):
                with st.spinner("Iniciando bot..."):
                    if start_bot():
                        st.success("✅ Bot iniciado")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Error iniciando bot")
    
    with control_col2:
        if st.button("🔄 REFRESH", use_container_width=True, key="refresh_trading"):
            st.rerun()
    
    with control_col3:
        auto_refresh = st.toggle("⚡ Auto-refresh", value=False, key="auto_refresh_trading")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Modo de trading
    st.markdown("### 🎯 Trading Mode")
    mode_col1, mode_col2 = st.columns(2)
    
    with mode_col1:
        demo_selected = st.button("📄 PAPER TRADING", use_container_width=True, type="primary", key="mode_paper")
    with mode_col2:
        live_selected = st.button("🚀 LIVE TRADING", use_container_width=True, key="mode_live")
    
    if demo_selected or not live_selected:
        st.success("📄 **MODO DEMO ACTIVO**")
    else:
        st.error("⚠️ **MODO LIVE**")

# ========================================
# COLUMNA DERECHA: LOGS DETALLADOS
# ========================================
with main_col_right:
    st.markdown("## 📋 System Logs")
    
    # Tabs para diferentes logs
    log_tabs = st.tabs(["🤖 Trading Bot", "🔧 Investment Backend", "🌐 Investment Frontend"])
    
    # Tab 1: Trading Bot Logs
    with log_tabs[0]:
        trading_logs = read_logs()
        if trading_logs:
            log_text = "".join(trading_logs[-20:])  # Últimas 20 líneas
            st.code(log_text, language="log", line_numbers=False)
        else:
            st.info("No logs available for Trading Bot")
        
        if st.button("📥 Download Full Log", key="download_trading_log"):
            try:
                log_file = "backtrader_engine/logs/paper_trading.log"
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        st.download_button(
                            label="💾 Download",
                            data=f.read(),
                            file_name="trading_bot.log",
                            mime="text/plain"
                        )
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Tab 2: Investment Backend Logs
    with log_tabs[1]:
        backend_log_file = "/home/alex/proyectos/investment-dashboard/logs/backend.log"
        if os.path.exists(backend_log_file):
            with open(backend_log_file, 'r') as f:
                lines = f.readlines()
                log_text = "".join(lines[-20:])  # Últimas 20 líneas
                st.code(log_text, language="log", line_numbers=False)
        else:
            st.info("No logs available for Investment Backend")
    
    # Tab 3: Investment Frontend Logs
    with log_tabs[2]:
        frontend_log_file = "/home/alex/proyectos/investment-dashboard/logs/frontend.log"
        if os.path.exists(frontend_log_file):
            with open(frontend_log_file, 'r') as f:
                lines = f.readlines()
                log_text = "".join(lines[-20:])  # Últimas 20 líneas
                st.code(log_text, language="log", line_numbers=False)
        else:
            st.info("No logs available for Investment Frontend")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Investment Dashboard Control (compacto)
    st.markdown("### 💼 Investment Dashboard Control")
    
    # Obtener estado
    investment_status = investment_manager.get_status()
    overall_status = investment_status['overall_status']
    backend_info = investment_status['backend']
    frontend_info = investment_status['frontend']
    
    # Estado General (compacto)
    if overall_status == "running":
        status_emoji = "🟢"
        status_text = "RUNNING"
    elif overall_status == "partial":
        status_emoji = "🟡"
        status_text = "PARTIAL"
    else:
        status_emoji = "🔴"
        status_text = "OFFLINE"
    
    st.markdown(f"**Status:** {status_emoji} {status_text}")
    
    # Status compacto de servicios
    backend_status_emoji = "🟢" if backend_info.get('status') == 'running' else "🔴"
    frontend_status_emoji = "🟢" if frontend_info.get('status') == 'running' else "🔴"
    
    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        st.markdown(f"🔧 Backend: {backend_status_emoji}")
    with col_inv2:
        st.markdown(f"🌐 Frontend: {frontend_status_emoji}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Control Panel
    st.markdown("### 🎮 Control Panel")
    
    inv_col1, inv_col2, inv_col3 = st.columns(3)
    
    with inv_col1:
        if overall_status != "stopped":
            if st.button("🛑 STOP", type="secondary", use_container_width=True, key="stop_investment"):
                with st.spinner("Deteniendo Investment Dashboard..."):
                    success, msg = investment_manager.stop()
                    if success:
                        st.success(f"✅ {msg}")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        else:
            if st.button("▶️ START", type="primary", use_container_width=True, key="start_investment"):
                with st.spinner("Iniciando Investment Dashboard..."):
                    success, msg = investment_manager.start()
                    if success:
                        st.success(f"✅ {msg}")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
    
    with inv_col2:
        if st.button("🔄 RESTART", use_container_width=True, key="restart_investment"):
            with st.spinner("Reiniciando Investment Dashboard..."):
                success, msg = investment_manager.restart()
                if success:
                    st.success(f"✅ {msg}")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
    
    with inv_col3:
        if st.button("🔄 REFRESH", use_container_width=True, key="refresh_investment"):
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Logs Recientes
    st.markdown("### 📋 Logs Recientes")
    
    tab_backend, tab_frontend = st.tabs(["Backend", "Frontend"])
    
    with tab_backend:
        backend_logs = investment_manager.get_logs("backend", lines=10)
        st.code(backend_logs, language=None)
    
    with tab_frontend:
        frontend_logs = investment_manager.get_logs("frontend", lines=10)
        st.code(frontend_logs, language=None)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Enlaces Directos
    st.markdown("### 🌐 Enlaces Directos")
    
    backend_url = "http://82.25.101.32:8000"
    frontend_url = "http://82.25.101.32:3000"
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="margin: 10px 0;">
            🔗 <strong>Backend:</strong><br>
            <a href="{backend_url}" target="_blank" style="color: #667eea;">{backend_url}</a>
        </div>
        <div style="margin: 10px 0;">
            🔗 <strong>Frontend:</strong><br>
            <a href="{frontend_url}" target="_blank" style="color: #667eea;">{frontend_url}</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
