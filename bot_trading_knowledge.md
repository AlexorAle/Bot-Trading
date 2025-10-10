# Documento Base de Conocimiento: Implementación Local de un Bot de Trading para Liquidation Hunting con Kalman Filter + Random Forest

**Versión: 1.0**  
**Fecha: 03 de octubre de 2025**  
**Autor: Grok 4 (basado en interacciones previas)**  
**Propósito:** Este documento sirve como guía detallada y base de conocimiento para implementar un bot de trading en Python de manera local en tu computadora. El enfoque es en la estrategia "Liquidation Hunting" utilizando Kalman Filter para filtrado de ruido y Random Forest para predicciones de dirección de precios, orientado a criptomonedas en exchanges como BingX o Bybit. Esta información se usará para crear un GPT personalizado en ChatGPT que te ayude a generar y depurar el código en Python.  

El bot se construirá de forma modular para facilitar el desarrollo, testing y escalabilidad. Se asume que tienes Python instalado (versión 3.10+), Cursor IDE y ChatGPT Pro para asistencia en codificación. El desarrollo se hace localmente primero (en tu PC), con backtesting y paper trading, antes de deployar a VPS.  

**Advertencias importantes:**  
- Esto no es consejo financiero. Los retornos estimados son aproximados y dependen de mercados reales; siempre usa capital de riesgo.  
- Backtestea exhaustivamente para evitar overfit.  
- Integra manejo de errores, rate limiting y seguridad (API keys en .env).  
- No garantiza profits; incluye riesgos como fees, slippage y crashes de mercado.  

## 1. Arquitectura General del Bot en Python

La arquitectura es modular y basada en principios de software limpio (e.g., separación de concerns). Se divide en capas para que cada parte sea independiente y testable. Usa un enfoque event-driven simple con un loop principal que orquesta todo.  

**Diagrama conceptual de arquitectura (texto-based):**  
```
[Fuente de Datos] --> [Procesamiento/ML] --> [Lógica de Estrategia] --> [Ejecución de Trades]
                  |                        |
                  v                        v
             [Monitoreo/Logs]         [Almacenamiento Temporal]
```  

**Capas principales:**  
- **Capa de Datos:** Recopila y preprocesa datos en vivo o históricos (precios, liquidaciones, open interest).  
- **Capa de Procesamiento/ML:** Aplica filtros (Kalman) y modelos (Random Forest) para generar predicciones.  
- **Capa de Lógica/Estrategia:** Decide señales de trading basadas en outputs de ML (e.g., entrar en short si predicción de reversal).  
- **Capa de Ejecución:** Interactúa con APIs de exchanges para colocar órdenes.  
- **Capa de Monitoreo:** Registra logs, envía alertas y maneja errores.  
- **Capa de Configuración:** Maneja parámetros (API keys, thresholds) via archivos .env o config.yaml.  

**Tecnologías y librerías requeridas en Python:**  
- **Core:** Python 3.10+ (usa venv para entorno aislado).  
- **Librerías esenciales (instala con pip):**  
  - `ccxt`: Para APIs de exchanges (BingX/Bybit).  
  - `pandas` y `numpy`: Manipulación de datos y arrays.  
  - `scipy`: Para Kalman Filter (usa `scipy.signal` o implementación custom).  
  - `scikit-learn`: Para Random Forest (modelo de clasificación).  
  - `python-dotenv`: Para cargar API keys desde .env.  
  - `python-telegram-bot` o `smtplib`: Para alertas (opcional, e.g., Telegram).  
  - `requests` o `websockets`: Para datos en vivo si CCXT no basta.  
  - `ta-lib` (opcional): Para indicadores técnicos como ATR en risk management.  
- **Estructura de archivos recomendada:**  
  ```
  bot_project/
  ├── main.py              # Loop principal y orquestación
  ├── config.py            # Carga configs y .env
  ├── data/
  │   └── data_fetcher.py  # Módulo de datos
  ├── processing/
  │   ├── kalman_filter.py # Filtro Kalman
  │   └── ml_model.py      # Random Forest
  ├── strategy/
  │   └── liquidation_hunter.py # Lógica de estrategia
  ├── execution/
  │   └── trader.py        # Ejecución de trades
  ├── monitoring/
  │   └── logger.py        # Logs y alertas
  ├── tests/               # Tests unitarios (usa pytest)
  ├── data/                # Datos históricos (CSV para backtests)
  ├── models/              # Modelos ML serializados (e.g., .pkl)
  ├── .env                 # API keys secretas
  └── requirements.txt     # Lista de dependencias
  ```  

**Modo de operación:**  
- **Modos:** Development (local, backtest), Paper Trading (simulado), Live (real). Configura via variable en config.py.  
- **Loop principal:** En main.py, un while True con sleep (e.g., cada 1-5 min) para fetch data, process, decide y execute.  

## 2. Detalle de Módulos

A continuación, descripción detallada de cada módulo, con responsabilidades, inputs/outputs y sugerencias de implementación. Usa esto en tu GPT para generar código específico.

### 2.1. Módulo de Configuración (config.py)
- **Responsabilidades:** Cargar variables de entorno, parámetros de estrategia y credenciales.  
- **Inputs:** Archivo .env (e.g., API_KEY_BYBIT, SECRET_BYBIT, EXCHANGE='bybit', SYMBOL='BTCUSDT', TIMEFRAME='5m').  
- **Outputs:** Diccionario o clase Config con valores.  
- **Detalles:** Usa `dotenv.load_dotenv()` para seguridad. Incluye params como RISK_PER_TRADE=0.01 (1% de capital), KALMAN_Q=0.01 (ruido proceso), RF_N_ESTIMATORS=100.  
- **Ejemplo de código base:**  
  ```python
  from dotenv import load_dotenv
  import os

  load_dotenv()
  class Config:
      API_KEY = os.getenv('API_KEY')
      # ... otros params
  ```

### 2.2. Módulo de Datos (data/data_fetcher.py)
- **Responsabilidades:** Fetch datos históricos/en vivo (precios OHLCV, liquidaciones, OI, funding rates). Preprocesar (limpiar nans, normalizar).  
- **Inputs:** Exchange, symbol, timeframe, limit (e.g., 1000 candles).  
- **Outputs:** Pandas DataFrame con columnas como timestamp, open, high, low, close, volume, liquidations_long, liquidations_short.  
- **Detalles:** Usa CCXT para fetch_ohlcv(), fetch_liquidations() si disponible (o APIs custom de Bybit/BingX). Para históricos, descarga CSV de exchanges. Maneja rate limits con try/except y sleep.  
- **Features para ML:** liquidations_volume, oi_change, funding_rate, price_deviation.  
- **Ejemplo:**  
  ```python
  import ccxt
  import pandas as pd

  def fetch_data(exchange, symbol, timeframe, limit):
      ex = ccxt.bybit()  # o bingx
      ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=limit)
      df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
      # Agregar liquidaciones via API específica
      return df
  ```

### 2.3. Módulo de Procesamiento - Kalman Filter (processing/kalman_filter.py)
- **Responsabilidades:** Suavizar series temporales (e.g., precios o liquidaciones) para estimar desviaciones mean-reverting.  
- **Inputs:** Serie de datos (numpy array o pd.Series). Params Q (ruido proceso), R (ruido medición).  
- **Outputs:** Serie filtrada y desviación (e.g., z-score > threshold para signal).  
- **Detalles:** Implementa Kalman 1D simple con SciPy o manual (matrices de estado). Aplica a precios para detectar outliers que indiquen hunts. Threshold típico: desviación > 2 std para signal.  
- **Ejemplo:**  
  ```python
  import numpy as np
  from scipy.signal import kalman  # O implementación custom

  def apply_kalman(series, Q=0.01, R=0.1):
      # Inicializar matrices Kalman
      # ... lógica de filtro
      filtered = []  # Aplicar iterativamente
      return np.array(filtered)
  ```

### 2.4. Módulo de Procesamiento - ML Model (processing/ml_model.py)
- **Responsabilidades:** Entrenar y predecir con Random Forest para dirección (up/down reversal).  
- **Inputs:** DataFrame con features; para predict: nuevos datos.  
- **Outputs:** Predicción (0: down, 1: up); probability.  
- **Detalles:** Usa sklearn.ensemble.RandomForestClassifier. Entrena con datos históricos (split 80/20). Features: lagged prices, liquidations ratio, Kalman deviation. Guarda modelo con joblib.dump(). Accuracy target: ~75%.  
- **Ejemplo:**  
  ```python
  from sklearn.ensemble import RandomForestClassifier
  import joblib

  def train_rf(X, y):
      model = RandomForestClassifier(n_estimators=100)
      model.fit(X, y)
      joblib.dump(model, 'rf_model.pkl')
      return model

  def predict_rf(new_data):
      model = joblib.load('rf_model.pkl')
      return model.predict(new_data)
  ```

### 2.5. Módulo de Estrategia (strategy/liquidation_hunter.py)
- **Responsabilidades:** Combinar outputs de Kalman y RF para generar signals (buy/sell/hold). Incluir risk management.  
- **Inputs:** Data filtrada, predicciones ML, capital actual.  
- **Outputs:** Signal dict (e.g., {'action': 'short', 'size': 0.01, 'sl': price*0.98}).  
- **Detalles:** Lógica: Si Kalman deviation > threshold Y RF predict 'down', short (hunt longs). Position sizing: risk% / distance to SL. Evita overtrading con cooldown.  
- **Ejemplo:**  
  ```python
  def generate_signal(filtered_data, prediction):
      if prediction == 0 and deviation > 2:  # Down reversal
          return {'action': 'short', 'size': calculate_size()}
      return None
  ```

### 2.6. Módulo de Ejecución (execution/trader.py)
- **Responsabilidades:** Colocar/cancelar órdenes, check balance/positions.  
- **Inputs:** Signal dict, exchange config.  
- **Outputs:** Resultado de order (success/error).  
- **Detalles:** Usa CCXT para create_order(), fetch_balance(). Soporta market/limit orders, leverage. Modo paper: simula sin API real.  
- **Ejemplo:**  
  ```python
  import ccxt

  def execute_trade(signal, ex):
      if signal['action'] == 'short':
          ex.create_market_sell_order(symbol, signal['size'])
  ```

### 2.7. Módulo de Monitoreo (monitoring/logger.py)
- **Responsabilidades:** Logs, alertas en errores/cruces de threshold.  
- **Inputs:** Mensajes/events.  
- **Outputs:** Archivos log, mensajes Telegram.  
- **Detalles:** Usa logging module. Integra telegram.bot para notificaciones.  
- **Ejemplo:**  
  ```python
  import logging
  logging.basicConfig(filename='bot.log', level=logging.INFO)
  def log_event(msg):
      logging.info(msg)
  ```

## 3. Pasos Detallados para Implementar Localmente

Sigue estos pasos secuencialmente en tu PC con Cursor IDE. Usa ChatGPT Pro para generar código basado en este doc.

1. **Preparación del Entorno (30 min):**  
   - Crea carpeta bot_project.  
   - Inicia venv: `python -m venv venv; source venv/bin/activate` (Linux/Mac) o `venv\Scripts\activate` (Windows).  
   - Instala libs: `pip install ccxt pandas numpy scipy scikit-learn python-dotenv joblib python-telegram-bot`.  
   - Crea .env con tus API keys (regístrate en Bybit/BingX para testnet).  
   - Genera requirements.txt: `pip freeze > requirements.txt`.  

2. **Desarrollo de Módulos (2-4 días):**  
   - Implementa cada módulo como descrito, empezando por config y data.  
   - Usa Cursor/ChatGPT: Copia descripciones de módulos y pide "Genera código Python para [módulo] basado en esto".  
   - Prueba unitariamente (e.g., fetch_data() y verifica DF).  

3. **Integración en main.py (1 día):**  
   - Crea loop: Importa módulos, carga config, while True: fetch -> process (Kalman + RF) -> strategy -> execute (si signal). Sleep 60s.  
   - Agrega modo backtest: Usa datos CSV en lugar de live.  

4. **Backtesting (1-2 días):**  
   - Descarga datos históricos (e.g., de Bybit API o Kaggle).  
   - Simula trades en loop con datos pasados; calcula ROI, win rate, drawdown. Usa pandas para metrics.  

5. **Paper Trading (3-5 días):**  
   - Configura modo paper en trader.py (simula balance).  
   - Corre 24/7 localmente; monitorea logs. Ajusta params basados en performance.  

6. **Depuración y Optimización (ongoing):**  
   - Maneja excepciones (e.g., API errors).  
   - Optimiza ML: Grid search para hiperparams.  
   - Prueba con diferentes symbols (BTCUSDT, ETHUSDT).  

Una vez local funcione, deploy a VPS: Copia archivos, setup venv, usa systemd para correr main.py como servicio.  

**Próximos pasos en GPT personalizado:** Copia este documento completo en la sección de "conocimiento" o "instrucciones" de tu GPT personalizado en ChatGPT. Esto le dará la referencia exacta de la arquitectura, módulos y pasos para que te ayude a construir el código en Python de manera consistente. Luego, puedes pedirle cosas como: "Basado en el documento base, genera el código para el módulo de datos".

Para descargar el archivo: Copia todo este contenido (incluyendo el encabezado) y pégalo en un editor de texto como Notepad, VS Code o Bloc de Notas. Guárdalo con el nombre "bot_trading_knowledge.md" (extensión .md para Markdown). Así podrás usarlo directamente en tu GPT o abrirlo como referencia. Si necesitas un enlace de descarga, puedo sugerirte subirlo a un sitio como GitHub Gist o Pastebin, pero esto es lo más directo.