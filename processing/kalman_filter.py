"""
Kalman filter implementation for price smoothing and signal generation.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple
import logging
from config import Config


class KalmanFilter:
    """Kalman filter for price smoothing and signal generation."""
    
    def __init__(self):
        """Initialize the Kalman filter."""
        self.config = Config()
        self.log = logging.getLogger(__name__)
        
        # Kalman filter parameters
        self.Q = self.config.KALMAN_Q  # Process noise
        self.R = self.config.KALMAN_R  # Measurement noise
        
        # State variables
        self.x = 0.0  # State estimate
        self.P = 1.0  # Error covariance
        self.initialized = False
    
    def apply_filter(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Apply Kalman filter to price data."""
        try:
            if data is None or data.empty:
                return None
            
            df = data.copy()
            
            # Initialize filter with first price
            if not self.initialized:
                self.x = df['close'].iloc[0]
                self.initialized = True
            
            # Apply Kalman filter
            kalman_prices = []
            kalman_deviations = []
            kalman_signals = []
            
            for price in df['close']:
                # Prediction step
                x_pred = self.x
                P_pred = self.P + self.Q
                
                # Update step
                K = P_pred / (P_pred + self.R)  # Kalman gain
                self.x = x_pred + K * (price - x_pred)
                self.P = (1 - K) * P_pred
                
                # Calculate deviation and signal
                deviation = abs(price - self.x)
                signal = 1 if deviation > self.config.DEVIATION_THRESHOLD else 0
                
                kalman_prices.append(self.x)
                kalman_deviations.append(deviation)
                kalman_signals.append(signal)
            
            # Add Kalman filter results to dataframe
            df['kalman_price'] = kalman_prices
            df['kalman_deviation'] = kalman_deviations
            df['kalman_signal'] = kalman_signals
            
            self.log.info(f"Applied Kalman filter to {len(df)} data points")
            return df
            
        except Exception as e:
            self.log.error(f"Error applying Kalman filter: {e}")
            return None
    
    def reset(self):
        """Reset the filter state."""
        self.x = 0.0
        self.P = 1.0
        self.initialized = False
    
    def validate(self) -> bool:
        """Validate Kalman filter configuration."""
        try:
            # Test with sample data
            test_data = pd.DataFrame({
                'close': [100, 101, 102, 101, 100]
            })
            result = self.apply_filter(test_data)
            return result is not None
        except Exception as e:
            self.log.error(f"Kalman filter validation failed: {e}")
            return False




