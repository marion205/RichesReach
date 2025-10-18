"""
DeFi Analytics GraphQL Schema
Time-series analytics and performance metrics
"""
import graphene
from graphene_django import DjangoObjectType
from .models_analytics import PoolAnalytics, PositionSnapshot, PortfolioMetrics, YieldHistory
from .services.analytics import get_pool_performance_metrics, calculate_portfolio_metrics

class PoolAnalyticsPointType(DjangoObjectType):
    class Meta:
        model = PoolAnalytics
        fields = "__all__"

class PositionSnapshotType(DjangoObjectType):
    class Meta:
        model = PositionSnapshot
        fields = "__all__"

class PortfolioMetricsType(DjangoObjectType):
    class Meta:
        model = PortfolioMetrics
        fields = "__all__"

class YieldHistoryType(DjangoObjectType):
    class Meta:
        model = YieldHistory
        fields = "__all__"

class PerformanceMetricsType(graphene.ObjectType):
    total_return = graphene.Float()
    volatility = graphene.Float()
    max_drawdown = graphene.Float()
    sharpe_ratio = graphene.Float()
    il_impact = graphene.Float()

class PortfolioMetricsSummaryType(graphene.ObjectType):
    total_value_usd = graphene.Float()
    weighted_apy = graphene.Float()
    portfolio_risk = graphene.Float()
    diversification_score = graphene.Float()
    active_positions = graphene.Int()
    protocols_count = graphene.Int()

class DeFiAnalyticsQuery(graphene.ObjectType):
    pool_analytics = graphene.List(
        PoolAnalyticsPointType,
        pool_id=graphene.ID(required=True),
        days=graphene.Int(default_value=30)
    )
    
    position_snapshots = graphene.List(
        PositionSnapshotType,
        position_id=graphene.ID(required=True),
        days=graphene.Int(default_value=30)
    )
    
    portfolio_metrics = graphene.List(
        PortfolioMetricsType,
        days=graphene.Int(default_value=30)
    )
    
    pool_performance = graphene.Field(
        PerformanceMetricsType,
        pool_id=graphene.ID(required=True),
        days=graphene.Int(default_value=30)
    )
    
    portfolio_summary = graphene.Field(
        PortfolioMetricsSummaryType,
        days=graphene.Int(default_value=30)
    )
    
    yield_history = graphene.List(
        YieldHistoryType,
        pool_id=graphene.ID(required=True),
        days=graphene.Int(default_value=30)
    )

    def resolve_pool_analytics(self, info, pool_id, days):
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        return PoolAnalytics.objects.filter(
            pool_id=pool_id,
            date__range=[start_date, end_date]
        ).order_by('date')

    def resolve_position_snapshots(self, info, position_id, days):
        from django.utils import timezone
        from datetime import timedelta
        
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days)
        
        return PositionSnapshot.objects.filter(
            position_id=position_id,
            timestamp__range=[start_time, end_time]
        ).order_by('timestamp')

    def resolve_portfolio_metrics(self, info, days):
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        return PortfolioMetrics.objects.filter(
            user=info.context.user,
            date__range=[start_date, end_date]
        ).order_by('date')

    def resolve_pool_performance(self, info, pool_id, days):
        from .models_defi import Pool
        
        try:
            pool = Pool.objects.get(id=pool_id)
            metrics = get_pool_performance_metrics(pool, days)
            if metrics:
                return PerformanceMetricsType(
                    total_return=metrics.get('total_return', 0),
                    volatility=metrics.get('volatility', 0),
                    max_drawdown=metrics.get('max_drawdown', 0),
                    sharpe_ratio=metrics.get('sharpe_ratio', 0),
                    il_impact=metrics.get('il_impact', 0),
                )
        except Pool.DoesNotExist:
            pass
        return None

    def resolve_portfolio_summary(self, info, days):
        from .models_defi import FarmPosition
        
        positions = FarmPosition.objects.filter(
            user=info.context.user,
            is_active=True
        ).select_related('pool', 'pool__protocol')
        
        metrics = calculate_portfolio_metrics(positions)
        if metrics:
            return PortfolioMetricsSummaryType(
                total_value_usd=metrics.get('total_value_usd', 0),
                weighted_apy=metrics.get('weighted_apy', 0),
                portfolio_risk=metrics.get('portfolio_risk', 0),
                diversification_score=metrics.get('diversification_score', 0),
                active_positions=metrics.get('active_positions', 0),
                protocols_count=metrics.get('protocols_count', 0),
            )
        return None

    def resolve_yield_history(self, info, pool_id, days):
        from django.utils import timezone
        from datetime import timedelta
        
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days)
        
        return YieldHistory.objects.filter(
            pool_id=pool_id,
            timestamp__range=[start_time, end_time]
        ).order_by('timestamp')
