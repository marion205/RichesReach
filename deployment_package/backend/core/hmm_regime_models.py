"""
HMM Regime Models - Stores HMM regime detection snapshots and training records.
"""
import uuid
from django.db import models


class HMMRegimeSnapshot(models.Model):
    """
    Records a regime detection result from the HMM + rule-based ensemble.
    Tracks agreement/disagreement between the two detectors.
    """
    symbol = models.CharField(max_length=10, db_index=True)
    hmm_regime = models.CharField(max_length=30)
    hmm_probabilities = models.JSONField(
        default=dict,
        help_text='Probability distribution: {"CRASH": 0.05, "TREND_UP": 0.70, ...}'
    )
    rule_regime = models.CharField(max_length=30)
    ensemble_regime = models.CharField(max_length=30)
    transition_probs = models.JSONField(
        default=dict,
        help_text='Transition probabilities from current state'
    )
    detected_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'hmm_regime_snapshots'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['symbol', 'detected_at']),
        ]

    def __str__(self):
        agreement = "AGREE" if self.hmm_regime == self.rule_regime else "DISAGREE"
        return f"{self.symbol} [{agreement}] hmm={self.hmm_regime} rule={self.rule_regime} → {self.ensemble_regime}"


class HMMTrainingRecord(models.Model):
    """Records metadata for each HMM training run."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=10, db_index=True)
    n_states = models.IntegerField(default=5)
    log_likelihood = models.FloatField(null=True, blank=True)
    bic = models.FloatField(null=True, blank=True)
    aic = models.FloatField(null=True, blank=True)
    state_mapping = models.JSONField(
        default=dict,
        help_text='Maps hidden state index to semantic label: {0: "CRASH", 1: "TREND_UP", ...}'
    )
    training_days = models.IntegerField(default=0)
    model_path = models.CharField(max_length=300)
    is_active = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hmm_training_records'
        ordering = ['-created_at']

    def __str__(self):
        status = "ACTIVE" if self.is_active else "inactive"
        return f"HMM [{status}] {self.n_states} states, {self.training_days} days, LL={self.log_likelihood}"
