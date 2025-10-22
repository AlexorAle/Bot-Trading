"""
Bybit REST API Client for trading operations
"""

import hmac
import hashlib
import time
import requests
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class BybitClient:
    """Bybit REST API Client with authentication and rate limiting"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize Bybit client
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            testnet: Use testnet (True) or mainnet (False)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Base URLs
        if testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
            
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TradingBot/1.0'
        })
        
        logger.info(f"BybitClient initialized - Testnet: {testnet}")
    
    def _generate_signature(self, params: str, timestamp: str) -> str:
        """Generate HMAC SHA256 signature for API requests"""
        message = timestamp + self.api_key + "5000" + params
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     signed: bool = False) -> Dict:
        """
        Make authenticated request to Bybit API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether to sign the request
            
        Returns:
            API response as dictionary
        """
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        if signed:
            timestamp = str(int(time.time() * 1000))
            params['api_key'] = self.api_key
            params['timestamp'] = timestamp
            params['recv_window'] = 5000
            
            # Sort parameters for signature
            sorted_params = sorted(params.items())
            query_string = urlencode(sorted_params)
            
            # Generate signature
            signature = self._generate_signature(query_string, timestamp)
            params['sign'] = signature
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            else:
                response = self.session.post(url, json=params)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('retCode') != 0:
                raise Exception(f"API Error: {data.get('retMsg', 'Unknown error')}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_account_balance(self) -> Dict:
        """Get account wallet balance"""
        try:
            response = self._make_request('GET', '/v5/account/wallet-balance', signed=True)
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            raise
    
    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Get current positions"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
                
            response = self._make_request('GET', '/v5/position/list', params, signed=True)
            return response.get('result', {}).get('list', [])
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get ticker information for symbol"""
        try:
            params = {'category': 'linear', 'symbol': symbol}
            response = self._make_request('GET', '/v5/market/tickers', params)
            result = response.get('result', {}).get('list', [])
            ticker_data = result[0] if result else {}
            
            # Use indexPrice (real market price) instead of lastPrice (simulated in testnet)
            if ticker_data and 'indexPrice' in ticker_data:
                ticker_data['realPrice'] = ticker_data['indexPrice']
            
            return ticker_data
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            raise
    
    def get_orderbook(self, symbol: str, limit: int = 25) -> Dict:
        """Get order book for symbol"""
        try:
            params = {'category': 'linear', 'symbol': symbol, 'limit': limit}
            response = self._make_request('GET', '/v5/market/orderbook', params)
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Failed to get orderbook for {symbol}: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str = '15', limit: int = 200) -> List[Dict]:
        """Get kline/candlestick data"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = self._make_request('GET', '/v5/market/kline', params)
            return response.get('result', {}).get('list', [])
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            raise
    
    def create_order(self, symbol: str, side: str, order_type: str, 
                    qty: str, price: str = None, time_in_force: str = 'GTC') -> Dict:
        """
        Create order (for paper trading simulation)
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            side: 'Buy' or 'Sell'
            order_type: 'Market' or 'Limit'
            qty: Order quantity
            price: Order price (required for Limit orders)
            time_in_force: 'GTC', 'IOC', 'FOK'
        """
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': side,
                'orderType': order_type,
                'qty': qty,
                'timeInForce': time_in_force
            }
            
            if price and order_type == 'Limit':
                params['price'] = price
            
            # For paper trading, we'll simulate the order creation
            logger.info(f"Paper Trading - Simulating order: {params}")
            
            # Return simulated order response
            simulated_response = {
                'retCode': 0,
                'retMsg': 'OK',
                'result': {
                    'orderId': f"paper_{int(time.time() * 1000)}",
                    'orderLinkId': f"paper_{symbol}_{side}_{int(time.time())}",
                    'symbol': symbol,
                    'side': side,
                    'orderType': order_type,
                    'qty': qty,
                    'price': price or '0',
                    'timeInForce': time_in_force,
                    'orderStatus': 'New',
                    'createdTime': str(int(time.time() * 1000))
                }
            }
            
            return simulated_response
            
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: str = None, order_link_id: str = None) -> Dict:
        """Cancel order"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol
            }
            
            if order_id:
                params['orderId'] = order_id
            elif order_link_id:
                params['orderLinkId'] = order_link_id
            else:
                raise ValueError("Either order_id or order_link_id must be provided")
            
            # For paper trading, simulate cancellation
            logger.info(f"Paper Trading - Simulating order cancellation: {params}")
            
            simulated_response = {
                'retCode': 0,
                'retMsg': 'OK',
                'result': {
                    'orderId': order_id or order_link_id,
                    'orderStatus': 'Cancelled'
                }
            }
            
            return simulated_response
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        try:
            params = {'category': 'linear'}
            if symbol:
                params['symbol'] = symbol
                
            # For paper trading, return empty list (no real orders)
            logger.info(f"Paper Trading - No open orders for {symbol or 'all symbols'}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Test with a simple public endpoint
            response = self._make_request('GET', '/v5/market/time')
            return response.get('retCode') == 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
