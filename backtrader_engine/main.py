#!/usr/bin/env python3
"""
Main entry point for Backtrader Liquidation Hunter Strategy
Supports multiple assets: Crypto (ETH/USDT) and Forex (EUR/USD)
"""

import backtrader as bt
import pandas as pd
import json
import argparse
import sys
from pathlib import Path
from strategies.liquidation_hunter import LiquidationHunterStrategy
from strategies.simple_test import SimpleTestStrategy


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


def load_data(data_file):
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


def run_backtest(config):
    """Run backtest with given configuration"""
    print(f"\n🚀 Starting backtest for {config['symbol']}")
    print("=" * 50)
    
    # Create Cerebro engine
    cerebro = bt.Cerebro()
    
    # Load data
    data_path = Path(__file__).parent / config['data_file']
    df = load_data(data_path)
    
    # Create data feed
    data_feed = PandasData(dataname=df)
    cerebro.adddata(data_feed)
    
    # Add strategy with parameters
    if 'kalman_threshold' in config:
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
        print(f"Winning Trades: {trades['won']['total']}")
        print(f"Losing Trades: {trades['lost']['total']}")
        win_rate = trades['won']['total'] / trades['total']['total'] * 100
        print(f"Win Rate: {win_rate:.2f}%")
    
    # Plot results
    try:
        print("\n📊 Generating plot...")
        cerebro.plot(style='candlestick', barup='green', bardown='red')
    except Exception as e:
        print(f"⚠️  Plot generation failed: {e}")
    
    return results


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
    
    # Run backtest
    results = run_backtest(config)
    
    print("\n✅ Backtest completed successfully!")


if __name__ == '__main__':
    main()

