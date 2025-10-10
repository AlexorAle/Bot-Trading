"""
Data fetcher for market data from exchanges.
"""

import ccxt
import pandas as pd
import numpy as np
import time
from typing import Optional, Dict, Any
import logging
from config import Config


class DataFetcher:
    """Fetches market data from exchanges."""
    
    def __init__(self):
        """Initialize the data fetcher."""
        self.config = Config()
        self.exchange = self._initialize_exchange()
        self.log = logging.getLogger(__name__)
    
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
    
    def _fetch_ohlcv_with_retry(self, max_retries: int = 3) -> Optional[list]:
        """Fetch OHLCV data with retry logic."""
        for attempt in range(max_retries):
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    self.config.SYMBOL,
                    self.config.TIMEFRAME,
                    limit=self.config.DATA_LIMIT
                )
                return ohlcv
            except Exception as e:
                self.log.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e
    
    def _validate_data_quality(self, df: pd.DataFrame) -> bool:
        """Validate data quality."""
        if df.empty:
            return False
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            return False
        
        if df[required_columns].isnull().any().any():
            return False
        
        if (df[['open', 'high', 'low', 'close']] <= 0).any().any():
            return False
        
        if (df['volume'] < 0).any():
            return False
        
        return True
    
    def fetch_data(self) -> Optional[pd.DataFrame]:
        """Fetch and process market data."""
        try:
            ohlcv = self._fetch_ohlcv_with_retry()
            if ohlcv is None:
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            if not self._validate_data_quality(df):
                self.log.warning("Data quality validation failed")
                return None
            
            # Add technical indicators
            df = self._add_technical_indicators(df)
            
            # Add liquidation data (simulated)
            df = self._add_liquidation_data(df)
            
            self.log.info(f"Fetched {len(df)} data points for {self.config.SYMBOL}")
            return df
            
        except Exception as e:
            self.log.error(f"Error fetching data: {e}")
            return None
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe."""
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Price change
        df['price_change'] = df['close'].pct_change()
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Volatility
        df['volatility'] = df['price_change'].rolling(window=20).std()
        
        return df
    
    def _add_liquidation_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add liquidation data (simulated for now)."""
        # Simulate liquidation data
        np.random.seed(42)  # For reproducible results
        df['liquidations_long'] = np.random.poisson(5, len(df))
        df['liquidations_short'] = np.random.poisson(5, len(df))
        df['liquidations_volume'] = df['liquidations_long'] + df['liquidations_short']
        
        return df
    
    def validate(self) -> bool:
        """Validate data fetcher configuration."""
        try:
            # Test exchange connection
            markets = self.exchange.load_markets()
            return len(markets) > 0
        except Exception as e:
            self.log.error(f"Data fetcher validation failed: {e}")
            return False




