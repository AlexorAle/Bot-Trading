#!/usr/bin/env python3
"""
Portfolio Engine for Multi-Strategy Backtesting

Este motor permite ejecutar múltiples estrategias de trading simultáneamente
sobre diferentes símbolos y timeframes, proporcionando análisis comparativo
y métricas de portfolio consolidado.
"""

import backtrader as bt
import pandas as pd
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from monitoring.logger import get_monitoring_logger

# Importar todas las estrategias
from strategies.volatility_breakout import VolatilityBreakoutStrategy
from strategies.bollinger_reversion import BollingerReversionStrategy
from strategies.rsi_ema_momentum import RSIEMAMomentumStrategy
from strategies.ema_breakout_conservative import EMABreakoutConservativeStrategy
from strategies.contrarian_volume import ContrarianVolumeSpikeStrategy
from strategies.trend_following_adx_ema import TrendFollowingADXEMAStrategy

# Importar Market Regime Detector
from market_regime_detector import MarketRegimeDetector, Regime

# Importar Risk Parity Allocator
from risk_parity_allocator import RiskParityAllocator, AllocationResult

# Importar StrategyHandle
from strategy_handle import StrategyHandle, StrategyHandleManager

# Importar Hybrid Logger
from hybrid_logger import HybridLogger, StrategyHandleLogger, RiskParityLogger, RegimeDetectionLogger


class PandasData(bt.feeds.PandasData):
    """Custom data feed for pandas DataFrames"""
    params = (
        ('datetime', None),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1)
    )


class PortfolioEngine:
    """Motor principal para ejecutar múltiples estrategias con Market Regime Detection, Risk Parity y StrategyHandle"""
    
    def __init__(self, enable_regime_detection: bool = True, enable_risk_parity: bool = True, enable_strategy_handle: bool = True):
        self.strategies = {
            'VolatilityBreakoutStrategy': VolatilityBreakoutStrategy,
            'BollingerReversionStrategy': BollingerReversionStrategy,
            'RSIEMAMomentumStrategy': RSIEMAMomentumStrategy,
            'EMABreakoutConservativeStrategy': EMABreakoutConservativeStrategy,
            'ContrarianVolumeSpikeStrategy': ContrarianVolumeSpikeStrategy,
            'TrendFollowingADXEMAStrategy': TrendFollowingADXEMAStrategy,
        }
        self.results = {}
        self.enable_regime_detection = enable_regime_detection
        self.enable_risk_parity = enable_risk_parity
        self.enable_strategy_handle = enable_strategy_handle
        self.regime_detector = None
        self.risk_parity_allocator = None
        self.strategy_handle_manager = None
        self.regime_history = {}
        self.allocation_history = {}
        self.equity_curves = {}
        self.hybrid_logger = None
        self.monitoring_logger = get_monitoring_logger("portfolio_engine")
        
        if enable_regime_detection:
            print("🎯 Market Regime Detection ENABLED")
        else:
            print("⚠️  Market Regime Detection DISABLED - All strategies will run")
            
        if enable_risk_parity:
            print("⚖️  Risk Parity Allocation ENABLED")
        else:
            print("⚠️  Risk Parity Allocation DISABLED - Fixed weights will be used")
            
        if enable_strategy_handle:
            print("🎮 StrategyHandle Wrapper ENABLED")
        else:
            print("⚠️  StrategyHandle Wrapper DISABLED - Direct strategy execution")
        
        # Initialize Hybrid Logger
        self.hybrid_logger = HybridLogger()
        print("📊 Hybrid Logging System ENABLED")
        
    def load_data(self, data_file: str, start_date: Optional[str] = None, 
                  end_date: Optional[str] = None) -> pd.DataFrame:
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

    def initialize_regime_detector(self, data_file: str) -> None:
        """Initialize Market Regime Detector with data"""
        if not self.enable_regime_detection:
            return
            
        try:
            print("\n🎯 Initializing Market Regime Detector...")
            
            # Load full data for regime detection (no date filtering)
            data_path = Path(__file__).parent / data_file
            df = self.load_data(data_path)
            
            # Initialize detector
            self.regime_detector = MarketRegimeDetector()
            
            # Prepare daily data and calculate indicators
            daily_df = self.regime_detector.prepare_daily_data(df)
            self.regime_detector.calculate_indicators(daily_df)
            
            print("✅ Market Regime Detector initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing regime detector: {e}")
            self.enable_regime_detection = False

    def initialize_risk_parity_allocator(self, method: str = "max_dd", lookback: int = 365) -> None:
        """Initialize Risk Parity Allocator"""
        if not self.enable_risk_parity:
            return
            
        try:
            print(f"\n⚖️  Initializing Risk Parity Allocator...")
            print(f"   Method: {method}, Lookback: {lookback} days")
            
            self.risk_parity_allocator = RiskParityAllocator(
                method=method,
                lookback=lookback,
                w_min=0.05,  # 5% mínimo
                w_max=0.40,  # 40% máximo
                rebalance_threshold=0.20  # 20% umbral de rebalance
            )
            
            print("✅ Risk Parity Allocator initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing risk parity allocator: {e}")
            self.enable_risk_parity = False

    def initialize_strategy_handle_manager(self, symbol: str) -> None:
        """Initialize StrategyHandle Manager for a symbol"""
        if not self.enable_strategy_handle:
            return
            
        try:
            print(f"\n🎮 Initializing StrategyHandle Manager for {symbol}...")
            
            self.strategy_handle_manager = StrategyHandleManager()
            
            # Crear handles para todas las estrategias disponibles
            for strategy_name, strategy_class in self.strategies.items():
                # Crear cerebro temporal para cada estrategia
                temp_cerebro = bt.Cerebro()
                
                # Configuración base
                base_config = {
                    'symbol': symbol,
                    'initial_cash': 10000,
                    'commission': 0.001
                }
                
                # Crear handle
                handle = StrategyHandle(
                    strategy_name=strategy_name,
                    strategy_class=strategy_class,
                    cerebro=temp_cerebro,
                    config=base_config,
                    hybrid_logger=self.hybrid_logger
                )
                
                # Configurar callbacks
                handle.set_callbacks(
                    on_enable=self._on_strategy_enable,
                    on_disable=self._on_strategy_disable,
                    on_sync=self._on_strategy_sync
                )
                
                # Agregar al manager
                self.strategy_handle_manager.add_strategy(handle)
            
            print(f"✅ StrategyHandle Manager initialized with {len(self.strategies)} strategies")
            
        except Exception as e:
            print(f"❌ Error initializing strategy handle manager: {e}")
            self.enable_strategy_handle = False

    def _on_strategy_enable(self, handle: StrategyHandle) -> None:
        """Callback cuando se habilita una estrategia"""
        print(f"🎮 Strategy {handle.strategy_name} ENABLED")

    def _on_strategy_disable(self, handle: StrategyHandle) -> None:
        """Callback cuando se deshabilita una estrategia"""
        print(f"🎮 Strategy {handle.strategy_name} DISABLED")

    def _on_strategy_sync(self, handle: StrategyHandle, target_value: float, current_value: float) -> None:
        """Callback cuando se sincroniza una estrategia"""
        print(f"🎮 Strategy {handle.strategy_name} synced: ${current_value:.2f} → ${target_value:.2f}")

    def manage_strategies_by_regime(self, symbol: str, active_strategies: List[str]) -> None:
        """Gestionar estrategias según el régimen de mercado"""
        if not self.enable_strategy_handle or not self.strategy_handle_manager:
            return
            
        try:
            # Deshabilitar estrategias no activas
            all_strategies = list(self.strategies.keys())
            inactive_strategies = [s for s in all_strategies if s not in active_strategies]
            
            for strategy_name in inactive_strategies:
                if self.strategy_handle_manager.handles[strategy_name].state.enabled:
                    self.strategy_handle_manager.disable_strategy(strategy_name)
            
            # Habilitar estrategias activas
            for strategy_name in active_strategies:
                if not self.strategy_handle_manager.handles[strategy_name].state.enabled:
                    self.strategy_handle_manager.enable_strategy(strategy_name)
            
            print(f"🎮 Managed {len(active_strategies)} active strategies for {symbol}")
            
        except Exception as e:
            print(f"⚠️  Error managing strategies by regime: {e}")

    def sync_strategies_with_risk_parity(self, symbol: str, weights: Dict[str, float], total_portfolio_value: float) -> None:
        """Sincronizar estrategias con pesos de Risk Parity"""
        if not self.enable_strategy_handle or not self.strategy_handle_manager:
            return
            
        try:
            # Calcular valores objetivo
            target_values = {}
            for strategy_name, weight in weights.items():
                target_values[strategy_name] = total_portfolio_value * weight
            
            # Sincronizar estrategias
            results = self.strategy_handle_manager.sync_strategies(target_values)
            
            # Log resultados
            for strategy_name, success in results.items():
                if success:
                    print(f"🎮 Strategy {strategy_name} synced to ${target_values[strategy_name]:.2f}")
                else:
                    print(f"⚠️  Failed to sync strategy {strategy_name}")
            
        except Exception as e:
            print(f"⚠️  Error syncing strategies with risk parity: {e}")

    def get_strategy_handles_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtener estado de todos los StrategyHandles"""
        if not self.enable_strategy_handle or not self.strategy_handle_manager:
            return {}
            
        return self.strategy_handle_manager.get_all_status()

    def update_equity_curve(self, strategy_name: str, symbol: str, equity_curve: pd.Series) -> None:
        """Update equity curve for a strategy"""
        if not self.enable_risk_parity or not self.risk_parity_allocator:
            return
            
        try:
            key = f"{symbol}_{strategy_name}"
            self.equity_curves[key] = equity_curve
            self.risk_parity_allocator.update_equity_curve(key, equity_curve)
            print(f"[RISK PARITY] Updated equity curve for {key}: {len(equity_curve)} points")
            
        except Exception as e:
            print(f"⚠️  Error updating equity curve for {strategy_name}: {e}")

    def get_risk_parity_weights(self, symbol: str, active_strategies: List[str]) -> Dict[str, float]:
        """Get Risk Parity weights for active strategies"""
        if not self.enable_risk_parity or not self.risk_parity_allocator:
            # Return equal weights if Risk Parity is disabled
            if active_strategies:
                equal_weight = 1.0 / len(active_strategies)
                return {strategy: equal_weight for strategy in active_strategies}
            return {}
        
        try:
            # Get strategy keys for this symbol
            strategy_keys = [f"{symbol}_{strategy}" for strategy in active_strategies]
            
            # Calculate Risk Parity allocation
            result = self.risk_parity_allocator.compute_weights(strategy_keys)
            
            # Convert back to strategy names
            weights = {}
            for key, weight in result.weights.items():
                strategy_name = key.replace(f"{symbol}_", "")
                weights[strategy_name] = weight
            
            # Store allocation history
            if symbol not in self.allocation_history:
                self.allocation_history[symbol] = []
            self.allocation_history[symbol].append({
                'timestamp': datetime.now(),
                'weights': weights.copy(),
                'risk_metrics': result.risk_metrics.copy(),
                'rebalanced': result.rebalanced,
                'drift': result.drift
            })
            
            print(f"⚖️  Risk Parity weights: {weights}")
            
            # Hybrid logging
            if self.hybrid_logger:
                risk_parity_logger = RiskParityLogger(self.hybrid_logger)
                risk_parity_logger.log_allocation(
                    strategy_names=active_strategies,
                    allocation_result=result,
                    weights=weights,
                    drift=result.drift,
                    rebalanced=result.rebalanced
                )
            
            return weights
            
        except Exception as e:
            print(f"⚠️  Error calculating Risk Parity weights: {e}")
            # Fallback to equal weights
            if active_strategies:
                equal_weight = 1.0 / len(active_strategies)
                return {strategy: equal_weight for strategy in active_strategies}
            return {}

    def get_active_strategies(self, timestamp: datetime, symbol: str) -> List[str]:
        """Get list of active strategies based on current market regime"""
        if not self.enable_regime_detection or not self.regime_detector:
            # Return all strategies if regime detection is disabled
            return list(self.strategies.keys())
        
        try:
            # Get current regime
            regime = self.regime_detector.regime_at(timestamp)
            
            # Store regime history
            if symbol not in self.regime_history:
                self.regime_history[symbol] = []
            self.regime_history[symbol].append({
                'timestamp': timestamp,
                'regime': regime.name,
                'trend': regime.trend,
                'vol_bucket': regime.vol_bucket,
                'strategies': regime.strategy_whitelist
            })
            
            print(f"🎯 Market Regime: {regime.name} - Active strategies: {regime.strategy_whitelist}")
            
            # Hybrid logging
            if self.hybrid_logger:
                regime_logger = RegimeDetectionLogger(self.hybrid_logger)
                regime_logger.log_regime_analysis(
                    regime=regime.name,
                    trend=regime.trend,
                    volatility=regime.vol_bucket,
                    active_strategies=regime.strategy_whitelist,
                    symbol=symbol,
                    timestamp=timestamp.isoformat()
                )
            
            return regime.strategy_whitelist
            
        except Exception as e:
            print(f"⚠️  Error getting regime, using all strategies: {e}")
            return list(self.strategies.keys())

    def print_regime_summary(self, symbol: str) -> None:
        """Print regime detection summary for a symbol"""
        if not self.enable_regime_detection or not self.regime_detector:
            return
            
        print(f"\n📊 Market Regime Summary for {symbol}")
        print("=" * 50)
        
        if symbol in self.regime_history:
            history = self.regime_history[symbol]
            
            # Count regimes
            regime_counts = {}
            for entry in history:
                regime = entry['regime']
                regime_counts[regime] = regime_counts.get(regime, 0) + 1
            
            print("📈 Regime Distribution:")
            total = len(history)
            for regime, count in regime_counts.items():
                percentage = (count / total) * 100
                print(f"  {regime}: {count} periods ({percentage:.1f}%)")
            
            # Current regime
            if history:
                current = history[-1]
                print(f"\n🎯 Current Regime: {current['regime']}")
                print(f"   Trend: {current['trend']}")
                print(f"   Volatility: {current['vol_bucket']}")
                print(f"   Active Strategies: {', '.join(current['strategies'])}")

    def run_single_strategy(self, strategy_name: str, symbol: str, 
                          data_file: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single strategy and return results"""
        print(f"\n🚀 Running {strategy_name} on {symbol}")
        print("=" * 60)
        
        # Create Cerebro engine
        cerebro = bt.Cerebro()
        
        # Load data
        data_path = Path(__file__).parent / data_file
        start_date = config.get('start_date')
        end_date = config.get('end_date')
        df = self.load_data(data_path, start_date, end_date)
        
        # Create data feed
        data_feed = PandasData(dataname=df)
        cerebro.adddata(data_feed)
        
        # Add strategy with parameters
        strategy_class = self.strategies[strategy_name]
        
        # Extract strategy-specific parameters
        strategy_params = {k: v for k, v in config.items() 
                          if k not in ['strategy', 'symbol', 'data_file', 'timeframe', 'commission', 
                                     'initial_cash', 'start_date', 'end_date']}
        
        cerebro.addstrategy(strategy_class, **strategy_params)
        
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
        
        # Calculate returns
        total_return = (final_value - config['initial_cash']) / config['initial_cash'] * 100
        
        # Get analyzer results
        strat = results[0]
        
        # Create detailed report
        report = self.generate_strategy_report(strat, config, final_value, total_return)
        
        # Save strategy result to hybrid logger
        if self.hybrid_logger:
            self.hybrid_logger.save_strategy_result(strategy_name, report)
        
        # Capture equity curve for Risk Parity
        if self.enable_risk_parity:
            try:
                # Get equity curve from cerebro
                equity_curve = pd.Series(
                    [cerebro.broker.getvalue()] * len(df),
                    index=df.index
                )
                self.update_equity_curve(strategy_name, symbol, equity_curve)
            except Exception as e:
                print(f"⚠️  Error capturing equity curve for {strategy_name}: {e}")
        
        # Print summary
        try:
            self.print_strategy_summary(strategy_name, strat, total_return)
        except Exception as e:
            print(f"❌ Error running {strategy_name} on {symbol}: {e}")
            report['error'] = str(e)
        
        return report

    def generate_strategy_report(self, strat, config: Dict[str, Any], 
                               final_value: float, total_return: float) -> Dict[str, Any]:
        """Generate detailed report for a single strategy"""
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

    def print_strategy_summary(self, strategy_name: str, strat, total_return: float):
        """Print summary for a single strategy"""
        print(f"\n📊 {strategy_name} - RESUMEN")
        print("=" * 40)
        print(f"Total Return: {total_return:.2f}%")

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

    def run_portfolio(self, symbols: List[str], strategies: List[str], 
                     configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Run multiple strategies on multiple symbols with Market Regime Detection, Risk Parity and StrategyHandle"""
        print(f"\n🎯 PORTFOLIO BACKTESTING")
        print(f"Symbols: {symbols}")
        print(f"Strategies: {strategies}")
        if self.enable_regime_detection:
            print("🎯 Market Regime Detection: ENABLED")
        else:
            print("⚠️  Market Regime Detection: DISABLED")
        if self.enable_risk_parity:
            print("⚖️  Risk Parity Allocation: ENABLED")
        else:
            print("⚠️  Risk Parity Allocation: DISABLED")
        if self.enable_strategy_handle:
            print("🎮 StrategyHandle Wrapper: ENABLED")
        else:
            print("⚠️  StrategyHandle Wrapper: DISABLED")
        print("=" * 80)
        
        portfolio_results = {}
        self.monitoring_logger.info("Starting portfolio run for symbols: %s", symbols)
        
        for symbol in symbols:
            print(f"\n📈 PROCESSING {symbol}")
            print("-" * 50)
            
            # Initialize regime detector for this symbol
            if self.enable_regime_detection:
                if symbol == 'BTCUSDT':
                    self.initialize_regime_detector('data/BTCUSDT_15min.csv')
                elif symbol == 'ETHUSDT':
                    self.initialize_regime_detector('data/ETHUSDT_15min.csv')
                else:
                    print(f"⚠️  No data file configured for regime detection on {symbol}")
            
            # Initialize Risk Parity Allocator
            if self.enable_risk_parity:
                self.initialize_risk_parity_allocator(method="max_dd", lookback=180)
            
            # Initialize StrategyHandle Manager
            if self.enable_strategy_handle:
                self.initialize_strategy_handle_manager(symbol)
            
            symbol_results = {}
            
            for strategy_name in strategies:
                if strategy_name in configs:
                    config = configs[strategy_name].copy()
                    config['symbol'] = symbol
                    
                    # Use appropriate data file for symbol
                    if symbol == 'BTCUSDT':
                        config['data_file'] = 'data/BTCUSDT_15min.csv'
                    elif symbol == 'ETHUSDT':
                        config['data_file'] = 'data/ETHUSDT_15min.csv'
                    else:
                        print(f"⚠️  No data file configured for {symbol}")
                        continue
                    
                    # Check if strategy should be active based on regime
                    active_strategies = []
                    if self.enable_regime_detection and self.regime_detector:
                        # Get regime for the start date of backtest
                        start_date = config.get('start_date', '2025-04-01')
                        try:
                            regime_timestamp = pd.to_datetime(start_date)
                            active_strategies = self.get_active_strategies(regime_timestamp, symbol)
                            
                            if strategy_name not in active_strategies:
                                print(f"⏸️  {strategy_name} DISABLED by regime detection")
                                symbol_results[strategy_name] = {
                                    'error': f'Strategy disabled by regime detection',
                                    'regime': 'DISABLED'
                                }
                                continue
                        except Exception as e:
                            print(f"⚠️  Error checking regime for {strategy_name}: {e}")
                    else:
                        # If regime detection is disabled, all strategies are active
                        active_strategies = strategies
                    
                # Manage strategies with StrategyHandle
                if self.enable_strategy_handle and active_strategies:
                    self.manage_strategies_by_regime(symbol, active_strategies)
                
                try:
                    result = self.run_single_strategy(strategy_name, symbol, 
                                                    config['data_file'], config)
                    symbol_results[strategy_name] = result
                except Exception as e:
                    print(f"❌ Error running {strategy_name} on {symbol}: {e}")
                    symbol_results[strategy_name] = {'error': str(e)}
                
                # Calculate Risk Parity weights after each strategy
                if self.enable_risk_parity and active_strategies:
                    risk_parity_weights = self.get_risk_parity_weights(symbol, active_strategies)
                    if risk_parity_weights:
                        print(f"⚖️  Risk Parity weights for {symbol}: {risk_parity_weights}")
            
            # Print regime summary for this symbol
            if self.enable_regime_detection:
                self.print_regime_summary(symbol)
            
            # Calculate portfolio metrics for this symbol
            if symbol_results:
                portfolio_metrics = self.calculate_portfolio_metrics(symbol_results)
                symbol_results['PortfolioTotal'] = portfolio_metrics
            
            portfolio_results[symbol] = symbol_results
        
        self._last_portfolio_metrics = portfolio_results
        return portfolio_results

    def get_monitoring_snapshot(self) -> Dict[str, Any]:
        strategies_snapshot = []
        portfolio_snapshot = {}

        results = getattr(self, "_last_portfolio_metrics", {})

        for symbol, symbol_results in results.items():
            if not isinstance(symbol_results, dict):
                continue

            portfolio_total = symbol_results.get("PortfolioTotal")
            if isinstance(portfolio_total, dict) and "error" not in portfolio_total:
                equity = 0.0
                final_value = portfolio_total.get("total_value")
                if final_value is None:
                    final_value = sum(
                        data.get("performance", {}).get("final_value", 0.0)
                        for name, data in symbol_results.items()
                        if name != "PortfolioTotal" and isinstance(data, dict)
                    )
                equity = final_value

                portfolio_snapshot[symbol] = {
                    "portfolio_type": symbol,
                    "bot_type": "crypto",
                    "equity": equity,
                    "drawdown": portfolio_total.get("max_drawdown"),
                }

            for strategy_name, data in symbol_results.items():
                if strategy_name == "PortfolioTotal" or not isinstance(data, dict):
                    continue
                performance = data.get("performance", {})
                analyzers = data.get("analyzers", {})
                trades_info = analyzers.get("trades", {})
                trades = trades_info.get("total", {}).get("total")
                win_rate = 0.0
                if trades:
                    won = trades_info.get("won", {}).get("total", 0)
                    win_rate = (won / trades) * 100

                strategies_snapshot.append(
                    {
                        "strategy_id": strategy_name,
                        "asset": symbol,
                        "portfolio_type": symbol,
                        "bot_type": "crypto",
                        "trades": trades or 0,
                        "win_rate": win_rate,
                        "pnl": performance.get("total_return", 0.0),
                        "trades_increment": 0,
                    }
                )

        latest_regime = None
        if self.regime_history:
            symbol = next(iter(self.regime_history))
            history = self.regime_history[symbol]
            if history:
                latest = history[-1]
                latest_regime = {
                    "state": latest.get("regime"),
                    "volatility": latest.get("vol_bucket"),
                    "bot_type": "crypto",
                }

        return {
            "portfolio": portfolio_snapshot,
            "strategies": strategies_snapshot,
            "regime": latest_regime,
            "bot_type": "crypto",
        }

    def calculate_portfolio_metrics(self, symbol_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio-level metrics"""
        valid_results = {k: v for k, v in symbol_results.items() 
                        if 'error' not in v and 'performance' in v}
        
        if not valid_results:
            return {'error': 'No valid results to aggregate'}
        
        # Calculate weighted averages (equal weight for now)
        total_return = sum(r['performance']['total_return'] for r in valid_results.values()) / len(valid_results)
        
        # Calculate portfolio drawdown (simplified)
        max_drawdown = max(r['analyzers'].get('drawdown', {}).get('max', {}).get('drawdown', 0) 
                          for r in valid_results.values())
        
        # Calculate total trades
        total_trades = sum(r['analyzers'].get('trades', {}).get('total', {}).get('total', 0) 
                          for r in valid_results.values())
        
        # Calculate total winning trades
        total_wins = sum(r['analyzers'].get('trades', {}).get('won', {}).get('total', 0) 
                        for r in valid_results.values())
        
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'strategies_count': len(valid_results)
        }

    def save_portfolio_report(self, results: Dict[str, Any], filename: str = None):
        """Save portfolio results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_report_{timestamp}.json"
        
        reports_dir = Path(__file__).parent / 'reports'
        reports_dir.mkdir(exist_ok=True)
        filepath = reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Portfolio report saved to: {filepath}")
        return filepath

    def print_portfolio_summary(self, results: Dict[str, Any]):
        """Print portfolio summary"""
        print(f"\n🎯 PORTFOLIO SUMMARY")
        print("=" * 80)
        
        for symbol, symbol_results in results.items():
            print(f"\n📈 {symbol}")
            print("-" * 40)
            
            if 'PortfolioTotal' in symbol_results:
                portfolio = symbol_results['PortfolioTotal']
                if 'error' not in portfolio:
                    print(f"Portfolio Return: {portfolio['total_return']:.2f}%")
                    print(f"Portfolio Drawdown: {portfolio['max_drawdown']:.2f}%")
                    print(f"Total Trades: {portfolio['total_trades']}")
                    print(f"Win Rate: {portfolio['win_rate']:.2f}%")
                    print(f"Strategies: {portfolio['strategies_count']}")
            
            # Individual strategy results
            for strategy_name, result in symbol_results.items():
                if strategy_name != 'PortfolioTotal' and 'error' not in result:
                    if 'performance' in result:
                        return_val = result['performance']['total_return']
                        print(f"  {strategy_name}: {return_val:.2f}%")


def load_strategy_configs(config_dir: str = 'configs') -> Dict[str, Dict[str, Any]]:
    """Load all strategy configuration files"""
    configs = {}
    config_path = Path(__file__).parent / config_dir
    
    strategy_configs = [
        'config_volatility.json',
        'config_bollinger.json', 
        'config_rsi_ema_v2.2.json',
        'config_ema_breakout_conservative_v2.1.json',
        'config_contrarian.json'
        # 'config_trend_following_adx_ema.json'    # Removed - strategy not available
    ]
    
    for config_file in strategy_configs:
        config_file_path = config_path / config_file
        if config_file_path.exists():
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    strategy_name = config.get('strategy', config_file.replace('config_', '').replace('.json', ''))
                    configs[strategy_name] = config
                    print(f"✅ Loaded config: {config_file}")
            except Exception as e:
                print(f"❌ Error loading {config_file}: {e}")
        else:
            print(f"⚠️  Config file not found: {config_file}")
    
    return configs


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Portfolio Engine for Multi-Strategy Backtesting")
    parser.add_argument('--symbols', nargs='+', default=['BTCUSDT'], 
                       help='Symbols to test (e.g., BTCUSDT ETHUSDT)')
    parser.add_argument('--strategies', nargs='+', 
                       default=['VolatilityBreakoutStrategy', 'BollingerReversionStrategy', 
                               'RSIEMAMomentumStrategy', 'EMABreakoutConservativeStrategy',
                               'ContrarianVolumeSpikeStrategy'],
                       help='Strategies to run')
    parser.add_argument('--config-dir', default='configs', 
                       help='Directory containing strategy configs')
    parser.add_argument('--output', help='Output filename for portfolio report')
    parser.add_argument('--disable-regime-detection', action='store_true',
                       help='Disable market regime detection (run all strategies)')
    parser.add_argument('--disable-risk-parity', action='store_true',
                       help='Disable risk parity allocation (use equal weights)')
    parser.add_argument('--disable-strategy-handle', action='store_true',
                       help='Disable strategy handle wrapper (direct strategy execution)')
    
    args = parser.parse_args()
    
    # Load strategy configurations
    configs = load_strategy_configs(args.config_dir)
    
    if not configs:
        print("❌ No strategy configurations found!")
        sys.exit(1)
    
    # Create and run portfolio engine
    enable_regime_detection = not args.disable_regime_detection
    enable_risk_parity = not args.disable_risk_parity
    enable_strategy_handle = not args.disable_strategy_handle
    engine = PortfolioEngine(enable_regime_detection=enable_regime_detection, 
                           enable_risk_parity=enable_risk_parity,
                           enable_strategy_handle=enable_strategy_handle)
    
    # Filter strategies to only those with configs
    available_strategies = [s for s in args.strategies if s in configs]
    
    if not available_strategies:
        print("❌ No available strategies with configurations!")
        sys.exit(1)
    
    print(f"🎯 Running portfolio with {len(available_strategies)} strategies on {len(args.symbols)} symbols")
    
    # Run portfolio backtesting
    results = engine.run_portfolio(args.symbols, available_strategies, configs)
    
    # Print summary
    engine.print_portfolio_summary(results)
    
    # Save report
    engine.save_portfolio_report(results, args.output)
    
    # Finalize hybrid logging session
    if engine.hybrid_logger:
        final_summary = {
            'session_id': engine.hybrid_logger.session_id,
            'total_strategies': len(available_strategies),
            'total_symbols': len(args.symbols),
            'portfolio_results': results,
            'regime_detection_enabled': enable_regime_detection,
            'risk_parity_enabled': enable_risk_parity,
            'strategy_handle_enabled': enable_strategy_handle
        }
        engine.hybrid_logger.finalize_session(final_summary)
    
    print("\n✅ Portfolio backtesting completed successfully!")


if __name__ == '__main__':
    main()
