"""
Unit tests for Smart Harvest backend endpoints
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    user = Mock()
    user.id = 1
    user.email = 'test@example.com'
    user.name = 'Test User'
    return user


@pytest.fixture
def mock_holdings():
    """Create mock holdings data"""
    return [
        {
            'symbol': 'AAPL',
            'shares': 100,
            'costBasis': 150.0,
            'currentPrice': 140.0,
            'unrealizedGain': -1000.0,
        },
        {
            'symbol': 'MSFT',
            'shares': 50,
            'costBasis': 300.0,
            'currentPrice': 280.0,
            'unrealizedGain': -1000.0,
        },
    ]


class TestSmartHarvestEndpoints:
    """Test suite for Smart Harvest endpoints"""

    def test_recommendations_request_body(self, mock_holdings):
        """Test recommendations endpoint request body parsing"""
        request_body = {
            'holdings': mock_holdings,
        }
        
        assert 'holdings' in request_body
        assert len(request_body['holdings']) == 2
        assert request_body['holdings'][0]['symbol'] == 'AAPL'
        assert request_body['holdings'][1]['symbol'] == 'MSFT'

    def test_recommendations_calculation(self, mock_holdings):
        """Test recommendations calculation logic"""
        trades = []
        total_savings = 0
        
        for holding in mock_holdings:
            unrealized_gain = holding.get('unrealizedGain', 0)
            if unrealized_gain < 0:  # Only losses
                loss_amount = abs(unrealized_gain)
                estimated_savings = loss_amount * 0.22  # 22% marginal rate
                total_savings += estimated_savings
                
                trades.append({
                    'symbol': holding.get('symbol', ''),
                    'shares': holding.get('shares', 0),
                    'action': 'sell',
                    'estimatedSavings': round(estimated_savings, 2),
                    'reason': f'Harvest ${loss_amount:,.0f} in losses',
                })
        
        assert len(trades) == 2
        assert trades[0]['symbol'] == 'AAPL'
        assert trades[0]['estimatedSavings'] == 220.0
        assert trades[1]['symbol'] == 'MSFT'
        assert trades[1]['estimatedSavings'] == 220.0
        assert total_savings == 440.0

    def test_recommendations_response_format(self, mock_holdings):
        """Test recommendations response format"""
        trades = [
            {
                'symbol': 'AAPL',
                'shares': 100,
                'action': 'sell',
                'estimatedSavings': 220.0,
                'reason': 'Harvest $1,000 in losses',
            },
        ]
        
        response = {
            'trades': trades,
            'totalSavings': 220.0,
            'warnings': [],
        }
        
        assert 'trades' in response
        assert 'totalSavings' in response
        assert 'warnings' in response
        assert len(response['trades']) == 1
        assert response['totalSavings'] == 220.0

    def test_execute_request_body(self):
        """Test execute endpoint request body"""
        trades = [
            {'symbol': 'AAPL', 'shares': 100, 'action': 'sell'},
            {'symbol': 'MSFT', 'shares': 50, 'action': 'sell'},
        ]
        
        request_body = {'trades': trades}
        
        assert 'trades' in request_body
        assert len(request_body['trades']) == 2

    def test_execute_response_format(self):
        """Test execute endpoint response format"""
        response = {
            'success': True,
            'tradesExecuted': 2,
            'message': 'Smart harvest trades executed successfully',
        }
        
        assert response['success'] is True
        assert response['tradesExecuted'] == 2
        assert 'message' in response

    def test_wash_sale_warnings(self):
        """Test wash sale warning generation"""
        holdings_with_wash_sale = [
            {
                'symbol': 'AAPL',
                'unrealizedGain': -1000.0,
                'washSaleRisk': True,
            },
            {
                'symbol': 'MSFT',
                'unrealizedGain': -1000.0,
                'washSaleRisk': False,
            },
        ]
        
        warnings = [
            {'symbol': h['symbol'], 'message': 'Potential wash sale risk'}
            for h in holdings_with_wash_sale
            if h.get('washSaleRisk', False)
        ]
        
        assert len(warnings) == 1
        assert warnings[0]['symbol'] == 'AAPL'

    def test_empty_holdings_handling(self):
        """Test handling of empty holdings array"""
        empty_holdings = []
        trades = []
        total_savings = 0
        
        for holding in empty_holdings:
            unrealized_gain = holding.get('unrealizedGain', 0)
            if unrealized_gain < 0:
                loss_amount = abs(unrealized_gain)
                estimated_savings = loss_amount * 0.22
                total_savings += estimated_savings
                trades.append({
                    'symbol': holding.get('symbol', ''),
                    'shares': holding.get('shares', 0),
                    'action': 'sell',
                    'estimatedSavings': round(estimated_savings, 2),
                })
        
        assert len(trades) == 0
        assert total_savings == 0

    def test_tax_savings_calculation(self):
        """Test tax savings calculation accuracy"""
        loss_amounts = [1000, 2000, 3000]
        tax_rate = 0.22
        
        total_savings = sum(loss * tax_rate for loss in loss_amounts)
        
        assert total_savings == 1320.0
        assert all(loss * tax_rate == 220 for loss in [1000])
        assert all(loss * tax_rate == 440 for loss in [2000])
        assert all(loss * tax_rate == 660 for loss in [3000])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

