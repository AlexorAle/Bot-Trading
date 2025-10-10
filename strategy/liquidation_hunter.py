"""
Liquidation hunting strategy implementation.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
import logging
from config import Config


class LiquidationHunter:
    """Liquidation hunting strategy."""
    
    def __init__(self):
        """Initialize the liquidation hunter strategy."""
        self.config = Config()
        self.log = logging.getLogger(__name__)
        self.last_signal_time = None
        self.position = None
    
    def generate_signal(self, data: pd.DataFrame, ml_prediction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on liquidation hunting strategy."""
        try:
            if data is None or data.empty:
                return None
            
            # Check cooldown period
            if self._is_in_cooldown():
                return None
            
            # Get latest data
            latest = data.iloc[-1]
            
            # Check Kalman filter conditions
            kalman_signal = self._check_kalman_conditions(latest)
            if not kalman_signal:
                return None
            
            # Check ML prediction
            ml_signal = self._check_ml_conditions(ml_prediction)
            if not ml_signal:
                return None
            
            # Check liquidation conditions
            liquidation_signal = self._check_liquidation_conditions(latest)
            if not liquidation_signal:
                return None
            
            # Generate final signal
            signal = self._create_signal(latest, ml_prediction)
            
            if signal:
                self.last_signal_time = pd.Timestamp.now()
                self.log.info(f"Generated signal: {signal}")
            
            return signal
            
        except Exception as e:
            self.log.error(f"Error generating signal: {e}")
            return None
    
    def _check_kalman_conditions(self, data: pd.Series) -> bool:
        """Check Kalman filter conditions."""
        try:
            # Check if Kalman signal is strong enough
            if 'kalman_signal' in data and data['kalman_signal'] == 1:
                if 'kalman_deviation' in data and data['kalman_deviation'] > self.config.DEVIATION_THRESHOLD:
                    return True
            return False
        except Exception as e:
            self.log.error(f"Error checking Kalman conditions: {e}")
            return False
    
    def _check_ml_conditions(self, ml_prediction: Dict[str, Any]) -> bool:
        """Check ML prediction conditions."""
        try:
            if ml_prediction is None:
                return False
            
            # Check confidence threshold
            confidence = ml_prediction.get('confidence', 0)
            if confidence < self.config.ML_CONFIDENCE_THRESHOLD:
                return False
            
            # Check prediction direction
            prediction = ml_prediction.get('prediction', 0)
            if prediction not in [0, 1]:
                return False
            
            return True
        except Exception as e:
            self.log.error(f"Error checking ML conditions: {e}")
            return False
    
    def _check_liquidation_conditions(self, data: pd.Series) -> bool:
        """Check liquidation conditions."""
        try:
            # Check if liquidation data is available
            if 'liquidations_volume' not in data:
                return False
            
            # Check liquidation volume threshold
            liquidation_volume = data.get('liquidations_volume', 0)
            if liquidation_volume < 10:  # Minimum liquidation volume
                return False
            
            # Check liquidation ratio
            if 'liquidations_short' in data and 'liquidations_long' in data:
                short_liquidations = data.get('liquidations_short', 0)
                long_liquidations = data.get('liquidations_long', 0)
                
                if short_liquidations > long_liquidations * 2:  # More short liquidations
                    return True
                elif long_liquidations > short_liquidations * 2:  # More long liquidations
                    return True
            
            return False
        except Exception as e:
            self.log.error(f"Error checking liquidation conditions: {e}")
            return False
    
    def _create_signal(self, data: pd.Series, ml_prediction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create trading signal."""
        try:
            # Determine signal direction based on liquidation pattern
            short_liquidations = data.get('liquidations_short', 0)
            long_liquidations = data.get('liquidations_long', 0)
            
            # If more short liquidations, expect price to go up (buy)
            # If more long liquidations, expect price to go down (sell)
            if short_liquidations > long_liquidations * 1.5:
                direction = 'buy'
            elif long_liquidations > short_liquidations * 1.5:
                direction = 'sell'
            else:
                return None
            
            # Calculate position size
            position_size = self._calculate_position_size(data)
            
            # Create signal
            signal = {
                'type': 'liquidation_hunt',
                'direction': direction,
                'symbol': self.config.SYMBOL,
                'price': data['close'],
                'size': position_size,
                'confidence': ml_prediction.get('confidence', 0),
                'kalman_deviation': data.get('kalman_deviation', 0),
                'liquidation_volume': data.get('liquidations_volume', 0),
                'timestamp': pd.Timestamp.now()
            }
            
            return signal
            
        except Exception as e:
            self.log.error(f"Error creating signal: {e}")
            return None
    
    def _calculate_position_size(self, data: pd.Series) -> float:
        """Calculate position size based on risk management."""
        try:
            # Base position size on capital and risk per trade
            base_size = self.config.CAPITAL * self.config.RISK_PER_TRADE
            
            # Adjust based on volatility
            volatility = data.get('volatility', 0.01)
            if volatility > 0.05:  # High volatility
                base_size *= 0.5
            elif volatility < 0.01:  # Low volatility
                base_size *= 1.5
            
            # Adjust based on liquidation volume
            liquidation_volume = data.get('liquidations_volume', 0)
            if liquidation_volume > 100:  # High liquidation volume
                base_size *= 1.2
            
            return min(base_size, self.config.CAPITAL * self.config.MAX_POSITION_SIZE)
            
        except Exception as e:
            self.log.error(f"Error calculating position size: {e}")
            return self.config.CAPITAL * self.config.RISK_PER_TRADE
    
    def _is_in_cooldown(self) -> bool:
        """Check if strategy is in cooldown period."""
        if self.last_signal_time is None:
            return False
        
        cooldown_period = pd.Timedelta(minutes=self.config.COOLDOWN_MINUTES)
        time_since_last = pd.Timestamp.now() - self.last_signal_time
        
        return time_since_last < cooldown_period
    
    def close_position(self, data: pd.Series) -> Optional[Dict[str, Any]]:
        """Close current position."""
        try:
            if self.position is None:
                return None
            
            # Check stop loss and take profit
            current_price = data['close']
            entry_price = self.position['price']
            direction = self.position['direction']
            
            # Calculate P&L
            if direction == 'buy':
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price
            
            # Check stop loss
            if pnl_pct <= -self.config.STOP_LOSS_PERCENTAGE:
                self.log.info(f"Stop loss triggered: {pnl_pct:.2%}")
                return {
                    'type': 'close',
                    'reason': 'stop_loss',
                    'pnl_pct': pnl_pct
                }
            
            # Check take profit
            if pnl_pct >= self.config.TAKE_PROFIT_PERCENTAGE:
                self.log.info(f"Take profit triggered: {pnl_pct:.2%}")
                return {
                    'type': 'close',
                    'reason': 'take_profit',
                    'pnl_pct': pnl_pct
                }
            
            return None
            
        except Exception as e:
            self.log.error(f"Error closing position: {e}")
            return None
    
    def validate(self) -> bool:
        """Validate strategy configuration."""
        try:
            # Check required config attributes
            required_attrs = [
                'KALMAN_THRESHOLD', 'DEVIATION_THRESHOLD', 'ML_CONFIDENCE_THRESHOLD',
                'CAPITAL', 'RISK_PER_TRADE', 'MAX_POSITION_SIZE'
            ]
            
            for attr in required_attrs:
                if not hasattr(self.config, attr):
                    self.log.error(f"Missing required config: {attr}")
                    return False
            
            return True
        except Exception as e:
            self.log.error(f"Strategy validation failed: {e}")
            return False




