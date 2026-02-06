"""
Execution RL Models - Reinforcement learning for execution optimization.
Stores policies (Q-tables) and experience replay buffer.
"""
import uuid
from django.db import models


class ExecutionPolicy(models.Model):
    """
    Stores a trained execution policy (Q-table) for optimal order execution.
    The active policy provides execution recommendations alongside signals.
    """
    POLICY_TYPE_CHOICES = [
        ('q_table', 'Q-Table'),
        ('contextual_bandit', 'Contextual Bandit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.IntegerField(default=1)
    policy_type = models.CharField(max_length=30, choices=POLICY_TYPE_CHOICES, default='q_table')
    policy_data = models.JSONField(
        default=dict,
        help_text='Serialized Q-table: {"state_key": {"action": q_value, ...}, ...}'
    )
    is_active = models.BooleanField(default=False, db_index=True)
    train_episodes = models.IntegerField(default=0)
    avg_reward = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'execution_policies'
        ordering = ['-created_at']

    def __str__(self):
        status = "ACTIVE" if self.is_active else "inactive"
        return f"v{self.version} [{status}] episodes={self.train_episodes} avg_reward={self.avg_reward}"


class ExecutionExperience(models.Model):
    """
    Records a single execution experience for RL training.
    State-action-reward tuple from actual user fills.
    """
    ACTION_CHOICES = [
        ('MARKET_IMMEDIATE', 'Market Immediate'),
        ('LIMIT_TIGHT', 'Limit Tight'),
        ('LIMIT_LOOSE', 'Limit Loose'),
        ('WAIT_5MIN', 'Wait 5 Minutes'),
    ]

    user_fill = models.OneToOneField(
        'core.UserFill', on_delete=models.CASCADE, related_name='rl_experience'
    )
    state_features = models.JSONField(
        default=dict,
        help_text='Discretized state: {spread_bps, volume_ratio, time_bucket, ...}'
    )
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reward = models.FloatField(
        help_text='Negative slippage + quality bonus, bounded [-50, +10]'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'execution_experiences'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
        ]
