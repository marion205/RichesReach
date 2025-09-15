"""
Simple Market Data Service for Real Financial Data
Integrates with Alpha Vantage and Finnhub APIs
"""
import os
import logging
import asyncio
import aiohttp
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class SimpleMarketDataService:
    """
    Simple service for fetching real market data from Alpha Vantage and Finnhub
    """
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.session = None
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time stock quote from available APIs
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
        Returns:
            Stock quote data or None if error
        """
        try:
            # Try Finnhub first (more reliable)
            if self.finnhub_key:
                try:
                    quote = await self._fetch_finnhub_quote(symbol)
                    if quote:
                        logger.info(f"Got Finnhub data for {symbol}: ${quote['price']}")
                        return quote
                except Exception as e:
                    logger.warning(f"Finnhub failed for {symbol}: {e}")
            
            # Try Alpha Vantage as fallback
            if self.alpha_vantage_key:
                try:
                    quote = await self._fetch_alpha_vantage_quote(symbol)
                    if quote:
                        logger.info(f"Got Alpha Vantage data for {symbol}: ${quote['price']}")
                        return quote
                except Exception as e:
                    logger.warning(f"Alpha Vantage failed for {symbol}: {e}")
            
            logger.warning(f"No API data available for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching stock quote for {symbol}: {e}")
            return None
    
    async def _fetch_alpha_vantage_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quote from Alpha Vantage"""
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }
        
        try:
            # Create SSL context that doesn't verify certificates (for development)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            # Create a new session for this request
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'Global Quote' in data and data['Global Quote']:
                            quote = data['Global Quote']
                            return {
                                'symbol': symbol,
                                'price': float(quote.get('05. price', 0)),
                                'change': float(quote.get('09. change', 0)),
                                'change_percent': float(quote.get('10. change percent', '0%').rstrip('%')),
                                'volume': int(quote.get('06. volume', 0)),
                                'high': float(quote.get('03. high', 0)),
                                'low': float(quote.get('04. low', 0)),
                                'open': float(quote.get('02. open', 0)),
                                'previous_close': float(quote.get('08. previous close', 0)),
                                'provider': 'alpha_vantage',
                                'timestamp': datetime.now().isoformat()
                            }
        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {e}")
        
        return None
    
    async def _fetch_finnhub_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quote from Finnhub"""
        url = f"https://finnhub.io/api/v1/quote"
        params = {
            'symbol': symbol,
            'token': self.finnhub_key
        }
        
        try:
            # Create SSL context that doesn't verify certificates (for development)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            # Create a new session for this request
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('c', 0) > 0:  # Check if we have a valid price
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
        except Exception as e:
            logger.error(f"Finnhub API error for {symbol}: {e}")
        
        return None
    
    def get_available_providers(self) -> List[str]:
        """Get list of available data providers"""
        providers = []
        if self.alpha_vantage_key:
            providers.append('alpha_vantage')
        if self.finnhub_key:
            providers.append('finnhub')
        return providers
