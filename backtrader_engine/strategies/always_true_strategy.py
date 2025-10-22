"""
AlwaysTrue Strategy - Test Strategy for 24h Validation
Generates BUY/SELL signals every 15 minutes for complete workflow testing
"""

import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AlwaysTrueStrategy:
    """
    Simple test strategy that always generates signals for validation.
    - Generates BUY every odd cycle, SELL every even cycle
    - Confidence: 0.85 (high confidence for testing)
    - Interval: 900 seconds (15 minutes)
    - Purpose: Validate complete trading flow (signals -> risk check -> orders -> execution)
    """

    def __init__(self, config=None):
        self.name = "AlwaysTrueStrategy"
        self.enabled = True
        self.signal_counter = 0
        self.last_signal_time = {}
        self.interval_seconds = 900  # 15 minutes
        self.symbols = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]
        self.base_confidence = 0.85
        self.config = config or {}
        
        logger.info(f"✅ AlwaysTrueStrategy inicializada - Intervalos de 15 minutos")

    def should_generate_signal(self, symbol, price, indicators=None):
        """
        Check if it's time to generate a signal for this symbol
        """
        current_time = time.time()
        
        if symbol not in self.last_signal_time:
            self.last_signal_time[symbol] = 0
        
        time_since_last = current_time - self.last_signal_time[symbol]
        
        if time_since_last >= self.interval_seconds:
            return True
        
        return False

    def generate_signal(self, symbol, price, indicators=None):
        """
        Generate a signal for testing
        Alternates between BUY and SELL
        """
        if not self.enabled:
            return None
        
        if not self.should_generate_signal(symbol, price, indicators):
            return None
        
        # Alternate BUY/SELL
        signal_type = "BUY" if self.signal_counter % 2 == 0 else "SELL"
        self.signal_counter += 1
        self.last_signal_time[symbol] = time.time()
        
        # Build signal
        signal = {
            "type": signal_type,
            "symbol": symbol,
            "confidence": self.base_confidence,
            "price": price,
            "strategy": self.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "indicators": {
                "always_true": True,
                "test_mode": True,
                "cycle_number": self.signal_counter,
                "signal_interval": "15min"
            },
            "metadata": {
                "source": "ALWAYSTRUE_TEST",
                "purpose": "24h_validation_test",
                "version": "1.0"
            }
        }
        
        logger.info(
            f"📊 [AlwaysTrue] {signal_type} signal for {symbol} @ ${price:.2f} "
            f"(Confidence: {self.base_confidence}, Cycle: {self.signal_counter})"
        )
        
        return signal

    def validate(self):
        """
        Validate strategy configuration
        """
        checks = {
            "enabled": self.enabled,
            "interval_seconds": self.interval_seconds == 900,
            "symbols": len(self.symbols) >= 3,
            "confidence": 0.7 <= self.base_confidence <= 1.0
        }
        
        if all(checks.values()):
            logger.info("✅ AlwaysTrueStrategy validation PASSED")
            return True
        
        failed = [k for k, v in checks.items() if not v]
        logger.error(f"❌ AlwaysTrueStrategy validation FAILED: {failed}")
        return False

    def reset(self):
        """
        Reset strategy state
        """
        self.signal_counter = 0
        self.last_signal_time = {}
        logger.info("🔄 AlwaysTrueStrategy resetted")

    def get_status(self):
        """
        Return current strategy status
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "signals_generated": self.signal_counter,
            "symbols_tracked": len(self.last_signal_time),
            "interval_seconds": self.interval_seconds,
            "base_confidence": self.base_confidence
        }
