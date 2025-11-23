"""
GraphQL Mutations for Broker Operations
"""
import graphene
import logging
from django.contrib.auth import get_user_model
from .broker_types import BrokerAccountType, BrokerOrderType
from .broker_models import BrokerAccount, BrokerOrder
from .alpaca_broker_service import AlpacaBrokerService, BrokerGuardrails
from django.utils import timezone
import uuid

User = get_user_model()
logger = logging.getLogger(__name__)
alpaca_service = AlpacaBrokerService()


class CreateBrokerAccount(graphene.Mutation):
    """Create/update broker account for KYC onboarding"""
    
    class Arguments:
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        phone_number = graphene.String()
        street_address = graphene.List(graphene.String)
        city = graphene.String()
        state = graphene.String()
        postal_code = graphene.String()
        country = graphene.String(default_value='USA')
        date_of_birth = graphene.String(required=True)
        ssn = graphene.String(required=True)
        funding_source = graphene.List(graphene.String)
    
    success = graphene.Boolean()
    account_id = graphene.String()
    kyc_status = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return CreateBrokerAccount(success=False, error="Authentication required")
        
        try:
            broker_account, created = BrokerAccount.objects.get_or_create(
                user=user,
                defaults={'kyc_status': 'NOT_STARTED'}
            )
            
            # Prepare account data for Alpaca
            account_data = {
                'contact': {
                    'email_address': user.email,
                    'phone_number': kwargs.get('phone_number', ''),
                    'street_address': kwargs.get('street_address', []),
                    'city': kwargs.get('city', ''),
                    'state': kwargs.get('state', ''),
                    'postal_code': kwargs.get('postal_code', ''),
                    'country': kwargs.get('country', 'USA'),
                },
                'identity': {
                    'given_name': kwargs.get('first_name', ''),
                    'family_name': kwargs.get('last_name', ''),
                    'date_of_birth': kwargs.get('date_of_birth', ''),
                    'tax_id': kwargs.get('ssn', ''),
                    'tax_id_type': 'USA_SSN',
                    'country_of_citizenship': 'USA',
                    'country_of_birth': 'USA',
                    'country_of_tax_residence': 'USA',
                    'funding_source': kwargs.get('funding_source', []),
                },
                'disclosures': {
                    'is_control_person': False,
                    'is_affiliated_exchange_or_finra': False,
                    'is_politically_exposed': False,
                    'immediate_family_exposed': False,
                },
                'agreements': [
                    {
                        'agreement': 'customer_agreement',
                        'signed_at': timezone.now().isoformat(),
                        'ip_address': info.context.META.get('REMOTE_ADDR', ''),
                    },
                ],
            }
            
            if broker_account.alpaca_account_id:
                result = alpaca_service.update_account(broker_account.alpaca_account_id, account_data)
            else:
                result = alpaca_service.create_account(account_data)
                if result and 'id' in result:
                    broker_account.alpaca_account_id = result['id']
                    broker_account.kyc_status = 'SUBMITTED'
                    broker_account.save()
            
            if result and 'error' in result:
                return CreateBrokerAccount(
                    success=False,
                    error=str(result.get('error'))
                )
            
            return CreateBrokerAccount(
                success=True,
                account_id=broker_account.alpaca_account_id or '',
                kyc_status=broker_account.kyc_status
            )
        
        except Exception as e:
            logger.error(f"Error creating broker account: {e}", exc_info=True)
            return CreateBrokerAccount(success=False, error=str(e))


class PlaceOrder(graphene.Mutation):
    """Place a broker order with guardrails"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        side = graphene.String(required=True)  # BUY or SELL
        order_type = graphene.String(required=True)  # MARKET, LIMIT, etc.
        quantity = graphene.Int(required=True)
        limit_price = graphene.Float()
        stop_price = graphene.Float()
        time_in_force = graphene.String(default_value='DAY')
        estimated_price = graphene.Float()  # For notional calculation
    
    success = graphene.Boolean()
    order_id = graphene.String()
    alpaca_order_id = graphene.String()
    status = graphene.String()
    execution_suggestion = graphene.JSONString(description="Execution suggestion that was used")
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, symbol, side, order_type, quantity, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return PlaceOrder(success=False, error="Authentication required")
        
        try:
            broker_account = BrokerAccount.objects.get(user=user)
            
            if not broker_account.alpaca_account_id:
                return PlaceOrder(success=False, error="Account not created yet")
            
            if broker_account.kyc_status != 'APPROVED':
                return PlaceOrder(
                    success=False,
                    error=f"Account not approved. Status: {broker_account.kyc_status}"
                )
            
            # Calculate notional
            estimated_price = kwargs.get('limit_price') or kwargs.get('estimated_price', 0)
            notional = float(quantity) * float(estimated_price)
            
            # Run guardrail checks
            daily_notional_used = BrokerGuardrails.get_daily_notional_used(user)
            can_place, reason = BrokerGuardrails.can_place_order(
                user, symbol.upper(), notional, order_type.upper(), daily_notional_used
            )
            
            # Log guardrail decision
            from .broker_models import BrokerGuardrailLog
            BrokerGuardrailLog.objects.create(
                broker_account=broker_account,
                action='PLACE_ORDER',
                symbol=symbol.upper(),
                notional=notional,
                allowed=can_place,
                reason=reason,
            )
            
            if not can_place:
                return PlaceOrder(success=False, error=reason)
            
            # Create order record
            client_order_id = str(uuid.uuid4())
            broker_order = BrokerOrder.objects.create(
                broker_account=broker_account,
                client_order_id=client_order_id,
                symbol=symbol.upper(),
                side=side.upper(),
                order_type=order_type.upper(),
                time_in_force=kwargs.get('time_in_force', 'DAY'),
                quantity=quantity,
                notional=notional,
                limit_price=kwargs.get('limit_price'),
                stop_price=kwargs.get('stop_price'),
                status='NEW',
                guardrail_checks_passed=True,
            )
            
            # Use ExecutionAdvisor if signal_data provided and use_execution_suggestions is True
            execution_suggestion = None
            if kwargs.get('use_execution_suggestions', True) and kwargs.get('signal_data'):
                try:
                    from .alpaca_order_adapter import AlpacaOrderAdapter
                    adapter = AlpacaOrderAdapter()
                    signal_type = kwargs.get('signal_type', 'day_trading')
                    order_data = adapter.create_order_from_signal(
                        kwargs['signal_data'],
                        signal_type=signal_type
                    )
                    alpaca_order = order_data.get('alpaca_order', {})
                    execution_suggestion = order_data.get('execution_suggestion')
                    logger.info(f"✅ Used execution suggestions for {symbol} order")
                except Exception as e:
                    logger.warning(f"⚠️ Execution suggestions failed, using manual order: {e}")
                    # Fallback to manual order
                    alpaca_order = {
                        'symbol': symbol.upper(),
                        'qty': str(quantity),
                        'side': side.lower(),
                        'type': order_type.lower(),
                        'time_in_force': kwargs.get('time_in_force', 'day').lower(),
                    }
                    if kwargs.get('limit_price'):
                        alpaca_order['limit_price'] = str(kwargs['limit_price'])
                    if kwargs.get('stop_price'):
                        alpaca_order['stop_price'] = str(kwargs['stop_price'])
            else:
                # Prepare order for Alpaca (manual)
                alpaca_order = {
                    'symbol': symbol.upper(),
                    'qty': str(quantity),
                    'side': side.lower(),
                    'type': order_type.lower(),
                    'time_in_force': kwargs.get('time_in_force', 'day').lower(),
                }
                
                if kwargs.get('limit_price'):
                    alpaca_order['limit_price'] = str(kwargs['limit_price'])
                if kwargs.get('stop_price'):
                    alpaca_order['stop_price'] = str(kwargs['stop_price'])
            
            # Submit to Alpaca
            result = alpaca_service.create_order(broker_account.alpaca_account_id, alpaca_order)
            
            if result and 'error' in result:
                broker_order.status = 'REJECTED'
                broker_order.rejection_reason = str(result.get('error'))
                broker_order.alpaca_response = result
                broker_order.save()
                return PlaceOrder(success=False, error=str(result.get('error')))
            
            if result:
                broker_order.alpaca_order_id = result.get('id')
                broker_order.status = result.get('status', 'NEW')
                broker_order.alpaca_response = result
                broker_order.submitted_at = timezone.now()
                broker_order.save()
            
            return PlaceOrder(
                success=True,
                order_id=broker_order.client_order_id,
                alpaca_order_id=broker_order.alpaca_order_id or '',
                status=broker_order.status,
                execution_suggestion=execution_suggestion
            )
        
        except BrokerAccount.DoesNotExist:
            return PlaceOrder(success=False, error="Broker account not found")
        except Exception as e:
            logger.error(f"Error placing order: {e}", exc_info=True)
            return PlaceOrder(success=False, error=str(e))


class BrokerMutations(graphene.ObjectType):
    create_broker_account = CreateBrokerAccount.Field()
    place_order = PlaceOrder.Field()

