"""
DeFi Database Models for RichesReach
Stores protocol data, pool information, yield snapshots, user positions, and transactions.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class DeFiProtocol(models.Model):
    """
    Represents a DeFi protocol (e.g., Aave V3, Compound V3, Curve).
    Populated from DefiLlama data and manual curation.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    logo_url = models.URLField(max_length=500, blank=True, default='')
    website = models.URLField(max_length=500, blank=True, default='')
    description = models.TextField(blank=True, default='')
    audit_firms = models.JSONField(default=list, help_text='List of audit firm names')
    risk_score = models.FloatField(
        default=0.5,
        help_text='Protocol risk score 0.0 (lowest risk) to 1.0 (highest risk)'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'defi_protocol'
        ordering = ['name']

    def __str__(self):
        return self.name


class DeFiPool(models.Model):
    """
    Represents a specific pool/vault on a DeFi protocol.
    Each pool has a chain, token pair, and address.
    """
    POOL_TYPES = [
        ('lending', 'Lending'),
        ('lp', 'Liquidity Pool'),
        ('staking', 'Staking'),
        ('vault', 'Vault'),
        ('yield', 'Yield Farming'),
    ]

    CHAINS = [
        ('ethereum', 'Ethereum'),
        ('polygon', 'Polygon'),
        ('arbitrum', 'Arbitrum'),
        ('base', 'Base'),
        ('optimism', 'Optimism'),
        ('avalanche', 'Avalanche'),
    ]

    protocol = models.ForeignKey(
        DeFiProtocol,
        on_delete=models.CASCADE,
        related_name='pools'
    )
    chain = models.CharField(max_length=50, choices=CHAINS)
    chain_id = models.IntegerField(help_text='EVM chain ID (1=Ethereum, 137=Polygon, etc.)')
    symbol = models.CharField(max_length=100, help_text='Token symbol (e.g., USDC, ETH/USDC)')
    pool_address = models.CharField(max_length=66, blank=True, default='')
    pool_type = models.CharField(max_length=30, choices=POOL_TYPES, default='lending')
    defi_llama_pool_id = models.CharField(
        max_length=200,
        unique=True,
        null=True,
        blank=True,
        help_text='DefiLlama pool UUID for data syncing'
    )
    url = models.URLField(max_length=500, blank=True, default='', help_text='Pool page URL on protocol')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'defi_pool'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['chain', 'is_active']),
            models.Index(fields=['protocol', 'chain']),
        ]

    def __str__(self):
        return f"{self.protocol.name} - {self.symbol} ({self.chain})"


class YieldSnapshot(models.Model):
    """
    Point-in-time snapshot of a pool's yield metrics.
    Populated every 5 minutes from DefiLlama.
    """
    pool = models.ForeignKey(
        DeFiPool,
        on_delete=models.CASCADE,
        related_name='yield_snapshots'
    )
    apy_base = models.FloatField(help_text='Base APY from protocol fees/interest')
    apy_reward = models.FloatField(default=0, help_text='Additional APY from reward tokens')
    apy_total = models.FloatField(help_text='Total APY (base + reward)')
    tvl_usd = models.FloatField(help_text='Total value locked in USD')
    risk_score = models.FloatField(
        default=0.5,
        help_text='Pool risk score 0.0-1.0'
    )
    il_estimate = models.FloatField(
        null=True,
        blank=True,
        help_text='Estimated impermanent loss percentage (for LP pools)'
    )
    volume_24h_usd = models.FloatField(
        null=True,
        blank=True,
        help_text='24-hour trading volume in USD'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'defi_yield_snapshot'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['pool', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        # Keep data manageable: partition by time in production
        get_latest_by = 'timestamp'

    def __str__(self):
        return f"{self.pool} - {self.apy_total:.2f}% APY @ {self.timestamp}"


class UserDeFiPosition(models.Model):
    """
    Tracks a user's active DeFi position (stake, lend, LP).
    Created when a user deposits, updated on harvest/withdraw.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='defi_positions'
    )
    pool = models.ForeignKey(
        DeFiPool,
        on_delete=models.CASCADE,
        related_name='user_positions'
    )
    wallet_address = models.CharField(max_length=66)
    staked_amount = models.DecimalField(
        max_digits=30,
        decimal_places=18,
        help_text='Amount of tokens staked/deposited'
    )
    staked_value_usd = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text='USD value at time of stake'
    )
    rewards_earned = models.DecimalField(
        max_digits=30,
        decimal_places=18,
        default=0,
        help_text='Accumulated rewards'
    )
    realized_apy = models.FloatField(
        null=True,
        blank=True,
        help_text='Actual realized APY for this position'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'defi_user_position'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['wallet_address']),
        ]

    def __str__(self):
        status = 'Active' if self.is_active else 'Closed'
        return f"{self.user} - {self.pool.symbol} ({status})"

    @property
    def total_value_usd(self):
        """Calculate current total value including rewards."""
        # In production, this would use current token prices
        return float(self.staked_value_usd) + float(self.rewards_earned)


class DeFiTransaction(models.Model):
    """
    Records every DeFi transaction for audit trail and analytics.
    """
    ACTION_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('harvest', 'Harvest Rewards'),
        ('approve', 'Token Approval'),
        ('borrow', 'Borrow'),
        ('repay', 'Repay'),
        ('swap', 'Token Swap'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='defi_transactions'
    )
    position = models.ForeignKey(
        UserDeFiPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    pool = models.ForeignKey(
        DeFiPool,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    tx_hash = models.CharField(max_length=66, unique=True)
    chain_id = models.IntegerField()
    amount = models.DecimalField(max_digits=30, decimal_places=18)
    amount_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    gas_used = models.BigIntegerField(null=True, blank=True)
    gas_price_gwei = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'defi_transaction'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['tx_hash']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.action} - {self.amount} on {self.pool.symbol} ({self.status})"


class DeFiAlert(models.Model):
    """
    Persistent DeFi alert record.
    Created by defi_alert_service and autopilot_notification_service.
    Displayed in the mobile notification center and used for deduplication.
    """
    ALERT_TYPE_CHOICES = [
        ('health_warning', 'Health Factor Warning'),
        ('health_critical', 'Health Factor Critical'),
        ('health_danger', 'Liquidation Risk'),
        ('apy_change', 'APY Changed'),
        ('harvest_ready', 'Rewards Ready'),
        ('repair_available', 'Repair Available'),
        ('repair_executed', 'Repair Executed'),
        ('revert_expiring', 'Revert Window Expiring'),
        ('policy_breach', 'Policy Breach'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='defi_alerts',
    )
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='low')
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    position = models.ForeignKey(
        'UserDeFiPosition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
    )
    pool = models.ForeignKey(
        'DeFiPool',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
    )
    repair_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'defi_alert'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'alert_type', '-created_at']),
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.alert_type} for user {self.user_id}: {self.title}"


class DeFiNotificationPreferences(models.Model):
    """
    User preferences for DeFi and Auto-Pilot push notifications.
    Replaces the deleted NotificationPreferences model (migration 0037)
    with DeFi-specific fields.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='defi_notification_preferences',
    )
    push_token = models.TextField(
        blank=True,
        null=True,
        help_text='Expo push notification token',
    )
    push_enabled = models.BooleanField(default=True, db_index=True)

    # DeFi alert categories
    health_alerts_enabled = models.BooleanField(default=True)
    apy_alerts_enabled = models.BooleanField(default=True)
    harvest_alerts_enabled = models.BooleanField(default=True)

    # Autopilot-specific
    autopilot_alerts_enabled = models.BooleanField(default=True)
    repair_alerts_enabled = models.BooleanField(default=True)
    revert_reminder_enabled = models.BooleanField(default=True)

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'defi_notification_preferences'
        verbose_name = 'DeFi Notification Preferences'
        verbose_name_plural = 'DeFi Notification Preferences'

    def __str__(self):
        status = 'on' if self.push_enabled else 'off'
        return f"DeFi Prefs for {self.user_id} (push={status})"
