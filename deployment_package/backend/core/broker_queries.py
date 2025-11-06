"""
GraphQL Queries for Broker Operations
"""
import graphene
from graphene_django import DjangoObjectType
from .broker_types import (
    BrokerAccountType, BrokerOrderType, BrokerPositionType,
    BrokerActivityType, BrokerFundingType
)
from .broker_models import (
    BrokerAccount, BrokerOrder, BrokerPosition, BrokerActivity,
    BrokerFunding
)
from .alpaca_broker_service import AlpacaBrokerService, BrokerGuardrails

alpaca_service = AlpacaBrokerService()


class BrokerQueries(graphene.ObjectType):
    """GraphQL queries for broker operations"""
    
    broker_account = graphene.Field(BrokerAccountType)
    broker_orders = graphene.List(
        BrokerOrderType,
        status=graphene.String(),
        limit=graphene.Int(default_value=50)
    )
    broker_positions = graphene.List(BrokerPositionType)
    broker_activities = graphene.List(
        BrokerActivityType,
        activity_type=graphene.String(),
        date=graphene.String()
    )
    broker_account_info = graphene.JSONString()  # Returns account info with buying power, etc.
    
    def resolve_broker_account(self, info):
        """Get user's broker account"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            return BrokerAccount.objects.get(user=user)
        except BrokerAccount.DoesNotExist:
            return None
    
    def resolve_broker_orders(self, info, status=None, limit=50):
        """Get user's broker orders"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            broker_account = BrokerAccount.objects.get(user=user)
            orders = BrokerOrder.objects.filter(broker_account=broker_account)
            
            if status:
                orders = orders.filter(status=status)
            
            return orders[:limit]
        except BrokerAccount.DoesNotExist:
            return []
    
    def resolve_broker_positions(self, info):
        """Get user's broker positions"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            broker_account = BrokerAccount.objects.get(user=user)
            return BrokerPosition.objects.filter(broker_account=broker_account)
        except BrokerAccount.DoesNotExist:
            return []
    
    def resolve_broker_activities(self, info, activity_type=None, date=None):
        """Get user's broker activities"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            broker_account = BrokerAccount.objects.get(user=user)
            activities = BrokerActivity.objects.filter(broker_account=broker_account)
            
            if activity_type:
                activities = activities.filter(activity_type=activity_type)
            if date:
                activities = activities.filter(date=date)
            
            return activities
        except BrokerAccount.DoesNotExist:
            return []
    
    def resolve_broker_account_info(self, info):
        """Get account info with buying power, daily limits, etc."""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            broker_account = BrokerAccount.objects.get(user=user)
            
            if not broker_account.alpaca_account_id:
                return {
                    'error': 'Account not created yet',
                    'kyc_status': broker_account.kyc_status
                }
            
            # Fetch latest from Alpaca
            account_info = alpaca_service.get_account_info(broker_account.alpaca_account_id)
            account_status = alpaca_service.get_account_status(broker_account.alpaca_account_id)
            
            # Update local cache
            if account_info:
                broker_account.buying_power = float(account_info.get('buying_power', 0))
                broker_account.cash = float(account_info.get('cash', 0))
                broker_account.equity = float(account_info.get('equity', 0))
                broker_account.day_trading_buying_power = float(account_info.get('day_trading_buying_power', 0))
                broker_account.pattern_day_trader = account_info.get('pattern_day_trader', False)
                broker_account.trading_blocked = account_info.get('trading_blocked', False)
                broker_account.transfer_blocked = account_info.get('transfer_blocked', False)
                broker_account.save()
            
            if account_status:
                broker_account.kyc_status = account_status.get('kyc_results', {}).get('status', broker_account.kyc_status)
                broker_account.save()
            
            daily_notional_used = BrokerGuardrails.get_daily_notional_used(user)
            
            return {
                'account_id': broker_account.alpaca_account_id,
                'kyc_status': broker_account.kyc_status,
                'buying_power': float(broker_account.buying_power),
                'cash': float(broker_account.cash),
                'equity': float(broker_account.equity),
                'day_trading_buying_power': float(broker_account.day_trading_buying_power),
                'pattern_day_trader': broker_account.pattern_day_trader,
                'day_trade_count': broker_account.day_trade_count,
                'trading_blocked': broker_account.trading_blocked,
                'transfer_blocked': broker_account.transfer_blocked,
                'daily_notional_used': daily_notional_used,
                'daily_notional_remaining': BrokerGuardrails.MAX_DAILY_NOTIONAL - daily_notional_used,
                'max_per_order': BrokerGuardrails.MAX_PER_ORDER_NOTIONAL,
                'max_daily': BrokerGuardrails.MAX_DAILY_NOTIONAL,
            }
        except BrokerAccount.DoesNotExist:
            return {
                'error': 'Broker account not found',
                'kyc_status': 'NOT_STARTED'
            }

