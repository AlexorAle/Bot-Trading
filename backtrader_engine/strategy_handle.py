#!/usr/bin/env python3
"""
StrategyHandle Wrapper

Wrapper para estrategias de trading que permite:
- Activación/desactivación controlada
- Sincronización de pesos con Risk Parity
- Gestión de órdenes abiertas y posiciones
- Logging detallado de estado y acciones

Métodos clave:
- enable(): Activar estrategia
- disable_and_flatten(): Desactivar y cerrar posiciones
- sync_to_target_value(target_value): Sincronizar con peso objetivo
"""

import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging


@dataclass
class StrategyState:
    """Estado actual de una estrategia"""
    enabled: bool
    target_value: float
    current_value: float
    position_size: float
    open_orders: int
    last_action: str
    last_timestamp: datetime
    equity_curve: List[float]
    actions_log: List[Dict[str, Any]]


class StrategyHandle:
    """
    Wrapper para estrategias de trading con control granular
    
    Permite:
    - Activación/desactivación controlada
    - Sincronización de pesos con Risk Parity
    - Gestión de órdenes abiertas
    - Logging detallado
    """
    
    def __init__(self, 
                 strategy_name: str,
                 strategy_class: type,
                 cerebro: bt.Cerebro,
                 config: Dict[str, Any],
                 logger: Optional[logging.Logger] = None,
                 hybrid_logger=None):
        """
        Inicializar StrategyHandle
        
        Args:
            strategy_name: Nombre de la estrategia
            strategy_class: Clase de la estrategia (ej: EMABreakoutStrategy)
            cerebro: Instancia de Cerebro de Backtrader
            config: Configuración de la estrategia
            logger: Logger opcional
        """
        self.strategy_name = strategy_name
        self.strategy_class = strategy_class
        self.cerebro = cerebro
        self.config = config.copy()
        self.logger = logger or self._setup_logger()
        self.hybrid_logger = hybrid_logger
        
        # Estado de la estrategia
        self.state = StrategyState(
            enabled=False,
            target_value=0.0,
            current_value=0.0,
            position_size=0.0,
            open_orders=0,
            last_action="INIT",
            last_timestamp=datetime.now(),
            equity_curve=[],
            actions_log=[]
        )
        
        # Referencias internas
        self.strategy_instance = None
        self.strategy_idx = None
        
        # Callbacks
        self.on_enable_callback = None
        self.on_disable_callback = None
        self.on_sync_callback = None
        
        self.logger.info(f"[STRATEGY HANDLE] Initialized: {strategy_name}")

    def _setup_logger(self) -> logging.Logger:
        """Configurar logger para la estrategia"""
        logger = logging.getLogger(f"StrategyHandle.{self.strategy_name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.strategy_name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def enable(self) -> bool:
        """
        Activar la estrategia
        
        Returns:
            True si se activó correctamente, False en caso contrario
        """
        try:
            if self.state.enabled:
                self.logger.warning(f"Strategy {self.strategy_name} is already enabled")
                return True
            
            # Agregar estrategia al cerebro
            self.strategy_idx = self.cerebro.addstrategy(
                self.strategy_class,
                **self._get_strategy_params()
            )
            
            self.state.enabled = True
            self.state.last_action = "ENABLED"
            self.state.last_timestamp = datetime.now()
            
            # Log acción
            self._log_action("ENABLED", {
                "strategy_idx": self.strategy_idx,
                "params": self._get_strategy_params()
            })
            
            # Callback
            if self.on_enable_callback:
                self.on_enable_callback(self)
            
            # Hybrid logging
            if self.hybrid_logger:
                from hybrid_logger import StrategyHandleLogger
                handle_logger = StrategyHandleLogger(self.hybrid_logger, self.strategy_name)
                handle_logger.log_enable(
                    timestamp=datetime.now(),
                    equity=self._get_current_value(),
                    strategy_idx=self.strategy_idx,
                    params=self._get_strategy_params()
                )
            
            self.logger.info(f"✅ Strategy {self.strategy_name} ENABLED")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error enabling strategy {self.strategy_name}: {e}")
            return False

    def disable_and_flatten(self) -> bool:
        """
        Desactivar estrategia y cerrar todas las posiciones
        
        Returns:
            True si se desactivó correctamente, False en caso contrario
        """
        try:
            if not self.state.enabled:
                self.logger.warning(f"Strategy {self.strategy_name} is already disabled")
                return True
            
            # Cerrar posiciones abiertas
            self._close_all_positions()
            
            # Remover estrategia del cerebro
            if self.strategy_idx is not None:
                # Nota: Backtrader no permite remover estrategias dinámicamente
                # En su lugar, marcamos como deshabilitada
                self.state.enabled = False
                self.state.last_action = "DISABLED"
                self.state.last_timestamp = datetime.now()
                
                # Log acción
                self._log_action("DISABLED", {
                    "strategy_idx": self.strategy_idx,
                    "positions_closed": True
                })
                
                # Callback
                if self.on_disable_callback:
                    self.on_disable_callback(self)
                
                # Hybrid logging
                if self.hybrid_logger:
                    from hybrid_logger import StrategyHandleLogger
                    handle_logger = StrategyHandleLogger(self.hybrid_logger, self.strategy_name)
                    handle_logger.log_disable(
                        timestamp=datetime.now(),
                        equity=self._get_current_value(),
                        strategy_idx=self.strategy_idx,
                        positions_closed=True
                    )
                
                self.logger.info(f"⏸️  Strategy {self.strategy_name} DISABLED")
                return True
            else:
                self.logger.warning(f"No strategy index found for {self.strategy_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error disabling strategy {self.strategy_name}: {e}")
            return False

    def sync_to_target_value(self, target_value: float) -> bool:
        """
        Sincronizar estrategia con valor objetivo
        
        Args:
            target_value: Valor objetivo en dólares
            
        Returns:
            True si se sincronizó correctamente, False en caso contrario
        """
        try:
            if not self.state.enabled:
                self.logger.warning(f"Cannot sync disabled strategy {self.strategy_name}")
                return False
            
            current_value = self._get_current_value()
            self.state.current_value = current_value
            self.state.target_value = target_value
            
            # Calcular diferencia
            value_diff = target_value - current_value
            position_diff = value_diff / self._get_current_price() if self._get_current_price() > 0 else 0
            
            # Determinar acción
            if abs(value_diff) < 100:  # Umbral mínimo de $100
                action = "NO_ACTION"
                self.logger.debug(f"Value difference too small: ${value_diff:.2f}")
            elif value_diff > 0:
                action = "INCREASE_POSITION"
                self._adjust_position(position_diff)
            else:
                action = "DECREASE_POSITION"
                self._adjust_position(position_diff)
            
            # Actualizar estado
            self.state.last_action = action
            self.state.last_timestamp = datetime.now()
            
            # Log acción
            self._log_action("SYNC", {
                "target_value": target_value,
                "current_value": current_value,
                "value_diff": value_diff,
                "position_diff": position_diff,
                "action": action
            })
            
            # Callback
            if self.on_sync_callback:
                self.on_sync_callback(self, target_value, current_value)
            
            # Hybrid logging
            if self.hybrid_logger:
                from hybrid_logger import StrategyHandleLogger
                handle_logger = StrategyHandleLogger(self.hybrid_logger, self.strategy_name)
                handle_logger.log_sync(
                    timestamp=datetime.now(),
                    target_value=target_value,
                    current_value=current_value,
                    delta=value_diff,
                    action=action,
                    position_diff=position_diff
                )
            
            self.logger.info(f"🔄 Strategy {self.strategy_name} synced: ${current_value:.2f} → ${target_value:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing strategy {self.strategy_name}: {e}")
            return False

    def _get_strategy_params(self) -> Dict[str, Any]:
        """Obtener parámetros de la estrategia desde la configuración"""
        # Filtrar parámetros específicos de la estrategia
        strategy_params = {}
        
        # Parámetros comunes
        common_params = [
            'position_size', 'take_profit', 'stop_loss', 'trailing_stop',
            'ema_fast', 'ema_slow', 'rsi_period', 'bb_period', 'std_dev',
            'volume_period', 'volume_spike_multiplier', 'spread_threshold',
            'adx_period', 'adx_threshold', 'lookback', 'atr_period', 'multiplier'
        ]
        
        for param in common_params:
            if param in self.config:
                strategy_params[param] = self.config[param]
        
        return strategy_params

    def _get_current_value(self) -> float:
        """Obtener valor actual de la estrategia"""
        try:
            # Obtener valor del broker
            return self.cerebro.broker.getvalue()
        except Exception as e:
            self.logger.error(f"Error getting current value: {e}")
            return 0.0

    def _get_current_price(self) -> float:
        """Obtener precio actual del instrumento"""
        try:
            # Obtener precio del último dato
            if hasattr(self.cerebro, 'datas') and len(self.cerebro.datas) > 0:
                return self.cerebro.datas[0].close[0]
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting current price: {e}")
            return 0.0

    def _close_all_positions(self) -> None:
        """Cerrar todas las posiciones abiertas"""
        try:
            # Obtener posición actual
            position = self.cerebro.broker.getposition()
            
            if position.size != 0:
                # Cerrar posición
                self.cerebro.broker.close()
                self.logger.info(f"Closed position: {position.size} units")
            
            # Cancelar órdenes pendientes
            self.cerebro.broker.cancel()
            self.state.open_orders = 0
            
        except Exception as e:
            self.logger.error(f"Error closing positions: {e}")

    def _adjust_position(self, position_diff: float) -> None:
        """Ajustar posición según diferencia calculada"""
        try:
            if abs(position_diff) < 0.001:  # Umbral mínimo
                return
            
            if position_diff > 0:
                # Aumentar posición (comprar)
                self.cerebro.broker.buy(size=abs(position_diff))
                self.logger.info(f"Position increased by {position_diff:.4f} units")
            else:
                # Disminuir posición (vender)
                self.cerebro.broker.sell(size=abs(position_diff))
                self.logger.info(f"Position decreased by {abs(position_diff):.4f} units")
                
        except Exception as e:
            self.logger.error(f"Error adjusting position: {e}")

    def _log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Registrar acción en el log"""
        log_entry = {
            "timestamp": datetime.now(),
            "action": action,
            "details": details,
            "state": {
                "enabled": self.state.enabled,
                "target_value": self.state.target_value,
                "current_value": self.state.current_value,
                "position_size": self.state.position_size
            }
        }
        
        self.state.actions_log.append(log_entry)
        
        # Mantener solo los últimos 100 logs
        if len(self.state.actions_log) > 100:
            self.state.actions_log = self.state.actions_log[-100:]

    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual de la estrategia"""
        return {
            "strategy_name": self.strategy_name,
            "enabled": self.state.enabled,
            "target_value": self.state.target_value,
            "current_value": self.state.current_value,
            "position_size": self.state.position_size,
            "open_orders": self.state.open_orders,
            "last_action": self.state.last_action,
            "last_timestamp": self.state.last_timestamp.isoformat(),
            "actions_count": len(self.state.actions_log)
        }

    def get_actions_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener log de acciones recientes"""
        return self.state.actions_log[-limit:] if self.state.actions_log else []

    def set_callbacks(self, 
                     on_enable: Optional[Callable] = None,
                     on_disable: Optional[Callable] = None,
                     on_sync: Optional[Callable] = None) -> None:
        """Configurar callbacks para eventos"""
        self.on_enable_callback = on_enable
        self.on_disable_callback = on_disable
        self.on_sync_callback = on_sync

    def update_equity_curve(self, value: float) -> None:
        """Actualizar curva de equity"""
        self.state.equity_curve.append(value)
        
        # Mantener solo los últimos 1000 puntos
        if len(self.state.equity_curve) > 1000:
            self.state.equity_curve = self.state.equity_curve[-1000:]

    def get_equity_curve(self) -> List[float]:
        """Obtener curva de equity"""
        return self.state.equity_curve.copy()

    def reset(self) -> None:
        """Resetear estado de la estrategia"""
        self.state = StrategyState(
            enabled=False,
            target_value=0.0,
            current_value=0.0,
            position_size=0.0,
            open_orders=0,
            last_action="RESET",
            last_timestamp=datetime.now(),
            equity_curve=[],
            actions_log=[]
        )
        
        self.strategy_instance = None
        self.strategy_idx = None
        
        self.logger.info(f"🔄 Strategy {self.strategy_name} RESET")


class StrategyHandleManager:
    """
    Manager para múltiples StrategyHandles
    
    Permite gestionar un conjunto de estrategias de forma coordinada
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.handles: Dict[str, StrategyHandle] = {}
        self.logger = logger or self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Configurar logger para el manager"""
        logger = logging.getLogger("StrategyHandleManager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - StrategyHandleManager - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def add_strategy(self, handle: StrategyHandle) -> None:
        """Agregar estrategia al manager"""
        self.handles[handle.strategy_name] = handle
        self.logger.info(f"Added strategy: {handle.strategy_name}")

    def enable_strategy(self, strategy_name: str) -> bool:
        """Habilitar estrategia específica"""
        if strategy_name in self.handles:
            return self.handles[strategy_name].enable()
        else:
            self.logger.error(f"Strategy not found: {strategy_name}")
            return False

    def disable_strategy(self, strategy_name: str) -> bool:
        """Deshabilitar estrategia específica"""
        if strategy_name in self.handles:
            return self.handles[strategy_name].disable_and_flatten()
        else:
            self.logger.error(f"Strategy not found: {strategy_name}")
            return False

    def sync_strategies(self, target_values: Dict[str, float]) -> Dict[str, bool]:
        """Sincronizar múltiples estrategias con valores objetivo"""
        results = {}
        
        for strategy_name, target_value in target_values.items():
            if strategy_name in self.handles:
                results[strategy_name] = self.handles[strategy_name].sync_to_target_value(target_value)
            else:
                self.logger.error(f"Strategy not found: {strategy_name}")
                results[strategy_name] = False
        
        return results

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtener estado de todas las estrategias"""
        return {name: handle.get_status() for name, handle in self.handles.items()}

    def get_enabled_strategies(self) -> List[str]:
        """Obtener lista de estrategias habilitadas"""
        return [name for name, handle in self.handles.items() if handle.state.enabled]

    def disable_all(self) -> Dict[str, bool]:
        """Deshabilitar todas las estrategias"""
        results = {}
        for name, handle in self.handles.items():
            results[name] = handle.disable_and_flatten()
        return results

    def reset_all(self) -> None:
        """Resetear todas las estrategias"""
        for handle in self.handles.values():
            handle.reset()
        self.logger.info("All strategies reset")


def test_strategy_handle():
    """Función de prueba para StrategyHandle"""
    print("🧪 Testing StrategyHandle...")
    
    # Crear cerebro de prueba
    cerebro = bt.Cerebro()
    
    # Crear datos de prueba
    dates = pd.date_range('2024-01-01', '2024-01-10', freq='D')
    prices = [100 + i for i in range(len(dates))]
    
    test_data = pd.DataFrame({
        'open': prices,
        'high': [p * 1.01 for p in prices],
        'low': [p * 0.99 for p in prices],
        'close': prices,
        'volume': [1000] * len(prices)
    }, index=dates)
    
    # Agregar datos al cerebro
    data_feed = bt.feeds.PandasData(dataname=test_data)
    cerebro.adddata(data_feed)
    
    # Configuración de prueba
    config = {
        'position_size': 0.1,
        'take_profit': 0.02,
        'stop_loss': 0.01
    }
    
    # Crear StrategyHandle de prueba
    handle = StrategyHandle(
        strategy_name="TestStrategy",
        strategy_class=bt.Strategy,  # Clase base para prueba
        cerebro=cerebro,
        config=config
    )
    
    # Probar métodos
    print(f"Initial status: {handle.get_status()}")
    
    # Habilitar estrategia
    handle.enable()
    print(f"After enable: {handle.get_status()}")
    
    # Sincronizar con valor objetivo
    handle.sync_to_target_value(1000.0)
    print(f"After sync: {handle.get_status()}")
    
    # Deshabilitar estrategia
    handle.disable_and_flatten()
    print(f"After disable: {handle.get_status()}")
    
    print("✅ StrategyHandle test completed")


if __name__ == "__main__":
    test_strategy_handle()
