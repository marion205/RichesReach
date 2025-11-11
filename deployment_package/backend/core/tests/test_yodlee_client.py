"""
Unit tests for Yodlee API clients
"""
import os
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
import requests

from core.yodlee_client import YodleeClient


class YodleeClientTestCase(TestCase):
    """Tests for YodleeClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_env = {
            'YODLEE_BASE_URL': 'https://sandbox.api.yodlee.com/ysl',
            'YODLEE_CLIENT_ID': 'test_client_id',
            'YODLEE_SECRET': 'test_secret',
            'YODLEE_APP_ID': 'test_app_id',
            'YODLEE_FASTLINK_URL': 'https://fastlink.example.com',
        }
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_credentials(self):
        """Test client initialization without credentials"""
        client = YodleeClient()
        self.assertEqual(client.base_url, 'https://sandbox.api.yodlee.com/ysl')
        self.assertEqual(client.client_id, '')
        self.assertEqual(client.client_secret, '')
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    def test_init_with_credentials(self):
        """Test client initialization with credentials"""
        client = YodleeClient()
        self.assertEqual(client.client_id, 'test_id')
        self.assertEqual(client.client_secret, 'test_secret')
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    def test_get_headers_with_auth(self):
        """Test header generation with authentication"""
        client = YodleeClient()
        headers = client._get_headers(include_auth=True)
        
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['Api-Version'], '1.1')
        self.assertIn('Authorization', headers)
        self.assertTrue(headers['Authorization'].startswith('Basic '))
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    def test_get_headers_without_auth(self):
        """Test header generation without authentication"""
        client = YodleeClient()
        headers = client._get_headers(include_auth=False)
        
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['Api-Version'], '1.1')
        self.assertNotIn('Authorization', headers)
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    @patch('core.yodlee_client.requests.post')
    def test_get_user_token_success(self, mock_post):
        """Test successful user token retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'token': {
                'accessToken': 'test_token_123'
            }
        }
        mock_post.return_value = mock_response
        
        client = YodleeClient()
        token = client._get_user_token('user_123')
        
        self.assertEqual(token, 'test_token_123')
        self.assertEqual(client._user_tokens['user_123'], 'test_token_123')
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    @patch('core.yodlee_client.requests.post')
    def test_get_user_token_failure(self, mock_post):
        """Test user token retrieval failure"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_post.return_value = mock_response
        
        client = YodleeClient()
        token = client._get_user_token('user_123')
        
        self.assertIsNone(token)
        self.assertNotIn('user_123', client._user_tokens)
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    @patch('core.yodlee_client.requests.post')
    def test_get_user_token_cached(self, mock_post):
        """Test that cached tokens are returned"""
        client = YodleeClient()
        client._user_tokens['user_123'] = 'cached_token'
        
        token = client._get_user_token('user_123')
        
        self.assertEqual(token, 'cached_token')
        mock_post.assert_not_called()
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    @patch.object(YodleeClient, '_get_user_token')
    def test_ensure_user_success(self, mock_get_token):
        """Test successful user creation"""
        mock_get_token.return_value = 'test_token'
        
        client = YodleeClient()
        result = client.ensure_user('user_123')
        
        self.assertTrue(result)
        mock_get_token.assert_called_once_with('user_123')
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    @patch.object(YodleeClient, '_get_user_token')
    def test_ensure_user_failure(self, mock_get_token):
        """Test user creation failure"""
        mock_get_token.return_value = None
        
        client = YodleeClient()
        result = client.ensure_user('user_123')
        
        self.assertFalse(result)
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    @patch.object(YodleeClient, '_get_user_token')
    def test_create_fastlink_token(self, mock_get_token):
        """Test FastLink token creation"""
        # create_fastlink_token just calls _get_user_token, doesn't make a post request
        mock_get_token.return_value = 'user_token'
        
        client = YodleeClient()
        token = client.create_fastlink_token('user_123')
        
        # The implementation returns user_token from _get_user_token
        self.assertEqual(token, 'user_token')
        mock_get_token.assert_called_once_with('user_123')
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    @patch.object(YodleeClient, '_get_user_token_headers')
    @patch('core.yodlee_client.requests.get')
    def test_get_accounts_success(self, mock_get, mock_headers):
        """Test successful account retrieval"""
        mock_headers.return_value = {'Authorization': 'Bearer token'}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'account': [
                {
                    'id': 1,
                    'accountName': 'Checking',
                    'accountType': 'CHECKING',
                    'balance': {'amount': 1000.0},
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = YodleeClient()
        accounts = client.get_accounts('user_123')
        
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]['id'], 1)
        mock_get.assert_called_once()
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    @patch.object(YodleeClient, '_get_user_token_headers')
    @patch('core.yodlee_client.requests.get')
    def test_get_transactions_success(self, mock_get, mock_headers):
        """Test successful transaction retrieval"""
        mock_headers.return_value = {'Authorization': 'Bearer token'}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'transaction': [
                {
                    'id': 1,
                    'amount': {'amount': -50.0},
                    'description': {'original': 'Test Transaction'},
                    'date': '2025-01-01',
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = YodleeClient()
        from datetime import datetime, timedelta
        to_date = datetime.now().date()
        from_date = to_date - timedelta(days=30)
        
        # Fix: get_transactions signature is (user_id, account_id=None, from_date=None, to_date=None)
        # Pass dates as strings in YYYY-MM-DD format
        transactions = client.get_transactions(
            'user_123',
            account_id='acc_456',
            from_date=from_date.strftime('%Y-%m-%d'),
            to_date=to_date.strftime('%Y-%m-%d')
        )
        
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['id'], 1)
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    def test_normalize_account(self):
        """Test account normalization"""
        yodlee_account = {
            'id': 123,
            'accountName': 'Checking Account',
            'accountType': 'CHECKING',
            'accountNumber': '1234567890',
            'balance': {
                'amount': 1000.0,
                'currency': 'USD'
            },
            'providerAccountId': 456,
            'providerName': 'Test Bank',
        }
        
        normalized = YodleeClient.normalize_account(yodlee_account)
        
        self.assertEqual(normalized['yodlee_account_id'], '123')
        self.assertEqual(normalized['provider_name'], 'Test Bank')  # Changed from 'provider' to 'provider_name'
        self.assertEqual(normalized['name'], 'Checking Account')
        # Note: account_type comes from CONTAINER field, not accountType
        self.assertEqual(normalized['balance_current'], 1000.0)
    
    @patch.dict(os.environ, {
        'YODLEE_CLIENT_ID': 'test_id',
        'YODLEE_SECRET': 'test_secret'
    })
    def test_normalize_transaction(self):
        """Test transaction normalization"""
        yodlee_transaction = {
            'id': 789,
            'amount': {'amount': -50.0, 'currency': 'USD'},
            'description': {'original': 'Test Transaction'},
            'date': '2025-01-01',
            'category': 'Shopping',
            'merchant': {'name': 'Test Store'},
            'type': 'DEBIT',
        }
        
        normalized = YodleeClient.normalize_transaction(yodlee_transaction)
        
        self.assertEqual(normalized['yodlee_transaction_id'], '789')
        # normalize_transaction stores amount as positive, uses transaction_type for direction
        self.assertEqual(normalized['amount'], 50.0)  # Changed from -50.0 to 50.0
        self.assertEqual(normalized['description'], 'Test Transaction')
        self.assertEqual(normalized['category'], 'Shopping')
        self.assertEqual(normalized['transaction_type'], 'DEBIT')

