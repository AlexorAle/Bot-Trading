#!/usr/bin/env python3
"""
Entry point for VSTRU Trading Strategy - Signals every 15 minutes
Based on agent guide: GUIA_TESTING_BYBIT_TESTNET_VSTRU.md
"""

import asyncio
import json
import logging
import signal
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vstru_trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Import trading engine
from exchanges.bybit_paper_trader import BybitPaperTrader
from signal_engine import TradingSignal
from alert_manager import AlertManager

class VSTRUTradingBot:
    """
    Bot with VSTRU Strategy - Generates signals every 15 minutes
    
    VSTRU Logic:
    - Frequency: Every 15 minutes (900 seconds)
    - Symbols: ETHUSDT, BTCUSDT, SOLUSDT
    - Signals: BUY/SELL alternating for testing
    - Confidence: 0.75 (high enough to pass risk checks)
    """
    
    def __init__(self, config_path='configs/bybit_x_config.json'):
        self.config_path = config_path
        self.config = self._load_config()
        self.paper_trader = None
        self.running = False
        self.start_time = None
        
        # VSTRU Strategy state
        self.signal_counter = 0
        self.last_signal_time = {}
        self.signal_interval = 900  # 15 minutes in seconds
        self.symbols = ['ETHUSDT', 'BTCUSDT', 'SOLUSDT']
        
        # Initialize AlertManager with Telegram
        self.alert_manager = self._init_alert_manager()
        
        logger.info("VSTRUTradingBot initialized")
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Signal interval: {self.signal_interval}s (15 minutes)")
    
    def _init_alert_manager(self):
        """Initialize AlertManager with Telegram notifications"""
        try:
            alert_config_path = Path(__file__).parent / 'configs' / 'alert_config.json'
            with open(alert_config_path, 'r') as f:
                alert_config = json.load(f)
            
            # Merge alerts and telegram config
            config = {
                **alert_config.get('alerts', {}),
                'telegram': alert_config.get('telegram', {})
            }
            
            alert_manager = AlertManager(config)
            logger.info("AlertManager initialized with Telegram support")
            return alert_manager
        except Exception as e:
            logger.error(f"Error initializing AlertManager: {e}")
            return None
    
    def _load_config(self):
        """Load configuration from JSON"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Config loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)
    
    async def start(self):
        """Start the VSTRU trading bot"""
        try:
            logger.info("=" * 80)
            logger.info("STARTING VSTRU TRADING BOT")
            logger.info("=" * 80)
            
            self.start_time = time.time()
            self.running = True
            
            # Initialize paper trader
            exchange_config = self.config.get('exchange', {})
            api_key = exchange_config.get('api_key')
            api_secret = exchange_config.get('api_secret')
            testnet = exchange_config.get('testnet', True)
            commission_rate = exchange_config.get('commission_rate', 0.0006)
            
            logger.info(f"API Key: {api_key[:10]}...")
            logger.info(f"Testnet: {testnet}")
            logger.info(f"Commission: {commission_rate * 100}%")
            
            self.paper_trader = BybitPaperTrader(
                api_key=api_key,
                api_secret=api_secret,
                initial_balance=10000.0,
                testnet=testnet,
                commission_rate=commission_rate,
                signal_config=self.config
            )
            
            # Subscribe to symbols
            symbols = self.config.get('symbols', self.symbols)
            logger.info(f"Subscribing to: {symbols}")
            
            # Start paper trader with symbols (it will subscribe automatically)
            await self.paper_trader.start(symbols=symbols)
            
            logger.info("Bot started successfully")
            logger.info("VSTRU Strategy active - Signals every 15 minutes")
            logger.info("=" * 80)
            
            # Send Telegram notification
            if self.alert_manager:
                config_info = f"Symbols: {', '.join(self.symbols)} | Signal interval: 15min"
                self.alert_manager.bot_started(config_info)
            
            # Start VSTRU signal generation loop in parallel
            vstru_task = asyncio.create_task(self._vstru_signal_loop())
            logger.info("VSTRU signal loop task created")
            
            # Keep running indefinitely
            await vstru_task
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _vstru_signal_loop(self):
        """Main loop for VSTRU signal generation"""
        logger.info("Starting VSTRU signal generation loop...")
        
        # Wait for price data to be available
        logger.info("Waiting for price data from WebSocket...")
        await asyncio.sleep(5)
        
        # Generate initial signals immediately for testing
        logger.info("Generating INITIAL test signals...")
        for symbol in self.symbols:
            await self._generate_vstru_signal(symbol)
            self.last_signal_time[symbol] = time.time()
            await asyncio.sleep(2)
        
        logger.info(f"Initial signals generated. Next signals in {self.signal_interval} seconds (15 minutes)")
        
        while self.running:
            try:
                current_time = time.time()
                
                for symbol in self.symbols:
                    # Check if it's time to generate signal
                    last_signal = self.last_signal_time.get(symbol, 0)
                    time_since_last = current_time - last_signal
                    
                    if time_since_last >= self.signal_interval:
                        await self._generate_vstru_signal(symbol)
                        self.last_signal_time[symbol] = current_time
                
                # Wait 10 seconds before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in VSTRU loop: {e}")
                import traceback
                traceback.print_exc()
    
    async def _generate_vstru_signal(self, symbol: str):
        """
        Generate VSTRU signal for symbol
        Alternates BUY/SELL for testing purposes
        """
        try:
            # Get current price
            price = self.paper_trader.current_prices.get(symbol, 0.0)
            
            if price == 0.0:
                logger.warning(f"No price data for {symbol}, skipping signal")
                return
            
            # Alternate BUY/SELL
            signal_type = 'BUY' if self.signal_counter % 2 == 0 else 'SELL'
            self.signal_counter += 1
            
            # Create trading signal
            signal = TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=0.75,  # High enough to pass risk checks
                price=price,
                strategy='VSTRUStrategy',
                timestamp=time.time(),
                indicators={
                    'vstru_cycle': self.signal_counter,
                    'test_mode': True,
                    'interval': '15min'
                },
                metadata={
                    'source': 'VSTRU',
                    'purpose': 'testnet_validation'
                }
            )
            
            logger.info("=" * 80)
            logger.info(f"VSTRU SIGNAL #{self.signal_counter}")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Type: {signal_type}")
            logger.info(f"   Price: ${price:.2f}")
            logger.info(f"   Confidence: {signal.confidence}")
            logger.info(f"   Time: {datetime.now(timezone.utc).isoformat()}")
            logger.info("=" * 80)
            
            # Send signal to paper trader
            if hasattr(self.paper_trader, '_on_signal_received'):
                self.paper_trader._on_signal_received(signal)
            else:
                logger.error("Paper trader doesn't have _on_signal_received method")
            
        except Exception as e:
            logger.error(f"Error generating VSTRU signal: {e}")
            import traceback
            traceback.print_exc()
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping VSTRU bot...")
        self.running = False
        
        # Send Telegram notification
        if self.alert_manager and self.start_time:
            runtime = time.time() - self.start_time
            hours = runtime / 3600
            reason = f"Runtime: {hours:.2f}h | Signals: {self.signal_counter}"
            self.alert_manager.bot_stopped(reason)
        
        if self.paper_trader:
            await self.paper_trader.stop()
        
        if self.start_time:
            runtime = time.time() - self.start_time
            hours = runtime / 3600
            logger.info(f"Bot ran for {hours:.2f} hours")
            logger.info(f"Total signals generated: {self.signal_counter}")
    
    def get_status(self):
        """Get bot status"""
        status = {
            'running': self.running,
            'signals_generated': self.signal_counter,
            'symbols': self.symbols,
            'signal_interval': self.signal_interval
        }
        
        if self.start_time:
            runtime = time.time() - self.start_time
            status['runtime_hours'] = runtime / 3600
            status['start_time'] = datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat()
        
        if self.paper_trader:
            status['balance'] = self.paper_trader.balance
            status['positions'] = len(self.paper_trader.positions)
            status['orders'] = len(self.paper_trader.orders)
        
        return status


async def main():
    """Main entry point"""
    bot = VSTRUTradingBot()
    
    # Signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.stop()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
