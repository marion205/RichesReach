import graphene


from django.contrib.auth import get_user_model


from .types import UserType, PostType, ChatSessionType, ChatMessageType, CommentType, StockType, StockDataType, ProfileInput, AIRecommendationsType


from .models import Post, ChatSession, ChatMessage, Comment, User, Stock, StockData


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
    # ai_recommendations moved to PremiumQueries to avoid duplicate field definition

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

    # resolve_ai_recommendations moved to PremiumQueries to avoid duplicate field definition
    # Social fields live in core.graphql.queries.social.SocialQuery
    # Market data (stocks, stock, fss_scores, top_fss_stocks, beginner_friendly_stocks, current_stock_prices)
    # live in core.graphql.queries.market_data.MarketDataQuery

    # my_watchlist = graphene.List(WatchlistItemType) # TODO: Uncomment when WatchlistItemType is available

    # Rust Engine queries - TODO: Uncomment when types are available

    # rust_stock_analysis = graphene.Field(RustStockAnalysisType, symbol=graphene.String(required=True))

    # rust_recommendations = graphene.List(RustRecommendationType)

    # rust_health = graphene.Field(RustHealthType)

    # AI Portfolio, watchlists, discussions, social_feed, top_performers, market_sentiment, stock_moments
    # live in core.graphql.queries.discussions.DiscussionsQuery

    # Day/swing/pre-market picks, execution suggestions, researchHub
    # live in core.graphql.queries.signals.SignalsQuery


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


def _get_real_intraday_day_trading_picks(
    mode="SAFE",
    limit=10,
    use_dynamic_discovery=True,
    min_bandit_weight: float = 0.10,
):
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
    from .day_trading_feature_service import DayTradingFeatureService
    from .day_trading_ml_scorer import DayTradingMLScorer
    from .bandit_service import BanditService
    
    # Check cache first (60 second TTL for intraday data)
    # NOTE: Currently global per mode. Future: per-user cache keys when we add user-specific filters
    # Future cache key: f"day_trading_picks:{user_id}:{mode}:v4"
    cache_key = f"day_trading_picks:{mode}:v4:dynamic_{use_dynamic_discovery}:bandit_{min_bandit_weight:.2f}"
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
    
    # Initialize core services (features, ML scoring, bandit allocation)
    feature_service = DayTradingFeatureService()
    ml_scorer = DayTradingMLScorer()
    bandit_weights = {}
    try:
        from .bandit_models import BanditArm
        arms = BanditArm.objects.filter(enabled=True)
        if arms.exists():
            bandit_weights = {arm.strategy_slug: float(arm.current_weight) for arm in arms}
        else:
            bandit_weights = BanditService().get_allocation_weights()
    except Exception as e:
        logger.debug(f"Bandit weights unavailable: {e}")

    def _classify_intraday_strategy(features: dict) -> str:
        """Heuristic mapping of feature state to strategy slug for bandit weighting."""
        breakout_pct = float(features.get('breakout_pct', 0.0))
        is_breakout = float(features.get('is_breakout', 0.0))
        is_vol_expansion = float(features.get('is_vol_expansion', 0.0))
        bb_position = float(features.get('bb_position', 0.5))
        rsi_14 = float(features.get('rsi_14', 50.0))
        trend_strength = float(features.get('trend_strength', 0.0))
        regime_conf = float(features.get('regime_confidence', 0.5))

        if is_breakout > 0.5 or breakout_pct > 0.08 or is_vol_expansion > 0.5:
            return 'breakout'
        if bb_position < 0.2 or bb_position > 0.8 or rsi_14 < 32 or rsi_14 > 68:
            return 'mean_reversion'
        if trend_strength > 0.015 and regime_conf > 0.6:
            return 'momentum'
        return 'momentum'

    def _regime_label(features: dict) -> str:
        is_trend = float(features.get('is_trend_regime', 0.0)) > 0.5
        is_range = float(features.get('is_range_regime', 0.0)) > 0.5
        is_chop = float(features.get('is_high_vol_chop', 0.0)) > 0.5
        is_trend_up = float(features.get('is_trend_up', 0.0)) > 0.5
        is_trend_down = float(features.get('is_trend_down', 0.0)) > 0.5
        is_vol_expansion = float(features.get('is_vol_expansion', 0.0)) > 0.5
        momentum_15m = float(features.get('momentum_15m', 0.0))
        sentiment_score = float(features.get('sentiment_score', 0.0))

        if is_chop and is_vol_expansion:
            return 'BREAKOUT_EXPANSION'
        if is_chop and momentum_15m < -0.02 and sentiment_score < -0.6:
            return 'CRASH_PANIC'
        if is_chop:
            return 'VOLATILE_CHOP'
        if is_trend and is_trend_up:
            return 'TREND_UP'
        if is_trend and is_trend_down:
            return 'TREND_DOWN'
        if is_range:
            return 'MEAN_REVERSION'
        return 'NEUTRAL'

    def _regime_risk_settings(regime_label: str) -> Dict[str, float]:
        """Return (time_stop_min, conviction_multiplier) by regime label."""
        if regime_label in {'TREND_UP', 'TREND_DOWN'}:
            return {'time_stop_min': 60, 'conviction_multiplier': 1.2}
        if regime_label == 'MEAN_REVERSION':
            return {'time_stop_min': 45, 'conviction_multiplier': 1.0}
        if regime_label == 'BREAKOUT_EXPANSION':
            return {'time_stop_min': 20, 'conviction_multiplier': 0.8}
        if regime_label == 'CRASH_PANIC':
            return {'time_stop_min': 15, 'conviction_multiplier': 0.5}
        if regime_label == 'VOLATILE_CHOP':
            return {'time_stop_min': 20, 'conviction_multiplier': 0.8}
        return {'time_stop_min': 30, 'conviction_multiplier': 1.0}

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
            
            import pandas as pd
            import numpy as np

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
            
            # Build 5m OHLCV DataFrame from bars
            df_5m = pd.DataFrame([
                {
                    'open': float(b.get('o', 0)),
                    'high': float(b.get('h', 0)),
                    'low': float(b.get('l', 0)),
                    'close': float(b.get('c', 0)),
                    'volume': float(b.get('v', 0)),
                    'timestamp': int(b.get('t', 0)),
                }
                for b in bars
            ])
            df_5m = df_5m[df_5m['close'] > 0].copy()
            if df_5m.empty:
                return None
            df_5m = df_5m.sort_values('timestamp')

            # Create a lightweight 1m approximation from 5m bars (for feature extraction)
            def _expand_5m_to_1m(df: pd.DataFrame) -> pd.DataFrame:
                if df.empty:
                    return df
                rows = []
                for _, row in df.iterrows():
                    base_ts = int(row['timestamp'])
                    o = float(row['open'])
                    h = float(row['high'])
                    l = float(row['low'])
                    c = float(row['close'])
                    v = float(row['volume'])
                    # Linear interpolation for close across 5 minutes
                    closes = np.linspace(o, c, 5)
                    volume_per_min = v / 5.0
                    for i in range(5):
                        rows.append({
                            'open': o if i == 0 else closes[i-1],
                            'high': max(h, closes[i]),
                            'low': min(l, closes[i]),
                            'close': closes[i],
                            'volume': volume_per_min,
                            'timestamp': base_ts + (i * 60_000),
                        })
                return pd.DataFrame(rows)

            df_1m = _expand_5m_to_1m(df_5m)
            if df_1m.empty:
                df_1m = df_5m.copy()

            # Extract full feature set
            current_time = datetime.now()
            try:
                if int(df_5m['timestamp'].iloc[-1]) > 0:
                    current_time = datetime.fromtimestamp(int(df_5m['timestamp'].iloc[-1]) / 1000.0)
            except Exception:
                pass

            features = feature_service.extract_all_features(
                df_1m,
                df_5m,
                symbol,
                sentiment_data=None,
                current_time=current_time
            )
            
            # Calculate volume metrics (fallback for filters if needed)
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
            
            # Execution/microstructure feature enrichment
            if microstructure:
                try:
                    features['order_imbalance'] = float(microstructure.get('order_imbalance', 0.0))
                    features['bid_depth'] = float(microstructure.get('bid_depth', 0.0))
                    features['ask_depth'] = float(microstructure.get('ask_depth', 0.0))
                    features['depth_imbalance'] = float(microstructure.get('depth_imbalance', 0.0))
                    features['spread_bps'] = float(microstructure.get('spread_bps', features.get('spread_bps', 5.0)))
                    features['execution_quality_score'] = float(
                        microstructure_service.get_execution_quality_score(microstructure)
                    )
                except Exception as e:
                    logger.debug(f"Microstructure enrich failed for {symbol}: {e}")
            
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
            momentum15m = float(features.get('momentum_15m', 0.0))
            side = 'LONG' if momentum15m > 0 else 'SHORT'

            # Score with ML learner + rule-based fallback
            base_score = ml_scorer.score(features, mode=mode, side=side, price_data=df_5m, symbol=symbol)

            # Bandit-weighted score (strategy-aware allocation)
            strategy_slug = _classify_intraday_strategy(features)
            bandit_weight = float(bandit_weights.get(strategy_slug, 0.25)) if bandit_weights else 0.25
            if bandit_weight < min_bandit_weight:
                return None

            regime_label = _regime_label(features)
            regime_settings = _regime_risk_settings(regime_label)

            score = base_score * (0.8 + (0.4 * bandit_weight))
            score *= float(regime_settings['conviction_multiplier'])

            # Execution-quality penalty for current microstructure snapshot
            exec_quality = float(features.get('execution_quality_score', 6.0))
            if exec_quality < 4.0:
                score *= 0.9
            if exec_quality < 2.5:
                score *= 0.8

            score = max(0.0, min(10.0, score))
            
            # Apply mode-specific filters
            volume_ratio = float(features.get('volume_ratio', rvol10m))

            if mode == "SAFE":
                # SAFE: Require lower volatility, higher liquidity
                if volatility > mode_max_volatility or avg_volume < mode_min_volume or volume_ratio < 1.2:
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
            
            # Calculate risk parameters using feature service
            risk_metrics = feature_service.calculate_risk_metrics(features, mode, current_price)
            risk_metrics['entryPrice'] = float(current_price)
            risk_metrics['timeStopMin'] = int(regime_settings['time_stop_min'])
            
            # Catalyst score based on expanded features
            catalyst_score = ml_scorer.calculate_catalyst_score(features)

            # Sanitize full feature set for JSON serialization
            def _sanitize_features(value):
                if isinstance(value, dict):
                    return {k: _sanitize_features(v) for k, v in value.items()}
                if isinstance(value, (list, tuple)):
                    return [_sanitize_features(v) for v in value]
                if isinstance(value, (np.floating, np.integer)):
                    return float(value)
                return value

            # Minimal feature payload for GraphQL + full features for logging
            features_dict = {
                'momentum15m': round(momentum15m, 4),
                'rvol10m': round(volume_ratio, 2),
                'vwapDist': round(float(features.get('vwap_dist_pct', 0.0)), 4),
                'breakoutPct': round(float(features.get('breakout_pct', 0.0)), 4),
                'spreadBps': round(float(features.get('spread_bps', 5.0)), 2),
                'catalystScore': round(float(catalyst_score), 2),
                'executionQualityScore': round(float(features.get('execution_quality_score', 6.0)), 1),
            }

            if microstructure:
                features_dict.update({
                    'orderImbalance': round(float(features.get('order_imbalance', 0.0)), 4),
                    'bidDepth': round(float(features.get('bid_depth', 0.0)), 2),
                    'askDepth': round(float(features.get('ask_depth', 0.0)), 2),
                    'depthImbalance': round(float(features.get('depth_imbalance', 0.0)), 4),
                })

                # Mark as microstructure risky if quality score is low
                if float(features.get('execution_quality_score', 6.0)) < 5.0:
                    features_dict['microstructureRisky'] = True

            # Attach full feature set for logging and ML feedback loops
            features_dict['_full_features'] = _sanitize_features(features)
            features_dict['_strategy'] = strategy_slug
            features_dict['_bandit_weight'] = round(bandit_weight, 4)
            
            return {
                'symbol': symbol,
                'side': side,
                'score': round(score, 2),
                'banditWeight': round(bandit_weight, 4),
                'strategyType': strategy_slug.upper(),
                'regimeLabel': regime_label,
                'features': features_dict,
                'risk': risk_metrics,
                'notes': (
                    f"{mode} mode: {momentum15m*100:.2f}% momentum, "
                    f"{volume_ratio:.1f}x volume, strategy={strategy_slug}, "
                    f"bandit={bandit_weight:.2f}"
                )
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

        # Try to get real intraday data via market data facade (singleton)
        try:
            from .market_data_manager import get_market_data_service
            from .market_data_api_service import DataProvider

            service = get_market_data_service()
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
                now = datetime.now()
                close_col = 'Close' if 'Close' in df.columns else 'close'
                daily_vol = df[close_col].pct_change().std() if len(df) > 1 else 0.02
                if pd.isna(daily_vol) or daily_vol == 0:
                    daily_vol = 0.02  # Default 2% volatility

                timestamps_1m = [now - timedelta(minutes=i) for i in range(390, 0, -1)]
                prices_1m = [current_price]
                for i in range(1, 390):
                    change = np.random.normal(0, daily_vol / np.sqrt(390))
                    prices_1m.append(prices_1m[-1] * (1 + change))

                ohlcv_1m = pd.DataFrame({
                    'timestamp': timestamps_1m,
                    'open': prices_1m,
                    'high': [p * (1 + abs(np.random.normal(0, daily_vol / 390))) for p in prices_1m],
                    'low': [p * (1 - abs(np.random.normal(0, daily_vol / 390))) for p in prices_1m],
                    'close': prices_1m,
                    'volume': [int(float(latest.get(volume_col, latest.get('volume', 1000000))) / 390) for _ in range(390)]
                })
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
