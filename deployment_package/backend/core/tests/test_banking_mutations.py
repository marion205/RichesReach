"""
Unit tests for GraphQL banking mutations
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client

from core.banking_mutations import RefreshBankAccount, SetPrimaryAccount, SyncTransactions
from core.banking_models import BankAccount, BankProviderAccount
try:
    from core.schema import schema
except ImportError:
    schema = None  # May not be available in all test contexts

User = get_user_model()


class BankingMutationsTestCase(TestCase):
    """Tests for Banking GraphQL mutations"""
    
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
            is_verified=True,
        )
    
    def _create_context(self, user=None):
        """Create GraphQL context"""
        context = Mock()
        context.user = user or self.user
        return context
    
    @patch('core.banking_mutations.refresh_bank_accounts_task')
    def test_refresh_bank_account_success(self, mock_task):
        """Test successful bank account refresh"""
        context = self._create_context()
        info = Mock()
        info.context = context
        
        result = RefreshBankAccount.mutate(None, info, account_id=self.bank_account.id)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.account)
        mock_task.delay.assert_called_once_with(self.user.id, self.provider_account.id)
    
    def test_refresh_bank_account_unauthenticated(self):
        """Test refresh bank account without authentication"""
        context = self._create_context()
        context.user.is_authenticated = False
        info = Mock()
        info.context = context
        
        result = RefreshBankAccount.mutate(None, info, account_id=self.bank_account.id)
        
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Authentication required")
    
    def test_refresh_bank_account_not_found(self):
        """Test refresh non-existent bank account"""
        context = self._create_context()
        info = Mock()
        info.context = context
        
        with self.assertRaises(BankAccount.DoesNotExist):
            RefreshBankAccount.mutate(None, info, account_id=99999)
    
    def test_set_primary_account_success(self):
        """Test setting primary account"""
        # Create another account
        account2 = BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
            yodlee_account_id='acc_789',
            provider='Test Bank 2',
            is_verified=True,
        )
        
        context = self._create_context()
        info = Mock()
        info.context = context
        
        result = SetPrimaryAccount.mutate(None, info, account_id=account2.id)
        
        self.assertTrue(result.success)
        account2.refresh_from_db()
        self.assertTrue(account2.is_primary)
        
        # Other accounts should not be primary
        self.bank_account.refresh_from_db()
        self.assertFalse(self.bank_account.is_primary)
    
    def test_set_primary_account_unauthenticated(self):
        """Test set primary account without authentication"""
        context = self._create_context()
        context.user.is_authenticated = False
        info = Mock()
        info.context = context
        
        result = SetPrimaryAccount.mutate(None, info, account_id=self.bank_account.id)
        
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Authentication required")
    
    @patch('core.banking_mutations.sync_transactions_task')
    def test_sync_transactions_success(self, mock_task):
        """Test successful transaction sync"""
        context = self._create_context()
        info = Mock()
        info.context = context
        
        result = SyncTransactions.mutate(None, info, account_id=self.bank_account.id)
        
        self.assertTrue(result.success)
        mock_task.delay.assert_called_once_with(self.user.id, self.bank_account.id)
    
    def test_sync_transactions_unauthenticated(self):
        """Test sync transactions without authentication"""
        context = self._create_context()
        context.user.is_authenticated = False
        info = Mock()
        info.context = context
        
        result = SyncTransactions.mutate(None, info, account_id=self.bank_account.id)
        
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Authentication required")


class BankingGraphQLMutationsIntegrationTestCase(TestCase):
    """Integration tests for GraphQL banking mutations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.client = Client(schema)
        
    def _execute_mutation(self, mutation, user=None):
        """Execute GraphQL mutation"""
        context = Mock()
        context.user = user or self.user
        return self.client.execute(mutation, context_value=context)
    
    @patch('core.banking_mutations.refresh_bank_accounts_task')
    def test_refresh_bank_account_mutation(self, mock_task):
        """Test refreshBankAccount GraphQL mutation"""
        # Create test account
        provider_account = BankProviderAccount.objects.create(
            user=self.user,
            provider_account_id='123',
            provider_name='Test Bank',
        )
        bank_account = BankAccount.objects.create(
            user=self.user,
            provider_account=provider_account,
            yodlee_account_id='acc_456',
            provider='Test Bank',
        )
        
        mutation = '''
        mutation {
            refreshBankAccount(accountId: %d) {
                success
                message
            }
        }
        ''' % bank_account.id
        
        result = self._execute_mutation(mutation)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertTrue(result['data']['refreshBankAccount']['success'])
        mock_task.delay.assert_called_once()

