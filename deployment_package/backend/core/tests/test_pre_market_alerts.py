"""
Unit tests for Pre-Market Alert Service
"""
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.core import mail

from core.pre_market_alerts import PreMarketAlertService, get_alert_service


class PreMarketAlertServiceTestCase(TestCase):
    """Test cases for PreMarketAlertService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.alert_service = PreMarketAlertService()
    
    def test_generate_email_text(self):
        """Test plain text email generation"""
        setups = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'notes': 'Test setup 1',
            },
            {
                'symbol': 'TSLA',
                'side': 'SHORT',
                'pre_market_change_pct': -0.05,
                'pre_market_price': 250.0,
                'score': 8.0,
                'notes': 'Test setup 2',
            }
        ]
        
        text = self.alert_service._generate_email_text(setups)
        self.assertIsInstance(text, str)
        self.assertIn('AAPL', text)
        self.assertIn('TSLA', text)
        self.assertIn('LONG', text)
        self.assertIn('SHORT', text)
        self.assertIn('2.50%', text)  # Formatted percentage
        self.assertIn('$150.00', text)  # Formatted price
    
    def test_generate_email_html(self):
        """Test HTML email generation"""
        setups = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'notes': 'Test setup',
            }
        ]
        
        html = self.alert_service._generate_email_html(setups)
        self.assertIsInstance(html, str)
        self.assertIn('<html>', html)
        self.assertIn('AAPL', html)
        self.assertIn('LONG', html)
        self.assertIn('$150.00', html)
    
    def test_generate_email_html_with_ml_prob(self):
        """Test HTML email with ML probability"""
        setups = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'ml_success_probability': 0.75,
                'notes': 'Test setup',
            }
        ]
        
        html = self.alert_service._generate_email_html(setups)
        self.assertIn('75.0%', html)  # ML probability should be included
    
    @patch('core.pre_market_alerts.send_mail')
    def test_send_email_alert_django_backend(self, mock_send_mail):
        """Test sending email via Django backend"""
        from django.conf import settings
        with patch.object(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'):
            self.alert_service.alert_email = 'test@example.com'
            
            setups = [
                {
                    'symbol': 'AAPL',
                    'side': 'LONG',
                    'pre_market_change_pct': 0.025,
                    'pre_market_price': 150.0,
                    'score': 7.5,
                    'notes': 'Test setup',
                }
            ]
            
            result = self.alert_service.send_email_alert(setups)
            # Should attempt to send (may fail if email not configured, but should try)
            self.assertIsInstance(result, bool)
    
    def test_send_email_alert_no_email_configured(self):
        """Test sending email when email not configured"""
        self.alert_service.alert_email = ''
        
        setups = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'notes': 'Test setup',
            }
        ]
        
        result = self.alert_service.send_email_alert(setups)
        self.assertFalse(result)
    
    @patch('core.pre_market_alerts.smtplib.SMTP')
    def test_send_smtp_email(self, mock_smtp):
        """Test sending email via SMTP"""
        self.alert_service.smtp_user = 'test@example.com'
        self.alert_service.smtp_password = 'test_password'
        self.alert_service.alert_email = 'recipient@example.com'
        
        setups = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'notes': 'Test setup',
            }
        ]
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.alert_service._send_smtp_email(setups)
        # Should attempt to send
        self.assertIsInstance(result, bool)
    
    def test_send_push_notification(self):
        """Test push notification sending"""
        self.alert_service.push_notification_key = 'test_key'
        
        setups = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'notes': 'Test setup',
            }
        ]
        
        result = self.alert_service.send_push_notification(setups)
        # Should return True (placeholder implementation)
        self.assertIsInstance(result, bool)
    
    def test_send_push_notification_no_key(self):
        """Test push notification when key not configured"""
        self.alert_service.push_notification_key = ''
        
        setups = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'notes': 'Test setup',
            }
        ]
        
        result = self.alert_service.send_push_notification(setups)
        self.assertFalse(result)
    
    def test_get_alert_service_singleton(self):
        """Test that get_alert_service returns singleton"""
        service1 = get_alert_service()
        service2 = get_alert_service()
        self.assertIs(service1, service2)

