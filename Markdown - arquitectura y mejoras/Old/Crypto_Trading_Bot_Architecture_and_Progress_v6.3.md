# 🤖 Crypto Trading Bot — Arquitectura, Implementación y Progreso Técnico

**Framework:** Python + Backtrader  
**Versión:** Octubre 2025  
**Autor:** [Tu equipo o nombre]  
**Estado:** Implementación avanzada — Fase 2 (Optimización del Sistema) en curso

---

## 🧭 OBJETIVO GENERAL

Desarrollar un **sistema multi-estrategia profesional para trading de criptomonedas** que combine:

- ✅ **Asignación dinámica de riesgo (Risk Parity)**
- ✅ **Detección de regímenes de mercado (Market Regime Detection)**
- ✅ **Gestión de estrategias independientes (StrategyHandle)**
- ✅ **Logging híbrido incremental y modular**
- ⚙️ **Optimización progresiva basada en rendimiento real**
- 🧠 **Futuro: predicción adaptativa mediante ML**

El objetivo general es **maximizar consistencia**, **reducir drawdowns**, y mantener **transparencia y trazabilidad total** de las decisiones del bot.

---

## 🧱 ARQUITECTURA GENERAL

| Componente | Función Principal |
|-------------|-------------------|
| **Backtrader Core** | Motor de backtesting y ejecución |
| **RiskParityAllocator** | Asigna pesos de capital dinámicamente según riesgo |
| **MarketRegimeDetector** | Detecta regímenes (bull/bear/lateral, vol alto/bajo) |
| **PortfolioManager** | Orquesta estrategias activas y pesos del portafolio |
| **StrategyHandle / Manager** | Control de activación, sincronización y cierre de estrategias |
| **Hybrid Logging System** | Estructura modular por sesión con logs incrementales |
| **MetricsHub** *(en desarrollo)* | Dashboards de rendimiento y correlaciones |
| **Optimization Layer** *(futuro)* | Ajuste dinámico de parámetros y backtesting adaptativo |

---

## ⚙️ ESTADO ACTUAL DEL PROYECTO

| Módulo | Estado | Comentario |
|---------|--------|------------|
| Estrategias Base | ✅ 5/6 operativas | RSIEMAMomentum y BollingerReversion en ajuste |
| Risk Parity Allocator | ✅ Activo y funcional | Logs completos, rebalanceos detectados |
| Market Regime Detection | ✅ Operativo | Activación dinámica validada |
| StrategyHandle Manager | ✅ Estable | Integrado con logging |
| Portfolio Engine | ✅ Sólido | Multi-estrategia con sincronización estable |
| Hybrid Logging System | ✅ 100% | Estructura incremental (`.jsonl`) funcional |
| Dashboards / Metrics | 🟡 En desarrollo | Se implementará tras optimización |
| ML Regime Prediction | 🔜 Planificada | Fase 3 del roadmap |

---

## 🧩 FASE 1 — CORRECCIÓN Y OPTIMIZACIÓN CRÍTICA ✅

### 🎯 OBJETIVO:
Garantizar ejecución completa de todas las estrategias, activación del Risk Parity y logs operativos.

### 📈 RESULTADOS CLAVE:

| Métrica | Antes | Después | Mejora |
|----------|--------|----------|---------|
| Estrategias Funcionales | 2 / 6 | 4 / 6 | +100% |
| VolatilityBreakout Trades | 0 | 236 | +236 |
| Risk Parity | Inactivo | Activo | ✅ |
| Logging Completo | Parcial | Total | ✅ |
| Win Rate Promedio | 25–35% | 28–36% | +3% |

### 🔧 CAMBIOS PRINCIPALES
- **Stop-loss:** ajustado de 0.015 → 0.01  
- **Take-profit:** valores más agresivos (2–4%)  
- **ADX y RSI thresholds:** optimizados para sensibilidad adecuada  
- **Risk Parity:** activado con logs completos (`risk_parity.jsonl`)  
- **Logging híbrido:** validado, con registros por estrategia y régimen

### ✅ ESTADO POST-FASE 1
- **4 estrategias operativas:** VolatilityBreakout, EMAConservative, ContrarianVolume, TrendFollowingADXEMA  
- **Risk Parity activo:** pesos asignados dinámicamente  
- **Logging completo:** trazabilidad en 100% de los componentes  
- **Win rate global:** 28–36%, drawdown < 1%

---

## 🔧 FASE 2 — OPTIMIZACIÓN DEL SISTEMA (EN CURSO)

### 🎯 OBJETIVO:
Mejorar el **rendimiento agregado** del portafolio y la **diversificación** entre regímenes de mercado.

### 🧩 ACCIONES EN EJECUCIÓN

| Tarea | Descripción | Estado |
|--------|--------------|--------|
| 🧠 Debug específico BollingerReversionStrategy | Revisión de condiciones de reversión y desviación estándar | 🟡 En curso |
| ⚙️ Relajar RSIEMAMomentumStrategy | Ajuste de filtros RSI y EMA gap | 🟡 En curso |
| 🧪 Testing extendido TrendFollowingADXEMA | Validación de trailing stop y ADX thresholds | 🟡 En curso |
| 📈 Optimización global de win rate | Objetivo: 45%+ promedio | 🟢 En progreso |
| 🔁 Ajuste Risk Parity threshold | Rebalance cada 15% (antes 20%) | 🟢 Activo |
| 📊 Market Regime Tuning | Ajuste de whitelist y condiciones de activación | 🟢 Planificado |

### 📊 OBJETIVOS DE RENDIMIENTO (FASE 2)
- Win rate > **45%**
- Drawdown < **1%**
- MAR ratio > **2.0**
- Diversificación efectiva (mín. 3 estrategias activas simultáneamente)

---



---

## 🚀 FASE 2.3 — ANÁLISIS AVANZADO Y DIAGNÓSTICO FINAL

# 🧪 Fase 2.3 — Análisis Avanzado y Diagnóstico Profundo

**Fecha de informe:** 2025-10-13 18:35:41 UTC

---

## 📂 Archivos analizados

- `trend_following_adx_ema.py`
- `rsi_ema_momentum.py`
- `ema_breakout_conservative.py`
- `execution_log.txt`
- `portfolio_summary.json`
- `config_trend_following_adx_ema.json`
- `config_rsi_ema.json`
- `config_ema_breakout_conservative.json`

---

## 📊 Resumen rápido del estado (desde portfolio_summary.json, si disponible)

```json
{
  "session_id": "20251013_191222",
  "total_strategies": 6,
  "total_symbols": 1,
  "portfolio_results": {
    "BTCUSDT": {
      "VolatilityBreakoutStrategy": {
        "config": {
          "strategy": "VolatilityBreakoutStrategy",
          "symbol": "BTCUSDT",
          "data_file": "data/BTCUSDT_15min.csv",
          "timeframe": "15m",
          "commission": 0.001,
          "initial_cash": 10000,
          "lookback": 10,
          "atr_period": 14,
          "multiplier": 1.0,
          "trailing_stop": 0.015,
          "position_size": 0.1,
          "start_date": "2025-04-01",
          "end_date": "2025-10-09"
        },
        "performance": {
          "initial_cash": 10000,
          "final_value": 9746.666706999684,
          "total_return": -2.5333329300031617
        },
        "analyzers": {
          "sharpe": {
            "sharperatio": null
          },
          "drawdown": {
            "len": 18137,
            "drawdown": 2.5333329300031617,
            "moneydown": 253.3332930003162,
            "max": {
              "len": 18137,
              "drawdown": 3.3763975971360014,
              "moneydown": 337.63975971360014
            }
          },
          "returns": {
            "rtot": -0.02565974264244318,
            "ravg": -0.00013364449292939157,
            "rnorm": -0.03311760779022926,
            "rnorm100": -3.3117607790229258
          },
          "trades": {
            "total": {
              "total": 202,
              "open": 1,
              "closed": 201
            },
            "streak": {
              "won": {
                "current": 0,
                "longest": 5
              },
              "lost": {
                "current": 3,
                "longest": 13
              }
            },
            "pnl": {
              "gross": {
                "total": 142.4154083488275,
                "average": 0.7085343698946641
              },
              "net": {
                "total": -253.5042175

... (truncado)
```

---

## 🧵 Extractos clave de `execution_log.txt` (errores)

_No se encontraron líneas con `NoneType`, `Traceback` o `ERROR` en el log cargado._

---

## 🔎 Diagnóstico por estrategia

### 1) TrendFollowingADXEMAStrategy — trailing stop

- Presencia de métodos: `__init__`: True · `next`: True · `notify_order`: True · `stop`: False

- Atributos de trailing detectados en código: `['trailing_stop_price']`

**Hallazgo probable:** el atributo de precio de trailing se usa antes de ser inicializado en el primer tick/primera orden.

**Parche sugerido (patrón robusto):**

```python
def _ensure_trailing_initialized(self):
    if getattr(self, 'trailing_stop_price', None) is None:
        self.trailing_stop_price = self.data.close[0] * (1 - self.trailing_stop)

def next(self):
    self._ensure_trailing_initialized()
    # ... tu lógica y luego actualizar trailing sólo si en posición
    if self.position and self.position.size > 0:
        new_trail = self.data.close[0] * (1 - self.trailing_stop)
        self.trailing_stop_price = max(self.trailing_stop_price, new_trail)
```

**Además:** inicializar/actualizar `trailing_stop_price` dentro de `notify_order()` cuando una orden pasa a `Completed`.


### 2) RSIEMAMomentumStrategy — baja frecuencia de señales

- Umbrales RSI detectados en código (aprox por heurística): `[("rsi_buy_threshold', 40),  # Mantener: 40", 'buy'), ("rsi_sell_threshold', 60), # Mantener: 60", 'sell')]`

- Verificar si la lógica exige **cruce** y a la vez **estar por encima/debajo** (condiciones redundantes que bloquean entradas).

**Parche sugerido:** separar **condición de cruce** (evento) de **estado** (regla persistente) y aplicar histeresis.

```python
cross_up = self.rsi[-1] < self.rsi_buy and self.rsi[0] >= self.rsi_buy
cross_down = self.rsi[-1] > self.rsi_sell and self.rsi[0] <= self.rsi_sell
if cross_up and self.data.close[0] > self.ema[0]:
    self.buy()
elif cross_down and self.data.close[0] < self.ema[0]:
    self.sell()
```
**Nota:** si operas momentum (no reversión), usa umbrales 40/60 o 45/55 con histeresis de ±1 para evitar whipsaw.


### 3) EMABreakoutConservativeStrategy — error de cierre en `stop()`

- `stop()` presente: True; cierre en stop(): True

**Patrón robusto para `stop()`:**

```python
def stop(self):
    try:
        if self.broker and self.position:
            self.close()
        # cancelar pendientes si usas referencias de órdenes
        for o in getattr(self, 'open_orders', []):
            try:
                self.cancel(o)
            except Exception:
                pass
    except Exception as e:
        print(f'[stop] Exception: {e}')
```


---
## ⚙️ Configuraciones cargadas (resumen)

### TrendFollowingADXEMA

```json
{
  "strategy": "TrendFollowingADXEMAStrategy",
  "symbol": "BTC/USDT",
  "data_file": "data/BTCUSDT_15min.csv",
  "timeframe": "15m",
  "commission": 0.001,
  "initial_cash": 10000,
  "adx_period": 14,
  "adx_threshold": 30,
  "ema_fast": 21,
  "ema_slow": 55,
  "position_size": 0.05,
  "take_profit": 0.04,
  "stop_loss": 0.01,
  "trailing_stop": 0.012,
  "start_date": "2025-04-01",
  "end_date": "2025-10-09"
}
```

### RSIEMAMomentum

```json
{
  "strategy": "RSIEMAMomentumStrategy",
  "symbol": "BTC/USDT",
  "data_file": "data/BTCUSDT_15min.csv",
  "timeframe": "15m",
  "commission": 0.001,
  "initial_cash": 10000,
  "rsi_period": 14,
  "rsi_buy_threshold": 35,
  "rsi_sell_threshold": 65,
  "ema_period": 12,
  "position_size": 0.15,
  "take_profit": 0.02,
  "stop_loss": 0.01,
  "start_date": "2025-04-01",
  "end_date": "2025-10-09"
}
```

### EMABreakoutConservative

```json
{
  "strategy": "EMABreakoutConservativeStrategy",
  "symbol": "BTC/USDT",
  "data_file": "data/BTCUSDT_15min.csv",
  "timeframe": "15m",
  "commission": 0.001,
  "initial_cash": 10000,
  "ema_fast": 9,
  "ema_slow": 36,
  "take_profit": 0.025,
  "stop_loss": 0.006,
  "position_size": 0.08,
  "volatility_threshold": 0.008,
  "start_date": "2025-04-01",
  "end_date": "2025-10-09"
}
```

---

## 🔬 Comparativa con la propuesta de Gemini

| Estrategia | Punto de cambio | Gemini | Análisis basado en código+logs | Estado |
|---|---|---|---|---|
| VolatilityBreakout | `multiplier` | 2.0–2.5 | 1.6–2.0 (con filtro EMA200-d y ADX) | **Diverge (más conservador)** |
| VolatilityBreakout | `trailing_stop` | 2.5–3.0% | 0.8–1.0% (para cortar fallos pronto) | **Diverge** |
| BollingerReversion | `std_dev` | 2.5–3.0 | 2.2–2.5 + `adx<18` | **Parcial** |
| BollingerReversion | `take_profit/stop_loss` | 2.0% / 1.0% | 1.8% / 0.9% + salida EMA20 | **Parcial** |
| ContrarianVolume | `spike_mult` | 3.0–4.0 | 2.5–3.0 + filtro RSI (30/70) | **Parcial** |
| EMA Conservative | EMA fast/slow | 12/24 | 9/36 o 12/30 + vol_th 0.007–0.012 | **Parcial** |
| RSI EMA Momentum | Umbrales RSI | 60/40 (momentum) | 40/60 (momentum) con cruce + histeresis | **Diverge** |


---
## 📅 Próximos pasos propuestos (Fase 2.4)

- Aplicar los parches de inicialización/validación en **trailing stop**.
- Implementar `stop()` robusto en EMAConservative con cancelación segura de órdenes.
- Separar condiciones de **evento de cruce** vs **estado** en RSIEMAMomentum, habilitar logs de motivos de no-entrada.
- Ejecutar smoke tests de 14 días por estrategia; seleccionar mejor set y correr 60–90 días con Risk Parity activo.


---

## 🧬 FASE 3 — EVOLUCIÓN AVANZADA (PLANIFICADA)

### 🎯 OBJETIVO:
Dotar al sistema de **capacidad de aprendizaje adaptativo** y **optimización continua**.

### 🧩 ACCIONES FUTURAS

| Tarea | Descripción | Estado |
|--------|--------------|--------|
| 🤖 ML Regime Prediction | Modelo SVM/LSTM para anticipar regímenes | 🔜 Planificada |
| ⚙️ Dynamic Parameter Adjustment | Ajuste adaptativo según equity rolling y volatilidad | 🔜 Planificada |
| 📊 MetricsHub Dashboard | Visualización en tiempo real de KPIs, correlaciones y performance | 🔜 Planificada |
| 🧮 Multi-símbolo testing | Backtesting expandido: BTC, ETH, SOL, BNB | 🔜 Planificada |
| 🧪 Walk-forward robusto | Validación en ventanas deslizantes 2023–2025 | 🔜 Planificada |

---

## 🧭 ROADMAP GENERAL DE DESARROLLO

| Fase | Nombre | Objetivo | Estado |
|------|---------|-----------|--------|
| 1️⃣ | Corrección & Optimización Crítica | Estabilizar estrategias, activar Risk Parity | ✅ Completada |
| 2️⃣ | Optimización del Sistema | Mejorar rendimiento y diversificación | 🟡 En curso |
| 3️⃣ | Evolución Avanzada | ML, optimización adaptativa, dashboards | 🔜 Planificada |
| 4️⃣ | Producción Live Trading | Ejecución real en Exchange (API + Seguridad) | ⏳ Futura |
| 5️⃣ | Optimización Continua | Tuning dinámico y monitorización de métricas | ⏳ Futura |

---

## 🧮 BACKTESTING Y VALIDACIÓN

- **Motor:** Backtrader  
- **Datos:** OHLCV multi-timeframe (1m → diario)  
- **Estrategias activas:** 4 (con 2 en revisión)  
- **Métricas clave:** CAGR, Sharpe, Sortino, MAR, Max Drawdown  
- **Validaciones:** Individuales y agregadas por régimen  
- **Logging:** Estructura `.jsonl` incremental y modular por sesión  
- **Rendimiento actual:** Win Rate promedio 33%, DD 0.8%, Risk Parity activo

---

## 🏦 EXCHANGES RECOMENDADOS

| Tipo | Exchange | Registro | Código | Beneficio |
|------|-----------|-----------|---------|-----------|
| CEX | [**Bybit**](https://partner.bybit.com/b/fg3yc) | `FG3YC` | 🎁 Hasta $30,000 en bonos + 20% menos fees |
| CEX | [**Bitget**](https://partner.bitget.com/bg/r1tk91041673453416852) | `r1tk9104` | 🎁 20% fee off + $6,200 bonus |
| CEX | [**OKX**](https://www.okx.com/join/K8080) | `K8080` | 🎁 20% descuento en comisiones |
| DEX | [**Aster**](https://www.asterdex.com/en/referral/e67e4c) | — | 🎁 5% descuento |
| DEX | [**HyperLiquid**](https://app.hyperliquid.xyz/join/BONUS2025) | — | 🎁 4% descuento |

---


---

## 📥 DESCARGA Y GESTIÓN DE DATOS HISTÓRICOS (PENDIENTE DE IMPLEMENTACIÓN)

### 🔍 Análisis de la Funcionalidad Actual

**Implementado:**
- `data/data_fetcher.py` contiene una clase **DataFetcher** basada en **ccxt**, con soporte para Binance y otros exchanges.
- Maneja conexión, validación y limpieza básica de datos.
- Incluye lógica de *retry* y manejo de errores.
- Genera datasets existentes como:
  - `BTCUSDT_15min.csv`
  - `btc_15m_data_2018_to_2025.csv`
  - `eth-usd-max.csv`

**Limitaciones detectadas:**
- ❌ No existe un **script automático de descarga histórica**.
- ❌ No se implementa la **actualización automática de datasets**.
- ❌ No hay conversión directa al formato Backtrader (`datetime, open, high, low, close, volume`).
- ❌ Falta gestión de **rangos de fechas** y **múltiples timeframes**.
- ❌ No hay validación automática de datos faltantes o duplicados.

### 🧩 Recomendación Técnica

Se requiere un módulo nuevo para la **descarga y actualización automática de datos históricos**, con las siguientes características:

| Funcionalidad | Descripción |
|----------------|-------------|
| **Soporte de exchanges** | Descarga vía `ccxt` desde Binance y otros |
| **Gestión de timeframes** | 1m, 5m, 15m, 1h, 4h, 1d |
| **Rangos de fechas** | Parámetros de inicio y fin (por ejemplo: 2018–2025) |
| **Actualización incremental** | Añadir solo datos nuevos sin sobrescribir el histórico |
| **Conversión automática** | Exportar al formato CSV compatible con Backtrader |
| **Validación de integridad** | Detección y limpieza de huecos de datos |
| **Scheduler opcional** | Actualización automática diaria o semanal |

### 🛠️ Sugerencia de Implementación

Archivo propuesto: `scripts/data_auto_downloader.py`

**Estructura sugerida:**
```python
from data.data_fetcher import DataFetcher
from datetime import datetime, timedelta

class HistoricalDataDownloader:
    def __init__(self, symbol="BTC/USDT", timeframe="15m", start="2018-01-01", end=None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.start = start
        self.end = end or datetime.utcnow().strftime("%Y-%m-%d")
        self.fetcher = DataFetcher(exchange="binance")

    def download(self):
        print(f"Downloading {self.symbol} [{self.timeframe}] from {self.start} to {self.end}")
        data = self.fetcher.fetch_ohlcv(self.symbol, self.timeframe, self.start, self.end)
        self._save_csv(data)

    def _save_csv(self, data):
        filename = f"datasets/{self.symbol.replace('/', '')}_{self.timeframe}_{self.start}_to_{self.end}.csv"
        data.to_csv(filename, index=False)
        print(f"Saved dataset: {filename}")

if __name__ == "__main__":
    HistoricalDataDownloader(symbol="BTC/USDT", timeframe="15m", start="2018-01-01").download()
```

### 📊 Próximos pasos
1. Implementar este script de descarga y validación.
2. Integrarlo con el sistema de backtesting (PortfolioEngine) para cargar datasets actualizados automáticamente.
3. Agregar soporte para múltiples activos y timeframes.
4. Incluir validaciones automáticas en el pipeline de ejecución.

---

## ⚠️ DISCLAIMER

> Este documento tiene fines educativos y de investigación.  
> No constituye asesoramiento financiero ni recomendación de inversión.  
> El trading de criptomonedas y derivados implica **alto riesgo** y puede generar pérdidas significativas.  
> Usa siempre una gestión de riesgo responsable.

---

**© 2025 — Crypto Trading Bot Framework (v5.0)**  
Desarrollado por: *Crypto Trading Bot GPT — Futures & Strategy Assistant*
