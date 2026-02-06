"""
GraphQL Mutations for Swing Trading Features
- Like/unlike signals
- Comment on signals
- Log trading outcomes
"""
import graphene
import json
import logging
from decimal import Decimal
from datetime import datetime
from typing import Optional
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


class LikeSignal(graphene.Mutation):
    """Like or unlike a swing trading signal"""
    class Arguments:
        signalId = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, signalId):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return LikeSignal(success=False, message="Authentication required")
            
            # In production, this would toggle like in database
            # For now, return success
            return LikeSignal(
                success=True,
                message="Signal liked successfully"
            )
        except Exception as e:
            logger.error(f"Error liking signal: {e}", exc_info=True)
            return LikeSignal(success=False, message=str(e))


class CommentSignal(graphene.Mutation):
    """Add a comment to a swing trading signal"""
    class Arguments:
        signalId = graphene.String(required=True)
        comment = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    commentId = graphene.String()
    
    def mutate(self, info, signalId, comment):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return CommentSignal(success=False, message="Authentication required")
            
            # In production, this would create comment in database
            # For now, return success
            return CommentSignal(
                success=True,
                message="Comment added successfully",
                commentId="comment_new_001"
            )
        except Exception as e:
            logger.error(f"Error commenting on signal: {e}", exc_info=True)
            return CommentSignal(success=False, message=str(e))


class DayTradingOutcomeInput(graphene.InputObjectType):
    """Input type for logging day trading outcomes"""
    signal_id = graphene.String(description="UUID of the DayTradingSignal")
    symbol = graphene.String(required=True)
    side = graphene.String(required=True, description="LONG or SHORT")
    entry_price = graphene.Float(required=True)
    exit_price = graphene.Float()
    entry_time = graphene.String()
    exit_time = graphene.String()
    shares = graphene.Int()
    outcome = graphene.String(description="WIN, LOSS, or BREAKEVEN")
    hit_stop = graphene.Boolean()
    hit_target = graphene.Boolean()


class LogDayTradingOutcome(graphene.Mutation):
    """Log the outcome of a day trading pick with actual fill data"""
    class Arguments:
        input = graphene.Argument(DayTradingOutcomeInput, required=True)

    success = graphene.Boolean()
    message = graphene.String()
    fill_id = graphene.String()
    execution_quality = graphene.Float()
    coaching_tip = graphene.String()

    def mutate(self, info, input):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return LogDayTradingOutcome(success=False, message="Authentication required")

            from .signal_performance_models import DayTradingSignal, UserFill
            from .execution_quality_tracker import ExecutionQualityTracker

            # Look up the signal if signal_id provided
            signal = None
            if input.signal_id:
                try:
                    signal = DayTradingSignal.objects.get(signal_id=input.signal_id)
                except DayTradingSignal.DoesNotExist:
                    logger.warning(f"Signal {input.signal_id} not found, logging fill without signal link")

            # Parse times
            entry_time = django_timezone.now()
            exit_time = None
            if input.entry_time:
                try:
                    entry_time = datetime.fromisoformat(input.entry_time.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            if input.exit_time:
                try:
                    exit_time = datetime.fromisoformat(input.exit_time.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass

            # Create UserFill record
            fill = UserFill(
                user=user,
                signal=signal,
                symbol=input.symbol.upper(),
                side=input.side.upper(),
                entry_price=Decimal(str(input.entry_price)),
                exit_price=Decimal(str(input.exit_price)) if input.exit_price else None,
                entry_time=entry_time,
                exit_time=exit_time,
                shares=input.shares or 100,
                outcome=input.outcome or '',
                hit_stop=input.hit_stop or False,
                hit_target=input.hit_target or False,
            )
            fill.save()  # PnL auto-computed in save()

            # Analyze execution quality if we have a signal to compare against
            quality_score = None
            coaching_tip = None
            if signal:
                tracker = ExecutionQualityTracker()
                quality_result = tracker.analyze_fill(
                    signal=signal,
                    actual_fill_price=Decimal(str(input.entry_price)),
                    actual_fill_time=entry_time,
                    signal_type='day_trading'
                )
                quality_score = quality_result.get('quality_score')
                coaching_tip = quality_result.get('coaching_tip')

                # Store quality back into the fill
                fill.slippage_bps = Decimal(str(quality_result.get('slippage_pct', 0) * 100))
                fill.execution_quality_score = Decimal(str(quality_score or 5.0))
                fill.save(update_fields=['slippage_bps', 'execution_quality_score'])

            # Record execution experience for RL optimizer
            try:
                from django.conf import settings as django_settings
                if getattr(django_settings, 'ENABLE_EXECUTION_RL', False):
                    from .execution_rl_service import ExecutionRLService
                    ExecutionRLService().record_experience(fill)
            except Exception as e:
                logger.debug(f"Could not record RL experience: {e}")

            # Check if we should trigger ML retraining
            try:
                recent_fill_count = UserFill.objects.filter(
                    created_at__gte=django_timezone.now() - django_timezone.timedelta(hours=6)
                ).count()
                if recent_fill_count >= 50:
                    from .celery_tasks import trigger_ml_retrain_task
                    trigger_ml_retrain_task.delay()
                    logger.info(f"Triggered ML retrain after {recent_fill_count} recent fills")
            except Exception as e:
                logger.debug(f"Could not check/trigger ML retrain: {e}")

            return LogDayTradingOutcome(
                success=True,
                message="Outcome logged successfully",
                fill_id=str(fill.id),
                execution_quality=quality_score,
                coaching_tip=coaching_tip,
            )
        except Exception as e:
            logger.error(f"Error logging day trading outcome: {e}", exc_info=True)
            return LogDayTradingOutcome(success=False, message=str(e))


class SwingTradingMutations(graphene.ObjectType):
    """GraphQL mutations for swing trading features"""
    
    like_signal = LikeSignal.Field()
    likeSignal = LikeSignal.Field(name='likeSignal')
    
    comment_signal = CommentSignal.Field()
    commentSignal = CommentSignal.Field(name='commentSignal')
    
    log_day_trading_outcome = LogDayTradingOutcome.Field()
    logDayTradingOutcome = LogDayTradingOutcome.Field(name='logDayTradingOutcome')

