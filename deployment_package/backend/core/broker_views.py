"""
Django REST API Views for Broker Operations
"""
import logging
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.conf import settings
import json

from .alpaca_broker_service import AlpacaBrokerService, BrokerGuardrails
from .broker_models import (
    BrokerAccount, BrokerOrder, BrokerPosition, BrokerActivity,
    BrokerFunding, BrokerGuardrailLog
)

logger = logging.getLogger(__name__)
alpaca_service = AlpacaBrokerService()


# CSRF exempt - Bearer token auth only (see CSRF_VERIFICATION_CHECKLIST.md)
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class BrokerOnboardView(View):
    """POST /broker/onboard - Create/update Alpaca account (KYC + docs + agreements)"""
    
    def post(self, request):
        try:
            user = request.user
            data = json.loads(request.body)
            
            # Get or create broker account
            broker_account, created = BrokerAccount.objects.get_or_create(
                user=user,
                defaults={'kyc_status': 'NOT_STARTED'}
            )
            
            # Prepare account data for Alpaca
            account_data = {
                'contact': {
                    'email_address': user.email,
                    'phone_number': data.get('phone_number', ''),
                    'street_address': data.get('street_address', []),
                    'city': data.get('city', ''),
                    'state': data.get('state', ''),
                    'postal_code': data.get('postal_code', ''),
                    'country': data.get('country', 'USA'),
                },
                'identity': {
                    'given_name': data.get('first_name', ''),
                    'family_name': data.get('last_name', ''),
                    'date_of_birth': data.get('date_of_birth', ''),
                    'tax_id': data.get('ssn', ''),  # SSN or ITIN
                    'tax_id_type': data.get('tax_id_type', 'USA_SSN'),
                    'country_of_citizenship': data.get('country_of_citizenship', 'USA'),
                    'country_of_birth': data.get('country_of_birth', 'USA'),
                    'country_of_tax_residence': data.get('country_of_tax_residence', 'USA'),
                    'funding_source': data.get('funding_source', []),
                },
                'disclosures': {
                    'is_control_person': data.get('is_control_person', False),
                    'is_affiliated_exchange_or_finra': data.get('is_affiliated_exchange_or_finra', False),
                    'is_politically_exposed': data.get('is_politically_exposed', False),
                    'immediate_family_exposed': data.get('immediate_family_exposed', False),
                },
                'agreements': [
                    {
                        'agreement': 'customer_agreement',
                        'signed_at': timezone.now().isoformat(),
                        'ip_address': request.META.get('REMOTE_ADDR', ''),
                    },
                    {
                        'agreement': 'account_agreement',
                        'signed_at': timezone.now().isoformat(),
                        'ip_address': request.META.get('REMOTE_ADDR', ''),
                    },
                ],
                'documents': [],  # Will be uploaded separately
                'trusted_contact': {
                    'given_name': data.get('trusted_contact_first_name', ''),
                    'family_name': data.get('trusted_contact_last_name', ''),
                    'email_address': data.get('trusted_contact_email', ''),
                },
            }
            
            # Create or update account in Alpaca
            if broker_account.alpaca_account_id:
                # Update existing account
                result = alpaca_service.update_account(broker_account.alpaca_account_id, account_data)
            else:
                # Create new account
                result = alpaca_service.create_account(account_data)
                if result and 'id' in result:
                    broker_account.alpaca_account_id = result['id']
                    broker_account.kyc_status = 'SUBMITTED'
                    broker_account.save()
            
            if result and 'error' in result:
                return JsonResponse({'error': result['error']}, status=400)
            
            return JsonResponse({
                'success': True,
                'account_id': broker_account.alpaca_account_id,
                'kyc_status': broker_account.kyc_status,
            })
        
        except Exception as e:
            logger.error(f"Error in broker onboarding: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


# CSRF exempt - Bearer token auth only (see CSRF_VERIFICATION_CHECKLIST.md)
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class BrokerAccountView(View):
    """GET /broker/account - Get account status, buying power, PDT flags, restrictions"""
    
    def get(self, request):
        try:
            user = request.user
            broker_account = BrokerAccount.objects.get(user=user)
            
            if not broker_account.alpaca_account_id:
                return JsonResponse({'error': 'Account not created yet'}, status=404)
            
            # Fetch latest account info from Alpaca
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
            
            return JsonResponse({
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
            })
        
        except BrokerAccount.DoesNotExist:
            return JsonResponse({'error': 'Broker account not found'}, status=404)
        except Exception as e:
            logger.error(f"Error getting broker account: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


# CSRF exempt - Bearer token auth only (see CSRF_VERIFICATION_CHECKLIST.md)
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class BrokerOrdersView(View):
    """POST /broker/orders - Place order (with guardrails)"""
    
    def post(self, request):
        try:
            user = request.user
            data = json.loads(request.body)
            
            broker_account = BrokerAccount.objects.get(user=user)
            
            if not broker_account.alpaca_account_id:
                return JsonResponse({'error': 'Account not created yet'}, status=400)
            
            if broker_account.kyc_status != 'APPROVED':
                return JsonResponse({
                    'error': f'Account not approved. Status: {broker_account.kyc_status}'
                }, status=400)
            
            # Extract order parameters
            symbol = data.get('symbol', '').upper()
            side = data.get('side', '').upper()
            order_type = data.get('order_type', 'MARKET').upper()
            quantity = int(data.get('quantity', 0))
            limit_price = data.get('limit_price')
            stop_price = data.get('stop_price')
            time_in_force = data.get('time_in_force', 'DAY')
            
            # Calculate notional (approximate)
            # For market orders, we'd need current price - will use limit_price if provided
            estimated_price = limit_price or data.get('estimated_price', 0)
            notional = float(quantity) * float(estimated_price)
            
            # Run guardrail checks
            daily_notional_used = BrokerGuardrails.get_daily_notional_used(user)
            can_place, reason = BrokerGuardrails.can_place_order(
                user, symbol, notional, order_type, daily_notional_used
            )
            
            # Log guardrail decision
            BrokerGuardrailLog.objects.create(
                broker_account=broker_account,
                action='PLACE_ORDER',
                symbol=symbol,
                notional=notional,
                allowed=can_place,
                reason=reason,
                checks_performed={
                    'symbol_whitelisted': BrokerGuardrails.is_symbol_whitelisted(symbol),
                    'notional_check': notional <= BrokerGuardrails.MAX_PER_ORDER_NOTIONAL,
                    'daily_notional_check': daily_notional_used + notional <= BrokerGuardrails.MAX_DAILY_NOTIONAL,
                    'market_hours': BrokerGuardrails.market_is_open_now() if order_type == 'MARKET' else True,
                },
                user_context={
                    'kyc_status': broker_account.kyc_status,
                    'trading_blocked': broker_account.trading_blocked,
                    'pattern_day_trader': broker_account.pattern_day_trader,
                }
            )
            
            if not can_place:
                return JsonResponse({'error': reason}, status=400)
            
            # Create order record
            client_order_id = str(uuid.uuid4())
            broker_order = BrokerOrder.objects.create(
                broker_account=broker_account,
                client_order_id=client_order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                time_in_force=time_in_force,
                quantity=quantity,
                notional=notional,
                limit_price=limit_price,
                stop_price=stop_price,
                status='NEW',
                guardrail_checks_passed=True,
            )
            
            # Prepare order for Alpaca
            alpaca_order = {
                'symbol': symbol,
                'qty': str(quantity),
                'side': side.lower(),
                'type': order_type.lower(),
                'time_in_force': time_in_force.lower(),
            }
            
            if limit_price:
                alpaca_order['limit_price'] = str(limit_price)
            if stop_price:
                alpaca_order['stop_price'] = str(stop_price)
            
            # Submit to Alpaca
            result = alpaca_service.create_order(broker_account.alpaca_account_id, alpaca_order)
            
            if result and 'error' in result:
                broker_order.status = 'REJECTED'
                broker_order.rejection_reason = result.get('detail', {}).get('message', str(result.get('error')))
                broker_order.alpaca_response = result
                broker_order.save()
                return JsonResponse({'error': result.get('error')}, status=400)
            
            if result:
                broker_order.alpaca_order_id = result.get('id')
                broker_order.status = result.get('status', 'NEW')
                broker_order.alpaca_response = result
                broker_order.submitted_at = timezone.now()
                broker_order.save()
            
            return JsonResponse({
                'success': True,
                'order_id': broker_order.client_order_id,
                'alpaca_order_id': broker_order.alpaca_order_id,
                'status': broker_order.status,
            })
        
        except BrokerAccount.DoesNotExist:
            return JsonResponse({'error': 'Broker account not found'}, status=404)
        except Exception as e:
            logger.error(f"Error placing order: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    
    def get(self, request):
        """GET /broker/orders - Get orders"""
        try:
            user = request.user
            broker_account = BrokerAccount.objects.get(user=user)
            
            status_filter = request.GET.get('status')
            limit = int(request.GET.get('limit', 50))
            
            # Fetch from Alpaca
            orders = alpaca_service.get_orders(
                broker_account.alpaca_account_id,
                status=status_filter,
                limit=limit
            )
            
            return JsonResponse({'orders': orders or []})
        
        except BrokerAccount.DoesNotExist:
            return JsonResponse({'error': 'Broker account not found'}, status=404)
        except Exception as e:
            logger.error(f"Error getting orders: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


# CSRF exempt - Bearer token auth only (see CSRF_VERIFICATION_CHECKLIST.md)
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class BrokerPositionsView(View):
    """GET /broker/positions - Get positions"""
    
    def get(self, request):
        try:
            user = request.user
            broker_account = BrokerAccount.objects.get(user=user)
            
            positions = alpaca_service.get_positions(broker_account.alpaca_account_id)
            
            return JsonResponse({'positions': positions or []})
        
        except BrokerAccount.DoesNotExist:
            return JsonResponse({'error': 'Broker account not found'}, status=404)
        except Exception as e:
            logger.error(f"Error getting positions: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


# CSRF exempt - Bearer token auth only (see CSRF_VERIFICATION_CHECKLIST.md)
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class BrokerActivitiesView(View):
    """GET /broker/activities - Get account activities"""
    
    def get(self, request):
        try:
            user = request.user
            broker_account = BrokerAccount.objects.get(user=user)
            
            activity_type = request.GET.get('activity_type')
            date = request.GET.get('date')
            
            activities = alpaca_service.get_activities(
                broker_account.alpaca_account_id,
                activity_type=activity_type,
                date=date
            )
            
            return JsonResponse({'activities': activities or []})
        
        except BrokerAccount.DoesNotExist:
            return JsonResponse({'error': 'Broker account not found'}, status=404)
        except Exception as e:
            logger.error(f"Error getting activities: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def alpaca_webhook_trade_updates(request):
    """POST /webhooks/alpaca/trade_updates - Handle Alpaca trade update webhooks"""
    try:
        # Verify HMAC signature
        signature = request.META.get('HTTP_X_SIGNATURE', '')
        payload = request.body.decode('utf-8')
        
        if not alpaca_service.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            return HttpResponse(status=401)
        
        data = json.loads(payload)
        event = data.get('event')
        order_data = data.get('order', {})
        
        # Find order by Alpaca order ID
        try:
            broker_order = BrokerOrder.objects.get(alpaca_order_id=order_data.get('id'))
        except BrokerOrder.DoesNotExist:
            logger.warning(f"Order not found: {order_data.get('id')}")
            return HttpResponse(status=404)
        
        # Update order status
        broker_order.status = order_data.get('status', broker_order.status)
        broker_order.filled_qty = int(order_data.get('filled_qty', broker_order.filled_qty))
        broker_order.filled_avg_price = float(order_data.get('filled_avg_price', broker_order.filled_avg_price or 0))
        broker_order.alpaca_response = order_data
        
        if event == 'fill':
            broker_order.filled_at = timezone.now()
        
        broker_order.save()
        
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error processing trade update webhook: {e}", exc_info=True)
        return HttpResponse(status=500)


@csrf_exempt
@require_http_methods(["POST"])
def alpaca_webhook_account_updates(request):
    """POST /webhooks/alpaca/account_updates - Handle Alpaca account update webhooks"""
    try:
        # Verify HMAC signature
        signature = request.META.get('HTTP_X_SIGNATURE', '')
        payload = request.body.decode('utf-8')
        
        if not alpaca_service.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            return HttpResponse(status=401)
        
        data = json.loads(payload)
        event = data.get('event')
        account_data = data.get('account', {})
        
        # Find account by Alpaca account ID
        try:
            broker_account = BrokerAccount.objects.get(alpaca_account_id=account_data.get('id'))
        except BrokerAccount.DoesNotExist:
            logger.warning(f"Account not found: {account_data.get('id')}")
            return HttpResponse(status=404)
        
        # Update account status
        if event == 'UPDATED':
            broker_account.status = account_data.get('status', broker_account.status)
            broker_account.trading_blocked = account_data.get('trading_blocked', broker_account.trading_blocked)
            broker_account.transfer_blocked = account_data.get('transfer_blocked', broker_account.transfer_blocked)
            broker_account.save()
        
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error processing account update webhook: {e}", exc_info=True)
        return HttpResponse(status=500)

