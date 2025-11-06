"""
Banking Models - Bank accounts, transactions, and provider accounts
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class BankProviderAccount(models.Model):
    """Yodlee provider account (links to Yodlee providerAccountId)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_provider_accounts')
    provider_account_id = models.CharField(max_length=255, unique=True, db_index=True)
    provider_name = models.CharField(max_length=255)  # e.g., "Bank of America"
    provider_id = models.CharField(max_length=255, blank=True)  # Yodlee provider ID
    access_token_enc = models.TextField(blank=True)  # Encrypted Yodlee access token
    refresh_token_enc = models.TextField(blank=True)  # Encrypted refresh token
    status = models.CharField(
        max_length=50,
        choices=[
            ('ACTIVE', 'Active'),
            ('INACTIVE', 'Inactive'),
            ('ERROR', 'Error'),
            ('DELETED', 'Deleted'),
        ],
        default='ACTIVE'
    )
    last_refresh = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_provider_accounts'
        unique_together = [('user', 'provider_account_id')]
        indexes = [
            models.Index(fields=['user', 'provider_account_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.provider_name} ({self.provider_account_id})"


class BankAccount(models.Model):
    """User's bank account (normalized from Yodlee)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    provider_account = models.ForeignKey(
        BankProviderAccount,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        null=True,
        blank=True
    )
    yodlee_account_id = models.CharField(max_length=255, db_index=True)  # Yodlee accountId
    provider = models.CharField(max_length=255)  # e.g., "Bank of America"
    name = models.CharField(max_length=255)  # Account name
    mask = models.CharField(max_length=10)  # Last 4 digits
    account_type = models.CharField(max_length=50)  # e.g., "CHECKING", "SAVINGS", "CREDIT_CARD"
    account_subtype = models.CharField(max_length=50, blank=True)  # e.g., "checking", "savings"
    currency = models.CharField(max_length=10, default='USD')
    balance_current = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    balance_available = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    last_updated = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_accounts'
        unique_together = [('user', 'yodlee_account_id')]
        indexes = [
            models.Index(fields=['user', 'yodlee_account_id']),
            models.Index(fields=['user', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.mask})"


class BankTransaction(models.Model):
    """Bank transaction (normalized from Yodlee)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_transactions')
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    yodlee_transaction_id = models.CharField(max_length=255, db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    description = models.CharField(max_length=500)
    merchant_name = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=100, blank=True)
    subcategory = models.CharField(max_length=100, blank=True)
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('DEBIT', 'Debit'),
            ('CREDIT', 'Credit'),
        ]
    )
    posted_date = models.DateField()
    transaction_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('POSTED', 'Posted'),
            ('PENDING', 'Pending'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='POSTED'
    )
    raw_json = models.JSONField(null=True, blank=True)  # Store raw Yodlee response
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_transactions'
        unique_together = [
            ('bank_account', 'yodlee_transaction_id'),
            # Additional unique constraint for deduplication
            ('bank_account', 'posted_date', 'amount', 'merchant_name'),
        ]
        indexes = [
            models.Index(fields=['user', 'posted_date']),
            models.Index(fields=['bank_account', 'posted_date']),
            models.Index(fields=['user', '-posted_date']),  # Descending for recent first
        ]

    def __str__(self):
        return f"{self.user.username} - {self.description} ({self.amount} {self.currency})"


class BankWebhookEvent(models.Model):
    """Yodlee webhook events for audit/logging"""
    event_type = models.CharField(max_length=100)  # e.g., "REFRESH", "DATA_UPDATES"
    provider_account_id = models.CharField(max_length=255, db_index=True)
    payload = models.JSONField()  # Full webhook payload
    signature_valid = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bank_webhook_events'
        indexes = [
            models.Index(fields=['provider_account_id', '-created_at']),
            models.Index(fields=['processed', '-created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.provider_account_id} ({self.created_at})"

