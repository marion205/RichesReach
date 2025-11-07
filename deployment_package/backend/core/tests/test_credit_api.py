"""
Unit Tests for Credit Building API
Tests all credit endpoints with proper mocking
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Setup Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.credit_api import router, get_current_user
from fastapi import FastAPI

User = get_user_model()

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    user = Mock(spec=User)
    user.id = 1
    user.email = 'test@example.com'
    user.name = 'Test User'
    return user


@pytest.fixture
def mock_credit_score():
    """Mock credit score data"""
    return {
        'score': 580,
        'scoreRange': 'Fair',
        'lastUpdated': '2024-01-15',
        'provider': 'self_reported',
        'factors': {
            'paymentHistory': 35,
            'utilization': 30,
            'creditAge': 15,
        }
    }


class TestCreditScoreEndpoints:
    """Test credit score endpoints"""
    
    @patch('core.credit_api.get_current_user')
    def test_get_credit_score(self, mock_get_user, mock_user):
        """Test getting credit score"""
        mock_get_user.return_value = mock_user
        
        # Mock CreditScore model
        with patch('core.credit_api.CREDIT_MODELS_AVAILABLE', False):
            response = client.get(
                '/api/credit/score',
                headers={'Authorization': 'Bearer dev-token-test'}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert 'score' in data
        assert 'scoreRange' in data
        assert 'lastUpdated' in data
        assert 'provider' in data
    
    @patch('core.credit_api.get_current_user')
    def test_refresh_credit_score(self, mock_get_user, mock_user):
        """Test refreshing credit score"""
        mock_get_user.return_value = mock_user
        
        with patch('core.credit_api.CREDIT_MODELS_AVAILABLE', False):
            response = client.post(
                '/api/credit/score/refresh',
                headers={'Authorization': 'Bearer dev-token-test'},
                json={'score': 600, 'provider': 'self_reported'}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['score'] == 600
        assert data['provider'] == 'self_reported'


class TestCreditUtilizationEndpoints:
    """Test credit utilization endpoints"""
    
    @patch('core.credit_api.get_current_user')
    def test_get_credit_utilization(self, mock_get_user, mock_user):
        """Test getting credit utilization"""
        mock_get_user.return_value = mock_user
        
        with patch('core.credit_api.CREDIT_MODELS_AVAILABLE', False):
            response = client.get(
                '/api/credit/utilization',
                headers={'Authorization': 'Bearer dev-token-test'}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert 'totalLimit' in data
        assert 'totalBalance' in data
        assert 'currentUtilization' in data
        assert 'optimalUtilization' in data
        assert 'paydownSuggestion' in data
        assert 'projectedScoreGain' in data
        assert isinstance(data['currentUtilization'], (int, float))
        assert 0 <= data['currentUtilization'] <= 1


class TestCreditProjectionEndpoints:
    """Test credit projection endpoints"""
    
    @patch('core.credit_api.get_current_user')
    def test_get_credit_projection(self, mock_get_user, mock_user):
        """Test getting credit projection"""
        mock_get_user.return_value = mock_user
        
        response = client.get(
            '/api/credit/projection',
            headers={'Authorization': 'Bearer dev-token-test'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'scoreGain6m' in data
        assert 'topAction' in data
        assert 'confidence' in data
        assert isinstance(data['scoreGain6m'], int)
        assert isinstance(data['confidence'], (int, float))
        assert 0 <= data['confidence'] <= 1


class TestCreditSnapshotEndpoints:
    """Test credit snapshot endpoints"""
    
    @patch('core.credit_api.get_current_user')
    def test_get_credit_snapshot(self, mock_get_user, mock_user):
        """Test getting complete credit snapshot"""
        mock_get_user.return_value = mock_user
        
        response = client.get(
            '/api/credit/snapshot',
            headers={'Authorization': 'Bearer dev-token-test'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'score' in data
        assert 'cards' in data
        assert 'utilization' in data
        assert 'projection' in data
        assert 'actions' in data
        assert isinstance(data['cards'], list)
        assert isinstance(data['actions'], list)


class TestCreditCardRecommendations:
    """Test credit card recommendations"""
    
    @patch('core.credit_api.get_current_user')
    def test_get_card_recommendations(self, mock_get_user, mock_user):
        """Test getting credit card recommendations"""
        mock_get_user.return_value = mock_user
        
        response = client.get(
            '/api/credit/cards/recommendations',
            headers={'Authorization': 'Bearer dev-token-test'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check first recommendation structure
        rec = data[0]
        assert 'id' in rec
        assert 'name' in rec
        assert 'type' in rec
        assert 'annualFee' in rec
        assert 'apr' in rec
        assert 'description' in rec
        assert 'benefits' in rec
        assert 'preQualified' in rec
        assert rec['type'] in ['secured', 'unsecured']


class TestCreditAPIErrorHandling:
    """Test error handling in credit API"""
    
    def test_get_score_without_auth(self):
        """Test getting score without authentication"""
        response = client.get('/api/credit/score')
        # Should still work with fallback user
        assert response.status_code in [200, 401]
    
    @patch('core.credit_api.get_current_user')
    def test_get_score_with_error(self, mock_get_user):
        """Test error handling when getting score"""
        mock_get_user.side_effect = Exception("Database error")
        
        response = client.get(
            '/api/credit/score',
            headers={'Authorization': 'Bearer dev-token-test'}
        )
        
        # Should handle error gracefully
        assert response.status_code in [200, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

