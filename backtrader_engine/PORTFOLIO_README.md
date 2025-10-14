# 🎯 Portfolio de Estrategias Cripto - Backtrader

## 📋 Descripción

Sistema de trading algorítmico compuesto por **5 estrategias complementarias** que maximizan la rentabilidad ajustada al riesgo sobre BTC/USDT y ETH/USDT. Este enfoque busca la **descorrelación entre estrategias** para lograr consistencia en distintos entornos de mercado.

## 🚀 Estrategias Implementadas

| # | Estrategia | Tipo | Timeframe | Condición Óptima |
|---|------------|------|-----------|------------------|
| 1 | `VolatilityBreakoutStrategy` | Breakout | 15min | Alta volatilidad / Bull markets |
| 2 | `BollingerReversionStrategy` | Mean Reversion | 15min | Rango lateral |
| 3 | `RSIEMAMomentumStrategy` | Momentum | 15min | Tendencias suaves |
| 4 | `EMABreakoutConservativeStrategy` | Breakout + Filtros | 15min | Consolidación técnica |
| 5 | `ContrarianVolumeSpikeStrategy` | Contrarian / Reversal | 15min | Capitulation / Overreaction |

## 📁 Estructura del Proyecto

```
backtrader_engine/
├── strategies/                     # Estrategias individuales
│   ├── volatility_breakout.py     # Breakout de volatilidad
│   ├── bollinger_reversion.py     # Reversión a la media
│   ├── rsi_ema_momentum.py        # Momentum RSI + EMA
│   ├── ema_breakout_conservative.py # Breakout conservador
│   └── contrarian_volume.py       # Contrarian con volumen
├── configs/                        # Configuraciones por estrategia
│   ├── config_volatility.json
│   ├── config_bollinger.json
│   ├── config_rsi_ema.json
│   ├── config_ema_conservative.json
│   └── config_contrarian.json
├── portfolio_engine.py            # 🎯 Motor de ejecución multi-estrategia
├── main.py                        # Entrada individual por estrategia
└── reports/                       # Salida de análisis
```

## 🎯 Uso del Portfolio Engine

### Ejecutar todas las estrategias en BTC/USDT:
```bash
python portfolio_engine.py --symbols BTCUSDT --strategies VolatilityBreakoutStrategy BollingerReversionStrategy RSIEMAMomentumStrategy EMABreakoutConservativeStrategy ContrarianVolumeSpikeStrategy
```

### Ejecutar estrategias específicas:
```bash
python portfolio_engine.py --symbols BTCUSDT ETHUSDT --strategies VolatilityBreakoutStrategy BollingerReversionStrategy
```

### Ejecutar con configuración personalizada:
```bash
python portfolio_engine.py --symbols BTCUSDT --config-dir configs --output portfolio_results.json
```

## 🔧 Uso Individual de Estrategias

### Volatility Breakout:
```bash
python main.py --config configs/config_volatility.json
```

### Bollinger Reversion:
```bash
python main.py --config configs/config_bollinger.json
```

### RSI + EMA Momentum:
```bash
python main.py --config configs/config_rsi_ema.json
```

### EMA Breakout Conservative:
```bash
python main.py --config configs/config_ema_conservative.json
```

### Contrarian Volume Spike:
```bash
python main.py --config configs/config_contrarian.json
```

## 📊 Parámetros por Estrategia

### 1. Volatility Breakout
- **lookback**: 20 períodos
- **atr_period**: 14 períodos
- **multiplier**: 1.5x
- **trailing_stop**: 2%
- **position_size**: 10%

### 2. Bollinger Reversion
- **bb_period**: 20 períodos
- **std_dev**: 2.0 desviaciones
- **volume_filter_period**: 20 períodos
- **position_size**: 10%
- **take_profit**: 1.5%
- **stop_loss**: 1%

### 3. RSI + EMA Momentum
- **rsi_period**: 14 períodos
- **rsi_buy_threshold**: 30
- **rsi_sell_threshold**: 70
- **ema_period**: 50 períodos
- **position_size**: 15%
- **take_profit**: 2.5%
- **stop_loss**: 1.5%

### 4. EMA Breakout Conservative
- **ema_fast**: 6 períodos
- **ema_slow**: 28 períodos
- **take_profit**: 2%
- **stop_loss**: 0.75%
- **position_size**: 8%
- **volatility_threshold**: 0.5%
- **trend_ema_fast**: 20 períodos
- **trend_ema_slow**: 50 períodos

### 5. Contrarian Volume Spike
- **volume_period**: 20 períodos
- **volume_spike_multiplier**: 2.0x
- **spread_threshold**: 1%
- **position_size**: 10%
- **stop_loss**: 1.5%
- **take_profit**: 3%
- **rsi_period**: 14 períodos

## 📈 Salida del Portfolio Engine

El motor genera un reporte JSON con:

```json
{
  "BTCUSDT": {
    "VolatilityBreakoutStrategy": {
      "performance": {"total_return": 5.2, "final_value": 10520},
      "analyzers": {"sharpe": {...}, "drawdown": {...}, "trades": {...}}
    },
    "BollingerReversionStrategy": {...},
    "PortfolioTotal": {
      "total_return": 4.3,
      "max_drawdown": 2.7,
      "win_rate": 38,
      "strategies_count": 5
    }
  }
}
```

## 🎯 Métricas de Evaluación

- **Total Return** individual y total
- **Max Drawdown** por estrategia y portfolio
- **Win Rate** y número de trades
- **Sharpe Ratio** para riesgo ajustado
- **Profit Factor** para eficiencia

## ⚠️ Consideraciones

1. **Gestión de Capital**: Cada estrategia usa position_size independiente
2. **Correlación**: Las estrategias están diseñadas para ser complementarias
3. **Timeframes**: Todas las estrategias usan 15min para consistencia
4. **Datos**: Requiere archivos CSV con formato estándar (datetime, open, high, low, close, volume)

## 🔄 Próximos Pasos

1. **Testing Individual**: Probar cada estrategia por separado
2. **Optimización**: Ajustar parámetros según resultados
3. **Walk-Forward**: Implementar reentrenamiento por trimestre
4. **Risk Management**: Añadir gestión de riesgo a nivel portfolio
5. **Live Trading**: Adaptar para trading en vivo

## 📚 Referencias

- Backtrader Documentation: https://www.backtrader.com/docu/
- "Building Winning Algorithmic Trading Systems" – Kevin Davey
- GitHub repos: btgym, quantdom
