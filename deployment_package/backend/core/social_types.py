"""
GraphQL Types for Enhanced Social Features
"""
import graphene
import json
from typing import List, Dict, Any
from django.utils import timezone
from .social_enhancements import SocialEnhancementsService
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


class SocialQueries(graphene.ObjectType):
    """Enhanced social feature queries"""
    
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
    
    def resolve_portfolio_leaderboard(self, info, timeframe='all_time', limit=50):
        """Resolve portfolio leaderboard"""
        service = SocialEnhancementsService()
        leaderboard = service.get_portfolio_leaderboard(timeframe, limit)
        
        return [
            LeaderboardEntryType(
                userId=entry['user_id'],
                userName=entry['user_name'],
                userEmail=entry['user_email'],
                totalReturnPct=entry['total_return_pct'],
                totalValue=entry['total_value'],
                rank=entry['rank'],
                holdingsCount=entry['holdings_count'],
                bestPerformer=entry['best_performer'],
                worstPerformer=entry['worst_performer'],
            )
            for entry in leaderboard
        ]
    
    def resolve_activity_feed(self, info, limit=50):
        """Resolve activity feed"""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return []
        
        service = SocialEnhancementsService()
        activities = service.get_user_activity_feed(user.id, limit)
        
        return [
            ActivityFeedItemType(
                type=activity['type'],
                userId=activity['user_id'],
                userName=activity['user_name'],
                timestamp=activity['timestamp'].isoformat(),
                content=activity['content'],
            )
            for activity in activities
        ]
    
    def resolve_portfolio_sharing_info(self, info):
        """Resolve portfolio sharing info"""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return PortfolioSharingInfoType(
                isPublic=False,
                shareToken='',
                totalFollowers=0,
                portfolioSummary={}
            )
        
        service = SocialEnhancementsService()
        info_data = service.get_portfolio_sharing_info(user.id)
        
        return PortfolioSharingInfoType(
            isPublic=info_data['is_public'],
            shareToken=info_data['share_token'],
            totalFollowers=info_data['total_followers'],
            portfolioSummary=info_data['portfolio_summary']
        )
    
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

