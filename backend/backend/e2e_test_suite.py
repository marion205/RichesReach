#!/usr/bin/env python3
"""
End-to-End Testing Suite for RichesReach
Tests all UI mutations, database schemas, and GraphQL endpoints
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

    def test_authentication_mutations(self):
        """Test authentication-related mutations"""
        print("🔍 Testing Authentication Mutations...")
        
        # Test user registration
        register_mutation = {
            "query": """
            mutation RegisterUser($input: RegisterInput!) {
                register(input: $input) {
                    success
                    message
                    user {
                        id
                        email
                        firstName
                        lastName
                    }
                }
            }
            """,
            "variables": {
                "input": {
                    "email": "test@e2e.com",
                    "password": "testpassword123",
                    "firstName": "E2E",
                    "lastName": "Test"
                }
            }
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=register_mutation,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    register_result = data['data']['register']
                    if register_result.get('success'):
                        self.log_test("User Registration", True, "User registered successfully")
                    else:
                        self.log_test("User Registration", False, f"Registration failed: {register_result.get('message')}")
                else:
                    self.log_test("User Registration", False, f"Invalid response: {data}")
            else:
                self.log_test("User Registration", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("User Registration", False, f"Request failed: {str(e)}")

        # Test user login
        login_mutation = {
            "query": """
            mutation LoginUser($email: String!, $password: String!) {
                login(email: $email, password: $password) {
                    success
                    message
                    token
                    user {
                        id
                        email
                        firstName
                        lastName
                    }
                }
            }
            """,
            "variables": {
                "email": "test@e2e.com",
                "password": "testpassword123"
            }
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=login_mutation,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    login_result = data['data']['login']
                    if login_result.get('success'):
                        self.log_test("User Login", True, "User logged in successfully")
                        return login_result.get('token')
                    else:
                        self.log_test("User Login", False, f"Login failed: {login_result.get('message')}")
                else:
                    self.log_test("User Login", False, f"Invalid response: {data}")
            else:
                self.log_test("User Login", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("User Login", False, f"Request failed: {str(e)}")
        
        return None

    def test_alpaca_mutations(self, token=None):
        """Test Alpaca-related mutations"""
        print("🔍 Testing Alpaca Mutations...")
        
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Test create Alpaca account
        create_account_mutation = {
            "query": """
            mutation CreateAlpacaAccount(
                $firstName: String!
                $lastName: String!
                $emailAddress: String!
                $phoneNumber: String!
                $dob: String!
                $streetAddress: String!
                $city: String!
                $state: String!
                $postalCode: String!
                $country: String!
            ) {
                createAlpacaAccount(
                    firstName: $firstName
                    lastName: $lastName
                    emailAddress: $emailAddress
                    phoneNumber: $phoneNumber
                    dob: $dob
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
                        accountNumber
                    }
                }
            }
            """,
            "variables": {
                "firstName": "E2E",
                "lastName": "Test",
                "emailAddress": "e2e@test.com",
                "phoneNumber": "+15551234567",
                "dob": "1990-01-01",
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
                headers=headers,
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

    def test_stock_trading_mutations(self, token=None, alpaca_account_id=None):
        """Test stock trading mutations"""
        print("🔍 Testing Stock Trading Mutations...")
        
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Test place stock order
        place_order_mutation = {
            "query": """
            mutation PlaceStockOrder(
                $symbol: String!
                $qty: Float!
                $side: String!
                $type: String!
                $timeInForce: String
            ) {
                placeStockOrder(
                    symbol: $symbol
                    qty: $qty
                    side: $side
                    type: $type
                    timeInForce: $timeInForce
                ) {
                    success
                    message
                    orderId
                    order {
                        orderId
                        symbol
                        qty
                        side
                        status
                    }
                }
            }
            """,
            "variables": {
                "symbol": "AAPL",
                "qty": 1.0,
                "side": "buy",
                "type": "market",
                "timeInForce": "day"
            }
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=place_order_mutation,
                headers=headers,
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

    def test_crypto_trading_mutations(self, token=None):
        """Test crypto trading mutations"""
        print("🔍 Testing Crypto Trading Mutations...")
        
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Test create crypto account
        create_crypto_mutation = {
            "query": """
            mutation CreateCryptoAccount {
                createCryptoAccount {
                    success
                    message
                    account {
                        id
                        status
                        isApproved
                    }
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=create_crypto_mutation,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    crypto_result = data['data']['createCryptoAccount']
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

        # Test execute crypto trade
        execute_crypto_mutation = {
            "query": """
            mutation ExecuteCryptoTrade(
                $symbol: String!
                $qty: Float!
                $side: String!
                $type: String!
            ) {
                executeCryptoTrade(
                    symbol: $symbol
                    qty: $qty
                    side: $side
                    type: $type
                ) {
                    ok
                    trade {
                        id
                        symbol
                        qty
                        side
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
                "qty": 0.001,
                "side": "buy",
                "type": "market"
            }
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=execute_crypto_mutation,
                headers=headers,
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

    def test_database_schema_queries(self, token=None):
        """Test database schema queries"""
        print("🔍 Testing Database Schema Queries...")
        
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Test user queries
        user_query = {
            "query": """
            query GetUser {
                me {
                    id
                    email
                    firstName
                    lastName
                    isActive
                    dateJoined
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=user_query,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    user_data = data['data']['me']
                    if user_data:
                        self.log_test("User Query", True, "User data retrieved successfully")
                    else:
                        self.log_test("User Query", False, "No user data returned")
                else:
                    self.log_test("User Query", False, f"Invalid response: {data}")
            else:
                self.log_test("User Query", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("User Query", False, f"Request failed: {str(e)}")

        # Test Alpaca account queries
        alpaca_query = {
            "query": """
            query GetAlpacaAccount {
                myAlpacaAccount {
                    id
                    alpacaAccountId
                    status
                    accountNumber
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
                headers=headers,
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

        # Test crypto account queries
        crypto_query = {
            "query": """
            query GetCryptoAccount {
                alpacaCryptoAccount {
                    id
                    alpacaCryptoAccountId
                    status
                    isApproved
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=crypto_query,
                headers=headers,
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

    def test_portfolio_queries(self, token=None):
        """Test portfolio-related queries"""
        print("🔍 Testing Portfolio Queries...")
        
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Test portfolio query
        portfolio_query = {
            "query": """
            query GetPortfolio {
                portfolio {
                    totalValue
                    totalGain
                    totalGainPercent
                    positions {
                        symbol
                        quantity
                        currentPrice
                        marketValue
                        gain
                        gainPercent
                    }
                }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=portfolio_query,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    portfolio_data = data['data']['portfolio']
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

    def run_all_tests(self):
        """Run all E2E tests"""
        print("🚀 Starting Comprehensive E2E Testing Suite")
        print("=" * 60)
        
        # Test server connectivity
        if not self.test_server_connectivity():
            print("❌ Server not available. Stopping tests.")
            return self.results
        
        # Test GraphQL schema
        if not self.test_graphql_schema_introspection():
            print("❌ GraphQL schema not available. Stopping tests.")
            return self.results
        
        # Test authentication
        token = self.test_authentication_mutations()
        
        # Test Alpaca mutations
        alpaca_account_id = self.test_alpaca_mutations(token)
        
        # Test stock trading
        self.test_stock_trading_mutations(token, alpaca_account_id)
        
        # Test crypto trading
        self.test_crypto_trading_mutations(token)
        
        # Test database schema queries
        self.test_database_schema_queries(token)
        
        # Test portfolio queries
        self.test_portfolio_queries(token)
        
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
        else:
            print("⚠️  Some tests failed. Please review the issues above.")

if __name__ == "__main__":
    # Load environment variables
    load_env_secrets()
    
    # Run E2E tests
    test_suite = E2ETestSuite()
    results = test_suite.run_all_tests()
    test_suite.print_summary()
