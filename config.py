"""
Configuration management for the trading bot.
"""

from dotenv import load_dotenv
import os
from typing import Dict, Any

import yaml

MONITORING_CONFIG_PATH = os.getenv(
    "MONITORING_CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "configs", "monitoring_config.yaml"),
)

load_dotenv()

class Config:
    """Configuration class for the trading bot."""
    
    # Exchange Configuration
    EXCHANGE = os.getenv('EXCHANGE', 'bybit')
    API_KEY = os.getenv('API_KEY', '')
    SECRET = os.getenv('SECRET', '')
    TESTNET = os.getenv('TESTNET', 'true').lower() == 'true'
    
    # Trading Configuration
    SYMBOL = os.getenv('SYMBOL', 'BTCUSDT')
    TIMEFRAME = os.getenv('TIMEFRAME', '15m')
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', '0.01'))
    LEVERAGE = int(os.getenv('LEVERAGE', '10'))
    
    # Bot Configuration
    MODE = 'paper'  # development, paper, live
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # ML Model Configuration
    KALMAN_Q = float(os.getenv('KALMAN_Q', '0.01'))
    KALMAN_R = float(os.getenv('KALMAN_R', '0.1'))
    RF_N_ESTIMATORS = int(os.getenv('RF_N_ESTIMATORS', '100'))
    RF_MAX_DEPTH = int(os.getenv('RF_MAX_DEPTH', '10'))
    
    # Risk Management
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '0.1'))
    STOP_LOSS_PERCENTAGE = float(os.getenv('STOP_LOSS_PERCENTAGE', '0.015'))
    TAKE_PROFIT_PERCENTAGE = float(os.getenv('TAKE_PROFIT_PERCENTAGE', '0.05'))
    COOLDOWN_MINUTES = int(os.getenv('COOLDOWN_MINUTES', '5'))
    
    # Data Configuration
    DATA_LIMIT = int(os.getenv('DATA_LIMIT', '1000'))
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '900'))  # seconds
    
    # Strategy Configuration
    KALMAN_THRESHOLD = float(os.getenv('KALMAN_THRESHOLD', '0.5'))
    DEVIATION_THRESHOLD = float(os.getenv('DEVIATION_THRESHOLD', '2.0'))
    ML_CONFIDENCE_THRESHOLD = float(os.getenv('ML_CONFIDENCE_THRESHOLD', '0.7'))
    CAPITAL = float(os.getenv('CAPITAL', '10000'))  # Starting capital
    
    @classmethod
    def get_exchange_config(cls) -> Dict[str, Any]:
        """Get exchange configuration dictionary."""
        return {
            'exchange': cls.EXCHANGE,
            'api_key': cls.API_KEY,
            'secret': cls.SECRET,
            'testnet': cls.TESTNET,
            'symbol': cls.SYMBOL,
            'timeframe': cls.TIMEFRAME
        }
    
    @classmethod
    def get_trading_config(cls) -> Dict[str, Any]:
        """Get trading configuration dictionary."""
        return {
            'risk_per_trade': cls.RISK_PER_TRADE,
            'leverage': cls.LEVERAGE,
            'mode': cls.MODE,
            'symbol': cls.SYMBOL,
            'timeframe': cls.TIMEFRAME
        }
    
    @classmethod
    def get_ml_config(cls) -> Dict[str, Any]:
        """Get ML model configuration dictionary."""
        return {
            'kalman_q': cls.KALMAN_Q,
            'kalman_r': cls.KALMAN_R,
            'rf_n_estimators': cls.RF_N_ESTIMATORS,
            'rf_max_depth': cls.RF_MAX_DEPTH,
        }
    
    @classmethod
    def get_risk_config(cls) -> Dict[str, Any]:
        """Get risk management configuration dictionary."""
        return {
            'risk_per_trade': cls.RISK_PER_TRADE,
            'max_position_size': cls.MAX_POSITION_SIZE,
            'stop_loss_percentage': cls.STOP_LOSS_PERCENTAGE,
            'take_profit_percentage': cls.TAKE_PROFIT_PERCENTAGE,
            'cooldown_minutes': cls.COOLDOWN_MINUTES,
        }
    
    @classmethod
    def validate_critical_config(cls):
        """Validar configuración crítica del bot"""
        errors = []
        
        # Validar API keys
        if not cls.API_KEY or cls.API_KEY == '':
            errors.append("API_KEY is required but not set")
        if not cls.SECRET or cls.SECRET == '':
            errors.append("SECRET is required but not set")
        
        # Validar TESTNET
        if not isinstance(cls.TESTNET, bool):
            errors.append("TESTNET must be a boolean value")
        
        # Validar exchange
        valid_exchanges = ['bybit', 'binance', 'okx', 'bingx']
        if cls.EXCHANGE not in valid_exchanges:
            errors.append(f"EXCHANGE must be one of: {valid_exchanges}")
        
        # Validar símbolo
        if not cls.SYMBOL or cls.SYMBOL == '':
            errors.append("SYMBOL is required but not set")
        
        # Validar timeframe
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d']
        if cls.TIMEFRAME not in valid_timeframes:
            errors.append(f"TIMEFRAME must be one of: {valid_timeframes}")
        
        # Validar valores numéricos
        if cls.RISK_PER_TRADE <= 0 or cls.RISK_PER_TRADE > 1:
            errors.append("RISK_PER_TRADE must be between 0 and 1")
        
        if cls.LEVERAGE <= 0 or cls.LEVERAGE > 100:
            errors.append("LEVERAGE must be between 1 and 100")
        
        if cls.CAPITAL <= 0:
            errors.append("CAPITAL must be greater than 0")
        
        return errors
    
    def validate(self) -> bool:
        """Validate configuration - required by main.py"""
        errors = self.validate_critical_config()
        return len(errors) == 0


def load_monitoring_config(env: str = "development") -> Dict[str, Any]:
    """Load monitoring configuration for the specified environment."""
    if not os.path.exists(MONITORING_CONFIG_PATH):
        raise FileNotFoundError(
            f"Monitoring config not found at {MONITORING_CONFIG_PATH}."
        )

    with open(MONITORING_CONFIG_PATH, "r", encoding="utf-8") as cfg_file:
        config = yaml.safe_load(cfg_file)

    monitoring = config.get("monitoring", {})
    if env not in monitoring:
        raise KeyError(f"Environment '{env}' not defined in monitoring config")

    merged = monitoring[env].copy()

    def _resolve(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_key = value[2:-1]
            return os.getenv(env_key)
        if isinstance(value, list):
            return [_resolve(item) for item in value]
        if isinstance(value, dict):
            return {k: _resolve(v) for k, v in value.items()}
        return value

    merged = _resolve(merged)

    return {
        "environment": env,
        **merged,
    }
