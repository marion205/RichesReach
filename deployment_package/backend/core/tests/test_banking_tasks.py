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
            username='testuser'
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
        task_instance = Mock()
        result = refresh_bank_accounts_task(
            task_instance,
            self.user.id,
            self.provider_account.id
        )
        
        # Should return early without error
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_tasks.YodleeClient')
    def test_refresh_bank_accounts_task_success(self, mock_client_class):
        """Test successful account refresh task"""
        mock_client = MagicMock()
        mock_client.refresh_account.return_value = True
        mock_client.get_accounts.return_value = [
            {
                'providerAccountId': '123',
                'accountId': 'acc_456',
                'accountName': 'Checking',
                'accountType': 'CHECKING',
                'balance': {'amount': 1000.0},
            }
        ]
        mock_client_class.return_value = mock_client
        
        task_instance = Mock()
        result = refresh_bank_accounts_task(
            task_instance,
            self.user.id,
            self.provider_account.id
        )
        
        self.assertIsNone(result)  # Task returns None on success
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
        mock_client = MagicMock()
        mock_client.get_transactions.return_value = [
            {
                'id': 'txn_789',
                'amount': {'amount': -50.0},
                'description': {'original': 'Test Transaction'},
                'date': timezone.now().date().isoformat(),
            }
        ]
        mock_client_class.return_value = mock_client
        
        task_instance = Mock()
        result = sync_transactions_task(
            task_instance,
            self.user.id,
            self.bank_account.id
        )
        
        self.assertIsNone(result)  # Task returns None on success
        
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
        mock_client.get_transactions.return_value = []
        mock_client_class.return_value = mock_client
        
        task_instance = Mock()
        result = sync_transactions_task(
            task_instance,
            self.user.id,
            self.bank_account.id
        )
        
        self.assertIsNone(result)
        
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
        
        task_instance = Mock()
        result = process_webhook_event_task(
            task_instance,
            webhook_event.id
        )
        
        self.assertIsNone(result)
        
        # Verify event was marked as processed
        webhook_event.refresh_from_db()
        self.assertTrue(webhook_event.processed)
    
    def test_process_webhook_event_task_not_found(self):
        """Test webhook event processing with non-existent event"""
        task_instance = Mock()
        
        with self.assertRaises(BankWebhookEvent.DoesNotExist):
            process_webhook_event_task(task_instance, 99999)

