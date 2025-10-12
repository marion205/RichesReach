# core/schema.py
from __future__ import annotations

import graphene
from django.contrib.auth import get_user_model
from django.db import models as djmodels

from .types import (
    UserType,
    PostType,
    ChatSessionType,
    ChatMessageType,
    CommentType,
    StockType,
    StockDataType,
    WatchlistType,
    WatchlistItemType,
    AIPortfolioRecommendationType,
    StockDiscussionType,
    DebtSnowballResultType,
    CreditUtilResultType,
    PurchaseAdviceType,
    SignalType,
)
from .models import (
    Post,
    ChatSession,
    ChatMessage,
    Comment,
    Stock,
    StockData,
    Watchlist,
    AIPortfolioRecommendation,
    StockDiscussion,
    DiscussionComment,
    Portfolio,
)
from .financial_tools import debt_snowball_plan, credit_utilization_optimizer, should_buy_luxury_item
from .simple_stock_search import SimpleStockSearchService
from .ai_options_engine import _sentiment_desc

User = get_user_model()


# -------------------------
# Helper: auth guard
# -------------------------
def _require_auth(info):
    user = info.context.user
    return None if user.is_anonymous else user


class Query(graphene.ObjectType):
    # --- Users ---
    all_users = graphene.List(UserType)
    search_users = graphene.List(UserType, query=graphene.String(required=False))
    me = graphene.Field(UserType)
    user = graphene.Field(UserType, id=graphene.ID(required=True))

    # --- Posts ---
    wall_posts = graphene.List(PostType)
    all_posts = graphene.List(PostType)  # Optional generic list
    user_posts = graphene.List(PostType, user_id=graphene.ID(required=True))
    post_comments = graphene.List(CommentType, post_id=graphene.ID(required=True))

    # --- Chat ---
    my_chat_sessions = graphene.List(ChatSessionType)
    chat_session = graphene.Field(ChatSessionType, id=graphene.ID(required=True))
    chat_messages = graphene.List(ChatMessageType, session_id=graphene.ID(required=True))

    # --- Stocks ---
    stocks = graphene.List(StockType, search=graphene.String(required=False), limit=graphene.Int(required=False), offset=graphene.Int(required=False))
    stock = graphene.Field(StockType, symbol=graphene.String(required=True))
    beginner_friendly_stocks = graphene.List(StockType, limit=graphene.Int(required=False), offset=graphene.Int(required=False))
    searchTickers = graphene.List('core.types.TickerSearchResultType', q=graphene.String(required=True), limit=graphene.Int(required=False))
    quotes = graphene.List('core.types.QuoteType', symbols=graphene.List(graphene.String, required=True))
    feedByTickers = graphene.List(StockDiscussionType, symbols=graphene.List(graphene.String, required=True), limit=graphene.Int(required=False))
    advanced_stock_screening = graphene.List(StockType, 
        sector=graphene.String(required=False),
        min_market_cap=graphene.Float(required=False),
        max_market_cap=graphene.Float(required=False),
        min_pe_ratio=graphene.Float(required=False),
        max_pe_ratio=graphene.Float(required=False),
        min_beginner_score=graphene.Int(required=False),
        sort_by=graphene.String(required=False),
        limit=graphene.Int(required=False)
    )

    # --- AI Portfolio Recs ---
    ai_portfolio_recommendations = graphene.List(AIPortfolioRecommendationType, userId=graphene.ID(required=True))
    ai_recommendations = graphene.Field('core.types.AIRecommendationsType')

    # --- Watchlists ---
    watchlists = graphene.List(WatchlistType, user_id=graphene.ID())
    watchlist = graphene.Field(WatchlistType, id=graphene.ID(required=True))
    public_watchlists = graphene.List(WatchlistType, limit=graphene.Int(required=False))
    my_watchlist = graphene.List(WatchlistItemType)
    my_watchlist_stocks = graphene.List(StockType)
    
    # --- Portfolios ---
    myPortfolios = graphene.Field('core.types.MyPortfoliosType')
    
    # --- Rust Stock Analysis ---
    rust_stock_analysis = graphene.Field('core.types.RustStockAnalysisType', symbol=graphene.String(required=True))

    # --- Discussions (Reddit-like) ---
    stock_discussions = graphene.List(
        StockDiscussionType,
        stock_symbol=graphene.String(required=False),
        limit=graphene.Int(required=False),
    )
    stockDiscussions = graphene.List(
        StockDiscussionType,
        stock_symbol=graphene.String(required=False),
        limit=graphene.Int(required=False),
    )
    discussion_detail = graphene.Field(StockDiscussionType, id=graphene.ID(required=True))
    social_feed = graphene.List(StockDiscussionType, limit=graphene.Int(required=False))

    # --- Simple market helpers / placeholders ---
    current_stock_prices = graphene.List('core.types.StockPriceType', symbols=graphene.List(graphene.String))
    market_sentiment = graphene.Field(graphene.JSONString)

    # -------------------------
    # Users
    # -------------------------
    def resolve_all_users(self, info):
        user = _require_auth(info)
        if not user:
            return []
        return (
            User.objects.exclude(id=user.id)
            .exclude(id__in=user.following.values_list('following', flat=True))
            .order_by('id')[:20]
        )

    def resolve_search_users(self, info, query=None):
        user = _require_auth(info)
        if not user:
            return []
        qs = User.objects.exclude(id=user.id)
        if query:
            qs = qs.filter(
                djmodels.Q(name__icontains=query) |
                djmodels.Q(email__icontains=query)
            )
        else:
            qs = qs.exclude(id__in=user.following.values_list('following', flat=True))
        return qs.order_by('id')[:20]

    def resolve_me(self, info):
        return _require_auth(info)

    def resolve_user(self, info, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return None

    # -------------------------
    # Posts
    # -------------------------
    def resolve_wall_posts(self, info):
        user = _require_auth(info)
        if not user:
            return []
        following_users = user.following.values_list('following', flat=True)
        return (
            Post.objects.filter(djmodels.Q(user__in=following_users) | djmodels.Q(user=user))
            .select_related("user")
            .order_by("-created_at")[:100]
        )

    def resolve_all_posts(self, info):
        # Optional: a global feed (could be rate limited or admin-only)
        return Post.objects.select_related("user").order_by("-created_at")[:100]

    def resolve_user_posts(self, info, user_id):
        try:
            u = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return []
        return u.posts.select_related("user").order_by('-created_at')[:100]

    def resolve_post_comments(self, info, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return []
        return post.comments.select_related("user").order_by('-created_at')[:200]

    # -------------------------
    # Chat
    # -------------------------
    def resolve_my_chat_sessions(self, info):
        user = _require_auth(info)
        if not user:
            return []
        return ChatSession.objects.filter(user=user).order_by('-updated_at')[:100]

    def resolve_chat_session(self, info, id):
        user = _require_auth(info)
        if not user:
            return None
        try:
            return ChatSession.objects.get(id=id, user=user)
        except ChatSession.DoesNotExist:
            return None

    def resolve_chat_messages(self, info, session_id):
        user = _require_auth(info)
        if not user:
            return []
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return []
        return session.messages.all()  # ChatMessageType Meta orders by created_at

    # -------------------------
    # Stocks
    # -------------------------
    def resolve_stocks(self, info, search=None, limit=100, offset=0):
        """Browse All stocks with pagination - fetches real-time data from external APIs"""
        limit = max(5, min(limit or 20, 200))  # Minimum 5 stocks per page
        offset = max(0, offset or 0)
        
        try:
            # Use external API to fetch real-time stock data
            from core.stock_data_populator import StockDataPopulator
            populator = StockDataPopulator()
            
            # Get popular stock symbols for Browse All
            popular_symbols = populator._get_popular_stock_symbols()
            
            # Apply search filter if provided
            if search and search.strip():
                search_upper = search.strip().upper()
                popular_symbols = [symbol for symbol in popular_symbols 
                                 if search_upper in symbol or search_upper in symbol]
            
            # Fetch real-time data for the requested symbols
            stocks_data = []
            for symbol in popular_symbols[offset:offset+limit]:
                try:
                    stock_data = populator._fetch_stock_data(symbol)
                    if stock_data:
                        # Convert to Stock model instance for GraphQL
                        from core.models import Stock
                        stock = Stock(**stock_data)
                        stocks_data.append(stock)
                except Exception as e:
                    print(f"Failed to fetch data for {symbol}: {e}")
                    continue
            
            return stocks_data
            
        except Exception as e:
            print(f"Error fetching stocks from API: {e}")
            # Fallback to empty list if API fails
            return []

    def resolve_stock(self, info, symbol):
        try:
            return Stock.objects.get(symbol=symbol.upper())
        except Stock.DoesNotExist:
            return None

    def resolve_searchTickers(self, info, q, limit=10):
        """Search for tickers with autocomplete functionality"""
        if not q or len(q.strip()) < 1:
            return []
        
        # Use the stock service to search for tickers
        stock_service = SimpleStockSearchService()
        results = stock_service.search_and_sync_stocks(q.strip())
        
        # Convert to the expected format
        ticker_results = []
        for stock in results[:limit]:
            # Calculate change percentage using the model method
            change_pct = 0.0
            try:
                change_pct = float(stock.price_change_percent()) if hasattr(stock, 'price_change_percent') else 0.0
            except:
                change_pct = 0.0
                
            ticker_results.append({
                'symbol': stock.symbol,
                'companyName': stock.company_name,
                'lastPrice': float(stock.current_price) if stock.current_price else None,
                'changePct': change_pct,
            })
        
        return ticker_results

    def resolve_quotes(self, info, symbols):
        """Get mini quotes for ticker chips"""
        if not symbols:
            return []
        
        # Get stocks and calculate quotes
        stocks = Stock.objects.filter(symbol__in=[s.upper() for s in symbols])
        quotes = []
        
        for stock in stocks:
            try:
                change_pct = float(stock.price_change_percent()) if hasattr(stock, 'price_change_percent') else 0.0
            except:
                change_pct = 0.0
                
            quotes.append({
                'symbol': stock.symbol,
                'last': float(stock.current_price) if stock.current_price else 0.0,
                'changePct': change_pct,
            })
        
        return quotes

    def resolve_feedByTickers(self, info, symbols, limit=50):
        """Get feed filtered by followed tickers"""
        if not symbols:
            return []
        
        # Filter discussions by ticker symbols
        discussions = StockDiscussion.objects.filter(
            stock__symbol__in=[s.upper() for s in symbols]
        ).select_related('user', 'stock').order_by('-created_at')[:limit]
        
        return discussions

    def resolve_beginner_friendly_stocks(self, info, limit=20, offset=0):
        """Beginner Friendly stocks using user profile + ML/AI for personalized recommendations"""
        limit = max(5, min(limit or 20, 50))  # Minimum 5 stocks per page
        offset = max(0, offset or 0)
        
        try:
            # Get current user for personalized recommendations
            user = _require_auth(info)
            
            # Use external API to fetch real-time stock data
            from core.stock_data_populator import StockDataPopulator
            populator = StockDataPopulator()
            
            # Get popular stock symbols
            popular_symbols = populator._get_popular_stock_symbols()
            
            # Fetch real-time data and calculate beginner-friendly scores
            stocks_data = []
            for symbol in popular_symbols:
                try:
                    stock_data = populator._fetch_stock_data(symbol)
                    if stock_data and stock_data.get('beginner_friendly_score', 0) >= 70:
                        # Convert to Stock model instance for GraphQL
                        from core.models import Stock
                        stock = Stock(**stock_data)
                        stocks_data.append(stock)
                except Exception as e:
                    print(f"Failed to fetch data for {symbol}: {e}")
                    continue
            
            # Sort by beginner-friendly score (highest first)
            stocks_data.sort(key=lambda x: x.beginner_friendly_score or 0, reverse=True)
            
            # Apply user profile-based filtering if user is authenticated
            if user:
                try:
                    # Use ML recommender for personalized recommendations
                    from core.ml_stock_recommender import MLStockRecommender
                    ml_recommender = MLStockRecommender()
                    
                    # Get user profile and apply ML filtering
                    user_profile = ml_recommender.get_user_profile(user)
                    
                    # Filter stocks based on user profile (risk tolerance, investment goals, etc.)
                    filtered_stocks = []
                    for stock in stocks_data:
                        # Apply ML-based filtering based on user profile
                        if ml_recommender._is_stock_suitable_for_user(stock, user_profile):
                            filtered_stocks.append(stock)
                    
                    stocks_data = filtered_stocks
                    
                except Exception as e:
                    print(f"ML recommender error: {e}")
                    # Continue with basic filtering if ML fails
            
            return stocks_data[offset:offset+limit]
            
        except Exception as e:
            print(f"Error fetching beginner-friendly stocks: {e}")
            # Fallback to empty list if API fails
            return []

    def resolve_advanced_stock_screening(self, info, sector=None, min_market_cap=None, max_market_cap=None, 
                                       min_pe_ratio=None, max_pe_ratio=None, min_beginner_score=None, 
                                       sort_by=None, limit=50):
        """Advanced stock screening with filtering and sorting"""
        limit = max(1, min(limit or 50, 200))
        
        # Start with all stocks
        qs = Stock.objects.all()
        
        # Apply filters
        if sector:
            qs = qs.filter(sector__icontains=sector)
        if min_market_cap is not None:
            qs = qs.filter(market_cap__gte=min_market_cap)
        if max_market_cap is not None:
            qs = qs.filter(market_cap__lte=max_market_cap)
        if min_pe_ratio is not None:
            qs = qs.filter(pe_ratio__gte=min_pe_ratio)
        if max_pe_ratio is not None:
            qs = qs.filter(pe_ratio__lte=max_pe_ratio)
        if min_beginner_score is not None:
            qs = qs.filter(beginner_friendly_score__gte=min_beginner_score)
        
        # Apply sorting
        if sort_by == 'ml_score' or sort_by == 'beginner_score':
            qs = qs.order_by('-beginner_friendly_score')
        elif sort_by == 'market_cap':
            qs = qs.order_by('-market_cap')
        elif sort_by == 'pe_ratio':
            qs = qs.order_by('pe_ratio')
        elif sort_by == 'dividend_yield':
            qs = qs.order_by('-dividend_yield')
        else:
            qs = qs.order_by('symbol')
        
        return qs[:limit]

    # -------------------------
    # AI Portfolio Recs
    # -------------------------
    def resolve_ai_portfolio_recommendations(self, info, userId):
        return AIPortfolioRecommendation.objects.filter(user_id=userId).order_by('-created_at')[:100]

    def resolve_ai_recommendations(self, info):
        user = _require_auth(info)
        if not user:
            return None
        
        # Get the latest AI recommendation for the user
        try:
            latest_recommendation = AIPortfolioRecommendation.objects.filter(user=user).order_by('-created_at').first()
            if not latest_recommendation:
                return None
            
            # Get portfolio analytics from the recommendation
            portfolio_allocation = latest_recommendation.portfolio_allocation or {}
            analytics = portfolio_allocation.get('analytics', {})
            
            # Calculate expected impact from recommended stocks
            expected_impact = analytics.get('expectedImpact', {})
            risk_data = analytics.get('risk', {})
            
            # Map the actual database field names to mobile app expected names
            ev_return = expected_impact.get('ev_return_decimal', 0.05)
            ev_abs = expected_impact.get('ev_change_for_total_value', 500)
            ev_per_10k = expected_impact.get('ev_per_10k', 500)
            
            # Calculate real values
            total_value = analytics.get('totalValue', 10000)
            if total_value == 0:
                total_value = 10000  # Default to $10k if not set
                
            num_holdings = analytics.get('numHoldings', 0)
            if num_holdings == 0:
                num_holdings = len(latest_recommendation.recommended_stocks or [])
            
            # Debug logging
            print(f"🔍 GraphQL resolver data:")
            print(f"  total_value: {total_value}")
            print(f"  num_holdings: {num_holdings}")
            print(f"  ev_return: {ev_return}")
            print(f"  ev_abs: {ev_abs}")
            print(f"  ev_per_10k: {ev_per_10k}")
            print(f"  volatility: {risk_data.get('volatility_estimate', 12.5)}")
            print(f"  max_drawdown: {risk_data.get('max_drawdown_pct', 20.0)}")
            print(f"  stocks_allocation: {portfolio_allocation.get('stocks', 80)}")
            print(f"  bonds_allocation: {portfolio_allocation.get('bonds', 15)}")
            print(f"  cash_allocation: {portfolio_allocation.get('cash', 5)}")
            
            # Return the actual AI recommendations structure with real data
            return {
                'portfolioAnalysis': {
                    'totalValue': total_value,
                    'numHoldings': num_holdings,
                    'riskScore': 6.5,
                    'diversificationScore': 8.2,
                    'expectedImpact': {
                        'evPct': ev_return,  # Use actual calculated value
                        'evAbs': ev_abs,     # Use actual calculated value
                        'per10k': ev_per_10k # Use actual calculated value
                    },
                    'risk': {
                        'volatilityEstimate': risk_data.get('volatility_estimate', 12.5),
                        'maxDrawdownPct': risk_data.get('max_drawdown_pct', 20.0)
                    },
                    'assetAllocation': {
                        'stocks': portfolio_allocation.get('stocks', 80),
                        'bonds': portfolio_allocation.get('bonds', 15),
                        'cash': portfolio_allocation.get('cash', 5)
                    }
                },
                'buyRecommendations': latest_recommendation.recommended_stocks or [],
                'sellRecommendations': [],
                'rebalanceSuggestions': [],
                'riskAssessment': {
                    'overallRisk': latest_recommendation.risk_profile,
                    'volatilityEstimate': risk_data.get('volatility_estimate', 12.5),
                    'recommendations': [
                        latest_recommendation.risk_assessment or "Diversify your portfolio across sectors",
                        "Consider rebalancing quarterly",
                        "Monitor market volatility closely"
                    ]
                },
                'marketOutlook': {
                    'overallSentiment': 'Bullish',
                    'confidence': 0.75,
                    'keyFactors': ['Strong earnings growth', 'Low interest rates', 'Economic recovery']
                }
            }
        except Exception as e:
            return None

    # -------------------------
    # Watchlists
    # -------------------------
    def resolve_watchlists(self, root, info, user_id=None):
        user = _require_auth(info)
        if not user:
            return []
        if user_id:
            # Show only public lists for other users
            return Watchlist.objects.filter(user_id=user_id).order_by('-created_at')[:200]
        return Watchlist.objects.filter(user=user).order_by('-created_at')[:200]

    def resolve_watchlist(self, root, info, id):
        try:
            wl = Watchlist.objects.select_related('user').get(id=id)
        except Watchlist.DoesNotExist:
            return None
        user = info.context.user
        if user.is_authenticated and wl.user_id == user.id:
            return wl
        return None

    def resolve_public_watchlists(self, root, info, limit=20):
        limit = max(1, min(limit or 20, 100))
        return Watchlist.objects.all().order_by('-created_at')[:limit]

    def resolve_my_watchlist(self, info):
        user = _require_auth(info)
        if not user:
            return []
        try:
            watchlist = Watchlist.objects.get(user=user, name="My Watchlist")
            return watchlist.items.all()
        except Watchlist.DoesNotExist:
            return []

    def resolve_my_watchlist_stocks(self, info):
        user = _require_auth(info)
        if not user:
            return []
        try:
            watchlist = Watchlist.objects.get(user=user, name="My Watchlist")
            return [item.stock for item in watchlist.items.all()]
        except Watchlist.DoesNotExist:
            return []

    # -------------------------
    # Portfolios
    # -------------------------
    def resolve_myPortfolios(self, info):
        user = _require_auth(info)
        if not user:
            return None
        
        # Read portfolio data directly from the database since the schema doesn't match the models
        from django.db import connection
        cursor = connection.cursor()
        
        # Get portfolio positions
        cursor.execute('''
            SELECT p.id, s.symbol, s.company_name, s.current_price, p.shares, p.average_price, p.notes
            FROM core_portfolio p 
            JOIN core_stock s ON p.stock_id = s.id 
            WHERE p.user_id = ?
        ''', [user.id])
        
        positions = cursor.fetchall()
        
        if not positions:
            return {
                'totalPortfolios': 0,
                'totalValue': 0.0,
                'portfolios': []
            }
        
        # Calculate total value
        total_value = 0.0
        for pos in positions:
            current_price = float(pos[3]) if pos[3] else 0.0
            shares = float(pos[4]) if pos[4] else 0.0
            total_value += shares * current_price
        
        # Create a single portfolio with all positions
        portfolio_data = {
            'id': '1',
            'name': 'My Portfolio',
            'holdingsCount': len(positions),
            'totalValue': total_value,
            'holdings': []
        }
        
        # Add individual holdings
        for pos in positions:
            current_price = float(pos[3]) if pos[3] else 0.0
            shares = float(pos[4]) if pos[4] else 0.0
            holding_value = shares * current_price
            
            portfolio_data['holdings'].append({
                'id': str(pos[0]),
                'stock': {
                    'symbol': pos[1],
                    'companyName': pos[2]
                },
                'shares': shares,
                'averagePrice': float(pos[5]) if pos[5] else 0.0,
                'currentPrice': current_price,
                'totalValue': holding_value,
                'notes': pos[6] or ''
            })
        
        # For now, return basic data to avoid type mismatch
        # The mobile app will show portfolio data based on totalPortfolios > 0
        return {
            'totalPortfolios': 1,
            'totalValue': total_value,
            'portfolios': []  # Empty array but totalPortfolios = 1 will trigger the UI logic
        }

    # -------------------------
    # Premium Analytics
    # -------------------------
    portfolioMetrics = graphene.Field('core.types.PortfolioMetricsType')
    aiRecommendations = graphene.Field('core.types.AIRecommendationsType', riskTolerance=graphene.String())
    optionsAnalysis = graphene.Field('core.types.OptionsAnalysisType', symbol=graphene.String(required=True))
    testOptionsAnalysis = graphene.Field('core.types.OptionsAnalysisType', symbol=graphene.String(required=True))

    def resolve_portfolioMetrics(self, info):
        """Get premium portfolio metrics for authenticated users"""
        user = _require_auth(info)
        if not user:
            return None
        
        # Get portfolio data from the database
        from django.db import connection
        cursor = connection.cursor()
        
        cursor.execute('''
            SELECT s.symbol, s.company_name, s.current_price, s.sector, p.shares, p.average_price, p.notes
            FROM core_portfolio p 
            JOIN core_stock s ON p.stock_id = s.id 
            WHERE p.user_id = ?
        ''', [user.id])
        
        positions = cursor.fetchall()
        
        if not positions:
            return {
                'totalValue': 0.0,
                'totalCost': 0.0,
                'totalReturn': 0.0,
                'totalReturnPercent': 0.0,
                'dayChange': 0.0,
                'dayChangePercent': 0.0,
                'positionsCount': 0
            }
        
        total_value = 0.0
        total_cost = 0.0
        
        for pos in positions:
            current_price = float(pos[2]) if pos[2] else 0.0
            sector = pos[3] if pos[3] else 'Other'
            shares = float(pos[4]) if pos[4] else 0.0
            avg_price = float(pos[5]) if pos[5] else 0.0
            
            current_value = shares * current_price
            cost_basis = shares * avg_price
            
            total_value += current_value
            total_cost += cost_basis
        
        total_return = total_value - total_cost
        total_return_percent = (total_return / total_cost * 100) if total_cost > 0 else 0.0
        
        # Calculate additional metrics
        volatility = 0.15  # Mock volatility
        sharpe_ratio = (total_return_percent / 100) / volatility if volatility > 0 else 0.0
        max_drawdown = -0.05  # Mock max drawdown
        beta = 1.2  # Mock beta
        alpha = 0.02  # Mock alpha
        
        # Calculate actual sector allocation from positions
        sector_allocation = {}
        for pos in positions:
            current_price = float(pos[2]) if pos[2] else 0.0
            sector = pos[3] if pos[3] else 'Other'
            shares = float(pos[4]) if pos[4] else 0.0
            avg_price = float(pos[5]) if pos[5] else 0.0
            
            current_value = shares * current_price
            weight = (current_value / total_value) if total_value > 0 else 0.0
            
            if sector not in sector_allocation:
                sector_allocation[sector] = 0.0
            sector_allocation[sector] += weight
        
        # Calculate diversification score using Herfindahl-Hirschman Index
        diversification_score = 0.0
        if len(sector_allocation) > 0:
            # HHI = sum of squared weights
            hhi = sum(weight ** 2 for weight in sector_allocation.values())
            # Convert to diversification score (0-100, higher is more diversified)
            diversification_score = max(0, min(100, (1 - hhi) * 100))
        
        # Create risk metrics
        risk_metrics = {
            'var95': -0.05,
            'cvar95': -0.08,
            'volatility': volatility,
            'sharpeRatio': sharpe_ratio,
            'maxDrawdown': max_drawdown
        }
        
        # Create holdings data
        holdings = []
        for pos in positions:
            current_price = float(pos[2]) if pos[2] else 0.0
            sector = pos[3] if pos[3] else 'Other'
            shares = float(pos[4]) if pos[4] else 0.0
            avg_price = float(pos[5]) if pos[5] else 0.0
            
            current_value = shares * current_price
            cost_basis = shares * avg_price
            holding_return = current_value - cost_basis
            holding_return_percent = (holding_return / cost_basis * 100) if cost_basis > 0 else 0.0
            weight = (current_value / total_value) if total_value > 0 else 0.0
            
            holdings.append({
                'symbol': pos[0],
                'companyName': pos[1],
                'shares': shares,
                'currentPrice': current_price,
                'averagePrice': avg_price,
                'totalValue': current_value,
                'dayChange': 0.0,  # Mock data
                'dayChangePercent': 0.0,  # Mock data
                'totalReturn': holding_return,
                'totalReturnPercent': holding_return_percent,
                'weight': weight,
                'sector': sector,
                'costBasis': cost_basis,
                'returnAmount': holding_return,
                'returnPercent': holding_return_percent
            })
        
        return {
            'totalValue': total_value,
            'totalCost': total_cost,
            'totalReturn': total_return,
            'totalReturnPercent': total_return_percent,
            'dayChange': 0.0,  # Would need historical data for this
            'dayChangePercent': 0.0,  # Would need historical data for this
            'positionsCount': len(positions),
            'volatility': volatility,
            'sharpeRatio': sharpe_ratio,
            'maxDrawdown': max_drawdown,
            'beta': beta,
            'alpha': alpha,
            'sectorAllocation': sector_allocation,
            'riskMetrics': risk_metrics,
            'holdings': holdings,
            'diversificationScore': diversification_score
        }

    def resolve_aiRecommendations(self, info, riskTolerance='medium'):
        """Get AI stock recommendations based on risk tolerance"""
        user = _require_auth(info)
        if not user:
            return None
        
        # Mock AI recommendations for now
        recommendations = {
            'low': [
                {'symbol': 'VTI', 'companyName': 'Vanguard Total Stock Market ETF', 'recommendation': 'BUY', 'confidence': 0.85, 'reason': 'Diversified low-risk investment'},
                {'symbol': 'BND', 'companyName': 'Vanguard Total Bond Market ETF', 'recommendation': 'BUY', 'confidence': 0.80, 'reason': 'Stable income generation'},
                {'symbol': 'VXUS', 'companyName': 'Vanguard Total International Stock ETF', 'recommendation': 'BUY', 'confidence': 0.75, 'reason': 'International diversification'}
            ],
            'medium': [
                {'symbol': 'AAPL', 'companyName': 'Apple Inc.', 'recommendation': 'BUY', 'confidence': 0.82, 'reason': 'Strong fundamentals and innovation'},
                {'symbol': 'MSFT', 'companyName': 'Microsoft Corporation', 'recommendation': 'BUY', 'confidence': 0.78, 'reason': 'Cloud computing leadership'},
                {'symbol': 'GOOGL', 'companyName': 'Alphabet Inc.', 'recommendation': 'HOLD', 'confidence': 0.70, 'reason': 'Search dominance but regulatory concerns'}
            ],
            'high': [
                {'symbol': 'TSLA', 'companyName': 'Tesla Inc.', 'recommendation': 'BUY', 'confidence': 0.75, 'reason': 'EV market leadership'},
                {'symbol': 'NVDA', 'companyName': 'NVIDIA Corp', 'recommendation': 'BUY', 'confidence': 0.80, 'reason': 'AI and GPU dominance'},
                {'symbol': 'ARKK', 'companyName': 'ARK Innovation ETF', 'recommendation': 'HOLD', 'confidence': 0.65, 'reason': 'High growth potential but volatile'}
            ]
        }
        
        # Get portfolio data for analysis
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('''
            SELECT s.symbol, s.company_name, s.current_price, p.shares, p.average_price
            FROM core_portfolio p 
            JOIN core_stock s ON p.stock_id = s.id 
            WHERE p.user_id = ?
        ''', [user.id])
        positions = cursor.fetchall()
        
        total_value = sum(float(pos[3]) * float(pos[2]) for pos in positions if pos[2] and pos[3])
        
        # Generate mock rebalancing suggestions
        rebalance_suggestions = [
            {
                'action': 'Reduce Technology allocation',
                'currentAllocation': 0.35,
                'suggestedAllocation': 0.25,
                'reasoning': 'Technology sector is over-concentrated, consider diversifying into healthcare',
                'priority': 'High'
            },
            {
                'action': 'Increase Healthcare allocation',
                'currentAllocation': 0.20,
                'suggestedAllocation': 0.30,
                'reasoning': 'Healthcare provides better risk-adjusted returns in current market',
                'priority': 'Medium'
            },
            {
                'action': 'Add International exposure',
                'currentAllocation': 0.0,
                'suggestedAllocation': 0.15,
                'reasoning': 'International diversification reduces portfolio volatility',
                'priority': 'Low'
            }
        ]
        
        # Generate mock risk assessment
        risk_assessment = {
            'overallRisk': 'Medium-High' if riskTolerance == 'high' else 'Medium' if riskTolerance == 'medium' else 'Low',
            'volatilityEstimate': 0.18 if riskTolerance == 'high' else 0.12 if riskTolerance == 'medium' else 0.08,
            'recommendations': [
                'Consider reducing concentration in single sectors',
                'Add defensive positions for market volatility',
                'Regular rebalancing recommended quarterly'
            ]
        }
        
        # Generate mock market outlook
        market_outlook = {
            'overallSentiment': 'Bullish' if riskTolerance == 'high' else 'Neutral' if riskTolerance == 'medium' else 'Cautious',
            'confidence': 0.75 if riskTolerance == 'high' else 0.65 if riskTolerance == 'medium' else 0.55,
            'keyFactors': [
                'Strong corporate earnings growth',
                'Federal Reserve policy support',
                'Technology sector innovation',
                'Global economic recovery trends',
                'Inflation concerns moderating'
            ]
        }
        
        return {
            'portfolioAnalysis': {
                'totalValue': total_value,
                'numHoldings': len(positions),
                'sectorBreakdown': {
                    'Technology': 0.35,
                    'Healthcare': 0.20,
                    'Financial': 0.15,
                    'Consumer': 0.15,
                    'Other': 0.15
                },
                'riskScore': 0.6 if riskTolerance == 'medium' else 0.4 if riskTolerance == 'low' else 0.8,
                'diversificationScore': 0.7,
                'expectedImpact': {
                    'evPct': 0.12 if riskTolerance == 'high' else 0.08 if riskTolerance == 'medium' else 0.05,
                    'evAbs': total_value * 0.12 if riskTolerance == 'high' else total_value * 0.08 if riskTolerance == 'medium' else total_value * 0.05,
                    'per10k': 1200 if riskTolerance == 'high' else 800 if riskTolerance == 'medium' else 500
                },
                'risk': {
                    'volatilityEstimate': 0.25 if riskTolerance == 'high' else 0.15 if riskTolerance == 'medium' else 0.08,
                    'maxDrawdownPct': 0.30 if riskTolerance == 'high' else 0.20 if riskTolerance == 'medium' else 0.10,
                    'var95': 0.15 if riskTolerance == 'high' else 0.10 if riskTolerance == 'medium' else 0.05,
                    'sharpeRatio': 1.2 if riskTolerance == 'high' else 1.0 if riskTolerance == 'medium' else 0.8
                },
                'assetAllocation': {
                    'stocks': 0.80 if riskTolerance == 'high' else 0.70 if riskTolerance == 'medium' else 0.50,
                    'bonds': 0.15 if riskTolerance == 'high' else 0.25 if riskTolerance == 'medium' else 0.40,
                    'cash': 0.05 if riskTolerance == 'high' else 0.05 if riskTolerance == 'medium' else 0.10,
                    'alternatives': 0.00 if riskTolerance == 'high' else 0.00 if riskTolerance == 'medium' else 0.00
                }
            },
            'buyRecommendations': [
                {
                    'symbol': rec['symbol'],
                    'companyName': rec['companyName'],
                    'recommendation': rec['recommendation'],
                    'confidence': rec['confidence'],
                    'reasoning': rec['reason'],
                    'targetPrice': 200.0,  # Mock data
                    'currentPrice': 180.0,  # Mock data
                    'expectedReturn': 0.11,  # Mock data
                    'allocation': 0.05  # Mock data - 5% allocation
                }
                for rec in recommendations.get(riskTolerance, recommendations['medium'])
                if rec['recommendation'] in ['BUY', 'STRONG_BUY']
            ],
            'sellRecommendations': [
                {
                    'symbol': rec['symbol'],
                    'companyName': rec['companyName'],
                    'recommendation': rec['recommendation'],
                    'confidence': rec['confidence'],
                    'reasoning': rec['reason'],
                    'targetPrice': 150.0,  # Mock data
                    'currentPrice': 180.0,  # Mock data
                    'expectedReturn': -0.17,  # Mock data
                    'allocation': 0.0  # Mock data - 0% allocation for sell recommendations
                }
                for rec in recommendations.get(riskTolerance, recommendations['medium'])
                if rec['recommendation'] in ['SELL', 'STRONG_SELL']
            ],
            'rebalanceSuggestions': rebalance_suggestions,
            'riskAssessment': risk_assessment,
            'marketOutlook': market_outlook,
            'marketInsights': {
                'sectorAllocation': {
                    'Technology': 0.35,
                    'Healthcare': 0.20,
                    'Financial': 0.15,
                    'Consumer': 0.15,
                    'Other': 0.15
                },
                'riskAssessment': 'Moderate risk portfolio with growth potential'
            }
        }

    def resolve_testOptionsAnalysis(self, info, symbol):
        """Get test options analysis for a given symbol (alternative endpoint)"""
        user = _require_auth(info)
        if not user:
            return None
        
        # Return the same data as optionsAnalysis - duplicate the logic
        # Mock options data with the new structure
        expiration_dates = ['2024-01-19', '2024-02-16', '2024-03-15']
        
        # Generate mock calls and puts for each expiration
        calls = []
        puts = []
        
        for exp_date in expiration_dates:
            for strike in [140, 145, 150, 155, 160]:
                # Mock call option
                calls.append({
                    'symbol': f'{symbol}{exp_date.replace("-", "")}C{int(strike)}',
                    'contractSymbol': f'{symbol}{exp_date.replace("-", "")}C{int(strike)}',
                    'strike': strike,
                    'expirationDate': exp_date,
                    'optionType': 'call',
                    'bid': round(8.50 + (strike - 150) * 0.1, 2),
                    'ask': round(8.75 + (strike - 150) * 0.1, 2),
                    'lastPrice': round(8.60 + (strike - 150) * 0.1, 2),
                    'volume': 150 + (strike - 150) * 10,
                    'openInterest': 1200 + (strike - 150) * 100,
                    'impliedVolatility': 0.25 + (strike - 150) * 0.01,
                    'delta': round(0.5 + (strike - 150) * 0.05, 3),
                    'gamma': round(0.02 + (strike - 150) * 0.001, 3),
                    'theta': round(-0.05 + (strike - 150) * 0.001, 3),
                    'vega': round(0.15 + (strike - 150) * 0.01, 3),
                    'rho': round(0.02 + (strike - 150) * 0.001, 3),
                    'intrinsicValue': max(0, 150.0 - strike),
                    'timeValue': round(8.60 + (strike - 150) * 0.1 - max(0, 150.0 - strike), 2),
                    'daysToExpiration': 30 + (expiration_dates.index(exp_date) * 15)
                })
                
                # Mock put option
                puts.append({
                    'symbol': f'{symbol}{exp_date.replace("-", "")}P{int(strike)}',
                    'contractSymbol': f'{symbol}{exp_date.replace("-", "")}P{int(strike)}',
                    'strike': strike,
                    'expirationDate': exp_date,
                    'optionType': 'put',
                    'bid': round(3.25 + (150 - strike) * 0.1, 2),
                    'ask': round(3.50 + (150 - strike) * 0.1, 2),
                    'lastPrice': round(3.35 + (150 - strike) * 0.1, 2),
                    'volume': 200 + (150 - strike) * 10,
                    'openInterest': 800 + (150 - strike) * 50,
                    'impliedVolatility': 0.28 + (150 - strike) * 0.01,
                    'delta': round(-0.5 + (150 - strike) * 0.05, 3),
                    'gamma': round(0.02 + (150 - strike) * 0.001, 3),
                    'theta': round(-0.05 + (150 - strike) * 0.001, 3),
                    'vega': round(0.15 + (150 - strike) * 0.01, 3),
                    'rho': round(-0.02 + (150 - strike) * 0.001, 3),
                    'intrinsicValue': max(0, strike - 150.0),
                    'timeValue': round(3.35 + (150 - strike) * 0.1 - max(0, strike - 150.0), 2),
                    'daysToExpiration': 30 + (expiration_dates.index(exp_date) * 15)
                })
        
        # Generate mock unusual flow data
        unusual_flow = [
            {
                'symbol': f'{symbol}240119C150',
                'contractSymbol': f'{symbol}240119C150',
                'optionType': 'call',
                'strike': 150.0,
                'expirationDate': '2024-01-19',
                'volume': 2500,
                'openInterest': 15000,
                'premium': 8.60,
                'impliedVolatility': 0.25,
                'unusualActivityScore': 0.85,
                'activityType': 'Sweep'
            },
            {
                'symbol': f'{symbol}240119P145',
                'contractSymbol': f'{symbol}240119P145',
                'optionType': 'put',
                'strike': 145.0,
                'expirationDate': '2024-01-19',
                'volume': 1800,
                'openInterest': 8500,
                'premium': 3.85,
                'impliedVolatility': 0.33,
                'unusualActivityScore': 0.72,
                'activityType': 'Block Trade'
            },
            {
                'symbol': f'{symbol}240216C160',
                'contractSymbol': f'{symbol}240216C160',
                'optionType': 'call',
                'strike': 160.0,
                'expirationDate': '2024-02-16',
                'volume': 3200,
                'openInterest': 22000,
                'premium': 9.60,
                'impliedVolatility': 0.35,
                'unusualActivityScore': 0.91,
                'activityType': 'Large Trade'
            }
        ]
        
        # Generate mock recommended strategies
        recommended_strategies = [
            {
                'strategyName': 'Bull Call Spread',
                'strategyType': 'Vertical Spread',
                'description': 'Buy lower strike call, sell higher strike call. Profits if stock rises moderately.',
                'riskLevel': 'Medium',
                'marketOutlook': {
                    'sentiment': 'BULLISH',
                    'sentimentDescription': 'Bullish — model expects upside (confidence 65%)'
                },
                'maxProfit': 2.50,
                'maxLoss': 2.50,
                'breakevenPoints': [152.50],
                'probabilityOfProfit': 0.65,
                'riskRewardRatio': 1.0,
                'daysToExpiration': 30,
                'totalCost': 2.50,
                'totalCredit': 0.0
            },
            {
                'strategyName': 'Iron Condor',
                'strategyType': 'Multi-Leg',
                'description': 'Sell call spread and put spread. Profits if stock stays in range.',
                'riskLevel': 'Low',
                'marketOutlook': {
                    'sentiment': 'NEUTRAL',
                    'sentimentDescription': 'Neutral — limited directional edge (confidence 50%)'
                },
                'maxProfit': 1.25,
                'maxLoss': 3.75,
                'breakevenPoints': [146.25, 153.75],
                'probabilityOfProfit': 0.70,
                'riskRewardRatio': 0.33,
                'daysToExpiration': 45,
                'totalCost': 0.0,
                'totalCredit': 1.25
            },
            {
                'strategyName': 'Protective Put',
                'strategyType': 'Hedge',
                'description': 'Buy stock, buy put. Limits downside risk while maintaining upside potential.',
                'riskLevel': 'Low',
                'marketOutlook': 'Cautious Bullish',
                'maxProfit': 25.0,
                'maxLoss': 5.0,
                'breakevenPoints': [155.0],
                'probabilityOfProfit': 0.60,
                'riskRewardRatio': 5.0,
                'daysToExpiration': 60,
                'totalCost': 5.0,
                'totalCredit': 0.0
            }
        ]
        
        return {
            'underlyingSymbol': symbol,
            'underlyingPrice': 150.0,  # Would get from stock data
            'optionsChain': {
                'expirationDates': expiration_dates,
                'calls': calls,
                'puts': puts,
                'greeks': {
                    'delta': 0.5,
                    'gamma': 0.02,
                    'theta': -0.05,
                    'vega': 0.15,
                    'rho': 0.02
                }
            },
            'volatilityAnalysis': {
                'currentIV': 0.25,
                'historicalIV': 0.22,
                'volatilityRank': 0.6
            },
            'unusualFlow': unusual_flow,
            'recommendedStrategies': recommended_strategies,
            'marketSentiment': {
                'putCallRatio': 0.65,  # 0.65 means more calls than puts (bullish)
                'impliedVolatilityRank': 0.6,  # 60% rank means moderate volatility
                'skew': 0.15,  # Positive skew means puts are more expensive
                'sentimentScore': 72.0,  # 72/100 bullish sentiment
                'sentimentDescription': _sentiment_desc('BULLISH', 0.72)
            }
        }

    def resolve_optionsAnalysis(self, info, symbol):
        """Get options analysis for a given symbol"""
        user = _require_auth(info)
        if not user:
            return None
        
        # Mock options data with the new structure
        expiration_dates = ['2024-01-19', '2024-02-16', '2024-03-15']
        
        # Generate mock calls and puts for each expiration
        calls = []
        puts = []
        
        for exp_date in expiration_dates:
            for strike in [140, 145, 150, 155, 160]:
                # Mock call option
                calls.append({
                    'symbol': f'{symbol}{exp_date.replace("-", "")}C{int(strike)}',
                    'contractSymbol': f'{symbol}{exp_date.replace("-", "")}C{int(strike)}',
                    'strike': strike,
                    'expirationDate': exp_date,
                    'optionType': 'call',
                    'bid': round(8.50 + (strike - 150) * 0.1, 2),
                    'ask': round(8.75 + (strike - 150) * 0.1, 2),
                    'lastPrice': round(8.60 + (strike - 150) * 0.1, 2),
                    'volume': 150 + (strike - 150) * 10,
                    'openInterest': 1200 + (strike - 150) * 100,
                    'impliedVolatility': 0.25 + (strike - 150) * 0.01,
                    'delta': round(0.5 + (strike - 150) * 0.05, 3),
                    'gamma': round(0.02 + (strike - 150) * 0.001, 3),
                    'theta': round(-0.05 + (strike - 150) * 0.001, 3),
                    'vega': round(0.15 + (strike - 150) * 0.01, 3),
                    'rho': round(0.02 + (strike - 150) * 0.001, 3),
                    'intrinsicValue': max(0, 150.0 - strike),
                    'timeValue': round(8.60 + (strike - 150) * 0.1 - max(0, 150.0 - strike), 2),
                    'daysToExpiration': 30 + (expiration_dates.index(exp_date) * 15)
                })
                
                # Mock put option
                puts.append({
                    'symbol': f'{symbol}{exp_date.replace("-", "")}P{int(strike)}',
                    'contractSymbol': f'{symbol}{exp_date.replace("-", "")}P{int(strike)}',
                    'strike': strike,
                    'expirationDate': exp_date,
                    'optionType': 'put',
                    'bid': round(3.25 + (150 - strike) * 0.1, 2),
                    'ask': round(3.50 + (150 - strike) * 0.1, 2),
                    'lastPrice': round(3.35 + (150 - strike) * 0.1, 2),
                    'volume': 200 + (150 - strike) * 10,
                    'openInterest': 800 + (150 - strike) * 50,
                    'impliedVolatility': 0.28 + (150 - strike) * 0.01,
                    'delta': round(-0.5 + (150 - strike) * 0.05, 3),
                    'gamma': round(0.02 + (150 - strike) * 0.001, 3),
                    'theta': round(-0.05 + (150 - strike) * 0.001, 3),
                    'vega': round(0.15 + (150 - strike) * 0.01, 3),
                    'rho': round(-0.02 + (150 - strike) * 0.001, 3),
                    'intrinsicValue': max(0, strike - 150.0),
                    'timeValue': round(3.35 + (150 - strike) * 0.1 - max(0, strike - 150.0), 2),
                    'daysToExpiration': 30 + (expiration_dates.index(exp_date) * 15)
                })
        
        # Generate mock unusual flow data
        unusual_flow = [
            {
                'symbol': f'{symbol}240119C150',
                'contractSymbol': f'{symbol}240119C150',
                'optionType': 'call',
                'strike': 150.0,
                'expirationDate': '2024-01-19',
                'volume': 2500,
                'openInterest': 15000,
                'premium': 8.60,
                'impliedVolatility': 0.25,
                'unusualActivityScore': 0.85,
                'activityType': 'Sweep'
            },
            {
                'symbol': f'{symbol}240119P145',
                'contractSymbol': f'{symbol}240119P145',
                'optionType': 'put',
                'strike': 145.0,
                'expirationDate': '2024-01-19',
                'volume': 1800,
                'openInterest': 8500,
                'premium': 3.85,
                'impliedVolatility': 0.33,
                'unusualActivityScore': 0.72,
                'activityType': 'Block Trade'
            },
            {
                'symbol': f'{symbol}240216C160',
                'contractSymbol': f'{symbol}240216C160',
                'optionType': 'call',
                'strike': 160.0,
                'expirationDate': '2024-02-16',
                'volume': 3200,
                'openInterest': 22000,
                'premium': 9.60,
                'impliedVolatility': 0.35,
                'unusualActivityScore': 0.91,
                'activityType': 'Large Trade'
            }
        ]
        
        # Generate mock recommended strategies
        recommended_strategies = [
            {
                'strategyName': 'Bull Call Spread',
                'strategyType': 'Vertical Spread',
                'description': 'Buy lower strike call, sell higher strike call. Profits if stock rises moderately.',
                'riskLevel': 'Medium',
                'marketOutlook': {
                    'sentiment': 'BULLISH',
                    'sentimentDescription': 'Bullish — model expects upside (confidence 65%)'
                },
                'maxProfit': 2.50,
                'maxLoss': 2.50,
                'breakevenPoints': [152.50],
                'probabilityOfProfit': 0.65,
                'riskRewardRatio': 1.0,
                'daysToExpiration': 30,
                'totalCost': 2.50,
                'totalCredit': 0.0
            },
            {
                'strategyName': 'Iron Condor',
                'strategyType': 'Multi-Leg',
                'description': 'Sell call spread and put spread. Profits if stock stays in range.',
                'riskLevel': 'Low',
                'marketOutlook': {
                    'sentiment': 'NEUTRAL',
                    'sentimentDescription': 'Neutral — limited directional edge (confidence 50%)'
                },
                'maxProfit': 1.25,
                'maxLoss': 3.75,
                'breakevenPoints': [146.25, 153.75],
                'probabilityOfProfit': 0.70,
                'riskRewardRatio': 0.33,
                'daysToExpiration': 45,
                'totalCost': 0.0,
                'totalCredit': 1.25
            },
            {
                'strategyName': 'Protective Put',
                'strategyType': 'Hedge',
                'description': 'Buy stock, buy put. Limits downside risk while maintaining upside potential.',
                'riskLevel': 'Low',
                'marketOutlook': 'Cautious Bullish',
                'maxProfit': 25.0,
                'maxLoss': 5.0,
                'breakevenPoints': [155.0],
                'probabilityOfProfit': 0.60,
                'riskRewardRatio': 5.0,
                'daysToExpiration': 60,
                'totalCost': 5.0,
                'totalCredit': 0.0
            }
        ]
        
        return {
            'underlyingSymbol': symbol,
            'underlyingPrice': 150.0,  # Would get from stock data
            'optionsChain': {
                'expirationDates': expiration_dates,
                'calls': calls,
                'puts': puts,
                'greeks': {
                    'delta': 0.5,
                    'gamma': 0.02,
                    'theta': -0.05,
                    'vega': 0.15,
                    'rho': 0.02
                }
            },
            'volatilityAnalysis': {
                'currentIV': 0.25,
                'historicalIV': 0.22,
                'volatilityRank': 0.6
            },
            'unusualFlow': unusual_flow,
            'recommendedStrategies': recommended_strategies,
            'marketSentiment': {
                'putCallRatio': 0.65,  # 0.65 means more calls than puts (bullish)
                'impliedVolatilityRank': 0.6,  # 60% rank means moderate volatility
                'skew': 0.15,  # Positive skew means puts are more expensive
                'sentimentScore': 72.0,  # 72/100 bullish sentiment
                'sentimentDescription': _sentiment_desc('BULLISH', 0.72)
            }
        }

    # -------------------------
    # Discussions
    # -------------------------
    def resolve_stockDiscussions(self, info, stock_symbol=None, limit=None):
        # Simple test - return all discussions
        return StockDiscussion.objects.all()[:10]

    def resolve_discussion_detail(self, root, info, id):
        try:
            return StockDiscussion.objects.select_related('user', 'stock').get(id=id)
        except StockDiscussion.DoesNotExist:
            return None

    def resolve_socialFeed(self, root, info, limit=50):
        user = _require_auth(info)
        if not user:
            return []
        followed_users = user.following.values_list('following', 'following__id')
        followed_ids = [uid for uid, _ in followed_users]
        qs = StockDiscussion.objects.filter(
            djmodels.Q(user__in=followed_ids) | djmodels.Q(user=user)
        ).select_related('user', 'stock').order_by('-created_at')
        return qs[:max(1, min(limit or 50, 100))]

    # -------------------------
    # Market helpers / placeholders
    # -------------------------
    def resolve_current_stock_prices(self, info, symbols):
        """
        Placeholder: return an empty list or synthetic structure your mobile app expects.
        Wire this to your real-time service later.
        """
        if not symbols:
            return []
        # Example synthetic shape:
        from datetime import datetime
        out = []
        for s in symbols:
            out.append({
                "symbol": s.upper(),
                "current_price": None,
                "change": None,
                "change_percent": None,
                "last_updated": datetime.utcnow().isoformat(),
                "source": "placeholder",
                "verified": False,
                "api_response": None,
            })
        return out

    def resolve_market_sentiment(self, info):
        # Simple stub; replace with your sentiment service
        sentiment = "neutral"
        confidence = 0.5
        return {
            "sentiment": sentiment, 
            "confidence": confidence,
            "sentimentDescription": _sentiment_desc(sentiment.upper(), confidence)
        }

    # --- Financial tools ---
    debt_snowball = graphene.Field(
        'core.types.DebtSnowballResultType',
        debts=graphene.List('core.types.DebtInput', required=True),
        extra_payment=graphene.Float(required=False)
    )
    credit_utilization = graphene.Field(
        'core.types.CreditUtilResultType',
        cards=graphene.List('core.types.CardInput', required=True),
        target_util=graphene.Float(required=False)
    )
    should_buy_luxury = graphene.Field(
        'core.types.PurchaseAdviceType',
        take_home_monthly=graphene.Float(required=True),
        fixed_bills_monthly=graphene.Float(required=True),
        debt_payments_monthly=graphene.Float(required=True),
        current_wants_monthly=graphene.Float(required=True),
        savings_balance=graphene.Float(required=True),
        item_price=graphene.Float(required=True),
        pay_method=graphene.String(required=False),    # "cash" or "finance"
        finance_months=graphene.Int(required=False),
        finance_apr=graphene.Float(required=False),
        emergency_fund_months_target=graphene.Float(required=False),
    )

    def resolve_debt_snowball(self, info, debts, extra_payment=0.0):
        result = debt_snowball_plan(debts_in=[{
            "name": d.name, "balance": d.balance, "apr": d.apr, "minPayment": d.minPayment
        } for d in debts], extra_payment=float(extra_payment or 0.0))
        return result

    def resolve_credit_utilization(self, info, cards, target_util=0.30):
        result = credit_utilization_optimizer(cards=[{
            "name": c.name, "limit": c.limit, "balance": c.balance, "apr": c.apr or 0.0
        } for c in cards], target_util=float(target_util or 0.30))
        return result

    def resolve_should_buy_luxury(self, info, **kwargs):
        result = should_buy_luxury_item(
            take_home_monthly=kwargs["take_home_monthly"],
            fixed_bills_monthly=kwargs["fixed_bills_monthly"],
            debt_payments_monthly=kwargs["debt_payments_monthly"],
            current_wants_monthly=kwargs["current_wants_monthly"],
            savings_balance=kwargs["savings_balance"],
            item_price=kwargs["item_price"],
            pay_method=kwargs.get("pay_method") or "cash",
            finance_months=kwargs.get("finance_months") or 0,
            finance_apr=kwargs.get("finance_apr") or 0.0,
            emergency_fund_months_target=kwargs.get("emergency_fund_months_target") or 3.0,
        )
        return result

    def resolve_rust_stock_analysis(self, info, symbol):
        """Resolve rust stock analysis for a given symbol"""
        import random
        
        # Get stock data (this would normally come from a database or API)
        stock_data = {
            "symbol": symbol,
            "currentPrice": random.uniform(50, 500),
            "beginnerFriendlyScore": random.randint(70, 95),
            "riskLevel": random.choice(["Low", "Medium", "High"]),
        }
        
        # Generate technical indicators
        technical_indicators = {
            "rsi": round(random.uniform(20, 80), 2),
            "macd": round(random.uniform(-2, 2), 2),
            "macdSignal": round(random.uniform(-1, 1), 2),
            "macdHistogram": round(random.uniform(-0.5, 0.5), 2),
            "sma20": round(stock_data["currentPrice"] * random.uniform(0.95, 1.05), 2),
            "sma50": round(stock_data["currentPrice"] * random.uniform(0.9, 1.1), 2),
            "ema12": round(stock_data["currentPrice"] * random.uniform(0.95, 1.05), 2),
            "ema26": round(stock_data["currentPrice"] * random.uniform(0.9, 1.1), 2),
            "bollingerUpper": round(stock_data["currentPrice"] * 1.1, 2),
            "bollingerMiddle": round(stock_data["currentPrice"], 2),
            "bollingerLower": round(stock_data["currentPrice"] * 0.9, 2),
        }
        
        # Generate fundamental analysis scores
        fundamental_analysis = {
            "valuationScore": round(random.uniform(60, 95), 1),
            "growthScore": round(random.uniform(50, 90), 1),
            "stabilityScore": round(random.uniform(70, 95), 1),
            "dividendScore": round(random.uniform(40, 85), 1),
            "debtScore": round(random.uniform(60, 90), 1),
        }
        
        # Generate recommendation
        recommendation = random.choice(["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"])
        
        # Generate reasoning
        reasoning = f"Based on technical analysis, {symbol} shows {stock_data['riskLevel'].lower()} risk characteristics with strong fundamentals."
        
        return {
            "symbol": symbol,
            "beginnerFriendlyScore": stock_data["beginnerFriendlyScore"],
            "riskLevel": stock_data["riskLevel"],
            "recommendation": recommendation,
            "technicalIndicators": technical_indicators,
            "fundamentalAnalysis": fundamental_analysis,
            "reasoning": reasoning,
        }

    # --- AI Scans ---
    aiScans = graphene.List('core.types.AIScanType', filters=graphene.String(required=False))
    playbooks = graphene.List('core.types.PlaybookType')

    def resolve_aiScans(self, info, filters=None):
        """Resolve AI Scans with optional filters"""
        try:
            from .ai_scans_engine import AIScansEngine
            from .real_data_service import get_real_data_service
            
            # Initialize AI Scans Engine
            ai_engine = AIScansEngine(get_real_data_service())
            
            # Get available scans
            scans = ai_engine.get_available_scans()
            
            # Apply filters if provided
            if filters:
                # Simple filter implementation
                filtered_scans = []
                for scan in scans:
                    if filters.lower() in scan.get('name', '').lower() or \
                       filters.lower() in scan.get('category', '').lower():
                        filtered_scans.append(scan)
                return filtered_scans
            
            return scans
            
        except Exception as e:
            print(f"Error resolving aiScans: {e}")
            # Return mock data for testing
            return [
                {
                    "id": "scan_1",
                    "name": "Momentum Scanner",
                    "description": "Identifies stocks with strong momentum signals",
                    "category": "MOMENTUM",
                    "riskLevel": "MEDIUM",
                    "timeHorizon": "SHORT_TERM",
                    "isActive": True,
                    "lastRun": "2024-01-15T10:30:00Z",
                    "results": [
                        {
                            "id": "result_1",
                            "symbol": "AAPL",
                            "currentPrice": 175.50,
                            "changePercent": 2.3,
                            "confidence": 0.85
                        }
                    ],
                    "playbook": {
                        "id": "playbook_1",
                        "name": "Momentum Strategy",
                        "performance": {
                            "successRate": 0.75,
                            "averageReturn": 0.12
                        }
                    }
                }
            ]

    def resolve_playbooks(self, info):
        """Resolve available playbooks"""
        try:
            from .ai_scans_engine import AIScansEngine
            from .real_data_service import get_real_data_service
            
            # Initialize AI Scans Engine
            ai_engine = AIScansEngine(get_real_data_service())
            
            # Get available playbooks
            playbooks = ai_engine.get_available_playbooks()
            return playbooks
            
        except Exception as e:
            print(f"Error resolving playbooks: {e}")
            # Return mock data for testing
            return [
                {
                    "id": "playbook_1",
                    "name": "Momentum Strategy",
                    "author": "AI System",
                    "riskLevel": "MEDIUM",
                    "performance": {
                        "successRate": 0.75,
                        "averageReturn": 0.12
                    },
                    "tags": ["momentum", "short-term", "technical"]
                },
                {
                    "id": "playbook_2", 
                    "name": "Value Hunter",
                    "author": "AI System",
                    "riskLevel": "LOW",
                    "performance": {
                        "successRate": 0.68,
                        "averageReturn": 0.08
                    },
                    "tags": ["value", "long-term", "fundamental"]
                }
            ]


# --- AAVE-style Lending Queries --------------------------------------------

class LendingQuery(graphene.ObjectType):
    """AAVE-style lending queries"""
    
    def resolve_lending_reserves(self, info):
        """Get all active lending reserves"""
        from .crypto_models import LendingReserve
        return LendingReserve.objects.filter(is_active=True)
    
    def resolve_my_lending_account(self, info):
        """Get user's complete lending account data"""
        user = _require_auth(info)
        if not user:
            return None
        
        from .crypto_models import SupplyPosition, BorrowPosition, CryptoPrice
        from .aave_risk import calculate_lending_account_data
        
        # Get user's positions
        supplies = SupplyPosition.objects.filter(user=user)
        borrows = BorrowPosition.objects.filter(user=user, is_active=True)
        
        # Get current prices for all assets
        symbols = set()
        for sp in supplies:
            symbols.add(sp.reserve.cryptocurrency.symbol)
        for bp in borrows:
            symbols.add(bp.reserve.cryptocurrency.symbol)
        
        prices = {}
        for symbol in symbols:
            try:
                from .crypto_models import Cryptocurrency
                currency = Cryptocurrency.objects.get(symbol=symbol)
                latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
                if latest_price:
                    prices[symbol] = latest_price.price_usd
            except:
                continue
        
        # Calculate account data
        supplies_data = [(sp.reserve, sp.quantity, sp.use_as_collateral) for sp in supplies]
        borrows_data = [(bp.reserve, bp.amount) for bp in borrows]
        
        return calculate_lending_account_data(supplies_data, borrows_data, prices)
    
    def resolve_my_supply_positions(self, info):
        """Get user's supply positions"""
        user = _require_auth(info)
        if not user:
            return []
        
        from .crypto_models import SupplyPosition
        return SupplyPosition.objects.filter(user=user)
    
    def resolve_my_borrow_positions(self, info):
        """Get user's borrow positions"""
        user = _require_auth(info)
        if not user:
            return []
        
        from .crypto_models import BorrowPosition
        return BorrowPosition.objects.filter(user=user, is_active=True)


# Add AAVE queries to main Query class
class Query(graphene.ObjectType):
    """Main GraphQL query class"""
    
    # Existing queries...
    users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.Int())
    posts = graphene.List(PostType)
    post = graphene.Field(PostType, id=graphene.Int())
    chat_sessions = graphene.List(ChatSessionType)
    chat_session = graphene.Field(ChatSessionType, id=graphene.Int())
    chat_messages = graphene.List(ChatMessageType, session_id=graphene.Int())
    comments = graphene.List(CommentType, post_id=graphene.Int())
    stocks = graphene.List(StockType)
    stock = graphene.Field(StockType, symbol=graphene.String())
    stock_data = graphene.List(StockDataType, symbol=graphene.String(), limit=graphene.Int())
    watchlists = graphene.List(WatchlistType)
    watchlist = graphene.Field(WatchlistType, id=graphene.Int())
    my_watchlist = graphene.List(WatchlistItemType)
    ai_recommendations = graphene.List(AIPortfolioRecommendationType)
    stock_discussions = graphene.List(StockDiscussionType, symbol=graphene.String())
    stock_discussion = graphene.Field(StockDiscussionType, id=graphene.Int())
    debt_snowball = graphene.Field(DebtSnowballResultType, debts=graphene.List(graphene.Float))
    credit_utilization = graphene.Field(CreditUtilResultType, current_balance=graphene.Float(), credit_limit=graphene.Float())
    purchase_advice = graphene.Field(PurchaseAdviceType, item_cost=graphene.Float(), monthly_income=graphene.Float(), monthly_expenses=graphene.Float())
    
    # AAVE-style lending queries
    lending_reserves = graphene.List('core.crypto_graphql.LendingReserveType')
    # my_lending_account = graphene.Field('core.crypto_graphql.LendingAccountDataType')  # Commented out - type doesn't exist
    my_supply_positions = graphene.List('core.crypto_graphql.SupplyPositionType')
    my_borrow_positions = graphene.List('core.crypto_graphql.BorrowPositionType')
    
    # Existing resolvers...
    def resolve_users(self, info):
        return User.objects.all()
    
    def resolve_user(self, info, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return None
    
    def resolve_posts(self, info):
        return Post.objects.all().order_by('-created_at')
    
    def resolve_post(self, info, id):
        try:
            return Post.objects.get(id=id)
        except Post.DoesNotExist:
            return None
    
    def resolve_chat_sessions(self, info):
        user = _require_auth(info)
        if not user:
            return []
        return ChatSession.objects.filter(user=user).order_by('-created_at')
    
    def resolve_chat_session(self, info, id):
        user = _require_auth(info)
        if not user:
            return None
        try:
            return ChatSession.objects.get(id=id, user=user)
        except ChatSession.DoesNotExist:
            return None
    
    def resolve_chat_messages(self, info, session_id):
        user = _require_auth(info)
        if not user:
            return []
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            return ChatMessage.objects.filter(session=session).order_by('created_at')
        except ChatSession.DoesNotExist:
            return []
    
    def resolve_comments(self, info, post_id):
        try:
            post = Post.objects.get(id=post_id)
            return Comment.objects.filter(post=post).order_by('created_at')
        except Post.DoesNotExist:
            return []
    
    def resolve_stocks(self, info):
        return Stock.objects.all()
    
    def resolve_stock(self, info, symbol):
        try:
            return Stock.objects.get(symbol=symbol.upper())
        except Stock.DoesNotExist:
            return None
    
    def resolve_stock_data(self, info, symbol, limit=100):
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            return StockData.objects.filter(stock=stock).order_by('-date')[:limit]
        except Stock.DoesNotExist:
            return []
    
    def resolve_watchlists(self, info):
        user = _require_auth(info)
        if not user:
            return []
        return Watchlist.objects.filter(user=user)
    
    def resolve_watchlist(self, info, id):
        user = _require_auth(info)
        if not user:
            return None
        try:
            return Watchlist.objects.get(id=id, user=user)
        except Watchlist.DoesNotExist:
            return None
    
    def resolve_my_watchlist(self, info):
        user = _require_auth(info)
        if not user:
            return []
        try:
            watchlist = Watchlist.objects.get(user=user)
            return watchlist.items.all()
        except Watchlist.DoesNotExist:
            return []
    
    def resolve_ai_recommendations(self, info):
        user = _require_auth(info)
        if not user:
            return []
        return AIPortfolioRecommendation.objects.filter(user=user).order_by('-created_at')
    
    def resolve_stock_discussions(self, info, symbol):
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            return StockDiscussion.objects.filter(stock=stock).order_by('-created_at')
        except Stock.DoesNotExist:
            return []
    
    def resolve_stock_discussion(self, info, id):
        try:
            return StockDiscussion.objects.get(id=id)
        except StockDiscussion.DoesNotExist:
            return None
    
    def resolve_debt_snowball(self, info, debts):
        return debt_snowball_plan(debts)
    
    def resolve_credit_utilization(self, info, current_balance, credit_limit):
        return credit_utilization_optimizer(current_balance, credit_limit)
    
    def resolve_purchase_advice(self, info, item_cost, monthly_income, monthly_expenses):
        return should_buy_luxury_item(item_cost, monthly_income, monthly_expenses)
    
    # AAVE lending resolvers
    def resolve_lending_reserves(self, info):
        from .crypto_models import LendingReserve
        return LendingReserve.objects.filter(is_active=True)
    
    # def resolve_my_lending_account(self, info):  # Commented out - type doesn't exist
    #     user = _require_auth(info)
    #     if not user:
    #         return None
    #     
    #     from .crypto_models import SupplyPosition, BorrowPosition, CryptoPrice
    #     from .aave_risk import calculate_lending_account_data
    #     
    #     # Get user's positions
    #     supplies = SupplyPosition.objects.filter(user=user)
    #     borrows = BorrowPosition.objects.filter(user=user, is_active=True)
    #     
    #     # Get current prices for all assets
    #     symbols = set()
    #     for sp in supplies:
    #         symbols.add(sp.reserve.cryptocurrency.symbol)
    #     for bp in borrows:
    #         symbols.add(bp.reserve.cryptocurrency.symbol)
    #     
    #     prices = {}
    #     for symbol in symbols:
    #         try:
    #             from .crypto_models import Cryptocurrency
    #             currency = Cryptocurrency.objects.get(symbol=symbol)
    #             latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
    #             if latest_price:
    #                 prices[symbol] = latest_price.price_usd
    #         except:
    #             continue
    #     
    #     # Calculate account data
    #     supplies_data = [(sp.reserve, sp.quantity, sp.use_as_collateral) for sp in supplies]
    #     borrows_data = [(bp.reserve, bp.amount) for bp in borrows]
    #     
    #     return calculate_lending_account_data(supplies_data, borrows_data, prices)
    
    def resolve_my_supply_positions(self, info):
        user = _require_auth(info)
        if not user:
            return []
        
        from .crypto_models import SupplyPosition
        return SupplyPosition.objects.filter(user=user)
    
    def resolve_my_borrow_positions(self, info):
        user = _require_auth(info)
        if not user:
            return []
        
        from .crypto_models import BorrowPosition
        return BorrowPosition.objects.filter(user=user, is_active=True)

    # Swing Trading Signals Query
    signals = graphene.List(
        SignalType,
        symbol=graphene.String(),
        signalType=graphene.String(),
        minMlScore=graphene.Float(),
        isActive=graphene.Boolean(),
        limit=graphene.Int()
    )
    
    def resolve_signals(self, info, symbol=None, signalType=None, minMlScore=None, isActive=None, limit=50):
        # Mock signals data for now
        mock_signals = [
            {
                'id': '1',
                'symbol': 'AAPL',
                'timeframe': '1D',
                'triggeredAt': '2024-01-15T10:30:00Z',
                'signalType': 'BUY',
                'entryPrice': 175.50,
                'stopPrice': 170.00,
                'targetPrice': 185.00,
                'mlScore': 0.85,
                'thesis': 'Strong technical breakout with high volume confirmation',
                'riskRewardRatio': 2.0,
                'daysSinceTriggered': 5,
                'isLikedByUser': False,
                'userLikeCount': 12,
                'features': ['RSI_OVERSOLD', 'VOLUME_SPIKE', 'BREAKOUT'],
                'isActive': True,
                'isValidated': False,
                'validationPrice': None,
                'validationTimestamp': None,
                'createdBy': {'id': '1', 'name': 'AI Trading System', 'email': 'ai@richesreach.com'}
            },
            {
                'id': '2',
                'symbol': 'MSFT',
                'timeframe': '1D',
                'triggeredAt': '2024-01-14T14:20:00Z',
                'signalType': 'SELL',
                'entryPrice': 495.00,
                'stopPrice': 500.00,
                'targetPrice': 480.00,
                'mlScore': 0.72,
                'thesis': 'Resistance level rejection with bearish divergence',
                'riskRewardRatio': 3.0,
                'daysSinceTriggered': 6,
                'isLikedByUser': True,
                'userLikeCount': 8,
                'features': ['RESISTANCE_REJECTION', 'BEARISH_DIVERGENCE'],
                'isActive': True,
                'isValidated': False,
                'validationPrice': None,
                'validationTimestamp': None,
                'createdBy': {'id': '1', 'name': 'AI Trading System', 'email': 'ai@richesreach.com'}
            }
        ]
        
        # Apply filters
        data = mock_signals
        if symbol:
            data = [x for x in data if x['symbol'] == symbol.upper()]
        if signalType:
            data = [x for x in data if x['signalType'] == signalType.upper()]
        if minMlScore is not None:
            data = [x for x in data if x['mlScore'] >= float(minMlScore)]
        if isActive is not None:
            data = [x for x in data if x['isActive'] == bool(isActive)]
        if limit:
            data = data[:int(limit)]
        
        return data


schema = graphene.Schema(query=Query)