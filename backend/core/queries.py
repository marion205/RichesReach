import graphene
from django.contrib.auth import get_user_model
from .types import UserType, PostType, ChatSessionType, ChatMessageType, CommentType, StockType, StockDataType, WatchlistType, AIPortfolioRecommendationType
# TODO: Add missing types: WatchlistItemType, RustStockAnalysisType, RustRecommendationType, RustHealthType, TechnicalIndicatorsType, FundamentalAnalysisType, StockDiscussionType, PortfolioType, PriceAlertType, SocialFeedType, UserAchievementType, StockSentimentType
from .models import Post, ChatSession, ChatMessage, Comment, User, Stock, StockData, Watchlist, AIPortfolioRecommendation, StockDiscussion, DiscussionComment
# TODO: Add missing models: StockDiscussion, Portfolio
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
    # my_watchlist = graphene.List(WatchlistItemType)  # TODO: Uncomment when WatchlistItemType is available
    beginner_friendly_stocks = graphene.List(StockType)
    
    # Rust Engine queries - TODO: Uncomment when types are available
    # rust_stock_analysis = graphene.Field(RustStockAnalysisType, symbol=graphene.String(required=True))
    # rust_recommendations = graphene.List(RustRecommendationType)
    # rust_health = graphene.Field(RustHealthType)
    
    # AI Portfolio queries
    ai_portfolio_recommendations = graphene.List(AIPortfolioRecommendationType, userId=graphene.ID(required=True))
    
    # Portfolio queries - TODO: Uncomment when types are available
    # my_portfolio = graphene.List('core.types.PortfolioType')
    portfolio_value = graphene.Float()
    
    # Stock price queries
    current_stock_prices = graphene.List('core.types.StockPriceType', symbols=graphene.List(graphene.String))

    # Phase 3 Social Features - TODO: Uncomment when types are available
    watchlists = graphene.List(WatchlistType, user_id=graphene.ID())
    watchlist = graphene.Field(WatchlistType, id=graphene.ID(required=True))
    public_watchlists = graphene.List(WatchlistType)
    my_watchlist = graphene.List(WatchlistType)
    rust_stock_analysis = graphene.Field('core.types.RustStockAnalysisType', symbol=graphene.String(required=True))
    
    # Discussion queries (Reddit-style)
    stock_discussions = graphene.List('core.types.StockDiscussionType', stock_symbol=graphene.String(required=False), limit=graphene.Int(required=False))
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
            )[:50]  # Limit search results
            
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
        
        return Stock.objects.all()[:100]  # Limit to 100 stocks
    
    def resolve_stock(self, info, symbol):
        """Get a specific stock by symbol"""
        try:
            return Stock.objects.get(symbol=symbol.upper())
        except Stock.DoesNotExist:
            return None
    
    def resolve_my_watchlist(self, info):
        """Get current user's watchlist items"""
        user = info.context.user
        if user.is_anonymous:
            return []
        
        # Get all watchlist items from all user's watchlists
        from .models import WatchlistItem
        return WatchlistItem.objects.filter(
            watchlist__user=user
        ).select_related('stock', 'watchlist').order_by('-added_at')
    
    def resolve_beginner_friendly_stocks(self, info):
        """Get stocks suitable for beginner investors (under $30k/year)"""
        return Stock.objects.filter(
            beginner_friendly_score__gte=65,  # Moderate beginner-friendly score
            market_cap__gte=10000000000,     # Mid to large cap companies (>$10B)
        ).order_by('-beginner_friendly_score')[:20]
    
    
    def resolve_rust_recommendations(self, info):
        """Get beginner-friendly recommendations from Rust engine"""
        try:
            from .stock_service import AlphaVantageService
            service = AlphaVantageService()
            recommendations = service.get_rust_recommendations()
            if recommendations:
                return [
                    RustRecommendationType(
                        symbol=rec.get('symbol', ''),
                        reason=rec.get('reason', ''),
                        riskLevel=rec.get('riskLevel', 'Unknown'),
                        beginnerScore=rec.get('beginnerScore', 0)
                    )
                    for rec in recommendations
                ]
            return []
        except Exception as e:
            print(f"Rust recommendations error: {e}")
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
            return Watchlist.objects.filter(user_id=user_id, is_public=True)
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
            return StockDiscussion.objects.filter(stock__symbol=stock_symbol.upper()).order_by('-created_at')
        return StockDiscussion.objects.all().order_by('-created_at')[:50]
    
    def resolve_trending_discussions(root, info):
        # Get discussions with most likes in the last 7 days
        from django.utils import timezone
        from datetime import timedelta
        
        week_ago = timezone.now() - timedelta(days=7)
        return StockDiscussion.objects.filter(
            created_at__gte=week_ago
        ).annotate(
            like_count=models.Count('likes')
        ).order_by('-like_count', '-created_at')[:20]
    
    def resolve_user_discussions(root, info, user_id=None):
        if user_id:
            return StockDiscussion.objects.filter(user_id=user_id).order_by('-created_at')
        user = info.context.user
        if user.is_authenticated:
            return StockDiscussion.objects.filter(user=user).order_by('-created_at')
        return []
    
    def resolve_discussion(root, info, id):
        try:
            return StockDiscussion.objects.get(id=id)
        except StockDiscussion.DoesNotExist:
            return None
    
    def resolve_portfolios(root, info, user_id=None):
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        if user_id:
            return Portfolio.objects.filter(user_id=user_id, is_public=True)
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
            return []
        
        if user_id and user_id == str(user.id):
            return PriceAlert.objects.filter(user=user, is_active=True)
        return []
    
    def resolve_social_feed(root, info):
        """Get personalized feed - only posts from followed users + user's own posts"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Get posts from followed users + user's own posts
        # This shows only follower-only posts (not public posts)
        followed_users = user.following.values_list('following', flat=True)
        return StockDiscussion.objects.filter(
            models.Q(user__in=followed_users) | models.Q(user=user)
        ).order_by('-created_at')[:50]
    
    def resolve_user_achievements(root, info, user_id=None):
        if user_id:
            return UserAchievement.objects.filter(user_id=user_id).order_by('-earned_at')
        user = info.context.user
        if user.is_authenticated:
            return UserAchievement.objects.filter(user=user).order_by('-earned_at')
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
        
        # Only allow users to see their own recommendations
        if str(user.id) != str(userId):
            return []
        
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
        """Get Rust engine stock analysis (mock implementation)"""
        from .types import RustStockAnalysisType, TechnicalIndicatorsType, FundamentalAnalysisType
        
        # Mock analysis data - in a real implementation, this would call the Rust engine
        return RustStockAnalysisType(
            symbol=symbol.upper(),
            beginnerFriendlyScore=7.5,
            riskLevel="Medium",
            recommendation="Hold",
            technicalIndicators=TechnicalIndicatorsType(
                rsi=45.2,
                macd=0.15,
                macdSignal=0.12,
                macdHistogram=0.03,
                sma20=150.25,
                sma50=148.75,
                ema12=150.10,
                ema26=149.85,
                bollingerUpper=155.50,
                bollingerLower=145.00,
                bollingerMiddle=150.25
            ),
            fundamentalAnalysis=FundamentalAnalysisType(
                valuationScore=6.8,
                growthScore=7.2,
                stabilityScore=8.1,
                dividendScore=5.5,
                debtScore=7.9
            ),
            reasoning=[
                f"Based on technical and fundamental analysis, {symbol.upper()} shows moderate growth potential with balanced risk.",
                "The stock is trading near its moving averages with positive momentum indicators.",
                "RSI indicates neutral momentum with room for upward movement.",
                "MACD shows bullish crossover potential in the near term.",
                "Fundamental metrics suggest stable financial health and growth prospects."
            ]
        )
    
    def resolve_stock_discussions(self, info, stock_symbol=None, limit=20):
        """Get stock discussions (Reddit-style) - shows public posts and posts from followed users"""
        user = info.context.user
        
        if user.is_anonymous:
            # Anonymous users only see public posts
            discussions = StockDiscussion.objects.filter(visibility='public')
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
            # Anonymous users see no social feed
            return []
        
        # Get users that the current user follows
        followed_users = user.following.values_list('following', flat=True)
        
        if not followed_users:
            # If user isn't following anyone, return empty list
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
            return 0
        
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
                        logger.info(f"💾 Database fallback for {symbol}: ${stock.current_price}")
                except Stock.DoesNotExist:
                    logger.warning(f"Stock {symbol} not found in database")
                except Exception as e:
                    logger.error(f"Error getting database price for {symbol}: {e}")
            
            return prices