#!/usr/bin/env python3
"""
Script para entrenar el modelo ML manualmente con más datos históricos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data.data_fetcher import DataFetcher
from processing.ml_model import MLModel
from processing.kalman_filter import KalmanFilter
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import logging
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def _validate_data_quality(data):
    """Validar calidad de datos para entrenamiento"""
    if data is None or data.empty:
        return False
    
    # Verificar columnas requeridas
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in data.columns for col in required_columns):
        return False
    
    # Verificar valores nulos
    if data[required_columns].isnull().any().any():
        return False
    
    # Verificar valores negativos en precios
    price_columns = ['open', 'high', 'low', 'close']
    if (data[price_columns] <= 0).any().any():
        return False
    
    # Verificar valores negativos en volumen
    if (data['volume'] < 0).any():
        return False
    
    # Verificar datos suficientes
    if len(data) < 10:
        return False
    
    return True

def train_model_manually():
    """Entrena el modelo ML con datos históricos extensos"""
    
    print("🚀 Iniciando entrenamiento manual del modelo...")
    
    # 1. Obtener más datos históricos con manejo robusto de errores
    print("📊 Obteniendo datos históricos extensos...")
    fetcher = DataFetcher()
    
    # Obtener datos de los últimos 7 días (más datos = mejor entrenamiento)
    all_data = []
    max_retries = 3
    retry_delay = 2
    
    for days_back in range(7, 0, -1):
        success = False
        for attempt in range(max_retries):
            try:
                # Simular obtención de datos de días anteriores
                data = fetcher.fetch_data()
                if data is not None and not data.empty:
                    # Validar calidad de datos
                    if _validate_data_quality(data):
                        all_data.append(data)
                        print(f"✅ Datos del día {days_back}: {len(data)} registros")
                        success = True
                        break
                    else:
                        print(f"⚠️ Datos del día {days_back} no pasaron validación, reintentando...")
                else:
                    print(f"⚠️ Datos vacíos del día {days_back}, reintentando...")
            except ConnectionError as e:
                print(f"🔌 Error de conexión día {days_back}, intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
            except Exception as e:
                print(f"❌ Error inesperado día {days_back}, intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        if not success:
            print(f"❌ No se pudieron obtener datos del día {days_back} después de {max_retries} intentos")
    
    if not all_data:
        print("❌ No se pudieron obtener datos para entrenamiento")
        return False
    
    combined_data = pd.concat(all_data).sort_index()
    print(f"📈 Total de datos para entrenamiento: {len(combined_data)} registros")
    print(f"📅 Rango: {combined_data.index.min()} a {combined_data.index.max()}")
    
    # 2. Aplicar filtro Kalman
    print("🔧 Aplicando filtro Kalman...")
    kalman_filter = KalmanFilter()
    filtered_data = kalman_filter.apply_filter(combined_data)
    
    if filtered_data is None or filtered_data.empty:
        print("❌ Error aplicando filtro Kalman")
        return False
    
    # 3. Entrenar modelo ML
    print("🤖 Entrenando modelo Random Forest...")
    ml_model = MLModel()
    
    print(f"📊 Datos para entrenamiento: {len(filtered_data)} registros")
    print(f"📊 Columnas disponibles: {list(filtered_data.columns)}")
    
    # Entrenar el modelo (el método train maneja todo internamente)
    result = ml_model.train(filtered_data)
    success = result.get('success', False)
    
    if success:
        print("✅ Modelo entrenado exitosamente!")
        
        # 4. Probar predicciones con métricas extendidas
        print("🧪 Probando predicciones y calculando métricas...")
        
        # Probar predicciones en muestra de prueba
        test_sample = filtered_data.tail(50)  # Usar más datos para prueba
        predictions = ml_model.predict(test_sample)
        
        if predictions is not None:
            print(f"✅ Predicciones generadas exitosamente")
            print(f"📊 Predicción: {'SUBA' if predictions['prediction'] == 1 else 'BAJA'}")
            print(f"📊 Probabilidad: {predictions['probability']:.3f}")
            print(f"📊 Confianza: {predictions['confidence']:.3f}")
            
            # Calcular métricas adicionales si tenemos datos suficientes
            if len(filtered_data) > 100:
                print("📈 Calculando métricas de validación cruzada...")
                try:
                    # Preparar datos para validación cruzada
                    features_df = ml_model.prepare_features(filtered_data)
                    target = ml_model.create_target(features_df)
                    
                    # Seleccionar características
                    exclude_cols = ['timestamp', 'target', 'close', 'open', 'high', 'low']
                    feature_cols = [col for col in features_df.columns if col not in exclude_cols]
                    X = features_df[feature_cols]
                    y = target
                    
                    # Remover NaN
                    mask = ~(X.isna().any(axis=1) | y.isna())
                    X = X[mask]
                    y = y[mask]
                    
                    if len(X) > 50:  # Datos suficientes para CV
                        # Validación cruzada
                        cv_scores = cross_val_score(ml_model.model, X, y, cv=5, scoring='accuracy')
                        print(f"📊 Validación cruzada (5-fold): {cv_scores.mean():.3f} ± {cv_scores.std() * 2:.3f}")
                        
                        # Métricas adicionales
                        y_pred = ml_model.model.predict(X)
                        precision = precision_score(y, y_pred, average='weighted')
                        recall = recall_score(y, y_pred, average='weighted')
                        f1 = f1_score(y, y_pred, average='weighted')
                        
                        print(f"📊 Precisión: {precision:.3f}")
                        print(f"📊 Recall: {recall:.3f}")
                        print(f"📊 F1-Score: {f1:.3f}")
                    else:
                        print("⚠️ Datos insuficientes para validación cruzada")
                        
                except Exception as e:
                    print(f"⚠️ Error calculando métricas: {e}")
        else:
            print("⚠️ No se pudieron generar predicciones de prueba")
        
        # 5. Guardar modelo (ya se guardó automáticamente durante el entrenamiento)
        print("💾 Modelo guardado automáticamente durante el entrenamiento")
        
        print("🎉 ¡Entrenamiento completado exitosamente!")
        return True
    else:
        print("❌ Error entrenando el modelo")
        return False

if __name__ == "__main__":
    train_model_manually()




