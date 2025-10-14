import backtrader as bt

class EMABreakoutAggressiveStrategy(bt.Strategy):
    params = (
        ("ema_fast", 4),
        ("ema_slow", 16),
        ("take_profit", 0.03),    # 3%
        ("stop_loss", 0.0125),   # 1.25%
        ("position_size", 0.20),  # 20%
        ("volatility_threshold", 0.01),  # 1.0% mínimo
        ("volume_period", 20),
        ("trend_ema_fast", 20),
        ("trend_ema_slow", 50),
    )

    def __init__(self):
        # EMAs principales
        self.ema_fast = bt.ind.EMA(period=self.p.ema_fast)
        self.ema_slow = bt.ind.EMA(period=self.p.ema_slow)
        self.cross = bt.ind.CrossOver(self.ema_fast, self.ema_slow)
        
        # Filtros de tendencia
        self.trend_ema_fast = bt.ind.EMA(period=self.p.trend_ema_fast)
        self.trend_ema_slow = bt.ind.EMA(period=self.p.trend_ema_slow)
        
        # Filtro de volumen
        self.volume_avg = bt.ind.SMA(self.data.volume, period=self.p.volume_period)
        
        # Variables de control
        self.order = None
        self.entry_price = None
        
        # Logging
        print(f"[STRATEGY INIT] EMABreakoutAggressiveStrategy initialized")
        print(f"[STRATEGY PARAMS] ema_fast: {self.p.ema_fast}")
        print(f"[STRATEGY PARAMS] ema_slow: {self.p.ema_slow}")
        print(f"[STRATEGY PARAMS] take_profit: {self.p.take_profit}")
        print(f"[STRATEGY PARAMS] stop_loss: {self.p.stop_loss}")
        print(f"[STRATEGY PARAMS] position_size: {self.p.position_size}")
        print(f"[STRATEGY PARAMS] volatility_threshold: {self.p.volatility_threshold}")
        print(f"[STRATEGY PARAMS] volume_period: {self.p.volume_period}")

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED - Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.entry_price = order.executed.price
            elif order.issell():
                self.log(f'SELL EXECUTED - Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'TRADE PROFIT - Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')

    def check_volatility_filter(self):
        """Filtro de volatilidad: solo entrar si high-low > 1.0%"""
        current_price = self.data.close[0]
        high_low_range = (self.data.high[0] - self.data.low[0]) / current_price
        return high_low_range > self.p.volatility_threshold

    def check_volume_filter(self):
        """Filtro de volumen: solo entrar si volumen > promedio de 20 velas"""
        return self.data.volume[0] > self.volume_avg[0]

    def check_trend_filter(self):
        """Filtro de tendencia: solo entrar si EMA20 > EMA50"""
        return self.trend_ema_fast[0] > self.trend_ema_slow[0]

    def next(self):
        if self.order:
            return

        if not self.position:  # No position
            # Verificar filtros
            volatility_ok = self.check_volatility_filter()
            volume_ok = self.check_volume_filter()
            trend_ok = self.check_trend_filter()
            
            if self.cross > 0 and volatility_ok and volume_ok and trend_ok:  # Buy signal
                self.log(f'BUY SIGNAL - EMA Fast: {self.ema_fast[0]:.2f}, EMA Slow: {self.ema_slow[0]:.2f}')
                self.log(f'FILTERS - Volatility: {volatility_ok}, Volume: {volume_ok}, Trend: {trend_ok}')
                self.order = self.buy(size=self.broker.getcash() * self.p.position_size / self.data.close[0])
            elif self.cross < 0 and volatility_ok and volume_ok and trend_ok:  # Sell signal
                self.log(f'SELL SIGNAL - EMA Fast: {self.ema_fast[0]:.2f}, EMA Slow: {self.ema_slow[0]:.2f}')
                self.log(f'FILTERS - Volatility: {volatility_ok}, Volume: {volume_ok}, Trend: {trend_ok}')
                self.order = self.sell(size=self.broker.getcash() * self.p.position_size / self.data.close[0])
        else:  # In position
            if self.entry_price:
                if self.position.size > 0:  # Long position
                    if self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                        self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                        self.order = self.close()
                    elif self.data.close[0] <= self.entry_price * (1 - self.p.stop_loss):
                        self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                        self.order = self.close()
                elif self.position.size < 0:  # Short position
                    if self.data.close[0] <= self.entry_price * (1 - self.p.take_profit):
                        self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                        self.order = self.close()
                    elif self.data.close[0] >= self.entry_price * (1 + self.p.stop_loss):
                        self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                        self.order = self.close()
