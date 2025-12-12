"""
Enhanced Stock Service with Real-Time Price Updates
Integrates multiple data sources for accurate, up-to-date stock prices
"""
from django.db import connection
from datetime import datetime
import requests
try:
    import yfinance as yf
except ImportError:
    yf = None
import os
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.core.cache import cache
from .models import Stock
from .market_data_api_service import MarketDataAPIService, DataProvider
logger = logging.getLogger(__name__)


class EnhancedStockService:
    """
    Enhanced stock service with real-time price updates
    Uses multiple data sources for reliability and accuracy
    """

    def __init__(self):
        self.market_data_service = MarketDataAPIService()
        self.cache_timeout = 300  # 5 minutes cache
        # No hardcoded fallback prices - always use real data from database
        self.fallback_prices = {}

    async def get_real_time_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time stock price with fallback mechanisms
        Args:
        symbol: Stock symbol (e.g., 'AAPL')
        Returns:
        Stock price data or None if error
        """
        try:

            # Try cache first
            cached_price = self._get_cached_price(symbol)

            if cached_price and not self._is_cache_expired(cached_price):
                logger.info(f"Using cached price for {symbol}: ${cached_price['price']}")
                return cached_price

            # Try to get real-time price from market data APIs

            logger.info(f"Fetching real-time price for {symbol}")

            # Use the unified MarketDataAPIService (prioritizes Finnhub, then Alpha Vantage)

            try:
                price_data = await self.market_data_service.get_stock_quote(symbol)
                if price_data and price_data.get('price', 0) > 0:
                    # Convert to our expected format
                    formatted_data = {
                        'symbol': symbol,
                        'price': price_data['price'],
                        'change': price_data.get('change', 0),
                        'change_percent': f"{price_data.get('change_percent', 0):.2f}%",
                        'volume': price_data.get('volume', 0),
                        'high': price_data.get('high', 0),
                        'low': price_data.get('low', 0),
                        'open': price_data.get('open', 0),
                        'source': price_data.get('provider', 'api'),
                        'verified': True,
                        'last_updated': timezone.now().isoformat()
                    }
                    self._cache_price(symbol, formatted_data)
                    logger.info(
                        f"API service price for {symbol}: ${formatted_data['price']} from {formatted_data['source']}")
                    
                    # Ingest price into regime oracle (non-blocking)
                    try:
                        from .regime_price_feed import regime_price_feed
                        regime_price_feed.ingest_stock_price(
                            symbol,
                            formatted_data['price'],
                            timezone.now()
                        )
                    except Exception as e:
                        logger.debug(f"Could not ingest price to regime oracle: {e}")
                    
                    return formatted_data
            except Exception as e:
                logger.warning(f"Market data API service failed for {symbol}: {e}")
            # Try database fallback
            db_price = self._get_database_price(symbol)

            if db_price and db_price.get('price', 0) > 0:
                logger.info(f"Using database price for {symbol}: ${db_price['price']}")
                return db_price

            # Use fallback price if available
            if symbol in self.fallback_prices:
                fallback_price = {
                    'symbol': symbol,
                    'price': self.fallback_prices[symbol],
                    'change': 0.0,
                    'change_percent': '0%',
                    'volume': 0,
                    'source': 'fallback',
                    'verified': False,
                    'last_updated': timezone.now().isoformat()
                }
                logger.warning(f"Using fallback price for {symbol}: ${fallback_price['price']}")
                return fallback_price
            logger.error(f"No price data available for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error getting real-time price for {symbol}: {e}")
            return None

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get real-time prices for multiple symbols
        Args:
        symbols: List of stock symbols
        Returns:
        Dictionary mapping symbols to price data
        """
        try:
            results = {}
            # Process symbols in batches to avoid overwhelming APIs
            batch_size = 5
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                # Create tasks for batch
                tasks = [self.get_real_time_price(symbol) for symbol in batch]
                # Execute batch concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                # Process results
                for symbol, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error getting price for {symbol}: {result}")
                        results[symbol] = None
                    elif result:
                        results[symbol] = result
                    else:
                        results[symbol] = None
                # Small delay between batches to respect rate limits
                if i + batch_size < len(symbols):
                    await asyncio.sleep(0.5)
            return results
        except Exception as e:
            logger.error(f"Error getting multiple prices: {e}")
            return {}

    async def _fetch_yahoo_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if 'regularMarketPrice' in info and info['regularMarketPrice']:
                return {
                    'symbol': symbol,
                    'price': float(info['regularMarketPrice']),
                    'change': float(info.get('regularMarketChange', 0)),
                    'change_percent': f"{info.get('regularMarketChangePercent', 0):.2f}%",
                    'volume': int(info.get('volume', 0)),
                    'high': float(info.get('regularMarketDayHigh', 0)),
                    'low': float(info.get('regularMarketDayLow', 0)),
                    'open': float(info.get('regularMarketOpen', 0)),
                    'previous_close': float(info.get('regularMarketPreviousClose', 0)),
                    'market_cap': info.get('marketCap'),
                    'pe_ratio': info.get('trailingPE'),
                    'dividend_yield': info.get('dividendYield'),
                    'source': 'yahoo_finance',
                    'verified': True,
                    'last_updated': timezone.now().isoformat()
                }
            return None
        except ImportError:
            logger.warning("yfinance not available")
            return None
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None

    async def _fetch_alpha_vantage_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from Alpha Vantage"""
        try:
            # Check if we have API key
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            if not api_key:
                return None
            import requests
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': api_key
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return None
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit for {symbol}: {data['Note']}")
                return None
            if 'Global Quote' not in data:
                return None
            quote = data['Global Quote']
            return {
                'symbol': quote.get('01. symbol'),
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%'),
                'volume': int(quote.get('06. volume', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'open': float(quote.get('02. open', 0)),
                'previous_close': float(quote.get('08. previous close', 0)),
                'source': 'alpha_vantage',
                'verified': True,
                'last_updated': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
            return None

    async def _fetch_finnhub_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from Finnhub"""
        try:
            # Check if we have API key
            api_key = os.getenv('FINNHUB_API_KEY')
            if not api_key:
                return None
            import requests
            url = "https://finnhub.io/api/v1/quote"
            params = {
                'symbol': symbol,
                'token': api_key
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'c' in data and data['c'] > 0:  # Current price
                return {
                    'symbol': symbol,
                    'price': float(data['c']),
                    'change': float(data.get('d', 0)),
                    'change_percent': f"{data.get('dp', 0):.2f}%",
                    'high': float(data.get('h', 0)),
                    'low': float(data.get('l', 0)),
                    'open': float(data.get('o', 0)),
                    'previous_close': float(data.get('pc', 0)),
                    'source': 'finnhub',
                    'verified': True,
                    'last_updated': timezone.now().isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"Finnhub error for {symbol}: {e}")
            return None

    def _get_database_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price from database"""
        try:
            stock = Stock.objects.filter(symbol=symbol).first()
            if stock and stock.current_price:
                return {
                    'symbol': symbol,
                    'price': float(stock.current_price),
                    'change': 0.0,
                    'change_percent': '0%',
                    'volume': 0,
                    'source': 'database',
                    'verified': False,
                    'last_updated': stock.last_updated.isoformat() if stock.last_updated else timezone.now().isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"Database error for {symbol}: {e}")
            return None

    def _get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price from cache"""
        try:
            cache_key = f"stock_price:{symbol.upper()}"
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Cache error for {symbol}: {e}")
            return None

    def _cache_price(self, symbol: str, price_data: Dict[str, Any]) -> bool:
        """Cache price data"""
        try:
            cache_key = f"stock_price:{symbol.upper()}"
            cache.set(cache_key, price_data, self.cache_timeout)
            return True
        except Exception as e:
            logger.error(f"Cache set error for {symbol}: {e}")
            return False

    def _is_cache_expired(self, price_data: Dict[str, Any]) -> bool:
        """Check if cached price is expired"""
        try:
            last_updated = price_data.get('last_updated')
            if not last_updated:
                return True
            # Parse ISO timestamp
            from datetime import datetime
            if isinstance(last_updated, str):
                # Handle timezone-aware and timezone-naive timestamps
                if 'Z' in last_updated:
                    last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                elif '+' in last_updated or '-' in last_updated[-6:]:  # Has timezone
                    last_updated = datetime.fromisoformat(last_updated)
                else:  # No timezone, assume UTC
                    last_updated = datetime.fromisoformat(last_updated + '+00:00')
            # Make both timestamps timezone-aware
            if last_updated.tzinfo is None:
                last_updated = timezone.make_aware(last_updated)
            # Check if cache is expired (5 minutes)
            age = timezone.now() - last_updated
            return age.total_seconds() > self.cache_timeout
        except Exception as e:
            logger.error(f"Cache expiration check error: {e}")
            return True

    def update_stock_price_in_database(self, symbol: str, price_data: Dict[str, Any]) -> bool:
        """
        Update stock price in database
        Args:
        symbol: Stock symbol
        price_data: Price data dictionary
        Returns:
        True if update successful
        """
        try:
            stock = Stock.objects.filter(symbol=symbol).first()
            if stock:
                stock.current_price = price_data['price']
                stock.last_updated = timezone.now()
                stock.save()
                logger.info(f"Updated database price for {symbol}: ${price_data['price']}")
                return True
            else:
                logger.warning(f"Stock {symbol} not found in database")
                return False
        except Exception as e:
            logger.error(f"Error updating database price for {symbol}: {e}")
            return False

    async def get_price_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive price summary for a symbol
        Args:
        symbol: Stock symbol
        Returns:
        Price summary dictionary
        """
        try:
            # Get current price
            current_price = self._get_cached_price(symbol)
            # Get database price (async-safe)
            db_price = None
            try:
                from django.db import connection
                if connection.connection is None:
                    # Database not connected, skip
                    pass
                else:
                    db_price = self._get_database_price(symbol)
            except Exception:
                # Database access failed, skip
                pass
            # Get fallback price
            fallback_price = self.fallback_prices.get(symbol, 0)
            summary = {
                'symbol': symbol,
                'current_price': current_price,
                'database_price': db_price,
                'fallback_price': fallback_price,
                'price_source': current_price.get('source') if current_price else 'unknown',
                'last_updated': current_price.get('last_updated') if current_price else 'unknown',
                'is_real_time': current_price and current_price.get('verified', False),
                'cache_status': 'fresh' if current_price and not self._is_cache_expired(current_price) else 'expired'
            }
            return summary
        except Exception as e:
            logger.error(f"Error getting price summary for {symbol}: {e}")
            return {'error': str(e)}

    def refresh_all_prices(self) -> Dict[str, bool]:
        """
        Refresh prices for all stocks in database
        Returns:
        Dictionary mapping symbols to refresh success status
        """
        try:
            stocks = Stock.objects.all()
            results = {}

            async def refresh_stock_prices():
                symbols = [stock.symbol for stock in stocks]
                prices = await self.get_multiple_prices(symbols)
                for symbol, price_data in prices.items():
                    if price_data:
                        success = self.update_stock_price_in_database(symbol, price_data)
                        results[symbol] = success
                    else:
                        results[symbol] = False

            # Run async refresh
            asyncio.run(refresh_stock_prices())
            logger.info(f"Refreshed prices for {len(results)} stocks")
            return results
        except Exception as e:
            logger.error(f"Error refreshing all prices: {e}")
            return {}


# Create global instance
enhanced_stock_service = EnhancedStockService()
