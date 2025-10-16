"""
Bot Monitor - Centralized monitoring system for trading bots
Provides metrics collection, health checks, and performance monitoring
"""

import time
import threading
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import logging

# Prometheus metrics
BOT_STATUS = Gauge('bot_status', 'Status of the trading bot (1=running, 0=stopped)')
TOTAL_EQUITY = Gauge('total_equity', 'Current total equity of the bot')
DAILY_PNL = Gauge('daily_pnl', 'Daily Profit and Loss')
TOTAL_TRADES = Counter('total_trades', 'Total number of trades executed')
ACTIVE_POSITIONS = Gauge('active_positions', 'Number of currently active trading positions')

# Strategy-specific metrics
STRATEGY_EQUITY = Gauge('strategy_equity', 'Equity per strategy', ['strategy_name', 'symbol'])
STRATEGY_PNL = Gauge('strategy_pnl', 'PNL per strategy', ['strategy_name', 'symbol'])
STRATEGY_TRADES = Counter('strategy_trades', 'Trades executed per strategy', ['strategy_name', 'symbol'])
STRATEGY_WIN_RATE = Gauge('strategy_win_rate', 'Win rate per strategy', ['strategy_name', 'symbol'])

# Market regime metrics
CURRENT_MARKET_REGIME = Gauge('current_market_regime', 'Current detected market regime', ['regime_type'])
REGIME_DETECTION_TIME = Histogram('regime_detection_duration_seconds', 'Time taken to detect market regime')

# Risk parity metrics
RISK_PARITY_WEIGHT = Gauge('risk_parity_weight', 'Allocated weight by Risk Parity', ['strategy_name', 'symbol'])
RISK_PARITY_REBALANCE_COUNT = Counter('risk_parity_rebalance_count', 'Number of rebalances by Risk Parity')

class BotMonitor:
    """Centralized bot monitoring system"""
    
    def __init__(self, config_path: str = "configs/monitoring_config.yaml"):
        self.config = self._load_config(config_path)
        self.bots = {}
        self.metrics_server_started = False
        self.logger = self._setup_logger()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load monitoring configuration"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load config {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Default configuration if config file not found"""
        return {
            'monitoring': {
                'development': {
                    'host': 'localhost',
                    'ports': {
                        'grafana': 3000,
                        'prometheus': 9090,
                        'metrics': 8080
                    },
                    'auth_enabled': False,
                    'cors_origins': ['*'],
                    'scrape_interval': 15,
                    'log_directories': [
                        'backtrader_engine/reports/portfolio_*',
                        'backtrader_engine/reports/forex_*'
                    ],
                    'bot_types': ['crypto', 'forex']
                }
            }
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the monitor"""
        logger = logging.getLogger('bot_monitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def start_metrics_server(self, port: int = 8080):
        """Start Prometheus metrics server"""
        if not self.metrics_server_started:
            start_http_server(port)
            self.metrics_server_started = True
            self.logger.info(f"Metrics server started on port {port}")
    
    def register_bot(self, bot_id: str, bot_type: str, config: Dict):
        """Register a new bot for monitoring"""
        self.bots[bot_id] = {
            'type': bot_type,
            'config': config,
            'status': 'stopped',
            'last_update': datetime.now(),
            'equity': 0.0,
            'trades': 0,
            'positions': 0
        }
        self.logger.info(f"Registered bot: {bot_id} (type: {bot_type})")
    
    def update_bot_status(self, bot_id: str, status: str, equity: float = None, 
                         trades: int = None, positions: int = None):
        """Update bot status and metrics"""
        if bot_id not in self.bots:
            self.logger.warning(f"Bot {bot_id} not registered")
            return
        
        bot = self.bots[bot_id]
        bot['status'] = status
        bot['last_update'] = datetime.now()
        
        if equity is not None:
            bot['equity'] = equity
            TOTAL_EQUITY.set(equity)
        
        if trades is not None:
            bot['trades'] = trades
            TOTAL_TRADES.inc(trades - bot.get('last_trades', 0))
            bot['last_trades'] = trades
        
        if positions is not None:
            bot['positions'] = positions
            ACTIVE_POSITIONS.set(positions)
        
        # Update bot status metric
        BOT_STATUS.set(1 if status == 'running' else 0)
        
        self.logger.debug(f"Updated bot {bot_id}: status={status}, equity={equity}")
    
    def update_strategy_metrics(self, strategy_name: str, symbol: str, 
                               equity: float, pnl: float, trades: int, win_rate: float):
        """Update strategy-specific metrics"""
        STRATEGY_EQUITY.labels(strategy_name=strategy_name, symbol=symbol).set(equity)
        STRATEGY_PNL.labels(strategy_name=strategy_name, symbol=symbol).set(pnl)
        STRATEGY_TRADES.labels(strategy_name=strategy_name, symbol=symbol).inc(trades)
        STRATEGY_WIN_RATE.labels(strategy_name=strategy_name, symbol=symbol).set(win_rate)
    
    def update_market_regime(self, regime_type: str, detection_time: float):
        """Update market regime metrics"""
        CURRENT_MARKET_REGIME.labels(regime_type=regime_type).set(1)
        REGIME_DETECTION_TIME.observe(detection_time)
    
    def update_risk_parity(self, strategy_name: str, symbol: str, weight: float):
        """Update risk parity allocation metrics"""
        RISK_PARITY_WEIGHT.labels(strategy_name=strategy_name, symbol=symbol).set(weight)
    
    def get_bot_status(self, bot_id: str) -> Optional[Dict]:
        """Get current status of a bot"""
        return self.bots.get(bot_id)
    
    def get_all_bots_status(self) -> Dict:
        """Get status of all registered bots"""
        return self.bots.copy()
    
    def health_check(self) -> Dict:
        """Perform health check on all bots"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'total_bots': len(self.bots),
            'running_bots': 0,
            'stopped_bots': 0,
            'bots': {}
        }
        
        for bot_id, bot in self.bots.items():
            status = bot['status']
            if status == 'running':
                health_status['running_bots'] += 1
            else:
                health_status['stopped_bots'] += 1
            
            health_status['bots'][bot_id] = {
                'status': status,
                'last_update': bot['last_update'].isoformat(),
                'equity': bot['equity'],
                'trades': bot['trades'],
                'positions': bot['positions']
            }
        
        return health_status

# Global monitor instance
monitor = BotMonitor()

def get_monitor() -> BotMonitor:
    """Get the global monitor instance"""
    return monitor
