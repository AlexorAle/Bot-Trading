"""
Telegram Notifier - Integración con Telegram para alertas del bot de trading
"""

import logging
import requests
import time
from typing import Optional, Dict, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Notificador de alertas via Telegram"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bot_token = config.get('bot_token')
        self.chat_id = config.get('chat_id')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.enabled = bool(self.bot_token and self.chat_id)
        
        # Rate limiting
        self.last_message_time = 0
        self.min_interval = config.get('min_interval', 1)  # 1 segundo entre mensajes
        
        # Configuración de mensajes
        self.max_message_length = config.get('max_message_length', 4096)
        self.include_timestamp = config.get('include_timestamp', True)
        
        if self.enabled:
            logger.info(f"TelegramNotifier initialized - Chat ID: {self.chat_id}")
        else:
            logger.warning("TelegramNotifier disabled - Missing bot_token or chat_id")
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Enviar mensaje a Telegram"""
        if not self.enabled:
            logger.debug("Telegram notifier disabled, skipping message")
            return False
        
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_message_time < self.min_interval:
                time.sleep(self.min_interval - (current_time - self.last_message_time))
            
            # Truncar mensaje si es muy largo
            if len(message) > self.max_message_length:
                message = message[:self.max_message_length-3] + "..."
            
            # Preparar datos del mensaje
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            # Enviar mensaje
            response = requests.post(
                f"{self.base_url}/sendMessage",
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.last_message_time = time.time()
                logger.debug("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_alert(self, alert) -> bool:
        """Enviar alerta formateada a Telegram"""
        try:
            # Formatear mensaje para Telegram
            message = self._format_alert_message(alert)
            
            # Enviar mensaje
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending alert to Telegram: {e}")
            return False
    
    def _format_alert_message(self, alert) -> str:
        """Formatear alerta para Telegram"""
        # Usar el método to_telegram_message del alert
        base_message = alert.to_telegram_message()
        
        # Agregar información adicional si está disponible
        if alert.data:
            additional_info = []
            
            # Información específica por tipo de alerta
            if alert.alert_type.value == "signal_generated":
                if 'confidence' in alert.data:
                    confidence = alert.data['confidence']
                    if confidence > 0.8:
                        additional_info.append("🔥 Alta confianza")
                    elif confidence > 0.6:
                        additional_info.append("⚡ Confianza media")
            
            elif alert.alert_type.value == "order_executed":
                if 'balance' in alert.data:
                    balance = alert.data['balance']
                    additional_info.append(f"💰 Balance: ${balance:,.2f}")
            
            elif alert.alert_type.value == "position_closed":
                if 'pnl' in alert.data and 'pnl_pct' in alert.data:
                    pnl = alert.data['pnl']
                    pnl_pct = alert.data['pnl_pct']
                    if pnl > 0:
                        additional_info.append("🎉 Trade ganador!")
                    else:
                        additional_info.append("📉 Trade perdedor")
            
            elif alert.alert_type.value == "pnl_update":
                if 'total_equity' in alert.data:
                    equity = alert.data['total_equity']
                    additional_info.append(f"💎 Equity total: ${equity:,.2f}")
            
            # Agregar información adicional al mensaje
            if additional_info:
                base_message += "\n" + " | ".join(additional_info)
        
        return base_message
    
    def send_test_message(self) -> bool:
        """Enviar mensaje de prueba"""
        test_message = """🤖 <b>Bot de Trading - Mensaje de Prueba</b>

✅ Conexión con Telegram establecida correctamente
📊 Sistema de alertas funcionando
🚀 Bot listo para operar

<i>Este es un mensaje de prueba del sistema de alertas.</i>"""
        
        return self.send_message(test_message)
    
    def send_startup_message(self, bot_info: str) -> bool:
        """Enviar mensaje de inicio del bot"""
        startup_message = f"""🚀 <b>Bot de Trading Iniciado</b>

{bot_info}

📈 <b>Estrategias activas:</b>
• VolatilityBreakoutStrategy
• RSIEMAMomentumStrategy  
• BollingerReversionStrategy

🔔 <b>Alertas configuradas:</b>
• Señales generadas/ejecutadas
• Órdenes y trades
• Performance y PnL
• Errores del sistema

<i>El bot está monitoreando el mercado y generará alertas automáticamente.</i>"""
        
        return self.send_message(startup_message)
    
    def send_shutdown_message(self, session_stats: str = None) -> bool:
        """Enviar mensaje de cierre del bot"""
        shutdown_message = """⏹️ <b>Bot de Trading Detenido</b>

El bot ha sido detenido correctamente."""
        
        if session_stats:
            shutdown_message += f"\n\n📊 <b>Estadísticas de la sesión:</b>\n{session_stats}"
        
        shutdown_message += "\n\n<i>Gracias por usar el bot de trading.</i>"
        
        return self.send_message(shutdown_message)
    
    def send_error_message(self, error_type: str, error_message: str, details: str = None) -> bool:
        """Enviar mensaje de error"""
        error_emoji = "🚨" if "critical" in error_type.lower() else "⚠️"
        
        error_msg = f"""{error_emoji} <b>Error del Sistema</b>

<b>Tipo:</b> {error_type}
<b>Mensaje:</b> {error_message}"""
        
        if details:
            error_msg += f"\n<b>Detalles:</b> {details}"
        
        error_msg += "\n\n<i>El bot continuará operando si es posible.</i>"
        
        return self.send_message(error_msg)
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Obtener información del bot de Telegram"""
        if not self.enabled:
            return {}
        
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                return response.json().get('result', {})
            else:
                logger.error(f"Failed to get bot info: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Probar conexión con Telegram"""
        if not self.enabled:
            logger.warning("Telegram notifier disabled")
            return False
        
        try:
            # Probar con getMe
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json().get('result', {})
                logger.info(f"Telegram connection OK - Bot: @{bot_info.get('username', 'unknown')}")
                return True
            else:
                logger.error(f"Telegram connection failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Telegram connection error: {e}")
            return False

class TelegramConfig:
    """Utilidad para configurar Telegram"""
    
    @staticmethod
    def create_config_template() -> Dict[str, Any]:
        """Crear plantilla de configuración"""
        return {
            "telegram": {
                "enabled": True,
                "bot_token": "YOUR_BOT_TOKEN_HERE",
                "chat_id": "YOUR_CHAT_ID_HERE",
                "min_interval": 1,
                "max_message_length": 4096,
                "include_timestamp": True
            }
        }
    
    @staticmethod
    def save_config(config: Dict[str, Any], file_path: str):
        """Guardar configuración en archivo"""
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Telegram config saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving Telegram config: {e}")
    
    @staticmethod
    def load_config(file_path: str) -> Dict[str, Any]:
        """Cargar configuración desde archivo"""
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Telegram config loaded from {file_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading Telegram config: {e}")
            return {}
