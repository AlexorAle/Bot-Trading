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
