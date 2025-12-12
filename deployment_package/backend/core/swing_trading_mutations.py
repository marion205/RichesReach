"""
GraphQL Mutations for Swing Trading Features
- Like/unlike signals
- Comment on signals
- Log trading outcomes
"""
import graphene
import logging
from typing import Optional

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


class LogDayTradingOutcome(graphene.Mutation):
    """Log the outcome of a day trading pick"""
    class Arguments:
        input = graphene.JSONString(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, input):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return LogDayTradingOutcome(success=False, message="Authentication required")
            
            # In production, this would log outcome in database
            # For now, return success
            return LogDayTradingOutcome(
                success=True,
                message="Outcome logged successfully"
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

