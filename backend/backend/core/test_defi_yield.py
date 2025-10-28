"""
Unit Tests for DeFi Yield Service
=================================

Tests for the DeFi yield farming functionality including pool management,
staking, unstaking, and user stake tracking.
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
import json
from decimal import Decimal

from core.defi_yield_service import DeFiYieldService
from core.defi_yield_views import get_yield_pools, stake_tokens, unstake_tokens, get_user_stakes

class DeFiYieldServiceTest(TestCase):
    """Test cases for DeFiYieldService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = DeFiYieldService()
        
    def test_get_yield_pools(self):
        """Test yield pool retrieval"""
        result = self.service.get_yield_pools('ethereum')
        
        self.assertTrue(result['success'])
        self.assertIn('pools', result)
        self.assertIsInstance(result['pools'], list)
        
        # Check pool structure
        if result['pools']:
            pool = result['pools'][0]
            self.assertIn('id', pool)
            self.assertIn('name', pool)
            self.assertIn('apy', pool)
            self.assertIn('tvl', pool)
            
    def test_stake_tokens(self):
        """Test token staking"""
        result = self.service.stake_tokens(
            pool_id='test-pool-123',
            amount=50.0,
            user_address='0x1234567890abcdef'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('transaction_hash', result)
        self.assertIn('stake_id', result)
        
    def test_unstake_tokens(self):
        """Test token unstaking"""
        result = self.service.unstake_tokens(
            pool_id='test-pool-123',
            amount=25.0,
            user_address='0x1234567890abcdef'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('transaction_hash', result)
        self.assertIn('amount_unstaked', result)
        
    def test_get_user_stakes(self):
        """Test user stake retrieval"""
        result = self.service.get_user_stakes('0x1234567890abcdef')
        
        self.assertTrue(result['success'])
        self.assertIn('stakes', result)
        self.assertIsInstance(result['stakes'], list)
        
        # Check stake structure
        if result['stakes']:
            stake = result['stakes'][0]
            self.assertIn('id', stake)
            self.assertIn('pool_id', stake)
            self.assertIn('amount', stake)
            self.assertIn('apy', stake)

class DeFiYieldViewsTest(TestCase):
    """Test cases for DeFi yield API views"""
    
    def test_get_yield_pools_view(self):
        """Test get yield pools API view"""
        with patch('core.defi_yield_service.DeFiYieldService.get_yield_pools') as mock_pools:
            mock_pools.return_value = {
                'success': True,
                'pools': [
                    {
                        'id': 'pool-1',
                        'name': 'USDC-USDT Pool',
                        'apy': 12.5,
                        'tvl': 1000000
                    }
                ]
            }
            
            response = self.client.get('/api/defi/pools/?chain=ethereum')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            self.assertIn('pools', response_data)
            
    def test_stake_tokens_view(self):
        """Test stake tokens API view"""
        data = {
            'pool_id': 'test-pool-123',
            'amount': 50.0,
            'user_address': '0x1234567890abcdef'
        }
        
        with patch('core.defi_yield_service.DeFiYieldService.stake_tokens') as mock_stake:
            mock_stake.return_value = {
                'success': True,
                'transaction_hash': '0xabcdef1234567890',
                'stake_id': 'stake-123'
            }
            
            response = self.client.post(
                '/api/defi/stake/',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            self.assertIn('transaction_hash', response_data)
            
    def test_unstake_tokens_view(self):
        """Test unstake tokens API view"""
        data = {
            'pool_id': 'test-pool-123',
            'amount': 25.0,
            'user_address': '0x1234567890abcdef'
        }
        
        with patch('core.defi_yield_service.DeFiYieldService.unstake_tokens') as mock_unstake:
            mock_unstake.return_value = {
                'success': True,
                'transaction_hash': '0xabcdef1234567890',
                'amount_unstaked': 25.0
            }
            
            response = self.client.post(
                '/api/defi/unstake/',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            self.assertIn('transaction_hash', response_data)
            
    def test_get_user_stakes_view(self):
        """Test get user stakes API view"""
        user_address = '0x1234567890abcdef'
        
        with patch('core.defi_yield_service.DeFiYieldService.get_user_stakes') as mock_stakes:
            mock_stakes.return_value = {
                'success': True,
                'stakes': [
                    {
                        'id': 'stake-123',
                        'pool_id': 'pool-1',
                        'amount': 50.0,
                        'apy': 12.5
                    }
                ]
            }
            
            response = self.client.get(f'/api/defi/stakes/{user_address}/')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            self.assertIn('stakes', response_data)
            
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        # Test stake tokens with missing fields
        incomplete_data = {'pool_id': 'test-pool-123'}
        
        response = self.client.post(
            '/api/defi/stake/',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
        
        # Test unstake tokens with missing fields
        incomplete_unstake_data = {'pool_id': 'test-pool-123'}
        
        response = self.client.post(
            '/api/defi/unstake/',
            data=json.dumps(incomplete_unstake_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        
    def test_invalid_json(self):
        """Test handling of invalid JSON"""
        response = self.client.post(
            '/api/defi/stake/',
            data="invalid json",
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid JSON data', response_data['error'])
        
    def test_service_error_handling(self):
        """Test handling of service errors"""
        with patch('core.defi_yield_service.DeFiYieldService.stake_tokens') as mock_stake:
            mock_stake.return_value = {
                'success': False,
                'error': 'Insufficient balance'
            }
            
            data = {
                'pool_id': 'test-pool-123',
                'amount': 50.0,
                'user_address': '0x1234567890abcdef'
            }
            
            response = self.client.post(
                '/api/defi/stake/',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
            response_data = json.loads(response.content)
            self.assertFalse(response_data['success'])
            self.assertIn('error', response_data)
            
    def test_different_chains(self):
        """Test yield pools for different chains"""
        chains = ['ethereum', 'polygon', 'arbitrum', 'base']
        
        for chain in chains:
            with patch('core.defi_yield_service.DeFiYieldService.get_yield_pools') as mock_pools:
                mock_pools.return_value = {
                    'success': True,
                    'pools': [
                        {
                            'id': f'{chain}-pool-1',
                            'name': f'{chain.title()} Pool',
                            'apy': 10.0,
                            'tvl': 500000
                        }
                    ]
                }
                
                response = self.client.get(f'/api/defi/pools/?chain={chain}')
                
                self.assertEqual(response.status_code, 200)
                response_data = json.loads(response.content)
                self.assertTrue(response_data['success'])
                self.assertIn('pools', response_data)
