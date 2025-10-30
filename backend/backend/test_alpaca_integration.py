#!/usr/bin/env python3
"""
Comprehensive Alpaca Integration Test Suite
Tests all Alpaca OAuth and API integration features
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_production_real')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from alpaca_integration.services import AlpacaOAuthService, AlpacaAPIService
from alpaca_integration.models import AlpacaOAuthToken
from core.models.alpaca_models import AlpacaAccount, AlpacaPosition, AlpacaOrder

User = get_user_model()

class AlpacaIntegrationTestSuite:
    """Comprehensive test suite for Alpaca integration"""
    
    def __init__(self):
        self.base_url = "process.env.API_BASE_URL || "http://localhost:8000""
        self.client = Client()
        self.test_user = None
        self.test_results = []
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if message:
            print(f"   {message}")
    
    def setup_test_user(self):
        """Create a test user for testing"""
        try:
            self.test_user, created = User.objects.get_or_create(
                email="test@alpaca.com",
                defaults={
                    'username': 'alpaca_test_user',
                    'first_name': 'Alpaca',
                    'last_name': 'Test'
                }
            )
            if created:
                self.test_user.set_password('testpassword123')
                self.test_user.save()
            
            self.log_test("Setup Test User", "PASS", f"User {'created' if created else 'found'}")
            return True
        except Exception as e:
            self.log_test("Setup Test User", "FAIL", str(e))
            return False
    
    def test_server_health(self):
        """Test if the server is running and healthy"""
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('production'):
                    self.log_test("Server Health", "PASS", "Production server running")
                    return True
                else:
                    self.log_test("Server Health", "FAIL", "Server not in production mode")
                    return False
            else:
                self.log_test("Server Health", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Health", "FAIL", str(e))
            return False
    
    def test_alpaca_oauth_endpoints(self):
        """Test Alpaca OAuth endpoints"""
        try:
            # Test OAuth authorization endpoint
            response = requests.get(f"{self.base_url}/oauth/authorize/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'error' in data and 'Authentication required' in data['error']:
                    self.log_test("OAuth Authorization Endpoint", "PASS", "Endpoint requires authentication")
                else:
                    self.log_test("OAuth Authorization Endpoint", "FAIL", "Unexpected response")
                    return False
            else:
                self.log_test("OAuth Authorization Endpoint", "FAIL", f"HTTP {response.status_code}")
                return False
            
            # Test OAuth callback endpoint
            response = requests.get(f"{self.base_url}/oauth/callback/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'error' in data and 'Authentication required' in data['error']:
                    self.log_test("OAuth Callback Endpoint", "PASS", "Endpoint requires authentication")
                else:
                    self.log_test("OAuth Callback Endpoint", "FAIL", "Unexpected response")
                    return False
            else:
                self.log_test("OAuth Callback Endpoint", "FAIL", f"HTTP {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_test("OAuth Endpoints", "FAIL", str(e))
            return False
    
    def test_alpaca_api_endpoints(self):
        """Test Alpaca API endpoints"""
        try:
            endpoints = [
                ("/account/", "Account Endpoint"),
                ("/positions/", "Positions Endpoint"),
                ("/orders/", "Orders Endpoint"),
                ("/market-data/", "Market Data Endpoint")
            ]
            
            all_passed = True
            for endpoint, name in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'error' in data and 'Authentication required' in data['error']:
                        self.log_test(name, "PASS", "Endpoint requires authentication")
                    else:
                        self.log_test(name, "FAIL", "Unexpected response")
                        all_passed = False
                else:
                    self.log_test(name, "FAIL", f"HTTP {response.status_code}")
                    all_passed = False
            
            return all_passed
        except Exception as e:
            self.log_test("API Endpoints", "FAIL", str(e))
            return False
    
    def test_oauth_service_initialization(self):
        """Test OAuth service initialization"""
        try:
            oauth_service = AlpacaOAuthService()
            
            # Check if service has required attributes
            required_attrs = ['client_id', 'client_secret', 'redirect_uri', 'base_url']
            for attr in required_attrs:
                if not hasattr(oauth_service, attr):
                    self.log_test("OAuth Service Initialization", "FAIL", f"Missing attribute: {attr}")
                    return False
            
            self.log_test("OAuth Service Initialization", "PASS", "Service initialized successfully")
            return True
        except Exception as e:
            self.log_test("OAuth Service Initialization", "FAIL", str(e))
            return False
    
    def test_api_service_initialization(self):
        """Test API service initialization"""
        try:
            if not self.test_user:
                self.log_test("API Service Initialization", "SKIP", "No test user available")
                return False
            
            api_service = AlpacaAPIService(user=self.test_user)
            
            # Check if service has required attributes
            required_attrs = ['user', 'base_url', 'data_url']
            for attr in required_attrs:
                if not hasattr(api_service, attr):
                    self.log_test("API Service Initialization", "FAIL", f"Missing attribute: {attr}")
                    return False
            
            self.log_test("API Service Initialization", "PASS", "Service initialized successfully")
            return True
        except Exception as e:
            self.log_test("API Service Initialization", "FAIL", str(e))
            return False
    
    def test_database_models(self):
        """Test database models"""
        try:
            # Test OAuth token model
            token = AlpacaOAuthToken(
                user=self.test_user,
                access_token="test_token",
                expires_at=datetime.now()
            )
            self.log_test("OAuth Token Model", "PASS", "Model can be instantiated")
            
            # Test Alpaca account model
            account = AlpacaAccount(
                user=self.test_user,
                alpaca_account_id="test_account",
                status="ACTIVE"
            )
            self.log_test("Alpaca Account Model", "PASS", "Model can be instantiated")
            
            return True
        except Exception as e:
            self.log_test("Database Models", "FAIL", str(e))
            return False
    
    def test_environment_configuration(self):
        """Test environment configuration"""
        try:
            from django.conf import settings
            
            # Check Alpaca OAuth settings
            oauth_settings = [
                'ALPACA_CLIENT_ID',
                'ALPACA_CLIENT_SECRET', 
                'ALPACA_REDIRECT_URI'
            ]
            
            for setting in oauth_settings:
                if not hasattr(settings, setting):
                    self.log_test("Environment Configuration", "FAIL", f"Missing setting: {setting}")
                    return False
            
            # Check that mock services are disabled
            mock_settings = [
                'USE_BROKER_MOCK',
                'USE_MARKET_MOCK',
                'USE_AI_RECS_MOCK'
            ]
            
            for setting in mock_settings:
                if hasattr(settings, setting) and getattr(settings, setting):
                    self.log_test("Environment Configuration", "FAIL", f"Mock service enabled: {setting}")
                    return False
            
            self.log_test("Environment Configuration", "PASS", "All settings configured correctly")
            return True
        except Exception as e:
            self.log_test("Environment Configuration", "FAIL", str(e))
            return False
    
    def test_mobile_app_endpoints(self):
        """Test mobile app specific endpoints"""
        try:
            endpoints = [
                ("/api/oracle/insights/", "Oracle Insights"),
                ("/api/voice/process/", "Voice AI"),
                ("/api/wealth-circles/", "Wealth Circles"),
                ("/api/blockchain/status/", "Blockchain Status")
            ]
            
            all_passed = True
            for endpoint, name in endpoints:
                if endpoint == "/api/voice/process/":
                    # Voice AI endpoint requires POST with JSON body
                    response = requests.post(f"{self.base_url}{endpoint}", 
                                           json={"text": "test query"}, 
                                           timeout=5)
                else:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if (isinstance(data, dict) and len(data) > 0) or (isinstance(data, list) and len(data) > 0):
                        self.log_test(f"Mobile App - {name}", "PASS", "Endpoint returns data")
                    else:
                        self.log_test(f"Mobile App - {name}", "FAIL", "Empty or invalid response")
                        all_passed = False
                else:
                    self.log_test(f"Mobile App - {name}", "FAIL", f"HTTP {response.status_code}")
                    all_passed = False
            
            return all_passed
        except Exception as e:
            self.log_test("Mobile App Endpoints", "FAIL", str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests and return summary"""
        print("🚀 Starting Alpaca Integration Test Suite")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user, aborting tests")
            return False
        
        # Run tests
        tests = [
            self.test_server_health,
            self.test_alpaca_oauth_endpoints,
            self.test_alpaca_api_endpoints,
            self.test_oauth_service_initialization,
            self.test_api_service_initialization,
            self.test_database_models,
            self.test_environment_configuration,
            self.test_mobile_app_endpoints
        ]
        
        passed = 0
        failed = 0
        skipped = 0
        
        for test in tests:
            try:
                result = test()
                if result is True:
                    passed += 1
                elif result is False:
                    failed += 1
                else:
                    skipped += 1
            except Exception as e:
                self.log_test(test.__name__, "FAIL", f"Test exception: {str(e)}")
                failed += 1
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Skipped: {skipped}")
        print(f"📈 Total: {passed + failed + skipped}")
        
        success_rate = (passed / (passed + failed + skipped)) * 100 if (passed + failed + skipped) > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Alpaca integration is ready for partnership.")
            return True
        else:
            print(f"\n⚠️  {failed} tests failed. Please review and fix issues.")
            return False

def main():
    """Main test runner"""
    test_suite = AlpacaIntegrationTestSuite()
    success = test_suite.run_all_tests()
    
    # Save results to file
    with open('alpaca_integration_test_results.json', 'w') as f:
        json.dump(test_suite.test_results, f, indent=2)
    
    print(f"\n📄 Test results saved to: alpaca_integration_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
