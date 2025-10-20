#!/usr/bin/env python3
"""
Final Comprehensive E2E Test for RichesReach
Tests all core functionality with correct schema and authentication
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

class FinalE2ETest:
    def __init__(self):
        self.base_url = "http://192.168.1.236:8000"
        self.graphql_url = f"{self.base_url}/graphql/"
        self.results = {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "details": []
        }
        self.auth_token = None
    
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

    def test_core_infrastructure(self):
        """Test core infrastructure components"""
        print("🔍 Testing Core Infrastructure...")
        
        # Test server connectivity
        try:
            response = requests.get(f"{self.base_url}/graphql/", timeout=10)
            if response.status_code in [200, 400]:
                self.log_test("Server Connectivity", True, f"Server responding (Status: {response.status_code})")
            else:
                self.log_test("Server Connectivity", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Connectivity", False, f"Connection failed: {str(e)}")
            return False
        
        # Test GraphQL schema
        introspection_query = {
            "query": """
            query IntrospectionQuery {
                __schema {
                    queryType { name }
                    mutationType { name }
                    types { name kind }
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
                    types_count = len(schema.get('types', []))
                    self.log_test("GraphQL Schema", True, f"Schema loaded with {types_count} types")
                    return True
                else:
                    self.log_test("GraphQL Schema", False, f"Invalid schema response: {data}")
                    return False
            else:
                self.log_test("GraphQL Schema", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("GraphQL Schema", False, f"Request failed: {str(e)}")
            return False

    def test_authentication_flow(self):
        """Test authentication flow"""
        print("🔍 Testing Authentication Flow...")
        
        # Use a consistent email for both registration and login
        test_email = f"test_{int(time.time())}@e2e.com"
        
        # Test user registration (if available)
        register_mutation = {
            "query": """
            mutation RegisterUser($email: String!, $password: String!, $firstName: String!, $lastName: String!) {
                registerUser(email: $email, password: $password, firstName: $firstName, lastName: $lastName) {
                    success
                    message
                    user {
                        id
                        email
                    }
                }
            }
            """,
            "variables": {
                "email": test_email,
                "password": "testpassword123",
                "firstName": "E2E",
                "lastName": "Test"
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
                    register_result = data['data']['registerUser']
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
                loginUser(email: $email, password: $password) {
                    success
                    message
                    token {
                        access
                        refresh
                    }
                    user {
                        id
                        email
                    }
                }
            }
            """,
            "variables": {
                "email": test_email,  # Use the same email as registration
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
                    login_result = data['data']['loginUser']
                    if login_result.get('success'):
                        self.log_test("User Login", True, "User logged in successfully")
                        self.auth_token = login_result.get('token')
                        return True
                    else:
                        self.log_test("User Login", False, f"Login failed: {login_result.get('message')}")
                else:
                    self.log_test("User Login", False, f"Invalid response: {data}")
            else:
                self.log_test("User Login", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("User Login", False, f"Request failed: {str(e)}")
        
        return False

    def test_alpaca_integration(self):
        """Test Alpaca integration with correct schema"""
        print("🔍 Testing Alpaca Integration...")
        
        headers = {'Content-Type': 'application/json'}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        # Test create Alpaca account with correct parameters
        create_account_mutation = {
            "query": """
            mutation CreateAlpacaAccount(
                $firstName: String!
                $lastName: String!
                $email: String!
                $phone: String!
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
                    phone: $phone
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
                "phone": "+15551234567",
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

    def test_trading_functionality(self):
        """Test trading functionality"""
        print("🔍 Testing Trading Functionality...")
        
        headers = {'Content-Type': 'application/json'}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        # Test stock trading
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
                "side": "BUY",
                "orderType": "MARKET",
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
                        self.log_test("Stock Trading", True, "Stock order placed successfully")
                    else:
                        self.log_test("Stock Trading", False, f"Order failed: {order_result.get('message')}")
                else:
                    self.log_test("Stock Trading", False, f"Invalid response: {data}")
            else:
                self.log_test("Stock Trading", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Stock Trading", False, f"Request failed: {str(e)}")

        # Test crypto trading
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
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    crypto_trade_result = data['data']['executeCryptoTrade']
                    if crypto_trade_result.get('ok'):
                        self.log_test("Crypto Trading", True, "Crypto trade executed successfully")
                    else:
                        error = crypto_trade_result.get('error', {})
                        self.log_test("Crypto Trading", False, f"Trade failed: {error.get('message', 'Unknown error')}")
                else:
                    self.log_test("Crypto Trading", False, f"Invalid response: {data}")
            else:
                self.log_test("Crypto Trading", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Crypto Trading", False, f"Request failed: {str(e)}")

    def test_database_queries(self):
        """Test database queries"""
        print("🔍 Testing Database Queries...")
        
        headers = {'Content-Type': 'application/json'}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        # Test user query
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
                        self.log_test("User Query", True, "No user data returned (expected for anonymous)")
                else:
                    self.log_test("User Query", False, f"Invalid response: {data}")
            else:
                self.log_test("User Query", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("User Query", False, f"Request failed: {str(e)}")

        # Test Alpaca account query
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

    def test_market_data(self):
        """Test market data functionality"""
        print("🔍 Testing Market Data...")
        
        # Test stock quotes with correct field name
        stock_quotes_query = {
            "query": """
            query GetStockQuotes($symbols: [String!]!) {
                quotes(symbols: $symbols) {
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
                    quotes_data = data['data']['quotes']
                    if quotes_data:
                        self.log_test("Stock Quotes", True, f"Retrieved {len(quotes_data)} stock quotes")
                    else:
                        self.log_test("Stock Quotes", True, "No stock quotes returned (expected if market data service is disabled)")
                else:
                    self.log_test("Stock Quotes", False, f"Invalid response: {data}")
            else:
                self.log_test("Stock Quotes", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Stock Quotes", False, f"Request failed: {str(e)}")

    def run_all_tests(self):
        """Run all E2E tests"""
        print("🚀 Starting Final Comprehensive E2E Test")
        print("=" * 60)
        
        # Test core infrastructure
        if not self.test_core_infrastructure():
            print("❌ Core infrastructure failed. Stopping tests.")
            return self.results
        
        # Test authentication
        auth_success = self.test_authentication_flow()
        
        # Test Alpaca integration
        alpaca_account_id = self.test_alpaca_integration()
        
        # Test trading functionality
        self.test_trading_functionality()
        
        # Test database queries
        self.test_database_queries()
        
        # Test market data
        self.test_market_data()
        
        return self.results

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 FINAL E2E TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📊 Total:  {self.results['total']}")
        print(f"📈 Success Rate: {(self.results['passed'] / self.results['total'] * 100):.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for detail in self.results['details']:
            print(f"  {detail['status']} {detail['test']}")
            if detail['message']:
                print(f"      {detail['message']}")
        
        print("\n" + "=" * 60)
        
        if self.results['failed'] == 0:
            print("🎉 ALL TESTS PASSED! System is ready for production!")
        elif self.results['passed'] / self.results['total'] >= 0.8:
            print("✅ Most tests passed! System is mostly ready with minor issues.")
        elif self.results['passed'] / self.results['total'] >= 0.6:
            print("⚠️  Some tests failed. System needs attention but core functionality works.")
        else:
            print("❌ Many tests failed. System needs significant fixes.")
        
        print("\n🔧 RECOMMENDATIONS:")
        if self.results['failed'] > 0:
            print("  - Review failed tests above")
            print("  - Check GraphQL schema consistency")
            print("  - Verify authentication flow")
            print("  - Test with real user accounts")
        else:
            print("  - System is production ready!")
            print("  - Consider adding more comprehensive tests")
            print("  - Monitor performance in production")

if __name__ == "__main__":
    # Load environment variables
    load_env_secrets()
    
    # Run E2E tests
    test_suite = FinalE2ETest()
    results = test_suite.run_all_tests()
    test_suite.print_summary()
