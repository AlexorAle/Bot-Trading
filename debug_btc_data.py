#!/usr/bin/env python3
"""
Script de debug para verificar formato del dataset BTC
"""

import pandas as pd

def debug_btc_dataset():
    """Debug del dataset BTC para entender su formato"""
    
    input_file = r"C:\Mis_Proyectos\BOT Trading\backtrader_engine\data\btc_15m_data_2018_to_2025.csv"
    
    try:
        # Cargar dataset
        df = pd.read_csv(input_file)
        
        print("📊 INFORMACIÓN DEL DATASET:")
        print(f"Registros: {len(df)}")
        print(f"Columnas: {list(df.columns)}")
        
        print("\n🔍 MUESTRA DE DATOS:")
        print(df.head())
        
        print("\n📅 ANÁLISIS DE COLUMNA 'Open time':")
        print(f"Tipo: {df['Open time'].dtype}")
        print(f"Primeros 5 valores: {df['Open time'].head().tolist()}")
        print(f"Últimos 5 valores: {df['Open time'].tail().tolist()}")
        
        # Intentar diferentes conversiones
        print("\n🧪 PRUEBAS DE CONVERSIÓN:")
        
        # Prueba 1: Como string de fecha
        try:
            test_date = pd.to_datetime(df['Open time'].iloc[0])
            print(f"✅ Conversión directa: {test_date}")
        except Exception as e:
            print(f"❌ Conversión directa falló: {e}")
        
        # Prueba 2: Como timestamp en segundos
        try:
            test_timestamp = pd.to_datetime(df['Open time'].iloc[0], unit='s')
            print(f"✅ Conversión con unit='s': {test_timestamp}")
        except Exception as e:
            print(f"❌ Conversión con unit='s' falló: {e}")
        
        # Prueba 3: Como timestamp en milisegundos
        try:
            test_timestamp_ms = pd.to_datetime(df['Open time'].iloc[0], unit='ms')
            print(f"✅ Conversión con unit='ms': {test_timestamp_ms}")
        except Exception as e:
            print(f"❌ Conversión con unit='ms' falló: {e}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    debug_btc_dataset()
