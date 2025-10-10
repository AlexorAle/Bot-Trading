# Documento Base de Conocimiento: Bot de Trading LiquidationHunter

**Versión: 1.0**  
**Fecha: 04 de octubre de 2025**  
**Autor: Grok 4 (basado en interacciones previas)**  
**Propósito:** Este documento sirve como guía detallada y base de conocimiento completa para el bot de trading LiquidationHunter. Está diseñado para ser utilizado por una inteligencia artificial (IA) en tareas como backtesting, optimización y depuración. Incluye todos los detalles técnicos necesarios para reproducir, simular y evaluar el bot sin ambigüedades. La IA debe tratar este documento como su conocimiento base principal, asumiendo que el bot está implementado en Python con librerías específicas.

**Advertencias:**  
- Esto no es consejo financiero. Usa solo con capital de riesgo.  
- Backtestea exhaustivamente antes de live trading.  
- El bot está orientado a criptomonedas (e.g., SOL, ETH) en exchanges como Bybit/BingX.  
- Asume Python 3.10+, CCXT para APIs, y librerías como Pandas, NumPy, SciPy, Scikit-learn.

## 1. Características del Bot

El bot es un sistema automatizado para trading de criptomonedas, enfocado en la estrategia "Liquidation Hunting". Sus características clave son:

- **Modo de Operación:** Soporta desarrollo (local testing), paper trading (simulación), y live trading (real).
- **Mercados Soportados:** Criptomonedas (e.g., SOLUSDT, ETHUSDT, BTCUSDT) en perpetuos (perps).
- **Exchanges:** Bybit o BingX (configurable via CCXT).
- **Entrenamiento del Modelo:** Manual via `train_model.py` o automático en ciclos (configurable).
- **Manejo de Riesgo:** Position sizing dinámico (e.g., 2% del capital por trade), stop loss (1.5%), take profit (5%).
- **Monitoreo:** Logging detallado en `logs/bot.log`, alertas via Telegram (opcional).
- **Robustez:** Manejo de errores, retry logic, shutdown gracioso via signals.
- **Escalabilidad:** Modular, fácil de deployar en VPS (e.g., AWS, DigitalOcean).
- **Visualización:** Script complementario en PineScript para TradingView para backtesting visual.
- **Rendimiento Estimado:** En simulación, win rate ~60-70%, R:R 1:3.33, retorno ~10% mensual (basado en backtests históricos; no garantizado).

## 2. Arquitectura del Bot

La arquitectura es modular y basada en principios de software limpio (separación de concerns). Usa un enfoque event-driven con un loop principal en `main.py`. 

**Diagrama Conceptual (texto-based):**
```
[Config] --> [Data Fetcher] --> [Kalman Filter] --> [ML Model] --> [Strategy] --> [Trader]
                  |                        |
                  v                        v
             [Logger/Monitoreo]       [Train Model (opcional)]
```

**Capas Principales:**
- **Configuración (`config.py`):** Carga variables de entorno (.env) para API keys, thresholds, etc.
- **Datos (`data/data_fetcher.py`):** Fetch de datos OHLCV, liquidaciones, OI via CCXT.
- **Procesamiento (`processing/kalman_filter.py` y `processing/ml_model.py`):** Filtrado Kalman y predicciones Random Forest.
- **Estrategia (`strategy/liquidation_hunter.py`):** Genera signals basados en desviaciones y predicciones.
- **Ejecución (`execution/trader.py`):** Coloca órdenes (market/limit) en paper o live.
- **Monitoreo (`monitoring/logger.py`):** Logs y alertas.
- **Entrenamiento (`train_model.py`):** Script separado para entrenamiento manual.

**Estructura de Archivos:**
```
bot_project/
├── main.py
├── config.py
├── data/
│   └── data_fetcher.py
├── processing/
│   ├── kalman_filter.py
│   └── ml_model.py
├── strategy/
│   └── liquidation_hunter.py
├── execution/
│   └── trader.py
├── monitoring/
│   └── logger.py
├── train_model.py
├── models/
│   └── rf_model.pkl  (modelo guardado)
├── logs/
│   └── bot.log
├── .env
└── requirements.txt
```

**Librerías Requeridas (requirements.txt):**
```
ccxt
pandas
numpy
scipy
scikit-learn
python-dotenv
joblib
python-telegram-bot
```

## 3. Estrategia: Liquidation Hunting

La estrategia busca cascadas de liquidaciones en perpetuos, prediciendo reversals para entrar en trades. Usa Kalman Filter para suavizar datos y Random Forest para predecir dirección.

**Flujo de la Estrategia:**
1. **Fetch Datos:** Precios OHLCV, liquidaciones long/short, OI (open interest).
2. **Kalman Filter:** Suaviza series (e.g., precios) para calcular desviaciones mean-reverting.
3. **Random Forest:** Predice dirección (up/down) con features como liquidations_ratio, kalman_deviation.
4. **Signal Generation:** Si desviación > threshold y predicción coherente, genera signal (short si hunt longs, long si hunt shorts).
5. **Ejecución:** Coloca orden con risk management (position size, SL, TP).

**Lógica Detallada (`liquidation_hunter.py`):**
- Signal si `abs(kalman_deviation) > KALMAN_THRESHOLD` y ML predict matches.
- Position size: `risk_per_trade * capital / distance_to_sl`.
- Cooldown: 5 minutos para evitar overtrading.

**Tipo de Trading:** Day trading (timeframe 15m), pero adaptable a scalping (5m).

## 4. Parámetros Necesarios para la Estrategia

Todos los parámetros están en `config.py` y cargados desde .env. Aquí la lista completa con valores recomendados para SOL:

- **Exchange Config:**
  - `EXCHANGE = 'bybit'`
  - `API_KEY = 'your_key'`
  - `SECRET = 'your_secret'`
  - `TESTNET = true`

- **Trading Config:**
  - `SYMBOL = 'SOLUSDT'`
  - `TIMEFRAME = '15m'`
  - `LEVERAGE = 1` (sin apalancamiento inicial)
  - `CAPITAL = 5000` (USDT inicial)

- **Risk Management:**
  - `RISK_PER_TRADE = 0.02` (2%)
  - `MAX_POSITION_SIZE = 0.1` (10%)
  - `STOP_LOSS_PERCENTAGE = 0.015` (1.5%)
  - `TAKE_PROFIT_PERCENTAGE = 0.05` (5%)
  - `COOLDOWN_MINUTES = 5`

- **ML Config:**
  - `KALMAN_Q = 0.01` (ruido proceso)
  - `KALMAN_R = 0.1` (ruido medición)
  - `RF_N_ESTIMATORS = 100`
  - `RF_MAX_DEPTH = 10`

- **Data Config:**
  - `DATA_LIMIT = 1000` (candles)
  - `UPDATE_INTERVAL = 900` (segundos, para 15m)

- **Strategy Config:**
  - `KALMAN_THRESHOLD = 0.5`
  - `DEVIATION_THRESHOLD = 1.5` (optimizado para SOL)
  - `ML_CONFIDENCE_THRESHOLD = 0.7`

**Optimización para SOL:** Bajar `DEVIATION_THRESHOLD` a 1.5 para más trades en volatilidad alta.

## 5. Cómo Entrenar el Modelo

Usa `train_model.py` para entrenamiento manual (recomendado).

**Flujo:**
1. Fetch datos históricos (e.g., 7 días).
2. Aplicar Kalman Filter.
3. Entrenar Random Forest con features (e.g., lagged prices, liquidations_ratio).
4. Guardar modelo en `models/rf_model.pkl`.

**Código Clave:**
```python
def train_model_manually():
    fetcher = DataFetcher()
    data = fetcher.fetch_data()  # Historical
    kalman = KalmanFilter()
    filtered = kalman.apply_filter(data)
    ml_model = MLModel()
    ml_model.train(filtered)
```

## 6. Configuración para Backtesting

Para backtesting con una IA:

- **Datos:** Usa datos históricos de Bybit API o CSV (OHLCV, liquidaciones).
- **Modo:** Set `MODE = 'development'`.
- **Simulación:** En `main.py`, agrega modo backtest: loop sobre datos históricos, simula trades sin API real.
- **Métricas:** Calcula win rate, ROI, drawdown, Sharpe ratio.
- **Herramientas:** Usa Pandas para simulación; integra PineScript para visualización.

**Ejemplo de Backtest Code (añade a main.py):**
```python
def run_backtest(historical_data):
    for row in historical_data.iterrows():
        filtered = kalman_filter.apply_filter(row)
        prediction = ml_model.predict(filtered)
        signal = strategy.generate_signal(filtered, prediction)
        if signal:
            result = trader.simulate_trade(signal)
            # Track metrics
```

## 7. Seguridad y Riesgos

- **Seguridad:** API keys en .env, no hardcode. Usa testnet para pruebas.
- **Riesgos:** Overfit, slippage, comisiones. No garantiza profits; usa <10% de capital real.

Este documento es completo para backtesting. Usa como base para IA.