import backtrader as bt

class EMABreakoutConservativeStrategy(bt.Strategy):
    params = (
        ("ema_fast", 12),          # Mantener: 12
        ("ema_slow", 26),          # v2.1: 24→26 (suavizar señal)
        ("take_profit", 0.024),    # ChatGPT: 2.2%→2.4% (mejorar neto)
        ("stop_loss", 0.010),      # Mantener: 1.0%
        ("position_size", 0.1),    # Mantener: 10%
        ("volatility_threshold", 0.0015),  # v2.1: 0.25%→0.15% (más rupturas)
        ("trend_ema_fast", 20),
        ("trend_ema_slow", 50),
        ("trend_filter", True),    # v2.1: Activar filtro de tendencia
        ("trend_filter_ema_period", 100),  # v2.1: EMA100 para tendencia
        ("max_bars_in_trade", 96), # v2.1: Nuevo - máximo 96 barras en trade
        ("exit_on_opposite_signal", True), # v2.1: Nuevo - salir en señal contraria
    )

    def __init__(self):
        # EMAs principales
        self.ema_fast = bt.ind.EMA(period=self.p.ema_fast)
        self.ema_slow = bt.ind.EMA(period=self.p.ema_slow)
        self.cross = bt.ind.CrossOver(self.ema_fast, self.ema_slow)
        
        # Filtros de tendencia
        self.trend_ema_fast = bt.ind.EMA(period=self.p.trend_ema_fast)
        self.trend_ema_slow = bt.ind.EMA(period=self.p.trend_ema_slow)
        
        # EMA200 para filtro de tendencia (solo cortos bajo EMA200)
        self.ema200 = bt.ind.EMA(period=200)
        
        # v2.1: EMA100 para filtro de tendencia
        self.ema100 = bt.ind.EMA(period=self.p.trend_filter_ema_period)
        
        # Variables de control
        self.order = None
        self.entry_price = None
        self.entry_bar = -999  # v2.1: Barra de entrada para max_bars_in_trade
        
        # Logging
        print(f"[STRATEGY INIT] EMABreakoutConservativeStrategy initialized")
        print(f"[STRATEGY PARAMS] ema_fast: {self.p.ema_fast}")
        print(f"[STRATEGY PARAMS] ema_slow: {self.p.ema_slow}")
        print(f"[STRATEGY PARAMS] take_profit: {self.p.take_profit}")
        print(f"[STRATEGY PARAMS] stop_loss: {self.p.stop_loss}")
        print(f"[STRATEGY PARAMS] position_size: {self.p.position_size}")
        print(f"[STRATEGY PARAMS] volatility_threshold: {self.p.volatility_threshold}")

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
        # Reset entry bar
        self.entry_bar = -999

    def check_volatility_filter(self):
        """Filtro de volatilidad: solo entrar si high-low > 0.25% (optimizado)"""
        current_price = self.data.close[0]
        high_low_range = (self.data.high[0] - self.data.low[0]) / current_price
        return high_low_range > self.p.volatility_threshold  # 0.25% optimizado

    def check_trend_filter(self):
        """Filtro de tendencia: configurable desde parámetros"""
        if not self.p.trend_filter:
            return True  # Filtro desactivado
        # v2.1: Usar EMA100 para tendencia (ya inicializado en __init__)
        return self.data.close[0] > self.ema100[0]

    def next(self):
        if self.order:
            return
        
        # v2.1: Check for time-based exit (max_bars_in_trade)
        if self.position and self.entry_bar != -999:
            bars_in_trade = len(self.data) - self.entry_bar
            if bars_in_trade >= self.p.max_bars_in_trade:
                self.log(f'TIME EXIT - Max bars reached: {bars_in_trade}')
                self.close()
                return

        if not self.position:  # No position
            # Verificar filtros
            volatility_ok = self.check_volatility_filter()
            trend_ok = self.check_trend_filter()
            
            # v2.1: Check for opposite signal exit first
            if self.position and self.p.exit_on_opposite_signal:
                if self.position.size > 0 and self.cross < 0 and volatility_ok and trend_ok:
                    self.log(f'OPPOSITE SIGNAL EXIT - Sell signal while long')
                    self.close()
                    return
                elif self.position.size < 0 and self.cross > 0 and volatility_ok and trend_ok:
                    self.log(f'OPPOSITE SIGNAL EXIT - Buy signal while short')
                    self.close()
                    return
            
            if self.cross > 0 and volatility_ok and trend_ok:  # Buy signal
                self.log(f'BUY SIGNAL - EMA Fast: {self.ema_fast[0]:.2f}, EMA Slow: {self.ema_slow[0]:.2f}')
                self.log(f'FILTERS - Volatility: {volatility_ok}, Trend: {trend_ok}')
                self.order = self.buy(size=self.broker.getcash() * self.p.position_size / self.data.close[0])
                self.entry_bar = len(self.data)  # v2.1: Registrar barra de entrada
            elif self.cross < 0 and volatility_ok and trend_ok:  # Sell signal
                # Solo cortos si precio < EMA200 (filtro adicional)
                ema200_filter = self.data.close[0] < self.ema200[0]
                if ema200_filter:
                    self.log(f'SELL SIGNAL - EMA Fast: {self.ema_fast[0]:.2f}, EMA Slow: {self.ema_slow[0]:.2f}')
                    self.log(f'FILTERS - Volatility: {volatility_ok}, Trend: {trend_ok}, EMA200: {ema200_filter}')
                    self.order = self.sell(size=self.broker.getcash() * self.p.position_size / self.data.close[0])
                    self.entry_bar = len(self.data)  # v2.1: Registrar barra de entrada
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

    def stop(self):
        """Called when the strategy is stopped - force close all positions"""
        try:
            # Cancelar órdenes pendientes con validación de estado
            if hasattr(self, 'order') and self.order and self.order.status not in [bt.Order.Completed, bt.Order.Canceled]:
                self.cancel(self.order)
            
            # Cerrar posición si existe
            if self.broker and self.position and self.position.size != 0:
                self.log(f'FORCE CLOSE - Final position: {self.position.size}')
                self.close()
                
            # v2.1: Cancelar todas las órdenes abiertas
            for order in getattr(self, 'open_orders', []):
                try:
                    self.cancel(order)
                except:
                    pass
        except Exception as e:
            print(f'[stop] Exception: {e}')
