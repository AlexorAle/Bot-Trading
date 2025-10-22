"""
Indicadores Técnicos en Tiempo Real
Adaptación de indicadores de Backtrader para uso con datos de WebSocket
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RealtimeIndicators:
    """Calculadora de indicadores técnicos en tiempo real"""
    
    def __init__(self, buffer_size: int = 200):
        self.buffer_size = buffer_size
        self.price_buffers: Dict[str, List[float]] = {}
        self.volume_buffers: Dict[str, List[float]] = {}
        self.high_buffers: Dict[str, List[float]] = {}
        self.low_buffers: Dict[str, List[float]] = {}
        
    def update_data(self, symbol: str, price: float, volume: float = 0, 
                   high: float = None, low: float = None):
        """Actualizar datos de mercado para un símbolo"""
        if symbol not in self.price_buffers:
            self.price_buffers[symbol] = []
            self.volume_buffers[symbol] = []
            self.high_buffers[symbol] = []
            self.low_buffers[symbol] = []
        
        # Actualizar buffer de precios
        self.price_buffers[symbol].append(price)
        if len(self.price_buffers[symbol]) > self.buffer_size:
            self.price_buffers[symbol].pop(0)
        
        # Actualizar buffer de volumen
        self.volume_buffers[symbol].append(volume)
        if len(self.volume_buffers[symbol]) > self.buffer_size:
            self.volume_buffers[symbol].pop(0)
        
        # Actualizar buffers de high/low si están disponibles
        if high is not None:
            self.high_buffers[symbol].append(high)
            if len(self.high_buffers[symbol]) > self.buffer_size:
                self.high_buffers[symbol].pop(0)
        
        if low is not None:
            self.low_buffers[symbol].append(low)
            if len(self.low_buffers[symbol]) > self.buffer_size:
                self.low_buffers[symbol].pop(0)
    
    def get_indicators(self, symbol: str) -> Dict[str, float]:
        """Obtener todos los indicadores calculados para un símbolo"""
        if symbol not in self.price_buffers or len(self.price_buffers[symbol]) < 20:
            return {}
        
        indicators = {}
        
        try:
            prices = self.price_buffers[symbol]
            volumes = self.volume_buffers.get(symbol, [])
            highs = self.high_buffers.get(symbol, [])
            lows = self.low_buffers.get(symbol, [])
            
            # RSI
            if len(prices) >= 14:
                indicators['rsi'] = self._calculate_rsi(prices, 14)
            
            # EMAs
            if len(prices) >= 20:
                indicators['ema_20'] = self._calculate_ema(prices, 20)
            if len(prices) >= 50:
                indicators['ema_50'] = self._calculate_ema(prices, 50)
            if len(prices) >= 200:
                indicators['ema_200'] = self._calculate_ema(prices, 200)
            
            # SMAs
            if len(prices) >= 20:
                indicators['sma_20'] = self._calculate_sma(prices, 20)
            if len(prices) >= 50:
                indicators['sma_50'] = self._calculate_sma(prices, 50)
            
            # ATR
            if len(prices) >= 14:
                if len(highs) >= 14 and len(lows) >= 14:
                    indicators['atr'] = self._calculate_atr(prices, highs, lows, 14)
                else:
                    indicators['atr'] = self._calculate_atr_simple(prices, 14)
            
            # Bollinger Bands
            if len(prices) >= 20:
                bb = self._calculate_bollinger_bands(prices, 20, 2.0)
                indicators.update(bb)
            
            # MACD
            if len(prices) >= 26:
                macd = self._calculate_macd(prices, 12, 26, 9)
                indicators.update(macd)
            
            # ADX
            if len(prices) >= 14 and len(highs) >= 14 and len(lows) >= 14:
                indicators['adx'] = self._calculate_adx(prices, highs, lows, 14)
            
            # Volume indicators
            if len(volumes) >= 20:
                indicators['volume_sma'] = self._calculate_sma(volumes, 20)
                indicators['volume_ratio'] = volumes[-1] / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1.0
            
            # Support/Resistance levels
            if len(prices) >= 50:
                support_resistance = self._calculate_support_resistance(prices, 50)
                indicators.update(support_resistance)
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
        
        return indicators
    
    def _calculate_rsi(self, prices: List[float], period: int) -> float:
        """Calcular RSI (Relative Strength Index)"""
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
        
        # Calcular promedio de ganancias y pérdidas
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calcular EMA (Exponential Moving Average)"""
        if len(prices) < period:
            return prices[-1]
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Calcular SMA (Simple Moving Average)"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        return sum(prices[-period:]) / period
    
    def _calculate_atr(self, prices: List[float], highs: List[float], lows: List[float], period: int) -> float:
        """Calcular ATR (Average True Range) completo"""
        if len(prices) < period + 1 or len(highs) < period + 1 or len(lows) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(prices)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - prices[i-1])
            tr3 = abs(lows[i] - prices[i-1])
            tr = max(tr1, tr2, tr3)
            true_ranges.append(tr)
        
        if len(true_ranges) < period:
            return 0.0
        
        return sum(true_ranges[-period:]) / period
    
    def _calculate_atr_simple(self, prices: List[float], period: int) -> float:
        """Calcular ATR simplificado usando solo precios de cierre"""
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
            'bb_lower': sma - (std * std_dev),
            'bb_width': (std * std_dev * 2) / sma if sma > 0 else 0
        }
    
    def _calculate_macd(self, prices: List[float], fast_period: int, slow_period: int, signal_period: int) -> Dict[str, float]:
        """Calcular MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow_period:
            return {}
        
        # Calcular EMAs
        ema_fast = self._calculate_ema(prices, fast_period)
        ema_slow = self._calculate_ema(prices, slow_period)
        
        macd_line = ema_fast - ema_slow
        
        # Para la línea de señal, necesitaríamos un buffer de MACD
        # Por simplicidad, usamos una aproximación
        signal_line = macd_line * 0.9  # Aproximación simple
        
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        }
    
    def _calculate_adx(self, prices: List[float], highs: List[float], lows: List[float], period: int) -> float:
        """Calcular ADX (Average Directional Index) simplificado"""
        if len(prices) < period + 1 or len(highs) < period + 1 or len(lows) < period + 1:
            return 25.0  # Valor neutral
        
        # Calcular DM+ y DM-
        dm_plus = []
        dm_minus = []
        
        for i in range(1, len(highs)):
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]
            
            dm_plus.append(max(high_diff, 0) if high_diff > low_diff else 0)
            dm_minus.append(max(low_diff, 0) if low_diff > high_diff else 0)
        
        if len(dm_plus) < period:
            return 25.0
        
        # Calcular True Range
        true_ranges = []
        for i in range(1, len(prices)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - prices[i-1])
            tr3 = abs(lows[i] - prices[i-1])
            tr = max(tr1, tr2, tr3)
            true_ranges.append(tr)
        
        if len(true_ranges) < period:
            return 25.0
        
        # Calcular DI+ y DI-
        avg_dm_plus = sum(dm_plus[-period:]) / period
        avg_dm_minus = sum(dm_minus[-period:]) / period
        avg_tr = sum(true_ranges[-period:]) / period
        
        if avg_tr == 0:
            return 25.0
        
        di_plus = (avg_dm_plus / avg_tr) * 100
        di_minus = (avg_dm_minus / avg_tr) * 100
        
        # Calcular DX
        dx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100 if (di_plus + di_minus) > 0 else 0
        
        # ADX es el promedio de DX (simplificado)
        return min(100, max(0, dx))
    
    def _calculate_support_resistance(self, prices: List[float], lookback: int) -> Dict[str, float]:
        """Calcular niveles de soporte y resistencia"""
        if len(prices) < lookback:
            return {}
        
        recent_prices = prices[-lookback:]
        
        # Encontrar máximos y mínimos locales
        highs = []
        lows = []
        
        for i in range(2, len(recent_prices) - 2):
            if (recent_prices[i] > recent_prices[i-1] and 
                recent_prices[i] > recent_prices[i-2] and
                recent_prices[i] > recent_prices[i+1] and
                recent_prices[i] > recent_prices[i+2]):
                highs.append(recent_prices[i])
            
            if (recent_prices[i] < recent_prices[i-1] and 
                recent_prices[i] < recent_prices[i-2] and
                recent_prices[i] < recent_prices[i+1] and
                recent_prices[i] < recent_prices[i+2]):
                lows.append(recent_prices[i])
        
        # Calcular niveles de soporte y resistencia
        resistance = max(highs) if highs else max(recent_prices)
        support = min(lows) if lows else min(recent_prices)
        
        return {
            'resistance': resistance,
            'support': support,
            'resistance_distance': (resistance - prices[-1]) / prices[-1] if prices[-1] > 0 else 0,
            'support_distance': (prices[-1] - support) / prices[-1] if prices[-1] > 0 else 0
        }
    
    def get_buffer_status(self) -> Dict[str, int]:
        """Obtener estado de los buffers"""
        return {
            symbol: len(prices) for symbol, prices in self.price_buffers.items()
        }
    
    def clear_buffers(self, symbol: str = None):
        """Limpiar buffers de datos"""
        if symbol:
            if symbol in self.price_buffers:
                del self.price_buffers[symbol]
            if symbol in self.volume_buffers:
                del self.volume_buffers[symbol]
            if symbol in self.high_buffers:
                del self.high_buffers[symbol]
            if symbol in self.low_buffers:
                del self.low_buffers[symbol]
        else:
            self.price_buffers.clear()
            self.volume_buffers.clear()
            self.high_buffers.clear()
            self.low_buffers.clear()
