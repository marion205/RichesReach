"""
GraphQL Mutations for Trading Operations
Includes placeStockOrder and placeLimitOrder as aliases/convenience mutations
"""
import graphene
import logging
from graphql_jwt.decorators import login_required
from .broker_mutations import PlaceOrder
from .broker_types import BrokerOrderType

logger = logging.getLogger(__name__)


class PlaceStockOrder(graphene.Mutation):
    """Place a stock order (alias for placeOrder with stock-specific defaults)"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        side = graphene.String(required=True)  # BUY or SELL
        quantity = graphene.Int(required=True)
        order_type = graphene.String(default_value='MARKET')  # MARKET or LIMIT
        limit_price = graphene.Float()
        time_in_force = graphene.String(default_value='DAY')
    
    success = graphene.Boolean()
    message = graphene.String()
    order_id = graphene.String()
    error = graphene.String()
    
    @login_required
    def mutate(self, info, symbol, side, quantity, order_type='MARKET', limit_price=None, time_in_force='DAY'):
        # Delegate to PlaceOrder mutation
        place_order = PlaceOrder()
        result = place_order.mutate(
            None, info, 
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            time_in_force=time_in_force
        )
        
        if result.success:
            return PlaceStockOrder(
                success=True,
                message="Order placed successfully",
                order_id=result.order_id or result.alpaca_order_id or ''
            )
        else:
            return PlaceStockOrder(
                success=False,
                message=result.error or "Order failed",
                error=result.error
            )


class PlaceLimitOrder(graphene.Mutation):
    """Place a limit order (alias for placeOrder with order_type='LIMIT')"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        side = graphene.String(required=True)  # BUY or SELL
        quantity = graphene.Int(required=True)
        limit_price = graphene.Float(required=True)
        time_in_force = graphene.String(default_value='DAY')
        notes = graphene.String()
    
    success = graphene.Boolean()
    order = graphene.Field(BrokerOrderType)
    error = graphene.String()
    
    @login_required
    def mutate(self, info, symbol, side, quantity, limit_price, time_in_force='DAY', notes=None):
        # Delegate to PlaceOrder mutation with order_type='LIMIT'
        place_order = PlaceOrder()
        result = place_order.mutate(
            None, info,
            symbol=symbol,
            side=side,
            order_type='LIMIT',
            quantity=quantity,
            limit_price=limit_price,
            time_in_force=time_in_force
        )
        
        if result.success:
            # Fetch the created order
            from .broker_models import BrokerOrder
            try:
                order = BrokerOrder.objects.get(
                    client_order_id=result.order_id
                )
                return PlaceLimitOrder(
                    success=True,
                    order=order
                )
            except BrokerOrder.DoesNotExist:
                return PlaceLimitOrder(
                    success=True,
                    order=None
                )
        else:
            return PlaceLimitOrder(
                success=False,
                error=result.error
            )


class TradingMutations(graphene.ObjectType):
    """Trading-related mutations"""
    place_stock_order = PlaceStockOrder.Field()
    place_limit_order = PlaceLimitOrder.Field()
    # CamelCase aliases for GraphQL schema
    placeStockOrder = PlaceStockOrder.Field()
    placeLimitOrder = PlaceLimitOrder.Field()

