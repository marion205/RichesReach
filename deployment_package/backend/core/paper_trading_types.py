"""
Paper Trading GraphQL Types and Mutations
"""
import graphene
from graphene_django import DjangoObjectType
from decimal import Decimal
from .paper_trading_models import (
    PaperTradingAccount, PaperTradingPosition, PaperTradingOrder, PaperTradingTrade
)
from .paper_trading_service import PaperTradingService
from .models import Stock
import logging

logger = logging.getLogger(__name__)


# ===================
# GraphQL Types
# ===================

class PaperTradingAccountType(DjangoObjectType):
    """Paper trading account GraphQL type"""
    class Meta:
        model = PaperTradingAccount
        fields = '__all__'


class PaperTradingPositionType(DjangoObjectType):
    """Paper trading position GraphQL type"""
    stock_symbol = graphene.String()
    stock_name = graphene.String()
    
    class Meta:
        model = PaperTradingPosition
        fields = '__all__'
    
    def resolve_stock_symbol(self, info):
        return self.stock.symbol if self.stock else None
    
    def resolve_stock_name(self, info):
        return self.stock.company_name if self.stock else None


class PaperTradingOrderType(DjangoObjectType):
    """Paper trading order GraphQL type"""
    stock_symbol = graphene.String()
    stock_name = graphene.String()
    
    class Meta:
        model = PaperTradingOrder
        fields = '__all__'
    
    def resolve_stock_symbol(self, info):
        return self.stock.symbol if self.stock else None
    
    def resolve_stock_name(self, info):
        return self.stock.company_name if self.stock else None


class PaperTradingTradeType(DjangoObjectType):
    """Paper trading trade GraphQL type"""
    stock_symbol = graphene.String()
    stock_name = graphene.String()
    
    class Meta:
        model = PaperTradingTrade
        fields = '__all__'
    
    def resolve_stock_symbol(self, info):
        return self.stock.symbol if self.stock else None
    
    def resolve_stock_name(self, info):
        return self.stock.company_name if self.stock else None


class PaperTradingStatisticsType(graphene.ObjectType):
    """Paper trading statistics"""
    total_trades = graphene.Int()
    winning_trades = graphene.Int()
    losing_trades = graphene.Int()
    win_rate = graphene.Float()
    total_pnl = graphene.Float()
    total_pnl_percent = graphene.Float()
    realized_pnl = graphene.Float()
    unrealized_pnl = graphene.Float()


class PaperTradingAccountSummaryType(graphene.ObjectType):
    """Paper trading account summary"""
    account = graphene.Field(PaperTradingAccountType)
    positions = graphene.List(PaperTradingPositionType)
    open_orders = graphene.List(PaperTradingOrderType)
    recent_trades = graphene.List(PaperTradingTradeType)
    statistics = graphene.Field(PaperTradingStatisticsType)


# ===================
# Mutations
# ===================

class PlacePaperOrder(graphene.Mutation):
    """Place a paper trading order"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        side = graphene.String(required=True)  # BUY or SELL
        quantity = graphene.Int(required=True)
        order_type = graphene.String(default_value='MARKET')  # MARKET, LIMIT
        limit_price = graphene.Float(required=False)
        stop_price = graphene.Float(required=False)
    
    success = graphene.Boolean()
    message = graphene.String()
    order = graphene.Field(PaperTradingOrderType)
    
    def mutate(self, info, symbol, side, quantity, order_type='MARKET', limit_price=None, stop_price=None):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return PlacePaperOrder(
                success=False,
                message="Authentication required"
            )
        
        try:
            service = PaperTradingService()
            limit_price_decimal = Decimal(str(limit_price)) if limit_price else None
            stop_price_decimal = Decimal(str(stop_price)) if stop_price else None
            
            order = service.place_order(
                user=user,
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=order_type,
                limit_price=limit_price_decimal,
                stop_price=stop_price_decimal
            )
            
            return PlacePaperOrder(
                success=True,
                message=f"Order placed successfully",
                order=order
            )
        except Exception as e:
            logger.error(f"Error placing paper order: {e}", exc_info=True)
            return PlacePaperOrder(
                success=False,
                message=str(e)
            )


class CancelPaperOrder(graphene.Mutation):
    """Cancel a paper trading order"""
    
    class Arguments:
        order_id = graphene.Int(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, order_id):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return CancelPaperOrder(
                success=False,
                message="Authentication required"
            )
        
        try:
            service = PaperTradingService()
            order = service.cancel_order(user, order_id)
            return CancelPaperOrder(
                success=True,
                message="Order cancelled successfully"
            )
        except Exception as e:
            logger.error(f"Error cancelling paper order: {e}", exc_info=True)
            return CancelPaperOrder(
                success=False,
                message=str(e)
            )


# ===================
# Query Root
# ===================

class PaperTradingQueries(graphene.ObjectType):
    """Paper trading queries"""
    
    paper_account = graphene.Field(PaperTradingAccountType)
    paper_positions = graphene.List(PaperTradingPositionType)
    paper_orders = graphene.List(PaperTradingOrderType, status=graphene.String())
    paper_trade_history = graphene.List(PaperTradingTradeType, limit=graphene.Int())
    paper_account_summary = graphene.Field(PaperTradingAccountSummaryType)
    
    def resolve_paper_account(self, info):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return None
        
        service = PaperTradingService()
        return service.get_account(user)
    
    def resolve_paper_positions(self, info):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return []
        
        service = PaperTradingService()
        return service.get_positions(user)
    
    def resolve_paper_orders(self, info, status=None):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return []
        
        service = PaperTradingService()
        return service.get_orders(user, status=status)
    
    def resolve_paper_trade_history(self, info, limit=100):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return []
        
        service = PaperTradingService()
        return service.get_trade_history(user, limit=limit)
    
    def resolve_paper_account_summary(self, info):
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return None
        
        service = PaperTradingService()
        summary = service.get_account_summary(user)
        
        return PaperTradingAccountSummaryType(
            account=summary['account'],
            positions=summary['positions'],
            open_orders=summary['open_orders'],
            recent_trades=summary['recent_trades'],
            statistics=PaperTradingStatisticsType(**summary['statistics'])
        )


# ===================
# Mutation Root
# ===================

class PaperTradingMutations(graphene.ObjectType):
    """Paper trading mutations"""
    place_paper_order = PlacePaperOrder.Field()
    cancel_paper_order = CancelPaperOrder.Field()

