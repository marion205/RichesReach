# core/stock_service.py
import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import redis
from celery import shared_task
import asyncio
import aiohttp
from dataclasses import dataclass
from enum import Enum
from .models import Stock

logger = logging.getLogger(__name__)

class RateLimitStatus(Enum):
    OK = "ok"
    RATE_LIMITED = "rate_limited"
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"

@dataclass
class RateLimitInfo:
    status: RateLimitStatus
    remaining_requests: int
    reset_time: datetime
    retry_after: Optional[int] = None

class StockDataCache:
    """Redis-based cache for stock data with TTL management"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.config = settings.STOCK_ANALYSIS_CONFIG['CACHE_TIMEOUT']
    
    def get_cache_key(self, data_type: str, symbol: str) -> str:
        """Generate cache key for stock data"""
        return f"stock:{data_type}:{symbol.upper()}"
    
    def get(self, data_type: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached stock data"""
        try:
            key = self.get_cache_key(data_type, symbol)
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def set(self, data_type: str, symbol: str, data: Dict[str, Any]) -> bool:
        """Set cached stock data with appropriate TTL"""
        try:
            key = self.get_cache_key(data_type, symbol)
            ttl = self.config.get(data_type.upper(), 300)
            self.redis_client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def invalidate(self, data_type: str, symbol: str) -> bool:
        """Invalidate cached data"""
        try:
            key = self.get_cache_key(data_type, symbol)
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return False

class RateLimiter:
    """Rate limiting for Alpha Vantage API"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.config = settings.STOCK_ANALYSIS_CONFIG['RATE_LIMITS']['ALPHA_VANTAGE']
    
    def check_rate_limit(self) -> RateLimitInfo:
        """Check current rate limit status"""
        now = timezone.now()
        minute_key = f"rate_limit:minute:{now.strftime('%Y%m%d%H%M')}"
        day_key = f"rate_limit:day:{now.strftime('%Y%m%d')}"
        
        try:
            # Check minute limit
            minute_requests = int(self.redis_client.get(minute_key) or 0)
            day_requests = int(self.redis_client.get(day_key) or 0)
            
            if minute_requests >= self.config['REQUESTS_PER_MINUTE']:
                return RateLimitInfo(
                    status=RateLimitStatus.RATE_LIMITED,
                    remaining_requests=0,
                    reset_time=now.replace(second=0, microsecond=0) + timedelta(minutes=1),
                    retry_after=60 - now.second
                )
            
            if day_requests >= self.config['REQUESTS_PER_DAY']:
                return RateLimitInfo(
                    status=RateLimitStatus.DAILY_LIMIT_EXCEEDED,
                    remaining_requests=0,
                    reset_time=now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                )
            
            remaining = min(
                self.config['REQUESTS_PER_MINUTE'] - minute_requests,
                self.config['REQUESTS_PER_DAY'] - day_requests
            )
            
            return RateLimitInfo(
                status=RateLimitStatus.OK,
                remaining_requests=remaining,
                reset_time=now.replace(second=0, microsecond=0) + timedelta(minutes=1)
            )
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Default to OK if Redis fails
            return RateLimitInfo(
                status=RateLimitStatus.OK,
                remaining_requests=self.config['REQUESTS_PER_MINUTE'],
                reset_time=now + timedelta(minutes=1)
            )
    
    def increment_usage(self) -> bool:
        """Increment API usage counters"""
        now = timezone.now()
        minute_key = f"rate_limit:minute:{now.strftime('%Y%m%d%H%M')}"
        day_key = f"rate_limit:day:{now.strftime('%Y%m%d')}"
        
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)  # Expire in 1 minute
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)  # Expire in 24 hours
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Rate limit increment error: {e}")
            return False

class AdvancedStockService:
    """Enhanced stock service with caching, rate limiting, and batch processing"""
    
    def __init__(self):
        self.cache = StockDataCache()
        self.rate_limiter = RateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RichesReach-Django/2.0'
        })
        self.config = settings.STOCK_ANALYSIS_CONFIG
    
    def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with rate limiting"""
        # Check rate limit
        rate_info = self.rate_limiter.check_rate_limit()
        
        if rate_info.status != RateLimitStatus.OK:
            logger.warning(f"Rate limited: {rate_info.status}")
            return None
        
        try:
            # Make request
            response = self.session.get(
                f"https://www.alphavantage.co/query",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            # Increment usage counter
            self.rate_limiter.increment_usage()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_stock_quote(self, symbol: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get stock quote with caching"""
        if use_cache:
            cached_data = self.cache.get('QUOTE_DATA', symbol)
            if cached_data:
                logger.info(f"Cache hit for quote: {symbol}")
                return cached_data
        
        # Fetch from API
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': 'K0A7XYLDNXHNQ1WI'  # Your API key
        }
        
        data = self._make_api_request('quote', params)
        if data and 'Global Quote' in data:
            # Cache the result
            self.cache.set('QUOTE_DATA', symbol, data)
            return data
        
        return None
    
    def get_company_overview(self, symbol: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get company overview with caching"""
        if use_cache:
            cached_data = self.cache.get('OVERVIEW_DATA', symbol)
            if cached_data:
                logger.info(f"Cache hit for overview: {symbol}")
                return cached_data
        
        # Fetch from API
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': 'K0A7XYLDNXHNQ1WI'
        }
        
        data = self._make_api_request('overview', params)
        if data and 'Symbol' in data:
            # Cache the result
            self.cache.set('OVERVIEW_DATA', symbol, data)
            return data
        
        return None
    
    def get_historical_data(self, symbol: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get historical data with caching"""
        if use_cache:
            cached_data = self.cache.get('HISTORICAL_DATA', symbol)
            if cached_data:
                logger.info(f"Cache hit for historical: {symbol}")
                return cached_data
        
        # Fetch from API
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': 'K0A7XYLDNXHNQ1WI'
        }
        
        data = self._make_api_request('historical', params)
        if data and 'Time Series (Daily)' in data:
            # Cache the result
            self.cache.set('HISTORICAL_DATA', symbol, data)
            return data
        
        return None
    
    def analyze_stock(self, symbol: str, include_technical: bool = True, include_fundamental: bool = True) -> Optional[Dict[str, Any]]:
        """Analyze stock with caching"""
        cache_key = f"ANALYSIS_RESULT:{symbol}:{include_technical}:{include_fundamental}"
        
        # Check cache first
        cached_analysis = self.cache.get('ANALYSIS_RESULT', cache_key)
        if cached_analysis:
            logger.info(f"Cache hit for analysis: {symbol}")
            return cached_analysis
        
        # Fetch data and analyze
        quote_data = self.get_stock_quote(symbol)
        overview_data = self.get_company_overview(symbol)
        
        if not quote_data or not overview_data:
            return None
        
        # Create analysis (simplified for now)
        analysis = {
            'symbol': symbol,
            'timestamp': timezone.now().isoformat(),
            'quote_data': quote_data,
            'overview_data': overview_data,
            'analysis_type': {
                'technical': include_technical,
                'fundamental': include_fundamental
            }
        }
        
        # Cache the analysis
        self.cache.set('ANALYSIS_RESULT', cache_key, analysis)
        
        return analysis
    
    def batch_analyze_stocks(self, symbols: List[str], include_technical: bool = True, include_fundamental: bool = True) -> Dict[str, Any]:
        """Batch analyze multiple stocks"""
        max_batch_size = self.config['BATCH_PROCESSING']['MAX_STOCKS_PER_BATCH']
        batch_delay = self.config['BATCH_PROCESSING']['BATCH_DELAY_SECONDS']
        
        results = {}
        batches = [symbols[i:i + max_batch_size] for i in range(0, len(symbols), max_batch_size)]
        
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)}: {batch}")
            
            for symbol in batch:
                try:
                    analysis = self.analyze_stock(symbol, include_technical, include_fundamental)
                    results[symbol] = analysis
                    
                    # Rate limiting delay between requests
                    time.sleep(batch_delay)
                    
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    results[symbol] = {'error': str(e)}
            
            # Delay between batches
            if i < len(batches) - 1:
                time.sleep(batch_delay * 2)
        
        return results

# Global instances
stock_cache = StockDataCache()
rate_limiter = RateLimiter()
advanced_stock_service = AdvancedStockService()

# Legacy compatibility
def get_stock_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Legacy function for backward compatibility"""
    return advanced_stock_service.get_stock_quote(symbol)

def analyze_stock_with_rust(symbol: str, include_technical: bool = True, include_fundamental: bool = True) -> Optional[Dict[str, Any]]:
    """Legacy function for backward compatibility"""
    return advanced_stock_service.analyze_stock(symbol, include_technical, include_fundamental)

# Celery tasks for background processing
@shared_task
def background_stock_analysis(symbol: str, include_technical: bool = True, include_fundamental: bool = True) -> Dict[str, Any]:
    """Background task for stock analysis"""
    try:
        result = advanced_stock_service.analyze_stock(symbol, include_technical, include_fundamental)
        return {'success': True, 'data': result}
    except Exception as e:
        logger.error(f"Background analysis failed for {symbol}: {e}")
        return {'success': False, 'error': str(e)}

@shared_task
def background_batch_analysis(symbols: List[str], include_technical: bool = True, include_fundamental: bool = True) -> Dict[str, Any]:
    """Background task for batch stock analysis"""
    try:
        results = advanced_stock_service.batch_analyze_stocks(symbols, include_technical, include_fundamental)
        return {'success': True, 'data': results}
    except Exception as e:
        logger.error(f"Background batch analysis failed: {e}")
        return {'success': False, 'error': str(e)}

@shared_task
def update_stock_data_periodic() -> Dict[str, Any]:
    """Periodic task to update stock data"""
    try:
        # Get popular stocks from database dynamically
        from .models import Stock
        popular_stocks = Stock.objects.all()[:20]  # Get top 20 stocks from database
        popular_symbols = [stock.symbol for stock in popular_stocks]
        
        logger.info(f"Starting periodic stock data update for {len(popular_symbols)} symbols")
        
        results = {}
        for symbol in popular_symbols:
            try:
                # Update quote data
                quote_data = advanced_stock_service.get_stock_quote(symbol, use_cache=False)
                if quote_data:
                    results[symbol] = {'quote_updated': True}
                else:
                    results[symbol] = {'quote_updated': False, 'error': 'Failed to fetch quote'}
                
                # Small delay to respect rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error updating {symbol}: {e}")
                results[symbol] = {'quote_updated': False, 'error': str(e)}
        
        logger.info(f"Periodic update completed. Results: {results}")
        return {'success': True, 'results': results}
        
    except Exception as e:
        logger.error(f"Periodic update failed: {e}")
        return {'success': False, 'error': str(e)}

@shared_task
def cleanup_old_cache() -> Dict[str, Any]:
    """Periodic task to cleanup old cache entries"""
    try:
        logger.info("Starting cache cleanup")
        
        # Get all cache keys
        all_keys = stock_cache.redis_client.keys("stock:*")
        cleaned_count = 0
        
        for key in all_keys:
            try:
                # Check if key is expired (Redis handles this automatically)
                # But we can also check for very old data
                data = stock_cache.redis_client.get(key)
                if data:
                    # For now, just log the cleanup
                    # In a real implementation, you might check data age
                    cleaned_count += 1
                    
            except Exception as e:
                logger.error(f"Error cleaning cache key {key}: {e}")
        
        logger.info(f"Cache cleanup completed. Processed {cleaned_count} keys")
        return {'success': True, 'cleaned_count': cleaned_count}
        
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        return {'success': False, 'error': str(e)}

@shared_task
def refresh_stock_cache(symbols: List[str] = None) -> Dict[str, Any]:
    """Task to refresh cache for specific symbols"""
    try:
        if not symbols:
            # Get default symbols from database
            from .models import Stock
            default_stocks = Stock.objects.all()[:10]  # Get top 10 stocks from database
            symbols = [stock.symbol for stock in default_stocks]
        
        logger.info(f"Refreshing cache for {len(symbols)} symbols")
        
        results = {}
        for symbol in symbols:
            try:
                # Invalidate existing cache
                stock_cache.invalidate('QUOTE_DATA', symbol)
                stock_cache.invalidate('OVERVIEW_DATA', symbol)
                stock_cache.invalidate('HISTORICAL_DATA', symbol)
                
                # Fetch fresh data
                quote_data = advanced_stock_service.get_stock_quote(symbol, use_cache=False)
                overview_data = advanced_stock_service.get_company_overview(symbol, use_cache=False)
                
                results[symbol] = {
                    'quote_refreshed': quote_data is not None,
                    'overview_refreshed': overview_data is not None
                }
                
                # Rate limiting delay
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error refreshing {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        logger.info(f"Cache refresh completed. Results: {results}")
        return {'success': True, 'results': results}
        
    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        return {'success': False, 'error': str(e)}

# Initialize services
advanced_stock_service = AdvancedStockService()
stock_cache = StockDataCache()

class AlphaVantageService:
    """Service for fetching stock data from Alpha Vantage API"""
    
    def __init__(self):
        from .enhanced_api_service import enhanced_api_service
        self.enhanced_api = enhanced_api_service
        self.api_key = 'K0A7XYLDNXHNQ1WI'  # Fallback key
        self.base_url = "https://www.alphavantage.co/query"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RichesReach-Django/2.0'
        })
    
    def search_and_sync_stocks(self, search_query: str) -> List[Stock]:
        """Search for stocks and sync them to the database using enhanced API service"""
        try:
            # Use enhanced API service with intelligent caching
            data = self.enhanced_api.search_stocks(search_query)
            
            if not data:
                logger.warning("No data returned from enhanced API service")
                return []
            
            if 'bestMatches' not in data:
                logger.warning("No matches found in API response")
                return []
            
            stocks = []
            for match in data['bestMatches'][:10]:  # Limit to 10 results
                try:
                    # Create or update stock in database
                    stock, created = Stock.objects.get_or_create(
                        symbol=match['1. symbol'],
                        defaults={
                            'company_name': match['2. name'],
                            'sector': match['4. region'],
                            'market_cap': None,  # Will be updated with overview
                            'pe_ratio': None,
                            'dividend_yield': None,
                            'beginner_friendly_score': 50  # Default score
                        }
                    )
                    
                    if created:
                        logger.info(f"Created new stock: {stock.symbol}")
                    
                    # Get additional data for the stock
                    self._update_stock_overview(stock)
                    stocks.append(stock)
                    
                except Exception as e:
                    logger.error(f"Error processing stock {match.get('1. symbol', 'Unknown')}: {e}")
                    continue
            
            return stocks
            
        except Exception as e:
            logger.error(f"Error searching Alpha Vantage: {e}")
            return []
    
    def _update_stock_overview(self, stock: Stock) -> bool:
        """Update stock with company overview data"""
        if not self.api_key:
            return False
        
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': stock.symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage overview error for {stock.symbol}: {data['Error Message']}")
                return False
            
            # Update stock with overview data
            if 'MarketCapitalization' in data and data['MarketCapitalization'] != 'None':
                try:
                    stock.market_cap = int(data['MarketCapitalization'])
                except (ValueError, TypeError):
                    pass
            
            if 'PERatio' in data and data['PERatio'] != 'None':
                try:
                    stock.pe_ratio = float(data['PERatio'])
                except (ValueError, TypeError):
                    pass
            
            if 'DividendYield' in data and data['DividendYield'] != 'None':
                try:
                    stock.dividend_yield = float(data['DividendYield'])
                except (ValueError, TypeError):
                    pass
            
            # Calculate beginner-friendly score
            stock.beginner_friendly_score = self._calculate_beginner_score(data)
            
            stock.save()
            logger.info(f"Updated stock overview for {stock.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating stock overview for {stock.symbol}: {e}")
            return False
    
    def _calculate_beginner_score(self, overview_data: dict) -> int:
        """Calculate beginner-friendly score based on company data"""
        score = 60  # Higher base score for more stocks to qualify
        
        try:
            # Market cap scoring (more generous)
            if 'MarketCapitalization' in overview_data and overview_data['MarketCapitalization'] != 'None':
                market_cap = int(overview_data['MarketCapitalization'])
                if market_cap > 100000000000:  # >$100B
                    score += 25
                elif market_cap > 10000000000:  # >$10B
                    score += 20
                elif market_cap > 1000000000:  # >$1B
                    score += 15
            
            # PE ratio scoring (more generous)
            if 'PERatio' in overview_data and overview_data['PERatio'] != 'None':
                pe_ratio = float(overview_data['PERatio'])
                if 10 <= pe_ratio <= 25:
                    score += 20
                elif 5 <= pe_ratio <= 30:
                    score += 15
                elif pe_ratio < 50:  # Accept higher PE ratios
                    score += 10
            
            # Dividend yield scoring (more generous)
            if 'DividendYield' in overview_data and overview_data['DividendYield'] != 'None':
                dividend_yield = float(overview_data['DividendYield'])
                if 2 <= dividend_yield <= 6:
                    score += 15
                elif dividend_yield > 0:
                    score += 10
            
            # Sector scoring (more sectors considered stable)
            if 'Sector' in overview_data:
                stable_sectors = ['Technology', 'Healthcare', 'Consumer Defensive', 'Utilities', 'Financial Services', 'Consumer Cyclical']
                if overview_data['Sector'] in stable_sectors:
                    score += 10
            
            # Company name recognition bonus (well-known companies are better for beginners)
            if 'Name' in overview_data:
                well_known = ['Apple', 'Microsoft', 'Amazon', 'Google', 'Tesla', 'Johnson & Johnson', 'Procter & Gamble']
                if any(name in overview_data['Name'] for name in well_known):
                    score += 10
            
        except Exception as e:
            logger.error(f"Error calculating beginner score: {e}")
        
        return min(100, max(0, score))  # Ensure score is between 0-100
    
    def get_stock_quote(self, symbol: str) -> Optional[dict]:
        """Get real-time stock quote"""
        if not self.api_key:
            logger.warning(f"No API key set for {symbol}")
            return None
        
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage quote error for {symbol}: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage note for {symbol}: {data['Note']}")
                return None
            
            if 'Global Quote' not in data:
                logger.warning(f"No Global Quote in response for {symbol}: {data}")
                return None
            
            quote = data['Global Quote']
            result = {
                'symbol': quote.get('01. symbol'),
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%'),
                'volume': int(quote.get('06. volume', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'open': float(quote.get('02. open', 0)),
                'previous_close': float(quote.get('08. previous close', 0))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting stock quote for {symbol}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def get_historical_data(self, symbol: str, interval: str = 'daily') -> Optional[dict]:
        """Get historical stock data"""
        if not self.api_key:
            return None
        
        try:
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.api_key,
                'outputsize': 'compact'  # Last 100 data points
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage historical error for {symbol}: {data['Error Message']}")
                return None
            
            if 'Time Series (Daily)' not in data:
                return None
            
            time_series = data['Time Series (Daily)']
            historical_data = []
            
            for date, values in list(time_series.items())[:30]:  # Last 30 days
                historical_data.append({
                    'date': date,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })
            
            return {
                'symbol': symbol,
                'data': historical_data
            }
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def analyze_stock_with_rust(self, symbol: str, include_technical: bool = True, include_fundamental: bool = True) -> Optional[dict]:
        """Analyze stock using Rust-based algorithms (placeholder for now)"""
        try:
            # Get current stock data
            quote = self.get_stock_quote(symbol)
            if not quote:
                return None
            
            # Get company overview
            stock = Stock.objects.filter(symbol=symbol).first()
            if not stock:
                return None
            
            # Basic analysis based on available data
            analysis = {
                'symbol': symbol,
                'current_price': quote['price'],
                'price_change': quote['change'],
                'price_change_percent': quote['change_percent'],
                'volume': quote['volume'],
                'market_cap': stock.market_cap,
                'pe_ratio': stock.pe_ratio,
                'dividend_yield': stock.dividend_yield,
                'beginner_friendly_score': stock.beginner_friendly_score,
                'analysis_date': timezone.now().isoformat(),
                'recommendation': self._generate_recommendation(stock, quote),
                'risk_level': self._calculate_risk_level(stock, quote),
                'growth_potential': self._calculate_growth_potential(stock, quote)
            }
            
            # Add technical indicators if requested
            if include_technical:
                analysis['technicalIndicators'] = self._get_technical_indicators(symbol, quote)
            
            # Add fundamental analysis if requested
            if include_fundamental:
                analysis['fundamentalAnalysis'] = self._get_fundamental_analysis(stock, quote)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {e}")
            return None
    
    def _generate_recommendation(self, stock: Stock, quote: dict) -> str:
        """Generate investment recommendation based on stock data"""
        try:
            score = stock.beginner_friendly_score
            
            if score >= 80:
                return "Strong Buy - Excellent for beginners"
            elif score >= 70:
                return "Buy - Good for beginners"
            elif score >= 60:
                return "Hold - Moderate risk"
            elif score >= 50:
                return "Hold - Higher risk"
            else:
                return "Research Required - High risk"
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "Research Required"
    
    def _calculate_risk_level(self, stock: Stock, quote: dict) -> str:
        """Calculate risk level based on stock metrics"""
        try:
            risk_score = 0
            
            # Market cap risk
            if stock.market_cap and stock.market_cap < 1000000000:  # <$1B
                risk_score += 3
            elif stock.market_cap and stock.market_cap < 10000000000:  # <$10B
                risk_score += 2
            else:
                risk_score += 1
            
            # PE ratio risk
            if stock.pe_ratio and stock.pe_ratio > 30:
                risk_score += 2
            elif stock.pe_ratio and stock.pe_ratio < 5:
                risk_score += 1
            
            # Volatility risk (price change)
            if quote['change_percent'] and abs(float(quote['change_percent'].replace('%', ''))) > 5:
                risk_score += 2
            
            if risk_score <= 2:
                return "Low"
            elif risk_score <= 4:
                return "Medium"
            else:
                return "High"
                
        except Exception as e:
            logger.error(f"Error calculating risk level: {e}")
            return "Medium"
    
    def _calculate_growth_potential(self, stock: Stock, quote: dict) -> str:
        """Calculate growth potential based on stock metrics"""
        try:
            if stock.pe_ratio and stock.pe_ratio < 15:
                return "High - Undervalued"
            elif stock.pe_ratio and stock.pe_ratio < 25:
                return "Medium - Fairly valued"
            elif stock.market_cap and stock.market_cap < 10000000000:  # <$10B
                return "High - Small cap growth potential"
            else:
                return "Medium - Stable growth"
                
        except Exception as e:
            logger.error(f"Error calculating growth potential: {e}")
            return "Medium"
    
    def _get_technical_indicators(self, symbol: str, quote: dict) -> dict:
        """Get basic technical indicators for a stock"""
        try:
            # For now, return placeholder technical indicators
            # In a real implementation, these would be calculated from historical data
            return {
                'rsi': 50.0,  # Relative Strength Index
                'macd': 0.0,  # MACD
                'macdSignal': 0.0,  # MACD Signal
                'macdHistogram': 0.0,  # MACD Histogram
                'sma20': quote.get('price', 0),  # 20-day Simple Moving Average
                'sma50': quote.get('price', 0),  # 50-day Simple Moving Average
                'ema12': quote.get('price', 0),  # 12-day Exponential Moving Average
                'ema26': quote.get('price', 0),  # 26-day Exponential Moving Average
                'bollingerUpper': quote.get('price', 0) * 1.02,  # Bollinger Upper Band
                'bollingerLower': quote.get('price', 0) * 0.98,  # Bollinger Lower Band
                'bollingerMiddle': quote.get('price', 0)  # Bollinger Middle Band
            }
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {e}")
            return {}
    
    def _get_fundamental_analysis(self, stock: Stock, quote: dict) -> dict:
        """Get fundamental analysis for a stock"""
        try:
            # Calculate scores based on available data
            valuation_score = 50
            growth_score = 50
            stability_score = 50
            dividend_score = 50
            debt_score = 50
            
            # Valuation scoring
            if stock.pe_ratio:
                if 10 <= stock.pe_ratio <= 25:
                    valuation_score = 80
                elif 5 <= stock.pe_ratio <= 30:
                    valuation_score = 70
                elif stock.pe_ratio < 5:
                    valuation_score = 60
                else:
                    valuation_score = 40
            
            # Growth scoring (market cap based)
            if stock.market_cap:
                if stock.market_cap > 100000000000:  # >$100B
                    growth_score = 60  # Large caps are more stable
                elif stock.market_cap > 10000000000:  # >$10B
                    growth_score = 70  # Mid caps have good growth potential
                else:
                    growth_score = 80  # Small caps have highest growth potential
            
            # Stability scoring (sector based)
            if stock.sector:
                stable_sectors = ['Utilities', 'Consumer Defensive', 'Healthcare']
                if stock.sector in stable_sectors:
                    stability_score = 80
                else:
                    stability_score = 60
            
            # Dividend scoring
            if stock.dividend_yield:
                if 2 <= stock.dividend_yield <= 6:
                    dividend_score = 80
                elif stock.dividend_yield > 0:
                    dividend_score = 70
                else:
                    dividend_score = 50
            
            return {
                'valuationScore': valuation_score,
                'growthScore': growth_score,
                'stabilityScore': stability_score,
                'dividendScore': dividend_score,
                'debtScore': debt_score
            }
            
        except Exception as e:
            logger.error(f"Error getting fundamental analysis: {e}")
            return {
                'valuationScore': 50,
                'growthScore': 50,
                'stabilityScore': 50,
                'dividendScore': 50,
                'debtScore': 50
            }
    
    def get_rust_recommendations(self) -> List[dict]:
        """Get beginner-friendly stock recommendations"""
        try:
            # Get stocks with moderate beginner-friendly scores
            beginner_stocks = Stock.objects.filter(
                beginner_friendly_score__gte=65
            ).order_by('-beginner_friendly_score')[:10]
            
            recommendations = []
            for stock in beginner_stocks:
                try:
                    quote = self.get_stock_quote(stock.symbol)
                    if quote:
                        recommendations.append({
                            'symbol': stock.symbol,
                            'reason': f"High beginner score ({stock.beginner_friendly_score}) with stable fundamentals",
                            'riskLevel': self._calculate_risk_level(stock, quote),
                            'beginnerScore': stock.beginner_friendly_score
                        })
                except Exception as e:
                    logger.error(f"Error processing recommendation for {stock.symbol}: {e}")
                    continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting rust recommendations: {e}")
            return []
