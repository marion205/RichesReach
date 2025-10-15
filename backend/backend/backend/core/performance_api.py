"""
Performance Optimization API - Phase 3
FastAPI endpoints for performance monitoring, optimization, and management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import logging
from datetime import datetime

from .performance_optimizer import performance_optimizer, CacheConfig, PerformanceMetrics, CacheMetrics
from .cdn_optimizer import cdn_optimizer, CDNConfig, CDNMetrics
from .database_optimizer import database_optimizer, DatabaseConfig, DatabaseMetrics

logger = logging.getLogger("richesreach")

# Create router
router = APIRouter(prefix="/performance", tags=["Performance Optimization"])

# Pydantic models for API
class CacheConfigModel(BaseModel):
    """Cache configuration model for API"""
    ttl_seconds: int = Field(3600, ge=60, le=86400, description="Cache TTL in seconds")
    max_size_mb: int = Field(100, ge=10, le=1000, description="Maximum cache size in MB")
    compression_enabled: bool = Field(True, description="Enable compression")
    serialization_method: str = Field("pickle", description="Serialization method")
    eviction_policy: str = Field("lru", description="Cache eviction policy")
    cluster_enabled: bool = Field(False, description="Enable Redis clustering")
    sentinel_enabled: bool = Field(False, description="Enable Redis sentinel")

class CDNConfigModel(BaseModel):
    """CDN configuration model for API"""
    distribution_id: str = Field(..., description="CloudFront distribution ID")
    region: str = Field("us-east-1", description="AWS region")
    cache_ttl: int = Field(86400, ge=3600, le=31536000, description="CDN cache TTL in seconds")
    compression_enabled: bool = Field(True, description="Enable compression")
    gzip_enabled: bool = Field(True, description="Enable Gzip compression")
    brotli_enabled: bool = Field(True, description="Enable Brotli compression")
    origin_domain: str = Field("", description="Origin domain")

class DatabaseConfigModel(BaseModel):
    """Database configuration model for API"""
    host: str = Field(..., description="Database host")
    port: int = Field(5432, ge=1, le=65535, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    min_connections: int = Field(5, ge=1, le=50, description="Minimum connections")
    max_connections: int = Field(20, ge=5, le=100, description="Maximum connections")
    connection_timeout: int = Field(30, ge=5, le=300, description="Connection timeout in seconds")
    query_timeout: int = Field(60, ge=10, le=600, description="Query timeout in seconds")
    enable_query_cache: bool = Field(True, description="Enable query caching")
    enable_connection_pooling: bool = Field(True, description="Enable connection pooling")
    enable_query_optimization: bool = Field(True, description="Enable query optimization")
    enable_slow_query_logging: bool = Field(True, description="Enable slow query logging")
    slow_query_threshold_ms: int = Field(1000, ge=100, le=10000, description="Slow query threshold in ms")

class OptimizationRequestModel(BaseModel):
    """Optimization request model"""
    optimization_type: str = Field(..., description="Type of optimization")
    target: str = Field(..., description="Target for optimization")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Optimization parameters")
    priority: str = Field("normal", description="Optimization priority")

class CacheOperationModel(BaseModel):
    """Cache operation model"""
    operation: str = Field(..., description="Cache operation (get, set, delete, clear)")
    key: str = Field(..., description="Cache key")
    value: Optional[Any] = Field(None, description="Cache value (for set operations)")
    ttl: Optional[int] = Field(None, description="TTL in seconds")
    namespace: str = Field("default", description="Cache namespace")

class QueryOptimizationModel(BaseModel):
    """Query optimization model"""
    query: str = Field(..., description="SQL query to optimize")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    analyze_performance: bool = Field(False, description="Analyze query performance")

# Performance Monitoring Endpoints
@router.get("/metrics")
async def get_performance_metrics():
    """Get comprehensive performance metrics"""
    try:
        # Get performance metrics
        performance_metrics = performance_optimizer.get_performance_metrics()
        cache_metrics = performance_optimizer.get_cache_metrics()
        
        # Get CDN metrics if available
        cdn_metrics = None
        if cdn_optimizer:
            cdn_metrics = cdn_optimizer.get_cdn_metrics()
        
        # Get database metrics if available
        db_metrics = None
        if database_optimizer:
            db_metrics = database_optimizer.get_database_metrics()
        
        return {
            "status": "success",
            "performance_metrics": {
                "api_response_time_ms": performance_metrics.api_response_time_ms,
                "database_query_time_ms": performance_metrics.database_query_time_ms,
                "cache_hit_rate": performance_metrics.cache_hit_rate,
                "memory_usage_mb": performance_metrics.memory_usage_mb,
                "cpu_usage_percent": performance_metrics.cpu_usage_percent,
                "network_io_mb": performance_metrics.network_io_mb,
                "disk_io_mb": performance_metrics.disk_io_mb,
                "active_connections": performance_metrics.active_connections,
                "requests_per_second": performance_metrics.requests_per_second,
                "error_rate": performance_metrics.error_rate
            },
            "cache_metrics": {
                "hits": cache_metrics.hits,
                "misses": cache_metrics.misses,
                "hit_rate": cache_metrics.hit_rate,
                "average_response_time_ms": cache_metrics.average_response_time_ms,
                "memory_usage_mb": cache_metrics.memory_usage_mb,
                "cache_size": cache_metrics.cache_size,
                "compression_ratio": cache_metrics.compression_ratio
            },
            "cdn_metrics": cdn_metrics.__dict__ if cdn_metrics else None,
            "database_metrics": db_metrics.__dict__ if db_metrics else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/cache")
async def get_cache_metrics():
    """Get cache performance metrics"""
    try:
        cache_metrics = performance_optimizer.get_cache_metrics()
        
        return {
            "status": "success",
            "cache_metrics": {
                "hits": cache_metrics.hits,
                "misses": cache_metrics.misses,
                "evictions": cache_metrics.evictions,
                "total_requests": cache_metrics.total_requests,
                "hit_rate": cache_metrics.hit_rate,
                "average_response_time_ms": cache_metrics.average_response_time_ms,
                "memory_usage_mb": cache_metrics.memory_usage_mb,
                "cache_size": cache_metrics.cache_size,
                "compression_ratio": cache_metrics.compression_ratio
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/cdn")
async def get_cdn_metrics():
    """Get CDN performance metrics"""
    try:
        if not cdn_optimizer:
            raise HTTPException(status_code=404, detail="CDN optimizer not available")
        
        cdn_metrics = cdn_optimizer.get_cdn_metrics()
        
        return {
            "status": "success",
            "cdn_metrics": {
                "total_requests": cdn_metrics.total_requests,
                "cache_hits": cdn_metrics.cache_hits,
                "cache_misses": cdn_metrics.cache_misses,
                "hit_rate": cdn_metrics.hit_rate,
                "average_latency_ms": cdn_metrics.average_latency_ms,
                "bandwidth_saved_mb": cdn_metrics.bandwidth_saved_mb,
                "compression_ratio": cdn_metrics.compression_ratio,
                "edge_locations_active": cdn_metrics.edge_locations_active,
                "origin_requests": cdn_metrics.origin_requests,
                "error_rate": cdn_metrics.error_rate
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting CDN metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/database")
async def get_database_metrics():
    """Get database performance metrics"""
    try:
        if not database_optimizer:
            raise HTTPException(status_code=404, detail="Database optimizer not available")
        
        db_metrics = database_optimizer.get_database_metrics()
        
        return {
            "status": "success",
            "database_metrics": {
                "active_connections": db_metrics.active_connections,
                "total_connections": db_metrics.total_connections,
                "connection_pool_utilization": db_metrics.connection_pool_utilization,
                "average_query_time_ms": db_metrics.average_query_time_ms,
                "slow_queries_count": db_metrics.slow_queries_count,
                "cache_hit_rate": db_metrics.cache_hit_rate,
                "deadlocks_count": db_metrics.deadlocks_count,
                "lock_waits_count": db_metrics.lock_waits_count,
                "buffer_hit_ratio": db_metrics.buffer_hit_ratio,
                "index_usage_ratio": db_metrics.index_usage_ratio
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting database metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cache Management Endpoints
@router.post("/cache/operation")
async def cache_operation(operation: CacheOperationModel):
    """Perform cache operation"""
    try:
        if operation.operation == "get":
            result = await performance_optimizer.cache.get(operation.key, operation.namespace)
            return {
                "status": "success",
                "operation": "get",
                "key": operation.key,
                "value": result,
                "timestamp": datetime.now().isoformat()
            }
        
        elif operation.operation == "set":
            if operation.value is None:
                raise HTTPException(status_code=400, detail="Value required for set operation")
            
            success = await performance_optimizer.cache.set(
                operation.key, 
                operation.value, 
                operation.ttl, 
                operation.namespace
            )
            
            return {
                "status": "success" if success else "error",
                "operation": "set",
                "key": operation.key,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
        
        elif operation.operation == "delete":
            # Note: This would require implementing delete method in cache
            return {
                "status": "success",
                "operation": "delete",
                "key": operation.key,
                "message": "Delete operation not yet implemented",
                "timestamp": datetime.now().isoformat()
            }
        
        elif operation.operation == "clear":
            await performance_optimizer.cache.clear(operation.namespace)
            return {
                "status": "success",
                "operation": "clear",
                "namespace": operation.namespace,
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")
        
    except Exception as e:
        logger.error(f"Error performing cache operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
async def clear_cache(namespace: str = "default"):
    """Clear cache namespace"""
    try:
        await performance_optimizer.cache.clear(namespace)
        
        return {
            "status": "success",
            "message": f"Cache namespace '{namespace}' cleared",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/preload")
async def preload_cache(keys: List[str], namespace: str = "default"):
    """Preload cache with frequently accessed data"""
    try:
        await performance_optimizer.preload_cache(keys, namespace)
        
        return {
            "status": "success",
            "message": f"Preloaded {len(keys)} keys into cache",
            "keys": keys,
            "namespace": namespace,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error preloading cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CDN Management Endpoints
@router.post("/cdn/invalidate")
async def invalidate_cdn_cache(paths: List[str]):
    """Invalidate CDN cache for specific paths"""
    try:
        if not cdn_optimizer:
            raise HTTPException(status_code=404, detail="CDN optimizer not available")
        
        await cdn_optimizer.invalidate_content(paths)
        
        return {
            "status": "success",
            "message": f"Invalidated {len(paths)} paths in CDN cache",
            "paths": paths,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error invalidating CDN cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cdn/preload")
async def preload_cdn_cache(paths: List[str]):
    """Preload CDN cache for specific paths"""
    try:
        if not cdn_optimizer:
            raise HTTPException(status_code=404, detail="CDN optimizer not available")
        
        await cdn_optimizer.preload_content(paths)
        
        return {
            "status": "success",
            "message": f"Preloaded {len(paths)} paths in CDN cache",
            "paths": paths,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error preloading CDN cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Database Optimization Endpoints
@router.post("/database/optimize-query")
async def optimize_database_query(request: QueryOptimizationModel):
    """Optimize database query"""
    try:
        if not database_optimizer:
            raise HTTPException(status_code=404, detail="Database optimizer not available")
        
        # Optimize query
        optimized_query = database_optimizer.query_optimizer.optimize_query(request.query)
        
        result = {
            "status": "success",
            "original_query": request.query,
            "optimized_query": optimized_query,
            "timestamp": datetime.now().isoformat()
        }
        
        # Analyze performance if requested
        if request.analyze_performance:
            analysis = await database_optimizer.analyze_query_performance(request.query)
            result["performance_analysis"] = analysis
        
        return result
        
    except Exception as e:
        logger.error(f"Error optimizing database query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/slow-queries")
async def get_slow_queries():
    """Get list of slow queries"""
    try:
        if not database_optimizer:
            raise HTTPException(status_code=404, detail="Database optimizer not available")
        
        slow_queries = database_optimizer.query_optimizer.get_slow_queries()
        
        return {
            "status": "success",
            "slow_queries": slow_queries,
            "count": len(slow_queries),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/query-metrics")
async def get_query_metrics():
    """Get query performance metrics"""
    try:
        if not database_optimizer:
            raise HTTPException(status_code=404, detail="Database optimizer not available")
        
        query_metrics = database_optimizer.get_query_metrics()
        
        # Convert to serializable format
        serializable_metrics = {}
        for query_hash, metrics in query_metrics.items():
            serializable_metrics[query_hash] = {
                "query_text": metrics.query_text,
                "execution_count": metrics.execution_count,
                "total_execution_time_ms": metrics.total_execution_time_ms,
                "average_execution_time_ms": metrics.average_execution_time_ms,
                "min_execution_time_ms": metrics.min_execution_time_ms,
                "max_execution_time_ms": metrics.max_execution_time_ms,
                "cache_hits": metrics.cache_hits,
                "cache_misses": metrics.cache_misses,
                "last_executed": metrics.last_executed.isoformat() if metrics.last_executed else None,
                "slow_query_count": metrics.slow_query_count
            }
        
        return {
            "status": "success",
            "query_metrics": serializable_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting query metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Optimization Endpoints
@router.post("/optimize")
async def run_optimization(request: OptimizationRequestModel, background_tasks: BackgroundTasks):
    """Run performance optimization"""
    try:
        # Add optimization task to background
        background_tasks.add_task(
            _run_optimization_task,
            request.optimization_type,
            request.target,
            request.parameters,
            request.priority
        )
        
        return {
            "status": "success",
            "message": f"Optimization task started for {request.optimization_type}",
            "optimization_type": request.optimization_type,
            "target": request.target,
            "priority": request.priority,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_optimization_task(optimization_type: str, target: str, parameters: Dict[str, Any], priority: str):
    """Background task for running optimization"""
    try:
        logger.info(f"Running optimization: {optimization_type} for {target}")
        
        # Implement optimization logic based on type
        if optimization_type == "cache":
            await _optimize_cache(target, parameters)
        elif optimization_type == "cdn":
            await _optimize_cdn(target, parameters)
        elif optimization_type == "database":
            await _optimize_database(target, parameters)
        else:
            logger.warning(f"Unknown optimization type: {optimization_type}")
        
    except Exception as e:
        logger.error(f"Error in optimization task: {e}")

async def _optimize_cache(target: str, parameters: Dict[str, Any]):
    """Optimize cache performance"""
    try:
        # Implement cache optimization
        logger.info(f"Optimizing cache for target: {target}")
        
    except Exception as e:
        logger.error(f"Error optimizing cache: {e}")

async def _optimize_cdn(target: str, parameters: Dict[str, Any]):
    """Optimize CDN performance"""
    try:
        # Implement CDN optimization
        logger.info(f"Optimizing CDN for target: {target}")
        
    except Exception as e:
        logger.error(f"Error optimizing CDN: {e}")

async def _optimize_database(target: str, parameters: Dict[str, Any]):
    """Optimize database performance"""
    try:
        # Implement database optimization
        logger.info(f"Optimizing database for target: {target}")
        
    except Exception as e:
        logger.error(f"Error optimizing database: {e}")

# Health Check
@router.get("/health")
async def performance_health():
    """Health check for performance optimization system"""
    try:
        # Check performance optimizer
        performance_metrics = performance_optimizer.get_performance_metrics()
        
        # Check cache
        cache_metrics = performance_optimizer.get_cache_metrics()
        
        # Check CDN if available
        cdn_healthy = False
        if cdn_optimizer:
            try:
                cdn_metrics = cdn_optimizer.get_cdn_metrics()
                cdn_healthy = True
            except:
                cdn_healthy = False
        
        # Check database if available
        db_healthy = False
        if database_optimizer:
            try:
                db_metrics = database_optimizer.get_database_metrics()
                db_healthy = True
            except:
                db_healthy = False
        
        return {
            "status": "healthy",
            "components": {
                "performance_optimizer": True,
                "cache": cache_metrics.cache_size >= 0,
                "cdn": cdn_healthy,
                "database": db_healthy
            },
            "metrics": {
                "cache_hit_rate": cache_metrics.hit_rate,
                "memory_usage_mb": performance_metrics.memory_usage_mb,
                "cpu_usage_percent": performance_metrics.cpu_usage_percent
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
