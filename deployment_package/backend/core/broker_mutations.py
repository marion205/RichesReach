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


class PlaceOptionsOrder(graphene.Mutation):
    """Place an options order with guardrails"""
    
    class Arguments:
        symbol = graphene.String(required=True)  # Underlying symbol (e.g., "AAPL")
        strike = graphene.Float(required=True)
        expiration = graphene.String(required=True)  # YYYY-MM-DD format
        option_type = graphene.String(required=True)  # "call" or "put"
        side = graphene.String(required=True)  # "BUY" or "SELL"
        quantity = graphene.Int(required=True)  # Number of contracts
        order_type = graphene.String(default_value='MARKET')  # MARKET or LIMIT
        limit_price = graphene.Float()  # Required for LIMIT orders
        time_in_force = graphene.String(default_value='DAY')
        estimated_premium = graphene.Float()  # For notional calculation
    
    success = graphene.Boolean()
    order_id = graphene.String()
    alpaca_order_id = graphene.String()
    status = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def _build_contract_symbol(symbol: str, expiration: str, option_type: str, strike: float) -> str:
        """
        Build OCC contract symbol format: SYMBOL + YYMMDD + C/P + STRIKE (8 digits, no decimal)
        Example: AAPL240119C00150000 (AAPL, Jan 19 2024, Call, $150.00)
        """
        from datetime import datetime
        
        # Parse expiration date
        try:
            exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        except ValueError:
            # Try alternative formats
            try:
                exp_date = datetime.strptime(expiration, '%Y/%m/%d')
            except ValueError:
                raise ValueError(f"Invalid expiration format: {expiration}. Use YYYY-MM-DD")
        
        # Format: YYMMDD
        date_str = exp_date.strftime('%y%m%d')
        
        # Option type: C for call, P for put
        option_char = 'C' if option_type.lower() == 'call' else 'P'
        
        # Strike: 8 digits, no decimal (multiply by 1000)
        # Example: $150.00 -> 00150000
        strike_int = int(strike * 1000)
        strike_str = f"{strike_int:08d}"
        
        # Combine: SYMBOL + YYMMDD + C/P + STRIKE
        contract_symbol = f"{symbol.upper()}{date_str}{option_char}{strike_str}"
        
        return contract_symbol
    
    @staticmethod
    def mutate(root, info, symbol, strike, expiration, option_type, side, quantity, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return PlaceOptionsOrder(success=False, error="Authentication required")
        
        try:
            broker_account = BrokerAccount.objects.get(user=user)
            
            if not broker_account.alpaca_account_id:
                return PlaceOptionsOrder(success=False, error="Account not created yet")
            
            if broker_account.kyc_status != 'APPROVED':
                return PlaceOptionsOrder(
                    success=False,
                    error=f"Account not approved. Status: {broker_account.kyc_status}"
                )
            
            # Build contract symbol
            try:
                contract_symbol = PlaceOptionsOrder._build_contract_symbol(
                    symbol, expiration, option_type, strike
                )
            except ValueError as e:
                return PlaceOptionsOrder(success=False, error=str(e))
            
            # Calculate notional (premium per contract * quantity * 100)
            # Options contracts are for 100 shares, so multiply by 100
            estimated_premium = kwargs.get('estimated_premium', 0) or kwargs.get('limit_price', 0)
            notional = float(estimated_premium) * float(quantity) * 100.0
            
            # Run guardrail checks (using underlying symbol)
            daily_notional_used = BrokerGuardrails.get_daily_notional_used(user)
            can_place, reason = BrokerGuardrails.can_place_order(
                user, symbol.upper(), notional, kwargs.get('order_type', 'MARKET').upper(), daily_notional_used
            )
            
            # Log guardrail decision
            from .broker_models import BrokerGuardrailLog
            BrokerGuardrailLog.objects.create(
                broker_account=broker_account,
                action='PLACE_OPTIONS_ORDER',
                symbol=contract_symbol,
                notional=notional,
                allowed=can_place,
                reason=reason,
            )
            
            if not can_place:
                return PlaceOptionsOrder(success=False, error=reason)
            
            # Create order record
            client_order_id = str(uuid.uuid4())
            broker_order = BrokerOrder.objects.create(
                broker_account=broker_account,
                client_order_id=client_order_id,
                symbol=contract_symbol,  # Store contract symbol
                side=side.upper(),
                order_type=kwargs.get('order_type', 'MARKET').upper(),
                time_in_force=kwargs.get('time_in_force', 'DAY'),
                quantity=quantity,
                notional=notional,
                limit_price=kwargs.get('limit_price'),
                status='NEW',
                guardrail_checks_passed=True,
            )
            
            # Prepare options order for Alpaca
            limit_price = kwargs.get('limit_price')
            result = alpaca_service.create_options_order(
                account_id=broker_account.alpaca_account_id,
                contract_symbol=contract_symbol,
                side=side.lower(),
                quantity=quantity,
                order_type=kwargs.get('order_type', 'MARKET').lower(),
                limit_price=limit_price,
                time_in_force=kwargs.get('time_in_force', 'DAY').lower()
            )
            
            if result and 'error' in result:
                broker_order.status = 'REJECTED'
                broker_order.rejection_reason = str(result.get('error'))
                broker_order.alpaca_response = result
                broker_order.save()
                return PlaceOptionsOrder(success=False, error=str(result.get('error')))
            
            if result:
                broker_order.alpaca_order_id = result.get('id')
                broker_order.status = result.get('status', 'NEW')
                broker_order.alpaca_response = result
                broker_order.submitted_at = timezone.now()
                broker_order.save()
            
            return PlaceOptionsOrder(
                success=True,
                order_id=broker_order.client_order_id,
                alpaca_order_id=broker_order.alpaca_order_id or '',
                status=broker_order.status
            )
        
        except BrokerAccount.DoesNotExist:
            return PlaceOptionsOrder(success=False, error="Broker account not found")
        except Exception as e:
            logger.error(f"Error placing options order: {e}", exc_info=True)
            return PlaceOptionsOrder(success=False, error=str(e))


class PlaceMultiLegOptionsOrder(graphene.Mutation):
    """Place a multi-leg options order (spreads, straddles, etc.)"""
    
    class Arguments:
        symbol = graphene.String(required=True)  # Underlying symbol
        legs = graphene.List(graphene.JSONString, required=True)  # Array of leg objects
        strategy_name = graphene.String()
    
    success = graphene.Boolean()
    order_ids = graphene.List(graphene.String)  # Multiple orders for multiple legs
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, symbol, legs, strategy_name=None):
        user = info.context.user
        if not user.is_authenticated:
            return PlaceMultiLegOptionsOrder(success=False, error="Authentication required")
        
        try:
            broker_account = BrokerAccount.objects.get(user=user)
            
            if not broker_account.alpaca_account_id:
                return PlaceMultiLegOptionsOrder(success=False, error="Account not created yet")
            
            if broker_account.kyc_status != 'APPROVED':
                return PlaceMultiLegOptionsOrder(
                    success=False,
                    error=f"Account not approved. Status: {broker_account.kyc_status}"
                )
            
            if len(legs) < 2:
                return PlaceMultiLegOptionsOrder(success=False, error="Multi-leg strategies require at least 2 legs")
            
            order_ids = []
            total_notional = 0.0
            
            # Place each leg as a separate order
            for leg in legs:
                # Build contract symbol
                try:
                    contract_symbol = PlaceOptionsOrder._build_contract_symbol(
                        symbol,
                        leg.get('expiration'),
                        leg.get('option_type'),
                        leg.get('strike')
                    )
                except ValueError as e:
                    return PlaceMultiLegOptionsOrder(success=False, error=str(e))
                
                # Calculate notional for this leg
                estimated_premium = leg.get('estimated_premium', 0) or leg.get('limit_price', 0)
                quantity = int(leg.get('quantity', 1))
                leg_notional = float(estimated_premium) * float(quantity) * 100.0
                total_notional += leg_notional
                
                # Run guardrail checks
                daily_notional_used = BrokerGuardrails.get_daily_notional_used(user)
                can_place, reason = BrokerGuardrails.can_place_order(
                    user, symbol.upper(), leg_notional, leg.get('order_type', 'MARKET').upper(), daily_notional_used
                )
                
                if not can_place:
                    return PlaceMultiLegOptionsOrder(success=False, error=f"Leg {legs.index(leg) + 1}: {reason}")
                
                # Create order record
                client_order_id = str(uuid.uuid4())
                broker_order = BrokerOrder.objects.create(
                    broker_account=broker_account,
                    client_order_id=client_order_id,
                    symbol=contract_symbol,
                    side=leg.get('side', 'BUY').upper(),
                    order_type=leg.get('order_type', 'MARKET').upper(),
                    time_in_force=leg.get('time_in_force', 'DAY'),
                    quantity=quantity,
                    notional=leg_notional,
                    limit_price=leg.get('limit_price'),
                    status='NEW',
                    guardrail_checks_passed=True,
                )
                
                # Place order with Alpaca
                limit_price = leg.get('limit_price')
                result = alpaca_service.create_options_order(
                    account_id=broker_account.alpaca_account_id,
                    contract_symbol=contract_symbol,
                    side=leg.get('side', 'BUY').lower(),
                    quantity=quantity,
                    order_type=leg.get('order_type', 'MARKET').lower(),
                    limit_price=limit_price,
                    time_in_force=leg.get('time_in_force', 'DAY').lower()
                )
                
                if result and 'error' in result:
                    broker_order.status = 'REJECTED'
                    broker_order.rejection_reason = str(result.get('error'))
                    broker_order.save()
                    return PlaceMultiLegOptionsOrder(
                        success=False,
                        error=f"Leg {legs.index(leg) + 1} failed: {result.get('error')}"
                    )
                
                if result:
                    broker_order.alpaca_order_id = result.get('id')
                    broker_order.status = result.get('status', 'NEW')
                    broker_order.alpaca_response = result
                    broker_order.submitted_at = timezone.now()
                    broker_order.save()
                    order_ids.append(broker_order.client_order_id)
            
            return PlaceMultiLegOptionsOrder(
                success=True,
                order_ids=order_ids
            )
        
        except BrokerAccount.DoesNotExist:
            return PlaceMultiLegOptionsOrder(success=False, error="Broker account not found")
        except Exception as e:
            logger.error(f"Error placing multi-leg options order: {e}", exc_info=True)
            return PlaceMultiLegOptionsOrder(success=False, error=str(e))


class CloseOptionsPosition(graphene.Mutation):
    """Close an options position (sell to close)"""
    
    class Arguments:
        symbol = graphene.String(required=True)  # Contract symbol
        quantity = graphene.Int()  # Optional: close partial position
    
    success = graphene.Boolean()
    order_id = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, symbol, quantity=None):
        user = info.context.user
        if not user.is_authenticated:
            return CloseOptionsPosition(success=False, error="Authentication required")
        
        try:
            broker_account = BrokerAccount.objects.get(user=user)
            
            if not broker_account.alpaca_account_id:
                return CloseOptionsPosition(success=False, error="Account not created yet")
            
            # Get current position to determine quantity
            position = alpaca_service.get_position(broker_account.alpaca_account_id, symbol)
            if not position:
                return CloseOptionsPosition(success=False, error="Position not found")
            
            qty_to_close = quantity or abs(int(position.get('qty', 0)))
            if qty_to_close <= 0:
                return CloseOptionsPosition(success=False, error="Invalid quantity")
            
            # Determine side based on position
            position_qty = int(position.get('qty', 0))
            side = 'SELL' if position_qty > 0 else 'BUY'  # Close long = sell, close short = buy
            
            # Place market order to close
            result = alpaca_service.create_options_order(
                account_id=broker_account.alpaca_account_id,
                contract_symbol=symbol.upper(),
                side=side.lower(),
                quantity=qty_to_close,
                order_type='market',
                time_in_force='day'
            )
            
            if result and 'error' in result:
                return CloseOptionsPosition(success=False, error=str(result.get('error')))
            
            # Create order record
            client_order_id = str(uuid.uuid4())
            broker_order = BrokerOrder.objects.create(
                broker_account=broker_account,
                client_order_id=client_order_id,
                symbol=symbol.upper(),
                side=side,
                order_type='MARKET',
                time_in_force='DAY',
                quantity=qty_to_close,
                status=result.get('status', 'NEW') if result else 'NEW',
                alpaca_order_id=result.get('id') if result else None,
                alpaca_response=result,
                submitted_at=timezone.now(),
            )
            
            return CloseOptionsPosition(
                success=True,
                order_id=broker_order.client_order_id
            )
        
        except BrokerAccount.DoesNotExist:
            return CloseOptionsPosition(success=False, error="Broker account not found")
        except Exception as e:
            logger.error(f"Error closing options position: {e}", exc_info=True)
            return CloseOptionsPosition(success=False, error=str(e))


class TakeOptionsProfits(graphene.Mutation):
    """Take profits on an options position (limit sell)"""
    
    class Arguments:
        symbol = graphene.String(required=True)  # Contract symbol
        quantity = graphene.Int()  # Optional: partial close
        limit_price = graphene.Float(required=True)  # Target price
    
    success = graphene.Boolean()
    order_id = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, symbol, limit_price, quantity=None):
        user = info.context.user
        if not user.is_authenticated:
            return TakeOptionsProfits(success=False, error="Authentication required")
        
        try:
            broker_account = BrokerAccount.objects.get(user=user)
            
            if not broker_account.alpaca_account_id:
                return TakeOptionsProfits(success=False, error="Account not created yet")
            
            # Get current position
            position = alpaca_service.get_position(broker_account.alpaca_account_id, symbol)
            if not position:
                return TakeOptionsProfits(success=False, error="Position not found")
            
            qty_to_sell = quantity or abs(int(position.get('qty', 0)))
            if qty_to_sell <= 0:
                return TakeOptionsProfits(success=False, error="Invalid quantity")
            
            position_qty = int(position.get('qty', 0))
            side = 'SELL' if position_qty > 0 else 'BUY'
            
            # Place limit order to take profits
            result = alpaca_service.create_options_order(
                account_id=broker_account.alpaca_account_id,
                contract_symbol=symbol.upper(),
                side=side.lower(),
                quantity=qty_to_sell,
                order_type='limit',
                limit_price=limit_price,
                time_in_force='day'
            )
            
            if result and 'error' in result:
                return TakeOptionsProfits(success=False, error=str(result.get('error')))
            
            # Create order record
            client_order_id = str(uuid.uuid4())
            broker_order = BrokerOrder.objects.create(
                broker_account=broker_account,
                client_order_id=client_order_id,
                symbol=symbol.upper(),
                side=side,
                order_type='LIMIT',
                time_in_force='DAY',
                quantity=qty_to_sell,
                limit_price=limit_price,
                status=result.get('status', 'NEW') if result else 'NEW',
                alpaca_order_id=result.get('id') if result else None,
                alpaca_response=result,
                submitted_at=timezone.now(),
            )
            
            return TakeOptionsProfits(
                success=True,
                order_id=broker_order.client_order_id
            )
        
        except BrokerAccount.DoesNotExist:
            return TakeOptionsProfits(success=False, error="Broker account not found")
        except Exception as e:
            logger.error(f"Error taking options profits: {e}", exc_info=True)
            return TakeOptionsProfits(success=False, error=str(e))


class BrokerMutations(graphene.ObjectType):
    create_broker_account = CreateBrokerAccount.Field()
    place_order = PlaceOrder.Field()
    place_options_order = PlaceOptionsOrder.Field()
    place_multi_leg_options_order = PlaceMultiLegOptionsOrder.Field()
    close_options_position = CloseOptionsPosition.Field()
    take_options_profits = TakeOptionsProfits.Field()

