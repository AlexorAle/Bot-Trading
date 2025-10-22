"""
Alert Manager - Sistema de gestión de alertas para el bot de trading
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from enum import Enum

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Tipos de alertas disponibles"""
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_EXECUTED = "signal_executed"
    SIGNAL_REJECTED = "signal_rejected"
    ORDER_EXECUTED = "order_executed"
    POSITION_CLOSED = "position_closed"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    PNL_UPDATE = "pnl_update"
    BALANCE_UPDATE = "balance_update"
    SYSTEM_ERROR = "system_error"
    CONNECTION_ERROR = "connection_error"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"

class AlertPriority(Enum):
    """Prioridades de alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Estructura de una alerta"""
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    timestamp: float
    data: Dict[str, Any] = None
    symbol: str = None
    strategy: str = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'alert_type': self.alert_type.value,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp,
            'data': self.data or {},
            'symbol': self.symbol,
            'strategy': self.strategy
        }
    
    def to_telegram_message(self) -> str:
        """Format message for Telegram"""
        # Emojis por tipo de alerta
        emoji_map = {
            AlertType.SIGNAL_GENERATED: "🎯",
            AlertType.SIGNAL_EXECUTED: "✅",
            AlertType.SIGNAL_REJECTED: "⚠️",
            AlertType.ORDER_EXECUTED: "🟢",
            AlertType.POSITION_CLOSED: "🔴",
            AlertType.STOP_LOSS: "🛑",
            AlertType.TAKE_PROFIT: "🎉",
            AlertType.PNL_UPDATE: "📊",
            AlertType.BALANCE_UPDATE: "💰",
            AlertType.SYSTEM_ERROR: "❌",
            AlertType.CONNECTION_ERROR: "🔌",
            AlertType.BOT_STARTED: "🚀",
            AlertType.BOT_STOPPED: "⏹️"
        }
        
        # Emojis por prioridad
        priority_emoji = {
            AlertPriority.LOW: "🔵",
            AlertPriority.MEDIUM: "🟡",
            AlertPriority.HIGH: "🟠",
            AlertPriority.CRITICAL: "🔴"
        }
        
        emoji = emoji_map.get(self.alert_type, "📢")
        priority_icon = priority_emoji.get(self.priority, "🔵")
        
        # Formatear timestamp
        dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        time_str = dt.strftime("%H:%M:%S UTC")
        
        # Construir mensaje
        message = f"{emoji} {self.title}\n"
        message += f"{priority_icon} {self.message}\n"
        
        if self.symbol:
            message += f"📈 {self.symbol}"
            if self.strategy:
                message += f" | {self.strategy}"
            message += "\n"
        
        message += f"🕐 {time_str}"
        
        return message

class AlertManager:
    """Gestor principal de alertas"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.notifiers: List[Callable] = []
        self.alert_history: List[Alert] = []
        self.rate_limits: Dict[str, float] = {}
        self.max_history = config.get('max_history', 1000)
        
        # Configuración de rate limiting
        self.rate_limit_config = config.get('rate_limits', {})
        
        logger.info("AlertManager initialized")
        
        # Initialize Telegram notifier if configured
        self.telegram_notifier = None
        if config.get('telegram', {}).get('enabled', False):
            try:
                from telegram_notifier import TelegramNotifier
                self.telegram_notifier = TelegramNotifier(config.get('telegram', {}))
                logger.info("Telegram notifier initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram notifier: {e}")
    
    def send_telegram_message(self, message: str) -> bool:
        """Send a direct message to Telegram"""
        if self.telegram_notifier:
            try:
                return self.telegram_notifier.send_message(message)
            except Exception as e:
                logger.error(f"Error sending Telegram message: {e}")
                return False
        return False
    
    def add_notifier(self, notifier: Callable):
        """Agregar un notificador (ej: Telegram)"""
        self.notifiers.append(notifier)
        logger.info(f"Notifier added: {notifier.__name__}")
    
    def send_alert(self, alert: Alert):
        """Enviar una alerta"""
        try:
            # Verificar rate limiting
            if self._is_rate_limited(alert):
                logger.debug(f"Alert rate limited: {alert.alert_type.value}")
                return
            
            # Agregar a historial
            self.alert_history.append(alert)
            if len(self.alert_history) > self.max_history:
                self.alert_history.pop(0)
            
            # Enviar a todos los notificadores
            for notifier in self.notifiers:
                try:
                    notifier(alert)
                except Exception as e:
                    logger.error(f"Error in notifier {notifier.__name__}: {e}")
            
            logger.info(f"Alert sent: {alert.alert_type.value} - {alert.title}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def _is_rate_limited(self, alert: Alert) -> bool:
        """Verificar si la alerta está rate limited"""
        alert_key = f"{alert.alert_type.value}_{alert.symbol or 'global'}"
        
        if alert_key not in self.rate_limits:
            self.rate_limits[alert_key] = 0
        
        current_time = time.time()
        last_sent = self.rate_limits[alert_key]
        
        # Obtener límite de tiempo para este tipo de alerta
        rate_limit_seconds = self.rate_limit_config.get(alert.alert_type.value, 60)
        
        if current_time - last_sent < rate_limit_seconds:
            return True
        
        self.rate_limits[alert_key] = current_time
        return False
    
    # Métodos de conveniencia para diferentes tipos de alertas
    
    def signal_generated(self, symbol: str, signal_type: str, price: float, 
                        confidence: float, strategy: str):
        """Alerta de señal generada"""
        alert = Alert(
            alert_type=AlertType.SIGNAL_GENERATED,
            priority=AlertPriority.HIGH,
            title="Nueva Señal Generada",
            message=f"{signal_type} @ ${price:,.2f} (confidence: {confidence:.1%})",
            timestamp=time.time(),
            symbol=symbol,
            strategy=strategy,
            data={
                'signal_type': signal_type,
                'price': price,
                'confidence': confidence
            }
        )
        self.send_alert(alert)
    
    def signal_executed(self, symbol: str, signal_type: str, price: float, 
                       qty: float, strategy: str):
        """Alerta de señal ejecutada"""
        alert = Alert(
            alert_type=AlertType.SIGNAL_EXECUTED,
            priority=AlertPriority.HIGH,
            title="Señal Ejecutada",
            message=f"{signal_type} {qty:.3f} {symbol.replace('USDT', '')} @ ${price:,.2f}",
            timestamp=time.time(),
            symbol=symbol,
            strategy=strategy,
            data={
                'signal_type': signal_type,
                'price': price,
                'qty': qty
            }
        )
        self.send_alert(alert)
    
    def signal_rejected(self, symbol: str, reason: str, confidence: float = None):
        """Alerta de señal rechazada"""
        message = f"Señal rechazada: {reason}"
        if confidence:
            message += f" (confidence: {confidence:.1%})"
        
        alert = Alert(
            alert_type=AlertType.SIGNAL_REJECTED,
            priority=AlertPriority.MEDIUM,
            title="Señal Rechazada",
            message=message,
            timestamp=time.time(),
            symbol=symbol,
            data={'reason': reason, 'confidence': confidence}
        )
        self.send_alert(alert)
    
    def order_executed(self, symbol: str, side: str, qty: float, price: float, 
                      balance: float):
        """Alerta de orden ejecutada"""
        side_emoji = "🟢" if side.lower() == "buy" else "🔴"
        alert = Alert(
            alert_type=AlertType.ORDER_EXECUTED,
            priority=AlertPriority.HIGH,
            title="Orden Ejecutada",
            message=f"{side_emoji} {side.upper()}: {qty:.3f} @ ${price:,.2f} | Balance: ${balance:,.2f}",
            timestamp=time.time(),
            symbol=symbol,
            data={
                'side': side,
                'qty': qty,
                'price': price,
                'balance': balance
            }
        )
        self.send_alert(alert)
    
    def position_closed(self, symbol: str, pnl: float, pnl_pct: float, 
                       total_balance: float):
        """Alerta de posición cerrada"""
        pnl_emoji = "🎉" if pnl >= 0 else "😞"
        alert = Alert(
            alert_type=AlertType.POSITION_CLOSED,
            priority=AlertPriority.HIGH,
            title="Posición Cerrada",
            message=f"{pnl_emoji} PnL: ${pnl:+,.2f} ({pnl_pct:+.2%}) | Balance: ${total_balance:,.2f}",
            timestamp=time.time(),
            symbol=symbol,
            data={
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'total_balance': total_balance
            }
        )
        self.send_alert(alert)
    
    def stop_loss_triggered(self, symbol: str, price: float, pnl: float):
        """Alerta de stop loss activado"""
        alert = Alert(
            alert_type=AlertType.STOP_LOSS,
            priority=AlertPriority.CRITICAL,
            title="Stop Loss Activado",
            message=f"🛑 {symbol} @ ${price:,.2f} | Pérdida: ${pnl:,.2f}",
            timestamp=time.time(),
            symbol=symbol,
            data={'price': price, 'pnl': pnl}
        )
        self.send_alert(alert)
    
    def pnl_update(self, symbol: str, pnl: float, pnl_pct: float, 
                   total_equity: float):
        """Alerta de actualización de PnL"""
        if abs(pnl_pct) < 0.01:  # Solo alertar cambios > 1%
            return
        
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        alert = Alert(
            alert_type=AlertType.PNL_UPDATE,
            priority=AlertPriority.MEDIUM,
            title="Actualización PnL",
            message=f"{pnl_emoji} PnL: ${pnl:+,.2f} ({pnl_pct:+.2%}) | Equity: ${total_equity:,.2f}",
            timestamp=time.time(),
            symbol=symbol,
            data={
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'total_equity': total_equity
            }
        )
        self.send_alert(alert)
    
    def system_error(self, error_type: str, message: str, details: str = None):
        """Alerta de error del sistema"""
        alert = Alert(
            alert_type=AlertType.SYSTEM_ERROR,
            priority=AlertPriority.CRITICAL,
            title=f"Error del Sistema: {error_type}",
            message=message,
            timestamp=time.time(),
            data={'error_type': error_type, 'details': details}
        )
        self.send_alert(alert)
    
    def connection_error(self, service: str, message: str):
        """Alerta de error de conexión"""
        alert = Alert(
            alert_type=AlertType.CONNECTION_ERROR,
            priority=AlertPriority.HIGH,
            title=f"Error de Conexión: {service}",
            message=message,
            timestamp=time.time(),
            data={'service': service}
        )
        self.send_alert(alert)
    
    def bot_started(self, config_info: str = None):
        """Alerta de bot iniciado"""
        message = "Bot de trading iniciado correctamente"
        if config_info:
            message += f" | {config_info}"
        
        alert = Alert(
            alert_type=AlertType.BOT_STARTED,
            priority=AlertPriority.MEDIUM,
            title="Bot Iniciado",
            message=message,
            timestamp=time.time(),
            data={'config_info': config_info}
        )
        self.send_alert(alert)
    
    def bot_stopped(self, reason: str = None):
        """Alerta de bot detenido"""
        message = "Bot de trading detenido"
        if reason:
            message += f" | Razón: {reason}"
        
        alert = Alert(
            alert_type=AlertType.BOT_STOPPED,
            priority=AlertPriority.HIGH,
            title="Bot Detenido",
            message=message,
            timestamp=time.time(),
            data={'reason': reason}
        )
        self.send_alert(alert)
    
    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """Obtener historial de alertas"""
        recent_alerts = self.alert_history[-limit:] if self.alert_history else []
        return [alert.to_dict() for alert in recent_alerts]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de alertas"""
        if not self.alert_history:
            return {}
        
        stats = {}
        for alert in self.alert_history:
            alert_type = alert.alert_type.value
            stats[alert_type] = stats.get(alert_type, 0) + 1
        
        return {
            'total_alerts': len(self.alert_history),
            'alerts_by_type': stats,
            'last_alert': self.alert_history[-1].to_dict() if self.alert_history else None
        }
