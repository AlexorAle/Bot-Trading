import unittest
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from exchanges.bybit_paper_trader import PaperPosition, PaperOrder
from risk_manager import RiskManager, RiskLimits

class TestPaperPosition(unittest.TestCase):
    def setUp(self):
        self.position = PaperPosition(
            symbol='ETHUSDT',
            side='Buy',
            size=0.5,
            entry_price=3800.0,
            mark_price=3850.0,
            unrealized_pnl=25.0
        )
    
    def test_paper_position_creation(self):
        self.assertEqual(self.position.symbol, 'ETHUSDT')
        self.assertEqual(self.position.side, 'Buy')
        self.assertEqual(self.position.size, 0.5)
        self.assertEqual(self.position.entry_price, 3800.0)
        self.assertEqual(self.position.mark_price, 3850.0)
        self.assertEqual(self.position.unrealized_pnl, 25.0)
    
    def test_paper_position_attributes(self):
        self.assertTrue(hasattr(self.position, 'size'))
        self.assertTrue(hasattr(self.position, 'side'))
        self.assertTrue(hasattr(self.position, 'symbol'))
        self.assertTrue(hasattr(self.position, 'entry_price'))
        self.assertTrue(hasattr(self.position, 'mark_price'))
    
    def test_paper_position_access(self):
        # Test direct attribute access
        self.assertEqual(self.position.size, 0.5)
        self.assertEqual(self.position.side, 'Buy')
        
        # Test that it's not a dict
        self.assertFalse(hasattr(self.position, 'get'))

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.config = {
            'risk_limits': {
                'max_position_size': 0.1,
                'min_confidence': 0.6,
                'max_volatility': 0.05
            }
        }
        self.risk_manager = RiskManager(self.config)
    
    def test_risk_manager_initialization(self):
        self.assertEqual(self.risk_manager.risk_limits.max_position_size, 0.1)
        self.assertEqual(self.risk_manager.risk_limits.min_confidence, 0.6)
        self.assertEqual(self.risk_manager.risk_limits.max_volatility, 0.05)
    
    def test_validate_signal_with_paper_position(self):
        # Create PaperPosition
        position = PaperPosition(
            symbol='ETHUSDT',
            side='Buy',
            size=0.5,
            entry_price=3800.0,
            mark_price=3850.0
        )
        
        positions = {'ETHUSDT': position}
        
        signal_data = {
            'symbol': 'ETHUSDT',
            'signal_type': 'Sell',
            'confidence': 0.8,
            'price': 3900.0,
            'strategy': 'TestStrategy'
        }
        
        market_data = {
            'price': 3900.0,
            'atr': 20.0,
            'volume': 1000000,
            'volume_avg': 1000000,
            'adx': 30.0,
            'rsi': 60.0,
            'volatility': 0.02
        }
        
        # This should not raise an exception
        is_valid, reason = self.risk_manager.validate_signal(
            signal_data=signal_data,
            current_balance=10000.0,
            current_positions=positions,
            market_data=market_data
        )
        
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(reason, str)
    
    def test_validate_signal_with_dict_position(self):
        # Test backward compatibility with dict-like positions
        positions = {
            'ETHUSDT': {
                'size': 0.5,
                'side': 'Buy',
                'entry_price': 3800.0
            }
        }
        
        signal_data = {
            'symbol': 'ETHUSDT',
            'signal_type': 'Sell',
            'confidence': 0.8,
            'price': 3900.0,
            'strategy': 'TestStrategy'
        }
        
        market_data = {
            'price': 3900.0,
            'atr': 20.0,
            'volume': 1000000,
            'volume_avg': 1000000,
            'adx': 30.0,
            'rsi': 60.0,
            'volatility': 0.02
        }
        
        # This should not raise an exception
        is_valid, reason = self.risk_manager.validate_signal(
            signal_data=signal_data,
            current_balance=10000.0,
            current_positions=positions,
            market_data=market_data
        )
        
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(reason, str)

if __name__ == '__main__':
    unittest.main()
