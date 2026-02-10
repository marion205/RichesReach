"""
Unit tests for RAHA GraphQL queries and mutations
"""
import unittest
from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from decimal import Decimal

from core.schema import schema
from core import raha_models

_raha_models_available = hasattr(raha_models, 'NotificationPreferences')
if _raha_models_available:
    from core.raha_models import Strategy, StrategyVersion, UserStrategySettings, RAHASignal, RAHABacktestRun, NotificationPreferences, StrategyBlend
else:
    Strategy = StrategyVersion = UserStrategySettings = RAHASignal = RAHABacktestRun = NotificationPreferences = StrategyBlend = None

User = get_user_model()


@unittest.skipUnless(_raha_models_available, "NotificationPreferences model not available")
class TestRAHAGraphQLQueries(TestCase):
    """Test RAHA GraphQL queries"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
        self.strategy = Strategy.objects.create(
            slug='test-strategy',
            name='Test Strategy',
            category='MOMENTUM',
            description='Test',
            market_type='STOCKS',
            timeframe_supported=['5m'],
            enabled=True
        )
        
        self.strategy_version = StrategyVersion.objects.create(
            strategy=self.strategy,
            version=1,
            is_default=True,
            config_schema={},
            logic_ref='momentum'
        )
        
        self.client = Client(schema)
        # Create a mock request object for GraphQL context
        from unittest.mock import Mock
        self.request = Mock()
        self.request.user = self.user
        self.context = self.request
    
    def test_query_strategies(self):
        """Test querying strategies"""
        query = """
        query {
            strategies {
                id
                name
                slug
                category
            }
        }
        """
        
        result = self.client.execute(query, context_value=self.context)
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertIn('strategies', result['data'])
    
    def test_query_user_strategy_settings(self):
        """Test querying user strategy settings"""
        UserStrategySettings.objects.create(
            user=self.user,
            strategy_version=self.strategy_version,
            enabled=True,
            parameters={}
        )
        
        query = """
        query {
            userStrategySettings {
                id
                enabled
            }
        }
        """
        
        result = self.client.execute(query, context_value=self.context)
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
    
    def test_query_raha_signals(self):
        """Test querying RAHA signals"""
        RAHASignal.objects.create(
            user=self.user,
            strategy_version=self.strategy_version,
            symbol='AAPL',
            timeframe='5m',
            signal_type='ENTRY_LONG',  # Use correct enum value
            price=Decimal('150.00'),
            confidence_score=Decimal('0.75')
        )
        
        query = """
        query {
            rahaSignals(symbol: "AAPL", limit: 10) {
                id
                symbol
                signalType
                price
                confidenceScore
            }
        }
        """
        
        result = self.client.execute(query, context_value=self.context)
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertIn('rahaSignals', result['data'])
    
    def test_query_notification_preferences(self):
        """Test querying notification preferences"""
        NotificationPreferences.objects.create(
            user=self.user,
            push_enabled=True,
            signal_notifications_enabled=True
        )
        
        query = """
        query {
            notificationPreferences {
                id
                pushEnabled
                signalNotificationsEnabled
            }
        }
        """
        
        result = self.client.execute(query, context_value=self.context)
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertIn('notificationPreferences', result['data'])
    
    def test_query_strategy_blends(self):
        """Test querying strategy blends"""
        blend = StrategyBlend.objects.create(
            user=self.user,
            name='Test Blend',
            components=[{
                'strategy_version_id': str(self.strategy_version.id),
                'weight': 1.0
            }]
        )
        
        query = """
        query {
            strategyBlends {
                id
                name
            }
        }
        """
        
        result = self.client.execute(query, context_value=self.context)
        self.assertNotIn('errors', result)
        self.assertIn('data', result)


@unittest.skipUnless(_raha_models_available, "NotificationPreferences model not available")
class TestRAHAGraphQLMutations(TestCase):
    """Test RAHA GraphQL mutations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
        self.strategy = Strategy.objects.create(
            slug='test-strategy',
            name='Test Strategy',
            category='MOMENTUM',
            description='Test',
            market_type='STOCKS',
            timeframe_supported=['5m'],
            enabled=True
        )
        
        self.strategy_version = StrategyVersion.objects.create(
            strategy=self.strategy,
            version=1,
            is_default=True,
            config_schema={},
            logic_ref='momentum'
        )
        
        self.client = Client(schema)
        # Create a mock request object for GraphQL context
        from unittest.mock import Mock
        self.request = Mock()
        self.request.user = self.user
        self.context = self.request
    
    def test_mutation_enable_strategy(self):
        """Test enabling a strategy"""
        mutation = """
        mutation {
            enableStrategy(strategyVersionId: "%s", parameters: "{}") {
                success
                message
                userStrategySettings {
                    id
                    enabled
                }
            }
        }
        """ % str(self.strategy_version.id)
        
        result = self.client.execute(mutation, context_value=self.context)
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertTrue(result['data']['enableStrategy']['success'])
    
    def test_mutation_update_notification_preferences(self):
        """Test updating notification preferences"""
        mutation = """
        mutation {
            updateNotificationPreferences(
                pushEnabled: true
                signalNotificationsEnabled: true
                signalConfidenceThreshold: 0.75
            ) {
                success
                message
                notificationPreferences {
                    id
                    pushEnabled
                    signalNotificationsEnabled
                }
            }
        }
        """
        
        result = self.client.execute(mutation, context_value=self.context)
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertTrue(result['data']['updateNotificationPreferences']['success'])


if __name__ == '__main__':
    unittest.main()

