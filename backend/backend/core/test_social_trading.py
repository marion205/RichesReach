"""
Unit Tests for Social Trading Service
=====================================

Tests for the social trading functionality including meme launches,
social feeds, voice commands, and raid coordination.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timezone

from core.social_trading_service import SocialTradingService, MemeTemplate, SocialPost, Raid
from core.social_trading_views import (
    launch_meme, get_social_feed, create_social_post, 
    process_voice_command, create_raid, join_raid,
    get_meme_templates, stake_meme_yield, get_meme_analytics,
    get_leaderboard, social_trading_health
)

class SocialTradingServiceTest(TestCase):
    """Test cases for SocialTradingService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = SocialTradingService()
        
    def test_launch_meme(self):
        """Test meme launch functionality"""
        meme_data = {
            'name': 'TestFrog',
            'template': 'wealth-frog',
            'description': 'Test meme coin',
            'cultural_theme': 'BIPOC Wealth Building',
            'ai_generated': False
        }
        
        result = self.service.launch_meme(str(self.user.id), meme_data)
        
        self.assertTrue(result['success'])
        self.assertIn('meme_id', result)
        self.assertIn('contract_address', result)
        
    def test_get_social_feed(self):
        """Test social feed retrieval"""
        result = self.service.get_social_feed()
        
        self.assertTrue(result['success'])
        self.assertIn('posts', result)
        self.assertIsInstance(result['posts'], list)
        
    def test_process_voice_command(self):
        """Test voice command processing"""
        command_data = {
            'command': 'launch meme',
            'user_id': str(self.user.id),
            'parameters': {
                'name': 'VoiceFrog',
                'template': 'frog'
            }
        }
        
        result = self.service.process_voice_command(command_data)
        
        self.assertTrue(result['success'])
        self.assertIn('action', result)
        self.assertIn('parameters', result)
        
    def test_create_raid(self):
        """Test raid creation"""
        raid_data = {
            'user_id': str(self.user.id),
            'meme_id': 'test-meme-123',
            'amount': 100.0
        }
        
        result = self.service.create_raid(raid_data)
        
        self.assertTrue(result['success'])
        self.assertIn('raid_id', result)
        
    def test_join_raid(self):
        """Test joining a raid"""
        join_data = {
            'user_id': str(self.user.id),
            'raid_id': 'test-raid-123',
            'amount': 50.0
        }
        
        result = self.service.join_raid(join_data)
        
        self.assertTrue(result['success'])
        self.assertIn('position', result)

class SocialTradingViewsTest(TestCase):
    """Test cases for social trading API views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_launch_meme_view(self):
        """Test launch meme API view"""
        data = {
            'user_id': str(self.user.id),
            'meme_data': {
                'name': 'TestFrog',
                'template': 'wealth-frog',
                'description': 'Test meme coin',
                'cultural_theme': 'BIPOC Wealth Building',
                'ai_generated': False
            }
        }
        
        with patch('core.social_trading_service.SocialTradingService.launch_meme') as mock_launch:
            mock_launch.return_value = {
                'success': True,
                'meme_id': 'meme-123',
                'contract_address': '0x1234567890abcdef'
            }
            
            response = self.client.post(
                '/api/social/launch-meme',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 201)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            
    def test_get_social_feed_view(self):
        """Test get social feed API view"""
        with patch('core.social_trading_service.SocialTradingService.get_social_feed') as mock_feed:
            mock_feed.return_value = {
                'success': True,
                'posts': [
                    {
                        'id': 'post-1',
                        'user': 'testuser',
                        'content': 'Test post',
                        'likes': 10,
                        'comments': 5
                    }
                ]
            }
            
            response = self.client.get('/api/social/feed')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            self.assertIn('posts', response_data)
            
    def test_process_voice_command_view(self):
        """Test voice command API view"""
        data = {
            'command': 'launch meme',
            'user_id': str(self.user.id),
            'parameters': {
                'name': 'VoiceFrog',
                'template': 'frog'
            }
        }
        
        with patch('core.social_trading_service.SocialTradingService.process_voice_command') as mock_voice:
            mock_voice.return_value = {
                'success': True,
                'action': 'launch_meme',
                'parameters': {'name': 'VoiceFrog'}
            }
            
            response = self.client.post(
                '/api/social/voice-command',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            
    def test_join_raid_view(self):
        """Test join raid API view"""
        data = {
            'user_id': str(self.user.id),
            'raid_id': 'test-raid-123',
            'amount': 50.0
        }
        
        with patch('core.social_trading_service.SocialTradingService.join_raid') as mock_raid:
            mock_raid.return_value = {
                'success': True,
                'raid_id': 'test-raid-123',
                'position': 1
            }
            
            response = self.client.post(
                '/api/social/join-raid',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
            
    def test_error_handling(self):
        """Test error handling in views"""
        # Test missing required fields
        response = self.client.post(
            '/api/social/launch-meme',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
        
        # Test invalid JSON
        response = self.client.post(
            '/api/social/launch-meme',
            data="invalid json",
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        
    def test_health_check(self):
        """Test social trading health check"""
        with patch('core.social_trading_service.SocialTradingService.health_check') as mock_health:
            mock_health.return_value = {
                'status': 'healthy',
                'services': {
                    'pump_fun': 'operational',
                    'voice_ai': 'operational',
                    'social_feed': 'operational'
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.get('/api/social/health')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertEqual(response_data['status'], 'healthy')
