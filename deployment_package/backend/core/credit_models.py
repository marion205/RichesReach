"""
Credit Building Models
Django ORM models for credit score tracking and credit card management
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

User = get_user_model()


class CreditScore(models.Model):
    """User's credit score record"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_scores')
    score = models.IntegerField()
    provider = models.CharField(
        max_length=50,
        choices=[
            ('experian', 'Experian'),
            ('equifax', 'Equifax'),
            ('transunion', 'TransUnion'),
            ('self_reported', 'Self Reported'),
            ('credit_karma', 'Credit Karma'),
        ],
        default='self_reported'
    )
    date = models.DateField(default=timezone.now)
    factors = models.JSONField(default=dict, blank=True)  # Payment history, utilization, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date', 'provider']

    def get_score_range(self) -> str:
        """Get score range category"""
        if self.score < 580:
            return 'Poor'
        elif self.score < 670:
            return 'Fair'
        elif self.score < 740:
            return 'Good'
        elif self.score < 800:
            return 'Very Good'
        else:
            return 'Excellent'

    def __str__(self):
        return f"{self.user.email} - {self.score} ({self.provider}) - {self.date}"


class CreditCard(models.Model):
    """User's credit card account"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_cards')
    name = models.CharField(max_length=200)
    limit = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    utilization = models.FloatField(default=0)  # 0-1 (0% to 100%)
    yodlee_account_id = models.CharField(max_length=100, null=True, blank=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    payment_due_date = models.DateField(null=True, blank=True)
    minimum_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def calculate_utilization(self):
        """Calculate utilization percentage"""
        if self.limit > 0:
            self.utilization = float(self.balance / self.limit)
        else:
            self.utilization = 0
        return self.utilization

    def __str__(self):
        return f"{self.user.email} - {self.name} (${self.balance}/{self.limit})"


class CreditAction(models.Model):
    """Credit building actions for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_actions')
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('AUTOPAY_SETUP', 'Set Up Autopay'),
            ('CARD_APPLIED', 'Applied for Card'),
            ('PAYMENT_MADE', 'Made Payment'),
            ('LIMIT_INCREASE', 'Requested Limit Increase'),
            ('UTILIZATION_REDUCED', 'Reduced Utilization'),
        ]
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    projected_score_gain = models.IntegerField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.action_type} - {'Completed' if self.completed else 'Pending'}"


class CreditProjection(models.Model):
    """ML-powered credit score projections"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_projections')
    current_score = models.IntegerField()
    projected_score_6m = models.IntegerField()
    projected_score_12m = models.IntegerField(null=True, blank=True)
    top_action = models.CharField(max_length=200)
    confidence = models.FloatField(default=0.5)  # 0-1
    factors = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.current_score} → {self.projected_score_6m} (confidence: {self.confidence:.2f})"

