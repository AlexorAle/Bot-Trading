import backtrader as bt

class VolatilityBreakoutStrategy(bt.Strategy):
    """
    Volatility Breakout Strategy
    
    Entra en posiciones cuando el precio rompe un nivel de volatilidad
    basado en ATR y el máximo de los últimos N períodos.
    Ideal para mercados con alta volatilidad y tendencias fuertes.
    """
    
    params = (
        ('lookback', 18),           # Mantener: 18
        ('atr_period', 14),         # Período para ATR
        ('multiplier', 2.2),        # Mantener: 2.2 (filtro de ruido)
        ('trailing_stop', 0.025),   # Mantener: 2.5% (mejor R:R)
        ('position_size', 0.10),    # 10% del capital por trade
        ('disable_shorts_above_ema200d', True),  # Deshabilitar shorts por encima de EMA200
        ('disable_all_shorts', True),  # ChatGPT: Desactivar todos los shorts (cortar sangrado)
    )

    def __init__(self):
        """Initialize indicators and variables"""
        # ATR para medir volatilidad
        self.atr = bt.ind.ATR(period=self.params.atr_period)
        
        # ADX para filtrar tendencias fuertes
        self.adx = bt.ind.ADX(period=14)
        
        # EMA200 para filtro de tendencia
        self.ema200 = bt.ind.EMA(period=200)
        
        # Máximo de los últimos N períodos
        self.highest = bt.ind.Highest(self.data.high, period=self.params.lookback)
        
        # Mínimo de los últimos N períodos
        self.lowest = bt.ind.Lowest(self.data.low, period=self.params.lookback)
        
        # Variables de control
        self.order = None
        self.entry_price = None
        self.trailing_stop_price = None
        
        # Logging
        print(f"[STRATEGY INIT] VolatilityBreakoutStrategy initialized")
        print(f"[STRATEGY PARAMS] lookback: {self.params.lookback}")
        print(f"[STRATEGY PARAMS] atr_period: {self.params.atr_period}")
        print(f"[STRATEGY PARAMS] multiplier: {self.params.multiplier}")
        print(f"[STRATEGY PARAMS] trailing_stop: {self.params.trailing_stop}")
        print(f"[STRATEGY PARAMS] position_size: {self.params.position_size}")

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
                # Inicializar trailing stop
                self.trailing_stop_price = self.entry_price * (1 - self.params.trailing_stop)
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
        """Main strategy logic executed on each bar"""
        # Skip if we have a pending order
        if self.order:
            return

        # Skip if we don't have enough data
        if len(self.data) < self.params.lookback:
            return

        # Get current position
        position = self.position.size

        # Entry logic
        if position == 0:  # No position
            # Filtros adicionales según el plan de ChatGPT
            adx_filter = self.adx[0] > 20  # ADX > 20 para tendencia fuerte
            atr_filter = self.atr[0] > 0   # ATR válido
            
            # Condiciones para entrada larga (con filtros mejorados)
            long_condition = (
                self.data.close[0] > self.highest[-1] and  # Breakout del máximo anterior
                self.data.volume[0] > 0 and                # Volumen válido
                adx_filter and                             # ADX > 20
                atr_filter                                 # ATR válido
            )
            
            # Condiciones para entrada corta (con filtros mejorados)
            # ChatGPT: Desactivar todos los shorts para cortar el sangrado
            short_condition = False  # Desactivado completamente

            if long_condition:
                self.log(f'LONG BREAKOUT - Price: {self.data.close[0]:.2f}, '
                        f'ATR: {self.atr[0]:.2f}, Highest: {self.highest[0]:.2f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.buy(size=size)
                
            elif short_condition:
                self.log(f'SHORT BREAKOUT - Price: {self.data.close[0]:.2f}, '
                        f'ATR: {self.atr[0]:.2f}, Lowest: {self.lowest[0]:.2f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.sell(size=size)

        # Exit logic for long positions
        elif position > 0:  # Long position
            # Actualizar trailing stop
            new_trailing_stop = self.data.close[0] * (1 - self.params.trailing_stop)
            if new_trailing_stop > self.trailing_stop_price:
                self.trailing_stop_price = new_trailing_stop
            
            # Salir si el precio toca el trailing stop
            if self.data.close[0] <= self.trailing_stop_price:
                self.log(f'TRAILING STOP - Price: {self.data.close[0]:.2f}, '
                        f'Stop: {self.trailing_stop_price:.2f}')
                self.order = self.close()

        # Exit logic for short positions
        elif position < 0:  # Short position
            # Actualizar trailing stop para shorts
            new_trailing_stop = self.data.close[0] * (1 + self.params.trailing_stop)
            if new_trailing_stop < self.trailing_stop_price:
                self.trailing_stop_price = new_trailing_stop
            
            # Salir si el precio toca el trailing stop
            if self.data.close[0] >= self.trailing_stop_price:
                self.log(f'TRAILING STOP - Price: {self.data.close[0]:.2f}, '
                        f'Stop: {self.trailing_stop_price:.2f}')
                self.order = self.close()
