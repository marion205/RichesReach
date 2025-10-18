"""
Tests for server-authoritative crypto trade execution
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client

from core.schema import schema
from core.crypto_models import Cryptocurrency, CryptoPrice, CryptoTrade
from core.crypto_quotes import get_fresh_crypto_quote, Quote, MAX_AGE

User = get_user_model()

# Test mutation
MUTATION = """
mutation ExecuteCryptoTrade(
    $symbol: String!
    $tradeType: String!
    $quantity: Float!
    $orderType: String!
    $pricePerUnit: Float
    $maxSlippageBps: Int
) {
    executeCryptoTrade(
        symbol: $symbol
        tradeType: $tradeType
        quantity: $quantity
        orderType: $orderType
        pricePerUnit: $pricePerUnit
        maxSlippageBps: $maxSlippageBps
    ) {
        ok
        trade {
            id
            tradeType
            quantity
            pricePerUnit
            totalAmount
            orderId
            status
        }
        error {
            code
            message
        }
    }
}
"""


class TestCryptoQuoteFreshness(TestCase):
    """Test quote freshness validation"""
    
    def test_fresh_quote_is_valid(self):
        """Fresh quotes should be accepted"""
        now = datetime.now(timezone.utc)
        quote = Quote(
            price=Decimal("50000"),
            bid=Decimal("49990"),
            ask=Decimal("50010"),
            ts=now,
            source="test"
        )
        self.assertTrue(quote.ts <= now + MAX_AGE)
    
    def test_stale_quote_is_rejected(self):
        """Stale quotes should be rejected"""
        old_time = datetime.now(timezone.utc) - timedelta(seconds=10)
        quote = Quote(
            price=Decimal("50000"),
            bid=Decimal("49990"),
            ask=Decimal("50010"),
            ts=old_time,
            source="test"
        )
        self.assertTrue(quote.ts < datetime.now(timezone.utc) - MAX_AGE)


class TestCryptoTradeExecution(TestCase):
    """Test crypto trade execution with server-authoritative pricing"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.btc = Cryptocurrency.objects.create(
            symbol='BTC',
            name='Bitcoin',
            is_active=True,
            min_trade_amount=Decimal('10.00')
        )
        
        self.btc_price = CryptoPrice.objects.create(
            cryptocurrency=self.btc,
            price_usd=Decimal('50000.00'),
            price_change_24h=Decimal('2.5'),
            volume_24h=Decimal('1000000000.00')
        )
        
        self.client = Client(schema)
    
    def create_authenticated_context(self):
        """Create authenticated GraphQL context"""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        token = str(refresh.access_token)
        return {
            'user': self.user,
            'META': {
                'HTTP_AUTHORIZATION': f'Bearer {token}'
            }
        }
    
    @patch('core.crypto_quotes.get_fresh_crypto_quote')
    def test_market_order_uses_server_quote(self, mock_get_quote):
        """Market orders should use fresh server quotes"""
        # Mock fresh quote
        now = datetime.now(timezone.utc)
        mock_quote = Quote(
            price=Decimal("50100.00"),
            bid=Decimal("50090.00"),
            ask=Decimal("50110.00"),
            ts=now,
            source="finnhub"
        )
        mock_get_quote.return_value = mock_quote
        
        # Execute market order
        result = self.client.execute(
            MUTATION,
            variables={
                "symbol": "BTC",
                "tradeType": "BUY",
                "quantity": 0.01,
                "orderType": "MARKET"
            },
            context=self.create_authenticated_context()
        )
        
        # Verify success
        self.assertTrue(result['data']['executeCryptoTrade']['ok'])
        trade_data = result['data']['executeCryptoTrade']['trade']
        
        # Verify trade details
        self.assertEqual(trade_data['tradeType'], 'BUY')
        self.assertEqual(float(trade_data['quantity']), 0.01)
        self.assertEqual(float(trade_data['pricePerUnit']), 50100.00)
        self.assertEqual(float(trade_data['totalAmount']), 501.00)
        self.assertEqual(trade_data['status'], 'COMPLETED')
        
        # Verify quote was fetched
        mock_get_quote.assert_called_once_with('BTC')
    
    @patch('core.crypto_quotes.get_fresh_crypto_quote')
    def test_limit_order_uses_client_price(self, mock_get_quote):
        """Limit orders should use client-specified price"""
        # Mock fresh quote (should not be used for limit orders)
        now = datetime.now(timezone.utc)
        mock_quote = Quote(
            price=Decimal("50100.00"),
            bid=Decimal("50090.00"),
            ask=Decimal("50110.00"),
            ts=now,
            source="finnhub"
        )
        mock_get_quote.return_value = mock_quote
        
        # Execute limit order
        result = self.client.execute(
            MUTATION,
            variables={
                "symbol": "BTC",
                "tradeType": "BUY",
                "quantity": 0.01,
                "orderType": "LIMIT",
                "pricePerUnit": 49000.00
            },
            context=self.create_authenticated_context()
        )
        
        # Verify success
        self.assertTrue(result['data']['executeCryptoTrade']['ok'])
        trade_data = result['data']['executeCryptoTrade']['trade']
        
        # Verify trade uses client price, not quote price
        self.assertEqual(float(trade_data['pricePerUnit']), 49000.00)
        self.assertEqual(float(trade_data['totalAmount']), 490.00)
        
        # Quote should still be fetched for validation
        mock_get_quote.assert_called_once_with('BTC')
    
    @patch('core.crypto_quotes.get_fresh_crypto_quote')
    def test_stale_quote_rejection(self, mock_get_quote):
        """Stale quotes should cause trade failure"""
        # Mock stale quote
        old_time = datetime.now(timezone.utc) - timedelta(seconds=10)
        mock_quote = Quote(
            price=Decimal("50000.00"),
            bid=Decimal("49990.00"),
            ask=Decimal("50010.00"),
            ts=old_time,
            source="finnhub"
        )
        mock_get_quote.return_value = mock_quote
        
        # Execute market order
        result = self.client.execute(
            MUTATION,
            variables={
                "symbol": "BTC",
                "tradeType": "BUY",
                "quantity": 0.01,
                "orderType": "MARKET"
            },
            context=self.create_authenticated_context()
        )
        
        # Verify failure
        self.assertFalse(result['data']['executeCryptoTrade']['ok'])
        error = result['data']['executeCryptoTrade']['error']
        self.assertEqual(error['code'], 'QUOTE')
        self.assertIn('fresh', error['message'].lower())
    
    def test_unauthorized_trade_rejection(self):
        """Unauthorized users should be rejected"""
        result = self.client.execute(
            MUTATION,
            variables={
                "symbol": "BTC",
                "tradeType": "BUY",
                "quantity": 0.01,
                "orderType": "MARKET"
            }
            # No authenticated context
        )
        
        # Verify failure
        self.assertFalse(result['data']['executeCryptoTrade']['ok'])
        error = result['data']['executeCryptoTrade']['error']
        self.assertEqual(error['code'], 'AUTH')
        self.assertIn('login', error['message'].lower())
    
    def test_invalid_trade_type_rejection(self):
        """Invalid trade types should be rejected"""
        result = self.client.execute(
            MUTATION,
            variables={
                "symbol": "BTC",
                "tradeType": "INVALID",
                "quantity": 0.01,
                "orderType": "MARKET"
            },
            context=self.create_authenticated_context()
        )
        
        # Verify failure
        self.assertFalse(result['data']['executeCryptoTrade']['ok'])
        error = result['data']['executeCryptoTrade']['error']
        self.assertEqual(error['code'], 'INPUT')
        self.assertIn('trade type', error['message'].lower())
    
    def test_minimum_trade_amount_validation(self):
        """Trades below minimum amount should be rejected"""
        with patch('core.crypto_quotes.get_fresh_crypto_quote') as mock_get_quote:
            # Mock fresh quote
            now = datetime.now(timezone.utc)
            mock_quote = Quote(
                price=Decimal("50000.00"),
                bid=Decimal("49990.00"),
                ask=Decimal("50010.00"),
                ts=now,
                source="finnhub"
            )
            mock_get_quote.return_value = mock_quote
            
            # Execute small trade (below $10 minimum)
            result = self.client.execute(
                MUTATION,
                variables={
                    "symbol": "BTC",
                    "tradeType": "BUY",
                    "quantity": 0.0001,  # $5 trade
                    "orderType": "MARKET"
                },
                context=self.create_authenticated_context()
            )
            
            # Verify failure
            self.assertFalse(result['data']['executeCryptoTrade']['ok'])
            error = result['data']['executeCryptoTrade']['error']
            self.assertEqual(error['code'], 'INPUT')
            self.assertIn('minimum', error['message'].lower())


class TestCryptoQuoteProviderFallback(TestCase):
    """Test quote provider fallback chain"""
    
    @patch('core.market_data_service.MarketDataService.get_crypto_price')
    def test_finnhub_primary_provider(self, mock_get_price):
        """Finnhub should be tried first"""
        mock_get_price.return_value = {
            'price': 50000.00,
            'bid': 49990.00,
            'ask': 50010.00,
            'ts': datetime.now(timezone.utc).isoformat()
        }
        
        quote = get_fresh_crypto_quote('BTC')
        
        self.assertEqual(quote.source, 'finnhub')
        self.assertEqual(quote.price, Decimal('50000.00'))
        mock_get_price.assert_called_once()
    
    @patch('core.market_data_service.MarketDataService.get_crypto_price')
    def test_provider_fallback_chain(self, mock_get_price):
        """Should fallback through providers if primary fails"""
        # First call fails, second succeeds
        mock_get_price.side_effect = [
            Exception("Finnhub failed"),
            {
                'price': 50000.00,
                'bid': 49990.00,
                'ask': 50010.00,
                'ts': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        quote = get_fresh_crypto_quote('BTC')
        
        self.assertEqual(quote.source, 'polygon')
        self.assertEqual(quote.price, Decimal('50000.00'))
        self.assertEqual(mock_get_price.call_count, 2)


if __name__ == '__main__':
    pytest.main([__file__])
