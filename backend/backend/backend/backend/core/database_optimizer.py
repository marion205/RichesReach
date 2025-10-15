"""
Database Query Optimizer - Phase 3
Advanced database optimization, connection pooling, and query performance
"""

import asyncio
import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, execute_values
import asyncpg
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import threading
import weakref

logger = logging.getLogger("richesreach")

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int = 5432
    database: str = "richesreach"
    username: str = "admin"
    password: str = "password"
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: int = 30
    query_timeout: int = 60
    enable_query_cache: bool = True
    enable_connection_pooling: bool = True
    enable_query_optimization: bool = True
    enable_slow_query_logging: bool = True
    slow_query_threshold_ms: int = 1000

@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    query_text: str
    execution_count: int = 0
    total_execution_time_ms: float = 0.0
    average_execution_time_ms: float = 0.0
    min_execution_time_ms: float = float('inf')
    max_execution_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_executed: datetime = None
    slow_query_count: int = 0

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    active_connections: int = 0
    total_connections: int = 0
    connection_pool_utilization: float = 0.0
    average_query_time_ms: float = 0.0
    slow_queries_count: int = 0
    cache_hit_rate: float = 0.0
    deadlocks_count: int = 0
    lock_waits_count: int = 0
    buffer_hit_ratio: float = 0.0
    index_usage_ratio: float = 0.0

class ConnectionPool:
    """Advanced database connection pool"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
        self.async_pool = None
        self.connection_metrics = DatabaseMetrics()
        self.query_cache = {}
        self.slow_queries = deque(maxlen=1000)
        self.query_metrics = {}
        
        # Initialize connection pool
        asyncio.create_task(self._initialize_pool())
        
        # Start monitoring
        asyncio.create_task(self._monitor_connections())
        asyncio.create_task(self._analyze_slow_queries())
    
    async def _initialize_pool(self):
        """Initialize database connection pool"""
        try:
            # Initialize synchronous connection pool
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.min_connections,
                maxconn=self.config.max_connections,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                connect_timeout=self.config.connection_timeout
            )
            
            # Initialize asynchronous connection pool
            self.async_pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.query_timeout
            )
            
            logger.info("✅ Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool: {e}")
            raise
    
    async def _monitor_connections(self):
        """Monitor connection pool metrics"""
        while True:
            try:
                # Update connection metrics
                if self.pool:
                    self.connection_metrics.active_connections = len(self.pool._used)
                    self.connection_metrics.total_connections = len(self.pool._used) + len(self.pool._pool)
                    
                    if self.config.max_connections > 0:
                        self.connection_metrics.connection_pool_utilization = (
                            self.connection_metrics.active_connections / self.config.max_connections
                        )
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring connections: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_slow_queries(self):
        """Analyze slow queries for optimization opportunities"""
        while True:
            try:
                if self.slow_queries:
                    # Analyze slow queries
                    slow_query_analysis = self._analyze_query_patterns()
                    
                    # Log optimization recommendations
                    if slow_query_analysis:
                        logger.info(f"Query optimization recommendations: {slow_query_analysis}")
                
                await asyncio.sleep(300)  # Analyze every 5 minutes
                
            except Exception as e:
                logger.error(f"Error analyzing slow queries: {e}")
                await asyncio.sleep(300)
    
    def _analyze_query_patterns(self) -> List[str]:
        """Analyze query patterns for optimization opportunities"""
        recommendations = []
        
        try:
            # Analyze recent slow queries
            recent_slow_queries = list(self.slow_queries)[-100:]  # Last 100 slow queries
            
            # Check for common patterns
            patterns = defaultdict(int)
            for query in recent_slow_queries:
                query_lower = query.lower()
                if 'select *' in query_lower:
                    patterns['select_star'] += 1
                if 'order by' in query_lower and 'limit' not in query_lower:
                    patterns['missing_limit'] += 1
                if 'join' in query_lower and 'where' not in query_lower:
                    patterns['missing_where'] += 1
                if 'like' in query_lower and '%' in query:
                    patterns['wildcard_like'] += 1
            
            # Generate recommendations
            if patterns['select_star'] > 10:
                recommendations.append("Consider replacing SELECT * with specific columns")
            if patterns['missing_limit'] > 5:
                recommendations.append("Add LIMIT clauses to ORDER BY queries")
            if patterns['missing_where'] > 5:
                recommendations.append("Add WHERE clauses to JOIN queries")
            if patterns['wildcard_like'] > 5:
                recommendations.append("Consider full-text search instead of LIKE with wildcards")
            
        except Exception as e:
            logger.error(f"Error analyzing query patterns: {e}")
        
        return recommendations
    
    def get_connection(self):
        """Get connection from pool"""
        try:
            if self.pool:
                return self.pool.getconn()
            else:
                raise Exception("Connection pool not initialized")
        except Exception as e:
            logger.error(f"Error getting connection: {e}")
            raise
    
    def return_connection(self, connection):
        """Return connection to pool"""
        try:
            if self.pool:
                self.pool.putconn(connection)
        except Exception as e:
            logger.error(f"Error returning connection: {e}")
    
    async def get_async_connection(self):
        """Get async connection from pool"""
        try:
            if self.async_pool:
                return await self.async_pool.acquire()
            else:
                raise Exception("Async connection pool not initialized")
        except Exception as e:
            logger.error(f"Error getting async connection: {e}")
            raise
    
    async def return_async_connection(self, connection):
        """Return async connection to pool"""
        try:
            if self.async_pool:
                await self.async_pool.release(connection)
        except Exception as e:
            logger.error(f"Error returning async connection: {e}")
    
    def get_metrics(self) -> DatabaseMetrics:
        """Get database performance metrics"""
        return self.connection_metrics

class QueryOptimizer:
    """Advanced query optimization system"""
    
    def __init__(self, connection_pool: ConnectionPool):
        self.connection_pool = connection_pool
        self.query_cache = {}
        self.query_metrics = {}
        self.optimization_rules = []
        
        # Initialize optimization rules
        self._initialize_optimization_rules()
    
    def _initialize_optimization_rules(self):
        """Initialize query optimization rules"""
        self.optimization_rules = [
            self._optimize_select_queries,
            self._optimize_join_queries,
            self._optimize_where_clauses,
            self._optimize_order_by_clauses,
            self._optimize_group_by_clauses,
            self._optimize_subqueries
        ]
    
    def _optimize_select_queries(self, query: str) -> str:
        """Optimize SELECT queries"""
        try:
            query_lower = query.lower().strip()
            
            # Replace SELECT * with specific columns when possible
            if 'select *' in query_lower:
                # This would typically analyze the query to determine specific columns
                # For now, just log the optimization opportunity
                logger.info("Query optimization opportunity: Replace SELECT * with specific columns")
            
            # Add LIMIT to queries without it
            if query_lower.startswith('select') and 'limit' not in query_lower and 'order by' in query_lower:
                query += ' LIMIT 1000'  # Add default limit
                logger.info("Added default LIMIT to query")
            
            return query
            
        except Exception as e:
            logger.error(f"Error optimizing SELECT query: {e}")
            return query
    
    def _optimize_join_queries(self, query: str) -> str:
        """Optimize JOIN queries"""
        try:
            query_lower = query.lower()
            
            # Ensure JOINs have proper WHERE clauses
            if 'join' in query_lower and 'where' not in query_lower:
                logger.info("Query optimization opportunity: Add WHERE clause to JOIN query")
            
            # Optimize JOIN order (smaller tables first)
            if 'join' in query_lower:
                logger.info("Query optimization opportunity: Consider JOIN order optimization")
            
            return query
            
        except Exception as e:
            logger.error(f"Error optimizing JOIN query: {e}")
            return query
    
    def _optimize_where_clauses(self, query: str) -> str:
        """Optimize WHERE clauses"""
        try:
            query_lower = query.lower()
            
            # Optimize LIKE queries
            if 'like' in query_lower and '%' in query:
                logger.info("Query optimization opportunity: Consider full-text search instead of LIKE")
            
            # Optimize IN clauses
            if ' in (' in query_lower:
                logger.info("Query optimization opportunity: Consider using EXISTS instead of IN for large lists")
            
            return query
            
        except Exception as e:
            logger.error(f"Error optimizing WHERE clause: {e}")
            return query
    
    def _optimize_order_by_clauses(self, query: str) -> str:
        """Optimize ORDER BY clauses"""
        try:
            query_lower = query.lower()
            
            # Ensure ORDER BY has LIMIT
            if 'order by' in query_lower and 'limit' not in query_lower:
                query += ' LIMIT 1000'
                logger.info("Added LIMIT to ORDER BY query")
            
            return query
            
        except Exception as e:
            logger.error(f"Error optimizing ORDER BY clause: {e}")
            return query
    
    def _optimize_group_by_clauses(self, query: str) -> str:
        """Optimize GROUP BY clauses"""
        try:
            query_lower = query.lower()
            
            # Check for missing indexes on GROUP BY columns
            if 'group by' in query_lower:
                logger.info("Query optimization opportunity: Ensure indexes exist on GROUP BY columns")
            
            return query
            
        except Exception as e:
            logger.error(f"Error optimizing GROUP BY clause: {e}")
            return query
    
    def _optimize_subqueries(self, query: str) -> str:
        """Optimize subqueries"""
        try:
            query_lower = query.lower()
            
            # Convert correlated subqueries to JOINs when possible
            if 'exists' in query_lower and 'select' in query_lower:
                logger.info("Query optimization opportunity: Consider converting EXISTS to JOIN")
            
            return query
            
        except Exception as e:
            logger.error(f"Error optimizing subquery: {e}")
            return query
    
    def optimize_query(self, query: str) -> str:
        """Apply all optimization rules to a query"""
        try:
            optimized_query = query
            
            for rule in self.optimization_rules:
                optimized_query = rule(optimized_query)
            
            return optimized_query
            
        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            return query
    
    def _generate_query_hash(self, query: str) -> str:
        """Generate hash for query caching"""
        # Normalize query for consistent hashing
        normalized_query = ' '.join(query.lower().split())
        return hashlib.md5(normalized_query.encode()).hexdigest()
    
    async def execute_query(self, query: str, params: tuple = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Execute optimized query with caching"""
        start_time = time.time()
        query_hash = self._generate_query_hash(query)
        
        try:
            # Check cache first
            if use_cache and self.connection_pool.config.enable_query_cache:
                if query_hash in self.query_cache:
                    self.query_metrics[query_hash].cache_hits += 1
                    logger.info(f"Query cache hit: {query_hash}")
                    return self.query_cache[query_hash]
            
            # Optimize query
            optimized_query = self.optimize_query(query)
            
            # Execute query
            connection = self.connection_pool.get_connection()
            try:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    if params:
                        cursor.execute(optimized_query, params)
                    else:
                        cursor.execute(optimized_query)
                    
                    results = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    result_list = [dict(row) for row in results]
                    
                    # Cache results
                    if use_cache and self.connection_pool.config.enable_query_cache:
                        self.query_cache[query_hash] = result_list
                        self.query_metrics[query_hash].cache_misses += 1
                    
                    return result_list
                    
            finally:
                self.connection_pool.return_connection(connection)
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
        finally:
            # Update query metrics
            execution_time = (time.time() - start_time) * 1000
            
            if query_hash not in self.query_metrics:
                self.query_metrics[query_hash] = QueryMetrics(
                    query_hash=query_hash,
                    query_text=query,
                    last_executed=datetime.now()
                )
            
            metrics = self.query_metrics[query_hash]
            metrics.execution_count += 1
            metrics.total_execution_time_ms += execution_time
            metrics.average_execution_time_ms = metrics.total_execution_time_ms / metrics.execution_count
            metrics.min_execution_time_ms = min(metrics.min_execution_time_ms, execution_time)
            metrics.max_execution_time_ms = max(metrics.max_execution_time_ms, execution_time)
            metrics.last_executed = datetime.now()
            
            # Check for slow queries
            if execution_time > self.connection_pool.config.slow_query_threshold_ms:
                metrics.slow_query_count += 1
                self.connection_pool.slow_queries.append(query)
                self.connection_pool.connection_metrics.slow_queries_count += 1
                
                if self.connection_pool.config.enable_slow_query_logging:
                    logger.warning(f"Slow query detected ({execution_time:.2f}ms): {query}")
    
    async def execute_batch_query(self, queries: List[str], params_list: List[tuple] = None) -> List[List[Dict[str, Any]]]:
        """Execute multiple queries in batch"""
        try:
            results = []
            
            for i, query in enumerate(queries):
                params = params_list[i] if params_list and i < len(params_list) else None
                result = await self.execute_query(query, params)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing batch queries: {e}")
            raise
    
    def get_query_metrics(self) -> Dict[str, QueryMetrics]:
        """Get query performance metrics"""
        return self.query_metrics
    
    def get_slow_queries(self) -> List[str]:
        """Get list of slow queries"""
        return list(self.connection_pool.slow_queries)
    
    def clear_query_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")

class DatabaseOptimizer:
    """Comprehensive database optimization system"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = ConnectionPool(config)
        self.query_optimizer = QueryOptimizer(self.connection_pool)
        self.index_optimizer = None
        self.vacuum_scheduler = None
        
        # Initialize additional optimizers
        asyncio.create_task(self._initialize_optimizers())
    
    async def _initialize_optimizers(self):
        """Initialize additional database optimizers"""
        try:
            # Initialize index optimizer
            self.index_optimizer = IndexOptimizer(self.connection_pool)
            
            # Initialize vacuum scheduler
            self.vacuum_scheduler = VacuumScheduler(self.connection_pool)
            
            logger.info("✅ Database optimizers initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database optimizers: {e}")
    
    async def execute_optimized_query(self, query: str, params: tuple = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Execute query with full optimization"""
        return await self.query_optimizer.execute_query(query, params, use_cache)
    
    async def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query performance and provide recommendations"""
        try:
            # Execute EXPLAIN ANALYZE
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            connection = self.connection_pool.get_connection()
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute(explain_query)
                    explain_result = cursor.fetchone()[0]
                    
                    # Analyze execution plan
                    analysis = self._analyze_execution_plan(explain_result)
                    
                    return analysis
                    
            finally:
                self.connection_pool.return_connection(connection)
                
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            return {"error": str(e)}
    
    def _analyze_execution_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze PostgreSQL execution plan"""
        try:
            analysis = {
                "total_cost": plan[0]["Plan"]["Total Cost"],
                "execution_time": plan[0]["Plan"]["Actual Total Time"],
                "recommendations": []
            }
            
            # Analyze for optimization opportunities
            if plan[0]["Plan"]["Total Cost"] > 1000:
                analysis["recommendations"].append("High cost query - consider adding indexes")
            
            if plan[0]["Plan"]["Actual Total Time"] > 1000:
                analysis["recommendations"].append("Slow execution time - consider query optimization")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing execution plan: {e}")
            return {"error": str(e)}
    
    def get_database_metrics(self) -> DatabaseMetrics:
        """Get comprehensive database metrics"""
        return self.connection_pool.get_metrics()
    
    def get_query_metrics(self) -> Dict[str, QueryMetrics]:
        """Get query performance metrics"""
        return self.query_optimizer.get_query_metrics()

class IndexOptimizer:
    """Database index optimization system"""
    
    def __init__(self, connection_pool: ConnectionPool):
        self.connection_pool = connection_pool
        self.index_recommendations = []
    
    async def analyze_index_usage(self) -> List[Dict[str, Any]]:
        """Analyze index usage and provide recommendations"""
        try:
            query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE idx_scan = 0
            ORDER BY idx_scan;
            """
            
            results = await self.connection_pool.query_optimizer.execute_query(query)
            
            recommendations = []
            for row in results:
                if row['idx_scan'] == 0:
                    recommendations.append({
                        "table": f"{row['schemaname']}.{row['tablename']}",
                        "index": row['indexname'],
                        "recommendation": "Consider dropping unused index",
                        "reason": "Index has never been used"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error analyzing index usage: {e}")
            return []

class VacuumScheduler:
    """Database vacuum and maintenance scheduler"""
    
    def __init__(self, connection_pool: ConnectionPool):
        self.connection_pool = connection_pool
        self.vacuum_schedule = {}
    
    async def schedule_vacuum(self, table_name: str, frequency_hours: int = 24):
        """Schedule regular vacuum for a table"""
        self.vacuum_schedule[table_name] = {
            "frequency_hours": frequency_hours,
            "last_vacuum": None,
            "next_vacuum": datetime.now() + timedelta(hours=frequency_hours)
        }
    
    async def run_scheduled_vacuums(self):
        """Run scheduled vacuum operations"""
        try:
            current_time = datetime.now()
            
            for table_name, schedule in self.vacuum_schedule.items():
                if schedule["next_vacuum"] <= current_time:
                    await self._vacuum_table(table_name)
                    schedule["last_vacuum"] = current_time
                    schedule["next_vacuum"] = current_time + timedelta(hours=schedule["frequency_hours"])
            
        except Exception as e:
            logger.error(f"Error running scheduled vacuums: {e}")
    
    async def _vacuum_table(self, table_name: str):
        """Vacuum a specific table"""
        try:
            query = f"VACUUM ANALYZE {table_name}"
            connection = self.connection_pool.get_connection()
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    logger.info(f"Vacuumed table: {table_name}")
                    
            finally:
                self.connection_pool.return_connection(connection)
                
        except Exception as e:
            logger.error(f"Error vacuuming table {table_name}: {e}")

# Global database optimizer instance
database_optimizer = None

def initialize_database_optimizer(config: DatabaseConfig):
    """Initialize global database optimizer"""
    global database_optimizer
    database_optimizer = DatabaseOptimizer(config)
    logger.info("✅ Database optimizer initialized successfully")
