import graphene


from django.contrib.auth import get_user_model


from .types import UserType, PostType, ChatSessionType, ChatMessageType, CommentType, StockType, StockDataType, WatchlistType, AIPortfolioRecommendationType, StockMomentType, ChartRangeEnum, DayTradingDataType


from .models import Post, ChatSession, ChatMessage, Comment, User, Stock, StockData, Watchlist, AIPortfolioRecommendation, StockDiscussion, DiscussionComment, Portfolio, StockMoment


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

    rust_stock_analysis = graphene.Field('core.types.RustStockAnalysisType', symbol=graphene.String(required=True))

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
    
    def resolve_day_trading_picks(self, info, mode="SAFE"):
        """Resolve day trading picks using Polygon API with ML fallback"""
        import sys
        print(f"🔍 RESOLVER CALLED: mode={mode}", file=sys.stderr, flush=True)
        logger.info(f"🔍 RESOLVER CALLED: Generating day trading picks for mode: {mode}")
        
        # Use Polygon API as primary source (always works)
        try:
            picks = _get_day_trading_picks_from_polygon(limit=20)
            
            print(f"✅ RESOLVER: Fetched {len(picks)} picks", file=sys.stderr, flush=True)
            logger.info(f"✅ Fetched {len(picks)} picks from Polygon/mock fallback")
            
            # Return dict - Graphene will serialize it automatically
            result = {
                'asOf': timezone.now().isoformat(),
                'mode': mode,
                'picks': picks,
                'universeSize': len(picks),
                'qualityThreshold': 0.0
            }
            
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
            logger.error(f"❌ Error with Polygon API: {fallback_error}", exc_info=True)
            import traceback
            traceback.print_exc()
            # Return empty picks on error
            return {
                'asOf': timezone.now().isoformat(),
                'mode': mode,
                'picks': [],
                'universeSize': 0,
                'qualityThreshold': 2.5 if mode == "SAFE" else 2.0
            }


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


def resolve_me(root, info):
    user = info.context.user

    if user.is_anonymous:
        return None

    return user


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


def resolve_stock(self, info, symbol):
    """Get a specific stock by symbol (using DataLoader to prevent N+1)"""
    from .dataloaders import get_stock_loader
    stock_loader = get_stock_loader()
    return stock_loader.load(symbol.upper())


def resolve_my_watchlist(self, info):
    """Get current user's watchlist items"""

    user = info.context.user

    if user.is_anonymous:

        return []
    if user.is_anonymous:

        return []
    from .models import WatchlistItem

    return WatchlistItem.objects.filter(

    watchlist__user=user

    ).select_related('stock', 'watchlist').order_by('-added_at')


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

def resolve_my_watchlist(self, info):
    """Get current user's watchlist"""

    user = info.context.user

    if user.is_anonymous:

        return []
    from .models import Watchlist

    return Watchlist.objects.filter(user=user).order_by('-added_at')

def resolve_rust_stock_analysis(self, info, symbol):
    """Get Rust engine stock analysis - calls the actual Rust service"""

    import logging

    logger = logging.getLogger(__name__)


    from .types import RustStockAnalysisType, TechnicalIndicatorsType, FundamentalAnalysisType

    from .rust_stock_service import rust_stock_service


    symbol_upper = symbol.upper()


    try:
        # Call the Rust service
        logger.info(f"Calling Rust service for stock analysis: {symbol_upper}")

        rust_response = rust_stock_service.analyze_stock(symbol_upper)

        logger.info(f"Rust service response received for {symbol_upper}: {rust_response}")

        # Map Rust service response to GraphQL type
        # The Rust service returns a dict with analysis data
        # We need to extract and map the fields

        # Extract technical indicators if available
        technical_data = rust_response.get('technicalIndicators', {}) or rust_response.get('technical_indicators', {}) or {}

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
            bollingerMiddle=technical_data.get('bollingerMiddle') or technical_data.get('bollinger_middle') or technical_data.get('BBMiddle') or 0.0
        )


        # Extract fundamental analysis if available
        fundamental_data = rust_response.get('fundamentalAnalysis', {}) or rust_response.get('fundamental_analysis', {}) or {}

        fundamental_analysis = FundamentalAnalysisType(
            valuationScore=fundamental_data.get('valuationScore') or fundamental_data.get('valuation_score') or 70.0,
            growthScore=fundamental_data.get('growthScore') or fundamental_data.get('growth_score') or 65.0,
            stabilityScore=fundamental_data.get('stabilityScore') or fundamental_data.get('stability_score') or 80.0,
            dividendScore=fundamental_data.get('dividendScore') or fundamental_data.get('dividend_score') or 60.0,
            debtScore=fundamental_data.get('debtScore') or fundamental_data.get('debt_score') or 75.0
        )


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

        beginner_friendly_score = rust_response.get('beginnerFriendlyScore') or rust_response.get('beginner_friendly_score')

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

        return RustStockAnalysisType(
            symbol=symbol_upper,
            beginnerFriendlyScore=float(beginner_friendly_score) if beginner_friendly_score else 75.0,
            riskLevel=risk_level,
            recommendation=recommendation.upper(),
            technicalIndicators=technical_indicators,
            fundamentalAnalysis=fundamental_analysis,
            reasoning=reasoning if reasoning else [f"Analysis for {symbol_upper}"]
        )


    except Exception as e:
        logger.error(f"Error calling Rust service for {symbol_upper}: {str(e)}", exc_info=True)

    # Fallback to basic analysis if Rust service fails

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

    reasoning=[f"Rust service unavailable for {symbol_upper}. Please try again later."]

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

def resolve_portfolio_metrics(self, info):
    """Get portfolio metrics (regular feature, not premium)"""

    from .premium_analytics import PremiumAnalyticsService

    service = PremiumAnalyticsService()

    # For testing purposes, use user ID 1 if no user is authenticated

    user = info.context.user

    user_id = user.id if user and not user.is_anonymous else 1

    return service.get_portfolio_performance_metrics(user_id)

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
                volatility = float(returns.std() * np.sqrt(252)) * 100 if len(returns) > 1 else 0.0  # Annualized volatility

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
            return None

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
            
            # Score with ML
            score = ml_scorer.score(features)
            
            # Filter by quality threshold
            if score < quality_threshold:
                continue
            
            # Calculate risk metrics
            current_price = float(ohlcv_5m.iloc[-1]['close'])
            risk_metrics = feature_service.calculate_risk_metrics(
                features, mode, current_price
            )
            
            # Determine side
            momentum = features.get('momentum_15m', 0.0)
            side = 'LONG' if momentum > 0 else 'SHORT'
            
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
                    timestamps_5m = [now - timedelta(minutes=i*5) for i in range(78, 0, -1)]
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
        timestamps_5m = [now - timedelta(minutes=i*5) for i in range(78, 0, -1)]
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
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{yesterday.strftime('%Y-%m-%d')}/{today.strftime('%Y-%m-%d')}"
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
        notes_parts.append(f"{abs(momentum)*100:.1f}% momentum")
    
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


