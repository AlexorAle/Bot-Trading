"""
Simple Test Strategy for Backtrader
Basic strategy to test framework stability
"""

import backtrader as bt


class SimpleTestStrategy(bt.Strategy):
    """Simple test strategy with basic indicators"""
    
    params = (
        ('rsi_period', 14),
        ('stop_loss', 0.03),
        ('take_profit', 0.06),
        ('position_size', 0.95),
    )
    
    def __init__(self):
        """Initialize indicators"""
        # Simple RSI indicator
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        
        # Strategy state
        self.order = None
        self.buy_price = None
        
        print(f"[SIMPLE STRATEGY] Initialized with RSI period: {self.params.rsi_period}")
    
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
                self.log(f'BUY EXECUTED - Price: {order.executed.price:.2f}')
                self.buy_price = order.executed.price
            else:
                self.log(f'SELL EXECUTED - Price: {order.executed.price:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications"""
        if not trade.isclosed:
            return
        self.log(f'TRADE PROFIT - Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')
    
    def next(self):
        """Main strategy logic"""
        # Skip if we have a pending order
        if self.order:
            return
        
        # Skip if we don't have enough data
        if len(self.data) < self.params.rsi_period:
            return
        
        # Get current position
        position = self.position.size
        
        # Entry logic - simple RSI strategy
        if position == 0:  # No position
            if self.rsi[0] < 30:  # Oversold
                self.log(f'BUY SIGNAL - RSI: {self.rsi[0]:.2f}')
                self.order = self.buy(size=self.params.position_size)
            elif self.rsi[0] > 70:  # Overbought
                self.log(f'SELL SIGNAL - RSI: {self.rsi[0]:.2f}')
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
            elif self.rsi[0] > 70:
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
            elif self.rsi[0] < 30:
                self.log(f'EXIT SIGNAL - RSI: {self.rsi[0]:.2f}')
                self.order = self.buy(size=abs(position))
