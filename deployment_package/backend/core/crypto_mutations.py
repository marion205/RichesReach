"""
GraphQL Mutations for Crypto Trading (Alpaca)
"""
import graphene
import logging
from .graphql_utils import get_user_from_context

logger = logging.getLogger(__name__)


class AlpacaCryptoAccountType(graphene.ObjectType):
    """Alpaca crypto account type"""
    id = graphene.String()
    status = graphene.String()
    alpacaCryptoAccountId = graphene.String()
    isApproved = graphene.Boolean()
    usdBalance = graphene.Float()
    totalCryptoValue = graphene.Float()
    createdAt = graphene.String()


class AlpacaCryptoBalanceType(graphene.ObjectType):
    """Alpaca crypto balance type"""
    id = graphene.String()
    symbol = graphene.String()
    totalAmount = graphene.Float()
    availableAmount = graphene.Float()
    usdValue = graphene.Float()
    updatedAt = graphene.String()


class AlpacaCryptoOrderType(graphene.ObjectType):
    """Alpaca crypto order type"""
    id = graphene.String()
    symbol = graphene.String()
    qty = graphene.Float()
    notional = graphene.Float()
    side = graphene.String()
    type = graphene.String()
    timeInForce = graphene.String()
    limitPrice = graphene.Float()
    stopPrice = graphene.Float()
    status = graphene.String()
    filledAvgPrice = graphene.Float()
    filledQty = graphene.Float()
    createdAt = graphene.String()
    submittedAt = graphene.String()
    filledAt = graphene.String()


class CreateAlpacaCryptoOrderResultType(graphene.ObjectType):
    """Result of creating Alpaca crypto order"""
    id = graphene.String()
    symbol = graphene.String()
    side = graphene.String()
    type = graphene.String()
    status = graphene.String()
    createdAt = graphene.String()


class CreateAlpacaCryptoOrderMutation(graphene.Mutation):
    """Create Alpaca crypto order"""
    class Arguments:
        accountId = graphene.Int(required=True)
        symbol = graphene.String(required=True)
        qty = graphene.Float()
        notional = graphene.Float()
        side = graphene.String(required=True)
        type = graphene.String(required=True)
        timeInForce = graphene.String(required=True)
        limitPrice = graphene.Float()
        stopPrice = graphene.Float()
    
    Output = CreateAlpacaCryptoOrderResultType
    
    def mutate(self, info, accountId, symbol, side, type, timeInForce, qty=None, notional=None, limitPrice=None, stopPrice=None):
        """Create crypto order"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return CreateAlpacaCryptoOrderResultType(
                    id="",
                    symbol=symbol,
                    side=side,
                    type=type,
                    status="REJECTED",
                    createdAt=""
                )
            
            # In production, this would create order via Alpaca API
            return CreateAlpacaCryptoOrderResultType(
                id="order-123",
                symbol=symbol,
                side=side,
                type=type,
                status="PENDING",
                createdAt="2024-01-01T12:00:00Z"
            )
        except Exception as e:
            logger.error(f"Error creating crypto order: {e}", exc_info=True)
            return CreateAlpacaCryptoOrderResultType(
                id="",
                symbol=symbol,
                side=side,
                type=type,
                status="REJECTED",
                createdAt=""
            )


class CancelAlpacaCryptoOrderResultType(graphene.ObjectType):
    """Result of canceling Alpaca crypto order"""
    success = graphene.Boolean()
    message = graphene.String()


class CancelAlpacaCryptoOrderMutation(graphene.Mutation):
    """Cancel Alpaca crypto order"""
    class Arguments:
        orderId = graphene.String(required=True)
        accountId = graphene.Int(required=True)
    
    Output = CancelAlpacaCryptoOrderResultType
    
    def mutate(self, info, orderId, accountId):
        """Cancel crypto order"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return CancelAlpacaCryptoOrderResultType(
                    success=False,
                    message="Authentication required"
                )
            
            # In production, this would cancel order via Alpaca API
            return CancelAlpacaCryptoOrderResultType(
                success=True,
                message=f"Order {orderId} canceled"
            )
        except Exception as e:
            logger.error(f"Error canceling crypto order: {e}", exc_info=True)
            return CancelAlpacaCryptoOrderResultType(
                success=False,
                message=str(e)
            )


class CryptoMutations(graphene.ObjectType):
    """Crypto mutations"""
    createAlpacaCryptoOrder = CreateAlpacaCryptoOrderMutation.Field()
    cancelAlpacaCryptoOrder = CancelAlpacaCryptoOrderMutation.Field()

