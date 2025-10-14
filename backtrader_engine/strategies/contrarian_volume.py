import backtrader as bt

class ContrarianVolumeSpikeStrategy(bt.Strategy):
    """
    Contrarian Volume Spike Strategy
    
    Opera en contra de movimientos extremos del precio cuando hay
    picos de volumen, asumiendo que son reacciones exageradas.
    Ideal para capturar reversiones después de capitulaciones.
    """
    
    params = (
        ('volume_period', 20),      # Período para promedio de volumen
        ('volume_spike_multiplier', 3.0), # ChatGPT: 3.2→3.0 (afinar entradas extremas)
        ('spread_threshold', 0.01), # 1% diferencia mínima entre high-low
        ('position_size', 0.10),    # 10% del capital por trade
        ('stop_loss', 0.01),        # Mantener: 1.0% (mejor R:R)
        ('take_profit', 0.025),     # Mantener: 2.5%
        ('rsi_period', 14),         # RSI para confirmación
        ('rsi_buy_threshold', 30),  # Nuevo: filtro RSI para compras
        ('rsi_sell_threshold', 70), # Nuevo: filtro RSI para ventas
    )

    def __init__(self):
        """Initialize indicators and variables"""
        # Volumen promedio
        self.volume_avg = bt.ind.SMA(self.data.volume, period=self.params.volume_period)
        
        # RSI para confirmación de extremos
        self.rsi = bt.ind.RSI(period=self.params.rsi_period)
        
        # Bollinger Bands para confirmar mean reversion
        self.bb = bt.ind.BollingerBands(period=20, devfactor=2.0)
        
        # EMA20 para salida al volver a la media
        self.ema20 = bt.ind.EMA(period=20)
        
        # Variables de control
        self.order = None
        self.entry_price = None
        
        # Logging
        print(f"[STRATEGY INIT] ContrarianVolumeSpikeStrategy initialized")
        print(f"[STRATEGY PARAMS] volume_period: {self.params.volume_period}")
        print(f"[STRATEGY PARAMS] volume_spike_multiplier: {self.params.volume_spike_multiplier}")
        print(f"[STRATEGY PARAMS] spread_threshold: {self.params.spread_threshold}")
        print(f"[STRATEGY PARAMS] position_size: {self.params.position_size}")
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
        """Main strategy logic executed on each bar"""
        # Skip if we have a pending order
        if self.order:
            return

        # Skip if we don't have enough data
        if len(self.data) < self.params.volume_period:
            return

        # Get current position
        position = self.position.size

        # Entry logic
        if position == 0:  # No position
            # Calcular spread de la vela actual
            current_spread = (self.data.high[0] - self.data.low[0]) / self.data.close[0]
            
            # Verificar pico de volumen
            volume_spike = self.data.volume[0] > (self.volume_avg[0] * self.params.volume_spike_multiplier)
            
            # Condiciones para entrada larga (contraria a caída extrema)
            # Filtros RSI según plan: longs si RSI < 30-35
            long_condition = (
                volume_spike and                                    # Pico de volumen
                current_spread > self.params.spread_threshold and  # Spread significativo
                self.rsi[0] < 30 and                               # Ajustado: 35→30
                self.data.close[0] < self.data.open[0] and         # Vela bajista
                self.data.volume[0] > 0 and                        # Volumen válido
                self.data.close[0] <= self.bb.lines.bot[0] * 1.02  # Precio cerca de banda inferior BB
            )
            
            # Condiciones para entrada corta (contraria a subida extrema)
            # Filtros RSI según plan: shorts si RSI > 65-70
            short_condition = (
                volume_spike and                                    # Pico de volumen
                current_spread > self.params.spread_threshold and  # Spread significativo
                self.rsi[0] > 70 and                               # Ajustado: 65→70
                self.data.close[0] > self.data.open[0] and         # Vela alcista
                self.data.volume[0] > 0 and                        # Volumen válido
                self.data.close[0] >= self.bb.lines.top[0] * 0.98  # Precio cerca de banda superior BB
            )

            if long_condition:
                self.log(f'LONG CONTRARIAN - Price: {self.data.close[0]:.2f}, '
                        f'Volume: {self.data.volume[0]:.0f}, Avg: {self.volume_avg[0]:.0f}, '
                        f'RSI: {self.rsi[0]:.2f}, Spread: {current_spread:.3f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.buy(size=size)
                
            elif short_condition:
                self.log(f'SHORT CONTRARIAN - Price: {self.data.close[0]:.2f}, '
                        f'Volume: {self.data.volume[0]:.0f}, Avg: {self.volume_avg[0]:.0f}, '
                        f'RSI: {self.rsi[0]:.2f}, Spread: {current_spread:.3f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.sell(size=size)

        # Exit logic for long positions
        elif position > 0:  # Long position
            # Take profit
            if self.data.close[0] >= self.entry_price * (1 + self.params.take_profit):
                self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                self.order = self.close()
            # Stop loss
            elif self.data.close[0] <= self.entry_price * (1 - self.params.stop_loss):
                self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                self.order = self.close()
            # Exit cuando RSI se normaliza
            elif self.rsi[0] > 50:
                self.log(f'RSI NORMALIZATION EXIT - Price: {self.data.close[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.close()

        # Exit logic for short positions
        elif position < 0:  # Short position
            # Take profit
            if self.data.close[0] <= self.entry_price * (1 - self.params.take_profit):
                self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                self.order = self.close()
            # Stop loss
            elif self.data.close[0] >= self.entry_price * (1 + self.params.stop_loss):
                self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                self.order = self.close()
            # Exit cuando RSI se normaliza
            elif self.rsi[0] < 50:
                self.log(f'RSI NORMALIZATION EXIT - Price: {self.data.close[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.close()
