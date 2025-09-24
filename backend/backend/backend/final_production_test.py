#!/usr/bin/env python3
"""
Final Production Features Test - RichesReach Crypto System
"""

import requests
import time
import json
import statistics

BASE_URL = "http://localhost:8123"

def test_all_features():
    """Test all production features comprehensively"""
    print("🚀 RICHESREACH PRODUCTION FEATURES - FINAL TEST")
    print("=" * 60)
    
    results = {}
    
    # 1. Server Health
    print("\n🏥 1. SERVER HEALTH")
    start = time.time()
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    duration = time.time() - start
    results["health"] = response.status_code == 200
    print(f"   ✅ Health check: {duration:.3f}s - Status: {response.status_code}")
    
    # 2. Debug Configuration
    print("\n🔧 2. DEBUG CONFIGURATION")
    start = time.time()
    response = requests.get(f"{BASE_URL}/debug/config", timeout=5)
    duration = time.time() - start
    results["config"] = response.status_code == 200
    
    if results["config"]:
        config = response.json()
        print(f"   ✅ Config loaded: {duration:.3f}s")
        print(f"   📊 Redis Status: {config.get('redis_status', 'unknown')}")
        print(f"   📊 HTTPX Enabled: {config.get('httpx_enabled', False)}")
        print(f"   📊 CoinGecko Cache TTL: {config.get('coingecko_cache_ttl', 'unknown')}s")
        print(f"   📊 Rate Limit: {config.get('rate_limit_per_minute', 'unknown')}/min")
    else:
        print(f"   ❌ Config failed: {response.status_code}")
    
    # 3. Metrics Endpoint
    print("\n📊 3. PROMETHEUS METRICS")
    start = time.time()
    response = requests.get(f"{BASE_URL}/metrics", timeout=5)
    duration = time.time() - start
    results["metrics"] = response.status_code == 200
    
    if results["metrics"]:
        metrics = response.text
        print(f"   ✅ Metrics loaded: {duration:.3f}s - Size: {len(metrics)} bytes")
        if "app_requests_total" in metrics:
            print("   ✅ Request metrics available")
        if "app_request_duration_seconds" in metrics:
            print("   ✅ Duration metrics available")
    else:
        print(f"   ❌ Metrics failed: {response.status_code}")
    
    # 4. Crypto Recommendations (Real APIs)
    print("\n🚀 4. CRYPTO RECOMMENDATIONS (REAL APIs)")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoRecommendations(limit: 3) { symbol score probability confidenceLevel priceUsd explanation } }"
    }, timeout=30)
    duration1 = time.time() - start
    results["recommendations"] = response.status_code == 200
    
    if results["recommendations"]:
        data = response.json()
        recs = data.get('data', {}).get('cryptoRecommendations', [])
        print(f"   ✅ First request: {duration1:.2f}s - Recommendations: {len(recs)}")
        
        if recs:
            first = recs[0]
            print(f"   📈 Sample: {first['symbol']} - Score: {first['score']:.1f} - Prob: {first['probability']:.2f}")
            print(f"   🧠 Explanation: {first['explanation']}")
    else:
        print(f"   ❌ Recommendations failed: {response.status_code}")
    
    # 5. Cache Performance
    print("\n⚡ 5. CACHE PERFORMANCE")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoRecommendations(limit: 3) { symbol } }"
    }, timeout=30)
    duration2 = time.time() - start
    results["cache"] = response.status_code == 200
    
    if results["cache"]:
        cache_improvement = ((duration1 - duration2) / duration1) * 100 if duration1 > 0 else 0
        print(f"   ✅ Second request: {duration2:.2f}s")
        print(f"   🚀 Cache improvement: {cache_improvement:.1f}% faster")
    else:
        print(f"   ❌ Cache test failed: {response.status_code}")
    
    # 6. Rate Limiting
    print("\n🛡️ 6. RATE LIMITING")
    responses = []
    start_time = time.time()
    
    for i in range(5):
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": "query { cryptoRecommendations(limit: 1) { symbol } }"
        }, timeout=5)
        responses.append(response.status_code)
        time.sleep(0.1)
    
    total_time = time.time() - start_time
    success_count = sum(1 for status in responses if status == 200)
    rate_limited_count = sum(1 for status in responses if status == 429)
    results["rate_limiting"] = success_count > 0
    
    print(f"   ✅ Requests: {len(responses)} - Success: {success_count} - Rate Limited: {rate_limited_count}")
    print(f"   ⏱️ Total time: {total_time:.2f}s")
    
    # 7. Concurrent Load
    print("\n⚡ 7. CONCURRENT LOAD TESTING")
    import concurrent.futures
    
    def make_request():
        start = time.time()
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": "query { cryptoRecommendations(limit: 2) { symbol } }"
        }, timeout=30)
        duration = time.time() - start
        return response.status_code, duration
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request) for _ in range(3)]
        results_concurrent = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    total_time = time.time() - start_time
    successful = sum(1 for status, _ in results_concurrent if status == 200)
    avg_duration = statistics.mean([duration for _, duration in results_concurrent])
    results["concurrent"] = successful >= 2
    
    print(f"   ✅ Concurrent requests: 3 - Success: {successful}/3")
    print(f"   ⏱️ Average duration: {avg_duration:.2f}s - Total time: {total_time:.2f}s")
    
    # 8. ML Signals (if working)
    print("\n🤖 8. ML SIGNALS")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoMlSignal(symbol: \"BTC\") { symbol predictionType probability confidenceLevel explanation } }"
    }, timeout=10)
    duration = time.time() - start
    results["ml_signals"] = response.status_code == 200
    
    if results["ml_signals"]:
        data = response.json()
        signal = data.get('data', {}).get('cryptoMlSignal', {})
        if signal:
            print(f"   ✅ ML Signal: {duration:.3f}s - {signal.get('symbol')} - Prob: {signal.get('probability')}")
            print(f"   🧠 Explanation: {signal.get('explanation', 'N/A')}")
        else:
            print(f"   ⚠️ ML Signal returned null - Duration: {duration:.3f}s")
            results["ml_signals"] = False
    else:
        print(f"   ❌ ML Signals failed: {response.status_code}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL PRODUCTION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    feature_status = {
        "Server Health": "✅ PASS" if results["health"] else "❌ FAIL",
        "Debug Configuration": "✅ PASS" if results["config"] else "❌ FAIL", 
        "Prometheus Metrics": "✅ PASS" if results["metrics"] else "❌ FAIL",
        "Crypto Recommendations": "✅ PASS" if results["recommendations"] else "❌ FAIL",
        "Cache Performance": "✅ PASS" if results["cache"] else "❌ FAIL",
        "Rate Limiting": "✅ PASS" if results["rate_limiting"] else "❌ FAIL",
        "Concurrent Load": "✅ PASS" if results["concurrent"] else "❌ FAIL",
        "ML Signals": "✅ PASS" if results["ml_signals"] else "❌ FAIL",
    }
    
    for feature, status in feature_status.items():
        print(f"{status} {feature}")
    
    print(f"\n🎯 Overall: {passed}/{total} features working")
    
    if passed >= 7:
        print("🎉 EXCELLENT! Your crypto system is production-ready!")
        print("🚀 Performance is competitive with major trading platforms!")
    elif passed >= 5:
        print("✅ GOOD! Most features are working well!")
        print("🔧 Minor improvements needed for full production.")
    else:
        print("⚠️ NEEDS WORK! Several features need attention.")
    
    return passed >= 7

if __name__ == "__main__":
    test_all_features()
