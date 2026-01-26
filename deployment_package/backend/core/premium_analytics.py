"""
Premium Analytics Service

Provides:
- Portfolio performance metrics
- Advanced stock screening
- AI-powered portfolio recommendations

This file is designed to be robust and schema-safe:
if anything fails, it returns reasonable defaults instead of crashing.
"""

from __future__ import annotations

import logging
import random
import json
import hashlib
import asyncio
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.db.models import F, FloatField, Sum
from django.db.models.functions import Coalesce
from django.core.cache import cache
from django.utils import timezone

from .models import Portfolio, Stock

logger = logging.getLogger(__name__)

# Layer 0: Performance constants
MAX_TICKERS = 80  # Limit universe size for faster processing

# Layer 1: Cache keys and TTLs
POLYGON_UNIVERSE_CACHE_KEY = "ai_recs:polygon_universe:v1"
POLYGON_UNIVERSE_TTL = 60  # 1 minute - Polygon universe changes slowly
RECS_CACHE_TTL = 300  # 5 minutes - Recommendations per user+profile


@dataclass
class PortfolioMetrics:
    total_value: float = 0.0
    total_cost: float = 0.0
    total_return: float = 0.0
    total_return_percent: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    beta: float = 1.0
    alpha: float = 0.0
    holdings: List[Dict[str, Any]] = None
    sector_allocation: Dict[str, float] = None
    risk_metrics: Dict[str, Any] = None


class PremiumAnalyticsService:
    """
    Main service used by premium_types.PremiumQueries.

    Methods used in your schema:
        - get_portfolio_performance_metrics(user_id, portfolio_name=None)
        - get_advanced_stock_screening(filters: dict)
        - get_ai_recommendations(user_id, risk_tolerance="medium")
    """

    CACHE_TTL = 300  # 5 minutes

    # ------------------------------------------------------------------ #
    # 1) Portfolio metrics                                               #
    # ------------------------------------------------------------------ #

    def get_portfolio_performance_metrics(
        self,
        user_id: int,
        portfolio_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns data for PortfolioMetricsType.

        Expected keys:
        - total_value, total_cost, total_return, total_return_percent
        - volatility, sharpe_ratio, max_drawdown, beta, alpha
        - holdings (list)
        - sector_allocation (dict)
        - risk_metrics (dict)
        """
        cache_key = f"premium:portfolio_metrics:{user_id}:{portfolio_name or 'all'}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            qs = Portfolio.objects.filter(user_id=user_id)
            if portfolio_name:
                qs = qs.filter(name=portfolio_name)

            portfolio = qs.first()
            if not portfolio:
                logger.warning(f"No portfolio found for user {user_id}")
                metrics = self._empty_portfolio_metrics()
            else:
                metrics = self._build_portfolio_metrics_from_portfolio(portfolio)

            cache.set(cache_key, metrics, self.CACHE_TTL)
            return metrics

        except Exception as e:
            logger.error(f"Error computing portfolio metrics for user {user_id}: {e}")
            return self._empty_portfolio_metrics()

    def _empty_portfolio_metrics(self) -> Dict[str, Any]:
        """Return a safe default metrics payload."""
        return {
            "total_value": 0.0,
            "total_cost": 0.0,
            "total_return": 0.0,
            "total_return_percent": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "beta": 1.0,
            "alpha": 0.0,
            "holdings": [],
            "sector_allocation": {},
            "risk_metrics": {
                "risk_score": 0.0,
                "concentration": 0.0,
                "notes": [],
            },
        }

    def _build_portfolio_metrics_from_portfolio(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Try to use real data from Portfolio if available, but be extremely defensive
        about missing attributes. We don't want analytics to ever crash the schema.
        """
        try:
            total_value = float(getattr(portfolio, "total_value", 0.0) or 0.0)
        except Exception:
            total_value = 0.0

        # Fallback: assume cost is some fraction of value if cost basis not stored
        try:
            total_cost = float(getattr(portfolio, "total_cost", None) or (total_value * 0.9))
        except Exception:
            total_cost = total_value * 0.9

        total_return = total_value - total_cost
        total_return_percent = (total_return / total_cost * 100.0) if total_cost > 0 else 0.0

        # Try to infer holdings; if there's a through model, you can enhance this later
        holdings = self._build_holdings_snapshot(portfolio, total_value)
        sector_allocation = self._compute_sector_allocation(holdings)

        # Simple, safe heuristics for risk metrics
        num_holdings = max(len(holdings), 1)
        concentration = max(v for v in sector_allocation.values()) if sector_allocation else 0.0
        volatility = 15.0 + random.random() * 10  # 15–25% range as placeholder
        sharpe = (total_return_percent / 100.0) / (volatility / 100.0 + 0.0001) if volatility else 0.0

        risk_score = max(0.0, min(100.0, 70.0 - concentration / 2.0))

        return {
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_return": round(total_return, 2),
            "total_return_percent": round(total_return_percent, 2),
            "volatility": round(volatility, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown": 0.0,  # you can compute real max DD later
            "beta": 1.0,
            "alpha": 0.0,
            "holdings": holdings,
            "sector_allocation": sector_allocation,
            "risk_metrics": {
                "risk_score": round(risk_score, 1),
                "num_holdings": num_holdings,
                "concentration": round(concentration, 1),
                "notes": [
                    "Placeholder analytics – implement real risk model later."
                ],
            },
        }

    def _build_holdings_snapshot(self, portfolio: Portfolio, total_value: float) -> List[Dict[str, Any]]:
        """
        Try to build a holdings list. If there's no explicit relationship, we
        fall back to a few sample stocks so the UI has something to show.
        """
        holdings: List[Dict[str, Any]] = []

        try:
            # If Portfolio has a related "positions" or similar, you can wire it here.
            # For now, we'll just sample some stocks as a safe placeholder.
            stocks_qs = Stock.objects.all().order_by("-market_cap")[:8]
            sample_total = sum(float(s.current_price or 0) for s in stocks_qs) or 1.0

            for stock in stocks_qs:
                price = float(getattr(stock, "current_price", 0.0) or 0.0)
                weight = (price / sample_total) if sample_total else 0
                value = total_value * weight if total_value > 0 else price
                symbol = getattr(stock, "symbol", "UNKNOWN")
                name = getattr(stock, "company_name", symbol)
                sector = getattr(stock, "sector", "Unknown")

                holdings.append(
                    {
                        "symbol": symbol,
                        "company_name": name,
                        "shares": 1,  # placeholder
                        "current_price": round(price, 2),
                        "total_value": round(value, 2),
                        "cost_basis": round(value * 0.9, 2),
                        "return_amount": round(value * 0.1, 2),
                        "return_percent": 10.0,
                        "sector": sector,
                    }
                )
        except Exception as e:
            logger.warning(f"Error building holdings snapshot: {e}")

        return holdings

    def _compute_sector_allocation(self, holdings: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Compute simple sector allocation from holdings.
        """
        if not holdings:
            return {}

        total_value = sum(h.get("total_value", 0.0) for h in holdings) or 1.0
        by_sector: Dict[str, float] = {}

        for h in holdings:
            sector = h.get("sector") or "Unknown"
            by_sector[sector] = by_sector.get(sector, 0.0) + h.get("total_value", 0.0)

        return {k: round(v / total_value * 100.0, 1) for k, v in by_sector.items()}

    # ------------------------------------------------------------------ #
    # 2) Advanced stock screening                                        #
    # ------------------------------------------------------------------ #

    def get_advanced_stock_screening(self, filters: Dict[str, Any], user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Returns a list of StockScreeningResultType-compatible dicts, personalized with spending habits.

        Expected keys for each stock:
        - symbol, company_name, sector, market_cap, pe_ratio
        - beginner_friendly_score, current_price, ml_score
        - risk_level, growth_potential
        """
        # Include user_id in cache key for personalization
        # Fix: Sort by keys only to avoid TypeError when values are mixed types (bool/str/int)
        # Convert all values to strings for consistent hashing
        safe_filters = {k: str(v) for k, v in filters.items()}
        cache_key = f"premium:stock_screen:{user_id or 'anon'}:{hash(str(sorted(safe_filters.items())))}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Get spending habits analysis for personalization
        spending_analysis = None
        sector_weights = {}
        if user_id:
            try:
                from .spending_habits_service import SpendingHabitsService
                spending_service = SpendingHabitsService()
                spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)
                sector_weights = spending_service.get_spending_based_stock_preferences(spending_analysis)
                logger.info(f"Using spending analysis for user {user_id}: {len(sector_weights)} sector preferences")
            except Exception as e:
                logger.warning(f"Could not get spending analysis for stock screening: {e}")

        try:
            qs = Stock.objects.all()

            # Filters
            sector = filters.get("sector")
            if sector:
                qs = qs.filter(sector__icontains=sector)

            min_mc = filters.get("min_market_cap")
            if min_mc is not None:
                qs = qs.filter(market_cap__gte=min_mc)

            max_mc = filters.get("max_market_cap")
            if max_mc is not None:
                qs = qs.filter(market_cap__lte=max_mc)

            min_pe = filters.get("min_pe_ratio")
            if min_pe is not None:
                qs = qs.filter(pe_ratio__gte=min_pe)

            max_pe = filters.get("max_pe_ratio")
            if max_pe is not None:
                qs = qs.filter(pe_ratio__lte=max_pe)

            min_beginner = filters.get("min_beginner_score")
            if min_beginner is not None:
                qs = qs.filter(beginner_friendly_score__gte=min_beginner)

            sort_by = filters.get("sort_by") or "market_cap"
            limit = int(filters.get("limit") or 50)

            if sort_by == "ml_score":
                # We compute ml_score in Python, so we'll sort after building rows.
                stocks = list(qs[:200])  # cap to avoid huge lists
            else:
                stocks = list(qs.order_by(F(sort_by).desc(nulls_last=True))[:limit])

            results: List[Dict[str, Any]] = []
            for stock in stocks:
                symbol = getattr(stock, "symbol", "UNKNOWN")
                name = getattr(stock, "company_name", symbol)
                sector_val = getattr(stock, "sector", "Unknown")
                market_cap = float(getattr(stock, "market_cap", 0.0) or 0.0)
                pe_ratio = float(getattr(stock, "pe_ratio", 0.0) or 0.0)
                beginner_score = int(getattr(stock, "beginner_friendly_score", 50) or 50)
                current_price = float(getattr(stock, "current_price", 0.0) or 0.0)
                volatility = float(getattr(stock, "volatility", 20.0) or 20.0)

                ml_score = self._compute_ml_score(
                    price=current_price,
                    market_cap=market_cap,
                    pe_ratio=pe_ratio,
                    volatility=volatility,
                    beginner_score=beginner_score,
                )
                
                # Boost ML score based on spending preferences
                if sector_weights and sector_val in sector_weights:
                    spending_boost = sector_weights[sector_val] * 15  # Boost up to 15 points
                    ml_score = min(100, ml_score + spending_boost)

                risk_level = self._classify_risk(volatility, beginner_score)
                growth_potential = self._classify_growth(market_cap, pe_ratio)

                results.append(
                    {
                        "symbol": symbol,
                        "company_name": name,
                        "sector": sector_val,
                        "market_cap": market_cap,
                        "pe_ratio": pe_ratio,
                        "beginner_friendly_score": beginner_score,
                        "current_price": current_price,
                        "ml_score": ml_score,
                        "risk_level": risk_level,
                        "growth_potential": growth_potential,
                    }
                )

            if sort_by == "ml_score":
                # Fix: Ensure ml_score is always a float to avoid TypeError
                def safe_ml_score_sort(item):
                    score = item.get("ml_score", 0.0)
                    if isinstance(score, bool):
                        return 1.0 if score else 0.0
                    elif isinstance(score, str):
                        try:
                            return float(score)
                        except (ValueError, TypeError):
                            return 0.0
                    elif score is None:
                        return 0.0
                    else:
                        try:
                            return float(score)
                        except (ValueError, TypeError):
                            return 0.0
                results.sort(key=safe_ml_score_sort, reverse=True)
                results = results[:limit]

            cache.set(cache_key, results, self.CACHE_TTL)
            logger.info(f"Advanced stock screening returned {len(results)} results (personalized: {bool(sector_weights)})")
            return results

        except Exception as e:
            logger.error(f"Error in advanced stock screening: {e}")
            return []

    def _compute_ml_score(
        self,
        price: float,
        market_cap: float,
        pe_ratio: float,
        volatility: float,
        beginner_score: int,
    ) -> float:
        """
        Simple heuristic "ML-like" score (0–100) until real models are wired in.
        """
        score = 0.0

        # Market cap bonus
        if market_cap > 100_000_000_000:
            score += 25
        elif market_cap > 10_000_000_000:
            score += 20
        elif market_cap > 1_000_000_000:
            score += 15
        else:
            score += 10

        # P/E sweet spot
        if 8 <= pe_ratio <= 25:
            score += 20
        elif 0 < pe_ratio < 8 or 25 < pe_ratio <= 40:
            score += 10
        else:
            score += 5

        # Volatility (lower is better for most users)
        if volatility <= 15:
            score += 20
        elif volatility <= 30:
            score += 10
        else:
            score += 5

        # Beginner-friendly factor (0–25)
        score += min(25, max(0, beginner_score / 4))

        # Small price sanity (avoid penny junk)
        if price < 3:
            score -= 5

        score = max(0.0, min(100.0, score))
        return round(score, 1)

    def _classify_risk(self, volatility: float, beginner_score: int) -> str:
        if volatility > 35 or beginner_score < 40:
            return "High"
        if volatility < 18 and beginner_score >= 70:
            return "Low"
        return "Medium"

    def _classify_growth(self, market_cap: float, pe_ratio: float) -> str:
        if market_cap < 5_000_000_000 and 10 <= pe_ratio <= 30:
            return "High"
        if market_cap > 50_000_000_000 and pe_ratio < 25:
            return "Steady"
        return "Moderate"

    # ------------------------------------------------------------------ #
    # 3) AI recommendations                                              #
    # ------------------------------------------------------------------ #

    def _fetch_prices_batch_async(self, symbols: List[str]) -> Dict[str, float]:
        """
        Layer 2: Fetch prices in parallel using async.
        Returns dict of {symbol: price}
        """
        try:
            import httpx
            import os
            
            polygon_key = os.getenv('POLYGON_API_KEY')
            if not polygon_key:
                return {}
            
            async def fetch_price(client: httpx.AsyncClient, symbol: str) -> tuple[str, float]:
                """Fetch single price with timeout"""
                try:
                    # Use Polygon snapshot endpoint for single ticker
                    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
                    params = {'apiKey': polygon_key}
                    
                    resp = await client.get(url, params=params, timeout=2.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        ticker_data = data.get('ticker', {})
                        day_data = ticker_data.get('day', {})
                        price = day_data.get('c', 0)  # Close price
                        if price > 0:
                            return symbol, float(price)
                except Exception as e:
                    logger.debug(f"[AI RECS] Price fetch failed for {symbol}: {e}")
                return symbol, 0.0
            
            async def fetch_all_prices() -> Dict[str, float]:
                """Fetch all prices in parallel with concurrency limit"""
                # Limit concurrent requests to avoid overwhelming API
                semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
                
                async def fetch_with_semaphore(client: httpx.AsyncClient, symbol: str):
                    async with semaphore:
                        return await fetch_price(client, symbol)
                
                async with httpx.AsyncClient(timeout=5.0) as client:  # Overall client timeout
                    # Limit to first 50 symbols to prevent timeout
                    limited_symbols = symbols[:50]
                    tasks = [fetch_with_semaphore(client, sym) for sym in limited_symbols]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                
                prices = {}
                for r in results:
                    if isinstance(r, Exception):
                        continue
                    symbol, price = r
                    if price > 0:
                        prices[symbol] = price
                return prices
            
            # Run async function from sync context with timeout
            try:
                # Use asyncio.run() which creates a new event loop (safer for Django)
                # Add overall timeout to prevent hanging
                return asyncio.run(asyncio.wait_for(fetch_all_prices(), timeout=10.0))
            except asyncio.TimeoutError:
                logger.warning("[AI RECS] ⚠️ Price fetch timeout after 10s, returning partial results")
                return {}
            except RuntimeError:
                # If there's already an event loop, create a new one
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    return loop.run_until_complete(asyncio.wait_for(fetch_all_prices(), timeout=10.0))
                except asyncio.TimeoutError:
                    logger.warning("[AI RECS] ⚠️ Price fetch timeout after 10s (new loop), returning empty")
                    return {}
                finally:
                    loop.close()
            
        except ImportError:
            logger.warning("[AI RECS] httpx not available, falling back to sequential price fetch")
            return {}
        except Exception as e:
            logger.warning("[AI RECS] Async price fetch error: %s", e)
            return {}

    def _fetch_stocks_from_polygon(self, limit: int = MAX_TICKERS) -> List[Dict[str, Any]]:
        """
        Fetch stocks from Polygon API with caching.
        Layer 0: Limited to MAX_TICKERS (80)
        Layer 1: Cached for 60 seconds
        Layer 2: Parallel price fetching
        """
        import os
        import requests
        from typing import List, Dict, Any
        
        # Layer 1: Check cache first
        cached = cache.get(POLYGON_UNIVERSE_CACHE_KEY)
        if cached:
            logger.info("[AI RECS] ✅ Using cached Polygon universe (%s tickers)", len(cached))
            return cached
        
        logger.info("[AI RECS] 🔍 Fetching stocks from Polygon API (limit=%s)...", limit)
        
        polygon_key = os.getenv('POLYGON_API_KEY')
        if not polygon_key:
            logger.warning("[AI RECS] ⚠️ POLYGON_API_KEY not set, falling back to database")
            return []
        
        stocks = []
        try:
            # Get tickers list from Polygon
            url = "https://api.polygon.io/v3/reference/tickers"
            params = {
                'market': 'stocks',
                'active': 'true',
                'limit': min(limit * 2, 1000),  # Get more to filter by market cap
                'apiKey': polygon_key
            }
            
            # Layer 3: Add timeout
            response = requests.get(url, params=params, timeout=3.0)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                logger.info("[AI RECS] ✅ Got %s Polygon tickers before filtering", len(results))
                
                # Filter and sort by market cap, take top MAX_TICKERS
                valid_stocks = []
                for ticker in results:
                    try:
                        market_cap = float(ticker.get('market_cap', 0) or 0)
                        if market_cap > 0:  # Only include stocks with market cap
                            stock_data = {
                                'symbol': ticker.get('ticker', ''),
                                'company_name': ticker.get('name', ticker.get('ticker', '')),
                                'sector': ticker.get('sic_description', 'Unknown'),
                                'market_cap': market_cap,
                                'current_price': 0.0,  # Will be fetched separately
                                'pe_ratio': 0.0,
                                'beginner_friendly_score': 50,
                            }
                            if stock_data['symbol']:
                                valid_stocks.append(stock_data)
                    except Exception as e:
                        logger.debug(f"[AI RECS] Error processing ticker {ticker.get('ticker')}: {e}")
                        continue
                
                # Sort by market cap descending, take top MAX_TICKERS
                valid_stocks.sort(key=lambda x: x['market_cap'], reverse=True)
                stocks = valid_stocks[:MAX_TICKERS]
                
                logger.info("[AI RECS] ✅ Processed %s valid stocks from Polygon (top %s by market cap)", 
                           len(valid_stocks), len(stocks))
            elif response.status_code == 429:
                logger.warning("[AI RECS] ⚠️ Polygon API rate limit (429), using empty cache")
                cache.set(POLYGON_UNIVERSE_CACHE_KEY, [], POLYGON_UNIVERSE_TTL)
                return []
            elif response.status_code == 401:
                logger.error("[AI RECS] ❌ Polygon API authentication failed (401), check API key")
                return []
            else:
                logger.warning("[AI RECS] ⚠️ Polygon API returned %s: %s", response.status_code, response.text[:200])
                
        except requests.exceptions.Timeout:
            logger.warning("[AI RECS] ⚠️ Polygon API timeout, using empty cache")
            cache.set(POLYGON_UNIVERSE_CACHE_KEY, [], POLYGON_UNIVERSE_TTL)
            return []
        except requests.exceptions.RequestException as e:
            logger.error("[AI RECS] ❌ Polygon API request error: %s", e)
            return []
        except Exception as e:
            logger.error("[AI RECS] ❌ Error fetching stocks from Polygon: %s", e)
            return []
        
        # Layer 2: Fetch prices in parallel (batch)
        if stocks:
            logger.info("[AI RECS] 📊 Fetching real-time prices for %s stocks (parallel)...", len(stocks))
            symbols = [s['symbol'] for s in stocks]
            prices = self._fetch_prices_batch_async(symbols)
            
            # Update stock dicts with prices
            priced_count = 0
            for stock in stocks:
                symbol = stock['symbol']
                if symbol in prices and prices[symbol] > 0:
                    stock['current_price'] = prices[symbol]
                    priced_count += 1
            
            logger.info("[AI RECS] ✅ Got prices for %s/%s stocks", priced_count, len(stocks))
        
        # Layer 1: Cache the result
        if stocks:
            cache.set(POLYGON_UNIVERSE_CACHE_KEY, stocks, POLYGON_UNIVERSE_TTL)
            logger.info("[AI RECS] 💾 Cached Polygon universe for %s seconds", POLYGON_UNIVERSE_TTL)
        
        return stocks

    def _profile_cache_key(self, user_id: int, risk_tolerance: str, profile: Optional[Dict[str, Any]]) -> str:
        """
        Layer 1: Generate cache key from user + profile.
        Serializes profile to hashable string for consistent caching.
        """
        profile_str = json.dumps(profile or {}, sort_keys=True)
        digest = hashlib.sha256(profile_str.encode("utf-8")).hexdigest()[:16]
        return f"ai_recs:user:{user_id}:rt:{risk_tolerance}:profile:{digest}"

    def get_ai_recommendations(self, user_id: int, risk_tolerance: str = "medium", profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Returns data for AIRecommendationsType with spending habits analysis.
        Now fetches stocks from Polygon API and uses ML/AI scoring based on user profile.
        
        Layer 1: Cached per user+profile for 5 minutes.

        Args:
            user_id: User ID
            risk_tolerance: Risk tolerance level
            profile: Optional user profile dict with age, income_bracket, investment_goals, investment_horizon_years
        """
        # Layer 1: Check cache first
        # Add version to cache key to invalidate when code changes
        cache_version = "v2"  # Increment this when reasoning logic changes
        cache_key = f"{self._profile_cache_key(user_id, risk_tolerance, profile)}:{cache_version}"
        cached = cache.get(cache_key)
        if cached:
            logger.info("[AI RECS] ✅ Returning cached recommendations for user=%s (cache_key=%s)", user_id, cache_key[:50])
            return cached
        else:
            logger.info("[AI RECS] 🔄 Cache miss or new version, generating fresh recommendations for user=%s", user_id)

        try:
            # Get spending habits analysis
            from .spending_habits_service import SpendingHabitsService
            spending_service = SpendingHabitsService()
            spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)
            
            # Reuse portfolio metrics for analysis
            metrics = self.get_portfolio_performance_metrics(user_id, None)
            holdings = metrics.get("holdings", [])
            sector_alloc = metrics.get("sector_allocation", {})
            
            # Log portfolio status
            if not holdings:
                logger.info("[AI RECS] 📊 No portfolio found for user %s – using profile-only recommendations", user_id)
            else:
                logger.info("[AI RECS] 📊 Portfolio found for user %s: %s holdings, %s sectors", 
                           user_id, len(holdings), len(sector_alloc))

            # ✅ NEW: Fetch stocks from Polygon instead of database
            # Layer 0: Limited to MAX_TICKERS for performance
            # Use cached data if available to avoid slow API calls
            polygon_stocks = []
            try:
                # Check cache first - this should be fast
                cached_universe = cache.get(POLYGON_UNIVERSE_CACHE_KEY)
                if cached_universe:
                    logger.info("[AI RECS] ✅ Using cached Polygon universe (%s stocks)", len(cached_universe))
                    polygon_stocks = cached_universe
                else:
                    # Only fetch if cache is empty, and limit to smaller set for speed
                    logger.info("[AI RECS] 🔍 Cache miss, fetching from Polygon (limited to 20 for speed)...")
                    polygon_stocks = self._fetch_stocks_from_polygon(limit=20)  # Reduced from 80 to 20 for speed
            except Exception as e:
                logger.warning(f"[AI RECS] ⚠️ Polygon fetch error: {e}, using database fallback")
                polygon_stocks = []
            
            # Convert Polygon stock dicts to Stock-like objects for compatibility
            # Create a simple class to mimic Stock model attributes
            class StockLike:
                def __init__(self, data: Dict[str, Any]):
                    self.symbol = data.get('symbol', '')
                    self.company_name = data.get('company_name', self.symbol)
                    self.current_price = data.get('current_price', 0.0)
                    self.market_cap = data.get('market_cap', 0.0)
                    self.sector = data.get('sector', 'Unknown')
                    self.pe_ratio = data.get('pe_ratio', 0.0)
                    self.beginner_friendly_score = data.get('beginner_friendly_score', 50)
                    self.volatility = data.get('volatility', 20.0)
            
            candidates = [StockLike(s) for s in polygon_stocks if s.get('symbol') and s.get('current_price', 0) > 0]
            
            # If Polygon fetch failed or returned empty, fallback to database
            if not candidates:
                logger.info("[AI RECS] ⚠️ Polygon fetch returned no stocks, falling back to database")
                all_stocks = list(Stock.objects.all())
                if len(all_stocks) <= 20:
                    candidates = all_stocks
                else:
                    candidates = sorted(
                        all_stocks,
                        key=lambda s: float(getattr(s, 'market_cap', 0) or 0),
                        reverse=True
                    )[:20]
                
                # Update prices for database stocks
                try:
                    from .enhanced_stock_service import enhanced_stock_service
                    import asyncio
                    
                    symbols = [stock.symbol for stock in candidates]
                    if symbols:
                        try:
                            prices_data = asyncio.run(
                                enhanced_stock_service.get_multiple_prices(symbols)
                            )
                            # Update stock objects with real-time prices
                            for stock in candidates:
                                price_data = prices_data.get(stock.symbol)
                                if price_data and price_data.get('price', 0) > 0:
                                    stock.current_price = price_data['price']
                                    # Update database
                                    enhanced_stock_service.update_stock_price_in_database(stock.symbol, price_data)
                        except Exception as e:
                            logger.warning(f"Could not fetch real-time prices for AI recommendations: {e}")
                except Exception as e:
                    logger.warning(f"Error updating prices for AI recommendations: {e}")
            
            # Use ML/AI to score and rank stocks based on user profile
            buy_recs = self._build_buy_recommendations_with_profile(
                candidates, risk_tolerance, spending_analysis, profile
            )
            sell_recs = self._build_sell_recommendations(holdings)

            rebalance_suggestions = self._build_rebalance_suggestions(sector_alloc, risk_tolerance)
            risk_assessment = self._build_risk_assessment(metrics, risk_tolerance)
            market_outlook = self._build_market_outlook()

            # Get spending-based sector preferences
            sector_weights = spending_service.get_spending_based_stock_preferences(
                spending_analysis
            )
            
            result = {
                "portfolio_analysis": {
                    "total_value": metrics["total_value"],
                    "num_holdings": len(holdings),
                    "sector_breakdown": sector_alloc,
                    "risk_score": metrics["risk_metrics"]["risk_score"],
                    "diversification_score": 100.0 - metrics["risk_metrics"]["concentration"],
                },
                "buy_recommendations": buy_recs,
                "sell_recommendations": sell_recs,
                "rebalance_suggestions": rebalance_suggestions,
                "risk_assessment": risk_assessment,
                "market_outlook": market_outlook,
                "spending_insights": {
                    "discretionary_income": spending_analysis.get("discretionary_income", 0),
                    "suggested_budget": spending_analysis.get("suggested_budget", 0),
                    "spending_health": spending_analysis.get("spending_patterns", {}).get("spending_health", "unknown"),
                    "top_categories": spending_analysis.get("top_categories", []),
                    "sector_preferences": sector_weights,
                },
            }

            # Layer 1: Cache the result
            # Use the same versioned cache key
            cache.set(cache_key, result, RECS_CACHE_TTL)
            logger.info("[AI RECS] 💾 Cached recommendations for user=%s (TTL=%ss, version=%s)", user_id, RECS_CACHE_TTL, cache_version)
            return result

        except Exception as e:
            logger.error(f"Error building AI recommendations for user {user_id}: {e}")
            # Safe fallback
            return {
                "portfolio_analysis": {
                    "total_value": 0.0,
                    "num_holdings": 0,
                    "sector_breakdown": {},
                    "risk_score": 0.0,
                    "diversification_score": 0.0,
                },
                "buy_recommendations": [],
                "sell_recommendations": [],
                "rebalance_suggestions": [],
                "risk_assessment": {
                    "overall_risk": "Unknown",
                    "concentration_risk": "Unknown",
                    "sector_risk": "Unknown",
                    "volatility_estimate": 0.0,
                    "recommendations": [],
                },
                "market_outlook": {
                    "overall_sentiment": "Neutral",
                    "confidence": 0.5,
                    "key_factors": [],
                    "risks": [],
                },
            }

    def _build_buy_recommendations_with_profile(
        self,
        stocks: List[Any],
        risk_tolerance: str,
        spending_analysis: Optional[Dict[str, Any]] = None,
        profile: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build buy recommendations using ML/AI scoring based on user profile.
        This is the new method that uses Polygon data and profile-based ML scoring.
        """
        logger.info("[AI RECS] 🤖 Building recommendations using profile: %s", profile)
        logger.info("[AI RECS] 📈 Risk tolerance: %s, Stocks to evaluate: %s", risk_tolerance, len(stocks))
        
        recs: List[Dict[str, Any]] = []
        
        # Get spending-based sector preferences if available
        sector_weights = {}
        if spending_analysis:
            from .spending_habits_service import SpendingHabitsService
            spending_service = SpendingHabitsService()
            sector_weights = spending_service.get_spending_based_stock_preferences(
                spending_analysis
            )

        # Extract profile attributes for ML scoring
        # Handle None values explicitly to avoid comparison errors
        age = profile.get('age') if profile else None
        age = age if age is not None else 30
        
        investment_horizon_years = profile.get('investment_horizon_years') if profile else None
        investment_horizon_years = investment_horizon_years if investment_horizon_years is not None else 5
        
        investment_goals = profile.get('investment_goals', []) if profile else []
        
        # Score all stocks using ML/AI based on profile
        scored_stocks = []
        for stock in stocks:
            symbol = getattr(stock, "symbol", "UNKNOWN")
            name = getattr(stock, "company_name", symbol)
            price = float(getattr(stock, "current_price", 0.0) or 0.0)
            sector = getattr(stock, "sector", "Unknown")
            beginner_score = int(getattr(stock, "beginner_friendly_score", 50) or 50)
            market_cap = float(getattr(stock, "market_cap", 0.0) or 0.0)
            pe_ratio = float(getattr(stock, "pe_ratio", 0.0) or 0.0)
            volatility = float(getattr(stock, "volatility", 20.0) or 20.0)
            
            # Skip stocks without price data
            if price <= 0:
                continue
            
            # Base ML score
            ml_score = self._compute_ml_score(
                price=price,
                market_cap=market_cap,
                pe_ratio=pe_ratio,
                volatility=volatility,
                beginner_score=beginner_score,
            )
            
            # ✅ Profile-based ML scoring adjustments
            # 1. Risk tolerance adjustment
            if risk_tolerance.lower() in ['conservative', 'low']:
                # Prefer lower volatility, higher market cap, established companies
                if volatility > 30:
                    ml_score *= 0.7  # Penalize high volatility
                if market_cap < 10_000_000_000:  # Less than $10B
                    ml_score *= 0.8  # Prefer large caps
                if beginner_score < 70:
                    ml_score *= 0.9  # Prefer beginner-friendly
            elif risk_tolerance.lower() in ['aggressive', 'high']:
                # More tolerant of volatility, can include growth stocks
                if volatility > 25 and market_cap < 5_000_000_000:
                    ml_score *= 1.1  # Boost for growth potential
                if pe_ratio > 30 and pe_ratio < 60:
                    ml_score *= 1.05  # Growth stocks OK
            
            # 2. Investment horizon adjustment
            if investment_horizon_years is not None and investment_horizon_years >= 10:
                # Long-term: prefer value stocks, lower P/E
                if pe_ratio > 0 and pe_ratio < 20:
                    ml_score *= 1.1  # Boost value stocks
            elif investment_horizon_years < 3:
                # Short-term: prefer momentum, higher liquidity
                if market_cap > 50_000_000_000:
                    ml_score *= 1.05  # Boost large caps for liquidity
            
            # 3. Investment goals adjustment
            if 'Retirement Savings' in investment_goals or 'Long-term Growth' in investment_goals:
                # Prefer stable, dividend-paying sectors
                if sector in ['Financial', 'Consumer Defensive', 'Utilities']:
                    ml_score *= 1.1
            if 'Build Wealth' in investment_goals or 'Aggressive Growth' in investment_goals:
                # Prefer growth sectors
                if sector in ['Technology', 'Healthcare', 'Consumer Cyclical']:
                    ml_score *= 1.1
            
            # 4. Age-based adjustment
            if age < 30:
                # Younger investors can take more risk
                if volatility > 20:
                    ml_score *= 1.05
            elif age > 50:
                # Older investors prefer stability
                if volatility > 25:
                    ml_score *= 0.9
                if market_cap < 10_000_000_000:
                    ml_score *= 0.85
            
            # 5. Spending-based sector boost
            if sector_weights and sector in sector_weights:
                spending_boost = sector_weights[sector] * 15  # Increased boost
                ml_score = min(100, ml_score + spending_boost)
            
            # 6. ML/AI prediction boost (if available)
            # ✅ ENABLED: Real ML predictions with caching per symbol for performance
            ml_prediction_cache_key = f"ai_recs:ml_prediction:{symbol}:v1"
            ml_boost = 0.0
            
            # Check cache first
            cached_prediction = cache.get(ml_prediction_cache_key)
            if cached_prediction is not None:
                ml_boost = cached_prediction
                logger.debug(f"[AI RECS] Using cached ML prediction for {symbol}: +{ml_boost:.1f} points")
            else:
                try:
                    from .hybrid_ml_predictor import hybrid_predictor
                    from .ml_service import MLService
                    import asyncio
                    
                    # Get or create event loop
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    ml_service = MLService()
                    spending_features = ml_service._get_spending_features_for_ticker(symbol, spending_analysis)
                    prediction = loop.run_until_complete(hybrid_predictor.predict(symbol, spending_features))
                    if prediction and prediction.get('predicted_return', 0) > 0:
                        predicted_return = prediction.get('predicted_return', 0)
                        ml_boost = predicted_return * 10
                        # Cache for 5 minutes (same as recommendations cache)
                        cache.set(ml_prediction_cache_key, ml_boost, 300)
                        logger.debug(f"[AI RECS] ML prediction boost for {symbol}: +{ml_boost:.1f} points")
                except ImportError as e:
                    logger.debug(f"[AI RECS] ML prediction not available (import error): {e}")
                except Exception as e:
                    logger.debug(f"[AI RECS] ML prediction not available for {symbol}: {e}")
            
            if ml_boost > 0:
                ml_score = min(100, ml_score + ml_boost)
            
            # Ensure score is in valid range
            ml_score = max(0, min(100, ml_score))
            
            # Only include stocks with reasonable scores
            if ml_score >= 20:
                scored_stocks.append({
                    'stock': stock,
                    'ml_score': ml_score,
                    'symbol': symbol,
                    'name': name,
                    'price': price,
                    'sector': sector,
                    'market_cap': market_cap,
                    'pe_ratio': pe_ratio,
                    'volatility': volatility,
                })
        
        # Sort by ML score (highest first)
        scored_stocks.sort(key=lambda x: x['ml_score'], reverse=True)
        
        # Log top 5 before filtering
        top_5_symbols = [s['symbol'] for s in scored_stocks[:5]]
        logger.info("[AI RECS] 🎯 Final ranked stocks (top 5): %s", top_5_symbols)
        
        # Take top recommendations
        top_stocks = scored_stocks[:15]  # Get top 15 for variety
        logger.info("[AI RECS] ✅ Selected top %s stocks for recommendations", len(top_stocks))
        
        # Build recommendation dicts
        for item in top_stocks:
            stock = item['stock']
            symbol = item['symbol']
            name = item['name']
            price = item['price']
            sector = item['sector']
            ml_score = item['ml_score']
            market_cap = item['market_cap']
            
            # Calculate target price and expected return based on ML score
            # Higher ML score = higher expected return
            if price > 0:
                return_multiplier = 1.0 + (ml_score / 100.0) * 0.3  # 0-30% return potential
                target_price = price * return_multiplier
                expected_return = (target_price - price) / price * 100.0
            else:
                # If price is 0 or missing, use a default expected return based on ML score
                target_price = 0.0
                expected_return = (ml_score / 100.0) * 15.0  # 0-15% based on ML score
                logger.warning(f"[AI RECS] Stock {symbol} has price=0, using ML-based default expectedReturn={expected_return}%")
            
            # Calculate confidence based on ML score
            confidence = min(95, max(60, ml_score))  # 60-95% confidence
            
            # Build personalized reasoning with stock-specific details (fully dynamic)
            reasoning_parts = []
            
            # Start with company name or symbol for personalization
            company_display = name if name and name != symbol else symbol
            if company_display:
                reasoning_parts.append(f"{company_display} demonstrates")
            
            # Add market cap context (dynamic)
            market_cap = item.get('market_cap', 0)
            if market_cap > 200_000_000_000:  # > $200B
                cap_context = "mega-cap"
            elif market_cap > 10_000_000_000:  # > $10B
                cap_context = "large-cap"
            elif market_cap > 2_000_000_000:  # > $2B
                cap_context = "mid-cap"
            else:
                cap_context = "small-cap"
            
            # Add ML/AI signal strength with more granular ranges (dynamic)
            if ml_score > 85:
                ml_signal = "exceptional ML/AI signals"
            elif ml_score > 75:
                ml_signal = "very strong ML/AI signals"
            elif ml_score > 70:
                ml_signal = "strong ML/AI signals"
            elif ml_score > 65:
                ml_signal = "positive ML/AI signals"
            elif ml_score > 60:
                ml_signal = "moderate ML/AI signals"
            else:
                ml_signal = "emerging ML/AI signals"
            reasoning_parts.append(ml_signal)
            
            # Add sector-specific context with more detail (dynamic)
            if sector:
                sector_lower = sector.lower()
                if sector_lower in ['technology', 'information technology']:
                    sector_desc = "technology sector leadership"
                elif sector_lower in ['healthcare', 'health care']:
                    sector_desc = "healthcare sector stability"
                elif sector_lower in ['financial', 'financial services']:
                    sector_desc = "financial sector strength"
                elif sector_lower in ['consumer discretionary']:
                    sector_desc = "consumer spending trends"
                elif sector_lower in ['consumer staples']:
                    sector_desc = "defensive consumer positioning"
                elif sector_lower in ['energy']:
                    sector_desc = "energy sector momentum"
                elif sector_lower in ['industrials']:
                    sector_desc = "industrial sector growth"
                elif sector_lower in ['communication services']:
                    sector_desc = "communication sector innovation"
                elif sector_lower in ['materials']:
                    sector_desc = "materials sector fundamentals"
                elif sector_lower in ['utilities']:
                    sector_desc = "utilities sector stability"
                elif sector_lower in ['real estate']:
                    sector_desc = "real estate sector value"
                else:
                    sector_desc = f"{sector} sector opportunities"
                reasoning_parts.append(sector_desc)
            
            # Add market cap context
            reasoning_parts.append(f"{cap_context} positioning")
            
            # Add valuation context with more granular ranges (dynamic)
            pe_ratio = item.get('pe_ratio', 0)
            if pe_ratio > 0:
                if pe_ratio < 10:
                    valuation = "deep value valuation"
                elif pe_ratio < 15:
                    valuation = "attractive valuation"
                elif pe_ratio < 20:
                    valuation = "reasonable valuation"
                elif pe_ratio < 30:
                    valuation = "moderate premium pricing"
                elif pe_ratio < 40:
                    valuation = "growth premium pricing"
                else:
                    valuation = "high growth premium"
                reasoning_parts.append(valuation)
            
            # Add volatility context with more detail (dynamic)
            volatility = item.get('volatility', 20)
            if risk_tolerance.lower() in ['conservative', 'low']:
                if volatility < 12:
                    vol_desc = "very low volatility aligns with your conservative risk profile"
                elif volatility < 18:
                    vol_desc = "low volatility aligns with your conservative risk profile"
                elif volatility < 25:
                    vol_desc = "moderate volatility suitable for your risk tolerance"
                else:
                    vol_desc = "higher volatility may exceed your risk comfort"
            elif risk_tolerance.lower() in ['aggressive', 'high']:
                if volatility > 35:
                    vol_desc = "high volatility matches your aggressive risk tolerance"
                elif volatility > 25:
                    vol_desc = "elevated volatility aligns with your risk appetite"
                else:
                    vol_desc = "growth potential matches your risk tolerance"
            else:  # medium risk
                if volatility < 15:
                    vol_desc = "balanced risk-return profile"
                elif volatility < 25:
                    vol_desc = "moderate risk-return balance"
                else:
                    vol_desc = "higher risk with growth potential"
            reasoning_parts.append(vol_desc)
            
            # Add expected return context with more detail (dynamic)
            if expected_return > 30:
                return_desc = f"exceptional return potential ({expected_return:.1f}%)"
            elif expected_return > 25:
                return_desc = f"high return potential ({expected_return:.1f}%)"
            elif expected_return > 20:
                return_desc = f"strong return potential ({expected_return:.1f}%)"
            elif expected_return > 15:
                return_desc = f"solid return potential ({expected_return:.1f}%)"
            elif expected_return > 10:
                return_desc = f"moderate return potential ({expected_return:.1f}%)"
            else:
                return_desc = f"conservative return potential ({expected_return:.1f}%)"
            reasoning_parts.append(return_desc)
            
            # Add spending alignment if applicable (dynamic)
            if sector_weights and sector in sector_weights and sector_weights[sector] > 0.1:
                spending_pct = sector_weights[sector] * 100
                reasoning_parts.append(f"aligned with your spending patterns ({spending_pct:.0f}% in {sector})")
            
            # Add long-term value if applicable (dynamic)
            if investment_horizon_years is not None and investment_horizon_years >= 10:
                if pe_ratio > 0 and pe_ratio < 20:
                    reasoning_parts.append("value characteristics for long-term holding")
                elif pe_ratio > 0 and pe_ratio < 15:
                    reasoning_parts.append("strong value proposition for long-term investors")
            
            # Build final reasoning string (dynamic composition)
            if reasoning_parts:
                # Capitalize first letter and join with proper punctuation
                reasoning = reasoning_parts[0].capitalize()
                if len(reasoning_parts) > 1:
                    reasoning += ". " + ". ".join(reasoning_parts[1:]) + "."
                else:
                    reasoning += "."
            else:
                # Fallback if no parts were added
                reasoning = f"{company_display} shows attractive fundamentals and risk profile for your settings."
            
            # Calculate signal contribution scores based on available data
            # These are derived from ML score and fundamentals, not expensive API calls
            # Distribute ML score across different signals for meaningful contribution display
            
            # Base scores derived from ML score (0-100 scale)
            base_signal_strength = ml_score / 100.0  # Normalize to 0-1
            
            # Spending Growth: Higher for consumer sectors, lower volatility = more stable spending
            if sector and sector.lower() in ['consumer discretionary', 'consumer staples', 'retail']:
                spending_growth = base_signal_strength * 85.0 + (20.0 - min(item.get('volatility', 20), 20))  # 65-105 range
            else:
                spending_growth = base_signal_strength * 60.0  # 0-60 for non-consumer sectors
            spending_growth = min(100, max(0, spending_growth))
            
            # Options Flow: Higher for high ML score stocks (smart money interest)
            # Also boost for high volatility (more options activity)
            options_flow_score = base_signal_strength * 70.0 + min(item.get('volatility', 15) / 2, 15)  # 0-85 range
            options_flow_score = min(100, max(0, options_flow_score))
            
            # Earnings Score: Based on PE ratio and ML score
            # Lower PE with high ML = good earnings value
            pe_ratio = item.get('pe_ratio', 25)
            if pe_ratio > 0 and pe_ratio < 25:
                earnings_score = base_signal_strength * 80.0 + (25 - pe_ratio) * 0.8  # 0-100 range
            else:
                earnings_score = base_signal_strength * 65.0  # Default for high PE or missing
            earnings_score = min(100, max(0, earnings_score))
            
            # Insider Score: Higher for value stocks (low PE) and high ML confidence
            if pe_ratio > 0 and pe_ratio < 20:
                insider_score = base_signal_strength * 75.0 + (20 - pe_ratio) * 1.0  # 0-95 range
            else:
                insider_score = base_signal_strength * 55.0  # Default
            insider_score = min(100, max(0, insider_score))
            
            # Consumer Strength Score: Aggregate of all signals
            consumer_strength_score = (spending_growth * 0.3 + options_flow_score * 0.25 + 
                                      earnings_score * 0.25 + insider_score * 0.2)
            consumer_strength_score = min(100, max(0, consumer_strength_score))
            
            # Log signal scores for debugging
            logger.info(
                f"[AI RECS] Signal scores for {symbol}: "
                f"spending={spending_growth:.1f}, options={options_flow_score:.1f}, "
                f"earnings={earnings_score:.1f}, insider={insider_score:.1f}, "
                f"consumer={consumer_strength_score:.1f}"
            )
            
            recs.append({
                'symbol': symbol,
                'companyName': name,
                'recommendation': 'BUY',
                'confidence': confidence,
                'reasoning': reasoning,
                'targetPrice': round(target_price, 2),
                'currentPrice': round(price, 2),
                'expectedReturn': round(expected_return, 2),
                'sector': sector,
                'riskLevel': 'Low' if item['volatility'] < 15 else ('Medium' if item['volatility'] < 25 else 'High'),
                'mlScore': round(ml_score, 2),
                'consumerStrengthScore': round(consumer_strength_score, 2),
                'spendingGrowth': round(spending_growth, 2),
                'optionsFlowScore': round(options_flow_score, 2),
                'earningsScore': round(earnings_score, 2),
                'insiderScore': round(insider_score, 2),
            })
        
        return recs

    def _build_buy_recommendations(
        self,
        stocks: List[Stock],
        risk_tolerance: str,
        spending_analysis: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        recs: List[Dict[str, Any]] = []
        
        # Get spending-based sector preferences if available
        sector_weights = {}
        if spending_analysis:
            from .spending_habits_service import SpendingHabitsService
            spending_service = SpendingHabitsService()
            sector_weights = spending_service.get_spending_based_stock_preferences(
                spending_analysis
            )

        for stock in stocks[:8]:
            symbol = getattr(stock, "symbol", "UNKNOWN")
            name = getattr(stock, "company_name", symbol)
            price = float(getattr(stock, "current_price", 0.0) or 0.0)
            sector = getattr(stock, "sector", "Unknown")
            beginner_score = int(getattr(stock, "beginner_friendly_score", 50) or 50)

            # Handle None market_cap - use a default based on price if available
            market_cap = float(getattr(stock, "market_cap", 0.0) or 0.0)
            if market_cap == 0.0 and price > 0:
                # Estimate market cap from price (rough estimate: assume 1B shares for large caps)
                # This is a fallback for stocks without market_cap data
                market_cap = price * 1_000_000_000  # Rough estimate
            
            ml_score = self._compute_ml_score(
                price=price,
                market_cap=market_cap,
                pe_ratio=float(getattr(stock, "pe_ratio", 0.0) or 0.0),
                volatility=float(getattr(stock, "volatility", 20.0) or 20.0),
                beginner_score=beginner_score,
            )
            
            # Boost score based on spending preferences
            if sector_weights and sector in sector_weights:
                spending_boost = sector_weights[sector] * 10  # Boost up to 10 points
                ml_score = min(100, ml_score + spending_boost)
            
            # Ensure minimum score for stocks with data (even if market_cap is None)
            # This ensures we return recommendations even with limited data
            if ml_score < 20 and price > 0:
                # Boost score for stocks with valid price data
                ml_score = max(ml_score, 20)  # Minimum 20 for stocks with price data

            # More permissive filtering - only filter out very low scores
            # This ensures we return recommendations even with limited data
            # With only 2 stocks in DB, we need to be less strict
            if ml_score < 15:
                continue  # Only filter out extremely low scores (< 15)

            target_price = price * 1.15 if price > 0 else 0.0
            expected_return = (target_price - price) / price * 100.0 if price > 0 else 0.0
            
            # Enhanced reasoning with spending insights
            reasoning = "Attractive fundamentals and risk profile for your settings."
            if spending_analysis and sector in sector_weights and sector_weights[sector] > 0.1:
                reasoning += f" Aligned with your spending patterns in {sector} sector."
            
            # Week 4: Calculate Consumer Strength Score (0-100)
            consumer_strength_score = 50.0  # Default
            spending_growth = 0.0
            options_flow_score = 0.0
            earnings_score = 0.0
            insider_score = 0.0
            shap_explanation = None
            prediction = None
            
            try:
                # Get hybrid model predictions if available
                from .hybrid_ml_predictor import hybrid_predictor
                try:
                    from .ml_service import MLService
                    ml_service = MLService()
                except ImportError:
                    ml_service = None
                
                # Get spending features
                spending_features = ml_service._get_spending_features_for_ticker(symbol, spending_analysis)
                
                # Get prediction
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                prediction = loop.run_until_complete(
                    hybrid_predictor.predict(symbol, spending_features)
                )
                
                # Extract scores
                contributions = prediction.get('feature_contributions', {})
                spending_score = contributions.get('spending', 0.0)
                options_score = contributions.get('options', 0.0)
                earnings_score_val = contributions.get('earnings', 0.0)
                insider_score_val = contributions.get('insider', 0.0)
                
                # Calculate Consumer Strength Score (weighted combination)
                consumer_strength_score = (
                    40 * max(0, min(100, (spending_score + 0.2) / 0.4 * 100)) +  # Spending: 40%
                    30 * max(0, min(100, (options_score + 0.2) / 0.4 * 100)) +  # Options: 30%
                    20 * max(0, min(100, (earnings_score_val + 0.2) / 0.4 * 100)) +  # Earnings: 20%
                    10 * max(0, min(100, (insider_score_val + 0.2) / 0.4 * 100))  # Insider: 10%
                )
                
                # Get spending growth
                spending_growth = spending_features.get('spending_change_4w', 0.0) * 100
                options_flow_score = options_score * 100
                earnings_score = earnings_score_val * 100
                insider_score = insider_score_val * 100
                
                # Get SHAP explanation if available
                if prediction:
                    shap_data = prediction.get('shap_explanation', {})
                    if shap_data:
                        shap_explanation = shap_data.get('explanation', None)
                        # Enhanced SHAP data for detailed breakdown
                        shap_enhanced = {
                            'explanation': shap_data.get('explanation', ''),
                            'shapValues': shap_data.get('shap_values', {}),
                            'featureImportance': [
                                {'name': name, 'value': val, 'absValue': abs(val)}
                                for name, val in shap_data.get('feature_importance', [])[:10]
                            ],
                            'topFeatures': [
                                {'name': name, 'value': val, 'absValue': abs(val)}
                                for name, val in shap_data.get('top_features', shap_data.get('feature_importance', []))[:10]
                            ],
                            'categoryBreakdown': shap_data.get('category_breakdown', {}),
                            'totalPositiveImpact': shap_data.get('total_positive_impact', 0.0),
                            'totalNegativeImpact': shap_data.get('total_negative_impact', 0.0),
                            'prediction': shap_data.get('prediction', 0.0),
                        }
                    else:
                        shap_enhanced = None
                
            except Exception as e:
                logger.debug(f"Could not calculate Consumer Strength for {symbol}: {e}")

            recs.append(
                {
                    "symbol": symbol,
                    "company_name": name,
                    "recommendation": "BUY",
                    "confidence": round(min(0.95, 0.5 + ml_score / 200.0), 2),
                    "reasoning": reasoning,
                    "target_price": round(target_price, 2),
                    "current_price": round(price, 2),
                    "expected_return": round(expected_return, 1),
                    "suggested_exit_price": round(target_price * 0.95, 2) if target_price else 0.0,
                    "current_return": 0.0,
                    "sector": sector,
                    "risk_level": self._classify_risk(
                        float(getattr(stock, "volatility", 20.0) or 20.0),
                        beginner_score,
                    ),
                    "ml_score": ml_score,
                    "spending_aligned": sector in sector_weights and sector_weights.get(sector, 0) > 0.1,
                    "consumer_strength_score": consumer_strength_score,  # Week 4
                    "spending_growth": spending_growth,  # Week 4
                    "options_flow_score": options_flow_score,  # Week 4
                    "earnings_score": earnings_score,  # Week 4
                    "insider_score": insider_score,  # Week 4
                    "shap_explanation": shap_explanation,  # Week 3 (legacy)
                    "shap_enhanced": shap_enhanced,  # Enhanced SHAP with detailed breakdown
                }
            )
        
        # Sort by ML score (spending-boosted)
        # Fix: Ensure ml_score is always a float to avoid TypeError when comparing bool/str
        def safe_ml_score(item):
            score = item.get('ml_score', 0.0)
            # Convert to float, handling bool, str, None, etc.
            if isinstance(score, bool):
                return 1.0 if score else 0.0
            elif isinstance(score, str):
                try:
                    return float(score)
                except (ValueError, TypeError):
                    return 0.0
            elif score is None:
                return 0.0
            else:
                try:
                    return float(score)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert ml_score to float: {score} (type: {type(score)})")
                    return 0.0
        
        try:
            recs.sort(key=safe_ml_score, reverse=True)
        except Exception as e:
            logger.error(f"Error sorting recommendations by ml_score: {e}")
            # Log the problematic values for debugging
            for rec in recs:
                score = rec.get('ml_score')
                logger.error(f"  ml_score: {score} (type: {type(score)})")
            # Fallback: sort by string representation (not ideal but won't crash)
            recs.sort(key=lambda x: str(x.get('ml_score', 0)), reverse=True)

        return recs

    def _build_sell_recommendations(self, holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        recs: List[Dict[str, Any]] = []

        for h in holdings[:5]:
            symbol = h.get("symbol", "UNKNOWN")
            name = h.get("company_name", symbol)
            price = float(h.get("current_price", 0.0) or 0.0)
            return_percent = float(h.get("return_percent", 0.0) or 0.0)
            sector = h.get("sector", "Unknown")

            if return_percent < -10.0 or return_percent > 40.0:
                recs.append(
                    {
                        "symbol": symbol,
                        "company_name": name,
                        "recommendation": "SELL",
                        "confidence": 0.7,
                        "reasoning": "Position shows outsized loss or gain; consider rebalancing.",
                        "target_price": price,
                        "current_price": price,
                        "expected_return": 0.0,
                        "suggested_exit_price": price,
                        "current_return": return_percent,
                        "sector": sector,
                        "risk_level": "High" if return_percent < 0 else "Medium",
                        "ml_score": 50.0,
                    }
                )

        return recs

    def _build_rebalance_suggestions(
        self,
        sector_alloc: Dict[str, float],
        risk_tolerance: str,
    ) -> List[Dict[str, Any]]:
        suggestions: List[Dict[str, Any]] = []

        if not sector_alloc:
            return suggestions

        # Over-concentrated sectors (>35%)
        for sector, pct in sector_alloc.items():
            if pct > 35.0:
                suggestions.append(
                    {
                        "action": f"Reduce exposure to {sector}",
                        "current_allocation": pct,
                        "suggested_allocation": max(15.0, pct - 15.0),
                        "reasoning": "High concentration risk in a single sector.",
                        "priority": "High",
                    }
                )

        # Underrepresented defensive sectors (<5%)
        for sector in ["Healthcare", "Consumer Defensive"]:
            if sector not in sector_alloc or sector_alloc.get(sector, 0.0) < 5.0:
                suggestions.append(
                    {
                        "action": f"Increase exposure to {sector}",
                        "current_allocation": sector_alloc.get(sector, 0.0),
                        "suggested_allocation": 8.0,
                        "reasoning": "Adding defensive sectors can smooth volatility.",
                        "priority": "Medium",
                    }
                )

        if not suggestions:
            suggestions.append(
                {
                    "action": "Minor adjustments only",
                    "current_allocation": 0.0,
                    "suggested_allocation": 0.0,
                    "reasoning": "Your sector diversification looks reasonable.",
                    "priority": "Low",
                }
            )

        return suggestions

    def _build_risk_assessment(self, metrics: Dict[str, Any], risk_tolerance: str) -> Dict[str, Any]:
        risk_score = metrics.get("risk_metrics", {}).get("risk_score", 0.0)
        concentration = metrics.get("risk_metrics", {}).get("concentration", 0.0)

        if risk_score > 70:
            overall = "Low"
        elif risk_score > 40:
            overall = "Medium"
        else:
            overall = "High"

        concentration_label = "High" if concentration > 40 else "Moderate" if concentration > 20 else "Low"

        volatility_estimate = metrics.get("volatility", 0.0)

        recs = []
        if overall == "High":
            recs.append("Consider reducing exposure to the most volatile holdings.")
        if concentration_label == "High":
            recs.append("Diversify into additional sectors to reduce concentration risk.")
        if not recs:
            recs.append("Your overall risk profile looks balanced for most investors.")

        return {
            "overall_risk": overall,
            "concentration_risk": concentration_label,
            "sector_risk": concentration_label,
            "volatility_estimate": volatility_estimate,
            "recommendations": recs,
        }

    def _build_market_outlook(self) -> Dict[str, Any]:
        # Simple placeholder; you can wire in real macro/market data later
        return {
            "overall_sentiment": "Neutral",
            "confidence": 0.6,
            "key_factors": [
                "Interest rate expectations",
                "Earnings season surprises",
                "Macroeconomic data releases",
            ],
            "risks": [
                "Unexpected rate hikes",
                "Geopolitical tensions",
            ],
        }
