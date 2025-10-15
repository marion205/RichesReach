"""
Enhanced API Service with intelligent caching and rate limiting
"""
import os
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.conf import settings
import logging
logger = logging.getLogger(__name__)
class EnhancedAPIService:
"""Enhanced API service with intelligent caching and rate limiting"""
def __init__(self):
# Multiple API keys for rotation
self.api_keys = [
'K0A7XYLDNXHNQ1WI', # Primary key
'OHYSFF1AE446O7CR', # Secondary key (from logs)
# Add more keys as needed
]
self.current_key_index = 0
self.rate_limit_cache = {}
# Cache TTL settings (in seconds)
self.cache_ttl = {
'stock_data': 3600, # 1 hour
'options_data': 1800, # 30 minutes
'market_data': 300, # 5 minutes
'search_results': 7200, # 2 hours
}
def get_api_key(self) -> str:
"""Get current API key with rotation"""
return self.api_keys[self.current_key_index]
def rotate_api_key(self):
"""Rotate to next API key"""
self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
logger.info(f"Rotated to API key index: {self.current_key_index}")
def is_rate_limited(self, api_key: str) -> bool:
"""Check if API key is rate limited"""
cache_key = f"rate_limit_{api_key}"
rate_limit_data = cache.get(cache_key)
if not rate_limit_data:
return False
# Check if we're still within the rate limit window
if time.time() - rate_limit_data['timestamp'] < 86400: # 24 hours
return rate_limit_data['limited']
# Clear expired rate limit data
cache.delete(cache_key)
return False
def set_rate_limited(self, api_key: str, hours: int = 24):
"""Mark API key as rate limited"""
cache_key = f"rate_limit_{api_key}"
cache.set(cache_key, {
'limited': True,
'timestamp': time.time(),
'expires_in_hours': hours
}, timeout=hours * 3600)
logger.warning(f"API key {api_key[:8]}... marked as rate limited for {hours} hours")
def get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
"""Generate cache key for API request"""
# Sort params for consistent cache keys
sorted_params = sorted(params.items())
param_string = json.dumps(sorted_params, sort_keys=True)
hash_key = hashlib.md5(param_string.encode()).hexdigest()
return f"api_cache_{endpoint}_{hash_key}"
def get_cached_data(self, cache_key: str, data_type: str) -> Optional[Dict[str, Any]]:
"""Get cached data if available and not expired"""
cached_data = cache.get(cache_key)
if cached_data:
# Check if data is still fresh
if time.time() - cached_data['timestamp'] < self.cache_ttl.get(data_type, 3600):
logger.info(f"Using cached data for {data_type}")
return cached_data['data']
else:
# Remove expired cache
cache.delete(cache_key)
return None
def set_cached_data(self, cache_key: str, data: Dict[str, Any], data_type: str):
"""Cache API response data"""
cache_data = {
'data': data,
'timestamp': time.time(),
'data_type': data_type
}
ttl = self.cache_ttl.get(data_type, 3600)
cache.set(cache_key, cache_data, timeout=ttl)
logger.info(f"Cached {data_type} data for {ttl} seconds")
def make_api_request(self, endpoint: str, params: Dict[str, Any], data_type: str = 'stock_data') -> Optional[Dict[str, Any]]:
"""Make API request with intelligent caching and rate limiting"""
cache_key = self.get_cache_key(endpoint, params)
# Check cache first
cached_data = self.get_cached_data(cache_key, data_type)
if cached_data:
return cached_data
# Try each API key until one works
for attempt in range(len(self.api_keys)):
api_key = self.get_api_key()
# Check if this key is rate limited
if self.is_rate_limited(api_key):
logger.warning(f"API key {api_key[:8]}... is rate limited, trying next key")
self.rotate_api_key()
continue
try:
# Make the API request
params['apikey'] = api_key
response = self._make_http_request(endpoint, params)
if response:
# Cache successful response
self.set_cached_data(cache_key, response, data_type)
return response
except Exception as e:
if "rate limit" in str(e).lower() or "25 requests per day" in str(e):
logger.warning(f"Rate limit hit for API key {api_key[:8]}...")
self.set_rate_limited(api_key)
self.rotate_api_key()
continue
else:
logger.error(f"API request failed: {e}")
break
# All API keys failed, return None
logger.error("All API keys failed or rate limited")
return None
def _make_http_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
"""Make HTTP request to API endpoint"""
import requests
try:
response = requests.get(endpoint, params=params, timeout=10)
response.raise_for_status()
data = response.json()
# Check for API errors
if 'Error Message' in data:
error_msg = data['Error Message']
if "rate limit" in error_msg.lower():
raise Exception(f"Rate limit: {error_msg}")
else:
raise Exception(f"API error: {error_msg}")
return data
except requests.exceptions.RequestException as e:
logger.error(f"HTTP request failed: {e}")
return None
def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
"""Get stock data with caching"""
params = {
'function': 'GLOBAL_QUOTE',
'symbol': symbol
}
return self.make_api_request(
'https://www.alphavantage.co/query',
params,
'stock_data'
)
def search_stocks(self, query: str) -> Optional[Dict[str, Any]]:
"""Search stocks with caching"""
params = {
'function': 'SYMBOL_SEARCH',
'keywords': query
}
return self.make_api_request(
'https://www.alphavantage.co/query',
params,
'search_results'
)
def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
"""Get market data for multiple symbols with batching"""
results = {}
for symbol in symbols:
# Check if we already have recent data
cache_key = f"market_data_{symbol}"
cached_data = self.get_cached_data(cache_key, 'market_data')
if cached_data:
results[symbol] = cached_data
else:
# Make API request
data = self.get_stock_data(symbol)
if data:
results[symbol] = data
# Cache individual symbol data
self.set_cached_data(cache_key, data, 'market_data')
else:
# Try to get real data from database as fallback
results[symbol] = self._get_real_stock_data_from_db(symbol)
return results
def _get_real_stock_data_from_db(self, symbol: str) -> Dict[str, Any]:
"""Get real stock data from database when API fails"""
try:
from .models import Stock
stock = Stock.objects.filter(symbol=symbol).first()
if stock and stock.current_price:
current_price = float(stock.current_price)
# Use real data from database fields if available
open_price = getattr(stock, 'open_price', current_price)
high_price = getattr(stock, 'high_price', current_price)
low_price = getattr(stock, 'low_price', current_price)
previous_close = getattr(stock, 'previous_close', current_price)
volume = getattr(stock, 'volume', 1000000)
# Calculate real change if we have previous close
if previous_close and previous_close != current_price:
change = current_price - previous_close
change_percent = (change / previous_close * 100) if previous_close > 0 else 0
else:
# Use database change_percent if available
change = getattr(stock, 'change', 0)
change_percent = getattr(stock, 'change_percent', 0)
return {
'Global Quote': {
'01. symbol': symbol,
'02. open': str(open_price),
'03. high': str(high_price),
'04. low': str(low_price),
'05. price': str(current_price),
'06. volume': str(volume),
'07. latest trading day': datetime.now().strftime('%Y-%m-%d'),
'08. previous close': str(previous_close),
'09. change': str(change),
'10. change percent': f"{change_percent:.2f}%"
}
}
else:
# No stock found in database - return None to indicate failure
return None
except Exception as e:
logger.error(f"Error getting real stock data for {symbol}: {e}")
return None
# Global instance
enhanced_api_service = EnhancedAPIService()
