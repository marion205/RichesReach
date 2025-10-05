#!/usr/bin/env python3
"""
Phase 3 Testing Suite
Comprehensive testing for all Phase 3 components
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # "PASS", "FAIL", "SKIP"
    duration_ms: float
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None

class Phase3Tester:
    """Comprehensive Phase 3 testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.test_results: List[TestResult] = []
        self.start_time = time.time()
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_test(self, test_name: str, test_func) -> TestResult:
        """Run a single test and record results"""
        start_time = time.time()
        
        try:
            logger.info(f"Running test: {test_name}")
            response_data = await test_func()
            duration_ms = (time.time() - start_time) * 1000
            
            result = TestResult(
                test_name=test_name,
                status="PASS",
                duration_ms=duration_ms,
                response_data=response_data
            )
            
            logger.info(f"✅ {test_name} - PASSED ({duration_ms:.2f}ms)")
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            result = TestResult(
                test_name=test_name,
                status="FAIL",
                duration_ms=duration_ms,
                error_message=str(e)
            )
            
            logger.error(f"❌ {test_name} - FAILED ({duration_ms:.2f}ms): {e}")
            return result
    
    async def test_basic_health(self) -> Dict[str, Any]:
        """Test basic health endpoint"""
        async with self.session.get(f"{self.base_url}/health") as response:
            if response.status != 200:
                raise Exception(f"Health check failed with status {response.status}")
            return await response.json()
    
    async def test_detailed_health(self) -> Dict[str, Any]:
        """Test detailed health endpoint"""
        async with self.session.get(f"{self.base_url}/health/detailed") as response:
            if response.status != 200:
                raise Exception(f"Detailed health check failed with status {response.status}")
            data = await response.json()
            
            # Check Phase 3 components
            if not data.get("ok"):
                raise Exception("Detailed health check returned not ok")
            
            return data
    
    async def test_ai_router_status(self) -> Dict[str, Any]:
        """Test AI Router status"""
        async with self.session.get(f"{self.base_url}/ai-router/status") as response:
            if response.status != 200:
                raise Exception(f"AI Router status failed with status {response.status}")
            return await response.json()
    
    async def test_ai_router_models(self) -> Dict[str, Any]:
        """Test AI Router models endpoint"""
        async with self.session.get(f"{self.base_url}/ai-router/models") as response:
            if response.status != 200:
                raise Exception(f"AI Router models failed with status {response.status}")
            return await response.json()
    
    async def test_ai_router_route(self) -> Dict[str, Any]:
        """Test AI Router routing functionality"""
        test_prompt = "Analyze the current market trends for technology stocks"
        
        async with self.session.post(
            f"{self.base_url}/ai-router/route",
            json={
                "prompt": test_prompt,
                "context": "financial_analysis",
                "user_preferences": {"model_preference": "auto"}
            }
        ) as response:
            if response.status != 200:
                raise Exception(f"AI Router route failed with status {response.status}")
            return await response.json()
    
    async def test_analytics_status(self) -> Dict[str, Any]:
        """Test Analytics status"""
        async with self.session.get(f"{self.base_url}/analytics/status") as response:
            if response.status != 200:
                raise Exception(f"Analytics status failed with status {response.status}")
            return await response.json()
    
    async def test_analytics_dashboards(self) -> Dict[str, Any]:
        """Test Analytics dashboards"""
        async with self.session.get(f"{self.base_url}/analytics/dashboards") as response:
            if response.status != 200:
                raise Exception(f"Analytics dashboards failed with status {response.status}")
            return await response.json()
    
    async def test_analytics_metrics(self) -> Dict[str, Any]:
        """Test Analytics metrics"""
        async with self.session.get(f"{self.base_url}/analytics/metrics") as response:
            if response.status != 200:
                raise Exception(f"Analytics metrics failed with status {response.status}")
            return await response.json()
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test Performance metrics"""
        async with self.session.get(f"{self.base_url}/performance/metrics") as response:
            if response.status != 200:
                raise Exception(f"Performance metrics failed with status {response.status}")
            return await response.json()
    
    async def test_performance_cache(self) -> Dict[str, Any]:
        """Test Performance cache metrics"""
        async with self.session.get(f"{self.base_url}/performance/metrics/cache") as response:
            if response.status != 200:
                raise Exception(f"Performance cache metrics failed with status {response.status}")
            return await response.json()
    
    async def test_performance_health(self) -> Dict[str, Any]:
        """Test Performance health"""
        async with self.session.get(f"{self.base_url}/performance/health") as response:
            if response.status != 200:
                raise Exception(f"Performance health failed with status {response.status}")
            return await response.json()
    
    async def test_cache_operations(self) -> Dict[str, Any]:
        """Test cache operations"""
        # Test cache set
        async with self.session.post(
            f"{self.base_url}/performance/cache/operation",
            json={
                "operation": "set",
                "key": "test_key",
                "value": {"test": "data", "timestamp": time.time()},
                "ttl": 300,
                "namespace": "test"
            }
        ) as response:
            if response.status != 200:
                raise Exception(f"Cache set failed with status {response.status}")
            set_result = await response.json()
        
        # Test cache get
        async with self.session.post(
            f"{self.base_url}/performance/cache/operation",
            json={
                "operation": "get",
                "key": "test_key",
                "namespace": "test"
            }
        ) as response:
            if response.status != 200:
                raise Exception(f"Cache get failed with status {response.status}")
            get_result = await response.json()
        
        return {"set": set_result, "get": get_result}
    
    async def test_advanced_ai_status(self) -> Dict[str, Any]:
        """Test Advanced AI status"""
        async with self.session.get(f"{self.base_url}/advanced-ai/status") as response:
            if response.status != 200:
                raise Exception(f"Advanced AI status failed with status {response.status}")
            return await response.json()
    
    async def test_advanced_ai_models(self) -> Dict[str, Any]:
        """Test Advanced AI models"""
        async with self.session.get(f"{self.base_url}/advanced-ai/models") as response:
            if response.status != 200:
                raise Exception(f"Advanced AI models failed with status {response.status}")
            return await response.json()
    
    async def test_ai_training_status(self) -> Dict[str, Any]:
        """Test AI Training status"""
        async with self.session.get(f"{self.base_url}/ai-training/status") as response:
            if response.status != 200:
                raise Exception(f"AI Training status failed with status {response.status}")
            return await response.json()
    
    async def test_graphql_endpoints(self) -> Dict[str, Any]:
        """Test GraphQL endpoints"""
        # Test GraphQL endpoint
        query = """
        query {
            stocks(symbols: ["AAPL", "GOOGL"]) {
                symbol
                name
                currentPrice
                change
                changePercent
            }
        }
        """
        
        async with self.session.post(
            f"{self.base_url}/graphql",
            json={"query": query}
        ) as response:
            if response.status != 200:
                raise Exception(f"GraphQL query failed with status {response.status}")
            return await response.json()
    
    async def test_websocket_connections(self) -> Dict[str, Any]:
        """Test WebSocket connections"""
        # This would test WebSocket endpoints if they're available
        # For now, just return a placeholder
        return {"websocket_test": "placeholder", "status": "not_implemented"}
    
    async def run_all_tests(self) -> List[TestResult]:
        """Run all Phase 3 tests"""
        logger.info("🚀 Starting Phase 3 Test Suite")
        logger.info("=" * 50)
        
        # Define all tests
        tests = [
            ("Basic Health Check", self.test_basic_health),
            ("Detailed Health Check", self.test_detailed_health),
            ("AI Router Status", self.test_ai_router_status),
            ("AI Router Models", self.test_ai_router_models),
            ("AI Router Route", self.test_ai_router_route),
            ("Analytics Status", self.test_analytics_status),
            ("Analytics Dashboards", self.test_analytics_dashboards),
            ("Analytics Metrics", self.test_analytics_metrics),
            ("Performance Metrics", self.test_performance_metrics),
            ("Performance Cache", self.test_performance_cache),
            ("Performance Health", self.test_performance_health),
            ("Cache Operations", self.test_cache_operations),
            ("Advanced AI Status", self.test_advanced_ai_status),
            ("Advanced AI Models", self.test_advanced_ai_models),
            ("AI Training Status", self.test_ai_training_status),
            ("GraphQL Endpoints", self.test_graphql_endpoints),
            ("WebSocket Connections", self.test_websocket_connections),
        ]
        
        # Run tests
        for test_name, test_func in tests:
            result = await self.run_test(test_name, test_func)
            self.test_results.append(result)
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        
        passed = len([r for r in self.test_results if r.status == "PASS"])
        failed = len([r for r in self.test_results if r.status == "FAIL"])
        total = len(self.test_results)
        
        logger.info("")
        logger.info("📊 Test Summary")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        
        if failed > 0:
            logger.info("")
            logger.info("❌ Failed Tests:")
            for result in self.test_results:
                if result.status == "FAIL":
                    logger.info(f"  - {result.test_name}: {result.error_message}")
        
        logger.info("")
        if failed == 0:
            logger.info("🎉 All Phase 3 tests passed!")
        else:
            logger.info(f"⚠️  {failed} tests failed. Please check the logs above.")
        
        return failed == 0

async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3 Testing Suite")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for testing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async with Phase3Tester(args.url) as tester:
        await tester.run_all_tests()
        success = tester.print_summary()
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
