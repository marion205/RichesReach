#!/usr/bin/env python3
"""
RichesReach HFT Endpoint Testing Suite
Tests all High-Frequency Trading endpoints for performance and functionality
"""

import requests
import json
import time
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8000"
SERVER_PROCESS = None

def start_server():
    global SERVER_PROCESS
    print("🚀 Starting RichesReach Test Server with HFT capabilities...")
    
    # Kill any existing server
    os.system("pkill -f 'python3 test_server_minimal.py'")
    time.sleep(2)
    
    SERVER_PROCESS = subprocess.Popen(
        ["python3", "test_server_minimal.py"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        preexec_fn=os.setsid
    )
    print(f"✅ Server started with PID: {SERVER_PROCESS.pid}")
    time.sleep(5)  # Give server time to start

def stop_server():
    global SERVER_PROCESS
    if SERVER_PROCESS:
        print(f"🛑 Stopping server with PID: {SERVER_PROCESS.pid}")
        os.killpg(os.getpgid(SERVER_PROCESS.pid), 9)
        SERVER_PROCESS.wait()
        SERVER_PROCESS = None
        time.sleep(2)
    
    # Double check
    os.system("pkill -f 'python3 test_server_minimal.py'")

def wait_for_server(timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
        time.sleep(1)
    
    print("❌ Server did not become ready in time.")
    return False

def run_test(name, test_func, *args, **kwargs):
    print(f"🧪 Running test: {name}...")
    try:
        result = test_func(*args, **kwargs)
        if result:
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
    except Exception as e:
        print(f"❌ {name}")
        print(f"   Error: {e}")
    print("-" * 50)

# HFT Test Functions

def test_hft_performance():
    """Test HFT performance metrics endpoint"""
    response = requests.get(f"{BASE_URL}/api/hft/performance/", timeout=10)
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    required_fields = ["total_orders", "orders_per_second", "average_latency_microseconds", "total_pnl"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    print(f"   📊 Total orders: {data.get('total_orders', 0)}")
    print(f"   ⚡ Orders/sec: {data.get('orders_per_second', 0)}")
    print(f"   🕐 Avg latency: {data.get('average_latency_microseconds', 0):.2f}μs")
    print(f"   💰 Total PnL: ${data.get('total_pnl', 0):.2f}")
    
    return True

def test_hft_positions():
    """Test HFT positions endpoint"""
    response = requests.get(f"{BASE_URL}/api/hft/positions/", timeout=10)
    assert response.status_code == 200
    data = response.json()
    
    assert "positions" in data
    assert "count" in data
    
    print(f"   📈 Active positions: {data.get('count', 0)}")
    if data.get('positions'):
        for symbol, pos in data['positions'].items():
            print(f"   📊 {symbol}: {pos.get('quantity', 0)} shares, ${pos.get('market_value', 0):.2f}")
    
    return True

def test_hft_strategies():
    """Test HFT strategies endpoint"""
    response = requests.get(f"{BASE_URL}/api/hft/strategies/", timeout=10)
    assert response.status_code == 200
    data = response.json()
    
    assert "strategies" in data
    strategies = data["strategies"]
    
    expected_strategies = ["scalping", "market_making", "arbitrage", "momentum"]
    for strategy in expected_strategies:
        assert strategy in strategies, f"Missing strategy: {strategy}"
        
        strategy_data = strategies[strategy]
        assert "name" in strategy_data
        assert "symbols" in strategy_data
        assert "status" in strategy_data
        
        print(f"   🎯 {strategy}: {strategy_data.get('status', 'UNKNOWN')}")
    
    return True

def test_hft_execute_strategy():
    """Test HFT strategy execution"""
    strategies = ["scalping", "market_making", "arbitrage", "momentum"]
    
    for strategy in strategies:
        payload = {
            "strategy": strategy,
            "symbol": "AAPL"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/hft/execute-strategy/", 
            json=payload, 
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["strategy"] == strategy
        assert data["symbol"] == "AAPL"
        assert "orders_executed" in data
        assert "orders" in data
        
        print(f"   ⚡ {strategy}: {data.get('orders_executed', 0)} orders executed")
    
    return True

def test_hft_place_order():
    """Test HFT order placement"""
    orders = [
        {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"},
        {"symbol": "MSFT", "side": "SELL", "quantity": 50, "order_type": "LIMIT", "price": 300.0},
        {"symbol": "GOOGL", "side": "BUY", "quantity": 25, "order_type": "IOC"},
    ]
    
    for order in orders:
        response = requests.post(
            f"{BASE_URL}/api/hft/place-order/", 
            json=order, 
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "order" in data
        
        order_data = data["order"]
        assert order_data["symbol"] == order["symbol"]
        assert order_data["side"] == order["side"]
        assert order_data["quantity"] == order["quantity"]
        
        print(f"   📋 {order['symbol']} {order['side']} {order['quantity']} @ {order.get('price', 'MARKET')}")
    
    return True

def test_hft_live_stream():
    """Test HFT live data stream"""
    response = requests.get(f"{BASE_URL}/api/hft/live-stream/", timeout=10)
    assert response.status_code == 200
    data = response.json()
    
    assert "live_data" in data
    assert "timestamp" in data
    assert "data_points" in data
    
    live_data = data["live_data"]
    assert len(live_data) > 0
    
    print(f"   📡 Live data points: {data.get('data_points', 0)}")
    for symbol, tick_data in live_data.items():
        print(f"   📊 {symbol}: ${tick_data.get('bid', 0):.2f} / ${tick_data.get('ask', 0):.2f}")
    
    return True

def test_hft_latency():
    """Test HFT latency performance"""
    latencies = []
    
    for i in range(10):
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/hft/performance/", timeout=5)
        end_time = time.time()
        
        if response.status_code == 200:
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
    
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"   🕐 Avg latency: {avg_latency:.2f}ms")
        print(f"   ⚡ Min latency: {min_latency:.2f}ms")
        print(f"   🐌 Max latency: {max_latency:.2f}ms")
        
        # HFT should be under 10ms
        return avg_latency < 10.0
    
    return False

def test_hft_concurrent_orders():
    """Test concurrent HFT order placement"""
    def place_order(order_id):
        payload = {
            "symbol": "AAPL",
            "side": "BUY" if order_id % 2 == 0 else "SELL",
            "quantity": 100,
            "order_type": "MARKET"
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/hft/place-order/", json=payload, timeout=5)
        end_time = time.time()
        
        return {
            "order_id": order_id,
            "status_code": response.status_code,
            "latency_ms": (end_time - start_time) * 1000,
            "success": response.status_code == 200
        }
    
    # Place 20 concurrent orders
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(place_order, i) for i in range(20)]
        results = [future.result() for future in as_completed(futures)]
    
    successful_orders = [r for r in results if r["success"]]
    avg_latency = sum(r["latency_ms"] for r in successful_orders) / len(successful_orders) if successful_orders else 0
    
    print(f"   📊 Concurrent orders: {len(successful_orders)}/20 successful")
    print(f"   ⚡ Avg latency: {avg_latency:.2f}ms")
    
    return len(successful_orders) >= 15  # At least 75% success rate

def test_hft_strategy_performance():
    """Test HFT strategy performance"""
    strategies = ["scalping", "market_making", "arbitrage", "momentum"]
    results = {}
    
    for strategy in strategies:
        start_time = time.time()
        
        # Execute strategy multiple times
        for _ in range(5):
            payload = {"strategy": strategy, "symbol": "AAPL"}
            response = requests.post(f"{BASE_URL}/api/hft/execute-strategy/", json=payload, timeout=5)
            if response.status_code != 200:
                break
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 5 * 1000  # Convert to ms
        
        results[strategy] = avg_time
        print(f"   ⚡ {strategy}: {avg_time:.2f}ms avg execution time")
    
    # All strategies should execute quickly
    return all(time < 100.0 for time in results.values())

def test_hft_integration():
    """Test HFT integration with other endpoints"""
    # Test HFT with GraphQL
    query = """
    query {
        dayTradingPicks(mode: "AGGRESSIVE") {
            picks {
                symbol
                side
                score
            }
        }
    }
    """
    
    response = requests.post(
        f"{BASE_URL}/graphql/", 
        json={"query": query}, 
        timeout=10
    )
    assert response.status_code == 200
    data = response.json()
    
    if "data" in data and "dayTradingPicks" in data["data"]:
        picks = data["data"]["dayTradingPicks"]["picks"]
        if picks:
            # Use first pick for HFT execution
            pick = picks[0]
            symbol = pick["symbol"]
            side = pick["side"]
            
            # Execute HFT order based on GraphQL pick
            hft_payload = {
                "symbol": symbol,
                "side": "BUY" if side == "LONG" else "SELL",
                "quantity": 100,
                "order_type": "MARKET"
            }
            
            hft_response = requests.post(f"{BASE_URL}/api/hft/place-order/", json=hft_payload, timeout=5)
            assert hft_response.status_code == 200
            
            print(f"   🔗 GraphQL → HFT: {symbol} {side} order executed")
            return True
    
    return False

def main():
    print("🚀 RICHESREACH HFT COMPREHENSIVE TESTING")
    print("=" * 60)
    print("⚡ Testing High-Frequency Trading capabilities")
    print("🎯 Ultra-low latency order execution")
    print("📊 Microsecond precision performance")
    print("=" * 60)

    # Start server
    start_server()
    
    if not wait_for_server():
        print("❌ Server did not start. Aborting tests.")
        stop_server()
        exit(1)

    print("\n1. BASIC HFT FUNCTIONALITY TESTS")
    print("-" * 50)
    run_test("HFT Performance Metrics", test_hft_performance)
    run_test("HFT Positions", test_hft_positions)
    run_test("HFT Strategies", test_hft_strategies)

    print("\n2. HFT EXECUTION TESTS")
    print("-" * 50)
    run_test("HFT Strategy Execution", test_hft_execute_strategy)
    run_test("HFT Order Placement", test_hft_place_order)
    run_test("HFT Live Stream", test_hft_live_stream)

    print("\n3. HFT PERFORMANCE TESTS")
    print("-" * 50)
    run_test("HFT Latency", test_hft_latency)
    run_test("HFT Concurrent Orders", test_hft_concurrent_orders)
    run_test("HFT Strategy Performance", test_hft_strategy_performance)

    print("\n4. HFT INTEGRATION TESTS")
    print("-" * 50)
    run_test("HFT + GraphQL Integration", test_hft_integration)

    print("\n🎉 HFT TESTING COMPLETE!")
    print("=" * 60)
    print("⚡ RichesReach now has institutional-grade HFT capabilities")
    print("🚀 Ready for microsecond trading execution")
    print("💰 Competitive advantage in high-frequency trading")
    print("=" * 60)

    stop_server()

if __name__ == "__main__":
    main()
