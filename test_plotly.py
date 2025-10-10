import streamlit as st
import sys
import os

# Configurar página PRIMERO
st.set_page_config(page_title="Test Plotly", layout="wide")

st.title("🔍 Test de Plotly - Diagnóstico")

# Logs de diagnóstico
st.subheader("📊 Información del Sistema")

st.write(f"**Python ejecutable:** {sys.executable}")
st.write(f"**Python path:** {sys.path[:3]}")

# Verificar plotly paso a paso
st.subheader("🧪 Test de Importación de Plotly")

try:
    st.write("1. Intentando importar plotly...")
    import plotly
    st.success(f"✅ Plotly importado - Versión: {plotly.__version__}")
    st.write(f"📁 Ubicación: {plotly.__file__}")
except Exception as e:
    st.error(f"❌ Error importando plotly: {e}")

try:
    st.write("2. Intentando importar plotly.graph_objects...")
    import plotly.graph_objects as go
    st.success("✅ plotly.graph_objects importado correctamente")
except Exception as e:
    st.error(f"❌ Error importando plotly.graph_objects: {e}")

try:
    st.write("3. Intentando importar plotly.express...")
    import plotly.express as px
    st.success("✅ plotly.express importado correctamente")
except Exception as e:
    st.error(f"❌ Error importando plotly.express: {e}")

# Test de gráfico simple
st.subheader("📈 Test de Gráfico Simple")

try:
    st.write("4. Creando gráfico simple...")
    
    # Crear datos simples
    import pandas as pd
    import numpy as np
    
    data = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 1, 5, 3]
    })
    
    # Crear gráfico con plotly
    fig = go.Figure(data=go.Scatter(x=data['x'], y=data['y'], mode='lines+markers'))
    fig.update_layout(title="Test Plotly - Gráfico Simple")
    
    st.plotly_chart(fig, use_container_width=True)
    st.success("✅ Gráfico plotly renderizado correctamente!")
    
except Exception as e:
    st.error(f"❌ Error creando gráfico: {e}")
    st.write(f"**Detalles del error:** {str(e)}")

# Test de gráfico con express
st.subheader("📊 Test de Gráfico con Express")

try:
    st.write("5. Creando gráfico con plotly.express...")
    
    # Crear datos
    data = pd.DataFrame({
        'category': ['A', 'B', 'C', 'D'],
        'value': [10, 20, 15, 25]
    })
    
    # Crear gráfico con express
    fig = px.bar(data, x='category', y='value', title="Test Plotly Express")
    
    st.plotly_chart(fig, use_container_width=True)
    st.success("✅ Gráfico plotly.express renderizado correctamente!")
    
except Exception as e:
    st.error(f"❌ Error creando gráfico express: {e}")
    st.write(f"**Detalles del error:** {str(e)}")

# Información adicional
st.subheader("🔧 Información Adicional")

st.write("**Variables de entorno:**")
st.write(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'No definido')}")

st.write("**Módulos instalados:**")
try:
    import pkg_resources
    installed_packages = [d.project_name for d in pkg_resources.working_set]
    plotly_related = [pkg for pkg in installed_packages if 'plotly' in pkg.lower()]
    st.write(f"Paquetes relacionados con plotly: {plotly_related}")
except:
    st.write("No se pudo obtener lista de paquetes")

st.write("**Test completado**")




