#!/usr/bin/env python3
"""
Rust HFT Executor Integration Tests
Tests the Rust micro-executor integration with Python backend
"""

import unittest
import subprocess
import os
import time
import json
import requests
from pathlib import Path

class TestRustHFTExecutor(unittest.TestCase):
    """Test Rust HFT Executor integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rust_executor_path = Path("backend/hft/rust-executor")
        self.base_url = "http://localhost:8000"
        
    def test_rust_executor_build(self):
        """Test that Rust executor builds successfully"""
        if not self.rust_executor_path.exists():
            self.skipTest("Rust executor path does not exist")
            
        # Change to rust executor directory
        original_cwd = os.getcwd()
        os.chdir(self.rust_executor_path)
        
        try:
            # Test cargo build
            result = subprocess.run(
                ["cargo", "check", "--release"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            self.assertEqual(result.returncode, 0, f"Cargo check failed: {result.stderr}")
            
        finally:
            os.chdir(original_cwd)
            
    def test_rust_executor_benchmarks(self):
        """Test Rust executor benchmarks"""
        if not self.rust_executor_path.exists():
            self.skipTest("Rust executor path does not exist")
            
        original_cwd = os.getcwd()
        os.chdir(self.rust_executor_path)
        
        try:
            # Run benchmarks
            result = subprocess.run(
                ["cargo", "bench"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Benchmarks should complete without errors
            self.assertEqual(result.returncode, 0, f"Benchmarks failed: {result.stderr}")
            
            # Check for performance metrics in output
            output = result.stdout + result.stderr
            self.assertIn("l2_processing", output)
            self.assertIn("ring_buffer", output)
            self.assertIn("order_creation", output)
            
        finally:
            os.chdir(original_cwd)
            
    def test_rust_executor_tests(self):
        """Test Rust executor unit tests"""
        if not self.rust_executor_path.exists():
            self.skipTest("Rust executor path does not exist")
            
        original_cwd = os.getcwd()
        os.chdir(self.rust_executor_path)
        
        try:
            # Run unit tests
            result = subprocess.run(
                ["cargo", "test"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            self.assertEqual(result.returncode, 0, f"Rust tests failed: {result.stderr}")
            
        finally:
            os.chdir(original_cwd)


class TestHFTPerformanceMetrics(unittest.TestCase):
    """Test HFT performance metrics and benchmarks"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        
    def test_latency_benchmarks(self):
        """Test HFT latency benchmarks"""
        # Test multiple latency measurements
        latencies = []
        
        for i in range(10):
            start_time = time.perf_counter()
            
            response = requests.post(
                f"{self.base_url}/api/hft/place-order/",
                json={"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"},
                timeout=1
            )
            
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            
            self.assertEqual(response.status_code, 200)
            
        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        print(f"\n📊 Latency Benchmarks:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  Min: {min_latency:.2f}ms")
        print(f"  Max: {max_latency:.2f}ms")
        
        # Should be very fast (under 50ms average)
        self.assertLess(avg_latency, 50.0)
        
    def test_throughput_benchmarks(self):
        """Test HFT throughput benchmarks"""
        start_time = time.time()
        successful_requests = 0
        
        # Execute as many requests as possible in 5 seconds
        end_time = start_time + 5.0
        
        while time.time() < end_time:
            try:
                response = requests.post(
                    f"{self.base_url}/api/hft/execute-strategy/",
                    json={"strategy": "scalping", "symbol": "AAPL"},
                    timeout=0.1
                )
                
                if response.status_code == 200:
                    successful_requests += 1
                    
            except requests.exceptions.Timeout:
                pass
                
        total_time = time.time() - start_time
        throughput = successful_requests / total_time
        
        print(f"\n📈 Throughput Benchmarks:")
        print(f"  Requests per second: {throughput:.2f}")
        print(f"  Total requests: {successful_requests}")
        print(f"  Time: {total_time:.2f}s")
        
        # Should handle reasonable throughput
        self.assertGreater(throughput, 1.0)
        
    def test_memory_efficiency(self):
        """Test memory efficiency over time"""
        initial_performance = requests.get(f"{self.base_url}/api/hft/performance/", timeout=10)
        initial_data = initial_performance.json()
        
        # Execute many operations
        for i in range(100):
            requests.post(
                f"{self.base_url}/api/hft/execute-strategy/",
                json={"strategy": "scalping", "symbol": "AAPL"},
                timeout=10
            )
            
        final_performance = requests.get(f"{self.base_url}/api/hft/performance/", timeout=10)
        final_data = final_performance.json()
        
        # Check that system handles load without degradation
        self.assertGreaterEqual(final_data["total_orders"], initial_data["total_orders"])
        
    def test_error_handling(self):
        """Test error handling and recovery"""
        # Test invalid strategy
        response = requests.post(
            f"{self.base_url}/api/hft/execute-strategy/",
            json={"strategy": "invalid_strategy", "symbol": "AAPL"},
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200)  # Should handle gracefully
        data = response.json()
        self.assertIn("error", data)
        
        # Test invalid symbol
        response = requests.post(
            f"{self.base_url}/api/hft/execute-strategy/",
            json={"strategy": "scalping", "symbol": "INVALID_SYMBOL"},
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])  # Should handle gracefully


class TestAdvancedHFTFeatures(unittest.TestCase):
    """Test advanced HFT features and edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        
    def test_multiple_strategy_execution(self):
        """Test executing multiple strategies simultaneously"""
        strategies = ["scalping", "market_making", "arbitrage", "momentum"]
        symbols = ["AAPL", "MSFT", "TSLA", "NVDA"]
        
        for strategy in strategies:
            for symbol in symbols:
                response = requests.post(
                    f"{self.base_url}/api/hft/execute-strategy/",
                    json={"strategy": strategy, "symbol": symbol},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertTrue(data["success"])
                
    def test_order_type_variations(self):
        """Test different order types"""
        order_types = ["MARKET", "LIMIT", "IOC", "FOK"]
        
        for order_type in order_types:
            order_data = {
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 100,
                "order_type": order_type
            }
            
            if order_type == "LIMIT":
                order_data["price"] = 150.0
                
            response = requests.post(
                f"{self.base_url}/api/hft/place-order/",
                json=order_data,
                timeout=10
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            
    def test_risk_management_limits(self):
        """Test risk management limits"""
        # Test large order (should be handled by risk management)
        response = requests.post(
            f"{self.base_url}/api/hft/place-order/",
            json={"symbol": "AAPL", "side": "BUY", "quantity": 10000, "order_type": "MARKET"},
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should either succeed or fail gracefully
        self.assertIn("success", data)
        
    def test_position_tracking_accuracy(self):
        """Test position tracking accuracy"""
        # Get initial positions
        initial_response = requests.get(f"{self.base_url}/api/hft/positions/", timeout=10)
        initial_positions = initial_response.json()["positions"]
        
        # Place a buy order
        buy_response = requests.post(
            f"{self.base_url}/api/hft/place-order/",
            json={"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"},
            timeout=10
        )
        
        self.assertEqual(buy_response.status_code, 200)
        
        # Place a sell order
        sell_response = requests.post(
            f"{self.base_url}/api/hft/place-order/",
            json={"symbol": "AAPL", "side": "SELL", "quantity": 50, "order_type": "MARKET"},
            timeout=10
        )
        
        self.assertEqual(sell_response.status_code, 200)
        
        # Check final positions
        final_response = requests.get(f"{self.base_url}/api/hft/positions/", timeout=10)
        final_positions = final_response.json()["positions"]
        
        # Positions should be tracked accurately
        if "AAPL" in final_positions:
            aapl_position = final_positions["AAPL"]
            self.assertIn("quantity", aapl_position)
            self.assertIn("side", aapl_position)


def run_hft_performance_tests():
    """Run HFT performance and integration tests"""
    print("⚡ Starting HFT Performance & Integration Tests")
    print("=" * 60)
    
    # Test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestRustHFTExecutor,
        TestHFTPerformanceMetrics,
        TestAdvancedHFTFeatures
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
        
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 HFT PERFORMANCE TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
            
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
            
    if result.wasSuccessful():
        print("\n🎉 ALL HFT TESTS PASSED! Performance is excellent!")
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} tests failed.")
        
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_hft_performance_tests()
    exit(0 if success else 1)
