"""
Liquidation Hunter Strategy for Backtrader
Migrated from Freqtrade LiquidationHunterFreq
Maintains Kalman Filter logic and ML predictions
"""

import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, Any


class LiquidationHunterStrategy(bt.Strategy):
    """
    Liquidation Hunter Strategy for Backtrader
    
    This strategy combines:
    - Kalman Filter signals for trend detection
    - ML-like predictions using RSI and EMA crossovers
    - Risk management with stop loss and take profit
    """
    
    params = (
        # Kalman Filter parameters
        ('kalman_threshold', 0.3),
        ('deviation_threshold', 1.5),
        ('ml_confidence_threshold', 0.55),
        
        # Technical indicator parameters
        ('rsi_period', 14),
        ('ema_fast_period', 8),
        ('ema_slow_period', 21),
        
        # Risk management
        ('stop_loss', 0.03),  # 3%
        ('take_profit', 0.06),  # 6%
        
        # Position sizing
        ('position_size', 0.95),  # 95% of portfolio
    )
    
    def __init__(self):
        """Initialize indicators and variables"""
        # Technical indicators
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.ema_fast = bt.indicators.EMA(self.data.close, period=self.params.ema_fast_period)
        self.ema_slow = bt.indicators.EMA(self.data.close, period=self.params.ema_slow_period)
        
        # Kalman-like signals
        self.kalman_signal = self.data.close - self.ema_fast
        self.kalman_deviation = bt.indicators.StandardDeviation(self.data.close, period=9)
        
        # Add startup period to ensure indicators are ready
        self.startup_period = max(self.params.rsi_period, self.params.ema_slow_period, 9)
        
        # ML-like prediction variables
        self.ml_prediction = 0
        self.ml_confidence = 0.0
        
        # Strategy state
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        
        # Logging
        print(f"[STRATEGY INIT] LiquidationHunterStrategy initialized")
        print(f"[STRATEGY PARAMS] kalman_threshold: {self.params.kalman_threshold}")
        print(f"[STRATEGY PARAMS] deviation_threshold: {self.params.deviation_threshold}")
        print(f"[STRATEGY PARAMS] ml_confidence_threshold: {self.params.ml_confidence_threshold}")
        print(f"[STRATEGY PARAMS] rsi_period: {self.params.rsi_period}")
        print(f"[STRATEGY PARAMS] ema_fast_period: {self.params.ema_fast_period}")
        print(f"[STRATEGY PARAMS] ema_slow_period: {self.params.ema_slow_period}")
        print(f"[STRATEGY PARAMS] stop_loss: {self.params.stop_loss}")
        print(f"[STRATEGY PARAMS] take_profit: {self.params.take_profit}")
    
    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')
    
    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED - Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
            else:
                self.log(f'SELL EXECUTED - Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications"""
        if not trade.isclosed:
            return
        
        self.log(f'TRADE PROFIT - Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')
    
    def calculate_ml_prediction(self):
        """Calculate ML-like prediction based on RSI and EMA"""
        rsi_value = self.rsi[0]
        ema_fast_value = self.ema_fast[0]
        ema_slow_value = self.ema_slow[0]
        
        # Long conditions (relaxed RSI thresholds)
        if rsi_value < 40 or ema_fast_value > ema_slow_value:
            self.ml_prediction = 1
            self.ml_confidence = 0.8 if rsi_value < 40 else 0.6
        # Short conditions (relaxed RSI thresholds)
        elif rsi_value > 60 or ema_fast_value < ema_slow_value:
            self.ml_prediction = 0
            self.ml_confidence = 0.8 if rsi_value > 60 else 0.6
        else:
            # Neutral zone
            self.ml_prediction = 1 if ema_fast_value > ema_slow_value else 0
            self.ml_confidence = 0.6
    
    def check_entry_conditions(self):
        """Check if entry conditions are met"""
        # Calculate ML prediction
        self.calculate_ml_prediction()
        
        # Get current values
        kalman_signal = abs(self.kalman_signal[0])
        kalman_deviation = self.kalman_deviation[0]
        
        # Strategy conditions
        strong_kalman = kalman_signal > self.params.kalman_threshold
        high_deviation = kalman_deviation > self.params.deviation_threshold
        high_confidence = self.ml_confidence > self.params.ml_confidence_threshold
        
        # Volume check (if available)
        volume_ok = True
        if hasattr(self.data, 'volume'):
            volume_ok = self.data.volume[0] > 0
        
        return strong_kalman and high_deviation and high_confidence and volume_ok
    
    def next(self):
        """Main strategy logic executed on each bar"""
        # Skip if we have a pending order
        if self.order:
            return
        
        # Skip if we don't have enough data for indicators
        if len(self.data) < self.startup_period:
            return
        
        # Get current position
        position = self.position.size
        
        # Entry logic
        if position == 0:  # No position
            if self.check_entry_conditions():
                if self.ml_prediction == 1:  # Long signal
                    self.log(f'LONG SIGNAL - RSI: {self.rsi[0]:.2f}, '
                            f'ML Confidence: {self.ml_confidence:.2f}')
                    self.order = self.buy(size=self.params.position_size)
                elif self.ml_prediction == 0:  # Short signal
                    self.log(f'SHORT SIGNAL - RSI: {self.rsi[0]:.2f}, '
                            f'ML Confidence: {self.ml_confidence:.2f}')
                    self.order = self.sell(size=self.params.position_size)
        
        # Exit logic for long positions
        elif position > 0:  # Long position
            # Take profit
            if self.data.close[0] >= self.buy_price * (1 + self.params.take_profit):
                self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                self.order = self.sell(size=position)
            # Stop loss
            elif self.data.close[0] <= self.buy_price * (1 - self.params.stop_loss):
                self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                self.order = self.sell(size=position)
            # Exit signal
            elif self.rsi[0] > 70 or self.ema_fast[0] < self.ema_slow[0]:
                self.log(f'EXIT SIGNAL - RSI: {self.rsi[0]:.2f}')
                self.order = self.sell(size=position)
        
        # Exit logic for short positions
        elif position < 0:  # Short position
            # Take profit
            if self.data.close[0] <= self.buy_price * (1 - self.params.take_profit):
                self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                self.order = self.buy(size=abs(position))
            # Stop loss
            elif self.data.close[0] >= self.buy_price * (1 + self.params.stop_loss):
                self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                self.order = self.buy(size=abs(position))
            # Exit signal
            elif self.rsi[0] < 30 or self.ema_fast[0] > self.ema_slow[0]:
                self.log(f'EXIT SIGNAL - RSI: {self.rsi[0]:.2f}')
                self.order = self.buy(size=abs(position))

