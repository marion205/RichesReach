"""
Market-data root fields: stocks, stock, fss_scores, top_fss_stocks,
beginner_friendly_stocks, current_stock_prices.
"""
import asyncio
import logging

import django.db.models as models
import graphene
from django.utils import timezone

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
        
        # Get all stocks and sort by beginner_friendly_score
        # The score is now personalized per user in the resolver
        stocks = Stock.objects.all()
        stocks_list = list(stocks[:100])
        
        # Sort by beginner_friendly_score (will be calculated per-user in resolver)
        # Note: This is a simple sort on DB value, actual score calculated in GraphQL type
        stocks_list.sort(key=lambda s: getattr(s, 'beginner_friendly_score', 0), reverse=True)
        if sector_weights:
            def score(stock):
                base = getattr(stock, "beginner_friendly_score", 65)
                sector = getattr(stock, "sector", "Unknown")
                return base + (sector_weights.get(sector, 0) * 20)
            stocks_list.sort(key=score, reverse=True)
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
                    logger.warning("Could not fetch real-time prices for beginner stocks: %s", e)
        except Exception as e:
            logger.warning("Error updating prices for beginner stocks: %s", e)
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
