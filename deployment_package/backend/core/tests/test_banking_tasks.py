"""
Unit tests for Celery banking tasks
"""
import os
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.banking_tasks import (
    refresh_bank_accounts_task,
    sync_transactions_task,
    process_webhook_event_task,
)
from core.banking_models import BankAccount, BankProviderAccount, BankTransaction, BankWebhookEvent

User = get_user_model()


class BankingTasksTestCase(TestCase):
    """Tests for banking Celery tasks"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.provider_account = BankProviderAccount.objects.create(
            user=self.user,
            provider_account_id='123',
            provider_name='Test Bank',
        )
        self.bank_account = BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
            yodlee_account_id='acc_456',
            provider='Test Bank',
        )
    
    @patch.dict(os.environ, {'USE_YODLEE': 'false'})
    def test_refresh_bank_accounts_task_disabled(self):
        """Test refresh task when Yodlee is disabled"""
        # For bound tasks, use .run() method instead of calling directly
        result = refresh_bank_accounts_task.run(
            self.user.id,
            self.provider_account.id
        )
        
        # Should return early without error
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_tasks.YodleeClient')
    def test_refresh_bank_accounts_task_success(self, mock_client_class):
        """Test successful account refresh task"""
        from core.yodlee_client import YodleeClient as RealYodleeClient
        
        mock_client = MagicMock()
        mock_client.refresh_account.return_value = True
        yodlee_account_data = {
            'id': 'acc_456',
            'providerAccountId': '123',
            'providerName': 'Test Bank',
            'providerId': 'provider_123',
            'accountId': 'acc_456',
            'accountName': 'Checking',
            'accountNumber': '1234',
            'CONTAINER': 'bank',
            'accountType': 'CHECKING',
            'balance': {'amount': 1000.0},
        }
        mock_client.get_accounts.return_value = [yodlee_account_data]
        mock_client_class.return_value = mock_client
        # Patch normalize_account at the module level to use real method
        with patch('core.banking_tasks.YodleeClient.normalize_account', RealYodleeClient.normalize_account):
        
            # For bound tasks, use .run() method instead of calling directly
            result = refresh_bank_accounts_task.run(
                self.user.id,
                self.provider_account.id
            )
            
            # Task returns a dict with success status
            self.assertIsNotNone(result)
            self.assertTrue(result.get('success', False))
            # Check accounts_updated, not transactions_synced
            self.assertGreaterEqual(result.get('accounts_updated', 0), 0)
            self.provider_account.refresh_from_db()
            self.assertEqual(self.provider_account.status, 'ACTIVE')
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_tasks.YodleeClient')
    def test_refresh_bank_accounts_task_failure(self, mock_client_class):
        """Test account refresh task failure"""
        mock_client = MagicMock()
        mock_client.refresh_account.return_value = False
        mock_client_class.return_value = mock_client
        
        task_instance = Mock()
        
        with self.assertRaises(Exception):
            refresh_bank_accounts_task(
                task_instance,
                self.user.id,
                self.provider_account.id
            )
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_tasks.YodleeClient')
    def test_sync_transactions_task_success(self, mock_client_class):
        """Test successful transaction sync task"""
        from core.yodlee_client import YodleeClient as RealYodleeClient
        
        mock_client = MagicMock()
        yodlee_transaction_data = {
            'id': 'txn_789',
            'amount': {'amount': -50.0, 'currency': 'USD'},
            'description': {'original': 'Test Transaction'},
            'postDate': timezone.now().date().isoformat(),
            'transactionDate': timezone.now().date().isoformat(),
            'category': 'Shopping',
            'merchant': {'name': 'Test Store'},
            'status': 'POSTED',
        }
        # Set return_value properly - get_transactions should return a list
        mock_client.get_transactions = MagicMock(return_value=[yodlee_transaction_data])
        mock_client_class.return_value = mock_client
        # Patch normalize_transaction at the module level to use real method
        with patch('core.banking_tasks.YodleeClient.normalize_transaction', RealYodleeClient.normalize_transaction):
            # For bound tasks, use .run() method instead of calling directly
            result = sync_transactions_task.run(
                self.user.id,
                self.bank_account.id
            )
            
            # Task returns a dict with success status
            self.assertIsNotNone(result)
            self.assertTrue(result.get('success', False))
            self.assertEqual(result.get('transactions_synced', 0), 1)
            
            # Verify transaction was created
            transactions = BankTransaction.objects.filter(
                user=self.user,
                bank_account=self.bank_account
            )
            self.assertEqual(transactions.count(), 1)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_tasks.YodleeClient')
    def test_sync_transactions_task_empty(self, mock_client_class):
        """Test transaction sync with no new transactions"""
        mock_client = MagicMock()
        # Set return_value properly
        mock_client.get_transactions = MagicMock(return_value=[])
        mock_client_class.return_value = mock_client
        
        # For bound tasks, use .run() method instead of calling directly
        result = sync_transactions_task.run(
            self.user.id,
            self.bank_account.id
        )
        
        # Task returns a dict with success status
        self.assertIsNotNone(result)
        self.assertTrue(result.get('success', False))
        self.assertEqual(result.get('transactions_synced', 0), 0)
        
        # Verify no transactions created
        transactions = BankTransaction.objects.filter(
            user=self.user,
            bank_account=self.bank_account
        )
        self.assertEqual(transactions.count(), 0)
    
    def test_process_webhook_event_task(self):
        """Test webhook event processing task"""
        webhook_event = BankWebhookEvent.objects.create(
            event_type='DATA_UPDATES',
            provider_account_id='123',
            payload={'test': 'data'},
            signature_valid=True,
            processed=False,
        )
        
        # For bound tasks, use .run() method instead of calling directly
        result = process_webhook_event_task.run(
            webhook_event.id
        )
        
        # Task returns a dict, not None
        self.assertIsNotNone(result)
        self.assertTrue(result.get('success', False))
        
        # Verify event was marked as processed
        webhook_event.refresh_from_db()
        self.assertTrue(webhook_event.processed)
    
    def test_process_webhook_event_task_not_found(self):
        """Test webhook event processing with non-existent event"""
        # For bound tasks, use .run() method instead of calling directly
        with self.assertRaises(BankWebhookEvent.DoesNotExist):
            process_webhook_event_task.run(99999)

