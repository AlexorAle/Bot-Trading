#!/usr/bin/env python3
"""
Main entry point for Backtrader Liquidation Hunter Strategy
Supports multiple assets: Crypto (ETH/USDT) and Forex (EUR/USD)
"""

import backtrader as bt
import pandas as pd
import json
import argparse
import os
import sys
from pathlib import Path

from strategies.liquidation_hunter import LiquidationHunterStrategy
from strategies.simple_test import SimpleTestStrategy
from strategies.ema_breakout import EMABreakoutStrategy
from strategies.ema_breakout_conservative import EMABreakoutConservativeStrategy
from strategies.ema_breakout_aggressive import EMABreakoutAggressiveStrategy
from strategies.volatility_breakout import VolatilityBreakoutStrategy
from strategies.bollinger_reversion import BollingerReversionStrategy
from strategies.rsi_ema_momentum import RSIEMAMomentumStrategy
from strategies.contrarian_volume import ContrarianVolumeSpikeStrategy
from strategies.trend_following_adx_ema import TrendFollowingADXEMAStrategy

from monitoring.metrics_server import MetricsServer
from monitoring.log_metrics_updater import LogMetricsUpdater
from monitoring.bot_monitor import BotMonitor
from config import load_monitoring_config


class PandasData(bt.feeds.PandasData):
    """Custom data feed for pandas DataFrames"""
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )


def load_config(config_path):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"✅ Config loaded: {config_path}")
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)


def load_data(data_file, start_date=None, end_date=None):
    """Load and prepare data from CSV file"""
    try:
        # Read CSV file
        df = pd.read_csv(data_file)
        
        # Ensure datetime column is properly formatted
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        elif 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'])
        else:
            # Assume first column is datetime
            df['datetime'] = pd.to_datetime(df.iloc[:, 0])
        
        # Set datetime as index
        df.set_index('datetime', inplace=True)
        
        # Filter by date range if specified
        if start_date:
            df = df[df.index >= start_date]
            print(f"📅 Filtered from {start_date}")
        if end_date:
            df = df[df.index <= end_date]
            print(f"📅 Filtered to {end_date}")
        
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close']
        for col in required_columns:
            if col not in df.columns:
                print(f"❌ Missing required column: {col}")
                sys.exit(1)
        
        # Add volume if not present
        if 'volume' not in df.columns:
            df['volume'] = 1000000  # Default volume
        
        print(f"✅ Data loaded: {len(df)} bars from {df.index[0]} to {df.index[-1]}")
        return df
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        sys.exit(1)


def run_backtest(config, monitoring_snapshot_callback=None):
    """Run backtest with given configuration"""
    print(f"\n🚀 Starting backtest for {config['symbol']}")
    print("=" * 50)
    
    # Create Cerebro engine
    cerebro = bt.Cerebro()
    
    # Load data
    data_path = Path(__file__).parent / config['data_file']
    start_date = config.get('start_date')
    end_date = config.get('end_date')
    df = load_data(data_path, start_date, end_date)
    
    # Create data feed
    data_feed = PandasData(dataname=df)
    cerebro.adddata(data_feed)
    
    # Add strategy with parameters - Dynamic strategy loading
    strategy_name = config.get('strategy', 'LiquidationHunterStrategy')
    
    if strategy_name == 'EMABreakoutConservativeStrategy':
        # Conservative EMA Breakout with filters
        cerebro.addstrategy(EMABreakoutConservativeStrategy,
                           ema_fast=config['ema_fast'],
                           ema_slow=config['ema_slow'],
                           take_profit=config['take_profit'],
                           stop_loss=config['stop_loss'],
                           position_size=config['position_size'],
                           volatility_threshold=config['volatility_threshold'],
                           trend_ema_fast=config['trend_ema_fast'],
                           trend_ema_slow=config['trend_ema_slow'])
    elif strategy_name == 'EMABreakoutAggressiveStrategy':
        # Aggressive EMA Breakout with filters
        cerebro.addstrategy(EMABreakoutAggressiveStrategy,
                           ema_fast=config['ema_fast'],
                           ema_slow=config['ema_slow'],
                           take_profit=config['take_profit'],
                           stop_loss=config['stop_loss'],
                           position_size=config['position_size'],
                           volatility_threshold=config['volatility_threshold'],
                           volume_period=config['volume_period'],
                           trend_ema_fast=config['trend_ema_fast'],
                           trend_ema_slow=config['trend_ema_slow'])
    elif strategy_name == 'EMABreakoutStrategy':
        # EMA Breakout Strategy
        cerebro.addstrategy(EMABreakoutStrategy,
                           ema_fast=config['ema_fast'],
                           ema_slow=config['ema_slow'],
                           take_profit=config['take_profit'],
                           stop_loss=config['stop_loss'],
                           position_size=config['position_size'])
    elif strategy_name == 'VolatilityBreakoutStrategy':
        # Volatility Breakout Strategy
        cerebro.addstrategy(VolatilityBreakoutStrategy,
                           lookback=config['lookback'],
                           atr_period=config['atr_period'],
                           multiplier=config['multiplier'],
                           trailing_stop=config['trailing_stop'],
                           position_size=config['position_size'])
    elif strategy_name == 'BollingerReversionStrategy':
        # Bollinger Bands Reversion Strategy
        cerebro.addstrategy(BollingerReversionStrategy,
                           bb_period=config['bb_period'],
                           std_dev=config['std_dev'],
                           volume_filter_period=config['volume_filter_period'],
                           position_size=config['position_size'],
                           take_profit=config['take_profit'],
                           stop_loss=config['stop_loss'])
    elif strategy_name == 'RSIEMAMomentumStrategy':
        # RSI + EMA Momentum Strategy
        cerebro.addstrategy(RSIEMAMomentumStrategy,
                           rsi_period=config['rsi_period'],
                           rsi_buy_threshold=config['rsi_buy_threshold'],
                           rsi_sell_threshold=config['rsi_sell_threshold'],
                           ema_period=config['ema_period'],
                           position_size=config['position_size'],
                           take_profit=config['take_profit'],
                           stop_loss=config['stop_loss'])
    elif strategy_name == 'ContrarianVolumeSpikeStrategy':
        # Contrarian Volume Spike Strategy
        cerebro.addstrategy(ContrarianVolumeSpikeStrategy,
                           volume_period=config['volume_period'],
                           volume_spike_multiplier=config['volume_spike_multiplier'],
                           spread_threshold=config['spread_threshold'],
                           position_size=config['position_size'],
                           stop_loss=config['stop_loss'],
                           take_profit=config['take_profit'],
                           rsi_period=config['rsi_period'])
    elif strategy_name == 'TrendFollowingADXEMAStrategy':
        # Trend Following ADX + EMA Strategy
        cerebro.addstrategy(TrendFollowingADXEMAStrategy,
                           adx_period=config['adx_period'],
                           adx_threshold=config['adx_threshold'],
                           ema_fast=config['ema_fast'],
                           ema_slow=config['ema_slow'],
                           position_size=config['position_size'],
                           take_profit=config['take_profit'],
                           stop_loss=config['stop_loss'],
                           trailing_stop=config['trailing_stop'])
    elif 'kalman_threshold' in config:
        # Full LiquidationHunterStrategy
        cerebro.addstrategy(LiquidationHunterStrategy,
                           kalman_threshold=config['kalman_threshold'],
                           deviation_threshold=config['deviation_threshold'],
                           ml_confidence_threshold=config['ml_confidence_threshold'],
                           rsi_period=config['rsi_period'],
                           ema_fast_period=config['ema_fast_period'],
                           ema_slow_period=config['ema_slow_period'],
                           stop_loss=config['stop_loss'],
                           take_profit=config['take_profit'],
                           position_size=config['position_size'])
    else:
        # Simple test strategy
        cerebro.addstrategy(SimpleTestStrategy,
                           rsi_period=config['rsi_period'],
                           stop_loss=config['stop_loss'],
                           take_profit=config['take_profit'],
                           position_size=config['position_size'])
    
    # Set initial cash
    cerebro.broker.setcash(config['initial_cash'])
    
    # Set commission
    cerebro.broker.setcommission(commission=config['commission'])
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Print starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")
    
    # Run backtest
    results = cerebro.run()
    
    # Get final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ${final_value:.2f}")
    
    # Calculate returns
    total_return = (final_value - config['initial_cash']) / config['initial_cash'] * 100
    print(f"Total Return: {total_return:.2f}%")
    
    # Get analyzer results
    strat = results[0]
    
    # Create detailed report
    report = generate_detailed_report(strat, config, final_value, total_return)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 RESUMEN EJECUTIVO")
    print("="*60)
    
    # Sharpe Ratio
    sharpe = strat.analyzers.sharpe.get_analysis()
    if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
        print(f"Sharpe Ratio: {sharpe['sharperatio']:.2f}")
    
    # Drawdown
    drawdown = strat.analyzers.drawdown.get_analysis()
    print(f"Max Drawdown: {drawdown['max']['drawdown']:.2f}%")
    
    # Trade Analysis
    trades = strat.analyzers.trades.get_analysis()
    if 'total' in trades and trades['total']['total'] > 0:
        print(f"Total Trades: {trades['total']['total']}")
        
        # Safe access to won/lost trades
        won_trades = trades.get('won', {}).get('total', 0)
        lost_trades = trades.get('lost', {}).get('total', 0)
        
        print(f"Winning Trades: {won_trades}")
        print(f"Losing Trades: {lost_trades}")
        
        if trades['total']['total'] > 0:
            win_rate = won_trades / trades['total']['total'] * 100
            print(f"Win Rate: {win_rate:.2f}%")
        
        # Additional metrics
        if 'won' in trades and 'pnl' in trades['won']:
            avg_win = trades['won']['pnl']['average']
            print(f"Average Win: ${avg_win:.2f}")
        if 'lost' in trades and 'pnl' in trades['lost']:
            avg_loss = trades['lost']['pnl']['average']
            print(f"Average Loss: ${avg_loss:.2f}")
    
    # Save detailed report
    save_report_to_file(report, config['symbol'])
    
    # Plot results
    try:
        print("\n📊 Generating plot...")
        cerebro.plot(style='candlestick', barup='green', bardown='red')
    except Exception as e:
        print(f"⚠️  Plot generation failed: {e}")
    
    if callable(monitoring_snapshot_callback):
        try:
            monitoring_snapshot_callback()
        except Exception as exc:
            print(f"⚠️ Monitoring callback failed: {exc}")

    return results


def generate_detailed_report(strat, config, final_value, total_return):
    """Generate detailed trading report"""
    report = {
        'config': config,
        'performance': {
            'initial_cash': config['initial_cash'],
            'final_value': final_value,
            'total_return': total_return
        },
        'analyzers': {}
    }
    
    # Collect all analyzer data
    analyzers = ['sharpe', 'drawdown', 'returns', 'trades']
    for analyzer_name in analyzers:
        if hasattr(strat.analyzers, analyzer_name):
            analyzer = getattr(strat.analyzers, analyzer_name)
            report['analyzers'][analyzer_name] = analyzer.get_analysis()
    
    return report

def save_report_to_file(report, symbol):
    """Save detailed report to JSON file"""
    import json
    from datetime import datetime
    
    # Create reports directory if it doesn't exist
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    symbol_clean = symbol.replace('/', '_').replace('\\', '_')
    filename = f"backtest_report_{symbol_clean}_{timestamp}.json"
    filepath = reports_dir / filename
    
    # Save report
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Reporte detallado guardado en: {filepath}")
    return filepath

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Liquidation Hunter Backtrader Strategy')
    parser.add_argument('--config', type=str, required=True,
                       help='Path to configuration JSON file')
    parser.add_argument('--plot', action='store_true',
                       help='Show plot after backtest')
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(__file__).parent / args.config
    config = load_config(config_path)
    
    monitoring_env = os.getenv("MONITORING_ENV", "development")
    try:
        monitoring_config = load_monitoring_config(env=monitoring_env)
    except Exception as exc:
        print(f"⚠️ Monitoring config load failed: {exc}")
        monitoring_config = None
    metrics_server = None
    log_updater = None
    bot_monitor = None

    if monitoring_config:
        try:
            log_updater = LogMetricsUpdater(
                directories=monitoring_config.get("log_directories", []),
                bot_types=monitoring_config.get("bot_types", ["crypto"]),
            )

            metrics_server = MetricsServer(monitoring_config)
            metrics_server.set_log_updater(log_updater)
            metrics_server.start()

            bot_monitor = BotMonitor()
            bot_monitor.start_monitoring(metrics_server)

        except Exception as exc:
            print(f"⚠️ Monitoring setup failed: {exc}")
            metrics_server = None
            log_updater = None
            bot_monitor = None

    results = run_backtest(
        config,
        monitoring_snapshot_callback=(
            lambda: metrics_server._update_metrics_from_snapshot(
                log_updater.collect_snapshot()
            )
            if metrics_server and log_updater
            else None
        ),
    )
    
    print("\n✅ Backtest completed successfully!")

    if metrics_server:
        metrics_server.stop()
    if bot_monitor:
        bot_monitor.stop_monitoring()


if __name__ == '__main__':
    main()

