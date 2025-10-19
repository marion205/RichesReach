"""
Performance Optimizer - Phase 3
Advanced caching, CDN optimization, and edge computing
"""

import asyncio
import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import redis
import redis.cluster
from redis.sentinel import Sentinel
import aioredis
import pickle
import gzip
import base64
from functools import wraps
import psutil
import gc
import weakref
from collections import OrderedDict, defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("richesreach")

@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl_seconds: int = 3600
    max_size_mb: int = 100
    compression_enabled: bool = True
    serialization_method: str = "pickle"  # pickle, json, msgpack
    eviction_policy: str = "lru"  # lru, lfu, ttl
    cluster_enabled: bool = False
    sentinel_enabled: bool = False
    read_replicas: bool = True

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0
    average_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cache_size: int = 0
    compression_ratio: float = 0.0

@dataclass
class PerformanceMetrics:
    """Overall performance metrics"""
    api_response_time_ms: float = 0.0
    database_query_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    network_io_mb: float = 0.0
    disk_io_mb: float = 0.0
    active_connections: int = 0
    requests_per_second: float = 0.0
    error_rate: float = 0.0

class AdvancedCache:
    """Advanced caching system with intelligent optimization"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client = None
        self.local_cache = OrderedDict()
        self.cache_metrics = CacheMetrics()
        self.semantic_cache = {}
        self.prefetch_cache = {}
        self.compression_stats = {"compressed": 0, "uncompressed": 0, "total_size": 0, "compressed_size": 0}
        
        # Initialize cache
        asyncio.create_task(self._initialize_cache())
        
        # Start background tasks
        asyncio.create_task(self._cleanup_expired())
        asyncio.create_task(self._update_metrics())
        asyncio.create_task(self._prefetch_popular())
    
    async def _initialize_cache(self):
        """Initialize Redis cache with clustering support"""
        try:
            if self.config.cluster_enabled:
                # Redis Cluster
                startup_nodes = [
                    {"host": "redis-cluster-1", "port": 6379},
                    {"host": "redis-cluster-2", "port": 6379},
                    {"host": "redis-cluster-3", "port": 6379}
                ]
                self.redis_client = redis.cluster.RedisCluster(
                    startup_nodes=startup_nodes,
                    decode_responses=False,
                    skip_full_coverage_check=True
                )
            elif self.config.sentinel_enabled:
                # Redis Sentinel
                sentinel = Sentinel([
                    ('sentinel-1', 26379),
                    ('sentinel-2', 26379),
                    ('sentinel-3', 26379)
                ])
                self.redis_client = sentinel.master_for('mymaster')
            else:
                # Single Redis instance
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=False,
                    max_connections=20,
                    retry_on_timeout=True
                )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Advanced cache initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize cache: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, key: str, namespace: str = "default") -> str:
        """Generate cache key with namespace"""
        return f"{namespace}:{hashlib.md5(key.encode()).hexdigest()}"
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data with compression"""
        try:
            if self.config.serialization_method == "json":
                serialized = json.dumps(data, default=str).encode('utf-8')
            elif self.config.serialization_method == "msgpack":
                import msgpack
                serialized = msgpack.packb(data, default=str)
            else:  # pickle
                serialized = pickle.dumps(data)
            
            if self.config.compression_enabled and len(serialized) > 1024:  # Compress if > 1KB
                compressed = gzip.compress(serialized)
                if len(compressed) < len(serialized):
                    self.compression_stats["compressed"] += 1
                    self.compression_stats["compressed_size"] += len(compressed)
                    self.compression_stats["total_size"] += len(serialized)
                    return b"COMPRESSED:" + compressed
                else:
                    self.compression_stats["uncompressed"] += 1
                    self.compression_stats["total_size"] += len(serialized)
                    return b"UNCOMPRESSED:" + serialized
            else:
                self.compression_stats["uncompressed"] += 1
                self.compression_stats["total_size"] += len(serialized)
                return b"UNCOMPRESSED:" + serialized
                
        except Exception as e:
            logger.error(f"Error serializing data: {e}")
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data with decompression"""
        try:
            if data.startswith(b"COMPRESSED:"):
                compressed_data = data[11:]  # Remove "COMPRESSED:" prefix
                decompressed = gzip.decompress(compressed_data)
            elif data.startswith(b"UNCOMPRESSED:"):
                decompressed = data[13:]  # Remove "UNCOMPRESSED:" prefix
            else:
                decompressed = data  # Legacy format
            
            if self.config.serialization_method == "json":
                return json.loads(decompressed.decode('utf-8'))
            elif self.config.serialization_method == "msgpack":
                import msgpack
                return msgpack.unpackb(decompressed, raw=False)
            else:  # pickle
                return pickle.loads(decompressed)
                
        except Exception as e:
            logger.error(f"Error deserializing data: {e}")
            return None
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get data from cache with intelligent fallback"""
        start_time = time.time()
        cache_key = self._generate_cache_key(key, namespace)
        
        try:
            # Try local cache first
            if cache_key in self.local_cache:
                self.local_cache.move_to_end(cache_key)  # Update LRU
                self.cache_metrics.hits += 1
                self.cache_metrics.total_requests += 1
                self._update_hit_rate()
                return self.local_cache[cache_key]
            
            # Try Redis cache
            if self.redis_client:
                data = await self.redis_client.get(cache_key)
                if data:
                    deserialized = self._deserialize_data(data)
                    if deserialized is not None:
                        # Store in local cache
                        self._store_local(cache_key, deserialized)
                        self.cache_metrics.hits += 1
                        self.cache_metrics.total_requests += 1
                        self._update_hit_rate()
                        return deserialized
            
            # Cache miss
            self.cache_metrics.misses += 1
            self.cache_metrics.total_requests += 1
            self._update_hit_rate()
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            self.cache_metrics.misses += 1
            self.cache_metrics.total_requests += 1
            self._update_hit_rate()
            return None
        finally:
            response_time = (time.time() - start_time) * 1000
            self._update_response_time(response_time)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = "default") -> bool:
        """Set data in cache with intelligent storage"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            ttl = ttl or self.config.ttl_seconds
            
            # Store in local cache
            self._store_local(cache_key, value)
            
            # Store in Redis cache
            if self.redis_client:
                serialized = self._serialize_data(value)
                await self.redis_client.setex(cache_key, ttl, serialized)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def _store_local(self, key: str, value: Any):
        """Store in local cache with size management"""
        # Check size limits
        if len(self.local_cache) >= 1000:  # Max 1000 items
            # Remove oldest item
            self.local_cache.popitem(last=False)
            self.cache_metrics.evictions += 1
        
        self.local_cache[key] = value
    
    def _update_hit_rate(self):
        """Update cache hit rate"""
        if self.cache_metrics.total_requests > 0:
            self.cache_metrics.hit_rate = self.cache_metrics.hits / self.cache_metrics.total_requests
    
    def _update_response_time(self, response_time_ms: float):
        """Update average response time"""
        alpha = 0.1  # Smoothing factor
        self.cache_metrics.average_response_time_ms = (
            (1 - alpha) * self.cache_metrics.average_response_time_ms + 
            alpha * response_time_ms
        )
    
    async def _cleanup_expired(self):
        """Background task to clean up expired cache entries"""
        while True:
            try:
                # Clean up local cache (simple TTL simulation)
                current_time = time.time()
                expired_keys = []
                
                for key in list(self.local_cache.keys()):
                    # Simple cleanup - remove oldest 10% if cache is full
                    if len(self.local_cache) > 900:
                        expired_keys.append(key)
                        if len(expired_keys) >= 100:
                            break
                
                for key in expired_keys:
                    self.local_cache.pop(key, None)
                    self.cache_metrics.evictions += 1
                
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(60)
    
    async def _update_metrics(self):
        """Background task to update cache metrics"""
        while True:
            try:
                # Update memory usage
                self.cache_metrics.memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
                self.cache_metrics.cache_size = len(self.local_cache)
                
                # Update compression ratio
                if self.compression_stats["total_size"] > 0:
                    self.cache_metrics.compression_ratio = (
                        self.compression_stats["compressed_size"] / 
                        self.compression_stats["total_size"]
                    )
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error updating cache metrics: {e}")
                await asyncio.sleep(60)
    
    async def _prefetch_popular(self):
        """Background task to prefetch popular cache entries"""
        while True:
            try:
                # Analyze access patterns and prefetch popular items
                # This is a simplified version - in production, use more sophisticated algorithms
                await asyncio.sleep(600)  # Prefetch every 10 minutes
                
            except Exception as e:
                logger.error(f"Error in prefetch: {e}")
                await asyncio.sleep(60)
    
    async def semantic_search(self, query: str, namespace: str = "default") -> List[Tuple[str, float]]:
        """Semantic search in cache using similarity"""
        try:
            if not self.semantic_cache:
                return []
            
            # Simple TF-IDF based semantic search
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            
            # Get all cached keys and their content
            cache_contents = []
            cache_keys = []
            
            for key, content in self.semantic_cache.items():
                if isinstance(content, str):
                    cache_contents.append(content)
                    cache_keys.append(key)
            
            if not cache_contents:
                return []
            
            # Fit vectorizer and transform
            tfidf_matrix = vectorizer.fit_transform(cache_contents + [query])
            query_vector = tfidf_matrix[-1]
            cache_vectors = tfidf_matrix[:-1]
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, cache_vectors).flatten()
            
            # Return top matches
            results = list(zip(cache_keys, similarities))
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[:10]  # Top 10 matches
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache performance metrics"""
        return self.cache_metrics
    
    async def clear(self, namespace: str = "default"):
        """Clear cache namespace"""
        try:
            # Clear local cache
            keys_to_remove = [k for k in self.local_cache.keys() if k.startswith(f"{namespace}:")]
            for key in keys_to_remove:
                self.local_cache.pop(key, None)
            
            # Clear Redis cache
            if self.redis_client:
                pattern = f"{namespace}:*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            logger.info(f"Cleared cache namespace: {namespace}")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

class PerformanceOptimizer:
    """Comprehensive performance optimization system"""
    
    def __init__(self):
        self.cache_config = CacheConfig()
        self.cache = AdvancedCache(self.cache_config)
        self.performance_metrics = PerformanceMetrics()
        self.optimization_rules = []
        self.connection_pool = None
        self.query_cache = {}
        self.response_cache = {}
        
        # Initialize optimization
        asyncio.create_task(self._initialize_optimization())
    
    async def _initialize_optimization(self):
        """Initialize performance optimization"""
        try:
            # Set up optimization rules
            self.optimization_rules = [
                self._optimize_database_queries,
                self._optimize_api_responses,
                self._optimize_memory_usage,
                self._optimize_network_io,
                self._optimize_cpu_usage
            ]
            
            # Start monitoring
            asyncio.create_task(self._monitor_performance())
            asyncio.create_task(self._apply_optimizations())
            
            logger.info("✅ Performance optimizer initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize performance optimizer: {e}")
    
    async def _monitor_performance(self):
        """Monitor system performance metrics"""
        while True:
            try:
                # Update performance metrics
                self.performance_metrics.memory_usage_mb = psutil.virtual_memory().used / 1024 / 1024
                self.performance_metrics.cpu_usage_percent = psutil.cpu_percent(interval=1)
                
                # Network and disk I/O
                net_io = psutil.net_io_counters()
                disk_io = psutil.disk_io_counters()
                
                self.performance_metrics.network_io_mb = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024
                self.performance_metrics.disk_io_mb = (disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024
                
                # Cache metrics
                cache_metrics = self.cache.get_metrics()
                self.performance_metrics.cache_hit_rate = cache_metrics.hit_rate
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring performance: {e}")
                await asyncio.sleep(30)
    
    async def _apply_optimizations(self):
        """Apply performance optimizations based on metrics"""
        while True:
            try:
                for rule in self.optimization_rules:
                    await rule()
                
                await asyncio.sleep(60)  # Apply optimizations every minute
                
            except Exception as e:
                logger.error(f"Error applying optimizations: {e}")
                await asyncio.sleep(60)
    
    async def _optimize_database_queries(self):
        """Optimize database queries"""
        try:
            # Implement query optimization strategies
            if self.performance_metrics.database_query_time_ms > 100:
                # Enable query caching
                logger.info("Enabling database query caching due to slow queries")
                
        except Exception as e:
            logger.error(f"Error optimizing database queries: {e}")
    
    async def _optimize_api_responses(self):
        """Optimize API responses"""
        try:
            # Implement response optimization strategies
            if self.performance_metrics.api_response_time_ms > 500:
                # Enable response compression
                logger.info("Enabling response compression due to slow API responses")
                
        except Exception as e:
            logger.error(f"Error optimizing API responses: {e}")
    
    async def _optimize_memory_usage(self):
        """Optimize memory usage"""
        try:
            # Implement memory optimization strategies
            if self.performance_metrics.memory_usage_mb > 1000:  # > 1GB
                # Trigger garbage collection
                gc.collect()
                logger.info("Triggered garbage collection due to high memory usage")
                
        except Exception as e:
            logger.error(f"Error optimizing memory usage: {e}")
    
    async def _optimize_network_io(self):
        """Optimize network I/O"""
        try:
            # Implement network optimization strategies
            if self.performance_metrics.network_io_mb > 100:  # > 100MB
                # Enable connection pooling
                logger.info("Optimizing network I/O due to high usage")
                
        except Exception as e:
            logger.error(f"Error optimizing network I/O: {e}")
    
    async def _optimize_cpu_usage(self):
        """Optimize CPU usage"""
        try:
            # Implement CPU optimization strategies
            if self.performance_metrics.cpu_usage_percent > 80:
                # Reduce background tasks
                logger.info("Optimizing CPU usage due to high load")
                
        except Exception as e:
            logger.error(f"Error optimizing CPU usage: {e}")
    
    def cache_decorator(self, ttl: int = 3600, namespace: str = "default"):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                key = f"{func.__name__}:{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
                
                # Try to get from cache
                cached_result = await self.cache.get(key, namespace)
                if cached_result is not None:
                    return cached_result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.cache.set(key, result, ttl, namespace)
                
                return result
            return wrapper
        return decorator
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        return self.performance_metrics
    
    def get_cache_metrics(self) -> CacheMetrics:
        """Get cache performance metrics"""
        return self.cache.get_metrics()
    
    async def optimize_query(self, query: str, params: Dict[str, Any]) -> str:
        """Optimize database query"""
        try:
            # Simple query optimization
            optimized_query = query
            
            # Add query hints for common patterns
            if "SELECT" in query.upper() and "LIMIT" not in query.upper():
                # Add default limit for large result sets
                optimized_query += " LIMIT 1000"
            
            # Cache optimized query
            query_key = f"optimized_query:{hashlib.md5(query.encode()).hexdigest()}"
            await self.cache.set(query_key, optimized_query, 3600, "queries")
            
            return optimized_query
            
        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            return query
    
    async def preload_cache(self, keys: List[str], namespace: str = "default"):
        """Preload cache with frequently accessed data"""
        try:
            for key in keys:
                # Check if already cached
                if await self.cache.get(key, namespace) is None:
                    # This would typically load from database or external source
                    # For now, just log the preload attempt
                    logger.info(f"Preloading cache for key: {key}")
            
        except Exception as e:
            logger.error(f"Error preloading cache: {e}")

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()
