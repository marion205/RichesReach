"""
Unit tests for Alpaca Broker Service
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, time
from django.test import TestCase
from django.contrib.auth import get_user_model

from core.alpaca_broker_service import AlpacaBrokerService, BrokerGuardrails

User = get_user_model()


class AlpacaBrokerServiceTestCase(TestCase):
    """Tests for Alpaca Broker Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch.dict(os.environ, {
            'ALPACA_BROKER_API_KEY': 'test_key',
            'ALPACA_BROKER_API_SECRET': 'test_secret',
            'ALPACA_BROKER_BASE_URL': 'https://test.alpaca.markets',
            'ALPACA_WEBHOOK_SECRET': 'test_webhook_secret'
        }):
            self.service = AlpacaBrokerService()
    
    def test_initialization(self):
        """Test service initialization"""
        self.assertEqual(self.service.api_key, 'test_key')
        self.assertEqual(self.service.api_secret, 'test_secret')
        self.assertEqual(self.service.base_url, 'https://test.alpaca.markets')
        self.assertEqual(self.service.webhook_secret, 'test_webhook_secret')
    
    def test_initialization_no_credentials(self):
        """Test initialization without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            service = AlpacaBrokerService()
            self.assertIsNone(service.api_key)
            self.assertIsNone(service.api_secret)
    
    def test_get_headers(self):
        """Test authentication headers"""
        headers = self.service._get_headers()
        self.assertEqual(headers['APCA-API-KEY-ID'], 'test_key')
        self.assertEqual(headers['APCA-API-SECRET-KEY'], 'test_secret')
        self.assertEqual(headers['Content-Type'], 'application/json')
    
    @patch('core.alpaca_broker_service.requests.get')
    def test_make_request_get_success(self, mock_get):
        """Test successful GET request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'test': 'data'}
        mock_response.content = b'{"test": "data"}'
        mock_get.return_value = mock_response
        
        result = self.service._make_request('GET', '/test', params={'key': 'value'})
        self.assertEqual(result, {'test': 'data'})
        mock_get.assert_called_once()
    
    @patch('core.alpaca_broker_service.requests.post')
    def test_make_request_post_success(self, mock_post):
        """Test successful POST request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': '123'}
        mock_response.content = b'{"id": "123"}'
        mock_post.return_value = mock_response
        
        result = self.service._make_request('POST', '/test', data={'key': 'value'})
        self.assertEqual(result, {'id': '123'})
        mock_post.assert_called_once()
    
    @patch('core.alpaca_broker_service.requests.patch')
    def test_make_request_patch_success(self, mock_patch):
        """Test successful PATCH request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'updated': True}
        mock_response.content = b'{"updated": true}'
        mock_patch.return_value = mock_response
        
        result = self.service._make_request('PATCH', '/test', data={'key': 'value'})
        self.assertEqual(result, {'updated': True})
    
    @patch('core.alpaca_broker_service.requests.delete')
    def test_make_request_delete_success(self, mock_delete):
        """Test successful DELETE request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b''
        mock_delete.return_value = mock_response
        
        result = self.service._make_request('DELETE', '/test')
        self.assertEqual(result, {})
    
    @patch('core.alpaca_broker_service.requests.get')
    def test_make_request_http_error(self, mock_get):
        """Test HTTP error handling"""
        from requests.exceptions import HTTPError
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'error': 'Not found'}
        mock_response.content = b'{"error": "Not found"}'
        
        # Create HTTPError with response
        http_error = HTTPError('404 Not Found')
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response
        
        result = self.service._make_request('GET', '/test')
        self.assertIn('error', result)
    
    @patch('core.alpaca_broker_service.requests.get')
    def test_make_request_no_credentials(self, mock_get):
        """Test request without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            service = AlpacaBrokerService()
            result = service._make_request('GET', '/test')
            self.assertIsNone(result)
            mock_get.assert_not_called()
    
    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature verification"""
        payload = 'test_payload'
        import hmac
        import hashlib
        expected_sig = hmac.new(
            'test_webhook_secret'.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = self.service.verify_webhook_signature(payload, expected_sig)
        self.assertTrue(result)
    
    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature verification"""
        payload = 'test_payload'
        invalid_sig = 'invalid_signature'
        
        result = self.service.verify_webhook_signature(payload, invalid_sig)
        self.assertFalse(result)
    
    def test_verify_webhook_signature_no_secret(self):
        """Test webhook verification without secret"""
        with patch.dict(os.environ, {'ALPACA_WEBHOOK_SECRET': ''}):
            service = AlpacaBrokerService()
            result = service.verify_webhook_signature('payload', 'signature')
            self.assertTrue(result)  # Should return True when no secret configured
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_create_account(self, mock_request):
        """Test account creation"""
        mock_request.return_value = {'id': 'acc_123', 'status': 'ACTIVE'}
        result = self.service.create_account({'name': 'Test Account'})
        self.assertEqual(result['id'], 'acc_123')
        mock_request.assert_called_once_with('POST', '/v1/accounts', data={'name': 'Test Account'})
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_account(self, mock_request):
        """Test get account"""
        mock_request.return_value = {'id': 'acc_123', 'name': 'Test'}
        result = self.service.get_account('acc_123')
        self.assertEqual(result['id'], 'acc_123')
        mock_request.assert_called_once_with('GET', '/v1/accounts/acc_123')
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_update_account(self, mock_request):
        """Test account update"""
        mock_request.return_value = {'id': 'acc_123', 'updated': True}
        result = self.service.update_account('acc_123', {'name': 'Updated'})
        self.assertEqual(result['id'], 'acc_123')
        mock_request.assert_called_once_with('PATCH', '/v1/accounts/acc_123', data={'name': 'Updated'})
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_account_status(self, mock_request):
        """Test get account status"""
        mock_request.return_value = {'kyc_status': 'APPROVED'}
        result = self.service.get_account_status('acc_123')
        self.assertEqual(result['kyc_status'], 'APPROVED')
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_create_order(self, mock_request):
        """Test order creation"""
        mock_request.return_value = {'id': 'order_123', 'status': 'NEW'}
        order_data = {'symbol': 'AAPL', 'qty': 10, 'side': 'buy'}
        result = self.service.create_order('acc_123', order_data)
        self.assertEqual(result['id'], 'order_123')
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_order(self, mock_request):
        """Test get order"""
        mock_request.return_value = {'id': 'order_123', 'symbol': 'AAPL'}
        result = self.service.get_order('acc_123', 'order_123')
        self.assertEqual(result['id'], 'order_123')
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_cancel_order(self, mock_request):
        """Test order cancellation"""
        mock_request.return_value = {'id': 'order_123', 'status': 'CANCELED'}
        result = self.service.cancel_order('acc_123', 'order_123')
        self.assertEqual(result['status'], 'CANCELED')
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_orders(self, mock_request):
        """Test get orders"""
        mock_request.return_value = [{'id': 'order_1'}, {'id': 'order_2'}]
        result = self.service.get_orders('acc_123', status='FILLED', limit=10)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result, list)
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_orders_non_list(self, mock_request):
        """Test get orders with non-list response"""
        mock_request.return_value = {'error': 'Not found'}
        result = self.service.get_orders('acc_123')
        self.assertEqual(result, [])
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_positions(self, mock_request):
        """Test get positions"""
        mock_request.return_value = [{'symbol': 'AAPL', 'qty': 10}]
        result = self.service.get_positions('acc_123')
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result, list)
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_position(self, mock_request):
        """Test get specific position"""
        mock_request.return_value = {'symbol': 'AAPL', 'qty': 10}
        result = self.service.get_position('acc_123', 'AAPL')
        self.assertEqual(result['symbol'], 'AAPL')
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_account_info(self, mock_request):
        """Test get account info"""
        mock_request.return_value = {'buying_power': 10000, 'cash': 5000}
        result = self.service.get_account_info('acc_123')
        self.assertIn('buying_power', result)
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_activities(self, mock_request):
        """Test get activities"""
        mock_request.return_value = [{'type': 'FILL', 'symbol': 'AAPL'}]
        result = self.service.get_activities('acc_123', activity_type='FILL')
        self.assertEqual(len(result), 1)
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_create_bank_link(self, mock_request):
        """Test create bank link"""
        mock_request.return_value = {'id': 'bank_123', 'status': 'VERIFIED'}
        result = self.service.create_bank_link('acc_123', {'routing_number': '123456'})
        self.assertEqual(result['id'], 'bank_123')
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_create_transfer(self, mock_request):
        """Test create transfer"""
        mock_request.return_value = {'id': 'transfer_123', 'status': 'PENDING'}
        result = self.service.create_transfer('acc_123', {'amount': 1000, 'direction': 'INCOMING'})
        self.assertEqual(result['id'], 'transfer_123')
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_transfers(self, mock_request):
        """Test get transfers"""
        mock_request.return_value = [{'id': 'transfer_1'}, {'id': 'transfer_2'}]
        result = self.service.get_transfers('acc_123')
        self.assertEqual(len(result), 2)
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_statements(self, mock_request):
        """Test get statements"""
        mock_request.return_value = [{'id': 'stmt_1', 'year': 2024}]
        result = self.service.get_statements('acc_123', year=2024)
        self.assertEqual(len(result), 1)
    
    @patch.object(AlpacaBrokerService, '_make_request')
    def test_get_tax_documents(self, mock_request):
        """Test get tax documents"""
        mock_request.return_value = [{'id': 'tax_1', 'year': 2024}]
        result = self.service.get_tax_documents('acc_123', year=2024)
        self.assertEqual(len(result), 1)


class BrokerGuardrailsTestCase(TestCase):
    """Tests for Broker Guardrails"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create broker tables if they don't exist (for --nomigrations mode)
        from django.db import connection
        with connection.cursor() as cursor:
            # Check if broker_accounts table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='broker_accounts'
            """)
            if not cursor.fetchone():
                # Create broker_accounts table
                cursor.execute("""
                    CREATE TABLE broker_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE,
                        alpaca_account_id VARCHAR(100) NULL UNIQUE,
                        kyc_status VARCHAR(20) NOT NULL DEFAULT 'NOT_STARTED',
                        approval_reason TEXT NULL,
                        suitability_flags TEXT NOT NULL DEFAULT '{}',
                        account_number VARCHAR(50) NULL,
                        status VARCHAR(50) NULL,
                        buying_power DECIMAL(15,2) NOT NULL DEFAULT 0,
                        cash DECIMAL(15,2) NOT NULL DEFAULT 0,
                        equity DECIMAL(15,2) NOT NULL DEFAULT 0,
                        day_trading_buying_power DECIMAL(15,2) NOT NULL DEFAULT 0,
                        pattern_day_trader BOOLEAN NOT NULL DEFAULT 0,
                        day_trade_count INTEGER NOT NULL DEFAULT 0,
                        trading_blocked BOOLEAN NOT NULL DEFAULT 0,
                        transfer_blocked BOOLEAN NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        approved_at DATETIME NULL,
                        FOREIGN KEY (user_id) REFERENCES core_user (id)
                    )
                """)
                cursor.execute("CREATE INDEX broker_accounts_user_kyc ON broker_accounts(user_id, kyc_status)")
                
                # Create broker_orders table
                cursor.execute("""
                    CREATE TABLE broker_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        broker_account_id INTEGER NOT NULL,
                        alpaca_order_id VARCHAR(100) NULL UNIQUE,
                        client_order_id VARCHAR(100) NULL UNIQUE,
                        symbol VARCHAR(10) NOT NULL,
                        side VARCHAR(10) NOT NULL,
                        order_type VARCHAR(20) NOT NULL,
                        time_in_force VARCHAR(10) NOT NULL DEFAULT 'DAY',
                        quantity INTEGER NOT NULL,
                        notional DECIMAL(15,2) NULL,
                        limit_price DECIMAL(10,2) NULL,
                        stop_price DECIMAL(10,2) NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'NEW',
                        filled_qty INTEGER NOT NULL DEFAULT 0,
                        filled_avg_price DECIMAL(10,2) NULL,
                        guardrail_checks_passed BOOLEAN NOT NULL DEFAULT 0,
                        guardrail_reject_reason TEXT NULL,
                        fills TEXT NOT NULL DEFAULT '[]',
                        alpaca_response TEXT NOT NULL DEFAULT '{}',
                        rejection_reason TEXT NULL,
                        submitted_at DATETIME NULL,
                        filled_at DATETIME NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (broker_account_id) REFERENCES broker_accounts (id)
                    )
                """)
                cursor.execute("CREATE INDEX broker_orders_account ON broker_orders(broker_account_id)")
                cursor.execute("CREATE INDEX broker_orders_status ON broker_orders(status)")
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
    
    def test_is_symbol_whitelisted(self):
        """Test symbol whitelist check"""
        # Whitelisted symbols
        self.assertTrue(BrokerGuardrails.is_symbol_whitelisted('AAPL'))
        self.assertTrue(BrokerGuardrails.is_symbol_whitelisted('SPY'))
        self.assertTrue(BrokerGuardrails.is_symbol_whitelisted('aapl'))  # Case insensitive
        
        # Non-whitelisted symbols
        self.assertFalse(BrokerGuardrails.is_symbol_whitelisted('INVALID'))
        self.assertFalse(BrokerGuardrails.is_symbol_whitelisted(''))
    
    def test_market_is_open_now_weekday(self):
        """Test market hours check on weekday"""
        # This test depends on current time, so we'll test the logic
        result = BrokerGuardrails.market_is_open_now()
        self.assertIsInstance(result, bool)
    
    def test_can_place_order_no_broker_account(self):
        """Test order placement check without broker account"""
        allowed, reason = BrokerGuardrails.can_place_order(
            self.user, 'AAPL', 1000.0
        )
        self.assertFalse(allowed)
        self.assertIn('No broker account', reason)
    
    def test_can_place_order_symbol_not_whitelisted(self):
        """Test order placement with non-whitelisted symbol"""
        from core.broker_models import BrokerAccount
        
        # Create broker account
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='acc_123',
            kyc_status='APPROVED',
            trading_blocked=False
        )
        
        allowed, reason = BrokerGuardrails.can_place_order(
            self.user, 'INVALID', 1000.0
        )
        self.assertFalse(allowed)
        self.assertIn('not available for trading', reason)
    
    def test_can_place_order_exceeds_per_order_limit(self):
        """Test order placement exceeding per-order limit"""
        from core.broker_models import BrokerAccount
        
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='acc_123',
            kyc_status='APPROVED',
            trading_blocked=False
        )
        
        allowed, reason = BrokerGuardrails.can_place_order(
            self.user, 'AAPL', 15000.0  # Exceeds $10k limit
        )
        self.assertFalse(allowed)
        self.assertIn('exceeds maximum per-order limit', reason)
    
    def test_can_place_order_exceeds_daily_limit(self):
        """Test order placement exceeding daily limit"""
        from core.broker_models import BrokerAccount
        
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='acc_123',
            kyc_status='APPROVED',
            trading_blocked=False
        )
        
        # Test with amount that would exceed the limit
        allowed, reason = BrokerGuardrails.can_place_order(
            self.user, 'AAPL', 2000.0,  # $49k + $2k = $51k (exceeds $50k limit)
            order_type='LIMIT',  # Use LIMIT to avoid market hours check
            daily_notional_used=49000.0  # Close to $50k limit
        )
        self.assertFalse(allowed)
        self.assertIn('exceed daily limit', reason)
    
    def test_can_place_order_kyc_not_approved(self):
        """Test order placement with non-approved KYC"""
        from core.broker_models import BrokerAccount
        
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='acc_123',
            kyc_status='PENDING',
            trading_blocked=False
        )
        
        allowed, reason = BrokerGuardrails.can_place_order(
            self.user, 'AAPL', 1000.0
        )
        self.assertFalse(allowed)
        self.assertIn('not approved', reason)
    
    def test_can_place_order_trading_blocked(self):
        """Test order placement with trading blocked"""
        from core.broker_models import BrokerAccount
        
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='acc_123',
            kyc_status='APPROVED',
            trading_blocked=True
        )
        
        allowed, reason = BrokerGuardrails.can_place_order(
            self.user, 'AAPL', 1000.0
        )
        self.assertFalse(allowed)
        self.assertIn('Trading is blocked', reason)
    
    def test_can_place_order_success(self):
        """Test successful order placement check"""
        from core.broker_models import BrokerAccount
        
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='acc_123',
            kyc_status='APPROVED',
            trading_blocked=False
        )
        
        allowed, reason = BrokerGuardrails.can_place_order(
            self.user, 'AAPL', 1000.0,
            order_type='LIMIT',  # Limit orders can be placed outside market hours
            daily_notional_used=0.0
        )
        self.assertTrue(allowed)
        self.assertIn('passed all guardrail checks', reason)
    
    def test_get_daily_notional_used(self):
        """Test daily notional calculation"""
        from core.broker_models import BrokerAccount, BrokerOrder
        
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='acc_123',
            kyc_status='APPROVED'
        )
        
        # Create some orders
        BrokerOrder.objects.create(
            broker_account=broker_account,
            client_order_id='order_1',
            alpaca_order_id='alpaca_order_1',
            symbol='AAPL',
            side='BUY',
            order_type='MARKET',
            time_in_force='DAY',
            quantity=10,
            notional=5000.0,
            status='FILLED',
            created_at=datetime.now()
        )
        
        BrokerOrder.objects.create(
            broker_account=broker_account,
            client_order_id='order_2',
            alpaca_order_id='alpaca_order_2',
            symbol='MSFT',
            side='BUY',
            order_type='MARKET',
            time_in_force='DAY',
            quantity=5,
            notional=3000.0,
            status='FILLED',
            created_at=datetime.now()
        )
        
        notional = BrokerGuardrails.get_daily_notional_used(self.user)
        self.assertEqual(notional, 8000.0)
    
    def test_get_daily_notional_used_no_account(self):
        """Test daily notional with no broker account"""
        notional = BrokerGuardrails.get_daily_notional_used(self.user)
        self.assertEqual(notional, 0.0)
    
    def test_get_daily_notional_used_only_filled_orders(self):
        """Test daily notional only counts filled orders"""
        from core.broker_models import BrokerAccount, BrokerOrder
        
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='acc_123',
            kyc_status='APPROVED'
        )
        
        # Filled order
        BrokerOrder.objects.create(
            broker_account=broker_account,
            client_order_id='order_1',
            alpaca_order_id='alpaca_order_1',
            symbol='AAPL',
            side='BUY',
            order_type='MARKET',
            time_in_force='DAY',
            quantity=10,
            notional=5000.0,
            status='FILLED',
            created_at=datetime.now()
        )
        
        # Pending order (should not count)
        BrokerOrder.objects.create(
            broker_account=broker_account,
            client_order_id='order_2',
            alpaca_order_id='alpaca_order_2',
            symbol='MSFT',
            side='BUY',
            order_type='MARKET',
            time_in_force='DAY',
            quantity=5,
            notional=3000.0,
            status='PENDING_NEW',
            created_at=datetime.now()
        )
        
        notional = BrokerGuardrails.get_daily_notional_used(self.user)
        self.assertEqual(notional, 5000.0)  # Only filled order counts

