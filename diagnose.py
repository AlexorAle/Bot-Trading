#!/usr/bin/env python3
"""
Script de diagnóstico para encontrar problemas con plotly y streamlit
"""

import sys
import os
import subprocess

print("🔍 DIAGNÓSTICO DEL SISTEMA")
print("=" * 50)

# 1. Verificar Python
print(f"🐍 Python ejecutable: {sys.executable}")
print(f"🐍 Python versión: {sys.version}")
print(f"🐍 Python path: {sys.path[:3]}...")

# 2. Verificar entorno virtual
venv_path = os.path.dirname(sys.executable)
print(f"📁 Entorno virtual: {venv_path}")
print(f"📁 ¿Es entorno virtual?: {'venv' in venv_path or 'Scripts' in venv_path}")

# 3. Verificar plotly
print("\n📊 VERIFICANDO PLOTLY:")
try:
    import plotly
    print(f"✅ Plotly importado correctamente")
    print(f"📊 Versión: {plotly.__version__}")
    print(f"📊 Ubicación: {plotly.__file__}")
    
    # Verificar submodules
    try:
        import plotly.graph_objects as go
        print("✅ plotly.graph_objects importado")
    except Exception as e:
        print(f"❌ Error importando plotly.graph_objects: {e}")
    
    try:
        import plotly.express as px
        print("✅ plotly.express importado")
    except Exception as e:
        print(f"❌ Error importando plotly.express: {e}")
        
except ImportError as e:
    print(f"❌ Error importando plotly: {e}")

# 4. Verificar streamlit
print("\n🌐 VERIFICANDO STREAMLIT:")
try:
    import streamlit as st
    print(f"✅ Streamlit importado correctamente")
    print(f"🌐 Versión: {st.__version__}")
    print(f"🌐 Ubicación: {st.__file__}")
except ImportError as e:
    print(f"❌ Error importando streamlit: {e}")

# 5. Verificar pandas y numpy
print("\n📈 VERIFICANDO DEPENDENCIAS:")
try:
    import pandas as pd
    print(f"✅ Pandas: {pd.__version__}")
except ImportError as e:
    print(f"❌ Error con pandas: {e}")

try:
    import numpy as np
    print(f"✅ Numpy: {np.__version__}")
except ImportError as e:
    print(f"❌ Error con numpy: {e}")

# 6. Verificar instalación de plotly
print("\n🔧 VERIFICANDO INSTALACIÓN DE PLOTLY:")
try:
    result = subprocess.run([sys.executable, "-m", "pip", "show", "plotly"], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print("✅ Plotly instalado correctamente:")
        print(result.stdout)
    else:
        print("❌ Plotly no encontrado en pip")
        print(result.stderr)
except Exception as e:
    print(f"❌ Error verificando plotly: {e}")

# 7. Verificar streamlit
print("\n🔧 VERIFICANDO INSTALACIÓN DE STREAMLIT:")
try:
    result = subprocess.run([sys.executable, "-m", "pip", "show", "streamlit"], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print("✅ Streamlit instalado correctamente:")
        print(result.stdout)
    else:
        print("❌ Streamlit no encontrado en pip")
        print(result.stderr)
except Exception as e:
    print(f"❌ Error verificando streamlit: {e}")

# 8. Probar importación completa del dashboard
print("\n🧪 PROBANDO IMPORTACIÓN DEL DASHBOARD:")
try:
    # Simular la importación del dashboard
    import streamlit as st
    import pandas as pd
    import numpy as np
    import os
    from datetime import datetime, timedelta
    import time
    
    # Intentar importar plotly
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        print("✅ Todas las importaciones del dashboard funcionan")
    except ImportError as e:
        print(f"❌ Error en importaciones del dashboard: {e}")
        
except Exception as e:
    print(f"❌ Error general en dashboard: {e}")

# 9. Verificar variables de entorno
print("\n🌍 VARIABLES DE ENTORNO:")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'No definido')}")
print(f"PATH: {os.environ.get('PATH', 'No definido')[:100]}...")

# 10. Verificar archivos del proyecto
print("\n📁 ARCHIVOS DEL PROYECTO:")
dashboard_exists = os.path.exists("dashboard.py")
print(f"📄 dashboard.py existe: {dashboard_exists}")
if dashboard_exists:
    with open("dashboard.py", "r") as f:
        lines = f.readlines()
        print(f"📄 Líneas en dashboard.py: {len(lines)}")
        # Buscar importaciones de plotly
        plotly_imports = [line for line in lines if "plotly" in line]
        print(f"📊 Líneas con plotly: {len(plotly_imports)}")
        for line in plotly_imports[:3]:  # Mostrar primeras 3
            print(f"   {line.strip()}")

print("\n" + "=" * 50)
print("🏁 DIAGNÓSTICO COMPLETADO")




