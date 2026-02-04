"""
Celery Tasks for Async Execution
Background tasks for RAHA backtesting and other long-running operations
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Celery
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not installed. Install with: pip install celery")
    # Create mock decorator for development
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


@shared_task(bind=True, max_retries=3)
def run_backtest_async(self, backtest_id: int):
    """
    Run a backtest asynchronously using Celery
    
    Args:
        backtest_id: ID of the backtest run to execute
    """
    try:
        from .raha_backtest_service import RAHABacktestService
        from .raha_models import RAHABacktestRun
        
        logger.info(f"Starting async backtest execution for ID: {backtest_id}")
        
        # Get the backtest run
        backtest = RAHABacktestRun.objects.get(id=backtest_id)
        backtest.status = 'RUNNING'
        backtest.save()
        
        # Execute the backtest
        service = RAHABacktestService()
        service.run_backtest(backtest_id)
        
        logger.info(f"Completed async backtest execution for ID: {backtest_id}")
        return {'status': 'success', 'backtest_id': backtest_id}
        
    except Exception as e:
        logger.error(f"Error in async backtest {backtest_id}: {e}", exc_info=True)
        
        # Update backtest status on failure
        try:
            backtest = RAHABacktestRun.objects.get(id=backtest_id)
            backtest.status = 'FAILED'
            backtest.save()
        except:
            pass
        
        # Retry if possible
        if CELERY_AVAILABLE and self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        
        return {'status': 'failed', 'backtest_id': backtest_id, 'error': str(e)}


@shared_task
def process_webhook_async(webhook_id: int):
    """
    Process a banking webhook asynchronously
    
    Args:
        webhook_id: ID of the webhook event to process
    """
    try:
        from .banking_models import BankWebhookEvent
        from .banking_service import refresh_account_data, sync_transactions
        
        logger.info(f"Processing webhook ID: {webhook_id}")
        
        webhook = BankWebhookEvent.objects.get(id=webhook_id)
        event_type = webhook.event_type
        provider_account_id = webhook.provider_account_id
        
        # Process based on event type
        if event_type == 'ACCOUNT_UPDATE':
            # Refresh account data
            refresh_account_data(provider_account_id)
        elif event_type == 'TRANSACTION_UPDATE':
            # Sync new transactions
            sync_transactions(provider_account_id)
        elif event_type == 'ACCOUNT_DISCONNECTED':
            # Mark account as disconnected
            logger.warning(f"Account {provider_account_id} disconnected")
        
        # Mark webhook as processed
        webhook.processed = True
        webhook.processed_at = datetime.now()
        webhook.save()
        
        logger.info(f"Successfully processed webhook ID: {webhook_id}")
        return {'status': 'success', 'webhook_id': webhook_id}
        
    except Exception as e:
        logger.error(f"Error processing webhook {webhook_id}: {e}", exc_info=True)
        return {'status': 'failed', 'webhook_id': webhook_id, 'error': str(e)}
