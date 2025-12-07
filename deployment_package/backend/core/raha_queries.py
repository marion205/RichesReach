"""
RAHA GraphQL Queries
Queries for strategy catalog, user settings, signals, and backtests
"""
import graphene
import logging
from decimal import Decimal
from django.db import models
from .raha_types import (
    StrategyType, StrategyVersionType, UserStrategySettingsType,
    RAHASignalType, RAHABacktestRunType, RAHAMetricsType, StrategyBlendType,
    NotificationPreferencesType, AutoTradingSettingsType
)
from .raha_models import Strategy, StrategyVersion, UserStrategySettings, RAHASignal, RAHABacktestRun, MLModel, StrategyBlend, NotificationPreferences, AutoTradingSettings
from .raha_query_cache import get_cache_key, cache_query_result, get_cached_query_result, CACHE_TIMEOUTS
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
        limit=graphene.Int(required=False, default_value=20),
        offset=graphene.Int(required=False, default_value=0),
        description="Get RAHA signals with pagination (optionally filtered by symbol, timeframe, strategy)"
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
        limit=graphene.Int(required=False, default_value=20),
        offset=graphene.Int(required=False, default_value=0),
        description="Get user's backtest runs with pagination"
    )
    
    # Performance Metrics
    raha_metrics = graphene.Field(
        RAHAMetricsType,
        strategy_version_id=graphene.ID(required=True),
        period=graphene.String(required=False, default_value="ALL_TIME"),
        description="Get aggregated performance metrics for a strategy"
    )
    
    # Strategy Dashboard
    strategy_dashboard = graphene.List(
        graphene.JSONString,
        description="Get dashboard data for all user's enabled strategies (returns JSON strings)"
    )
    
    # ML Models
    ml_models = graphene.List(
        graphene.JSONString,
        strategy_version_id=graphene.ID(required=False),
        model_type=graphene.String(required=False),
        description="Get user's trained ML models (returns JSON strings)"
    )
    
    strategy_blends = graphene.List(
        StrategyBlendType,
        is_active=graphene.Boolean(required=False),
        description="Get user's strategy blends"
    )
    
    notification_preferences = graphene.Field(
        NotificationPreferencesType,
        description="Get user's RAHA notification preferences"
    )
    
    auto_trading_settings = graphene.Field(
        AutoTradingSettingsType,
        description="Get user's auto-trading settings"
    )
    
    def resolve_strategies(self, info, market_type=None, category=None, include_custom=False):
        """Get available strategies with optional filters (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Check cache
        cache_key = get_cache_key(
            'strategies',
            user.id,
            market_type=market_type,
            category=category,
            include_custom=include_custom
        )
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for strategies query (user={user.id})")
            return cached_result
        
        # Query database with select_related for related objects
        queryset = Strategy.objects.filter(enabled=True).select_related('created_by')
        
        # Filter custom strategies - only show user's own custom strategies
        if not include_custom:
            queryset = queryset.filter(is_custom=False)
        else:
            # Include user's custom strategies
            queryset = queryset.filter(
                models.Q(is_custom=False) | models.Q(is_custom=True, created_by=user)
            )
        
        if market_type:
            queryset = queryset.filter(market_type=market_type)
        if category:
            queryset = queryset.filter(category=category)
        
        result = list(queryset.all())
        
        # Cache result
        cache_query_result(cache_key, result, timeout=CACHE_TIMEOUTS['strategies'])
        
        return result
    
    def resolve_strategy(self, info, id=None, slug=None):
        """Get a specific strategy (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        # Check cache
        cache_key = get_cache_key('strategy', user.id, id=id, slug=slug)
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for strategy query (user={user.id}, id={id}, slug={slug})")
            return cached_result
        
        # Query database with select_related
        strategy = None
        if id:
            try:
                strategy = Strategy.objects.select_related('created_by').get(id=id, enabled=True)
            except Strategy.DoesNotExist:
                pass
        elif slug:
            try:
                strategy = Strategy.objects.select_related('created_by').get(slug=slug, enabled=True)
            except Strategy.DoesNotExist:
                pass
        
        # Cache result (even if None, to prevent repeated DB queries)
        if strategy:
            cache_query_result(cache_key, strategy, timeout=CACHE_TIMEOUTS['strategy'])
        
        return strategy
    
    def resolve_user_strategy_settings(self, info):
        """Get user's strategy settings (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Check cache
        cache_key = get_cache_key('user_strategy_settings', user.id)
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for user_strategy_settings (user={user.id})")
            return cached_result
        
        # Query with select_related to prevent N+1 queries
        result = list(UserStrategySettings.objects.filter(
            user=user, enabled=True
        ).select_related('strategy_version', 'strategy_version__strategy'))
        
        # Cache result
        cache_query_result(cache_key, result, timeout=CACHE_TIMEOUTS['user_strategy_settings'])
        
        return result
    
    def resolve_raha_signals(self, info, symbol=None, timeframe=None, strategy_version_id=None, limit=20, offset=0):
        """Get RAHA signals with optional filters and pagination (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Check cache (only for first page to avoid cache bloat)
        if offset == 0:
            cache_key = get_cache_key(
                'raha_signals',
                user.id,
                symbol=symbol,
                timeframe=timeframe,
                strategy_version_id=strategy_version_id,
                limit=limit
            )
            cached_result = get_cached_query_result(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for raha_signals (user={user.id})")
                return cached_result
        
        # Query with select_related to prevent N+1 queries
        queryset = RAHASignal.objects.filter(user=user)
        
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)
        if strategy_version_id:
            queryset = queryset.filter(strategy_version_id=strategy_version_id)
        
        # Apply pagination with select_related
        queryset = queryset.select_related(
            'strategy_version',
            'strategy_version__strategy',
            'day_trading_signal'
        ).order_by('-timestamp')
        
        result = list(queryset[offset:offset + limit])
        
        # Cache first page only
        if offset == 0:
            cache_query_result(cache_key, result, timeout=CACHE_TIMEOUTS['raha_signals'])
        
        return result
    
    def resolve_backtest_run(self, info, id):
        """Get a specific backtest run (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        # Check cache
        cache_key = get_cache_key('backtest_run', user.id, id=id)
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for backtest_run (user={user.id}, id={id})")
            return cached_result
        
        # Query with select_related to prevent N+1 queries
        try:
            backtest = RAHABacktestRun.objects.select_related(
                'strategy_version',
                'strategy_version__strategy'
            ).get(id=id, user=user)
            
            # Cache result
            cache_query_result(cache_key, backtest, timeout=CACHE_TIMEOUTS['backtest_run'])
            
            return backtest
        except RAHABacktestRun.DoesNotExist:
            return None
    
    def resolve_user_backtests(self, info, strategy_version_id=None, status=None, limit=20, offset=0):
        """Get user's backtest runs with pagination (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Check cache (only for first page)
        if offset == 0:
            cache_key = get_cache_key(
                'user_backtests',
                user.id,
                strategy_version_id=strategy_version_id,
                status=status,
                limit=limit
            )
            cached_result = get_cached_query_result(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for user_backtests (user={user.id})")
                return cached_result
        
        # Query with select_related to prevent N+1 queries
        queryset = RAHABacktestRun.objects.filter(user=user)
        
        if strategy_version_id:
            queryset = queryset.filter(strategy_version_id=strategy_version_id)
        if status:
            queryset = queryset.filter(status=status)
        
        # Apply pagination with select_related
        queryset = queryset.select_related(
            'strategy_version',
            'strategy_version__strategy'
        ).order_by('-created_at')
        
        result = list(queryset[offset:offset + limit])
        
        # Cache first page only
        if offset == 0:
            cache_query_result(cache_key, result, timeout=CACHE_TIMEOUTS['user_backtests'])
        
        return result
    
    def resolve_raha_metrics(self, info, strategy_version_id, period="ALL_TIME"):
        """Get aggregated performance metrics for a strategy (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        # Check cache
        cache_key = get_cache_key(
            'raha_metrics',
            user.id,
            strategy_version_id=strategy_version_id,
            period=period
        )
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for raha_metrics (user={user.id}, strategy={strategy_version_id})")
            return cached_result
        
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
            
            # Get linked SignalPerformance records via day_trading_signal
            from .signal_performance_models import SignalPerformance, DayTradingSignal
            
            # Get day_trading_signal IDs from RAHA signals
            day_trading_signal_ids = list(signals.filter(day_trading_signal__isnull=False).values_list('day_trading_signal_id', flat=True))
            
            if day_trading_signal_ids:
                # Get performance records for these signals
                performances = SignalPerformance.objects.filter(
                    signal_id__in=day_trading_signal_ids
                ).order_by('evaluated_at')
                
                if performances.exists():
                    # Calculate metrics from actual performance data
                    return self._calculate_metrics_from_performances(
                        performances, strategy_version_id, period, total_signals
                    )
            
            # Fallback: Use backtest results if available (optimized with select_related)
            from .raha_models import RAHABacktestRun
            backtests = RAHABacktestRun.objects.filter(
                user=user,
                strategy_version_id=strategy_version_id,
                status='COMPLETED'
            ).select_related('strategy_version', 'strategy_version__strategy').order_by('-completed_at')[:1]
            
            if backtests.exists():
                backtest = backtests.first()
                metrics = backtest.metrics or {}
                
                metrics_result = RAHAMetricsType(
                    strategy_version_id=strategy_version_id,
                    period=period,
                    total_signals=total_signals,
                    winning_signals=int(metrics.get('winning_trades', 0)),
                    losing_signals=int(metrics.get('losing_trades', 0)),
                    win_rate=float(metrics.get('win_rate', 0.0)),
                    total_pnl_dollars=float(metrics.get('total_pnl_dollars', 0.0)),
                    total_pnl_percent=float(metrics.get('total_pnl_percent', 0.0)),
                    avg_pnl_per_signal=float(metrics.get('avg_pnl_per_signal', 0.0)),
                    sharpe_ratio=float(metrics.get('sharpe_ratio', 0.0)) if metrics.get('sharpe_ratio') else None,
                    sortino_ratio=float(metrics.get('sortino_ratio', 0.0)) if metrics.get('sortino_ratio') else None,
                    max_drawdown=float(metrics.get('max_drawdown', 0.0)) if metrics.get('max_drawdown') else None,
                    max_drawdown_duration_days=int(metrics.get('max_drawdown_duration_days', 0)) if metrics.get('max_drawdown_duration_days') else None,
                    expectancy=float(metrics.get('expectancy', 0.0)),
                    avg_win=float(metrics.get('avg_win', 0.0)),
                    avg_loss=float(metrics.get('avg_loss', 0.0)),
                    avg_r_multiple=float(metrics.get('avg_r_multiple', 0.0)),
                    best_r_multiple=float(metrics.get('best_r_multiple', 0.0)),
                    worst_r_multiple=float(metrics.get('worst_r_multiple', 0.0)),
                )
                
                # Cache result
                cache_query_result(cache_key, metrics_result, timeout=CACHE_TIMEOUTS['raha_metrics'])
                
                return metrics_result
            
            # Final fallback: Estimate from confidence scores
            from django.db.models import Avg
            avg_confidence = signals.aggregate(Avg('confidence_score'))['confidence_score__avg'] or Decimal('0.5')
            estimated_win_rate = float(avg_confidence) * 100.0
            winning_signals = int(total_signals * (estimated_win_rate / 100.0))
            losing_signals = total_signals - winning_signals
            
            metrics_result = RAHAMetricsType(
                strategy_version_id=strategy_version_id,
                period=period,
                total_signals=total_signals,
                winning_signals=winning_signals,
                losing_signals=losing_signals,
                win_rate=estimated_win_rate,
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
            
            # Cache result
            cache_query_result(cache_key, metrics_result, timeout=CACHE_TIMEOUTS['raha_metrics'])
            
            return metrics_result
        except Exception as e:
            logger.error(f"Error resolving RAHA metrics: {e}", exc_info=True)
            return None
    
    def resolve_strategy_dashboard(self, info):
        """Get dashboard data for all user's enabled strategies (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Check cache
        cache_key = get_cache_key('strategy_dashboard', user.id)
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for strategy_dashboard (user={user.id})")
            return cached_result
        
        try:
            from .raha_dashboard_service import RAHADashboardService
            service = RAHADashboardService()
            dashboard_data = service.get_strategy_dashboard_data(user)
            
            # Convert to JSON strings for GraphQL
            import json
            result = [json.dumps(item) for item in dashboard_data]
            
            # Cache result
            cache_query_result(cache_key, result, timeout=CACHE_TIMEOUTS['strategy_dashboard'])
            
            return result
        except Exception as e:
            logger.error(f"Error resolving strategy dashboard: {e}", exc_info=True)
            return []
    
    def resolve_ml_models(self, info, strategy_version_id=None, model_type=None):
        """Get user's trained ML models (cached, optimized to prevent N+1)"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Check cache
        cache_key = get_cache_key(
            'ml_models',
            user.id,
            strategy_version_id=strategy_version_id,
            model_type=model_type
        )
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for ml_models (user={user.id})")
            return cached_result
        
        try:
            # Use select_related to prevent N+1 queries when accessing strategy_version.strategy
            queryset = MLModel.objects.filter(user=user).select_related(
                'strategy_version',
                'strategy_version__strategy'
            )
            
            if strategy_version_id:
                queryset = queryset.filter(strategy_version_id=strategy_version_id)
            
            if model_type:
                queryset = queryset.filter(model_type=model_type)
            
            models_data = []
            for model in queryset.order_by('-created_at'):
                models_data.append({
                    'id': str(model.id),
                    'strategy_version_id': str(model.strategy_version.id) if model.strategy_version else None,
                    'strategy_name': model.strategy_version.strategy.name if model.strategy_version and model.strategy_version.strategy else 'All Strategies',
                    'symbol': model.symbol,
                    'model_type': model.model_type,
                    'lookback_days': model.lookback_days,
                    'training_samples': model.training_samples,
                    'metrics': model.metrics,
                    'is_active': model.is_active,
                    'created_at': model.created_at.isoformat() if model.created_at else None,
                    'trained_at': model.trained_at.isoformat() if model.trained_at else None,
                })
            
            # Convert to JSON strings for GraphQL
            import json
            result = [json.dumps(item) for item in models_data]
            
            # Cache result
            cache_query_result(cache_key, result, timeout=CACHE_TIMEOUTS['ml_models'])
            
            return result
        except Exception as e:
            logger.error(f"Error resolving ML models: {e}", exc_info=True)
            return []
    
    def resolve_strategy_blends(self, info, is_active=None):
        """Get user's strategy blends (cached, optimized with prefetch_related)"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Check cache
        cache_key = get_cache_key('strategy_blends', user.id, is_active=is_active)
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for strategy_blends (user={user.id})")
            return cached_result
        
        try:
            # Use prefetch_related to optimize access to blend components
            queryset = StrategyBlend.objects.filter(user=user).prefetch_related('components')
            
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active)
            
            result = list(queryset.order_by('-is_default', '-created_at'))
            
            # Cache result
            cache_query_result(cache_key, result, timeout=CACHE_TIMEOUTS['strategy_blends'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching strategy blends: {e}", exc_info=True)
            return []
    
    def resolve_notification_preferences(self, info):
        """Get or create user's notification preferences (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        # Check cache
        cache_key = get_cache_key('notification_preferences', user.id)
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for notification_preferences (user={user.id})")
            return cached_result
        
        try:
            prefs, _ = NotificationPreferences.objects.get_or_create(user=user)
            
            # Cache result
            cache_query_result(cache_key, prefs, timeout=CACHE_TIMEOUTS['notification_preferences'])
            
            return prefs
        except Exception as e:
            logger.error(f"Error fetching notification preferences: {e}", exc_info=True)
            return None
    
    def resolve_auto_trading_settings(self, info):
        """Get or create user's auto-trading settings (cached)"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        # Check cache
        cache_key = get_cache_key('auto_trading_settings', user.id)
        cached_result = get_cached_query_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for auto_trading_settings (user={user.id})")
            return cached_result
        
        try:
            settings, _ = AutoTradingSettings.objects.get_or_create(user=user)
            
            # Cache result
            cache_query_result(cache_key, settings, timeout=CACHE_TIMEOUTS['auto_trading_settings'])
            
            return settings
        except Exception as e:
            logger.error(f"Error fetching auto-trading settings: {e}", exc_info=True)
            return None
    
    def _calculate_metrics_from_performances(
        self,
        performances,
        strategy_version_id: str,
        period: str,
        total_signals: int
    ) -> 'RAHAMetricsType':
        """Calculate metrics from SignalPerformance records"""
        from django.db.models import Sum, Avg, Max, Min
        from decimal import Decimal
        import math
        
        # Win/Loss stats
        winning = performances.filter(outcome__in=['WIN', 'TARGET_HIT']).count()
        losing = performances.filter(outcome__in=['LOSS', 'STOP_HIT']).count()
        win_rate = (winning / len(performances) * 100) if performances.exists() else 0.0
        
        # P&L stats
        total_pnl_dollars = performances.aggregate(Sum('pnl_dollars'))['pnl_dollars__sum'] or Decimal('0.00')
        total_pnl_percent = performances.aggregate(Sum('pnl_percent'))['pnl_percent__sum'] or Decimal('0.00')
        avg_pnl = performances.aggregate(Avg('pnl_percent'))['pnl_percent__avg'] or Decimal('0.00')
        
        # Calculate returns for Sharpe/Sortino
        returns = [float(p.pnl_percent) for p in performances]
        
        # Sharpe ratio
        sharpe = self._calculate_sharpe(returns) if len(returns) > 1 else None
        
        # Sortino ratio
        sortino = self._calculate_sortino(returns) if len(returns) > 1 else None
        
        # Max drawdown
        max_dd, max_dd_duration = self._calculate_max_drawdown(performances)
        
        # Expectancy and R-multiples
        wins = [float(p.pnl_dollars) for p in performances if p.pnl_dollars > 0]
        losses = [abs(float(p.pnl_dollars)) for p in performances if p.pnl_dollars < 0]
        
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        
        # Calculate R-multiples (assuming 1% risk per trade)
        # R-multiple = P&L / Risk
        # For simplicity, use average entry price * 0.01 as risk estimate
        avg_entry = performances.aggregate(Avg('signal__entry_price'))['signal__entry_price__avg']
        if avg_entry:
            risk_per_trade = float(avg_entry) * 0.01
            avg_win_r = avg_win / risk_per_trade if risk_per_trade > 0 else 0.0
            avg_loss_r = avg_loss / risk_per_trade if risk_per_trade > 0 else 0.0
            avg_r_multiple = (avg_win_r + avg_loss_r) / 2 if (avg_win_r + avg_loss_r) > 0 else 0.0
            best_r = max([w / risk_per_trade for w in wins], default=0.0) if wins else 0.0
            worst_r = max([l / risk_per_trade for l in losses], default=0.0) if losses else 0.0
        else:
            avg_r_multiple = 0.0
            best_r = 0.0
            worst_r = 0.0
        
        # Expectancy = (Win Rate * Avg Win R) - (Loss Rate * Avg Loss R)
        win_rate_decimal = win_rate / 100.0
        expectancy = (win_rate_decimal * avg_win_r) - ((1 - win_rate_decimal) * avg_loss_r)
        
        return RAHAMetricsType(
            strategy_version_id=strategy_version_id,
            period=period,
            total_signals=total_signals,
            winning_signals=winning,
            losing_signals=losing,
            win_rate=round(win_rate, 2),
            total_pnl_dollars=float(total_pnl_dollars),
            total_pnl_percent=float(total_pnl_percent),
            avg_pnl_per_signal=float(avg_pnl),
            sharpe_ratio=round(sharpe, 2) if sharpe else None,
            sortino_ratio=round(sortino, 2) if sortino else None,
            max_drawdown=round(max_dd, 4) if max_dd else None,
            max_drawdown_duration_days=max_dd_duration,
            expectancy=round(expectancy, 2),
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            avg_r_multiple=round(avg_r_multiple, 2),
            best_r_multiple=round(best_r, 2),
            worst_r_multiple=round(-worst_r, 2),  # Negative for losses
        )
    
    def _calculate_sharpe(self, returns: list) -> float:
        """Calculate Sharpe ratio (annualized)"""
        if not returns or len(returns) < 2:
            return None
        
        import statistics
        import math
        
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0
        
        if std_return == 0:
            return None
        
        # Annualize (assuming ~252 trading days)
        sharpe = (mean_return / std_return) * math.sqrt(252)
        return sharpe
    
    def _calculate_sortino(self, returns: list) -> float:
        """Calculate Sortino ratio (downside deviation only)"""
        if not returns or len(returns) < 2:
            return None
        
        import statistics
        import math
        
        mean_return = statistics.mean(returns)
        
        # Only count negative returns for downside deviation
        downside_returns = [r for r in returns if r < 0]
        if len(downside_returns) < 2:
            return None
        
        downside_std = statistics.stdev(downside_returns)
        if downside_std == 0:
            return None
        
        sortino = (mean_return / downside_std) * math.sqrt(252)
        return sortino
    
    def _calculate_max_drawdown(self, performances) -> tuple:
        """Calculate maximum drawdown and duration"""
        if not performances.exists():
            return None, None
        
        # Build cumulative equity curve
        sorted_perfs = performances.order_by('evaluated_at')
        equity = 100.0  # Start at 100
        equity_curve = [equity]
        dates = []
        
        for perf in sorted_perfs:
            equity *= (1 + float(perf.pnl_percent) / 100)
            equity_curve.append(equity)
            dates.append(perf.evaluated_at)
        
        # Calculate drawdowns
        max_equity = equity_curve[0]
        max_dd = 0.0
        max_dd_start = None
        max_dd_end = None
        
        for i, eq in enumerate(equity_curve):
            if eq > max_equity:
                max_equity = eq
            dd = ((eq - max_equity) / max_equity) * 100
            if dd < max_dd:
                max_dd = dd
                if max_dd_start is None:
                    max_dd_start = dates[i-1] if i > 0 else dates[0] if dates else None
                max_dd_end = dates[i-1] if i < len(dates) else dates[-1] if dates else None
        
        duration = (max_dd_end - max_dd_start).days if max_dd_start and max_dd_end else None
        
        return abs(max_dd), duration

