"""
Celery tasks for real-time data updates
"""
import asyncio
import logging
from celery import shared_task
from django.utils import timezone

from .simple_realtime_service import simple_realtime_service
from .models import Stock

logger = logging.getLogger(__name__)

@shared_task
def update_all_stocks_realtime():
    """
    Celery task to update all stocks with real-time data
    """
    logger.info("Starting scheduled real-time stock update...")
    
    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(simple_realtime_service.update_all_stocks())
        loop.close()
        
        logger.info(f"Scheduled update complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in scheduled stock update: {e}")
        return {'error': str(e)}

@shared_task
def update_priority_stocks_realtime():
    """
    Celery task to update priority stocks (most popular/active)
    """
    logger.info("Starting scheduled priority stock update...")
    
    # Define priority stocks (most popular/active)
    priority_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'JPM', 'JNJ', 'PG']
    
    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(simple_realtime_service.update_priority_stocks(priority_symbols))
        loop.close()
        
        logger.info(f"Priority update complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in priority stock update: {e}")
        return {'error': str(e)}

@shared_task
def update_single_stock_realtime(symbol: str):
    """
    Celery task to update a single stock with real-time data
    """
    logger.info(f"Starting real-time update for {symbol}...")
    
    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(simple_realtime_service.update_stock_in_database(symbol))
        loop.close()
        
        if success:
            logger.info(f"Successfully updated {symbol}")
            return {'symbol': symbol, 'status': 'success'}
        else:
            logger.warning(f"Failed to update {symbol}")
            return {'symbol': symbol, 'status': 'failed'}
            
    except Exception as e:
        logger.error(f"Error updating {symbol}: {e}")
        return {'symbol': symbol, 'status': 'error', 'error': str(e)}

@shared_task
def cleanup_old_stock_data():
    """
    Celery task to cleanup old stock data
    """
    logger.info("Starting cleanup of old stock data...")
    
    try:
        # Clean up old StockData records (keep last 30 days)
        from datetime import timedelta
        cutoff_date = timezone.now().date() - timedelta(days=30)
        
        old_records = StockData.objects.filter(date__lt=cutoff_date)
        count = old_records.count()
        old_records.delete()
        
        logger.info(f"Cleaned up {count} old stock data records")
        return {'cleaned_records': count}
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        return {'error': str(e)}