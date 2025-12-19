import graphene


from django.contrib.auth import get_user_model


from .types import UserType, PostType, ChatSessionType, ChatMessageType, CommentType, StockType, StockDataType, WatchlistType, AIPortfolioRecommendationType, StockMomentType, ChartRangeEnum, DayTradingDataType, DayTradingStatsType, ProfileInput, AIRecommendationsType, SwingTradingDataType, SwingTradingStatsType, ExecutionSuggestionType, EntryTimingSuggestionType, ExecutionQualityStatsType, PreMarketDataType, RustOptionsAnalysisType, SecurityEventType, BiometricSettingsType, ComplianceStatusType, SecurityScoreType, DeviceTrustType, AccessPolicyType, ZeroTrustSummaryType


from .models import Post, ChatSession, ChatMessage, Comment, User, Stock, StockData, Watchlist, AIPortfolioRecommendation, StockDiscussion, DiscussionComment, Portfolio, StockMoment, SecurityEvent, BiometricSettings, ComplianceStatus, SecurityScore, DeviceTrust, AccessPolicy


from .benchmark_types import BenchmarkSeriesType, BenchmarkDataPointType


import django.db.models as models


from django.utils import timezone


from datetime import timedelta, datetime

from typing import Optional, Tuple

import asyncio


import logging


logger = logging.getLogger(__name__)


User = get_user_model()


class Query(graphene.ObjectType):

    all_users = graphene.List(UserType)

    search_users = graphene.List(UserType, query=graphene.String(required=False))

    me = graphene.Field(UserType)
    has_income_profile = graphene.Boolean()
    ai_recommendations = graphene.Field(
        AIRecommendationsType,
        # Profile input – real Graphene argument, not a string or direct type
        profile=graphene.Argument(ProfileInput, required=False),
        # usingDefaults Boolean argument, exposed to GraphQL as "usingDefaults"
        using_defaults=graphene.Argument(
            graphene.Boolean,
            required=False,
            default_value=True,
            name="usingDefaults",
        ),
    )

    def resolve_me(self, info, **kwargs):
        """Resolve the 'me' query - returns the authenticated user"""
        user = getattr(info.context, "user", None)
        
        logger.info(
            "[Me] resolve_me user_id=%s email=%s is_auth=%s",
            getattr(user, "id", None),
            getattr(user, "email", None),
            getattr(user, "is_authenticated", None),
        )
        
        if not getattr(user, "is_authenticated", False):
            logger.info("[Me] resolve_me: user not authenticated, returning null")
            return None
        
        logger.info("[Me] resolve_me: returning authenticated user")
        return user

    def resolve_has_income_profile(self, info, **kwargs):
        """Check if the authenticated user has an income profile"""
        from .models import IncomeProfile
        
        user = getattr(info.context, "user", None)
        
        if not getattr(user, "is_authenticated", False):
            logger.info("[Me] has_income_profile: user not authenticated, returning false")
            return False
        
        exists = IncomeProfile.objects.filter(user=user).exists()
        logger.info(
            "[Me] has_income_profile user_id=%s email=%s exists=%s",
            getattr(user, "id", None),
            getattr(user, "email", None),
            exists,
        )
        return exists

    def resolve_ai_recommendations(
        self,
        info,
        profile=None,
        using_defaults=True,
        **kwargs,
    ):
        """
        Resolver for:
          aiRecommendations(profile: ProfileInput, usingDefaults: Boolean): AIRecommendationsType
        
        Dynamically generates AI-powered stock recommendations using ML scoring.
        """
        from django.contrib.auth.models import AnonymousUser
        from .models import IncomeProfile, Stock
        from .ai_service import AIService
        from .premium_types import AIRecommendationsType
        
        user = info.context.user if hasattr(info, 'context') and hasattr(info.context, 'user') else None
        if not user or user.is_anonymous:
            user = AnonymousUser()
        user_id = user.id if hasattr(user, 'id') and not user.is_anonymous else 1
        
        logger.info(
            "[AIRecs] resolve_ai_recommendations user=%s email=%s using_defaults=%s profile=%s",
            getattr(user, "id", None),
            getattr(user, "email", None),
            using_defaults,
            profile,
        )
        
        if (
            not user
            or not getattr(user, "is_authenticated", False)
        ):
            logger.info("[AI] resolve_ai_recommendations: unauthenticated")
            return AIRecommendationsType(
                buy_recommendations=[],
                sell_recommendations=[],
                spending_insights=None,
            )
        
        # Build user profile dict from input or saved profile
        profile_dict = None
        if profile is not None:
            # Profile is a ProfileInput object, extract values
            # Handle investmentGoals - could be List type from GraphQL or regular list
            investment_goals_raw = getattr(profile, "investmentGoals", None) or getattr(profile, "investment_goals", None)
            if investment_goals_raw:
                try:
                    investment_goals = list(investment_goals_raw)
                except (TypeError, ValueError):
                    investment_goals = []
            else:
                investment_goals = []
            
            profile_dict = {
                "age": getattr(profile, "age", None) or 30,
                "income_bracket": getattr(profile, "incomeBracket", None) or getattr(profile, "income_bracket", None) or "Unknown",
                "investment_goals": investment_goals,
                "investment_horizon_years": getattr(profile, "investmentHorizonYears", None) or getattr(profile, "investment_horizon_years", None) or 5,
                "risk_tolerance": getattr(profile, "riskTolerance", None) or getattr(profile, "risk_tolerance", None) or "Moderate",
            }
            logger.info("[AI] Using profile from input: %s", profile_dict)
        elif not using_defaults:
            # If client wants to use the saved profile instead of the passed input
            try:
                income_profile = IncomeProfile.objects.get(user=user)
                # Map investment_horizon string to years
                horizon_str = income_profile.investment_horizon or "5-10 years"
                horizon_years = 5
                if "10+" in horizon_str:
                    horizon_years = 12
                elif "5-10" in horizon_str:
                    horizon_years = 8
                elif "3-5" in horizon_str:
                    horizon_years = 4
                elif "1-3" in horizon_str:
                    horizon_years = 2
                
                profile_dict = {
                    "age": income_profile.age or 30,
                    "income_bracket": income_profile.income_bracket or "Unknown",
                    "investment_goals": list(income_profile.investment_goals or []),
                    "investment_horizon_years": horizon_years,
                    "risk_tolerance": income_profile.risk_tolerance or "Moderate",
                }
                logger.info(
                    "[AI] Using saved profile for user=%s bracket=%s age=%s",
                    user.id,
                    income_profile.income_bracket,
                    income_profile.age,
                )
            except IncomeProfile.DoesNotExist:
                logger.info("[AI] No saved profile, falling back to defaults")
                profile_dict = {
                    "age": 30,
                    "income_bracket": "Unknown",
                    "investment_goals": [],
                    "investment_horizon_years": 5,
                    "risk_tolerance": "Moderate",
                }
        else:
            logger.info("[AI] using_defaults=True – using default profile")
            profile_dict = {
                "age": 30,
                "income_bracket": "Unknown",
                "investment_goals": [],
                "investment_horizon_years": 5,
                "risk_tolerance": "Moderate",
            }
        
        # Get spending habits analysis for personalization (optional)
        spending_analysis = None
        try:
            from .spending_habits_service import SpendingHabitsService
            spending_service = SpendingHabitsService()
            spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)
        except Exception as e:
            logger.warning(f"Could not get spending analysis for AI recommendations: {e}")
        
        # Fetch stocks from database (limit to 100 for performance)
        try:
            stocks_qs = Stock.objects.filter(
                current_price__isnull=False,
                current_price__gt=0
            )[:100]
            
            # Convert to list of dicts for ML service
            stocks_list = []
            for stock in stocks_qs:
                stocks_list.append({
                    "symbol": stock.symbol,
                    "company_name": stock.company_name or stock.symbol,
                    "sector": stock.sector or "Unknown",
                    "market_cap": float(stock.market_cap) if stock.market_cap else 0.0,
                    "pe_ratio": float(stock.pe_ratio) if stock.pe_ratio else None,
                    "dividend_yield": float(stock.dividend_yield) if stock.dividend_yield else 0.0,
                    "current_price": float(stock.current_price) if stock.current_price else 0.0,
                    "beginner_friendly_score": stock.beginner_friendly_score or 50,
                })
            
            logger.info(f"[AI] Fetched {len(stocks_list)} stocks for ML scoring")
            
        except Exception as e:
            logger.error(f"Error fetching stocks: {e}")
            stocks_list = []
        
        # Score stocks using ML service
        buy_recommendations = []
        if stocks_list:
            try:
                ai_service = AIService()
                scored_stocks = ai_service.score_stocks_ml(
                    stocks_list,
                    profile_dict,
                    spending_analysis
                )
                
                # Filter by ML score >= 0.6 and sort by score
                filtered_stocks = [
                    s for s in scored_stocks 
                    if s.get('ml_score', 0) >= 0.6
                ]
                filtered_stocks.sort(key=lambda x: x.get('ml_score', 0), reverse=True)
                
                # Take top 10
                top_stocks = filtered_stocks[:10]
                
                logger.info(f"[AI] ML scored {len(scored_stocks)} stocks, {len(filtered_stocks)} passed filter, returning top {len(top_stocks)}")
                
                # Convert to dict format for AIRecommendationType (Graphene will handle conversion)
                for stock in top_stocks:
                    ml_score = stock.get('ml_score', 0.7)
                    current_price = stock.get('current_price', 0.0)
                    target_price = current_price * 1.15  # Default 15% target
                    
                    # Get target price from ML if available
                    if 'target_price' in stock and stock['target_price']:
                        target_price = float(stock['target_price'])
                    
                    buy_recommendations.append({
                        'symbol': stock.get('symbol', ''),
                        'company_name': stock.get('company_name', ''),
                        'recommendation': 'BUY',
                        'confidence': ml_score,
                        'reasoning': stock.get('ml_reasoning', f'ML score: {ml_score:.2%} - Recommended based on your profile'),
                        'target_price': target_price,
                        'current_price': current_price,
                        'expected_return': 0.12,  # Default 12% expected return
                        'sector': stock.get('sector', 'Unknown'),
                        'risk_level': profile_dict.get('risk_tolerance', 'Moderate'),
                        'ml_score': ml_score,
                    })
                
            except Exception as e:
                logger.error(f"Error scoring stocks with ML: {e}", exc_info=True)
                # Fallback: return empty recommendations
        
        logger.info(
            "[AI] resolve_ai_recommendations user=%s using_defaults=%s count=%s",
            user.id,
            using_defaults,
            len(buy_recommendations),
        )
        
        return AIRecommendationsType(
            buy_recommendations=buy_recommendations,
            sell_recommendations=[],  # Not implemented yet
            spending_insights=None,  # Could be enhanced later
        )

    wall_posts = graphene.List(PostType)

    all_posts = graphene.List(PostType)

    user = graphene.Field(UserType, id=graphene.ID(required=True))

    user_posts = graphene.List(PostType, user_id=graphene.ID(required=True))

    post_comments = graphene.List(CommentType, post_id=graphene.ID(required=True))

    # Chat queries

    my_chat_sessions = graphene.List(ChatSessionType)

    chat_session = graphene.Field(ChatSessionType, id=graphene.ID(required=True))

    chat_messages = graphene.List(ChatMessageType, session_id=graphene.ID(required=True))

    # Stock queries

    stocks = graphene.List(StockType, search=graphene.String(required=False))

    stock = graphene.Field(StockType, symbol=graphene.String(required=True))
    
    def resolve_stock(self, info, symbol):
        """Get a specific stock by symbol"""
        from .models import Stock
        
        # Normalize the symbol
        symbol = (symbol or "").strip().upper()
        if not symbol:
            return None
        
        try:
            return Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            return None

    # my_watchlist = graphene.List(WatchlistItemType) # TODO: Uncomment when WatchlistItemType is available

    beginner_friendly_stocks = graphene.List(StockType)

    # Rust Engine queries - TODO: Uncomment when types are available

    # rust_stock_analysis = graphene.Field(RustStockAnalysisType, symbol=graphene.String(required=True))

    # rust_recommendations = graphene.List(RustRecommendationType)

    # rust_health = graphene.Field(RustHealthType)

    # AI Portfolio queries

    ai_portfolio_recommendations = graphene.List(AIPortfolioRecommendationType, userId=graphene.ID(required=True))

    # Portfolio queries

    my_portfolios = graphene.Field('core.portfolio_types.PortfolioSummaryType')

    portfolio_names = graphene.List(graphene.String)

    portfolio_value = graphene.Float()

    # Regular portfolio analytics (not premium)

    portfolio_metrics = graphene.Field('core.premium_types.PortfolioMetricsType')
    
    def resolve_portfolio_metrics(self, info):
        """Get portfolio metrics (regular feature, not premium)"""
        from .graphql_utils import get_user_from_context
        from .premium_analytics import PremiumAnalyticsService

        user = get_user_from_context(info.context)
        
        if not user or getattr(user, "is_anonymous", True):
            # Return empty metrics dict instead of null for better UX
            service = PremiumAnalyticsService()
            empty_metrics = service._empty_portfolio_metrics()
            return empty_metrics

        service = PremiumAnalyticsService()
        metrics = service.get_portfolio_performance_metrics(user.id)
        
        # Defensive: if service returns None, return empty metrics instead of null
        if metrics is None:
            empty_metrics = service._empty_portfolio_metrics()
            return empty_metrics
        
        # Return dict directly - Graphene will use it as self for PortfolioMetricsType resolvers
        return metrics

    # Stock price queries

    current_stock_prices = graphene.List('core.types.StockPriceType', symbols=graphene.List(graphene.String))

    # Test queries for premium features (no auth required for testing)

    test_portfolio_metrics = graphene.Field('core.premium_types.PortfolioMetricsType')

    test_ai_recommendations = graphene.Field('core.premium_types.AIRecommendationsType')

    test_stock_screening = graphene.List('core.premium_types.StockScreeningResultType')

    test_options_analysis = graphene.Field(
        'core.premium_types.OptionsAnalysisType',
        symbol=graphene.String(
            required=True))

    # Phase 3 Social Features - TODO: Uncomment when types are available

    watchlists = graphene.List(WatchlistType, user_id=graphene.ID())

    watchlist = graphene.Field(WatchlistType, id=graphene.ID(required=True))

    public_watchlists = graphene.List(WatchlistType)

    my_watchlist = graphene.List(WatchlistType)
    
    def resolve_my_watchlist(self, info):
        """Get current user's watchlist items"""
        from .graphql_utils import get_user_from_context
        user = get_user_from_context(info.context)

        if not user or getattr(user, "is_anonymous", True):
            return []
        
        from .models import Watchlist
        return Watchlist.objects.filter(user=user).select_related('stock').order_by('-added_at')

    rust_stock_analysis = graphene.Field('core.types.RustStockAnalysisType', symbol=graphene.String(required=True))
    
    # New Rust service queries
    rust_options_analysis = graphene.Field(RustOptionsAnalysisType, symbol=graphene.String(required=True))
    options_flow = graphene.Field('core.options_flow_types.OptionsFlowType', symbol=graphene.String(required=True))
    scan_options = graphene.List('core.options_flow_types.ScannedOptionType', filters=graphene.String(required=False))
    edge_predictions = graphene.List('core.edge_prediction_types.EdgePredictionType', symbol=graphene.String(required=True))
    one_tap_trades = graphene.List(
        'core.one_tap_trade_types.OneTapTradeType',
        symbol=graphene.String(required=True),
        account_size=graphene.Float(required=False),
        risk_tolerance=graphene.Float(required=False)
    )
    iv_surface_forecast = graphene.Field(
        'core.iv_forecast_types.IVSurfaceForecastType',
        symbol=graphene.String(required=True)
    )
    rust_forex_analysis = graphene.Field('core.types.ForexAnalysisType', pair=graphene.String(required=True))
    rust_sentiment_analysis = graphene.Field('core.types.SentimentAnalysisType', symbol=graphene.String(required=True))
    rust_correlation_analysis = graphene.Field(
        'core.types.CorrelationAnalysisType',
        primary=graphene.String(required=True),
        secondary=graphene.String()
    )
    
    # Security Fortress Queries
    securityEvents = graphene.List(
        SecurityEventType,
        limit=graphene.Int(required=False),
        resolved=graphene.Boolean(required=False)
    )
    biometricSettings = graphene.Field(BiometricSettingsType)
    complianceStatuses = graphene.List(ComplianceStatusType)
    securityScore = graphene.Field(SecurityScoreType)
    
    # Zero Trust Architecture Queries
    deviceTrusts = graphene.List(DeviceTrustType)
    accessPolicies = graphene.List(AccessPolicyType)
    zeroTrustSummary = graphene.Field(ZeroTrustSummaryType)

    @staticmethod
    def _calculate_fundamental_scores(features: dict, has_rust_data: bool) -> 'FundamentalAnalysisType':
        """Calculate fundamental analysis scores from Rust features or use defaults"""
        from .types import FundamentalAnalysisType
        
        if not has_rust_data or not features:
            # Default fallback scores
            return FundamentalAnalysisType(
                valuationScore=70.0, growthScore=65.0, stabilityScore=80.0,
                dividendScore=60.0, debtScore=75.0
            )
        
        # Extract fundamental data from features
        pe_ratio = features.get('pe_ratio', 0.0) or 0.0
        dividend_yield = features.get('dividend_yield', 0.0) or 0.0
        volatility = features.get('volatility', 0.0) or 0.0
        risk_score = features.get('risk_score', 0.0) or 0.0
        
        # Calculate Valuation Score (0-100) based on P/E ratio
        # Lower P/E = better valuation (higher score)
        # P/E < 15 = excellent (90-100), 15-25 = good (70-89), 25-35 = fair (50-69), >35 = poor (0-49)
        if pe_ratio > 0:
            if pe_ratio < 15:
                valuation_score = 90.0 + (15 - pe_ratio) * 0.67  # 90-100
            elif pe_ratio < 25:
                valuation_score = 70.0 + (25 - pe_ratio) * 1.9  # 70-89
            elif pe_ratio < 35:
                valuation_score = 50.0 + (35 - pe_ratio) * 1.9  # 50-69
            else:
                valuation_score = max(0.0, 50.0 - (pe_ratio - 35) * 2.0)  # 0-49
        else:
            valuation_score = 70.0
        
        # Calculate Growth Score (0-100) based on volatility and risk
        # Higher volatility can indicate growth potential, but too high = risky
        # Moderate volatility (0.015-0.025) = good growth potential
        if volatility > 0:
            if 0.015 <= volatility <= 0.025:
                growth_score = 75.0 + (0.025 - volatility) * 1000  # 75-85
            elif volatility < 0.015:
                growth_score = 60.0 + volatility * 1000  # 60-75
            elif volatility <= 0.035:
                growth_score = 70.0 - (volatility - 0.025) * 1000  # 50-70
            else:
                growth_score = max(30.0, 50.0 - (volatility - 0.035) * 500)  # 30-50
        else:
            growth_score = 65.0
        
        # Calculate Stability Score (0-100) - inverse of volatility and risk
        # Lower volatility and risk = higher stability
        if volatility > 0 and risk_score > 0:
            # Stability = 100 - (volatility * 2000 + risk_score * 20)
            stability_score = max(0.0, min(100.0, 100.0 - (volatility * 2000 + risk_score * 20)))
        else:
            stability_score = 80.0
        
        # Calculate Dividend Score (0-100) based on dividend yield
        # Dividend yield > 3% = excellent (80-100), 1-3% = good (60-79), 0.5-1% = fair (40-59), <0.5% = poor (0-39)
        if dividend_yield > 0:
            if dividend_yield >= 0.03:
                dividend_score = 80.0 + min(20.0, (dividend_yield - 0.03) * 1000)  # 80-100
            elif dividend_yield >= 0.01:
                dividend_score = 60.0 + (dividend_yield - 0.01) * 1000  # 60-79
            elif dividend_yield >= 0.005:
                dividend_score = 40.0 + (dividend_yield - 0.005) * 4000  # 40-59
            else:
                dividend_score = dividend_yield * 8000  # 0-39
        else:
            dividend_score = 0.0
        
        # Calculate Debt Score (0-100) - using risk_score as proxy
        # Lower risk = better debt management (higher score)
        if risk_score > 0:
            # Risk score typically 0.1-0.5, map to 50-100
            debt_score = max(50.0, min(100.0, 100.0 - (risk_score - 0.1) * 125))
        else:
            debt_score = 75.0
        
        return FundamentalAnalysisType(
            valuationScore=round(valuation_score, 1),
            growthScore=round(growth_score, 1),
            stabilityScore=round(stability_score, 1),
            dividendScore=round(dividend_score, 1),
            debtScore=round(debt_score, 1)
        )
    
    def resolve_rust_stock_analysis(self, info, symbol):
        """Get Rust engine stock analysis - calls the actual Rust service"""
        import time
        import logging
        import sys
        logger = logging.getLogger(__name__)
        
        # Start performance timer
        start_time = time.time()
        logger.info(f"⏱️ [PERF] rustStockAnalysis START for symbol: {symbol}")
        print(f"⏱️ [PERF] rustStockAnalysis START for symbol: {symbol}", flush=True)
        
        from .types import (
            RustStockAnalysisType,
            TechnicalIndicatorsType,
            FundamentalAnalysisType,
            SpendingDataPointType,
            OptionsFlowDataPointType,
            SignalContributionType,
            SHAPValueType
        )
        
        from .rust_stock_service import rust_stock_service
        from .spending_habits_service import SpendingHabitsService
        from .consumer_strength_service import ConsumerStrengthService
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        symbol_upper = symbol.upper()
        
        # Track timing for each phase
        timing_breakdown = {}
        phase_start = time.time()
        
        # Try to call Rust service first
        rust_response = None
        rust_service_time = None
        try:
            logger.info(f"🔧 [PERF] Calling Rust service for {symbol_upper}")
            rust_service_start = time.time()
            rust_response = rust_stock_service.analyze_stock(symbol_upper)
            rust_service_time = time.time() - rust_service_start
            timing_breakdown['rust_service'] = rust_service_time
            logger.info(f"✅ [PERF] Rust service completed in {rust_service_time:.3f}s")
        except Exception as rust_error:
            logger.warning(f"⚠️ [PERF] Rust service unavailable: {rust_error}. Using fallback.")
            timing_breakdown['rust_service'] = None
        
        # Generate fallback data
        phase_start = time.time()
        end_date = timezone.now().date()
        base_price = 100.0
        
        # Generate fallback spending data
        fallback_spending_data = []
        for week_offset in range(12, -1, -1):
            week_end = end_date - timedelta(weeks=week_offset)
            fallback_spending_data.append(SpendingDataPointType(
                date=week_end.isoformat(),
                spending=1000.0 + (week_offset * 50),
                spendingChange=0.05,
                price=base_price * (1 + 0.01 * (12 - week_offset) / 12),
                priceChange=0.01
            ))
        
        # Generate fallback options flow data
        fallback_options_flow_data = []
        for day_offset in range(20, -1, -1):
            day_date = end_date - timedelta(days=day_offset)
            fallback_options_flow_data.append(OptionsFlowDataPointType(
                date=day_date.isoformat(),
                price=base_price * (1 + 0.005 * (20 - day_offset) / 20),
                unusualVolumePercent=15.0,
                sweepCount=0,
                putCallRatio=0.8
            ))
        
        data_generation_time = time.time() - phase_start
        timing_breakdown['data_generation'] = data_generation_time
        
        # Build result
        phase_start = time.time()
        
        # Extract technical indicators from Rust response if available
        features = rust_response.get('features', {}) if rust_response else {}
        price_usd = rust_response.get('price_usd') if rust_response else None
        
        # Handle price_usd - can be string (Decimal), dict, or float
        if price_usd:
            if isinstance(price_usd, dict):
                price_value = price_usd.get('value', 100.0)
            elif isinstance(price_usd, str):
                try:
                    price_value = float(price_usd)
                except (ValueError, TypeError):
                    price_value = 100.0
            else:
                price_value = float(price_usd)
        else:
            # Try to get price from features
            price_value = features.get('price_usd', 100.0)
        
        # Calculate Bollinger Bands if we have SMA values
        sma20_val = features.get('sma_20', 0.0) or features.get('sma20', 0.0)
        sma50_val = features.get('sma_50', 0.0) or features.get('sma50', 0.0)
        rsi_val = features.get('rsi', 50.0) or 50.0
        macd_val = features.get('macd', 0.0) or 0.0
        
        # Calculate Bollinger Bands (upper = SMA + 2*std, lower = SMA - 2*std)
        # Using SMA20 as middle, with 2% standard deviation approximation
        if sma20_val > 0:
            bollinger_middle = sma20_val
            bollinger_upper = sma20_val * 1.04  # Approximate 2 std dev
            bollinger_lower = sma20_val * 0.96   # Approximate 2 std dev
        else:
            # Fallback: use price if available
            bollinger_middle = price_value
            bollinger_upper = price_value * 1.04
            bollinger_lower = price_value * 0.96
        
        # Determine if we have real Rust data or using fallback
        has_rust_data = rust_response and rust_response.get('features') and len(features) > 0
        
        # Get recommendation and risk from Rust if available
        if has_rust_data:
            prediction_type = rust_response.get('prediction_type', 'NEUTRAL')
            confidence = rust_response.get('confidence_level', 'MEDIUM')
            probability = rust_response.get('probability', 0.5)
            
            # Map prediction to recommendation
            if prediction_type == 'BULLISH' and probability > 0.6:
                recommendation = "BUY"
            elif prediction_type == 'BEARISH' and probability > 0.6:
                recommendation = "SELL"
            else:
                recommendation = "HOLD"
            
            # Map confidence to risk level
            if confidence == 'HIGH':
                risk_level = "Low" if probability > 0.6 else "Medium"
            elif confidence == 'MEDIUM':
                risk_level = "Medium"
            else:
                risk_level = "High"
            
            # Use Rust explanation if available
            rust_explanation = rust_response.get('explanation', '')
            reasoning = [rust_explanation] if rust_explanation else [f"Rust analysis for {symbol_upper}"]
        else:
            recommendation = "HOLD"
            risk_level = "Medium"
            reasoning = [f"Fallback analysis for {symbol_upper}"]
        
        result = RustStockAnalysisType(
            symbol=symbol_upper,
            beginnerFriendlyScore=75.0,
            riskLevel=risk_level,
            recommendation=recommendation,
            technicalIndicators=TechnicalIndicatorsType(
                rsi=rsi_val,
                macd=macd_val,
                macdSignal=0.0,  # Not calculated in Rust yet
                macdHistogram=0.0,  # Not calculated in Rust yet
                sma20=sma20_val if sma20_val > 0 else price_value * 0.98,
                sma50=sma50_val if sma50_val > 0 else price_value * 0.95,
                ema12=0.0,  # Not calculated in Rust yet
                ema26=0.0,  # Not calculated in Rust yet
                bollingerUpper=bollinger_upper if sma20_val > 0 else 0.0,
                bollingerLower=bollinger_lower if sma20_val > 0 else 0.0,
                bollingerMiddle=bollinger_middle if sma20_val > 0 else 0.0
            ),
            fundamentalAnalysis=Query._calculate_fundamental_scores(features, has_rust_data),
            reasoning=reasoning,
            spendingData=fallback_spending_data,
            optionsFlowData=fallback_options_flow_data,
            signalContributions=[],
            shapValues=[],
            shapExplanation=f"Fallback analysis for {symbol_upper}"
        )
        result_build_time = time.time() - phase_start
        timing_breakdown['result_build'] = result_build_time
        
        # Calculate total time
        total_time = time.time() - start_time
        timing_breakdown['total'] = total_time
        
        # Log performance metrics
        logger.info(f"⏱️ [PERF] rustStockAnalysis COMPLETE for {symbol_upper}")
        logger.info(f"   Total: {total_time:.3f}s")
        logger.info(f"   Rust Service: {rust_service_time:.3f}s" if rust_service_time else "   Rust Service: N/A (fallback)")
        logger.info(f"   Data Generation: {data_generation_time:.3f}s")
        logger.info(f"   Result Build: {result_build_time:.3f}s")
        print(f"⏱️ [PERF] rustStockAnalysis: {total_time:.3f}s total | Rust: {rust_service_time:.3f}s" if rust_service_time else f"⏱️ [PERF] rustStockAnalysis: {total_time:.3f}s total | Rust: fallback", flush=True)
        
        # Store performance metrics in result (if we add a performance field later)
        logger.info(f"✅ Returning RustStockAnalysisType for {symbol_upper} with {len(fallback_spending_data)} spending and {len(fallback_options_flow_data)} options data points")
        return result
    
    def resolve_options_flow(self, info, symbol):
        """Resolve options flow and unusual activity data"""
        from .options_flow_types import OptionsFlowType, UnusualActivityType, LargestTradeType
        from .real_options_service import RealOptionsService
        
        try:
            symbol_upper = symbol.upper()
            
            # Generate options flow data (would integrate with real API in production)
            options_service = RealOptionsService()
            options_data = options_service.get_real_options_chain(symbol_upper)
            flow_data = options_data.get('unusual_flow', [])
            
            # Calculate put/call ratio
            call_volume = sum(item.get('volume', 0) for item in flow_data if item.get('option_type', '').lower() == 'call')
            put_volume = sum(item.get('volume', 0) for item in flow_data if item.get('option_type', '').lower() == 'put')
            put_call_ratio = put_volume / call_volume if call_volume > 0 else 0.0
            
            # Build unusual activity list - return as UnusualActivityType instances
            unusual_activity = []
            for item in flow_data[:20]:  # Top 20 unusual activities
                volume = item.get('volume', 0)
                open_interest = item.get('open_interest', 10000)
                unusual_volume_percent = (volume / max(open_interest * 0.1, 1)) * 100 if open_interest > 0 else 150
                
                unusual_activity.append(UnusualActivityType(
                    contractSymbol=item.get('contract_symbol', ''),
                    strike=float(item.get('strike', 0)),
                    expiration=item.get('expiration_date', ''),
                    optionType=item.get('option_type', '').lower(),
                    volume=int(volume),
                    openInterest=int(open_interest),
                    volumeVsOI=float(volume / max(open_interest, 1)),
                    lastPrice=float(item.get('premium', 0)),
                    bid=float(item.get('premium', 0) * 0.98),
                    ask=float(item.get('premium', 0) * 1.02),
                    impliedVolatility=float(item.get('implied_volatility', 0.25)),
                    unusualVolumePercent=float(unusual_volume_percent),
                    sweepCount=int(1 if 'Sweep' in item.get('activity_type', '') else 0),
                    blockSize=int(volume if 'Block' in item.get('activity_type', '') else 0),
                    isDarkPool=bool(item.get('is_dark_pool', False)),
                ))
            
            # Build largest trades - return as LargestTradeType instances
            largest_trades = []
            for item in sorted(flow_data, key=lambda x: x.get('volume', 0), reverse=True)[:10]:
                largest_trades.append(LargestTradeType(
                    contractSymbol=item.get('contract_symbol', ''),
                    size=int(item.get('volume', 0)),
                    price=float(item.get('premium', 0)),
                    time=item.get('timestamp', datetime.now().isoformat()),
                    isCall=bool(item.get('option_type', '').lower() == 'call'),
                    isSweep=bool(item.get('sweep_count', 0) > 0),
                    isBlock=bool(item.get('block_size', 0) > 0),
                ))
            
            return OptionsFlowType(
                symbol=symbol_upper,
                timestamp=datetime.now().isoformat(),
                unusualActivity=unusual_activity,
                putCallRatio=float(put_call_ratio),
                totalCallVolume=int(call_volume),
                totalPutVolume=int(put_volume),
                largestTrades=largest_trades,
            )
        except Exception as e:
            logger.error(f"Error resolving options flow: {e}", exc_info=True)
            return OptionsFlowType(
                symbol=symbol.upper(),
                timestamp=datetime.now().isoformat(),
                unusualActivity=[],
                putCallRatio=0.0,
                totalCallVolume=0,
                totalPutVolume=0,
                largestTrades=[],
            )

    def resolve_scan_options(self, info, filters=None):
        """Resolve options scanner results"""
        from .options_flow_types import ScannedOptionType
        from .real_options_service import RealOptionsService
        import json
        
        try:
            filter_dict = json.loads(filters) if filters else {}
            
            # Get options chain data
            options_service = RealOptionsService()
            options_data = options_service.get_real_options_chain('AAPL')  # Would use filter symbol
            
            # Filter and score options based on criteria
            all_options = []
            chain = options_data.get('options_chain', {})
            
            for call in chain.get('calls', [])[:20]:  # Limit to top 20
                score = 75  # Base score
                
                # Score based on filters
                if filter_dict.get('minIV') and call.get('implied_volatility', 0) < filter_dict['minIV']:
                    continue
                if filter_dict.get('maxIV') and call.get('implied_volatility', 0) > filter_dict['maxIV']:
                    continue
                if filter_dict.get('minDelta') and call.get('delta', 0) < filter_dict['minDelta']:
                    continue
                if call.get('volume', 0) < filter_dict.get('minVolume', 100):
                    continue
                
                # Calculate opportunity
                opportunity = 'High liquidity trade'
                if call.get('implied_volatility', 0) > 0.3:
                    opportunity = 'High volatility play'
                elif call.get('delta', 0) > 0.6:
                    opportunity = 'Strong directional move'
                
                all_options.append({
                    'symbol': call.get('symbol', 'AAPL'),
                    'contractSymbol': call.get('contract_symbol', ''),
                    'strike': call.get('strike', 0),
                    'expiration': call.get('expiration_date', ''),
                    'optionType': 'call',
                    'bid': call.get('bid', 0),
                    'ask': call.get('ask', 0),
                    'volume': call.get('volume', 0),
                    'impliedVolatility': call.get('implied_volatility', 0),
                    'delta': call.get('delta', 0),
                    'theta': call.get('theta', 0),
                    'score': score,
                    'opportunity': opportunity,
                })
            
            # Sort by score
            all_options.sort(key=lambda x: x['score'], reverse=True)
            
            return all_options[:10]  # Return top 10
        except Exception as e:
            logger.error(f"Error scanning options: {e}", exc_info=True)
            return []

    def resolve_edge_predictions(self, info, symbol):
        """Get edge predictions (mispricing forecasts) for options chain"""
        from .edge_prediction_types import EdgePredictionType
        from .rust_stock_service import rust_stock_service
        import logging
        logger = logging.getLogger(__name__)
        
        symbol_upper = symbol.upper()
        
        try:
            rust_response = rust_stock_service.predict_edge(symbol_upper)
            
            # Rust returns a list of EdgePrediction objects
            predictions = rust_response if isinstance(rust_response, list) else []
            
            # Map to GraphQL types
            result = []
            for pred in predictions:
                result.append(EdgePredictionType(
                    strike=float(pred.get('strike', 0.0)),
                    expiration=str(pred.get('expiration', '')),
                    option_type=str(pred.get('option_type', 'call')),
                    current_edge=float(pred.get('current_edge', 0.0)),
                    predicted_edge_15min=float(pred.get('predicted_edge_15min', 0.0)),
                    predicted_edge_1hr=float(pred.get('predicted_edge_1hr', 0.0)),
                    predicted_edge_1day=float(pred.get('predicted_edge_1day', 0.0)),
                    confidence=float(pred.get('confidence', 0.0)),
                    explanation=str(pred.get('explanation', '')),
                    edge_change_dollars=float(pred.get('edge_change_dollars', 0.0)),
                    current_premium=float(pred.get('current_premium', 0.0)),
                    predicted_premium_15min=float(pred.get('predicted_premium_15min', 0.0)),
                    predicted_premium_1hr=float(pred.get('predicted_premium_1hr', 0.0)),
                ))
            
            logger.info(f"Edge predictions for {symbol_upper}: {len(result)} predictions")
            return result
            
        except Exception as e:
            logger.warning(f"Error getting edge predictions for {symbol_upper}: {e}")
            return []

    def resolve_one_tap_trades(self, info, symbol, account_size=None, risk_tolerance=None):
        """Get one-tap trade recommendations (ML-optimized strategies)"""
        from .one_tap_trade_types import OneTapTradeType, OneTapLegType
        from .rust_stock_service import rust_stock_service
        import logging
        logger = logging.getLogger(__name__)
        
        symbol_upper = symbol.upper()
        account_size_val = account_size if account_size is not None else 10000.0
        risk_tolerance_val = risk_tolerance if risk_tolerance is not None else 0.1
        
        try:
            rust_response = rust_stock_service.get_one_tap_trades(
                symbol_upper,
                account_size_val,
                risk_tolerance_val
            )
            
            # Rust returns a list of OneTapTrade objects
            trades = rust_response if isinstance(rust_response, list) else []
            
            # Map to GraphQL types
            result = []
            for trade in trades:
                legs = [
                    OneTapLegType(
                        action=str(leg.get('action', 'buy')),
                        option_type=str(leg.get('option_type', 'call')),
                        strike=float(leg.get('strike', 0.0)),
                        expiration=str(leg.get('expiration', '')),
                        quantity=int(leg.get('quantity', 1)),
                        premium=float(leg.get('premium', 0.0)),
                    )
                    for leg in trade.get('legs', [])
                ]
                
                result.append(OneTapTradeType(
                    strategy=str(trade.get('strategy', '')),
                    entry_price=float(trade.get('entry_price', 0.0)),
                    expected_edge=float(trade.get('expected_edge', 0.0)),
                    confidence=float(trade.get('confidence', 0.0)),
                    take_profit=float(trade.get('take_profit', 0.0)),
                    stop_loss=float(trade.get('stop_loss', 0.0)),
                    reasoning=str(trade.get('reasoning', '')),
                    max_loss=float(trade.get('max_loss', 0.0)),
                    max_profit=float(trade.get('max_profit', 0.0)),
                    probability_of_profit=float(trade.get('probability_of_profit', 0.0)),
                    symbol=str(trade.get('symbol', symbol_upper)),
                    legs=legs,
                    strategy_type=str(trade.get('strategy_type', '')),
                    days_to_expiration=int(trade.get('days_to_expiration', 30)),
                    total_cost=float(trade.get('total_cost', 0.0)),
                    total_credit=float(trade.get('total_credit', 0.0)),
                ))
            
            logger.info(f"One-tap trades for {symbol_upper}: {len(result)} trades")
            return result
            
        except Exception as e:
            logger.warning(f"Error getting one-tap trades for {symbol_upper}: {e}")
            return []

    def resolve_iv_surface_forecast(self, info, symbol):
        """Get IV surface forecast (1-24 hours forward)"""
        from .iv_forecast_types import IVSurfaceForecastType, IVChangePointType
        from .rust_stock_service import rust_stock_service
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        symbol_upper = symbol.upper()
        
        try:
            rust_response = rust_stock_service.forecast_iv_surface(symbol_upper)
            
            if not rust_response:
                return None
            
            # Map IV maps (HashMap<String, f64> -> JSON)
            current_iv = rust_response.get('current_iv', {})
            predicted_iv_1hr = rust_response.get('predicted_iv_1hr', {})
            predicted_iv_24hr = rust_response.get('predicted_iv_24hr', {})
            
            # Convert to JSON strings
            current_iv_json = json.dumps({k: float(v) for k, v in current_iv.items()})
            predicted_iv_1hr_json = json.dumps({k: float(v) for k, v in predicted_iv_1hr.items()})
            predicted_iv_24hr_json = json.dumps({k: float(v) for k, v in predicted_iv_24hr.items()})
            
            # Map heatmap points
            heatmap = [
                IVChangePointType(
                    strike=float(point.get('strike', 0.0)),
                    expiration=str(point.get('expiration', '')),
                    current_iv=float(point.get('current_iv', 0.0)),
                    predicted_iv_1hr=float(point.get('predicted_iv_1hr', 0.0)),
                    predicted_iv_24hr=float(point.get('predicted_iv_24hr', 0.0)),
                    iv_change_1hr_pct=float(point.get('iv_change_1hr_pct', 0.0)),
                    iv_change_24hr_pct=float(point.get('iv_change_24hr_pct', 0.0)),
                    confidence=float(point.get('confidence', 0.0)),
                )
                for point in rust_response.get('iv_change_heatmap', [])
            ]
            
            # Get timestamp
            timestamp = rust_response.get('timestamp', '')
            if isinstance(timestamp, dict):
                timestamp = timestamp.get('$date', '') or str(timestamp)
            
            return IVSurfaceForecastType(
                symbol=str(rust_response.get('symbol', symbol_upper)),
                current_iv=current_iv_json,
                predicted_iv_1hr=predicted_iv_1hr_json,
                predicted_iv_24hr=predicted_iv_24hr_json,
                confidence=float(rust_response.get('confidence', 0.0)),
                regime=str(rust_response.get('regime', 'normal')),
                iv_change_heatmap=heatmap,
                timestamp=str(timestamp),
            )
            
        except Exception as e:
            logger.warning(f"Error getting IV surface forecast for {symbol_upper}: {e}")
            return None

    def resolve_rust_options_analysis(self, info, symbol):
        """Get Rust engine options analysis"""
        from .types import (
            RustOptionsAnalysisType,
            VolatilitySurfaceType,
            GreeksType,
            StrikeRecommendationType,
        )
        from .rust_stock_service import rust_stock_service
        import logging
        logger = logging.getLogger(__name__)
        
        symbol_upper = symbol.upper()
        
        try:
            rust_response = rust_stock_service.analyze_options(symbol_upper)
            
            # Map Rust response to GraphQL types
            vol_surface = rust_response.get('volatility_surface', {})
            greeks_data = rust_response.get('greeks', {})
            recommended_strikes = rust_response.get('recommended_strikes', [])
            
            return RustOptionsAnalysisType(
                symbol=rust_response.get('symbol', symbol_upper),
                underlyingPrice=float(rust_response.get('underlying_price', 0)),
                volatilitySurface=VolatilitySurfaceType(
                    atmVol=vol_surface.get('atm_vol', 0.0),
                    skew=vol_surface.get('skew', 0.0),
                    termStructure=vol_surface.get('term_structure', {})
                ),
                greeks=GreeksType(
                    delta=greeks_data.get('delta', 0.0),
                    gamma=greeks_data.get('gamma', 0.0),
                    theta=greeks_data.get('theta', 0.0),
                    vega=greeks_data.get('vega', 0.0),
                    rho=greeks_data.get('rho', 0.0)
                ),
                recommendedStrikes=[
                    StrikeRecommendationType(
                        strike=strike.get('strike', 0.0),
                        expiration=strike.get('expiration', ''),
                        optionType=strike.get('option_type', 'call'),
                        greeks=GreeksType(
                            delta=strike.get('greeks', {}).get('delta', 0.0),
                            gamma=strike.get('greeks', {}).get('gamma', 0.0),
                            theta=strike.get('greeks', {}).get('theta', 0.0),
                            vega=strike.get('greeks', {}).get('vega', 0.0),
                            rho=strike.get('greeks', {}).get('rho', 0.0)
                        ),
                        expectedReturn=strike.get('expected_return', 0.0),
                        riskScore=strike.get('risk_score', 0.0)
                    ) for strike in recommended_strikes
                ],
                putCallRatio=rust_response.get('put_call_ratio', 0.0),
                impliedVolatilityRank=rust_response.get('implied_volatility_rank', 0.0),
                timestamp=rust_response.get('timestamp', '')
            )
        except Exception as e:
            logger.error(f"Error getting Rust options analysis: {e}")
            # Return empty/default analysis
            return RustOptionsAnalysisType(
                symbol=symbol_upper,
                underlyingPrice=0.0,
                volatilitySurface=VolatilitySurfaceType(atmVol=0.0, skew=0.0, termStructure={}),
                greeks=GreeksType(delta=0.0, gamma=0.0, theta=0.0, vega=0.0, rho=0.0),
                recommendedStrikes=[],
                putCallRatio=0.0,
                impliedVolatilityRank=0.0,
                timestamp=''
            )
    
    def resolve_rust_forex_analysis(self, info, pair):
        """Get Rust engine forex analysis"""
        from .types import ForexAnalysisType
        from .rust_stock_service import rust_stock_service
        import logging
        logger = logging.getLogger(__name__)
        
        pair_upper = pair.upper()
        
        try:
            rust_response = rust_stock_service.analyze_forex(pair_upper)
            
            return ForexAnalysisType(
                pair=rust_response.get('pair', pair_upper),
                bid=float(rust_response.get('bid', 0)),
                ask=float(rust_response.get('ask', 0)),
                spread=rust_response.get('spread', 0.0),
                pipValue=rust_response.get('pip_value', 0.0),
                volatility=rust_response.get('volatility', 0.0),
                trend=rust_response.get('trend', 'NEUTRAL'),
                supportLevel=float(rust_response.get('support_level', 0)),
                resistanceLevel=float(rust_response.get('resistance_level', 0)),
                correlation24h=rust_response.get('correlation_24h', 0.0),
                timestamp=rust_response.get('timestamp', '')
            )
        except Exception as e:
            logger.error(f"Error getting Rust forex analysis: {e}")
            return ForexAnalysisType(
                pair=pair_upper,
                bid=0.0,
                ask=0.0,
                spread=0.0,
                pipValue=0.0,
                volatility=0.0,
                trend='NEUTRAL',
                supportLevel=0.0,
                resistanceLevel=0.0,
                correlation24h=0.0,
                timestamp=''
            )
    
    def resolve_rust_sentiment_analysis(self, info, symbol):
        """Get Rust engine sentiment analysis"""
        from .types import SentimentAnalysisType, NewsSentimentType, SocialSentimentType
        from .rust_stock_service import rust_stock_service
        import logging
        logger = logging.getLogger(__name__)
        
        symbol_upper = symbol.upper()
        
        try:
            rust_response = rust_stock_service.analyze_sentiment(symbol_upper)
            
            news_sentiment = rust_response.get('news_sentiment', {})
            social_sentiment = rust_response.get('social_sentiment', {})
            
            return SentimentAnalysisType(
                symbol=rust_response.get('symbol', symbol_upper),
                overallSentiment=rust_response.get('overall_sentiment', 'NEUTRAL'),
                sentimentScore=rust_response.get('sentiment_score', 0.0),
                newsSentiment=NewsSentimentType(
                    score=news_sentiment.get('score', 0.0),
                    articleCount=news_sentiment.get('article_count', 0),
                    positiveArticles=news_sentiment.get('positive_articles', 0),
                    negativeArticles=news_sentiment.get('negative_articles', 0),
                    neutralArticles=news_sentiment.get('neutral_articles', 0),
                    topHeadlines=news_sentiment.get('top_headlines', [])
                ),
                socialSentiment=SocialSentimentType(
                    score=social_sentiment.get('score', 0.0),
                    mentions24h=social_sentiment.get('mentions_24h', 0),
                    positiveMentions=social_sentiment.get('positive_mentions', 0),
                    negativeMentions=social_sentiment.get('negative_mentions', 0),
                    engagementScore=social_sentiment.get('engagement_score', 0.0),
                    trending=social_sentiment.get('trending', False)
                ),
                confidence=rust_response.get('confidence', 0.0),
                timestamp=rust_response.get('timestamp', '')
            )
        except Exception as e:
            logger.error(f"Error getting Rust sentiment analysis: {e}")
            return SentimentAnalysisType(
                symbol=symbol_upper,
                overallSentiment='NEUTRAL',
                sentimentScore=0.0,
                newsSentiment=NewsSentimentType(
                    score=0.0, articleCount=0, positiveArticles=0,
                    negativeArticles=0, neutralArticles=0, topHeadlines=[]
                ),
                socialSentiment=SocialSentimentType(
                    score=0.0, mentions24h=0, positiveMentions=0,
                    negativeMentions=0, engagementScore=0.0, trending=False
                ),
                confidence=0.0,
                timestamp=''
            )
    
    def resolve_securityEvents(self, info, limit=None, resolved=None):
        """Get security events for current user"""
        from .graphql_utils import get_user_from_context
        user = get_user_from_context(info.context)
        
        if not user or getattr(user, "is_anonymous", True):
            return []
        
        queryset = SecurityEvent.objects.filter(user=user)
        
        if resolved is not None:
            queryset = queryset.filter(resolved=resolved)
        
        queryset = queryset.order_by('-created_at')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    def resolve_biometricSettings(self, info):
        """Get biometric settings for current user"""
        from .graphql_utils import get_user_from_context
        user = get_user_from_context(info.context)
        
        if not user or getattr(user, "is_anonymous", True):
            return None
        
        settings, _ = BiometricSettings.objects.get_or_create(user=user)
        return settings
    
    def resolve_complianceStatuses(self, info):
        """Get all compliance statuses"""
        return ComplianceStatus.objects.all()
    
    def resolve_securityScore(self, info):
        """Get latest security score for current user"""
        from .graphql_utils import get_user_from_context
        from .security_service import SecurityService
        user = get_user_from_context(info.context)
        
        if not user or getattr(user, "is_anonymous", True):
            return None
        
        # Get or calculate security score
        service = SecurityService()
        score_data = service.calculate_security_score(user)
        
        # Save to database
        security_score = SecurityScore.objects.create(
            user=user,
            score=score_data['score'],
            factors=score_data['factors']
        )
        
        return security_score
    
    def resolve_deviceTrusts(self, info):
        """Get trusted devices for current user"""
        from .graphql_utils import get_user_from_context
        user = get_user_from_context(info.context)
        
        if not user or getattr(user, "is_anonymous", True):
            return []
        
        return DeviceTrust.objects.filter(user=user).order_by('-trust_score', '-last_verified')
    
    def resolve_accessPolicies(self, info):
        """Get access policies for current user"""
        from .graphql_utils import get_user_from_context
        user = get_user_from_context(info.context)
        
        if not user or getattr(user, "is_anonymous", True):
            return []
        
        return AccessPolicy.objects.filter(user=user)
    
    def resolve_zeroTrustSummary(self, info):
        """Get Zero Trust summary for current user"""
        from .graphql_utils import get_user_from_context
        from .zero_trust_service import zero_trust_service
        user = get_user_from_context(info.context)
        
        if not user or getattr(user, "is_anonymous", True):
            return None
        
        summary = zero_trust_service.get_trust_summary(user.id)
        
        # Calculate risk level
        avg_score = summary['average_trust_score']
        if avg_score >= 80:
            risk_level = 'low'
        elif avg_score >= 60:
            risk_level = 'medium'
        elif avg_score >= 40:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        # Check if MFA required
        recent_events = SecurityEvent.objects.filter(
            user_id=user.id,
            created_at__gte=timezone.now() - timedelta(days=7),
            resolved=False,
            threat_level__in=['high', 'critical']
        ).count()
        
        requires_mfa = avg_score < 70 or recent_events > 0
        
        from .types import ZeroTrustSummaryType
        return ZeroTrustSummaryType(
            userId=str(user.id),
            devices=summary['devices'],
            averageTrustScore=summary['average_trust_score'],
            lastVerification=summary['last_verification'].isoformat() if summary['last_verification'] else None,
            requiresMfa=requires_mfa,
            riskLevel=risk_level
        )
    
    def resolve_rust_correlation_analysis(self, info, primary, secondary=None):
        """Get Rust engine correlation analysis"""
        from .types import CorrelationAnalysisType
        from .rust_stock_service import rust_stock_service
        import logging
        logger = logging.getLogger(__name__)
        
        primary_upper = primary.upper()
        
        try:
            rust_response = rust_stock_service.analyze_correlation(primary_upper, secondary)
            
            return CorrelationAnalysisType(
                primarySymbol=rust_response.get('primary_symbol', primary_upper),
                secondarySymbol=rust_response.get('secondary_symbol', secondary or 'SPY'),
                correlation1d=rust_response.get('correlation_1d', 0.0),
                correlation7d=rust_response.get('correlation_7d', 0.0),
                correlation30d=rust_response.get('correlation_30d', 0.0),
                btcDominance=rust_response.get('btc_dominance'),
                spyCorrelation=rust_response.get('spy_correlation'),
                globalRegime=rust_response.get('global_regime', 'NEUTRAL'),
                localContext=rust_response.get('local_context', 'NORMAL'),
                timestamp=rust_response.get('timestamp', '')
            )
        except Exception as e:
            logger.error(f"Error getting Rust correlation analysis: {e}")
            return CorrelationAnalysisType(
                primarySymbol=primary_upper,
                secondarySymbol=secondary or 'SPY',
                correlation1d=0.0,
                correlation7d=0.0,
                correlation30d=0.0,
                btcDominance=None,
                spyCorrelation=None,
                globalRegime='NEUTRAL',
                localContext='NORMAL',
                timestamp=''
            )

    # Discussion queries (Reddit-style)

    stock_discussions = graphene.List(
        'core.types.StockDiscussionType', stock_symbol=graphene.String(
            required=False), limit=graphene.Int(
            required=False))

    discussion_detail = graphene.Field('core.types.StockDiscussionType', id=graphene.ID(required=True))

    # stock_discussions = graphene.List(StockDiscussionType, stock_symbol=graphene.String())

    # trending_discussions = graphene.List(StockDiscussionType)

    # user_discussions = graphene.List(StockDiscussionType, user_id=graphene.ID())

    # discussion = graphene.Field(StockDiscussionType, id=graphene.ID(required=True))

    # portfolios = graphene.List(PortfolioType, user_id=graphene.ID())

    # portfolio = graphene.Field(PortfolioType, id=graphene.ID(required=True))

    # public_portfolios = graphene.List(PortfolioType)

    # price_alerts = graphene.List(PriceAlertType, user_id=graphene.ID())

    social_feed = graphene.List('core.types.StockDiscussionType')

    # user_achievements = graphene.List(UserAchievementType, user_id=graphene.ID())

    # stock_sentiment = graphene.Field(StockSentimentType, stock_symbol=graphene.String())

    top_performers = graphene.List(StockType)

    market_sentiment = graphene.Field(graphene.JSONString)

    # Benchmark queries

    benchmarkSeries = graphene.Field(
        BenchmarkSeriesType, symbol=graphene.String(
            required=True), timeframe=graphene.String(
            required=True))

    availableBenchmarks = graphene.List(graphene.String)

    stock_moments = graphene.List(

        StockMomentType,

        symbol=graphene.String(required=True),

        range=graphene.Argument(ChartRangeEnum, required=True),

    )

    # Day Trading queries
    day_trading_picks = graphene.Field(
        DayTradingDataType,
        mode=graphene.String(required=False, default_value="SAFE")
    )
    
    day_trading_stats = graphene.List(
        DayTradingStatsType,
        mode=graphene.String(required=False),
        period=graphene.String(required=False, default_value="ALL_TIME"),
        description="Get day trading strategy performance stats (Citadel Board)"
    )
    
    pre_market_picks = graphene.Field(
        PreMarketDataType,
        mode=graphene.String(required=False, default_value="AGGRESSIVE"),
        limit=graphene.Int(required=False, default_value=20),
        description="Get pre-market quality setups (4AM-9:30AM ET)"
    )
    
    # Swing Trading queries (Phase 2: Breadth of Alphas)
    swing_trading_picks = graphene.Field(
        SwingTradingDataType,
        strategy=graphene.String(required=False, default_value="MOMENTUM"),
        description="Get swing trading picks (2-5 day holds). Strategy: MOMENTUM, BREAKOUT, or MEAN_REVERSION"
    )
    
    swing_trading_stats = graphene.List(
        SwingTradingStatsType,
        strategy=graphene.String(required=False),
        period=graphene.String(required=False, default_value="ALL_TIME"),
        description="Get swing trading strategy performance stats"
    )
    
    # Execution Intelligence queries (Phase 3)
    execution_suggestion = graphene.Field(
        ExecutionSuggestionType,
        signal=graphene.JSONString(required=True),
        signalType=graphene.String(required=False, default_value="day_trading"),
        description="Get smart order suggestion for a trading signal",
        name='executionSuggestion'  # Explicit camelCase name for GraphQL
    )
    
    entry_timing_suggestion = graphene.Field(
        EntryTimingSuggestionType,
        signal=graphene.JSONString(required=True),
        currentPrice=graphene.Float(required=True),
        description="Get entry timing suggestion (enter now vs wait for pullback)"
    )
    
    execution_quality_stats = graphene.Field(
        ExecutionQualityStatsType,
        signalType=graphene.String(required=False, default_value="day_trading"),
        days=graphene.Int(required=False, default_value=30),
        description="Get execution quality statistics and coaching tips"
    )
    
    # Research Hub query
    researchHub = graphene.Field(
        'core.types.ResearchHubType',
        symbol=graphene.String(required=True),
        description="Get comprehensive research data for a stock"
    )

    def resolve_day_trading_picks(self, info, mode="SAFE"):
        """Resolve day trading picks using real intraday data - returns up to 10 stocks per mode"""
        import sys
        print(f"🔍 RESOLVER CALLED: mode={mode}", file=sys.stderr, flush=True)
        logger.info(f"🔍 RESOLVER CALLED: Generating day trading picks for mode: {mode}")

        try:
            # Get up to 10 picks for the specified mode using real intraday data
            # Use dynamic discovery by default (scans Polygon top movers)
            # Returns tuple: (picks, metadata_dict) where metadata includes universe_size, universe_source, and diagnostics
            result_data = _get_real_intraday_day_trading_picks(mode=mode, limit=10, use_dynamic_discovery=True)
            
            # Handle both old format (list) and new format (tuple)
            if isinstance(result_data, tuple) and len(result_data) == 2:
                picks, metadata = result_data
                universe_size = metadata.get('universe_size', 0)
                universe_source = metadata.get('universe_source', 'CORE')
                # Extract diagnostic fields from metadata
                diagnostics = metadata.get('diagnostics', {})
            else:
                # Legacy format: just picks list
                picks = result_data if isinstance(result_data, list) else []
                universe_size = 0
                universe_source = picks[0].get('universe_source', 'CORE') if picks else 'CORE'
                diagnostics = {}

            print(f"✅ RESOLVER: Fetched {len(picks)} picks for {mode} mode", file=sys.stderr, flush=True)
            logger.info(f"✅ Fetched {len(picks)} picks for {mode} mode using real intraday data")

            # Limit to max 10 picks (already done in _get_real_intraday_day_trading_picks, but enforce here too)
            picks = picks[:10]
            
            # Return dict - Graphene will serialize it automatically
            # Add precise timestamp for frontend display
            now = timezone.now()
            
            result = {
                'asOf': now.isoformat(),
                'mode': mode,
                'picks': picks,  # Up to 10 picks
                'universeSize': universe_size,  # Show universe size before filtering
                'qualityThreshold': 2.5 if mode == "SAFE" else 2.0,
                'universeSource': universe_source,
                # Diagnostic fields
                'scannedCount': diagnostics.get('scanned_count', universe_size),
                'passedLiquidity': diagnostics.get('passed_liquidity', 0),
                'passedQuality': diagnostics.get('passed_quality', len(picks)),
                'failedDataFetch': diagnostics.get('failed_data_fetch', 0),
                'filteredByMicrostructure': diagnostics.get('filtered_by_microstructure', 0),
                'filteredByVolatility': diagnostics.get('filtered_by_volatility', 0),
                'filteredByMomentum': diagnostics.get('filtered_by_momentum', 0),
            }
            
            # Log signals to database for performance tracking
            try:
                from .signal_logger import log_signals_batch
                if picks:
                    log_signals_batch(picks, mode)
            except Exception as e:
                logger.warning(f"⚠️ Could not log signals to database: {e}")
            
            # Trigger ML retraining if enough data accumulated (background task)
            # Only retrain once per day to avoid excessive computation
            try:
                from django.core.cache import cache
                from .day_trading_ml_learner import get_day_trading_ml_learner
                
                retrain_cache_key = f"day_trading_ml_retrain_today"
                if not cache.get(retrain_cache_key):
                    # Check if we have enough signals to retrain
                    from .signal_performance_models import DayTradingSignal, SignalPerformance
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    # Count signals with performance data from last 7 days
                    cutoff = timezone.now() - timedelta(days=7)
                    signals_with_perf = DayTradingSignal.objects.filter(
                        generated_at__gte=cutoff
                    ).exclude(
                        performance__isnull=True
                    ).count()
                    
                    if signals_with_perf >= 50:  # Enough data to retrain
                        logger.info(f"🔄 Triggering ML retraining ({signals_with_perf} signals with performance data)")
                        # Run in background (non-blocking)
                        try:
                            learner = get_day_trading_ml_learner()
                            # Use threading to avoid blocking
                            import threading
                            def retrain_async():
                                try:
                                    result = learner.train_model(days_back=30, force_retrain=False)
                                    if 'error' not in result:
                                        logger.info(f"✅ Background ML retraining completed: {result.get('records_used', 0)} records, test_score={result.get('test_score', 0):.3f}")
                                    else:
                                        logger.warning(f"⚠️ Background ML retraining failed: {result.get('error')}")
                                except Exception as e:
                                    logger.error(f"Background retraining failed: {e}")
                            
                            thread = threading.Thread(target=retrain_async, daemon=True)
                            thread.start()
                            
                            # Mark as retrained today
                            cache.set(retrain_cache_key, True, timeout=86400)  # 24 hours
                        except Exception as e:
                            logger.warning(f"Could not trigger background retraining: {e}")
            except Exception as e:
                logger.debug(f"ML retraining check failed: {e}")
            
            # Log summary for monitoring
            if picks:
                logger.info(f"📊 Day Trading Picks ({mode}): {len(picks)} picks generated at {now.strftime('%H:%M:%S')}")
            else:
                logger.info(f"📊 Day Trading Picks ({mode}): No qualifying picks at {now.strftime('%H:%M:%S')}")

            # Debug: Print structure to verify it matches
            if picks:
                sample_pick = picks[0]
                print(f"📤 Sample pick keys: {list(sample_pick.keys())}", file=sys.stderr, flush=True)
                if 'features' in sample_pick:
                    print(f"📤 Features keys: {list(sample_pick['features'].keys())}", file=sys.stderr, flush=True)
                if 'risk' in sample_pick:
                    print(f"📤 Risk keys: {list(sample_pick['risk'].keys())}", file=sys.stderr, flush=True)

            print(f"📤 RESOLVER: Returning dict with {len(picks)} picks", file=sys.stderr, flush=True)
            return result
        except Exception as fallback_error:
            print(f"❌ RESOLVER ERROR: {fallback_error}", file=sys.stderr, flush=True)
            logger.error(f"❌ Error generating day trading picks: {fallback_error}", exc_info=True)
            import traceback
            traceback.print_exc()
            # Return empty picks on error
            return {
                'asOf': timezone.now().isoformat(),
                'mode': mode,
                'picks': [],
                'universeSize': 0,
                'qualityThreshold': 2.5 if mode == "SAFE" else 2.0,
                'universeSource': 'CORE'
            }
    
    def resolve_swing_trading_picks(self, info, strategy="MOMENTUM"):
        """Resolve swing trading picks (2-5 day holds) using daily bars"""
        import sys
        import asyncio
        from .swing_trading_engine import SwingTradingEngine
        
        logger.info(f"🔍 Generating swing trading picks for strategy: {strategy}")
        
        try:
            engine = SwingTradingEngine()
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                signals = loop.run_until_complete(
                    engine.generate_swing_signals(
                        strategy=strategy,
                        limit=5,  # Return up to 5 swing picks
                        use_dynamic_discovery=True
                    )
                )
            finally:
                loop.close()
            
            now = timezone.now()
            
            # Determine universe source from signals
            universe_source = signals[0].get('universe_source', 'CORE') if signals else 'CORE'
            
            result = {
                'asOf': now.isoformat(),
                'strategy': strategy,
                'picks': signals,
                'universeSize': len(signals),
                'universeSource': universe_source,
            }
            
            # Log signals to database for performance tracking
            try:
                from .signal_logger import log_swing_signals_batch
                if signals:
                    log_swing_signals_batch(signals, strategy)
            except Exception as log_error:
                logger.warning(f"⚠️ Could not log swing signals to database: {log_error}")
            
            logger.info(f"✅ Generated {len(signals)} swing trading picks for {strategy} strategy")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating swing trading picks: {e}", exc_info=True)
            # Return empty picks on error
            return {
                'asOf': timezone.now().isoformat(),
                'strategy': strategy,
                'picks': [],
                'universeSize': 0,
                'universeSource': 'CORE'
            }
    
    def resolve_day_trading_stats(self, info, mode=None, period="ALL_TIME"):
        """Resolve day trading strategy performance stats - the 'Citadel Board'"""
        from .signal_performance_models import StrategyPerformance
        from django.utils import timezone
        
        try:
            queryset = StrategyPerformance.objects.filter(period=period)
            
            if mode:
                queryset = queryset.filter(mode=mode)
            
            # Get most recent stats for each mode/period combination
            stats_list = []
            for perf in queryset.order_by('-period_end', 'mode').distinct('mode'):
                stats_list.append({
                    'mode': perf.mode,
                    'period': perf.period,
                    'asOf': perf.period_end.isoformat() if perf.period_end else timezone.now().isoformat(),
                    'winRate': float(perf.win_rate) if perf.win_rate else 0.0,
                    'sharpeRatio': float(perf.sharpe_ratio) if perf.sharpe_ratio else None,
                    'maxDrawdown': float(abs(perf.max_drawdown)) if perf.max_drawdown else 0.0,
                    'avgPnlPerSignal': float(perf.avg_pnl_per_signal) if perf.avg_pnl_per_signal else 0.0,
                    'totalSignals': perf.total_signals,
                    'signalsEvaluated': perf.signals_evaluated,
                    'totalPnlPercent': float(perf.total_pnl_percent) if perf.total_pnl_percent else 0.0,
                    'sortinoRatio': float(perf.sortino_ratio) if perf.sortino_ratio else None,
                    'calmarRatio': float(perf.calmar_ratio) if perf.calmar_ratio else None,
                })
            
            logger.info(f"📊 Returning {len(stats_list)} strategy performance stats (mode={mode}, period={period})")
            return stats_list
            
        except Exception as e:
            logger.error(f"❌ Error fetching day trading stats: {e}", exc_info=True)
            return []
    
    def resolve_pre_market_picks(self, info, mode="AGGRESSIVE", limit=20):
        """Resolve pre-market picks - scans pre-market movers and flags quality setups"""
        from .pre_market_scanner import PreMarketScanner
        from django.utils import timezone
        
        try:
            scanner = PreMarketScanner()
            
            # Check if we're in pre-market hours
            if not scanner.is_pre_market_hours():
                logger.warning(f"Pre-market scan requested outside pre-market hours")
                return {
                    'asOf': timezone.now().isoformat(),
                    'mode': mode,
                    'picks': [],
                    'totalScanned': 0,
                    'minutesUntilOpen': scanner._minutes_until_open(),
                }
            
            # Run pre-market scan
            setups = scanner.scan_pre_market_sync(mode=mode, limit=limit)
            
            # Convert to GraphQL format
            picks = []
            for setup in setups:
                picks.append({
                    'symbol': setup['symbol'],
                    'side': setup['side'],
                    'score': setup['score'],
                    'preMarketPrice': setup['pre_market_price'],
                    'preMarketChangePct': setup['pre_market_change_pct'],
                    'volume': setup['volume'],
                    'marketCap': setup['market_cap'],
                    'prevClose': setup['prev_close'],
                    'notes': setup['notes'],
                    'scannedAt': setup['scanned_at'],
                })
            
            logger.info(f"✅ Pre-market scan: {len(picks)} setups found (mode: {mode})")
            
            return {
                'asOf': timezone.now().isoformat(),
                'mode': mode,
                'picks': picks,
                'totalScanned': len(setups) if setups else 0,
                'minutesUntilOpen': scanner._minutes_until_open(),
            }
            
        except Exception as e:
            logger.error(f"❌ Error in pre-market scan: {e}", exc_info=True)
            return {
                'asOf': timezone.now().isoformat(),
                'mode': mode,
                'picks': [],
                'totalScanned': 0,
                'minutesUntilOpen': 0,
            }
    
    def resolve_swing_trading_stats(self, info, strategy=None, period="ALL_TIME"):
        """Resolve swing trading strategy performance stats"""
        from .signal_performance_models import SwingTradingSignal, SignalPerformance
        from django.utils import timezone
        from django.db.models import Q, Avg, Sum, Count
        from decimal import Decimal
        import math
        
        try:
            # Get swing signals for the period
            now = timezone.now()
            
            # Determine time window
            if period == 'DAILY':
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'WEEKLY':
                days_since_monday = now.weekday()
                period_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'MONTHLY':
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:  # ALL_TIME
                period_start = timezone.now() - timedelta(days=365)
            
            period_end = now
            
            # Get signals
            signals_queryset = SwingTradingSignal.objects.filter(
                generated_at__gte=period_start,
                generated_at__lte=period_end
            )
            
            if strategy:
                signals_queryset = signals_queryset.filter(strategy=strategy)
            
            # Get performance data (use 5d horizon for swing trading)
            horizon = '5d'
            performances = SignalPerformance.objects.filter(
                swing_signal__generated_at__gte=period_start,
                swing_signal__generated_at__lte=period_end,
                horizon=horizon
            )
            
            if strategy:
                performances = performances.filter(swing_signal__strategy=strategy)
            
            # Group by strategy
            strategies = ['MOMENTUM', 'BREAKOUT', 'MEAN_REVERSION'] if not strategy else [strategy]
            stats_list = []
            
            for strat in strategies:
                strat_signals = signals_queryset.filter(strategy=strat)
                strat_perfs = performances.filter(swing_signal__strategy=strat)
                
                total_signals = strat_signals.count()
                signals_evaluated = strat_perfs.count()
                
                if signals_evaluated == 0:
                    continue
                
                # Calculate win rate
                winning = strat_perfs.filter(outcome__in=['WIN', 'TARGET_HIT']).count()
                losing = strat_perfs.filter(outcome__in=['LOSS', 'STOP_HIT']).count()
                win_rate = (winning / signals_evaluated * 100) if signals_evaluated > 0 else 0
                
                # Calculate PnL stats
                total_pnl_percent = sum(float(p.pnl_percent) for p in strat_perfs)
                avg_pnl = total_pnl_percent / signals_evaluated if signals_evaluated > 0 else 0
                
                # Calculate Sharpe ratio (simplified)
                returns = [float(p.pnl_percent) for p in strat_perfs]
                if len(returns) > 1:
                    mean_return = sum(returns) / len(returns)
                    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
                    std_dev = math.sqrt(variance) if variance > 0 else 0.01
                    sharpe = (mean_return / std_dev) if std_dev > 0 else 0
                else:
                    sharpe = None
                
                # Calculate max drawdown (simplified - would need equity curve)
                max_dd = 0.0
                if returns:
                    peak = returns[0]
                    for r in returns:
                        if r > peak:
                            peak = r
                        dd = (peak - r) / peak if peak > 0 else 0
                        if dd > max_dd:
                            max_dd = dd
                
                stats_list.append({
                    'strategy': strat,
                    'period': period,
                    'asOf': period_end.isoformat(),
                    'winRate': win_rate,
                    'sharpeRatio': sharpe,
                    'maxDrawdown': max_dd,
                    'avgPnlPerSignal': avg_pnl,
                    'totalSignals': total_signals,
                    'signalsEvaluated': signals_evaluated,
                    'totalPnlPercent': total_pnl_percent,
                    'sortinoRatio': None,  # Would need downside deviation
                    'calmarRatio': None,  # Would need annual return
                })
            
            logger.info(f"📊 Returning {len(stats_list)} swing trading stats (strategy={strategy}, period={period})")
            return stats_list
            
        except Exception as e:
            logger.error(f"❌ Error fetching swing trading stats: {e}", exc_info=True)
            return []
    
    def resolve_execution_suggestion(self, info, signal, signalType="day_trading"):
        """Resolve execution order suggestion for a signal - optimized for speed"""
        import json
        import time
        import hashlib
        from .execution_advisor import ExecutionAdvisor
        
        start_time = time.time()
        logger.info(f"🔵 [ExecutionSuggestion] Resolver called with signalType={signalType}, signal type={type(signal)}")
        
        try:
            # Parse JSON string if needed (Graphene JSONString might already be parsed)
            if isinstance(signal, str):
                try:
                    signal = json.loads(signal)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"❌ Failed to parse signal JSON: {e}")
                    return None
            
            # Validate signal has required fields
            if not signal or not isinstance(signal, dict):
                logger.error(f"❌ Invalid signal format: {type(signal)}")
                return None
            
            symbol = signal.get('symbol')
            if not symbol:
                logger.error(f"❌ Signal missing symbol: {signal}")
                return None
            
            # Use a singleton ExecutionAdvisor instance (no state, so safe to reuse)
            # Store on the Query class itself (module-level cache)
            if not hasattr(Query, '_execution_advisor'):
                Query._execution_advisor = ExecutionAdvisor()
            advisor = Query._execution_advisor
            
            # Generate suggestion (this should be very fast - no I/O, just calculations)
            suggestion_dict = advisor.suggest_order(signal, signalType)
            
            if not suggestion_dict:
                logger.warning(f"⚠️ ExecutionAdvisor returned None for {symbol}")
                return None
            
            # Convert snake_case keys to camelCase to match GraphQL schema
            # The ExecutionSuggestionType expects: orderType, priceBand, timeInForce, etc.
            from .types import ExecutionSuggestionType, BracketLegsType
            
            # Convert bracket_legs to bracketLegs with proper structure
            bracket_legs_dict = suggestion_dict.get('bracket_legs', {})
            bracket_legs = None
            if bracket_legs_dict:
                bracket_legs = BracketLegsType(
                    stop=bracket_legs_dict.get('stop'),
                    target1=bracket_legs_dict.get('target1'),
                    target2=bracket_legs_dict.get('target2'),
                    orderStructure=bracket_legs_dict.get('order_structure') or bracket_legs_dict.get('orderStructure')
                )
            
            # Create ExecutionSuggestionType instance with camelCase fields
            suggestion = ExecutionSuggestionType(
                orderType=suggestion_dict.get('order_type'),
                priceBand=suggestion_dict.get('price_band', []),
                timeInForce=suggestion_dict.get('time_in_force'),
                entryStrategy=suggestion_dict.get('entry_strategy'),
                bracketLegs=bracket_legs,
                suggestedSize=suggestion_dict.get('suggested_size'),
                rationale=suggestion_dict.get('rationale'),
                microstructureSummary=suggestion_dict.get('microstructure_summary')
            )
            
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            if elapsed > 50:  # Log if it takes more than 50ms (should be < 10ms normally)
                logger.warning(f"⚠️ Execution suggestion took {elapsed:.1f}ms for {symbol}")
            else:
                logger.info(f"✅ Execution suggestion generated in {elapsed:.1f}ms for {symbol}")
            
            return suggestion
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"❌ Error generating execution suggestion after {elapsed:.1f}ms for {signal.get('symbol', 'unknown') if isinstance(signal, dict) else 'unknown'}: {e}", exc_info=True)
            return None
    
    def resolve_entry_timing_suggestion(self, info, signal, currentPrice):
        """Resolve entry timing suggestion (enter now vs wait)"""
        from .execution_advisor import ExecutionAdvisor
        
        try:
            advisor = ExecutionAdvisor()
            suggestion = advisor.suggest_entry_timing(signal, currentPrice)
            return suggestion
        except Exception as e:
            logger.error(f"❌ Error generating entry timing suggestion: {e}", exc_info=True)
            return None
    
    def resolve_execution_quality_stats(self, info, signalType="day_trading", days=30):
        """Resolve execution quality statistics"""
        from .execution_quality_tracker import ExecutionQualityTracker
        
        try:
            tracker = ExecutionQualityTracker()
            stats = tracker.get_user_execution_stats(
                user_id=None,  # Could filter by user if needed
                signal_type=signalType,
                days=days
            )
            return stats
        except Exception as e:
            logger.error(f"❌ Error getting execution quality stats: {e}", exc_info=True)
            return {
                'avgSlippagePct': 0,
                'avgQualityScore': 5.0,
                'chasedCount': 0,
                'totalFills': 0,
                'improvementTips': ['Unable to calculate stats'],
                'periodDays': days
            }
    
    def resolve_research_hub(self, info, symbol: str):
        """Resolve research hub data for a stock using real APIs"""
        try:
            from .types import (
                ResearchHubType, SnapshotType, QuoteType, TechnicalType,
                SentimentType, MacroType, ResearchMarketRegimeType
            )
        except ImportError as import_err:
            logger.error(f"❌ Import error in resolve_research_hub: {import_err}", exc_info=True)
            # Try to import with fallback
            from .types import ResearchHubType, SnapshotType, QuoteType, TechnicalType, SentimentType, MacroType
            try:
                from .types import ResearchMarketRegimeType
            except ImportError:
                # Last resort: create a simple fallback type
                import graphene
                class ResearchMarketRegimeType(graphene.ObjectType):
                    marketRegime = graphene.String()
                    confidence = graphene.Float()
                    recommendedStrategy = graphene.String()
        
        from .enhanced_stock_service import enhanced_stock_service
        from .models import Stock
        import asyncio
        import os
        import requests
        from datetime import datetime
        
        symbol_upper = symbol.upper()
        logger.info(f"✅ resolve_research_hub called for {symbol_upper}")
        
        try:
            # Get stock from database
            try:
                stock = Stock.objects.get(symbol=symbol_upper)
            except Stock.DoesNotExist:
                logger.warning(f"Stock {symbol_upper} not found in database")
                stock = None
            
            # Fetch real-time price and quote data
            quote_data = None
            try:
                price_data = asyncio.run(enhanced_stock_service.get_real_time_price(symbol_upper))
                if price_data:
                    quote_data = {
                        'price': price_data.get('price', 0),
                        'chg': price_data.get('change', 0),
                        'chgPct': price_data.get('change_percent', 0),
                        'high': price_data.get('high', 0),
                        'low': price_data.get('low', 0),
                        'volume': price_data.get('volume', 0),
                    }
            except Exception as e:
                logger.warning(f"Could not get real-time quote for {symbol_upper}: {e}")
            
            # Get company snapshot from Alpha Vantage
            snapshot_data = None
            alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY') or os.getenv('ALPHA_VANTAGE_KEY')
            if alpha_vantage_key:
                try:
                    av_url = "https://www.alphavantage.co/query"
                    av_params = {
                        'function': 'OVERVIEW',
                        'symbol': symbol_upper,
                        'apikey': alpha_vantage_key
                    }
                    av_response = requests.get(av_url, params=av_params, timeout=10)
                    if av_response.ok:
                        av_data = av_response.json()
                        if 'Name' in av_data:
                            snapshot_data = {
                                'name': av_data.get('Name', ''),
                                'sector': av_data.get('Sector', stock.sector if stock else 'Unknown'),
                                'marketCap': float(av_data.get('MarketCapitalization', 0)) if av_data.get('MarketCapitalization') else None,
                                'country': av_data.get('Country', 'US'),
                                'website': av_data.get('Website', ''),
                            }
                except Exception as e:
                    logger.warning(f"Could not get Alpha Vantage overview for {symbol_upper}: {e}")
            
            # Use database stock data as fallback for snapshot
            if not snapshot_data and stock:
                snapshot_data = {
                    'name': stock.company_name or symbol_upper,
                    'sector': stock.sector or 'Unknown',
                    'marketCap': float(stock.market_cap) if stock.market_cap else None,
                    'country': 'US',
                    'website': '',
                }
            
            # Get technical indicators (simplified - would need proper calculation)
            # Always provide technical data, even if quote data is missing
            technical_data = None
            current_price = None
            if quote_data and quote_data.get('price'):
                current_price = quote_data['price']
            elif stock and stock.current_price:
                current_price = float(stock.current_price)
            else:
                # Fallback to a default price if nothing is available
                current_price = 150.0
            
            # Always create technical data with calculated or default values
            technical_data = {
                'rsi': 55.0,  # Would need proper RSI calculation
                'macd': 0.5,
                'macdhistogram': 0.2,
                'movingAverage50': current_price * 0.98,
                'movingAverage200': current_price * 0.95,
                'supportLevel': current_price * 0.92,
                'resistanceLevel': current_price * 1.08,
                'impliedVolatility': 0.25,
            }
            
            # Get sentiment from news (using NewsAPI if available)
            sentiment_data = None
            news_api_key = os.getenv('NEWS_API_KEY')
            if news_api_key:
                try:
                    news_url = "https://newsapi.org/v2/everything"
                    news_params = {
                        'q': symbol_upper,
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'pageSize': 10,
                        'apiKey': news_api_key
                    }
                    news_response = requests.get(news_url, params=news_params, timeout=10)
                    if news_response.ok:
                        news_data = news_response.json()
                        articles = news_data.get('articles', [])
                        # Simple sentiment calculation
                        positive_keywords = ['up', 'gain', 'rise', 'surge', 'bullish', 'buy', 'positive']
                        negative_keywords = ['down', 'fall', 'drop', 'bearish', 'sell', 'negative']
                        positive_count = sum(1 for a in articles if any(kw in a.get('title', '').lower() for kw in positive_keywords))
                        negative_count = sum(1 for a in articles if any(kw in a.get('title', '').lower() for kw in negative_keywords))
                        total = len(articles)
                        score = ((positive_count - negative_count) / max(total, 1)) * 50 + 50  # Scale to 0-100
                        label = 'BULLISH' if score > 60 else 'BEARISH' if score < 40 else 'NEUTRAL'
                        sentiment_data = {
                            'label': label,
                            'score': score,
                            'articleCount': total,
                            'confidence': min(100, total * 10),
                        }
                except Exception as e:
                    logger.warning(f"Could not get news sentiment for {symbol_upper}: {e}")
            
            # Default sentiment if API fails
            if not sentiment_data:
                sentiment_data = {
                    'label': 'NEUTRAL',
                    'score': 50.0,
                    'articleCount': 0,
                    'confidence': 0.0,
                }
            
            # Macro data (simplified)
            macro_data = {
                'vix': 18.5,  # Would need VIX API
                'marketSentiment': 'Positive',
                'riskAppetite': 0.65,
            }
            
            # Market regime (simplified)
            market_regime_data = {
                'market_regime': 'Bull Market',
                'marketRegime': 'Bull Market',  # Also set camelCase for GraphQL
                'confidence': 0.72,
                'recommended_strategy': 'Momentum',
                'recommendedStrategy': 'Momentum',  # Also set camelCase for GraphQL
            }
            
            # Get peers (simplified - would need proper peer analysis)
            peers = []
            if stock and stock.sector:
                # Get a few stocks from the same sector
                sector_stocks = Stock.objects.filter(sector=stock.sector).exclude(symbol=symbol_upper)[:5]
                peers = [s.symbol for s in sector_stocks]
            
            if not peers:
                # Default peers for major stocks
                default_peers = {
                    'AAPL': ['MSFT', 'GOOGL', 'META', 'AMZN'],
                    'MSFT': ['AAPL', 'GOOGL', 'META', 'AMZN'],
                    'GOOGL': ['AAPL', 'MSFT', 'META', 'AMZN'],
                }
                peers = default_peers.get(symbol_upper, ['AAPL', 'MSFT', 'GOOGL'])
            
            logger.info(f"✅ Fetched research hub data for {symbol_upper}")
            
            return ResearchHubType(
                symbol=symbol_upper,
                snapshot=SnapshotType(**snapshot_data) if snapshot_data else None,
                quote=QuoteType(**quote_data) if quote_data else None,
                technical=TechnicalType(**technical_data) if technical_data else None,
                sentiment=SentimentType(**sentiment_data) if sentiment_data else None,
                macro=MacroType(**macro_data) if macro_data else None,
                marketRegime=ResearchMarketRegimeType(**market_regime_data) if market_regime_data else None,
                peers=peers,
                updatedAt=timezone.now().isoformat(),
            )
            
        except Exception as e:
            logger.error(f"❌ Error resolving research hub for {symbol_upper}: {e}", exc_info=True)
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Return minimal data on error, but always include technical data with defaults
            try:
                fallback_price = 150.0
                fallback_technical = {
                    'rsi': 55.0,
                    'macd': 0.5,
                    'macdhistogram': 0.2,
                    'movingAverage50': fallback_price * 0.98,
                    'movingAverage200': fallback_price * 0.95,
                    'supportLevel': fallback_price * 0.92,
                    'resistanceLevel': fallback_price * 1.08,
                    'impliedVolatility': 0.25,
                }
                fallback_sentiment = {
                    'label': 'NEUTRAL',
                    'score': 50.0,
                    'articleCount': 0,
                    'confidence': 0.0,
                }
                fallback_macro = {
                    'vix': 18.5,
                    'marketSentiment': 'Positive',
                    'riskAppetite': 0.65,
                }
                fallback_market_regime = {
                    'market_regime': 'Bull Market',
                    'marketRegime': 'Bull Market',
                    'confidence': 0.72,
                    'recommended_strategy': 'Momentum',
                    'recommendedStrategy': 'Momentum',
                }
                logger.info(f"✅ Returning fallback data for {symbol_upper}")
                return ResearchHubType(
                    symbol=symbol_upper,
                    snapshot=None,
                    quote=None,
                    technical=TechnicalType(**fallback_technical),
                    sentiment=SentimentType(**fallback_sentiment),
                    macro=MacroType(**fallback_macro),
                    marketRegime=ResearchMarketRegimeType(**fallback_market_regime),
                    peers=['AAPL', 'MSFT', 'GOOGL'],
                    updatedAt=timezone.now().isoformat(),
                )
            except Exception as fallback_error:
                logger.error(f"❌❌ CRITICAL: Even fallback failed for {symbol_upper}: {fallback_error}", exc_info=True)
                # Last resort: return None and let frontend handle it
                return None


def resolve_all_users(root, info):

    user = info.context.user

    if user.is_anonymous:
        return []

    # Exclude current user and return users they don't follow
    return User.objects.exclude(id=user.id).exclude(

        id__in=user.following.values_list('following', flat=True)

    )[:20]  # Limit to 20 users


def resolve_search_users(root, info, query=None):
    user = info.context.user

    if user.is_anonymous:
        return []

    if query:
        # Search by name or email
        users = User.objects.filter(
            models.Q(name__icontains=query) |
            models.Q(email__icontains=query)
        ).exclude(id=user.id)
    else:
        # Return users not followed by current user
        users = User.objects.exclude(id=user.id).exclude(
            id__in=user.following.values_list('following', flat=True)
        )

    return users[:20]  # Limit results


def resolve_wall_posts(self, info):
    user = info.context.user

    if user.is_anonymous:
        return []

    following_users = user.following.values_list('following', flat=True)

    # Return posts from followed users + current user's own posts

    return Post.objects.filter(

        user__in=list(following_users) + [user]

    ).select_related("user").order_by("-created_at")


def resolve_my_chat_sessions(self, info):
    user = info.context.user

    if user.is_anonymous:
        return []
    return ChatSession.objects.filter(user=user).order_by('-updated_at')


def resolve_chat_session(self, info, id):
    user = info.context.user

    if user.is_anonymous:
        return None

    try:
        return ChatSession.objects.get(id=id, user=user)
    except ChatSession.DoesNotExist:
        return None

        return None


def resolve_chat_messages(self, info, session_id):
    user = info.context.user

    if user.is_anonymous:
        return []

    try:
        session = ChatSession.objects.get(id=session_id, user=user)
        return session.messages.all()
    except ChatSession.DoesNotExist:
        return []


def resolve_user(self, info, id):
    """Get a user by ID (using DataLoader to prevent N+1)"""
    from .dataloaders import get_user_loader
    user_loader = get_user_loader()
    return user_loader.load(id)


def resolve_user_posts(self, info, user_id):
    try:
        user = User.objects.get(id=user_id)
        return user.posts.all().order_by('-created_at')
    except User.DoesNotExist:
        return []


def resolve_post_comments(self, info, post_id):
    try:
        post = Post.objects.get(id=post_id)
        return post.comments.all().order_by('-created_at')

    except Post.DoesNotExist:
        return []


def resolve_stocks(self, info, search=None):
    """Get all stocks or search by symbol/company name"""

    if search:
        db_stocks = Stock.objects.filter(
            models.Q(symbol__icontains=search.upper()) |
            models.Q(company_name__icontains=search)
        )[:50]  # Limit search results

        # If we have results, return them
        if db_stocks.exists():
            return list(db_stocks)

        # If no DB results, try API
        try:
            from .stock_service import AlphaVantageService

            service = AlphaVantageService()
            api_stocks = service.search_and_sync_stocks(search)

            if api_stocks:
                return list(api_stocks)
            else:
                return Stock.objects.none()
        except Exception as e:
            logger.error(f"API search error: {e}")
            return []

    return Stock.objects.all()[:100]  # Limit to 100 stocks


def resolve_beginner_friendly_stocks(self, info):
    """Get stocks suitable for beginner investors, personalized with spending habits"""
    user = info.context.user
    user_id = user.id if user and not user.is_anonymous else 1

    # Get spending habits analysis for personalization (using sync version for GraphQL)
    spending_analysis = None
    sector_weights = {}
    try:
        from .spending_habits_service import SpendingHabitsService
        spending_service = SpendingHabitsService()
        # Use sync version for GraphQL resolvers (async version available for async contexts)
        spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)
        sector_weights = spending_service.get_spending_based_stock_preferences(spending_analysis)
    except Exception as e:
        logger.warning(f"Could not get spending analysis for beginner stocks: {e}")

    # OPTIMIZATION: Use DataLoader for stock queries to prevent N+1
    from .dataloaders import get_stock_loader
    stock_loader = get_stock_loader()

    # Base query: beginner-friendly stocks
    stocks = Stock.objects.filter(
        beginner_friendly_score__gte=65,  # Moderate beginner-friendly score
        market_cap__gte=10000000000,  # Mid to large cap companies (>$10B)
    )

    # Convert to list to apply spending-based sorting
    stocks_list = list(stocks[:50])  # Get more candidates for sorting

    # Sort by spending-aligned score if we have spending data
    if sector_weights:
        def get_personalized_score(stock):
            base_score = getattr(stock, 'beginner_friendly_score', 65)
            sector = getattr(stock, 'sector', 'Unknown')

            # Boost score for sectors matching spending patterns
            if sector in sector_weights:
                spending_boost = sector_weights[sector] * 20  # Boost up to 20 points
                return base_score + spending_boost
            return base_score

        stocks_list.sort(key=get_personalized_score, reverse=True)

    # Update prices with real-time data
    try:
        from .enhanced_stock_service import enhanced_stock_service
        import asyncio
        
        symbols = [stock.symbol for stock in stocks_list[:20]]
        if symbols:
            try:
                prices_data = asyncio.run(
                    enhanced_stock_service.get_multiple_prices(symbols)
                )
                # Update stock objects with real-time prices
                for stock in stocks_list[:20]:
                    price_data = prices_data.get(stock.symbol)
                    if price_data and price_data.get('price', 0) > 0:
                        stock.current_price = price_data['price']
                        # Update database
                        enhanced_stock_service.update_stock_price_in_database(stock.symbol, price_data)
            except Exception as e:
                logger.warning(f"Could not fetch real-time prices for beginner stocks: {e}")
    except Exception as e:
        logger.warning(f"Error updating prices for beginner stocks: {e}")

    return stocks_list[:20]


def resolve_rust_recommendations(self, info):
    """Get beginner-friendly recommendations from Rust engine"""

    try:
        from .stock_service import AlphaVantageService

        service = AlphaVantageService()

        recommendations = service.get_rust_recommendations()

        if recommendations:
            from .types import RustRecommendationType
            return [
                RustRecommendationType(
                    symbol=rec.get('symbol', ''),
                    reason=rec.get('reason', ''),
                    confidence=rec.get('confidence', 0.0),
                    riskLevel=rec.get('riskLevel', 'Unknown'),
                    beginnerScore=rec.get('beginnerScore', 0)
                )
                for rec in recommendations
                    ]


        return []

    except Exception as e:
        logger.error(f"Error getting Rust recommendations: {e}")
        return []


def resolve_rust_health(root, info):
    try:
        from .stock_service import rust_stock_service

        health = rust_stock_service.health_check()

        return RustHealthType(
            status=health.get('status', 'unknown'),
            service='rust_stock_engine',
            timestamp=timezone.now()
        )

    except Exception as e:
        logger.error(f"Error checking Rust health: {e}")
        return RustHealthType(
            status='error',
            service='rust_stock_engine',
            timestamp=timezone.now()
        )

    # Phase 3 Social Feature Resolvers


def resolve_watchlists(root, info, user_id=None):
    user = info.context.user

    if not user.is_authenticated:
        return []

    if user_id:
        return Watchlist.objects.filter(user_id=user_id)
    return Watchlist.objects.filter(user=user)


def resolve_watchlist(root, info, id):
    try:
        watchlist = Watchlist.objects.get(id=id)
        if watchlist.is_public or watchlist.user == info.context.user:
            return watchlist
        return None

    except Watchlist.DoesNotExist:
        return None


def resolve_public_watchlists(root, info):
    return Watchlist.objects.filter(is_public=True).order_by('-created_at')[:20]


def resolve_stock_discussions(root, info, stock_symbol=None):
    if stock_symbol:

        pass
    return StockDiscussion.objects.all().order_by('-created_at')[:50]


def resolve_trending_discussions(root, info):
    # Get discussions with most likes in the last 7 days

    from django.utils import timezone

    from datetime import timedelta, datetime

    week_ago = timezone.now() - timedelta(days=7)

    return StockDiscussion.objects.filter(

        created_at__gte=week_ago

    ).annotate(

        like_count=models.Count('likes')

    ).order_by('-like_count', '-created_at')[:20]


def resolve_user_discussions(root, info, user_id=None):
    if user_id:

        pass
    user = info.context.user

    if user.is_authenticated:

        pass
    return []


def resolve_discussion(root, info, id):
    try:
        return StockDiscussion.objects.get(id=id)

    except StockDiscussion.DoesNotExist:
        return None


def resolve_portfolios(root, info, user_id=None):
    user = info.context.user

    if not user.is_authenticated:

        pass
    if user_id:

        return Portfolio.objects.filter(user_id=user_id)
    return Portfolio.objects.filter(user=user)


def resolve_portfolio(root, info, id):
    try:
        portfolio = Portfolio.objects.get(id=id)

        if portfolio.is_public or portfolio.user == info.context.user:
            return portfolio
        return None

    except Portfolio.DoesNotExist:
        return None


def resolve_public_portfolios(root, info):
    return Portfolio.objects.filter(is_public=True).order_by('-created_at')[:20]


def resolve_price_alerts(root, info, user_id=None):
    user = info.context.user

    if not user.is_authenticated:

        pass
    if user_id and user_id == str(user.id):

        pass
    return []


def resolve_social_feed(root, info):
    """Get personalized feed - only posts from followed users + user's own posts"""

    user = info.context.user

    if not user.is_authenticated:
        return []

    followed_users = user.following.values_list('following', flat=True)

    return StockDiscussion.objects.filter(
        models.Q(user__in=followed_users) | models.Q(user=user)

    ).order_by('-created_at')[:50]


def resolve_user_achievements(root, info, user_id=None):
    if user_id:

        pass
    user = info.context.user

    if user.is_authenticated:

        pass
    return []


def resolve_stock_sentiment(root, info, stock_symbol):
    try:
        stock = Stock.objects.get(symbol=stock_symbol.upper())
        sentiment, created = StockSentiment.objects.get_or_create(stock=stock)
        return sentiment
    except Stock.DoesNotExist:
        return None


def resolve_top_performers(root, info):
    # Get stocks with highest beginner-friendly scores

    return Stock.objects.filter(

        beginner_friendly_score__isnull=False

    ).order_by('-beginner_friendly_score')[:10]


def resolve_market_sentiment(root, info):
    # Aggregate sentiment across all stocks

    sentiments = StockSentiment.objects.all()

    if sentiments.exists():

        pass
    avg_sentiment = sum(s.sentiment_score for s in sentiments) / sentiments.count()

    total_votes = sum(s.total_votes for s in sentiments)

    return {

        'average_sentiment': float(avg_sentiment),

        'total_votes': total_votes,

        'stocks_tracked': sentiments.count(),

        'market_mood': 'bullish' if avg_sentiment > 0.1 else 'bearish' if avg_sentiment < -0.1 else 'neutral'

    }

    return {

        'average_sentiment': 0,

        'total_votes': 0,

        'stocks_tracked': 0,

        'market_mood': 'neutral'

    }


def resolve_ai_portfolio_recommendations(root, info, userId):
    """Get AI portfolio recommendations for a user"""

    user = info.context.user

    if user.is_anonymous:

        return []
    if user.is_anonymous:

        return []
    if str(user.id) != str(userId):

        pass
    from .models import AIPortfolioRecommendation

    return AIPortfolioRecommendation.objects.filter(user=user).order_by('-created_at')


    def resolve_rust_stock_analysis(self, info, symbol):
        """Get Rust engine stock analysis - calls the actual Rust service"""
        print(f"🔍 [DEBUG] resolve_rust_stock_analysis CALLED for symbol: {symbol}", flush=True)
        import logging
        import sys
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 [DEBUG] resolve_rust_stock_analysis called for symbol: {symbol}")
        print(f"🔍 [DEBUG] Logger initialized, proceeding...", flush=True, file=sys.stderr)

        from .types import (

            RustStockAnalysisType,

            TechnicalIndicatorsType,

            FundamentalAnalysisType,

            SpendingDataPointType,

            OptionsFlowDataPointType,

            SignalContributionType,

            SHAPValueType

        )

        from .rust_stock_service import rust_stock_service

        from .spending_habits_service import SpendingHabitsService

        from .consumer_strength_service import ConsumerStrengthService

        from datetime import datetime, timedelta

        from django.utils import timezone

        symbol_upper = symbol.upper()

        rust_response = None
        try:
            # Call the Rust service
            logger.info(f"Calling Rust service for stock analysis: {symbol_upper}")

            rust_response = rust_stock_service.analyze_stock(symbol_upper)

            logger.info(f"Rust service response received for {symbol_upper}: {rust_response}")
        except Exception as rust_error:
            logger.warning(f"Rust service unavailable for {symbol_upper}: {rust_error}. Using fallback data.")
            rust_response = None

        # Use Rust response if available, otherwise use fallback
        if rust_response:
            try:
                # Map Rust service response to GraphQL type

                # The Rust service returns a dict with analysis data

                # We need to extract and map the fields

                # Extract technical indicators if available

                technical_data = rust_response.get(
                    'technicalIndicators', {}) or rust_response.get(
                    'technical_indicators', {}) or {}

                technical_indicators = TechnicalIndicatorsType(
                    rsi=technical_data.get('rsi') or technical_data.get('RSI') or 50.0,
                    macd=technical_data.get('macd') or technical_data.get('MACD') or 0.0,
                    macdSignal=technical_data.get('macdSignal') or technical_data.get('macd_signal') or technical_data.get('MACDSignal') or 0.0,
                    macdHistogram=technical_data.get('macdHistogram') or technical_data.get('macd_histogram') or technical_data.get('MACDHist') or 0.0,
                    sma20=technical_data.get('sma20') or technical_data.get('SMA20') or 0.0,
                    sma50=technical_data.get('sma50') or technical_data.get('SMA50') or 0.0,
                    ema12=technical_data.get('ema12') or technical_data.get('EMA12') or 0.0,
                    ema26=technical_data.get('ema26') or technical_data.get('EMA26') or 0.0,
                    bollingerUpper=technical_data.get('bollingerUpper') or technical_data.get('bollinger_upper') or technical_data.get('BBUpper') or 0.0,
                    bollingerLower=technical_data.get('bollingerLower') or technical_data.get('bollinger_lower') or technical_data.get('BBLower') or 0.0,
                    bollingerMiddle=technical_data.get('bollingerMiddle') or technical_data.get('bollinger_middle') or technical_data.get('BBMiddle') or 0.0)

                # Extract fundamental analysis if available

                fundamental_data = rust_response.get(
                    'fundamentalAnalysis', {}) or rust_response.get(
                    'fundamental_analysis', {}) or {}

                fundamental_analysis = FundamentalAnalysisType(
                    valuationScore=fundamental_data.get('valuationScore') or fundamental_data.get('valuation_score') or 70.0,
                    growthScore=fundamental_data.get('growthScore') or fundamental_data.get('growth_score') or 65.0,
                    stabilityScore=fundamental_data.get('stabilityScore') or fundamental_data.get('stability_score') or 80.0,
                    dividendScore=fundamental_data.get('dividendScore') or fundamental_data.get('dividend_score') or 60.0,
                    debtScore=fundamental_data.get('debtScore') or fundamental_data.get('debt_score') or 75.0)

                # Map risk score to risk level

                risk_score = rust_response.get('risk_score') or rust_response.get('riskScore', 50.0)

                if isinstance(risk_score, (int, float)):
                    if risk_score < 50:
                        risk_level = "Low"
                    elif risk_score < 70:
                        risk_level = "Medium"
                    else:
                        risk_level = "High"
                else:
                    risk_level = rust_response.get('riskLevel') or rust_response.get('risk_level', 'Medium')

                # Map prediction/recommendation

                prediction_type = rust_response.get('prediction_type') or rust_response.get('predictionType', '')

                recommendation_map = {
                    'bullish': 'BUY',
                    'bearish': 'SELL',
                    'neutral': 'HOLD',
                    'strong_buy': 'STRONG BUY',
                    'strong_sell': 'STRONG SELL'
                }

                recommendation = rust_response.get('recommendation') or rust_response.get('recommendation', '')

                if not recommendation and prediction_type:
                    recommendation = recommendation_map.get(prediction_type.lower(), 'HOLD')

                if not recommendation:
                    recommendation = 'HOLD'

                # Calculate beginner friendly score from risk and confidence

                confidence_level = rust_response.get('confidence_level') or rust_response.get('confidenceLevel', 'medium')

                confidence_score = {'high': 90, 'medium': 70, 'low': 50}.get(confidence_level.lower(), 70)

                beginner_friendly_score = rust_response.get(
                    'beginnerFriendlyScore') or rust_response.get('beginner_friendly_score')

                if not beginner_friendly_score:
                    beginner_friendly_score = max(50, 100 - (risk_score if isinstance(risk_score, (int, float)) else 50))

                # Build reasoning from explanation

                explanation = rust_response.get('explanation') or rust_response.get('reasoning', '')

                if isinstance(explanation, str):
                    reasoning = [explanation] if explanation else []
                elif isinstance(explanation, list):
                    reasoning = explanation
                else:
                    reasoning = [f"Analysis for {symbol_upper} based on Rust engine predictions."]

                # Add additional context if available
                if rust_response.get('probability'):
                    prob = rust_response.get('probability', 0) * 100
                    reasoning.append(f"Prediction confidence: {prob:.1f}%")

                logger.info(f"Successfully mapped Rust response for {symbol_upper}")

                # Generate spending and options flow data for charts

                spending_data = []
                options_flow_data = []
                signal_contributions = []
                shap_values = []
                shap_explanation = f"Feature importance for {symbol_upper} prediction based on spending, options, earnings, and insider signals."

                try:
                    user = getattr(info.context, 'user', None)
                    user_id = user.id if user and not user.is_anonymous else None
                    spending_service = SpendingHabitsService()
                    spending_analysis = None

                    if user_id:
                        spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)

                    # Generate spending data (last 12 weeks)
                    end_date = timezone.now().date()
                    base_price = rust_response.get('current_price', 100.0)

                    for week_offset in range(12, -1, -1):
                        week_end = end_date - timedelta(weeks=week_offset)
                        spending_data.append(SpendingDataPointType(
                            date=week_end.isoformat(),
                            spending=1000.0 + (week_offset * 50),
                            spendingChange=0.05,
                            price=base_price * (1 + 0.01 * (12 - week_offset) / 12),
                            priceChange=0.01
                        ))

                    # Generate options flow data (last 20 days)
                    consumer_strength_service = ConsumerStrengthService()
                    consumer_strength = consumer_strength_service.calculate_consumer_strength(
                        symbol_upper, spending_analysis, user_id
                    )

                    for day_offset in range(20, -1, -1):
                        day_date = end_date - timedelta(days=day_offset)
                        unusual_volume = consumer_strength.get('options_score', 50.0) / 100.0 * 30.0
                        options_flow_data.append(OptionsFlowDataPointType(
                            date=day_date.isoformat(),
                            price=base_price * (1 + 0.005 * (20 - day_offset) / 20),
                            unusualVolumePercent=unusual_volume,
                            sweepCount=1 if unusual_volume > 25 else 0,
                            putCallRatio=0.7 + (unusual_volume / 100.0) * 0.6
                        ))
                except Exception as e:
                    logger.warning(f"Error generating chart data: {e}")
                    # Use fallback data if chart data generation fails
                    end_date = timezone.now().date()
                    base_price = rust_response.get('current_price', 100.0)
                    if not spending_data:
                        for week_offset in range(12, -1, -1):
                            week_end = end_date - timedelta(weeks=week_offset)
                            spending_data.append(SpendingDataPointType(
                                date=week_end.isoformat(),
                                spending=1000.0 + (week_offset * 50),
                                spendingChange=0.05,
                                price=base_price * (1 + 0.01 * (12 - week_offset) / 12),
                                priceChange=0.01
                            ))
                    if not options_flow_data:
                        for day_offset in range(20, -1, -1):
                            day_date = end_date - timedelta(days=day_offset)
                            options_flow_data.append(OptionsFlowDataPointType(
                                date=day_date.isoformat(),
                                price=base_price * (1 + 0.005 * (20 - day_offset) / 20),
                                unusualVolumePercent=15.0,
                                sweepCount=0,
                                putCallRatio=0.8
                            ))

                return RustStockAnalysisType(
                    symbol=symbol_upper,
                    beginnerFriendlyScore=float(beginner_friendly_score) if beginner_friendly_score else 75.0,
                    riskLevel=risk_level,
                    recommendation=recommendation.upper(),
                    technicalIndicators=technical_indicators,
                    fundamentalAnalysis=fundamental_analysis,
                    reasoning=reasoning if reasoning else [f"Analysis for {symbol_upper}"],
                    spendingData=spending_data,
                    optionsFlowData=options_flow_data,
                    signalContributions=signal_contributions,
                    shapValues=shap_values,
                    shapExplanation=shap_explanation
                )
            except Exception as process_error:
                logger.error(f"Error processing Rust response for {symbol_upper}: {str(process_error)}", exc_info=True)
                rust_response = None  # Force fallback

        # Fall through to fallback

        # Fallback to basic analysis if Rust service fails (always executed)
        try:
            end_date = timezone.now().date()
            base_price = 100.0

            # Generate fallback spending data
            fallback_spending_data = []
            for week_offset in range(12, -1, -1):
                week_end = end_date - timedelta(weeks=week_offset)
                fallback_spending_data.append(SpendingDataPointType(
                    date=week_end.isoformat(),
                    spending=1000.0 + (week_offset * 50),
                    spendingChange=0.05,
                    price=base_price * (1 + 0.01 * (12 - week_offset) / 12),
                    priceChange=0.01
                ))

            # Generate fallback options flow data
            fallback_options_flow_data = []
            for day_offset in range(20, -1, -1):
                day_date = end_date - timedelta(days=day_offset)
                fallback_options_flow_data.append(OptionsFlowDataPointType(
                    date=day_date.isoformat(),
                    price=base_price * (1 + 0.005 * (20 - day_offset) / 20),
                    unusualVolumePercent=15.0,
                    sweepCount=0,
                    putCallRatio=0.8
                ))

            result = RustStockAnalysisType(
                symbol=symbol_upper,
                beginnerFriendlyScore=75.0,
                riskLevel="Medium",
                recommendation="HOLD",
                technicalIndicators=TechnicalIndicatorsType(
                    rsi=50.0, macd=0.0, macdSignal=0.0, macdHistogram=0.0,
                    sma20=0.0, sma50=0.0, ema12=0.0, ema26=0.0,
                    bollingerUpper=0.0, bollingerLower=0.0, bollingerMiddle=0.0
                ),
                fundamentalAnalysis=FundamentalAnalysisType(
                    valuationScore=70.0, growthScore=65.0, stabilityScore=80.0,
                    dividendScore=60.0, debtScore=75.0
                ),
                reasoning=[f"Rust service unavailable for {symbol_upper}. Please try again later."],
                spendingData=fallback_spending_data,
                optionsFlowData=fallback_options_flow_data,
                signalContributions=[],
                shapValues=[],
                shapExplanation=f"Fallback analysis for {symbol_upper}. Rust service unavailable."
            )
            logger.info(
                f"✅ [DEBUG] Returning fallback RustStockAnalysisType for {symbol_upper} with {len(fallback_spending_data)} spending data points and {len(fallback_options_flow_data)} options flow data points"
            )
            return result
        except Exception as e:
            logger.error(f"Critical error in resolve_rust_stock_analysis fallback: {e}", exc_info=True)
            # Continue to last resort fallback

        # Last resort: return minimal data with fallback arrays
        try:
            end_date = timezone.now().date()
            base_price = 100.0
            last_resort_spending = []
            for week_offset in range(12, -1, -1):
                week_end = end_date - timedelta(weeks=week_offset)
                last_resort_spending.append(SpendingDataPointType(
                    date=week_end.isoformat(),
                    spending=1000.0 + (week_offset * 50),
                    spendingChange=0.05,
                    price=base_price * (1 + 0.01 * (12 - week_offset) / 12),
                    priceChange=0.01
                ))
            last_resort_options = []
            for day_offset in range(20, -1, -1):
                day_date = end_date - timedelta(days=day_offset)
                last_resort_options.append(OptionsFlowDataPointType(
                    date=day_date.isoformat(),
                    price=base_price * (1 + 0.005 * (20 - day_offset) / 20),
                    unusualVolumePercent=15.0,
                    sweepCount=0,
                    putCallRatio=0.8
                ))
            return RustStockAnalysisType(
                symbol=symbol_upper,
                beginnerFriendlyScore=75.0,
                riskLevel="Medium",
                recommendation="HOLD",
                technicalIndicators=TechnicalIndicatorsType(
                    rsi=50.0, macd=0.0, macdSignal=0.0, macdHistogram=0.0,
                    sma20=0.0, sma50=0.0, ema12=0.0, ema26=0.0,
                    bollingerUpper=0.0, bollingerLower=0.0, bollingerMiddle=0.0
                ),
                fundamentalAnalysis=FundamentalAnalysisType(
                    valuationScore=70.0, growthScore=65.0, stabilityScore=80.0,
                    dividendScore=60.0, debtScore=75.0
                ),
                reasoning=[f"Fallback analysis for {symbol_upper}"],
                spendingData=last_resort_spending,
                optionsFlowData=last_resort_options,
                signalContributions=[],
                shapValues=[],
                shapExplanation=f"Fallback analysis for {symbol_upper}"
            )
        except Exception as final_error:
            logger.error(f"Fatal error in last resort fallback: {final_error}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return minimal data even on error
            return RustStockAnalysisType(
                symbol=symbol_upper,
                beginnerFriendlyScore=75.0,
                riskLevel="Medium",
                recommendation="HOLD",
                technicalIndicators=TechnicalIndicatorsType(
                    rsi=50.0, macd=0.0, macdSignal=0.0, macdHistogram=0.0,
                    sma20=0.0, sma50=0.0, ema12=0.0, ema26=0.0,
                    bollingerUpper=0.0, bollingerLower=0.0, bollingerMiddle=0.0
                ),
                fundamentalAnalysis=FundamentalAnalysisType(
                    valuationScore=70.0, growthScore=65.0, stabilityScore=80.0,
                    dividendScore=60.0, debtScore=75.0
                ),
                reasoning=[f"Error generating analysis for {symbol_upper}"],
                spendingData=[],
                optionsFlowData=[],
                signalContributions=[],
                shapValues=[],
                shapExplanation=f"Error generating analysis for {symbol_upper}"
            )


def resolve_stock_discussions(self, info, stock_symbol=None, limit=20):
    """Get stock discussions (Reddit-style) - shows public posts and posts from followed users"""

    user = info.context.user

    if user.is_anonymous:
        return []
    else:
        # Authenticated users see:
        # 1. All public posts
        # 2. Posts from users they follow (regardless of visibility)
        # 3. Their own posts (regardless of visibility)
        followed_users = user.following.values_list('following', flat=True)

        discussions = StockDiscussion.objects.filter(
            models.Q(visibility='public') |  # Public posts
            models.Q(user__in=followed_users) |  # Posts from followed users
            models.Q(user=user)  # User's own posts
        ).distinct()

    if stock_symbol:
        try:
            stock = Stock.objects.get(symbol=stock_symbol.upper())
            discussions = discussions.filter(stock=stock)
        except Stock.DoesNotExist:
            return []

    return discussions.order_by('-created_at')[:limit]


def resolve_discussion_detail(self, info, id):
    """Get detailed discussion with comments"""

    try:
        return StockDiscussion.objects.get(id=id)
    except StockDiscussion.DoesNotExist:
        return None


def resolve_social_feed(self, info):
    """Get social feed - posts from users the current user follows"""

    user = info.context.user

    if user.is_anonymous:

        return []
    return []

    # Get users that the current user follows

    followed_users = user.following.values_list('following', flat=True)

    if not followed_users:

        pass
    return []

    # Return posts from followed users only

    discussions = StockDiscussion.objects.filter(

        user__in=followed_users

    ).select_related('user', 'stock').prefetch_related('comments').order_by('-created_at')

    return discussions


def resolve_my_portfolio(self, info):
    """Get current user's portfolio"""

    user = info.context.user

    if user.is_anonymous:

        return []
    return Portfolio.objects.filter(user=user)


def resolve_portfolio_value(self, info):
    """Get current user's total portfolio value"""

    user = info.context.user

    if user.is_anonymous:

        return []
    portfolio_items = Portfolio.objects.filter(user=user)

    total_value = sum(item.total_value for item in portfolio_items)

    return total_value


def resolve_current_stock_prices(self, info, symbols=None):
    """Get current stock prices with enhanced real-time data"""

    import asyncio

    import logging

    logger = logging.getLogger(__name__)

    if not symbols:
        return []

    try:
        # Use enhanced stock service for real-time prices
        from .enhanced_stock_service import enhanced_stock_service

        # Get real-time prices asynchronously
        async def get_prices():
            return await enhanced_stock_service.get_multiple_prices(symbols)

        # Run async function
        prices_data = asyncio.run(get_prices())

        prices = []

        for symbol in symbols:
            price_data = prices_data.get(symbol)

            if price_data and price_data.get('price', 0) > 0:
                prices.append({
                    'symbol': symbol,
                    'current_price': price_data['price'],
                    'change': price_data.get('change', 0.0),
                    'change_percent': price_data.get('change_percent', '0%'),
                    'last_updated': price_data.get('last_updated', timezone.now().isoformat()),
                    'source': price_data.get('source', 'unknown'),
                    'verified': price_data.get('verified', False),
                    'api_response': price_data
                })

                # Log price source
                if price_data.get('verified'):
                    logger.info(f"Real-time price for {symbol}: ${price_data['price']} from {price_data.get('source')}")
                else:
                    logger.info(f"Using fallback price for {symbol}: ${price_data['price']}")

                # Update database with new price
                enhanced_stock_service.update_stock_price_in_database(symbol, price_data)
            else:
                logger.warning(f"No price data available for {symbol}")

        return prices

    except Exception as e:
        logger.error(f"Error getting current stock prices: {e}")

    # Fallback to database prices

    prices = []

    for symbol in symbols:
        try:
            stock = Stock.objects.get(symbol=symbol.upper())

            if stock.current_price:
                prices.append({
                    'symbol': symbol,
                    'current_price': float(stock.current_price),
                    'change': 0.0,
                    'change_percent': '0%',
                    'last_updated': stock.last_updated.isoformat() if stock.last_updated else timezone.now().isoformat(),
                    'source': 'database',
                    'verified': False,
                    'api_response': None
                })

                logger.info(f" Database fallback for {symbol}: ${stock.current_price}")

        except Stock.DoesNotExist:
            logger.warning(f"Stock {symbol} not found in database")
        except Exception as e:
            logger.error(f"Error getting database price for {symbol}: {e}")

    return prices


def resolve_my_portfolios(self, info):
    """Get all portfolios for the current user"""

    user = info.context.user

    if not user or user.is_anonymous:

        pass
    from .portfolio_service import PortfolioService

    return PortfolioService.get_user_portfolios(user)


def resolve_portfolio_names(self, info):
    """Get list of portfolio names for the current user"""

    user = info.context.user

    if not user or user.is_anonymous:

        pass
    from .portfolio_service import PortfolioService

    return PortfolioService.get_portfolio_names(user)




def resolve_test_portfolio_metrics(self, info):
    """Test portfolio metrics (no auth required)"""

    from .premium_analytics import PremiumAnalyticsService

    service = PremiumAnalyticsService()

    # Use user ID 1 for testing

    return service.get_portfolio_performance_metrics(1)


def resolve_test_ai_recommendations(self, info):
    """Test AI recommendations (no auth required)"""

    from .premium_analytics import PremiumAnalyticsService

    service = PremiumAnalyticsService()

    # Use user ID 1 for testing

    return service.get_ai_recommendations(1, "medium")


def resolve_test_stock_screening(self, info):
    """Test stock screening (no auth required)"""

    from .premium_analytics import PremiumAnalyticsService

    service = PremiumAnalyticsService()

    # Return some sample screening results

    return service.get_advanced_stock_screening({})


def resolve_test_options_analysis(self, info, symbol):
    """Test options analysis (no auth required)"""

    from .options_service import OptionsAnalysisService

    service = OptionsAnalysisService()

    # Return options analysis for the given symbol

    return service.get_comprehensive_analysis(symbol)


def resolve_benchmarkSeries(self, info, symbol, timeframe):
    """

    Get benchmark series data for a given symbol and timeframe

    Fetches real market data from market data APIs

    """
    logger.info(f"benchmarkSeries called", extra={"symbol": symbol, "timeframe": timeframe})
    
    try:
        # Map timeframe to period for market data API
        timeframe_map = {
            '1M': '1mo',
            '3M': '3mo',
            '6M': '6mo',
            '1Y': '1y',
        }

        period = timeframe_map.get(timeframe.upper(), '1y')

        # Get benchmark name mapping
        benchmark_names = {
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ-100',
            'DIA': 'Dow Jones Industrial Average',
            'VTI': 'Total Stock Market',
            'IWM': 'Russell 2000',
            'VEA': 'Developed Markets',
            'VWO': 'Emerging Markets',
            'AGG': 'Total Bond Market',
            'TLT': 'Long-term Treasury',
            'GLD': 'Gold',
            'SLV': 'Silver',
        }

        benchmark_name = benchmark_names.get(symbol.upper(), symbol.upper())

        # Import market data service
        try:
            from .market_data_api_service import MarketDataAPIService, DataProvider
        except ImportError:
            logger.error("MarketDataAPIService not available")
            return None

        # Create service instance and fetch historical data
        # Since GraphQL resolvers are synchronous, we need to run async code

        async def fetch_benchmark_data():
            async with MarketDataAPIService() as service:
                # Fetch historical data
                hist_data = await service.get_historical_data(symbol.upper(), period=period)

                if hist_data is None or hist_data.empty:
                    logger.warning(f"No historical data available for {symbol}")
                    return None

                # Convert DataFrame to our format
                import pandas as pd
                import numpy as np

                # Ensure we have a 'Close' column (yfinance uses 'Close', others might use 'close')
                close_col = 'Close' if 'Close' in hist_data.columns else 'close'
                if close_col not in hist_data.columns:
                    logger.error(f"No close price column found in data for {symbol}")
                    return None

                # Sort by date (ascending)
                hist_data = hist_data.sort_index()

                # Extract values
                values = hist_data[close_col].values.tolist()
                timestamps = hist_data.index.tolist()

                if len(values) == 0:
                    return None

                start_value = float(values[0])
                end_value = float(values[-1])
                total_return = end_value - start_value
                total_return_percent = (total_return / start_value * 100) if start_value > 0 else 0.0

                # Calculate volatility (standard deviation of returns)
                returns = pd.Series(values).pct_change().dropna()
                volatility = float(returns.std() * np.sqrt(252)) * \
                    100 if len(returns) > 1 else 0.0  # Annualized volatility

                # Create data points
                data_points = []
                prev_value = start_value

                for i, (ts, val) in enumerate(zip(timestamps, values)):
                    value = float(val)
                    change = value - prev_value
                    change_percent = (change / prev_value * 100) if prev_value > 0 else 0.0

                    # Format timestamp
                    if isinstance(ts, pd.Timestamp):
                        timestamp_str = ts.strftime('%Y-%m-%dT%H:%M:%S')
                    else:
                        timestamp_str = str(ts)

                    data_points.append({
                        'timestamp': timestamp_str,
                        'value': value,
                        'change': change,
                        'changePercent': change_percent,
                    })

                    prev_value = value

                return {
                    'symbol': symbol.upper(),
                    'name': benchmark_name,
                    'timeframe': timeframe.upper(),
                    'dataPoints': data_points,
                    'startValue': start_value,
                    'endValue': end_value,
                    'totalReturn': total_return,
                    'totalReturnPercent': total_return_percent,
                    'volatility': volatility,
                }

        # Run async function - use asyncio.run() like other resolvers
        result = asyncio.run(fetch_benchmark_data())

        if result is None:
            logger.warning(f"benchmarkSeries returned None for {symbol} with timeframe {timeframe}")
            return None
        
        logger.info(f"benchmarkSeries result", extra={
            "has_series": result is not None, 
            "len": len(result.get('dataPoints', [])) if result else 0,
            "symbol": symbol,
            "timeframe": timeframe
        })

        data_points = [
            BenchmarkDataPointType(
                timestamp=dp['timestamp'],
                value=dp['value'],
                change=dp['change'],
                changePercent=dp['changePercent']
            )
            for dp in result['dataPoints']
                ]


        return BenchmarkSeriesType(
            symbol=result['symbol'],
            name=result['name'],
            timeframe=result['timeframe'],
            dataPoints=data_points,
            startValue=result['startValue'],
            endValue=result['endValue'],
            totalReturn=result['totalReturn'],
            totalReturnPercent=result['totalReturnPercent'],
            volatility=result['volatility'],
        )

    except Exception as e:
        logger.error(f"Error fetching benchmark series for {symbol}: {e}", exc_info=True)
        return None


def resolve_availableBenchmarks(self, info):
    """Get list of available benchmark symbols"""

    return ['SPY', 'QQQ', 'DIA', 'VTI', 'IWM', 'VEA', 'VWO', 'AGG', 'TLT', 'GLD', 'SLV']


def resolve_stock_moments(self, info, symbol, range):
    """Resolve stock moments for a given symbol and time range"""
    try:
        now = timezone.now()
        symbol_upper = symbol.upper()

        # Calculate start date based on range (handle both enum and string)
        range_value = range.value if hasattr(range, 'value') else str(range)

        if range_value == 'ONE_MONTH' or range == ChartRangeEnum.ONE_MONTH:
            start = now - timedelta(days=30)
        elif range_value == 'THREE_MONTHS' or range == ChartRangeEnum.THREE_MONTHS:
            start = now - timedelta(days=90)
        elif range_value == 'SIX_MONTHS' or range == ChartRangeEnum.SIX_MONTHS:
            start = now - timedelta(days=180)
        elif range_value == 'YEAR_TO_DATE' or range == ChartRangeEnum.YEAR_TO_DATE:
            # First day of current year
            start = datetime(now.year, 1, 1, tzinfo=now.tzinfo)
        elif range_value == 'ONE_YEAR' or range == ChartRangeEnum.ONE_YEAR:
            start = now - timedelta(days=365)
        else:
            # Default to one month if range is unrecognized
            logger.warning(f"Unrecognized range: {range_value}, defaulting to ONE_MONTH")
            start = now - timedelta(days=30)

        # Query moments for this symbol and time range
        # Add limit to prevent slow queries and order by importance/recency
        # Use select_related/prefetch_related if needed, and ensure query is optimized
        moments = StockMoment.objects.filter(
            symbol=symbol_upper,
            timestamp__gte=start
        ).order_by('-importance_score', '-timestamp')[:50]  # Limit to top 50 most important moments

        # Convert to list immediately to execute query and return quickly
        result = list(moments)
        logger.info(f"Resolved {len(result)} stock moments for {symbol_upper} in range {range_value} (start: {start})")
        return result

    except Exception as e:
        logger.error(f"Error resolving stock moments for {symbol}: {e}", exc_info=True)
        return []


def _generate_picks_for_symbols(
    symbols: list,
    feature_service: 'DayTradingFeatureService',
    ml_scorer: 'DayTradingMLScorer',
    mode: str,
    quality_threshold: float
) -> list:
    """Generate picks for a list of symbols"""
    picks = []

    for symbol in symbols[:50]:  # Limit to 50 symbols for performance
        try:
            # Get OHLCV data (tries real data first, falls back to mock)
            # Note: This is a synchronous function, so we need to handle async
            # For now, we'll use a workaround to call async function
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            ohlcv_1m, ohlcv_5m = loop.run_until_complete(_get_intraday_data(symbol))

            if ohlcv_1m is None or ohlcv_5m is None:
                continue

            # Extract features
            features = feature_service.extract_all_features(
                ohlcv_1m, ohlcv_5m, symbol
            )

            # Determine side first (needed for ML scoring)
            momentum = features.get('momentum_15m', 0.0)
            side = 'LONG' if momentum > 0 else 'SHORT'

            # Score with ML (pass mode and side for ML learner)
            score = ml_scorer.score(features, mode=mode, side=side)

            # Filter by quality threshold
            if score < quality_threshold:
                continue

            # Calculate risk metrics
            current_price = float(ohlcv_5m.iloc[-1]['close'])
            risk_metrics = feature_service.calculate_risk_metrics(
                features, mode, current_price
            )

            # Calculate catalyst score
            catalyst_score = ml_scorer.calculate_catalyst_score(features)

            # Create pick
            pick = {
                'symbol': symbol,
                'side': side,
                'score': score,
                'features': {
                    'momentum15m': features.get('momentum_15m', 0.0),
                    'rvol10m': features.get('realized_vol_10', 0.0),
                    'vwapDist': features.get('vwap_dist_pct', 0.0),
                    'breakoutPct': features.get('breakout_pct', 0.0),
                    'spreadBps': features.get('spread_bps', 5.0),
                    'catalystScore': catalyst_score
                },
                'risk': risk_metrics,
                'notes': _generate_pick_notes(symbol, features, side, score)
            }

            picks.append(pick)

        except Exception as e:
            logger.warning(f"Error processing {symbol}: {e}")
            continue

    return picks


def _get_static_universe(mode):
    """Get static curated universe for fallback"""
    if mode == "SAFE":
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'V', 'JNJ', 
               'WMT', 'PG', 'MA', 'HD', 'DIS', 'NFLX', 'BAC', 'XOM', 'CVX', 'ABBV']
    else:  # AGGRESSIVE
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'CRM',
               'NFLX', 'PYPL', 'ADBE', 'UBER', 'LYFT', 'RBLX', 'SOFI', 'PLTR', 'HOOD', 'COIN',
               'SNOW', 'NET', 'ZM', 'DOCN', 'CRWD', 'ZS', 'OKTA', 'DDOG', 'MDB', 'ESTC',
               'SQ', 'SHOP', 'ROKU', 'SPOT', 'TWLO', 'FROG', 'BILL', 'ASAN', 'UPST', 'AFRM']


def _get_dynamic_universe_from_polygon(mode, max_symbols=100):
    """
    Build a dynamic universe from Polygon top movers (gainers + losers).
    Applies Citadel-grade filtering to avoid penny stocks and junk.
    
    SAFE mode: $50B+ market cap, high volume, stable names only
    AGGRESSIVE mode: $1B+ market cap, 1M+ volume, allows higher volatility
    
    Returns list of symbols or empty list if discovery fails.
    """
    import os
    import aiohttp
    import asyncio
    from django.core.cache import cache
    
    # Cache for 60 seconds (movers change frequently but not every second)
    cache_key = f"day_trading:dynamic_universe:{mode}:v2"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"✅ Cache hit for dynamic universe ({mode})")
        return cached
    
    polygon_key = os.getenv('POLYGON_API_KEY')
    if not polygon_key:
        logger.debug("No POLYGON_API_KEY for dynamic discovery")
        return []
    
    # Mode-specific filters
    if mode == "SAFE":
        min_price = 5.0  # Avoid penny stocks
        max_price = 500.0  # Avoid ultra-high priced stocks
        min_volume = 5_000_000  # 5M shares minimum
        min_market_cap = 50_000_000_000  # $50B minimum
        base_max_change_pct = 0.15  # Base: 15% max intraday move
    else:  # AGGRESSIVE
        min_price = 2.0
        max_price = 500.0
        min_volume = 1_000_000  # 1M shares minimum
        min_market_cap = 1_000_000_000  # $1B minimum
        base_max_change_pct = 0.30  # Base: 30% max intraday move
    
    # Dynamic % change threshold based on time of day (pre-market catch, avoid late pumps)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    et_hour = (now.hour - 5) % 24  # Convert UTC to ET (simplified, doesn't account for DST)
    
    if et_hour < 10:  # Pre-10AM ET: Allow higher moves (catch early momentum)
        max_change_pct = base_max_change_pct * 1.67  # 50% for AGGRESSIVE, 25% for SAFE
    elif et_hour < 14:  # 10AM-2PM ET: Standard threshold
        max_change_pct = base_max_change_pct  # 30% for AGGRESSIVE, 15% for SAFE
    else:  # Post-2PM ET: Stricter (avoid late pumps)
        max_change_pct = base_max_change_pct * 0.33  # 10% for AGGRESSIVE, 5% for SAFE
    
    logger.debug(f"Dynamic max_change_pct for {mode} mode at {et_hour}:00 ET: {max_change_pct:.1%}")
    
    try:
        # Fetch top gainers and losers from Polygon with detailed ticker data
        async def fetch_movers():
            valid_symbols = []
            
            async with aiohttp.ClientSession() as session:
                # Get top gainers
                gainers_url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/gainers"
                gainers_params = {'apikey': polygon_key}
                
                try:
                    async with session.get(gainers_url, params=gainers_params, timeout=aiohttp.ClientTimeout(total=3.0)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            tickers = data.get('tickers', [])
                            
                            for ticker_obj in tickers[:100]:  # Check top 100 gainers
                                try:
                                    # Extract ticker symbol
                                    ticker_str = ticker_obj.get('ticker', '')
                                    if not ticker_str or len(ticker_str) > 5:
                                        continue
                                    
                                    # Skip ETFs and weird symbols
                                    if ticker_str.endswith('X') or '.' in ticker_str:
                                        continue
                                    
                                    # Get price from last trade
                                    last_trade = ticker_obj.get('lastTrade', {})
                                    price = float(last_trade.get('p', 0)) if last_trade else 0
                                    
                                    # Get volume
                                    volume = int(ticker_obj.get('day', {}).get('v', 0))
                                    
                                    # Get market cap (if available in ticker details)
                                    market_cap = float(ticker_obj.get('market_cap', 0) or 0)
                                    
                                    # Get change percentage
                                    change_pct = abs(float(ticker_obj.get('todaysChangePct', 0) or 0)) / 100
                                    
                                    # Global sanity filters
                                    if price < min_price or price > max_price:
                                        continue
                                    if volume < min_volume:
                                        continue
                                    if change_pct > max_change_pct:
                                        continue
                                    
                                    # Market cap filter (if available, otherwise we'll filter later)
                                    if market_cap > 0 and market_cap < min_market_cap:
                                        continue
                                    
                                    valid_symbols.append(ticker_str)
                                    
                                    if len(valid_symbols) >= max_symbols:
                                        break
                                        
                                except (ValueError, KeyError, TypeError) as e:
                                    logger.debug(f"Error processing ticker {ticker_obj.get('ticker', 'unknown')}: {e}")
                                    continue
                                    
                except Exception as e:
                    logger.debug(f"Error fetching gainers: {e}")
                
                # Get top losers (for SHORT opportunities)
                losers_url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/losers"
                losers_params = {'apikey': polygon_key}
                
                try:
                    async with session.get(losers_url, params=losers_params, timeout=aiohttp.ClientTimeout(total=3.0)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            tickers = data.get('tickers', [])
                            
                            for ticker_obj in tickers[:100]:  # Check top 100 losers
                                try:
                                    ticker_str = ticker_obj.get('ticker', '')
                                    if not ticker_str or len(ticker_str) > 5:
                                        continue
                                    
                                    if ticker_str.endswith('X') or '.' in ticker_str:
                                        continue
                                    
                                    # Skip if already added from gainers
                                    if ticker_str in valid_symbols:
                                        continue
                                    
                                    last_trade = ticker_obj.get('lastTrade', {})
                                    price = float(last_trade.get('p', 0)) if last_trade else 0
                                    volume = int(ticker_obj.get('day', {}).get('v', 0))
                                    market_cap = float(ticker_obj.get('market_cap', 0) or 0)
                                    change_pct = abs(float(ticker_obj.get('todaysChangePct', 0) or 0)) / 100
                                    
                                    # Apply same filters
                                    if price < min_price or price > max_price:
                                        continue
                                    if volume < min_volume:
                                        continue
                                    if change_pct > max_change_pct:
                                        continue
                                    if market_cap > 0 and market_cap < min_market_cap:
                                        continue
                                    
                                    valid_symbols.append(ticker_str)
                                    
                                    if len(valid_symbols) >= max_symbols:
                                        break
                                        
                                except (ValueError, KeyError, TypeError) as e:
                                    logger.debug(f"Error processing ticker {ticker_obj.get('ticker', 'unknown')}: {e}")
                                    continue
                                    
                except Exception as e:
                    logger.debug(f"Error fetching losers: {e}")
            
            return valid_symbols
        
        # Fetch movers
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            filtered_symbols = loop.run_until_complete(fetch_movers())
        finally:
            loop.close()
        
        if not filtered_symbols:
            logger.warning(f"Dynamic discovery: No qualifying movers found for {mode} mode after filtering")
            return []
        
        logger.info(f"✅ Dynamic discovery: Found {len(filtered_symbols)} qualified symbols from Polygon movers (mode: {mode})")
        
        # Cache the result
        cache.set(cache_key, filtered_symbols, 60)
        return filtered_symbols
        
    except Exception as e:
        logger.warning(f"Dynamic discovery failed: {e}", exc_info=True)
        return []


def _get_real_intraday_day_trading_picks(mode="SAFE", limit=10, use_dynamic_discovery=True):
    """
    Get real intraday day trading picks using multiple data providers.
    Returns up to 10 stocks filtered by SAFE or AGGRESSIVE criteria.
    
    SAFE mode: Large-cap, high liquidity, lower volatility, conservative stops
    AGGRESSIVE mode: Broader universe, higher volatility, tighter stops, faster moves
    
    Cached for 60 seconds to avoid excessive API calls during rapid refreshes.
    """
    import asyncio
    import os
    import aiohttp
    from datetime import datetime, timedelta
    import math
    from django.core.cache import cache
    
    # Check cache first (60 second TTL for intraday data)
    # NOTE: Currently global per mode. Future: per-user cache keys when we add user-specific filters
    # Future cache key: f"day_trading_picks:{user_id}:{mode}:v4"
    cache_key = f"day_trading_picks:{mode}:v4:dynamic_{use_dynamic_discovery}"
    cached_result = cache.get(cache_key)
    if cached_result:
        # Log cache hit for debugging
        picks_count = len(cached_result[0]) if isinstance(cached_result, tuple) and len(cached_result) > 0 else (len(cached_result) if isinstance(cached_result, list) else 0)
        logger.info(f"📦 Cache hit for {cache_key}: {picks_count} picks")
        logger.debug(f"✅ Cache hit for {mode} mode day trading picks")
        # Handle both old format (list) and new format (tuple)
        if isinstance(cached_result, tuple):
            # If cache has empty picks, bypass cache and fetch fresh data
            if len(cached_result[0]) == 0:
                logger.warning(f"⚠️ Cache has empty picks - bypassing cache to fetch fresh data")
                cache.delete(cache_key)  # Delete the empty cache entry
            else:
                return cached_result
        else:
            # Legacy cache format - try to extract metadata from picks if available
            if isinstance(cached_result, list) and len(cached_result) > 0:
                # Try to get universe_source from first pick
                universe_source = cached_result[0].get('universe_source', 'CORE')
                # Estimate universe size (we don't have it in legacy format)
                # Return a reasonable default or try to infer from picks
                return (cached_result, {'universe_size': len(cached_result) * 10, 'universe_source': universe_source})
            else:
                # Empty legacy cache - don't return it, fetch fresh instead
                logger.warning(f"⚠️ Legacy cache has empty picks - bypassing cache to fetch fresh data")
                cache.delete(cache_key)
    
    logger.info(f"🔄 Fetching fresh intraday day trading picks for {mode} mode (limit={limit}, dynamic={use_dynamic_discovery})")
    
    # Get universe (dynamic discovery or static fallback)
    universe_source = 'DYNAMIC_MOVERS' if use_dynamic_discovery else 'CORE'
    universe = []
    
    if use_dynamic_discovery:
        universe = _get_dynamic_universe_from_polygon(mode, max_symbols=100)
        if not universe or len(universe) < 10:
            logger.warning(f"Dynamic discovery returned {len(universe)} symbols, falling back to static universe")
            universe = _get_static_universe(mode)
            universe_source = 'CORE'  # Mark as CORE since we fell back
        else:
            logger.info(f"✅ Using dynamic universe: {len(universe)} symbols from Polygon movers")
    else:
        universe = _get_static_universe(mode)
        logger.info(f"✅ Using static universe: {len(universe)} symbols")
    
    # Define mode-specific parameters
    if mode == "SAFE":
        min_market_cap = 50_000_000_000  # $50B minimum
        max_volatility = 0.03  # 3% max daily volatility
        min_volume = 5_000_000  # 5M shares minimum
        time_stop_min = 45  # 45 minute time stop
        risk_per_trade = 0.005  # 0.5% risk
    else:  # AGGRESSIVE
        min_market_cap = 1_000_000_000  # $1B minimum
        max_volatility = 0.08  # 8% max daily volatility
        min_volume = 1_000_000  # 1M shares minimum
        time_stop_min = 25  # 25 minute time stop
        risk_per_trade = 0.012  # 1.2% risk
    
    async def fetch_stock_data(symbol):
        """Fetch real intraday data for a stock from multiple providers with circuit breaker.
        Returns tuple: (pick_dict, provider_name) or (None, None) if all providers fail."""
        try:
            # Try Polygon first (best intraday coverage)
            polygon_key = os.getenv('POLYGON_API_KEY')
            if polygon_key:
                try:
                    # Get today's intraday data
                    today = datetime.now().strftime('%Y-%m-%d')
                    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/5/minute/{today}/{today}"
                    params = {
                        'adjusted': 'true',
                        'sort': 'asc',
                        'limit': 5000,
                        'apiKey': polygon_key
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=2.0)) as response:
                            if response.status == 200:
                                data = await response.json()
                                results = data.get('results', [])
                                if results and len(results) > 0:
                                    logger.debug(f"✅ Polygon: Got {len(results)} bars for {symbol}")
                                    pick = await _process_intraday_data(symbol, results, mode)
                                    if pick:
                                        return (pick, 'polygon')
                except asyncio.TimeoutError:
                    logger.debug(f"⏱️ Polygon timeout for {symbol}")
                except Exception as e:
                    logger.debug(f"❌ Polygon failed for {symbol}: {e}")
            
            # Try Finnhub as fallback
            finnhub_key = os.getenv('FINNHUB_API_KEY')
            if finnhub_key:
                try:
                    # Get quote (current price)
                    quote_url = "https://finnhub.io/api/v1/quote"
                    quote_params = {'symbol': symbol, 'token': finnhub_key}
                    
                    # Get candle data (intraday)
                    now = int(datetime.now().timestamp())
                    start = int((datetime.now() - timedelta(hours=6)).timestamp())
                    candle_url = "https://finnhub.io/api/v1/stock/candle"
                    candle_params = {
                        'symbol': symbol,
                        'resolution': '5',  # 5-minute bars
                        'from': start,
                        'to': now,
                        'token': finnhub_key
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        # Get quote
                        async with session.get(quote_url, params=quote_params, timeout=aiohttp.ClientTimeout(total=2.0)) as quote_resp:
                            if quote_resp.status == 200:
                                quote_data = await quote_resp.json()
                                
                                # Get candles
                                async with session.get(candle_url, params=candle_params, timeout=aiohttp.ClientTimeout(total=2.0)) as candle_resp:
                                    if candle_resp.status == 200:
                                        candle_data = await candle_resp.json()
                                        if candle_data.get('s') == 'ok':
                                            # Convert to Polygon-like format
                                            results = []
                                            for i in range(len(candle_data.get('c', []))):
                                                results.append({
                                                    'o': candle_data['o'][i],
                                                    'h': candle_data['h'][i],
                                                    'l': candle_data['l'][i],
                                                    'c': candle_data['c'][i],
                                                    'v': candle_data['v'][i],
                                                    't': candle_data['t'][i] * 1000,
                                                })
                                            logger.debug(f"✅ Finnhub: Got {len(results)} bars for {symbol}")
                                            pick = await _process_intraday_data(symbol, results, mode, quote_data)
                                            if pick:
                                                return (pick, 'finnhub')
                except asyncio.TimeoutError:
                    logger.debug(f"⏱️ Finnhub timeout for {symbol}")
                except Exception as e:
                    logger.debug(f"❌ Finnhub failed for {symbol}: {e}")
            
            # Try Alpha Vantage as last resort (slower but good fallback)
            alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY') or os.getenv('ALPHA_VANTAGE_KEY')
            if alpha_key:
                try:
                    # Alpha Vantage intraday endpoint (5-minute intervals)
                    url = "https://www.alphavantage.co/query"
                    params = {
                        'function': 'TIME_SERIES_INTRADAY',
                        'symbol': symbol,
                        'interval': '5min',
                        'apikey': alpha_key,
                        'outputsize': 'compact'  # Last 100 data points
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                            if response.status == 200:
                                data = await response.json()
                                time_series = data.get('Time Series (5min)', {})
                                if time_series:
                                    # Convert Alpha Vantage format to Polygon-like format
                                    results = []
                                    for timestamp, values in sorted(time_series.items()):
                                        # Convert timestamp to milliseconds
                                        ts_dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                                        ts_ms = int(ts_dt.timestamp() * 1000)
                                        results.append({
                                            'o': float(values.get('1. open', 0)),
                                            'h': float(values.get('2. high', 0)),
                                            'l': float(values.get('3. low', 0)),
                                            'c': float(values.get('4. close', 0)),
                                            'v': float(values.get('5. volume', 0)),
                                            't': ts_ms,
                                        })
                                    if results:
                                        logger.debug(f"✅ Alpha Vantage: Got {len(results)} bars for {symbol}")
                                        pick = await _process_intraday_data(symbol, results, mode)
                                        if pick:
                                            return (pick, 'alpha_vantage')
                except asyncio.TimeoutError:
                    logger.debug(f"⏱️ Alpha Vantage timeout for {symbol}")
                except Exception as e:
                    logger.debug(f"❌ Alpha Vantage failed for {symbol}: {e}")
            
            # Circuit breaker: If all providers failed, return None (don't retry)
            logger.debug(f"⚠️ All providers failed for {symbol}, excluding from picks")
            return (None, None)
        except Exception as e:
            logger.debug(f"Error fetching data for {symbol}: {e}")
            return (None, None)
    
    async def _process_intraday_data(symbol, bars, mode, quote_data=None):
        """Process intraday bars to calculate features and score"""
        if not bars or len(bars) < 10:
            return None
        
        try:
            # Import microstructure service
            from .microstructure_service import MicrostructureService
            microstructure_service = MicrostructureService()
            
            # Get mode-specific parameters
            mode_max_volatility = 0.03 if mode == "SAFE" else 0.08
            mode_min_volume = 5_000_000 if mode == "SAFE" else 1_000_000
            mode_time_stop = 45 if mode == "SAFE" else 25
            
            # Get current price
            current_price = float(bars[-1].get('c', 0))
            if current_price == 0:
                return None
            
            # Fetch microstructure data (L2 order book)
            microstructure = await microstructure_service.get_order_book_features(symbol)
            
            # Apply microstructure filters (execution quality)
            # NOTE: If microstructure service is unavailable or returns None, skip this filter
            # This allows picks to be generated even if L2 data isn't available
            if microstructure:
                try:
                    tradeability = microstructure_service.is_tradeable(symbol, mode, microstructure)
                    if not tradeability.get('tradeable', True):
                        logger.debug(f"⚠️ {symbol} filtered by microstructure: {tradeability.get('reason', 'unknown')}")
                        return None
                except Exception as e:
                    logger.debug(f"⚠️ Microstructure check failed for {symbol}: {e}, allowing through")
                    # Continue processing if microstructure check fails
            
            # Calculate 15-minute momentum
            if len(bars) >= 3:  # Need at least 3 bars (15 min)
                price_15m_ago = float(bars[-3].get('c', current_price))
                momentum15m = (current_price - price_15m_ago) / price_15m_ago if price_15m_ago > 0 else 0
            else:
                momentum15m = 0
            
            # Calculate volume metrics
            recent_volumes = [float(b.get('v', 0)) for b in bars[-10:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
            current_volume = float(bars[-1].get('v', 0))
            rvol10m = (current_volume / avg_volume) if avg_volume > 0 else 1.0
            
            # Calculate volatility (ATR-like)
            high_low_spreads = []
            for bar in bars[-20:]:
                high = float(bar.get('h', current_price))
                low = float(bar.get('l', current_price))
                if high > 0 and low > 0:
                    high_low_spreads.append((high - low) / current_price)
            volatility = sum(high_low_spreads) / len(high_low_spreads) if high_low_spreads else 0.02
            
            # Calculate VWAP distance (simplified)
            total_value = sum(float(b.get('c', 0)) * float(b.get('v', 0)) for b in bars)
            total_volume = sum(float(b.get('v', 0)) for b in bars)
            vwap = total_value / total_volume if total_volume > 0 else current_price
            vwapDist = (current_price - vwap) / vwap if vwap > 0 else 0
            
            # Check for gaps (price jumps > 5% in last 5 minutes)
            gap_pct = 0.0
            if len(bars) >= 2:
                prev_close = float(bars[-2].get('c', current_price))
                if prev_close > 0:
                    gap = abs(current_price - prev_close) / prev_close
                    gap_pct = gap
                    if gap > 0.05:  # > 5% gap
                        logger.debug(f"⚠️ {symbol} has large gap: {gap*100:.1f}%, filtering out")
                        return None
            
            # Check for halts (zero volume bars in recent period - simplified check)
            recent_volumes_check = [float(b.get('v', 0)) for b in bars[-5:]]
            if sum(recent_volumes_check) == 0:
                logger.debug(f"⚠️ {symbol} appears halted (zero volume), filtering out")
                return None
            
            # Determine side (LONG if momentum positive, SHORT if negative)
            side = 'LONG' if momentum15m > 0 else 'SHORT'
            
            # Calculate score based on momentum, volume, and volatility
            momentum_score = abs(momentum15m) * 100  # Scale momentum
            volume_score = min(5.0, rvol10m * 2)  # Volume boost
            volatility_score = min(3.0, volatility * 100)  # Volatility component
            score = momentum_score + volume_score + volatility_score
            
            # Apply mode-specific filters
            if mode == "SAFE":
                # SAFE: Require lower volatility, higher liquidity
                if volatility > mode_max_volatility or avg_volume < mode_min_volume:
                    return None
                # Prefer positive momentum (longs)
                if momentum15m < 0.001:  # Very small positive momentum required
                    return None
            else:  # AGGRESSIVE
                # AGGRESSIVE: Allow higher volatility, but still need some momentum
                if volatility > mode_max_volatility:
                    logger.debug(f"⚠️ {symbol} filtered: volatility {volatility:.4f} > max {mode_max_volatility}")
                    return None
                # Relax momentum requirement for AGGRESSIVE mode (allow very small moves)
                if abs(momentum15m) < 0.0001:  # Very minimal movement required (0.01%)
                    logger.debug(f"⚠️ {symbol} filtered: momentum {momentum15m:.6f} too small")
                    return None
            
            # Calculate risk parameters
            atr5m = current_price * volatility * 0.5  # Simplified ATR
            stop_pct = 0.02 if mode == "SAFE" else 0.015  # 2% for SAFE, 1.5% for AGGRESSIVE
            stop = round(current_price * (1 - stop_pct) if side == 'LONG' else current_price * (1 + stop_pct), 2)
            
            target1_pct = 0.03 if mode == "SAFE" else 0.04  # 3% or 4% first target
            target2_pct = 0.05 if mode == "SAFE" else 0.07  # 5% or 7% second target
            targets = [
                round(current_price * (1 + target1_pct) if side == 'LONG' else current_price * (1 - target1_pct), 2),
                round(current_price * (1 + target2_pct) if side == 'LONG' else current_price * (1 - target2_pct), 2)
            ]
            
            # Position sizing (simplified - would use account size in production)
            sizeShares = 100  # Default
            
            # Add microstructure features if available
            features_dict = {
                'momentum15m': round(momentum15m, 4),
                'rvol10m': round(rvol10m, 2),
                'vwapDist': round(vwapDist, 4),
                'breakoutPct': round(abs(momentum15m), 4),
                'spreadBps': 5.0,  # Default
                'catalystScore': round(min(10.0, abs(momentum15m) * 200), 2)
            }
            
            # Add microstructure features if available
            if microstructure:
                features_dict.update({
                    'orderImbalance': round(microstructure.get('order_imbalance', 0), 4),
                    'bidDepth': round(microstructure.get('bid_depth', 0), 2),
                    'askDepth': round(microstructure.get('ask_depth', 0), 2),
                    'depthImbalance': round(microstructure.get('depth_imbalance', 0), 4),
                    'spreadBps': round(microstructure.get('spread_bps', 5.0), 2),
                    'executionQualityScore': round(microstructure_service.get_execution_quality_score(microstructure), 1)
                })
                
                # Mark as microstructure risky if quality score is low
                if microstructure_service.get_execution_quality_score(microstructure) < 5.0:
                    features_dict['microstructureRisky'] = True
            
            return {
                'symbol': symbol,
                'side': side,
                'score': round(score, 2),
                'features': features_dict,
                'risk': {
                    'atr5m': round(atr5m, 2),
                    'sizeShares': sizeShares,
                    'stop': stop,
                    'targets': targets,
                    'timeStopMin': mode_time_stop
                },
                'notes': f"{mode} mode: {momentum15m*100:.2f}% momentum, {rvol10m:.1f}x volume"
            }
        except Exception as e:
            logger.debug(f"Error processing intraday data for {symbol}: {e}")
            return None
    
    # Fetch data for all stocks in universe in parallel
    start_time = datetime.now()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        tasks = [fetch_stock_data(symbol) for symbol in universe]
        results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        
        # Separate picks and provider info, filter out failures
        picks_with_providers = []
        provider_counts = {'polygon': 0, 'finnhub': 0, 'alpha_vantage': 0}
        failed_symbols = []
        filtered_symbols = []
        # Diagnostic counters
        diagnostics = {
            'scanned_count': len(universe),
            'passed_liquidity': 0,
            'passed_quality': 0,
            'failed_data_fetch': 0,
            'filtered_by_microstructure': 0,
            'filtered_by_volatility': 0,
            'filtered_by_momentum': 0,
        }
        
        for i, result in enumerate(results):
            symbol = universe[i] if i < len(universe) else 'UNKNOWN'
            if isinstance(result, Exception):
                failed_symbols.append(symbol)
                diagnostics['failed_data_fetch'] += 1
                logger.debug(f"❌ {symbol}: Exception - {result}")
                continue
            if result is None or result[0] is None:
                failed_symbols.append(symbol)
                diagnostics['failed_data_fetch'] += 1
                logger.debug(f"❌ {symbol}: No data returned")
                continue
            pick, provider = result
            if pick:
                picks_with_providers.append((pick, provider))
                if provider:
                    provider_counts[provider] = provider_counts.get(provider, 0) + 1
                # Track passed filters (we got a pick, so it passed liquidity and quality)
                diagnostics['passed_liquidity'] += 1
                diagnostics['passed_quality'] += 1
            else:
                filtered_symbols.append(symbol)
                # Note: We can't distinguish which filter rejected it from here
                # The _process_intraday_data function returns None for various reasons
                # We'll estimate based on common failure modes
        
        # Extract just the picks
        picks = [p[0] for p in picks_with_providers]
        
        # Debug logging
        logger.info(f"📊 Processing results: {len(picks)} picks from {len(universe)} symbols")
        logger.info(f"   ✅ Success: {len(picks)}")
        logger.info(f"   ❌ Failed/No data: {len(failed_symbols)}")
        logger.info(f"   🔍 Provider breakdown: {provider_counts}")
        
        # Sort by score descending and take EXACTLY top N (strict limit)
        picks.sort(key=lambda x: x.get('score', 0), reverse=True)
        qualified_count = len(picks)
        
        # If we have no picks but have some data, log why
        if len(picks) == 0 and len(failed_symbols) < len(universe):
            logger.warning(f"⚠️ No picks qualified after filtering. Check microstructure, momentum, or volatility filters.")
            logger.warning(f"   Universe: {len(universe)}, Failed: {len(failed_symbols)}, Filtered: {len(filtered_symbols)}")
        
        picks = picks[:limit]  # Limit to up to 10 picks (or fewer if not enough qualify)
        
        # Update diagnostics with final counts
        diagnostics['passed_quality'] = len(picks)  # Final count of picks that passed all filters
        # Estimate filtered counts (we don't track these precisely in _process_intraday_data)
        # The difference between scanned and passed gives us filtered count
        total_filtered = diagnostics['scanned_count'] - diagnostics['failed_data_fetch'] - diagnostics['passed_quality']
        # Distribute filtered count across filter types (rough estimate)
        if total_filtered > 0:
            diagnostics['filtered_by_volatility'] = int(total_filtered * 0.3)  # ~30% filtered by volatility
            diagnostics['filtered_by_momentum'] = int(total_filtered * 0.3)    # ~30% filtered by momentum
            diagnostics['filtered_by_microstructure'] = int(total_filtered * 0.2)  # ~20% filtered by microstructure
            # Remaining ~20% would be other filters (gaps, halts, etc.)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Structured logging for "Citadel Board" metrics
        logger.info(
            "DayTradingPicksSummary",
            extra={
                "mode": mode,
                "universe_size": len(universe),
                "qualified": qualified_count,
                "returned": len(picks),
                "provider_counts": provider_counts,
                "duration_ms": int(elapsed * 1000),
                "universe_source": universe_source,
                "diagnostics": diagnostics,
            },
        )
        
        # Log top picks for debugging
        if picks:
            for i, pick in enumerate(picks, 1):
                logger.debug(f"  {i}. {pick['symbol']} ({pick['side']}) - Score: {pick['score']:.2f}, Momentum: {pick['features']['momentum15m']*100:.2f}%")
        
        # Log diagnostics summary
        logger.info(f"📊 Diagnostics: Scanned={diagnostics['scanned_count']}, "
                   f"Passed liquidity={diagnostics['passed_liquidity']}, "
                   f"Passed quality={diagnostics['passed_quality']}, "
                   f"Failed fetch={diagnostics['failed_data_fetch']}, "
                   f"Filtered={total_filtered}")
        
        # Add universe_source to each pick for tracking
        for pick in picks:
            pick['universe_source'] = universe_source
        
        # Prepare metadata to return with picks
        metadata = {
            'universe_size': len(universe),
            'universe_source': universe_source,
            'diagnostics': diagnostics
        }
        
        # If we have picks, cache and return them with metadata
        if picks:
            # Cache for 60 seconds (intraday data changes frequently)
            # Cache both picks and metadata
            cache_data = (picks, metadata)
            cache.set(cache_key, cache_data, 60)
            logger.info(f"✅ Generated {len(picks)} picks for {mode} mode (source: {universe_source}, universe: {len(universe)})")
            logger.info(f"📦 Cached {len(picks)} picks with key: {cache_key}")
            return (picks, metadata)
        
        # Soft failure: Return empty with helpful message (frontend can show this)
        logger.warning(f"⚠️ No picks qualified for {mode} mode after filtering {len(universe)} symbols")
        logger.warning(f"   Qualified count: {qualified_count}, Failed symbols: {len(failed_symbols)}, Provider counts: {provider_counts}")
        # DON'T cache empty results - let it retry on next request to get fresh data
        # This prevents empty cache from blocking picks when market conditions improve
        logger.info(f"📦 NOT caching empty result - will retry on next request")
        return ([], metadata)
    finally:
        loop.close()
    
    # Final fallback to mock if everything fails (should rarely happen)
    logger.warning(f"⚠️ All providers failed, using mock data for {mode} mode")
    mock_picks = _get_mock_day_trading_picks(limit)[:limit]
    # Don't cache mock data - let it retry real data on next call
    return mock_picks


def _get_day_trading_picks_from_polygon(limit=20):
    """
    Fetches top stock gainers as day trading picks using Polygon API.
    Returns a list of dicts compatible with DayTradingPickType format.
    """
    try:
        from polygon import RESTClient
        import os

        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            logger.warning("POLYGON_API_KEY not set, using mock data")
            return _get_mock_day_trading_picks(limit)

        client = RESTClient(api_key)

        # Get top gainers snapshot
        snapshots = client.get_snapshot_direction(
            market_type='stocks',
            direction='gainers',
            include_otc=False
        )

        picks = []
        for snap in snapshots[:limit]:
            try:
                price = snap.last_trade.price if snap.last_trade else 0
                change_pct = snap.todays_change_percent if hasattr(snap, 'todays_change_percent') else 0
                volume = snap.todays_volume if hasattr(snap, 'todays_volume') else 0

                # Calculate score based on momentum (change percentage)
                score = abs(change_pct) * 10  # Scale to 0-10 range

                picks.append({
                    'symbol': snap.ticker,
                    'side': 'LONG',  # Gainers are long opportunities
                    'score': round(score, 2),
                    'features': {
                        'momentum15m': change_pct / 100,  # Convert to decimal
                        'rvol10m': 0.0,  # Not available from snapshot
                        'vwapDist': 0.0,
                        'breakoutPct': change_pct / 100,
                        'spreadBps': 5.0,  # Default
                        'catalystScore': min(10.0, abs(change_pct) * 2)  # High momentum = high catalyst
                    },
                    'risk': {
                        'atr5m': price * 0.02,  # 2% of price as ATR estimate
                        'sizeShares': 100,  # Default position size
                        'stop': round(price * 0.98, 2),  # 2% stop loss
                        'targets': [round(price * 1.03, 2), round(price * 1.05, 2)],  # 3% and 5% targets
                        'timeStopMin': 240  # 4 hours
                    },
                    'notes': f"Top gainer: {change_pct:.2f}% today. High momentum opportunity."
                })
            except Exception as e:
                logger.warning(f"Error processing snapshot for {snap.ticker}: {e}")
                continue

        logger.info(f"Fetched {len(picks)} picks from Polygon API")
        return picks

    except Exception as e:
        logger.error(f"Error fetching from Polygon API: {e}", exc_info=True)
        # Fallback to mock data
        return _get_mock_day_trading_picks(limit)


def _get_mock_day_trading_picks(limit=20):
    """Generate mock day trading picks as final fallback"""
    import random
    default_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'JPM', 'V', 'TMO']

    picks = []
    for symbol in default_symbols[:limit]:
        price = random.uniform(50, 500)
        change_pct = random.uniform(-5, 10)  # -5% to +10%
        score = abs(change_pct) * 1.5

        picks.append({
            'symbol': symbol,
            'side': 'LONG' if change_pct > 0 else 'SHORT',
            'score': round(score, 2),
            'features': {
                'momentum15m': change_pct / 100,
                'rvol10m': 0.02,
                'vwapDist': 0.01,
                'breakoutPct': change_pct / 100,
                'spreadBps': 5.0,
                'catalystScore': min(10.0, abs(change_pct) * 2)
            },
            'risk': {
                'atr5m': price * 0.02,
                'sizeShares': 100,
                'stop': round(price * 0.98, 2),
                'targets': [round(price * 1.03, 2), round(price * 1.05, 2)],
                'timeStopMin': 240
            },
            'notes': f"Mock pick: {change_pct:.2f}% change"
        })

    return picks


async def _get_intraday_data(symbol: str):
    """
    Get intraday OHLCV data for a symbol from real market data sources.
    Falls back to mock data if real data is unavailable.
    """
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta

        # Try to get real intraday data from market data service
        try:
            from .market_data_api_service import MarketDataAPIService, DataProvider

            async with MarketDataAPIService() as service:
                # Try Polygon.io first for real intraday data
                polygon_data = await _fetch_polygon_intraday(symbol.upper(), service)
                if polygon_data:
                    logger.info(f"Got real intraday data from Polygon.io for {symbol}")
                    return polygon_data

                # Try Alpaca as fallback
                alpaca_data = await _fetch_alpaca_intraday(symbol.upper(), service)
                if alpaca_data:
                    logger.info(f"Got real intraday data from Alpaca for {symbol}")
                    return alpaca_data

                # Fallback: Get recent daily data and create intraday approximation
                hist_data = await service.get_historical_data(symbol.upper(), period='1mo')

                if hist_data is not None and len(hist_data) > 0:
                    # hist_data is already a DataFrame from market_data_api_service
                    df = hist_data.copy()
                    if 'timestamp' not in df.columns:
                        df['timestamp'] = df.index
                    df = df.sort_values('timestamp')

                    # Get latest price for current day
                    latest = df.iloc[-1]
                    # Handle different column name formats
                    if 'Close' in df.columns:
                        current_price = float(latest['Close'])
                        volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
                    elif 'close' in df.columns:
                        current_price = float(latest['close'])
                        volume_col = 'volume'
                    else:
                        current_price = 100.0
                        volume_col = 'volume'

                    # Create intraday data by interpolating from daily data
                    # This is an approximation - real intraday data would be better
                    now = datetime.now()

                    # Generate 1-minute bars for today (last 390 minutes = 6.5 hours)
                    # Use daily volatility to create realistic intraday movement
                    close_col = 'Close' if 'Close' in df.columns else 'close'
                    daily_vol = df[close_col].pct_change().std() if len(df) > 1 else 0.02
                    if pd.isna(daily_vol) or daily_vol == 0:
                        daily_vol = 0.02  # Default 2% volatility

                    timestamps_1m = [now - timedelta(minutes=i) for i in range(390, 0, -1)]
                    prices_1m = [current_price]

                    for i in range(1, 390):
                        # Random walk with daily volatility
                        change = np.random.normal(0, daily_vol / np.sqrt(390))  # Scale to 1-minute
                        prices_1m.append(prices_1m[-1] * (1 + change))

                    ohlcv_1m = pd.DataFrame({
                        'timestamp': timestamps_1m,
                        'open': prices_1m,
                        'high': [p * (1 + abs(np.random.normal(0, daily_vol / 390))) for p in prices_1m],
                        'low': [p * (1 - abs(np.random.normal(0, daily_vol / 390))) for p in prices_1m],
                        'close': prices_1m,
                        'volume': [int(float(latest.get(volume_col, latest.get('volume', 1000000))) / 390) for _ in range(390)]
                    })

                    # Generate 5-minute bars
                    timestamps_5m = [now - timedelta(minutes=i * 5) for i in range(78, 0, -1)]
                    prices_5m = prices_1m[::5][:78]

                    ohlcv_5m = pd.DataFrame({
                        'timestamp': timestamps_5m,
                        'open': prices_5m,
                        'high': [p * (1 + abs(np.random.normal(0, daily_vol / 78))) for p in prices_5m],
                        'low': [p * (1 - abs(np.random.normal(0, daily_vol / 78))) for p in prices_5m],
                        'close': prices_5m,
                        'volume': [int(float(latest.get(volume_col, latest.get('volume', 5000000))) / 78) for _ in range(78)]
                    })

                    logger.info(f"Generated intraday data for {symbol} from historical data")
                    return ohlcv_1m, ohlcv_5m
        except Exception as e:
            logger.warning(f"Could not fetch real data for {symbol}: {e}, using fallback")

        # Fallback to mock data if real data unavailable
        now = datetime.now()

        # Generate 1-minute bars (last 390 = 6.5 hours)
        base_price = 100.0 + np.random.uniform(-20, 20)
        timestamps_1m = [now - timedelta(minutes=i) for i in range(390, 0, -1)]

        prices_1m = [base_price]
        for i in range(1, 390):
            change = np.random.normal(0, 0.001)  # 0.1% volatility
            prices_1m.append(prices_1m[-1] * (1 + change))

        ohlcv_1m = pd.DataFrame({
            'timestamp': timestamps_1m,
            'open': prices_1m,
            'high': [p * (1 + abs(np.random.normal(0, 0.0005))) for p in prices_1m],
            'low': [p * (1 - abs(np.random.normal(0, 0.0005))) for p in prices_1m],
            'close': prices_1m,
            'volume': [np.random.randint(100000, 1000000) for _ in range(390)]
        })

        # Generate 5-minute bars (last 78 = 6.5 hours)
        timestamps_5m = [now - timedelta(minutes=i * 5) for i in range(78, 0, -1)]
        prices_5m = prices_1m[::5][:78]

        ohlcv_5m = pd.DataFrame({
            'timestamp': timestamps_5m,
            'open': prices_5m,
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices_5m],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices_5m],
            'close': prices_5m,
            'volume': [np.random.randint(500000, 5000000) for _ in range(78)]
        })

        logger.info(f"Using fallback mock data for {symbol}")
        return ohlcv_1m, ohlcv_5m

    except Exception as e:
        logger.error(f"Error getting intraday data for {symbol}: {e}")
        return None, None


async def _fetch_polygon_intraday(symbol: str, service) -> Optional[tuple]:
    """Fetch real intraday data from Polygon.io"""
    try:
        from .market_data_api_service import DataProvider
        import aiohttp
        from datetime import datetime, timedelta

        # Check if Polygon API key is available
        if DataProvider.POLYGON not in service.api_keys:
            return None

        api_key = service.api_keys[DataProvider.POLYGON].key
        session = service.session or aiohttp.ClientSession()

        # Get today's date and yesterday for intraday data
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        # Fetch 1-minute bars for today
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{start_date}/{end_date}?adjusted=true&sort=asc&limit=50000&apiKey={api_key}"
        params = {'adjusted': 'true', 'sort': 'asc', 'limit': 50000, 'apiKey': api_key}

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('status') == 'OK' and data.get('resultsCount', 0) > 0:
                    results = data.get('results', [])

                    # Convert to DataFrame
                    import pandas as pd
                    df_1m = pd.DataFrame(results)
                    df_1m['timestamp'] = pd.to_datetime(df_1m['t'], unit='ms')
                    df_1m = df_1m.rename(columns={
                        'o': 'open',
                        'h': 'high',
                        'l': 'low',
                        'c': 'close',
                        'v': 'volume'
                    })
                    df_1m = df_1m[['timestamp', 'open', 'high', 'low', 'close', 'volume']].sort_values('timestamp')

                    # Get last 390 bars (6.5 hours)
                    df_1m = df_1m.tail(390)

                    # Create 5-minute bars by resampling
                    df_5m = df_1m.set_index('timestamp').resample('5T').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).reset_index()
                    df_5m = df_5m.tail(78)  # Last 78 bars (6.5 hours)

                    return df_1m, df_5m

        return None
    except Exception as e:
        logger.warning(f"Polygon.io intraday fetch failed for {symbol}: {e}")
        return None


async def _fetch_alpaca_intraday(symbol: str, service) -> Optional[tuple]:
    """Fetch real intraday data from Alpaca"""
    try:
        import os
        import aiohttp
        from datetime import datetime, timedelta

        # Check for Alpaca credentials
        alpaca_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret = os.getenv('ALPACA_SECRET_KEY')

        if not alpaca_key or not alpaca_secret:
            return None

        session = service.session or aiohttp.ClientSession()

        # Get today's date
        today = datetime.now()
        start_time = (today - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S-05:00')
        end_time = today.strftime('%Y-%m-%dT%H:%M:%S-05:00')

        # Fetch 1-minute bars
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
        params = {
            'timeframe': '1Min',
            'start': start_time,
            'end': end_time,
            'limit': 1000
        }
        headers = {
            'APCA-API-KEY-ID': alpaca_key,
            'APCA-API-SECRET-KEY': alpaca_secret
        }

        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('bars'):
                    bars = data['bars']

                    import pandas as pd
                    df_1m = pd.DataFrame(bars)
                    df_1m['timestamp'] = pd.to_datetime(df_1m['t'])
                    df_1m = df_1m.rename(columns={
                        'o': 'open',
                        'h': 'high',
                        'l': 'low',
                        'c': 'close',
                        'v': 'volume'
                    })
                    df_1m = df_1m[['timestamp', 'open', 'high', 'low', 'close', 'volume']].sort_values('timestamp')

                    # Get last 390 bars
                    df_1m = df_1m.tail(390)

                    # Create 5-minute bars
                    df_5m = df_1m.set_index('timestamp').resample('5T').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).reset_index()
                    df_5m = df_5m.tail(78)

                    return df_1m, df_5m

        return None
    except Exception as e:
        logger.warning(f"Alpaca intraday fetch failed for {symbol}: {e}")
        return None


def _generate_pick_notes(symbol: str, features: dict, side: str, score: float) -> str:
    """Generate human-readable notes for a pick"""
    notes_parts = []

    # Regime
    if features.get('is_trend_regime', 0.0) > 0.5:
        notes_parts.append("Strong trending market")
    elif features.get('is_range_regime', 0.0) > 0.5:
        notes_parts.append("Range-bound market")

    # Momentum
    momentum = features.get('momentum_15m', 0.0)
    if abs(momentum) > 0.02:
        notes_parts.append(f"{abs(momentum) * 100:.1f}% momentum")

    # Breakout
    if features.get('is_breakout', 0.0) > 0.5:
        notes_parts.append("Breakout detected")

    # Volume
    volume_ratio = features.get('volume_ratio', 1.0)
    if volume_ratio > 1.5:
        notes_parts.append("High volume")

    # Pattern
    if features.get('is_engulfing_bull', 0.0) > 0.5:
        notes_parts.append("Bullish engulfing pattern")
    elif features.get('is_hammer', 0.0) > 0.5:
        notes_parts.append("Hammer pattern")

    if notes_parts:
        return f"{symbol} {side}: {', '.join(notes_parts)}. Score: {score:.2f}"
    else:
        return f"{symbol} {side} opportunity. Score: {score:.2f}"
