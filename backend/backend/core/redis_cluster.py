"""
Enhanced Redis Clustering for RichesReach AI
Phase 1: Improved Caching Performance
"""

import redis
import json
import time
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import hashlib

class RedisClusterManager:
    """Enhanced Redis cluster management with failover and performance optimization"""
    
    def __init__(self, 
                 primary_host: str = "localhost", 
                 primary_port: int = 6379,
                 secondary_host: str = None,
                 secondary_port: int = 6379,
                 db: int = 0,
                 password: str = None):
        
        self.primary_host = primary_host
        self.primary_port = primary_port
        self.secondary_host = secondary_host or primary_host
        self.secondary_port = secondary_port
        self.db = db
        self.password = password
        
        self.primary_client = None
        self.secondary_client = None
        self.current_client = None
        
        self.connection_pool = None
        self.retry_attempts = 3
        self.retry_delay = 0.1
        
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize Redis connections with failover support"""
        try:
            # Primary connection
            self.primary_client = redis.Redis(
                host=self.primary_host,
                port=self.primary_port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test primary connection
            self.primary_client.ping()
            self.current_client = self.primary_client
            logging.info(f"✅ Connected to primary Redis: {self.primary_host}:{self.primary_port}")
            
            # Secondary connection (if different from primary)
            if self.secondary_host != self.primary_host or self.secondary_port != self.primary_port:
                self.secondary_client = redis.Redis(
                    host=self.secondary_host,
                    port=self.secondary_port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test secondary connection
                self.secondary_client.ping()
                logging.info(f"✅ Connected to secondary Redis: {self.secondary_host}:{self.secondary_port}")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize Redis connections: {e}")
            self.current_client = None
    
    def _get_client(self) -> Optional[redis.Redis]:
        """Get current Redis client with failover support"""
        if self.current_client is None:
            return None
        
        try:
            # Test current client
            self.current_client.ping()
            return self.current_client
        except Exception as e:
            logging.warning(f"Primary Redis connection failed: {e}")
            
            # Try to failover to secondary
            if self.secondary_client and self.current_client == self.primary_client:
                try:
                    self.secondary_client.ping()
                    self.current_client = self.secondary_client
                    logging.info("✅ Failed over to secondary Redis")
                    return self.current_client
                except Exception as e2:
                    logging.error(f"Secondary Redis also failed: {e2}")
            
            # Try to reconnect to primary
            try:
                self._initialize_connections()
                return self.current_client
            except Exception as e3:
                logging.error(f"Failed to reconnect to Redis: {e3}")
                return None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis with automatic deserialization"""
        client = self._get_client()
        if not client:
            return None
        
        try:
            value = client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logging.error(f"Error getting key {key}: {e}")
            return None
    
    def set(self, 
            key: str, 
            value: Any, 
            ex: Optional[int] = None,
            nx: bool = False,
            xx: bool = False) -> bool:
        """Set value in Redis with automatic serialization"""
        client = self._get_client()
        if not client:
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            return client.set(key, serialized_value, ex=ex, nx=nx, xx=xx)
            
        except Exception as e:
            logging.error(f"Error setting key {key}: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """Delete keys from Redis"""
        client = self._get_client()
        if not client:
            return 0
        
        try:
            return client.delete(*keys)
        except Exception as e:
            logging.error(f"Error deleting keys {keys}: {e}")
            return 0
    
    def exists(self, *keys: str) -> int:
        """Check if keys exist in Redis"""
        client = self._get_client()
        if not client:
            return 0
        
        try:
            return client.exists(*keys)
        except Exception as e:
            logging.error(f"Error checking existence of keys {keys}: {e}")
            return 0
    
    def expire(self, key: str, time: int) -> bool:
        """Set expiration time for a key"""
        client = self._get_client()
        if not client:
            return False
        
        try:
            return client.expire(key, time)
        except Exception as e:
            logging.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        client = self._get_client()
        if not client:
            return -1
        
        try:
            return client.ttl(key)
        except Exception as e:
            logging.error(f"Error getting TTL for key {key}: {e}")
            return -1
    
    def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field value"""
        client = self._get_client()
        if not client:
            return None
        
        try:
            value = client.hget(name, key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logging.error(f"Error getting hash field {name}:{key}: {e}")
            return None
    
    def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field value"""
        client = self._get_client()
        if not client:
            return False
        
        try:
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            return client.hset(name, key, serialized_value)
            
        except Exception as e:
            logging.error(f"Error setting hash field {name}:{key}: {e}")
            return False
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        client = self._get_client()
        if not client:
            return {}
        
        try:
            data = client.hgetall(name)
            result = {}
            
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            
            return result
            
        except Exception as e:
            logging.error(f"Error getting all hash fields for {name}: {e}")
            return {}
    
    def lpush(self, name: str, *values: Any) -> int:
        """Push values to the left of a list"""
        client = self._get_client()
        if not client:
            return 0
        
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list, tuple)):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(str(value))
            
            return client.lpush(name, *serialized_values)
            
        except Exception as e:
            logging.error(f"Error pushing to list {name}: {e}")
            return 0
    
    def rpop(self, name: str) -> Optional[Any]:
        """Pop value from the right of a list"""
        client = self._get_client()
        if not client:
            return None
        
        try:
            value = client.rpop(name)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logging.error(f"Error popping from list {name}: {e}")
            return None
    
    def pipeline(self):
        """Get Redis pipeline for batch operations"""
        client = self._get_client()
        if not client:
            return None
        
        return client.pipeline()
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis cluster health"""
        health = {
            "status": "unhealthy",
            "primary": {"host": self.primary_host, "port": self.primary_port, "connected": False},
            "secondary": {"host": self.secondary_host, "port": self.secondary_port, "connected": False},
            "current_client": None
        }
        
        # Check primary
        try:
            if self.primary_client:
                self.primary_client.ping()
                health["primary"]["connected"] = True
        except Exception as e:
            health["primary"]["error"] = str(e)
        
        # Check secondary
        try:
            if self.secondary_client:
                self.secondary_client.ping()
                health["secondary"]["connected"] = True
        except Exception as e:
            health["secondary"]["error"] = str(e)
        
        # Determine overall status
        if health["primary"]["connected"] or health["secondary"]["connected"]:
            health["status"] = "healthy"
            health["current_client"] = "primary" if health["primary"]["connected"] else "secondary"
        else:
            health["status"] = "unhealthy"
        
        return health
    
    def get_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        client = self._get_client()
        if not client:
            return {}
        
        try:
            info = client.info()
            return {
                "version": info.get("redis_version"),
                "uptime": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "keyspace": info.get("db0", {}),
                "total_commands_processed": info.get("total_commands_processed")
            }
        except Exception as e:
            logging.error(f"Error getting Redis info: {e}")
            return {}

# Global instance
redis_cluster = RedisClusterManager()

# Convenience functions
def cache_get(key: str, default: Any = None) -> Any:
    """Get value from cache with default"""
    value = redis_cluster.get(key)
    return value if value is not None else default

def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache with TTL"""
    return redis_cluster.set(key, value, ex=ttl)

def cache_delete(*keys: str) -> int:
    """Delete keys from cache"""
    return redis_cluster.delete(*keys)

def cache_exists(*keys: str) -> bool:
    """Check if keys exist in cache"""
    return redis_cluster.exists(*keys) > 0

def get_cache_key(prefix: str, *args: str) -> str:
    """Generate consistent cache key"""
    key_parts = [prefix] + [str(arg) for arg in args]
    return ":".join(key_parts)

def get_hash_key(data: str) -> str:
    """Generate hash key for data"""
    return hashlib.md5(data.encode()).hexdigest()
