import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class EnhancedLogger:
    def __init__(self, name: str, log_dir: str = 'logs'):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        
        self.simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        
        # Setup file handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        # Main log file
        main_handler = logging.FileHandler(self.log_dir / f'{self.name}.log')
        main_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(main_handler)
        
        # Error log file
        error_handler = logging.FileHandler(self.log_dir / f'{self.name}_errors.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.simple_formatter)
        self.logger.addHandler(console_handler)
    
    def log_signal(self, signal_data: Dict[str, Any], result: str, reason: str = ''):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'signal',
            'symbol': signal_data.get('symbol', ''),
            'signal_type': signal_data.get('signal_type', ''),
            'confidence': signal_data.get('confidence', 0.0),
            'price': signal_data.get('price', 0.0),
            'strategy': signal_data.get('strategy', ''),
            'result': result,
            'reason': reason
        }
        
        self.logger.info(f'SIGNAL | {result} | {signal_data.get(\"symbol\", \"\")} {signal_data.get(\"signal_type\", \"\")} @ {signal_data.get(\"price\", 0.0)} | Conf: {signal_data.get(\"confidence\", 0.0):.3f} | {reason}')
        
        # Write to JSON log for analysis
        json_log_file = self.log_dir / f'{self.name}_signals.jsonl'
        with open(json_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_position(self, position_data: Dict[str, Any], action: str):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'position',
            'action': action,
            'symbol': position_data.get('symbol', ''),
            'side': position_data.get('side', ''),
            'size': position_data.get('size', 0.0),
            'price': position_data.get('price', 0.0),
            'pnl': position_data.get('pnl', 0.0)
        }
        
        self.logger.info(f'POSITION | {action} | {position_data.get(\"symbol\", \"\")} {position_data.get(\"side\", \"\")} {position_data.get(\"size\", 0.0)} @ {position_data.get(\"price\", 0.0)}')
        
        # Write to JSON log
        json_log_file = self.log_dir / f'{self.name}_positions.jsonl'
        with open(json_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_risk_event(self, event_type: str, details: Dict[str, Any]):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'risk_event',
            'event_type': event_type,
            'details': details
        }
        
        self.logger.warning(f'RISK | {event_type} | {details}')
        
        # Write to JSON log
        json_log_file = self.log_dir / f'{self.name}_risk.jsonl'
        with open(json_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_performance(self, metrics: Dict[str, Any]):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'performance',
            'metrics': metrics
        }
        
        self.logger.info(f'PERFORMANCE | {metrics}')
        
        # Write to JSON log
        json_log_file = self.log_dir / f'{self.name}_performance.jsonl'
        with open(json_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

# Usage example
if __name__ == '__main__':
    logger = EnhancedLogger('trading_bot')
    
    # Test signal logging
    signal_data = {
        'symbol': 'ETHUSDT',
        'signal_type': 'BUY',
        'confidence': 0.75,
        'price': 3850.0,
        'strategy': 'RSIEMAMomentumStrategy'
    }
    
    logger.log_signal(signal_data, 'ACCEPTED', 'Confidence above threshold')
    
    # Test position logging
    position_data = {
        'symbol': 'ETHUSDT',
        'side': 'Buy',
        'size': 0.5,
        'price': 3850.0,
        'pnl': 25.0
    }
    
    logger.log_position(position_data, 'OPENED')
    
    # Test risk event logging
    risk_details = {
        'symbol': 'ETHUSDT',
        'reason': 'Volatility exceeds limit',
        'volatility': 0.06,
        'limit': 0.05
    }
    
    logger.log_risk_event('VOLATILITY_BREACH', risk_details)
    
    print('Enhanced logging test completed!')
