"""
Unit Tests for Pump.fun Integration
=================================

Tests for the Pump.fun integration including meme coin launches,
bonding curve data, and trade execution.
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
import json
from decimal import Decimal

from core.pump_fun_service import PumpFunService
from core.pump_fun_views import launch_meme_coin, get_bonding_curve, execute_trade

class PumpFunServiceTest(TestCase):
    """Test cases for PumpFunService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = PumpFunService()
        
    def test_launch_meme_coin(self):
        """Test meme coin launch"""
        result = self.service.launch_meme_coin(
            name='TestFrog',
            symbol='TFROG',
            description='Test meme coin',
            template_id='wealth-frog',
            cultural_theme='BIPOC Wealth Building'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('contract_address', result)
        self.assertIn('transaction_hash', result)
        
    def test_get_bonding_curve(self):
        """Test bonding curve retrieval"""
        contract_address = '0x1234567890abcdef'
        
        result = self.service.get_bonding_curve(contract_address)
        
        self.assertTrue(result['success'])
        self.assertIn('current_price', result)
        self.assertIn('total_supply', result)
        self.assertIn('market_cap', result)
        
    def test_execute_trade(self):
        """Test trade execution"""
        result = self.service.execute_trade(
            contract_address='0x1234567890abcdef',
            amount=100.0,
            trade_type='buy'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('transaction_hash', result)
        self.assertIn('amount_received', result)
        
    def test_execute_sell_trade(self):
        """Test sell trade execution"""
        result = self.service.execute_trade(
            contract_address='0x1234567890abcdef',
            amount=50.0,
            trade_type='sell'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('transaction_hash', result)
        self.assertIn('amount_received', result)

class PumpFunViewsTest(TestCase):
    """Test cases for Pump.fun API views"""
    
    def test_launch_meme_coin_view(self):
        """Test launch meme coin API view"""
        data = {
            'name': 'TestFrog',
            'symbol': 'TFROG',
            'description': 'Test meme coin',
            'template': 'wealth-frog',
            'cultural_theme': 'BIPOC Wealth Building'
        }
        
        with patch('core.pump_fun_service.PumpFunService.launch_meme_coin') as mock_launch:
            mock_launch.return_value = {
                'success': True,
                'contract_address': '0x1234567890abcdef',
                'transaction_hash': '0xabcdef1234567890'
            }
            
            response = self.client.post(
                '/api/pump-fun/launch/',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 201)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            self.assertIn('contract_address', response_data)
            
    def test_get_bonding_curve_view(self):
        """Test get bonding curve API view"""
        contract_address = '0x1234567890abcdef'
        
        with patch('core.pump_fun_service.PumpFunService.get_bonding_curve') as mock_curve:
            mock_curve.return_value = {
                'success': True,
                'current_price': 0.001,
                'total_supply': 1000000,
                'market_cap': 1000
            }
            
            response = self.client.get(f'/api/pump-fun/bonding-curve/{contract_address}/')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            self.assertIn('current_price', response_data)
            
    def test_execute_trade_view(self):
        """Test execute trade API view"""
        data = {
            'contract_address': '0x1234567890abcdef',
            'amount': 100.0,
            'trade_type': 'buy'
        }
        
        with patch('core.pump_fun_service.PumpFunService.execute_trade') as mock_trade:
            mock_trade.return_value = {
                'success': True,
                'transaction_hash': '0xabcdef1234567890',
                'amount_received': 1000
            }
            
            response = self.client.post(
                '/api/pump-fun/trade/',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            self.assertIn('transaction_hash', response_data)
            
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        # Test launch meme coin with missing fields
        incomplete_data = {'name': 'TestFrog'}
        
        response = self.client.post(
            '/api/pump-fun/launch/',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
        
        # Test trade execution with missing fields
        incomplete_trade_data = {'contract_address': '0x1234567890abcdef'}
        
        response = self.client.post(
            '/api/pump-fun/trade/',
            data=json.dumps(incomplete_trade_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        
    def test_invalid_json(self):
        """Test handling of invalid JSON"""
        response = self.client.post(
            '/api/pump-fun/launch/',
            data="invalid json",
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid JSON data', response_data['error'])
        
    def test_service_error_handling(self):
        """Test handling of service errors"""
        with patch('core.pump_fun_service.PumpFunService.launch_meme_coin') as mock_launch:
            mock_launch.return_value = {
                'success': False,
                'error': 'Service unavailable'
            }
            
            data = {
                'name': 'TestFrog',
                'symbol': 'TFROG',
                'description': 'Test meme coin',
                'template': 'wealth-frog',
                'cultural_theme': 'BIPOC Wealth Building'
            }
            
            response = self.client.post(
                '/api/pump-fun/launch/',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
            response_data = json.loads(response.content)
            self.assertFalse(response_data['success'])
            self.assertIn('error', response_data)
