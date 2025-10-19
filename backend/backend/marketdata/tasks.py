# marketdata/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta
import logging
from .service import MarketDataService
from .models import DailyBar, Quote, Equity

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def refresh_quotes(self, symbols):
    """Refresh quotes for a list of symbols"""
    try:
        service = MarketDataService()
        updated_count = 0
        
        for symbol in symbols:
            try:
                service.get_quote(symbol)
                updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to refresh quote for {symbol}: {e}")
                continue
        
        logger.info(f"Refreshed {updated_count}/{len(symbols)} quotes")
        return {"updated": updated_count, "total": len(symbols)}
        
    except Exception as e:
        logger.error(f"Quote refresh task failed: {e}")
        raise self.retry(countdown=60, exc=e)

@shared_task(bind=True, max_retries=3)
def refresh_profiles(self, symbols):
    """Refresh company profiles for a list of symbols"""
    try:
        service = MarketDataService()
        updated_count = 0
        
        for symbol in symbols:
            try:
                service.get_profile(symbol)
                updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to refresh profile for {symbol}: {e}")
                continue
        
        logger.info(f"Refreshed {updated_count}/{len(symbols)} profiles")
        return {"updated": updated_count, "total": len(symbols)}
        
    except Exception as e:
        logger.error(f"Profile refresh task failed: {e}")
        raise self.retry(countdown=300, exc=e)  # 5 minute retry for profiles

@shared_task(bind=True, max_retries=3)
def refresh_options_chains(self, symbols, limit=50):
    """Refresh options chains for a list of symbols"""
    try:
        service = MarketDataService()
        updated_count = 0
        
        for symbol in symbols:
            try:
                service.get_options_chain(symbol, limit)
                updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to refresh options for {symbol}: {e}")
                continue
        
        logger.info(f"Refreshed {updated_count}/{len(symbols)} options chains")
        return {"updated": updated_count, "total": len(symbols)}
        
    except Exception as e:
        logger.error(f"Options refresh task failed: {e}")
        raise self.retry(countdown=300, exc=e)

@shared_task
def backfill_daily_bars(symbol, days=365):
    """Backfill daily bars for a symbol (placeholder for future implementation)"""
    try:
        # This would integrate with providers to get historical data
        # For now, just log the request
        logger.info(f"Backfill requested for {symbol} ({days} days)")
        
        # In a real implementation, you would:
        # 1. Call provider API for historical data
        # 2. Parse and normalize the data
        # 3. Store in DailyBar model
        # 4. Handle rate limits and pagination
        
        return {"symbol": symbol, "days": days, "status": "placeholder"}
        
    except Exception as e:
        logger.error(f"Backfill task failed for {symbol}: {e}")
        raise

@shared_task
def cleanup_old_quotes(days=7):
    """Clean up old quote records to manage database size"""
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = Quote.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old quote records")
        return {"deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"Quote cleanup task failed: {e}")
        raise

@shared_task
def health_check_providers():
    """Check health of all providers and update status"""
    try:
        service = MarketDataService()
        status = service.get_provider_status()
        
        # Log provider health
        for provider, health in status.items():
            if health["available"]:
                logger.info(f"Provider {provider} is healthy")
            else:
                logger.warning(f"Provider {provider} is unhealthy (failures: {health['failures']})")
        
        return status
        
    except Exception as e:
        logger.error(f"Provider health check failed: {e}")
        raise

@shared_task
def warm_cache(symbols):
    """Warm the cache with frequently requested symbols"""
    try:
        service = MarketDataService()
        warmed_count = 0
        
        for symbol in symbols:
            try:
                # Warm quote cache
                service.get_quote(symbol)
                # Warm profile cache
                service.get_profile(symbol)
                warmed_count += 1
            except Exception as e:
                logger.warning(f"Failed to warm cache for {symbol}: {e}")
                continue
        
        logger.info(f"Warmed cache for {warmed_count}/{len(symbols)} symbols")
        return {"warmed": warmed_count, "total": len(symbols)}
        
    except Exception as e:
        logger.error(f"Cache warming task failed: {e}")
        raise
