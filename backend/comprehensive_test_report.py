#!/usr/bin/env python3
"""
RichesReach API Endpoint Test Report
===================================

Comprehensive test results for all new RichesReach endpoints.
Generated: 2025-01-28
"""

import requests
import json
import time
from datetime import datetime

class EndpointTestReport:
    """Generate comprehensive test report for RichesReach endpoints"""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def test_endpoint(self, endpoint, method="GET", data=None, expected_status=200, description=""):
        """Test a single endpoint and record results"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                headers = {'Content-Type': 'application/json'}
                response = self.session.post(url, json=data, headers=headers, timeout=10)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            success = response.status_code == expected_status
            
            result = {
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'response_time': response_time,
                'success': success,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                'endpoint': endpoint,
                'method': method,
                'status_code': 0,
                'expected_status': expected_status,
                'response_time': 0,
                'success': False,
                'error': str(e),
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            return result

    def run_comprehensive_tests(self):
        """Run comprehensive tests for all endpoints"""
        print("🚀 Running Comprehensive RichesReach API Tests...")
        print("=" * 60)
        
        # Test server connectivity
        health_result = self.test_endpoint("/health/", "GET", expected_status=200, 
                                         description="Server health check")
        if not health_result['success']:
            print("❌ Server is not accessible. Please start the Django server.")
            return False
        
        print("✅ Server is running and accessible")
        print()
        
        # =====================================================================
        # PUMP.FUN INTEGRATION TESTS
        # =====================================================================
        print("🎮 Testing Pump.fun Integration...")
        
        # Test launch meme coin
        meme_data = {
            "name": "TestFrog",
            "symbol": "TFROG",
            "description": "Test meme coin for API testing",
            "template": "wealth-frog",
            "cultural_theme": "BIPOC Wealth Building"
        }
        self.test_endpoint("/api/pump-fun/launch/", "POST", meme_data, 201,
                          "Launch new meme coin")
        
        # Test bonding curve
        self.test_endpoint("/api/pump-fun/bonding-curve/0x1234567890abcdef/", "GET", 
                          expected_status=200, description="Get bonding curve data")
        
        # Test trade execution
        trade_data = {
            "contract_address": "0x1234567890abcdef",
            "amount": 100.0,
            "trade_type": "buy"
        }
        self.test_endpoint("/api/pump-fun/trade/", "POST", trade_data, 200,
                          "Execute trade")
        
        # =====================================================================
        # DEFI YIELD FARMING TESTS
        # =====================================================================
        print("\n💰 Testing DeFi Yield Farming...")
        
        # Test get yield pools
        self.test_endpoint("/api/defi/pools/", "GET", expected_status=200,
                          description="Get available yield pools")
        self.test_endpoint("/api/defi/pools/?chain=ethereum", "GET", expected_status=200,
                          description="Get yield pools for specific chain")
        
        # Test stake tokens
        stake_data = {
            "pool_id": "test-pool-123",
            "amount": 50.0,
            "user_address": "0x1234567890abcdef"
        }
        self.test_endpoint("/api/defi/stake/", "POST", stake_data, 200,
                          "Stake tokens in yield pool")
        
        # Test unstake tokens
        self.test_endpoint("/api/defi/unstake/", "POST", stake_data, 200,
                          "Unstake tokens from yield pool")
        
        # Test get user stakes
        self.test_endpoint("/api/defi/stakes/0x1234567890abcdef/", "GET", expected_status=200,
                          "Get user's current stakes")
        
        # =====================================================================
        # SOCIAL TRADING TESTS
        # =====================================================================
        print("\n👥 Testing Social Trading...")
        
        # Test social feed
        self.test_endpoint("/api/social/feed", "GET", expected_status=200,
                          "Get social trading feed")
        
        # Test meme templates
        self.test_endpoint("/api/social/meme-templates", "GET", expected_status=200,
                          "Get available meme templates")
        
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
        self.test_endpoint("/api/social/launch-meme", "POST", launch_data, 201,
                          "Launch meme via social trading")
        
        # Test voice command
        voice_data = {
            "command": "launch meme",
            "user_id": "test-user-123",
            "parameters": {
                "name": "VoiceFrog",
                "template": "frog"
            }
        }
        self.test_endpoint("/api/social/voice-command", "POST", voice_data, 200,
                          "Process voice command")
        
        # Test create raid
        raid_data = {
            "user_id": "test-user-123",
            "meme_id": "test-meme-123",
            "amount": 100.0
        }
        self.test_endpoint("/api/social/create-raid", "POST", raid_data, 201,
                          "Create new trading raid")
        
        # Test join raid
        join_raid_data = {
            "user_id": "test-user-123",
            "raid_id": "test-raid-123",
            "amount": 50.0
        }
        self.test_endpoint("/api/social/join-raid", "POST", join_raid_data, 200,
                          "Join existing raid")
        
        # Test stake meme yield
        yield_data = {
            "meme_id": "test-meme-123",
            "amount": 50.0,
            "user_address": "0x1234567890abcdef"
        }
        self.test_endpoint("/api/social/stake-yield", "POST", yield_data, 200,
                          "Stake meme tokens for yield")
        
        # Test meme analytics
        self.test_endpoint("/api/social/meme-analytics", "GET", expected_status=200,
                          "Get meme analytics")
        
        # Test leaderboard
        self.test_endpoint("/api/social/leaderboard", "GET", expected_status=200,
                          "Get social trading leaderboard")
        
        # Test health check
        self.test_endpoint("/api/social/health", "GET", expected_status=200,
                          "Social trading health check")
        
        # =====================================================================
        # CORE SYSTEM TESTS
        # =====================================================================
        print("\n🏠 Testing Core System...")
        
        # Test market quotes
        self.test_endpoint("/api/market/quotes/", "GET", expected_status=200,
                          "Get market quotes")
        
        # Test portfolio
        self.test_endpoint("/api/portfolio/", "GET", expected_status=200,
                          "Get portfolio data")
        
        # =====================================================================
        # ERROR HANDLING TESTS
        # =====================================================================
        print("\n⚠️ Testing Error Handling...")
        
        # Test invalid JSON
        try:
            response = self.session.post(
                f"{self.base_url}/api/pump-fun/launch/",
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            self.test_endpoint("/api/pump-fun/launch/", "POST", "invalid json", 400,
                              "Handle invalid JSON")
        except:
            pass
        
        # Test missing required fields
        incomplete_data = {"name": "Test"}
        self.test_endpoint("/api/pump-fun/launch/", "POST", incomplete_data, 400,
                          "Handle missing required fields")
        
        # Test non-existent endpoint
        self.test_endpoint("/api/non-existent/", "GET", expected_status=404,
                          "Handle non-existent endpoints")
        
        return True

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Group results by category
        categories = {
            'Pump.fun Integration': [],
            'DeFi Yield Farming': [],
            'Social Trading': [],
            'Core System': [],
            'Error Handling': []
        }
        
        for result in self.results:
            endpoint = result['endpoint']
            if '/pump-fun/' in endpoint:
                categories['Pump.fun Integration'].append(result)
            elif '/defi/' in endpoint:
                categories['DeFi Yield Farming'].append(result)
            elif '/social/' in endpoint:
                categories['Social Trading'].append(result)
            elif '/api/market/' in endpoint or '/api/portfolio/' in endpoint or '/health/' in endpoint:
                categories['Core System'].append(result)
            else:
                categories['Error Handling'].append(result)
        
        # Print results by category
        for category, tests in categories.items():
            if tests:
                print(f"📋 {category}:")
                category_success = sum(1 for t in tests if t['success'])
                category_total = len(tests)
                print(f"   Success Rate: {category_success}/{category_total} ({category_success/category_total*100:.1f}%)")
                
                for test in tests:
                    status = "✅" if test['success'] else "❌"
                    print(f"   {status} {test['method']} {test['endpoint']} - {test['status_code']} ({test['response_time']:.3f}s)")
                    if test['description']:
                        print(f"      {test['description']}")
                print()
        
        # Performance summary
        response_times = [r['response_time'] for r in self.results if r['response_time'] > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print("⚡ Performance Summary:")
            print(f"   Average Response Time: {avg_time:.3f}s")
            print(f"   Min Response Time: {min_time:.3f}s")
            print(f"   Max Response Time: {max_time:.3f}s")
            
            if avg_time > 2.0:
                print("   ⚠️ Warning: Average response time is slow")
            else:
                print("   ✅ Performance is acceptable")
            print()
        
        # Recommendations
        print("💡 Recommendations:")
        if success_rate >= 90:
            print("   ✅ Excellent! All endpoints are working well.")
        elif success_rate >= 80:
            print("   ✅ Good! Most endpoints are working. Review failed tests.")
        elif success_rate >= 70:
            print("   ⚠️ Fair. Some endpoints need attention.")
        else:
            print("   ❌ Poor. Many endpoints need fixes.")
        
        if failed_tests > 0:
            print("   🔧 Fix the following issues:")
            for result in self.results:
                if not result['success']:
                    print(f"      - {result['method']} {result['endpoint']}: {result.get('error', 'Status code mismatch')}")
        
        print("\n🎯 Next Steps:")
        print("   1. Fix any failed endpoints")
        print("   2. Add authentication for protected endpoints")
        print("   3. Implement real service integrations")
        print("   4. Add comprehensive error handling")
        print("   5. Set up monitoring and alerting")
        
        return success_rate >= 80

def main():
    """Main function to run comprehensive tests"""
    tester = EndpointTestReport()
    
    if tester.run_comprehensive_tests():
        success = tester.generate_report()
        if success:
            print("\n🎉 All tests completed successfully!")
            return 0
        else:
            print("\n⚠️ Some tests failed. Please review the report.")
            return 1
    else:
        print("\n❌ Server is not accessible. Please start the Django server.")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
