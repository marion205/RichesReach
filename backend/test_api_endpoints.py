#!/usr/bin/env python3
"""
RichesReach API Endpoint Testing Script
=======================================

This script tests all new API endpoints with real HTTP requests
to ensure they're working correctly in the running application.

Usage: python test_api_endpoints.py
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

class APITester:
    """Comprehensive API testing for RichesReach endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def log_test(self, endpoint: str, method: str, status_code: int, 
                 response_time: float, success: bool, error: str = None):
        """Log test result"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time,
            'success': success,
            'error': error
        }
        self.results.append(result)
        
        status_emoji = "✅" if success else "❌"
        print(f"{status_emoji} {method} {endpoint} - {status_code} ({response_time:.3f}s)")
        if error:
            print(f"   Error: {error}")

    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     data: Dict[str, Any] = None, expected_status: int = 200) -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                headers = {'Content-Type': 'application/json'}
                response = self.session.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == "PUT":
                headers = {'Content-Type': 'application/json'}
                response = self.session.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            success = response.status_code == expected_status
            error = None if success else f"Expected {expected_status}, got {response.status_code}"
            
            self.log_test(endpoint, method, response.status_code, response_time, success, error)
            
            return success
            
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            response_time = end_time - start_time
            self.log_test(endpoint, method, 0, response_time, False, str(e))
            return False

    def test_pump_fun_endpoints(self):
        """Test Pump.fun integration endpoints"""
        print("\n🎮 Testing Pump.fun Endpoints...")
        
        # Test launch meme coin
        meme_data = {
            "name": "TestFrog",
            "symbol": "TFROG", 
            "description": "Test meme coin for API testing",
            "template": "wealth-frog",
            "cultural_theme": "BIPOC Wealth Building"
        }
        
        self.test_endpoint("/api/pump-fun/launch/", "POST", meme_data, 201)
        
        # Test bonding curve (with mock contract address)
        self.test_endpoint("/api/pump-fun/bonding-curve/0x1234567890abcdef/", "GET")
        
        # Test trade execution
        trade_data = {
            "contract_address": "0x1234567890abcdef",
            "amount": 100.0,
            "trade_type": "buy"
        }
        self.test_endpoint("/api/pump-fun/trade/", "POST", trade_data)

    def test_defi_endpoints(self):
        """Test DeFi yield farming endpoints"""
        print("\n💰 Testing DeFi Yield Endpoints...")
        
        # Test get yield pools
        self.test_endpoint("/api/defi/pools/", "GET")
        self.test_endpoint("/api/defi/pools/?chain=ethereum", "GET")
        
        # Test stake tokens
        stake_data = {
            "pool_id": "test-pool-123",
            "amount": 50.0,
            "user_address": "0x1234567890abcdef"
        }
        self.test_endpoint("/api/defi/stake/", "POST", stake_data)
        
        # Test unstake tokens
        self.test_endpoint("/api/defi/unstake/", "POST", stake_data)
        
        # Test get user stakes
        self.test_endpoint("/api/defi/stakes/0x1234567890abcdef/", "GET")

    def test_social_trading_endpoints(self):
        """Test social trading endpoints"""
        print("\n👥 Testing Social Trading Endpoints...")
        
        # Test social feed
        self.test_endpoint("/api/social/feed", "GET")
        
        # Test meme templates
        self.test_endpoint("/api/social/meme-templates", "GET")
        
        # Test launch meme
        launch_data = {
            "user_id": "test-user-123",
            "meme_data": {
                "name": "SocialFrog",
                "template": "wealth-frog",
                "description": "Social trading test meme",
                "cultural_theme": "BIPOC Wealth Building",
                "ai_generated": False
            }
        }
        self.test_endpoint("/api/social/launch-meme", "POST", launch_data, 201)
        
        # Test voice command
        voice_data = {
            "command": "launch meme",
            "user_id": "test-user-123",
            "parameters": {
                "name": "VoiceFrog",
                "template": "frog"
            }
        }
        self.test_endpoint("/api/social/voice-command", "POST", voice_data)
        
        # Test create raid
        raid_data = {
            "user_id": "test-user-123",
            "meme_id": "test-meme-123",
            "amount": 100.0
        }
        self.test_endpoint("/api/social/create-raid", "POST", raid_data)
        
        # Test join raid
        self.test_endpoint("/api/social/join-raid", "POST", raid_data)
        
        # Test stake meme yield
        yield_data = {
            "meme_id": "test-meme-123",
            "amount": 50.0,
            "user_address": "0x1234567890abcdef"
        }
        self.test_endpoint("/api/social/stake-yield", "POST", yield_data)
        
        # Test meme analytics
        self.test_endpoint("/api/social/meme-analytics", "GET")
        
        # Test leaderboard
        self.test_endpoint("/api/social/leaderboard", "GET")
        
        # Test health check
        self.test_endpoint("/api/social/health", "GET")

    def test_existing_endpoints(self):
        """Test existing RichesReach endpoints"""
        print("\n🏠 Testing Existing Endpoints...")
        
        # Test health endpoint
        self.test_endpoint("/health/", "GET")
        
        # Test market quotes
        self.test_endpoint("/api/market/quotes/", "GET")
        
        # Test portfolio endpoints
        self.test_endpoint("/api/portfolio/", "GET")
        
        # Test user profile
        self.test_endpoint("/api/user/profile/", "GET")

    def test_error_scenarios(self):
        """Test error handling scenarios"""
        print("\n⚠️ Testing Error Scenarios...")
        
        # Test invalid JSON
        try:
            response = self.session.post(
                f"{self.base_url}/api/pump-fun/launch/",
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            self.log_test("/api/pump-fun/launch/", "POST", response.status_code, 0, 
                         response.status_code == 400, "Should handle invalid JSON")
        except Exception as e:
            self.log_test("/api/pump-fun/launch/", "POST", 0, 0, False, str(e))
        
        # Test missing required fields
        incomplete_data = {"name": "Test"}
        self.test_endpoint("/api/pump-fun/launch/", "POST", incomplete_data, 400)
        
        # Test non-existent endpoint
        self.test_endpoint("/api/non-existent/", "GET", expected_status=404)

    def test_performance(self):
        """Test endpoint performance"""
        print("\n⚡ Testing Performance...")
        
        # Test multiple requests to same endpoint
        endpoint = "/api/defi/pools/"
        times = []
        
        for i in range(5):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                times.append(end_time - start_time)
            except Exception as e:
                print(f"   Performance test {i+1} failed: {e}")
        
        if times:
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"   Average response time: {avg_time:.3f}s")
            print(f"   Min response time: {min_time:.3f}s")
            print(f"   Max response time: {max_time:.3f}s")
            
            if avg_time > 2.0:
                print("   ⚠️ Warning: Average response time is slow")
            else:
                print("   ✅ Performance is acceptable")

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting RichesReach API Endpoint Tests...")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test server connectivity
        try:
            response = self.session.get(f"{self.base_url}/health/", timeout=5)
            if response.status_code == 200:
                print("✅ Server is running and accessible")
            else:
                print(f"⚠️ Server responded with status {response.status_code}")
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("Make sure the Django server is running on port 8001")
            return False
        
        # Run all test suites
        self.test_existing_endpoints()
        self.test_pump_fun_endpoints()
        self.test_defi_endpoints()
        self.test_social_trading_endpoints()
        self.test_error_scenarios()
        self.test_performance()
        
        # Print summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['method']} {result['endpoint']}: {result['error']}")
        
        # Performance summary
        response_times = [r['response_time'] for r in self.results if r['response_time'] > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"\n⚡ Average response time: {avg_time:.3f}s")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test RichesReach API endpoints')
    parser.add_argument('--url', default='http://localhost:8001', 
                       help='Base URL for the API (default: http://localhost:8001)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    tester = APITester(args.url)
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests completed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
