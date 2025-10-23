"""
Bybit Paper Trading Engine - Simulates trading without real money
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import threading
from queue import Queue

from .bybit_client import BybitClient
from .bybit_websocket import BybitWebSocket
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from signal_engine import SignalEngine, TradingSignal
from indicators_realtime import RealtimeIndicators
from alert_manager import AlertManager
from risk_manager import RiskManager

logger = logging.getLogger(__name__)

@dataclass
class PaperOrder:
    """Paper trading order representation"""
    order_id: str
    symbol: str
    side: str  # 'Buy' or 'Sell'
    order_type: str  # 'Market' or 'Limit'
    qty: float
    price: Optional[float]
    filled_qty: float = 0.0
    status: str = 'New'  # New, PartiallyFilled, Filled, Cancelled
    created_time: float = 0.0
    filled_time: Optional[float] = None
    avg_price: Optional[float] = None

@dataclass
class PaperPosition:
    """Paper trading position representation"""
    symbol: str
    side: str  # 'Buy' or 'Sell'
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    margin: float = 0.0
    leverage: float = 1.0

@dataclass
class PaperTrade:
    """Paper trading trade execution"""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    qty: float
    price: float
    timestamp: float
    commission: float = 0.0

class BybitPaperTrader:
    """Paper trading engine that simulates real trading with Bybit"""
    
    def __init__(self, api_key: str, api_secret: str, initial_balance: float = 10000.0, 
                 testnet: bool = True, commission_rate: float = 0.0006, signal_config: Dict = None):
        """
        Initialize paper trader
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            initial_balance: Starting balance in USDT
            testnet: Use testnet
            commission_rate: Commission rate (0.06% default)
            signal_config: Configuration for signal engine
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.initial_balance = initial_balance
        self.testnet = testnet
        self.commission_rate = commission_rate
        
        # Initialize clients
        self.client = BybitClient(api_key, api_secret, testnet)
        self.websocket = BybitWebSocket(api_key, api_secret, testnet)
        
        # Paper trading state
        self.balance = initial_balance
        self.positions: Dict[str, PaperPosition] = {}
        self.orders: Dict[str, PaperOrder] = {}
        self.trades: List[PaperTrade] = []
        self.order_counter = 0
        
        # Real-time data
        self.current_prices: Dict[str, float] = {}
        self.orderbook_data: Dict[str, Dict] = {}
        
        # Signal engine
        self.signal_config = signal_config or {}
        self.signal_engine = SignalEngine(self.signal_config)
        self.indicators = RealtimeIndicators(buffer_size=200)
        
        # Alert system
        self.alert_config = signal_config.get('alerts', {}) if signal_config else {}
        self.alert_manager = AlertManager(self.alert_config)
        
        # Risk management
        self.risk_config = signal_config.get('risk', {}) if signal_config else {}
        self.risk_manager = RiskManager(self.risk_config)
        
        # Callbacks
        self.order_callbacks: List[Callable] = []
        self.trade_callbacks: List[Callable] = []
        self.position_callbacks: List[Callable] = []
        self.balance_callbacks: List[Callable] = []
        self.signal_callbacks: List[Callable] = []
        self.state_callbacks: List[Callable] = []
        
        # Threading
        self.running = False
        self.data_thread = None
        self.order_queue = Queue()
        
        # Signal processing
        self.last_signal_time: Dict[str, float] = {}
        self.signal_throttle = 300  # 5 minutes between signals per symbol
        
        logger.info(f"BybitPaperTrader initialized - Balance: ${initial_balance}, Testnet: {testnet}")
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        self.order_counter += 1
        return f"paper_{int(time.time() * 1000)}_{self.order_counter}"
    
    def _generate_trade_id(self) -> str:
        """Generate unique trade ID"""
        return f"trade_{int(time.time() * 1000)}_{len(self.trades)}"
    
    def _calculate_commission(self, qty: float, price: float) -> float:
        """Calculate commission for trade"""
        return qty * price * self.commission_rate
    
    def _update_position_pnl(self, symbol: str):
        """Update unrealized PnL for position"""
        if symbol not in self.positions:
            return
            
        position = self.positions[symbol]
        if symbol in self.current_prices:
            mark_price = self.current_prices[symbol]
            position.mark_price = mark_price
            
            if position.side == 'Buy':
                position.unrealized_pnl = (mark_price - position.entry_price) * position.size
            else:  # Sell
                position.unrealized_pnl = (position.entry_price - mark_price) * position.size
    
    def _execute_market_order(self, order: PaperOrder) -> List[PaperTrade]:
        """Execute market order immediately"""
        if order.symbol not in self.current_prices:
            logger.error(f"No price data for {order.symbol}")
            return []
        
        execution_price = self.current_prices[order.symbol]
        commission = self._calculate_commission(order.qty, execution_price)
        
        # Create trade
        trade = PaperTrade(
            trade_id=self._generate_trade_id(),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=execution_price,
            timestamp=time.time(),
            commission=commission
        )
        
        # Update order
        order.filled_qty = order.qty
        order.status = 'Filled'
        order.filled_time = time.time()
        order.avg_price = execution_price
        
        # Send alert for order executed
        self.alert_manager.order_executed(
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=execution_price,
            balance=self.balance
        )
        
        # Update position
        self._update_position_from_trade(trade)
        
        # Update balance
        self.balance -= commission
        
        logger.info(f"Executed market order: {order.symbol} {order.side} {order.qty} @ {execution_price}")
        
        return [trade]
    
    def _execute_limit_order(self, order: PaperOrder) -> List[PaperTrade]:
        """Check if limit order can be executed"""
        if order.symbol not in self.current_prices:
            return []
        
        current_price = self.current_prices[order.symbol]
        can_execute = False
        
        if order.side == 'Buy' and current_price <= order.price:
            can_execute = True
        elif order.side == 'Sell' and current_price >= order.price:
            can_execute = True
        
        if can_execute:
            return self._execute_market_order(order)
        
        return []
    
    def _update_position_from_trade(self, trade: PaperTrade):
        """Update position based on trade execution"""
        symbol = trade.symbol
        
        if symbol not in self.positions:
            # Create new position
            self.positions[symbol] = PaperPosition(
                symbol=symbol,
                side=trade.side,
                size=trade.qty,
                entry_price=trade.price,
                mark_price=trade.price,
                leverage=1.0
            )
        else:
            # Update existing position
            position = self.positions[symbol]
            
            if position.side == trade.side:
                # Increase position
                total_value = (position.size * position.entry_price) + (trade.qty * trade.price)
                position.size += trade.qty
                position.entry_price = total_value / position.size
            else:
                # Reduce or close position
                if trade.qty >= position.size:
                    # Close position completely
                    realized_pnl = (trade.price - position.entry_price) * position.size
                    if position.side == 'Sell':
                        realized_pnl = -realized_pnl
                    
                    position.realized_pnl += realized_pnl
                    self.balance += realized_pnl
                    
                    # Remove position if fully closed
                    if trade.qty == position.size:
                        # Send alert for position closed
                        pnl_pct = realized_pnl / (position.entry_price * position.size) if position.entry_price > 0 else 0
                        self.alert_manager.position_closed(
                            symbol=symbol,
                            pnl=realized_pnl,
                            pnl_pct=pnl_pct,
                            total_balance=self.balance
                        )
                        del self.positions[symbol]
                    else:
                        # Partial close, reverse position
                        remaining_qty = trade.qty - position.size
                        position.side = trade.side
                        position.size = remaining_qty
                        position.entry_price = trade.price
                else:
                    # Partial close
                    realized_pnl = (trade.price - position.entry_price) * trade.qty
                    if position.side == 'Sell':
                        realized_pnl = -realized_pnl
                    
                    position.realized_pnl += realized_pnl
                    self.balance += realized_pnl
                    position.size -= trade.qty
        
        # Update PnL
        self._update_position_pnl(symbol)
    
    def create_order(self, symbol: str, side: str, order_type: str, 
                    qty: float, price: Optional[float] = None) -> PaperOrder:
        """
        Create paper trading order
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            side: 'Buy' or 'Sell'
            order_type: 'Market' or 'Limit'
            qty: Order quantity
            price: Order price (required for Limit orders)
            
        Returns:
            Created paper order
        """
        order_id = self._generate_order_id()
        
        order = PaperOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            qty=qty,
            price=price,
            created_time=time.time()
        )
        
        self.orders[order_id] = order
        
        # Execute immediately if market order
        if order_type == 'Market':
            trades = self._execute_market_order(order)
            for trade in trades:
                self.trades.append(trade)
                self._notify_trade_callbacks(trade)
        else:
            # Add to order queue for limit order processing
            self.order_queue.put(order)
        
        self._notify_order_callbacks(order)
        logger.info(f"Created paper order: {order_id} - {symbol} {side} {qty} @ {price or 'Market'}")
        
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel paper trading order"""
        if order_id not in self.orders:
            logger.warning(f"Order {order_id} not found")
            return False
        
        order = self.orders[order_id]
        if order.status in ['Filled', 'Cancelled']:
            logger.warning(f"Order {order_id} cannot be cancelled (status: {order.status})")
            return False
        
        order.status = 'Cancelled'
        self._notify_order_callbacks(order)
        
        logger.info(f"Cancelled paper order: {order_id}")
        return True
    
    def get_positions(self) -> Dict[str, PaperPosition]:
        """Get current positions"""
        return self.positions.copy()
    
    def get_orders(self, status: str = None) -> List[PaperOrder]:
        """Get orders, optionally filtered by status"""
        orders = list(self.orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return orders
    
    def get_trades(self) -> List[PaperTrade]:
        """Get all trades"""
        return self.trades.copy()
    
    def get_balance(self) -> float:
        """Get current balance"""
        return self.balance
    
    def get_total_equity(self) -> float:
        """Get total equity (balance + unrealized PnL)"""
        total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        return self.balance + total_unrealized
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        total_equity = self.get_total_equity()
        total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_realized = sum(pos.realized_pnl for pos in self.positions.values())
        
        return {
            'balance': self.balance,
            'total_equity': total_equity,
            'unrealized_pnl': total_unrealized,
            'realized_pnl': total_realized,
            'total_return': ((total_equity - self.initial_balance) / self.initial_balance) * 100,
            'positions_count': len(self.positions),
            'open_orders': len([o for o in self.orders.values() if o.status == 'New']),
            'total_trades': len(self.trades)
        }
    
    async def _process_order_queue(self):
        """Process limit orders in queue"""
        while self.running:
            try:
                if not self.order_queue.empty():
                    order = self.order_queue.get_nowait()
                    
                    if order.status == 'New':
                        trades = self._execute_limit_order(order)
                        for trade in trades:
                            self.trades.append(trade)
                            self._notify_trade_callbacks(trade)
                
                await asyncio.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                logger.error(f"Error processing order queue: {e}")
                await asyncio.sleep(1)
    
    async def _handle_ticker_update(self, data: Dict):
        """Handle ticker updates from WebSocket"""
        try:
            topic = data.get('topic', '')
            if 'tickers' in topic:
                ticker_data = data.get('data', {})
                symbol = ticker_data.get('symbol', '')
                # Use indexPrice (real market price) instead of lastPrice (simulated in testnet)
                real_price = float(ticker_data.get('indexPrice', ticker_data.get('lastPrice', 0)))
                volume = float(ticker_data.get('volume24h', 0))
                
                if symbol and real_price > 0:
                    self.current_prices[symbol] = real_price
                    self._update_position_pnl(symbol)
                    
                    # Update indicators with new data
                    self.indicators.update_data(symbol, real_price, volume)
                    
                    # Update signal engine
                    self.signal_engine.update_market_data(symbol, real_price, volume)
                    
                    # Generate signals
                    await self._process_signals(symbol)
                    
        except Exception as e:
            logger.error(f"Error handling ticker update: {e}")
    
    async def _handle_orderbook_update(self, data: Dict):
        """Handle order book updates from WebSocket"""
        try:
            topic = data.get('topic', '')
            if 'orderbook' in topic:
                orderbook_data = data.get('data', {})
                symbol = orderbook_data.get('s', '')
                
                if symbol:
                    self.orderbook_data[symbol] = orderbook_data
                    
        except Exception as e:
            logger.error(f"Error handling orderbook update: {e}")
    
    def _notify_order_callbacks(self, order: PaperOrder):
        """Notify order callbacks"""
        for callback in self.order_callbacks:
            try:
                callback(order)
            except Exception as e:
                logger.error(f"Error in order callback: {e}")
    
    def _notify_trade_callbacks(self, trade: PaperTrade):
        """Notify trade callbacks"""
        for callback in self.trade_callbacks:
            try:
                callback(trade)
            except Exception as e:
                logger.error(f"Error in trade callback: {e}")
        
        # Notify state callbacks for trade executions
        self._notify_state_callbacks('trade', trade)
    
    def _notify_position_callbacks(self, position: PaperPosition):
        """Notify position callbacks"""
        for callback in self.position_callbacks:
            try:
                callback(position)
            except Exception as e:
                logger.error(f"Error in position callback: {e}")
        
        # Notify state callbacks for position changes
        self._notify_state_callbacks('position', position)
    
    def _notify_balance_callbacks(self, balance: float):
        """Notify balance callbacks"""
        for callback in self.balance_callbacks:
            try:
                callback(balance)
            except Exception as e:
                logger.error(f"Error in balance callback: {e}")
        
        # Notify state callbacks for balance changes
        self._notify_state_callbacks('balance', balance)
    
    def _notify_state_callbacks(self, event_type: str, data: Any):
        """Notify state callbacks"""
        for callback in self.state_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
    
    def add_order_callback(self, callback: Callable):
        """Add callback for order updates"""
        self.order_callbacks.append(callback)
    
    def add_trade_callback(self, callback: Callable):
        """Add callback for trade executions"""
        self.trade_callbacks.append(callback)
    
    def add_position_callback(self, callback: Callable):
        """Add callback for position updates"""
        self.position_callbacks.append(callback)
    
    def add_balance_callback(self, callback: Callable):
        """Add callback for balance updates"""
        self.balance_callbacks.append(callback)
    
    def add_signal_callback(self, callback: Callable):
        """Add callback for signal updates"""
        self.signal_callbacks.append(callback)
    
    def add_state_callback(self, callback: Callable):
        """Add callback for state updates"""
        self.state_callbacks.append(callback)
    
    def add_alert_notifier(self, notifier: Callable):
        """Add alert notifier (e.g., Telegram)"""
        self.alert_manager.add_notifier(notifier)
    
    async def start(self, symbols: List[str] = None):
        """Start paper trading engine"""
        if self.running:
            logger.warning("Paper trader already running")
            return
        
        self.running = True
        symbols = symbols or ['ETHUSDT']
        
        logger.info(f"Starting paper trader for symbols: {symbols}")
        
        # Set up WebSocket callbacks
        self.websocket.add_ticker_callback(self._handle_ticker_update)
        self.websocket.add_orderbook_callback(self._handle_orderbook_update)
        
        # Start WebSocket connections
        await self.websocket.start()
        
        # Subscribe to market data
        for symbol in symbols:
            await self.websocket.subscribe_ticker(symbol)
            await self.websocket.subscribe_orderbook(symbol)
        
        # Start order processing task
        asyncio.create_task(self._process_order_queue())
        
        # Register signal engine callback
        self.signal_engine.add_signal_callback(self._on_signal_received)
        
        logger.info("Paper trader started successfully")
    
    async def stop(self):
        """Stop paper trading engine"""
        if not self.running:
            return
        
        self.running = False
        await self.websocket.stop()
        logger.info("Paper trader stopped")
    
    def is_running(self) -> bool:
        """Check if paper trader is running"""
        return self.running
    
    async def _process_signals(self, symbol: str):
        """Process signals for a symbol"""
        try:
            # Check throttling
            current_time = time.time()
            if symbol in self.last_signal_time:
                time_since_last = current_time - self.last_signal_time[symbol]
                if time_since_last < self.signal_throttle:
                    return  # Skip if too soon
            
            # Generate signals
            signals = self.signal_engine.generate_signals(symbol)
            
            for signal in signals:
                logger.info(f"Signal generated: {signal.symbol} {signal.signal_type} @ {signal.price} (confidence: {signal.confidence:.2f})")
                
                # Send alert for signal generated
                self.alert_manager.signal_generated(
                    symbol=signal.symbol,
                    signal_type=signal.signal_type,
                    price=signal.price,
                    confidence=signal.confidence,
                    strategy=signal.strategy
                )
                
                # Update last signal time
                self.last_signal_time[symbol] = current_time
                
                # Notify callbacks
                self._notify_signal_callbacks(signal)
                
        except Exception as e:
            logger.error(f"Error processing signals for {symbol}: {e}")
    
    def _on_signal_received(self, signal: TradingSignal):
        """Handle signal received from signal engine"""
        try:
            logger.info(f"Processing signal: {signal.symbol} {signal.signal_type} @ {signal.price}")
            
            # Prepare signal data for risk validation
            signal_data = {
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'confidence': signal.confidence,
                'price': signal.price,
                'strategy': signal.strategy,
                'indicators': signal.indicators
            }
            
            # Prepare market data for risk validation
            market_data = {
                'price': signal.price,
                'atr': signal.indicators.get('atr', 0.0),
                'volume': signal.indicators.get('volume_ratio', 1.0) * 1000000,  # Simulated volume
                'volume_avg': 1000000,  # Simulated average volume
                'adx': signal.indicators.get('adx', 25.0),
                'rsi': signal.indicators.get('rsi', 50.0),
                'volatility': signal.indicators.get('atr', 0.0) / signal.price if signal.price > 0 else 0.0
            }
            
            # Validate signal with risk manager
            is_valid, reason = self.risk_manager.validate_signal(
                signal_data=signal_data,
                current_balance=self.balance,
                current_positions=self.positions,
                market_data=market_data
            )
            
            if not is_valid:
                logger.warning(f"Signal rejected by risk manager: {reason}")
                self.alert_manager.signal_rejected(signal.symbol, reason, signal.confidence)
                return
            
            # Determine order parameters
            if signal.signal_type == 'BUY':
                side = 'Buy'
                qty = self._calculate_position_size(signal.symbol, signal.price)
            elif signal.signal_type == 'SELL':
                side = 'Sell'
                qty = self._calculate_position_size(signal.symbol, signal.price)
            else:
                return  # HOLD signal, do nothing
            
            if qty <= 0:
                logger.warning(f"Invalid position size calculated: {qty}")
                return
            
            # Create order
            order = self.create_order(
                symbol=signal.symbol,
                side=side,
                order_type='Market',
                qty=qty
            )
            
            logger.info(f"Order created from signal: {order.order_id} - {signal.symbol} {side} {qty}")
            
            # Send alert for signal executed
            self.alert_manager.signal_executed(
                symbol=signal.symbol,
                signal_type=signal.signal_type,
                price=signal.price,
                qty=qty,
                strategy=signal.strategy
            )
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
    
    def _calculate_position_size(self, symbol: str, price: float) -> float:
        """Calculate position size based on risk management"""
        try:
            # Get current balance
            available_balance = self.balance
            
            # Calculate position value (10% of balance by default)
            position_value = available_balance * 0.1
            
            # Calculate quantity
            qty = position_value / price
            
            # Round to reasonable precision
            if symbol.endswith('USDT'):
                qty = round(qty, 3)  # 3 decimal places for most crypto
            else:
                qty = round(qty, 6)  # 6 decimal places for others
            
            return max(0.001, qty)  # Minimum quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def _notify_signal_callbacks(self, signal: TradingSignal):
        """Notify signal callbacks"""
        for callback in self.signal_callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"Error in signal callback: {e}")
    
    def register_strategy(self, name: str, strategy_class, params: Dict[str, Any]):
        """Register a strategy with the signal engine"""
        self.signal_engine.register_strategy(name, strategy_class, params)
        logger.info(f"Strategy registered: {name}")
    
    def get_signal_engine_status(self) -> Dict[str, Any]:
        """Get signal engine status"""
        return self.signal_engine.get_strategy_status()
    
    def get_indicators_status(self) -> Dict[str, Any]:
        """Get indicators status"""
        return self.indicators.get_buffer_status()
