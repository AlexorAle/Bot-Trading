# AlwaysTrue Testing Strategy - Implementation Guide

**Fecha:** 18 de Octubre, 2025  
**Para:** Agente de Desarrollo  
**Versión:** 1.0

---

##  Propósito

Estrategia de testing que genera señales cada 15 minutos alternando BUY/SELL para validar flujo completo del bot en Testnet.

---

##  Archivo: backtrader_engine/strategies/always_true_strategy.py

```python
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class AlwaysTrueStrategy:
    def __init__(self, config=None):
        self.last_signal_time = 0
        self.signal_counter = 0
        self.interval_seconds = 900
        self.enabled = True
    
    def should_generate_signal(self, symbol, price, indicators):
        if not self.enabled:
            return False
        return (time.time() - self.last_signal_time) >= self.interval_seconds
    
    def generate_signal(self, symbol, price, indicators):
        signal_type = 'BUY' if self.signal_counter % 2 == 0 else 'SELL'
        self.signal_counter += 1
        self.last_signal_time = time.time()
        
        return {
            'type': signal_type,
            'confidence': 0.85,
            'price': price,
            'strategy': 'AlwaysTrueTest',
            'indicators': {'test_mode': True, 'signal_number': self.signal_counter},
            'metadata': {'source': 'ALWAYSTRUE', 'purpose': 'TESTING'}
        }
```

---

## 🔧 Integración en SignalEngine

Agregar en signal_engine.py:

```python
from strategies.always_true_strategy import AlwaysTrueStrategy

# En __init__
self.always_true_strategy = AlwaysTrueStrategy(config.get('always_true', {}))

# En generate_signals()
if self.always_true_strategy.enabled and self.always_true_strategy.should_generate_signal(symbol, price, indicators):
    signal_data = self.always_true_strategy.generate_signal(symbol, price, indicators)
    signal = TradingSignal(...)
    signals.append(signal)
```

---

##  Configuración en bybit_x_config.json

```json
{
  \"always_true\": {
    \"enabled\": true,
    \"interval_minutes\": 15
  }
}
```

---

##  Validación

- Bot inicia sin errores
- Primera señal a los 15 minutos
- Señales alternan BUY  SELL
- Órdenes en Bybit Testnet
- Telegram notifica cada señal

---

**Listo para implementación**
