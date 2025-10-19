"""
Market Data API Service for Real Financial Data
Integrates with Alpha Vantage, Finnhub, Yahoo Finance, and other providers
"""
import os
import logging
import asyncio
import aiohttp
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
from dataclasses import dataclass
from enum import Enum
logger = logging.getLogger(__name__)
class DataProvider(Enum):
    """Supported data providers"""
ALPHA_VANTAGE = "alpha_vantage"
FINNHUB = "finnhub"
YAHOO_FINANCE = "yahoo_finance"
QUANDL = "quandl"
POLYGON = "polygon"
IEX_CLOUD = "iex_cloud"
@dataclass
class APIKey:
    """API key configuration"""
provider: DataProvider
key: str
rate_limit: int # requests per minute
last_request: float = 0.0
request_count: int = 0
class MarketDataAPIService:
    """
    Service for fetching real market data from various providers
    """
    def __init__(self):
        # Rate limiting
        self.rate_limits = {
            DataProvider.ALPHA_VANTAGE: 5, # 5 requests per minute (free tier)
            DataProvider.FINNHUB: 60, # 60 requests per minute (free tier)
            DataProvider.YAHOO_FINANCE: 100, # 100 requests per minute (estimated)
            DataProvider.QUANDL: 50, # 50 requests per day (free tier)
            DataProvider.POLYGON: 5, # 5 requests per minute (free tier)
            DataProvider.IEX_CLOUD: 100 # 100 requests per minute (free tier)
        }
        self.api_keys = self._load_api_keys()
        self.session = None
        self.cache = {}
        self.cache_duration = 300 # 5 minutes
    
    def _load_api_keys(self) -> Dict[DataProvider, APIKey]:
        """Load API keys from environment variables"""
        api_keys = {}
        # Alpha Vantage
        alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if alpha_key:
            api_keys[DataProvider.ALPHA_VANTAGE] = APIKey(
                provider=DataProvider.ALPHA_VANTAGE,
                key=alpha_key,
                rate_limit=self.rate_limits[DataProvider.ALPHA_VANTAGE]
            )
        # Finnhub
        finnhub_key = os.getenv('FINNHUB_API_KEY')
        if finnhub_key:
            api_keys[DataProvider.FINNHUB] = APIKey(
                provider=DataProvider.FINNHUB,
                key=finnhub_key,
                rate_limit=self.rate_limits[DataProvider.FINNHUB]
            )
        # Quandl
        quandl_key = os.getenv('QUANDL_API_KEY')
        if quandl_key:
            api_keys[DataProvider.QUANDL] = APIKey(
                provider=DataProvider.QUANDL,
                key=quandl_key,
                rate_limit=self.rate_limits[DataProvider.QUANDL]
            )
        # Polygon
        polygon_key = os.getenv('POLYGON_API_KEY')
        if polygon_key:
            api_keys[DataProvider.POLYGON] = APIKey(
                provider=DataProvider.POLYGON,
                key=polygon_key,
                rate_limit=self.rate_limits[DataProvider.POLYGON]
            )
        # IEX Cloud
        iex_key = os.getenv('IEX_CLOUD_API_KEY')
        if iex_key:
            api_keys[DataProvider.IEX_CLOUD] = APIKey(
                provider=DataProvider.IEX_CLOUD,
                key=iex_key,
                rate_limit=self.rate_limits[DataProvider.IEX_CLOUD]
            )
        logger.info(f"Loaded {len(api_keys)} API keys")
        return api_keys
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _check_rate_limit(self, provider: DataProvider) -> bool:
        """Check if we can make a request to the provider"""
        if provider not in self.api_keys:
            return False
        api_key = self.api_keys[provider]
        current_time = time.time()
        # Reset counter if a minute has passed
        if current_time - api_key.last_request >= 60:
            api_key.request_count = 0
            api_key.last_request = current_time
        # Check if we're under the rate limit
        if api_key.request_count >= api_key.rate_limit:
            return False
        api_key.request_count += 1
        return True
    
    def _get_cache_key(self, provider: str, symbol: str, data_type: str) -> str:
        """Generate cache key for data"""
        return f"{provider}_{symbol}_{data_type}_{datetime.now().strftime('%Y%m%d_%H')}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        cache_time, _ = self.cache[cache_key]
        return time.time() - cache_time < self.cache_duration
    
    async def get_stock_quote(self, symbol: str, provider: Optional[DataProvider] = None) -> Optional[Dict[str, Any]]:
        """
        Get real-time stock quote
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            provider: Preferred data provider
        Returns:
            Stock quote data or None if error
        """
        try:
            # Initialize session if not already done
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            # Try preferred provider first
            if provider and self._check_rate_limit(provider):
                quote = await self._fetch_quote_from_provider(symbol, provider)
                if quote:
                    return quote
            
            # Try other available providers (only implemented ones)
            implemented_providers = [DataProvider.ALPHA_VANTAGE, DataProvider.FINNHUB, DataProvider.YAHOO_FINANCE, DataProvider.IEX_CLOUD]
            for available_provider in self.api_keys.keys():
                if (available_provider != provider and 
                    available_provider in implemented_providers and 
                    self._check_rate_limit(available_provider)):
                    quote = await self._fetch_quote_from_provider(symbol, available_provider)
                    if quote:
                        return quote
            
            logger.warning(f"No available providers for stock quote: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching stock quote for {symbol}: {e}")
            return None
    async def _fetch_quote_from_provider(self, symbol: str, provider: DataProvider) -> Optional[Dict[str, Any]]:
        """Fetch quote from specific provider"""
        try:
            if provider == DataProvider.ALPHA_VANTAGE:
                return await self._fetch_alpha_vantage_quote(symbol)
elif provider == DataProvider.FINNHUB:
return await self._fetch_finnhub_quote(symbol)
elif provider == DataProvider.YAHOO_FINANCE:
return await self._fetch_yahoo_quote(symbol)
elif provider == DataProvider.IEX_CLOUD:
return await self._fetch_iex_quote(symbol)
else:
logger.warning(f"Provider {provider} not implemented for quotes")
return None
except Exception as e:
logger.error(f"Error fetching quote from {provider} for {symbol}: {e}")
return None
async def _fetch_alpha_vantage_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
"""Fetch quote from Alpha Vantage"""
if not self.session:
return None
api_key = self.api_keys[DataProvider.ALPHA_VANTAGE]
url = f"https://www.alphavantage.co/query"
params = {
'function': 'GLOBAL_QUOTE',
'symbol': symbol,
'apikey': api_key.key
}
# Create SSL context that doesn't verify certificates (for development)
import ssl
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
connector = aiohttp.TCPConnector(ssl=ssl_context)
async with aiohttp.ClientSession(connector=connector) as temp_session:
async with temp_session.get(url, params=params) as response:
if response.status == 200:
data = await response.json()
if 'Global Quote' in data:
quote = data['Global Quote']
return {
'symbol': symbol,
'price': float(quote.get('05. price', 0)),
'change': float(quote.get('09. change', 0)),
'change_percent': float(quote.get('10. change percent', '0%').rstrip('%')),
'volume': int(quote.get('06. volume', 0)),
'market_cap': float(quote.get('07. market cap', 0)),
'provider': 'alpha_vantage',
'timestamp': datetime.now().isoformat()
}
return None
async def _fetch_finnhub_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
"""Fetch quote from Finnhub"""
if not self.session:
return None
api_key = self.api_keys[DataProvider.FINNHUB]
url = f"https://finnhub.io/api/v1/quote"
params = {
'symbol': symbol,
'token': api_key.key
}
# Create SSL context that doesn't verify certificates (for development)
import ssl
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
connector = aiohttp.TCPConnector(ssl=ssl_context)
async with aiohttp.ClientSession(connector=connector) as temp_session:
async with temp_session.get(url, params=params) as response:
if response.status == 200:
data = await response.json()
return {
'symbol': symbol,
'price': data.get('c', 0),
'change': data.get('d', 0),
'change_percent': data.get('dp', 0),
'high': data.get('h', 0),
'low': data.get('l', 0),
'open': data.get('o', 0),
'previous_close': data.get('pc', 0),
'provider': 'finnhub',
'timestamp': datetime.now().isoformat()
}
return None
async def _fetch_yahoo_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
"""Fetch quote from Yahoo Finance"""
try:
import yfinance as yf
ticker = yf.Ticker(symbol)
info = ticker.info
return {
'symbol': symbol,
'price': info.get('regularMarketPrice', 0),
'change': info.get('regularMarketChange', 0),
'change_percent': info.get('regularMarketChangePercent', 0),
'volume': info.get('volume', 0),
'market_cap': info.get('marketCap', 0),
'pe_ratio': info.get('trailingPE', 0),
'dividend_yield': info.get('dividendYield', 0),
'provider': 'yahoo_finance',
'timestamp': datetime.now().isoformat()
}
except ImportError:
logger.warning("yfinance not available for Yahoo Finance quotes")
return None
except Exception as e:
logger.error(f"Error fetching Yahoo Finance quote: {e}")
return None
async def _fetch_iex_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
"""Fetch quote from IEX Cloud"""
if not self.session:
return None
api_key = self.api_keys[DataProvider.IEX_CLOUD]
url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
params = {
'token': api_key.key
}
async with self.session.get(url, params=params) as response:
if response.status == 200:
data = await response.json()
return {
'symbol': symbol,
'price': data.get('latestPrice', 0),
'change': data.get('change', 0),
'change_percent': data.get('changePercent', 0),
'volume': data.get('volume', 0),
'market_cap': data.get('marketCap', 0),
'pe_ratio': data.get('peRatio', 0),
'dividend_yield': data.get('ytdChange', 0),
'provider': 'iex_cloud',
'timestamp': datetime.now().isoformat()
}
return None
async def get_historical_data(self, symbol: str, period: str = '1y', 
provider: Optional[DataProvider] = None) -> Optional[pd.DataFrame]:
"""
Get historical price data
Args:
symbol: Stock symbol
period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
provider: Preferred data provider
Returns:
Historical data DataFrame or None if error
"""
try:
# Try Yahoo Finance first (most reliable for historical data)
if provider == DataProvider.YAHOO_FINANCE or provider is None:
try:
import yfinance as yf
ticker = yf.Ticker(symbol)
hist = ticker.history(period=period)
if not hist.empty:
return hist
except ImportError:
logger.warning("yfinance not available")
except Exception as e:
logger.warning(f"Yahoo Finance failed: {e}")
# Try other providers
for available_provider in self.api_keys.keys():
if available_provider != provider and self._check_rate_limit(available_provider):
hist = await self._fetch_historical_from_provider(symbol, period, available_provider)
if hist is not None and not hist.empty:
return hist
logger.warning(f"No available providers for historical data: {symbol}")
return None
except Exception as e:
logger.error(f"Error fetching historical data for {symbol}: {e}")
return None
async def _fetch_historical_from_provider(self, symbol: str, period: str, 
provider: DataProvider) -> Optional[pd.DataFrame]:
"""Fetch historical data from specific provider"""
try:
if provider == DataProvider.ALPHA_VANTAGE:
return await self._fetch_alpha_vantage_historical(symbol, period)
elif provider == DataProvider.FINNHUB:
return await self._fetch_finnhub_historical(symbol, period)
else:
logger.warning(f"Provider {provider} not implemented for historical data")
return None
except Exception as e:
logger.error(f"Error fetching historical data from {provider} for {symbol}: {e}")
return None
async def _fetch_alpha_vantage_historical(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
"""Fetch historical data from Alpha Vantage"""
if not self.session:
return None
api_key = self.api_keys[DataProvider.ALPHA_VANTAGE]
url = f"https://www.alphavantage.co/query"
params = {
'function': 'TIME_SERIES_DAILY',
'symbol': symbol,
'apikey': api_key.key,
'outputsize': 'full'
}
async with self.session.get(url, params=params) as response:
if response.status == 200:
data = await response.json()
if 'Time Series (Daily)' in data:
time_series = data['Time Series (Daily)']
# Convert to DataFrame
df = pd.DataFrame.from_dict(time_series, orient='index')
df.index = pd.to_datetime(df.index)
df.columns = ['open', 'high', 'low', 'close', 'volume']
# Convert to numeric
for col in df.columns:
df[col] = pd.to_numeric(df[col])
# Sort by date
df = df.sort_index()
return df
return None
async def _fetch_finnhub_historical(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
"""Fetch historical data from Finnhub"""
if not self.session:
return None
api_key = self.api_keys[DataProvider.FINNHUB]
# Calculate date range
end_date = datetime.now()
if period == '1y':
start_date = end_date - timedelta(days=365)
elif period == '6mo':
start_date = end_date - timedelta(days=180)
elif period == '3mo':
start_date = end_date - timedelta(days=90)
elif period == '1mo':
start_date = end_date - timedelta(days=30)
else:
start_date = end_date - timedelta(days=365) # Default to 1 year
url = f"https://finnhub.io/api/v1/stock/candle"
params = {
'symbol': symbol,
'resolution': 'D', # Daily
'from': int(start_date.timestamp()),
'to': int(end_date.timestamp()),
'token': api_key.key
}
async with self.session.get(url, params=params) as response:
if response.status == 200:
data = await response.json()
if data['s'] == 'ok':
# Convert to DataFrame
df = pd.DataFrame({
'open': data['o'],
'high': data['h'],
'low': data['l'],
'close': data['c'],
'volume': data['v']
}, index=pd.to_datetime(data['t'], unit='s'))
return df
return None
async def get_market_overview(self) -> Optional[Dict[str, Any]]:
"""Get overall market overview"""
try:
# Get major indices
indices = ['^GSPC', '^DJI', '^IXIC', '^VIX'] # S&P 500, Dow, NASDAQ, VIX
market_data = {}
for index in indices:
quote = await self.get_stock_quote(index)
if quote:
market_data[index] = quote
# Calculate market sentiment
if market_data:
total_change = sum(quote['change_percent'] for quote in market_data.values() if 'change_percent' in quote)
avg_change = total_change / len(market_data)
if avg_change > 1:
sentiment = 'bullish'
elif avg_change < -1:
sentiment = 'bearish'
else:
sentiment = 'neutral'
return {
'indices': market_data,
'sentimentDescription': sentiment,
'average_change': avg_change,
'timestamp': datetime.now().isoformat()
}
return None
except Exception as e:
logger.error(f"Error fetching market overview: {e}")
return None
async def get_economic_indicators(self) -> Optional[Dict[str, Any]]:
"""Get key economic indicators"""
try:
indicators = {}
# Try to get economic data from available providers
for provider in self.api_keys.keys():
if provider == DataProvider.ALPHA_VANTAGE and self._check_rate_limit(provider):
# Get GDP data
gdp_data = await self._fetch_alpha_vantage_economic('REAL_GDP', provider)
if gdp_data:
indicators['gdp'] = gdp_data
elif provider == DataProvider.FINNHUB and self._check_rate_limit(provider):
# Get economic calendar
calendar = await self._fetch_finnhub_economic_calendar(provider)
if calendar:
indicators['economic_calendar'] = calendar
return indicators if indicators else None
except Exception as e:
logger.error(f"Error fetching economic indicators: {e}")
return None
async def _fetch_alpha_vantage_economic(self, indicator: str, provider: DataProvider) -> Optional[Dict[str, Any]]:
"""Fetch economic data from Alpha Vantage"""
if not self.session:
return None
api_key = self.api_keys[provider]
url = f"https://www.alphavantage.co/query"
params = {
'function': indicator,
'apikey': api_key.key
}
async with self.session.get(url, params=params) as response:
if response.status == 200:
data = await response.json()
return data
return None
async def _fetch_finnhub_economic_calendar(self, provider: DataProvider) -> Optional[List[Dict[str, Any]]]:
"""Fetch economic calendar from Finnhub"""
if not self.session:
return None
api_key = self.api_keys[provider]
url = f"https://finnhub.io/api/v1/calendar/economic"
params = {
'token': api_key.key
}
async with self.session.get(url, params=params) as response:
if response.status == 200:
data = await response.json()
return data.get('economicCalendar', [])
return None
def get_available_providers(self) -> List[DataProvider]:
"""Get list of available data providers"""
return list(self.api_keys.keys())
def get_provider_status(self) -> Dict[str, Any]:
"""Get status of all data providers"""
status = {}
for provider, api_key in self.api_keys.items():
status[provider.value] = {
'available': True,
'rate_limit': api_key.rate_limit,
'requests_this_minute': api_key.request_count,
'last_request': api_key.last_request
}
return status
def set_cache_duration(self, seconds: int):
"""Set cache duration in seconds"""
self.cache_duration = seconds
def clear_cache(self):
"""Clear all cached data"""
self.cache.clear()
def get_cache_stats(self) -> Dict[str, Any]:
"""Get cache statistics"""
return {
'cache_size': len(self.cache),
'cache_duration': self.cache_duration,
'cache_keys': list(self.cache.keys())
}
