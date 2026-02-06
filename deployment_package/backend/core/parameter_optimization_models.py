"""
Parameter Optimization Models - Records Optuna optimization runs and results.
"""
from django.db import models
import uuid


class ParameterOptimizationRun(models.Model):
    """Records Optuna Bayesian optimization runs and their results."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strategy_name = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Search space definition
    parameter_space = models.JSONField(default=dict)

    # Results
    best_parameters = models.JSONField(default=dict)
    best_objective_value = models.FloatField(null=True, blank=True)  # e.g., Sharpe ratio
    n_trials = models.IntegerField(default=50)
    all_trials = models.JSONField(default=list)  # [{params, value}, ...]

    # Metadata
    triggered_by = models.CharField(max_length=50, default='nightly_backtest')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'parameter_optimization_runs'
        ordering = ['-created_at']
        verbose_name = 'Parameter Optimization Run'
        verbose_name_plural = 'Parameter Optimization Runs'

    def __str__(self):
        return f"{self.strategy_name} [{self.status}] - best={self.best_objective_value}"
