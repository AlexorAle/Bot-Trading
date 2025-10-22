"""
Risk Manager - Sistema de gestión de riesgo dinámico
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class RiskLimits:
    """Límites de riesgo configurables"""
    max_position_size: float = 0.1  # 10% del balance por trade
    max_daily_trades: int = 10
    max_daily_loss: float = 0.05  # 5% del balance diario
    max_drawdown: float = 0.10  # 10% drawdown máximo
    min_confidence: float = 0.7  # Confianza mínima para señales
    max_volatility: float = 0.05  # 5% volatilidad máxima (ATR/price)
    min_volume_ratio: float = 0.8  # 80% del volumen promedio
    max_correlation: float = 0.8  # Correlación máxima entre posiciones

@dataclass
class MarketConditions:
    """Condiciones de mercado"""
    volatility: float
    volume_ratio: float
    trend_strength: float
    market_regime: str  # 'trending', 'ranging', 'volatile'
    is_suitable_for_trading: bool

class RiskManager:
    """Gestor de riesgo dinámico"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.risk_limits = RiskLimits(**config.get('risk_limits', {}))
        
        # Tracking de riesgo
        self.daily_stats = {
            'trades_count': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'last_reset': time.time()
        }
        
        # Historial de posiciones para correlación
        self.position_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        # Condiciones de mercado
        self.market_conditions: Dict[str, MarketConditions] = {}
        
        logger.info("RiskManager initialized")
    
    def validate_signal(self, signal_data: Dict[str, Any], 
                       current_balance: float, 
                       current_positions: Dict[str, Any],
                       market_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validar una señal de trading
        
        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        try:
            symbol = signal_data.get('symbol', '')
            signal_type = signal_data.get('signal_type', '')
            confidence = signal_data.get('confidence', 0.0)
            price = signal_data.get('price', 0.0)
            strategy = signal_data.get('strategy', '')
            
            # 1. Validar confianza mínima
            if confidence < self.risk_limits.min_confidence:
                return False, f"Confidence {confidence:.2%} below minimum {self.risk_limits.min_confidence:.2%}"
            
            # 2. Validar límites diarios
            if not self._validate_daily_limits():
                return False, "Daily trading limits exceeded"
            
            # 3. Validar condiciones de mercado
            market_valid, market_reason = self._validate_market_conditions(symbol, market_data)
            if not market_valid:
                return False, f"Market conditions: {market_reason}"
            
            # 4. Validar tamaño de posición
            position_valid, position_reason = self._validate_position_size(
                symbol, signal_type, price, current_balance, current_positions
            )
            if not position_valid:
                return False, f"Position size: {position_reason}"
            
            # 5. Validar correlación
            correlation_valid, correlation_reason = self._validate_correlation(
                symbol, signal_type, current_positions
            )
            if not correlation_valid:
                return False, f"Correlation: {correlation_reason}"
            
            # 6. Validar drawdown
            if not self._validate_drawdown(current_balance):
                return False, "Maximum drawdown exceeded"
            
            logger.info(f"Signal validated: {symbol} {signal_type} @ {price}")
            return True, "Signal validated successfully"
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return False, f"Validation error: {e}"
    
    def _validate_daily_limits(self) -> bool:
        """Validar límites diarios"""
        current_time = time.time()
        
        # Reset diario si es un nuevo día
        if current_time - self.daily_stats['last_reset'] > 86400:  # 24 horas
            self.daily_stats = {
                'trades_count': 0,
                'total_pnl': 0.0,
                'max_drawdown': 0.0,
                'last_reset': current_time
            }
        
        # Verificar límite de trades diarios
        if self.daily_stats['trades_count'] >= self.risk_limits.max_daily_trades:
            return False
        
        # Verificar pérdida diaria máxima
        if self.daily_stats['total_pnl'] < -self.risk_limits.max_daily_loss:
            return False
        
        return True
    
    def _validate_market_conditions(self, symbol: str, market_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validar condiciones de mercado"""
        try:
            # Obtener indicadores de mercado
            atr = market_data.get('atr', 0.0)
            price = market_data.get('price', 0.0)
            volume = market_data.get('volume', 0.0)
            volume_avg = market_data.get('volume_avg', 0.0)
            
            if price <= 0:
                return False, "Invalid price data"
            
            # Calcular volatilidad (ATR/Price)
            volatility = atr / price if price > 0 else 0
            
            # Validar volatilidad máxima
            if volatility > self.risk_limits.max_volatility:
                return False, f"Volatility {volatility:.2%} exceeds limit {self.risk_limits.max_volatility:.2%}"
            
            # Validar volumen mínimo
            if volume_avg > 0:
                volume_ratio = volume / volume_avg
                if volume_ratio < self.risk_limits.min_volume_ratio:
                    return False, f"Volume ratio {volume_ratio:.2%} below minimum {self.risk_limits.min_volume_ratio:.2%}"
            
            # Determinar régimen de mercado
            market_regime = self._determine_market_regime(market_data)
            
            # Actualizar condiciones de mercado
            self.market_conditions[symbol] = MarketConditions(
                volatility=volatility,
                volume_ratio=volume_ratio if volume_avg > 0 else 1.0,
                trend_strength=market_data.get('adx', 25.0),
                market_regime=market_regime,
                is_suitable_for_trading=self._is_market_suitable(market_regime, volatility)
            )
            
            if not self.market_conditions[symbol].is_suitable_for_trading:
                return False, f"Market regime '{market_regime}' not suitable for trading"
            
            return True, "Market conditions suitable"
            
        except Exception as e:
            logger.error(f"Error validating market conditions: {e}")
            return False, f"Market validation error: {e}"
    
    def _determine_market_regime(self, market_data: Dict[str, Any]) -> str:
        """Determinar régimen de mercado"""
        try:
            adx = market_data.get('adx', 25.0)
            volatility = market_data.get('volatility', 0.0)
            rsi = market_data.get('rsi', 50.0)
            
            # Lógica para determinar régimen
            if adx > 30 and volatility < 0.03:
                return 'trending'
            elif adx < 20 and volatility < 0.02:
                return 'ranging'
            elif volatility > 0.04:
                return 'volatile'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Error determining market regime: {e}")
            return 'unknown'
    
    def _is_market_suitable(self, regime: str, volatility: float) -> bool:
        """Determinar si el mercado es adecuado para trading"""
        # Configuración de regímenes adecuados
        suitable_regimes = ['trending', 'ranging', 'neutral']
        
        # Verificar régimen
        if regime not in suitable_regimes:
            return False
        
        # Verificar volatilidad
        if volatility > self.risk_limits.max_volatility:
            return False
        
        return True
    
    def _validate_position_size(self, symbol: str, signal_type: str, price: float,
                              current_balance: float, current_positions: Dict[str, Any]) -> Tuple[bool, str]:
        """Validar tamaño de posición"""
        try:
            # Calcular tamaño de posición propuesto
            position_value = current_balance * self.risk_limits.max_position_size
            position_size = position_value / price if price > 0 else 0
            
            # Verificar si ya existe posición en el símbolo
            if symbol in current_positions:
                existing_position = current_positions[symbol]
                # Fix: PaperPosition is a dataclass, not a dict
                if hasattr(existing_position, 'size'):
                    existing_size = existing_position.size
                    existing_side = existing_position.side
                else:
                    # Fallback for dict-like positions
                    existing_size = existing_position.get('size', 0)
                    existing_side = existing_position.get('side', '')
                
                # Si es la misma dirección, verificar límite total
                if existing_side == signal_type:
                    total_size = existing_size + position_size
                    total_value = total_size * price
                    
                    if total_value > current_balance * self.risk_limits.max_position_size * 1.5:  # 15% máximo
                        return False, f"Total position size would exceed limit"
            
            # Verificar balance suficiente
            required_balance = position_size * price
            if required_balance > current_balance * 0.95:  # Dejar 5% de margen
                return False, "Insufficient balance for position"
            
            return True, "Position size valid"
            
        except Exception as e:
            logger.error(f"Error validating position size: {e}")
            return False, f"Position size validation error: {e}"
    
    def _validate_correlation(self, symbol: str, signal_type: str, 
                            current_positions: Dict[str, Any]) -> Tuple[bool, str]:
        """Validar correlación entre posiciones"""
        try:
            # Si no hay posiciones existentes, no hay correlación
            if not current_positions:
                return True, "No existing positions"
            
            # Verificar correlación con posiciones existentes
            for existing_symbol, position in current_positions.items():
                if existing_symbol == symbol:
                    continue
                
                # Calcular correlación simplificada (basada en tipo de activo)
                correlation = self._calculate_correlation(symbol, existing_symbol)
                
                if correlation > self.risk_limits.max_correlation:
                    return False, f"High correlation {correlation:.2%} with {existing_symbol}"
            
            return True, "Correlation acceptable"
            
        except Exception as e:
            logger.error(f"Error validating correlation: {e}")
            return False, f"Correlation validation error: {e}"
    
    def _calculate_correlation(self, symbol1: str, symbol2: str) -> float:
        """Calcular correlación simplificada entre símbolos"""
        # Correlación basada en tipo de activo
        crypto_pairs = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK']
        
        symbol1_base = symbol1.replace('USDT', '').replace('BUSD', '')
        symbol2_base = symbol2.replace('USDT', '').replace('BUSD', '')
        
        # Si ambos son crypto, alta correlación
        if symbol1_base in crypto_pairs and symbol2_base in crypto_pairs:
            return 0.7  # 70% correlación entre crypto
        
        # Si son el mismo activo, correlación perfecta
        if symbol1_base == symbol2_base:
            return 1.0
        
        return 0.3  # Correlación baja por defecto
    
    def _validate_drawdown(self, current_balance: float) -> bool:
        """Validar drawdown máximo"""
        # Calcular drawdown desde el máximo
        if hasattr(self, 'max_balance'):
            if current_balance > self.max_balance:
                self.max_balance = current_balance
            
            drawdown = (self.max_balance - current_balance) / self.max_balance
            return drawdown <= self.risk_limits.max_drawdown
        else:
            self.max_balance = current_balance
            return True
    
    def update_trade_stats(self, pnl: float):
        """Actualizar estadísticas de trading"""
        self.daily_stats['trades_count'] += 1
        self.daily_stats['total_pnl'] += pnl
        
        # Actualizar drawdown máximo
        if pnl < 0:
            self.daily_stats['max_drawdown'] = max(
                self.daily_stats['max_drawdown'], 
                abs(pnl)
            )
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Obtener estado actual del riesgo"""
        return {
            'daily_stats': self.daily_stats,
            'risk_limits': {
                'max_position_size': self.risk_limits.max_position_size,
                'max_daily_trades': self.risk_limits.max_daily_trades,
                'max_daily_loss': self.risk_limits.max_daily_loss,
                'max_drawdown': self.risk_limits.max_drawdown,
                'min_confidence': self.risk_limits.min_confidence
            },
            'market_conditions': {
                symbol: {
                    'volatility': conditions.volatility,
                    'volume_ratio': conditions.volume_ratio,
                    'trend_strength': conditions.trend_strength,
                    'market_regime': conditions.market_regime,
                    'is_suitable': conditions.is_suitable_for_trading
                }
                for symbol, conditions in self.market_conditions.items()
            }
        }
    
    def save_backup(self, file_path: str):
        """Guardar backup del estado de riesgo"""
        try:
            backup_data = {
                'timestamp': time.time(),
                'daily_stats': self.daily_stats,
                'position_history': self.position_history[-10:],  # Últimas 10 posiciones
                'market_conditions': {
                    symbol: {
                        'volatility': conditions.volatility,
                        'volume_ratio': conditions.volume_ratio,
                        'trend_strength': conditions.trend_strength,
                        'market_regime': conditions.market_regime
                    }
                    for symbol, conditions in self.market_conditions.items()
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Risk backup saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving risk backup: {e}")
    
    def load_backup(self, file_path: str):
        """Cargar backup del estado de riesgo"""
        try:
            if not Path(file_path).exists():
                logger.warning(f"Backup file not found: {file_path}")
                return
            
            with open(file_path, 'r') as f:
                backup_data = json.load(f)
            
            # Restaurar datos
            self.daily_stats = backup_data.get('daily_stats', self.daily_stats)
            self.position_history = backup_data.get('position_history', [])
            
            # Restaurar condiciones de mercado
            market_data = backup_data.get('market_conditions', {})
            for symbol, data in market_data.items():
                self.market_conditions[symbol] = MarketConditions(
                    volatility=data.get('volatility', 0.0),
                    volume_ratio=data.get('volume_ratio', 1.0),
                    trend_strength=data.get('trend_strength', 25.0),
                    market_regime=data.get('market_regime', 'unknown'),
                    is_suitable_for_trading=True
                )
            
            logger.info(f"Risk backup loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading risk backup: {e}")
