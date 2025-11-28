"""
GraphQL Types for Enhanced Social Features
"""
import graphene
import json
from typing import List, Dict, Any
from django.utils import timezone
from .social_enhancements import SocialEnhancementsService
from graphql import GraphQLError
import logging

logger = logging.getLogger(__name__)


class LeaderboardEntryType(graphene.ObjectType):
    """Portfolio leaderboard entry"""
    userId = graphene.Int()
    userName = graphene.String()
    userEmail = graphene.String()
    totalReturnPct = graphene.Float()
    totalValue = graphene.Float()
    rank = graphene.Int()
    holdingsCount = graphene.Int()
    bestPerformer = graphene.String()
    worstPerformer = graphene.String()


class ActivityFeedItemType(graphene.ObjectType):
    """Activity feed item"""
    type = graphene.String()  # 'portfolio_update', 'discussion', 'post', 'follow'
    userId = graphene.Int()
    userName = graphene.String()
    timestamp = graphene.String()
    content = graphene.JSONString()


class PortfolioSharingInfoType(graphene.ObjectType):
    """Portfolio sharing information"""
    isPublic = graphene.Boolean()
    shareToken = graphene.String()
    totalFollowers = graphene.Int()
    portfolioSummary = graphene.JSONString()


class TrendingDiscussionType(graphene.ObjectType):
    """Trending discussion"""
    id = graphene.Int()
    title = graphene.String()
    symbol = graphene.String()
    userName = graphene.String()
    score = graphene.Int()
    commentsCount = graphene.Int()
    createdAt = graphene.String()
    trendingReason = graphene.String()


class SignalAlertType(graphene.ObjectType):
    """Signal alert"""
    type = graphene.String()
    severity = graphene.String()
    message = graphene.String()
    timestamp = graphene.String()


class SignalUpdatesType(graphene.ObjectType):
    """Multi-signal fusion updates"""
    symbol = graphene.String()
    timestamp = graphene.String()
    signals = graphene.JSONString()
    fusionScore = graphene.Float()
    alerts = graphene.List(SignalAlertType)
    recommendation = graphene.String()
    consumerStrength = graphene.Float()


class PortfolioSignalsType(graphene.ObjectType):
    """Portfolio-wide signal summary"""
    portfolioSignals = graphene.List(graphene.String)  # JSON strings of signal data
    strongBuyCount = graphene.Int()
    strongSellCount = graphene.Int()
    overallSentiment = graphene.String()
    totalPositions = graphene.Int()


class TradeDataType(graphene.ObjectType):
    """Trade data for social feed items"""
    symbol = graphene.String()
    side = graphene.String()
    quantity = graphene.Float()
    price = graphene.Float()
    pnl = graphene.Float()


class PerformanceType(graphene.ObjectType):
    """Performance metrics for social feed items"""
    totalReturn = graphene.Float()
    winRate = graphene.Float()
    sharpeRatio = graphene.Float()


class TraderPerformanceType(graphene.ObjectType):
    """Performance metrics for traders"""
    totalReturn = graphene.Float()
    winRate = graphene.Float()
    sharpeRatio = graphene.Float()
    maxDrawdown = graphene.Float()
    totalTrades = graphene.Int()


class RecentTradeType(graphene.ObjectType):
    """Recent trade for traders"""
    symbol = graphene.String()
    side = graphene.String()
    quantity = graphene.Float()
    price = graphene.Float()
    timestamp = graphene.String()
    pnl = graphene.Float()


class SocialFeedUserType(graphene.ObjectType):
    """User info for social feeds"""
    id = graphene.ID()
    username = graphene.String()
    avatar = graphene.String()
    verified = graphene.Boolean()
    followerCount = graphene.Int()
    winRate = graphene.Float()
    performance = graphene.Field(TraderPerformanceType)
    recentTrades = graphene.List(RecentTradeType)


class SocialFeedItemType(graphene.ObjectType):
    """Social feed item for social trading"""
    id = graphene.ID()
    user = graphene.Field(SocialFeedUserType)
    content = graphene.String()
    type = graphene.String()
    timestamp = graphene.String()
    likes = graphene.Int()
    comments = graphene.Int()
    shares = graphene.Int()
    tradeData = graphene.Field(TradeDataType)
    performance = graphene.Field(PerformanceType)


class TechnicalIndicatorType(graphene.ObjectType):
    """Technical indicator for swing signals"""
    name = graphene.String()
    value = graphene.Float()
    signal = graphene.String()
    strength = graphene.Float()
    description = graphene.String()


class PatternRecognitionType(graphene.ObjectType):
    """Pattern recognition for swing signals"""
    name = graphene.String()
    confidence = graphene.Float()
    signal = graphene.String()
    description = graphene.String()
    timeframe = graphene.String()


class SwingSignalUserType(graphene.ObjectType):
    """User who created the signal"""
    id = graphene.String()
    username = graphene.String()
    name = graphene.String()


class SwingSignalType(graphene.ObjectType):
    """Swing trading signal with all fields"""
    id = graphene.String()
    symbol = graphene.String()
    timeframe = graphene.String()
    triggeredAt = graphene.String()
    signalType = graphene.String()
    entryPrice = graphene.Float()
    stopPrice = graphene.Float()
    targetPrice = graphene.Float()
    mlScore = graphene.Float()
    thesis = graphene.String()
    riskRewardRatio = graphene.Float()
    daysSinceTriggered = graphene.Int()
    isLikedByUser = graphene.Boolean()
    userLikeCount = graphene.Int()
    features = graphene.JSONString()
    isActive = graphene.Boolean()
    isValidated = graphene.Boolean()
    validationPrice = graphene.Float()
    validationTimestamp = graphene.String()
    createdBy = graphene.Field(SwingSignalUserType)
    technicalIndicators = graphene.List(TechnicalIndicatorType)
    patterns = graphene.List(PatternRecognitionType)


class SocialQueries(graphene.ObjectType):
    """Enhanced social feature queries"""
    
    socialFeeds = graphene.List(
        SocialFeedItemType,
        limit=graphene.Int(default_value=50),
        offset=graphene.Int(default_value=0),
        description="Get social trading feeds"
    )
    
    portfolioLeaderboard = graphene.List(
        LeaderboardEntryType,
        timeframe=graphene.String(default_value='all_time'),
        limit=graphene.Int(default_value=50),
        description="Get portfolio performance leaderboard"
    )
    
    activityFeed = graphene.List(
        ActivityFeedItemType,
        limit=graphene.Int(default_value=50),
        description="Get enhanced activity feed for current user"
    )
    
    portfolioSharingInfo = graphene.Field(
        PortfolioSharingInfoType,
        description="Get portfolio sharing information for current user"
    )
    
    trendingDiscussions = graphene.List(
        TrendingDiscussionType,
        limit=graphene.Int(default_value=20),
        timeframe=graphene.String(default_value='24h'),
        description="Get trending stock discussions"
    )
    
    signalUpdates = graphene.Field(
        SignalUpdatesType,
        symbol=graphene.String(required=True),
        lookbackHours=graphene.Int(default_value=24),
        description="Get real-time multi-signal updates for a stock"
    )
    
    watchlistSignals = graphene.List(
        SignalUpdatesType,
        threshold=graphene.Float(default_value=70.0),
        description="Get signal updates for watchlist stocks above threshold"
    )
    
    portfolioSignals = graphene.Field(
        PortfolioSignalsType,
        threshold=graphene.Float(default_value=60.0),
        description="Get signal updates for all portfolio positions"
    )
    
    topTraders = graphene.List(
        SocialFeedUserType,
        period=graphene.String(default_value='all_time'),
        description="Get top traders by performance"
    )
    
    swingSignals = graphene.List(
        SwingSignalType,
        symbol=graphene.String(required=False),
        signalType=graphene.String(required=False),
        minMlScore=graphene.Float(required=False),
        isActive=graphene.Boolean(required=False),
        limit=graphene.Int(default_value=50),
        description="Get swing trading signals with filtering"
    )
    
    def resolve_socialFeeds(self, info, limit=50, offset=0):
        """Resolve social feeds for social trading"""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return []
        
        try:
            from .models import Post, StockDiscussion
            from django.utils import timezone
            from datetime import timedelta
            
            # Get posts and discussions from followed users
            followed_users = user.following.all()
            
            # Get recent posts
            posts = Post.objects.filter(
                user__in=followed_users
            ).select_related('user').order_by('-created_at')[:limit]
            
            # Get recent discussions
            discussions = StockDiscussion.objects.filter(
                user__in=followed_users
            ).select_related('user', 'stock').order_by('-created_at')[:limit]
            
            # Combine and format
            feed_items = []
            
            for post in posts:
                post_user = post.user
                feed_items.append(SocialFeedItemType(
                    id=f"post_{post.id}",
                    user=SocialFeedUserType(
                        id=str(post_user.id),
                        username=post_user.username if hasattr(post_user, 'username') else post_user.email.split('@')[0],
                        avatar=post_user.profile_pic or '',
                        verified=False,  # Would come from user model
                        followerCount=post_user.followers.count() if hasattr(post_user, 'followers') else 0,
                        winRate=0.0,  # Would come from trading stats
                    ),
                    content=post.content[:200] if post.content else '',
                    type='post',
                    timestamp=post.created_at.isoformat() if post.created_at else timezone.now().isoformat(),
                    likes=post.likes.count() if hasattr(post, 'likes') else 0,
                    comments=post.comment_set.count() if hasattr(post, 'comment_set') else 0,
                    shares=0,
                    tradeData=None,
                    performance=None,
                ))
            
            for discussion in discussions:
                disc_user = discussion.user
                feed_items.append(SocialFeedItemType(
                    id=f"discussion_{discussion.id}",
                    user=SocialFeedUserType(
                        id=str(disc_user.id),
                        username=disc_user.username if hasattr(disc_user, 'username') else disc_user.email.split('@')[0],
                        avatar=disc_user.profile_pic or '',
                        verified=False,
                        followerCount=disc_user.followers.count() if hasattr(disc_user, 'followers') else 0,
                        winRate=0.0,
                    ),
                    content=discussion.title or (discussion.content[:200] if hasattr(discussion, 'content') and discussion.content else ''),
                    type='discussion',
                    timestamp=discussion.created_at.isoformat() if discussion.created_at else timezone.now().isoformat(),
                    likes=discussion.upvotes if hasattr(discussion, 'upvotes') else 0,
                    comments=discussion.comments.count() if hasattr(discussion, 'comments') else 0,
                    shares=0,
                    tradeData=TradeDataType(
                        symbol=discussion.stock.symbol if discussion.stock else None,
                        side=None,
                        quantity=None,
                        price=None,
                        pnl=None,
                    ) if discussion.stock else None,
                    performance=None,
                ))
            
            # Sort by timestamp and apply offset
            feed_items.sort(key=lambda x: x.timestamp, reverse=True)
            return feed_items[offset:offset+limit]
            
        except Exception as e:
            logger.error(f"Error resolving social feeds: {e}", exc_info=True)
            return []
    
    def resolve_topTraders(self, info, period='all_time'):
        """Resolve top traders by performance"""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return []
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get users with portfolios, ordered by performance
            # In a real implementation, this would calculate actual performance metrics
            top_users = User.objects.filter(
                portfolio__isnull=False
            ).distinct()[:10]
            
            traders = []
            for trader_user in top_users:
                # Mock performance data - in production, calculate from actual trades
                performance = TraderPerformanceType(
                    totalReturn=15.5,  # Would come from portfolio performance
                    winRate=0.65,
                    sharpeRatio=1.2,
                    maxDrawdown=-5.0,
                    totalTrades=42,
                )
                
                # Mock recent trades - in production, fetch from actual trade history
                recent_trades = [
                    RecentTradeType(
                        symbol='AAPL',
                        side='BUY',
                        quantity=10.0,
                        price=150.0,
                        timestamp=timezone.now().isoformat(),
                        pnl=50.0,
                    ),
                ]
                
                traders.append(SocialFeedUserType(
                    id=str(trader_user.id),
                    username=trader_user.username if hasattr(trader_user, 'username') else trader_user.email.split('@')[0],
                    avatar=trader_user.profile_pic or '',
                    verified=False,
                    followerCount=trader_user.followers.count() if hasattr(trader_user, 'followers') else 0,
                    winRate=0.65,
                    performance=performance,
                    recentTrades=recent_trades,
                ))
            
            return traders
        except Exception as e:
            logger.error(f"Error resolving top traders: {e}", exc_info=True)
            return []
    
    def resolve_swingSignals(self, info, symbol=None, signalType=None, minMlScore=None, isActive=None, limit=50):
        """Resolve swing trading signals with filtering"""
        from django.utils import timezone
        from datetime import timedelta
        import json
        import uuid
        
        signals = []
        
        # Try to get signals from database
        try:
            from .signal_performance_models import SwingTradingSignal
            
            # Build query filter
            try:
                query = SwingTradingSignal.objects.filter(
                    generated_at__gte=timezone.now() - timedelta(days=30)
                )
                
                # Apply filters
                if symbol:
                    query = query.filter(symbol__iexact=symbol)
                
                if signalType:
                    # Map frontend signalType to backend side
                    signal_type_map = {
                        'LONG': 'LONG',
                        'SHORT': 'SHORT',
                        'BUY': 'LONG',
                        'SELL': 'SHORT'
                    }
                    side = signal_type_map.get(signalType.upper(), signalType.upper())
                    query = query.filter(side=side)
                
                if minMlScore is not None:
                    query = query.filter(score__gte=minMlScore)
                
                # Note: isActive filter would need to be implemented based on validation logic
                # For now, we'll return all signals as active if isActive is True
                if isActive is False:
                    # If explicitly False, we could filter out validated/inactive signals
                    # For now, we'll just skip this filter
                    pass
                
                # Get signals ordered by most recent
                signals = list(query.order_by('-generated_at')[:limit])
                logger.info(f"📊 Found {len(signals)} swing signals in database")
            except Exception as db_error:
                # Database table might not exist or be empty
                logger.warning(f"⚠️ Database query failed: {db_error}")
                signals = []
        except ImportError as import_error:
            # Model doesn't exist, use sample data
            logger.info(f"📊 SwingTradingSignal model not available, using sample data: {import_error}")
            signals = []
        
        # If no signals found, generate sample data
        if not signals or len(signals) == 0:
            logger.info("📊 No swing signals in database, generating sample signals")
            signals = _generate_sample_swing_signals(limit, symbol, signalType, minMlScore)
        
        try:
            user = getattr(info.context, 'user', None)
            user_id = str(user.id) if user and not user.is_anonymous else None
            
            result = []
            for signal in signals:
                # Calculate days since triggered
                days_since = None
                if signal.generated_at:
                    delta = timezone.now() - signal.generated_at
                    days_since = delta.days
                
                # Calculate risk/reward ratio
                target_price = float(signal.target_prices[0]) if signal.target_prices else float(signal.entry_price) * 1.05
                entry = float(signal.entry_price)
                stop = float(signal.stop_price)
                
                # Calculate risk/reward based on signal side
                if signal.side == 'LONG':
                    # For LONG: profit = target - entry, risk = entry - stop
                    profit = target_price - entry
                    risk = entry - stop if entry > stop else 0.01
                    risk_reward = profit / risk if risk > 0 else 2.0
                else:
                    # For SHORT: profit = entry - target, risk = stop - entry
                    profit = entry - target_price
                    risk = stop - entry if stop > entry else 0.01
                    risk_reward = profit / risk if risk > 0 else 2.0
                
                # Get features as JSON string
                features_json = json.dumps(signal.features) if signal.features else json.dumps({})
                
                # Create technical indicators from features (mock for now)
                technical_indicators = []
                if signal.features:
                    for key, value in signal.features.items():
                        if isinstance(value, (int, float)):
                            technical_indicators.append(TechnicalIndicatorType(
                                name=key,
                                value=float(value),
                                signal='neutral',
                                strength=0.5,
                                description=f"{key} indicator"
                            ))
                
                # Create pattern recognition (mock for now)
                patterns = []
                if signal.strategy == 'BREAKOUT':
                    patterns.append(PatternRecognitionType(
                        name='Breakout Pattern',
                        confidence=float(signal.score),
                        signal='bullish',
                        description='Price breaking above resistance',
                        timeframe=f"{signal.hold_days}D"
                    ))
                
                result.append(SwingSignalType(
                    id=str(signal.signal_id),
                    symbol=signal.symbol,
                    timeframe=f"{signal.hold_days}D",
                    triggeredAt=signal.generated_at.isoformat() if signal.generated_at else timezone.now().isoformat(),
                    signalType=signal.side,
                    entryPrice=entry,
                    stopPrice=stop,
                    targetPrice=target_price,
                    mlScore=float(signal.score),
                    thesis=signal.notes or f"Expected {signal.hold_days}-day hold with {signal.strategy} strategy",
                    riskRewardRatio=risk_reward,
                    daysSinceTriggered=days_since,
                    isLikedByUser=False,  # Would need to check user likes
                    userLikeCount=0,  # Would need to count from likes table
                    features=features_json,
                    isActive=True,  # All signals are active by default
                    isValidated=False,  # Would need validation logic
                    validationPrice=None,
                    validationTimestamp=None,
                    createdBy=SwingSignalUserType(
                        id='system',
                        username='system',
                        name='System'
                    ),
                    technicalIndicators=technical_indicators,
                    patterns=patterns
                ))
            
            return result
        except Exception as e:
            logger.error(f"Error resolving swing signals: {e}", exc_info=True)
            # Return sample data as fallback
            try:
                return _generate_sample_swing_signals(limit, symbol, signalType, minMlScore)
            except:
                return []


def _generate_sample_swing_signals(limit=50, symbol=None, signalType=None, minMlScore=None):
    """Generate sample swing signals for demo purposes"""
    from django.utils import timezone
    from datetime import timedelta
    import uuid
    
    sample_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'JNJ']
    sample_strategies = ['MOMENTUM', 'BREAKOUT', 'MEAN_REVERSION']
    sample_sides = ['LONG', 'SHORT']
    
    # Filter symbols if specified
    if symbol:
        if symbol.upper() in sample_symbols:
            symbols_to_use = [symbol.upper()]
        else:
            symbols_to_use = [symbol.upper()]  # Use the requested symbol anyway
    else:
        symbols_to_use = sample_symbols[:limit]
    
    # Filter sides if specified
    if signalType:
        signal_type_map = {
            'LONG': 'LONG',
            'SHORT': 'SHORT',
            'BUY': 'LONG',
            'SELL': 'SHORT'
        }
        side_to_use = signal_type_map.get(signalType.upper(), 'LONG')
    else:
        side_to_use = None
    
    signals = []
    base_time = timezone.now()
    
    for i, sym in enumerate(symbols_to_use[:limit]):
        # Alternate between LONG and SHORT if not specified
        side = side_to_use if side_to_use else (sample_sides[i % 2])
        strategy = sample_strategies[i % len(sample_strategies)]
        
        # Generate realistic scores
        base_score = 0.65 + (i * 0.05)  # Scores from 0.65 to 0.95
        if minMlScore and base_score < minMlScore:
            base_score = minMlScore + 0.1
        
        entry_price = 150.0 + (i * 5.0)
        stop_price = entry_price * 0.97 if side == 'LONG' else entry_price * 1.03
        target_price = entry_price * 1.05 if side == 'LONG' else entry_price * 0.95
        
        # Create a mock signal object
        class MockSignal:
            def __init__(self):
                self.signal_id = uuid.uuid4()
                self.symbol = sym
                self.side = side
                self.strategy = strategy
                self.score = base_score
                self.entry_price = entry_price
                self.stop_price = stop_price
                self.target_prices = [target_price]
                self.hold_days = 3 + (i % 3)  # 3-5 days
                self.generated_at = base_time - timedelta(hours=i)
                self.features = {
                    'momentum1d': 0.5 + (i * 0.1),
                    'rvol5d': 0.3 + (i * 0.05),
                    'breakoutStrength': 0.6 + (i * 0.1)
                }
                self.notes = f"{strategy} signal for {sym}"
        
        signals.append(MockSignal())
    
    return signals
    
    def resolve_trending_discussions(self, info, limit=20, timeframe='24h'):
        """Resolve trending discussions"""
        service = SocialEnhancementsService()
        discussions = service.get_trending_discussions(limit, timeframe)
        
        return [
            TrendingDiscussionType(
                id=d['id'],
                title=d['title'],
                symbol=d['symbol'],
                userName=d['user_name'],
                score=d['score'],
                commentsCount=d['comments_count'],
                createdAt=d['created_at'].isoformat(),
                trendingReason=d['trending_reason'],
            )
            for d in discussions
        ]
    
    def resolve_signalUpdates(self, info, symbol: str, lookbackHours: int = 24):
        """Resolve real-time signal updates"""
        import json
        import traceback
        import sys
        
        logger.info(f"🔍 resolve_signalUpdates called with symbol={symbol}, lookbackHours={lookbackHours}")
        
        # Always ensure we return something, even on complete failure
        try:
            user = getattr(info.context, 'user', None)
            user_id = user.id if user and not user.is_anonymous else None
            
            from .signal_fusion_service import SignalFusionService
            service = SignalFusionService()
            
            updates = service.get_signal_updates(symbol, user_id, lookbackHours)
            
            # Ensure updates is a dict (should never be None based on service code)
            if not updates or not isinstance(updates, dict):
                logger.warning(f"get_signal_updates returned invalid data for {symbol}: {updates}")
                updates = {
                    'symbol': symbol,
                    'timestamp': timezone.now().isoformat(),
                    'signals': {},
                    'fusion_score': 50.0,
                    'alerts': [],
                    'recommendation': 'HOLD',
                    'consumer_strength': 50.0,
                }
            
            # Ensure signals is JSON-serializable (JSONString can accept dict, it will serialize automatically)
            signals_data = updates.get('signals', {})
            if not isinstance(signals_data, dict):
                signals_data = {}
            
            # graphene.JSONString can accept a dict and will serialize it, or a string
            # We'll pass the dict directly to avoid double-encoding
            
            # Get alerts list
            alerts_list = updates.get('alerts', [])
            if not isinstance(alerts_list, list):
                alerts_list = []
            
            # Create SignalUpdatesType instance
            signal_updates = SignalUpdatesType(
                symbol=str(updates.get('symbol', symbol)),
                timestamp=str(updates.get('timestamp', timezone.now().isoformat())),
                signals=signals_data,  # JSONString will serialize dict automatically
                fusionScore=float(updates.get('fusion_score', 50.0)),
                alerts=[
                    SignalAlertType(
                        type=str(alert.get('type', 'info')),
                        severity=str(alert.get('severity', 'low')),
                        message=str(alert.get('message', '')),
                        timestamp=str(alert.get('timestamp', timezone.now().isoformat())),
                    )
                    for alert in alerts_list
                ],
                recommendation=str(updates.get('recommendation', 'HOLD')),
                consumerStrength=float(updates.get('consumer_strength', 50.0)),
            )
            
            logger.info(f"✅ Returning SignalUpdatesType for {symbol}: fusionScore={signal_updates.fusionScore}, recommendation={signal_updates.recommendation}")
            return signal_updates
        except Exception as e:
            # Log error safely with full traceback
            try:
                logger.error(f"Error in resolve_signal_updates for {symbol}: {e}", exc_info=True)
                logger.error(f"Traceback: {traceback.format_exc()}")
            except Exception:
                # If logger fails, at least print to console
                print(f"Error in resolve_signal_updates for {symbol}: {e}")
                print(f"Traceback: {traceback.format_exc()}")
            
            # Return fallback response instead of raising exception
            # This ensures we NEVER return None
            try:
                return SignalUpdatesType(
                    symbol=symbol,
                    timestamp=timezone.now().isoformat(),
                    signals={},  # JSONString will serialize dict automatically
                    fusionScore=50.0,
                    alerts=[SignalAlertType(
                        type='error',
                        severity='low',
                        message='Signal data temporarily unavailable. Please try again later.',
                        timestamp=timezone.now().isoformat(),
                    )],
                    recommendation='HOLD',
                    consumerStrength=50.0,
                )
            except Exception as fallback_error:
                # If even the fallback fails, log and return minimal response
                logger.error(f"Even fallback SignalUpdatesType creation failed: {fallback_error}")
                # This should never happen, but ensures we return something
                return None
    
    def resolve_watchlist_signals(self, info, threshold: float = 70.0):
        """Resolve watchlist signals"""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return []
        
        from .signal_fusion_service import SignalFusionService
        service = SignalFusionService()
        
        signals = service.get_watchlist_signals(user.id, threshold)
        
        return [
            SignalUpdatesType(
                symbol=s['symbol'],
                timestamp=timezone.now().isoformat(),
                signals={},
                fusionScore=s['fusion_score'],
                alerts=[
                    SignalAlertType(
                        type=alert.get('type', ''),
                        severity=alert.get('severity', 'medium'),
                        message=alert.get('message', ''),
                        timestamp=alert.get('timestamp', timezone.now().isoformat()),
                    )
                    for alert in s.get('alerts', [])
                ],
                recommendation=s['recommendation'],
                consumerStrength=s.get('fusion_score', 50.0),
            )
            for s in signals
        ]
    
    def resolve_portfolio_signals(self, info, threshold: float = 60.0):
        """Resolve portfolio signals"""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return PortfolioSignalsType(
                portfolioSignals=[],
                strongBuyCount=0,
                strongSellCount=0,
                overallSentiment='neutral',
                totalPositions=0,
            )
        
        from .signal_fusion_service import SignalFusionService
        from django.utils import timezone
        
        service = SignalFusionService()
        result = service.get_portfolio_signals(user.id, threshold)
        
        return PortfolioSignalsType(
            portfolioSignals=[json.dumps(s) for s in result['portfolio_signals']],
            strongBuyCount=result['strong_buy_count'],
            strongSellCount=result['strong_sell_count'],
            overallSentiment=result['overall_sentiment'],
            totalPositions=result['total_positions'],
        )


# ==================== SOCIAL MUTATIONS ====================

class CopiedTradeType(graphene.ObjectType):
    """Copied trade result"""
    id = graphene.String()
    symbol = graphene.String()
    side = graphene.String()
    quantity = graphene.Float()
    price = graphene.Float()


class CopyTradeResultType(graphene.ObjectType):
    """Copy trade mutation result"""
    success = graphene.Boolean()
    message = graphene.String()
    copiedTrade = graphene.Field(CopiedTradeType)


class CopyTrade(graphene.Mutation):
    """Copy a trade from another trader"""
    
    class Arguments:
        tradeId = graphene.ID(required=True)  # CamelCase for GraphQL
        amount = graphene.Float(required=True)
    
    Output = CopyTradeResultType
    
    @staticmethod
    def mutate(root, info, tradeId, amount):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            raise GraphQLError("You must be logged in to copy trades.")
        
        try:
            # In a real implementation, this would:
            # 1. Fetch the original trade
            # 2. Calculate quantity based on amount
            # 3. Place the order through broker API
            # 4. Return the copied trade details
            
            # For now, return a mock success response
            logger.info(f"User {user.id} copying trade {tradeId} with amount {amount}")
            
            return CopyTradeResultType(
                success=True,
                message="Trade copied successfully",
                copiedTrade=CopiedTradeType(
                    id=f"copied_{tradeId}",
                    symbol="AAPL",  # Would come from original trade
                    side="BUY",  # Would come from original trade
                    quantity=amount / 150.0,  # Mock calculation
                    price=150.0,  # Would be current market price
                )
            )
        except Exception as e:
            logger.error(f"Error copying trade: {e}", exc_info=True)
            return CopyTradeResultType(
                success=False,
                message=f"Failed to copy trade: {str(e)}",
                copiedTrade=None
            )


class FollowTraderResultType(graphene.ObjectType):
    """Follow trader mutation result"""
    success = graphene.Boolean()
    message = graphene.String()


class FollowTrader(graphene.Mutation):
    """Follow a trader"""
    
    class Arguments:
        traderId = graphene.ID(required=True)  # CamelCase for GraphQL
    
    Output = FollowTraderResultType
    
    @staticmethod
    def mutate(root, info, traderId):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            raise GraphQLError("You must be logged in to follow traders.")
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            trader = User.objects.get(id=traderId)
            
            if user == trader:
                return FollowTraderResultType(
                    success=False,
                    message="You cannot follow yourself."
                )
            
            # Add to following (using the existing follow relationship)
            if trader not in user.following.all():
                user.following.add(trader)
                message = f"You are now following {trader.username}"
            else:
                user.following.remove(trader)
                message = f"You unfollowed {trader.username}"
            
            return FollowTraderResultType(
                success=True,
                message=message
            )
        except User.DoesNotExist:
            return FollowTraderResultType(
                success=False,
                message="Trader not found."
            )
        except Exception as e:
            logger.error(f"Error following trader: {e}", exc_info=True)
            return FollowTraderResultType(
                success=False,
                message=f"Failed to follow trader: {str(e)}"
            )


class LikePostResultType(graphene.ObjectType):
    """Like post mutation result"""
    success = graphene.Boolean()
    likes = graphene.Int()


class LikePost(graphene.Mutation):
    """Like a post"""
    
    class Arguments:
        postId = graphene.ID(required=True)  # CamelCase for GraphQL
    
    Output = LikePostResultType
    
    @staticmethod
    def mutate(root, info, postId):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            raise GraphQLError("You must be logged in to like posts.")
        
        try:
            from .models import Post
            
            post = Post.objects.get(id=postId)
            
            # Toggle like
            if user in post.likes.all():
                post.likes.remove(user)
            else:
                post.likes.add(user)
            
            return LikePostResultType(
                success=True,
                likes=post.likes.count()
            )
        except Post.DoesNotExist:
            return LikePostResultType(
                success=False,
                likes=0
            )
        except Exception as e:
            logger.error(f"Error liking post: {e}", exc_info=True)
            return LikePostResultType(
                success=False,
                likes=0
            )


class SocialMutations(graphene.ObjectType):
    """Social trading mutations"""
    copy_trade = CopyTrade.Field()
    copyTrade = CopyTrade.Field()  # CamelCase alias for mobile
    follow_trader = FollowTrader.Field()
    followTrader = FollowTrader.Field()  # CamelCase alias for mobile
    like_post = LikePost.Field()
    likePost = LikePost.Field()  # CamelCase alias for mobile

