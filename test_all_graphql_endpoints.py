#!/usr/bin/env python3
"""
Comprehensive GraphQL Endpoint Testing Script
Tests every GraphQL query and mutation to ensure they work correctly
"""

import requests
import json
import time
from typing import Dict, Any, List
import sys

# Configuration
BASE_URL = "http://192.168.1.236:8000"
GRAPHQL_ENDPOINT = f"{BASE_URL}/graphql/"

# Test user credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

class GraphQLTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def make_request(self, query: str, variables: Dict = None, use_auth: bool = True) -> Dict[str, Any]:
        """Make a GraphQL request"""
        headers = {
            "Content-Type": "application/json",
        }
        
        if use_auth and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = self.session.post(GRAPHQL_ENDPOINT, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return {"errors": [{"message": str(e)}]}
    
    def test_auth(self) -> bool:
        """Test authentication endpoints"""
        self.log("🔐 Testing Authentication Endpoints")
        
        # Test 1: Login
        login_query = """
        mutation TokenAuth($email: String!, $password: String!) {
            tokenAuth(email: $email, password: $password) {
                token
                refreshToken
                user {
                    id
                    email
                    username
                }
            }
        }
        """
        
        login_result = self.make_request(login_query, {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, use_auth=False)
        
        if "errors" in login_result:
            self.log(f"❌ Login failed: {login_result['errors']}", "ERROR")
            return False
            
        if not login_result.get("data", {}).get("tokenAuth", {}).get("token"):
            self.log("❌ No token received from login", "ERROR")
            return False
            
        self.auth_token = login_result["data"]["tokenAuth"]["token"]
        self.log("✅ Login successful, token obtained")
        
        # Test 2: GetMe
        me_query = """
        query GetMe {
            me {
                id
                email
                username
                firstName
                lastName
                isActive
                dateJoined
            }
        }
        """
        
        me_result = self.make_request(me_query)
        
        if "errors" in me_result:
            self.log(f"❌ GetMe failed: {me_result['errors']}", "ERROR")
            return False
            
        user_data = me_result.get("data", {}).get("me")
        if not user_data:
            self.log("❌ No user data received from GetMe", "ERROR")
            return False
            
        self.log(f"✅ GetMe successful - User: {user_data.get('email')} (ID: {user_data.get('id')})")
        self.test_results["auth"] = {"status": "PASS", "user_id": user_data.get("id")}
        return True
    
    def test_crypto_queries(self) -> bool:
        """Test crypto-related queries"""
        self.log("₿ Testing Crypto Queries")
        
        crypto_tests = [
            {
                "name": "CryptoPortfolio",
                "query": """
                query GetCryptoPortfolio {
                    cryptoPortfolio {
                        totalValue
                        totalReturn
                        totalReturnPercent
                        positions {
                            id
                            symbol
                            quantity
                            currentPrice
                            marketValue
                            unrealizedPnL
                            unrealizedPnLPercent
                        }
                    }
                }
                """
            },
            {
                "name": "CryptoAnalytics", 
                "query": """
                query GetCryptoAnalytics {
                    cryptoAnalytics {
                        totalTrades
                        winRate
                        avgReturn
                        bestPerformer {
                            symbol
                            return
                        }
                        worstPerformer {
                            symbol
                            return
                        }
                    }
                }
                """
            },
            {
                "name": "CryptoMLSignal",
                "query": """
                query GetCryptoMLSignal($symbol: String!) {
                    cryptoMlSignal(symbol: $symbol) {
                        symbol
                        predictionType
                        probability
                        confidence
                        targetPrice
                        stopLoss
                        explanation
                        createdAt
                    }
                }
                """,
                "variables": {"symbol": "BTC"}
            }
        ]
        
        all_passed = True
        for test in crypto_tests:
            result = self.make_request(test["query"], test.get("variables"))
            
            if "errors" in result:
                self.log(f"❌ {test['name']} failed: {result['errors']}", "ERROR")
                all_passed = False
            else:
                data = result.get("data", {})
                self.log(f"✅ {test['name']} successful - Data keys: {list(data.keys())}")
                
        self.test_results["crypto_queries"] = {"status": "PASS" if all_passed else "FAIL"}
        return all_passed
    
    def test_defi_queries(self) -> bool:
        """Test DeFi-related queries"""
        self.log("🏦 Testing DeFi Queries")
        
        defi_tests = [
            {
                "name": "TopYields",
                "query": """
                query GetTopYields($limit: Int, $chain: String) {
                    topYields(limit: $limit, chain: $chain) {
                        protocol
                        chain
                        apy
                        tvl
                        pool
                        token
                        risk
                    }
                }
                """,
                "variables": {"limit": 10, "chain": "ethereum"}
            },
            {
                "name": "AIYieldOptimizer",
                "query": """
                query GetAIYieldOptimizer($input: JSONString!) {
                    aiYieldOptimizer(input: $input) {
                        optimizedYield
                        strategy
                        riskScore
                        recommendations {
                            protocol
                            allocation
                            expectedReturn
                        }
                    }
                }
                """,
                "variables": {
                    "input": json.dumps({
                        "riskTolerance": "medium",
                        "investmentAmount": 10000,
                        "timeHorizon": "6months"
                    })
                }
            },
            {
                "name": "MyDeFiPositions",
                "query": """
                query GetMyDeFiPositions {
                    myDeFiPositions {
                        id
                        protocol
                        chain
                        pool
                        token
                        amount
                        apy
                        value
                        rewards
                    }
                }
                """
            }
        ]
        
        all_passed = True
        for test in defi_tests:
            result = self.make_request(test["query"], test.get("variables"))
            
            if "errors" in result:
                self.log(f"❌ {test['name']} failed: {result['errors']}", "ERROR")
                all_passed = False
            else:
                data = result.get("data", {})
                self.log(f"✅ {test['name']} successful - Data keys: {list(data.keys())}")
                
        self.test_results["defi_queries"] = {"status": "PASS" if all_passed else "FAIL"}
        return all_passed
    
    def test_stock_quotes(self) -> bool:
        """Test stock quote endpoints"""
        self.log("📈 Testing Stock Quote Endpoints")
        
        # Test direct REST API first
        try:
            response = self.session.get(f"{BASE_URL}/api/market/quotes?symbols=AAPL,MSFT,TSLA", timeout=10)
            if response.status_code == 200:
                quotes_data = response.json()
                self.log(f"✅ REST Quotes API working - {len(quotes_data.get('quotes', []))} quotes received")
            else:
                self.log(f"❌ REST Quotes API failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ REST Quotes API error: {str(e)}", "ERROR")
            return False
        
        # Test GraphQL stock queries
        stock_tests = [
            {
                "name": "StockQuotes",
                "query": """
                query GetStockQuotes($symbols: [String!]!) {
                    stockQuotes(symbols: $symbols) {
                        symbol
                        price
                        change
                        changePercent
                        volume
                        marketCap
                    }
                }
                """,
                "variables": {"symbols": ["AAPL", "MSFT", "TSLA"]}
            }
        ]
        
        all_passed = True
        for test in stock_tests:
            result = self.make_request(test["query"], test.get("variables"))
            
            if "errors" in result:
                self.log(f"❌ {test['name']} failed: {result['errors']}", "ERROR")
                all_passed = False
            else:
                data = result.get("data", {})
                self.log(f"✅ {test['name']} successful - Data keys: {list(data.keys())}")
                
        self.test_results["stock_quotes"] = {"status": "PASS" if all_passed else "FAIL"}
        return all_passed
    
    def test_portfolio_queries(self) -> bool:
        """Test portfolio-related queries"""
        self.log("💼 Testing Portfolio Queries")
        
        portfolio_tests = [
            {
                "name": "MyPortfolios",
                "query": """
                query GetMyPortfolios {
                    myPortfolios {
                        id
                        name
                        totalValue
                        totalReturn
                        totalReturnPercent
                        positions {
                            id
                            symbol
                            quantity
                            currentPrice
                            marketValue
                        }
                    }
                }
                """
            },
            {
                "name": "PortfolioPerformance",
                "query": """
                query GetPortfolioPerformance($portfolioId: ID!) {
                    portfolioPerformance(portfolioId: $portfolioId) {
                        totalReturn
                        totalReturnPercent
                        dailyReturns
                        monthlyReturns
                        sharpeRatio
                        maxDrawdown
                    }
                }
                """,
                "variables": {"portfolioId": "1"}
            }
        ]
        
        all_passed = True
        for test in portfolio_tests:
            result = self.make_request(test["query"], test.get("variables"))
            
            if "errors" in result:
                self.log(f"❌ {test['name']} failed: {result['errors']}", "ERROR")
                all_passed = False
            else:
                data = result.get("data", {})
                self.log(f"✅ {test['name']} successful - Data keys: {list(data.keys())}")
                
        self.test_results["portfolio_queries"] = {"status": "PASS" if all_passed else "FAIL"}
        return all_passed
    
    def test_mutations(self) -> bool:
        """Test mutations"""
        self.log("🔄 Testing Mutations")
        
        mutation_tests = [
            {
                "name": "ExecuteCryptoTrade",
                "query": """
                mutation ExecuteCryptoTrade($symbol: String!, $side: String!, $quantity: Float!, $orderType: String!) {
                    executeCryptoTrade(symbol: $symbol, side: $side, quantity: $quantity, orderType: $orderType) {
                        ok
                        trade {
                            id
                            symbol
                            side
                            quantity
                            orderType
                            status
                        }
                        error {
                            code
                            message
                        }
                    }
                }
                """,
                "variables": {
                    "symbol": "BTC",
                    "side": "BUY", 
                    "quantity": 0.001,
                    "orderType": "MARKET"
                }
            },
            {
                "name": "GenerateMLPrediction",
                "query": """
                mutation GenerateMLPrediction($symbol: String!) {
                    generateMlPrediction(symbol: $symbol) {
                        success
                        predictionId
                        probability
                        direction
                        targetPrice
                        explanation
                        message
                    }
                }
                """,
                "variables": {"symbol": "ETH"}
            }
        ]
        
        all_passed = True
        for test in mutation_tests:
            result = self.make_request(test["query"], test.get("variables"))
            
            if "errors" in result:
                self.log(f"❌ {test['name']} failed: {result['errors']}", "ERROR")
                all_passed = False
            else:
                data = result.get("data", {})
                self.log(f"✅ {test['name']} successful - Data keys: {list(data.keys())}")
                
        self.test_results["mutations"] = {"status": "PASS" if all_passed else "FAIL"}
        return all_passed
    
    def test_schema_introspection(self) -> bool:
        """Test GraphQL schema introspection"""
        self.log("🔍 Testing Schema Introspection")
        
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                queryType {
                    name
                    fields {
                        name
                        description
                        type {
                            name
                            kind
                        }
                    }
                }
                mutationType {
                    name
                    fields {
                        name
                        description
                        type {
                            name
                            kind
                        }
                    }
                }
            }
        }
        """
        
        result = self.make_request(introspection_query)
        
        if "errors" in result:
            self.log(f"❌ Schema introspection failed: {result['errors']}", "ERROR")
            return False
            
        schema_data = result.get("data", {}).get("__schema", {})
        query_fields = len(schema_data.get("queryType", {}).get("fields", []))
        mutation_fields = len(schema_data.get("mutationType", {}).get("fields", []))
        
        self.log(f"✅ Schema introspection successful - {query_fields} queries, {mutation_fields} mutations")
        self.test_results["schema_introspection"] = {"status": "PASS", "queries": query_fields, "mutations": mutation_fields}
        return True
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        self.log("🚀 Starting Comprehensive GraphQL Testing")
        self.log("=" * 60)
        
        start_time = time.time()
        
        # Run all test suites
        test_suites = [
            ("Authentication", self.test_auth),
            ("Schema Introspection", self.test_schema_introspection),
            ("Crypto Queries", self.test_crypto_queries),
            ("DeFi Queries", self.test_defi_queries),
            ("Stock Quotes", self.test_stock_quotes),
            ("Portfolio Queries", self.test_portfolio_queries),
            ("Mutations", self.test_mutations),
        ]
        
        passed_tests = 0
        total_tests = len(test_suites)
        
        for suite_name, test_func in test_suites:
            try:
                if test_func():
                    passed_tests += 1
                else:
                    self.log(f"❌ {suite_name} test suite failed", "ERROR")
            except Exception as e:
                self.log(f"❌ {suite_name} test suite crashed: {str(e)}", "ERROR")
                self.test_results[suite_name.lower().replace(" ", "_")] = {"status": "CRASH", "error": str(e)}
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Summary
        self.log("=" * 60)
        self.log(f"🏁 Testing Complete - {passed_tests}/{total_tests} test suites passed")
        self.log(f"⏱️  Total time: {duration:.2f} seconds")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED! All GraphQL endpoints are working correctly.", "SUCCESS")
        else:
            self.log(f"⚠️  {total_tests - passed_tests} test suites failed. Check the logs above.", "WARNING")
        
        return {
            "summary": {
                "passed": passed_tests,
                "total": total_tests,
                "duration": duration,
                "success_rate": (passed_tests / total_tests) * 100
            },
            "results": self.test_results
        }

def main():
    """Main function"""
    print("GraphQL Comprehensive Testing Suite")
    print("=" * 60)
    
    tester = GraphQLTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open("graphql_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: graphql_test_results.json")
    
    # Exit with appropriate code
    if results["summary"]["passed"] == results["summary"]["total"]:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Some tests failed

if __name__ == "__main__":
    main()
