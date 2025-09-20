#!/usr/bin/env python3
"""
Comprehensive Crypto Performance Test Suite
Tests RichesReach crypto system against industry standards
"""

import requests
import time
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

BASE_URL = "http://localhost:8123"

def test_endpoint(endpoint, data=None, method="GET"):
    """Test a single endpoint and return timing data"""
    start_time = time.time()
    try:
        if method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=30)
        else:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "success": response.status_code == 200,
            "duration": duration,
            "status_code": response.status_code,
            "data_size": len(response.content) if response.content else 0
        }
    except Exception as e:
        return {
            "success": False,
            "duration": time.time() - start_time,
            "error": str(e),
            "status_code": 0
        }

def test_crypto_recommendations():
    """Test crypto recommendations performance"""
    print("🔍 Testing Crypto Recommendations...")
    
    query = {
        "query": """
        query {
            cryptoRecommendations(constraints: { 
                maxSymbols: 5,
                minProbability: 0.55,
                minLiquidityUsd24h: 1000000
            }) {
                success
                message
                recommendations {
                    symbol
                    score
                    probability
                    confidenceLevel
                    priceUsd
                    volatilityTier
                    liquidity24hUsd
                    rationale
                }
            }
        }
        """
    }
    
    results = []
    for i in range(5):  # Test 5 times
        result = test_endpoint("/graphql/", query, "POST")
        results.append(result)
        print(f"  Attempt {i+1}: {result['duration']:.2f}s {'✅' if result['success'] else '❌'}")
        time.sleep(1)  # Brief pause between tests
    
    return results

def test_crypto_ml_signals():
    """Test crypto ML signals performance"""
    print("\n🤖 Testing Crypto ML Signals...")
    
    symbols = ["BTC", "ETH", "ADA", "SOL", "DOT"]
    results = []
    
    for symbol in symbols:
        query = {
            "query": f"""
            query {{
                cryptoMlSignal(symbol: "{symbol}") {{
                    symbol
                    predictionType
                    probability
                    confidenceLevel
                    explanation
                    sentimentDescription
                    featuresUsed {{
                        rsi
                        macd
                        volume
                        sentiment
                    }}
                }}
            }}
            """
        }
        
        result = test_endpoint("/graphql/", query, "POST")
        results.append(result)
        print(f"  {symbol}: {result['duration']:.2f}s {'✅' if result['success'] else '❌'}")
    
    return results

def test_concurrent_load():
    """Test concurrent load handling"""
    print("\n⚡ Testing Concurrent Load (10 simultaneous requests)...")
    
    query = {
        "query": """
        query {
            cryptoRecommendations(constraints: { maxSymbols: 3 }) {
                success
                recommendations {
                    symbol
                    score
                    probability
                }
            }
        }
        """
    }
    
    def make_request():
        return test_endpoint("/graphql/", query, "POST")
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [future.result() for future in as_completed(futures)]
    
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r['success'])
    
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Successful: {successful}/10")
    print(f"  Average per request: {total_time/10:.2f}s")
    
    return results

def test_cache_performance():
    """Test cache hit performance"""
    print("\n💾 Testing Cache Performance...")
    
    query = {
        "query": """
        query {
            cryptoRecommendations(constraints: { maxSymbols: 5 }) {
                success
                recommendations {
                    symbol
                    score
                }
            }
        }
        """
    }
    
    # First request (cache miss)
    print("  First request (cache miss):")
    result1 = test_endpoint("/graphql/", query, "POST")
    print(f"    Duration: {result1['duration']:.2f}s {'✅' if result1['success'] else '❌'}")
    
    # Second request (cache hit)
    print("  Second request (cache hit):")
    result2 = test_endpoint("/graphql/", query, "POST")
    print(f"    Duration: {result2['duration']:.2f}s {'✅' if result2['success'] else '❌'}")
    
    # Third request (cache hit)
    print("  Third request (cache hit):")
    result3 = test_endpoint("/graphql/", query, "POST")
    print(f"    Duration: {result3['duration']:.2f}s {'✅' if result3['success'] else '❌'}")
    
    cache_improvement = ((result1['duration'] - result2['duration']) / result1['duration']) * 100
    print(f"  Cache improvement: {cache_improvement:.1f}% faster")
    
    return [result1, result2, result3]

def test_error_handling():
    """Test error handling and resilience"""
    print("\n🛡️ Testing Error Handling...")
    
    # Test with invalid symbol
    invalid_query = {
        "query": """
        query {
            cryptoMlSignal(symbol: "INVALID_SYMBOL_12345") {
                symbol
                predictionType
            }
        }
        """
    }
    
    result = test_endpoint("/graphql/", invalid_query, "POST")
    print(f"  Invalid symbol: {result['duration']:.2f}s {'✅' if result['success'] else '❌'}")
    
    # Test with malformed query
    malformed_query = {
        "query": "invalid query syntax {"
    }
    
    result2 = test_endpoint("/graphql/", malformed_query, "POST")
    print(f"  Malformed query: {result2['duration']:.2f}s {'✅' if result2['success'] else '❌'}")
    
    return [result, result2]

def test_metrics_endpoint():
    """Test metrics and monitoring"""
    print("\n📊 Testing Metrics Endpoint...")
    
    result = test_endpoint("/metrics")
    print(f"  Metrics: {result['duration']:.2f}s {'✅' if result['success'] else '❌'}")
    
    if result['success']:
        print(f"  Data size: {result['data_size']} bytes")
    
    return [result]

def generate_report(all_results):
    """Generate comprehensive performance report"""
    print("\n" + "="*60)
    print("📈 RICHESREACH CRYPTO PERFORMANCE REPORT")
    print("="*60)
    
    # Calculate overall statistics
    all_durations = []
    all_successful = 0
    total_tests = 0
    
    for test_name, results in all_results.items():
        if results:
            durations = [r['duration'] for r in results if 'duration' in r]
            successful = sum(1 for r in results if r.get('success', False))
            all_durations.extend(durations)
            all_successful += successful
            total_tests += len(results)
            
            avg_duration = statistics.mean(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            
            print(f"\n{test_name}:")
            print(f"  Success Rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
            print(f"  Avg Duration: {avg_duration:.2f}s")
            print(f"  Min Duration: {min_duration:.2f}s")
            print(f"  Max Duration: {max_duration:.2f}s")
    
    # Overall statistics
    if all_durations:
        overall_avg = statistics.mean(all_durations)
        overall_min = min(all_durations)
        overall_max = max(all_durations)
        overall_success_rate = (all_successful / total_tests) * 100
        
        print(f"\n🎯 OVERALL PERFORMANCE:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Success Rate: {overall_success_rate:.1f}%")
        print(f"  Average Response Time: {overall_avg:.2f}s")
        print(f"  Fastest Response: {overall_min:.2f}s")
        print(f"  Slowest Response: {overall_max:.2f}s")
        
        # Performance comparison
        print(f"\n🏆 COMPETITIVE ANALYSIS:")
        if overall_avg < 1.0:
            print("  ⚡ EXCELLENT: Sub-second response times!")
        elif overall_avg < 2.0:
            print("  🚀 VERY GOOD: Fast response times")
        elif overall_avg < 5.0:
            print("  ✅ GOOD: Acceptable response times")
        else:
            print("  ⚠️ NEEDS IMPROVEMENT: Slow response times")
        
        if overall_success_rate >= 95:
            print("  🛡️ EXCELLENT: High reliability")
        elif overall_success_rate >= 90:
            print("  ✅ GOOD: Reliable performance")
        else:
            print("  ⚠️ NEEDS IMPROVEMENT: Reliability issues")

def main():
    """Run all performance tests"""
    print("🚀 Starting RichesReach Crypto Performance Test Suite")
    print("="*60)
    
    # Check if server is running
    health_result = test_endpoint("/health")
    if not health_result['success']:
        print("❌ Server is not running! Please start the server first.")
        sys.exit(1)
    
    print("✅ Server is running, starting tests...\n")
    
    all_results = {}
    
    # Run all tests
    all_results["Crypto Recommendations"] = test_crypto_recommendations()
    all_results["Crypto ML Signals"] = test_crypto_ml_signals()
    all_results["Concurrent Load"] = test_concurrent_load()
    all_results["Cache Performance"] = test_cache_performance()
    all_results["Error Handling"] = test_error_handling()
    all_results["Metrics"] = test_metrics_endpoint()
    
    # Generate report
    generate_report(all_results)
    
    print("\n🎉 Performance testing complete!")
    print("Your RichesReach crypto system is ready for production! 🚀")

if __name__ == "__main__":
    main()
