"""
Signal Engine - Motor de generación de señales en tiempo real
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Estructura de una señal de trading"""
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 - 1.0
    timestamp: float
    strategy: str
    price: float
    indicators: Dict[str, float]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

class SignalValidator:
    """Validador de señales con filtros de calidad"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.min_confidence = config.get('min_confidence', 0.7)
        self.throttle_seconds = config.get('throttle_seconds', 300)  # 5 minutos
        self.max_signals_per_hour = config.get('max_signals_per_hour', 6)
        
        # Tracking de señales para throttling
        self.last_signals: Dict[str, float] = {}  # symbol -> timestamp
        self.signals_this_hour: Dict[str, int] = {}  # symbol -> count
        self.hour_start = time.time()
    
    def validate_signal(self, signal: TradingSignal) -> bool:
        """Validar una señal de trading"""
        try:
            # 1. Validar confianza mínima
            if signal.confidence < self.min_confidence:
                logger.debug(f"Signal rejected: confidence {signal.confidence} < {self.min_confidence}")
                return False
            
            # 2. Validar throttling por símbolo
            if self._is_throttled(signal.symbol, signal.timestamp):
                logger.debug(f"Signal rejected: throttled for {signal.symbol}")
                return False
            
            # 3. Validar límite por hora
            if self._exceeds_hourly_limit(signal.symbol):
                logger.debug(f"Signal rejected: hourly limit exceeded for {signal.symbol}")
                return False
            
            # 4. Validar precio válido
            if signal.price <= 0:
                logger.debug(f"Signal rejected: invalid price {signal.price}")
                return False
            
            # 5. Validar indicadores básicos
            if not self._validate_indicators(signal.indicators):
                logger.debug(f"Signal rejected: invalid indicators")
                return False
            
            # Actualizar tracking
            self._update_tracking(signal.symbol, signal.timestamp)
            
            logger.info(f"Signal validated: {signal.symbol} {signal.signal_type} @ {signal.price} (confidence: {signal.confidence:.2f})")
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return False
    
    def _is_throttled(self, symbol: str, timestamp: float) -> bool:
        """Verificar si el símbolo está en período de throttling"""
        if symbol in self.last_signals:
            time_since_last = timestamp - self.last_signals[symbol]
            return time_since_last < self.throttle_seconds
        return False
    
    def _exceeds_hourly_limit(self, symbol: str) -> bool:
        """Verificar si se excede el límite de señales por hora"""
        current_hour = int(time.time() // 3600)
        if current_hour != int(self.hour_start // 3600):
            # Nueva hora, resetear contadores
            self.signals_this_hour.clear()
            self.hour_start = time.time()
        
        current_count = self.signals_this_hour.get(symbol, 0)
        return current_count >= self.max_signals_per_hour
    
    def _validate_indicators(self, indicators: Dict[str, float]) -> bool:
        """Validar que los indicadores tengan valores razonables"""
        required_indicators = ['rsi', 'ema_20', 'atr']
        
        for indicator in required_indicators:
            if indicator not in indicators:
                continue  # No todos los indicadores son requeridos
            
            value = indicators[indicator]
            
            # Validaciones específicas por indicador
            if indicator == 'rsi' and (value < 0 or value > 100):
                return False
            elif indicator == 'ema_20' and value <= 0:
                return False
            elif indicator == 'atr' and value <= 0:
                return False
        
        return True
    
    def _update_tracking(self, symbol: str, timestamp: float):
        """Actualizar tracking de señales"""
        self.last_signals[symbol] = timestamp
        self.signals_this_hour[symbol] = self.signals_this_hour.get(symbol, 0) + 1

class SignalEngine:
    """Motor principal de generación de señales"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validator = SignalValidator(config.get('signal_filters', {}))
        self.strategies = {}
        self.callbacks: List[Callable] = []
        
        # Buffer de datos para indicadores
        self.price_buffer: Dict[str, List[float]] = {}
        self.volume_buffer: Dict[str, List[float]] = {}
        self.buffer_size = config.get('buffer_size', 200)
        
        logger.info("SignalEngine initialized")
    
    def register_strategy(self, name: str, strategy_class, params: Dict[str, Any]):
        """Registrar una estrategia"""
        self.strategies[name] = {
            'class': strategy_class,
            'params': params,
            'enabled': True
        }
        logger.info(f"Strategy registered: {name}")
    
    def add_signal_callback(self, callback: Callable):
        """Agregar callback para señales generadas"""
        self.callbacks.append(callback)
    
    def update_market_data(self, symbol: str, price: float, volume: float = 0):
        """Actualizar datos de mercado"""
        # Actualizar buffer de precios
        if symbol not in self.price_buffer:
            self.price_buffer[symbol] = []
        
        self.price_buffer[symbol].append(price)
        if len(self.price_buffer[symbol]) > self.buffer_size:
            self.price_buffer[symbol].pop(0)
        
        # Actualizar buffer de volumen
        if symbol not in self.volume_buffer:
            self.volume_buffer[symbol] = []
        
        self.volume_buffer[symbol].append(volume)
        if len(self.volume_buffer[symbol]) > self.buffer_size:
            self.volume_buffer[symbol].pop(0)
    
    def generate_signals(self, symbol: str) -> List[TradingSignal]:
        """Generar señales para un símbolo"""
        signals = []
        
        if symbol not in self.price_buffer or len(self.price_buffer[symbol]) < 50:
            logger.info(f"🔍 SignalEngine: Insufficient data for {symbol} (buffer size: {len(self.price_buffer.get(symbol, []))})")
            return signals  # No hay suficientes datos
        
        current_price = self.price_buffer[symbol][-1]
        current_time = time.time()
        
        logger.info(f"🎯 SignalEngine: Evaluating {len(self.strategies)} strategies for {symbol} @ ${current_price}")
        
        # Generar señales para cada estrategia activa
        for strategy_name, strategy_info in self.strategies.items():
            logger.info(f"📊 Strategy: {strategy_name} - Enabled: {strategy_info['enabled']}")
            
            if not strategy_info['enabled']:
                logger.info(f"⏭️ Strategy: {strategy_name} - DISABLED, skipping")
                continue
            
            try:
                logger.info(f"🔍 Strategy: {strategy_name} - Evaluating conditions...")
                signal = self._generate_strategy_signal(
                    strategy_name, 
                    strategy_info, 
                    symbol, 
                    current_price, 
                    current_time
                )
                
                if signal:
                    logger.info(f"✅ Strategy: {strategy_name} - Signal generated: {signal.signal_type} (confidence: {signal.confidence:.2f})")
                    
                    if self.validator.validate_signal(signal):
                        logger.info(f"✅ Strategy: {strategy_name} - Signal VALIDATED and added")
                        signals.append(signal)
                        self._notify_callbacks(signal)
                    else:
                        logger.info(f"❌ Strategy: {strategy_name} - Signal REJECTED by validator")
                else:
                    logger.info(f"⏭️ Strategy: {strategy_name} - No signal generated (conditions not met)")
                    
            except Exception as e:
                logger.error(f"❌ Strategy: {strategy_name} - Error: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"📊 SignalEngine: Generated {len(signals)} total signals for {symbol}")
        return signals
    
    def _generate_strategy_signal(self, strategy_name: str, strategy_info: Dict, 
                                 symbol: str, price: float, timestamp: float) -> Optional[TradingSignal]:
        """Generar señal para una estrategia específica"""
        try:
            # Obtener indicadores calculados
            indicators = self._calculate_indicators(symbol)
            logger.info(f"📈 Strategy: {strategy_name} - Indicators: {indicators}")
            
            # Generar señal basada en la estrategia
            if strategy_name == 'VolatilityBreakoutStrategy':
                logger.info(f"🔍 Strategy: {strategy_name} - Calling volatility breakout logic...")
                return self._volatility_breakout_signal(symbol, price, timestamp, indicators, strategy_info['params'])
            elif strategy_name == 'RSIEMAMomentumStrategy':
                logger.info(f"🔍 Strategy: {strategy_name} - Calling RSI EMA momentum logic...")
                return self._rsi_ema_momentum_signal(symbol, price, timestamp, indicators, strategy_info['params'])
            elif strategy_name == 'BollingerReversionStrategy':
                logger.info(f"🔍 Strategy: {strategy_name} - Calling Bollinger reversion logic...")
                return self._bollinger_reversion_signal(symbol, price, timestamp, indicators, strategy_info['params'])
            elif strategy_name == 'EMABreakoutConservativeStrategy':
                logger.info(f"🔍 Strategy: {strategy_name} - Calling EMA breakout conservative logic...")
                return self._ema_breakout_conservative_signal(symbol, price, timestamp, indicators, strategy_info['params'])
            elif strategy_name == 'ContrarianVolumeSpikeStrategy':
                logger.info(f"🔍 Strategy: {strategy_name} - Calling contrarian volume spike logic...")
                return self._contrarian_volume_spike_signal(symbol, price, timestamp, indicators, strategy_info['params'])
            else:
                logger.warning(f"❌ Strategy: {strategy_name} - Unknown strategy type")
                return None
                
        except Exception as e:
            logger.error(f"❌ Strategy: {strategy_name} - Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_indicators(self, symbol: str) -> Dict[str, float]:
        """Calcular indicadores técnicos"""
        if symbol not in self.price_buffer or len(self.price_buffer[symbol]) < 20:
            return {}
        
        prices = self.price_buffer[symbol]
        indicators = {}
        
        try:
            # RSI (14 períodos)
            if len(prices) >= 14:
                indicators['rsi'] = self._calculate_rsi(prices, 14)
            
            # EMA (20 períodos)
            if len(prices) >= 20:
                indicators['ema_20'] = self._calculate_ema(prices, 20)
            
            # EMA (50 períodos)
            if len(prices) >= 50:
                indicators['ema_50'] = self._calculate_ema(prices, 50)
            
            # ATR (14 períodos)
            if len(prices) >= 14:
                indicators['atr'] = self._calculate_atr(prices, 14)
            
            # Bollinger Bands
            if len(prices) >= 20:
                bb = self._calculate_bollinger_bands(prices, 20, 2.0)
                indicators.update(bb)
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
        
        return indicators
    
    def _calculate_rsi(self, prices: List[float], period: int) -> float:
        """Calcular RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calcular EMA"""
        if len(prices) < period:
            return prices[-1]
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_atr(self, prices: List[float], period: int) -> float:
        """Calcular ATR simplificado (usando solo precios de cierre)"""
        if len(prices) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(prices)):
            tr = abs(prices[i] - prices[i-1])
            true_ranges.append(tr)
        
        if len(true_ranges) < period:
            return 0.0
        
        return sum(true_ranges[-period:]) / period
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int, std_dev: float) -> Dict[str, float]:
        """Calcular Bollinger Bands"""
        if len(prices) < period:
            return {}
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std = variance ** 0.5
        
        return {
            'bb_upper': sma + (std * std_dev),
            'bb_middle': sma,
            'bb_lower': sma - (std * std_dev)
        }
    
    def _volatility_breakout_signal(self, symbol: str, price: float, timestamp: float, 
                                   indicators: Dict[str, float], params: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generar señal para VolatilityBreakoutStrategy"""
        try:
            logger.info(f"🔍 VolatilityBreakout: Checking indicators for {symbol}")
            
            if 'atr' not in indicators or 'ema_20' not in indicators:
                logger.info(f"❌ VolatilityBreakout: Missing indicators - ATR: {'atr' in indicators}, EMA20: {'ema_20' in indicators}")
                return None
            
            atr = indicators['atr']
            ema_20 = indicators['ema_20']
            lookback = params.get('lookback', 18)
            multiplier = params.get('multiplier', 2.2)
            
            logger.info(f"📊 VolatilityBreakout: ATR={atr:.2f}, EMA20={ema_20:.2f}, Lookback={lookback}, Multiplier={multiplier}")
            
            # Calcular niveles de breakout
            if len(self.price_buffer[symbol]) >= lookback:
                recent_highs = self.price_buffer[symbol][-lookback:]
                recent_lows = self.price_buffer[symbol][-lookback:]
                
                highest = max(recent_highs)
                lowest = min(recent_lows)
                
                breakout_high = highest + (atr * multiplier)
                breakout_low = lowest - (atr * multiplier)
                
                logger.info(f"📈 VolatilityBreakout: Highest={highest:.2f}, Lowest={lowest:.2f}")
                logger.info(f"📈 VolatilityBreakout: Breakout High={breakout_high:.2f}, Breakout Low={breakout_low:.2f}")
                logger.info(f"📈 VolatilityBreakout: Current Price={price:.2f}")
                
                # Señal de compra: precio rompe por encima del máximo + ATR
                if price > breakout_high:
                    confidence = min(0.9, 0.6 + (atr / price) * 10)  # Confianza basada en volatilidad
                    logger.info(f"✅ VolatilityBreakout: BUY signal generated! Price {price:.2f} > Breakout High {breakout_high:.2f}")
                    return TradingSignal(
                        symbol=symbol,
                        signal_type='BUY',
                        confidence=confidence,
                        timestamp=timestamp,
                        strategy='VolatilityBreakoutStrategy',
                        price=price,
                        indicators=indicators,
                        metadata={'breakout_level': highest + (atr * multiplier)}
                    )
                
                # Señal de venta: precio rompe por debajo del mínimo - ATR
                elif price < breakout_low:
                    confidence = min(0.9, 0.6 + (atr / price) * 10)
                    logger.info(f"✅ VolatilityBreakout: SELL signal generated! Price {price:.2f} < Breakout Low {breakout_low:.2f}")
                    return TradingSignal(
                        symbol=symbol,
                        signal_type='SELL',
                        confidence=confidence,
                        timestamp=timestamp,
                        strategy='VolatilityBreakoutStrategy',
                        price=price,
                        indicators=indicators,
                        metadata={'breakout_level': breakout_low}
                    )
                else:
                    logger.info(f"⏭️ VolatilityBreakout: No signal - Price {price:.2f} between breakout levels")
            else:
                logger.info(f"❌ VolatilityBreakout: Insufficient data - Buffer size: {len(self.price_buffer[symbol])}, Required: {lookback}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ VolatilityBreakout: Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _rsi_ema_momentum_signal(self, symbol: str, price: float, timestamp: float, 
                                indicators: Dict[str, float], params: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generar señal para RSIEMAMomentumStrategy"""
        try:
            if 'rsi' not in indicators or 'ema_20' not in indicators:
                return None
            
            rsi = indicators['rsi']
            ema_20 = indicators['ema_20']
            rsi_buy_threshold = params.get('rsi_buy_threshold', 58)
            rsi_sell_threshold = params.get('rsi_sell_threshold', 42)
            
            # Señal de compra: RSI > threshold y precio > EMA
            if rsi > rsi_buy_threshold and price > ema_20:
                confidence = min(0.9, 0.5 + (rsi - rsi_buy_threshold) / 20)
                return TradingSignal(
                    symbol=symbol,
                    signal_type='BUY',
                    confidence=confidence,
                    timestamp=timestamp,
                    strategy='RSIEMAMomentumStrategy',
                    price=price,
                    indicators=indicators,
                    metadata={'rsi': rsi, 'ema_20': ema_20}
                )
            
            # Señal de venta: RSI < threshold y precio < EMA
            elif rsi < rsi_sell_threshold and price < ema_20:
                confidence = min(0.9, 0.5 + (rsi_sell_threshold - rsi) / 20)
                return TradingSignal(
                    symbol=symbol,
                    signal_type='SELL',
                    confidence=confidence,
                    timestamp=timestamp,
                    strategy='RSIEMAMomentumStrategy',
                    price=price,
                    indicators=indicators,
                    metadata={'rsi': rsi, 'ema_20': ema_20}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in RSI EMA momentum signal: {e}")
            return None
    
    def _bollinger_reversion_signal(self, symbol: str, price: float, timestamp: float, 
                                   indicators: Dict[str, float], params: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generar señal para BollingerReversionStrategy"""
        try:
            if 'bb_upper' not in indicators or 'bb_lower' not in indicators or 'bb_middle' not in indicators:
                return None
            
            bb_upper = indicators['bb_upper']
            bb_lower = indicators['bb_lower']
            bb_middle = indicators['bb_middle']
            
            # Señal de compra: precio toca banda inferior (reversión)
            if price <= bb_lower:
                confidence = min(0.9, 0.6 + (bb_lower - price) / bb_middle * 5)
                return TradingSignal(
                    symbol=symbol,
                    signal_type='BUY',
                    confidence=confidence,
                    timestamp=timestamp,
                    strategy='BollingerReversionStrategy',
                    price=price,
                    indicators=indicators,
                    metadata={'bb_lower': bb_lower, 'bb_middle': bb_middle}
                )
            
            # Señal de venta: precio toca banda superior (reversión)
            elif price >= bb_upper:
                confidence = min(0.9, 0.6 + (price - bb_upper) / bb_middle * 5)
                return TradingSignal(
                    symbol=symbol,
                    signal_type='SELL',
                    confidence=confidence,
                    timestamp=timestamp,
                    strategy='BollingerReversionStrategy',
                    price=price,
                    indicators=indicators,
                    metadata={'bb_upper': bb_upper, 'bb_middle': bb_middle}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in Bollinger reversion signal: {e}")
            return None
    
    def _notify_callbacks(self, signal: TradingSignal):
        """Notificar callbacks sobre nueva señal"""
        for callback in self.callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"Error in signal callback: {e}")
    
    def _ema_breakout_conservative_signal(self, symbol: str, price: float, timestamp: float, 
                                         indicators: Dict[str, float], params: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generar señal para EMABreakoutConservativeStrategy"""
        try:
            logger.info(f"🔍 EMABreakoutConservative: Checking indicators for {symbol}")
            
            if 'ema_20' not in indicators or 'ema_50' not in indicators:
                logger.info(f"❌ EMABreakoutConservative: Missing indicators - EMA20: {'ema_20' in indicators}, EMA50: {'ema_50' in indicators}")
                return None
            
            ema_20 = indicators['ema_20']
            ema_50 = indicators['ema_50']
            rsi = indicators.get('rsi', 50)
            atr = indicators.get('atr', 0)
            
            # Parámetros conservadores
            min_rsi_diff = params.get('min_rsi_diff', 5)
            min_ema_diff = params.get('min_ema_diff', 0.1)
            volume_confirmation = params.get('volume_confirmation', True)
            
            logger.info(f"📊 EMABreakoutConservative: EMA20={ema_20:.2f}, EMA50={ema_50:.2f}, RSI={rsi:.2f}")
            logger.info(f"📊 EMABreakoutConservative: MinRSI={min_rsi_diff}, MinEMA={min_ema_diff}, VolumeConf={volume_confirmation}")
            
            # Condiciones conservadoras para breakout
            ema_diff = abs(ema_20 - ema_50)
            rsi_diff = abs(rsi - 50)
            
            # Señal de compra: EMA20 cruza por encima de EMA50 con confirmaciones
            if ema_20 > ema_50 and ema_diff > min_ema_diff and rsi > 50 + min_rsi_diff:
                confidence = min(0.85, 0.6 + (ema_diff / price) * 100 + (rsi_diff / 50) * 0.2)
                logger.info(f"✅ EMABreakoutConservative: BUY signal generated! EMA20 {ema_20:.2f} > EMA50 {ema_50:.2f}, RSI {rsi:.2f}")
                return TradingSignal(
                    symbol=symbol,
                    signal_type='BUY',
                    confidence=confidence,
                    timestamp=timestamp,
                    strategy='EMABreakoutConservativeStrategy',
                    price=price,
                    indicators=indicators,
                    metadata={'ema_diff': ema_diff, 'rsi_diff': rsi_diff}
                )
            
            # Señal de venta: EMA20 cruza por debajo de EMA50 con confirmaciones
            elif ema_20 < ema_50 and ema_diff > min_ema_diff and rsi < 50 - min_rsi_diff:
                confidence = min(0.85, 0.6 + (ema_diff / price) * 100 + (rsi_diff / 50) * 0.2)
                logger.info(f"✅ EMABreakoutConservative: SELL signal generated! EMA20 {ema_20:.2f} < EMA50 {ema_50:.2f}, RSI {rsi:.2f}")
                return TradingSignal(
                    symbol=symbol,
                    signal_type='SELL',
                    confidence=confidence,
                    timestamp=timestamp,
                    strategy='EMABreakoutConservativeStrategy',
                    price=price,
                    indicators=indicators,
                    metadata={'ema_diff': ema_diff, 'rsi_diff': rsi_diff}
                )
            else:
                logger.info(f"⏭️ EMABreakoutConservative: No signal - EMA20 {ema_20:.2f}, EMA50 {ema_50:.2f}, RSI {rsi:.2f} (diff: {ema_diff:.2f}, rsi_diff: {rsi_diff:.2f})")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ EMABreakoutConservative: Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _contrarian_volume_spike_signal(self, symbol: str, price: float, timestamp: float, 
                                       indicators: Dict[str, float], params: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generar señal para ContrarianVolumeSpikeStrategy"""
        try:
            logger.info(f"🔍 ContrarianVolumeSpike: Checking indicators for {symbol}")
            
            if 'rsi' not in indicators:
                logger.info(f"❌ ContrarianVolumeSpike: Missing RSI indicator")
                return None
            
            rsi = indicators['rsi']
            ema_20 = indicators.get('ema_20', price)
            bb_upper = indicators.get('bb_upper', price * 1.02)
            bb_lower = indicators.get('bb_lower', price * 0.98)
            
            # Parámetros para detección de spike
            rsi_oversold = params.get('rsi_oversold', 30)
            rsi_overbought = params.get('rsi_overbought', 70)
            volume_spike_threshold = params.get('volume_spike_threshold', 1.5)
            
            logger.info(f"📊 ContrarianVolumeSpike: RSI={rsi:.2f}, Price={price:.2f}, EMA20={ema_20:.2f}")
            logger.info(f"📊 ContrarianVolumeSpike: BB_Upper={bb_upper:.2f}, BB_Lower={bb_lower:.2f}")
            
            # Detectar condiciones de spike contrario
            price_vs_ema = (price - ema_20) / ema_20 * 100
            
            # Señal contraria de compra: RSI sobrevendido + precio cerca de banda inferior
            if rsi < rsi_oversold and price <= bb_lower * 1.005 and price_vs_ema < -0.5:
                confidence = min(0.8, 0.5 + (rsi_oversold - rsi) / 30 * 0.3)
                logger.info(f"✅ ContrarianVolumeSpike: BUY signal generated! RSI {rsi:.2f} oversold, price {price:.2f} near BB lower")
                return TradingSignal(
                    symbol=symbol,
                    signal_type='BUY',
                    confidence=confidence,
                    timestamp=timestamp,
                    strategy='ContrarianVolumeSpikeStrategy',
                    price=price,
                    indicators=indicators,
                    metadata={'rsi_oversold': rsi, 'price_vs_ema': price_vs_ema}
                )
            
            # Señal contraria de venta: RSI sobrecomprado + precio cerca de banda superior
            elif rsi > rsi_overbought and price >= bb_upper * 0.995 and price_vs_ema > 0.5:
                confidence = min(0.8, 0.5 + (rsi - rsi_overbought) / 30 * 0.3)
                logger.info(f"✅ ContrarianVolumeSpike: SELL signal generated! RSI {rsi:.2f} overbought, price {price:.2f} near BB upper")
                return TradingSignal(
                    symbol=symbol,
                    signal_type='SELL',
                    confidence=confidence,
                    timestamp=timestamp,
                    strategy='ContrarianVolumeSpikeStrategy',
                    price=price,
                    indicators=indicators,
                    metadata={'rsi_overbought': rsi, 'price_vs_ema': price_vs_ema}
                )
            else:
                logger.info(f"⏭️ ContrarianVolumeSpike: No signal - RSI {rsi:.2f}, Price {price:.2f}, PriceVsEMA {price_vs_ema:.2f}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ ContrarianVolumeSpike: Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_strategy_status(self) -> Dict[str, Any]:
        """Obtener estado de las estrategias"""
        return {
            'strategies': {name: info['enabled'] for name, info in self.strategies.items()},
            'buffer_sizes': {symbol: len(prices) for symbol, prices in self.price_buffer.items()},
            'validator_stats': {
                'last_signals': self.validator.last_signals,
                'signals_this_hour': self.validator.signals_this_hour
            }
        }
