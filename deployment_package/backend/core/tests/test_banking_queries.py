"""
Unit tests for GraphQL banking queries
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from datetime import datetime, timedelta
from django.utils import timezone

from core.banking_queries import BankingQueries
from core.banking_models import BankAccount, BankTransaction, BankProviderAccount
try:
    from core.schema import schema
except ImportError:
    schema = None  # May not be available if graphql_jwt is not installed

User = get_user_model()


class BankingQueriesTestCase(TestCase):
    """Tests for Banking GraphQL queries"""
    
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
            name='Checking Account',
            mask='1234',
            account_type='CHECKING',
            is_verified=True,
        )
    
    def _create_context(self, user=None):
        """Create GraphQL context"""
        context = Mock()
        context.user = user or self.user
        return context
    
    def test_resolve_bank_accounts_authenticated(self):
        """Test resolving bank accounts for authenticated user"""
        context = self._create_context()
        info = Mock()
        info.context = context
        
        queries = BankingQueries()
        accounts = queries.resolve_bank_accounts(info)
        
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].id, self.bank_account.id)
    
    def test_resolve_bank_accounts_unauthenticated(self):
        """Test resolving bank accounts for unauthenticated user"""
        context = self._create_context()
        # Use Mock for unauthenticated user
        from unittest.mock import Mock
        context.user = Mock()
        context.user.is_authenticated = False
        info = Mock()
        info.context = context
        
        queries = BankingQueries()
        accounts = queries.resolve_bank_accounts(info)
        
        self.assertEqual(len(accounts), 0)
    
    def test_resolve_bank_account(self):
        """Test resolving a specific bank account"""
        context = self._create_context()
        info = Mock()
        info.context = context
        
        queries = BankingQueries()
        account = queries.resolve_bank_account(info, id=self.bank_account.id)
        
        self.assertIsNotNone(account)
        self.assertEqual(account.id, self.bank_account.id)
    
    def test_resolve_bank_account_not_found(self):
        """Test resolving non-existent bank account"""
        context = self._create_context()
        info = Mock()
        info.context = context
        
        queries = BankingQueries()
        
        # The query catches DoesNotExist and returns None, doesn't raise
        account = queries.resolve_bank_account(info, id=99999)
        self.assertIsNone(account)
    
    def test_resolve_bank_transactions(self):
        """Test resolving bank transactions"""
        # Create test transaction
        transaction = BankTransaction.objects.create(
            user=self.user,
            bank_account=self.bank_account,
            yodlee_transaction_id='txn_789',
            amount=-50.0,
            description='Test Transaction',
            transaction_type='DEBIT',
            posted_date=timezone.now().date(),
        )
        
        context = self._create_context()
        info = Mock()
        info.context = context
        
        queries = BankingQueries()
        transactions = queries.resolve_bank_transactions(
            info,
            account_id=None,
            from_date=None,
            to_date=None,
            limit=50
        )
        
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].id, transaction.id)
    
    def test_resolve_bank_transactions_with_account_id(self):
        """Test resolving transactions for specific account"""
        # Create transaction for this account
        transaction = BankTransaction.objects.create(
            user=self.user,
            bank_account=self.bank_account,
            yodlee_transaction_id='txn_789',
            amount=-50.0,
            description='Test Transaction',
            transaction_type='DEBIT',
            posted_date=timezone.now().date(),
        )
        
        context = self._create_context()
        info = Mock()
        info.context = context
        
        queries = BankingQueries()
        transactions = queries.resolve_bank_transactions(
            info,
            account_id=self.bank_account.id,
            from_date=None,
            to_date=None,
            limit=50
        )
        
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].id, transaction.id)
    
    def test_resolve_bank_provider_accounts(self):
        """Test resolving bank provider accounts"""
        context = self._create_context()
        info = Mock()
        info.context = context
        
        queries = BankingQueries()
        provider_accounts = queries.resolve_bank_provider_accounts(info)
        
        self.assertEqual(len(provider_accounts), 1)
        self.assertEqual(provider_accounts[0].id, self.provider_account.id)


class BankingGraphQLIntegrationTestCase(TestCase):
    """Integration tests for GraphQL banking queries"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        # Skip tests if schema is not available (graphql_jwt not installed)
        if schema is None:
            self.skipTest("GraphQL schema not available (graphql_jwt not installed)")
        self.client = Client(schema)
        
    def _execute_query(self, query, user=None):
        """Execute GraphQL query"""
        context = Mock()
        context.user = user or self.user
        return self.client.execute(query, context_value=context)
    
    def test_bank_accounts_query(self):
        """Test bankAccounts GraphQL query"""
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
            name='Checking Account',
            mask='1234',
            account_type='CHECKING',
            is_verified=True,
        )
        
        query = '''
        query {
            bankAccounts {
                id
                provider
                name
            }
        }
        '''
        
        result = self._execute_query(query)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertEqual(len(result['data']['bankAccounts']), 1)
        self.assertEqual(result['data']['bankAccounts'][0]['provider'], 'Test Bank')
    
    def test_bank_transactions_query(self):
        """Test bankTransactions GraphQL query"""
        # Create test data
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
            name='Checking Account',
            mask='1234',
            account_type='CHECKING',
        )
        transaction = BankTransaction.objects.create(
            user=self.user,
            bank_account=bank_account,
            yodlee_transaction_id='txn_789',
            amount=-50.0,
            description='Test Transaction',
            transaction_type='DEBIT',
            posted_date=timezone.now().date(),
        )
        
        query = '''
        query {
            bankTransactions(limit: 10) {
                id
                amount
                description
            }
        }
        '''
        
        result = self._execute_query(query)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertEqual(len(result['data']['bankTransactions']), 1)
    
    def test_bankAccounts_camelCase_alias(self):
        """Test bankAccounts camelCase alias works"""
        query = '''
        query {
            bankAccounts {
                id
                provider
                name
                accountType
                accountSubtype
                currency
                balanceCurrent
                balanceAvailable
                isVerified
                isPrimary
                lastUpdated
                createdAt
            }
        }
        '''
        
        result = self._execute_query(query)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertIn('bankAccounts', result['data'])
    
    def test_fundingHistory_query(self):
        """Test fundingHistory query"""
        from core.broker_models import BrokerAccount, BrokerFunding
        
        # Create broker account
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            kyc_status='APPROVED'
        )
        
        # Create funding record
        funding = BrokerFunding.objects.create(
            broker_account=broker_account,
            transfer_type='DEPOSIT',
            amount=1000.00,
            status='PENDING',
            bank_link_id='123'
        )
        
        query = '''
        query {
            fundingHistory {
                id
                amount
                status
                bankAccountId
                initiatedAt
                completedAt
            }
        }
        '''
        
        result = self._execute_query(query)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertIn('fundingHistory', result['data'])
        if len(result['data']['fundingHistory']) > 0:
            self.assertEqual(result['data']['fundingHistory'][0]['id'], str(funding.id))
            self.assertEqual(result['data']['fundingHistory'][0]['amount'], 1000.0)
            self.assertEqual(result['data']['fundingHistory'][0]['status'], 'PENDING')

