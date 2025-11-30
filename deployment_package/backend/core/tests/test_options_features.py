"""
Unit and Integration Tests for Options Trading Features
- Bracket Orders
- Options Paper Trading
- Options Alerts
- Options Scanner
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from core.broker_models import BrokerAccount, BrokerOrder
from core.options_alert_models import OptionsAlert, OptionsAlertNotification
from core.paper_trading_models import PaperTradingAccount

try:
    from core.schema import schema
except ImportError:
    schema = None  # May not be available if graphql_jwt is not installed

User = get_user_model()


class PlaceBracketOptionsOrderTestCase(TestCase):
    """Tests for PlaceBracketOptionsOrder mutation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='test_account_123',
            kyc_status='APPROVED'
        )
    
    def _create_context(self):
        """Create GraphQL context"""
        context = Mock()
        context.user = self.user
        return context
    
    def test_place_bracket_order_paper_trading(self):
        """Test placing bracket order with paper trading enabled"""
        # Create a Stock object for paper trading
        from core.models import Stock
        stock = Stock.objects.create(
            symbol='AAPL',
            company_name='Apple Inc.',
            sector='Technology'
        )
        
        mutation = '''
        mutation {
            placeBracketOptionsOrder(
                symbol: "AAPL"
                strike: 150.0
                expiration: "2024-01-19"
                optionType: "CALL"
                side: "BUY"
                quantity: 1
                takeProfit: 2.50
                stopLoss: 1.50
                usePaperTrading: true
            ) {
                success
                orderId
                parentOrderId
                takeProfitOrderId
                stopLossOrderId
                error
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(mutation, context_value=context)
        
        # Should succeed with paper trading
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        data = result['data']['placeBracketOptionsOrder']
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['orderId'])
        self.assertIsNotNone(data['parentOrderId'])
    
    @patch('core.broker_mutations.alpaca_service')
    def test_place_bracket_order_real_trading(self, mock_alpaca):
        """Test placing bracket order with real trading"""
        # Mock Alpaca responses
        mock_alpaca.create_order.side_effect = [
            {'id': 'parent_order_123'},  # Parent order
            {'id': 'tp_order_456'},      # Take profit order
            {'id': 'sl_order_789'},      # Stop loss order
        ]
        
        mutation = '''
        mutation {
            placeBracketOptionsOrder(
                symbol: "AAPL"
                strike: 150.0
                expiration: "2024-01-19"
                optionType: "CALL"
                side: "BUY"
                quantity: 1
                takeProfit: 2.50
                stopLoss: 1.50
                orderType: "LIMIT"
                limitPrice: 2.00
                usePaperTrading: false
            ) {
                success
                orderId
                parentOrderId
                takeProfitOrderId
                stopLossOrderId
                error
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(mutation, context_value=context)
        
        # Should succeed
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        data = result['data']['placeBracketOptionsOrder']
        self.assertTrue(data['success'])
        self.assertEqual(data['parentOrderId'], 'parent_order_123')
        self.assertEqual(data['takeProfitOrderId'], 'tp_order_456')
        self.assertEqual(data['stopLossOrderId'], 'sl_order_789')
    
    def test_place_bracket_order_unauthenticated(self):
        """Test bracket order requires authentication"""
        mutation = '''
        mutation {
            placeBracketOptionsOrder(
                symbol: "AAPL"
                strike: 150.0
                expiration: "2024-01-19"
                optionType: "CALL"
                side: "BUY"
                quantity: 1
                takeProfit: 2.50
                stopLoss: 1.50
            ) {
                success
                error
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = Mock()
        context.user = Mock()
        context.user.is_authenticated = False
        
        result = client.execute(mutation, context_value=context)
        
        data = result['data']['placeBracketOptionsOrder']
        self.assertFalse(data['success'])
        self.assertIn('Authentication', data['error'])


class OptionsPaperTradingTestCase(TestCase):
    """Tests for options paper trading integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.broker_account = BrokerAccount.objects.create(
            user=self.user,
            alpaca_account_id='test_account_123',
            kyc_status='APPROVED'
        )
    
    def _create_context(self):
        """Create GraphQL context"""
        context = Mock()
        context.user = self.user
        return context
    
    @patch('core.broker_mutations.alpaca_service')
    def test_place_options_order_with_paper_trading(self, mock_alpaca):
        """Test PlaceOptionsOrder with paper trading enabled"""
        mutation = '''
        mutation {
            placeOptionsOrder(
                symbol: "AAPL"
                strike: 150.0
                expiration: "2024-01-19"
                optionType: "CALL"
                side: "BUY"
                quantity: 1
                orderType: "MARKET"
                usePaperTrading: true
            ) {
                success
                orderId
                alpacaOrderId
                status
                error
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(mutation, context_value=context)
        
        # Should succeed with paper trading
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        data = result['data']['placeOptionsOrder']
        self.assertTrue(data['success'])
        # Paper trading orders should have orderId but alpacaOrderId should start with "paper_"
        self.assertIsNotNone(data['orderId'])
        if data.get('alpacaOrderId'):
            self.assertTrue(data['alpacaOrderId'].startswith('paper_'))


class OptionsAlertsTestCase(TestCase):
    """Tests for options alerts queries and mutations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
    
    def _create_context(self):
        """Create GraphQL context"""
        context = Mock()
        context.user = self.user
        return context
    
    def test_create_price_alert(self):
        """Test creating a price alert"""
        mutation = '''
        mutation {
            createOptionsAlert(
                symbol: "AAPL"
                strike: 150.0
                expiration: "2024-01-19"
                optionType: "CALL"
                alertType: "PRICE"
                targetValue: 2.50
                direction: "above"
            ) {
                success
                alert {
                    id
                    symbol
                    alertType
                    targetValue
                    direction
                    status
                }
                error
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(mutation, context_value=context)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        data = result['data']['createOptionsAlert']
        self.assertTrue(data['success'])
        self.assertEqual(data['alert']['symbol'], 'AAPL')
        self.assertEqual(data['alert']['alertType'], 'PRICE')
        self.assertEqual(float(data['alert']['targetValue']), 2.50)
        self.assertEqual(data['alert']['direction'], 'above')
        self.assertEqual(data['alert']['status'], 'ACTIVE')
    
    def test_create_iv_alert(self):
        """Test creating an IV alert"""
        mutation = '''
        mutation {
            createOptionsAlert(
                symbol: "AAPL"
                strike: 150.0
                expiration: "2024-01-19"
                optionType: "CALL"
                alertType: "IV"
                targetValue: 0.30
                direction: "below"
            ) {
                success
                alert {
                    id
                    alertType
                    targetValue
                }
                error
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(mutation, context_value=context)
        
        self.assertNotIn('errors', result)
        data = result['data']['createOptionsAlert']
        self.assertTrue(data['success'])
        self.assertEqual(data['alert']['alertType'], 'IV')
    
    def test_create_expiration_alert(self):
        """Test creating an expiration alert"""
        mutation = '''
        mutation {
            createOptionsAlert(
                symbol: "AAPL"
                strike: 150.0
                expiration: "2024-01-19"
                optionType: "CALL"
                alertType: "EXPIRATION"
            ) {
                success
                alert {
                    id
                    alertType
                    status
                }
                error
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(mutation, context_value=context)
        
        self.assertNotIn('errors', result)
        data = result['data']['createOptionsAlert']
        self.assertTrue(data['success'])
        self.assertEqual(data['alert']['alertType'], 'EXPIRATION')
    
    def test_query_options_alerts(self):
        """Test querying user's options alerts"""
        # Create test alerts
        alert1 = OptionsAlert.objects.create(
            user=self.user,
            symbol='AAPL',
            strike=Decimal('150.00'),
            expiration='2024-01-19',
            option_type='CALL',
            alert_type='PRICE',
            target_value=Decimal('2.50'),
            direction='above',
            status='ACTIVE'
        )
        alert2 = OptionsAlert.objects.create(
            user=self.user,
            symbol='TSLA',
            strike=Decimal('200.00'),
            expiration='2024-01-19',
            option_type='PUT',
            alert_type='IV',
            target_value=Decimal('0.30'),
            direction='below',
            status='ACTIVE'
        )
        
        query = '''
        query {
            optionsAlerts {
                id
                symbol
                alertType
                status
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(query, context_value=context)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        alerts = result['data']['optionsAlerts']
        self.assertEqual(len(alerts), 2)
        self.assertEqual(alerts[0]['symbol'], 'TSLA')  # Ordered by -created_at
    
    def test_query_options_alerts_filtered(self):
        """Test querying alerts with filters"""
        # Create test alerts
        alert1 = OptionsAlert.objects.create(
            user=self.user,
            symbol='AAPL',
            alert_type='PRICE',
            status='ACTIVE'
        )
        alert2 = OptionsAlert.objects.create(
            user=self.user,
            symbol='AAPL',
            alert_type='IV',
            status='TRIGGERED'
        )
        
        query = '''
        query {
            optionsAlerts(status: "ACTIVE", symbol: "AAPL") {
                id
                symbol
                alertType
                status
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(query, context_value=context)
        
        self.assertNotIn('errors', result)
        alerts = result['data']['optionsAlerts']
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['status'], 'ACTIVE')
        self.assertEqual(alerts[0]['symbol'], 'AAPL')
    
    def test_update_options_alert(self):
        """Test updating an options alert"""
        alert = OptionsAlert.objects.create(
            user=self.user,
            symbol='AAPL',
            alert_type='PRICE',
            target_value=Decimal('2.50'),
            direction='above',
            status='ACTIVE'
        )
        
        mutation = '''
        mutation {
            updateOptionsAlert(
                id: "%s"
                targetValue: 3.00
                direction: "below"
            ) {
                success
                alert {
                    id
                    targetValue
                    direction
                }
                error
            }
        }
        ''' % alert.id
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(mutation, context_value=context)
        
        self.assertNotIn('errors', result)
        data = result['data']['updateOptionsAlert']
        self.assertTrue(data['success'])
        self.assertEqual(float(data['alert']['targetValue']), 3.00)
        self.assertEqual(data['alert']['direction'], 'below')
    
    def test_delete_options_alert(self):
        """Test deleting (cancelling) an options alert"""
        alert = OptionsAlert.objects.create(
            user=self.user,
            symbol='AAPL',
            alert_type='PRICE',
            status='ACTIVE'
        )
        
        mutation = '''
        mutation {
            deleteOptionsAlert(id: "%s") {
                success
                error
            }
        }
        ''' % alert.id
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(mutation, context_value=context)
        
        self.assertNotIn('errors', result)
        data = result['data']['deleteOptionsAlert']
        self.assertTrue(data['success'])
        
        # Verify alert is cancelled
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'CANCELLED')
    
    def test_create_alert_unauthenticated(self):
        """Test creating alert requires authentication"""
        mutation = '''
        mutation {
            createOptionsAlert(
                symbol: "AAPL"
                alertType: "PRICE"
                targetValue: 2.50
                direction: "above"
            ) {
                success
                error
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = Mock()
        context.user = Mock()
        context.user.is_anonymous = True
        
        result = client.execute(mutation, context_value=context)
        
        data = result['data']['createOptionsAlert']
        self.assertFalse(data['success'])
        self.assertIn('Authentication', data['error'])


class OptionsScannerTestCase(TestCase):
    """Tests for options scanner query"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
    
    def _create_context(self):
        """Create GraphQL context"""
        context = Mock()
        context.user = self.user
        return context
    
    @patch('core.real_options_service.RealOptionsService')
    def test_scan_options_high_iv(self, mock_service_class):
        """Test scanning options with high IV filter"""
        # Mock options service response
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_real_options_chain.return_value = {
            'options_chain': {
                'calls': [
                    {
                        'symbol': 'AAPL',
                        'contract_symbol': 'AAPL240119C00150000',
                        'strike': 150.0,
                        'expiration_date': '2024-01-19',
                        'bid': 2.40,
                        'ask': 2.50,
                        'volume': 5000,
                        'implied_volatility': 0.35,  # High IV
                        'delta': 0.5,
                        'theta': -0.05,
                    },
                    {
                        'symbol': 'AAPL',
                        'contract_symbol': 'AAPL240119C00155000',
                        'strike': 155.0,
                        'expiration_date': '2024-01-19',
                        'bid': 1.80,
                        'ask': 1.90,
                        'volume': 3000,
                        'implied_volatility': 0.25,  # Lower IV (should be filtered out)
                        'delta': 0.4,
                        'theta': -0.04,
                    },
                ],
                'puts': [],
            }
        }
        
        query = '''
        query {
            scanOptions(filters: "{\\"minIV\\": 0.3, \\"sortBy\\": \\"iv\\"}") {
                symbol
                strike
                impliedVolatility
                score
                opportunity
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(query, context_value=context)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        options = result['data']['scanOptions']
        # Should only return options with IV >= 0.3
        self.assertGreaterEqual(len(options), 1)
        if len(options) > 0:
            self.assertGreaterEqual(float(options[0]['impliedVolatility']), 0.3)
    
    @patch('core.real_options_service.RealOptionsService')
    def test_scan_options_high_volume(self, mock_service_class):
        """Test scanning options with high volume filter"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_real_options_chain.return_value = {
            'options_chain': {
                'calls': [
                    {
                        'symbol': 'AAPL',
                        'contract_symbol': 'AAPL240119C00150000',
                        'strike': 150.0,
                        'expiration_date': '2024-01-19',
                        'bid': 2.40,
                        'ask': 2.50,
                        'volume': 10000,  # High volume
                        'implied_volatility': 0.25,
                        'delta': 0.5,
                        'theta': -0.05,
                    },
                ],
                'puts': [],
            }
        }
        
        query = '''
        query {
            scanOptions(filters: "{\\"minVolume\\": 5000, \\"sortBy\\": \\"volume\\"}") {
                symbol
                volume
                score
            }
        }
        '''
        
        if schema is None:
            self.skipTest("GraphQL schema not available")
        
        client = Client(schema)
        context = self._create_context()
        
        result = client.execute(query, context_value=context)
        
        self.assertNotIn('errors', result)
        options = result['data']['scanOptions']
        self.assertGreaterEqual(len(options), 1)
        if len(options) > 0:
            self.assertGreaterEqual(int(options[0]['volume']), 5000)


class OptionsAlertsBackgroundJobTestCase(TestCase):
    """Tests for options alerts background job"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use unique email to avoid conflicts with other tests
        import uuid
        unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        self.user = User.objects.create_user(
            email=unique_email,
            password='testpass123',
            name='Test User'
        )
    
    @patch('core.management.commands.check_options_alerts.RealOptionsService')
    def test_check_price_alert_triggered(self, mock_service_class):
        """Test that price alert triggers when condition met"""
        # Mock the service at the command level (where it's imported)
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Create alert
        alert = OptionsAlert.objects.create(
            user=self.user,
            symbol='AAPL',
            strike=Decimal('150.00'),
            expiration='2024-01-19',
            option_type='CALL',
            alert_type='PRICE',
            target_value=Decimal('2.50'),
            direction='above',
            status='ACTIVE'
        )
        
        # Mock options service to return price above target
        # The service returns the full structure with options_chain containing calls/puts
        # Note: The command calculates current_price as (bid + ask) / 2, so we need bid + ask >= 2 * target
        mock_service.get_real_options_chain.return_value = {
            'underlying_symbol': 'AAPL',
            'underlying_price': 150.0,
            'options_chain': {
                'expiration_dates': ['2024-01-19'],
                'calls': [
                    {
                        'symbol': 'AAPL',
                        'strike': float(alert.strike),  # Match the Decimal strike from alert
                        'expiration_date': '2024-01-19',
                        'bid': 2.50,  # (2.50 + 2.60) / 2 = 2.55 >= 2.50 target
                        'ask': 2.60,
                        'last_price': 2.55,
                    },
                ],
                'puts': [],
            },
            'unusual_flow': [],
            'recommended_strategies': [],
            'market_sentiment': {},
        }
        
        from core.management.commands.check_options_alerts import Command
        command = Command()
        command.handle(dry_run=False)
        
        # Verify alert was triggered
        alert.refresh_from_db()
        # The alert should be triggered since (2.50 + 2.60) / 2 = 2.55 >= 2.50
        self.assertEqual(alert.status, 'TRIGGERED', f"Alert status is {alert.status}, expected TRIGGERED. Alert error: {getattr(alert, 'error', 'none')}")
        self.assertIsNotNone(alert.triggered_at)
        
        # Verify notification was created
        notifications = OptionsAlertNotification.objects.filter(alert=alert)
        self.assertEqual(notifications.count(), 1)
    
    @patch('core.real_options_service.RealOptionsService')
    def test_check_expiration_alert_triggered(self, mock_service_class):
        """Test that expiration alert triggers 1 day before expiration"""
        # Mock the service before importing
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        from core.management.commands.check_options_alerts import Command
        
        # Create alert with expiration tomorrow
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        alert = OptionsAlert.objects.create(
            user=self.user,
            symbol='AAPL',
            expiration=tomorrow.strftime('%Y-%m-%d'),
            alert_type='EXPIRATION',
            status='ACTIVE'
        )
        
        command = Command()
        command.handle(dry_run=False)
        
        # Verify alert was triggered
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'TRIGGERED')


if __name__ == '__main__':
    import django
    django.setup()
    import unittest
    unittest.main()

