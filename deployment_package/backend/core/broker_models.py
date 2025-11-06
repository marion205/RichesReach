"""
Broker API Models for Alpaca Integration
Models for tracking broker accounts, orders, positions, and activities
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class BrokerAccount(models.Model):
    """Alpaca Broker API account linked to a user"""
    
    KYC_STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVAL_PENDING', 'Approval Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('INFO_REQUIRED', 'Information Required'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='broker_account')
    alpaca_account_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='NOT_STARTED')
    approval_reason = models.TextField(blank=True, null=True)
    suitability_flags = models.JSONField(default=dict, blank=True)  # Risk flags, restrictions, etc.
    
    # Account details from Alpaca
    account_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)  # OPEN, CLOSED, etc.
    buying_power = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    equity = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    day_trading_buying_power = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    pattern_day_trader = models.BooleanField(default=False)
    
    # Restrictions
    day_trade_count = models.IntegerField(default=0)
    trading_blocked = models.BooleanField(default=False)
    transfer_blocked = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'broker_accounts'
        indexes = [
            models.Index(fields=['user', 'kyc_status']),
            models.Index(fields=['alpaca_account_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.kyc_status}"


class BrokerFunding(models.Model):
    """Bank linking and funding transfers"""
    
    TRANSFER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REVERSED', 'Reversed'),
    ]
    
    broker_account = models.ForeignKey(BrokerAccount, on_delete=models.CASCADE, related_name='funding_records')
    bank_link_id = models.CharField(max_length=100, blank=True, null=True)
    transfer_type = models.CharField(max_length=20, choices=[('DEPOSIT', 'Deposit'), ('WITHDRAWAL', 'Withdrawal')])
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=TRANSFER_STATUS_CHOICES, default='PENDING')
    alpaca_transfer_id = models.CharField(max_length=100, blank=True, null=True)
    
    # ACH details
    ach_relationship_id = models.CharField(max_length=100, blank=True, null=True)
    micro_deposit_verified = models.BooleanField(default=False)
    
    # Settlement info
    settlement_date = models.DateField(null=True, blank=True)
    estimated_settlement_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'broker_funding'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.broker_account.user.email} - {self.transfer_type} ${self.amount} - {self.status}"


class BrokerOrder(models.Model):
    """Broker orders (mirror of Alpaca orders with guardrail tracking)"""
    
    ORDER_STATUS_CHOICES = [
        ('NEW', 'New'),
        ('PENDING_NEW', 'Pending New'),
        ('ACCEPTED', 'Accepted'),
        ('PARTIALLY_FILLED', 'Partially Filled'),
        ('FILLED', 'Filled'),
        ('DONE_FOR_DAY', 'Done For Day'),
        ('CANCELED', 'Canceled'),
        ('EXPIRED', 'Expired'),
        ('REPLACED', 'Replaced'),
        ('PENDING_CANCEL', 'Pending Cancel'),
        ('PENDING_REPLACE', 'Pending Replace'),
        ('REJECTED', 'Rejected'),
        ('STOPPED', 'Stopped'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
        ('STOP', 'Stop'),
        ('STOP_LIMIT', 'Stop Limit'),
        ('TRAILING_STOP', 'Trailing Stop'),
    ]
    
    SIDE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    TIME_IN_FORCE_CHOICES = [
        ('DAY', 'Day'),
        ('GTC', 'Good Till Canceled'),
        ('OPG', 'Opening'),
        ('CLS', 'Closing'),
        ('IOC', 'Immediate or Cancel'),
        ('FOK', 'Fill or Kill'),
    ]
    
    broker_account = models.ForeignKey(BrokerAccount, on_delete=models.CASCADE, related_name='orders')
    client_order_id = models.CharField(max_length=100, unique=True)  # Our UUID
    alpaca_order_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # Order details
    symbol = models.CharField(max_length=10)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    time_in_force = models.CharField(max_length=3, choices=TIME_IN_FORCE_CHOICES, default='DAY')
    quantity = models.IntegerField()
    notional = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # Calculated
    limit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stop_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='NEW')
    filled_qty = models.IntegerField(default=0)
    filled_avg_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Guardrail tracking
    guardrail_checks_passed = models.BooleanField(default=False)
    guardrail_reject_reason = models.TextField(blank=True, null=True)
    
    # Fill tracking
    fills = models.JSONField(default=list, blank=True)  # Array of fill objects
    
    # Alpaca response
    alpaca_response = models.JSONField(default=dict, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    filled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'broker_orders'
        indexes = [
            models.Index(fields=['broker_account', 'status']),
            models.Index(fields=['client_order_id']),
            models.Index(fields=['alpaca_order_id']),
            models.Index(fields=['symbol', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client_order_id} - {self.symbol} {self.side} {self.quantity} @ {self.status}"


class BrokerPosition(models.Model):
    """Broker positions (lightweight mirror, fetch from Alpaca when needed)"""
    
    broker_account = models.ForeignKey(BrokerAccount, on_delete=models.CASCADE, related_name='positions')
    symbol = models.CharField(max_length=10)
    
    # Position details (cached from Alpaca)
    qty = models.IntegerField(default=0)
    avg_entry_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    market_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cost_basis = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unrealized_pl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unrealized_plpc = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Last sync timestamp
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'broker_positions'
        unique_together = [['broker_account', 'symbol']]
        indexes = [
            models.Index(fields=['broker_account']),
            models.Index(fields=['symbol']),
        ]
    
    def __str__(self):
        return f"{self.broker_account.user.email} - {self.symbol} x{self.qty}"


class BrokerActivity(models.Model):
    """Account activity log (lightweight mirror, fetch from Alpaca when needed)"""
    
    ACTIVITY_TYPE_CHOICES = [
        ('FILL', 'Fill'),
        ('TRANS', 'Transfer'),
        ('DIV', 'Dividend'),
        ('FEE', 'Fee'),
        ('INT', 'Interest'),
        ('CSD', 'Cash Settlement'),
        ('CSW', 'Cash Withdrawal'),
        ('CSR', 'Cash Receipt'),
        ('JRN', 'Journal'),
        ('JNLC', 'Journal (Cash)'),
        ('JNLS', 'Journal (Stock)'),
    ]
    
    broker_account = models.ForeignKey(BrokerAccount, on_delete=models.CASCADE, related_name='activities')
    activity_id = models.CharField(max_length=100, unique=True)  # Alpaca activity ID
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPE_CHOICES)
    date = models.DateField()
    net_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    symbol = models.CharField(max_length=10, blank=True, null=True)
    qty = models.IntegerField(null=True, blank=True)
    per_share_amount = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Raw Alpaca activity data (cached)
    raw_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'broker_activities'
        indexes = [
            models.Index(fields=['broker_account', 'date']),
            models.Index(fields=['activity_id']),
        ]
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.broker_account.user.email} - {self.activity_type} - {self.date}"


class BrokerStatement(models.Model):
    """Statements and tax documents (metadata only, fetch from Alpaca when needed)"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('STATEMENT', 'Account Statement'),
        ('TAX_1099', '1099 Tax Document'),
        ('CONFIRM', 'Trade Confirmation'),
    ]
    
    broker_account = models.ForeignKey(BrokerAccount, on_delete=models.CASCADE, related_name='statements')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    year = models.IntegerField(null=True, blank=True)  # For tax docs
    
    # Alpaca document reference
    alpaca_document_id = models.CharField(max_length=100, blank=True, null=True)
    document_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Metadata
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'broker_statements'
        indexes = [
            models.Index(fields=['broker_account', 'document_type', 'year']),
        ]
        ordering = ['-period_end', '-year']
    
    def __str__(self):
        return f"{self.broker_account.user.email} - {self.document_type} - {self.period_end}"


class BrokerGuardrailLog(models.Model):
    """Audit log for guardrail decisions"""
    
    broker_account = models.ForeignKey(BrokerAccount, on_delete=models.CASCADE, related_name='guardrail_logs')
    action = models.CharField(max_length=50)  # 'PLACE_ORDER', 'SYMBOL_CHECK', etc.
    symbol = models.CharField(max_length=10, blank=True, null=True)
    notional = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Decision
    allowed = models.BooleanField(default=False)
    reason = models.TextField()
    
    # Context
    checks_performed = models.JSONField(default=dict, blank=True)  # {check_name: result}
    user_context = models.JSONField(default=dict, blank=True)  # Account status, restrictions, etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'broker_guardrail_logs'
        indexes = [
            models.Index(fields=['broker_account', 'created_at']),
            models.Index(fields=['action', 'allowed']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.broker_account.user.email} - {self.action} - {'ALLOWED' if self.allowed else 'BLOCKED'}"

