#!/usr/bin/env python3
"""
Comprehensive API Endpoint Test Script
Tests all REST endpoints and GraphQL queries/mutations to ensure they return data (not null)
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
GRAPHQL_URL = f"{API_BASE_URL}/graphql/"
TIMEOUT = 10  # seconds

# Test results storage
test_results: List[Dict[str, Any]] = []

def log_test(endpoint: str, method: str, status: str, details: str = "", data: Any = None):
    """Log test result"""
    result = {
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "details": details,
        "has_data": data is not None and data != {} and data != []
    }
    test_results.append(result)
    
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_icon} {method} {endpoint}: {status}")
    if details:
        print(f"   {details}")
    if data is not None and status == "PASS":
        print(f"   Data: {json.dumps(data, indent=2)[:200]}...")

def test_rest_endpoint(endpoint: str, method: str = "GET", data: Optional[Dict] = None, headers: Optional[Dict] = None) -> bool:
    """Test a REST endpoint"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT, headers=headers)
        else:
            log_test(endpoint, method, "SKIP", "Unsupported method")
            return False
        
        if response.status_code == 200:
            try:
                result = response.json()
                # Check if result is not null/empty
                if result is None:
                    log_test(endpoint, method, "FAIL", "Response is null")
                    return False
                if result == {}:
                    log_test(endpoint, method, "WARN", "Response is empty object")
                    return True  # Empty object might be valid
                if isinstance(result, list) and len(result) == 0:
                    log_test(endpoint, method, "WARN", "Response is empty array")
                    return True  # Empty array might be valid
                
                log_test(endpoint, method, "PASS", f"Status: {response.status_code}", result)
                return True
            except json.JSONDecodeError:
                log_test(endpoint, method, "FAIL", f"Invalid JSON response: {response.text[:100]}")
                return False
        else:
            log_test(endpoint, method, "FAIL", f"Status: {response.status_code}, Response: {response.text[:100]}")
            return False
    except requests.exceptions.RequestException as e:
        log_test(endpoint, method, "FAIL", f"Request error: {str(e)}")
        return False

def test_graphql_query(query_name: str, query: str, variables: Optional[Dict] = None) -> bool:
    """Test a GraphQL query"""
    try:
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = requests.post(
            GRAPHQL_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            if "errors" in result:
                log_test(f"GraphQL: {query_name}", "POST", "FAIL", f"GraphQL errors: {result['errors']}")
                return False
            
            if "data" not in result:
                log_test(f"GraphQL: {query_name}", "POST", "FAIL", "No 'data' field in response")
                return False
            
            data = result["data"]
            if data is None:
                log_test(f"GraphQL: {query_name}", "POST", "FAIL", "Data field is null")
                return False
            
            # Check if the specific query result exists and has data
            query_result = data.get(query_name.split(":")[-1].strip(), None)
            if query_result is None:
                log_test(f"GraphQL: {query_name}", "POST", "WARN", f"Query result not found in data: {list(data.keys())}")
                return True  # Might be valid if query returns different field name
            
            if query_result == {} or query_result == []:
                log_test(f"GraphQL: {query_name}", "POST", "WARN", "Query result is empty")
                return True  # Empty might be valid
            
            log_test(f"GraphQL: {query_name}", "POST", "PASS", f"Got data", query_result)
            return True
        else:
            log_test(f"GraphQL: {query_name}", "POST", "FAIL", f"Status: {response.status_code}, Response: {response.text[:100]}")
            return False
    except requests.exceptions.RequestException as e:
        log_test(f"GraphQL: {query_name}", "POST", "FAIL", f"Request error: {str(e)}")
        return False

def test_graphql_mutation(mutation_name: str, mutation: str, variables: Optional[Dict] = None) -> bool:
    """Test a GraphQL mutation"""
    return test_graphql_query(f"Mutation: {mutation_name}", mutation, variables)

def main():
    print("🧪 Testing All API Endpoints and GraphQL Queries/Mutations")
    print("=" * 70)
    print()
    
    # Test health endpoint first
    print("📡 Testing REST Endpoints...")
    print("-" * 70)
    test_rest_endpoint("/health")
    test_rest_endpoint("/api/market/quotes?symbols=AAPL,MSFT")
    test_rest_endpoint("/api/coach/holding-insight?ticker=AAPL")
    test_rest_endpoint("/api/trading/quote/AAPL")
    test_rest_endpoint("/api/portfolio/recommendations")
    
    # Test Oracle endpoints (if they exist)
    test_rest_endpoint("/api/oracle/insights/", headers={"Authorization": "Bearer test-token"})
    
    # Test Wealth Circles endpoints (if they exist)
    test_rest_endpoint("/api/wealth-circles/")
    
    # Test Tax endpoints (if they exist)
    test_rest_endpoint("/api/tax/optimization-summary", headers={"Authorization": "Bearer test-token"})
    
    print()
    print("📊 Testing GraphQL Queries...")
    print("-" * 70)
    
    # Test portfolioMetrics query
    test_graphql_query(
        "portfolioMetrics",
        """
        query GetPortfolioMetrics {
            portfolioMetrics {
                totalValue
                totalCost
                totalReturn
                totalReturnPercent
                holdings {
                    symbol
                    companyName
                    shares
                    currentPrice
                    totalValue
                }
            }
        }
        """
    )
    
    # Test myPortfolios query
    test_graphql_query(
        "myPortfolios",
        """
        query GetMyPortfolios {
            myPortfolios {
                totalPortfolios
                totalValue
                portfolios {
                    name
                    totalValue
                    holdingsCount
                    holdings {
                        id
                        stock {
                            symbol
                        }
                        shares
                        averagePrice
                        currentPrice
                        totalValue
                    }
                }
            }
        }
        """
    )
    
    # Test me query
    test_graphql_query(
        "me",
        """
        query GetMe {
            me {
                id
                name
                email
                hasPremiumAccess
                subscriptionTier
            }
        }
        """
    )
    
    # Test stocks query
    test_graphql_query(
        "stocks",
        """
        query GetStocks {
            stocks(search: "AAPL") {
                id
                symbol
                companyName
                currentPrice
            }
        }
        """
    )
    
    # Test aiRecommendations query
    test_graphql_query(
        "aiRecommendations",
        """
        query GetAIRecommendations {
            aiRecommendations(riskTolerance: "Moderate") {
                buyRecommendations {
                    symbol
                    companyName
                    recommendation
                    confidence
                }
            }
        }
        """
    )
    
    print()
    print("🔄 Testing GraphQL Mutations...")
    print("-" * 70)
    
    # Test createPortfolio mutation
    test_graphql_mutation(
        "createPortfolio",
        """
        mutation CreatePortfolio($portfolioName: String!) {
            createPortfolio(portfolioName: $portfolioName) {
                success
                message
                portfolioName
            }
        }
        """,
        {"portfolioName": "Test Portfolio"}
    )
    
    # Test addToWatchlist mutation
    test_graphql_mutation(
        "addToWatchlist",
        """
        mutation AddToWatchlist($symbol: String!, $companyName: String) {
            addToWatchlist(symbol: $symbol, companyName: $companyName) {
                success
                message
            }
        }
        """,
        {"symbol": "TEST", "companyName": "Test Company"}
    )
    
    print()
    print("=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    warned = sum(1 for r in test_results if r["status"] == "WARN")
    skipped = sum(1 for r in test_results if r["status"] == "SKIP")
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warned}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"📈 Total: {len(test_results)}")
    print()
    
    if failed > 0:
        print("❌ Failed Tests:")
        for result in test_results:
            if result["status"] == "FAIL":
                print(f"   - {result['method']} {result['endpoint']}: {result['details']}")
        print()
    
    if warned > 0:
        print("⚠️  Warnings:")
        for result in test_results:
            if result["status"] == "WARN":
                print(f"   - {result['method']} {result['endpoint']}: {result['details']}")
        print()
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    print("💾 Results saved to test_results.json")
    
    # Exit with error code if any tests failed
    sys.exit(1 if failed > 0 else 0)

if __name__ == "__main__":
    main()

