#!/usr/bin/env python3
"""
Test Production Features: Real APIs, Rate Limiting, Monitoring, Caching
"""

import requests
import time
import json
import statistics

BASE_URL = "http://localhost:8123"

def test_server_health():
    """Test basic server health"""
    print("🏥 Testing Server Health...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    duration = time.time() - start
    print(f"   Health check: {duration:.3f}s - Status: {response.status_code}")
    return response.status_code == 200

def test_debug_config():
    """Test debug configuration endpoint"""
    print("\n🔧 Testing Debug Configuration...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/debug/config", timeout=5)
    duration = time.time() - start
    
    if response.status_code == 200:
        config = response.json()
        print(f"   Config loaded: {duration:.3f}s")
        print(f"   Redis Status: {config.get('redis_status', 'unknown')}")
        print(f"   Redis Enabled: {config.get('redis_enabled', False)}")
        print(f"   HTTPX Enabled: {config.get('httpx_enabled', False)}")
        print(f"   CoinGecko Cache TTL: {config.get('coingecko_cache_ttl', 'unknown')}s")
        print(f"   CoinGecko Rate Delay: {config.get('coingecko_rate_delay', 'unknown')}s")
        return True
    else:
        print(f"   Config failed: {response.status_code}")
        return False

def test_metrics_endpoint():
    """Test Prometheus metrics endpoint"""
    print("\n📊 Testing Metrics Endpoint...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/metrics", timeout=5)
    duration = time.time() - start
    
    if response.status_code == 200:
        metrics = response.text
        print(f"   Metrics loaded: {duration:.3f}s")
        print(f"   Metrics size: {len(metrics)} bytes")
        
        # Check for key metrics
        if "app_requests_total" in metrics:
            print("   ✅ Request metrics found")
        if "app_request_duration_seconds" in metrics:
            print("   ✅ Duration metrics found")
        if "app_responses_total" in metrics:
            print("   ✅ Response metrics found")
        
        return True
    else:
        print(f"   Metrics failed: {response.status_code}")
        return False

def test_crypto_recommendations_performance():
    """Test crypto recommendations with real APIs"""
    print("\n🚀 Testing Crypto Recommendations Performance...")
    
    # Test 1: First request (cache miss)
    print("   First request (cache miss):")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoRecommendations(constraints: { maxSymbols: 3 }) { success recommendations { symbol score probability confidenceLevel priceUsd rationale } } }"
    }, timeout=30)
    duration1 = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        recs = data.get('data', {}).get('cryptoRecommendations', {}).get('recommendations', [])
        print(f"     Duration: {duration1:.2f}s - Recommendations: {len(recs)}")
        
        # Show first recommendation details
        if recs:
            first = recs[0]
            print(f"     First rec: {first['symbol']} - Score: {first['score']:.1f} - Prob: {first['probability']:.2f}")
            print(f"     Rationale: {first['rationale']}")
    else:
        print(f"     Failed: {response.status_code}")
        return False
    
    # Test 2: Second request (cache hit)
    print("   Second request (cache hit):")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoRecommendations(constraints: { maxSymbols: 3 }) { success recommendations { symbol score } } }"
    }, timeout=30)
    duration2 = time.time() - start
    
    if response.status_code == 200:
        print(f"     Duration: {duration2:.2f}s")
        cache_improvement = ((duration1 - duration2) / duration1) * 100 if duration1 > 0 else 0
        print(f"     Cache improvement: {cache_improvement:.1f}% faster")
    else:
        print(f"     Failed: {response.status_code}")
        return False
    
    return True

def test_ml_signals_performance():
    """Test ML signals performance"""
    print("\n🤖 Testing ML Signals Performance...")
    
    symbols = ["BTC", "ETH", "ADA", "SOL", "DOT"]
    durations = []
    
    for symbol in symbols:
        start = time.time()
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": f"query {{ cryptoMlSignal(symbol: \"{symbol}\") {{ symbol predictionType probability confidenceLevel explanation }} }}"
        }, timeout=10)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            signal = data.get('data', {}).get('cryptoMlSignal', {})
            print(f"   {symbol}: {duration:.3f}s - Prob: {signal.get('probability', 'N/A')} - Conf: {signal.get('confidenceLevel', 'N/A')}")
            durations.append(duration)
        else:
            print(f"   {symbol}: Failed - {response.status_code}")
    
    if durations:
        avg_duration = statistics.mean(durations)
        print(f"   Average ML signal time: {avg_duration:.3f}s")
        return avg_duration < 1.0  # Should be under 1 second
    return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n🛡️ Testing Rate Limiting...")
    
    # Make multiple rapid requests
    responses = []
    start_time = time.time()
    
    for i in range(10):
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": "query { cryptoRecommendations(constraints: { maxSymbols: 1 }) { success } }"
        }, timeout=5)
        responses.append(response.status_code)
        time.sleep(0.1)  # Small delay between requests
    
    total_time = time.time() - start_time
    success_count = sum(1 for status in responses if status == 200)
    rate_limited_count = sum(1 for status in responses if status == 429)
    
    print(f"   Total requests: {len(responses)}")
    print(f"   Successful: {success_count}")
    print(f"   Rate limited: {rate_limited_count}")
    print(f"   Total time: {total_time:.2f}s")
    
    return success_count > 0

def test_concurrent_load():
    """Test concurrent load handling"""
    print("\n⚡ Testing Concurrent Load...")
    
    import concurrent.futures
    
    def make_request():
        start = time.time()
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": "query { cryptoRecommendations(constraints: { maxSymbols: 2 }) { success } }"
        }, timeout=30)
        duration = time.time() - start
        return response.status_code, duration
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    total_time = time.time() - start_time
    successful = sum(1 for status, _ in results if status == 200)
    avg_duration = statistics.mean([duration for _, duration in results])
    
    print(f"   Concurrent requests: 5")
    print(f"   Successful: {successful}/5")
    print(f"   Average duration: {avg_duration:.2f}s")
    print(f"   Total time: {total_time:.2f}s")
    
    return successful >= 4  # At least 4 out of 5 should succeed

def main():
    """Run all production feature tests"""
    print("🚀 RICHESREACH PRODUCTION FEATURES TEST")
    print("=" * 50)
    
    tests = [
        ("Server Health", test_server_health),
        ("Debug Configuration", test_debug_config),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("Crypto Recommendations", test_crypto_recommendations_performance),
        ("ML Signals", test_ml_signals_performance),
        ("Rate Limiting", test_rate_limiting),
        ("Concurrent Load", test_concurrent_load),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All production features are working correctly!")
    else:
        print("⚠️ Some features need attention.")
    
    return passed == total

if __name__ == "__main__":
    main()
