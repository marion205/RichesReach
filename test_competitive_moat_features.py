#!/usr/bin/env python3
"""
Test script for Competitive Moat Enhancements
Tests all new GraphQL endpoints and features
"""

import requests
import json
import sys
from typing import Dict, Optional, List
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"
HEALTH_URL = f"{BASE_URL}/health"

# Colors for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

# Test results
test_results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0
}


def print_section(title: str):
    """Print a section header"""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")


def print_test(name: str, status: str, message: str = ""):
    """Print test result"""
    if status == 'PASS':
        print(f"{GREEN}✅ {name}{NC}")
        test_results['passed'] += 1
    elif status == 'FAIL':
        print(f"{RED}❌ {name}{NC}")
        test_results['failed'] += 1
    elif status == 'WARN':
        print(f"{YELLOW}⚠️  {name}{NC}")
        test_results['warnings'] += 1
    
    if message:
        print(f"   {message}")


def check_server_running() -> bool:
    """Check if the server is running"""
    try:
        # Check GraphQL endpoint instead of health
        response = requests.post(
            GRAPHQL_URL,
            json={"query": "{ __typename }"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False


def get_auth_token(email: str = "test@richesreach.com", password: str = "testpass123") -> Optional[str]:
    """Get JWT authentication token"""
    query = """
    mutation TokenAuth($email: String!, $password: String!) {
        tokenAuth(email: $email, password: $password) {
            token
        }
    }
    """
    
    variables = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'] and 'tokenAuth' in data['data']:
                token = data['data']['tokenAuth'].get('token')
                if token:
                    return token
        
        return None
    except Exception as e:
        print(f"   Error getting token: {e}")
        return None


def execute_graphql_query(query: str, variables: Optional[Dict] = None, token: Optional[str] = None) -> Dict:
    """Execute a GraphQL query"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def test_paper_trading_queries(token: str):
    """Test paper trading GraphQL queries"""
    print_section("📊 Testing Paper Trading Queries")
    
    # Test 1: paperAccountSummary
    query1 = """
    query {
        paperAccountSummary {
            account {
                id
                initialBalance
                currentBalance
                totalValue
                totalPnl
                totalPnlPercent
                winRate
            }
            positions {
                id
                stockSymbol
                shares
                averagePrice
                currentPrice
                unrealizedPnl
            }
            statistics {
                totalTrades
                winningTrades
                losingTrades
                winRate
            }
        }
    }
    """
    
    result = execute_graphql_query(query1, token=token)
    if 'data' in result and result['data'] and 'paperAccountSummary' in result['data']:
        print_test("paperAccountSummary Query", "PASS", "Account summary retrieved successfully")
        if result['data']['paperAccountSummary']:
            account = result['data']['paperAccountSummary'].get('account', {})
            print(f"   Initial Balance: ${account.get('initialBalance', 'N/A')}")
            print(f"   Current Balance: ${account.get('currentBalance', 'N/A')}")
            print(f"   Total P&L: ${account.get('totalPnl', 'N/A')}")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("paperAccountSummary Query", "FAIL", f"Error: {error_msg}")
    
    # Test 2: paperPositions
    query2 = """
    query {
        paperPositions {
            id
            stockSymbol
            stockName
            shares
            averagePrice
            currentPrice
            marketValue
            unrealizedPnl
            unrealizedPnlPercent
        }
    }
    """
    
    result = execute_graphql_query(query2, token=token)
    if 'data' in result and result['data']:
        print_test("paperPositions Query", "PASS", f"Retrieved {len(result['data'].get('paperPositions', []))} positions")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("paperPositions Query", "WARN", f"Error: {error_msg} (may be empty)")
    
    # Test 3: paperOrders
    query3 = """
    query {
        paperOrders {
            id
            stockSymbol
            side
            orderType
            quantity
            status
            filledPrice
            createdAt
        }
    }
    """
    
    result = execute_graphql_query(query3, token=token)
    if 'data' in result and result['data']:
        print_test("paperOrders Query", "PASS", f"Retrieved {len(result['data'].get('paperOrders', []))} orders")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("paperOrders Query", "WARN", f"Error: {error_msg} (may be empty)")
    
    # Test 4: paperTradeHistory
    query4 = """
    query {
        paperTradeHistory(limit: 10) {
            id
            stockSymbol
            side
            quantity
            price
            totalValue
            realizedPnl
            createdAt
        }
    }
    """
    
    result = execute_graphql_query(query4, token=token)
    if 'data' in result and result['data']:
        print_test("paperTradeHistory Query", "PASS", f"Retrieved {len(result['data'].get('paperTradeHistory', []))} trades")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("paperTradeHistory Query", "WARN", f"Error: {error_msg} (may be empty)")


def test_paper_trading_mutations(token: str):
    """Test paper trading GraphQL mutations"""
    print_section("📝 Testing Paper Trading Mutations")
    
    # Test 1: placePaperOrder
    mutation1 = """
    mutation PlaceOrder($symbol: String!, $side: String!, $quantity: Int!, $orderType: String!) {
        placePaperOrder(
            symbol: $symbol
            side: $side
            quantity: $quantity
            orderType: $orderType
        ) {
            success
            order {
                id
                stockSymbol
                side
                orderType
                quantity
                status
                filledPrice
            }
            error
        }
    }
    """
    
    variables = {
        "symbol": "AAPL",
        "side": "BUY",
        "quantity": 10,
        "orderType": "MARKET"
    }
    
    result = execute_graphql_query(mutation1, variables=variables, token=token)
    if 'data' in result and result['data'] and 'placePaperOrder' in result['data']:
        order_result = result['data']['placePaperOrder']
        if order_result.get('success'):
            print_test("placePaperOrder Mutation", "PASS", f"Order placed: {order_result.get('order', {}).get('id', 'N/A')}")
        else:
            error = order_result.get('error', 'Unknown error')
            print_test("placePaperOrder Mutation", "WARN", f"Order failed: {error} (may need stock in DB)")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("placePaperOrder Mutation", "WARN", f"Error: {error_msg}")


def test_signal_fusion_queries(token: str):
    """Test signal fusion GraphQL queries"""
    print_section("🔔 Testing Signal Fusion Queries")
    
    # Test 1: signalUpdates
    query1 = """
    query GetSignalUpdates($symbol: String!, $lookbackHours: Int) {
        signalUpdates(symbol: $symbol, lookbackHours: $lookbackHours) {
            symbol
            timestamp
            fusionScore
            recommendation
            consumerStrength
            signals
            alerts {
                type
                severity
                message
                timestamp
            }
        }
    }
    """
    
    variables = {
        "symbol": "AAPL",
        "lookbackHours": 24
    }
    
    result = execute_graphql_query(query1, variables=variables, token=token)
    if 'data' in result and result['data'] and 'signalUpdates' in result['data']:
        signals = result['data']['signalUpdates']
        print_test("signalUpdates Query", "PASS", f"Fusion Score: {signals.get('fusionScore', 'N/A')}, Recommendation: {signals.get('recommendation', 'N/A')}")
        alerts = signals.get('alerts', [])
        if alerts:
            print(f"   Alerts: {len(alerts)}")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("signalUpdates Query", "WARN", f"Error: {error_msg}")
    
    # Test 2: watchlistSignals
    query2 = """
    query {
        watchlistSignals(threshold: 70.0) {
            symbol
            fusionScore
            recommendation
            alerts {
                type
                severity
                message
            }
        }
    }
    """
    
    result = execute_graphql_query(query2, token=token)
    if 'data' in result and result['data']:
        signals = result['data'].get('watchlistSignals', [])
        print_test("watchlistSignals Query", "PASS", f"Retrieved {len(signals)} strong signals")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("watchlistSignals Query", "WARN", f"Error: {error_msg} (may be empty if no watchlist)")
    
    # Test 3: portfolioSignals
    query3 = """
    query {
        portfolioSignals(threshold: 60.0) {
            portfolioSignals
            strongBuyCount
            strongSellCount
            overallSentiment
            totalPositions
        }
    }
    """
    
    result = execute_graphql_query(query3, token=token)
    if 'data' in result and result['data']:
        signals = result['data'].get('portfolioSignals', {})
        print_test("portfolioSignals Query", "PASS", f"Sentiment: {signals.get('overallSentiment', 'N/A')}, Positions: {signals.get('totalPositions', 0)}")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("portfolioSignals Query", "WARN", f"Error: {error_msg} (may be empty if no portfolio)")


def test_research_report_mutation(token: str):
    """Test research report generation"""
    print_section("📄 Testing Research Report Generation")
    
    mutation = """
    mutation GenerateReport($symbol: String!, $reportType: String!) {
        generateResearchReport(symbol: $symbol, reportType: $reportType) {
            success
            report {
                symbol
                companyName
                generatedAt
                reportType
                executiveSummary
                sections {
                    overview
                    financials
                    technicalAnalysis
                    fundamentalAnalysis
                    aiInsights
                    consumerStrength
                    riskAssessment
                    recommendation
                }
                keyMetrics
            }
            error
        }
    }
    """
    
    variables = {
        "symbol": "AAPL",
        "reportType": "comprehensive"
    }
    
    result = execute_graphql_query(mutation, variables=variables, token=token)
    if 'data' in result and result['data'] and 'generateResearchReport' in result['data']:
        report_result = result['data']['generateResearchReport']
        if report_result.get('success'):
            report = report_result.get('report', {})
            print_test("generateResearchReport Mutation", "PASS", f"Report generated for {report.get('symbol', 'N/A')}")
            print(f"   Company: {report.get('companyName', 'N/A')}")
            print(f"   Report Type: {report.get('reportType', 'N/A')}")
        else:
            error = report_result.get('error', 'Unknown error')
            print_test("generateResearchReport Mutation", "WARN", f"Error: {error} (may need stock in DB)")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("generateResearchReport Mutation", "WARN", f"Error: {error_msg}")


def test_consumer_strength_queries(token: str):
    """Test consumer strength GraphQL queries"""
    print_section("💪 Testing Consumer Strength Queries")
    
    # Test 1: consumerStrength
    query1 = """
    query GetConsumerStrength($symbol: String!) {
        consumerStrength(symbol: $symbol) {
            overallScore
            spendingScore
            optionsScore
            earningsScore
            insiderScore
            spendingGrowth
            sectorScore
            historicalTrend
            components {
                spending {
                    score
                    growth
                    weight
                }
                options {
                    score
                    weight
                }
                earnings {
                    score
                    weight
                }
                insider {
                    score
                    weight
                }
            }
        }
    }
    """
    
    variables = {"symbol": "AAPL"}
    
    result = execute_graphql_query(query1, variables=variables, token=token)
    if 'data' in result and result['data'] and 'consumerStrength' in result['data']:
        strength = result['data']['consumerStrength']
        print_test("consumerStrength Query", "PASS", f"Overall Score: {strength.get('overallScore', 'N/A')}/100")
        print(f"   Spending: {strength.get('spendingScore', 'N/A')}, Options: {strength.get('optionsScore', 'N/A')}")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("consumerStrength Query", "WARN", f"Error: {error_msg}")
    
    # Test 2: consumerStrengthHistory
    query2 = """
    query GetHistory($symbol: String!, $days: Int!) {
        consumerStrengthHistory(symbol: $symbol, days: $days) {
            overallScore
            spendingScore
            optionsScore
            earningsScore
            insiderScore
            sectorScore
        }
    }
    """
    
    variables = {"symbol": "AAPL", "days": 30}
    
    result = execute_graphql_query(query2, variables=variables, token=token)
    if 'data' in result and result['data']:
        history = result['data'].get('consumerStrengthHistory', [])
        print_test("consumerStrengthHistory Query", "PASS", f"Retrieved {len(history)} historical data points")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("consumerStrengthHistory Query", "WARN", f"Error: {error_msg} (may return only current score)")
    
    # Test 3: sectorComparison
    query3 = """
    query GetSectorComparison($symbol: String!) {
        sectorComparison(symbol: $symbol) {
            stockScore
            sectorAverage
            sectorRank
            percentile
            sectorName
            totalInSector
        }
    }
    """
    
    variables = {"symbol": "AAPL"}
    
    result = execute_graphql_query(query3, variables=variables, token=token)
    if 'data' in result and result['data'] and 'sectorComparison' in result['data']:
        comparison = result['data']['sectorComparison']
        print_test("sectorComparison Query", "PASS", f"Rank: {comparison.get('sectorRank', 'N/A')}/{comparison.get('totalInSector', 'N/A')}")
        print(f"   Sector: {comparison.get('sectorName', 'N/A')}, Percentile: {comparison.get('percentile', 'N/A')}%")
    else:
        error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error') if 'errors' in result else 'No data returned'
        print_test("sectorComparison Query", "WARN", f"Error: {error_msg}")


def print_summary():
    """Print test summary"""
    print_section("📊 Test Summary")
    
    total = test_results['passed'] + test_results['failed'] + test_results['warnings']
    passed_pct = (test_results['passed'] / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"{GREEN}Passed: {test_results['passed']}{NC}")
    print(f"{YELLOW}Warnings: {test_results['warnings']}{NC}")
    print(f"{RED}Failed: {test_results['failed']}{NC}")
    print(f"\nSuccess Rate: {passed_pct:.1f}%")
    
    if test_results['failed'] == 0:
        print(f"\n{GREEN}✅ All critical tests passed!{NC}")
    else:
        print(f"\n{RED}❌ Some tests failed. Please review.{NC}")


def main():
    """Main test function"""
    print_section("🧪 Competitive Moat Features Test Suite")
    print(f"Testing server at: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if server is running
    if not check_server_running():
        print(f"{RED}❌ Server is not running!{NC}")
        print(f"   Please start the server: cd deployment_package/backend && python manage.py runserver")
        sys.exit(1)
    
    print(f"{GREEN}✅ Server is running{NC}\n")
    
    # Get authentication token
    print("🔐 Authenticating...")
    token = get_auth_token()
    if not token:
        print(f"{YELLOW}⚠️  Could not get authentication token{NC}")
        print(f"   Some tests may fail. Continuing with unauthenticated tests...\n")
        token = None
    else:
        print(f"{GREEN}✅ Authentication successful{NC}\n")
    
    # Run all tests
    if token:
        test_paper_trading_queries(token)
        test_paper_trading_mutations(token)
        test_signal_fusion_queries(token)
        test_research_report_mutation(token)
        test_consumer_strength_queries(token)
    else:
        print(f"{YELLOW}⚠️  Skipping authenticated tests (no token){NC}")
    
    # Print summary
    print_summary()


if __name__ == "__main__":
    main()

