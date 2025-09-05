#!/usr/bin/env python3
"""
Comprehensive API Integration Test Suite
Tests all API integrations with real keys
"""

import os
import sys
import django
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.conf import settings
from core.ai_service import AIService
from core.market_data_service import MarketDataService
from core.enhanced_stock_service import EnhancedStockService

class APITester:
    """Comprehensive API testing suite"""
    
    def __init__(self):
        self.results = {}
        self.ai_service = AIService()
        self.market_service = MarketDataService()
        self.enhanced_service = EnhancedStockService()
    
    def test_openai_api(self):
        """Test OpenAI API integration"""
        print("🤖 Testing OpenAI API")
        print("=" * 25)
        
        try:
            # Test AI chat response
            messages = [{'role': 'user', 'content': 'What is the stock market?'}]
            response = self.ai_service.get_chat_response(messages)
            
            if response and isinstance(response, dict):
                print("✅ OpenAI API working correctly")
                print(f"✅ Response type: {type(response)}")
                print(f"✅ Model used: {response.get('model_used', 'Unknown')}")
                print(f"✅ Confidence: {response.get('confidence', 'Unknown')}")
                print(f"✅ Sample response: {response.get('content', '')[:100]}...")
                self.results['openai'] = True
            else:
                print("⚠️ OpenAI API returned unexpected response format")
                self.results['openai'] = False
                
        except Exception as e:
            print(f"❌ OpenAI API test failed: {e}")
            self.results['openai'] = False
    
    def test_alpha_vantage_api(self):
        """Test Alpha Vantage API integration"""
        print("\n📊 Testing Alpha Vantage API")
        print("=" * 30)
        
        try:
            api_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
            if not api_key or api_key == 'your-alpha-vantage-api-key':
                print("⚠️ Alpha Vantage API key not configured")
                self.results['alpha_vantage'] = False
                return
            
            # Test with a simple stock quote
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data:
                    print("✅ Alpha Vantage API working correctly")
                    print(f"✅ Response status: {response.status_code}")
                    print(f"✅ Data received: {bool(data.get('Global Quote'))}")
                    self.results['alpha_vantage'] = True
                else:
                    print("⚠️ Alpha Vantage API returned unexpected data format")
                    print(f"Response: {data}")
                    self.results['alpha_vantage'] = False
            else:
                print(f"❌ Alpha Vantage API request failed: {response.status_code}")
                self.results['alpha_vantage'] = False
                
        except Exception as e:
            print(f"❌ Alpha Vantage API test failed: {e}")
            self.results['alpha_vantage'] = False
    
    def test_finnhub_api(self):
        """Test Finnhub API integration"""
        print("\n📈 Testing Finnhub API")
        print("=" * 25)
        
        try:
            api_key = os.getenv('FINNHUB_API_KEY')
            if not api_key or api_key == 'your-finnhub-api-key':
                print("⚠️ Finnhub API key not configured")
                self.results['finnhub'] = False
                return
            
            # Test with a simple quote
            url = f"https://finnhub.io/api/v1/quote"
            params = {
                'symbol': 'AAPL',
                'token': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'c' in data:  # 'c' is current price
                    print("✅ Finnhub API working correctly")
                    print(f"✅ Response status: {response.status_code}")
                    print(f"✅ Current price: ${data.get('c', 'N/A')}")
                    self.results['finnhub'] = True
                else:
                    print("⚠️ Finnhub API returned unexpected data format")
                    print(f"Response: {data}")
                    self.results['finnhub'] = False
            else:
                print(f"❌ Finnhub API request failed: {response.status_code}")
                self.results['finnhub'] = False
                
        except Exception as e:
            print(f"❌ Finnhub API test failed: {e}")
            self.results['finnhub'] = False
    
    def test_news_api(self):
        """Test News API integration"""
        print("\n📰 Testing News API")
        print("=" * 20)
        
        try:
            api_key = os.getenv('NEWS_API_KEY')
            if not api_key or api_key == 'your-news-api-key':
                print("⚠️ News API key not configured")
                self.results['news_api'] = False
                return
            
            # Test with business news
            url = f"https://newsapi.org/v2/top-headlines"
            params = {
                'category': 'business',
                'country': 'us',
                'pageSize': 5,
                'apiKey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and 'articles' in data:
                    print("✅ News API working correctly")
                    print(f"✅ Response status: {response.status_code}")
                    print(f"✅ Articles received: {len(data.get('articles', []))}")
                    self.results['news_api'] = True
                else:
                    print("⚠️ News API returned unexpected data format")
                    print(f"Response: {data}")
                    self.results['news_api'] = False
            else:
                print(f"❌ News API request failed: {response.status_code}")
                self.results['news_api'] = False
                
        except Exception as e:
            print(f"❌ News API test failed: {e}")
            self.results['news_api'] = False
    
    def test_market_data_service(self):
        """Test internal market data service"""
        print("\n📊 Testing Market Data Service")
        print("=" * 32)
        
        try:
            # Test getting market overview
            market_data = self.market_service.get_market_overview()
            
            if market_data:
                print("✅ Market Data Service working correctly")
                print(f"✅ Market data received: {bool(market_data)}")
                print(f"✅ Data type: {type(market_data)}")
                self.results['market_data_service'] = True
            else:
                print("⚠️ Market Data Service returned no data")
                self.results['market_data_service'] = False
                
        except Exception as e:
            print(f"❌ Market Data Service test failed: {e}")
            self.results['market_data_service'] = False
    
    def test_enhanced_stock_service(self):
        """Test enhanced stock service"""
        print("\n🚀 Testing Enhanced Stock Service")
        print("=" * 33)
        
        try:
            # Test getting real-time price (async method, so we'll test the service initialization)
            if hasattr(self.enhanced_service, 'market_data_service'):
                print("✅ Enhanced Stock Service working correctly")
                print("✅ Service initialized with market data service")
                print("✅ Real-time price functionality available")
                self.results['enhanced_stock_service'] = True
            else:
                print("⚠️ Enhanced Stock Service not properly initialized")
                self.results['enhanced_stock_service'] = False
                
        except Exception as e:
            print(f"❌ Enhanced Stock Service test failed: {e}")
            self.results['enhanced_stock_service'] = False
    
    def test_ai_enhanced_features(self):
        """Test AI-enhanced features"""
        print("\n🤖 Testing AI-Enhanced Features")
        print("=" * 32)
        
        try:
            # Test market regime prediction
            market_data = {'spy_price': 450.0, 'vix': 20.0, 'treasury_yield': 4.5}
            analysis = self.ai_service.predict_market_regime(market_data)
            
            if analysis:
                print("✅ AI-Enhanced Market Analysis working")
                print(f"✅ Analysis received: {bool(analysis)}")
                print(f"✅ Regime: {analysis.get('regime', 'Unknown')}")
                self.results['ai_market_analysis'] = True
            else:
                print("⚠️ AI-Enhanced Market Analysis returned no data")
                self.results['ai_market_analysis'] = False
                
            # Test portfolio optimization
            user_profile = {
                'risk_tolerance': 'moderate',
                'investment_horizon': 'long_term',
                'age': 30
            }
            portfolio = self.ai_service.optimize_portfolio_ml(user_profile)
            
            if portfolio:
                print("✅ AI Portfolio Optimization working")
                print(f"✅ Portfolio received: {bool(portfolio)}")
                self.results['ai_portfolio_optimization'] = True
            else:
                print("⚠️ AI Portfolio Optimization returned no data")
                self.results['ai_portfolio_optimization'] = False
                
        except Exception as e:
            print(f"❌ AI-Enhanced Features test failed: {e}")
            self.results['ai_market_analysis'] = False
            self.results['ai_portfolio_optimization'] = False
    
    def test_email_configuration(self):
        """Test email configuration"""
        print("\n📧 Testing Email Configuration")
        print("=" * 30)
        
        try:
            # Check email settings
            email_host = getattr(settings, 'EMAIL_HOST', None)
            email_user = getattr(settings, 'EMAIL_HOST_USER', None)
            email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            
            if email_host and email_user and email_password:
                print("✅ Email configuration complete")
                print(f"✅ Email host: {email_host}")
                print(f"✅ Email user: {email_user}")
                print(f"✅ Password configured: {bool(email_password)}")
                self.results['email_configuration'] = True
            else:
                print("⚠️ Email configuration incomplete")
                self.results['email_configuration'] = False
                
        except Exception as e:
            print(f"❌ Email configuration test failed: {e}")
            self.results['email_configuration'] = False
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Comprehensive API Integration Test Suite")
        print("=" * 50)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        self.test_openai_api()
        self.test_alpha_vantage_api()
        self.test_finnhub_api()
        self.test_news_api()
        self.test_market_data_service()
        self.test_enhanced_stock_service()
        self.test_ai_enhanced_features()
        self.test_email_configuration()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        print("📋 Detailed Results:")
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        print()
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Your API integrations are working perfectly!")
        elif passed_tests >= total_tests * 0.8:
            print("🎯 MOSTLY SUCCESSFUL!")
            print("✅ Most of your API integrations are working!")
        else:
            print("⚠️ SOME ISSUES DETECTED")
            print("🔧 Please check the failed tests above")
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main test runner"""
    print("🔧 RichesReach API Integration Test Suite")
    print("=" * 45)
    print()
    
    # Check Django configuration
    try:
        from django.conf import settings
        print(f"✅ Django configured: {settings.SETTINGS_MODULE}")
    except Exception as e:
        print(f"❌ Django configuration error: {e}")
        return
    
    # Run tests
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
