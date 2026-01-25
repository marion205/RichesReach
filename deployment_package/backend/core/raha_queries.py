"""
RAHA GraphQL Queries
Queries for strategy catalog, user settings, signals, and backtests
"""
import graphene
import logging
import json
from decimal import Decimal
from django.db import models
from .raha_types import (
    StrategyType, StrategyVersionType, UserStrategySettingsType,
    RAHASignalType, RAHABacktestRunType, RAHAMetricsType
)
# Optional types - import if available
try:
    from .raha_types import StrategyBlendType, NotificationPreferencesType, AutoTradingSettingsType
except ImportError:
    StrategyBlendType = None
    NotificationPreferencesType = None
    AutoTradingSettingsType = None
from .raha_models import Strategy, StrategyVersion, UserStrategySettings, RAHASignal, RAHABacktestRun
# Optional models - import if available
try:
    from .raha_models import MLModel, StrategyBlend, NotificationPreferences, AutoTradingSettings
except ImportError:
    MLModel = None
    StrategyBlend = None
    NotificationPreferences = None
    AutoTradingSettings = None
from .raha_query_cache import get_cache_key, cache_query_result, get_cached_query_result, CACHE_TIMEOUTS
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


def _generate_mock_signals_helper(symbol: str, limit: int = 3, user=None):
    """Helper function to generate mock RAHA signals for UI testing"""
    from django.utils import timezone
    from datetime import timedelta
    import uuid
    import random
    
    # Try to get or create a strategy version for mock data
    try:
        strategy = Strategy.objects.filter(enabled=True).first()
        if strategy:
            strategy_version = strategy.versions.filter(is_default=True).first() or strategy.versions.first()
            if not strategy_version:
                # Create a version if strategy exists but has no versions
                strategy_version = StrategyVersion.objects.create(
                    strategy=strategy,
                    version=1,
                    is_default=True,
                    logic_ref='MOCK_v1',
                    config_schema={}
                )
        else:
            # Create a minimal mock strategy if none exists
            strategy, created = Strategy.objects.get_or_create(
                slug='mock_orb_momentum',
                defaults={
                    'name': 'Mock ORB Momentum',
                    'category': 'MOMENTUM',
                    'market_type': 'STOCKS',
                    'description': 'Mock strategy for UI testing',
                    'enabled': True
                }
            )
            strategy_version = strategy.versions.filter(is_default=True).first() or strategy.versions.first()
            if not strategy_version:
                strategy_version = StrategyVersion.objects.create(
                    strategy=strategy,
                    version=1,
                    is_default=True,
                    logic_ref='MOCK_ORB_v1',
                    config_schema={}
                )
    except Exception as e:
        logger.error(f"Could not create mock strategy: {e}", exc_info=True)
        return []
    
    mock_signals = []
    regimes = [
        {
            'global_regime': 'EQUITY_RISK_ON',
            'local_context': 'IDIOSYNCRATIC_BREAKOUT',
            'regime_multiplier': 1.3,
            'regime_narration': 'Risk-on environment with strong momentum. Ideal for aggressive entries with wider stops.',
        },
        {
            'global_regime': 'EQUITY_RISK_OFF',
            'local_context': 'CHOPPY_MEAN_REVERT',
            'regime_multiplier': 0.7,
            'regime_narration': 'Risk-off conditions detected. Reduce position sizes and tighten stops. Favor mean reversion setups.',
        },
        {
            'global_regime': 'NEUTRAL',
            'local_context': 'NORMAL',
            'regime_multiplier': 1.0,
            'regime_narration': 'Neutral market conditions. Standard position sizing and risk management apply.',
        },
    ]
    
    base_price = 175.50  # Mock base price
    signal_types = ['ENTRY_LONG', 'ENTRY_LONG', 'ENTRY_SHORT']
    
    for i in range(min(limit, len(regimes))):
        regime = regimes[i]
        signal_type = signal_types[i] if i < len(signal_types) else 'ENTRY_LONG'
        price_variation = random.uniform(-2, 2)
        current_price = base_price + price_variation
        
        # Calculate stop loss and take profit based on signal type
        if signal_type == 'ENTRY_LONG':
            stop_loss = current_price * 0.98  # 2% stop
            take_profit = current_price * 1.04  # 4% target
        else:  # ENTRY_SHORT
            stop_loss = current_price * 1.02  # 2% stop
            take_profit = current_price * 0.96  # 4% target
        
        signal = RAHASignal(
            id=uuid.uuid4(),
            user=user,  # Associate with user so query finds it
            strategy_version=strategy_version,
            symbol=symbol,
            timestamp=timezone.now() - timedelta(minutes=i * 5),
            timeframe='5m',
            signal_type=signal_type,
            price=Decimal(str(round(current_price, 2))),
            stop_loss=Decimal(str(round(stop_loss, 2))),
            take_profit=Decimal(str(round(take_profit, 2))),
            confidence_score=Decimal(str(round(random.uniform(0.65, 0.95), 4))),
            meta={
                'regime_global': regime['global_regime'],
                'regime_local': regime['local_context'],
                'regime_multiplier': regime['regime_multiplier'],
                'regime_narration': regime['regime_narration'],
                'pattern': 'Bullish Engulfing' if signal_type == 'ENTRY_LONG' else 'Bearish Engulfing',
                'volume_surge': True,
                'rsi': round(random.uniform(45, 75), 1),
            }
        )
        mock_signals.append(signal)
    
    return mock_signals


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
    userStrategySettings = graphene.List(
        UserStrategySettingsType,
        description="Get user's enabled strategy settings"
    )
    
    # RAHA Signals
    rahaSignals = graphene.List(
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
    
    # Strategy Blends
    strategy_blends = graphene.List(
        graphene.JSONString,
        is_active=graphene.Boolean(required=False),
        description="Get user's strategy blends (returns JSON strings)"
    )
    
    # Notification Preferences (commented out - type not available)
    # notification_preferences = graphene.Field(
    #     NotificationPreferencesType,
    #     description="Get user's RAHA notification preferences"
    # )
    
    # Auto-Trading Settings (commented out - type not available)
    # auto_trading_settings = graphene.Field(
    #     AutoTradingSettingsType,
    #     description="Get user's auto-trading settings"
    # )
    
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
    
    def resolve_userStrategySettings(self, info):
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
        
        # ✅ MOCK DATA: If no settings exist, return mock data for UI testing
        if not result:
            logger.info(f"userStrategySettings: No settings found, returning mock data for UI testing (user={user.id})")
            try:
                mock_settings = self._generate_mock_strategy_settings(user)
                if mock_settings:
                    result = mock_settings
                    logger.info(f"userStrategySettings: Generated {len(mock_settings)} mock settings")
                else:
                    logger.warning(f"userStrategySettings: Mock settings generation returned empty list")
            except Exception as e:
                logger.error(f"userStrategySettings: Error generating mock settings: {e}", exc_info=True)
        
        # Cache result
        cache_query_result(cache_key, result, timeout=CACHE_TIMEOUTS['user_strategy_settings'])
        
        return result
    
    def resolve_rahaSignals(self, info, symbol=None, timeframe=None, strategy_version_id=None, limit=20, offset=0):
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
        # Include both user-specific and global (user=None) signals
        from django.db.models import Q
        queryset = RAHASignal.objects.filter(Q(user=user) | Q(user__isnull=True))
        
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
        
        # ✅ MOCK DATA: If no signals exist, return mock data for UI testing
        if not result and offset == 0:
            logger.info(f"rahaSignals: No signals found, generating mock data for UI testing (symbol={symbol}, limit={limit}, user={user.id if user.is_authenticated else None}, self={type(self).__name__})")
            try:
                # Use module-level helper function to avoid self issues
                mock_signals = _generate_mock_signals_helper(symbol or 'AAPL', limit, user)
                if mock_signals:
                    # Save mock signals to database so they persist
                    saved_signals = []
                    for signal in mock_signals:
                        try:
                            signal.save()
                            saved_signals.append(signal.id)
                            logger.debug(f"rahaSignals: Saved mock signal {signal.id} for {signal.symbol}")
                        except Exception as save_error:
                            logger.warning(f"rahaSignals: Failed to save mock signal {signal.id}: {save_error}")
                    
                    if saved_signals:
                        # Re-fetch with proper select_related
                        result = list(RAHASignal.objects.filter(
                            id__in=saved_signals
                        ).select_related('strategy_version', 'strategy_version__strategy'))
                        logger.info(f"rahaSignals: Generated and saved {len(result)} mock signals")
                    else:
                        logger.warning(f"rahaSignals: No mock signals were saved successfully")
                else:
                    logger.warning(f"rahaSignals: Mock signal generation returned empty list")
            except Exception as e:
                logger.error(f"rahaSignals: Error generating mock signals: {e}", exc_info=True)
        
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
        """Get user's strategy blends"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        if StrategyBlend is None:
            return []
        
        try:
            query = StrategyBlend.objects.filter(user=user)
            if is_active is not None:
                query = query.filter(is_active=is_active)
            
            blends = query.order_by('-created_at')
            
            # Convert to JSON strings for frontend
            result = []
            for blend in blends:
                # Get strategy names for components
                components_with_names = []
                for comp in blend.components:
                    try:
                        strategy_version = StrategyVersion.objects.get(id=comp.get('strategy_version_id'))
                        strategy_name = strategy_version.strategy.name
                    except StrategyVersion.DoesNotExist:
                        strategy_name = 'Unknown'
                    
                    components_with_names.append({
                        'strategyVersionId': comp.get('strategy_version_id'),
                        'weight': comp.get('weight', 0),
                        'strategyName': strategy_name
                    })
                
                result.append(json.dumps({
                    'id': str(blend.id),
                    'name': blend.name,
                    'description': blend.description,
                    'components': components_with_names,
                    'isActive': blend.is_active,
                    'isDefault': blend.is_default,
                    'createdAt': blend.created_at.isoformat() if blend.created_at else None,
                    'updatedAt': blend.updated_at.isoformat() if blend.updated_at else None,
                }))
            
            return result
        except Exception as e:
            logger.error(f"Error resolving strategy blends: {e}", exc_info=True)
            return []
    # 
    # def resolve_notification_preferences(self, info):
    #     return None
    # 
    # def resolve_auto_trading_settings(self, info):
    #     return None
    
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
    
    def _generate_mock_signals(self, symbol: str, limit: int = 3, user=None):
        """Generate mock RAHA signals for UI testing (delegates to helper)"""
        return _generate_mock_signals_helper(symbol, limit, user)
    
    def _generate_mock_strategy_settings(self, user):
        """Generate mock user strategy settings for UI testing"""
        from django.utils import timezone
        import uuid
        
        # Try to get existing strategies
        strategies = Strategy.objects.filter(enabled=True)[:3]
        
        if not strategies.exists():
            # Create minimal mock strategies if none exist
            mock_strategies = [
                {'slug': 'orb_momentum', 'name': 'ORB Momentum', 'category': 'MOMENTUM'},
                {'slug': 'trend_swing', 'name': 'Trend Swing', 'category': 'SWING'},
                {'slug': 'mean_revert', 'name': 'Mean Reversion', 'category': 'REVERSAL'},
            ]
            for mock in mock_strategies:
                strategy, _ = Strategy.objects.get_or_create(
                    slug=mock['slug'],
                    defaults={
                        'name': mock['name'],
                        'category': mock['category'],
                        'market_type': 'STOCKS',
                        'description': f'Mock {mock["name"]} strategy',
                        'enabled': True,
                    }
                )
                if not strategy.versions.exists():
                    StrategyVersion.objects.create(
                        strategy=strategy,
                        version=1,
                        is_default=True,
                        logic_ref=f'{mock["slug"].upper()}_v1',
                        config_schema={}
                    )
            strategies = Strategy.objects.filter(enabled=True)[:3]
        
        mock_settings = []
        for strategy in strategies:
            strategy_version = strategy.versions.filter(is_default=True).first() or strategy.versions.first()
            if not strategy_version:
                continue
            
            # Check if setting already exists
            existing = UserStrategySettings.objects.filter(
                user=user,
                strategy_version=strategy_version
            ).first()
            
            if not existing:
                setting = UserStrategySettings(
                    id=uuid.uuid4(),
                    user=user,
                    strategy_version=strategy_version,
                    parameters={
                        'risk_per_trade': 0.01,
                        'max_positions': 3,
                        'stop_loss_pct': 2.0,
                    },
                    enabled=True,
                    auto_trade_enabled=False,
                    max_daily_loss_percent=Decimal('2.0'),
                    max_concurrent_positions=3,
                )
                mock_settings.append(setting)
            else:
                mock_settings.append(existing)
        
        return mock_settings

