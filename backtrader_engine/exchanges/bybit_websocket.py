"""
Bybit WebSocket client for real-time data streaming
"""

import asyncio
import websockets
import json
import hmac
import hashlib
import time
import logging
from typing import Dict, List, Callable, Optional, Any
import threading

logger = logging.getLogger(__name__)

class BybitWebSocket:
    """Bybit WebSocket client for real-time market data and private updates"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        """
        Initialize Bybit WebSocket client
        
        Args:
            api_key: Bybit API key (for private streams)
            api_secret: Bybit API secret (for private streams)
            testnet: Use testnet (True) or mainnet (False)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # WebSocket URLs
        if testnet:
            self.public_url = "wss://stream-testnet.bybit.com/v5/public/linear"
            self.private_url = "wss://stream-testnet.bybit.com/v5/private"
        else:
            self.public_url = "wss://stream.bybit.com/v5/public/linear"
            self.private_url = "wss://stream.bybit.com/v5/private"
        
        # Connection state
        self.public_ws = None
        self.private_ws = None
        self.public_connected = False
        self.private_connected = False
        
        # Callbacks
        self.ticker_callbacks: List[Callable] = []
        self.orderbook_callbacks: List[Callable] = []
        self.order_callbacks: List[Callable] = []
        self.position_callbacks: List[Callable] = []
        
        # Reconnection
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5
        
        logger.info(f"BybitWebSocket initialized - Testnet: {testnet}")
    
    def _generate_auth_signature(self, expires: int) -> str:
        """Generate authentication signature for private WebSocket"""
        message = f"GET/realtime{expires}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _connect_public(self):
        """Connect to public WebSocket stream"""
        try:
            self.public_ws = await websockets.connect(self.public_url)
            self.public_connected = True
            self.reconnect_attempts = 0
            logger.info("Connected to Bybit public WebSocket")
            
            # Start listening for messages in background task
            asyncio.create_task(self._listen_public())
            logger.info("Started public WebSocket listener task")
            
        except Exception as e:
            logger.error(f"Failed to connect to public WebSocket: {e}")
            self.public_connected = False
            await self._reconnect_public()
    
    async def _connect_private(self):
        """Connect to private WebSocket stream"""
        if not self.api_key or not self.api_secret:
            logger.warning("API credentials not provided, skipping private WebSocket")
            return
            
        try:
            self.private_ws = await websockets.connect(self.private_url)
            
            # Authenticate
            expires = int((time.time() + 1) * 1000)
            signature = self._generate_auth_signature(expires)
            
            auth_message = {
                "op": "auth",
                "args": [self.api_key, expires, signature]
            }
            
            await self.private_ws.send(json.dumps(auth_message))
            auth_response = await self.private_ws.recv()
            auth_data = json.loads(auth_response)
            
            if auth_data.get('success'):
                self.private_connected = True
                self.reconnect_attempts = 0
                logger.info("Authenticated with Bybit private WebSocket")
                
                # Start listening for messages in background task
                asyncio.create_task(self._listen_private())
                logger.info("Started private WebSocket listener task")
            else:
                logger.error(f"Authentication failed: {auth_data}")
                
        except Exception as e:
            logger.error(f"Failed to connect to private WebSocket: {e}")
            self.private_connected = False
            await self._reconnect_private()
    
    async def _listen_public(self):
        """Listen for public WebSocket messages"""
        try:
            async for message in self.public_ws:
                try:
                    data = json.loads(message)
                    await self._handle_public_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse public message: {e}")
                except Exception as e:
                    logger.error(f"Error handling public message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Public WebSocket connection closed")
            self.public_connected = False
            await self._reconnect_public()
        except Exception as e:
            logger.error(f"Error in public WebSocket listener: {e}")
            self.public_connected = False
    
    async def _listen_private(self):
        """Listen for private WebSocket messages"""
        try:
            async for message in self.private_ws:
                try:
                    data = json.loads(message)
                    await self._handle_private_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse private message: {e}")
                except Exception as e:
                    logger.error(f"Error handling private message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Private WebSocket connection closed")
            self.private_connected = False
            await self._reconnect_private()
        except Exception as e:
            logger.error(f"Error in private WebSocket listener: {e}")
            self.private_connected = False
    
    async def _handle_public_message(self, data: Dict):
        """Handle public WebSocket messages"""
        topic = data.get('topic', '')
        logger.info(f"📨 Received public message: {topic}")
        
        if 'tickers' in topic:
            logger.info(f"📊 Processing ticker data: {data}")
            # Ticker data
            for callback in self.ticker_callbacks:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error in ticker callback: {e}")
                    
        elif 'orderbook' in topic:
            logger.info(f"📚 Processing orderbook data: {data}")
            # Order book data
            for callback in self.orderbook_callbacks:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error in orderbook callback: {e}")
        else:
            logger.info(f"📄 Unknown message type: {topic}")
    
    async def _handle_private_message(self, data: Dict):
        """Handle private WebSocket messages"""
        topic = data.get('topic', '')
        
        if 'order' in topic:
            # Order updates
            for callback in self.order_callbacks:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error in order callback: {e}")
                    
        elif 'position' in topic:
            # Position updates
            for callback in self.position_callbacks:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error in position callback: {e}")
    
    async def _reconnect_public(self):
        """Reconnect to public WebSocket"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached for public WebSocket")
            return
            
        self.reconnect_attempts += 1
        logger.info(f"Reconnecting to public WebSocket (attempt {self.reconnect_attempts})")
        
        await asyncio.sleep(self.reconnect_delay)
        await self._connect_public()
    
    async def _reconnect_private(self):
        """Reconnect to private WebSocket"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached for private WebSocket")
            return
            
        self.reconnect_attempts += 1
        logger.info(f"Reconnecting to private WebSocket (attempt {self.reconnect_attempts})")
        
        await asyncio.sleep(self.reconnect_delay)
        await self._connect_private()
    
    async def subscribe_ticker(self, symbol: str):
        """Subscribe to ticker updates for symbol"""
        if not self.public_connected:
            await self._connect_public()
        
        subscribe_message = {
            "op": "subscribe",
            "args": [f"tickers.{symbol}"]
        }
        
        await self.public_ws.send(json.dumps(subscribe_message))
        logger.info(f"📡 Subscribed to ticker updates for {symbol}")
        logger.info(f"📡 Subscription message: {subscribe_message}")
    
    async def subscribe_orderbook(self, symbol: str, depth: int = 25):
        """Subscribe to order book updates for symbol"""
        if not self.public_connected:
            await self._connect_public()
        
        subscribe_message = {
            "op": "subscribe",
            "args": [f"orderbook.{depth}.{symbol}"]
        }
        
        await self.public_ws.send(json.dumps(subscribe_message))
        logger.info(f"Subscribed to orderbook updates for {symbol} (depth: {depth})")
    
    async def subscribe_orders(self):
        """Subscribe to order updates (private)"""
        if not self.private_connected:
            await self._connect_private()
        
        subscribe_message = {
            "op": "subscribe",
            "args": ["order"]
        }
        
        await self.private_ws.send(json.dumps(subscribe_message))
        logger.info("Subscribed to order updates")
    
    async def subscribe_positions(self):
        """Subscribe to position updates (private)"""
        if not self.private_connected:
            await self._connect_private()
        
        subscribe_message = {
            "op": "subscribe",
            "args": ["position"]
        }
        
        await self.private_ws.send(json.dumps(subscribe_message))
        logger.info("Subscribed to position updates")
    
    def add_ticker_callback(self, callback: Callable):
        """Add callback for ticker updates"""
        self.ticker_callbacks.append(callback)
    
    def add_orderbook_callback(self, callback: Callable):
        """Add callback for order book updates"""
        self.orderbook_callbacks.append(callback)
    
    def add_order_callback(self, callback: Callable):
        """Add callback for order updates"""
        self.order_callbacks.append(callback)
    
    def add_position_callback(self, callback: Callable):
        """Add callback for position updates"""
        self.position_callbacks.append(callback)
    
    async def start(self):
        """Start WebSocket connections"""
        logger.info("Starting Bybit WebSocket connections...")
        
        # Start public connection
        logger.info("Connecting to public WebSocket...")
        await self._connect_public()
        logger.info("Public WebSocket connection completed")
        
        # Start private connection if credentials provided
        if self.api_key and self.api_secret:
            logger.info("Connecting to private WebSocket...")
            await self._connect_private()
            logger.info("Private WebSocket connection completed")
        else:
            logger.info("No credentials provided, skipping private WebSocket")
    
    async def stop(self):
        """Stop WebSocket connections"""
        logger.info("Stopping Bybit WebSocket connections...")
        
        if self.public_ws:
            await self.public_ws.close()
            self.public_connected = False
            
        if self.private_ws:
            await self.private_ws.close()
            self.private_connected = False
    
    def is_connected(self) -> Dict[str, bool]:
        """Check connection status"""
        return {
            'public': self.public_connected,
            'private': self.private_connected
        }
