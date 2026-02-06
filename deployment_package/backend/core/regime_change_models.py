"""
Regime Change Models - Records regime transitions for adaptive bandit discounting.
"""
from django.db import models


class RegimeChangeEvent(models.Model):
    """
    Records a regime transition detected by the regime detector.
    Used by AdaptiveBanditService to compute discount rates:
    more regime changes → faster forgetting of old evidence.
    """
    symbol = models.CharField(max_length=10, db_index=True)
    previous_regime = models.CharField(max_length=30)
    new_regime = models.CharField(max_length=30)
    detected_at = models.DateTimeField(db_index=True)
    confidence = models.FloatField(default=1.0)

    class Meta:
        db_table = 'regime_change_events'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['detected_at', 'symbol']),
        ]

    def __str__(self):
        return f"{self.symbol}: {self.previous_regime} → {self.new_regime} at {self.detected_at}"
