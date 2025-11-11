"""
Banking REST API Views - Yodlee integration endpoints
"""
import os
import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, Any

from .yodlee_client import YodleeClient
from .yodlee_client_enhanced import EnhancedYodleeClient
from .banking_encryption import encrypt_token, decrypt_token
# Import models inside view functions to avoid "Apps aren't loaded" errors

logger = logging.getLogger(__name__)


def _is_yodlee_enabled() -> bool:
    """Check if Yodlee is enabled"""
    return os.getenv('USE_YODLEE', 'false').lower() == 'true'


@method_decorator(csrf_exempt, name='dispatch')
class StartFastlinkView(View):
    """Create FastLink session for bank account linking"""
    
    def get(self, request):
        """GET /api/yodlee/fastlink/start"""
        if not _is_yodlee_enabled():
            return JsonResponse(
                {'error': 'Yodlee integration is disabled'},
                status=503
            )
        
        # Handle case where request.user might be None (FastAPI -> Django conversion)
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            # Use enhanced client with retry logic
            yodlee = EnhancedYodleeClient()
            user_id = str(request.user.id)
            
            # Ensure user exists in Yodlee
            if not yodlee.ensure_user(user_id):
                return JsonResponse(
                    {'error': 'Failed to create Yodlee user session'},
                    status=500
                )
            
            # Create FastLink token
            token = yodlee.create_fastlink_token(user_id)
            if not token:
                return JsonResponse(
                    {'error': 'Failed to create FastLink token'},
                    status=500
                )
            
            fastlink_url = yodlee.fastlink_url
            
            return JsonResponse({
                'fastlinkUrl': fastlink_url,
                'accessToken': token,
                'expiresAt': int((timezone.now() + timedelta(hours=1)).timestamp()),
            })
        
        except Exception as e:
            logger.error(f"Error starting FastLink: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class YodleeCallbackView(View):
    """Handle FastLink callback after bank account linking"""
    
    def post(self, request):
        """POST /api/yodlee/fastlink/callback"""
        if not _is_yodlee_enabled():
            return JsonResponse(
                {'error': 'Yodlee integration is disabled'},
                status=503
            )
        
        # Handle case where request.user might be None (FastAPI -> Django conversion)
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            data = json.loads(request.body)
            provider_account_id = data.get('providerAccountId')
            
            if not provider_account_id:
                return JsonResponse(
                    {'error': 'providerAccountId is required'},
                    status=400
                )
            
            yodlee = YodleeClient()
            user_id = str(request.user.id)
            
            # Get accounts for this provider
            accounts = yodlee.get_accounts(user_id)
            
            # Find accounts for this provider
            provider_accounts = [
                acc for acc in accounts
                if str(acc.get('providerAccountId', '')) == str(provider_account_id)
            ]
            
            if not provider_accounts:
                return JsonResponse(
                    {'error': 'Provider account not found'},
                    status=404
                )
            
            # Import models inside view to avoid "Apps aren't loaded" errors
            from .banking_models import BankProviderAccount, BankAccount
            
            # Store provider account
            provider_account, created = BankProviderAccount.objects.get_or_create(
                user=request.user,
                provider_account_id=str(provider_account_id),
                defaults={
                    'provider_name': provider_accounts[0].get('providerName', ''),
                    'provider_id': provider_accounts[0].get('providerId', ''),
                    'status': 'ACTIVE',
                }
            )
            
            # Store normalized bank accounts
            bank_link_ids = []
            for yodlee_account in accounts:
                if str(yodlee_account.get('providerAccountId', '')) == str(provider_account_id):
                    normalized = YodleeClient.normalize_account(yodlee_account)
                    
                    bank_account, _ = BankAccount.objects.update_or_create(
                        user=request.user,
                        yodlee_account_id=normalized['yodlee_account_id'],
                        defaults={
                            'provider_account': provider_account,
                            'provider': normalized['provider_name'],
                            'name': normalized['name'],
                            'mask': normalized['mask'],
                            'account_type': normalized['account_type'],
                            'account_subtype': normalized['account_subtype'],
                            'currency': normalized['currency'],
                            'balance_current': normalized['balance_current'],
                            'balance_available': normalized['balance_available'],
                            'is_verified': True,
                            'last_updated': timezone.now(),
                        }
                    )
                    bank_link_ids.append(bank_account.id)
            
            return JsonResponse({
                'success': True,
                'message': 'Bank account linked successfully',
                'bankLinkId': provider_account.id,
                'accountsCount': len(bank_link_ids),
            })
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error processing FastLink callback: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AccountsView(View):
    """Get user's bank accounts"""
    
    def get(self, request):
        """GET /api/yodlee/accounts"""
        if not _is_yodlee_enabled():
            return JsonResponse(
                {'error': 'Yodlee integration is disabled'},
                status=503
            )
        
        # Handle case where request.user might be None (FastAPI -> Django conversion)
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            # Import models inside view to avoid "Apps aren't loaded" errors
            from .banking_models import BankAccount, BankProviderAccount
            
            # Try to get from database first
            db_accounts = BankAccount.objects.filter(user=request.user, is_verified=True)
            
            if db_accounts.exists():
                accounts = []
                for db_account in db_accounts:
                    accounts.append({
                        'id': db_account.id,
                        'yodleeAccountId': db_account.yodlee_account_id,
                        'provider': db_account.provider,
                        'name': db_account.name,
                        'mask': db_account.mask,
                        'accountType': db_account.account_type,
                        'accountSubtype': db_account.account_subtype,
                        'currency': db_account.currency,
                        'balance': {
                            'current': float(db_account.balance_current) if db_account.balance_current else None,
                            'available': float(db_account.balance_available) if db_account.balance_available else None,
                        },
                        'isVerified': db_account.is_verified,
                        'isPrimary': db_account.is_primary,
                        'lastUpdated': db_account.last_updated.isoformat() if db_account.last_updated else None,
                    })
                
                return JsonResponse({
                    'success': True,
                    'accounts': accounts,
                    'count': len(accounts),
                })
            
            # If no DB accounts, fetch from Yodlee
            # Use enhanced client with retry logic
            yodlee = EnhancedYodleeClient()
            user_id = str(request.user.id)
            yodlee_accounts = yodlee.get_accounts(user_id)
            
            if not yodlee_accounts:
                return JsonResponse({
                    'success': True,
                    'accounts': [],
                    'count': 0,
                })
            
            # Normalize and store
            accounts = []
            for yodlee_account in yodlee_accounts:
                normalized = YodleeClient.normalize_account(yodlee_account)
                
                # Get or create provider account
                provider_account, _ = BankProviderAccount.objects.get_or_create(
                    user=request.user,
                    provider_account_id=normalized['provider_account_id'],
                    defaults={
                        'provider_name': normalized['provider_name'],
                        'status': 'ACTIVE',
                    }
                )
                
                # Get or create bank account
                bank_account, _ = BankAccount.objects.update_or_create(
                    user=request.user,
                    yodlee_account_id=normalized['yodlee_account_id'],
                    defaults={
                        'provider_account': provider_account,
                        'provider': normalized['provider_name'],
                        'name': normalized['name'],
                        'mask': normalized['mask'],
                        'account_type': normalized['account_type'],
                        'account_subtype': normalized['account_subtype'],
                        'currency': normalized['currency'],
                        'balance_current': normalized['balance_current'],
                        'balance_available': normalized['balance_available'],
                        'is_verified': True,
                        'last_updated': timezone.now(),
                    }
                )
                
                accounts.append({
                    'id': bank_account.id,
                    'yodleeAccountId': bank_account.yodlee_account_id,
                    'provider': bank_account.provider,
                    'name': bank_account.name,
                    'mask': bank_account.mask,
                    'accountType': bank_account.account_type,
                    'accountSubtype': bank_account.account_subtype,
                    'currency': bank_account.currency,
                    'balance': {
                        'current': float(bank_account.balance_current) if bank_account.balance_current else None,
                        'available': float(bank_account.balance_available) if bank_account.balance_available else None,
                    },
                    'isVerified': bank_account.is_verified,
                    'isPrimary': bank_account.is_primary,
                    'lastUpdated': bank_account.last_updated.isoformat() if bank_account.last_updated else None,
                })
            
            return JsonResponse({
                'success': True,
                'accounts': accounts,
                'count': len(accounts),
            })
        
        except Exception as e:
            logger.error(f"Error getting accounts: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TransactionsView(View):
    """Get bank transactions"""
    
    def get(self, request):
        """GET /api/yodlee/transactions?accountId={id}&from={date}&to={date}"""
        if not _is_yodlee_enabled():
            return JsonResponse(
                {'error': 'Yodlee integration is disabled'},
                status=503
            )
        
        # Handle case where request.user might be None (FastAPI -> Django conversion)
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            account_id = request.GET.get('accountId')
            from_date = request.GET.get('from')
            to_date = request.GET.get('to')
            
            # Default to last 30 days if not specified
            if not to_date:
                to_date = timezone.now().date()
            else:
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            
            if not from_date:
                from_date = to_date - timedelta(days=30)
            else:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            
            # Import models inside view to avoid "Apps aren't loaded" errors
            from .banking_models import BankTransaction, BankAccount
            
            # Get from database first
            db_transactions = BankTransaction.objects.filter(
                user=request.user,
                posted_date__gte=from_date,
                posted_date__lte=to_date,
            )
            
            if account_id:
                try:
                    bank_account = BankAccount.objects.get(
                        id=account_id,
                        user=request.user
                    )
                    db_transactions = db_transactions.filter(bank_account=bank_account)
                except BankAccount.DoesNotExist:
                    return JsonResponse({'error': 'Account not found'}, status=404)
            
            if db_transactions.exists():
                transactions = []
                for txn in db_transactions.order_by('-posted_date'):
                    transactions.append({
                        'id': txn.id,
                        'bankAccountId': txn.bank_account.id,
                        'amount': float(txn.amount),
                        'currency': txn.currency,
                        'description': txn.description,
                        'merchantName': txn.merchant_name,
                        'category': txn.category,
                        'subcategory': txn.subcategory,
                        'transactionType': txn.transaction_type,
                        'postedDate': txn.posted_date.isoformat(),
                        'transactionDate': txn.transaction_date.isoformat() if txn.transaction_date else None,
                        'status': txn.status,
                    })
                
                return JsonResponse({
                    'success': True,
                    'transactions': transactions,
                    'count': len(transactions),
                })
            
            # Fetch from Yodlee if not in DB
            # Use enhanced client with retry logic
            yodlee = EnhancedYodleeClient()
            user_id = str(request.user.id)
            
            yodlee_account_id = None
            if account_id:
                try:
                    bank_account = BankAccount.objects.get(
                        id=account_id,
                        user=request.user
                    )
                    yodlee_account_id = bank_account.yodlee_account_id
                except BankAccount.DoesNotExist:
                    return JsonResponse({'error': 'Account not found'}, status=404)
            
            yodlee_transactions = yodlee.get_transactions(
                user_id,
                account_id=yodlee_account_id,
                from_date=from_date.strftime('%Y-%m-%d'),
                to_date=to_date.strftime('%Y-%m-%d'),
            )
            
            # Store transactions
            transactions = []
            for yodlee_txn in yodlee_transactions:
                normalized = YodleeClient.normalize_transaction(yodlee_txn)
                
                # Find bank account
                bank_account = BankAccount.objects.filter(
                    user=request.user,
                    yodlee_account_id=yodlee_txn.get('accountId', ''),
                ).first()
                
                if not bank_account:
                    continue
                
                # Get or create transaction
                txn, _ = BankTransaction.objects.update_or_create(
                    bank_account=bank_account,
                    yodlee_transaction_id=normalized['yodlee_transaction_id'],
                    defaults={
                        'user': request.user,
                        'amount': normalized['amount'],
                        'currency': normalized['currency'],
                        'description': normalized['description'],
                        'merchant_name': normalized['merchant_name'],
                        'category': normalized['category'],
                        'subcategory': normalized['subcategory'],
                        'transaction_type': normalized['transaction_type'],
                        'posted_date': datetime.strptime(normalized['posted_date'], '%Y-%m-%d').date() if normalized['posted_date'] else timezone.now().date(),
                        'transaction_date': datetime.strptime(normalized['transaction_date'], '%Y-%m-%d').date() if normalized['transaction_date'] else None,
                        'status': normalized['status'],
                        'raw_json': normalized['raw_json'],
                    }
                )
                
                transactions.append({
                    'id': txn.id,
                    'bankAccountId': txn.bank_account.id,
                    'amount': float(txn.amount),
                    'currency': txn.currency,
                    'description': txn.description,
                    'merchantName': txn.merchant_name,
                    'category': txn.category,
                    'subcategory': txn.subcategory,
                    'transactionType': txn.transaction_type,
                    'postedDate': txn.posted_date.isoformat(),
                    'transactionDate': txn.transaction_date.isoformat() if txn.transaction_date else None,
                    'status': txn.status,
                })
            
            return JsonResponse({
                'success': True,
                'transactions': transactions,
                'count': len(transactions),
            })
        
        except Exception as e:
            logger.error(f"Error getting transactions: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RefreshAccountView(View):
    """Refresh bank account data"""
    
    def post(self, request):
        """POST /api/yodlee/refresh"""
        if not _is_yodlee_enabled():
            return JsonResponse(
                {'error': 'Yodlee integration is disabled'},
                status=503
            )
        
        # Handle case where request.user might be None (FastAPI -> Django conversion)
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            data = json.loads(request.body)
            bank_link_id = data.get('bankLinkId')
            
            if not bank_link_id:
                return JsonResponse({'error': 'bankLinkId is required'}, status=400)
            
            # Import models inside view functions to avoid "Apps aren't loaded" errors
            from .banking_models import BankProviderAccount
            
            try:
                provider_account = BankProviderAccount.objects.get(
                    id=bank_link_id,
                    user=request.user
                )
            except BankProviderAccount.DoesNotExist:
                return JsonResponse({'error': 'Bank link not found'}, status=404)
            
            # Use enhanced client with retry logic
            yodlee = EnhancedYodleeClient()
            success = yodlee.refresh_account(provider_account.provider_account_id)
            
            if success:
                provider_account.last_refresh = timezone.now()
                provider_account.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Account refresh initiated',
                })
            else:
                return JsonResponse(
                    {'error': 'Failed to refresh account'},
                    status=500
                )
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error refreshing account: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteBankLinkView(View):
    """Delete bank link"""
    
    def delete(self, request, bank_link_id):
        """DELETE /api/yodlee/bank-link/{id}"""
        if not _is_yodlee_enabled():
            return JsonResponse(
                {'error': 'Yodlee integration is disabled'},
                status=503
            )
        
        # Handle case where request.user might be None (FastAPI -> Django conversion)
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            # Import models inside view to avoid "Apps aren't loaded" errors
            from .banking_models import BankProviderAccount
            
            try:
                provider_account = BankProviderAccount.objects.get(
                    id=bank_link_id,
                    user=request.user
                )
            except BankProviderAccount.DoesNotExist:
                return JsonResponse({'error': 'Bank link not found'}, status=404)
            
            # Delete from Yodlee
            # Use enhanced client with retry logic
            yodlee = EnhancedYodleeClient()
            yodlee.delete_account(provider_account.provider_account_id)
            
            # Delete from database
            provider_account.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Bank link deleted successfully',
            })
        
        except Exception as e:
            logger.error(f"Error deleting bank link: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    """Handle Yodlee webhook events"""
    
    def post(self, request):
        """POST /api/yodlee/webhook"""
        if not _is_yodlee_enabled():
            return JsonResponse(
                {'error': 'Yodlee integration is disabled'},
                status=503
            )
        
        try:
            payload = request.body.decode('utf-8')
            signature = request.headers.get('X-Yodlee-Signature', '')
            
            # Verify signature
            # Use enhanced client with retry logic
            yodlee = EnhancedYodleeClient()
            if not yodlee.verify_webhook_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return JsonResponse({'error': 'Invalid signature'}, status=401)
            
            data = json.loads(payload)
            event_type = data.get('eventType', 'UNKNOWN')
            provider_account_id = data.get('providerAccountId', '')
            
            # Import models inside view to avoid "Apps aren't loaded" errors
            from .banking_models import BankWebhookEvent
            
            # Store webhook event
            BankWebhookEvent.objects.create(
                event_type=event_type,
                provider_account_id=provider_account_id,
                payload=data,
                signature_valid=True,
                processed=False,
            )
            
            # TODO: Process webhook (refresh accounts, update transactions, etc.)
            # This can be done async via Celery
            
            return JsonResponse({'success': True, 'message': 'Webhook received'})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

