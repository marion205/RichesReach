#!/usr/bin/env python3
"""
Phase 3 Health Check Script
Comprehensive health monitoring for all Phase 3 components
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    """Health status data structure"""
    component: str
    status: str  # "healthy", "unhealthy", "degraded"
    response_time_ms: float
    last_check: datetime
    details: Dict[str, Any]
    error_message: Optional[str] = None

class Phase3HealthChecker:
    """Comprehensive Phase 3 health checker"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.health_statuses: List[HealthStatus] = []
        self.start_time = time.time()
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_component_health(self, component: str, endpoint: str, expected_status: int = 200) -> HealthStatus:
        """Check health of a specific component"""
        start_time = time.time()
        
        try:
            async with self.session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status == expected_status:
                    try:
                        data = await response.json()
                        status = "healthy"
                        error_message = None
                    except:
                        data = {"raw_response": await response.text()}
                        status = "healthy"
                        error_message = None
                else:
                    data = {"status_code": response.status}
                    status = "unhealthy"
                    error_message = f"HTTP {response.status}"
                
                return HealthStatus(
                    component=component,
                    status=status,
                    response_time_ms=response_time_ms,
                    last_check=datetime.now(),
                    details=data,
                    error_message=error_message
                )
                
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                component=component,
                status="unhealthy",
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                details={},
                error_message="Request timeout"
            )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                component=component,
                status="unhealthy",
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                details={},
                error_message=str(e)
            )
    
    async def check_basic_health(self) -> HealthStatus:
        """Check basic application health"""
        return await self.check_component_health("Basic Health", "/health")
    
    async def check_detailed_health(self) -> HealthStatus:
        """Check detailed application health"""
        return await self.check_component_health("Detailed Health", "/health/detailed")
    
    async def check_ai_router_health(self) -> HealthStatus:
        """Check AI Router health"""
        return await self.check_component_health("AI Router", "/ai-router/status")
    
    async def check_analytics_health(self) -> HealthStatus:
        """Check Analytics health"""
        return await self.check_component_health("Analytics", "/analytics/status")
    
    async def check_performance_health(self) -> HealthStatus:
        """Check Performance Optimization health"""
        return await self.check_component_health("Performance", "/performance/health")
    
    async def check_advanced_ai_health(self) -> HealthStatus:
        """Check Advanced AI health"""
        return await self.check_component_health("Advanced AI", "/advanced-ai/status")
    
    async def check_ai_training_health(self) -> HealthStatus:
        """Check AI Training health"""
        return await self.check_component_health("AI Training", "/ai-training/status")
    
    async def check_graphql_health(self) -> HealthStatus:
        """Check GraphQL health"""
        try:
            start_time = time.time()
            
            query = """
            query {
                __schema {
                    types {
                        name
                    }
                }
            }
            """
            
            async with self.session.post(
                f"{self.base_url}/graphql",
                json={"query": query},
                timeout=10
            ) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    if "errors" in data:
                        status = "degraded"
                        error_message = f"GraphQL errors: {data['errors']}"
                    else:
                        status = "healthy"
                        error_message = None
                else:
                    data = {"status_code": response.status}
                    status = "unhealthy"
                    error_message = f"HTTP {response.status}"
                
                return HealthStatus(
                    component="GraphQL",
                    status=status,
                    response_time_ms=response_time_ms,
                    last_check=datetime.now(),
                    details=data,
                    error_message=error_message
                )
                
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                component="GraphQL",
                status="unhealthy",
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                details={},
                error_message=str(e)
            )
    
    async def check_metrics_health(self) -> HealthStatus:
        """Check metrics endpoint health"""
        return await self.check_component_health("Metrics", "/metrics")
    
    async def run_all_health_checks(self) -> List[HealthStatus]:
        """Run all health checks"""
        logger.info("🏥 Starting Phase 3 Health Checks")
        logger.info("=" * 50)
        
        # Define all health checks
        health_checks = [
            self.check_basic_health(),
            self.check_detailed_health(),
            self.check_ai_router_health(),
            self.check_analytics_health(),
            self.check_performance_health(),
            self.check_advanced_ai_health(),
            self.check_ai_training_health(),
            self.check_graphql_health(),
            self.check_metrics_health(),
        ]
        
        # Run all health checks concurrently
        results = await asyncio.gather(*health_checks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Health check failed with exception: {result}")
                continue
            
            self.health_statuses.append(result)
            
            # Log status
            if result.status == "healthy":
                logger.info(f"✅ {result.component}: {result.status} ({result.response_time_ms:.2f}ms)")
            elif result.status == "degraded":
                logger.warning(f"⚠️  {result.component}: {result.status} ({result.response_time_ms:.2f}ms)")
                if result.error_message:
                    logger.warning(f"   Error: {result.error_message}")
            else:
                logger.error(f"❌ {result.component}: {result.status} ({result.response_time_ms:.2f}ms)")
                if result.error_message:
                    logger.error(f"   Error: {result.error_message}")
        
        return self.health_statuses
    
    def print_summary(self):
        """Print health check summary"""
        total_time = time.time() - self.start_time
        
        healthy = len([s for s in self.health_statuses if s.status == "healthy"])
        degraded = len([s for s in self.health_statuses if s.status == "degraded"])
        unhealthy = len([s for s in self.health_statuses if s.status == "unhealthy"])
        total = len(self.health_statuses)
        
        logger.info("")
        logger.info("📊 Health Check Summary")
        logger.info("=" * 50)
        logger.info(f"Total Components: {total}")
        logger.info(f"Healthy: {healthy}")
        logger.info(f"Degraded: {degraded}")
        logger.info(f"Unhealthy: {unhealthy}")
        logger.info(f"Health Score: {(healthy/total)*100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        
        # Show unhealthy components
        if unhealthy > 0:
            logger.info("")
            logger.info("❌ Unhealthy Components:")
            for status in self.health_statuses:
                if status.status == "unhealthy":
                    logger.info(f"  - {status.component}: {status.error_message}")
        
        # Show degraded components
        if degraded > 0:
            logger.info("")
            logger.info("⚠️  Degraded Components:")
            for status in self.health_statuses:
                if status.status == "degraded":
                    logger.info(f"  - {status.component}: {status.error_message}")
        
        # Show response times
        logger.info("")
        logger.info("⏱️  Response Times:")
        for status in sorted(self.health_statuses, key=lambda x: x.response_time_ms, reverse=True):
            logger.info(f"  - {status.component}: {status.response_time_ms:.2f}ms")
        
        logger.info("")
        if unhealthy == 0 and degraded == 0:
            logger.info("🎉 All Phase 3 components are healthy!")
        elif unhealthy == 0:
            logger.info("⚠️  Some components are degraded but functional.")
        else:
            logger.info("❌ Some components are unhealthy and need attention.")
        
        return unhealthy == 0
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        healthy = len([s for s in self.health_statuses if s.status == "healthy"])
        degraded = len([s for s in self.health_statuses if s.status == "degraded"])
        unhealthy = len([s for s in self.health_statuses if s.status == "unhealthy"])
        total = len(self.health_statuses)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy" if unhealthy == 0 else "unhealthy",
            "health_score": (healthy/total)*100 if total > 0 else 0,
            "summary": {
                "total_components": total,
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy
            },
            "components": [
                {
                    "name": status.component,
                    "status": status.status,
                    "response_time_ms": status.response_time_ms,
                    "last_check": status.last_check.isoformat(),
                    "error_message": status.error_message,
                    "details": status.details
                }
                for status in self.health_statuses
            ],
            "recommendations": self._get_recommendations()
        }
    
    def _get_recommendations(self) -> List[str]:
        """Get health recommendations based on status"""
        recommendations = []
        
        for status in self.health_statuses:
            if status.status == "unhealthy":
                if "timeout" in (status.error_message or "").lower():
                    recommendations.append(f"Check network connectivity for {status.component}")
                elif "404" in (status.error_message or ""):
                    recommendations.append(f"Verify {status.component} endpoint is properly configured")
                elif "500" in (status.error_message or ""):
                    recommendations.append(f"Check server logs for {status.component} errors")
                else:
                    recommendations.append(f"Investigate {status.component} configuration and dependencies")
            
            elif status.status == "degraded":
                recommendations.append(f"Monitor {status.component} for potential issues")
            
            if status.response_time_ms > 1000:
                recommendations.append(f"Optimize {status.component} performance (response time: {status.response_time_ms:.2f}ms)")
        
        return recommendations

async def main():
    """Main health check runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3 Health Check")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for health checks")
    parser.add_argument("--output", help="Output file for health report (JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async with Phase3HealthChecker(args.url) as checker:
        await checker.run_all_health_checks()
        success = checker.print_summary()
        
        # Save health report if requested
        if args.output:
            report = checker.get_health_report()
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Health report saved to: {args.output}")
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
