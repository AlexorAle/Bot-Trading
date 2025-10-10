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

# Importar controlador del bot
try:
    from bot_controller import bot_controller
    BOT_CONTROLLER_AVAILABLE = True
except ImportError:
    BOT_CONTROLLER_AVAILABLE = False

# Header con título y controles
col_title, col_status, col_control = st.columns([3, 1, 1])

# Función para verificar estado del bot
def check_bot_status():
    """Verificar si el bot está ejecutándose"""
    try:
        # Usar controlador del bot si está disponible
        if BOT_CONTROLLER_AVAILABLE:
            status = bot_controller.get_bot_status()
            if status.get("running", False):
                return "🟢 Ejecutándose"
            else:
                return "🔴 Inactivo"
        
        # Fallback: verificar por logs
        if not os.path.exists('logs/bot.log'):
            return "❌ Sin logs"
        
        with open('logs/bot.log', 'r', encoding='utf-8') as f:
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
    
    # Botones de control del bot
    if BOT_CONTROLLER_AVAILABLE:
        if "Ejecutándose" in bot_status or "Procesando" in bot_status:
            if st.button("🛑 Detener", key="stop_bot"):
                with st.spinner("Deteniendo bot..."):
                    result = bot_controller.stop_bot()
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
        else:
            if st.button("▶️ Iniciar", key="start_bot"):
                with st.spinner("Iniciando bot..."):
                    result = bot_controller.start_bot()
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
    else:
        # Fallback si no hay controlador
        if "Ejecutándose" in bot_status or "Procesando" in bot_status:
            if st.button("🛑 Detener", key="stop_bot"):
                st.warning("Controlador del bot no disponible")
        else:
            if st.button("▶️ Iniciar", key="start_bot"):
                st.warning("Controlador del bot no disponible")

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
        
        with open('logs/bot.log', 'r', encoding='utf-8') as f:
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
            with open('logs/bot.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-n:] if len(lines) >= n else lines
        return []
    except:
        return []

# Analizar logs para métricas
def analyze_logs():
    """Analizar logs para extraer métricas reales"""
    try:
        if not os.path.exists('logs/bot.log'):
            return {
                'cycles': 0, 'signals': 0, 'trades': 0, 'errors': 0, 'warnings': 0, 'info': 0,
                'uptime': 0, 'ml_accuracy': 0.0, 'start_time': None, 'last_activity': None
            }
        
        with open('logs/bot.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Contar eventos reales
        cycles = len([l for l in lines if 'Starting trading cycle' in l])
        signals = len([l for l in lines if 'Generated signal' in l or 'Trading signal generated' in l])
        trades = len([l for l in lines if 'Trade executed successfully' in l or 'Order placed' in l])
        errors = len([l for l in lines if 'ERROR' in l])
        warnings = len([l for l in lines if 'WARNING' in l])
        info = len([l for l in lines if 'INFO' in l])
        
        # Calcular uptime real basado en timestamps
        start_time = None
        last_activity = None
        
        for line in lines:
            try:
                if ' - ' in line:
                    timestamp_str = line.split(' - ')[0]
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    
                    if start_time is None or timestamp < start_time:
                        start_time = timestamp
                    if last_activity is None or timestamp > last_activity:
                        last_activity = timestamp
            except:
                continue
        
        # Calcular uptime real en horas
        if start_time and last_activity:
            uptime = (last_activity - start_time).total_seconds() / 3600
        else:
            uptime = 0
        
        # Calcular ML accuracy basado en predicciones exitosas vs fallidas
        ml_predictions = len([l for l in lines if 'ML prediction' in l])
        ml_errors = len([l for l in lines if 'Error making prediction' in l])
        
        if ml_predictions > 0:
            ml_accuracy = max(0.0, (ml_predictions - ml_errors) / ml_predictions)
        else:
            ml_accuracy = 0.0
        
        return {
            'cycles': cycles, 'signals': signals, 'trades': trades, 'errors': errors,
            'warnings': warnings, 'info': info, 'uptime': uptime, 'ml_accuracy': ml_accuracy,
            'start_time': start_time, 'last_activity': last_activity
        }
    except Exception as e:
        return {
            'cycles': 0, 'signals': 0, 'trades': 0, 'errors': 0, 'warnings': 0, 'info': 0,
            'uptime': 0, 'ml_accuracy': 0.0, 'start_time': None, 'last_activity': None
        }

# Crear gráficos si plotly está disponible
def create_bot_timeline():
    """Crear timeline del bot con datos reales de los logs"""
    if not PLOTLY_AVAILABLE:
        return None
    
    try:
        timeline_data = []
        
        # Leer logs reales
        if os.path.exists('logs/bot.log'):
            with open('logs/bot.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Procesar cada línea del log
            for line in lines:
                try:
                    # Extraer timestamp (formato: 2025-10-06 10:26:28,799)
                    if ' - ' in line and ' - INFO - ' in line:
                        timestamp_str = line.split(' - ')[0]
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        # Solo incluir eventos de los últimos 30 días
                        if timestamp >= datetime.now() - timedelta(days=30):
                            event_type = 'Info'
                            status = 'Success'
                            
                            # Determinar tipo de evento y status
                            if 'Starting trading cycle' in line:
                                event_type = 'Cycle'
                                status = 'Success'
                            elif 'Generated signal' in line or 'Trading signal generated' in line:
                                event_type = 'Signal'
                                status = 'Success'
                            elif 'Trade executed' in line or 'Order placed' in line:
                                event_type = 'Trade'
                                status = 'Success'
                            elif 'ERROR' in line:
                                event_type = 'Error'
                                status = 'Error'
                            elif 'WARNING' in line:
                                event_type = 'Warning'
                                status = 'Warning'
                            elif 'Dashboard started' in line:
                                event_type = 'Dashboard'
                                status = 'Success'
                            elif 'Starting trading bot' in line:
                                event_type = 'Startup'
                                status = 'Success'
                            
                            timeline_data.append({
                                'timestamp': timestamp,
                                'event': event_type,
                                'status': status
                            })
                            
                except Exception as e:
                    continue
        
        # Si no hay datos reales, crear algunos datos de ejemplo para los últimos 30 días
        if not timeline_data:
            for i in range(30):  # Últimos 30 días
                timestamp = datetime.now() - timedelta(days=29-i)
                # Agregar algunos eventos de ejemplo
                timeline_data.append({
                    'timestamp': timestamp,
                    'event': 'Cycle',
                    'status': 'Success'
                })
        
        if timeline_data:
            df = pd.DataFrame(timeline_data)
            
            # Crear el gráfico timeline
            fig = px.timeline(df, x_start='timestamp', x_end='timestamp', y='event', color='status',
                              color_discrete_map={'Success': 'green', 'Warning': 'orange', 'Error': 'red'})
            
            fig.update_layout(
                title="📈 Timeline de Actividad del Bot (Últimos 30 días)",
                xaxis_title="Tiempo",
                yaxis_title="Eventos",
                height=400,
                xaxis=dict(
                    range=[datetime.now() - timedelta(days=30), datetime.now()]
                )
            )
            
            return fig
        else:
            return None
            
    except Exception as e:
        st.error(f"Error creando timeline: {e}")
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
    """Crear radar de rendimiento con datos reales"""
    if not PLOTLY_AVAILABLE:
        return None
    
    try:
        metrics = analyze_logs()
        
        # Calcular métricas reales basadas en los logs
        total_events = metrics['cycles'] + metrics['signals'] + metrics['trades']
        error_rate = metrics['errors'] / max(total_events, 1)
        success_rate = 1 - error_rate
        
        # Métricas normalizadas basadas en datos reales
        categories = ['Ciclos', 'Señales', 'Trades', 'Precisión ML', 'Tasa Éxito']
        values = [
            min(metrics['cycles'] / 10, 1),  # Normalizar ciclos (máximo 10 = 100%)
            min(metrics['signals'] / 5, 1),  # Normalizar señales (máximo 5 = 100%)
            min(metrics['trades'] / 3, 1),   # Normalizar trades (máximo 3 = 100%)
            metrics['ml_accuracy'],          # Precisión ML real
            success_rate                     # Tasa de éxito real
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
            title="🎯 Radar de Rendimiento (Datos Reales)",
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
