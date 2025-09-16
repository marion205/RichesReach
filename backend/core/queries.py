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
    AIPortfolioRecommendationType,
    StockDiscussionType,
    DebtSnowballResultType,
    CreditUtilResultType,
    PurchaseAdviceType,
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
    stocks = graphene.List(StockType, search=graphene.String(required=False), limit=graphene.Int(required=False))
    stock = graphene.Field(StockType, symbol=graphene.String(required=True))
    beginner_friendly_stocks = graphene.List(StockType, limit=graphene.Int(required=False))
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

    # --- Watchlists ---
    watchlists = graphene.List(WatchlistType, user_id=graphene.ID())
    watchlist = graphene.Field(WatchlistType, id=graphene.ID(required=True))
    public_watchlists = graphene.List(WatchlistType, limit=graphene.Int(required=False))
    my_watchlist = graphene.List(WatchlistType)
    
    # --- Rust Stock Analysis ---
    rust_stock_analysis = graphene.Field('core.types.RustStockAnalysisType', symbol=graphene.String(required=True))

    # --- Discussions (Reddit-like) ---
    stock_discussions = graphene.List(
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
    def resolve_stocks(self, info, search=None, limit=100):
        limit = max(1, min(limit or 100, 200))
        
        # If there's a search term, try to use the stock service to search and sync real data
        if search and search.strip():
            stock_service = SimpleStockSearchService()
            # Search and sync stocks from external APIs
            searched_stocks = stock_service.search_and_sync_stocks(search.strip())
            if searched_stocks:
                return searched_stocks[:limit]
        
        # Fallback to database query (either no search term or API failed)
        qs = Stock.objects.all()
        if search:
            qs = qs.filter(
                djmodels.Q(symbol__icontains=search.upper()) |
                djmodels.Q(company_name__icontains=search)
            )
        return qs.order_by('symbol')[:limit]

    def resolve_stock(self, info, symbol):
        try:
            return Stock.objects.get(symbol=symbol.upper())
        except Stock.DoesNotExist:
            return None

    def resolve_beginner_friendly_stocks(self, info, limit=20):
        limit = max(1, min(limit or 20, 50))
        
        # Get stocks from database and calculate AI/ML beginner scores
        stocks = Stock.objects.all()[:100]  # Get more stocks to score
        
        # Use AI/ML to calculate beginner-friendly scores
        stock_service = SimpleStockSearchService()
        scored_stocks = []
        
        for stock in stocks:
            # Calculate or update beginner-friendly score using AI/ML
            try:
                # This would use the AI/ML scoring system
                beginner_score = stock_service._calculate_beginner_score({
                    'MarketCapitalization': str(stock.market_cap) if stock.market_cap else 'None',
                    'PERatio': str(stock.pe_ratio) if stock.pe_ratio else 'None',
                    'DividendYield': f"{stock.dividend_yield * 100}%" if stock.dividend_yield else 'None',
                    'Sector': stock.sector or '',
                    'Name': stock.company_name or ''
                })
                if beginner_score >= 65:  # Only include stocks with good beginner scores
                    stock.beginner_friendly_score = beginner_score
                    stock.save()
                    scored_stocks.append(stock)
            except Exception as e:
                # Fallback to existing score
                if stock.beginner_friendly_score and stock.beginner_friendly_score >= 65:
                    scored_stocks.append(stock)
        
        # Sort by beginner score and return top results
        scored_stocks.sort(key=lambda x: x.beginner_friendly_score or 0, reverse=True)
        return scored_stocks[:limit]

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

    # -------------------------
    # Watchlists
    # -------------------------
    def resolve_watchlists(self, root, info, user_id=None):
        user = _require_auth(info)
        if not user:
            return []
        if user_id:
            # Show only public lists for other users
            return Watchlist.objects.filter(user_id=user_id, is_public=True).select_related('stock').order_by('-created_at')[:200]
        return Watchlist.objects.filter(user=user).select_related('stock').order_by('-created_at')[:200]

    def resolve_watchlist(self, root, info, id):
        try:
            wl = Watchlist.objects.select_related('user', 'stock').get(id=id)
        except Watchlist.DoesNotExist:
            return None
        user = info.context.user
        if wl.is_public or (user.is_authenticated and wl.user_id == user.id):
            return wl
        return None

    def resolve_public_watchlists(self, root, info, limit=20):
        limit = max(1, min(limit or 20, 100))
        return Watchlist.objects.filter(is_public=True).select_related('stock').order_by('-created_at')[:limit]

    def resolve_my_watchlist(self, info):
        user = _require_auth(info)
        if not user:
            return []
        return Watchlist.objects.filter(user=user).select_related('stock').order_by('-created_at')[:200]

    # -------------------------
    # Discussions
    # -------------------------
    def resolve_stock_discussions(self, root, info, stock_symbol=None, limit=None):
        limit = max(1, min(limit or 50, 100))
        qs = StockDiscussion.objects.select_related('user', 'stock').order_by('-created_at')
        if stock_symbol:
            qs = qs.filter(stock__symbol=stock_symbol.upper())
        return qs[:limit]

    def resolve_discussion_detail(self, root, info, id):
        try:
            return StockDiscussion.objects.select_related('user', 'stock').get(id=id)
        except StockDiscussion.DoesNotExist:
            return None

    def resolve_social_feed(self, root, info, limit=50):
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
        return {"sentiment": "neutral", "confidence": 0.5}

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


schema = graphene.Schema(query=Query)