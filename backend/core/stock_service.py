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
        # Get popular stocks from database or config
        popular_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
        
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
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
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
