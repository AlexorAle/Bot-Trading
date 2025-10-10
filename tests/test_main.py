"""
Unit tests for the main trading bot.
"""

import unittest
from unittest.mock import patch, Mock
import pandas as pd
from main import TradingBot


class TestTradingBot(unittest.TestCase):
    """Test cases for TradingBot class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bot = TradingBot()
    
    @patch('main.Config')
    @patch('main.DataFetcher')
    @patch('main.KalmanFilter')
    @patch('main.MLModel')
    @patch('main.LiquidationHunter')
    @patch('main.Trader')
    @patch('main.BotLogger')
    def test_initialization(self, mock_logger, mock_trader, mock_strategy, 
                           mock_ml, mock_kalman, mock_fetcher, mock_config):
        """Test bot initialization."""
        mock_config.return_value.LOG_LEVEL = 'INFO'
        
        bot = TradingBot()
        
        self.assertIsNotNone(bot.config)
        self.assertIsNotNone(bot.data_fetcher)
        self.assertIsNotNone(bot.kalman_filter)
        self.assertIsNotNone(bot.ml_model)
        self.assertIsNotNone(bot.strategy)
        self.assertIsNotNone(bot.trader)
        self.assertIsNotNone(bot.logger)
    
    @patch('main.Config')
    @patch('main.DataFetcher')
    @patch('main.KalmanFilter')
    @patch('main.MLModel')
    @patch('main.LiquidationHunter')
    @patch('main.Trader')
    @patch('main.BotLogger')
    def test_validate_components(self, mock_logger, mock_trader, mock_strategy, 
                                mock_ml, mock_kalman, mock_fetcher, mock_config):
        """Test component validation."""
        mock_config.return_value.LOG_LEVEL = 'INFO'
        
        # Mock all components to return True for validate()
        mock_fetcher.return_value.validate.return_value = True
        mock_kalman.return_value.validate.return_value = True
        mock_ml.return_value.validate.return_value = True
        mock_strategy.return_value.validate.return_value = True
        mock_trader.return_value.validate.return_value = True
        
        bot = TradingBot()
        result = bot.validate_components()
        
        self.assertTrue(result)
    
    @patch('main.Config')
    @patch('main.DataFetcher')
    @patch('main.KalmanFilter')
    @patch('main.MLModel')
    @patch('main.LiquidationHunter')
    @patch('main.Trader')
    @patch('main.BotLogger')
    def test_validate_components_failure(self, mock_logger, mock_trader, mock_strategy, 
                                       mock_ml, mock_kalman, mock_fetcher, mock_config):
        """Test component validation failure."""
        mock_config.return_value.LOG_LEVEL = 'INFO'
        
        # Mock one component to return False for validate()
        mock_fetcher.return_value.validate.return_value = False
        mock_kalman.return_value.validate.return_value = True
        mock_ml.return_value.validate.return_value = True
        mock_strategy.return_value.validate.return_value = True
        mock_trader.return_value.validate.return_value = True
        
        bot = TradingBot()
        result = bot.validate_components()
        
        self.assertFalse(result)
    
    @patch('main.Config')
    @patch('main.DataFetcher')
    @patch('main.KalmanFilter')
    @patch('main.MLModel')
    @patch('main.LiquidationHunter')
    @patch('main.Trader')
    @patch('main.BotLogger')
    def test_execute_trading_cycle(self, mock_logger, mock_trader, mock_strategy, 
                                  mock_ml, mock_kalman, mock_fetcher, mock_config):
        """Test trading cycle execution."""
        mock_config.return_value.LOG_LEVEL = 'INFO'
        
        # Mock data
        mock_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, 1100, 1200]
        })
        
        # Mock filtered data
        mock_filtered_data = mock_data.copy()
        mock_filtered_data['kalman_price'] = [100, 101, 102]
        mock_filtered_data['kalman_deviation'] = [0.1, 0.2, 0.3]
        mock_filtered_data['kalman_signal'] = [0, 1, 0]
        
        # Mock ML prediction
        mock_prediction = {
            'prediction': 1,
            'probability': 0.8,
            'confidence': 0.8
        }
        
        # Mock signal
        mock_signal = {
            'type': 'liquidation_hunt',
            'direction': 'buy',
            'symbol': 'BTCUSDT',
            'price': 102.5,
            'size': 0.1
        }
        
        # Mock trade result
        mock_trade_result = {
            'order_id': 'test_123',
            'status': 'filled'
        }
        
        # Setup mocks
        mock_fetcher.return_value.fetch_data.return_value = mock_data
        mock_kalman.return_value.apply_filter.return_value = mock_filtered_data
        mock_ml.return_value.predict.return_value = mock_prediction
        mock_strategy.return_value.generate_signal.return_value = mock_signal
        mock_trader.return_value.execute_trade.return_value = mock_trade_result
        
        bot = TradingBot()
        bot._execute_trading_cycle()
        
        # Verify method calls
        mock_fetcher.return_value.fetch_data.assert_called_once()
        mock_kalman.return_value.apply_filter.assert_called_once_with(mock_data)
        mock_ml.return_value.predict.assert_called_once_with(mock_filtered_data)
        mock_strategy.return_value.generate_signal.assert_called_once_with(mock_filtered_data, mock_prediction)
        mock_trader.return_value.execute_trade.assert_called_once_with(mock_signal)
    
    @patch('main.Config')
    @patch('main.DataFetcher')
    @patch('main.KalmanFilter')
    @patch('main.MLModel')
    @patch('main.LiquidationHunter')
    @patch('main.Trader')
    @patch('main.BotLogger')
    def test_signal_handler(self, mock_logger, mock_trader, mock_strategy, 
                           mock_ml, mock_kalman, mock_fetcher, mock_config):
        """Test signal handler."""
        mock_config.return_value.LOG_LEVEL = 'INFO'
        
        bot = TradingBot()
        bot.running = True
        
        # Test signal handler
        bot._signal_handler(2, None)  # SIGINT
        
        self.assertFalse(bot.running)


if __name__ == '__main__':
    unittest.main()




