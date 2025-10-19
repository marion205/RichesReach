"""
Alpaca Crypto-specific GraphQL mutations for cryptocurrency trading and management
"""
import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime
import logging

# Get the User model (handles custom user models)
User = get_user_model()

from .models.alpaca_crypto_models import AlpacaCryptoAccount, AlpacaCryptoOrder, AlpacaCryptoBalance, AlpacaCryptoActivity, AlpacaCryptoTransfer
from .services.alpaca_crypto_service import AlpacaCryptoService

logger = logging.getLogger(__name__)

# =============================================================================
# GRAPHQL TYPES
# =============================================================================

class AlpacaCryptoAccountType(DjangoObjectType):
    class Meta:
        model = AlpacaCryptoAccount
        fields = '__all__'

class AlpacaCryptoOrderType(DjangoObjectType):
    class Meta:
        model = AlpacaCryptoOrder
        fields = '__all__'

class AlpacaCryptoBalanceType(DjangoObjectType):
    class Meta:
        model = AlpacaCryptoBalance
        fields = '__all__'

class AlpacaCryptoActivityType(DjangoObjectType):
    class Meta:
        model = AlpacaCryptoActivity
        fields = '__all__'

class AlpacaCryptoTransferType(DjangoObjectType):
    class Meta:
        model = AlpacaCryptoTransfer
        fields = '__all__'

class CryptoAssetType(graphene.ObjectType):
    """Type for crypto assets from Alpaca API"""
    symbol = graphene.String()
    name = graphene.String()
    status = graphene.String()
    tradable = graphene.Boolean()
    marginable = graphene.Boolean()
    shortable = graphene.Boolean()
    easy_to_borrow = graphene.Boolean()
    fractionable = graphene.Boolean()
    min_order_size = graphene.String()
    min_trade_increment = graphene.String()
    price_increment = graphene.String()

class CryptoQuoteType(graphene.ObjectType):
    """Type for crypto quotes"""
    symbol = graphene.String()
    bid = graphene.Float()
    ask = graphene.Float()
    bid_size = graphene.Float()
    ask_size = graphene.Float()
    timestamp = graphene.DateTime()

# =============================================================================
# MUTATIONS
# =============================================================================

class CreateCryptoOrder(graphene.Mutation):
    """Create a crypto trading order"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        side = graphene.String(required=True)
        order_type = graphene.String(required=True)
        quantity = graphene.Float()
        notional = graphene.Float()
        price = graphene.Float()
        stop_price = graphene.Float()
        time_in_force = graphene.String(default_value="day")
    
    success = graphene.Boolean()
    message = graphene.String()
    order = graphene.Field(AlpacaCryptoOrderType)
    alpaca_order_id = graphene.String()
    
    def mutate(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return CreateCryptoOrder(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Get the crypto account
            crypto_account = AlpacaCryptoAccount.objects.get(user=user)
            
            if not crypto_account.is_approved:
                return CreateCryptoOrder(
                    success=False,
                    message="Crypto account not approved for trading"
                )
            
            # Validate order parameters
            crypto_service = AlpacaCryptoService()
            order_data = {
                'symbol': kwargs['symbol'],
                'side': kwargs['side'],
                'type': kwargs['order_type'],
                'time_in_force': kwargs.get('time_in_force', 'day'),
            }
            
            if kwargs.get('quantity'):
                order_data['qty'] = str(kwargs['quantity'])
            elif kwargs.get('notional'):
                order_data['notional'] = str(kwargs['notional'])
            else:
                return CreateCryptoOrder(
                    success=False,
                    message="Either quantity or notional must be specified"
                )
            
            if kwargs.get('price'):
                order_data['limit_price'] = str(kwargs['price'])
            
            if kwargs.get('stop_price'):
                order_data['stop_price'] = str(kwargs['stop_price'])
            
            # Validate order
            validation = crypto_service.validate_crypto_order(order_data)
            if not validation['valid']:
                return CreateCryptoOrder(
                    success=False,
                    message=f"Invalid order: {', '.join(validation['errors'])}"
                )
            
            # Create order in Alpaca
            alpaca_response = crypto_service.create_crypto_order(order_data)
            
            # Create local order record
            crypto_order = AlpacaCryptoOrder.objects.create(
                alpaca_crypto_account=crypto_account,
                alpaca_order_id=alpaca_response['id'],
                symbol=kwargs['symbol'],
                order_type=kwargs['order_type'],
                side=kwargs['side'],
                quantity=kwargs.get('quantity'),
                notional=kwargs.get('notional'),
                price=kwargs.get('price'),
                stop_price=kwargs.get('stop_price'),
                time_in_force=kwargs.get('time_in_force', 'day'),
                status=alpaca_response.get('status', 'new'),
                submitted_at=timezone.now(),
            )
            
            return CreateCryptoOrder(
                success=True,
                message="Crypto order created successfully",
                order=crypto_order,
                alpaca_order_id=alpaca_response['id']
            )
            
        except AlpacaCryptoAccount.DoesNotExist:
            return CreateCryptoOrder(
                success=False,
                message="Crypto account not found. Please create a crypto account first."
            )
        except Exception as e:
            logger.error(f"Failed to create crypto order: {e}")
            return CreateCryptoOrder(
                success=False,
                message=f"Failed to create order: {str(e)}"
            )

class GetCryptoAssets(graphene.Mutation):
    """Get available crypto assets"""
    
    class Arguments:
        status = graphene.String(default_value="active")
    
    success = graphene.Boolean()
    message = graphene.String()
    assets = graphene.List(CryptoAssetType)
    
    def mutate(self, info, **kwargs):
        try:
            crypto_service = AlpacaCryptoService()
            assets_data = crypto_service.get_crypto_assets(kwargs.get('status', 'active'))
            
            assets = []
            for asset_data in assets_data:
                assets.append(CryptoAssetType(
                    symbol=asset_data.get('symbol'),
                    name=asset_data.get('name'),
                    status=asset_data.get('status'),
                    tradable=asset_data.get('tradable', False),
                    marginable=asset_data.get('marginable', False),
                    shortable=asset_data.get('shortable', False),
                    easy_to_borrow=asset_data.get('easy_to_borrow', False),
                    fractionable=asset_data.get('fractionable', False),
                    min_order_size=asset_data.get('min_order_size'),
                    min_trade_increment=asset_data.get('min_trade_increment'),
                    price_increment=asset_data.get('price_increment'),
                ))
            
            return GetCryptoAssets(
                success=True,
                message=f"Retrieved {len(assets)} crypto assets",
                assets=assets
            )
            
        except Exception as e:
            logger.error(f"Failed to get crypto assets: {e}")
            return GetCryptoAssets(
                success=False,
                message=f"Failed to get assets: {str(e)}"
            )

class SyncCryptoData(graphene.Mutation):
    """Sync crypto data from Alpaca API to local database"""
    
    success = graphene.Boolean()
    message = graphene.String()
    synced_orders = graphene.Int()
    synced_balances = graphene.Int()
    synced_activities = graphene.Int()
    
    def mutate(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return SyncCryptoData(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Get the crypto account
            crypto_account = AlpacaCryptoAccount.objects.get(user=user)
            
            crypto_service = AlpacaCryptoService()
            synced_orders = 0
            synced_balances = 0
            synced_activities = 0
            
            # Sync orders
            orders = crypto_service.get_crypto_orders()
            for order_data in orders:
                order, created = AlpacaCryptoOrder.objects.get_or_create(
                    alpaca_order_id=order_data['id'],
                    defaults={
                        'alpaca_crypto_account': crypto_account,
                        'symbol': order_data['symbol'],
                        'order_type': order_data['order_type'],
                        'side': order_data['side'],
                        'quantity': order_data.get('qty'),
                        'notional': order_data.get('notional'),
                        'price': order_data.get('limit_price'),
                        'stop_price': order_data.get('stop_price'),
                        'time_in_force': order_data.get('time_in_force', 'day'),
                        'status': order_data['status'],
                        'filled_quantity': order_data.get('filled_qty', 0),
                        'filled_notional': order_data.get('filled_notional', 0),
                        'average_fill_price': order_data.get('filled_avg_price'),
                        'commission': order_data.get('commission', 0),
                        'commission_asset': order_data.get('commission_asset', 'USD'),
                        'submitted_at': timezone.now(),
                    }
                )
                if created:
                    synced_orders += 1
            
            # Sync balances
            positions = crypto_service.get_crypto_positions()
            for position_data in positions:
                balance, created = AlpacaCryptoBalance.objects.get_or_create(
                    alpaca_crypto_account=crypto_account,
                    asset=position_data['symbol'],
                    defaults={
                        'quantity': position_data['qty'],
                        'available_quantity': position_data.get('available_qty', position_data['qty']),
                        'locked_quantity': position_data.get('locked_qty', 0),
                        'market_value': position_data.get('market_value'),
                        'cost_basis': position_data.get('cost_basis'),
                        'unrealized_pl': position_data.get('unrealized_pl'),
                    }
                )
                if created:
                    synced_balances += 1
            
            # Sync activities
            activities = crypto_service.get_crypto_activities()
            for activity_data in activities:
                activity, created = AlpacaCryptoActivity.objects.get_or_create(
                    alpaca_activity_id=activity_data['id'],
                    defaults={
                        'alpaca_crypto_account': crypto_account,
                        'activity_type': activity_data['activity_type'],
                        'symbol': activity_data.get('symbol', ''),
                        'asset': activity_data.get('asset', ''),
                        'quantity': activity_data.get('qty'),
                        'price': activity_data.get('price'),
                        'net_amount': activity_data.get('net_amount'),
                        'description': activity_data.get('description', ''),
                        'transaction_id': activity_data.get('transaction_id', ''),
                        'activity_date': timezone.now(),
                    }
                )
                if created:
                    synced_activities += 1
            
            return SyncCryptoData(
                success=True,
                message="Crypto data synced successfully",
                synced_orders=synced_orders,
                synced_balances=synced_balances,
                synced_activities=synced_activities
            )
            
        except AlpacaCryptoAccount.DoesNotExist:
            return SyncCryptoData(
                success=False,
                message="Crypto account not found"
            )
        except Exception as e:
            logger.error(f"Failed to sync crypto data: {e}")
            return SyncCryptoData(
                success=False,
                message=f"Failed to sync data: {str(e)}"
            )

class CreateCryptoTransfer(graphene.Mutation):
    """Create an on-chain crypto transfer"""
    
    class Arguments:
        transfer_type = graphene.String(required=True)
        asset = graphene.String(required=True)
        quantity = graphene.Float(required=True)
        to_address = graphene.String()
        from_address = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    transfer = graphene.Field(AlpacaCryptoTransferType)
    
    def mutate(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return CreateCryptoTransfer(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Get the crypto account
            crypto_account = AlpacaCryptoAccount.objects.get(user=user)
            
            if not crypto_account.transfers_enabled:
                return CreateCryptoTransfer(
                    success=False,
                    message="On-chain transfers not enabled for this account"
                )
            
            # Create transfer in Alpaca
            crypto_service = AlpacaCryptoService()
            
            transfer_data = {
                'transfer_type': kwargs['transfer_type'],
                'amount': str(kwargs['quantity']),
                'currency': kwargs['asset'],
            }
            
            if kwargs.get('to_address'):
                transfer_data['address'] = kwargs['to_address']
            
            alpaca_response = crypto_service.create_crypto_transfer(transfer_data)
            
            # Create local transfer record
            crypto_transfer = AlpacaCryptoTransfer.objects.create(
                alpaca_crypto_account=crypto_account,
                alpaca_transfer_id=alpaca_response['id'],
                transfer_type=kwargs['transfer_type'],
                asset=kwargs['asset'],
                quantity=kwargs['quantity'],
                to_address=kwargs.get('to_address', ''),
                from_address=kwargs.get('from_address', ''),
                status=alpaca_response.get('status', 'pending'),
                network_fee=alpaca_response.get('network_fee', 0),
                network_fee_asset=alpaca_response.get('network_fee_asset', 'USD'),
            )
            
            return CreateCryptoTransfer(
                success=True,
                message="Crypto transfer created successfully",
                transfer=crypto_transfer
            )
            
        except AlpacaCryptoAccount.DoesNotExist:
            return CreateCryptoTransfer(
                success=False,
                message="Crypto account not found"
            )
        except Exception as e:
            logger.error(f"Failed to create crypto transfer: {e}")
            return CreateCryptoTransfer(
                success=False,
                message=f"Failed to create transfer: {str(e)}"
            )

# =============================================================================
# QUERIES
# =============================================================================

class AlpacaCryptoQuery(graphene.ObjectType):
    """Alpaca Crypto-related queries"""
    
    my_crypto_account = graphene.Field(AlpacaCryptoAccountType)
    my_crypto_orders = graphene.List(AlpacaCryptoOrderType)
    my_crypto_balances = graphene.List(AlpacaCryptoBalanceType)
    my_crypto_activities = graphene.List(AlpacaCryptoActivityType)
    my_crypto_transfers = graphene.List(AlpacaCryptoTransferType)
    crypto_quotes = graphene.List(CryptoQuoteType, symbols=graphene.List(graphene.String))
    
    def resolve_my_crypto_account(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return None
        try:
            return AlpacaCryptoAccount.objects.get(user=user)
        except AlpacaCryptoAccount.DoesNotExist:
            return None
    
    def resolve_my_crypto_orders(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        try:
            crypto_account = AlpacaCryptoAccount.objects.get(user=user)
            return AlpacaCryptoOrder.objects.filter(alpaca_crypto_account=crypto_account)
        except AlpacaCryptoAccount.DoesNotExist:
            return []
    
    def resolve_my_crypto_balances(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        try:
            crypto_account = AlpacaCryptoAccount.objects.get(user=user)
            return AlpacaCryptoBalance.objects.filter(alpaca_crypto_account=crypto_account)
        except AlpacaCryptoAccount.DoesNotExist:
            return []
    
    def resolve_my_crypto_activities(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        try:
            crypto_account = AlpacaCryptoAccount.objects.get(user=user)
            return AlpacaCryptoActivity.objects.filter(alpaca_crypto_account=crypto_account)
        except AlpacaCryptoAccount.DoesNotExist:
            return []
    
    def resolve_my_crypto_transfers(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        try:
            crypto_account = AlpacaCryptoAccount.objects.get(user=user)
            return AlpacaCryptoTransfer.objects.filter(alpaca_crypto_account=crypto_account)
        except AlpacaCryptoAccount.DoesNotExist:
            return []
    
    def resolve_crypto_quotes(self, info, symbols):
        try:
            crypto_service = AlpacaCryptoService()
            quotes_data = crypto_service.get_crypto_quotes(symbols)
            
            quotes = []
            for symbol, quote_data in quotes_data.get('quotes', {}).items():
                quotes.append(CryptoQuoteType(
                    symbol=symbol,
                    bid=quote_data.get('bp'),
                    ask=quote_data.get('ap'),
                    bid_size=quote_data.get('bs'),
                    ask_size=quote_data.get('as'),
                    timestamp=timezone.now(),
                ))
            
            return quotes
            
        except Exception as e:
            logger.error(f"Failed to get crypto quotes: {e}")
            return []

# =============================================================================
# MUTATION CLASS
# =============================================================================

class AlpacaCryptoMutation(graphene.ObjectType):
    """Alpaca Crypto-related mutations"""
    
    create_crypto_order = CreateCryptoOrder.Field()
    get_crypto_assets = GetCryptoAssets.Field()
    sync_crypto_data = SyncCryptoData.Field()
    create_crypto_transfer = CreateCryptoTransfer.Field()
