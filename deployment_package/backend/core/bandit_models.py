"""
Bandit Models - Thompson Sampling for strategy allocation.
Each arm represents a strategy with a Beta distribution posterior
updated by win/loss rewards from backtest results and real outcomes.
"""
from django.db import models


class BanditArm(models.Model):
    """
    Thompson Sampling arm for strategy allocation.
    Each arm = one strategy, with Beta(alpha, beta) posterior.
    """
    strategy_slug = models.CharField(max_length=50, unique=True, db_index=True)
    # e.g., 'breakout', 'mean_reversion', 'momentum', 'etf_rotation'

    # Beta distribution parameters (posterior)
    alpha = models.FloatField(default=1.0)  # Prior successes + 1
    beta_param = models.FloatField(default=1.0)  # Prior failures + 1

    total_pulls = models.IntegerField(default=0)
    total_rewards = models.FloatField(default=0.0)

    # Context-dependent posteriors (keyed by regime)
    context_alphas = models.JSONField(
        default=dict,
        help_text='Regime-specific alpha values, e.g. {"TREND_UP": 5.0}'
    )
    context_betas = models.JSONField(
        default=dict,
        help_text='Regime-specific beta values, e.g. {"TREND_UP": 2.0}'
    )

    # Current allocation weight (output of Thompson Sampling Monte Carlo)
    current_weight = models.FloatField(default=0.25)

    # Adaptive Discounted Thompson Sampling (ADTS) fields
    discount_rate = models.FloatField(
        default=0.995,
        help_text='Current adaptive discount rate (0.90 = aggressive forgetting, 0.995 = slow)'
    )
    reward_history = models.JSONField(
        default=list,
        help_text='Sliding window of last 100 rewards [{reward, timestamp, regime}, ...]'
    )
    regime_change_count = models.IntegerField(
        default=0,
        help_text='Recent regime changes (decayed over time)'
    )

    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bandit_arms'
        verbose_name = 'Bandit Arm'
        verbose_name_plural = 'Bandit Arms'

    def __str__(self):
        win_rate = self.alpha / (self.alpha + self.beta_param) if (self.alpha + self.beta_param) > 0 else 0
        return f"{self.strategy_slug}: alpha={self.alpha:.1f}, beta={self.beta_param:.1f}, win_rate={win_rate:.2%}"

    @property
    def expected_win_rate(self):
        total = self.alpha + self.beta_param
        return self.alpha / total if total > 0 else 0.5
