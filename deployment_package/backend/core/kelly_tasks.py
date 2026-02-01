"""
Celery Tasks for Kelly Criterion Pre-calculation
Pre-calculates Kelly metrics for all user portfolios nightly to warm the cache
"""
import logging
from celery import shared_task
from django.core.cache import cache
from django.contrib.auth import get_user_model
from .portfolio_service import PortfolioService
from .chan_quant_signal_engine import ChanQuantSignalEngine
from .fss_data_pipeline import FSSDataPipeline, FSSDataRequest
import pandas as pd
import asyncio

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def precalculate_kelly_metrics_task(self, user_id=None):
    """
    Pre-calculate Kelly Criterion metrics for user portfolios to warm the cache.
    
    If user_id is provided, calculates for that user only.
    Otherwise, calculates for all users with portfolios.
    
    Args:
        user_id: Optional Django user ID. If None, processes all users.
    """
    try:
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            # Get all users who have portfolio holdings
            users = User.objects.filter(portfolios__isnull=False).distinct()
        
        total_users = users.count()
        logger.info(f"Pre-calculating Kelly metrics for {total_users} user(s)")
        
        engine = ChanQuantSignalEngine()
        pipeline = FSSDataPipeline()
        
        processed_count = 0
        cached_count = 0
        error_count = 0
        
        for user in users:
            try:
                # Get user's portfolio holdings
                portfolios_data = PortfolioService.get_user_portfolios(user)
                if not portfolios_data or not portfolios_data.get('portfolios'):
                    continue
                
                # Collect all unique symbols from user's portfolio
                symbols = set()
                for portfolio in portfolios_data.get('portfolios', []):
                    for holding in portfolio.get('holdings', []):
                        stock = holding.get('stock')
                        if stock:
                            if hasattr(stock, 'symbol'):
                                symbol = stock.symbol
                            elif isinstance(stock, dict):
                                symbol = stock.get('symbol')
                            else:
                                continue
                            
                            if symbol:
                                symbols.add(symbol)
                
                # Pre-calculate Kelly for each symbol
                for symbol in symbols:
                    try:
                        # Check if already cached (skip if recent)
                        symbol_cache_key = f"kelly:symbol:{symbol}"
                        if cache.get(symbol_cache_key):
                            cached_count += 1
                            continue
                        
                        # Fetch historical data
                        prices = None
                        try:
                            import yfinance as yf
                            ticker = yf.Ticker(symbol)
                            hist = ticker.history(period="1y")
                            if not hist.empty:
                                prices = hist['Close']
                        except Exception as yf_error:
                            logger.debug(f"yfinance failed for {symbol}: {yf_error}, trying FSSDataPipeline")
                            try:
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        logger.warning(f"Event loop running for {symbol}, skipping")
                                        continue
                                except RuntimeError:
                                    pass
                                
                                data_result = asyncio.run(pipeline.fetch_data(
                                    tickers=[symbol],
                                    request=FSSDataRequest(lookback_days=252, include_fundamentals=False)
                                ))
                                
                                if data_result and not data_result.prices.empty and symbol in data_result.prices.columns:
                                    prices = data_result.prices[symbol]
                            except Exception as fss_error:
                                logger.debug(f"FSSDataPipeline failed for {symbol}: {fss_error}")
                                continue
                        
                        if prices is None or len(prices) < 20:
                            continue
                        
                        # Calculate Kelly
                        returns = prices.pct_change().dropna()
                        kelly_result = engine.calculate_kelly_position_size(symbol, returns)
                        
                        # Cache the result (1 hour TTL)
                        cache.set(symbol_cache_key, {
                            'kelly_fraction': float(kelly_result.kelly_fraction),
                            'recommended_fraction': float(kelly_result.recommended_fraction),
                            'max_drawdown_risk': float(kelly_result.max_drawdown_risk),
                            'win_rate': float(kelly_result.win_rate),
                            'avg_win': float(kelly_result.avg_win),
                            'avg_loss': float(kelly_result.avg_loss),
                        }, 3600)  # 1 hour TTL
                        
                        processed_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Error pre-calculating Kelly for {symbol}: {e}")
                        error_count += 1
                        continue
                
                # Pre-calculate portfolio-level metrics (this will use cached symbol data)
                portfolio_cache_key = f"kelly:portfolio_metrics:{user.id}"
                # Trigger calculation by calling the resolver logic (it will use cached symbols)
                # We'll just warm the cache here - actual calculation happens on first request
                
            except Exception as e:
                logger.error(f"Error processing user {user.id}: {e}")
                error_count += 1
                continue
        
        logger.info(
            f"Kelly pre-calculation complete: {processed_count} symbols calculated, "
            f"{cached_count} already cached, {error_count} errors"
        )
        
        return {
            'processed': processed_count,
            'cached': cached_count,
            'errors': error_count,
            'total_users': total_users
        }
        
    except Exception as e:
        logger.error(f"Error in precalculate_kelly_metrics_task: {e}", exc_info=True)
        # Retry on failure
        raise self.retry(exc=e)


@shared_task
def precalculate_kelly_for_symbol(symbol: str):
    """
    Pre-calculate Kelly metrics for a single symbol.
    Useful for on-demand cache warming when a new symbol is added to a portfolio.
    
    Args:
        symbol: Stock symbol to calculate Kelly for
    """
    try:
        symbol_cache_key = f"kelly:symbol:{symbol}"
        
        # Check if already cached
        if cache.get(symbol_cache_key):
            logger.debug(f"Kelly metrics already cached for {symbol}")
            return {'status': 'cached', 'symbol': symbol}
        
        engine = ChanQuantSignalEngine()
        pipeline = FSSDataPipeline()
        
        # Fetch historical data
        prices = None
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            if not hist.empty:
                prices = hist['Close']
        except Exception as yf_error:
            logger.debug(f"yfinance failed for {symbol}: {yf_error}, trying FSSDataPipeline")
            try:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        logger.warning(f"Event loop running for {symbol}, skipping")
                        return {'status': 'error', 'symbol': symbol, 'error': 'event_loop_running'}
                except RuntimeError:
                    pass
                
                data_result = asyncio.run(pipeline.fetch_data(
                    tickers=[symbol],
                    request=FSSDataRequest(lookback_days=252, include_fundamentals=False)
                ))
                
                if data_result and not data_result.prices.empty and symbol in data_result.prices.columns:
                    prices = data_result.prices[symbol]
            except Exception as fss_error:
                logger.error(f"FSSDataPipeline failed for {symbol}: {fss_error}")
                return {'status': 'error', 'symbol': symbol, 'error': str(fss_error)}
        
        if prices is None or len(prices) < 20:
            return {'status': 'error', 'symbol': symbol, 'error': 'insufficient_data'}
        
        # Calculate Kelly
        returns = prices.pct_change().dropna()
        kelly_result = engine.calculate_kelly_position_size(symbol, returns)
        
        # Cache the result (1 hour TTL)
        cache.set(symbol_cache_key, {
            'kelly_fraction': float(kelly_result.kelly_fraction),
            'recommended_fraction': float(kelly_result.recommended_fraction),
            'max_drawdown_risk': float(kelly_result.max_drawdown_risk),
            'win_rate': float(kelly_result.win_rate),
            'avg_win': float(kelly_result.avg_win),
            'avg_loss': float(kelly_result.avg_loss),
        }, 3600)  # 1 hour TTL
        
        logger.info(f"Pre-calculated and cached Kelly metrics for {symbol}")
        return {'status': 'success', 'symbol': symbol}
        
    except Exception as e:
        logger.error(f"Error pre-calculating Kelly for {symbol}: {e}", exc_info=True)
        return {'status': 'error', 'symbol': symbol, 'error': str(e)}

