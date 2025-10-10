"""
Unit tests for the liquidation hunting strategy.
"""

import unittest
from unittest.mock import patch, Mock
import pandas as pd
from strategy.liquidation_hunter import LiquidationHunter


class TestLiquidationHunter(unittest.TestCase):
    """Test cases for LiquidationHunter strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = LiquidationHunter()
    
    def test_initialization(self):
        """Test strategy initialization."""
        self.assertIsNotNone(self.strategy.config)
        self.assertIsNone(self.strategy.last_signal_time)
        self.assertIsNone(self.strategy.position)
    
    def test_generate_signal(self):
        """Test signal generation."""
        # Mock data
        data = pd.DataFrame({
            'close': [100, 101, 102],
            'kalman_signal': [0, 1, 0],
            'kalman_deviation': [0.1, 2.5, 0.2],
            'liquidations_short': [5, 10, 3],
            'liquidations_long': [3, 5, 8],
            'liquidations_volume': [8, 15, 11]
        })
        
        # Mock ML prediction
        ml_prediction = {
            'prediction': 1,
            'probability': 0.8,
            'confidence': 0.8
        }
        
        # Test signal generation
        signal = self.strategy.generate_signal(data, ml_prediction)
        
        if signal:
            self.assertIn('type', signal)
            self.assertIn('direction', signal)
            self.assertIn('symbol', signal)
            self.assertIn('price', signal)
            self.assertIn('size', signal)
    
    def test_calculate_position_size(self):
        """Test position size calculation."""
        data = pd.Series({
            'close': 100,
            'volatility': 0.02,
            'liquidations_volume': 50
        })
        
        size = self.strategy._calculate_position_size(data)
        
        self.assertGreater(size, 0)
        self.assertLessEqual(size, self.strategy.config.CAPITAL * self.strategy.config.MAX_POSITION_SIZE)
    
    def test_cooldown_period(self):
        """Test cooldown period functionality."""
        # Test when not in cooldown
        self.assertFalse(self.strategy._is_in_cooldown())
        
        # Set last signal time
        self.strategy.last_signal_time = pd.Timestamp.now()
        
        # Test when in cooldown
        self.assertTrue(self.strategy._is_in_cooldown())
    
    def test_close_position(self):
        """Test position closing."""
        # Set up position
        self.strategy.position = {
            'direction': 'buy',
            'price': 100,
            'size': 0.1
        }
        
        # Test data with price increase
        data = pd.Series({'close': 105})
        
        close_result = self.strategy.close_position(data)
        
        if close_result:
            self.assertIn('type', close_result)
            self.assertIn('reason', close_result)
            self.assertIn('pnl_pct', close_result)
    
    def test_validate(self):
        """Test strategy validation."""
        result = self.strategy.validate()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()




