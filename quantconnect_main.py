from AlgorithmImports import *
import pandas as pd
import numpy as np
from datetime import timedelta
from liquidation_hunter_ai_coded import LiquidationHunterAICoded


class LiquidationHunterQC(QCAlgorithm):

    def Initialize(self):
        # === CONFIGURACIÓN GENERAL ===
        self.SetStartDate(2025, 9, 1)
        self.SetEndDate(2025, 10, 1)
        self.SetCash(5000)

        # === MERCADO ===
        self.symbol = self.AddCrypto("ETHUSD", Resolution.Minute).Symbol

        # Consolidar a velas de 15 minutos
        self.consolidator = TradeBarConsolidator(timedelta(minutes=15))
        self.SubscriptionManager.AddConsolidator(self.symbol, self.consolidator)
        self.consolidator.DataConsolidated += self.On15mBar

        # === HISTÓRICO DE VELAS ===
        # CORRECCIÓN: Inicializar correctamente el RollingWindow
        self.window = RollingWindow[TradeBar](50)  # 50 velas de 15 minutos

        # === INDICADORES ===
        self.rsi = RelativeStrengthIndex(14, MovingAverageType.Simple)
        self.ema_fast = ExponentialMovingAverage(9)
        self.ema_slow = ExponentialMovingAverage(21)

        self.RegisterIndicator(self.symbol, self.rsi, self.consolidator)
        self.RegisterIndicator(self.symbol, self.ema_fast, self.consolidator)
        self.RegisterIndicator(self.symbol, self.ema_slow, self.consolidator)

        # Calentar datos 10 días antes de iniciar
        self.SetWarmUp(timedelta(days=10))

        # === ESTRATEGIA ===
        self.strategy = LiquidationHunterAICoded()
        self.last_action = None

        self.Debug("✅ LiquidationHunterQC initialized successfully")

    def On15mBar(self, sender, bar: TradeBar):
        # Agregar vela a la ventana
        self.window.Add(bar)

        # Logs informativos
        self.Debug(f"[BAR] {bar.EndTime} | Close: {bar.Close}")

        # Validar que haya suficiente histórico
        if self.IsWarmingUp or self.window.Count < 20 or not self.rsi.IsReady:
            return

        # === PREPARAR FEATURES ===
        closes = [x.Close for x in self.window]
        series = pd.Series(closes)
        df = pd.DataFrame({
            "close": closes,
            "kalman_signal": series - series.rolling(9).mean(),
            "kalman_deviation": series.rolling(9).std().fillna(0.0)
        })

        # === SIMULAR PREDICCIÓN ML ===
        rsi_value = float(self.rsi.Current.Value)
        if rsi_value < 30:
            ml_prediction = {"prediction": 1, "confidence": 0.8}  # long
        elif rsi_value > 70:
            ml_prediction = {"prediction": 0, "confidence": 0.8}  # short
        else:
            ml_prediction = {
                "prediction": 1 if float(self.ema_fast.Current.Value) > float(self.ema_slow.Current.Value) else 0,
                "confidence": 0.6
            }

        # Loguear señales de ML
        self.Debug(f"[ML] RSI={rsi_value:.2f}, pred={ml_prediction['prediction']}, conf={ml_prediction['confidence']}")

        # === GENERAR SEÑAL ===
        signal = self.strategy.generate_signal(df, ml_prediction)
        if signal:
            self.Debug(f"[SIGNAL] {signal}")
            self.ExecuteSignal(signal)

        # === GESTIÓN DE SALIDA ===
        current_price = float(self.Securities[self.symbol].Price)
        if self.strategy.should_close_position(current_price):
            self.Liquidate(self.symbol)
            self.strategy.current_position = None
            self.last_action = None
            self.Debug(f"[EXIT] Closed position at {current_price}")

    def ExecuteSignal(self, signal: dict):
        action = signal.get("action")
        price = float(signal.get("price", 0.0))

        if action == "long" and self.last_action != "long":
            self.SetHoldings(self.symbol, 1.0)
            self.last_action = "long"
            self.strategy.current_position = signal
            self.Debug(f"[TRADE] LONG @ {price}")

        elif action == "short" and self.last_action != "short":
            self.SetHoldings(self.symbol, -1.0)
            self.last_action = "short"
            self.strategy.current_position = signal
            self.Debug(f"[TRADE] SHORT @ {price}")



