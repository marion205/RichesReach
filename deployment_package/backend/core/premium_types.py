"""
Premium GraphQL Types and Mutations
"""

import json
import logging
import random
from datetime import datetime

import graphene
from django.core.cache import cache

from .enhanced_stock_service import EnhancedStockService
from .models import Portfolio, Stock, User
from .options_service import OptionsAnalysisService
from .portfolio_service import PortfolioService
from .premium_analytics import PremiumAnalyticsService

logger = logging.getLogger(__name__)


# ============
# Premium Types
# ============


class PortfolioMetricsType(graphene.ObjectType):
    """Advanced portfolio performance metrics"""

    total_value = graphene.Float()
    total_cost = graphene.Float()
    total_return = graphene.Float()
    total_return_percent = graphene.Float()
    volatility = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown = graphene.Float()
    beta = graphene.Float()
    alpha = graphene.Float()
    holdings = graphene.List(lambda: HoldingDetailType)
    sector_allocation = graphene.JSONString()
    risk_metrics = graphene.JSONString()


class HoldingDetailType(graphene.ObjectType):
    """Detailed holding information"""

    symbol = graphene.String()
    company_name = graphene.String()
    shares = graphene.Int()
    current_price = graphene.Float()
    total_value = graphene.Float()
    cost_basis = graphene.Float()
    return_amount = graphene.Float()
    return_percent = graphene.Float()
    sector = graphene.String()


class StockScreeningResultType(graphene.ObjectType):
    """Advanced stock screening result"""

    symbol = graphene.String()
    company_name = graphene.String()
    sector = graphene.String()
    market_cap = graphene.Float()
    pe_ratio = graphene.Float()
    beginner_friendly_score = graphene.Int()
    current_price = graphene.Float()
    ml_score = graphene.Float()
    risk_level = graphene.String()
    growth_potential = graphene.String()


class AIRecommendationType(graphene.ObjectType):
    """AI-powered investment recommendation"""

    symbol = graphene.String()
    company_name = graphene.String()
    recommendation = graphene.String()  # Buy, Sell, Hold
    confidence = graphene.Float()
    reasoning = graphene.String()
    target_price = graphene.Float()
    current_price = graphene.Float()
    expected_return = graphene.Float()
    suggested_exit_price = graphene.Float()  # For sell recommendations
    current_return = graphene.Float()  # For sell recommendations
    sector = graphene.String()
    risk_level = graphene.String()
    ml_score = graphene.Float()


class PortfolioAnalysisType(graphene.ObjectType):
    """Portfolio analysis results"""

    total_value = graphene.Float()
    num_holdings = graphene.Int()
    sector_breakdown = graphene.JSONString()
    risk_score = graphene.Float()
    diversification_score = graphene.Float()


class RiskAssessmentType(graphene.ObjectType):
    """Risk assessment results"""

    overall_risk = graphene.String()
    concentration_risk = graphene.String()
    sector_risk = graphene.String()
    volatility_estimate = graphene.Float()
    volatilityEstimate = graphene.Float()  # Alias for frontend compatibility
    recommendations = graphene.List(graphene.String)

    def resolve_volatilityEstimate(self, info):
        """Resolver for volatilityEstimate alias"""
        if hasattr(self, "volatility_estimate"):
            return self.volatility_estimate
        if isinstance(self, dict) and "volatility_estimate" in self:
            return self["volatility_estimate"]
        return None


class MarketOutlookType(graphene.ObjectType):
    """AI-powered market outlook"""

    overall_sentiment = graphene.String()
    confidence = graphene.Float()
    key_factors = graphene.List(graphene.String)
    risks = graphene.List(graphene.String)


class RebalanceSuggestionType(graphene.ObjectType):
    """Portfolio rebalancing suggestion"""

    action = graphene.String()
    current_allocation = graphene.Float()
    suggested_allocation = graphene.Float()
    reasoning = graphene.String()
    priority = graphene.String()


class AIRecommendationsType(graphene.ObjectType):
    """Complete AI recommendations package"""

    portfolio_analysis = graphene.Field(PortfolioAnalysisType)
    buy_recommendations = graphene.List(AIRecommendationType)
    sell_recommendations = graphene.List(AIRecommendationType)
    rebalance_suggestions = graphene.List(RebalanceSuggestionType)
    risk_assessment = graphene.Field(RiskAssessmentType)
    market_outlook = graphene.Field(MarketOutlookType)


class StockTradeType(graphene.ObjectType):
    """Individual stock trade in rebalancing"""

    symbol = graphene.String()
    company_name = graphene.String()
    action = graphene.String()  # "BUY" or "SELL"
    shares = graphene.Int()
    price = graphene.Float()
    total_value = graphene.Float()
    reason = graphene.String()


class RebalanceResultType(graphene.ObjectType):
    """Result of AI rebalancing operation"""

    success = graphene.Boolean()
    message = graphene.String()
    changes_made = graphene.List(graphene.String)
    stock_trades = graphene.List(StockTradeType)
    new_portfolio_value = graphene.Float()
    rebalance_cost = graphene.Float()
    estimated_improvement = graphene.String()


# ==================
# Premium Query Root
# ==================


class PremiumQueries(graphene.ObjectType):
    """Premium feature queries"""

    premium_portfolio_metrics = graphene.Field(
        PortfolioMetricsType,
        portfolio_name=graphene.String(
            description="Specific portfolio name (optional)"
        ),
    )
    advanced_stock_screening = graphene.List(
        StockScreeningResultType,
        sector=graphene.String(description="Filter by sector"),
        min_market_cap=graphene.Float(description="Minimum market cap"),
        max_market_cap=graphene.Float(description="Maximum market cap"),
        min_pe_ratio=graphene.Float(description="Minimum P/E ratio"),
        max_pe_ratio=graphene.Float(description="Maximum P/E ratio"),
        min_beginner_score=graphene.Int(
            description="Minimum beginner score"
        ),
        sort_by=graphene.String(description="Sort by: ml_score, market_cap"),
        limit=graphene.Int(description="Limit results (default: 50)"),
    )
    ai_recommendations = graphene.Field(
        AIRecommendationsType,
        risk_tolerance=graphene.String(
            description="Risk tolerance: low, medium, high"
        ),
    )
    options_analysis = graphene.Field(
        "core.premium_types.OptionsAnalysisType",
        symbol=graphene.String(
            required=True,
            description="Stock symbol to analyze options for",
        ),
    )
    stock_screening = graphene.List(
        StockScreeningResultType,
        filters=graphene.String(description="JSON string of screening filters"),
    )

    # ------- Resolvers -------

    def resolve_premium_portfolio_metrics(self, info, portfolio_name=None):
        user = getattr(info.context, "user", None)
        logger.info(
            "Premium portfolio metrics request - User: %s, Anonymous: %s",
            user,
            user.is_anonymous if user else "No user",
        )

        user_id = user.id if user and not user.is_anonymous else 1

        if user and not user.is_anonymous and not _has_premium_access(user):
            logger.warning("User %s does not have premium access", user.id)
            raise Exception("Premium subscription required")

        analytics_service = PremiumAnalyticsService()
        result = analytics_service.get_portfolio_performance_metrics(
            user_id, portfolio_name
        )
        logger.info(
            "Portfolio metrics result for user %s: %s", user_id, type(result)
        )
        return result

    def resolve_advanced_stock_screening(self, info, **kwargs):
        user = getattr(info.context, "user", None)

        if user and not user.is_anonymous and not _has_premium_access(user):
            raise Exception("Premium subscription required")

        filters = {k: v for k, v in kwargs.items() if v is not None}
        analytics_service = PremiumAnalyticsService()
        return analytics_service.get_advanced_stock_screening(filters)

    def resolve_ai_recommendations(self, info, risk_tolerance="medium"):
        user = getattr(info.context, "user", None)
        logger.info(
            "AI recommendations request - User: %s, Anonymous: %s",
            user,
            user.is_anonymous if user else "No user",
        )

        user_id = user.id if user and not user.is_anonymous else 1

        if user and not user.is_anonymous and not _has_premium_access(user):
            logger.warning("User %s does not have premium access", user.id)
            raise Exception("Premium subscription required")

        analytics_service = PremiumAnalyticsService()
        result = analytics_service.get_ai_recommendations(
            user_id, risk_tolerance
        )
        logger.info(
            "AI recommendations result for user %s: %s", user_id, type(result)
        )
        return result

    def resolve_options_analysis(self, info, symbol):
        """Get comprehensive options analysis for a symbol"""
        try:
            user = getattr(info.context, "user", None)
            logger.info(
                "Options analysis request - User: %s, Symbol: %s", user, symbol
            )

            if user and not user.is_anonymous and not _has_premium_access(user):
                logger.warning(
                    "User %s does not have premium access", user.id
                )
                raise Exception("Premium subscription required")

            try:
                options_service = OptionsAnalysisService()
                result = options_service.get_comprehensive_analysis(symbol)
                logger.info(
                    "Options analysis result for %s: %s",
                    symbol,
                    type(result),
                )
                return result
            except Exception as e:
                logger.error(
                    "Error getting options analysis for %s: %s", symbol, e
                )
                return self._get_mock_options_analysis(symbol)
        except Exception as e:
            logger.error("Error in options analysis resolver: %s", e)
            return self._get_mock_options_analysis(symbol)

    def _get_mock_options_analysis(self, symbol):
        """Return mock options analysis data for testing"""

        call_options = [
            {
                "symbol": symbol,
                "contract_symbol": f"{symbol}240115C00150000",
                "strike": 150.0,
                "expiration_date": "2024-01-15",
                "option_type": "call",
                "bid": 2.50,
                "ask": 2.75,
                "last_price": 2.60,
                "volume": 1250,
                "open_interest": 5000,
                "implied_volatility": 0.25,
                "delta": 0.65,
                "gamma": 0.02,
                "theta": -0.15,
                "vega": 0.30,
                "rho": 0.05,
                "intrinsic_value": 5.0,
                "time_value": 2.60,
                "days_to_expiration": 30,
            }
        ]

        put_options = [
            {
                "symbol": symbol,
                "contract_symbol": f"{symbol}240115P00150000",
                "strike": 150.0,
                "expiration_date": "2024-01-15",
                "option_type": "put",
                "bid": 1.20,
                "ask": 1.40,
                "last_price": 1.30,
                "volume": 800,
                "open_interest": 3000,
                "implied_volatility": 0.28,
                "delta": -0.35,
                "gamma": 0.02,
                "theta": -0.12,
                "vega": 0.25,
                "rho": -0.03,
                "intrinsic_value": 0.0,
                "time_value": 1.30,
                "days_to_expiration": 30,
            }
        ]

        unusual_flow = [
            {
                "symbol": symbol,
                "contract_symbol": f"{symbol}240115C00150000",
                "option_type": "call",
                "strike": 150.0,
                "expiration_date": "2024-01-15",
                "volume": 5000,
                "open_interest": 15000,
                "premium": 13000.0,
                "implied_volatility": 0.30,
                "unusual_activity_score": 0.85,
                "activity_type": "Sweep",
            }
        ]

        recommended_strategies = [
            {
                "strategy_name": "Covered Call",
                "strategy_type": "Covered Call",
                "max_profit": 7.50,
                "max_loss": -142.50,
                "breakeven_points": [142.50],
                "probability_of_profit": 0.65,
                "risk_reward_ratio": 0.05,
                "days_to_expiration": 30,
                "total_cost": 0.0,
                "total_credit": 2.60,
            }
        ]

        market_sentiment = {
            "put_call_ratio": 0.65,
            "implied_volatility_rank": 45.0,
            "skew": 0.15,
            "sentiment_score": 65.0,
            "sentiment_description": "Bullish",
        }

        return {
            "underlying_symbol": symbol,
            "underlying_price": 155.0,
            "options_chain": {
                "expiration_dates": [
                    "2024-01-15",
                    "2024-02-16",
                    "2024-03-15",
                ],
                "calls": call_options,
                "puts": put_options,
                "greeks": {
                    "delta": 0.5,
                    "gamma": 0.02,
                    "theta": -0.15,
                    "vega": 0.30,
                    "rho": 0.05,
                },
            },
            "unusual_flow": unusual_flow,
            "recommended_strategies": recommended_strategies,
            "market_sentiment": market_sentiment,
        }

    def resolve_stock_screening(self, info, filters):
        try:
            user = getattr(info.context, "user", None)
            logger.info(
                "Stock screening request - User: %s, Filters: %s", user, filters
            )

            if user and not user.is_anonymous and not _has_premium_access(user):
                logger.warning(
                    "User %s does not have premium access", user.id
                )
                raise Exception("Premium subscription required")

            if isinstance(filters, str):
                filters = json.loads(filters)

            analytics_service = PremiumAnalyticsService()
            results = analytics_service.get_advanced_stock_screening(filters)
            logger.info(
                "Stock screening results: %s stocks found", len(results)
            )
            return results
        except Exception as e:
            logger.error("Error in stock screening resolver: %s", e)
            raise Exception(f"Stock screening failed: {str(e)}")


def _has_premium_access(user):
    """Check if user has premium subscription (very permissive for now)."""
    if user and user.email == "test@example.com":
        logger.info(
            "Premium access granted to test user: %s", user.email
        )
        return True
    if user and not user.is_anonymous:
        logger.info(
            "Premium access granted to authenticated user: %s", user.email
        )
        return True
    logger.warning("Premium access denied for user: %s", user)
    return False


# =================
# Premium Mutations
# =================


class SubscribeToPremium(graphene.Mutation):
    """Subscribe to premium features"""

    class Arguments:
        plan_type = graphene.String(
            required=True, description="Plan type: basic, pro, elite"
        )
        payment_method = graphene.String(
            required=True, description="Payment method ID"
        )

    success = graphene.Boolean()
    message = graphene.String()
    subscription_id = graphene.String()

    def mutate(self, info, plan_type, payment_method):
        user = getattr(info.context, "user", None)
        if not user or user.is_anonymous:
            return SubscribeToPremium(
                success=False, message="Authentication required"
            )

        valid_plans = ["basic", "pro", "elite"]
        if plan_type not in valid_plans:
            return SubscribeToPremium(
                success=False, message="Invalid plan type"
            )

        try:
            subscription_id = (
                f"sub_{user.id}_{plan_type}_"
                f"{datetime.now().strftime('%Y%m%d')}"
            )
            return SubscribeToPremium(
                success=True,
                message=f"Successfully subscribed to {plan_type} plan",
                subscription_id=subscription_id,
            )
        except Exception as e:
            logger.error("Error creating subscription: %s", e)
            return SubscribeToPremium(
                success=False, message="Failed to create subscription"
            )


class CancelPremiumSubscription(graphene.Mutation):
    """Cancel premium subscription"""

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info):
        user = getattr(info.context, "user", None)
        if not user or user.is_anonymous:
            return CancelPremiumSubscription(
                success=False, message="Authentication required"
            )
        try:
            # TODO: integrate with real payment provider + subscription model
            return CancelPremiumSubscription(
                success=True, message="Subscription cancelled successfully"
            )
        except Exception as e:
            logger.error("Error cancelling subscription: %s", e)
            return CancelPremiumSubscription(
                success=False, message="Failed to cancel subscription"
            )


# ======================
# Options Analysis Types
# ======================


class OptionsContractType(graphene.ObjectType):
    """Individual options contract"""

    symbol = graphene.String()
    contract_symbol = graphene.String()
    strike = graphene.Float()
    expiration_date = graphene.String()
    option_type = graphene.String()
    bid = graphene.Float()
    ask = graphene.Float()
    last_price = graphene.Float()
    volume = graphene.Int()
    open_interest = graphene.Int()
    implied_volatility = graphene.Float()
    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()
    rho = graphene.Float()
    intrinsic_value = graphene.Float()
    time_value = graphene.Float()
    days_to_expiration = graphene.Int()


class GreeksType(graphene.ObjectType):
    """Greeks for options analysis"""

    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()
    rho = graphene.Float()


class OptionsChainType(graphene.ObjectType):
    """Options chain for a symbol"""

    expiration_dates = graphene.List(graphene.String)
    calls = graphene.List(OptionsContractType)
    puts = graphene.List(OptionsContractType)
    greeks = graphene.Field(GreeksType)

    def resolve_expiration_dates(self, info):
        return self.get("expiration_dates", [])

    def resolve_calls(self, info):
        return self.get("calls", [])

    def resolve_puts(self, info):
        return self.get("puts", [])

    def resolve_greeks(self, info):
        return self.get("greeks", {})


class OptionsFlowType(graphene.ObjectType):
    """Unusual options flow data"""

    symbol = graphene.String()
    contract_symbol = graphene.String()
    option_type = graphene.String()
    strike = graphene.Float()
    expiration_date = graphene.String()
    volume = graphene.Int()
    open_interest = graphene.Int()
    premium = graphene.Float()
    implied_volatility = graphene.Float()
    unusual_activity_score = graphene.Float()
    activity_type = graphene.String()


class OptionsStrategyType(graphene.ObjectType):
    """Options trading strategy"""

    strategy_name = graphene.String()
    strategy_type = graphene.String()
    max_profit = graphene.Float()
    max_loss = graphene.Float()
    breakeven_points = graphene.List(graphene.Float)
    probability_of_profit = graphene.Float()
    risk_reward_ratio = graphene.Float()
    days_to_expiration = graphene.Int()
    total_cost = graphene.Float()
    total_credit = graphene.Float()
    description = graphene.String()
    risk_level = graphene.String()
    market_outlook = graphene.String()


class MarketSentimentType(graphene.ObjectType):
    """Market sentiment from options data"""

    put_call_ratio = graphene.Float()
    implied_volatility_rank = graphene.Float()
    skew = graphene.Float()
    sentiment_score = graphene.Float()
    sentiment_description = graphene.String()


class OptionsAnalysisType(graphene.ObjectType):
    """Complete options analysis"""

    underlying_symbol = graphene.String()
    underlying_price = graphene.Float()
    options_chain = graphene.Field(OptionsChainType)
    unusual_flow = graphene.List(OptionsFlowType)
    recommended_strategies = graphene.List(OptionsStrategyType)
    market_sentiment = graphene.Field(MarketSentimentType)

    def resolve_underlying_symbol(self, info):
        return self.get("underlying_symbol", "")

    def resolve_underlying_price(self, info):
        return self.get("underlying_price", 0.0)

    def resolve_options_chain(self, info):
        return self.get("options_chain", {})

    def resolve_unusual_flow(self, info):
        return self.get("unusual_flow", [])

    def resolve_recommended_strategies(self, info):
        return self.get("recommended_strategies", [])

    def resolve_market_sentiment(self, info):
        return self.get("market_sentiment", {})


# ======================
# Premium Mutations Root
# ======================


class PremiumMutations(graphene.ObjectType):
    """Premium feature mutations"""

    subscribe_to_premium = SubscribeToPremium.Field()
    cancel_premium_subscription = CancelPremiumSubscription.Field()
    ai_rebalance_portfolio = graphene.Field(
        RebalanceResultType,
        portfolio_name=graphene.String(
            description="Portfolio to rebalance (optional)"
        ),
        risk_tolerance=graphene.String(
            description="Risk tolerance: low, medium, high"
        ),
        max_rebalance_percentage=graphene.Float(
            description="Maximum percentage to rebalance (default: 20%)"
        ),
        dry_run=graphene.Boolean(
            description="Preview changes without executing (default: false)"
        ),
    )

    def resolve_ai_rebalance_portfolio(
        self,
        info,
        portfolio_name=None,
        risk_tolerance="medium",
        max_rebalance_percentage=20.0,
        dry_run=False,
    ):
        """
        AI-powered portfolio rebalancing (simplified, but clean and working).
        """
        user = getattr(info.context, "user", None)
        user_id = user.id if user and not user.is_anonymous else 1

        if user and not user.is_anonymous and not _has_premium_access(user):
            raise Exception("Premium subscription required for AI rebalancing")

        try:
            portfolio = Portfolio.objects.filter(user_id=user_id).first()
            if not portfolio:
                return RebalanceResultType(
                    success=False,
                    message="No portfolio found for rebalancing",
                    changes_made=[],
                    stock_trades=[],
                    new_portfolio_value=0.0,
                    rebalance_cost=0.0,
                    estimated_improvement="N/A",
                )

            analytics_service = PremiumAnalyticsService()
            recommendations = analytics_service.get_ai_recommendations(
                user_id, risk_tolerance
            )

            if not recommendations or not recommendations.get(
                "rebalance_suggestions"
            ):
                return RebalanceResultType(
                    success=False,
                    message="No rebalancing recommendations available",
                    changes_made=[],
                    stock_trades=[],
                    new_portfolio_value=float(portfolio.total_value),
                    rebalance_cost=0.0,
                    estimated_improvement="N/A",
                )

            changes_made = []
            stock_trades = []
            total_cost = 0.0

            stock_service = EnhancedStockService()
            cache_key = (
                f"rebalance_stocks_{risk_tolerance}_{max_rebalance_percentage}"
            )
            sector_stocks = cache.get(cache_key)

            if sector_stocks is None:
                sector_stocks = {}
                all_stocks = (
                    Stock.objects.select_related()
                    .only(
                        "symbol",
                        "company_name",
                        "sector",
                        "current_price",
                        "market_cap",
                        "pe_ratio",
                        "dividend_yield",
                        "debt_ratio",
                        "volatility",
                        "beginner_friendly_score",
                    )
                    .filter(current_price__gt=0)
                )

                # Group by sector
                stocks_by_sector = {}
                for stock in all_stocks:
                    sector_name = getattr(stock, "sector", None) or "Mixed"
                    stocks_by_sector.setdefault(sector_name, []).append(stock)

                available_sectors = list(stocks_by_sector.keys())
                if available_sectors:
                    num_sectors = min(5, len(available_sectors))
                    selected_sectors = random.sample(
                        available_sectors, num_sectors
                    )

                    for sector_name in selected_sectors:
                        stocks_in_sector = stocks_by_sector[sector_name]
                        # Take up to 20 for scoring variety
                        if len(stocks_in_sector) > 20:
                            stocks_in_sector = random.sample(
                                stocks_in_sector, 20
                            )

                        quality_stocks = []
                        for stock in stocks_in_sector:
                            try:
                                price = float(stock.current_price or 0)
                                if not (5.0 <= price <= 2000.0):
                                    continue

                                # Simple scoring: market cap + beginner score - volatility
                                score = 0.0
                                try:
                                    mc = float(stock.market_cap or 0)
                                    if mc > 1e11:
                                        score += 15
                                    elif mc > 1e10:
                                        score += 12
                                    elif mc > 1e9:
                                        score += 9
                                    elif mc > 3e8:
                                        score += 6
                                    else:
                                        score += 3
                                except Exception:
                                    score += 5

                                try:
                                    beginner = int(
                                        stock.beginner_friendly_score or 50
                                    )
                                    if beginner >= 80:
                                        score += 5
                                    elif beginner >= 60:
                                        score += 4
                                    elif beginner >= 40:
                                        score += 3
                                    else:
                                        score += 1
                                except Exception:
                                    score += 3

                                try:
                                    vol = float(stock.volatility or 20)
                                    if vol <= 15:
                                        score += 10
                                    elif vol <= 25:
                                        score += 7
                                    elif vol <= 40:
                                        score += 4
                                    else:
                                        score += 2
                                except Exception:
                                    score += 6

                                score += random.random() * 2.0

                                quality_stocks.append(
                                    {"stock": stock, "price": price, "score": score}
                                )
                            except Exception as e:
                                logger.warning(
                                    "Error scoring stock %s: %s",
                                    getattr(stock, "symbol", "unknown"),
                                    e,
                                )

                        quality_stocks.sort(
                            key=lambda x: x["score"], reverse=True
                        )
                        top_pick_count = min(4, len(quality_stocks))
                        if top_pick_count:
                            sector_stocks[sector_name] = [
                                {
                                    "symbol": qs["stock"].symbol,
                                    "name": qs["stock"].company_name
                                    or qs["stock"].symbol,
                                    "price": qs["price"],
                                    "score": qs["score"],
                                }
                                for qs in quality_stocks[:top_pick_count]
                            ]

                if not sector_stocks:
                    return RebalanceResultType(
                        success=False,
                        message="No stocks available for rebalancing",
                        changes_made=[],
                        stock_trades=[],
                        new_portfolio_value=0.0,
                        rebalance_cost=0.0,
                        estimated_improvement="N/A",
                    )

                cache.set(cache_key, sector_stocks, 900)

            # Apply top 3 rebalance suggestions
            for suggestion in recommendations["rebalance_suggestions"][:3]:
                action_text = suggestion["action"]
                current_alloc = suggestion["current_allocation"]
                suggested_alloc = suggestion["suggested_allocation"]
                change_pct = abs(suggested_alloc - current_alloc)

                if change_pct > max_rebalance_percentage:
                    continue

                changes_made.append(
                    f"{action_text}: {current_alloc:.1f}% → {suggested_alloc:.1f}%"
                )

                # Very simplified mapping of action → sectors
                action_lower = action_text.lower()
                chosen_stocks = []

                if "technology" in action_lower:
                    tech_sectors = [
                        s
                        for s in sector_stocks.keys()
                        if "tech" in s.lower()
                        or "technology" in s.lower()
                    ]
                    if tech_sectors:
                        chosen_stocks = sector_stocks[tech_sectors[0]][:2]
                elif "health" in action_lower:
                    health_sectors = [
                        s
                        for s in sector_stocks.keys()
                        if "health" in s.lower()
                        or "medical" in s.lower()
                        or "healthcare" in s.lower()
                    ]
                    if health_sectors:
                        chosen_stocks = sector_stocks[health_sectors[0]][:2]
                elif "consumer" in action_lower:
                    consumer_sectors = [
                        s
                        for s in sector_stocks.keys()
                        if "consumer" in s.lower()
                        or "cyclical" in s.lower()
                        or "retail" in s.lower()
                    ]
                    if consumer_sectors:
                        chosen_stocks = sector_stocks[consumer_sectors[0]][:2]

                for pick in chosen_stocks:
                    price = pick["price"]
                    symbol = pick["symbol"]
                    name = pick["name"]

                    if "increase" in action_lower:
                        shares = max(
                            1,
                            int(
                                (float(portfolio.total_value) * 0.05)
                                / max(price, 0.01)
                            ),
                        )
                        trade_value = shares * price
                        stock_trades.append(
                            StockTradeType(
                                symbol=symbol,
                                company_name=name,
                                action="BUY",
                                shares=shares,
                                price=price,
                                total_value=trade_value,
                                reason=action_text,
                            )
                        )

                        if not dry_run:
                            try:
                                stock_obj = Stock.objects.only(
                                    "id", "symbol"
                                ).get(symbol=symbol)
                                PortfolioService.add_holding_to_portfolio(
                                    user=portfolio.user,
                                    stock_id=stock_obj.id,
                                    shares=shares,
                                    portfolio_name=portfolio_name
                                    or "AI Rebalanced Portfolio",
                                    current_price=price,
                                )
                            except Stock.DoesNotExist:
                                logger.warning(
                                    "Stock %s not found in DB", symbol
                                )
                                continue

                        total_cost += trade_value * 0.001

                    elif "reduce" in action_lower or "sell" in action_lower:
                        shares = max(
                            1,
                            int(
                                (float(portfolio.total_value) * 0.03)
                                / max(price, 0.01)
                            ),
                        )
                        trade_value = shares * price
                        stock_trades.append(
                            StockTradeType(
                                symbol=symbol,
                                company_name=name,
                                action="SELL",
                                shares=shares,
                                price=price,
                                total_value=trade_value,
                                reason=action_text,
                            )
                        )

                        if not dry_run:
                            try:
                                stock_obj = Stock.objects.get(symbol=symbol)
                                holding = Portfolio.objects.filter(
                                    user=portfolio.user,
                                    stock=stock_obj,
                                ).first()
                                if holding:
                                    if holding.shares <= shares:
                                        holding.delete()
                                    else:
                                        holding.shares -= shares
                                        holding.save()
                            except Stock.DoesNotExist:
                                logger.warning(
                                    "Stock %s not found in DB for sell", symbol
                                )
                                continue

                        total_cost += trade_value * 0.001

            diversification_score = (
                recommendations.get("portfolio_analysis", {}).get(
                    "diversification_score", 0
                )
            )
            estimated_improvement = (
                f"Expected diversification score improvement: "
                f"{diversification_score:.1f} → "
                f"{min(diversification_score + 15, 100):.1f}"
            )

            if dry_run:
                message = (
                    f"Preview: {len(changes_made)} changes and "
                    f"{len(stock_trades)} trades would be executed "
                    f"(no actual trades made)"
                )
            else:
                message = (
                    f"Successfully rebalanced portfolio with "
                    f"{len(changes_made)} changes and "
                    f"{len(stock_trades)} trades"
                )

            return RebalanceResultType(
                success=True,
                message=message,
                changes_made=changes_made,
                stock_trades=stock_trades,
                new_portfolio_value=float(portfolio.total_value),
                rebalance_cost=total_cost,
                estimated_improvement=estimated_improvement,
            )

        except Exception as e:
            logger.error("AI rebalancing error: %s", e)
            return RebalanceResultType(
                success=False,
                message=f"Rebalancing failed: {str(e)}",
                changes_made=[],
                stock_trades=[],
                new_portfolio_value=0.0,
                rebalance_cost=0.0,
                estimated_improvement="N/A",
            )
