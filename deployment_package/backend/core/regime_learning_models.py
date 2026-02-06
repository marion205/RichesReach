"""
Regime Learning Models - Stores learned regime detection thresholds.
"""
from django.db import models


class RegimeThresholdSet(models.Model):
    """
    Stores a set of learned regime detection thresholds.
    The active set overrides the hardcoded defaults in RegimeDetector.
    """
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=False, db_index=True)

    thresholds = models.JSONField(
        default=dict,
        help_text='Learned thresholds, e.g. {"rv_spike_threshold": 1.15, "price_crash_threshold": -0.035}'
    )

    # Performance of this threshold set
    accuracy = models.FloatField(null=True, blank=True)
    sharpe_improvement = models.FloatField(null=True, blank=True)

    optimization_run_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'regime_threshold_sets'
        ordering = ['-created_at']
        verbose_name = 'Regime Threshold Set'
        verbose_name_plural = 'Regime Threshold Sets'

    def __str__(self):
        status = "ACTIVE" if self.is_active else "inactive"
        return f"v{self.version} [{status}] accuracy={self.accuracy}"
