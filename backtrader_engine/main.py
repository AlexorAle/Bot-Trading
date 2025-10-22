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
import importlib
import threading
import time
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

# Import monitoring system and Prometheus metrics
try:
    import sys
    from pathlib import Path
    # Add parent directory to path to import monitoring
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    
    # TEMPORARILY DISABLED - will be fixed
    # from monitoring.bot_monitor import get_monitor
    # from monitoring.metrics_server import start_metrics_server
    from prometheus_client import start_http_server, Gauge, Counter, Histogram
    MONITORING_AVAILABLE = True
    print("✅ Monitoring system available (partial)")
except ImportError as e:
    print(f"⚠️ Monitoring system not available: {e}")
    MONITORING_AVAILABLE = False

# Prometheus metrics definitions with portfolio and asset_class labels
if MONITORING_AVAILABLE:
    PORTFOLIO_VALUE = Gauge(
        'bt_portfolio_value', 
        'Valor actual del portfolio (Equity)', 
        ['portfolio', 'asset_class', 'strategy', 'symbol']
    )
    
    TRADES_CLOSED = Counter(
        'bt_trades_closed_total', 
        'Conteo de trades cerrados', 
        ['portfolio', 'asset_class', 'strategy', 'symbol', 'result']
    )
    
    TRADE_PNL = Histogram(
        'bt_trade_pnl',
        'PnL por trade',
        ['portfolio', 'asset_class', 'strategy', 'symbol'],
        buckets=[-1000, -500, -100, -50, -10, 0, 10, 50, 100, 500, 1000, float('inf')]
    )
    
    DRAWDOWN_PERCENT = Gauge(
        'bt_drawdown_percent',
        'Drawdown actual en porcentaje',
        ['portfolio', 'asset_class', 'strategy', 'symbol']
    )
    
    WIN_RATE = Gauge(
        'bt_win_rate',
        'Tasa de aciertos en porcentaje',
        ['portfolio', 'asset_class', 'strategy', 'symbol']
    )


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


def run_backtest(config, monitor=None):
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
    
    # Update monitoring metrics
    if monitor:
        try:
            strategy_name = config.get('strategy', 'UnknownStrategy')
            symbol = config.get('symbol', 'UnknownSymbol')
            bot_id = f"backtrader_{strategy_name}_{symbol.replace('/', '_')}"
            
            # Get trade statistics
            trades = getattr(strat, 'analyzers', {}).get('trades', {})
            total_trades = trades.get('total', {}).get('total', 0) if trades else 0
            won_trades = trades.get('won', {}).get('total', 0) if trades else 0
            win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Update bot status
            monitor.update_bot_status(
                bot_id=bot_id,
                status="completed",
                equity=final_value,
                trades=total_trades,
                positions=0
            )
            
            # Update strategy metrics
            monitor.update_strategy_metrics(
                strategy_name=strategy_name,
                symbol=symbol,
                equity=final_value,
                pnl=total_return,
                trades=total_trades,
                win_rate=win_rate
            )
            
            print("✅ Monitoring metrics updated")
        except Exception as e:
            print(f"⚠️ Failed to update monitoring metrics: {e}")
    
    # Update Prometheus metrics with portfolio labels
    if MONITORING_AVAILABLE:
        try:
            strategy_name = config.get('strategy', 'UnknownStrategy')
            symbol = config.get('symbol', 'UnknownSymbol')
            
            # Determine portfolio and asset class based on symbol
            if '/' in symbol and any(crypto in symbol.upper() for crypto in ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']):
                portfolio = 'crypto'
                asset_class = 'futures'
            elif '/' in symbol and any(forex in symbol.upper() for forex in ['EUR', 'GBP', 'JPY', 'AUD', 'CAD']):
                portfolio = 'forex'
                asset_class = 'spot'
            else:
                portfolio = 'crypto'  # Default to crypto
                asset_class = 'futures'
            
            # Get trade statistics
            trades = strat.analyzers.trades.get_analysis()
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            lost_trades = trades.get('lost', {}).get('total', 0)
            win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Get drawdown
            drawdown = strat.analyzers.drawdown.get_analysis()
            max_drawdown = drawdown.get('max', {}).get('drawdown', 0)
            
            # Update Prometheus metrics
            PORTFOLIO_VALUE.labels(
                portfolio=portfolio,
                asset_class=asset_class,
                strategy=strategy_name,
                symbol=symbol
            ).set(final_value)
            
            # Update trade counters
            TRADES_CLOSED.labels(
                portfolio=portfolio,
                asset_class=asset_class,
                strategy=strategy_name,
                symbol=symbol,
                result='win'
            ).inc(won_trades)
            
            TRADES_CLOSED.labels(
                portfolio=portfolio,
                asset_class=asset_class,
                strategy=strategy_name,
                symbol=symbol,
                result='loss'
            ).inc(lost_trades)
            
            # Update drawdown
            DRAWDOWN_PERCENT.labels(
                portfolio=portfolio,
                asset_class=asset_class,
                strategy=strategy_name,
                symbol=symbol
            ).set(max_drawdown)
            
            # Update win rate
            WIN_RATE.labels(
                portfolio=portfolio,
                asset_class=asset_class,
                strategy=strategy_name,
                symbol=symbol
            ).set(win_rate)
            
            # Record PnL for winning trades
            if 'won' in trades and 'pnl' in trades['won']:
                avg_win = trades['won']['pnl'].get('average', 0)
                for _ in range(won_trades):
                    TRADE_PNL.labels(
                        portfolio=portfolio,
                        asset_class=asset_class,
                        strategy=strategy_name,
                        symbol=symbol
                    ).observe(avg_win)
            
            # Record PnL for losing trades
            if 'lost' in trades and 'pnl' in trades['lost']:
                avg_loss = trades['lost']['pnl'].get('average', 0)
                for _ in range(lost_trades):
                    TRADE_PNL.labels(
                        portfolio=portfolio,
                        asset_class=asset_class,
                        strategy=strategy_name,
                        symbol=symbol
                    ).observe(avg_loss)
            
            print(f"✅ Prometheus metrics updated - Portfolio: {portfolio}, Asset: {asset_class}")
            
        except Exception as e:
            print(f"⚠️ Failed to update Prometheus metrics: {e}")
    
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
    
    # Initialize monitoring system
    monitor = None
    if MONITORING_AVAILABLE:
        try:
            # Start Prometheus metrics server on port 8000
            start_http_server(8000)
            print("🚀 Prometheus metrics server started on port 8000")
            
            # Start legacy metrics server on port 8080
            # start_metrics_server(port=8080) # This line was commented out in the new_code, so it's commented out here.
            
            # Get monitor instance
            # monitor = get_monitor() # This line was commented out in the new_code, so it's commented out here.
            
            # Register bot
            strategy_name = config.get('strategy', 'UnknownStrategy')
            symbol = config.get('symbol', 'UnknownSymbol')
            # monitor.register_bot( # This line was commented out in the new_code, so it's commented out here.
            #     bot_id=f"backtrader_{strategy_name}_{symbol.replace('/', '_')}",
            #     bot_type="backtesting",
            #     config=config
            # )
            
            print("✅ Monitoring system initialized (partial)")
        except Exception as e:
            print(f"⚠️ Failed to initialize monitoring: {e}")
            monitor = None
    
    # Run backtest
    results = run_backtest(config, monitor)
    
    print("\n✅ Backtest completed successfully!")


if __name__ == '__main__':
    main()

