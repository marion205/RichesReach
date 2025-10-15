#!/usr/bin/env python3
"""
React Native Endpoint Test Script
Tests all endpoints that the React Native app will be calling
"""

import requests
import json
import time
from typing import Dict, List, Tuple, Any

class ReactNativeEndpointTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "endpoints": []
        }
    
    def test_endpoint(self, name: str, method: str, path: str, 
                     expected_status: int = 200, data: Dict = None, 
                     headers: Dict = None) -> Dict[str, Any]:
        """Test a single endpoint"""
        url = f"{self.base_url}{path}"
        
        try:
            if method.upper() == "POST":
                response = requests.post(
                    url, 
                    json=data, 
                    headers=headers or {},
                    timeout=10
                )
            elif method.upper() == "GET":
                response = requests.get(
                    url, 
                    headers=headers or {},
                    timeout=10
                )
            else:
                response = requests.request(
                    method, 
                    url, 
                    json=data, 
                    headers=headers or {},
                    timeout=10
                )
            
            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = {"content": response.text[:200]}
            
            result = {
                "name": name,
                "method": method,
                "path": path,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "response_data": response_data,
                "error": None
            }
            
            if success:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
                result["error"] = f"Expected {expected_status}, got {response.status_code}"
            
            self.results["total_tests"] += 1
            self.results["endpoints"].append(result)
            
            return result
            
        except Exception as e:
            result = {
                "name": name,
                "method": method,
                "path": path,
                "expected_status": expected_status,
                "actual_status": 0,
                "success": False,
                "response_time_ms": 0,
                "response_data": None,
                "error": str(e)
            }
            
            self.results["failed"] += 1
            self.results["total_tests"] += 1
            self.results["endpoints"].append(result)
            
            return result
    
    def test_authentication_endpoints(self):
        """Test authentication-related endpoints"""
        print("🔐 Testing Authentication Endpoints...")
        
        # Test login endpoint
        self.test_endpoint(
            "User Login",
            "POST",
            "/auth/",
            expected_status=200,
            data={"email": "test@example.com", "password": "test123"}
        )
        
        # Test user profile endpoint
        self.test_endpoint(
            "User Profile",
            "GET",
            "/me/",
            expected_status=200
        )
    
    def test_graphql_endpoints(self):
        """Test GraphQL endpoints"""
        print("🔍 Testing GraphQL Endpoints...")
        
        # Test GraphQL schema introspection
        self.test_endpoint(
            "GraphQL Schema",
            "POST",
            "/graphql/",
            expected_status=200,
            data={"query": "query { __schema { types { name } } }"}
        )
        
        # Test GraphQL with stock query
        self.test_endpoint(
            "GraphQL Stock Query",
            "POST",
            "/graphql/",
            expected_status=200,
            data={"query": "query { stocks { symbol companyName currentPrice } }"}
        )
        
        # Test GraphQL with user query
        self.test_endpoint(
            "GraphQL User Query",
            "POST",
            "/graphql/",
            expected_status=200,
            data={"query": "query { me { id name email } }"}
        )
    
    def test_ai_endpoints(self):
        """Test AI-powered endpoints"""
        print("🤖 Testing AI Endpoints...")
        
        # Test AI options recommendations
        self.test_endpoint(
            "AI Options Recommendations",
            "POST",
            "/api/ai-options/recommendations/",
            expected_status=200,
            data={
                "symbol": "AAPL",
                "amount": 10000,
                "timeframe": "30d",
                "risk_tolerance": "medium"
            }
        )
        
        # Test AI portfolio optimization
        self.test_endpoint(
            "AI Portfolio Optimization",
            "POST",
            "/api/ai-portfolio/optimize",
            expected_status=200,
            data={
                "portfolio": [
                    {"symbol": "AAPL", "shares": 100},
                    {"symbol": "MSFT", "shares": 50}
                ],
                "risk_tolerance": "medium"
            }
        )
        
        # Test ML service status
        self.test_endpoint(
            "ML Service Status",
            "POST",
            "/api/ml/status",
            expected_status=200
        )
    
    def test_bank_integration_endpoints(self):
        """Test bank integration endpoints"""
        print("🏦 Testing Bank Integration Endpoints...")
        
        # Test SBLOC health
        self.test_endpoint(
            "SBLOC Health Check",
            "GET",
            "/api/sbloc/health/",
            expected_status=200
        )
        
        # Test SBLOC banks
        self.test_endpoint(
            "SBLOC Banks List",
            "GET",
            "/api/sbloc/banks",
            expected_status=200
        )
        
        # Test Yodlee bank linking (expects redirect)
        self.test_endpoint(
            "Yodlee Bank Linking",
            "GET",
            "/api/yodlee/fastlink/start",
            expected_status=302  # Redirect to login is expected
        )
        
        # Test Yodlee accounts
        self.test_endpoint(
            "Yodlee Accounts",
            "GET",
            "/api/yodlee/accounts",
            expected_status=200
        )
    
    def test_market_data_endpoints(self):
        """Test market data endpoints"""
        print("📈 Testing Market Data Endpoints...")
        
        # Test stock data
        self.test_endpoint(
            "Stock Market Data",
            "GET",
            "/api/market-data/stocks",
            expected_status=200
        )
        
        # Test options data
        self.test_endpoint(
            "Options Market Data",
            "GET",
            "/api/market-data/options",
            expected_status=200
        )
        
        # Test market news
        self.test_endpoint(
            "Market News",
            "GET",
            "/api/market-data/news",
            expected_status=200
        )
        
        # Test crypto prices
        self.test_endpoint(
            "Crypto Prices",
            "POST",
            "/api/crypto/prices",
            expected_status=200,
            data={"symbols": ["BTC", "ETH", "USDC"]}
        )
    
    def test_defi_endpoints(self):
        """Test DeFi endpoints"""
        print("₿ Testing DeFi Endpoints...")
        
        # Test DeFi account
        self.test_endpoint(
            "DeFi Account",
            "POST",
            "/api/defi/account",
            expected_status=200
        )
        
        # Test Rust crypto analysis
        self.test_endpoint(
            "Rust Crypto Analysis",
            "POST",
            "/rust/analyze",
            expected_status=200,
            data={"symbols": ["BTC", "ETH"]}
        )
    
    def test_mobile_specific_endpoints(self):
        """Test mobile-specific endpoints"""
        print("📱 Testing Mobile-Specific Endpoints...")
        
        # Test mobile configuration
        self.test_endpoint(
            "Mobile Configuration",
            "GET",
            "/api/mobile/config",
            expected_status=200
        )
        
        # Test health endpoints
        self.test_endpoint(
            "Health Check",
            "GET",
            "/health/",
            expected_status=200
        )
        
        self.test_endpoint(
            "Liveness Probe",
            "GET",
            "/live/",
            expected_status=200
        )
        
        self.test_endpoint(
            "Readiness Probe",
            "GET",
            "/ready/",
            expected_status=200
        )
    
    def test_user_data_endpoints(self):
        """Test user data endpoints"""
        print("👤 Testing User Data Endpoints...")
        
        # Test user profile
        self.test_endpoint(
            "User Profile Data",
            "GET",
            "/user-profile/",
            expected_status=200
        )
        
        # Test signals
        self.test_endpoint(
            "Trading Signals",
            "GET",
            "/signals/",
            expected_status=200
        )
        
        # Test discussions
        self.test_endpoint(
            "Stock Discussions",
            "GET",
            "/discussions/",
            expected_status=200
        )
        
        # Test prices
        self.test_endpoint(
            "Price Data",
            "GET",
            "/prices/?symbols=BTC,ETH,AAPL",
            expected_status=200
        )
    
    def test_cors_headers(self):
        """Test CORS headers for React Native compatibility"""
        print("🌐 Testing CORS Headers...")
        
        try:
            response = requests.options(
                f"{self.base_url}/graphql/",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                },
                timeout=10
            )
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            }
            
            print(f"   CORS Headers: {cors_headers}")
            
        except Exception as e:
            print(f"   CORS Test Error: {e}")
    
    def run_all_tests(self):
        """Run all React Native endpoint tests"""
        print("🚀 Starting React Native Endpoint Tests...")
        print("=" * 60)
        
        # Run all test suites
        self.test_authentication_endpoints()
        self.test_graphql_endpoints()
        self.test_ai_endpoints()
        self.test_bank_integration_endpoints()
        self.test_market_data_endpoints()
        self.test_defi_endpoints()
        self.test_mobile_specific_endpoints()
        self.test_user_data_endpoints()
        self.test_cors_headers()
        
        # Print results
        self.print_results()
        
        return self.results
    
    def print_results(self):
        """Print test results"""
        print("\n" + "=" * 60)
        print("📊 REACT NATIVE ENDPOINT TEST RESULTS")
        print("=" * 60)
        
        success_rate = (self.results["passed"] / self.results["total_tests"]) * 100 if self.results["total_tests"] > 0 else 0
        
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Print detailed results
        print("\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        for endpoint in self.results["endpoints"]:
            status_emoji = "✅" if endpoint["success"] else "❌"
            print(f"{status_emoji} {endpoint['method']} {endpoint['path']}")
            print(f"   Status: {endpoint['actual_status']} (Expected: {endpoint['expected_status']})")
            print(f"   Response Time: {endpoint['response_time_ms']:.2f}ms")
            
            if endpoint["error"]:
                print(f"   Error: {endpoint['error']}")
            
            # Show sample response data
            if endpoint["response_data"] and isinstance(endpoint["response_data"], dict):
                if "status" in endpoint["response_data"]:
                    print(f"   Response Status: {endpoint['response_data']['status']}")
                if "data" in endpoint["response_data"]:
                    print(f"   Response Data: Available")
            
            print()
        
        # Summary
        print("=" * 60)
        if success_rate >= 95:
            print("🎉 EXCELLENT! React Native endpoints are ready!")
        elif success_rate >= 80:
            print("✅ GOOD! Most endpoints working, minor issues to fix.")
        elif success_rate >= 60:
            print("⚠️ FAIR! Several endpoints need attention.")
        else:
            print("❌ POOR! Many endpoints need fixing.")
        
        print(f"\n📱 React Native Compatibility: {'✅ Ready' if success_rate >= 90 else '⚠️ Needs Work'}")
        print(f"🏦 Bank Integration: {'✅ Ready' if self.check_bank_integration() else '⚠️ Needs Work'}")
        print(f"🤖 AI Features: {'✅ Ready' if self.check_ai_features() else '⚠️ Needs Work'}")
    
    def check_bank_integration(self) -> bool:
        """Check if bank integration endpoints are working"""
        bank_endpoints = [
            ep for ep in self.results["endpoints"] 
            if "sbloc" in ep["path"] or "yodlee" in ep["path"]
        ]
        return all(ep["success"] for ep in bank_endpoints)
    
    def check_ai_features(self) -> bool:
        """Check if AI feature endpoints are working"""
        ai_endpoints = [
            ep for ep in self.results["endpoints"] 
            if "ai-" in ep["path"] or "ml" in ep["path"]
        ]
        return all(ep["success"] for ep in ai_endpoints)
    
    def save_results(self, filename: str = "react_native_test_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Results saved to: {filename}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test React Native Endpoints")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL to test")
    parser.add_argument("--save", action="store_true", 
                       help="Save results to file")
    
    args = parser.parse_args()
    
    tester = ReactNativeEndpointTester(args.url)
    results = tester.run_all_tests()
    
    if args.save:
        tester.save_results()
    
    # Exit with appropriate code
    success_rate = (results["passed"] / results["total_tests"]) * 100 if results["total_tests"] > 0 else 0
    exit(0 if success_rate >= 90 else 1)

if __name__ == "__main__":
    main()
