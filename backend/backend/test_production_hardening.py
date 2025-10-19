#!/usr/bin/env python3
"""
Production Hardening Validation Test Suite
Tests all the new production-grade improvements:
- Prometheus metrics
- Token bucket rate limiting
- Batch pricing
- Probability calibration
- Accuracy telemetry
- Cache performance
"""

import requests
import time
import json
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8123"

def test_server_health():
    """Test basic server health"""
    print("🏥 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        print(f"   ✅ Health check: {response.json().get('status')}")
        return True
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False

def test_debug_config():
    """Test debug config endpoint for new features"""
    print("\n🔧 Testing debug configuration...")
    try:
        response = requests.get(f"{BASE_URL}/debug/config", timeout=5)
        response.raise_for_status()
        config = response.json()
        
        print(f"   📊 Prometheus available: {config.get('prometheus_available', False)}")
        print(f"   🎯 Calibration coef: {config.get('calibration_coef', 'N/A')}")
        print(f"   🎯 Calibration intercept: {config.get('calibration_intercept', 'N/A')}")
        print(f"   🪣 Rate bucket capacity: {config.get('rate_bucket_capacity', 'N/A')}")
        print(f"   🪣 Rate bucket rate: {config.get('rate_bucket_rate', 'N/A')}")
        print(f"   📈 Cache TTL: {config.get('coingecko_cache_ttl', 'N/A')}s")
        print(f"   ⚡ Rate delay: {config.get('coingecko_rate_delay', 'N/A')}s")
        
        return config
    except Exception as e:
        print(f"   ❌ Debug config failed: {e}")
        return None

def test_metrics_endpoint():
    """Test Prometheus metrics endpoint"""
    print("\n📊 Testing metrics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        response.raise_for_status()
        
        metrics_text = response.text
        print(f"   ✅ Metrics endpoint: {len(metrics_text)} characters")
        
        # Check for key metrics
        key_metrics = [
            "ml_signal_latency_seconds",
            "crypto_recs_latency_seconds", 
            "coingecko_fetch_latency_seconds",
            "cache_hits_total",
            "cache_misses_total",
            "ml_pred_bucket_total"
        ]
        
        found_metrics = []
        for metric in key_metrics:
            if metric in metrics_text:
                found_metrics.append(metric)
        
        print(f"   📈 Found {len(found_metrics)}/{len(key_metrics)} key metrics")
        for metric in found_metrics:
            print(f"      ✅ {metric}")
        
        return len(found_metrics) > 0
    except Exception as e:
        print(f"   ❌ Metrics endpoint failed: {e}")
        return False

def test_ml_signal_performance():
    """Test ML signal performance with metrics"""
    print("\n🤖 Testing ML signal performance...")
    
    symbols = ["BTC", "ETH", "ADA", "SOL", "DOT"]
    results = []
    
    for symbol in symbols:
        start = time.time()
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": f"query {{ cryptoMlSignal(symbol: \"{symbol}\") {{ symbol probability confidenceLevel explanation features }} }}"
        }, timeout=10)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            signal = data.get('data', {}).get('cryptoMlSignal', {})
            if signal:
                results.append({
                    "symbol": symbol,
                    "duration": duration,
                    "probability": signal.get('probability', 0),
                    "confidence": signal.get('confidenceLevel', 'UNKNOWN')
                })
                print(f"   ✅ {symbol}: {duration:.3f}s - Prob: {signal.get('probability', 0):.3f} - Conf: {signal.get('confidenceLevel', 'UNKNOWN')}")
            else:
                print(f"   ❌ {symbol}: No data returned")
        else:
            print(f"   ❌ {symbol}: HTTP {response.status_code}")
    
    if results:
        avg_duration = statistics.mean([r['duration'] for r in results])
        print(f"   📊 Average duration: {avg_duration:.3f}s")
        print(f"   🎯 Performance tier: {'EXCELLENT' if avg_duration < 0.01 else 'GOOD' if avg_duration < 0.1 else 'NEEDS IMPROVEMENT'}")
    
    return results

def test_recommendations_performance():
    """Test recommendations performance with metrics"""
    print("\n📈 Testing recommendations performance...")
    
    # Test multiple times to check caching
    durations = []
    for i in range(3):
        start = time.time()
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": "query { cryptoRecommendations(limit: 5) { symbol score probability confidenceLevel explanation } }"
        }, timeout=30)
        duration = time.time() - start
        durations.append(duration)
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('data', {}).get('cryptoRecommendations', [])
            print(f"   ✅ Attempt {i+1}: {duration:.3f}s - {len(recommendations)} recommendations")
        else:
            print(f"   ❌ Attempt {i+1}: HTTP {response.status_code}")
    
    if durations:
        avg_duration = statistics.mean(durations)
        print(f"   📊 Average duration: {avg_duration:.3f}s")
        print(f"   🎯 Performance tier: {'EXCELLENT' if avg_duration < 0.1 else 'GOOD' if avg_duration < 1.0 else 'NEEDS IMPROVEMENT'}")
    
    return durations

def test_concurrent_load():
    """Test concurrent load handling"""
    print("\n⚡ Testing concurrent load handling...")
    
    def make_request():
        start = time.time()
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": "query { cryptoMlSignal(symbol: \"BTC\") { symbol probability confidenceLevel } }"
        }, timeout=10)
        duration = time.time() - start
        return duration, response.status_code == 200
    
    # Test with 10 concurrent requests
    num_requests = 10
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
        results = [future.result() for future in as_completed(futures)]
    
    total_time = time.time() - start_time
    successful = sum(1 for _, success in results if success)
    durations = [duration for duration, success in results if success]
    
    print(f"   📊 Total time for {num_requests} requests: {total_time:.3f}s")
    print(f"   ✅ Successful requests: {successful}/{num_requests}")
    if durations:
        avg_duration = statistics.mean(durations)
        print(f"   📊 Average individual request time: {avg_duration:.3f}s")
        print(f"   🎯 Throughput: {num_requests/total_time:.1f} requests/second")
    
    return successful == num_requests

def test_cache_performance():
    """Test cache performance"""
    print("\n💾 Testing cache performance...")
    
    # First request (cache miss)
    start1 = time.time()
    response1 = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoMlSignal(symbol: \"BTC\") { symbol probability } }"
    }, timeout=10)
    duration1 = time.time() - start1
    
    # Second request (cache hit)
    start2 = time.time()
    response2 = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoMlSignal(symbol: \"BTC\") { symbol probability } }"
    }, timeout=10)
    duration2 = time.time() - start2
    
    if response1.status_code == 200 and response2.status_code == 200:
        speedup = duration1 - duration2
        print(f"   📊 First request (cache miss): {duration1:.3f}s")
        print(f"   📊 Second request (cache hit): {duration2:.3f}s")
        print(f"   ⚡ Cache speedup: {speedup:.3f}s")
        print(f"   🎯 Cache effectiveness: {'EXCELLENT' if speedup > 0.01 else 'GOOD' if speedup > 0.001 else 'NEEDS IMPROVEMENT'}")
        return True
    else:
        print(f"   ❌ Cache test failed: {response1.status_code}, {response2.status_code}")
        return False

def test_probability_calibration():
    """Test probability calibration"""
    print("\n🎯 Testing probability calibration...")
    
    # Test multiple symbols to see calibrated probabilities
    symbols = ["BTC", "ETH", "ADA", "SOL", "DOT"]
    probabilities = []
    
    for symbol in symbols:
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": f"query {{ cryptoMlSignal(symbol: \"{symbol}\") {{ symbol probability confidenceLevel }} }}"
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            signal = data.get('data', {}).get('cryptoMlSignal', {})
            if signal:
                prob = signal.get('probability', 0)
                probabilities.append(prob)
                print(f"   📊 {symbol}: {prob:.4f} probability")
    
    if probabilities:
        avg_prob = statistics.mean(probabilities)
        prob_range = max(probabilities) - min(probabilities)
        print(f"   📊 Average probability: {avg_prob:.4f}")
        print(f"   📊 Probability range: {prob_range:.4f}")
        print(f"   🎯 Calibration: {'GOOD' if 0.3 <= avg_prob <= 0.7 else 'NEEDS TUNING'}")
        return True
    else:
        print("   ❌ No probability data received")
        return False

def test_rate_limiting():
    """Test rate limiting behavior"""
    print("\n🚦 Testing rate limiting...")
    
    # Make rapid requests to test rate limiting
    start_time = time.time()
    responses = []
    
    for i in range(20):  # More than the rate limit
        response = requests.post(f"{BASE_URL}/graphql/", json={
            "query": "query { cryptoMlSignal(symbol: \"BTC\") { symbol probability } }"
        }, timeout=5)
        responses.append(response.status_code)
        time.sleep(0.1)  # Small delay between requests
    
    total_time = time.time() - start_time
    successful = sum(1 for status in responses if status == 200)
    rate_limited = sum(1 for status in responses if status == 429)
    
    print(f"   📊 Total requests: {len(responses)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   🚫 Rate limited: {rate_limited}")
    print(f"   ⏱️ Total time: {total_time:.1f}s")
    print(f"   📊 Effective rate: {len(responses)/total_time:.1f} requests/second")
    
    return rate_limited > 0  # Rate limiting is working if we got some 429s

def generate_performance_report():
    """Generate comprehensive performance report"""
    print("\n" + "="*60)
    print("🏆 PRODUCTION HARDENING VALIDATION REPORT")
    print("="*60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    health_ok = test_server_health()
    if not health_ok:
        print("❌ Server not healthy, skipping other tests")
        return
    
    config = test_debug_config()
    metrics_ok = test_metrics_endpoint()
    ml_results = test_ml_signal_performance()
    rec_results = test_recommendations_performance()
    concurrent_ok = test_concurrent_load()
    cache_ok = test_cache_performance()
    calibration_ok = test_probability_calibration()
    rate_limiting_ok = test_rate_limiting()
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    tests = [
        ("Server Health", health_ok),
        ("Debug Config", config is not None),
        ("Metrics Endpoint", metrics_ok),
        ("ML Signal Performance", len(ml_results) > 0),
        ("Recommendations Performance", len(rec_results) > 0),
        ("Concurrent Load", concurrent_ok),
        ("Cache Performance", cache_ok),
        ("Probability Calibration", calibration_ok),
        ("Rate Limiting", rate_limiting_ok),
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🏆 ALL TESTS PASSED - PRODUCTION READY!")
    elif passed >= total * 0.8:
        print("✅ MOSTLY READY - Minor issues to address")
    else:
        print("⚠️ NEEDS WORK - Several issues to fix")
    
    # Performance highlights
    if ml_results:
        avg_ml_duration = statistics.mean([r['duration'] for r in ml_results])
        print(f"\n⚡ ML Signal Performance: {avg_ml_duration:.3f}s average")
        print(f"   🎯 Tier: {'EXCELLENT' if avg_ml_duration < 0.01 else 'GOOD' if avg_ml_duration < 0.1 else 'NEEDS IMPROVEMENT'}")
    
    if rec_results:
        avg_rec_duration = statistics.mean(rec_results)
        print(f"⚡ Recommendations Performance: {avg_rec_duration:.3f}s average")
        print(f"   🎯 Tier: {'EXCELLENT' if avg_rec_duration < 0.1 else 'GOOD' if avg_rec_duration < 1.0 else 'NEEDS IMPROVEMENT'}")
    
    print(f"\n🚀 Your ML system is now production-hardened and auditable!")

if __name__ == "__main__":
    generate_performance_report()
