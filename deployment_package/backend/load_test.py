#!/usr/bin/env python3
"""
Load Testing Script for RAHA GraphQL API
Tests the system under various load conditions
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
from datetime import datetime
import argparse

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql/"

# Test queries
QUERIES = {
    "strategies": {
        "query": """
        query {
            strategies {
                id
                name
                slug
                category
                enabled
                defaultVersion {
                    version
                }
            }
        }
        """
    },
    "raha_signals": {
        "query": """
        query {
            rahaSignals(symbol: "AAPL", limit: 20, offset: 0) {
                id
                symbol
                timestamp
                confidenceScore
                strategyVersion {
                    name
                }
            }
        }
        """
    },
    "raha_metrics": {
        "query": """
        query {
            rahaMetrics(symbol: "AAPL") {
                totalSignals
                winRate
                avgReturn
                sharpeRatio
            }
        }
        """
    },
    "user_backtests": {
        "query": """
        query {
            userBacktests(limit: 10, offset: 0) {
                id
                symbol
                status
                metrics
                completedAt
            }
        }
        """
    },
    "strategy_dashboard": {
        "query": """
        query {
            strategyDashboard {
                totalSignals
                avgWinRate
                strategies {
                    strategyName
                    totalSignals
                    winRate
                }
            }
        }
        """
    },
}


class LoadTester:
    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.results: List[Dict[str, Any]] = []

    async def execute_query(
        self, session: aiohttp.ClientSession, query_name: str, query_data: Dict
    ) -> Dict[str, Any]:
        """Execute a single GraphQL query"""
        start_time = time.time()
        
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            async with session.post(
                self.base_url,
                json=query_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                status = response.status
                response_data = await response.json()
                
                return {
                    "query": query_name,
                    "status": status,
                    "response_time_ms": response_time,
                    "success": status == 200 and "errors" not in response_data,
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                "query": query_name,
                "status": 0,
                "response_time_ms": response_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def run_concurrent_requests(
        self, num_requests: int, query_name: str, query_data: Dict
    ) -> List[Dict[str, Any]]:
        """Run multiple concurrent requests"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.execute_query(session, query_name, query_data)
                for _ in range(num_requests)
            ]
            results = await asyncio.gather(*tasks)
            return results

    async def run_load_test(
        self,
        query_name: str,
        concurrent_users: int,
        requests_per_user: int,
        delay_between_requests: float = 0.1,
    ):
        """Run a load test scenario"""
        print(f"\n🧪 Testing: {query_name}")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Requests per user: {requests_per_user}")
        
        query_data = QUERIES[query_name]
        all_results = []
        
        start_time = time.time()
        
        # Run concurrent users
        user_tasks = []
        for user_id in range(concurrent_users):
            async def user_requests():
                user_results = []
                for _ in range(requests_per_user):
                    async with aiohttp.ClientSession() as session:
                        result = await self.execute_query(session, query_name, query_data)
                        user_results.append(result)
                    await asyncio.sleep(delay_between_requests)
                return user_results
            
            user_tasks.append(user_requests())
        
        # Wait for all users to complete
        user_results_list = await asyncio.gather(*user_tasks)
        
        # Flatten results
        for user_results in user_results_list:
            all_results.extend(user_results)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate statistics
        response_times = [r["response_time_ms"] for r in all_results]
        success_count = sum(1 for r in all_results if r["success"])
        error_count = len(all_results) - success_count
        
        stats = {
            "query": query_name,
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": len(all_results),
            "successful_requests": success_count,
            "failed_requests": error_count,
            "success_rate": (success_count / len(all_results) * 100) if all_results else 0,
            "total_time_seconds": total_time,
            "requests_per_second": len(all_results) / total_time if total_time > 0 else 0,
            "avg_response_time_ms": statistics.mean(response_times) if response_times else 0,
            "median_response_time_ms": statistics.median(response_times) if response_times else 0,
            "min_response_time_ms": min(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "p95_response_time_ms": self._percentile(response_times, 95) if response_times else 0,
            "p99_response_time_ms": self._percentile(response_times, 99) if response_times else 0,
        }
        
        self.results.append(stats)
        
        # Print results
        print(f"   ✅ Success rate: {stats['success_rate']:.1f}%")
        print(f"   ⏱️  Avg response time: {stats['avg_response_time_ms']:.2f}ms")
        print(f"   📊 Requests/sec: {stats['requests_per_second']:.2f}")
        print(f"   📈 P95: {stats['p95_response_time_ms']:.2f}ms")
        
        if error_count > 0:
            print(f"   ⚠️  Failed requests: {error_count}")
        
        return stats

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def generate_report(self, output_file: str = None):
        """Generate a load test report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "total_requests": sum(r["total_requests"] for r in self.results),
                "total_successful": sum(r["successful_requests"] for r in self.results),
                "total_failed": sum(r["failed_requests"] for r in self.results),
                "overall_success_rate": (
                    sum(r["successful_requests"] for r in self.results)
                    / sum(r["total_requests"] for r in self.results) * 100
                    if sum(r["total_requests"] for r in self.results) > 0
                    else 0
                ),
                "avg_response_time_ms": statistics.mean(
                    [r["avg_response_time_ms"] for r in self.results]
                ) if self.results else 0,
            },
            "test_results": self.results,
        }
        
        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Report saved to: {output_file}")
        
        return report


async def main():
    parser = argparse.ArgumentParser(description="Load test RAHA GraphQL API")
    parser.add_argument(
        "--url", default=GRAPHQL_URL, help="GraphQL endpoint URL"
    )
    parser.add_argument(
        "--users", type=int, default=10, help="Number of concurrent users"
    )
    parser.add_argument(
        "--requests", type=int, default=5, help="Requests per user"
    )
    parser.add_argument(
        "--query", choices=list(QUERIES.keys()), help="Specific query to test"
    )
    parser.add_argument(
        "--output", help="Output file for report"
    )
    parser.add_argument(
        "--token", help="Authentication token"
    )
    
    args = parser.parse_args()
    
    tester = LoadTester(args.url, args.token)
    
    queries_to_test = [args.query] if args.query else list(QUERIES.keys())
    
    print("🚀 Starting Load Test")
    print("=" * 50)
    print(f"URL: {args.url}")
    print(f"Concurrent users: {args.users}")
    print(f"Requests per user: {args.requests}")
    print(f"Queries to test: {', '.join(queries_to_test)}")
    print("=" * 50)
    
    for query_name in queries_to_test:
        await tester.run_load_test(
            query_name,
            concurrent_users=args.users,
            requests_per_user=args.requests,
        )
    
    # Generate report
    output_file = args.output or f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report = tester.generate_report(output_file)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Load Test Summary")
    print("=" * 50)
    print(f"Total requests: {report['summary']['total_requests']}")
    print(f"Success rate: {report['summary']['overall_success_rate']:.1f}%")
    print(f"Avg response time: {report['summary']['avg_response_time_ms']:.2f}ms")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

