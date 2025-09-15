import graphene
from django.contrib.auth import get_user_model
from .types import UserType, PostType, ChatSessionType, ChatMessageType, CommentType, StockType, StockDataType, WatchlistType, AIPortfolioRecommendationType
from .models import Post, ChatSession, ChatMessage, Comment, User, Stock, StockData, Watchlist, AIPortfolioRecommendation, StockDiscussion, DiscussionComment, Portfolio
import django.db.models as models
from django.utils import timezone
from datetime import timedelta

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
    beginner_friendly_stocks = graphene.List(StockType)
    
    # AI Portfolio queries
    ai_portfolio_recommendations = graphene.List(AIPortfolioRecommendationType, userId=graphene.ID(required=True))
    
    # Portfolio queries
    my_portfolios = graphene.Field('core.portfolio_types.PortfolioSummaryType')
    portfolio_names = graphene.List(graphene.String)
    portfolio_value = graphene.Float()
    portfolio_metrics = graphene.Field('core.premium_types.PortfolioMetricsType')
    
    # Stock price queries
    current_stock_prices = graphene.List('core.types.StockPriceType', symbols=graphene.List(graphene.String))
    
    # Test queries for premium features (no auth required for testing)
    test_portfolio_metrics = graphene.Field('core.premium_types.PortfolioMetricsType')
    test_ai_recommendations = graphene.Field('core.premium_types.AIRecommendationsType')
    test_stock_screening = graphene.List('core.premium_types.StockScreeningResultType')
    test_options_analysis = graphene.Field('core.premium_types.OptionsAnalysisType', symbol=graphene.String(required=True))
    
    # Advanced stock screening query
    advanced_stock_screening = graphene.List(
        'core.premium_types.StockScreeningResultType',
        sector=graphene.String(required=False),
        min_market_cap=graphene.Float(required=False),
        max_market_cap=graphene.Float(required=False),
        min_pe_ratio=graphene.Float(required=False),
        max_pe_ratio=graphene.Float(required=False),
        min_beginner_score=graphene.Int(required=False),
        sort_by=graphene.String(required=False),
        limit=graphene.Int(required=False)
    )
    
    # Phase 3 Social Features
    watchlists = graphene.List(WatchlistType, user_id=graphene.ID())
    watchlist = graphene.Field(WatchlistType, id=graphene.ID(required=True))
    public_watchlists = graphene.List(WatchlistType)
    my_watchlist = graphene.List(WatchlistType)
    rust_stock_analysis = graphene.Field('core.types.RustStockAnalysisType', symbol=graphene.String(required=True))
    
    # Discussion queries (Reddit-style)
    stock_discussions = graphene.List('core.types.StockDiscussionType', stock_symbol=graphene.String(required=False), limit=graphene.Int(required=False))
    discussion_detail = graphene.Field('core.types.StockDiscussionType', id=graphene.ID(required=True))
    
    social_feed = graphene.List('core.types.StockDiscussionType')
    top_performers = graphene.List(StockType)
    market_sentiment = graphene.Field(graphene.JSONString)

    def resolve_all_users(root, info):
        user = info.context.user
        if user.is_anonymous:
            return []
        # Exclude current user and return users they don't follow
        return User.objects.exclude(id=user.id).exclude(
            id__in=user.following.values_list('following', flat=True)
        )[:20] # Limit to 20 users

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
        return users[:20] # Limit results

    def resolve_me(root, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        return user

    def resolve_wall_posts(self, info):
        user = info.context.user
        if user.is_anonymous:
            return []
        # Get users that the current user follows
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
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return None

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
            # First try to find in database
            db_stocks = Stock.objects.filter(
                models.Q(symbol__icontains=search.upper()) |
                models.Q(company_name__icontains=search)
            )[:50] # Limit search results
            # If we have results, return them
            if db_stocks.exists():
                return db_stocks
            # If no results, try API search
            try:
                from .stock_service import AlphaVantageService
                service = AlphaVantageService()
                api_stocks = service.search_and_sync_stocks(search)
                if api_stocks:
                    return api_stocks
                else:
                    return Stock.objects.none()
            except Exception as e:
                print(f"API search error: {e}")
                return Stock.objects.none()
        return Stock.objects.all()[:100] # Limit to 100 stocks

    def resolve_stock(self, info, symbol):
        """Get a specific stock by symbol"""
        try:
            return Stock.objects.get(symbol=symbol.upper())
        except Stock.DoesNotExist:
            return None

    def resolve_beginner_friendly_stocks(self, info):
        """Get stocks suitable for beginner investors (under $30k/year)"""
        return Stock.objects.filter(
            beginner_friendly_score__gte=65, # Moderate beginner-friendly score
            market_cap__gte=10000000000, # Mid to large cap companies (>$10B)
        ).order_by('-beginner_friendly_score')[:20]

    def resolve_ai_portfolio_recommendations(self, info, userId):
        """Get AI portfolio recommendations for a user"""
        try:
            return AIPortfolioRecommendation.objects.filter(user_id=userId).order_by('-created_at')
        except Exception as e:
            print(f"AI recommendations error: {e}")
            return []

    def resolve_my_portfolios(self, info):
        """Get current user's portfolios"""
        user = info.context.user
        if user.is_anonymous:
            return None
        # This would return a summary of all user's portfolios
        return {"portfolios": Portfolio.objects.filter(user=user)}

    def resolve_portfolio_names(self, info):
        """Get list of portfolio names for current user"""
        user = info.context.user
        if user.is_anonymous:
            return []
        return list(Portfolio.objects.filter(user=user).values_list('name', flat=True))

    def resolve_portfolio_value(self, info):
        """Get total portfolio value for current user"""
        user = info.context.user
        if user.is_anonymous:
            return 0.0
        # This would calculate total value across all portfolios
        return 0.0  # Placeholder

    def resolve_portfolio_metrics(self, info):
        """Get portfolio metrics for current user"""
        user = info.context.user
        if user.is_anonymous:
            return None
        # This would return comprehensive portfolio metrics
        return None  # Placeholder

    def resolve_current_stock_prices(self, info, symbols):
        """Get current stock prices for given symbols"""
        # This would fetch real-time prices
        return []  # Placeholder

    def resolve_test_portfolio_metrics(self, info):
        """Test endpoint for portfolio metrics"""
        return None  # Placeholder

    def resolve_test_ai_recommendations(self, info):
        """Test endpoint for AI recommendations"""
        return None  # Placeholder

    def resolve_test_stock_screening(self, info):
        """Test endpoint for stock screening"""
        return []  # Placeholder

    def resolve_advanced_stock_screening(self, info, sector=None, min_market_cap=None, max_market_cap=None, 
                                        min_pe_ratio=None, max_pe_ratio=None, min_beginner_score=None, 
                                        sort_by=None, limit=50):
        """Advanced stock screening with filters"""
        queryset = Stock.objects.all()
        
        # Apply filters
        if sector:
            queryset = queryset.filter(sector__icontains=sector)
        if min_market_cap:
            queryset = queryset.filter(market_cap__gte=min_market_cap)
        if max_market_cap:
            queryset = queryset.filter(market_cap__lte=max_market_cap)
        if min_pe_ratio:
            queryset = queryset.filter(pe_ratio__gte=min_pe_ratio)
        if max_pe_ratio:
            queryset = queryset.filter(pe_ratio__lte=max_pe_ratio)
        if min_beginner_score:
            queryset = queryset.filter(beginner_friendly_score__gte=min_beginner_score)
        
        # Apply sorting
        if sort_by == 'ml_score':
            queryset = queryset.order_by('-beginner_friendly_score')
        elif sort_by == 'market_cap':
            queryset = queryset.order_by('-market_cap')
        elif sort_by == 'pe_ratio':
            queryset = queryset.order_by('pe_ratio')
        else:
            queryset = queryset.order_by('symbol')
        
        # Apply limit
        if limit:
            queryset = queryset[:limit]
        
        # Convert to screening results format
        results = []
        for stock in queryset:
            results.append({
                'symbol': stock.symbol,
                'company_name': stock.company_name,
                'sector': stock.sector,
                'market_cap': float(stock.market_cap) if stock.market_cap else None,
                'pe_ratio': float(stock.pe_ratio) if stock.pe_ratio else None,
                'dividend_yield': float(stock.dividend_yield) if stock.dividend_yield else None,
                'beginner_friendly_score': stock.beginner_friendly_score,
                'score': float(stock.beginner_friendly_score),  # For GraphQL schema
                'ml_score': float(stock.beginner_friendly_score),  # For mobile app compatibility
                'reasoning': f"Based on beginner-friendly score of {stock.beginner_friendly_score}",
                'current_price': float(stock.current_price) if stock.current_price else None,
                'volatility': float(stock.volatility) if stock.volatility else None,
                'debt_ratio': float(stock.debt_ratio) if stock.debt_ratio else None,
            })
        
        return results

    def resolve_rust_stock_analysis(self, info, symbol):
        """Rust engine stock analysis"""
        try:
            stock = Stock.objects.get(symbol=symbol)
            
            # Calculate analysis based on stock data
            risk_level = "Low"
            recommendation = "HOLD"
            beginner_score = float(stock.beginner_friendly_score) if stock.beginner_friendly_score else 50.0
            
            # Determine risk level based on volatility
            if stock.volatility:
                if stock.volatility > 0.3:
                    risk_level = "High"
                elif stock.volatility > 0.15:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
            
            # Determine recommendation based on beginner score and other factors
            if beginner_score >= 80:
                recommendation = "STRONG BUY"
            elif beginner_score >= 60:
                recommendation = "BUY"
            elif beginner_score >= 40:
                recommendation = "HOLD"
            elif beginner_score >= 20:
                recommendation = "SELL"
            else:
                recommendation = "AVOID"
            
            # Create technical indicators
            technical_indicators = {
                'rsi': 50.0,  # Placeholder
                'macd': 0.0,  # Placeholder
                'bollinger_bands': {'upper': 0, 'middle': 0, 'lower': 0},  # Placeholder
                'moving_averages': {'sma_20': 0, 'sma_50': 0, 'sma_200': 0}  # Placeholder
            }
            
            # Create fundamental analysis
            fundamental_analysis = {
                'pe_ratio': float(stock.pe_ratio) if stock.pe_ratio else None,
                'market_cap': float(stock.market_cap) if stock.market_cap else None,
                'debt_ratio': float(stock.debt_ratio) if stock.debt_ratio else None,
                'dividend_yield': float(stock.dividend_yield) if stock.dividend_yield else None
            }
            
            # Create reasoning
            reasoning = [
                f"Beginner-friendly score: {beginner_score}/100",
                f"Risk level: {risk_level}",
                f"Volatility: {float(stock.volatility) if stock.volatility else 'N/A'}",
                f"PE Ratio: {float(stock.pe_ratio) if stock.pe_ratio else 'N/A'}"
            ]
            
            return {
                'symbol': symbol,
                'beginnerFriendlyScore': beginner_score,  # Match GraphQL field name
                'riskLevel': risk_level,  # Match GraphQL field name
                'recommendation': recommendation,
                'technicalIndicators': technical_indicators,  # Match GraphQL field name
                'fundamentalAnalysis': fundamental_analysis,  # Match GraphQL field name
                'reasoning': reasoning
            }
            
        except Stock.DoesNotExist:
            return None

    def resolve_test_options_analysis(self, info, symbol):
        """Test endpoint for options analysis"""
        return None  # Placeholder

    def resolve_watchlists(self, root, info, user_id=None):
        user = info.context.user
        if not user.is_authenticated:
            return []
        if user_id:
            return Watchlist.objects.filter(user_id=user_id, is_public=True)
        return Watchlist.objects.filter(user=user)

    def resolve_watchlist(self, root, info, id):
        try:
            watchlist = Watchlist.objects.get(id=id)
            if watchlist.is_public or watchlist.user == info.context.user:
                return watchlist
            return None
        except Watchlist.DoesNotExist:
            return None

    def resolve_public_watchlists(self, root, info):
        return Watchlist.objects.filter(is_public=True).order_by('-created_at')[:20]

    def resolve_my_watchlist(self, info):
        """Get current user's watchlist items"""
        user = info.context.user
        if user.is_anonymous:
            return []
        return Watchlist.objects.filter(user=user)


    def resolve_stock_discussions(self, root, info, stock_symbol=None, limit=None):
        if stock_symbol:
            discussions = StockDiscussion.objects.filter(stock__symbol=stock_symbol.upper()).order_by('-created_at')
        else:
            discussions = StockDiscussion.objects.all().order_by('-created_at')
        
        if limit:
            discussions = discussions[:limit]
        else:
            discussions = discussions[:50]
        
        return discussions

    def resolve_discussion_detail(self, root, info, id):
        try:
            return StockDiscussion.objects.get(id=id)
        except StockDiscussion.DoesNotExist:
            return None

    def resolve_social_feed(self, root, info):
        """Get personalized feed - only posts from followed users + user's own posts"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        # Get posts from followed users + user's own posts
        followed_users = user.following.values_list('following', flat=True)
        return StockDiscussion.objects.filter(
            models.Q(user__in=followed_users) | models.Q(user=user)
        ).order_by('-created_at')[:50]

    def resolve_top_performers(self, info):
        """Get top performing stocks"""
        return Stock.objects.all().order_by('-price_change_percent')[:20]

    def resolve_market_sentiment(self, info):
        """Get market sentiment data"""
        return {"sentiment": "neutral", "confidence": 0.5}  # Placeholder
