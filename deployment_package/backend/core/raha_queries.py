"""
RAHA GraphQL Queries
Queries for strategy catalog, user settings, signals, and backtests
"""
import graphene
import logging
from .raha_types import (
    StrategyType, StrategyVersionType, UserStrategySettingsType,
    RAHASignalType, RAHABacktestRunType, RAHAMetricsType
)
from .raha_models import Strategy, StrategyVersion, UserStrategySettings, RAHASignal, RAHABacktestRun
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class RAHAQueries(graphene.ObjectType):
    """GraphQL queries for RAHA system"""
    
    # Strategy Catalog
    strategies = graphene.List(
        StrategyType,
        market_type=graphene.String(required=False),
        category=graphene.String(required=False),
        description="Get available RAHA strategies"
    )
    
    strategy = graphene.Field(
        StrategyType,
        id=graphene.ID(required=False),
        slug=graphene.String(required=False),
        description="Get a specific strategy by ID or slug"
    )
    
    # User Strategy Settings
    user_strategy_settings = graphene.List(
        UserStrategySettingsType,
        description="Get user's enabled strategy settings"
    )
    
    # RAHA Signals
    raha_signals = graphene.List(
        RAHASignalType,
        symbol=graphene.String(required=False),
        timeframe=graphene.String(required=False),
        strategy_version_id=graphene.ID(required=False),
        limit=graphene.Int(required=False, default_value=100),
        description="Get RAHA signals (optionally filtered by symbol, timeframe, strategy)"
    )
    
    # Backtests
    backtest_run = graphene.Field(
        RAHABacktestRunType,
        id=graphene.ID(required=True),
        description="Get a specific backtest run by ID"
    )
    
    user_backtests = graphene.List(
        RAHABacktestRunType,
        strategy_version_id=graphene.ID(required=False),
        status=graphene.String(required=False),
        limit=graphene.Int(required=False),
        description="Get user's backtest runs"
    )
    
    # Performance Metrics
    raha_metrics = graphene.Field(
        RAHAMetricsType,
        strategy_version_id=graphene.ID(required=True),
        period=graphene.String(required=False, default_value="ALL_TIME"),
        description="Get aggregated performance metrics for a strategy"
    )
    
    def resolve_strategies(self, info, market_type=None, category=None):
        """Get available strategies with optional filters"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        queryset = Strategy.objects.filter(enabled=True)
        
        if market_type:
            queryset = queryset.filter(market_type=market_type)
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.all()
    
    def resolve_strategy(self, info, id=None, slug=None):
        """Get a specific strategy"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        if id:
            try:
                return Strategy.objects.get(id=id, enabled=True)
            except Strategy.DoesNotExist:
                return None
        elif slug:
            try:
                return Strategy.objects.get(slug=slug, enabled=True)
            except Strategy.DoesNotExist:
                return None
        
        return None
    
    def resolve_user_strategy_settings(self, info):
        """Get user's strategy settings"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        return UserStrategySettings.objects.filter(user=user, enabled=True).select_related('strategy_version', 'strategy_version__strategy')
    
    def resolve_raha_signals(self, info, symbol=None, timeframe=None, strategy_version_id=None, limit=100):
        """Get RAHA signals with optional filters"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        queryset = RAHASignal.objects.filter(user=user)
        
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)
        if strategy_version_id:
            queryset = queryset.filter(strategy_version_id=strategy_version_id)
        
        return queryset.select_related('strategy_version', 'strategy_version__strategy').order_by('-timestamp')[:limit]
    
    def resolve_backtest_run(self, info, id):
        """Get a specific backtest run"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            backtest = RAHABacktestRun.objects.get(id=id, user=user)
            return backtest
        except RAHABacktestRun.DoesNotExist:
            return None
    
    def resolve_user_backtests(self, info, strategy_version_id=None, status=None, limit=None):
        """Get user's backtest runs"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        queryset = RAHABacktestRun.objects.filter(user=user)
        
        if strategy_version_id:
            queryset = queryset.filter(strategy_version_id=strategy_version_id)
        if status:
            queryset = queryset.filter(status=status)
        
        queryset = queryset.select_related('strategy_version', 'strategy_version__strategy').order_by('-created_at')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    def resolve_raha_metrics(self, info, strategy_version_id, period="ALL_TIME"):
        """Get aggregated performance metrics for a strategy"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            from .signal_performance_models import StrategyPerformance
            from django.utils import timezone
            from datetime import timedelta
            
            # Map period to StrategyPerformance period
            period_map = {
                "DAILY": "DAILY",
                "WEEKLY": "WEEKLY",
                "MONTHLY": "MONTHLY",
                "ALL_TIME": "ALL_TIME",
            }
            perf_period = period_map.get(period.upper(), "ALL_TIME")
            
            # Get strategy performance (reuse existing model)
            # Note: We'll need to link RAHA signals to StrategyPerformance
            # For now, calculate from RAHASignal + SignalPerformance
            
            # Get user's signals for this strategy
            signals = RAHASignal.objects.filter(
                user=user,
                strategy_version_id=strategy_version_id
            )
            
            # Calculate basic metrics
            total_signals = signals.count()
            
            # Try to get linked SignalPerformance records
            from .signal_performance_models import SignalPerformance
            signal_ids = [s.id for s in signals]
            performances = SignalPerformance.objects.filter(
                signal__raha_signals__in=signal_ids
            ) if hasattr(SignalPerformance, 'signal') else []
            
            # For MVP, return basic structure
            # TODO: Calculate full metrics from SignalPerformance
            return RAHAMetricsType(
                strategy_version_id=strategy_version_id,
                period=period,
                total_signals=total_signals,
                winning_signals=0,  # TODO: Calculate from performances
                losing_signals=0,
                win_rate=0.0,
                total_pnl_dollars=0.0,
                total_pnl_percent=0.0,
                avg_pnl_per_signal=0.0,
                sharpe_ratio=None,
                sortino_ratio=None,
                max_drawdown=None,
                max_drawdown_duration_days=None,
                expectancy=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                avg_r_multiple=0.0,
                best_r_multiple=0.0,
                worst_r_multiple=0.0,
            )
        except Exception as e:
            logger.error(f"Error resolving RAHA metrics: {e}", exc_info=True)
            return None

