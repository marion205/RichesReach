"""
Shadow Model Models - Tracks candidate ML models through training, validation, and promotion.
Part of the evolutionary model promotion system.
"""
import uuid
from django.db import models


class ShadowModel(models.Model):
    """
    A candidate ML model being validated against the incumbent.
    Lifecycle: TRAINING → VALIDATING (72hr) → PROMOTED or EXPIRED
    """
    STATUS_CHOICES = [
        ('TRAINING', 'Training'),
        ('VALIDATING', 'Validating'),
        ('PROMOTED', 'Promoted'),
        ('EXPIRED', 'Expired'),
        ('FAILED', 'Failed'),
    ]

    ALGORITHM_CHOICES = [
        ('gradient_boosting', 'Gradient Boosting'),
        ('random_forest', 'Random Forest'),
        ('mlp', 'MLP Neural Network'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    algorithm = models.CharField(max_length=30, choices=ALGORITHM_CHOICES)
    hyperparameters = models.JSONField(default=dict)
    model_path = models.CharField(max_length=300)
    scaler_path = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TRAINING')

    train_score = models.FloatField(null=True, blank=True)
    test_score = models.FloatField(null=True, blank=True)
    validation_accuracy = models.FloatField(null=True, blank=True)
    incumbent_accuracy = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    validation_start = models.DateTimeField(null=True, blank=True)
    validation_end = models.DateTimeField(null=True, blank=True)
    promoted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'shadow_models'
        ordering = ['-created_at']
        verbose_name = 'Shadow Model'

    def __str__(self):
        return f"{self.algorithm} [{self.status}] train={self.train_score}"


class ShadowPrediction(models.Model):
    """
    Records a shadow model's prediction alongside the incumbent's for comparison.
    Accumulated over 72hrs to evaluate whether shadow beats incumbent.
    """
    shadow_model = models.ForeignKey(
        ShadowModel, on_delete=models.CASCADE, related_name='predictions'
    )
    signal = models.ForeignKey(
        'core.DayTradingSignal', on_delete=models.CASCADE, related_name='shadow_predictions'
    )
    shadow_score = models.FloatField()
    incumbent_score = models.FloatField()
    actual_outcome = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shadow_predictions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shadow_model', 'created_at']),
        ]
