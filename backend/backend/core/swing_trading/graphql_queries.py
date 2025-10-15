"""
GraphQL Queries for Swing Trading Features
"""
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from core.models import (
    OHLCV, Signal, SignalLike, SignalComment, TraderScore, 
    BacktestStrategy, BacktestResult, SwingWatchlist
)
from .graphql_types import *
from .risk_management import RiskManager
from .backtesting import BacktestEngine, BacktestConfig, run_strategy_backtest

logger = logging.getLogger(__name__)


class SwingTradingQuery(graphene.ObjectType):
    """Swing Trading GraphQL Queries"""
    
    # Signal queries
    signals = graphene.List(
        SignalType,
        symbol=graphene.String(),
        signal_type=graphene.String(),
        min_ml_score=graphene.Float(),
        max_ml_score=graphene.Float(),
        is_active=graphene.Boolean(),
        limit=graphene.Int(),
        offset=graphene.Int()
    )
    
    signal = graphene.Field(SignalType, id=graphene.ID(required=True))
    
    signal_analysis = graphene.Field(
        SignalAnalysisType,
        signal_id=graphene.ID(required=True)
    )
    
    signal_stats = graphene.Field(SignalStatsType)
    
    # OHLCV queries
    ohlcv_data = graphene.List(
        OHLCVType,
        symbol=graphene.String(required=True),
        timeframe=graphene.String(),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
        limit=graphene.Int()
    )
    
    # Risk management queries
    calculate_position_size = graphene.Field(
        RiskAnalysisType,
        account_equity=graphene.Float(required=True),
        entry_price=graphene.Float(required=True),
        stop_price=graphene.Float(required=True),
        risk_per_trade=graphene.Float(),
        max_position_pct=graphene.Float(),
        confidence=graphene.Float()
    )
    
    calculate_dynamic_stop = graphene.Field(
        RiskAnalysisType,
        entry_price=graphene.Float(required=True),
        atr=graphene.Float(required=True),
        atr_multiplier=graphene.Float(),
        support_level=graphene.Float(),
        resistance_level=graphene.Float(),
        signal_type=graphene.String()
    )
    
    calculate_target_price = graphene.Field(
        RiskAnalysisType,
        entry_price=graphene.Float(required=True),
        stop_price=graphene.Float(required=True),
        risk_reward_ratio=graphene.Float(),
        atr=graphene.Float(),
        resistance_level=graphene.Float(),
        support_level=graphene.Float(),
        signal_type=graphene.String()
    )
    
    portfolio_heat = graphene.Field(
        PortfolioHeatType,
        positions=graphene.JSONString()
    )
    
    # Backtesting queries
    backtest_strategies = graphene.List(
        BacktestStrategyType,
        user_id=graphene.ID(),
        is_public=graphene.Boolean(),
        strategy_type=graphene.String()
    )
    
    backtest_strategy = graphene.Field(
        BacktestStrategyType,
        id=graphene.ID(required=True)
    )
    
    backtest_results = graphene.List(
        BacktestResultType,
        strategy_id=graphene.ID(),
        symbol=graphene.String(),
        limit=graphene.Int()
    )
    
    run_backtest = graphene.Field(
        BacktestMetricsType,
        strategy_name=graphene.String(required=True),
        symbol=graphene.String(required=True),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
        config=graphene.Argument(BacktestConfigType),
        params=graphene.Argument(StrategyParamsType)
    )
    
    # Watchlist queries
    swing_watchlists = graphene.List(SwingWatchlistType, user_id=graphene.ID())
    swing_watchlist = graphene.Field(SwingWatchlistType, id=graphene.ID(required=True))
    
    # Trader score queries
    trader_scores = graphene.List(
        TraderScoreType,
        limit=graphene.Int(),
        order_by=graphene.String()
    )
    
    trader_score = graphene.Field(
        TraderScoreType,
        user_id=graphene.ID(required=True)
    )
    
    leaderboard = graphene.List(
        LeaderboardEntryType,
        category=graphene.String(),
        limit=graphene.Int()
    )
    
    # Market data queries
    market_scanner = graphene.List(
        MarketScannerType,
        signal_types=graphene.List(graphene.String),
        min_ml_score=graphene.Float(),
        min_volume=graphene.Float(),
        sectors=graphene.List(graphene.String)
    )
    
    market_conditions = graphene.Field(MarketConditionType)
    
    # Social features
    signal_comments = graphene.List(
        SignalCommentType,
        signal_id=graphene.ID(required=True)
    )
    
    trending_strategies = graphene.List(
        TrendingStrategyType,
        limit=graphene.Int()
    )
    
    social_feed = graphene.List(
        FeedItemType,
        limit=graphene.Int(),
        offset=graphene.Int()
    )
    
    # Performance queries
    trader_performance = graphene.Field(
        TraderPerformanceType,
        user_id=graphene.ID(required=True),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime()
    )
    
    strategy_performance = graphene.List(
        StrategyPerformanceType,
        strategy_names=graphene.List(graphene.String),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime()
    )
    
    performance_comparison = graphene.Field(
        PerformanceComparisonType,
        strategy_name=graphene.String(required=True),
        benchmark=graphene.String(required=True),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime()
    )
    
    # Alert queries
    alerts = graphene.List(
        AlertType,
        user_id=graphene.ID(),
        is_active=graphene.Boolean()
    )
    
    notifications = graphene.List(
        NotificationType,
        user_id=graphene.ID(),
        is_read=graphene.Boolean(),
        limit=graphene.Int()
    )
    
    # Market insights
    market_insights = graphene.List(
        MarketInsightType,
        insight_type=graphene.String(),
        limit=graphene.Int()
    )
    
    def resolve_signals(self, info, **kwargs):
        """Resolve signals with filtering"""
        try:
            user = info.context.user
            if not user.is_authenticated:
                return []
            
            queryset = Signal.objects.all()
            
            # Apply filters
            if kwargs.get('symbol'):
                queryset = queryset.filter(symbol=kwargs['symbol'])
            
            if kwargs.get('signal_type'):
                queryset = queryset.filter(signal_type=kwargs['signal_type'])
            
            if kwargs.get('min_ml_score') is not None:
                queryset = queryset.filter(ml_score__gte=kwargs['min_ml_score'])
            
            if kwargs.get('max_ml_score') is not None:
                queryset = queryset.filter(ml_score__lte=kwargs['max_ml_score'])
            
            if kwargs.get('is_active') is not None:
                queryset = queryset.filter(is_active=kwargs['is_active'])
            
            # Order by triggered_at descending
            queryset = queryset.order_by('-triggered_at')
            
            # Apply pagination
            limit = kwargs.get('limit', 50)
            offset = kwargs.get('offset', 0)
            
            return queryset[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Error resolving signals: {e}")
            return []
    
    def resolve_signal(self, info, id):
        """Resolve single signal"""
        try:
            return Signal.objects.get(id=id)
        except Signal.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error resolving signal: {e}")
            return None
    
    def resolve_signal_analysis(self, info, signal_id):
        """Resolve signal analysis"""
        try:
            signal = Signal.objects.get(id=signal_id)
            
            # Get risk analysis
            risk_manager = RiskManager()
            risk_analysis = risk_manager.calculate_position_size(
                account_equity=10000,  # Default account size
                entry_price=float(signal.entry_price),
                stop_price=float(signal.stop_price) if signal.stop_price else float(signal.entry_price) * 0.95,
                risk_per_trade=0.01
            )
            
            # Get similar signals
            similar_signals = Signal.objects.filter(
                symbol=signal.symbol,
                signal_type=signal.signal_type
            ).exclude(id=signal.id)[:5]
            
            return SignalAnalysisType(
                signal=signal,
                risk_analysis=RiskAnalysisType(**risk_analysis),
                confidence_score=float(signal.ml_score),
                market_conditions={},
                similar_signals=similar_signals
            )
            
        except Exception as e:
            logger.error(f"Error resolving signal analysis: {e}")
            return None
    
    def resolve_signal_stats(self, info):
        """Resolve signal statistics"""
        try:
            total_signals = Signal.objects.count()
            active_signals = Signal.objects.filter(is_active=True).count()
            validated_signals = Signal.objects.filter(is_validated=True).count()
            
            avg_ml_score = Signal.objects.aggregate(avg_score=Avg('ml_score'))['avg_score'] or 0
            avg_risk_reward = Signal.objects.filter(
                risk_reward_ratio__isnull=False
            ).aggregate(avg_rr=Avg('risk_reward_ratio'))['avg_rr'] or 0
            
            # Top performing symbols
            top_symbols = Signal.objects.values('symbol').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            top_performing_symbols = [item['symbol'] for item in top_symbols]
            
            # Signal type distribution
            type_dist = Signal.objects.values('signal_type').annotate(
                count=Count('id')
            )
            signal_type_distribution = {item['signal_type']: item['count'] for item in type_dist}
            
            # Daily signal count (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            daily_counts = []
            for i in range(30):
                date = thirty_days_ago + timedelta(days=i)
                count = Signal.objects.filter(
                    triggered_at__date=date.date()
                ).count()
                daily_counts.append(count)
            
            return SignalStatsType(
                total_signals=total_signals,
                active_signals=active_signals,
                validated_signals=validated_signals,
                avg_ml_score=float(avg_ml_score),
                avg_risk_reward=float(avg_risk_reward),
                top_performing_symbols=top_performing_symbols,
                signal_type_distribution=signal_type_distribution,
                daily_signal_count=daily_counts
            )
            
        except Exception as e:
            logger.error(f"Error resolving signal stats: {e}")
            return None
    
    def resolve_ohlcv_data(self, info, symbol, **kwargs):
        """Resolve OHLCV data"""
        try:
            queryset = OHLCV.objects.filter(symbol=symbol)
            
            if kwargs.get('timeframe'):
                queryset = queryset.filter(timeframe=kwargs['timeframe'])
            
            if kwargs.get('start_date'):
                queryset = queryset.filter(timestamp__gte=kwargs['start_date'])
            
            if kwargs.get('end_date'):
                queryset = queryset.filter(timestamp__lte=kwargs['end_date'])
            
            queryset = queryset.order_by('-timestamp')
            
            limit = kwargs.get('limit', 100)
            return queryset[:limit]
            
        except Exception as e:
            logger.error(f"Error resolving OHLCV data: {e}")
            return []
    
    def resolve_calculate_position_size(self, info, **kwargs):
        """Calculate position size"""
        try:
            risk_manager = RiskManager()
            result = risk_manager.calculate_position_size(
                account_equity=kwargs['account_equity'],
                entry_price=kwargs['entry_price'],
                stop_price=kwargs['stop_price'],
                risk_per_trade=kwargs.get('risk_per_trade', 0.01),
                max_position_pct=kwargs.get('max_position_pct', 0.1)
            )
            
            return RiskAnalysisType(**result)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return None
    
    def resolve_calculate_dynamic_stop(self, info, **kwargs):
        """Calculate dynamic stop loss"""
        try:
            risk_manager = RiskManager()
            result = risk_manager.calculate_dynamic_stop_loss(
                entry_price=kwargs['entry_price'],
                atr=kwargs['atr'],
                atr_multiplier=kwargs.get('atr_multiplier', 1.5),
                support_level=kwargs.get('support_level'),
                resistance_level=kwargs.get('resistance_level'),
                signal_type=kwargs.get('signal_type', 'long')
            )
            
            return RiskAnalysisType(**result)
            
        except Exception as e:
            logger.error(f"Error calculating dynamic stop: {e}")
            return None
    
    def resolve_calculate_target_price(self, info, **kwargs):
        """Calculate target price"""
        try:
            risk_manager = RiskManager()
            result = risk_manager.calculate_target_price(
                entry_price=kwargs['entry_price'],
                stop_price=kwargs['stop_price'],
                risk_reward_ratio=kwargs.get('risk_reward_ratio', 2.0),
                atr=kwargs.get('atr'),
                resistance_level=kwargs.get('resistance_level'),
                support_level=kwargs.get('support_level'),
                signal_type=kwargs.get('signal_type', 'long')
            )
            
            return RiskAnalysisType(**result)
            
        except Exception as e:
            logger.error(f"Error calculating target price: {e}")
            return None
    
    def resolve_portfolio_heat(self, info, positions):
        """Calculate portfolio heat"""
        try:
            risk_manager = RiskManager()
            result = risk_manager.calculate_portfolio_heat(positions or [])
            
            return PortfolioHeatType(**result)
            
        except Exception as e:
            logger.error(f"Error calculating portfolio heat: {e}")
            return None
    
    def resolve_backtest_strategies(self, info, **kwargs):
        """Resolve backtest strategies"""
        try:
            user = info.context.user
            queryset = BacktestStrategy.objects.all()
            
            if kwargs.get('user_id'):
                queryset = queryset.filter(user_id=kwargs['user_id'])
            elif user.is_authenticated:
                # Show user's strategies and public strategies
                queryset = queryset.filter(
                    Q(user=user) | Q(is_public=True)
                )
            else:
                # Show only public strategies
                queryset = queryset.filter(is_public=True)
            
            if kwargs.get('is_public') is not None:
                queryset = queryset.filter(is_public=kwargs['is_public'])
            
            if kwargs.get('strategy_type'):
                queryset = queryset.filter(strategy_type=kwargs['strategy_type'])
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Error resolving backtest strategies: {e}")
            return []
    
    def resolve_backtest_strategy(self, info, id):
        """Resolve single backtest strategy"""
        try:
            return BacktestStrategy.objects.get(id=id)
        except BacktestStrategy.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error resolving backtest strategy: {e}")
            return None
    
    def resolve_backtest_results(self, info, **kwargs):
        """Resolve backtest results"""
        try:
            queryset = BacktestResult.objects.all()
            
            if kwargs.get('strategy_id'):
                queryset = queryset.filter(strategy_id=kwargs['strategy_id'])
            
            if kwargs.get('symbol'):
                queryset = queryset.filter(symbol=kwargs['symbol'])
            
            queryset = queryset.order_by('-created_at')
            
            limit = kwargs.get('limit', 20)
            return queryset[:limit]
            
        except Exception as e:
            logger.error(f"Error resolving backtest results: {e}")
            return []
    
    def resolve_run_backtest(self, info, **kwargs):
        """Run backtest"""
        try:
            # This would typically be run asynchronously
            # For now, return a placeholder
            return BacktestMetricsType(
                total_return=0.0,
                annualized_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0.0,
                avg_loss=0.0,
                initial_capital=10000.0,
                final_capital=10000.0,
                equity_curve=[],
                daily_returns=[]
            )
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return None
    
    def resolve_swing_watchlists(self, info, **kwargs):
        """Resolve swing watchlists"""
        try:
            user = info.context.user
            if not user.is_authenticated:
                return []
            
            queryset = SwingWatchlist.objects.filter(user=user)
            
            if kwargs.get('user_id'):
                queryset = queryset.filter(user_id=kwargs['user_id'])
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Error resolving swing watchlists: {e}")
            return []
    
    def resolve_swing_watchlist(self, info, id):
        """Resolve single swing watchlist"""
        try:
            return SwingWatchlist.objects.get(id=id)
        except SwingWatchlist.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error resolving swing watchlist: {e}")
            return None
    
    def resolve_trader_scores(self, info, **kwargs):
        """Resolve trader scores"""
        try:
            queryset = TraderScore.objects.all()
            
            order_by = kwargs.get('order_by', '-overall_score')
            queryset = queryset.order_by(order_by)
            
            limit = kwargs.get('limit', 100)
            return queryset[:limit]
            
        except Exception as e:
            logger.error(f"Error resolving trader scores: {e}")
            return []
    
    def resolve_trader_score(self, info, user_id):
        """Resolve single trader score"""
        try:
            return TraderScore.objects.get(user_id=user_id)
        except TraderScore.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error resolving trader score: {e}")
            return None
    
    def resolve_leaderboard(self, info, **kwargs):
        """Resolve leaderboard"""
        try:
            category = kwargs.get('category', 'overall')
            limit = kwargs.get('limit', 50)
            
            if category == 'accuracy':
                queryset = TraderScore.objects.order_by('-accuracy_score')
            elif category == 'consistency':
                queryset = TraderScore.objects.order_by('-consistency_score')
            else:
                queryset = TraderScore.objects.order_by('-overall_score')
            
            leaderboard = []
            for i, score in enumerate(queryset[:limit]):
                leaderboard.append(LeaderboardEntryType(
                    user=score.user,
                    trader_score=score,
                    rank=i + 1,
                    category=category
                ))
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error resolving leaderboard: {e}")
            return []
    
    def resolve_market_scanner(self, info, **kwargs):
        """Resolve market scanner results"""
        try:
            # This would typically query real-time market data
            # For now, return recent signals as scanner results
            queryset = Signal.objects.filter(is_active=True)
            
            if kwargs.get('signal_types'):
                queryset = queryset.filter(signal_type__in=kwargs['signal_types'])
            
            if kwargs.get('min_ml_score'):
                queryset = queryset.filter(ml_score__gte=kwargs['min_ml_score'])
            
            queryset = queryset.order_by('-triggered_at')[:50]
            
            scanner_results = []
            for signal in queryset:
                scanner_results.append(MarketScannerType(
                    symbol=signal.symbol,
                    current_price=float(signal.entry_price),
                    signal_type=signal.signal_type,
                    ml_score=float(signal.ml_score),
                    risk_reward_ratio=float(signal.risk_reward_ratio) if signal.risk_reward_ratio else 0,
                    volume_surge=1.0,  # Would come from real-time data
                    rsi=50.0,  # Would come from real-time data
                    ema_trend='neutral',  # Would come from real-time data
                    market_cap=0.0,  # Would come from real-time data
                    sector='Unknown',  # Would come from real-time data
                    last_updated=signal.triggered_at
                ))
            
            return scanner_results
            
        except Exception as e:
            logger.error(f"Error resolving market scanner: {e}")
            return []
    
    def resolve_market_conditions(self, info):
        """Resolve market conditions"""
        try:
            # This would typically analyze current market data
            # For now, return default conditions
            return MarketConditionType(
                volatility_regime='medium',
                trend_direction='sideways',
                volume_profile='normal',
                market_sentiment='neutral',
                vix_level=20.0,
                sector_rotation={}
            )
            
        except Exception as e:
            logger.error(f"Error resolving market conditions: {e}")
            return None
    
    def resolve_signal_comments(self, info, signal_id):
        """Resolve signal comments"""
        try:
            return SignalComment.objects.filter(signal_id=signal_id).order_by('created_at')
        except Exception as e:
            logger.error(f"Error resolving signal comments: {e}")
            return []
    
    def resolve_trending_strategies(self, info, **kwargs):
        """Resolve trending strategies"""
        try:
            limit = kwargs.get('limit', 10)
            strategies = BacktestStrategy.objects.filter(
                is_public=True
            ).order_by('-likes_count', '-created_at')[:limit]
            
            trending = []
            for strategy in strategies:
                trending.append(TrendingStrategyType(
                    strategy=strategy,
                    performance_score=float(strategy.total_return or 0),
                    popularity_score=float(strategy.likes_count),
                    trending_score=float(strategy.likes_count + strategy.shares_count),
                    followers_count=0  # Would need follower model
                ))
            
            return trending
            
        except Exception as e:
            logger.error(f"Error resolving trending strategies: {e}")
            return []
    
    def resolve_social_feed(self, info, **kwargs):
        """Resolve social feed"""
        try:
            user = info.context.user
            if not user.is_authenticated:
                return []
            
            # This would typically combine signals, backtest results, etc.
            # For now, return recent signals
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            signals = Signal.objects.filter(is_active=True).order_by('-triggered_at')[offset:offset + limit]
            
            feed_items = []
            for signal in signals:
                feed_items.append(FeedItemType(
                    id=signal.id,
                    type='signal',
                    content=signal,
                    user=signal.created_by,
                    created_at=signal.triggered_at,
                    likes_count=signal.likes_count,
                    comments_count=signal.comments_count,
                    shares_count=signal.shares_count,
                    is_liked_by_user=False  # Would check user's likes
                ))
            
            return feed_items
            
        except Exception as e:
            logger.error(f"Error resolving social feed: {e}")
            return []
    
    def resolve_trader_performance(self, info, user_id, **kwargs):
        """Resolve trader performance"""
        try:
            # This would calculate performance from trade history
            # For now, return placeholder data
            return TraderPerformanceType(
                user_id=user_id,
                total_signals=0,
                win_rate=0.0,
                avg_return=0.0,
                best_trade=0.0,
                worst_trade=0.0,
                total_pnl=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                consistency_score=0.0,
                risk_score=0.0
            )
            
        except Exception as e:
            logger.error(f"Error resolving trader performance: {e}")
            return None
    
    def resolve_strategy_performance(self, info, **kwargs):
        """Resolve strategy performance"""
        try:
            # This would analyze performance of different strategies
            # For now, return placeholder data
            return []
            
        except Exception as e:
            logger.error(f"Error resolving strategy performance: {e}")
            return []
    
    def resolve_performance_comparison(self, info, **kwargs):
        """Resolve performance comparison"""
        try:
            # This would compare strategy vs benchmark
            # For now, return placeholder data
            return PerformanceComparisonType(
                benchmark=kwargs['benchmark'],
                strategy_performance=0.0,
                benchmark_performance=0.0,
                outperformance=0.0,
                correlation=0.0,
                beta=1.0,
                alpha=0.0,
                tracking_error=0.0,
                information_ratio=0.0
            )
            
        except Exception as e:
            logger.error(f"Error resolving performance comparison: {e}")
            return None
    
    def resolve_alerts(self, info, **kwargs):
        """Resolve alerts"""
        try:
            user = info.context.user
            if not user.is_authenticated:
                return []
            
            # This would query user's alerts
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error resolving alerts: {e}")
            return []
    
    def resolve_notifications(self, info, **kwargs):
        """Resolve notifications"""
        try:
            user = info.context.user
            if not user.is_authenticated:
                return []
            
            # This would query user's notifications
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error resolving notifications: {e}")
            return []
    
    def resolve_market_insights(self, info, **kwargs):
        """Resolve market insights"""
        try:
            # This would provide AI-generated market insights
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error resolving market insights: {e}")
            return []
