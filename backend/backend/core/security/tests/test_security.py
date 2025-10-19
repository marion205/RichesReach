"""
Security Test Suite for RichesReach
Tests all security measures and configurations
"""

import json
import time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from unittest.mock import patch, MagicMock
import jwt
from datetime import datetime, timedelta

User = get_user_model()


class GraphQLSecurityTests(TestCase):
    """Test GraphQL security measures"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_introspection_blocked(self):
        """Test that introspection queries are blocked in production"""
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        
        response = self.client.post(
            '/graphql/',
            data=json.dumps({'query': introspection_query}),
            content_type='application/json'
        )
        
        # Should be blocked in production
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('errors', data)
        self.assertIn('Introspection queries are disabled', data['errors'][0]['message'])
    
    def test_rate_limiting(self):
        """Test GraphQL rate limiting"""
        query = 'query { ping }'
        
        # Make multiple requests quickly
        for i in range(65):  # Exceed rate limit
            response = self.client.post(
                '/graphql/',
                data=json.dumps({'query': query}),
                content_type='application/json'
            )
            
            if i >= 60:  # Should be rate limited
                self.assertEqual(response.status_code, 429)
                data = response.json()
                self.assertIn('Rate limit exceeded', data['errors'][0]['message'])
    
    def test_query_depth_limiting(self):
        """Test that deep queries are blocked"""
        # Create a very deep query
        deep_query = "query { " + "stocks { " * 15 + "symbol" + " }" * 15 + " }"
        
        response = self.client.post(
            '/graphql/',
            data=json.dumps({'query': deep_query}),
            content_type='application/json'
        )
        
        # Should be blocked due to depth
        self.assertEqual(response.status_code, 400)
    
    def test_query_complexity_limiting(self):
        """Test that complex queries are blocked"""
        # Create a complex query
        complex_query = """
        query {
            stocks { symbol }
            allStocks { symbol }
            searchTickers(q: "test") { symbol }
            quotes(symbols: ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]) { symbol }
        }
        """
        
        response = self.client.post(
            '/graphql/',
            data=json.dumps({'query': complex_query}),
            content_type='application/json'
        )
        
        # Should be blocked due to complexity
        self.assertEqual(response.status_code, 400)


class JWTSecurityTests(TestCase):
    """Test JWT security measures"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_token_generation(self):
        """Test secure token generation"""
        from core.security.jwt_security import secure_jwt_handler
        
        tokens = secure_jwt_handler.generate_token_pair(self.user)
        
        self.assertIn('access_token', tokens)
        self.assertIn('refresh_token', tokens)
        self.assertIn('expires_in', tokens)
        
        # Verify token structure
        access_payload = jwt.decode(
            tokens['access_token'], 
            settings.SECRET_KEY, 
            algorithms=['HS256']
        )
        
        self.assertEqual(access_payload['user_id'], self.user.id)
        self.assertEqual(access_payload['type'], 'access')
        self.assertIn('jti', access_payload)
        self.assertIn('iss', access_payload)
        self.assertIn('aud', access_payload)
    
    def test_token_validation(self):
        """Test token validation with security checks"""
        from core.security.jwt_security import secure_jwt_handler
        
        tokens = secure_jwt_handler.generate_token_pair(self.user)
        access_token = tokens['access_token']
        
        # Valid token should pass
        payload = secure_jwt_handler.validate_token(access_token)
        self.assertEqual(payload['user_id'], self.user.id)
        
        # Expired token should fail
        expired_payload = {
            'user_id': self.user.id,
            'type': 'access',
            'iat': datetime.utcnow() - timedelta(hours=2),
            'exp': datetime.utcnow() - timedelta(hours=1),
            'jti': 'test-jti',
            'iss': 'richesreach-api',
            'aud': 'richesreach-client'
        }
        
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')
        
        with self.assertRaises(Exception):
            secure_jwt_handler.validate_token(expired_token)
    
    def test_token_revocation(self):
        """Test token revocation functionality"""
        from core.security.jwt_security import secure_jwt_handler
        
        tokens = secure_jwt_handler.generate_token_pair(self.user)
        access_token = tokens['access_token']
        
        # Token should be valid initially
        payload = secure_jwt_handler.validate_token(access_token)
        self.assertEqual(payload['user_id'], self.user.id)
        
        # Revoke token
        secure_jwt_handler.revoke_token(access_token)
        
        # Token should now be invalid
        with self.assertRaises(Exception):
            secure_jwt_handler.validate_token(access_token)
    
    def test_refresh_token_flow(self):
        """Test secure refresh token flow"""
        from core.security.jwt_security import secure_jwt_handler
        
        tokens = secure_jwt_handler.generate_token_pair(self.user)
        refresh_token = tokens['refresh_token']
        
        # Use refresh token to get new access token
        new_tokens = secure_jwt_handler.refresh_access_token(refresh_token)
        
        self.assertIn('access_token', new_tokens)
        self.assertIn('refresh_token', new_tokens)
        
        # Old refresh token should be invalid
        with self.assertRaises(Exception):
            secure_jwt_handler.refresh_access_token(refresh_token)


class PIIRedactionTests(TestCase):
    """Test PII redaction functionality"""
    
    def test_email_redaction(self):
        """Test email address redaction"""
        from core.security.secure_logging import pii_redactor
        
        text = "User email is john.doe@example.com and contact is admin@company.com"
        redacted = pii_redactor.redact(text)
        
        self.assertNotIn('john.doe@example.com', redacted)
        self.assertNotIn('admin@company.com', redacted)
        self.assertIn('[EMAIL_REDACTED]', redacted)
    
    def test_phone_redaction(self):
        """Test phone number redaction"""
        from core.security.secure_logging import pii_redactor
        
        text = "Call us at (555) 123-4567 or 555-987-6543"
        redacted = pii_redactor.redact(text)
        
        self.assertNotIn('(555) 123-4567', redacted)
        self.assertNotIn('555-987-6543', redacted)
        self.assertIn('[PHONE_REDACTED]', redacted)
    
    def test_jwt_token_redaction(self):
        """Test JWT token redaction"""
        from core.security.secure_logging import pii_redactor
        
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        text = f"Authorization: Bearer {jwt_token}"
        redacted = pii_redactor.redact(text)
        
        self.assertNotIn(jwt_token, redacted)
        self.assertIn('[JWT_REDACTED]', redacted)
    
    def test_dict_redaction(self):
        """Test dictionary redaction"""
        from core.security.secure_logging import pii_redactor
        
        data = {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'secret123',
            'phone': '555-123-4567',
            'nested': {
                'api_key': 'sk-1234567890abcdef',
                'normal_field': 'normal_value'
            }
        }
        
        redacted = pii_redactor.redact_dict(data)
        
        self.assertEqual(redacted['username'], 'john_doe')  # Not sensitive
        self.assertEqual(redacted['email'], '[EMAIL_REDACTED]')
        self.assertEqual(redacted['password'], '[REDACTED]')
        self.assertEqual(redacted['phone'], '[PHONE_REDACTED]')
        self.assertEqual(redacted['nested']['api_key'], '[REDACTED]')
        self.assertEqual(redacted['nested']['normal_field'], 'normal_value')


class SecurityHeadersTests(TestCase):
    """Test security headers"""
    
    def test_security_headers(self):
        """Test that security headers are present"""
        response = self.client.get('/healthz/')
        
        # Check security headers
        self.assertEqual(response.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.get('X-Content-Type-Options'), 'nosniff')
        self.assertIn('X-XSS-Protection', response)
        self.assertIn('Referrer-Policy', response)
    
    def test_cors_headers(self):
        """Test CORS configuration"""
        response = self.client.options('/graphql/')
        
        # Should not allow all origins in production
        self.assertNotEqual(response.get('Access-Control-Allow-Origin'), '*')


class AuthenticationTests(TestCase):
    """Test authentication security"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_password_requirements(self):
        """Test password validation requirements"""
        # Weak password should fail
        weak_user = User(
            username='weakuser',
            email='weak@example.com',
            password='123'  # Too short
        )
        
        with self.assertRaises(Exception):
            weak_user.full_clean()
    
    def test_authentication_attempts(self):
        """Test authentication attempt logging"""
        from core.security.secure_logging import security_audit_logger
        
        # Mock request
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        # Log authentication attempt
        with patch('core.security.secure_logging.security_audit_logger.logger') as mock_logger:
            security_audit_logger.log_authentication_attempt(request, False, None)
            mock_logger.info.assert_called_once()
    
    def test_suspicious_activity_logging(self):
        """Test suspicious activity detection and logging"""
        from core.security.secure_logging import security_audit_logger
        
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        with patch('core.security.secure_logging.security_audit_logger.logger') as mock_logger:
            security_audit_logger.log_suspicious_activity(
                request, 
                'multiple_failed_logins', 
                {'attempts': 5, 'user': 'testuser'}
            )
            mock_logger.warning.assert_called_once()


class PerformanceSecurityTests(TestCase):
    """Test performance-related security measures"""
    
    def test_slow_query_detection(self):
        """Test slow query detection and logging"""
        from core.security.secure_logging import slow_query_logger
        
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        request.user = MagicMock()
        request.user.id = 1
        
        with patch('core.security.secure_logging.slow_query_logger.logger') as mock_logger:
            slow_query_logger.log_slow_query(
                request,
                'query { stocks { symbol name price } }',
                6.5,  # 6.5 seconds - should trigger slow query log
                150   # complexity
            )
            mock_logger.warning.assert_called_once()
    
    def test_query_complexity_analysis(self):
        """Test query complexity analysis"""
        from core.security.graphql_security import QueryComplexityAnalyzer
        
        analyzer = QueryComplexityAnalyzer()
        
        # Simple query
        simple_query = "query { ping }"
        complexity = analyzer.calculate_complexity(simple_query)
        self.assertEqual(complexity, 1)
        
        # Complex query
        complex_query = "query { stocks { symbol } allStocks { symbol } searchTickers(q: \"test\") { symbol } }"
        complexity = analyzer.calculate_complexity(complex_query)
        self.assertGreater(complexity, 10)


class IntegrationSecurityTests(TestCase):
    """Integration tests for security measures"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_end_to_end_security_flow(self):
        """Test complete security flow"""
        # 1. Test rate limiting
        for i in range(5):
            response = self.client.post(
                '/graphql/',
                data=json.dumps({'query': 'query { ping }'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
        
        # 2. Test introspection blocking
        response = self.client.post(
            '/graphql/',
            data=json.dumps({'query': 'query { __schema { queryType { name } } }'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # 3. Test security headers
        response = self.client.get('/healthz/')
        self.assertEqual(response.get('X-Frame-Options'), 'DENY')
    
    def test_production_settings_validation(self):
        """Test that production settings are properly configured"""
        # Debug should be False
        self.assertFalse(settings.DEBUG)
        
        # Security settings should be enabled
        self.assertTrue(settings.SECURE_SSL_REDIRECT)
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertTrue(settings.SECURE_BROWSER_XSS_FILTER)
        
        # CORS should not allow all origins
        self.assertFalse(settings.CORS_ALLOW_ALL_ORIGINS)
        
        # JWT settings should be secure
        self.assertEqual(settings.GRAPHQL_JWT['JWT_EXPIRATION_DELTA'], timedelta(minutes=15))
        self.assertTrue(settings.GRAPHQL_JWT['JWT_VERIFY_EXPIRATION'])
