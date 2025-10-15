"""
GraphQL Mutations for Swing Trading Features
"""
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q
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


class CreateSignalMutation(graphene.Mutation):
    """Create a new signal"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        timeframe = graphene.String()
        signal_type = graphene.String(required=True)
        entry_price = graphene.Float(required=True)
        stop_price = graphene.Float()
        target_price = graphene.Float()
        ml_score = graphene.Float(required=True)
        features = graphene.JSONString(required=True)
        thesis = graphene.String(required=True)
    
    success = graphene.Boolean()
    signal = graphene.Field(SignalType)
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return CreateSignalMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            # Create signal
            signal = Signal.objects.create(
                symbol=kwargs['symbol'],
                timeframe=kwargs.get('timeframe', '1d'),
                triggered_at=timezone.now(),
                signal_type=kwargs['signal_type'],
                entry_price=kwargs['entry_price'],
                stop_price=kwargs.get('stop_price'),
                target_price=kwargs.get('target_price'),
                ml_score=kwargs['ml_score'],
                features=kwargs['features'],
                thesis=kwargs['thesis'],
                created_by=user
            )
            
            # Calculate risk/reward ratio
            if signal.stop_price and signal.target_price:
                risk = abs(float(signal.entry_price - signal.stop_price))
                reward = abs(float(signal.target_price - signal.entry_price))
                if risk > 0:
                    signal.risk_reward_ratio = reward / risk
                    signal.save()
            
            return CreateSignalMutation(
                success=True,
                signal=signal,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Error creating signal: {e}")
            return CreateSignalMutation(
                success=False,
                errors=[str(e)]
            )


class LikeSignalMutation(graphene.Mutation):
    """Like/unlike a signal"""
    
    class Arguments:
        signal_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    is_liked = graphene.Boolean()
    like_count = graphene.Int()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, signal_id):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return LikeSignalMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            signal = Signal.objects.get(id=signal_id)
            like, created = SignalLike.objects.get_or_create(
                user=user,
                signal=signal
            )
            
            if created:
                # Like created
                signal.likes_count += 1
                signal.save()
                is_liked = True
            else:
                # Unlike
                like.delete()
                signal.likes_count = max(0, signal.likes_count - 1)
                signal.save()
                is_liked = False
            
            return LikeSignalMutation(
                success=True,
                is_liked=is_liked,
                like_count=signal.likes_count,
                errors=[]
            )
            
        except Signal.DoesNotExist:
            return LikeSignalMutation(
                success=False,
                errors=["Signal not found"]
            )
        except Exception as e:
            logger.error(f"Error liking signal: {e}")
            return LikeSignalMutation(
                success=False,
                errors=[str(e)]
            )


class CommentSignalMutation(graphene.Mutation):
    """Comment on a signal"""
    
    class Arguments:
        signal_id = graphene.ID(required=True)
        content = graphene.String(required=True)
    
    success = graphene.Boolean()
    comment = graphene.Field(SignalCommentType)
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, signal_id, content):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return CommentSignalMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            signal = Signal.objects.get(id=signal_id)
            
            # Create comment
            comment = SignalComment.objects.create(
                user=user,
                signal=signal,
                content=content
            )
            
            # Update comment count
            signal.comments_count += 1
            signal.save()
            
            return CommentSignalMutation(
                success=True,
                comment=comment,
                errors=[]
            )
            
        except Signal.DoesNotExist:
            return CommentSignalMutation(
                success=False,
                errors=["Signal not found"]
            )
        except Exception as e:
            logger.error(f"Error commenting on signal: {e}")
            return CommentSignalMutation(
                success=False,
                errors=[str(e)]
            )


class CreateSwingWatchlistMutation(graphene.Mutation):
    """Create a new swing watchlist"""
    
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        symbols = graphene.List(graphene.String, required=True)
        is_public = graphene.Boolean()
    
    success = graphene.Boolean()
    watchlist = graphene.Field(SwingWatchlistType)
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return CreateSwingWatchlistMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            # Create watchlist
            watchlist = SwingWatchlist.objects.create(
                user=user,
                name=kwargs['name'],
                description=kwargs.get('description', ''),
                symbols=kwargs['symbols'],
                is_public=kwargs.get('is_public', False)
            )
            
            return CreateSwingWatchlistMutation(
                success=True,
                watchlist=watchlist,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Error creating swing watchlist: {e}")
            return CreateSwingWatchlistMutation(
                success=False,
                errors=[str(e)]
            )


class UpdateSwingWatchlistMutation(graphene.Mutation):
    """Update a swing watchlist"""
    
    class Arguments:
        watchlist_id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        symbols = graphene.List(graphene.String)
        is_public = graphene.Boolean()
    
    success = graphene.Boolean()
    watchlist = graphene.Field(SwingWatchlistType)
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, watchlist_id, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return UpdateSwingWatchlistMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            watchlist = SwingWatchlist.objects.get(id=watchlist_id, user=user)
            
            # Update fields
            if 'name' in kwargs:
                watchlist.name = kwargs['name']
            if 'description' in kwargs:
                watchlist.description = kwargs['description']
            if 'symbols' in kwargs:
                watchlist.symbols = kwargs['symbols']
            if 'is_public' in kwargs:
                watchlist.is_public = kwargs['is_public']
            
            watchlist.save()
            
            return UpdateSwingWatchlistMutation(
                success=True,
                watchlist=watchlist,
                errors=[]
            )
            
        except SwingWatchlist.DoesNotExist:
            return UpdateSwingWatchlistMutation(
                success=False,
                errors=["Watchlist not found"]
            )
        except Exception as e:
            logger.error(f"Error updating swing watchlist: {e}")
            return UpdateSwingWatchlistMutation(
                success=False,
                errors=[str(e)]
            )


class DeleteSwingWatchlistMutation(graphene.Mutation):
    """Delete a swing watchlist"""
    
    class Arguments:
        watchlist_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, watchlist_id):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return DeleteSwingWatchlistMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            watchlist = SwingWatchlist.objects.get(id=watchlist_id, user=user)
            watchlist.delete()
            
            return DeleteSwingWatchlistMutation(
                success=True,
                errors=[]
            )
            
        except SwingWatchlist.DoesNotExist:
            return DeleteSwingWatchlistMutation(
                success=False,
                errors=["Watchlist not found"]
            )
        except Exception as e:
            logger.error(f"Error deleting swing watchlist: {e}")
            return DeleteSwingWatchlistMutation(
                success=False,
                errors=[str(e)]
            )


class CreateBacktestStrategyMutation(graphene.Mutation):
    """Create a new backtest strategy"""
    
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        strategy_type = graphene.String(required=True)
        parameters = graphene.JSONString(required=True)
        is_public = graphene.Boolean()
    
    success = graphene.Boolean()
    strategy = graphene.Field(BacktestStrategyType)
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return CreateBacktestStrategyMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            # Create strategy
            strategy = BacktestStrategy.objects.create(
                user=user,
                name=kwargs['name'],
                description=kwargs.get('description', ''),
                strategy_type=kwargs['strategy_type'],
                parameters=kwargs['parameters'],
                is_public=kwargs.get('is_public', False)
            )
            
            return CreateBacktestStrategyMutation(
                success=True,
                strategy=strategy,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Error creating backtest strategy: {e}")
            return CreateBacktestStrategyMutation(
                success=False,
                errors=[str(e)]
            )


class RunBacktestMutation(graphene.Mutation):
    """Run a backtest"""
    
    class Arguments:
        strategy_name = graphene.String(required=True)
        symbol = graphene.String(required=True)
        start_date = graphene.DateTime()
        end_date = graphene.DateTime()
        config = graphene.Argument(BacktestConfigType)
        params = graphene.Argument(StrategyParamsType)
    
    success = graphene.Boolean()
    result = graphene.Field(BacktestMetricsType)
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return RunBacktestMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            # This would typically run asynchronously
            # For now, return placeholder result
            result = BacktestMetricsType(
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
            
            return RunBacktestMutation(
                success=True,
                result=result,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return RunBacktestMutation(
                success=False,
                errors=[str(e)]
            )


class ValidateSignalMutation(graphene.Mutation):
    """Validate a signal (mark as validated)"""
    
    class Arguments:
        signal_id = graphene.ID(required=True)
        validation_price = graphene.Float()
    
    success = graphene.Boolean()
    signal = graphene.Field(SignalType)
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, signal_id, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return ValidateSignalMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            signal = Signal.objects.get(id=signal_id)
            
            # Update validation
            signal.is_validated = True
            signal.validation_timestamp = timezone.now()
            if 'validation_price' in kwargs:
                signal.validation_price = kwargs['validation_price']
            
            signal.save()
            
            return ValidateSignalMutation(
                success=True,
                signal=signal,
                errors=[]
            )
            
        except Signal.DoesNotExist:
            return ValidateSignalMutation(
                success=False,
                errors=["Signal not found"]
            )
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return ValidateSignalMutation(
                success=False,
                errors=[str(e)]
            )


class UpdateTraderScoreMutation(graphene.Mutation):
    """Update trader score"""
    
    class Arguments:
        accuracy_score = graphene.Float()
        consistency_score = graphene.Float()
        discipline_score = graphene.Float()
    
    success = graphene.Boolean()
    trader_score = graphene.Field(TraderScoreType)
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return UpdateTraderScoreMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            # Get or create trader score
            trader_score, created = TraderScore.objects.get_or_create(user=user)
            
            # Update scores
            if 'accuracy_score' in kwargs:
                trader_score.accuracy_score = kwargs['accuracy_score']
            if 'consistency_score' in kwargs:
                trader_score.consistency_score = kwargs['consistency_score']
            if 'discipline_score' in kwargs:
                trader_score.discipline_score = kwargs['discipline_score']
            
            # Recalculate overall score
            trader_score.overall_score = (
                trader_score.accuracy_score * 0.4 +
                trader_score.consistency_score * 0.3 +
                trader_score.discipline_score * 0.3
            )
            
            trader_score.save()
            
            return UpdateTraderScoreMutation(
                success=True,
                trader_score=trader_score,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Error updating trader score: {e}")
            return UpdateTraderScoreMutation(
                success=False,
                errors=[str(e)]
            )


class CreateAlertMutation(graphene.Mutation):
    """Create a price alert"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        alert_type = graphene.String(required=True)
        condition = graphene.String(required=True)
        threshold = graphene.Float(required=True)
        message = graphene.String()
    
    success = graphene.Boolean()
    alert = graphene.Field(AlertType)
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return CreateAlertMutation(
                    success=False,
                    errors=["Authentication required"]
                )
            
            # This would create an alert in the database
            # For now, return placeholder
            alert = AlertType(
                id="1",
                user=user,
                symbol=kwargs['symbol'],
                alert_type=kwargs['alert_type'],
                condition=kwargs['condition'],
                threshold=kwargs['threshold'],
                is_active=True,
                created_at=timezone.now(),
                triggered_at=None,
                message=kwargs.get('message', '')
            )
            
            return CreateAlertMutation(
                success=True,
                alert=alert,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return CreateAlertMutation(
                success=False,
                errors=[str(e)]
            )


class SwingTradingMutation(graphene.ObjectType):
    """Swing Trading GraphQL Mutations"""
    
    create_signal = CreateSignalMutation.Field()
    like_signal = LikeSignalMutation.Field()
    comment_signal = CommentSignalMutation.Field()
    validate_signal = ValidateSignalMutation.Field()
    
    create_swing_watchlist = CreateSwingWatchlistMutation.Field()
    update_swing_watchlist = UpdateSwingWatchlistMutation.Field()
    delete_swing_watchlist = DeleteSwingWatchlistMutation.Field()
    
    create_backtest_strategy = CreateBacktestStrategyMutation.Field()
    run_backtest = RunBacktestMutation.Field()
    
    update_trader_score = UpdateTraderScoreMutation.Field()
    create_alert = CreateAlertMutation.Field()
