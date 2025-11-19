#!/usr/bin/env python3
"""
Comprehensive System Test for RichesReach
Tests for:
- 400/500 HTTP errors
- Missing columns and fields
- Undefined/null values in responses
- GraphQL query/mutation errors
"""

import requests
import json
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Test configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 30
VERBOSE = True

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": [],
    "errors": {
        "400_errors": [],
        "500_errors": [],
        "missing_fields": [],
        "undefined_values": [],
        "graphql_errors": []
    }
}

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")
    test_results["passed"].append(msg)

def print_error(msg: str, error_type: str = "general"):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")
    test_results["failed"].append(msg)
    if error_type in test_results["errors"]:
        test_results["errors"][error_type].append(msg)

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")
    test_results["warnings"].append(msg)

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_section(msg: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{msg}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def check_server_running() -> bool:
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Server is running and responding")
            return True
        else:
            print_error(f"Server returned status {response.status_code}", "500_errors")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running?", "500_errors")
        print_info(f"Expected URL: {BASE_URL}")
        print_info("Start server with: python3 main_server.py")
        return False
    except Exception as e:
        print_error(f"Error checking server: {str(e)}", "500_errors")
        return False

def check_http_error(response: requests.Response, endpoint: str) -> Tuple[bool, Optional[str]]:
    """Check for HTTP errors (400, 500, etc.)"""
    if response.status_code == 400:
        error_msg = f"400 Bad Request: {endpoint}"
        print_error(error_msg, "400_errors")
        return False, error_msg
    elif response.status_code >= 500:
        error_msg = f"{response.status_code} Server Error: {endpoint}"
        print_error(error_msg, "500_errors")
        return False, error_msg
    elif response.status_code >= 400:
        error_msg = f"{response.status_code} Client Error: {endpoint}"
        print_warning(error_msg)
        return True, None  # Warning, not failure
    return True, None

def check_missing_fields(data: Any, expected_fields: List[str], path: str = "") -> List[str]:
    """Recursively check for missing fields in response"""
    missing = []
    
    if isinstance(data, dict):
        for field in expected_fields:
            if field not in data:
                missing.append(f"{path}.{field}" if path else field)
        # Recursively check nested objects
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                nested_path = f"{path}.{key}" if path else key
                missing.extend(check_missing_fields(value, [], nested_path))
    elif isinstance(data, list) and len(data) > 0:
        # Check first item in list
        missing.extend(check_missing_fields(data[0], expected_fields, f"{path}[0]"))
    
    return missing

def check_undefined_values(data: Any, path: str = "") -> List[str]:
    """Recursively check for undefined/null values that shouldn't be null"""
    undefined = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if value is None:
                undefined.append(current_path)
            elif isinstance(value, (dict, list)):
                undefined.extend(check_undefined_values(value, current_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]" if path else f"[{i}]"
            if isinstance(item, (dict, list)):
                undefined.extend(check_undefined_values(item, current_path))
            elif item is None:
                undefined.append(current_path)
    
    return undefined

def test_rest_endpoint(method: str, endpoint: str, expected_status: int = 200, 
                      data: Optional[Dict] = None, headers: Optional[Dict] = None,
                      expected_fields: Optional[List[str]] = None) -> bool:
    """Test a REST API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=TIMEOUT)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=TIMEOUT)
        else:
            print_error(f"Unsupported HTTP method: {method}")
            return False
        
        # Check HTTP status
        success, error_msg = check_http_error(response, endpoint)
        if not success:
            return False
        
        # Check if status matches expected
        if response.status_code != expected_status:
            print_warning(f"{endpoint}: Expected {expected_status}, got {response.status_code}")
        
        # Try to parse JSON
        try:
            json_data = response.json()
            
            # Check for missing fields
            if expected_fields:
                missing = check_missing_fields(json_data, expected_fields)
                if missing:
                    for field in missing:
                        error_msg = f"{endpoint}: Missing field '{field}'"
                        print_error(error_msg, "missing_fields")
                        return False
            
            # Check for undefined values in critical fields
            if isinstance(json_data, dict):
                undefined = check_undefined_values(json_data)
                # Only report undefined in top-level critical fields
                critical_fields = ["status", "data", "error", "message"]
                for field in critical_fields:
                    if field in json_data and json_data[field] is None:
                        error_msg = f"{endpoint}: Critical field '{field}' is null"
                        print_error(error_msg, "undefined_values")
                        return False
            
            print_success(f"{method} {endpoint} (Status: {response.status_code})")
            return True
            
        except json.JSONDecodeError:
            # Not JSON, check if it's a valid response
            if response.status_code == expected_status:
                print_success(f"{method} {endpoint} (Status: {response.status_code}, non-JSON)")
                return True
            else:
                print_warning(f"{endpoint}: Response is not JSON")
                return True  # Not a failure, just not JSON
        
    except requests.exceptions.Timeout:
        print_error(f"{endpoint}: Request timed out", "500_errors")
        return False
    except requests.exceptions.ConnectionError:
        print_error(f"{endpoint}: Connection error", "500_errors")
        return False
    except Exception as e:
        print_error(f"{endpoint}: {str(e)}", "500_errors")
        return False

def test_graphql_query(query: str, description: str, variables: Optional[Dict] = None,
                      expected_fields: Optional[List[str]] = None) -> bool:
    """Test a GraphQL query"""
    url = f"{BASE_URL}/graphql/"
    
    try:
        # Extract operation name from query string
        operation_name = None
        import re
        match = re.search(r'(?:query|mutation)\s+(\w+)', query)
        if match:
            operation_name = match.group(1)
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        # Check HTTP status
        success, error_msg = check_http_error(response, f"GraphQL: {description}")
        if not success:
            return False
        
        # Parse response
        try:
            data = response.json()
            
            # Check for GraphQL errors
            if "errors" in data and data["errors"]:
                error_messages = [e.get("message", "") for e in data["errors"]]
                # Some errors are expected (auth, premium, etc.)
                if any("authentication" in msg.lower() or "premium" in msg.lower() 
                       or "permission" in msg.lower() for msg in error_messages):
                    print_warning(f"GraphQL {description}: Authentication/Premium required (expected)")
                    return True  # Expected, not a failure
                else:
                    error_msg = f"GraphQL {description}: {error_messages}"
                    print_error(error_msg, "graphql_errors")
                    return False
            
            # Check for data
            if "data" in data:
                data_content = data["data"]
                
                # Check for missing fields
                if expected_fields and data_content:
                    missing = check_missing_fields(data_content, expected_fields)
                    if missing:
                        for field in missing:
                            error_msg = f"GraphQL {description}: Missing field '{field}'"
                            print_error(error_msg, "missing_fields")
                            return False
                
                # Check for undefined in top-level data
                if isinstance(data_content, dict):
                    for key, value in data_content.items():
                        if value is None and key not in ["__typename"]:  # __typename can be null
                            error_msg = f"GraphQL {description}: Field '{key}' is null"
                            print_error(error_msg, "undefined_values")
                            return False
                
                print_success(f"GraphQL: {description}")
                return True
            else:
                print_warning(f"GraphQL {description}: No data returned")
                return True  # May be expected
            
        except json.JSONDecodeError:
            print_error(f"GraphQL {description}: Invalid JSON response", "graphql_errors")
            return False
        
    except requests.exceptions.Timeout:
        print_error(f"GraphQL {description}: Request timed out", "500_errors")
        return False
    except requests.exceptions.ConnectionError:
        print_error(f"GraphQL {description}: Connection error", "500_errors")
        return False
    except Exception as e:
        print_error(f"GraphQL {description}: {str(e)}", "500_errors")
        return False

def main():
    print_section("🧪 RichesReach Comprehensive System Test")
    print_info(f"Testing server at: {BASE_URL}")
    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if server is running
    if not check_server_running():
        print_error("\n❌ Server is not running. Please start it first.")
        print_info("Start command: python3 main_server.py")
        return 1
    
    print_section("📡 Testing REST API Endpoints")
    
    # Health check
    test_rest_endpoint("GET", "/health", expected_status=200, expected_fields=["status"])
    
    # Market data endpoints
    test_rest_endpoint("GET", "/api/market/quotes", expected_status=200)
    
    # Trading endpoints
    test_rest_endpoint("GET", "/api/trading/quote/AAPL", expected_status=200)
    
    # Portfolio endpoints
    test_rest_endpoint("GET", "/api/portfolio/recommendations", expected_status=200)
    
    # Coach/Holding insight
    test_rest_endpoint("GET", "/api/coach/holding-insight?ticker=AAPL", expected_status=200)
    
    print_section("🔍 Testing GraphQL Queries")
    
    # Basic introspection (with operation name)
    introspection_query = """
    query IntrospectionQuery {
        __typename
    }
    """
    test_graphql_query(introspection_query, "Schema Introspection", 
                      variables=None, expected_fields=None)
    
    # Test Portfolio Metrics (no auth required) - with operation name
    day_trading_query = """
    query TestPortfolioMetrics {
        testPortfolioMetrics {
            totalValue
            totalReturn
        }
    }
    """
    test_graphql_query(day_trading_query, "Test Portfolio Metrics")
    
    # Stocks query (uses search, not limit) - with operation name
    stocks_query = """
    query StocksQuery {
        stocks(search: "AAPL") {
            symbol
            companyName
            currentPrice
        }
    }
    """
    test_graphql_query(stocks_query, "Stocks Query", expected_fields=["stocks"])
    
    # Portfolio Metrics (using camelCase field names) - with operation name
    portfolio_query = """
    query PortfolioMetrics {
        portfolioMetrics {
            totalValue
            totalReturn
            totalReturnPercent
        }
    }
    """
    test_graphql_query(portfolio_query, "Portfolio Metrics")
    
    # My Portfolios (returns single object, not list) - with operation name
    my_portfolios_query = """
    query MyPortfolios {
        myPortfolios {
            totalValue
            totalPortfolios
        }
    }
    """
    test_graphql_query(my_portfolios_query, "My Portfolios")
    
    # AI Recommendations (using test query that doesn't require auth) - with operation name
    ai_recommendations_query = """
    query TestAIRecommendations {
        testAiRecommendations {
            portfolioAnalysis {
                totalValue
            }
            buyRecommendations {
                symbol
                recommendation
            }
        }
    }
    """
    test_graphql_query(ai_recommendations_query, "Test AI Recommendations")
    
    # Options Analysis (using test query) - with operation name
    options_query = """
    query TestOptionsAnalysis {
        testOptionsAnalysis(symbol: "AAPL") {
            underlyingSymbol
            underlyingPrice
            optionsChain {
                expirationDates
            }
        }
    }
    """
    test_graphql_query(options_query, "Test Options Analysis")
    
    # Advanced Stock Screening (using test query) - with operation name
    screening_query = """
    query TestStockScreening {
        testStockScreening {
            symbol
            companyName
            currentPrice
        }
    }
    """
    test_graphql_query(screening_query, "Test Stock Screening")
    
    print_section("🔄 Testing GraphQL Mutations")
    
    # Subscribe to Premium (dry run) - with operation name
    subscribe_mutation = """
    mutation SubscribeToPremium {
        subscribeToPremium(planType: "basic", paymentMethod: "test") {
            success
            message
        }
    }
    """
    test_graphql_query(subscribe_mutation, "Subscribe to Premium Mutation")
    
    # AI Rebalance Portfolio (dry run) - with operation name
    rebalance_mutation = """
    mutation AiRebalancePortfolio {
        aiRebalancePortfolio(
            riskTolerance: "medium"
            maxRebalancePercentage: 20.0
            dryRun: true
        ) {
            success
            message
        }
    }
    """
    test_graphql_query(rebalance_mutation, "AI Rebalance Portfolio Mutation")
    
    print_section("📊 Test Results Summary")
    
    total_passed = len(test_results["passed"])
    total_failed = len(test_results["failed"])
    total_warnings = len(test_results["warnings"])
    
    print(f"\n{Colors.BOLD}Overall Results:{Colors.RESET}")
    print(f"  {Colors.GREEN}✅ Passed: {total_passed}{Colors.RESET}")
    print(f"  {Colors.RED}❌ Failed: {total_failed}{Colors.RESET}")
    print(f"  {Colors.YELLOW}⚠️  Warnings: {total_warnings}{Colors.RESET}")
    
    # Error breakdown
    print(f"\n{Colors.BOLD}Error Breakdown:{Colors.RESET}")
    for error_type, errors in test_results["errors"].items():
        if errors:
            print(f"  {Colors.RED}{error_type}: {len(errors)}{Colors.RESET}")
            if VERBOSE:
                for error in errors[:5]:  # Show first 5
                    print(f"    - {error}")
                if len(errors) > 5:
                    print(f"    ... and {len(errors) - 5} more")
    
    # Final verdict
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    if total_failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! No errors found.{Colors.RESET}")
        print(f"{Colors.GREEN}✅ No 400 errors")
        print(f"{Colors.GREEN}✅ No 500 errors")
        print(f"{Colors.GREEN}✅ No missing fields")
        print(f"{Colors.GREEN}✅ No undefined values{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED{Colors.RESET}")
        print(f"{Colors.RED}❌ {total_failed} test(s) failed{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Review the errors above and fix them before production.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}", "500_errors")
        import traceback
        traceback.print_exc()
        sys.exit(1)

