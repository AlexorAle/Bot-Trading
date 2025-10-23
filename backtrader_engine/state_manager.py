"""
State Manager - Persistencia de estado del bot para recovery
"""

import json
import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import threading
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class BotState:
    """Estado completo del bot"""
    # Trading state
    balance: float = 10000.0
    total_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # Positions
    positions: Dict[str, Dict[str, Any]] = None
    
    # Orders
    pending_orders: Dict[str, Dict[str, Any]] = None
    
    # Bot metadata
    start_time: Optional[str] = None
    last_update: Optional[str] = None
    signals_generated: int = 0
    last_signal_time: Optional[str] = None
    
    # System state
    websocket_connected: bool = False
    last_heartbeat: Optional[str] = None
    
    def __post_init__(self):
        if self.positions is None:
            self.positions = {}
        if self.pending_orders is None:
            self.pending_orders = {}

class StateManager:
    """Gestor de persistencia de estado del bot"""
    
    def __init__(self, state_file: str = "bot_state.json", backup_dir: str = "state_backups"):
        self.state_file = Path(state_file)
        self.backup_dir = Path(backup_dir)
        self.lock = threading.Lock()
        
        # Crear directorio de backups
        self.backup_dir.mkdir(exist_ok=True)
        
        # Estado actual
        self.current_state = BotState()
        self.last_save_time = 0
        self.auto_save_interval = 30  # segundos
        
        logger.info(f"StateManager initialized - State file: {self.state_file}")
    
    def load_state(self) -> Optional[BotState]:
        """Cargar estado desde archivo"""
        try:
            if not self.state_file.exists():
                logger.info("No existing state file found, starting fresh")
                return BotState()
            
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            
            # Convertir dict a BotState
            state = BotState(**data)
            logger.info(f"State loaded successfully - Balance: ${state.balance:.2f}, Trades: {state.total_trades}")
            return state
            
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return BotState()
    
    def save_state(self, state: BotState = None, force: bool = False) -> bool:
        """Guardar estado a archivo"""
        try:
            with self.lock:
                current_time = time.time()
                
                # Auto-save solo si ha pasado el intervalo
                if not force and (current_time - self.last_save_time) < self.auto_save_interval:
                    return True
                
                state_to_save = state or self.current_state
                state_to_save.last_update = datetime.now(timezone.utc).isoformat()
                
                # Crear backup antes de sobrescribir
                if self.state_file.exists():
                    self._create_backup()
                
                # Guardar estado
                with open(self.state_file, 'w') as f:
                    json.dump(asdict(state_to_save), f, indent=2)
                
                self.last_save_time = current_time
                logger.debug(f"State saved - Balance: ${state_to_save.balance:.2f}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            return False
    
    def _create_backup(self):
        """Crear backup del estado actual"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"bot_state_backup_{timestamp}.json"
            
            # Copiar archivo actual a backup
            import shutil
            shutil.copy2(self.state_file, backup_file)
            
            # Limpiar backups antiguos (mantener solo los últimos 10)
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Limpiar backups antiguos"""
        try:
            backup_files = sorted(self.backup_dir.glob("bot_state_backup_*.json"))
            if len(backup_files) > keep_count:
                for old_backup in backup_files[:-keep_count]:
                    old_backup.unlink()
                    logger.debug(f"Removed old backup: {old_backup.name}")
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
    
    def update_balance(self, new_balance: float):
        """Actualizar balance"""
        self.current_state.balance = new_balance
        self.save_state()
    
    def add_trade(self, pnl: float):
        """Agregar trade al historial"""
        self.current_state.total_trades += 1
        self.current_state.total_pnl += pnl
        
        if pnl > 0:
            self.current_state.winning_trades += 1
        else:
            self.current_state.losing_trades += 1
        
        self.save_state()
    
    def update_position(self, symbol: str, position_data: Dict[str, Any]):
        """Actualizar posición"""
        self.current_state.positions[symbol] = position_data
        self.save_state()
    
    def remove_position(self, symbol: str):
        """Remover posición"""
        if symbol in self.current_state.positions:
            del self.current_state.positions[symbol]
            self.save_state()
    
    def add_pending_order(self, order_id: str, order_data: Dict[str, Any]):
        """Agregar orden pendiente"""
        self.current_state.pending_orders[order_id] = order_data
        self.save_state()
    
    def remove_pending_order(self, order_id: str):
        """Remover orden pendiente"""
        if order_id in self.current_state.pending_orders:
            del self.current_state.pending_orders[order_id]
            self.save_state()
    
    def update_signal_count(self):
        """Actualizar contador de señales"""
        self.current_state.signals_generated += 1
        self.current_state.last_signal_time = datetime.now(timezone.utc).isoformat()
        self.save_state()
    
    def set_websocket_status(self, connected: bool):
        """Actualizar estado de WebSocket"""
        self.current_state.websocket_connected = connected
        self.current_state.last_heartbeat = datetime.now(timezone.utc).isoformat()
        self.save_state()
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Obtener resumen del estado"""
        state = self.current_state
        return {
            'balance': state.balance,
            'total_pnl': state.total_pnl,
            'total_trades': state.total_trades,
            'win_rate': (state.winning_trades / state.total_trades * 100) if state.total_trades > 0 else 0,
            'active_positions': len(state.positions),
            'pending_orders': len(state.pending_orders),
            'signals_generated': state.signals_generated,
            'websocket_connected': state.websocket_connected,
            'last_update': state.last_update
        }
    
    def start_auto_save(self):
        """Iniciar auto-save en background"""
        def auto_save_loop():
            while True:
                time.sleep(self.auto_save_interval)
                self.save_state()
        
        thread = threading.Thread(target=auto_save_loop, daemon=True)
        thread.start()
        logger.info("Auto-save started")
    
    def emergency_save(self):
        """Guardado de emergencia (llamar antes de crash)"""
        try:
            self.save_state(force=True)
            logger.info("Emergency state save completed")
        except Exception as e:
            logger.error(f"Emergency save failed: {e}")
