"""
Unit and Integration Tests for ML-Powered Options Features

Tests:
1. Edge Predictor - Real-time mispricing forecasts
2. One-Tap Trades - ML-optimized strategy recommendations
3. IV Surface Forecast - Forward-looking IV predictions
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from decimal import Decimal
from django.test import TestCase
from graphene.test import Client
from django.contrib.auth import get_user_model
import json

from core.schema import schema
from core.rust_stock_service import rust_stock_service
from core.models import Stock

User = get_user_model()


class EdgePredictorTestCase(TestCase):
    """Tests for Edge Predictor feature"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client(schema)
        Stock.objects.create(
            symbol='AAPL',
            company_name='Apple Inc.',
            current_price=Decimal('175.50')
        )

    @patch('core.rust_stock_service.rust_stock_service.predict_edge')
    def test_get_edge_predictions_success(self, mock_predict_edge):
        """Test successful edge predictions query"""
        # Mock Rust service response
        mock_predict_edge.return_value = [
            {
                'strike': 175.0,
                'expiration': '30d',
                'option_type': 'call',
                'current_edge': 5.2,
                'predicted_edge_15min': 6.1,
                'predicted_edge_1hr': 7.5,
                'predicted_edge_1day': 8.3,
                'confidence': 85.0,
                'explanation': 'IV crush expected post-earnings',
                'edge_change_dollars': 12.50,
                'current_premium': 5.25,
                'predicted_premium_15min': 5.57,
                'predicted_premium_1hr': 5.64,
            },
            {
                'strike': 180.0,
                'expiration': '30d',
                'option_type': 'call',
                'current_edge': 3.1,
                'predicted_edge_15min': 4.2,
                'predicted_edge_1hr': 5.8,
                'predicted_edge_1day': 6.5,
                'confidence': 72.0,
                'explanation': 'Price movement expected',
                'edge_change_dollars': 8.30,
                'current_premium': 3.50,
                'predicted_premium_15min': 3.65,
                'predicted_premium_1hr': 3.70,
            }
        ]

        query = """
        query {
            edgePredictions(symbol: "AAPL") {
                strike
                expiration
                optionType
                currentEdge
                predictedEdge15min
                predictedEdge1hr
                predictedEdge1day
                confidence
                explanation
                edgeChangeDollars
                currentPremium
                predictedPremium15min
                predictedPremium1hr
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        self.assertIsNone(result.get('errors'))
        self.assertIn('data', result)
        self.assertIn('edgePredictions', result['data'])
        self.assertEqual(len(result['data']['edgePredictions']), 2)
        
        # Verify first prediction
        pred1 = result['data']['edgePredictions'][0]
        self.assertEqual(pred1['strike'], 175.0)
        self.assertEqual(pred1['expiration'], '30d')
        self.assertEqual(pred1['optionType'], 'call')
        self.assertEqual(pred1['currentEdge'], 5.2)
        self.assertEqual(pred1['predictedEdge1hr'], 7.5)
        self.assertEqual(pred1['confidence'], 85.0)
        self.assertIn('IV crush', pred1['explanation'])

    @patch('core.rust_stock_service.rust_stock_service.predict_edge')
    def test_get_edge_predictions_empty(self, mock_predict_edge):
        """Test edge predictions when Rust service returns empty"""
        mock_predict_edge.return_value = []

        query = """
        query {
            edgePredictions(symbol: "AAPL") {
                strike
                confidence
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        self.assertIsNone(result.get('errors'))
        self.assertEqual(len(result['data']['edgePredictions']), 0)

    @patch('core.rust_stock_service.rust_stock_service.predict_edge')
    def test_get_edge_predictions_error_handling(self, mock_predict_edge):
        """Test edge predictions error handling"""
        mock_predict_edge.side_effect = Exception("Rust service unavailable")

        query = """
        query {
            edgePredictions(symbol: "AAPL") {
                strike
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        # Should return empty list on error
        self.assertIsNone(result.get('errors'))
        self.assertEqual(len(result['data']['edgePredictions']), 0)


class OneTapTradesTestCase(TestCase):
    """Tests for One-Tap Trades feature"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client(schema)
        Stock.objects.create(
            symbol='AAPL',
            company_name='Apple Inc.',
            current_price=Decimal('175.50')
        )

    @patch('core.rust_stock_service.rust_stock_service.get_one_tap_trades')
    def test_get_one_tap_trades_success(self, mock_get_trades):
        """Test successful one-tap trades query"""
        # Mock Rust service response
        mock_get_trades.return_value = [
            {
                'strategy': 'Sell 10x AAPL 175/180 call spreads',
                'entry_price': 1.92,
                'expected_edge': 18.5,
                'confidence': 94.0,
                'take_profit': 960.0,
                'stop_loss': 1000.0,
                'reasoning': 'IV crush expected post-earnings',
                'max_loss': 500.0,
                'max_profit': 1920.0,
                'probability_of_profit': 0.72,
                'symbol': 'AAPL',
                'legs': [
                    {
                        'action': 'sell',
                        'option_type': 'call',
                        'strike': 175.0,
                        'expiration': '30d',
                        'quantity': 10,
                        'premium': 5.25,
                    },
                    {
                        'action': 'buy',
                        'option_type': 'call',
                        'strike': 180.0,
                        'expiration': '30d',
                        'quantity': 10,
                        'premium': 3.33,
                    }
                ],
                'strategy_type': 'credit_spread',
                'days_to_expiration': 30,
                'total_cost': -192.0,
                'total_credit': 192.0,
            }
        ]

        query = """
        query {
            oneTapTrades(symbol: "AAPL", accountSize: 10000, riskTolerance: 0.1) {
                strategy
                entryPrice
                expectedEdge
                confidence
                takeProfit
                stopLoss
                reasoning
                maxLoss
                maxProfit
                probabilityOfProfit
                symbol
                legs {
                    action
                    optionType
                    strike
                    expiration
                    quantity
                    premium
                }
                strategyType
                daysToExpiration
                totalCost
                totalCredit
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        self.assertIsNone(result.get('errors'))
        self.assertIn('data', result)
        self.assertIn('oneTapTrades', result['data'])
        self.assertEqual(len(result['data']['oneTapTrades']), 1)
        
        # Verify trade details
        trade = result['data']['oneTapTrades'][0]
        self.assertEqual(trade['strategy'], 'Sell 10x AAPL 175/180 call spreads')
        self.assertEqual(trade['entryPrice'], 1.92)
        self.assertEqual(trade['expectedEdge'], 18.5)
        self.assertEqual(trade['confidence'], 94.0)
        self.assertEqual(trade['maxProfit'], 1920.0)
        self.assertEqual(trade['maxLoss'], 500.0)
        self.assertEqual(trade['probabilityOfProfit'], 0.72)
        self.assertEqual(len(trade['legs']), 2)
        self.assertEqual(trade['legs'][0]['action'], 'sell')
        self.assertEqual(trade['legs'][0]['strike'], 175.0)

    @patch('core.rust_stock_service.rust_stock_service.get_one_tap_trades')
    def test_get_one_tap_trades_default_params(self, mock_get_trades):
        """Test one-tap trades with default parameters"""
        mock_get_trades.return_value = []

        query = """
        query {
            oneTapTrades(symbol: "AAPL") {
                strategy
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        self.assertIsNone(result.get('errors'))
        # Should call with default account_size=10000, risk_tolerance=0.1
        mock_get_trades.assert_called_once()
        call_args = mock_get_trades.call_args
        # Resolver calls with positional args: (symbol, account_size, risk_tolerance)
        self.assertEqual(call_args[0][0], 'AAPL')
        self.assertEqual(call_args[0][1], 10000.0)  # default account_size
        self.assertEqual(call_args[0][2], 0.1)      # default risk_tolerance

    @patch('core.rust_stock_service.rust_stock_service.get_one_tap_trades')
    def test_get_one_tap_trades_custom_params(self, mock_get_trades):
        """Test one-tap trades with custom parameters"""
        mock_get_trades.return_value = []

        query = """
        query {
            oneTapTrades(symbol: "AAPL", accountSize: 50000, riskTolerance: 0.2) {
                strategy
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        self.assertIsNone(result.get('errors'))
        mock_get_trades.assert_called_once()
        call_args = mock_get_trades.call_args
        # Resolver calls with positional args: (symbol, account_size, risk_tolerance)
        self.assertEqual(call_args[0][0], 'AAPL')
        self.assertEqual(call_args[0][1], 50000.0)  # account_size
        self.assertEqual(call_args[0][2], 0.2)      # risk_tolerance

    @patch('core.rust_stock_service.rust_stock_service.get_one_tap_trades')
    def test_get_one_tap_trades_error_handling(self, mock_get_trades):
        """Test one-tap trades error handling"""
        mock_get_trades.side_effect = Exception("Rust service unavailable")

        query = """
        query {
            oneTapTrades(symbol: "AAPL") {
                strategy
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        # Should return empty list on error
        self.assertIsNone(result.get('errors'))
        self.assertEqual(len(result['data']['oneTapTrades']), 0)


class IVSurfaceForecastTestCase(TestCase):
    """Tests for IV Surface Forecast feature"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client(schema)
        Stock.objects.create(
            symbol='AAPL',
            company_name='Apple Inc.',
            current_price=Decimal('175.50')
        )

    @patch('core.rust_stock_service.rust_stock_service.forecast_iv_surface')
    def test_get_iv_surface_forecast_success(self, mock_forecast):
        """Test successful IV surface forecast query"""
        # Mock Rust service response
        mock_forecast.return_value = {
            'symbol': 'AAPL',
            'current_iv': {
                '30d': 0.25,
                '60d': 0.27,
            },
            'predicted_iv_1hr': {
                '30d': 0.26,
                '60d': 0.28,
            },
            'predicted_iv_24hr': {
                '30d': 0.28,
                '60d': 0.30,
            },
            'confidence': 85.0,
            'regime': 'earnings',
            'iv_change_heatmap': [
                {
                    'strike': 175.0,
                    'expiration': '30d',
                    'current_iv': 0.25,
                    'predicted_iv_1hr': 0.26,
                    'predicted_iv_24hr': 0.28,
                    'iv_change_1hr_pct': 4.0,
                    'iv_change_24hr_pct': 12.0,
                    'confidence': 80.0,
                },
                {
                    'strike': 180.0,
                    'expiration': '30d',
                    'current_iv': 0.24,
                    'predicted_iv_1hr': 0.25,
                    'predicted_iv_24hr': 0.27,
                    'iv_change_1hr_pct': 4.2,
                    'iv_change_24hr_pct': 12.5,
                    'confidence': 78.0,
                }
            ],
            'timestamp': '2025-11-30T12:00:00Z',
        }

        query = """
        query {
            ivSurfaceForecast(symbol: "AAPL") {
                symbol
                currentIv
                predictedIv1hr
                predictedIv24hr
                confidence
                regime
                ivChangeHeatmap {
                    strike
                    expiration
                    currentIv
                    predictedIv1hr
                    predictedIv24hr
                    ivChange1hrPct
                    ivChange24hrPct
                    confidence
                }
                timestamp
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        self.assertIsNone(result.get('errors'))
        self.assertIn('data', result)
        self.assertIn('ivSurfaceForecast', result['data'])
        
        forecast = result['data']['ivSurfaceForecast']
        self.assertEqual(forecast['symbol'], 'AAPL')
        self.assertEqual(forecast['confidence'], 85.0)
        self.assertEqual(forecast['regime'], 'earnings')
        
        # Verify heatmap
        self.assertEqual(len(forecast['ivChangeHeatmap']), 2)
        point1 = forecast['ivChangeHeatmap'][0]
        self.assertEqual(point1['strike'], 175.0)
        self.assertEqual(point1['expiration'], '30d')
        self.assertEqual(point1['currentIv'], 0.25)
        self.assertEqual(point1['predictedIv1hr'], 0.26)
        self.assertEqual(point1['ivChange1hrPct'], 4.0)
        self.assertEqual(point1['ivChange24hrPct'], 12.0)

    @patch('core.rust_stock_service.rust_stock_service.forecast_iv_surface')
    def test_get_iv_surface_forecast_empty(self, mock_forecast):
        """Test IV forecast when Rust service returns empty"""
        mock_forecast.return_value = None

        query = """
        query {
            ivSurfaceForecast(symbol: "AAPL") {
                symbol
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        self.assertIsNone(result.get('errors'))
        self.assertIsNone(result['data']['ivSurfaceForecast'])

    @patch('core.rust_stock_service.rust_stock_service.forecast_iv_surface')
    def test_get_iv_surface_forecast_error_handling(self, mock_forecast):
        """Test IV forecast error handling"""
        mock_forecast.side_effect = Exception("Rust service unavailable")

        query = """
        query {
            ivSurfaceForecast(symbol: "AAPL") {
                symbol
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        # Should return None on error
        self.assertIsNone(result.get('errors'))
        self.assertIsNone(result['data']['ivSurfaceForecast'])

    @patch('core.rust_stock_service.rust_stock_service.forecast_iv_surface')
    def test_iv_forecast_regime_detection(self, mock_forecast):
        """Test IV forecast with different regimes"""
        # Test earnings regime
        mock_forecast.return_value = {
            'symbol': 'AAPL',
            'current_iv': {'30d': 0.25},
            'predicted_iv_1hr': {'30d': 0.26},
            'predicted_iv_24hr': {'30d': 0.28},
            'confidence': 85.0,
            'regime': 'earnings',
            'iv_change_heatmap': [],
            'timestamp': '2025-11-30T12:00:00Z',
        }

        query = """
        query {
            ivSurfaceForecast(symbol: "AAPL") {
                regime
                confidence
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        self.assertIsNone(result.get('errors'))
        forecast = result['data']['ivSurfaceForecast']
        self.assertEqual(forecast['regime'], 'earnings')
        self.assertEqual(forecast['confidence'], 85.0)


class MLFeaturesIntegrationTestCase(TestCase):
    """Integration tests for all ML features working together"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client(schema)
        Stock.objects.create(
            symbol='AAPL',
            company_name='Apple Inc.',
            current_price=Decimal('175.50')
        )

    @patch('core.rust_stock_service.rust_stock_service.predict_edge')
    @patch('core.rust_stock_service.rust_stock_service.get_one_tap_trades')
    @patch('core.rust_stock_service.rust_stock_service.forecast_iv_surface')
    def test_all_ml_features_together(self, mock_iv, mock_trades, mock_edge):
        """Test all three ML features can be queried together"""
        # Mock responses
        mock_edge.return_value = [
            {
                'strike': 175.0,
                'expiration': '30d',
                'option_type': 'call',
                'current_edge': 5.2,
                'predicted_edge_15min': 6.1,
                'predicted_edge_1hr': 7.5,
                'predicted_edge_1day': 8.3,
                'confidence': 85.0,
                'explanation': 'Test explanation',
                'edge_change_dollars': 12.50,
                'current_premium': 5.25,
                'predicted_premium_15min': 5.57,
                'predicted_premium_1hr': 5.64,
            }
        ]
        
        mock_trades.return_value = [
            {
                'strategy': 'Test strategy',
                'entry_price': 1.92,
                'expected_edge': 18.5,
                'confidence': 94.0,
                'take_profit': 960.0,
                'stop_loss': 1000.0,
                'reasoning': 'Test reasoning',
                'max_loss': 500.0,
                'max_profit': 1920.0,
                'probability_of_profit': 0.72,
                'symbol': 'AAPL',
                'legs': [],
                'strategy_type': 'credit_spread',
                'days_to_expiration': 30,
                'total_cost': -192.0,
                'total_credit': 192.0,
            }
        ]
        
        mock_iv.return_value = {
            'symbol': 'AAPL',
            'current_iv': {'30d': 0.25},
            'predicted_iv_1hr': {'30d': 0.26},
            'predicted_iv_24hr': {'30d': 0.28},
            'confidence': 85.0,
            'regime': 'earnings',
            'iv_change_heatmap': [],
            'timestamp': '2025-11-30T12:00:00Z',
        }

        query = """
        query {
            edgePredictions(symbol: "AAPL") {
                strike
                confidence
            }
            oneTapTrades(symbol: "AAPL") {
                strategy
                confidence
            }
            ivSurfaceForecast(symbol: "AAPL") {
                symbol
                confidence
                regime
            }
        }
        """

        result = self.client.execute(query, context={'user': self.user})
        
        self.assertIsNone(result.get('errors'))
        self.assertIn('edgePredictions', result['data'])
        self.assertIn('oneTapTrades', result['data'])
        self.assertIn('ivSurfaceForecast', result['data'])
        
        # Verify all features returned data
        self.assertEqual(len(result['data']['edgePredictions']), 1)
        self.assertEqual(len(result['data']['oneTapTrades']), 1)
        self.assertIsNotNone(result['data']['ivSurfaceForecast'])

    @patch('core.rust_stock_service.rust_stock_service.predict_edge')
    @patch('core.rust_stock_service.rust_stock_service.get_one_tap_trades')
    @patch('core.rust_stock_service.rust_stock_service.forecast_iv_surface')
    def test_ml_features_performance(self, mock_iv, mock_trades, mock_edge):
        """Test that ML features respond quickly"""
        import time
        
        # Mock fast responses
        mock_edge.return_value = []
        mock_trades.return_value = []
        mock_iv.return_value = {
            'symbol': 'AAPL',
            'current_iv': {},
            'predicted_iv_1hr': {},
            'predicted_iv_24hr': {},
            'confidence': 0.0,
            'regime': 'normal',
            'iv_change_heatmap': [],
            'timestamp': '2025-11-30T12:00:00Z',
        }

        query = """
        query {
            edgePredictions(symbol: "AAPL") { strike }
            oneTapTrades(symbol: "AAPL") { strategy }
            ivSurfaceForecast(symbol: "AAPL") { symbol }
        }
        """

        start = time.time()
        result = self.client.execute(query, context={'user': self.user})
        elapsed = time.time() - start
        
        self.assertIsNone(result.get('errors'))
        # Should complete in reasonable time (< 1 second for mocked responses)
        self.assertLess(elapsed, 1.0, "ML features should respond quickly")


if __name__ == '__main__':
    unittest.main()

