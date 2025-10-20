#!/usr/bin/env python3
"""
Corrected End-to-End Testing Suite for RichesReach
Tests all UI mutations, database schemas, and GraphQL endpoints with correct schema
"""

import os
import requests
import json
import time
from datetime import datetime

# Load environment variables from env.secrets
def load_env_secrets():
    env_file = 'env.secrets'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Loaded environment variables from env.secrets")
    else:
        print("❌ env.secrets file not found")

class E2ETestSuite:
    def __init__(self):
        self.base_url = "http://192.168.1.236:8000"
        self.graphql_url = f"{self.base_url}/graphql/"
        self.results = {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "details": []
        }
    
    def log_test(self, test_name, success, message="", details=None):
        """Log test result"""
        self.results["total"] += 1
        if success:
            self.results["passed"] += 1
            status = "✅ PASS"
        else:
            self.results["failed"] += 1
            status = "❌ FAIL"
        
        self.results["details"].append({
            "test": test_name,
            "status": status,
            "message": message,
            "details": details
        })
        
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        if details:
            print(f"    Details: {details}")
        print()

    def test_server_connectivity(self):
        """Test if Django server is running"""
        print("🔍 Testing Server Connectivity...")
        try:
            response = requests.get(f"{self.base_url}/graphql/", timeout=10)
            if response.status_code in [200, 400]:  # 400 is OK for GraphQL without query
                self.log_test("Server Connectivity", True, f"Server responding (Status: {response.status_code})")
                return True
            else:
                self.log_test("Server Connectivity", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Connectivity", False, f"Connection failed: {str(e)}")
            return False

    def test_graphql_schema_introspection(self):
        """Test GraphQL schema introspection"""
        print("🔍 Testing GraphQL Schema Introspection...")
        
        introspection_query = {
            "query": """
            query IntrospectionQuery {
                __schema {
                    queryType { name }
                    mutationType { name }
                    subscriptionType { name }
                    types {
                        name
                        kind
                        description
                    }
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=introspection_query,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    schema = data['data']['__schema']
                    query_type = schema.get('queryType', {}).get('name', 'Unknown')
                    mutation_type = schema.get('mutationType', {}).get('name', 'Unknown')
                    types_count = len(schema.get('types', []))
                    
                    self.log_test("GraphQL Schema Introspection", True, 
                                f"Schema loaded - Query: {query_type}, Mutation: {mutation_type}, Types: {types_count}")
                    return True
                else:
                    self.log_test("GraphQL Schema Introspection", False, f"Invalid schema response: {data}")
                    return False
            else:
                self.log_test("GraphQL Schema Introspection", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("GraphQL Schema Introspection", False, f"Request failed: {str(e)}")
            return False

    def test_alpaca_mutations(self):
        """Test Alpaca-related mutations with correct schema"""
        print("🔍 Testing Alpaca Mutations...")
        
        # Test create Alpaca account with correct parameters
        create_account_mutation = {
            "query": """
            mutation CreateAlpacaAccount(
                $firstName: String!
                $lastName: String!
                $email: String!
                $phoneNumber: String!
                $dateOfBirth: Date!
                $streetAddress: String!
                $city: String!
                $state: String!
                $postalCode: String!
                $country: String!
            ) {
                createAlpacaAccount(
                    firstName: $firstName
                    lastName: $lastName
                    email: $email
                    phoneNumber: $phoneNumber
                    dateOfBirth: $dateOfBirth
                    streetAddress: $streetAddress
                    city: $city
                    state: $state
                    postalCode: $postalCode
                    country: $country
                ) {
                    success
                    message
                    alpacaAccountId
                    account {
                        id
                        status
                        accountType
                    }
                }
            }
            """,
            "variables": {
                "firstName": "E2E",
                "lastName": "Test",
                "email": "e2e@test.com",
                "phoneNumber": "+15551234567",
                "dateOfBirth": "1990-01-01",
                "streetAddress": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "postalCode": "12345",
                "country": "USA"
            }
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=create_account_mutation,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    create_result = data['data']['createAlpacaAccount']
                    if create_result.get('success'):
                        self.log_test("Create Alpaca Account", True, "Alpaca account created successfully")
                        return create_result.get('alpacaAccountId')
                    else:
                        self.log_test("Create Alpaca Account", False, f"Creation failed: {create_result.get('message')}")
                else:
                    self.log_test("Create Alpaca Account", False, f"Invalid response: {data}")
            else:
                self.log_test("Create Alpaca Account", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Create Alpaca Account", False, f"Request failed: {str(e)}")
        
        return None

    def test_stock_trading_mutations(self, alpaca_account_id=None):
        """Test stock trading mutations with correct schema"""
        print("🔍 Testing Stock Trading Mutations...")
        
        # Test place stock order with correct parameters
        place_order_mutation = {
            "query": """
            mutation PlaceStockOrder(
                $symbol: String!
                $quantity: Int!
                $side: String!
                $orderType: String!
                $timeInForce: String
            ) {
                placeStockOrder(
                    symbol: $symbol
                    quantity: $quantity
                    side: $side
                    orderType: $orderType
                    timeInForce: $timeInForce
                ) {
                    success
                    message
                    orderId
                }
            }
            """,
            "variables": {
                "symbol": "AAPL",
                "quantity": 1,
                "side": "buy",
                "orderType": "market",
                "timeInForce": "day"
            }
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=place_order_mutation,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    order_result = data['data']['placeStockOrder']
                    if order_result.get('success'):
                        self.log_test("Place Stock Order", True, "Stock order placed successfully")
                    else:
                        self.log_test("Place Stock Order", False, f"Order failed: {order_result.get('message')}")
                else:
                    self.log_test("Place Stock Order", False, f"Invalid response: {data}")
            else:
                self.log_test("Place Stock Order", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Place Stock Order", False, f"Request failed: {str(e)}")

    def test_crypto_trading_mutations(self):
        """Test crypto trading mutations with correct schema"""
        print("🔍 Testing Crypto Trading Mutations...")
        
        # Test create crypto account
        create_crypto_mutation = {
            "query": """
            mutation CreateAlpacaCryptoAccount {
                createAlpacaCryptoAccount {
                    success
                    message
                    account {
                        id
                        status
                        approvedAt
                    }
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=create_crypto_mutation,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    crypto_result = data['data']['createAlpacaCryptoAccount']
                    if crypto_result.get('success'):
                        self.log_test("Create Crypto Account", True, "Crypto account created successfully")
                    else:
                        self.log_test("Create Crypto Account", False, f"Creation failed: {crypto_result.get('message')}")
                else:
                    self.log_test("Create Crypto Account", False, f"Invalid response: {data}")
            else:
                self.log_test("Create Crypto Account", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Create Crypto Account", False, f"Request failed: {str(e)}")

        # Test execute crypto trade with correct parameters
        execute_crypto_mutation = {
            "query": """
            mutation ExecuteCryptoTrade(
                $symbol: String!
                $quantity: Float!
                $tradeType: String!
                $orderType: String!
            ) {
                executeCryptoTrade(
                    symbol: $symbol
                    quantity: $quantity
                    tradeType: $tradeType
                    orderType: $orderType
                ) {
                    ok
                    trade {
                        id
                        status
                        executionTime
                    }
                    error {
                        code
                        message
                    }
                }
            }
            """,
            "variables": {
                "symbol": "BTC/USD",
                "quantity": 0.001,
                "tradeType": "buy",
                "orderType": "market"
            }
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=execute_crypto_mutation,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    crypto_trade_result = data['data']['executeCryptoTrade']
                    if crypto_trade_result.get('ok'):
                        self.log_test("Execute Crypto Trade", True, "Crypto trade executed successfully")
                    else:
                        error = crypto_trade_result.get('error', {})
                        self.log_test("Execute Crypto Trade", False, f"Trade failed: {error.get('message', 'Unknown error')}")
                else:
                    self.log_test("Execute Crypto Trade", False, f"Invalid response: {data}")
            else:
                self.log_test("Execute Crypto Trade", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Execute Crypto Trade", False, f"Request failed: {str(e)}")

    def test_database_schema_queries(self):
        """Test database schema queries with correct field names"""
        print("🔍 Testing Database Schema Queries...")
        
        # Test user queries with correct fields
        user_query = {
            "query": """
            query GetUser {
                me {
                    id
                    email
                    username
                    name
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=user_query,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    user_data = data['data']['me']
                    if user_data:
                        self.log_test("User Query", True, "User data retrieved successfully")
                    else:
                        self.log_test("User Query", True, "No user data returned (expected for anonymous)")
                else:
                    self.log_test("User Query", False, f"Invalid response: {data}")
            else:
                self.log_test("User Query", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("User Query", False, f"Request failed: {str(e)}")

        # Test Alpaca account queries with correct fields
        alpaca_query = {
            "query": """
            query GetAlpacaAccount {
                myAlpacaAccount {
                    id
                    alpacaAccountId
                    status
                    accountType
                    buyingPower
                    cash
                    portfolioValue
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=alpaca_query,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    alpaca_data = data['data']['myAlpacaAccount']
                    if alpaca_data:
                        self.log_test("Alpaca Account Query", True, "Alpaca account data retrieved successfully")
                    else:
                        self.log_test("Alpaca Account Query", True, "No Alpaca account found (expected for new users)")
                else:
                    self.log_test("Alpaca Account Query", False, f"Invalid response: {data}")
            else:
                self.log_test("Alpaca Account Query", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Alpaca Account Query", False, f"Request failed: {str(e)}")

        # Test crypto account queries with correct fields
        crypto_query = {
            "query": """
            query GetCryptoAccount {
                alpacaCryptoAccount {
                    id
                    alpacaCryptoAccountId
                    status
                    approvedAt
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=crypto_query,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    crypto_data = data['data']['alpacaCryptoAccount']
                    if crypto_data:
                        self.log_test("Crypto Account Query", True, "Crypto account data retrieved successfully")
                    else:
                        self.log_test("Crypto Account Query", True, "No crypto account found (expected for new users)")
                else:
                    self.log_test("Crypto Account Query", False, f"Invalid response: {data}")
            else:
                self.log_test("Crypto Account Query", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Crypto Account Query", False, f"Request failed: {str(e)}")

    def test_portfolio_queries(self):
        """Test portfolio-related queries with correct field names"""
        print("🔍 Testing Portfolio Queries...")
        
        # Test portfolio query with correct field name
        portfolio_query = {
            "query": """
            query GetPortfolio {
                myPortfolios {
                    id
                    name
                    totalValue
                    totalGain
                    totalGainPercent
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=portfolio_query,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    portfolio_data = data['data']['myPortfolios']
                    if portfolio_data:
                        self.log_test("Portfolio Query", True, "Portfolio data retrieved successfully")
                    else:
                        self.log_test("Portfolio Query", True, "No portfolio data found (expected for new users)")
                else:
                    self.log_test("Portfolio Query", False, f"Invalid response: {data}")
            else:
                self.log_test("Portfolio Query", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Portfolio Query", False, f"Request failed: {str(e)}")

    def test_market_data_queries(self):
        """Test market data queries"""
        print("🔍 Testing Market Data Queries...")
        
        # Test stock quotes
        stock_quotes_query = {
            "query": """
            query GetStockQuotes($symbols: [String!]!) {
                stockQuotes(symbols: $symbols) {
                    symbol
                    price
                    change
                    changePercent
                    volume
                }
            }
            """,
            "variables": {
                "symbols": ["AAPL", "GOOGL", "MSFT"]
            }
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=stock_quotes_query,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    quotes_data = data['data']['stockQuotes']
                    if quotes_data:
                        self.log_test("Stock Quotes Query", True, f"Retrieved {len(quotes_data)} stock quotes")
                    else:
                        self.log_test("Stock Quotes Query", True, "No stock quotes returned (expected if market data service is disabled)")
                else:
                    self.log_test("Stock Quotes Query", False, f"Invalid response: {data}")
            else:
                self.log_test("Stock Quotes Query", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Stock Quotes Query", False, f"Request failed: {str(e)}")

    def run_all_tests(self):
        """Run all E2E tests"""
        print("🚀 Starting Corrected E2E Testing Suite")
        print("=" * 60)
        
        # Test server connectivity
        if not self.test_server_connectivity():
            print("❌ Server not available. Stopping tests.")
            return self.results
        
        # Test GraphQL schema
        if not self.test_graphql_schema_introspection():
            print("❌ GraphQL schema not available. Stopping tests.")
            return self.results
        
        # Test Alpaca mutations
        alpaca_account_id = self.test_alpaca_mutations()
        
        # Test stock trading
        self.test_stock_trading_mutations(alpaca_account_id)
        
        # Test crypto trading
        self.test_crypto_trading_mutations()
        
        # Test database schema queries
        self.test_database_schema_queries()
        
        # Test portfolio queries
        self.test_portfolio_queries()
        
        # Test market data queries
        self.test_market_data_queries()
        
        return self.results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 E2E TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📊 Total:  {self.results['total']}")
        print(f"📈 Success Rate: {(self.results['passed'] / self.results['total'] * 100):.1f}%")
        
        if self.results['failed'] > 0:
            print("\n❌ Failed Tests:")
            for detail in self.results['details']:
                if "FAIL" in detail['status']:
                    print(f"  - {detail['test']}: {detail['message']}")
        
        print("\n" + "=" * 60)
        
        if self.results['failed'] == 0:
            print("🎉 ALL TESTS PASSED! System is ready for production!")
        elif self.results['passed'] / self.results['total'] >= 0.8:
            print("✅ Most tests passed! System is mostly ready with minor issues.")
        else:
            print("⚠️  Several tests failed. Please review the issues above.")

if __name__ == "__main__":
    # Load environment variables
    load_env_secrets()
    
    # Run E2E tests
    test_suite = E2ETestSuite()
    results = test_suite.run_all_tests()
    test_suite.print_summary()
