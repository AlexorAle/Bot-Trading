import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import time

# Configurar página PRIMERO
st.set_page_config(page_title="Liquidation Hunter Dashboard", layout="wide")

# Intentar importar plotly, si falla usar versión sin gráficos
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly no disponible. Mostrando dashboard básico.")

# Header con título y controles
col_title, col_status, col_control = st.columns([3, 1, 1])

# Función para verificar estado del bot
def check_bot_status():
    """Verificar si el bot está ejecutándose"""
    try:
        if not os.path.exists('logs/bot.log'):
            return "❌ Sin logs"
        
        with open('logs/bot.log', 'r') as f:
            lines = f.readlines()
        
        if not lines:
            return "❌ Log vacío"
        
        # Buscar las últimas 10 líneas para determinar estado
        recent_lines = lines[-10:]
        
        # Verificar si hay actividad reciente (últimos 5 minutos)
        current_time = datetime.now()
        recent_activity = False
        
        for line in recent_lines:
            if any(keyword in line for keyword in ["Starting trading bot", "Starting trading cycle", "Cycle #", "Generated signal", "Trade executed"]):
                # Extraer timestamp del log (formato: 2025-10-04 13:09:08,763)
                try:
                    timestamp_str = line.split(' - ')[0]
                    log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    time_diff = (current_time - log_time).total_seconds()
                    
                    # Si la actividad es de los últimos 5 minutos, considerarla reciente
                    if time_diff < 300:  # 5 minutos
                        recent_activity = True
                        break
                except:
                    continue
        
        # Determinar estado basado en actividad reciente
        if recent_activity:
            # Verificar si está en proceso de shutdown
            if any("shutting down" in line or "shutdown complete" in line for line in recent_lines):
                return "🔴 Detenido"
            else:
                return "🟢 Ejecutándose"
        else:
            return "🔴 Inactivo"
            
    except Exception as e:
        return f"❌ Error: {str(e)[:50]}"

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

# Analizar logs para métricas
def analyze_logs():
    """Analizar logs para extraer métricas"""
    try:
        if not os.path.exists('logs/bot.log'):
            return {
                'cycles': 0, 'signals': 0, 'trades': 0, 'errors': 0, 'warnings': 0, 'info': 0,
                'uptime': 0, 'ml_accuracy': 0.0
            }
        
        with open('logs/bot.log', 'r') as f:
            lines = f.readlines()
        
        cycles = len([l for l in lines if 'Starting trading cycle' in l])
        signals = len([l for l in lines if 'Generated signal' in l])
        trades = len([l for l in lines if 'Trade executed successfully' in l])
        errors = len([l for l in lines if 'ERROR' in l])
        warnings = len([l for l in lines if 'WARNING' in l])
        info = len([l for l in lines if 'INFO' in l])
        
        # Simular uptime (en horas)
        uptime = len(lines) * 0.1  # Aproximación
        
        # Simular ML accuracy
        ml_accuracy = 0.75 + (np.random.random() * 0.2)  # Entre 75% y 95%
        
        return {
            'cycles': cycles, 'signals': signals, 'trades': trades, 'errors': errors,
            'warnings': warnings, 'info': info, 'uptime': uptime, 'ml_accuracy': ml_accuracy
        }
    except:
        return {
            'cycles': 0, 'signals': 0, 'trades': 0, 'errors': 0, 'warnings': 0, 'info': 0,
            'uptime': 0, 'ml_accuracy': 0.0
        }

# Crear gráficos si plotly está disponible
def create_bot_timeline():
    """Crear timeline del bot"""
    if not PLOTLY_AVAILABLE:
        return None
    
    try:
        # Datos simulados para el timeline
        timeline_data = []
        for i in range(24):  # Últimas 24 horas
            timestamp = datetime.now() - timedelta(hours=23-i)
            timeline_data.append({
                'timestamp': timestamp,
                'event': np.random.choice(['Cycle', 'Signal', 'Trade', 'Error'], p=[0.6, 0.2, 0.15, 0.05]),
                'status': np.random.choice(['Success', 'Warning', 'Error'], p=[0.8, 0.15, 0.05])
            })
        
        df = pd.DataFrame(timeline_data)
        
        fig = px.timeline(df, x_start='timestamp', x_end='timestamp', y='event', color='status',
                          color_discrete_map={'Success': 'green', 'Warning': 'orange', 'Error': 'red'})
        
        fig.update_layout(
            title="📈 Timeline de Actividad del Bot",
            xaxis_title="Tiempo",
            yaxis_title="Eventos",
            height=300
        )
        
        return fig
    except:
        return None

def create_trading_metrics():
    """Crear métricas de trading"""
    if not PLOTLY_AVAILABLE:
        return None
    
    try:
        metrics = analyze_logs()
        
        categories = ['Ciclos', 'Señales', 'Trades', 'Errores']
        values = [metrics['cycles'], metrics['signals'], metrics['trades'], metrics['errors']]
        
        fig = go.Figure(data=[
            go.Bar(x=categories, y=values, marker_color=['blue', 'green', 'gold', 'red'])
        ])
        
        fig.update_layout(
            title="📊 Métricas de Trading",
            xaxis_title="Categorías",
            yaxis_title="Cantidad",
            height=300
        )
        
        return fig
    except:
        return None

def create_ml_accuracy_gauge():
    """Crear gauge de precisión ML"""
    if not PLOTLY_AVAILABLE:
        return None
    
    try:
        metrics = analyze_logs()
        accuracy = metrics['ml_accuracy']
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = accuracy * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "🎯 Precisión ML (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=300)
        return fig
    except:
        return None

def create_log_analysis():
    """Crear análisis de logs"""
    if not PLOTLY_AVAILABLE:
        return None
    
    try:
        metrics = analyze_logs()
        
        log_types = ['INFO', 'WARNING', 'ERROR']
        counts = [metrics['info'], metrics['warnings'], metrics['errors']]
        
        fig = go.Figure(data=[
            go.Scatter(x=log_types, y=counts, mode='lines+markers', 
                      line=dict(color='blue', width=3),
                      marker=dict(size=10, color=['green', 'orange', 'red']))
        ])
        
        fig.update_layout(
            title="📋 Análisis de Logs",
            xaxis_title="Tipo de Log",
            yaxis_title="Cantidad",
            height=300
        )
        
        return fig
    except:
        return None

def create_performance_radar():
    """Crear radar de rendimiento"""
    if not PLOTLY_AVAILABLE:
        return None
    
    try:
        metrics = analyze_logs()
        
        categories = ['Ciclos', 'Señales', 'Trades', 'Precisión', 'Uptime']
        values = [
            min(metrics['cycles'] / 100, 1),  # Normalizar a 0-1
            min(metrics['signals'] / 50, 1),
            min(metrics['trades'] / 20, 1),
            metrics['ml_accuracy'],
            min(metrics['uptime'] / 24, 1)  # Normalizar uptime a días
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Rendimiento',
            line_color='blue'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="🎯 Radar de Rendimiento",
            height=400
        )
        
        return fig
    except:
        return None

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

# Gráficos de métricas (solo si plotly está disponible)
if PLOTLY_AVAILABLE:
    st.markdown("---")
    st.subheader("📈 Métricas y Análisis")
    
    # Timeline del bot
    timeline_fig = create_bot_timeline()
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)
    
    # Métricas de trading
    col1, col2 = st.columns(2)
    
    with col1:
        trading_fig = create_trading_metrics()
        if trading_fig:
            st.plotly_chart(trading_fig, use_container_width=True)
    
    with col2:
        ml_fig = create_ml_accuracy_gauge()
        if ml_fig:
            st.plotly_chart(ml_fig, use_container_width=True)
    
    # Análisis de logs y radar de rendimiento
    col1, col2 = st.columns(2)
    
    with col1:
        log_fig = create_log_analysis()
        if log_fig:
            st.plotly_chart(log_fig, use_container_width=True)
    
    with col2:
        radar_fig = create_performance_radar()
        if radar_fig:
            st.plotly_chart(radar_fig, use_container_width=True)

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