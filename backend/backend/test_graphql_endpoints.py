#!/usr/bin/env python3
"""
Comprehensive GraphQL endpoint test script for RichesReach React Native app
Tests all endpoints used by the mobile app to ensure no 400, 404, or 500 errors
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
GRAPHQL_ENDPOINT = f"{BASE_URL}/graphql/"
AUTH_ENDPOINT = f"{BASE_URL}/api/auth/login/"

class GraphQLTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, response_code: int, error_msg: str = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "code": response_code,
            "error": error_msg
        }
        self.test_results.append(result)
        print(f"{status} {test_name} (HTTP {response_code})")
        if error_msg:
            print(f"   Error: {error_msg}")
    
    def make_graphql_request(self, query: str, variables: Dict = None) -> Dict[str, Any]:
        """Make a GraphQL request"""
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = self.session.post(
                GRAPHQL_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=10
            )
            return {
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "success": response.status_code < 400
            }
        except Exception as e:
            return {
                "status_code": 0,
                "data": None,
                "success": False,
                "error": str(e)
            }
    
    def test_authentication(self):
        """Test authentication endpoint"""
        print("\n🔐 Testing Authentication...")
        
        # Test login endpoint
        try:
            response = self.session.post(
                AUTH_ENDPOINT,
                json={"email": "test@example.com", "password": "test"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and data["token"]:
                    self.auth_token = data["token"]
                    self.log_test("Authentication Login", True, response.status_code)
                else:
                    self.log_test("Authentication Login", False, response.status_code, "No token in response")
            else:
                self.log_test("Authentication Login", False, response.status_code, response.text)
                
        except Exception as e:
            self.log_test("Authentication Login", False, 0, str(e))
    
    def test_basic_queries(self):
        """Test basic GraphQL queries"""
        print("\n📊 Testing Basic Queries...")
        
        # Test 1: Ping query
        query = """
        query {
            ping
        }
        """
        result = self.make_graphql_request(query)
        self.log_test("Ping Query", result["success"], result["status_code"], 
                     result.get("error") or (result["data"].get("errors")[0]["message"] if result["data"] and result["data"].get("errors") else None))
        
        # Test 2: Stocks query (main browse screen)
        query = """
        query {
            stocks {
                id
                symbol
                companyName
                sector
                currentPrice
                marketCap
                peRatio
                dividendYield
                beginnerFriendlyScore
                dividendScore
            }
        }
        """
        result = self.make_graphql_request(query)
        self.log_test("Stocks Query", result["success"], result["status_code"],
                     result.get("error") or (result["data"].get("errors")[0]["message"] if result["data"] and result["data"].get("errors") else None))
        
        # Test 3: Beginner Friendly Stocks query
        query = """
        query {
            beginnerFriendlyStocks {
                id
                symbol
                companyName
                sector
                currentPrice
                marketCap
                peRatio
                dividendYield
                beginnerFriendlyScore
                dividendScore
            }
        }
        """
        result = self.make_graphql_request(query)
        self.log_test("Beginner Friendly Stocks Query", result["success"], result["status_code"],
                     result.get("error") or (result["data"].get("errors")[0]["message"] if result["data"] and result["data"].get("errors") else None))
    
    def test_advanced_queries(self):
        """Test advanced GraphQL queries"""
        print("\n🔍 Testing Advanced Queries...")
        
        # Test 1: Rust Stock Analysis (Advanced Analysis screen)
        query = """
        query {
            rustStockAnalysis(symbol: "AAPL") {
                symbol
                beginnerFriendlyScore
                riskLevel
                recommendation
                technicalIndicators {
                    rsi
                    macd
                    macdSignal
                    macdHistogram
                    sma20
                    sma50
                    ema12
                    ema26
                    bollingerUpper
                    bollingerLower
                    bollingerMiddle
                }
                fundamentalAnalysis {
                    valuationScore
                    growthScore
                    stabilityScore
                    debtScore
                    dividendScore
                }
                reasoning
            }
        }
        """
        result = self.make_graphql_request(query)
        self.log_test("Rust Stock Analysis Query", result["success"], result["status_code"],
                     result.get("error") or (result["data"].get("errors")[0]["message"] if result["data"] and result["data"].get("errors") else None))
        
        # Test 2: Advanced Stock Screening
        query = """
        query {
            advancedStockScreening(sector: "Technology", minMarketCap: 1000000000) {
                id
                symbol
                companyName
                sector
                currentPrice
                marketCap
                peRatio
                dividendYield
                beginnerFriendlyScore
                dividendScore
            }
        }
        """
        result = self.make_graphql_request(query)
        self.log_test("Advanced Stock Screening Query", result["success"], result["status_code"],
                     result.get("error") or (result["data"].get("errors")[0]["message"] if result["data"] and result["data"].get("errors") else None))
        
        # Test 3: My Watchlist
        query = """
        query {
            myWatchlist {
                id
                symbol
                companyName
                currentPrice
                changePercent
            }
        }
        """
        result = self.make_graphql_request(query)
        self.log_test("My Watchlist Query", result["success"], result["status_code"],
                     result.get("error") or (result["data"].get("errors")[0]["message"] if result["data"] and result["data"].get("errors") else None))
    
    def test_crypto_queries(self):
        """Test crypto-related queries"""
        print("\n₿ Testing Crypto Queries...")
        
        # Test 1: Crypto Prices
        query = """
        query {
            cryptoPrices(symbols: ["BTC", "ETH"]) {
                symbol
                price
                change24h
                changePercent24h
            }
        }
        """
        result = self.make_graphql_request(query)
        self.log_test("Crypto Prices Query", result["success"], result["status_code"],
                     result.get("error") or (result["data"].get("errors")[0]["message"] if result["data"] and result["data"].get("errors") else None))
    
    def test_portfolio_queries(self):
        """Test portfolio-related queries"""
        print("\n💼 Testing Portfolio Queries...")
        
        # Test 1: Portfolio Analysis
        query = """
        query {
            portfolioAnalysis {
                totalValue
                totalGainLoss
                totalGainLossPercent
                dailyChange
                dailyChangePercent
            }
        }
        """
        result = self.make_graphql_request(query)
        self.log_test("Portfolio Analysis Query", result["success"], result["status_code"],
                     result.get("error") or (result["data"].get("errors")[0]["message"] if result["data"] and result["data"].get("errors") else None))
    
    def test_social_queries(self):
        """Test social features queries"""
        print("\n👥 Testing Social Queries...")
        
        # Test 1: Stock Discussions
        query = """
        query {
            stockDiscussions(stockSymbol: "AAPL", limit: 5) {
                id
                content
                createdAt
                user {
                    username
                }
                stock {
                    symbol
                }
            }
        }
        """
        result = self.make_graphql_request(query)
        self.log_test("Stock Discussions Query", result["success"], result["status_code"],
                     result.get("error") or (result["data"].get("errors")[0]["message"] if result["data"] and result["data"].get("errors") else None))
    
    def test_health_endpoints(self):
        """Test health and utility endpoints"""
        print("\n🏥 Testing Health Endpoints...")
        
        # Test 1: Health endpoint
        try:
            response = self.session.get(f"{BASE_URL}/health/", timeout=5)
            self.log_test("Health Endpoint", response.status_code == 200, response.status_code)
        except Exception as e:
            self.log_test("Health Endpoint", False, 0, str(e))
        
        # Test 2: Root endpoint
        try:
            response = self.session.get(f"{BASE_URL}/", timeout=5)
            self.log_test("Root Endpoint", response.status_code == 200, response.status_code)
        except Exception as e:
            self.log_test("Root Endpoint", False, 0, str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive GraphQL Endpoint Tests")
        print("=" * 60)
        
        # Test health endpoints first
        self.test_health_endpoints()
        
        # Test authentication
        self.test_authentication()
        
        # Test all GraphQL queries
        self.test_basic_queries()
        self.test_advanced_queries()
        self.test_crypto_queries()
        self.test_portfolio_queries()
        self.test_social_queries()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌" in result["status"]:
                    print(f"  - {result['test']} (HTTP {result['code']})")
                    if result.get("error"):
                        print(f"    Error: {result['error']}")
        
        print("\n" + "=" * 60)
        
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! Your GraphQL backend is ready for React Native!")
        else:
            print(f"⚠️  {failed_tests} tests failed. Please review the errors above.")
            sys.exit(1)

def main():
    """Main function"""
    tester = GraphQLTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
