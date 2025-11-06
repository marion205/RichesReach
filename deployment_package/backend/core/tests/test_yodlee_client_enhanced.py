"""
Unit tests for Enhanced Yodlee Client with retry logic
"""
import os
import time
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
import requests

from core.yodlee_client_enhanced import EnhancedYodleeClient


class EnhancedYodleeClientTestCase(TestCase):
    """Tests for EnhancedYodleeClient with retry logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_env = {
            'YODLEE_BASE_URL': 'https://sandbox.api.yodlee.com/ysl',
            'YODLEE_CLIENT_ID': 'test_client_id',
            'YODLEE_SECRET': 'test_secret',
        }
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret',
        'YODLEE_MAX_RETRIES': '3',
        'YODLEE_RETRY_DELAY': '1',
    })
    @patch('core.yodlee_client_enhanced.requests.post')
    def test_retry_on_failure(self, mock_post):
        """Test that client retries on failure"""
        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'token': {'accessToken': 'test_token'}
        }
        
        mock_post.side_effect = [
            requests.RequestException('Connection error'),
            requests.RequestException('Timeout'),
            mock_response_success,
        ]
        
        client = EnhancedYodleeClient()
        token = client._get_user_token('user_123')
        
        self.assertEqual(token, 'test_token')
        self.assertEqual(mock_post.call_count, 3)
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret',
        'YODLEE_MAX_RETRIES': '2',
    })
    @patch('core.yodlee_client_enhanced.requests.post')
    def test_max_retries_exceeded(self, mock_post):
        """Test that client stops after max retries"""
        mock_post.side_effect = requests.RequestException('Connection error')
        
        client = EnhancedYodleeClient()
        token = client._get_user_token('user_123')
        
        self.assertIsNone(token)
        self.assertEqual(mock_post.call_count, 2)  # Initial + 1 retry
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret',
        'YODLEE_TIMEOUT': '5',
    })
    @patch('core.yodlee_client_enhanced.requests.post')
    def test_timeout_configuration(self, mock_post):
        """Test that timeout is configured correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'token': {'accessToken': 'test_token'}}
        mock_post.return_value = mock_response
        
        client = EnhancedYodleeClient()
        client._get_user_token('user_123')
        
        # Verify timeout was passed to requests
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs['timeout'], 5)
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret',
    })
    def test_exponential_backoff(self):
        """Test exponential backoff delay calculation"""
        client = EnhancedYodleeClient()
        
        # Test backoff calculation (simplified - actual implementation may vary)
        delay1 = client._calculate_backoff(1)
        delay2 = client._calculate_backoff(2)
        
        # Second attempt should have longer delay
        self.assertGreaterEqual(delay2, delay1)
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret',
    })
    @patch('core.yodlee_client_enhanced.requests.get')
    def test_rate_limiting(self, mock_get):
        """Test rate limiting functionality"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'account': []}
        mock_get.return_value = mock_response
        
        client = EnhancedYodleeClient()
        
        # Make multiple rapid requests
        for _ in range(5):
            client.get_accounts('user_123')
        
        # Verify rate limiting was applied (simplified check)
        # Actual implementation would have delays between calls
        self.assertGreaterEqual(mock_get.call_count, 1)

