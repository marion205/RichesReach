"""
Simple Real-Time Data Service
A simplified version that works with the existing enhanced stock service
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

from .models import Stock
from .enhanced_stock_service import EnhancedStockService

logger = logging.getLogger(__name__)

class SimpleRealTimeDataService:
    """
    Simplified service for real-time stock data integration
    """
    
    def __init__(self):
        self.enhanced_service = EnhancedStockService()
        self.cache_timeout = 300  # 5 minutes cache
        self.rate_limit_delay = 1  # 1 second between API calls
        
        # Rate limiting tracking
        self.rate_limits = {
            'enhanced_service': {'count': 0, 'reset_time': 0, 'limit': 10, 'window': 60}
        }
    
    def _check_rate_limit(self, service: str) -> bool:
        """Check and enforce rate limits"""
        if service not in self.rate_limits:
            return True
            
        current_time = time.time()
        rate_info = self.rate_limits[service]
        
        # Reset counter if window has passed
        if current_time >= rate_info['reset_time']:
            rate_info['count'] = 0
            rate_info['reset_time'] = current_time + rate_info['window']
        
        # Check if we're under the limit
        if rate_info['count'] >= rate_info['limit']:
            logger.warning(f"Rate limit exceeded for {service}. Waiting...")
            return False
        
        rate_info['count'] += 1
        return True
    
    async def _wait_for_rate_limit(self, service: str):
        """Wait if rate limit is exceeded"""
        while not self._check_rate_limit(service):
            await asyncio.sleep(1)
    
    async def get_stock_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time price data for a stock
        """
        try:
            # Check cache first
            cache_key = f"stock_price_{symbol}"
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Using cached price data for {symbol}")
                return cached_data
            
            # Wait for rate limit
            await self._wait_for_rate_limit('enhanced_service')
            
            # Get real-time price data
            price_data = await self.enhanced_service.get_real_time_price(symbol)
            
            if price_data:
                # Cache the data
                cache.set(cache_key, price_data, self.cache_timeout)
                logger.info(f"Got real-time price for {symbol}: ${price_data.get('price', 'N/A')}")
                return price_data
            else:
                logger.warning(f"No price data available for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return None
    
    async def update_stock_in_database(self, symbol: str) -> bool:
        """
        Update a single stock in the database with real-time data
        """
        try:
            # Get real-time price data
            price_data = await self.get_stock_price_data(symbol)
            
            if not price_data:
                logger.warning(f"No price data available for {symbol}")
                return False
            
            # Update database
            with transaction.atomic():
                try:
                    stock = Stock.objects.get(symbol=symbol)
                    
                    # Update fields with real data
                    if price_data.get('price'):
                        stock.current_price = Decimal(str(price_data['price']))
                    
                    stock.save()
                    
                    logger.info(f"Updated {symbol} in database: ${stock.current_price}")
                    return True
                    
                except Stock.DoesNotExist:
                    logger.warning(f"Stock {symbol} not found in database")
                    return False
                
        except Exception as e:
            logger.error(f"Error updating {symbol} in database: {e}")
            return False
    
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

# Global instance
simple_realtime_service = SimpleRealTimeDataService()
