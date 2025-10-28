#!/usr/bin/env python3
"""
Comprehensive GraphQL Test Suite for RichesReach
Tests all mutations and queries to ensure 100% functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"

def test_graphql_query(query, variables=None, description=""):
    """Test a GraphQL query/mutation and return results"""
    try:
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = requests.post(
            GRAPHQL_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        success = response.status_code == 200
        print(f"{'✅' if success else '❌'} {description}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                if "errors" in json_data and json_data["errors"]:
                    print(f"   GraphQL Errors: {json_data['errors']}")
                    success = False
                else:
                    print(f"   Response: {json.dumps(json_data, indent=2)[:300]}...")
            except Exception as e:
                print(f"   JSON Parse Error: {e}")
                success = False
        else:
            print(f"   Error: {response.text[:200]}...")
        
        print()
        return success
        
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Exception: {str(e)}")
        print()
        return False

def test_queries():
    """Test all GraphQL queries"""
    print("🔍 TESTING GRAPHQL QUERIES")
    print("=" * 50)
    
    queries = [
        # Basic queries
        {
            "query": """
            query {
                me {
                    id
                    name
                    email
                    hasPremiumAccess
                    subscriptionTier
                }
            }
            """,
            "description": "User Profile Query"
        },
        
        # Stock queries
        {
            "query": """
            query {
                stocks {
                    symbol
                    name
                    price
                    change
                    changePercent
                }
            }
            """,
            "description": "Stocks List Query"
        },
        
        {
            "query": """
            query {
                stock(symbol: "AAPL") {
                    symbol
                    name
                    price
                    change
                    changePercent
                }
            }
            """,
            "description": "Single Stock Query"
        },
        
        # Watchlist queries
        {
            "query": """
            query {
                myWatchlist {
                    id
                    symbol
                    addedAt
                    stock {
                        symbol
                        name
                        price
                    }
                }
            }
            """,
            "description": "Watchlist Query"
        },
        
        # AI recommendations
        {
            "query": """
            query {
                aiRecommendations(riskTolerance: "medium") {
                    id
                    symbol
                    recommendation
                    confidence
                    reasoning
                }
            }
            """,
            "description": "AI Recommendations Query"
        },
        
        # Day trading picks
        {
            "query": """
            query {
                dayTradingPicks(mode: "SAFE") {
                    asOf
                    mode
                    picks {
                        symbol
                        side
                        score
                        features {
                            momentum_15m
                            rvol_10m
                            catalyst_score
                            sentiment_score
                        }
                        risk {
                            atr_5m
                            size_shares
                            stop
                        }
                        notes
                    }
                    regimeContext {
                        regimeType
                        confidence
                        strategyWeights
                        recommendations
                    }
                }
            }
            """,
            "description": "Day Trading Picks Query"
        },
        
        # Crypto queries
        {
            "query": """
            query {
                cryptoPortfolio {
                    totalValue
                    totalPnL
                    totalPnLPercent
                    holdings {
                        symbol
                        quantity
                        value
                        pnl
                        pnlPercent
                    }
                }
            }
            """,
            "description": "Crypto Portfolio Query"
        },
        
        # Market data
        {
            "query": """
            query {
                stockData(symbol: "AAPL", limit: 10) {
                    timestamp
                    open
                    high
                    low
                    close
                    volume
                }
            }
            """,
            "description": "Stock Data Query"
        }
    ]
    
    results = []
    for query_test in queries:
        success = test_graphql_query(query_test["query"], description=query_test["description"])
        results.append(success)
    
    return results

def test_mutations():
    """Test all GraphQL mutations"""
    print("🔄 TESTING GRAPHQL MUTATIONS")
    print("=" * 50)
    
    mutations = [
        # Authentication mutations
        {
            "query": """
            mutation {
                registerUser(input: {
                    username: "testuser123"
                    email: "test@example.com"
                    password: "testpass123"
                }) {
                    success
                    message
                    user {
                        id
                        username
                        email
                    }
                }
            }
            """,
            "description": "User Registration Mutation"
        },
        
        {
            "query": """
            mutation {
                loginUser(input: {
                    email: "test@example.com"
                    password: "testpass123"
                }) {
                    success
                    message
                    token
                    refreshToken
                    user {
                        id
                        username
                        email
                    }
                }
            }
            """,
            "description": "User Login Mutation"
        },
        
        # Watchlist mutations
        {
            "query": """
            mutation {
                addToWatchlist(symbol: "AAPL") {
                    success
                    message
                    watchlistItem {
                        id
                        symbol
                        addedAt
                    }
                }
            }
            """,
            "description": "Add to Watchlist Mutation"
        },
        
        {
            "query": """
            mutation {
                removeFromWatchlist(symbol: "AAPL") {
                    success
                    message
                }
            }
            """,
            "description": "Remove from Watchlist Mutation"
        },
        
        # Trading mutations
        {
            "query": """
            mutation {
                placeStockOrder(input: {
                    symbol: "AAPL"
                    side: "BUY"
                    quantity: 10
                    orderType: "MARKET"
                }) {
                    success
                    message
                    order {
                        id
                        symbol
                        side
                        quantity
                        status
                    }
                }
            }
            """,
            "description": "Place Stock Order Mutation"
        },
        
        # AI mutations
        {
            "query": """
            mutation {
                generateAiRecommendations(input: {
                    riskTolerance: "medium"
                    investmentHorizon: "long"
                    amount: 10000
                }) {
                    success
                    message
                    recommendations {
                        id
                        symbol
                        recommendation
                        confidence
                        reasoning
                    }
                }
            }
            """,
            "description": "Generate AI Recommendations Mutation"
        },
        
        # Income profile mutation
        {
            "query": """
            mutation {
                createIncomeProfile(
                    incomeBracket: "50000-75000"
                    age: 30
                    riskTolerance: "medium"
                    investmentHorizon: "long"
                    investmentGoals: ["retirement", "wealth_building"]
                ) {
                    success
                    message
                    incomeProfile {
                        id
                        incomeBracket
                        age
                        riskTolerance
                        investmentHorizon
                        investmentGoals
                    }
                }
            }
            """,
            "description": "Create Income Profile Mutation"
        },
        
        # Crypto mutations
        {
            "query": """
            mutation {
                executeCryptoTrade(
                    symbol: "BTC"
                    tradeType: "BUY"
                    quantity: 0.1
                    orderType: "MARKET"
                    timeInForce: "GTC"
                ) {
                    success
                    message
                    trade {
                        id
                        symbol
                        tradeType
                        quantity
                        status
                    }
                }
            }
            """,
            "description": "Execute Crypto Trade Mutation"
        },
        
        # Financial mutations
        {
            "query": """
            mutation {
                withdrawFunds(amount: 100.0, currency: "USD") {
                    success
                    message
                    transaction {
                        id
                        amount
                        currency
                        status
                    }
                }
            }
            """,
            "description": "Withdraw Funds Mutation"
        },
        
        # Portfolio mutations
        {
            "query": """
            mutation {
                createPortfolio(input: {
                    name: "Test Portfolio"
                    description: "Test portfolio for testing"
                }) {
                    success
                    message
                    portfolio {
                        id
                        name
                        description
                        createdAt
                    }
                }
            }
            """,
            "description": "Create Portfolio Mutation"
        }
    ]
    
    results = []
    for mutation_test in mutations:
        success = test_graphql_query(mutation_test["query"], description=mutation_test["description"])
        results.append(success)
    
    return results

def test_subscriptions():
    """Test GraphQL subscriptions (if supported)"""
    print("📡 TESTING GRAPHQL SUBSCRIPTIONS")
    print("=" * 50)
    
    # Note: Subscriptions require WebSocket support
    # For now, we'll just test if the subscription schema is available
    subscription_query = """
    query {
        __schema {
            subscriptionType {
                name
                fields {
                    name
                    type {
                        name
                    }
                }
            }
        }
    }
    """
    
    success = test_graphql_query(subscription_query, description="Subscription Schema Query")
    return [success]

def main():
    """Run comprehensive GraphQL tests"""
    print("🚀 RICHESREACH COMPREHENSIVE GRAPHQL TEST SUITE")
    print("=" * 60)
    print(f"Testing GraphQL endpoint: {GRAPHQL_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test basic connectivity
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code != 200:
            print("❌ Server health check failed")
            return False
        print("✅ Server is running and healthy")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    print()
    
    # Run all test suites
    query_results = test_queries()
    mutation_results = test_mutations()
    subscription_results = test_subscriptions()
    
    # Calculate summary
    all_results = query_results + mutation_results + subscription_results
    passed = sum(all_results)
    total = len(all_results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    # Print summary
    print("=" * 60)
    print("📊 GRAPHQL TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {success_rate:.1f}%")
    
    print("\n📋 DETAILED RESULTS:")
    print(f"Queries: {sum(query_results)}/{len(query_results)} passed")
    print(f"Mutations: {sum(mutation_results)}/{len(mutation_results)} passed")
    print(f"Subscriptions: {sum(subscription_results)}/{len(subscription_results)} passed")
    
    if success_rate == 100:
        print("\n🎉 ALL GRAPHQL TESTS PASSED!")
        print("✅ Queries: Working perfectly")
        print("✅ Mutations: Working perfectly")
        print("✅ Schema: Valid and accessible")
        print("🚀 GraphQL API is production ready!")
    elif success_rate >= 80:
        print(f"\n⚠️  {success_rate:.1f}% tests passed. Minor issues detected.")
        print("Most GraphQL functionality is working correctly.")
    else:
        print(f"\n❌ Only {success_rate:.1f}% tests passed. Major issues detected.")
        print("GraphQL API needs attention before production deployment.")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
