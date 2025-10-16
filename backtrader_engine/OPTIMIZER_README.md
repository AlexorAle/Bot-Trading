# 🚀 Parameter Optimizer with Optuna

## 📋 Overview

Bayesian parameter optimization system for trading strategies using Optuna. This tool automatically finds optimal parameters for your trading strategies by testing thousands of parameter combinations and selecting the best performing ones.

## 🎯 Key Features

- **Bayesian Optimization**: Uses Optuna's Tree-structured Parzen Estimator (TPE) for efficient parameter search
- **Multiple Metrics**: Optimize for Return/MaxDD (RMD), Sharpe Ratio, or Total Return
- **Strategy Agnostic**: Works with any Backtrader strategy
- **Comprehensive Results**: Saves best parameters, all trials, and study summary
- **Parallel Processing**: Support for multi-core optimization
- **Integration Ready**: Compatible with existing monitoring system

## 📦 Dependencies

```bash
pip install optuna backtrader pandas
```

## 🚀 Quick Start

### Basic Usage

```bash
python parameter_optimizer.py \
  --config backtrader_engine/configs/config_btc_24months.json \
  --strategy VolatilityBreakoutStrategy \
  --trials 60 \
  --metric rmd \
  --spaces param_spaces_example.json \
  --output-dir backtrader_engine/reports/optuna \
  --n-jobs 1
```

### Advanced Usage

```bash
# Multi-core optimization
python parameter_optimizer.py \
  --config backtrader_engine/configs/config_eth_6months.json \
  --strategy RSIEMAMomentumStrategy \
  --trials 200 \
  --metric sharpe \
  --spaces param_spaces_example.json \
  --output-dir backtrader_engine/reports/optuna \
  --n-jobs 4
```

## 📊 Optimization Metrics

### Return/MaxDD (RMD) - Default
- **Formula**: Total Return / Maximum Drawdown
- **Best for**: Risk-adjusted returns
- **Range**: Higher is better (typically 0.5-5.0)

### Sharpe Ratio
- **Formula**: (Mean Return - Risk Free Rate) / Standard Deviation
- **Best for**: Risk-adjusted performance
- **Range**: Higher is better (typically 0.5-3.0)

### Total Return
- **Formula**: (Final Value - Initial Value) / Initial Value
- **Best for**: Pure profit maximization
- **Range**: Higher is better (can be negative)

## 🔧 Configuration

### Parameter Spaces File (`param_spaces_example.json`)

```json
{
  "VolatilityBreakoutStrategy": {
    "lookback": {
      "type": "int",
      "low": 10,
      "high": 30,
      "description": "Lookback period for highest/lowest calculation"
    },
    "multiplier": {
      "type": "float",
      "low": 1.0,
      "high": 3.0,
      "description": "ATR multiplier for volatility threshold"
    }
  }
}
```

### Parameter Types

- **`int`**: Integer parameters with min/max bounds
- **`float`**: Float parameters with min/max bounds  
- **`categorical`**: Discrete choices from a list

### Strategy Configuration

The optimizer reads strategy parameters from your existing config files:

```json
{
  "strategy": "VolatilityBreakoutStrategy",
  "symbol": "BTC/USDT",
  "data_file": "data/BTCUSDT_15min.csv",
  "start_date": "2024-10-01",
  "end_date": "2025-10-01",
  "initial_cash": 10000,
  "commission": 0.001
}
```

## 📁 Output Structure

```
backtrader_engine/reports/optuna/
└── VolatilityBreakoutStrategy_20251014_143022/
    ├── best_params.json          # Best parameters found
    ├── trials.csv                # All optimization trials
    ├── study_summary.json        # Study metadata
    └── study.db                  # Optuna study database
```

### Best Parameters (`best_params.json`)

```json
{
  "lookback": 18,
  "multiplier": 2.2,
  "trailing_stop": 0.025,
  "position_size": 0.10,
  "objective_value": 2.45,
  "sharpe": 1.23,
  "total_return": 0.15,
  "max_drawdown": 0.061
}
```

### Trials Data (`trials.csv`)

| number | value | lookback | multiplier | sharpe | total_return | max_drawdown | state |
|--------|-------|----------|------------|--------|--------------|--------------|-------|
| 0      | 1.23  | 15       | 1.8        | 0.95   | 0.12         | 0.098        | COMPLETE |
| 1      | 2.45  | 18       | 2.2        | 1.23  | 0.15         | 0.061        | COMPLETE |

## 🎯 Supported Strategies

### VolatilityBreakoutStrategy
- **Parameters**: lookback, atr_period, multiplier, trailing_stop, position_size
- **Best for**: Trending markets with high volatility
- **Typical RMD**: 1.5-3.0

### RSIEMAMomentumStrategy  
- **Parameters**: rsi_period, rsi_buy_threshold, rsi_sell_threshold, ema_period, take_profit, stop_loss
- **Best for**: Momentum-based trading in trending markets
- **Typical RMD**: 1.0-2.5

### EMABreakoutConservativeStrategy
- **Parameters**: ema_fast, ema_slow, take_profit, stop_loss, position_size, volatility_threshold
- **Best for**: Conservative trend following
- **Typical RMD**: 1.2-2.8

### BollingerReversionStrategy
- **Parameters**: bb_period, std_dev, take_profit, stop_loss, position_size
- **Best for**: Mean reversion in ranging markets
- **Typical RMD**: 0.8-2.0

### ContrarianVolumeSpikeStrategy
- **Parameters**: volume_period, volume_spike_multiplier, take_profit, stop_loss
- **Best for**: Contrarian trading on volume spikes
- **Typical RMD**: 0.5-1.8

### TrendFollowingADXEMAStrategy
- **Parameters**: adx_threshold, ema_fast, ema_slow, take_profit, stop_loss, trailing_stop
- **Best for**: Strong trend following with ADX confirmation
- **Typical RMD**: 1.0-2.2

## 🔄 Integration with Monitoring

The optimizer integrates seamlessly with the existing monitoring system:

```python
from monitoring.bot_monitor import get_monitor

# During optimization
monitor = get_monitor()
monitor.update_bot_status(
    bot_id="optimizer",
    status="running",
    equity=current_best_value
)
```

## 📈 Performance Tips

### Optimization Settings

1. **Trial Count**: Start with 50-100 trials, increase for better results
2. **Parallel Jobs**: Use `n_jobs=4` for 4-core systems
3. **Parameter Ranges**: Keep ranges reasonable to avoid overfitting
4. **Data Period**: Use at least 6 months of data for reliable results

### Best Practices

1. **Walk-Forward Testing**: Optimize on training data, validate on out-of-sample
2. **Multiple Metrics**: Test with different metrics (RMD, Sharpe, Return)
3. **Parameter Stability**: Check if optimal parameters are stable across time periods
4. **Overfitting Prevention**: Use cross-validation or out-of-sample testing

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure strategy files are in the correct directory
2. **Data File Not Found**: Check data file paths in config
3. **Memory Issues**: Reduce trial count or use fewer parallel jobs
4. **Poor Results**: Expand parameter ranges or increase trial count

### Debug Mode

Add debug logging to see detailed optimization progress:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Example Results

### VolatilityBreakoutStrategy (BTC 24 months)
- **Best RMD**: 2.45
- **Sharpe**: 1.23
- **Total Return**: 15.2%
- **Max Drawdown**: 6.1%
- **Optimal Parameters**:
  - lookback: 18
  - multiplier: 2.2
  - trailing_stop: 2.5%
  - position_size: 10%

### RSIEMAMomentumStrategy (ETH 6 months)
- **Best RMD**: 1.87
- **Sharpe**: 1.45
- **Total Return**: 12.8%
- **Max Drawdown**: 6.8%
- **Optimal Parameters**:
  - rsi_period: 14
  - rsi_buy_threshold: 58
  - ema_period: 34
  - take_profit: 2.8%

## 🔮 Future Enhancements

- [ ] Walk-forward optimization
- [ ] Multi-strategy optimization
- [ ] Real-time parameter updates
- [ ] Integration with live trading
- [ ] Advanced metrics (Calmar ratio, Sortino ratio)
- [ ] Parameter sensitivity analysis
- [ ] Automated re-optimization schedules

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example configurations
3. Ensure all dependencies are installed
4. Verify data file formats and paths

---

**Happy Optimizing! 🚀**
