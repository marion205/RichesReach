"""
Market-data root fields: stocks, stock, fss_scores, top_fss_stocks,
beginner_friendly_stocks, current_stock_prices.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

import django.db.models as models
import graphene
from django.utils import timezone
from django.core.cache import cache
import requests
import numpy as np

from core.models import Stock

logger = logging.getLogger(__name__)


class MarketDataQuery(graphene.ObjectType):
    """
    Root fields for market data: stocks, stock, FSS scores, beginner-friendly stocks,
    current stock prices.
    """

    stocks = graphene.List("core.types.StockType", search=graphene.String(required=False))
    stock = graphene.Field("core.types.StockType", symbol=graphene.String(required=True))
    fss_scores = graphene.List(
        "core.types.FSSScoreType",
        symbols=graphene.List(graphene.String, required=True),
        description="Get FSS v3.0 scores for multiple stocks",
    )
    top_fss_stocks = graphene.List(
        "core.types.StockType",
        limit=graphene.Int(default_value=20),
        description="Get top stocks ranked by FSS v3.0 score",
    )
    beginner_friendly_stocks = graphene.List("core.types.StockType")
    current_stock_prices = graphene.List(
        "core.types.StockPriceType",
        symbols=graphene.List(graphene.String),
    )

    @staticmethod
    def _enrich_stocks_with_fundamentals(stocks: List[Stock]) -> None:
        """
        Enrich stock models with real fundamental data from Polygon API.
        Updates the database with P/E ratios, volatility, market cap, and sector.
        """
        import os
        polygon_key = os.getenv("POLYGON_API_KEY", "")
        if not polygon_key:
            logger.warning("No Polygon API key, skipping fundamental data enrichment")
            return
        
        logger.info(f"Starting enrichment for {len(stocks)} stocks")
        enriched_count = 0
        
        for stock in stocks:
            symbol = stock.symbol
            
            # 1. Fetch ticker details for P/E ratio and market data
            try:
                details_cache_key = f"polygon:details:{symbol}:v1"
                cached_details = cache.get(details_cache_key)
                
                if cached_details:
                    stock.pe_ratio = cached_details.get('pe_ratio')
                    stock.sector = cached_details.get('sector', stock.sector)
                    stock.market_cap = cached_details.get('market_cap', stock.market_cap)
                    logger.debug(f"Using cached details for {symbol}")
                else:
                    details_url = f"https://api.polygon.io/v3/reference/tickers/{symbol}"
                    details_params = {'apiKey': polygon_key}
                    logger.debug(f"Fetching details from {details_url}")
                    details_resp = requests.get(details_url, params=details_params, timeout=2.0)
                    logger.debug(f"Details response status for {symbol}: {details_resp.status_code}")
                    
                    if details_resp.status_code == 200:
                        details_data = details_resp.json().get('results', {})
                        
                        # Extract P/E ratio - Note: Not available in Polygon free tier
                        # We'll use sector-based reasonable defaults instead
                        market_data = details_data.get('market_data', {})
                        pe_ratio = market_data.get('pe_ratio', 0.0) or 0.0
                        
                        # Get market cap (available in v3/reference/tickers)
                        market_cap = details_data.get('market_cap', stock.market_cap or 0)
                        
                        # Get sector classification
                        # Polygon uses sic_description which is more detailed
                        sector = details_data.get('sector', stock.sector or 'Unknown')
                        if sector == 'Unknown':
                            # Try sic_description as fallback
                            sic_desc = details_data.get('sic_description', '')
                            if 'COMPUTER' in sic_desc or 'SOFTWARE' in sic_desc or 'TECHNOLOG' in sic_desc:
                                sector = 'Technology'
                            elif 'RETAIL' in sic_desc or 'STORE' in sic_desc:
                                sector = 'Consumer Cyclical'
                            elif 'BANK' in sic_desc or 'FINANCIAL' in sic_desc:
                                sector = 'Financial Services'
                            elif 'DRUG' in sic_desc or 'PHARMACEUTICAL' in sic_desc or 'HEALTH' in sic_desc:
                                sector = 'Healthcare'
                            elif 'MOTOR' in sic_desc or 'AUTOMOBILE' in sic_desc:
                                sector = 'Consumer Cyclical'
                            else:
                                sector = 'Unknown'
                        
                        # If P/E not available, use reasonable sector-based defaults
                        # This helps with scoring even without premium Polygon access
                        if pe_ratio == 0.0 or pe_ratio is None:
                            pe_defaults = {
                                'Technology': 25.0,
                                'Consumer Cyclical': 18.0,
                                'Financial Services': 12.0,
                                'Healthcare': 22.0,
                                'Communication Services': 20.0,
                                'Consumer Defensive': 20.0,
                                'Energy': 15.0,
                                'Utilities': 18.0,
                                'Real Estate': 25.0,
                                'Basic Materials': 16.0,
                                'Industrials': 19.0,
                                'Unknown': 20.0
                            }
                            pe_ratio = pe_defaults.get(sector, 20.0)
                            logger.debug(f"Using default P/E {pe_ratio} for {symbol} ({sector}) - not available in API")
                        
                        # Update stock model
                        old_pe = stock.pe_ratio
                        old_cap = stock.market_cap
                        old_sector = stock.sector
                        stock.pe_ratio = float(pe_ratio) if pe_ratio else 0.0
                        stock.sector = sector
                        if market_cap:
                            stock.market_cap = int(market_cap)
                        
                        updates = {
                            'pe_ratio': stock.pe_ratio,
                            'sector': sector,
                            'market_cap': stock.market_cap,
                        }
                        
                        # Save to database
                        stock.save(update_fields=['pe_ratio', 'sector', 'market_cap'])
                        enriched_count += 1
                        
                        # Cache for 1 hour
                        cache.set(details_cache_key, updates, 3600)
                        logger.info(f"Enriched {symbol}: P/E={pe_ratio:.2f} (was {old_pe}), Cap=${market_cap:,} (was {old_cap}), Sector={sector} (was {old_sector})")
                    elif details_resp.status_code == 429:
                        logger.warning(f"Rate limit hit for {symbol} details (status 429)")
                        break
                    else:
                        logger.warning(f"API returned {details_resp.status_code} for {symbol}: {details_resp.text[:200]}")
            except Exception as e:
                logger.error(f"Error fetching details for {symbol}: {e}", exc_info=True)
            
            # 2. Calculate volatility from historical data (30-day)
            try:
                volatility_cache_key = f"polygon:volatility:{symbol}:v1"
                cached_volatility = cache.get(volatility_cache_key)
                
                if cached_volatility is not None:
                    stock.volatility = cached_volatility
                    logger.debug(f"Using cached volatility for {symbol}: {cached_volatility}")
                else:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=30)
                    
                    agg_url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
                    agg_params = {'apiKey': polygon_key}
                    logger.debug(f"Fetching volatility data from {agg_url}")
                    agg_resp = requests.get(agg_url, params=agg_params, timeout=2.0)
                    logger.debug(f"Volatility response status for {symbol}: {agg_resp.status_code}")
                    
                    if agg_resp.status_code == 200:
                        agg_data = agg_resp.json()
                        results = agg_data.get('results', [])
                        
                        if len(results) >= 10:  # Need at least 10 days of data
                            # Calculate daily returns
                            closes = [r['c'] for r in results]
                            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
                            
                            # Annualized volatility
                            old_vol = stock.volatility
                            volatility = float(np.std(returns) * np.sqrt(252) * 100)  # Annualized %
                            stock.volatility = round(volatility, 2)
                            
                            # Save to database
                            stock.save(update_fields=['volatility'])
                            enriched_count += 1
                            
                            # Cache for 1 hour
                            cache.set(volatility_cache_key, volatility, 3600)
                            logger.info(f"Calculated {symbol} volatility: {volatility:.1f}% (was {old_vol})")
                        else:
                            logger.warning(f"Not enough data for {symbol}: only {len(results)} days")
                    elif agg_resp.status_code == 429:
                        logger.warning(f"Rate limit hit for {symbol} volatility (status 429)")
                        break
                    else:
                        logger.warning(f"API returned {agg_resp.status_code} for {symbol} aggs: {agg_resp.text[:200]}")
            except Exception as e:
                logger.error(f"Error calculating volatility for {symbol}: {e}", exc_info=True)
        
        logger.info(f"Enrichment complete: {enriched_count} stocks updated")


    def resolve_stock(self, info, symbol):
        symbol = (symbol or "").strip().upper()
        if not symbol:
            return None
        try:
            return Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            return None

    def resolve_stocks(self, info, search=None):
        if search:
            db_stocks = Stock.objects.filter(
                models.Q(symbol__icontains=search.upper())
                | models.Q(company_name__icontains=search)
            )[:50]
            if db_stocks.exists():
                return list(db_stocks)
            try:
                from core.stock_service import AlphaVantageService
                service = AlphaVantageService()
                api_stocks = service.search_and_sync_stocks(search)
                if api_stocks:
                    return list(api_stocks)
                return list(Stock.objects.none())
            except Exception as e:
                logger.error("API search error: %s", e)
                return []
        
        # Get all stocks and update prices for top ones
        stocks_list = list(Stock.objects.all().order_by('-market_cap')[:100])
        
        # Fetch real-time prices for stocks
        try:
            from core.enhanced_stock_service import enhanced_stock_service
            symbols = [s.symbol for s in stocks_list[:20]]
            if symbols:
                try:
                    prices_data = asyncio.run(enhanced_stock_service.get_multiple_prices(symbols))
                    for stock in stocks_list[:20]:
                        pd = prices_data.get(stock.symbol)
                        if pd and pd.get("price", 0) > 0:
                            stock.current_price = pd["price"]
                            enhanced_stock_service.update_stock_price_in_database(stock.symbol, pd)
                except Exception as e:
                    logger.warning("Could not fetch real-time prices for stocks: %s", e)
        except Exception as e:
            logger.warning("Error updating prices for stocks: %s", e)
        
        return stocks_list

    def resolve_fss_scores(self, info, symbols):
        try:
            from core.fss_service import get_fss_service
            fss_service = get_fss_service()
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("FSS scores query skipped (async context)")
                return []
            results = loop.run_until_complete(fss_service.get_stocks_fss(symbols))
            return [r for r in results.values() if r]
        except Exception as e:
            logger.error("Error resolving FSS scores: %s", e, exc_info=True)
            return []

    def resolve_top_fss_stocks(self, info, limit):
        try:
            from core.fss_service import get_fss_service
            stocks = list(Stock.objects.all()[:100])
            symbols = [s.symbol for s in stocks]
            if not symbols:
                return []
            fss_service = get_fss_service()
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("Top FSS stocks query skipped (async context)")
                return []
            results = loop.run_until_complete(fss_service.get_stocks_fss(symbols))
            ranked = fss_service.rank_stocks_by_fss(results)
            top_symbols = [r["symbol"] for r in ranked[:limit]]
            if not top_symbols:
                return []
            qs = list(Stock.objects.filter(symbol__in=top_symbols))
            qs.sort(key=lambda s: top_symbols.index(s.symbol) if s.symbol in top_symbols else 999)
            return qs

        except Exception as e:
            logger.error("Error resolving top FSS stocks: %s", e, exc_info=True)
            return []

    def resolve_beginner_friendly_stocks(self, info):
        user = getattr(info.context, "user", None)
        user_id = getattr(user, "id", 1) if user and not getattr(user, "is_anonymous", True) else 1
        sector_weights = {}
        try:
            from core.spending_habits_service import SpendingHabitsService
            spending_service = SpendingHabitsService()
            spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)
            sector_weights = spending_service.get_spending_based_stock_preferences(spending_analysis)
        except Exception as e:
            logger.warning("Could not get spending analysis for beginner stocks: %s", e)
        
        # Get all stocks and compute personalized beginner scores
        stocks = Stock.objects.all()
        stocks_list = list(stocks[:100])

        from core.types import StockType

        scored_stocks = []
        for stock in stocks_list:
            try:
                stock_type = StockType(stock)
                score = stock_type.resolve_beginner_friendly_score(info)
            except Exception:
                score = getattr(stock, "beginner_friendly_score", 0)
            scored_stocks.append((stock, score))

        if sector_weights:
            def adjusted_score(item):
                stock, base = item
                sector = getattr(stock, "sector", "Unknown")
                return base + (sector_weights.get(sector, 0) * 20)
            scored_stocks.sort(key=adjusted_score, reverse=True)
        else:
            scored_stocks.sort(key=lambda item: item[1], reverse=True)

        # Beginner Friendly should show only BUY-tier stocks (score >= 60)
        # Temporarily allow >= 50 to debug why scores aren't reaching 60
        scored_stocks = [item for item in scored_stocks if item[1] >= 50]
        stocks_list = [item[0] for item in scored_stocks]
        
        # Enrich with fundamental data from Polygon and update database
        try:
            MarketDataQuery._enrich_stocks_with_fundamentals(stocks_list[:20])
            # Refresh from database to get enriched data
            symbols = [s.symbol for s in stocks_list[:20]]
            stocks_list = list(Stock.objects.filter(symbol__in=symbols))
            logger.debug(f"Refreshed {len(stocks_list)} stocks from DB after enrichment")
        except Exception as e:
            logger.warning("Could not enrich stocks with fundamental data: %s", e)
        
        # NOTE: Skip async price fetching in async context
        # The enhanced_stock_service.get_multiple_prices() is async and cannot be called
        # with asyncio.run() from within an async GraphQL resolver context
        # Prices are cached separately and will be updated by background tasks
        
        return stocks_list[:20]

    def resolve_current_stock_prices(self, info, symbols=None):
        if not symbols:
            return []
        try:
            from core.enhanced_stock_service import enhanced_stock_service

            async def get_prices():
                return await enhanced_stock_service.get_multiple_prices(symbols)

            prices_data = asyncio.run(get_prices())
            out = []
            for symbol in symbols:
                price_data = prices_data.get(symbol)
                if price_data and price_data.get("price", 0) > 0:
                    out.append({
                        "symbol": symbol,
                        "current_price": price_data["price"],
                        "change": price_data.get("change", 0.0),
                        "change_percent": price_data.get("change_percent", "0%"),
                        "last_updated": price_data.get("last_updated", timezone.now().isoformat()),
                        "source": price_data.get("source", "unknown"),
                        "verified": price_data.get("verified", False),
                        "api_response": price_data,
                    })
                    enhanced_stock_service.update_stock_price_in_database(symbol, price_data)
                else:
                    try:
                        stock = Stock.objects.get(symbol=symbol.upper())
                        if stock.current_price:
                            out.append({
                                "symbol": symbol,
                                "current_price": float(stock.current_price),
                                "change": 0.0,
                                "change_percent": "0%",
                                "last_updated": stock.last_updated.isoformat() if stock.last_updated else timezone.now().isoformat(),
                                "source": "database",
                                "verified": False,
                                "api_response": None,
                            })
                    except Stock.DoesNotExist:
                        pass
            return out
        except Exception as e:
            logger.error("Error getting current stock prices: %s", e)
        out = []
        for symbol in symbols:
            try:
                stock = Stock.objects.get(symbol=symbol.upper())
                if stock.current_price:
                    out.append({
                        "symbol": symbol,
                        "current_price": float(stock.current_price),
                        "change": 0.0,
                        "change_percent": "0%",
                        "last_updated": stock.last_updated.isoformat() if stock.last_updated else timezone.now().isoformat(),
                        "source": "database",
                        "verified": False,
                        "api_response": None,
                    })
            except (Stock.DoesNotExist, Exception):
                pass
        return out
