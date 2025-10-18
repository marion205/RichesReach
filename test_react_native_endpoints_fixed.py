#!/usr/bin/env python3
"""
Fixed GraphQL Endpoint Testing for React Native App
Uses correct field names and query names from the actual schema
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://192.168.1.236:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

class GraphQLTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "ReactNative-Test/1.0"
        })
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def make_request(self, query, variables=None, use_auth=True):
        """Make a GraphQL request"""
        headers = {}
        if use_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = self.session.post(GRAPHQL_URL, json=payload, headers=headers, timeout=10)
            return response.json(), response.status_code
        except Exception as e:
            self.log(f"Request failed: {e}", "ERROR")
            return None, 0
    
    def test_health_check(self):
        """Test basic health check"""
        self.log("Testing health check...")
        try:
            response = requests.get(f"{BASE_URL}/healthz", timeout=5)
            if response.status_code == 200:
                self.log("✅ Health check passed")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Health check error: {e}", "ERROR")
            return False
    
    def test_authentication(self):
        """Test JWT authentication"""
        self.log("Testing authentication...")
        
        auth_query = """
        mutation TokenAuth($email: String!, $password: String!) {
            tokenAuth(email: $email, password: $password) {
                token
            }
        }
        """
        
        data, status = self.make_request(auth_query, {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, use_auth=False)
        
        if data and "data" in data and data["data"]["tokenAuth"]["token"]:
            self.token = data["data"]["tokenAuth"]["token"]
            self.log(f"✅ Authentication successful (token length: {len(self.token)})")
            return True
        else:
            self.log(f"❌ Authentication failed: {data}", "ERROR")
            # Try to get a token directly from Django
            try:
                import subprocess
                result = subprocess.run([
                    "python3", "manage.py", "shell", "-c",
                    f"""
from django.contrib.auth import get_user_model
from graphql_jwt.shortcuts import get_token
U = get_user_model()
user = U.objects.get(email='{TEST_EMAIL}')
token = get_token(user)
print(token)
"""
                ], cwd="/Users/marioncollins/RichesReach/backend/backend/backend/backend", 
                capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout.strip():
                    self.token = result.stdout.strip()
                    self.log(f"✅ Got token via Django shell (token length: {len(self.token)})")
                    return True
            except Exception as e:
                self.log(f"❌ Django shell token generation failed: {e}", "ERROR")
            
            return False
    
    def test_user_profile(self):
        """Test user profile queries with correct field names"""
        self.log("Testing user profile queries...")
        
        # Test 'me' query with correct field names
        me_query = """
        query {
            me {
                id
                email
                username
                name
                profilePic
                hasPremiumAccess
                subscriptionTier
            }
        }
        """
        
        data, status = self.make_request(me_query)
        if data and "data" in data and data["data"]["me"]:
            self.log("✅ 'me' query successful")
            user = data["data"]["me"]
            self.log(f"   User: {user.get('email', 'N/A')} ({user.get('username', 'N/A')})")
            self.log(f"   Name: {user.get('name', 'N/A')}")
            self.log(f"   Premium: {user.get('hasPremiumAccess', False)}")
        else:
            self.log(f"❌ 'me' query failed: {data}", "ERROR")
            return False
        return True
    
    def test_watchlist_operations(self):
        """Test watchlist operations"""
        self.log("Testing watchlist operations...")
        
        # Test myWatchlist query
        watchlist_query = """
        query {
            myWatchlist {
                id
                stock {
                    symbol
                    companyName
                }
                notes
                addedAt
            }
        }
        """
        
        data, status = self.make_request(watchlist_query)
        if data and "data" in data:
            items = data["data"]["myWatchlist"]
            self.log(f"✅ myWatchlist query successful ({len(items)} items)")
            for item in items[:3]:  # Show first 3 items
                self.log(f"   - {item['stock']['symbol']}: {item['stock']['companyName']}")
        else:
            self.log(f"❌ myWatchlist query failed: {data}", "ERROR")
            return False
        
        # Test addToWatchlist mutation
        add_mutation = """
        mutation AddToWatchlist($symbol: String!, $companyName: String, $notes: String) {
            addToWatchlist(symbol: $symbol, companyName: $companyName, notes: $notes) {
                success
                message
            }
        }
        """
        
        data, status = self.make_request(add_mutation, {
            "symbol": "GOOGL",
            "companyName": "Alphabet Inc.",
            "notes": "Test from React Native endpoint test"
        })
        
        if data and "data" in data and data["data"]["addToWatchlist"]["success"]:
            self.log("✅ addToWatchlist mutation successful")
            self.log(f"   Message: {data['data']['addToWatchlist']['message']}")
        else:
            self.log(f"❌ addToWatchlist mutation failed: {data}", "ERROR")
            return False
        
        return True
    
    def test_stock_queries(self):
        """Test stock-related queries with correct names"""
        self.log("Testing stock queries...")
        
        # Test stocks query (not searchStocks)
        stock_query = """
        query {
            stocks {
                symbol
                companyName
                currentPrice
                changePercent
            }
        }
        """
        
        data, status = self.make_request(stock_query)
        if data and "data" in data:
            stocks = data["data"]["stocks"]
            self.log(f"✅ stocks query successful ({len(stocks)} results)")
            for stock in stocks[:3]:  # Show first 3 results
                self.log(f"   - {stock['symbol']}: {stock['companyName']}")
        else:
            self.log(f"❌ stocks query failed: {data}", "ERROR")
            return False
        
        return True
    
    def test_portfolio_queries(self):
        """Test portfolio-related queries with correct field names"""
        self.log("Testing portfolio queries...")
        
        # Test myPortfolios query with correct field names
        portfolio_query = """
        query {
            myPortfolios {
                totalValue
                totalReturn
                holdings {
                    symbol
                    shares
                    currentValue
                }
            }
        }
        """
        
        data, status = self.make_request(portfolio_query)
        if data and "data" in data:
            portfolios = data["data"]["myPortfolios"]
            self.log(f"✅ myPortfolios query successful ({len(portfolios)} portfolios)")
        else:
            self.log(f"❌ myPortfolios query failed: {data}", "ERROR")
            return False
        
        return True
    
    def test_ai_recommendations(self):
        """Test AI recommendation queries with correct field names"""
        self.log("Testing AI recommendation queries...")
        
        # Test AI recommendations with correct field names
        ai_query = """
        query {
            aiRecommendations {
                buyRecommendations {
                    symbol
                    confidence
                    reasoning
                }
                sellRecommendations {
                    symbol
                    confidence
                    reasoning
                }
            }
        }
        """
        
        data, status = self.make_request(ai_query)
        if data and "data" in data:
            recommendations = data["data"]["aiRecommendations"]
            buy_recs = recommendations.get("buyRecommendations", [])
            sell_recs = recommendations.get("sellRecommendations", [])
            self.log(f"✅ aiRecommendations query successful")
            self.log(f"   Buy recommendations: {len(buy_recs)}")
            self.log(f"   Sell recommendations: {len(sell_recs)}")
        else:
            self.log(f"❌ aiRecommendations query failed: {data}", "ERROR")
            return False
        
        return True
    
    def test_market_data(self):
        """Test market data queries with correct names"""
        self.log("Testing market data queries...")
        
        # Test marketData query (not marketOverview)
        market_query = """
        query {
            marketData {
                symbol
                price
                change
                changePercent
                volume
            }
        }
        """
        
        data, status = self.make_request(market_query)
        if data and "data" in data:
            market_data = data["data"]["marketData"]
            self.log(f"✅ marketData query successful ({len(market_data)} symbols)")
            for item in market_data[:3]:  # Show first 3 items
                self.log(f"   - {item['symbol']}: ${item.get('price', 'N/A')}")
        else:
            self.log(f"❌ marketData query failed: {data}", "ERROR")
            return False
        
        return True
    
    def test_schema_introspection(self):
        """Test GraphQL schema introspection"""
        self.log("Testing schema introspection...")
        
        # Test basic schema query
        schema_query = """
        query {
            __schema {
                queryType {
                    fields {
                        name
                    }
                }
                mutationType {
                    fields {
                        name
                    }
                }
            }
        }
        """
        
        data, status = self.make_request(schema_query, use_auth=False)
        if data and "data" in data:
            schema = data["data"]["__schema"]
            queries = [field["name"] for field in schema["queryType"]["fields"]]
            mutations = [field["name"] for field in schema["mutationType"]["fields"]]
            
            self.log("✅ Schema introspection successful")
            self.log(f"   Available queries: {len(queries)}")
            self.log(f"   Available mutations: {len(mutations)}")
            
            # Check for key endpoints
            key_queries = ["me", "myWatchlist", "stocks", "myPortfolios", "marketData", "aiRecommendations"]
            key_mutations = ["tokenAuth", "addToWatchlist", "removeFromWatchlist"]
            
            missing_queries = [q for q in key_queries if q not in queries]
            missing_mutations = [m for m in key_mutations if m not in mutations]
            
            if missing_queries:
                self.log(f"⚠️  Missing queries: {missing_queries}", "WARNING")
            if missing_mutations:
                self.log(f"⚠️  Missing mutations: {missing_mutations}", "WARNING")
            
            return True
        else:
            self.log(f"❌ Schema introspection failed: {data}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("🧪 Starting FIXED GraphQL endpoint testing for React Native app")
        self.log("=" * 70)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Authentication", self.test_authentication),
            ("Schema Introspection", self.test_schema_introspection),
            ("User Profile", self.test_user_profile),
            ("Watchlist Operations", self.test_watchlist_operations),
            ("Stock Queries", self.test_stock_queries),
            ("Portfolio Queries", self.test_portfolio_queries),
            ("AI Recommendations", self.test_ai_recommendations),
            ("Market Data", self.test_market_data),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                self.log(f"\n--- {test_name} ---")
                result = test_func()
                results[test_name] = result
            except Exception as e:
                self.log(f"❌ {test_name} failed with exception: {e}", "ERROR")
                results[test_name] = False
        
        # Summary
        self.log("\n" + "=" * 70)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 70)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status}: {test_name}")
        
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! React Native app should work with local server.")
        else:
            self.log("⚠️  Some tests failed. Check the logs above for details.")
        
        return results

if __name__ == "__main__":
    tester = GraphQLTester()
    results = tester.run_all_tests()
    sys.exit(0 if all(results.values()) else 1)
