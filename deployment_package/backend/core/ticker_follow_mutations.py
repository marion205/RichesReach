"""
GraphQL Mutations for Ticker Following
"""
import graphene
from graphql import GraphQLError
from django.contrib.auth import get_user_model

User = get_user_model()


class FollowTickerResultType(graphene.ObjectType):
    """Result type for follow ticker mutation"""
    success = graphene.Boolean()
    message = graphene.String()
    following = graphene.Field('core.types.UserType')


class FollowTicker(graphene.Mutation):
    """Follow a stock ticker"""
    
    class Arguments:
        symbol = graphene.String(required=True)
    
    Output = FollowTickerResultType
    
    @staticmethod
    def mutate(root, info, symbol):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            raise GraphQLError("You must be logged in to follow tickers.")
        
        try:
            symbol = symbol.upper().strip()
            
            # Get current followed tickers
            followed_tickers = getattr(user, 'followedTickers', []) or []
            if not isinstance(followed_tickers, list):
                followed_tickers = []
            
            # Add symbol if not already following
            if symbol not in followed_tickers:
                followed_tickers.append(symbol)
                setattr(user, 'followedTickers', followed_tickers)
                user.save(update_fields=['followedTickers'])
                message = f"Now following {symbol}"
            else:
                message = f"Already following {symbol}"
            
            return FollowTickerResultType(
                success=True,
                message=message,
                following=user
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error following ticker: {e}", exc_info=True)
            return FollowTickerResultType(
                success=False,
                message=f"Failed to follow ticker: {str(e)}"
            )


class UnfollowTicker(graphene.Mutation):
    """Unfollow a stock ticker"""
    
    class Arguments:
        symbol = graphene.String(required=True)
    
    Output = FollowTickerResultType  # Reuse same result type
    
    @staticmethod
    def mutate(root, info, symbol):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            raise GraphQLError("You must be logged in to unfollow tickers.")
        
        try:
            symbol = symbol.upper().strip()
            
            # Get current followed tickers
            followed_tickers = getattr(user, 'followedTickers', []) or []
            if not isinstance(followed_tickers, list):
                followed_tickers = []
            
            # Remove symbol if following
            if symbol in followed_tickers:
                followed_tickers.remove(symbol)
                setattr(user, 'followedTickers', followed_tickers)
                user.save(update_fields=['followedTickers'])
                message = f"Unfollowed {symbol}"
            else:
                message = f"Not following {symbol}"
            
            return FollowTickerResultType(
                success=True,
                message=message,
                following=user
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error unfollowing ticker: {e}", exc_info=True)
            return FollowTickerResultType(
                success=False,
                message=f"Failed to unfollow ticker: {str(e)}"
            )


class TickerFollowMutations(graphene.ObjectType):
    """Mutations for ticker following"""
    follow_ticker = FollowTicker.Field()
    followTicker = FollowTicker.Field()  # CamelCase alias
    unfollow_ticker = UnfollowTicker.Field()
    unfollowTicker = UnfollowTicker.Field()  # CamelCase alias

