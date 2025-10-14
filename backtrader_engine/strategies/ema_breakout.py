import backtrader as bt

class EMABreakoutStrategy(bt.Strategy):
    params = (
        ("ema_fast", 8),
        ("ema_slow", 21),
        ("take_profit", 0.03),  # 3%
        ("stop_loss", 0.015),   # 1.5%
        ("position_size", 0.3)
    )

    def __init__(self):
        self.ema_fast = bt.ind.EMA(period=self.p.ema_fast)
        self.ema_slow = bt.ind.EMA(period=self.p.ema_slow)
        self.cross = bt.ind.CrossOver(self.ema_fast, self.ema_slow)
        self.order = None
        self.entry_price = None
        
        # Logging
        print(f"[STRATEGY INIT] EMABreakoutStrategy initialized")
        print(f"[STRATEGY PARAMS] ema_fast: {self.p.ema_fast}")
        print(f"[STRATEGY PARAMS] ema_slow: {self.p.ema_slow}")
        print(f"[STRATEGY PARAMS] take_profit: {self.p.take_profit}")
        print(f"[STRATEGY PARAMS] stop_loss: {self.p.stop_loss}")
        print(f"[STRATEGY PARAMS] position_size: {self.p.position_size}")

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
                self.entry_price = order.executed.price
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

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.cross > 0:
                size = self.broker.getvalue() * self.p.position_size / self.data.close[0]
                self.order = self.buy(size=size)
                self.log(f'BUY SIGNAL - EMA Fast: {self.ema_fast[0]:.2f}, EMA Slow: {self.ema_slow[0]:.2f}')

        else:
            if self.cross < 0:
                self.order = self.close()
                self.log(f'SELL SIGNAL - EMA Fast: {self.ema_fast[0]:.2f}, EMA Slow: {self.ema_slow[0]:.2f}')
            elif self.entry_price:
                if self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                    self.order = self.close()
                    self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                elif self.data.close[0] <= self.entry_price * (1 - self.p.stop_loss):
                    self.order = self.close()
                    self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
