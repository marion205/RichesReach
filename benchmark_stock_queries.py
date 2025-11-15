#!/usr/bin/env python3
"""
Benchmark Test for Stock Data Queries
Tests how long it takes to fetch data for random stocks
"""

import requests
import json
import time
import random
import statistics
from typing import List, Dict, Any
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
GRAPHQL_URL = f"{API_BASE_URL}/graphql/"
TIMEOUT = 30  # seconds

# Popular stock symbols for testing
STOCK_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ",
    "WMT", "PG", "MA", "UNH", "HD", "DIS", "BAC", "ADBE", "NFLX", "CRM",
    "PYPL", "INTC", "AMD", "NKE", "SBUX", "COST", "TMO", "ABBV", "AVGO", "ACN"
]

def benchmark_rest_endpoint(endpoint: str, method: str = "GET", data: Dict = None, iterations: int = 10) -> Dict[str, Any]:
    """Benchmark a REST endpoint"""
    times = []
    errors = 0
    successes = 0
    
    for i in range(iterations):
        try:
            start = time.time()
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=TIMEOUT)
            elif method == "POST":
                response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=TIMEOUT)
            else:
                continue
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                times.append(elapsed)
                successes += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
            print(f"  Error on iteration {i+1}: {e}")
    
    if not times:
        return {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "successes": successes,
            "errors": errors,
            "avg_time": None,
            "min_time": None,
            "max_time": None,
            "median_time": None,
            "p95_time": None,
        }
    
    return {
        "endpoint": endpoint,
        "method": method,
        "iterations": iterations,
        "successes": successes,
        "errors": errors,
        "avg_time": statistics.mean(times),
        "min_time": min(times),
        "max_time": max(times),
        "median_time": statistics.median(times),
        "p95_time": sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
        "all_times": times,
    }

def benchmark_graphql_query(query_name: str, query: str, variables: Dict = None, iterations: int = 10) -> Dict[str, Any]:
    """Benchmark a GraphQL query"""
    times = []
    errors = 0
    successes = 0
    
    for i in range(iterations):
        try:
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            start = time.time()
            response = requests.post(
                GRAPHQL_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                if "errors" not in result or not result["errors"]:
                    times.append(elapsed)
                    successes += 1
                else:
                    errors += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
            print(f"  Error on iteration {i+1}: {e}")
    
    if not times:
        return {
            "query": query_name,
            "iterations": iterations,
            "successes": successes,
            "errors": errors,
            "avg_time": None,
            "min_time": None,
            "max_time": None,
            "median_time": None,
            "p95_time": None,
        }
    
    return {
        "query": query_name,
        "iterations": iterations,
        "successes": successes,
        "errors": errors,
        "avg_time": statistics.mean(times),
        "min_time": min(times),
        "max_time": max(times),
        "median_time": statistics.median(times),
        "p95_time": sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
        "all_times": times,
    }

def main():
    print("🚀 Stock Data Benchmark Test")
    print("=" * 80)
    print(f"Testing against: {API_BASE_URL}")
    print(f"Iterations per test: 10")
    print(f"Random stocks: {len(STOCK_SYMBOLS)} symbols")
    print()
    
    results = []
    
    # Test 1: REST - Market Quotes (single random stock)
    print("📡 Testing REST Endpoints...")
    print("-" * 80)
    
    random_symbol = random.choice(STOCK_SYMBOLS)
    print(f"1. Market Quotes (single stock: {random_symbol})")
    result = benchmark_rest_endpoint(f"/api/market/quotes?symbols={random_symbol}", iterations=10)
    results.append(result)
    if result["avg_time"]:
        print(f"   ✅ Avg: {result['avg_time']*1000:.2f}ms | Min: {result['min_time']*1000:.2f}ms | Max: {result['max_time']*1000:.2f}ms | P95: {result['p95_time']*1000:.2f}ms")
    else:
        print(f"   ❌ Failed: {result['errors']} errors")
    
    # Test 2: REST - Trading Quote
    print(f"2. Trading Quote ({random_symbol})")
    result = benchmark_rest_endpoint(f"/api/trading/quote/{random_symbol}", iterations=10)
    results.append(result)
    if result["avg_time"]:
        print(f"   ✅ Avg: {result['avg_time']*1000:.2f}ms | Min: {result['min_time']*1000:.2f}ms | Max: {result['max_time']*1000:.2f}ms | P95: {result['p95_time']*1000:.2f}ms")
    else:
        print(f"   ❌ Failed: {result['errors']} errors")
    
    print()
    print("📊 Testing GraphQL Queries...")
    print("-" * 80)
    
    # Test 3: GraphQL - Stock query (random stock)
    random_symbol = random.choice(STOCK_SYMBOLS)
    print(f"3. GraphQL: Stock Query ({random_symbol})")
    result = benchmark_graphql_query(
        "stock",
        """
        query GetStock($symbol: String!) {
            stock(symbol: $symbol) {
                id
                symbol
                companyName
                currentPrice
                sector
                marketCap
                peRatio
                dividendYield
                beginnerFriendlyScore
            }
        }
        """,
        {"symbol": random_symbol},
        iterations=10
    )
    results.append(result)
    if result["avg_time"]:
        print(f"   ✅ Avg: {result['avg_time']*1000:.2f}ms | Min: {result['min_time']*1000:.2f}ms | Max: {result['max_time']*1000:.2f}ms | P95: {result['p95_time']*1000:.2f}ms")
    else:
        print(f"   ❌ Failed: {result['errors']} errors")
    
    # Test 4: GraphQL - Stock Chart Data
    random_symbol = random.choice(STOCK_SYMBOLS)
    print(f"4. GraphQL: Stock Chart Data ({random_symbol})")
    result = benchmark_graphql_query(
        "stockChartData",
        """
        query GetChartData($symbol: String!, $timeframe: String!) {
            stockChartData(symbol: $symbol, timeframe: $timeframe) {
                currentPrice
                changePercent
                data {
                    timestamp
                    open
                    high
                    low
                    close
                    volume
                }
                indicators {
                    SMA20
                    SMA50
                    RSI
                    MACD
                }
            }
        }
        """,
        {"symbol": random_symbol, "timeframe": "1D"},
        iterations=10
    )
    results.append(result)
    if result["avg_time"]:
        print(f"   ✅ Avg: {result['avg_time']*1000:.2f}ms | Min: {result['min_time']*1000:.2f}ms | Max: {result['max_time']*1000:.2f}ms | P95: {result['p95_time']*1000:.2f}ms")
    else:
        print(f"   ❌ Failed: {result['errors']} errors")
    
    # Test 5: GraphQL - Research Hub
    random_symbol = random.choice(STOCK_SYMBOLS)
    print(f"5. GraphQL: Research Hub ({random_symbol})")
    result = benchmark_graphql_query(
        "researchHub",
        """
        query GetResearchHub($symbol: String!) {
            researchHub(symbol: $symbol) {
                symbol
                company {
                    name
                    sector
                    marketCap
                }
                quote {
                    price
                    change
                    changePercent
                }
                technicals {
                    rsi
                    macd
                    movingAverage50
                }
            }
        }
        """,
        {"symbol": random_symbol},
        iterations=10
    )
    results.append(result)
    if result["avg_time"]:
        print(f"   ✅ Avg: {result['avg_time']*1000:.2f}ms | Min: {result['min_time']*1000:.2f}ms | Max: {result['max_time']*1000:.2f}ms | P95: {result['p95_time']*1000:.2f}ms")
    else:
        print(f"   ❌ Failed: {result['errors']} errors")
    
    # Test 6: GraphQL - Stock Moments
    random_symbol = random.choice(STOCK_SYMBOLS)
    print(f"6. GraphQL: Stock Moments ({random_symbol})")
    result = benchmark_graphql_query(
        "stockMoments",
        """
        query GetStockMoments($symbol: String!, $range: ChartRangeEnum!) {
            stockMoments(symbol: $symbol, range: $range) {
                id
                symbol
                timestamp
                title
                quickSummary
                category
                importanceScore
            }
        }
        """,
        {"symbol": random_symbol, "range": "ONE_MONTH"},
        iterations=10
    )
    results.append(result)
    if result["avg_time"]:
        print(f"   ✅ Avg: {result['avg_time']*1000:.2f}ms | Min: {result['min_time']*1000:.2f}ms | Max: {result['max_time']*1000:.2f}ms | P95: {result['p95_time']*1000:.2f}ms")
    else:
        print(f"   ❌ Failed: {result['errors']} errors")
    
    # Test 7: GraphQL - Rust Stock Analysis
    random_symbol = random.choice(STOCK_SYMBOLS)
    print(f"7. GraphQL: Rust Stock Analysis ({random_symbol})")
    result = benchmark_graphql_query(
        "rustStockAnalysis",
        """
        query GetRustAnalysis($symbol: String!) {
            rustStockAnalysis(symbol: $symbol) {
                symbol
                recommendation
                riskLevel
                beginnerFriendlyScore
                reasoning
                technicalIndicators {
                    rsi
                    macd
                    sma20
                    sma50
                }
            }
        }
        """,
        {"symbol": random_symbol},
        iterations=10
    )
    results.append(result)
    if result["avg_time"]:
        print(f"   ✅ Avg: {result['avg_time']*1000:.2f}ms | Min: {result['min_time']*1000:.2f}ms | Max: {result['max_time']*1000:.2f}ms | P95: {result['p95_time']*1000:.2f}ms")
    else:
        print(f"   ❌ Failed: {result['errors']} errors")
    
    # Test 8: GraphQL - Stocks List (search)
    random_symbol = random.choice(STOCK_SYMBOLS)
    print(f"8. GraphQL: Stocks List (search: {random_symbol})")
    result = benchmark_graphql_query(
        "stocks",
        """
        query GetStocks($search: String!) {
            stocks(search: $search) {
                id
                symbol
                companyName
                currentPrice
                sector
                beginnerFriendlyScore
            }
        }
        """,
        {"search": random_symbol},
        iterations=10
    )
    results.append(result)
    if result["avg_time"]:
        print(f"   ✅ Avg: {result['avg_time']*1000:.2f}ms | Min: {result['min_time']*1000:.2f}ms | Max: {result['max_time']*1000:.2f}ms | P95: {result['p95_time']*1000:.2f}ms")
    else:
        print(f"   ❌ Failed: {result['errors']} errors")
    
    print()
    print("=" * 80)
    print("📊 Benchmark Summary")
    print("=" * 80)
    print()
    
    # Calculate statistics
    successful_tests = [r for r in results if r.get("avg_time") is not None]
    failed_tests = [r for r in results if r.get("avg_time") is None]
    
    if successful_tests:
        avg_times = [r["avg_time"] for r in successful_tests]
        print(f"✅ Successful Tests: {len(successful_tests)}/{len(results)}")
        print(f"❌ Failed Tests: {len(failed_tests)}")
        print()
        print("Performance Metrics:")
        print(f"  Fastest Query: {min(avg_times)*1000:.2f}ms ({[r.get('endpoint') or r.get('query') for r in successful_tests if r['avg_time'] == min(avg_times)][0]})")
        print(f"  Slowest Query: {max(avg_times)*1000:.2f}ms ({[r.get('endpoint') or r.get('query') for r in successful_tests if r['avg_time'] == max(avg_times)][0]})")
        print(f"  Average Across All: {statistics.mean(avg_times)*1000:.2f}ms")
        print(f"  Median: {statistics.median(avg_times)*1000:.2f}ms")
        print()
        
        print("Detailed Results:")
        print("-" * 80)
        for result in successful_tests:
            name = result.get("endpoint") or result.get("query", "Unknown")
            print(f"{name[:50]:<50} | Avg: {result['avg_time']*1000:>7.2f}ms | P95: {result['p95_time']*1000:>7.2f}ms")
    
    if failed_tests:
        print()
        print("Failed Tests:")
        for result in failed_tests:
            name = result.get("endpoint") or result.get("query", "Unknown")
            print(f"  ❌ {name}: {result['errors']} errors")
    
    # Save results to file
    results_file = "benchmark_stock_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(results),
                "successful": len(successful_tests),
                "failed": len(failed_tests),
            },
            "results": results,
        }, f, indent=2)
    print()
    print(f"💾 Detailed results saved to {results_file}")

if __name__ == "__main__":
    main()

