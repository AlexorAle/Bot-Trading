"""
Trade execution and order management.
"""

import ccxt
import pandas as pd
from typing import Optional, Dict, Any
import logging
from config import Config


class Trader:
    """Handles trade execution and order management."""
    
    def __init__(self):
        """Initialize the trader."""
        self.config = Config()
        self.log = logging.getLogger(__name__)
        self.exchange = self._initialize_exchange()
        self.positions = {}
    
    def _initialize_exchange(self):
        """Initialize exchange connection."""
        try:
            exchange_class = getattr(ccxt, self.config.EXCHANGE)
            exchange = exchange_class({
                'apiKey': self.config.API_KEY,
                'secret': self.config.SECRET,
                'sandbox': self.config.TESTNET,
                'enableRateLimit': True,
            })
            return exchange
        except Exception as e:
            self.log.error(f"Failed to initialize exchange: {e}")
            raise
    
    def execute_trade(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a trade based on signal."""
        try:
            if signal is None:
                return None
            
            # In paper trading mode, simulate trade execution
            if self.config.MODE == 'paper':
                return self._simulate_trade(signal)
            
            # In live mode, execute real trade
            elif self.config.MODE == 'live':
                return self._execute_real_trade(signal)
            
            else:
                self.log.warning(f"Unknown trading mode: {self.config.MODE}")
                return None
                
        except Exception as e:
            self.log.error(f"Error executing trade: {e}")
            return None
    
    def _simulate_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate trade execution for paper trading."""
        try:
            # Simulate order placement
            order_id = f"sim_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Calculate fees (simplified)
            fee_rate = 0.001  # 0.1% fee
            fee = signal['size'] * signal['price'] * fee_rate
            
            # Create simulated trade result
            trade_result = {
                'order_id': order_id,
                'symbol': signal['symbol'],
                'side': signal['direction'],
                'amount': signal['size'],
                'price': signal['price'],
                'fee': fee,
                'status': 'filled',
                'timestamp': pd.Timestamp.now(),
                'simulated': True
            }
            
            # Store position
            self.positions[signal['symbol']] = {
                'side': signal['direction'],
                'size': signal['size'],
                'entry_price': signal['price'],
                'timestamp': pd.Timestamp.now()
            }
            
            self.log.info(f"Simulated trade executed: {trade_result}")
            return trade_result
            
        except Exception as e:
            self.log.error(f"Error simulating trade: {e}")
            return None
    
    def _execute_real_trade(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute real trade on exchange."""
        try:
            # Place order
            order = self.exchange.create_order(
                symbol=signal['symbol'],
                type='market',
                side=signal['direction'],
                amount=signal['size']
            )
            
            # Wait for order to be filled
            filled_order = self.exchange.fetch_order(order['id'], signal['symbol'])
            
            if filled_order['status'] == 'closed':
                # Store position
                self.positions[signal['symbol']] = {
                    'side': signal['direction'],
                    'size': signal['size'],
                    'entry_price': filled_order['average'],
                    'timestamp': pd.Timestamp.now()
                }
                
                self.log.info(f"Real trade executed: {filled_order}")
                return filled_order
            else:
                self.log.warning(f"Order not filled: {filled_order}")
                return None
                
        except Exception as e:
            self.log.error(f"Error executing real trade: {e}")
            return None
    
    def close_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Close a position."""
        try:
            if symbol not in self.positions:
                self.log.warning(f"No position found for {symbol}")
                return None
            
            position = self.positions[symbol]
            
            # In paper trading mode, simulate position closure
            if self.config.MODE == 'paper':
                return self._simulate_close_position(symbol, position)
            
            # In live mode, execute real close
            elif self.config.MODE == 'live':
                return self._execute_real_close(symbol, position)
            
            else:
                self.log.warning(f"Unknown trading mode: {self.config.MODE}")
                return None
                
        except Exception as e:
            self.log.error(f"Error closing position: {e}")
            return None
    
    def _simulate_close_position(self, symbol: str, position: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate position closure for paper trading."""
        try:
            # Get current price
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Calculate P&L
            entry_price = position['entry_price']
            size = position['size']
            
            if position['side'] == 'buy':
                pnl = (current_price - entry_price) * size
            else:
                pnl = (entry_price - current_price) * size
            
            # Create close result
            close_result = {
                'symbol': symbol,
                'side': 'close',
                'amount': size,
                'price': current_price,
                'pnl': pnl,
                'timestamp': pd.Timestamp.now(),
                'simulated': True
            }
            
            # Remove position
            del self.positions[symbol]
            
            self.log.info(f"Simulated position closed: {close_result}")
            return close_result
            
        except Exception as e:
            self.log.error(f"Error simulating close: {e}")
            return None
    
    def _execute_real_close(self, symbol: str, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute real position closure."""
        try:
            # Determine opposite side
            opposite_side = 'sell' if position['side'] == 'buy' else 'buy'
            
            # Place closing order
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=opposite_side,
                amount=position['size']
            )
            
            # Wait for order to be filled
            filled_order = self.exchange.fetch_order(order['id'], symbol)
            
            if filled_order['status'] == 'closed':
                # Remove position
                del self.positions[symbol]
                
                self.log.info(f"Real position closed: {filled_order}")
                return filled_order
            else:
                self.log.warning(f"Close order not filled: {filled_order}")
                return None
                
        except Exception as e:
            self.log.error(f"Error executing real close: {e}")
            return None
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current positions."""
        return self.positions.copy()
    
    def validate(self) -> bool:
        """Validate trader configuration."""
        try:
            # Test exchange connection
            if self.config.MODE == 'live':
                markets = self.exchange.load_markets()
                return len(markets) > 0
            else:
                # For paper trading, just check if exchange can be initialized
                return self.exchange is not None
        except Exception as e:
            self.log.error(f"Trader validation failed: {e}")
            return False




