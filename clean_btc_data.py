#!/usr/bin/env python3
"""
Script de limpieza para dataset BTC
Convierte datos de Kaggle al formato requerido por Backtrader
"""

import pandas as pd
import os
from pathlib import Path

def clean_btc_dataset():
    """Limpia y convierte el dataset BTC para Backtrader"""
    
    # 📂 Rutas de archivos
    input_file = r"C:\Mis_Proyectos\BOT Trading\backtrader_engine\data\btc_15m_data_2018_to_2025.csv"
    output_file = r"C:\Mis_Proyectos\BOT Trading\backtrader_engine\data\BTCUSDT_15min.csv"
    
    print("🔍 Verificando archivo de entrada...")
    
    # Verificar que el archivo existe
    if not os.path.exists(input_file):
        print(f"❌ ERROR: No se encontró el archivo {input_file}")
        return False
    
    try:
        # 📥 Cargar el CSV original desde Kaggle
        print("📥 Cargando dataset original...")
        df = pd.read_csv(input_file)
        
        print(f"✅ Dataset cargado: {len(df)} registros")
        print(f"📊 Columnas disponibles: {list(df.columns)}")
        
        # 🧼 Limpiar y renombrar columnas
        print("🧼 Limpiando y convirtiendo columnas...")
        df_clean = pd.DataFrame()
        
        # Convertir string de fecha a datetime (ya está en formato correcto)
        df_clean['datetime'] = pd.to_datetime(df['Open time'])
        df_clean['open'] = df['Open']
        df_clean['high'] = df['High']
        df_clean['low'] = df['Low']
        df_clean['close'] = df['Close']
        df_clean['volume'] = df['Volume']
        
        # Verificar que no hay valores nulos
        print("🔍 Verificando datos...")
        null_counts = df_clean.isnull().sum()
        if null_counts.sum() > 0:
            print(f"⚠️  Valores nulos encontrados: {null_counts}")
            df_clean = df_clean.dropna()
            print(f"✅ Datos limpiados: {len(df_clean)} registros válidos")
        
        # Verificar rango de fechas
        print(f"📅 Rango de fechas: {df_clean['datetime'].min()} a {df_clean['datetime'].max()}")
        
        # 🗑️ Opcional: Filtrar solo últimos 6 meses si se desea
        # df_clean = df_clean[df_clean['datetime'] >= "2025-04-01"]
        
        # 💾 Guardar archivo limpio
        print(f"💾 Guardando archivo limpio en: {output_file}")
        df_clean.to_csv(output_file, index=False)
        
        print("✅ Dataset limpio y guardado correctamente.")
        print(f"📊 Registros finales: {len(df_clean)}")
        print(f"📅 Período: {df_clean['datetime'].min()} a {df_clean['datetime'].max()}")
        
        # Verificar formato final
        print("\n🔍 Verificando formato final...")
        sample = df_clean.head(3)
        print("📋 Muestra de datos:")
        print(sample.to_string(index=False))
        
        print(f"\n✅ Archivo listo para Backtrader: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR durante la limpieza: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando limpieza de dataset BTC...")
    success = clean_btc_dataset()
    
    if success:
        print("\n🎉 ¡Limpieza completada exitosamente!")
        print("📁 El archivo BTCUSDT_15min.csv está listo para usar con Backtrader")
    else:
        print("\n💥 Error en la limpieza. Revisa los mensajes anteriores.")
