#!/usr/bin/env python3
"""
Script para iniciar paper trading de 72 horas con 5 estrategias
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
import time
from datetime import datetime, timezone

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from paper_trading_main import PaperTradingBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/72h_trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Trading72hBot:
    """Bot de trading para 72 horas"""
    
    def __init__(self):
        self.bot = None
        self.start_time = None
        self.running = False
        
    async def start(self):
        """Iniciar bot de 72 horas"""
        try:
            logger.info("🚀 Iniciando bot de trading de 72 horas...")
            logger.info("📊 Configuración: 5 estrategias, Bybit X, Paper Trading")
            logger.info("🔔 Alertas: Telegram habilitadas")
            logger.info("📈 Monitoreo: Grafana + Prometheus")
            
            self.start_time = time.time()
            self.running = True
            
            # Initialize bot with 72h configuration
            self.bot = PaperTradingBot('configs/bybit_x_config.json')
            
            # Start the bot
            await self.bot.start()
            
        except Exception as e:
            logger.error(f"Error starting 72h bot: {e}")
            raise
    
    async def stop(self):
        """Detener bot"""
        logger.info("🛑 Deteniendo bot de 72 horas...")
        self.running = False
        
        if self.bot:
            await self.bot.stop()
        
        # Calculate runtime
        if self.start_time:
            runtime = time.time() - self.start_time
            hours = runtime / 3600
            logger.info(f"⏱️ Bot ejecutado por {hours:.2f} horas")
    
    def get_status(self):
        """Obtener estado del bot"""
        if not self.bot:
            return {"status": "not_started"}
        
        status = self.bot.get_status()
        if self.start_time:
            runtime = time.time() - self.start_time
            status["runtime_hours"] = runtime / 3600
            status["start_time"] = datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat()
        
        return status

async def main():
    """Función principal"""
    trading_bot = Trading72hBot()
    
    # Signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(trading_bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await trading_bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await trading_bot.stop()

if __name__ == "__main__":
    print("""
    🚀 BOT DE TRADING 72 HORAS
    =========================
    
    📊 Configuración:
    - 5 estrategias activas
    - Bybit X (datos reales)
    - Paper Trading
    - Alertas Telegram
    - Monitoreo Grafana
    
    🔔 Alertas que recibirás:
    - Señales generadas
    - Órdenes ejecutadas
    - Performance por estrategia
    - Alertas de riesgo
    
    📈 Para ver métricas:
    - Grafana: http://localhost:3000
    - Prometheus: http://localhost:9090
    
    ⏱️ Duración: 72 horas
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


