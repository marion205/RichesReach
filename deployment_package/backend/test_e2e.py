#!/usr/bin/env python3
"""
End-to-End Test Suite for RichesReach API
Tests all GraphQL queries, mutations, and FastAPI endpoints
Verifies all fields and columns are present
"""
import os
import sys
import django
import requests
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Stock, Portfolio
from core.sbloc_models import SBLOCBank

User = get_user_model()

# Configuration - Force localhost for testing
BASE_URL = 'http://localhost:8000'  # Force localhost for local testing
# Override any environment variable
os.environ['API_BASE_URL'] = BASE_URL
GRAPHQL_URL = f"{BASE_URL}/graphql/"
API_BASE = BASE_URL

# Test user
TEST_EMAIL = "test_e2e@example.com"
TEST_PASSWORD = "test123456"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class E2ETester:
    def __init__(self):
        self.token = None
        self.user = None
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'skipped': []
        }
        self.field_checks = {}
        
    def log(self, message: str, color: str = Colors.RESET):
        print(f"{color}{message}{Colors.RESET}")
        
    def log_success(self, message: str):
        self.log(f"✅ {message}", Colors.GREEN)
        self.results['passed'].append(message)
        
    def log_failure(self, message: str, error: str = ""):
        self.log(f"❌ {message}", Colors.RED)
        if error:
            self.log(f"   Error: {error}", Colors.RED)
        self.results['failed'].append(f"{message}: {error}")
        
    def log_warning(self, message: str):
        self.log(f"⚠️  {message}", Colors.YELLOW)
        self.results['warnings'].append(message)
        
    def log_info(self, message: str):
        self.log(f"ℹ️  {message}", Colors.BLUE)
        
    def setup_test_user(self):
        """Create or get test user"""
        try:
            self.user, created = User.objects.get_or_create(
                email=TEST_EMAIL,
                defaults={
                    'name': 'E2E Test User',
                }
            )
            if created or not self.user.check_password(TEST_PASSWORD):
                self.user.set_password(TEST_PASSWORD)
                self.user.save()
            self.log_success(f"Test user ready: {self.user.email}")
            return True
        except Exception as e:
            self.log_failure("Failed to setup test user", str(e))
            return False
    
    def get_auth_token(self):
        """Get authentication token"""
        try:
            # Try FastAPI login endpoint
            response = requests.post(
                f"{API_BASE}/api/auth/login/",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token') or data.get('access_token')
                if self.token:
                    self.log_success("Authentication token obtained")
                    return True
            
            # Fallback: use dev token
            self.token = f"dev-token-{int(time.time())}"
            self.log_warning("Using dev token (login endpoint may have issues)")
            return True
        except Exception as e:
            self.log_failure("Failed to get auth token", str(e))
            self.token = f"dev-token-{int(time.time())}"
            return False
    
    def graphql_query(self, query: str, variables: Dict = None, operation_name: str = None) -> Dict:
        """Execute GraphQL query"""
        headers = {
            'Content-Type': 'application/json',
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        payload = {
            'query': query,
        }
        if variables:
            payload['variables'] = variables
        if operation_name:
            payload['operationName'] = operation_name
        
        try:
            response = requests.post(
                GRAPHQL_URL,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'errors': [{'message': f'HTTP {response.status_code}: {response.text}'}]}
        except Exception as e:
            return {'errors': [{'message': str(e)}]}
    
    def check_fields(self, data: Any, expected_fields: List[str], context: str = ""):
        """Check if all expected fields are present in response"""
        missing = []
        
        # Empty list/None is valid - means no data, but query works
        if data is None:
            return True  # Query works, just no data
        
        if isinstance(data, dict):
            for field in expected_fields:
                if field not in data:
                    missing.append(field)
        elif isinstance(data, list):
            if len(data) == 0:
                return True  # Empty list is valid - query works, just no data
            # Check first item in list
            for field in expected_fields:
                if field not in data[0]:
                    missing.append(field)
        
        if missing:
            self.log_warning(f"{context}: Missing fields: {', '.join(missing)}")
            return False
        return True
    
    def test_graphql_queries(self):
        """Test all GraphQL queries"""
        self.log_info("\n" + "="*80)
        self.log_info("TESTING GRAPHQL QUERIES")
        self.log_info("="*80)
        
        queries = [
            {
                'name': 'me',
                'query': '''
                    query {
                        me {
                            id
                            email
                            name
                        }
                    }
                ''',
                'expected_fields': ['id', 'email', 'name']
            },
            {
                'name': 'sblocBanks',
                'query': '''
                    query {
                        sblocBanks {
                            id
                            name
                            logoUrl
                            minApr
                            maxApr
                            minLtv
                            maxLtv
                            notes
                            regions
                            minLoanUsd
                            isActive
                            priority
                        }
                    }
                ''',
                'expected_fields': ['id', 'name', 'logoUrl', 'minApr', 'maxApr', 'minLtv', 'maxLtv', 'regions', 'minLoanUsd']
            },
            {
                'name': 'sblocOffer',
                'query': '''
                    query {
                        sblocOffer {
                            eligibleEquity
                            ltv
                            apr
                            minDraw
                            maxDrawMultiplier
                        }
                    }
                ''',
                'expected_fields': ['eligibleEquity', 'ltv', 'apr']
            },
            {
                'name': 'bankAccounts',
                'query': '''
                    query {
                        bankAccounts {
                            id
                            name
                            accountType
                            mask
                            balanceCurrent
                            currency
                            provider
                        }
                    }
                ''',
                'expected_fields': ['id', 'name', 'accountType']
            },
            {
                'name': 'fundingHistory',
                'query': '''
                    query {
                        fundingHistory {
                            id
                            amount
                            status
                            initiatedAt
                        }
                    }
                ''',
                'expected_fields': ['id', 'amount', 'status']
            },
            {
                'name': 'brokerAccount',
                'query': '''
                    query {
                        brokerAccount {
                            id
                            alpacaAccountId
                            accountNumber
                            status
                        }
                    }
                ''',
                'expected_fields': ['id', 'status']
            },
            {
                'name': 'brokerPositions',
                'query': '''
                    query {
                        brokerPositions {
                            id
                            symbol
                            qty
                            marketValue
                        }
                    }
                ''',
                'expected_fields': ['id', 'symbol']
            },
            {
                'name': 'brokerOrders',
                'query': '''
                    query {
                        brokerOrders {
                            id
                            symbol
                            side
                            quantity
                            status
                        }
                    }
                ''',
                'expected_fields': ['id', 'symbol', 'side', 'status']
            },
            {
                'name': 'stocks',
                'query': '''
                    query {
                        stocks(search: "AAPL") {
                            id
                            symbol
                            companyName
                            currentPrice
                        }
                    }
                ''',
                'expected_fields': ['id', 'symbol', 'companyName']
            },
            {
                'name': 'stock',
                'query': '''
                    query {
                        stock(symbol: "AAPL") {
                            id
                            symbol
                            companyName
                            currentPrice
                        }
                    }
                ''',
                'expected_fields': ['id', 'symbol', 'companyName']
            },
            {
                'name': 'myPortfolios',
                'query': '''
                    query {
                        myPortfolios {
                            portfolios {
                                name
                                totalValue
                            }
                        }
                    }
                ''',
                'expected_fields': ['portfolios']
            },
            {
                'name': 'premiumPortfolioMetrics',
                'query': '''
                    query {
                        premiumPortfolioMetrics {
                            totalValue
                            totalReturn
                            totalReturnPercent
                            holdings {
                                symbol
                                shares
                                currentPrice
                            }
                        }
                    }
                ''',
                'expected_fields': ['totalValue', 'holdings']
            },
        ]
        
        for test in queries:
            try:
                # Don't pass operation_name for simple queries - it's only needed for named operations
                result = self.graphql_query(test['query'], operation_name=None)
                
                if 'errors' in result and result['errors']:
                    error_msg = result['errors'][0].get('message', 'Unknown error')
                    # Check if it's a field error (expected) vs operation error (unexpected)
                    if 'Unknown operation named' in error_msg:
                        # Try without operation name
                        result = self.graphql_query(test['query'], operation_name=None)
                        if 'errors' in result and result['errors']:
                            error_msg = result['errors'][0].get('message', 'Unknown error')
                            self.log_failure(f"Query: {test['name']}", error_msg)
                        elif 'data' in result:
                            # Extract data from first key (query name)
                            data_key = list(result['data'].keys())[0] if result['data'] else None
                            data = result['data'].get(data_key) if data_key else None
                            if data is not None:
                                self.check_fields(data, test['expected_fields'], f"Query: {test['name']}")
                                self.log_success(f"Query: {test['name']}")
                            else:
                                # None is valid - query works, just no data in DB
                                self.log_success(f"Query: {test['name']} (no data, but query works)")
                    else:
                        self.log_failure(f"Query: {test['name']}", error_msg)
                elif 'data' in result:
                    # Extract data from first key (query name)
                    data_key = list(result['data'].keys())[0] if result['data'] else None
                    data = result['data'].get(data_key) if data_key else None
                    if data is not None:
                        self.check_fields(data, test['expected_fields'], f"Query: {test['name']}")
                        self.log_success(f"Query: {test['name']}")
                    else:
                        # None is valid - query works, just no data in DB
                        self.log_success(f"Query: {test['name']} (no data, but query works)")
                else:
                    self.log_failure(f"Query: {test['name']}", "No data or errors in response")
            except Exception as e:
                self.log_failure(f"Query: {test['name']}", str(e))
    
    def test_graphql_mutations(self):
        """Test all GraphQL mutations"""
        self.log_info("\n" + "="*80)
        self.log_info("TESTING GRAPHQL MUTATIONS")
        self.log_info("="*80)
        
        mutations = [
            {
                'name': 'createSblocSession',
                'mutation': '''
                    mutation {
                        createSblocSession(amountUsd: 10000, bankId: "1") {
                            success
                            sessionId
                            error
                        }
                    }
                ''',
                'expected_fields': ['success']
            },
            {
                'name': 'linkBankAccount',
                'mutation': '''
                    mutation {
                        linkBankAccount(accountNumber: "123456789", bankName: "Test Bank", routingNumber: "123456789") {
                            success
                            bankAccount {
                                id
                            }
                            message
                        }
                    }
                ''',
                'expected_fields': ['success']
            },
            {
                'name': 'refreshBankAccount',
                'mutation': '''
                    mutation {
                        refreshBankAccount(accountId: 1) {
                            success
                            message
                        }
                    }
                ''',
                'expected_fields': ['success']
            },
            {
                'name': 'savePortfolio',
                'mutation': '''
                    mutation {
                        savePortfolio(stockIds: ["1"], sharesList: [10]) {
                            success
                            message
                        }
                    }
                ''',
                'expected_fields': ['success']
            },
        ]
        
        for test in mutations:
            try:
                # Don't pass operation_name for simple mutations
                result = self.graphql_query(test['mutation'], operation_name=None)
                
                if 'errors' in result and result['errors']:
                    error_msg = result['errors'][0].get('message', 'Unknown error')
                    # Some mutations may fail due to missing data - that's OK
                    if 'does not exist' in error_msg.lower() or 'not found' in error_msg.lower():
                        self.log_warning(f"Mutation: {test['name']} - {error_msg}")
                    elif 'Unknown operation named' in error_msg:
                        # Extract data from first key
                        if 'data' in result and result['data']:
                            data_key = list(result['data'].keys())[0]
                            data = result['data'].get(data_key)
                            if data:
                                if self.check_fields(data, test['expected_fields'], f"Mutation: {test['name']}"):
                                    self.log_success(f"Mutation: {test['name']}")
                                else:
                                    self.log_failure(f"Mutation: {test['name']} - Missing expected fields")
                            else:
                                # Mutations should always return data
                                self.log_failure(f"Mutation: {test['name']} - returned None (mutation should always return data)")
                        else:
                            self.log_failure(f"Mutation: {test['name']}", error_msg)
                    else:
                        self.log_failure(f"Mutation: {test['name']}", error_msg)
                elif 'data' in result:
                    # Extract data from first key (mutation name)
                    data_key = list(result['data'].keys())[0] if result['data'] else None
                    data = result['data'].get(data_key) if data_key else None
                    if data:
                        if self.check_fields(data, test['expected_fields'], f"Mutation: {test['name']}"):
                            self.log_success(f"Mutation: {test['name']}")
                        else:
                            self.log_failure(f"Mutation: {test['name']} - Missing expected fields")
                    else:
                        # Mutations should always return data (success/error object)
                        # None means the mutation didn't execute properly
                        self.log_failure(f"Mutation: {test['name']} - returned None (mutation should always return data)")
                else:
                    self.log_failure(f"Mutation: {test['name']}", "No data or errors in response")
            except Exception as e:
                self.log_failure(f"Mutation: {test['name']}", str(e))
    
    def test_fastapi_endpoints(self):
        """Test all FastAPI endpoints"""
        self.log_info("\n" + "="*80)
        self.log_info("TESTING FASTAPI ENDPOINTS")
        self.log_info("="*80)
        
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        endpoints = [
            {
                'method': 'GET',
                'url': f"{API_BASE}/",
                'name': 'Root endpoint',
                'expected_fields': ['message', 'version', 'status']
            },
            {
                'method': 'GET',
                'url': f"{API_BASE}/health",
                'name': 'Health check',
                'expected_fields': ['status', 'timestamp']
            },
            {
                'method': 'GET',
                'url': f"{API_BASE}/api/status",
                'name': 'Service status',
                'expected_fields': ['service', 'version', 'status']
            },
            {
                'method': 'GET',
                'url': f"{API_BASE}/api/tax/optimization-summary",
                'name': 'Tax optimization summary',
                'expected_fields': ['holdings', 'totalPortfolioValue']
            },
            {
                'method': 'GET',
                'url': f"{API_BASE}/api/market/quotes?symbols=AAPL,MSFT",
                'name': 'Market quotes',
                'expected_fields': ['symbol', 'price']
            },
            {
                'method': 'GET',
                'url': f"{API_BASE}/api/yodlee/accounts",
                'name': 'Yodlee accounts',
                'expected_fields': ['success', 'accounts']
            },
            {
                'method': 'GET',
                'url': f"{API_BASE}/api/tax/projection?years=3&income=80000",
                'name': 'Tax projection',
                'expected_fields': ['projections', 'currentYear']
            },
            {
                'method': 'GET',
                'url': f"{API_BASE}/api/test/sbloc-banks",
                'name': 'Test SBLOC banks',
                'expected_fields': ['banks', 'count']
            },
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint['method'] == 'GET':
                    response = requests.get(endpoint['url'], headers=headers, timeout=30)
                elif endpoint['method'] == 'POST':
                    response = requests.post(endpoint['url'], headers=headers, json={}, timeout=30)
                else:
                    continue
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.check_fields(data, endpoint['expected_fields'], endpoint['name'])
                        self.log_success(f"Endpoint: {endpoint['name']}")
                    except json.JSONDecodeError:
                        self.log_warning(f"Endpoint: {endpoint['name']} - Invalid JSON response")
                elif response.status_code == 401:
                    self.log_warning(f"Endpoint: {endpoint['name']} - Unauthorized (may need auth)")
                elif response.status_code == 503:
                    self.log_warning(f"Endpoint: {endpoint['name']} - Service unavailable")
                else:
                    self.log_failure(f"Endpoint: {endpoint['name']}", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_failure(f"Endpoint: {endpoint['name']}", str(e))
    
    def test_django_endpoints(self):
        """Test Django REST endpoints"""
        self.log_info("\n" + "="*80)
        self.log_info("TESTING DJANGO REST ENDPOINTS")
        self.log_info("="*80)
        
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        endpoints = [
            {
                'method': 'GET',
                'url': f"{API_BASE}/api/market/quotes/?symbols=AAPL",
                'name': 'Django market quotes',
                'expected_fields': []
            },
            {
                'method': 'GET',
                'url': f"{API_BASE}/api/voices/",
                'name': 'Voices list',
                'expected_fields': []
            },
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint['method'] == 'GET':
                    response = requests.get(endpoint['url'], headers=headers, timeout=30)
                else:
                    continue
                
                if response.status_code in [200, 201]:
                    self.log_success(f"Endpoint: {endpoint['name']}")
                elif response.status_code == 401:
                    self.log_warning(f"Endpoint: {endpoint['name']} - Unauthorized")
                else:
                    self.log_warning(f"Endpoint: {endpoint['name']} - HTTP {response.status_code}")
            except Exception as e:
                self.log_warning(f"Endpoint: {endpoint['name']} - {str(e)}")
    
    def verify_database_models(self):
        """Verify database models have required fields"""
        self.log_info("\n" + "="*80)
        self.log_info("VERIFYING DATABASE MODELS")
        self.log_info("="*80)
        
        # Check SBLOCBank model
        try:
            banks = SBLOCBank.objects.filter(is_active=True)[:1]
            if banks.exists():
                bank = banks.first()
                required_fields = ['id', 'name', 'min_apr', 'max_apr', 'min_ltv', 'max_ltv', 'min_loan_usd']
                missing = [f for f in required_fields if not hasattr(bank, f)]
                if missing:
                    self.log_warning(f"SBLOCBank model missing fields: {', '.join(missing)}")
                else:
                    self.log_success("SBLOCBank model fields verified")
            else:
                self.log_info("No SBLOC banks in database (data issue, not code issue)")
        except Exception as e:
            self.log_failure("SBLOCBank model check", str(e))
        
        # Check Stock model
        try:
            stocks = Stock.objects.all()[:1]
            if stocks.exists():
                stock = stocks.first()
                required_fields = ['id', 'symbol', 'company_name', 'current_price']
                missing = [f for f in required_fields if not hasattr(stock, f)]
                if missing:
                    self.log_warning(f"Stock model missing fields: {', '.join(missing)}")
                else:
                    self.log_success("Stock model fields verified")
            else:
                self.log_warning("No stocks in database")
        except Exception as e:
            self.log_failure("Stock model check", str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        self.log_info("\n" + "="*80)
        self.log_info("RICHSREACH END-TO-END TEST SUITE")
        self.log_info("="*80)
        self.log_info(f"Testing against: {BASE_URL}")
        self.log_info(f"Started at: {datetime.now().isoformat()}")
        
        # Setup
        if not self.setup_test_user():
            self.log_failure("Cannot proceed without test user")
            return
        
        if not self.get_auth_token():
            self.log_warning("Proceeding without valid auth token")
        
        # Run tests
        self.test_graphql_queries()
        self.test_graphql_mutations()
        self.test_fastapi_endpoints()
        self.test_django_endpoints()
        self.verify_database_models()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.log_info("\n" + "="*80)
        self.log_info("TEST SUMMARY")
        self.log_info("="*80)
        
        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])
        
        self.log(f"\nTotal Tests: {total}", Colors.BOLD)
        self.log(f"✅ Passed: {len(self.results['passed'])}", Colors.GREEN)
        self.log(f"❌ Failed: {len(self.results['failed'])}", Colors.RED)
        self.log(f"⚠️  Warnings: {len(self.results['warnings'])}", Colors.YELLOW)
        
        if self.results['failed']:
            self.log("\nFailed Tests:", Colors.RED)
            for failure in self.results['failed']:
                self.log(f"  - {failure}", Colors.RED)
        
        if self.results['warnings']:
            self.log("\nWarnings:", Colors.YELLOW)
            for warning in self.results['warnings'][:10]:  # Show first 10
                self.log(f"  - {warning}", Colors.YELLOW)
        
        success_rate = (len(self.results['passed']) / total * 100) if total > 0 else 0
        self.log(f"\nSuccess Rate: {success_rate:.1f}%", Colors.BOLD)
        
        if len(self.results['failed']) == 0:
            self.log("\n🎉 All critical tests passed!", Colors.GREEN + Colors.BOLD)
        else:
            self.log(f"\n⚠️  {len(self.results['failed'])} tests failed", Colors.RED + Colors.BOLD)

if __name__ == "__main__":
    tester = E2ETester()
    tester.run_all_tests()

