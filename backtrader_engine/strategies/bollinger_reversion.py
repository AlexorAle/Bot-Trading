import backtrader as bt

class BollingerReversionStrategy(bt.Strategy):
    """
    Bollinger Bands Mean Reversion Strategy
    
    Opera en contra de la tendencia cuando el precio toca las bandas
    de Bollinger, asumiendo que volverá a la media.
    Ideal para mercados en rango lateral con volatilidad constante.
    """
    
    params = (
        ('bb_period', 18),          # Mantener: 18
        ('std_dev', 2.8),           # ChatGPT: 2.6→2.8 (mejor R:R sin perder WR)
        ('volume_filter_period', 20), # Período para filtro de volumen
        ('position_size', 0.10),    # 10% del capital por trade
        ('take_profit', 0.020),     # Mantener: 2.0% (mejor R:R)
        ('stop_loss', 0.009),       # Mantener: 0.9%
        ('max_bars_in_trade', 48),  # Máximo 48 barras en trade (2 días en 15min)
        ('adx_filter_max', 18),     # Filtro ADX máximo
    )

    def __init__(self):
        """Initialize indicators and variables"""
        # Bollinger Bands
        self.bb = bt.ind.BollingerBands(period=self.params.bb_period, 
                                       devfactor=self.params.std_dev)
        
        # Volumen promedio para filtro
        self.volume_avg = bt.ind.SMA(self.data.volume, period=self.params.volume_filter_period)
        
        # RSI para confirmación adicional
        self.rsi = bt.ind.RSI(period=14)
        
        # Filtros de tendencia según el plan
        self.ema50 = bt.ind.EMA(period=50)
        self.ema200 = bt.ind.EMA(period=200)
        self.adx = bt.ind.ADX(period=14)
        
        # Variables de control
        self.order = None
        self.entry_price = None
        self.entry_bar = None  # Barra de entrada para control de tiempo
        
        # Logging
        print(f"[STRATEGY INIT] BollingerReversionStrategy initialized")
        print(f"[STRATEGY PARAMS] bb_period: {self.params.bb_period}")
        print(f"[STRATEGY PARAMS] std_dev: {self.params.std_dev}")
        print(f"[STRATEGY PARAMS] volume_filter_period: {self.params.volume_filter_period}")
        print(f"[STRATEGY PARAMS] position_size: {self.params.position_size}")
        print(f"[STRATEGY PARAMS] take_profit: {self.params.take_profit}")
        print(f"[STRATEGY PARAMS] stop_loss: {self.params.stop_loss}")

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
                self.entry_bar = len(self.data)  # Registrar barra de entrada
            else:
                self.log(f'SELL EXECUTED - Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.entry_price = order.executed.price
                self.entry_bar = len(self.data)  # Registrar barra de entrada

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
        if len(self.data) < self.params.bb_period:
            return

        # Get current position
        position = self.position.size

        # Entry logic
        if position == 0:  # No position
            # Filtro de volumen más relajado
            volume_ok = self.data.volume[0] > self.volume_avg[0] * 0.5
            
            # Filtros de tendencia según el plan: operar solo si precio entre EMA50 y EMA200 o ADX < 18
            trend_filter = (
                (self.ema50[0] <= self.data.close[0] <= self.ema200[0]) or  # Precio entre EMA50 y EMA200
                (self.adx[0] < 18)  # ADX < 18 (tendencia débil)
            )
            
            # Condiciones para entrada larga (precio cerca de banda inferior)
            long_condition = (
                self.data.close[0] <= self.bb.lines.bot[0] * 1.02 and  # Precio cerca de banda inferior (2% tolerancia)
                self.rsi[0] < 35 and                                   # RSI oversold (más relajado)
                volume_ok and                                          # Volumen por encima del 50% del promedio
                self.data.close[0] < self.bb.lines.mid[0] and          # Precio por debajo de la media
                trend_filter                                            # Filtro de tendencia
            )
            
            # Condiciones para entrada corta (precio cerca de banda superior)
            short_condition = (
                self.data.close[0] >= self.bb.lines.top[0] * 0.98 and  # Precio cerca de banda superior (2% tolerancia)
                self.rsi[0] > 65 and                                   # RSI overbought (más relajado)
                volume_ok and                                          # Volumen por encima del 50% del promedio
                self.data.close[0] > self.bb.lines.mid[0] and          # Precio por encima de la media
                trend_filter                                            # Filtro de tendencia
            )

            if long_condition:
                self.log(f'LONG REVERSION - Price: {self.data.close[0]:.2f}, '
                        f'BB Bot: {self.bb.lines.bot[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.buy(size=size)
                
            elif short_condition:
                self.log(f'SHORT REVERSION - Price: {self.data.close[0]:.2f}, '
                        f'BB Top: {self.bb.lines.top[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.sell(size=size)

        # Exit logic for long positions
        elif position > 0:  # Long position
            if self.entry_price is not None:
                # Control de tiempo máximo en trade
                bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
                time_exit = bars_in_trade >= self.params.max_bars_in_trade
                
                # Take profit
                if self.data.close[0] >= self.entry_price * (1 + self.params.take_profit):
                    self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Stop loss
                elif self.data.close[0] <= self.entry_price * (1 - self.params.stop_loss):
                    self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Time exit
                elif time_exit:
                    self.log(f'TIME EXIT - Price: {self.data.close[0]:.2f}, Bars: {bars_in_trade}')
                    self.order = self.close()
                # Exit cuando precio vuelve a la media
                elif self.data.close[0] >= self.bb.lines.mid[0]:
                    self.log(f'MEAN REVERSION EXIT - Price: {self.data.close[0]:.2f}, '
                            f'BB Mid: {self.bb.lines.mid[0]:.2f}')
                    self.order = self.close()

        # Exit logic for short positions
        elif position < 0:  # Short position
            if self.entry_price is not None:
                # Take profit
                if self.data.close[0] <= self.entry_price * (1 - self.params.take_profit):
                    self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Stop loss
                elif self.data.close[0] >= self.entry_price * (1 + self.params.stop_loss):
                    self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Exit cuando precio vuelve a la media
                elif self.data.close[0] <= self.bb.lines.mid[0]:
                    self.log(f'MEAN REVERSION EXIT - Price: {self.data.close[0]:.2f}, '
                            f'BB Mid: {self.bb.lines.mid[0]:.2f}')
                    self.order = self.close()
