import backtrader as bt

class TrendFollowingADXEMAStrategy(bt.Strategy):
    """
    Trend Following Strategy with ADX + EMA
    
    Esta estrategia identifica tendencias fuertes y sostenidas usando:
    - ADX (Average Directional Index) para confirmar fuerza de tendencia
    - EMA (Exponential Moving Average) para dirección de tendencia
    - Ideal para mercados en tendencia fuerte (bull/bear markets)
    """
    
    params = (
        ('adx_period', 14),         # Período para ADX
        ('adx_threshold', 30),      # Ajustado: 20→30 (más restrictivo)
        ('ema_fast', 21),           # Ajustado: 8→21 (menos sensible)
        ('ema_slow', 55),           # Ajustado: 21→55 (menos sensible)
        ('position_size', 0.05),    # Ajustado: 20%→5% (menos riesgo)
        ('take_profit', 0.04),      # 4% take profit
        ('stop_loss', 0.01),        # 1% stop loss
        ('trailing_stop', 0.012),   # Ajustado: 2%→1.2%
    )

    def __init__(self):
        """Initialize indicators and variables"""
        # ADX para medir fuerza de tendencia
        self.adx = bt.ind.ADX(period=self.params.adx_period)
        
        # EMAs para dirección de tendencia
        self.ema_fast = bt.ind.EMA(period=self.params.ema_fast)
        self.ema_slow = bt.ind.EMA(period=self.params.ema_slow)
        
        # Crossover de EMAs
        self.ema_cross = bt.ind.CrossOver(self.ema_fast, self.ema_slow)
        
        # EMA200 para filtro de tendencia
        self.ema200 = bt.ind.EMA(period=200)
        
        # ATR para filtro de volatilidad
        self.atr = bt.ind.ATR(period=14)
        
        # Variables de control
        self.order = None
        self.entry_price = None
        self.trailing_stop_price = None
        
        # Logging
        print(f"[STRATEGY INIT] TrendFollowingADXEMAStrategy initialized")
        print(f"[STRATEGY PARAMS] adx_period: {self.params.adx_period}")
        print(f"[STRATEGY PARAMS] adx_threshold: {self.params.adx_threshold}")
        print(f"[STRATEGY PARAMS] ema_fast: {self.params.ema_fast}")
        print(f"[STRATEGY PARAMS] ema_slow: {self.params.ema_slow}")
        print(f"[STRATEGY PARAMS] position_size: {self.params.position_size}")
        print(f"[STRATEGY PARAMS] take_profit: {self.params.take_profit}")
        print(f"[STRATEGY PARAMS] stop_loss: {self.params.stop_loss}")
        print(f"[STRATEGY PARAMS] trailing_stop: {self.params.trailing_stop}")

    def _ensure_trailing_initialized(self):
        """Ensure trailing stop is properly initialized"""
        if getattr(self, 'trailing_stop_price', None) is None:
            self.trailing_stop_price = self.data.close[0] * (1 - self.params.trailing_stop)

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
                # Si es una compra que cierra posición, resetear trailing stop
                if self.position.size == 0:
                    self.trailing_stop_price = None
                else:
                    self.entry_price = order.executed.price
                    # Inicializar trailing stop
                    self.trailing_stop_price = self.entry_price * (1 - self.params.trailing_stop)
            else:
                self.log(f'SELL EXECUTED - Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                # Si es una venta que cierra posición, resetear trailing stop
                if self.position.size == 0:
                    self.trailing_stop_price = None
                else:
                    # Inicializar trailing stop para shorts
                    self.trailing_stop_price = self.entry_price * (1 + self.params.trailing_stop)

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
        # Ensure trailing stop is initialized
        self._ensure_trailing_initialized()
        
        # Skip if we have a pending order
        if self.order:
            return

        # Skip if we don't have enough data
        if len(self.data) < self.params.ema_slow:
            return

        # Get current position
        position = self.position.size

        # Entry logic
        if position == 0:  # No position
            # Filtros adicionales según el plan de ChatGPT
            atr_percentile_filter = self.atr[0] > 0  # ATR válido (simplificado)
            
            # Condiciones para entrada larga (tendencia alcista fuerte)
            # Solo longs si precio > EMA200 (filtro de tendencia)
            long_condition = (
                self.adx[0] > self.params.adx_threshold and    # ADX indica tendencia fuerte
                self.ema_fast[0] > self.ema_slow[0] and        # EMA rápida > EMA lenta
                self.data.volume[0] > 0 and                    # Volumen válido
                self.data.close[0] > self.ema_fast[0] and      # Precio por encima de EMA rápida
                self.data.close[0] > self.ema200[0] and        # Precio > EMA200 (tendencia alcista)
                atr_percentile_filter                           # ATR válido
            )
            
            # Condiciones para entrada corta (tendencia bajista fuerte)
            # Solo shorts si precio < EMA200 (filtro de tendencia)
            short_condition = (
                self.adx[0] > self.params.adx_threshold and    # ADX indica tendencia fuerte
                self.ema_fast[0] < self.ema_slow[0] and        # EMA rápida < EMA lenta
                self.data.volume[0] > 0 and                    # Volumen válido
                self.data.close[0] < self.ema_fast[0] and      # Precio por debajo de EMA rápida
                self.data.close[0] < self.ema200[0] and        # Precio < EMA200 (tendencia bajista)
                atr_percentile_filter                           # ATR válido
            )

            if long_condition:
                self.log(f'LONG TREND - Price: {self.data.close[0]:.2f}, '
                        f'ADX: {self.adx[0]:.2f}, EMA Fast: {self.ema_fast[0]:.2f}, '
                        f'EMA Slow: {self.ema_slow[0]:.2f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.buy(size=size)
                
            elif short_condition:
                self.log(f'SHORT TREND - Price: {self.data.close[0]:.2f}, '
                        f'ADX: {self.adx[0]:.2f}, EMA Fast: {self.ema_fast[0]:.2f}, '
                        f'EMA Slow: {self.ema_slow[0]:.2f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.sell(size=size)

        # Exit logic for long positions
        elif position > 0:  # Long position
            if self.entry_price is not None:
                # Inicializar trailing stop si es la primera vez
                if self.trailing_stop_price is None:
                    self.trailing_stop_price = self.data.close[0] * (1 - self.params.trailing_stop)
                else:
                    # Actualizar trailing stop solo si en posición
                    new_trailing_stop = self.data.close[0] * (1 - self.params.trailing_stop)
                    self.trailing_stop_price = max(
                        self.trailing_stop_price,
                        new_trailing_stop
                    )
                
                # Take profit
                if self.data.close[0] >= self.entry_price * (1 + self.params.take_profit):
                    self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Stop loss
                elif self.data.close[0] <= self.entry_price * (1 - self.params.stop_loss):
                    self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Trailing stop
                elif self.trailing_stop_price is not None and self.data.close[0] <= self.trailing_stop_price:
                    self.log(f'TRAILING STOP - Price: {self.data.close[0]:.2f}, '
                            f'Stop: {self.trailing_stop_price:.2f}')
                    self.order = self.close()
                # Exit cuando ADX pierde fuerza (tendencia se debilita)
                elif self.adx[0] < self.params.adx_threshold:
                    self.log(f'ADX WEAK EXIT - Price: {self.data.close[0]:.2f}, '
                            f'ADX: {self.adx[0]:.2f}')
                    self.order = self.close()
                # Exit cuando EMAs se cruzan en contra
                elif self.ema_cross[0] < 0:
                    self.log(f'EMA CROSS EXIT - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()

        # Exit logic for short positions
        elif position < 0:  # Short position
            if self.entry_price is not None:
                # Inicializar trailing stop si es la primera vez
                if self.trailing_stop_price is None:
                    self.trailing_stop_price = self.data.close[0] * (1 + self.params.trailing_stop)
                else:
                    # Actualizar trailing stop para shorts
                    new_trailing_stop = self.data.close[0] * (1 + self.params.trailing_stop)
                    self.trailing_stop_price = min(
                        self.trailing_stop_price,
                        new_trailing_stop
                    )
                
                # Take profit
                if self.data.close[0] <= self.entry_price * (1 - self.params.take_profit):
                    self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Stop loss
                elif self.data.close[0] >= self.entry_price * (1 + self.params.stop_loss):
                    self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Trailing stop
                elif self.trailing_stop_price is not None and self.data.close[0] >= self.trailing_stop_price:
                    self.log(f'TRAILING STOP - Price: {self.data.close[0]:.2f}, '
                            f'Stop: {self.trailing_stop_price:.2f}')
                    self.order = self.close()
                # Exit cuando ADX pierde fuerza (tendencia se debilita)
                elif self.adx[0] < self.params.adx_threshold:
                    self.log(f'ADX WEAK EXIT - Price: {self.data.close[0]:.2f}, '
                            f'ADX: {self.adx[0]:.2f}')
                    self.order = self.close()
                # Exit cuando EMAs se cruzan en contra
                elif self.ema_cross[0] > 0:
                    self.log(f'EMA CROSS EXIT - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
