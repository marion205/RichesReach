"""
DeFi Analytics Models
Time-series data for pool performance and analytics
"""
from django.db import models
from .models_defi import Pool

class PoolAnalytics(models.Model):
    """Daily analytics snapshot for each pool"""
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    fee_apy = models.FloatField(null=True, blank=True)
    il_estimate = models.FloatField(null=True, blank=True)
    net_apy = models.FloatField(null=True, blank=True)  # fee_apy + rewards - IL
    volume_24h_usd = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    tvl_usd = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    risk_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("pool", "date")
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["pool", "date"]),
            models.Index(fields=["date"]),
        ]

class PositionSnapshot(models.Model):
    """Hourly snapshots of user positions for performance tracking"""
    position = models.ForeignKey('core.FarmPosition', on_delete=models.CASCADE, related_name='snapshots')
    timestamp = models.DateTimeField()
    staked_lp = models.DecimalField(max_digits=38, decimal_places=18)
    rewards_earned = models.DecimalField(max_digits=38, decimal_places=18)
    total_value_usd = models.DecimalField(max_digits=24, decimal_places=6)
    realized_apy = models.FloatField()
    pool_apy = models.FloatField()  # Pool APY at time of snapshot
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("position", "timestamp")
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["position", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]

class PortfolioMetrics(models.Model):
    """Daily portfolio-level metrics for users"""
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='portfolio_metrics')
    date = models.DateField()
    total_value_usd = models.DecimalField(max_digits=24, decimal_places=6)
    weighted_apy = models.FloatField()
    portfolio_risk = models.FloatField()
    diversification_score = models.FloatField()
    active_positions = models.IntegerField()
    protocols_count = models.IntegerField()
    total_return_1d = models.FloatField(null=True, blank=True)
    total_return_7d = models.FloatField(null=True, blank=True)
    total_return_30d = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["date"]),
        ]

class YieldHistory(models.Model):
    """Historical yield data for pools"""
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name='yield_history')
    timestamp = models.DateTimeField()
    apy_base = models.FloatField()
    apy_reward = models.FloatField()
    total_apy = models.FloatField()
    tvl_usd = models.DecimalField(max_digits=24, decimal_places=6)
    volume_24h_usd = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("pool", "timestamp")
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["pool", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]
