"""
LSTM Data Fetcher
Production-grade data fetching layer for LSTM feature extraction.
Handles Alpaca, Polygon, and yfinance with proper sequence preprocessing.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class LSTMDataFetcher:
    """
    Fetches and preprocesses price data for LSTM feature extraction.
    Handles warm-up, sequence creation, and normalization.
    """
    
    def __init__(self, window_size: int = 60):
        """
        Initialize data fetcher.
        
        Args:
            window_size: Number of time steps for LSTM (default: 60 minutes)
        """
        self.window_size = window_size
        self.warm_up_data = {}  # Cache for warm-up sequences
    
    async def get_hybrid_features(
        self,
        symbol: str,
        use_alpaca: bool = True,
        timeframe: str = '1Min'
    ) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Get hybrid features: LSTM sequence + alternative data.
        
        Args:
            symbol: Stock symbol
            use_alpaca: Use Alpaca API (if available)
            timeframe: Timeframe for bars ('1Min', '5Min', etc.)
        
        Returns:
            Tuple of (lstm_input, alt_data_df)
            - lstm_input: 3D array (1, window_size, 5) for LSTM
            - alt_data_df: DataFrame with alternative data features
        """
        try:
            # 1. Fetch intraday price data for LSTM
            price_data = await self._fetch_price_data(symbol, use_alpaca, timeframe)
            
            if price_data is None or len(price_data) < self.window_size:
                logger.warning(f"Insufficient data for {symbol}, using warm-up cache")
                price_data = self._get_warm_up_data(symbol)
            
            # 2. Create LSTM sequence (last N bars)
            lstm_input = self._create_lstm_sequence(price_data)
            
            # 3. Fetch alternative data for XGBoost
            alt_data = await self._fetch_alternative_data(symbol)
            alt_data_df = pd.DataFrame([alt_data])
            
            # 4. Store in warm-up cache
            self.warm_up_data[symbol] = price_data.tail(self.window_size)
            
            return lstm_input, alt_data_df
            
        except Exception as e:
            logger.error(f"Error getting hybrid features for {symbol}: {e}")
            # Return default/empty data
            return np.zeros((1, self.window_size, 5)), pd.DataFrame()
    
    async def _fetch_price_data(
        self,
        symbol: str,
        use_alpaca: bool,
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """Fetch price data from Alpaca or yfinance"""
        try:
            # Try Alpaca first (if configured)
            if use_alpaca:
                try:
                    from .alpaca_trading_service import AlpacaTradingService
                    from .broker_models import BrokerAccount
                    
                    # Get first active broker account (for API access)
                    broker_account = BrokerAccount.objects.filter(status='ACTIVE').first()
                    if broker_account and broker_account.access_token:
                        # Use Alpaca API directly
                        import requests
                        headers = {
                            'APCA-API-KEY-ID': broker_account.api_key or '',
                            'APCA-API-SECRET-KEY': broker_account.api_secret or '',
                        }
                        
                        # Alpaca bars endpoint
                        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
                        params = {
                            'timeframe': timeframe,
                            'limit': self.window_size,
                            'adjustment': 'raw'
                        }
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, headers=headers, params=params) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    bars = data.get('bars', [])
                                    
                                    if bars:
                                        df = pd.DataFrame(bars)
                                        df['timestamp'] = pd.to_datetime(df['t'])
                                        df = df.set_index('timestamp')
                                        df = df[['o', 'h', 'l', 'c', 'v']]
                                        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                                        return df
                except Exception as e:
                    logger.debug(f"Alpaca fetch failed for {symbol}: {e}, trying yfinance")
            
            # Fallback to yfinance
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            
            # Get intraday data (last 5 days should cover 60 minutes)
            hist = ticker.history(period='5d', interval='1m')
            
            if hist.empty:
                # Try daily data as fallback
                hist = ticker.history(period='60d', interval='1d')
                if hist.empty:
                    return None
            
            # Ensure we have OHLCV columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in hist.columns for col in required_cols):
                return None
            
            # Get last N bars
            return hist[required_cols].tail(self.window_size)
            
        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {e}")
            return None
    
    def _create_lstm_sequence(self, price_data: pd.DataFrame) -> np.ndarray:
        """
        Create LSTM input sequence from price data.
        Returns 3D array: (1, window_size, 5) for OHLCV
        """
        try:
            # Get OHLCV columns
            ohlcv_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            sequence = price_data[ohlcv_cols].values
            
            # Ensure we have exactly window_size rows
            if len(sequence) < self.window_size:
                # Pad with last value
                padding = np.tile(sequence[-1:], (self.window_size - len(sequence), 1))
                sequence = np.vstack([padding, sequence])
            elif len(sequence) > self.window_size:
                # Take last N rows
                sequence = sequence[-self.window_size:]
            
            # Reshape to (1, window_size, 5) for LSTM
            sequence = np.expand_dims(sequence, axis=0)
            
            return sequence
            
        except Exception as e:
            logger.error(f"Error creating LSTM sequence: {e}")
            return np.zeros((1, self.window_size, 5))
    
    async def _fetch_alternative_data(self, symbol: str) -> Dict[str, float]:
        """Fetch alternative data (options, earnings, insider, sentiment)"""
        try:
            from .hybrid_ml_predictor import HybridMLPredictor
            
            predictor = HybridMLPredictor()
            
            # Get all alternative features
            options_feat = await predictor.options_features.get_options_features(symbol)
            earnings_feat = await predictor.earnings_insider.get_earnings_features(symbol)
            insider_feat = await predictor.earnings_insider.get_insider_features(symbol)
            
            # Get social sentiment
            try:
                from .deep_social_sentiment_service import get_deep_social_sentiment_service
                social_service = get_deep_social_sentiment_service()
                social_data = await social_service.get_comprehensive_sentiment(symbol, hours_back=24)
                social_feat = {
                    'social_sentiment': social_data.sentiment_score,
                    'social_volume': social_data.volume,
                    'social_engagement': social_data.engagement_score
                }
            except:
                social_feat = {}
            
            # Combine all features
            return {
                **options_feat,
                **earnings_feat,
                **insider_feat,
                **social_feat
            }
            
        except Exception as e:
            logger.error(f"Error fetching alternative data for {symbol}: {e}")
            return {}
    
    def _get_warm_up_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get warm-up data from cache"""
        return self.warm_up_data.get(symbol)
    
    def warm_up(self, symbols: List[str]):
        """
        Warm up data cache for symbols.
        Call this before live trading to pre-fetch sequences.
        """
        logger.info(f"Warming up LSTM data cache for {len(symbols)} symbols...")
        
        async def fetch_all():
            tasks = [self.get_hybrid_features(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        # Run warm-up
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule as task
                asyncio.create_task(fetch_all())
            else:
                loop.run_until_complete(fetch_all())
        except RuntimeError:
            # No event loop, create new one
            asyncio.run(fetch_all())
        
        logger.info("✅ Warm-up complete")


# Global instance
_lstm_data_fetcher = None

def get_lstm_data_fetcher(window_size: int = 60) -> LSTMDataFetcher:
    """Get global LSTM data fetcher instance"""
    global _lstm_data_fetcher
    if _lstm_data_fetcher is None:
        _lstm_data_fetcher = LSTMDataFetcher(window_size=window_size)
    return _lstm_data_fetcher

