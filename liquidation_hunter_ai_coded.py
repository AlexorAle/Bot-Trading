"""
Liquidation hunting strategy implementation for QuantConnect.
Simplified to avoid external dependencies and to run cleanly in LEAN.
"""

import pandas as pd
from typing import Optional, Dict, Any


class Config:
    KALMAN_THRESHOLD = 0.5
    DEVIATION_THRESHOLD = 1.5
    ML_CONFIDENCE_THRESHOLD = 0.6
    STOP_LOSS_PERCENTAGE = 0.015
    TAKE_PROFIT_PERCENTAGE = 0.05
    CAPITAL = 10000
    RISK_PER_TRADE = 0.01
    MAX_POSITION_SIZE = 10
    COOLDOWN_MINUTES = 30


class LiquidationHunterAICoded:
    def __init__(self):
        self.config = Config()
        self.current_position: Optional[Dict[str, Any]] = None

    def generate_signal(self, data: pd.DataFrame, ml_prediction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if data is None or data.empty or ml_prediction is None:
            return None

        latest = data.iloc[-1]
        kalman_signal = float(latest.get("kalman_signal", 0.0))
        kalman_dev = float(latest.get("kalman_deviation", 0.0))
        ml_dir = int(ml_prediction.get("prediction", 1))
        ml_conf = float(ml_prediction.get("confidence", 0.0))
        price = float(latest["close"])

        strong_kalman = abs(kalman_signal) > self.config.KALMAN_THRESHOLD
        high_deviation = kalman_dev > self.config.DEVIATION_THRESHOLD
        high_conf = ml_conf > self.config.ML_CONFIDENCE_THRESHOLD

        if strong_kalman and high_deviation and high_conf:
            if ml_dir == 1:
                return self._create_long_signal(price)
            else:
                return self._create_short_signal(price)

        return None

    def _create_long_signal(self, price: float) -> Dict[str, Any]:
        sl = price * (1.0 - self.config.STOP_LOSS_PERCENTAGE)
        tp = price * (1.0 + self.config.TAKE_PROFIT_PERCENTAGE)
        return {
            "action": "long",
            "price": price,
            "stop_loss": sl,
            "take_profit": tp,
            "timestamp": pd.Timestamp.utcnow()
        }

    def _create_short_signal(self, price: float) -> Dict[str, Any]:
        sl = price * (1.0 + self.config.STOP_LOSS_PERCENTAGE)
        tp = price * (1.0 - self.config.TAKE_PROFIT_PERCENTAGE)
        return {
            "action": "short",
            "price": price,
            "stop_loss": sl,
            "take_profit": tp,
            "timestamp": pd.Timestamp.utcnow()
        }

    def should_close_position(self, current_price: float) -> bool:
        if self.current_position is None:
            return False

        action = self.current_position.get("action")
        sl = float(self.current_position.get("stop_loss"))
        tp = float(self.current_position.get("take_profit"))

        if action == "long":
            return current_price <= sl or current_price >= tp
        if action == "short":
            return current_price >= sl or current_price <= tp
        return False

