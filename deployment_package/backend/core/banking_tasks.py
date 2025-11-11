"""
Celery Tasks for Banking Operations - Async account refresh and transaction sync
"""
import os
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta, datetime
from .banking_models import BankAccount, BankProviderAccount, BankTransaction
from .yodlee_client import YodleeClient

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_bank_accounts_task(self, user_id, provider_account_id):
    """
    Async task to refresh bank account data from Yodlee
    
    Args:
        user_id: Django user ID
        provider_account_id: BankProviderAccount ID
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=user_id)
        provider_account = BankProviderAccount.objects.get(
            id=provider_account_id,
            user=user
        )
        
        # Check if Yodlee is enabled
        if os.getenv('USE_YODLEE', 'false').lower() != 'true':
            logger.warning("Yodlee is disabled, skipping refresh")
            return
        
        yodlee = YodleeClient()
        
        # Refresh account in Yodlee
        success = yodlee.refresh_account(provider_account.provider_account_id)
        
        if not success:
            raise Exception("Failed to refresh account in Yodlee")
        
        # Update last_refresh timestamp
        provider_account.last_refresh = timezone.now()
        provider_account.status = 'ACTIVE'
        provider_account.error_message = ''
        provider_account.save()
        
        # Fetch updated accounts from Yodlee
        user_id_str = str(user_id)
        yodlee_accounts = yodlee.get_accounts(user_id_str)
        
        # Update bank accounts in database
        for yodlee_account in yodlee_accounts:
            if str(yodlee_account.get('providerAccountId', '')) == str(provider_account.provider_account_id):
                normalized = YodleeClient.normalize_account(yodlee_account)
                
                bank_account, created = BankAccount.objects.update_or_create(
                    user=user,
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
        
        logger.info(f"Successfully refreshed bank accounts for user {user_id}")
        return {'success': True, 'accounts_updated': len(yodlee_accounts)}
    
    except Exception as e:
        logger.error(f"Error refreshing bank accounts: {e}", exc_info=True)
        
        # Update error status
        try:
            provider_account = BankProviderAccount.objects.get(id=provider_account_id)
            provider_account.status = 'ERROR'
            provider_account.error_message = str(e)
            provider_account.save()
        except:
            pass
        
        # Retry if not max retries
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_transactions_task(self, user_id, bank_account_id, from_date=None, to_date=None):
    """
    Async task to sync transactions for a bank account
    
    Args:
        user_id: Django user ID
        bank_account_id: BankAccount ID
        from_date: Start date (YYYY-MM-DD) or None for last 30 days
        to_date: End date (YYYY-MM-DD) or None for today
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=user_id)
        bank_account = BankAccount.objects.get(id=bank_account_id, user=user)
        
        # Check if Yodlee is enabled
        if os.getenv('USE_YODLEE', 'false').lower() != 'true':
            logger.warning("Yodlee is disabled, skipping transaction sync")
            return
        
        # Default to last 30 days if not specified
        if not to_date:
            to_date = timezone.now().date()
        else:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        
        if not from_date:
            from_date = to_date - timedelta(days=30)
        else:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        
        yodlee = YodleeClient()
        user_id_str = str(user_id)
        
        # Fetch transactions from Yodlee
        yodlee_transactions = yodlee.get_transactions(
            user_id_str,
            account_id=bank_account.yodlee_account_id,
            from_date=from_date.strftime('%Y-%m-%d'),
            to_date=to_date.strftime('%Y-%m-%d'),
        )
        
        # Store transactions
        count = 0
        for yodlee_txn in yodlee_transactions:
            normalized = YodleeClient.normalize_transaction(yodlee_txn)
            
            # Get or create transaction
            txn, created = BankTransaction.objects.update_or_create(
                bank_account=bank_account,
                yodlee_transaction_id=normalized['yodlee_transaction_id'],
                defaults={
                    'user': user,
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
            if created:
                count += 1
        
        logger.info(f"Successfully synced {count} new transactions for account {bank_account_id}")
        return {'success': True, 'transactions_synced': count}
    
    except Exception as e:
        logger.error(f"Error syncing transactions: {e}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def process_webhook_event_task(self, webhook_event_id):
    """
    Async task to process Yodlee webhook events
    
    Args:
        webhook_event_id: BankWebhookEvent ID
    """
    try:
        from .banking_models import BankWebhookEvent
        
        webhook_event = BankWebhookEvent.objects.get(id=webhook_event_id)
        payload = webhook_event.payload
        
        event_type = payload.get('eventType', '')
        provider_account_id = payload.get('providerAccountId', '')
        
        if event_type == 'REFRESH':
            # Trigger account refresh
            try:
                provider_account = BankProviderAccount.objects.get(
                    provider_account_id=provider_account_id
                )
                refresh_bank_accounts_task.delay(
                    provider_account.user.id,
                    provider_account.id
                )
            except BankProviderAccount.DoesNotExist:
                logger.warning(f"Provider account not found: {provider_account_id}")
        
        elif event_type == 'DATA_UPDATES':
            # Sync transactions for affected accounts
            account_ids = payload.get('accountIds', [])
            for account_id in account_ids:
                try:
                    bank_account = BankAccount.objects.get(
                        yodlee_account_id=str(account_id)
                    )
                    sync_transactions_task.delay(
                        bank_account.user.id,
                        bank_account.id
                    )
                except BankAccount.DoesNotExist:
                    logger.warning(f"Bank account not found: {account_id}")
        
        # Mark webhook as processed
        webhook_event.processed = True
        webhook_event.save()
        
        logger.info(f"Successfully processed webhook event {webhook_event_id}")
        return {'success': True}
    
    except Exception as e:
        logger.error(f"Error processing webhook event: {e}", exc_info=True)
        raise self.retry(exc=e)

