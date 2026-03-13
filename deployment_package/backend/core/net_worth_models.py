"""
Net Worth Snapshot Model
========================
Stores a point-in-time net worth snapshot for a user so the app can
render a historical net worth chart and compute change-over-time metrics.

One row per user per day (enforced by unique_together).  Captured by the
Celery beat task `capture_net_worth_snapshots` and on-demand when the
user loads the Wealth screen.

Fields
------
net_worth          : assets − liabilities (the headline number)
portfolio_value    : sum of Portfolio.total_value
savings_balance    : sum of CHECKING + SAVINGS BankAccount balances
debt               : sum of CreditCard.balance
captured_at        : the date this snapshot represents (not created_at)
source             : "scheduled" | "on_demand" | "backfill"
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class NetWorthSnapshot(models.Model):
    """Daily net worth snapshot for a user."""

    SOURCE_CHOICES = [
        ('scheduled',  'Scheduled (Celery beat)'),
        ('on_demand',  'On-demand (user loaded Wealth screen)'),
        ('backfill',   'Backfill'),
    ]

    user           = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='net_worth_snapshots'
    )
    captured_at    = models.DateField()                      # one per day
    net_worth      = models.DecimalField(max_digits=18, decimal_places=2)
    portfolio_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    savings_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    debt           = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    source         = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='on_demand')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'net_worth_snapshots'
        unique_together = [('user', 'captured_at')]
        ordering = ['-captured_at']
        indexes = [
            models.Index(fields=['user', '-captured_at']),
        ]

    def __str__(self):
        return f"{self.user_id} @ {self.captured_at}: ${self.net_worth:,.0f}"
