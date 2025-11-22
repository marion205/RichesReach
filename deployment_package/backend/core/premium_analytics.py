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
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.db.models import F, FloatField, Sum
from django.db.models.functions import Coalesce
from django.core.cache import cache
from django.utils import timezone

from .models import Portfolio, Stock

logger = logging.getLogger(__name__)


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
        cache_key = f"premium:stock_screen:{user_id or 'anon'}:{hash(str(sorted(filters.items())))}"
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
                results.sort(key=lambda x: x["ml_score"], reverse=True)
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

    def get_ai_recommendations(self, user_id: int, risk_tolerance: str = "medium") -> Dict[str, Any]:
        """
        Returns data for AIRecommendationsType with spending habits analysis:

        {
          portfolio_analysis: { ... },
          buy_recommendations: [ ... ],
          sell_recommendations: [ ... ],
          rebalance_suggestions: [ ... ],
          risk_assessment: { ... },
          market_outlook: { ... },
          spending_insights: { ... },
          suggested_budget: float
        }
        """
        cache_key = f"premium:ai_recommendations:{user_id}:{risk_tolerance}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Get spending habits analysis
            from .spending_habits_service import SpendingHabitsService
            spending_service = SpendingHabitsService()
            spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)
            
            # Reuse portfolio metrics for analysis
            metrics = self.get_portfolio_performance_metrics(user_id, None)
            holdings = metrics.get("holdings", [])
            sector_alloc = metrics.get("sector_allocation", {})

            # Choose a few candidate stocks from DB for buy/sell lists
            # Apply spending-based preferences to stock selection
            candidates = list(Stock.objects.all().order_by("-market_cap")[:20])
            
            # Update prices with real-time data
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
            
            buy_recs = self._build_buy_recommendations(
                candidates, risk_tolerance, spending_analysis
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

            cache.set(cache_key, result, self.CACHE_TTL)
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

            ml_score = self._compute_ml_score(
                price=price,
                market_cap=float(getattr(stock, "market_cap", 0.0) or 0.0),
                pe_ratio=float(getattr(stock, "pe_ratio", 0.0) or 0.0),
                volatility=float(getattr(stock, "volatility", 20.0) or 20.0),
                beginner_score=beginner_score,
            )
            
            # Boost score based on spending preferences
            if sector_weights and sector in sector_weights:
                spending_boost = sector_weights[sector] * 10  # Boost up to 10 points
                ml_score = min(100, ml_score + spending_boost)

            if risk_tolerance == "low" and ml_score < 60:
                continue
            if risk_tolerance == "high" and ml_score < 40:
                # high risk tolerance can accept lower score; still filter out really bad
                continue

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
        recs.sort(key=lambda x: x['ml_score'], reverse=True)

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
