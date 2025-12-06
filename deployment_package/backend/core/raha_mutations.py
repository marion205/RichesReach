"""
RAHA GraphQL Mutations
Mutations for enabling strategies, running backtests, generating signals
"""
import graphene
import logging
from .raha_types import (
    UserStrategySettingsType, RAHASignalType, RAHABacktestRunType
)
from .raha_models import (
    Strategy, StrategyVersion, UserStrategySettings, RAHASignal, RAHABacktestRun
)
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date

User = get_user_model()
logger = logging.getLogger(__name__)


class EnableStrategy(graphene.Mutation):
    """Enable a strategy for a user with custom parameters"""
    
    class Arguments:
        strategy_version_id = graphene.ID(required=True)
        parameters = graphene.JSONString(required=False)
        auto_trade_enabled = graphene.Boolean(required=False, default_value=False)
        max_daily_loss_percent = graphene.Float(required=False)
        max_concurrent_positions = graphene.Int(required=False, default_value=3)
    
    user_strategy_settings = graphene.Field(UserStrategySettingsType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, strategy_version_id, parameters=None, auto_trade_enabled=False, max_daily_loss_percent=None, max_concurrent_positions=3):
        user = info.context.user
        if not user.is_authenticated:
            return EnableStrategy(
                success=False,
                message="Authentication required"
            )
        
        try:
            strategy_version = StrategyVersion.objects.get(id=strategy_version_id)
            
            # Create or update user settings
            settings, created = UserStrategySettings.objects.update_or_create(
                user=user,
                strategy_version=strategy_version,
                defaults={
                    'parameters': parameters or {},
                    'enabled': True,
                    'auto_trade_enabled': auto_trade_enabled,
                    'max_daily_loss_percent': max_daily_loss_percent,
                    'max_concurrent_positions': max_concurrent_positions,
                }
            )
            
            return EnableStrategy(
                user_strategy_settings=settings,
                success=True,
                message=f"Strategy '{strategy_version.strategy.name}' enabled successfully"
            )
        except StrategyVersion.DoesNotExist:
            return EnableStrategy(
                success=False,
                message="Strategy version not found"
            )
        except Exception as e:
            logger.error(f"Error enabling strategy: {e}", exc_info=True)
            return EnableStrategy(
                success=False,
                message=f"Error: {str(e)}"
            )


class DisableStrategy(graphene.Mutation):
    """Disable a strategy for a user"""
    
    class Arguments:
        strategy_version_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, strategy_version_id):
        user = info.context.user
        if not user.is_authenticated:
            return DisableStrategy(
                success=False,
                message="Authentication required"
            )
        
        try:
            settings = UserStrategySettings.objects.get(
                user=user,
                strategy_version_id=strategy_version_id
            )
            settings.enabled = False
            settings.save()
            
            return DisableStrategy(
                success=True,
                message="Strategy disabled successfully"
            )
        except UserStrategySettings.DoesNotExist:
            return DisableStrategy(
                success=False,
                message="Strategy not found for user"
            )
        except Exception as e:
            logger.error(f"Error disabling strategy: {e}", exc_info=True)
            return DisableStrategy(
                success=False,
                message=f"Error: {str(e)}"
            )


class RunBacktest(graphene.Mutation):
    """Run a backtest for a strategy"""
    
    class Arguments:
        strategy_version_id = graphene.ID(required=True)
        symbol = graphene.String(required=True)
        timeframe = graphene.String(required=True, default_value="5m")
        start_date = graphene.Date(required=True)
        end_date = graphene.Date(required=True)
        parameters = graphene.JSONString(required=False)
    
    backtest_run = graphene.Field(RAHABacktestRunType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, strategy_version_id, symbol, timeframe, start_date, end_date, parameters=None):
        user = info.context.user
        if not user.is_authenticated:
            return RunBacktest(
                success=False,
                message="Authentication required"
            )
        
        try:
            strategy_version = StrategyVersion.objects.get(id=strategy_version_id)
            
            # Create backtest run
            backtest = RAHABacktestRun.objects.create(
                user=user,
                strategy_version=strategy_version,
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                parameters=parameters or {},
                status='PENDING'
            )
            
            # Queue backtest job (async)
            # TODO: Use Celery or similar for async execution
            from .raha_backtest_service import RAHABacktestService
            backtest_service = RAHABacktestService()
            # For now, run synchronously (will be async in production)
            try:
                backtest_service.run_backtest(backtest.id)
            except Exception as e:
                logger.error(f"Error running backtest: {e}", exc_info=True)
                backtest.status = 'FAILED'
                backtest.save()
                return RunBacktest(
                    backtest_run=backtest,
                    success=False,
                    message=f"Backtest failed: {str(e)}"
                )
            
            return RunBacktest(
                backtest_run=backtest,
                success=True,
                message="Backtest queued successfully"
            )
        except StrategyVersion.DoesNotExist:
            return RunBacktest(
                success=False,
                message="Strategy version not found"
            )
        except Exception as e:
            logger.error(f"Error creating backtest: {e}", exc_info=True)
            return RunBacktest(
                success=False,
                message=f"Error: {str(e)}"
            )


class GenerateRAHASignals(graphene.Mutation):
    """Generate RAHA signals for a strategy (live or historical)"""
    
    class Arguments:
        strategy_version_id = graphene.ID(required=True)
        symbol = graphene.String(required=True)
        timeframe = graphene.String(required=True, default_value="5m")
        lookback_candles = graphene.Int(required=False, default_value=500)
        parameters = graphene.JSONString(required=False)
    
    signals = graphene.List(RAHASignalType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, strategy_version_id, symbol, timeframe, lookback_candles=500, parameters=None):
        user = info.context.user
        if not user.is_authenticated:
            return GenerateRAHASignals(
                success=False,
                message="Authentication required"
            )
        
        try:
            from .raha_strategy_engine import RAHAStrategyEngine
            
            strategy_version = StrategyVersion.objects.get(id=strategy_version_id)
            
            # Get user's parameters or use defaults
            try:
                user_settings = UserStrategySettings.objects.get(
                    user=user,
                    strategy_version=strategy_version,
                    enabled=True
                )
                merged_parameters = {**(parameters or {}), **user_settings.parameters}
            except UserStrategySettings.DoesNotExist:
                merged_parameters = parameters or {}
            
            # Generate signals
            engine = RAHAStrategyEngine()
            signals_data = engine.generate_signals(
                strategy_version=strategy_version,
                symbol=symbol,
                timeframe=timeframe,
                lookback_candles=lookback_candles,
                parameters=merged_parameters
            )
            
            # Create RAHASignal records
            signals = []
            for signal_data in signals_data:
                signal = RAHASignal.objects.create(
                    user=user,
                    strategy_version=strategy_version,
                    symbol=symbol,
                    timestamp=timezone.now(),
                    timeframe=timeframe,
                    signal_type=signal_data['signal_type'],
                    price=signal_data['price'],
                    stop_loss=signal_data.get('stop_loss'),
                    take_profit=signal_data.get('take_profit'),
                    confidence_score=signal_data.get('confidence_score', 0.5),
                    meta=signal_data.get('meta', {})
                )
                signals.append(signal)
            
            return GenerateRAHASignals(
                signals=signals,
                success=True,
                message=f"Generated {len(signals)} signals"
            )
        except StrategyVersion.DoesNotExist:
            return GenerateRAHASignals(
                success=False,
                message="Strategy version not found"
            )
        except Exception as e:
            logger.error(f"Error generating RAHA signals: {e}", exc_info=True)
            return GenerateRAHASignals(
                success=False,
                message=f"Error: {str(e)}"
            )


class RAHAMutations(graphene.ObjectType):
    """RAHA GraphQL mutations"""
    enable_strategy = EnableStrategy.Field()
    disable_strategy = DisableStrategy.Field()
    run_backtest = RunBacktest.Field()
    generate_raha_signals = GenerateRAHASignals.Field()

