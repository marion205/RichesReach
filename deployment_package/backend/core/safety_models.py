"""
Safety v0 — central decision log for cross-cutting guardrails (Ask, auto-execute).
DeFi and broker have their own ledgers (DeFiRepairDecision, BrokerGuardrailLog).
"""
from django.db import models


class SafetyDecisionLog(models.Model):
    """
    Append-only log for safety-relevant decisions that are not specific to
    DeFi or broker (e.g. Ask buy/add disclaimer, auto-execute block).
    user_id is stored as string so we can log from FastAPI without resolving User.
    """
    user_id = models.CharField(max_length=64, db_index=True, help_text='User ID from request or Django user pk')
    action_type = models.CharField(max_length=64, db_index=True)  # e.g. ask_buy_add, auto_execute
    decision = models.CharField(max_length=32, db_index=True)     # e.g. disclaimer_applied, blocked, allowed
    reason = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'safety_decision_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.action_type} {self.decision} user={self.user_id}"
