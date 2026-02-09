"""
Unit tests for banking REST API views
"""
import os
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta

from core.banking_views import (
    StartFastlinkView,
    YodleeCallbackView,
    AccountsView,
    TransactionsView,
    RefreshAccountView,
    DeleteBankLinkView,
    WebhookView,
    _is_yodlee_enabled,
)

User = get_user_model()


class BankingViewsTestCase(TestCase):
    """Base test case for banking views"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        # Use Django test client for authentication
        self.client = RequestFactory()
        # Create provider account for tests that need it
        # Note: With --nomigrations, we need to create tables manually
        from django.db import connection
        from core.banking_models import BankProviderAccount
        
        # Create banking tables if they don't exist (for --nomigrations mode)
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='bank_provider_accounts'
            """)
            if not cursor.fetchone():
                # Create tables manually using raw SQL
                # Create bank_provider_accounts table
                cursor.execute("""
                    CREATE TABLE bank_provider_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        provider_account_id VARCHAR(255) NOT NULL UNIQUE,
                        provider_name VARCHAR(255) NOT NULL,
                        provider_id VARCHAR(255) NOT NULL DEFAULT '',
                        access_token_enc TEXT NOT NULL DEFAULT '',
                        refresh_token_enc TEXT NOT NULL DEFAULT '',
                        status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
                        last_refresh DATETIME NULL,
                        error_message TEXT NOT NULL DEFAULT '',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES core_user (id)
                    )
                """)
                cursor.execute("CREATE INDEX bank_provider_accounts_user_provider ON bank_provider_accounts(user_id, provider_account_id)")
                
                # Create bank_accounts table
                cursor.execute("""
                    CREATE TABLE bank_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        provider_account_id INTEGER NULL,
                        yodlee_account_id VARCHAR(255) NOT NULL,
                        provider VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        mask VARCHAR(10) NOT NULL,
                        account_type VARCHAR(50) NOT NULL,
                        account_subtype VARCHAR(50) NOT NULL DEFAULT '',
                        currency VARCHAR(10) NOT NULL DEFAULT 'USD',
                        balance_current DECIMAL(15,2) NULL,
                        balance_available DECIMAL(15,2) NULL,
                        is_verified BOOLEAN NOT NULL DEFAULT 0,
                        is_primary BOOLEAN NOT NULL DEFAULT 0,
                        last_updated DATETIME NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES core_user (id),
                        FOREIGN KEY (provider_account_id) REFERENCES bank_provider_accounts (id)
                    )
                """)
                cursor.execute("CREATE UNIQUE INDEX bank_accounts_user_yodlee ON bank_accounts(user_id, yodlee_account_id)")
                
                # Create bank_transactions table
                cursor.execute("""
                    CREATE TABLE bank_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        bank_account_id INTEGER NOT NULL,
                        yodlee_transaction_id VARCHAR(255) NOT NULL,
                        amount DECIMAL(15,2) NOT NULL,
                        currency VARCHAR(10) NOT NULL DEFAULT 'USD',
                        description VARCHAR(500) NOT NULL,
                        merchant_name VARCHAR(255) NOT NULL DEFAULT '',
                        category VARCHAR(100) NOT NULL DEFAULT '',
                        subcategory VARCHAR(100) NOT NULL DEFAULT '',
                        transaction_type VARCHAR(20) NOT NULL,
                        posted_date DATE NOT NULL,
                        transaction_date DATE NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'POSTED',
                        raw_json TEXT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES core_user (id),
                        FOREIGN KEY (bank_account_id) REFERENCES bank_accounts (id)
                    )
                """)
                cursor.execute("CREATE UNIQUE INDEX bank_transactions_account_yodlee ON bank_transactions(bank_account_id, yodlee_transaction_id)")
                
                # Create bank_webhook_events table
                cursor.execute("""
                    CREATE TABLE bank_webhook_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type VARCHAR(100) NOT NULL,
                        provider_account_id VARCHAR(255) NOT NULL,
                        payload TEXT NOT NULL,
                        signature VARCHAR(500) NOT NULL DEFAULT '',
                        signature_valid BOOLEAN NOT NULL DEFAULT 0,
                        processed BOOLEAN NOT NULL DEFAULT 0,
                        processed_at DATETIME NULL,
                        error_message TEXT NOT NULL DEFAULT '',
                        created_at DATETIME NOT NULL
                    )
                """)
                cursor.execute("CREATE INDEX bank_webhook_events_provider ON bank_webhook_events(provider_account_id)")
        
        self.provider_account = BankProviderAccount.objects.create(
            user=self.user,
            provider_account_id='123',
            provider_name='Test Bank',
        )
        
    def _create_authenticated_request(self, method='GET', path='/', data=None):
        """Helper to create authenticated request"""
        if method == 'GET':
            request = self.factory.get(path)
        elif method == 'POST':
            request = self.factory.post(path, data=json.dumps(data) if data else None, content_type='application/json')
        elif method == 'DELETE':
            request = self.factory.delete(path)
        else:
            request = self.factory.get(path)
        
        request.user = self.user
        return request


class TestStartFastlinkView(BankingViewsTestCase):
    """Tests for StartFastlinkView"""
    
    @patch.dict(os.environ, {'USE_YODLEE': 'false'})
    def test_fastlink_disabled(self):
        """Test that FastLink returns 503 when Yodlee is disabled"""
        request = self._create_authenticated_request('GET', '/api/yodlee/fastlink/start')
        view = StartFastlinkView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Yodlee integration is disabled')
    
    def test_fastlink_unauthenticated(self):
        """Test that FastLink requires authentication"""
        request = self.factory.get('/api/yodlee/fastlink/start')
        request.user = None
        view = StartFastlinkView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Authentication required')
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_views.EnhancedYodleeClient')
    def test_fastlink_success(self, mock_client_class):
        """Test successful FastLink token creation"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.ensure_user_registered.return_value = True
        mock_client.create_fastlink_token.return_value = 'test_token_123'
        mock_client.fastlink_url = 'https://fastlink.example.com'
        mock_client_class.return_value = mock_client
        
        request = self._create_authenticated_request('GET', '/api/yodlee/fastlink/start')
        view = StartFastlinkView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['fastlinkUrl'], 'https://fastlink.example.com')
        self.assertEqual(data['accessToken'], 'test_token_123')
        self.assertIn('expiresAt', data)
        
        # Verify client methods were called
        expected_login = f"rr_{self.user.id}".replace(' ', '_')[:150]
        mock_client.ensure_user_registered.assert_called_once_with(expected_login, self.user.email)
        mock_client.create_fastlink_token.assert_called_once_with(expected_login)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_views.EnhancedYodleeClient')
    def test_fastlink_user_creation_failure(self, mock_client_class):
        """Test handling when user creation fails"""
        mock_client = MagicMock()
        mock_client.ensure_user_registered.return_value = False
        mock_client_class.return_value = mock_client
        
        request = self._create_authenticated_request('GET', '/api/yodlee/fastlink/start')
        view = StartFastlinkView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_views.EnhancedYodleeClient')
    def test_fastlink_token_creation_failure(self, mock_client_class):
        """Test handling when token creation fails"""
        mock_client = MagicMock()
        mock_client.ensure_user_registered.return_value = True
        mock_client.create_fastlink_token.return_value = None
        mock_client_class.return_value = mock_client
        
        request = self._create_authenticated_request('GET', '/api/yodlee/fastlink/start')
        view = StartFastlinkView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)


class TestYodleeCallbackView(BankingViewsTestCase):
    """Tests for YodleeCallbackView"""
    
    @patch.dict(os.environ, {'USE_YODLEE': 'false'})
    def test_callback_disabled(self):
        """Test callback returns 503 when Yodlee is disabled"""
        request = self._create_authenticated_request('POST', '/api/yodlee/fastlink/callback', {})
        view = YodleeCallbackView()
        response = view.post(request)
        
        self.assertEqual(response.status_code, 503)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_views.YodleeClient')
    def test_callback_success(self, mock_client_class):
        """Test successful callback processing"""
        # Setup mocks - use real database models
        from core.yodlee_client import YodleeClient as RealYodleeClient
        mock_client = MagicMock()
        mock_client.get_accounts.return_value = [
            {
                'id': 'acc_456',
                'providerAccountId': '123',
                'providerName': 'Test Bank',
                'providerId': 'provider_123',
                'accountId': 'acc_456',
                'accountName': 'Checking Account',
                'accountNumber': '1234',
                'CONTAINER': 'bank',
                'accountType': 'CHECKING',
                'balance': {'amount': 1000.0},
            }
        ]
        mock_client_class.return_value = mock_client
        # Use real normalize_account method to ensure proper dict is returned
        with patch('core.banking_views.YodleeClient.normalize_account', RealYodleeClient.normalize_account):
            request = self._create_authenticated_request('POST', '/api/yodlee/fastlink/callback', {
                'providerAccountId': '123'
            })
            view = YodleeCallbackView()
            response = view.post(request)
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data['success'], True)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    def test_callback_missing_provider_account_id(self):
        """Test callback with missing providerAccountId"""
        request = self._create_authenticated_request('POST', '/api/yodlee/fastlink/callback', {})
        view = YodleeCallbackView()
        response = view.post(request)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)


class TestAccountsView(BankingViewsTestCase):
    """Tests for AccountsView"""
    
    @patch.dict(os.environ, {'USE_YODLEE': 'false'})
    def test_accounts_disabled(self):
        """Test accounts returns 503 when Yodlee is disabled"""
        request = self._create_authenticated_request('GET', '/api/yodlee/accounts')
        view = AccountsView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 503)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    def test_accounts_from_database(self):
        """Test retrieving accounts from database"""
        # Use real database models - create actual bank account
        from core.banking_models import BankAccount, BankProviderAccount
        
        bank_account = BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
            yodlee_account_id='acc_456',
            provider='Test Bank',
            name='Checking Account',
            mask='1234',
            account_type='CHECKING',
            balance_current=1000.0,
            is_verified=True,
        )
        
        request = self._create_authenticated_request('GET', '/api/yodlee/accounts')
        view = AccountsView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('accounts', data)
        self.assertEqual(len(data['accounts']), 1)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_views.EnhancedYodleeClient')
    def test_accounts_from_yodlee(self, mock_client_class):
        """Test fetching accounts from Yodlee API"""
        # Use real database - ensure no accounts exist first
        from core.banking_models import BankAccount
        BankAccount.objects.filter(user=self.user).delete()
        
        # Mock Yodlee response
        mock_client = MagicMock()
        mock_client.get_accounts.return_value = [
            {
                'id': 'acc_789',
                'providerAccountId': '456',
                'providerName': 'Another Bank',
                'providerId': 'provider_456',
                'accountId': 'acc_789',
                'accountName': 'Savings Account',
                'accountNumber': '5678',
                'CONTAINER': 'bank',
                'accountType': 'SAVINGS',
                'balance': {'amount': 2000.0},
            }
        ]
        mock_client_class.return_value = mock_client
        
        request = self._create_authenticated_request('GET', '/api/yodlee/accounts')
        view = AccountsView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('accounts', data)


class TestTransactionsView(BankingViewsTestCase):
    """Tests for TransactionsView"""
    
    @patch.dict(os.environ, {'USE_YODLEE': 'false'})
    def test_transactions_disabled(self):
        """Test transactions returns 503 when Yodlee is disabled"""
        request = self._create_authenticated_request('GET', '/api/yodlee/transactions')
        view = TransactionsView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 503)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    def test_transactions_from_database(self):
        """Test retrieving transactions from database"""
        # Use real database models
        from core.banking_models import BankTransaction, BankAccount
        
        bank_account = BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
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
        
        request = self._create_authenticated_request('GET', '/api/yodlee/transactions')
        view = TransactionsView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('transactions', data)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    def test_transactions_with_date_range(self):
        """Test transactions with date range parameters"""
        from_date = (timezone.now() - timedelta(days=30)).date().isoformat()
        to_date = timezone.now().date().isoformat()
        
        # Use real database - create a transaction
        from core.banking_models import BankTransaction, BankAccount
        
        bank_account = BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
            yodlee_account_id='acc_456',
            provider='Test Bank',
            name='Checking Account',
            mask='1234',
            account_type='CHECKING',
        )
        
        request = self._create_authenticated_request(
            'GET', 
            f'/api/yodlee/transactions?from={from_date}&to={to_date}'
        )
        view = TransactionsView()
        response = view.get(request)
        self.assertEqual(response.status_code, 200)


class TestRefreshAccountView(BankingViewsTestCase):
    """Tests for RefreshAccountView"""
    
    @patch.dict(os.environ, {'USE_YODLEE': 'false'})
    def test_refresh_disabled(self):
        """Test refresh returns 503 when Yodlee is disabled"""
        request = self._create_authenticated_request('POST', '/api/yodlee/refresh', {})
        view = RefreshAccountView()
        response = view.post(request)
        
        self.assertEqual(response.status_code, 503)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    def test_refresh_missing_bank_link_id(self):
        """Test refresh with missing bankLinkId"""
        request = self._create_authenticated_request('POST', '/api/yodlee/refresh', {})
        view = RefreshAccountView()
        response = view.post(request)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_views.EnhancedYodleeClient')
    def test_refresh_success(self, mock_client_class):
        """Test successful account refresh"""
        # Use real provider account
        from core.banking_models import BankProviderAccount
        from core.yodlee_client import YodleeClient as RealYodleeClient
        
        # Mock Yodlee client
        mock_client = MagicMock()
        mock_client.refresh_account.return_value = True
        mock_client.get_accounts.return_value = [
            {
                'id': 'acc_456',
                'providerAccountId': '123',
                'providerName': 'Test Bank',
                'providerId': 'provider_123',
                'accountId': 'acc_456',
                'accountName': 'Checking Account',
                'accountNumber': '1234',
                'CONTAINER': 'bank',
                'accountType': 'CHECKING',
                'balance': {'amount': 1000.0},
            }
        ]
        mock_client_class.return_value = mock_client
        
        # Use real normalize_account method
        with patch('core.banking_views.YodleeClient.normalize_account', RealYodleeClient.normalize_account):
            request = self._create_authenticated_request('POST', '/api/yodlee/refresh', {
                'bankLinkId': self.provider_account.id
            })
            view = RefreshAccountView()
            response = view.post(request)
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data['success'], True)


class TestDeleteBankLinkView(BankingViewsTestCase):
    """Tests for DeleteBankLinkView"""
    
    @patch.dict(os.environ, {'USE_YODLEE': 'false'})
    def test_delete_disabled(self):
        """Test delete returns 503 when Yodlee is disabled"""
        request = self._create_authenticated_request('DELETE', '/api/yodlee/bank-link/1')
        view = DeleteBankLinkView()
        response = view.delete(request, bank_link_id=1)
        
        self.assertEqual(response.status_code, 503)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_views.EnhancedYodleeClient')
    def test_delete_success(self, mock_client_class):
        """Test successful bank link deletion"""
        # Use real provider account
        from core.banking_models import BankProviderAccount
        
        # Mock Yodlee client
        mock_client = MagicMock()
        mock_client.delete_account.return_value = True
        mock_client_class.return_value = mock_client
        
        request = self._create_authenticated_request('DELETE', f'/api/yodlee/bank-link/{self.provider_account.id}')
        view = DeleteBankLinkView()
        response = view.delete(request, bank_link_id=self.provider_account.id)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        
        # Verify deletion - provider account should no longer exist
        from core.banking_models import BankProviderAccount
        self.assertFalse(BankProviderAccount.objects.filter(id=self.provider_account.id).exists())


class TestWebhookView(BankingViewsTestCase):
    """Tests for WebhookView"""
    
    @patch.dict(os.environ, {'USE_YODLEE': 'false'})
    def test_webhook_disabled(self):
        """Test webhook returns 503 when Yodlee is disabled"""
        request = self._create_authenticated_request('POST', '/api/yodlee/webhook', {})
        view = WebhookView()
        response = view.post(request)
        
        self.assertEqual(response.status_code, 503)
    
    @patch.dict(os.environ, {'USE_YODLEE': 'true'})
    @patch('core.banking_views.EnhancedYodleeClient')
    def test_webhook_success(self, mock_client_class):
        """Test successful webhook processing"""
        # Mock Yodlee client with signature verification
        mock_client = MagicMock()
        mock_client.verify_webhook_signature.return_value = True
        mock_client_class.return_value = mock_client
        
        webhook_data = {
            'eventType': 'DATA_UPDATES',
            'providerAccountId': '123',
            'additionalData': {}
        }
        
        request = self._create_authenticated_request('POST', '/api/yodlee/webhook', webhook_data)
        view = WebhookView()
        response = view.post(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)


class TestYodleeEnabledHelper(TestCase):
    """Tests for _is_yodlee_enabled helper function"""
    
    def test_yodlee_enabled_true(self):
        """Test when USE_YODLEE is true"""
        with patch.dict(os.environ, {'USE_YODLEE': 'true'}):
            self.assertTrue(_is_yodlee_enabled())
    
    def test_yodlee_enabled_false(self):
        """Test when USE_YODLEE is false"""
        with patch.dict(os.environ, {'USE_YODLEE': 'false'}):
            self.assertFalse(_is_yodlee_enabled())
    
    def test_yodlee_enabled_missing(self):
        """Test when USE_YODLEE is not set"""
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(_is_yodlee_enabled())
    
    def test_yodlee_enabled_case_insensitive(self):
        """Test that case doesn't matter"""
        with patch.dict(os.environ, {'USE_YODLEE': 'TRUE'}):
            self.assertTrue(_is_yodlee_enabled())
        
        with patch.dict(os.environ, {'USE_YODLEE': 'True'}):
            self.assertTrue(_is_yodlee_enabled())

