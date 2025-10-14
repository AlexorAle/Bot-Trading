import backtrader as bt

class RSIEMAMomentumStrategy(bt.Strategy):
    """
    RSI + EMA Momentum Strategy
    
    Combina señales de momentum del RSI con la dirección de tendencia
    de una EMA para identificar entradas en tendencias suaves.
    Ideal para mercados con tendencias claras y sostenidas.
    """
    
    params = (
        ('rsi_period', 14),         # Período para RSI
        ('rsi_buy_threshold', 58),  # v2.2: 60→58 (activar señales sin ruido)
        ('rsi_sell_threshold', 42), # v2.2: 40→42 (activar señales sin ruido)
        ('ema_period', 34),         # v2.2: 50→34 (activar momentum antes)
        ('position_size', 0.10),    # 10% del capital por trade
        ('take_profit', 0.028),     # v2.2: 3%→2.8% take profit
        ('stop_loss', 0.012),       # v2.2: 1%→1.2% stop loss
        ('volume_filter', 0.95),    # v2.2: 1.0→0.95 (liberar señales)
        ('cooldown_period', 3),     # v2.2: 5→3 (mayor reactividad)
        ('risk_filter_enabled', True), # Filtro de riesgo
        ('risk_tolerance', 0.03),   # v2.2: 2%→3% (menos restrictivo)
        ('max_bars_in_trade', 96),  # v2.2: Nuevo - máximo 96 barras en trade
        ('exit_on_opposite_signal', True), # v2.2: Nuevo - salir en señal contraria
        ('disable_shorts', False),  # ChatGPT: Control para desactivar shorts si es necesario
    )

    def __init__(self):
        """Initialize indicators and variables"""
        # RSI para momentum
        self.rsi = bt.ind.RSI(period=self.params.rsi_period)
        
        # EMA para tendencia
        self.ema = bt.ind.EMA(period=self.params.ema_period)
        
        # Volume filter - promedio de volumen
        self.volume_avg = bt.ind.SMA(self.data.volume, period=20)
        
        # ChatGPT: Indicadores para filtrar shorts
        self.adx = bt.ind.ADX(period=14)
        self.ema200 = bt.ind.EMA(period=200)
        
        # Variables de control
        self.order = None
        self.entry_price = None
        self.last_trade_bar = -999  # Para cooldown
        self.entry_bar = -999  # v2.2: Barra de entrada para max_bars_in_trade
        
        # Risk filter variables
        self.peak_value = self.broker.getvalue()  # Valor máximo alcanzado
        self.current_drawdown = 0.0  # Drawdown actual
        
        # Logging
        print(f"[STRATEGY INIT] RSIEMAMomentumStrategy initialized")
        print(f"[STRATEGY PARAMS] rsi_period: {self.params.rsi_period}")
        print(f"[STRATEGY PARAMS] rsi_buy_threshold: {self.params.rsi_buy_threshold}")
        print(f"[STRATEGY PARAMS] rsi_sell_threshold: {self.params.rsi_sell_threshold}")
        print(f"[STRATEGY PARAMS] ema_period: {self.params.ema_period}")
        print(f"[STRATEGY PARAMS] position_size: {self.params.position_size}")
        print(f"[STRATEGY PARAMS] take_profit: {self.params.take_profit}")
        print(f"[STRATEGY PARAMS] stop_loss: {self.params.stop_loss}")
        print(f"[STRATEGY PARAMS] volume_filter: {self.params.volume_filter}")
        print(f"[STRATEGY PARAMS] cooldown_period: {self.params.cooldown_period}")
        print(f"[STRATEGY PARAMS] risk_filter_enabled: {self.params.risk_filter_enabled}")
        print(f"[STRATEGY PARAMS] risk_tolerance: {self.params.risk_tolerance}")

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')
    
    def update_risk_metrics(self):
        """Update risk metrics (drawdown calculation)"""
        current_value = self.broker.getvalue()
        
        # Update peak value
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        # Calculate current drawdown
        if self.peak_value > 0:
            self.current_drawdown = (self.peak_value - current_value) / self.peak_value
        else:
            self.current_drawdown = 0.0
    
    def check_risk_filter(self):
        """Check if risk filter allows new trades"""
        if not self.params.risk_filter_enabled:
            return True
        
        return self.current_drawdown <= self.params.risk_tolerance

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
        # Registrar barra del último trade para cooldown
        self.last_trade_bar = len(self.data)
        # Reset entry bar
        self.entry_bar = -999

    def next(self):
        """Main strategy logic executed on each bar"""
        # Update risk metrics
        self.update_risk_metrics()
        
        # Skip if we have a pending order
        if self.order:
            return
        
        # v2.2: Check for time-based exit (max_bars_in_trade)
        if self.position and self.entry_bar != -999:
            bars_in_trade = len(self.data) - self.entry_bar
            if bars_in_trade >= self.params.max_bars_in_trade:
                self.log(f'TIME EXIT - Max bars reached: {bars_in_trade}')
                self.close()
                return

        # Skip if we don't have enough data
        if len(self.data) < self.params.ema_period:
            return

        # Get current position
        position = self.position.size

        # Entry logic
        if position == 0:  # No position
            # Debug: Log cada 50 barras para entender por qué no hay señales
            if len(self.data) % 50 == 0:
                self.log(f'DEBUG - RSI: {self.rsi[0]:.2f}, EMA: {self.ema[0]:.2f}, Close: {self.data.close[0]:.2f}')
                self.log(f'DEBUG - Buy threshold: {self.params.rsi_buy_threshold}, Sell threshold: {self.params.rsi_sell_threshold}')
                self.log(f'DEBUG - Volume: {self.data.volume[0]:.0f}')
            
            # Detectar cruces de RSI para momentum (eventos)
            # LONG: RSI cruza hacia abajo desde >60 (momentum bajista se agota)
            cross_down_for_long = (self.rsi[-1] > self.params.rsi_buy_threshold and 
                                  self.rsi[0] <= self.params.rsi_buy_threshold)
            # SHORT: RSI cruza hacia arriba desde <40 (momentum alcista se agota)
            cross_up_for_short = (self.rsi[-1] < self.params.rsi_sell_threshold and 
                                 self.rsi[0] >= self.params.rsi_sell_threshold)
            
            # Filtros adicionales
            volume_ok = self.data.volume[0] > self.volume_avg[0] * self.params.volume_filter
            cooldown_ok = len(self.data) - self.last_trade_bar >= self.params.cooldown_period
            risk_ok = self.check_risk_filter()  # v2.1: Nuevo filtro de riesgo
            
            # Condiciones para entrada larga (momentum puro v2.1)
            long_condition = (
                cross_down_for_long and                        # RSI cruza hacia abajo desde >60
                self.data.close[0] > self.ema[0] and           # Precio > EMA (confirmación de tendencia)
                volume_ok and                                  # Volumen > 1.0x promedio
                cooldown_ok and                                # Cooldown respetado (5 barras)
                risk_ok and                                    # v2.1: DD < 2%
                self.rsi[0] > 20 and self.rsi[0] < 80          # RSI en rango válido
            )
            
            # Condiciones para entrada corta (momentum puro v2.1 + filtros ChatGPT)
            short_condition = (
                cross_up_for_short and                         # RSI cruza hacia arriba desde <40
                self.data.close[0] < self.ema[0] and          # Precio < EMA (confirmación de tendencia)
                volume_ok and                                  # Volumen > 1.0x promedio
                cooldown_ok and                                # Cooldown respetado (5 barras)
                risk_ok and                                    # v2.1: DD < 2%
                self.rsi[0] > 20 and self.rsi[0] < 80 and     # RSI en rango válido
                self.adx[0] > 18 and                          # ChatGPT: ADX > 18 (tendencia fuerte)
                self.data.close[0] < self.ema200[0]           # ChatGPT: Precio < EMA200 (tendencia bajista global)
            )

            # v2.2: Check for opposite signal exit first
            if self.position and self.params.exit_on_opposite_signal:
                if self.position.size > 0 and short_condition:
                    self.log(f'OPPOSITE SIGNAL EXIT - Short signal while long')
                    self.close()
                    return
                elif self.position.size < 0 and long_condition:
                    self.log(f'OPPOSITE SIGNAL EXIT - Long signal while short')
                    self.close()
                    return
            
            if long_condition:
                self.log(f'LONG MOMENTUM - Price: {self.data.close[0]:.2f}, '
                        f'RSI: {self.rsi[0]:.2f}, EMA: {self.ema[0]:.2f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.buy(size=size)
                self.entry_bar = len(self.data)  # v2.2: Registrar barra de entrada
                
            elif short_condition:
                self.log(f'SHORT MOMENTUM - Price: {self.data.close[0]:.2f}, '
                        f'RSI: {self.rsi[0]:.2f}, EMA: {self.ema[0]:.2f}')
                amount_to_invest = self.broker.getcash() * self.params.position_size
                size = amount_to_invest / self.data.close[0]
                self.order = self.sell(size=size)
                self.entry_bar = len(self.data)  # v2.2: Registrar barra de entrada

        # Exit logic for long positions
        elif position > 0:  # Long position
            if self.entry_price is not None:
                # Take profit
                if self.data.close[0] >= self.entry_price * (1 + self.params.take_profit):
                    self.log(f'TAKE PROFIT - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Stop loss
                elif self.data.close[0] <= self.entry_price * (1 - self.params.stop_loss):
                    self.log(f'STOP LOSS - Price: {self.data.close[0]:.2f}')
                    self.order = self.close()
                # Exit cuando RSI se vuelve overbought
                elif self.rsi[0] > self.params.rsi_sell_threshold:
                    self.log(f'RSI EXIT - Price: {self.data.close[0]:.2f}, RSI: {self.rsi[0]:.2f}')
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
                
            # v2.2: Cancelar todas las órdenes abiertas
            for order in getattr(self, 'open_orders', []):
                try:
                    self.cancel(order)
                except:
                    pass
        except Exception as e:
            print(f'[stop] Exception: {e}')
