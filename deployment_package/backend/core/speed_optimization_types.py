"""
GraphQL Types for Speed Optimization
Latency monitoring and optimization status queries.
"""
import graphene
from .speed_optimization_service import get_speed_optimization_service
from typing import Dict, Any


class LatencyStatsType(graphene.ObjectType):
    """Latency statistics"""
    count = graphene.Int()
    avg_ms = graphene.Float()
    median_ms = graphene.Float()
    p95_ms = graphene.Float()
    p99_ms = graphene.Float()
    min_ms = graphene.Float()
    max_ms = graphene.Float()
    below_target = graphene.Float()  # % below 500ms target
    target_ms = graphene.Float()


class OptimizationStatusType(graphene.ObjectType):
    """Speed optimization status"""
    websocket_active = graphene.Boolean()
    model_optimized = graphene.Boolean()
    latency_target_ms = graphene.Float()
    current_avg_latency_ms = graphene.Float()
    below_target_percent = graphene.Float()
    recommendations = graphene.List(graphene.String)


class SpeedOptimizationQueries(graphene.ObjectType):
    """GraphQL queries for speed optimization"""
    
    speed_optimization_status = graphene.Field(
        OptimizationStatusType,
        description="Get current speed optimization status"
    )
    
    latency_stats = graphene.Field(
        LatencyStatsType,
        operation=graphene.String(),
        description="Get latency statistics (optionally filtered by operation)"
    )
    
    def resolve_speed_optimization_status(self, info) -> OptimizationStatusType:
        """Resolve speed optimization status"""
        service = get_speed_optimization_service()
        status = service.get_optimization_status()
        
        return OptimizationStatusType(
            websocket_active=status['websocket_active'],
            model_optimized=status['model_optimized'],
            latency_target_ms=status['latency_target_ms'],
            current_avg_latency_ms=status['current_avg_latency_ms'],
            below_target_percent=status['below_target_percent'],
            recommendations=status['recommendations']
        )
    
    def resolve_latency_stats(self, info, operation: str = None) -> LatencyStatsType:
        """Resolve latency statistics"""
        service = get_speed_optimization_service()
        stats = service.get_latency_stats(operation=operation)
        
        return LatencyStatsType(
            count=stats.get('count', 0),
            avg_ms=stats.get('avg_ms', 0.0),
            median_ms=stats.get('median_ms', 0.0),
            p95_ms=stats.get('p95_ms', 0.0),
            p99_ms=stats.get('p99_ms', 0.0),
            min_ms=stats.get('min_ms', 0.0),
            max_ms=stats.get('max_ms', 0.0),
            below_target=stats.get('below_target', 0.0),
            target_ms=stats.get('target_ms', 500.0)
        )

