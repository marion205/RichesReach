"""
Real-Time Data Integration Service
Connects to existing APIs to populate and update stock data in real-time
"""
import os
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction

from .models import Stock, StockData
from .market_data_api_service import MarketDataAPIService, DataProvider
from .enhanced_stock_service import EnhancedStockService

logger = logging.getLogger(__name__)

class RealTimeDataService:
    """
    Service for real-time stock data integration and updates
    """
    
    def __init__(self):
        self.market_data_service = MarketDataAPIService()
        self.enhanced_service = EnhancedStockService()
        self.cache_timeout = 300  # 5 minutes cache
        self.rate_limit_delay = 1  # 1 second between API calls
        
        # API Keys from environment
        self.api_keys = {
            'ALPHA_VANTAGE': os.getenv('ALPHA_VANTAGE_API_KEY', 'OHYSFF1AE446O7CR'),
            'FINNHUB': os.getenv('FINNHUB_API_KEY', 'd2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0'),
        }
        
        # Rate limiting tracking
        self.rate_limits = {
            'ALPHA_VANTAGE': {'limit': 5, 'window': 60, 'count': 0, 'reset_time': 0},
            'FINNHUB': {'limit': 60, 'window': 60, 'count': 0, 'reset_time': 0},
        }
    
    def _check_rate_limit(self, provider: str) -> bool:
        """Check and enforce rate limits for API providers"""
        if provider not in self.rate_limits:
            return True
            
        current_time = time.time()
        rate_info = self.rate_limits[provider]
        
        # Reset counter if window has passed
        if current_time >= rate_info['reset_time']:
            rate_info['count'] = 0
            rate_info['reset_time'] = current_time + rate_info['window']
        
        # Check if we're under the limit
        if rate_info['count'] >= rate_info['limit']:
            logger.warning(f"Rate limit exceeded for {provider}. Waiting...")
            return False
        
        rate_info['count'] += 1
        return True
    
    async def _wait_for_rate_limit(self, provider: str):
        """Wait if rate limit is exceeded"""
        while not self._check_rate_limit(provider):
            await asyncio.sleep(1)
    
    async def get_comprehensive_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive stock data from multiple sources
        """
        try:
            # Check cache first
            cache_key = f"stock_data_{symbol}"
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Using cached data for {symbol}")
                return cached_data
            
            # Try to get real-time price data
            price_data = None
            try:
                await self._wait_for_rate_limit('FINNHUB')
                price_data = await self.enhanced_service.get_real_time_price(symbol)
                if price_data:
                    logger.info(f"Got real-time price for {symbol}: ${price_data.get('price', 'N/A')}")
            except Exception as e:
                logger.warning(f"Failed to get real-time price for {symbol}: {e}")
            
            # Try to get additional market data from Alpha Vantage
            market_data = None
            try:
                await self._wait_for_rate_limit('ALPHA_VANTAGE')
                market_data = await self._get_alpha_vantage_data(symbol)
                if market_data:
                    logger.info(f"Got market data for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to get market data for {symbol}: {e}")
            
            # Combine data
            comprehensive_data = {
                'symbol': symbol,
                'current_price': price_data.get('price') if price_data else None,
                'change': price_data.get('change') if price_data else None,
                'change_percent': price_data.get('change_percent') if price_data else None,
                'volume': price_data.get('volume') if price_data else None,
                'high': price_data.get('high') if price_data else None,
                'low': price_data.get('low') if price_data else None,
                'open': price_data.get('open') if price_data else None,
                'market_cap': market_data.get('market_cap') if market_data else None,
                'pe_ratio': market_data.get('pe_ratio') if market_data else None,
                'dividend_yield': market_data.get('dividend_yield') if market_data else None,
                'last_updated': timezone.now().isoformat(),
                'source': price_data.get('source', 'api') if price_data else 'fallback'
            }
            
            # Cache the data
            cache.set(cache_key, comprehensive_data, self.cache_timeout)
            
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive data for {symbol}: {e}")
            return None
    
    async def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get additional market data from Alpha Vantage
        """
        try:
            # This would integrate with your existing Alpha Vantage implementation
            # For now, return mock data structure
            return {
                'market_cap': None,  # Would be populated from API
                'pe_ratio': None,    # Would be populated from API
                'dividend_yield': None,  # Would be populated from API
            }
        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {e}")
            return None
    
    async def update_stock_in_database(self, symbol: str) -> bool:
        """
        Update a single stock in the database with real-time data
        """
        try:
            # Get comprehensive data
            data = await self.get_comprehensive_stock_data(symbol)
            if not data:
                logger.warning(f"No data available for {symbol}")
                return False
            
            # Update database
            with transaction.atomic():
                stock, created = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'company_name': f"{symbol} Corp.",  # Would be populated from API
                        'sector': 'Technology',  # Would be populated from API
                    }
                )
                
                # Update fields with real data
                if data.get('current_price'):
                    stock.current_price = Decimal(str(data['current_price']))
                if data.get('market_cap'):
                    stock.market_cap = int(data['market_cap'])
                if data.get('pe_ratio'):
                    stock.pe_ratio = float(data['pe_ratio'])
                if data.get('dividend_yield'):
                    stock.dividend_yield = float(data['dividend_yield'])
                
                stock.save()
                
                logger.info(f"Updated {symbol} in database: ${stock.current_price}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating {symbol} in database: {e}")
            return False
    
    async def update_all_stocks(self) -> Dict[str, Any]:
        """
        Update all stocks in the database with real-time data
        """
        logger.info("Starting real-time update of all stocks...")
        
        # Get all stock symbols
        stocks = Stock.objects.all()
        results = {
            'total': stocks.count(),
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for stock in stocks:
            try:
                success = await self.update_stock_in_database(stock.symbol)
                if success:
                    results['updated'] += 1
                else:
                    results['failed'] += 1
                
                # Rate limiting delay
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{stock.symbol}: {str(e)}")
                logger.error(f"Error updating {stock.symbol}: {e}")
        
        logger.info(f"Real-time update complete: {results['updated']}/{results['total']} updated")
        return results
    
    async def update_priority_stocks(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Update specific priority stocks with real-time data
        """
        logger.info(f"Updating priority stocks: {symbols}")
        
        results = {
            'total': len(symbols),
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for symbol in symbols:
            try:
                success = await self.update_stock_in_database(symbol)
                if success:
                    results['updated'] += 1
                else:
                    results['failed'] += 1
                
                # Rate limiting delay
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{symbol}: {str(e)}")
                logger.error(f"Error updating {symbol}: {e}")
        
        return results

# Global instance
realtime_data_service = RealTimeDataService()
