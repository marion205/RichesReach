"""
Alpaca-specific models for account management and trading
"""
from django.db import models
from django.utils import timezone
import uuid

class AlpacaAccount(models.Model):
    """Model to track Alpaca brokerage accounts"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='alpaca_account')
    alpaca_account_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Account details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    account_type = models.CharField(max_length=50, default='individual')  # individual, joint, trust, etc.
    
    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField()
    ssn = models.CharField(max_length=11, blank=True)  # Encrypted in production
    
    # Address information
    street_address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50, default='US')
    
    # Financial information
    employment_status = models.CharField(max_length=50, blank=True)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    net_worth = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Trading preferences
    risk_tolerance = models.CharField(max_length=20, default='medium')  # conservative, moderate, aggressive
    investment_experience = models.CharField(max_length=50, default='beginner')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    alpaca_created_at = models.DateTimeField(null=True, blank=True)
    alpaca_updated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'alpaca_accounts'
        verbose_name = 'Alpaca Account'
        verbose_name_plural = 'Alpaca Accounts'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.status})"
    
    @property
    def is_approved(self):
        return self.status == 'APPROVED'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class AlpacaKycDocument(models.Model):
    """Model to track KYC documents for Alpaca accounts"""
    
    DOCUMENT_TYPES = [
        ('identity', 'Identity Document'),
        ('address', 'Address Verification'),
        ('income', 'Income Verification'),
        ('tax', 'Tax Document'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alpaca_account = models.ForeignKey(AlpacaAccount, on_delete=models.CASCADE, related_name='kyc_documents')
    
    # Document details
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=200)
    alpaca_document_id = models.CharField(max_length=100, null=True, blank=True)
    
    # File information
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=100)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'alpaca_kyc_documents'
        verbose_name = 'Alpaca KYC Document'
        verbose_name_plural = 'Alpaca KYC Documents'
    
    def __str__(self):
        return f"{self.alpaca_account.full_name} - {self.document_type}"

class AlpacaOrder(models.Model):
    """Model to track Alpaca trading orders"""
    
    ORDER_TYPES = [
        ('market', 'Market'),
        ('limit', 'Limit'),
        ('stop', 'Stop'),
        ('stop_limit', 'Stop Limit'),
    ]
    
    ORDER_SIDES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    
    TIME_IN_FORCE = [
        ('day', 'Day'),
        ('gtc', 'Good Till Canceled'),
        ('ioc', 'Immediate or Cancel'),
        ('fok', 'Fill or Kill'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('partially_filled', 'Partially Filled'),
        ('filled', 'Filled'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alpaca_account = models.ForeignKey(AlpacaAccount, on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    alpaca_order_id = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=20)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    side = models.CharField(max_length=10, choices=ORDER_SIDES)
    quantity = models.DecimalField(max_digits=15, decimal_places=8)
    price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    stop_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    time_in_force = models.CharField(max_length=10, choices=TIME_IN_FORCE, default='day')
    
    # Status and execution
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    filled_quantity = models.DecimalField(max_digits=15, decimal_places=8, default=0)
    average_fill_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    filled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'alpaca_orders'
        verbose_name = 'Alpaca Order'
        verbose_name_plural = 'Alpaca Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.side.upper()} {self.quantity} {self.symbol} @ {self.price or 'Market'}"

class AlpacaPosition(models.Model):
    """Model to track Alpaca positions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alpaca_account = models.ForeignKey(AlpacaAccount, on_delete=models.CASCADE, related_name='positions')
    
    # Position details
    symbol = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=15, decimal_places=8)
    market_value = models.DecimalField(max_digits=15, decimal_places=2)
    cost_basis = models.DecimalField(max_digits=15, decimal_places=2)
    unrealized_pl = models.DecimalField(max_digits=15, decimal_places=2)
    unrealized_plpc = models.DecimalField(max_digits=10, decimal_places=4)  # percentage
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alpaca_positions'
        verbose_name = 'Alpaca Position'
        verbose_name_plural = 'Alpaca Positions'
        unique_together = ['alpaca_account', 'symbol']
    
    def __str__(self):
        return f"{self.symbol}: {self.quantity} shares"

class AlpacaActivity(models.Model):
    """Model to track Alpaca account activities"""
    
    ACTIVITY_TYPES = [
        ('fill', 'Fill'),
        ('partial_fill', 'Partial Fill'),
        ('cancel', 'Cancel'),
        ('expire', 'Expire'),
        ('reject', 'Reject'),
        ('dividend', 'Dividend'),
        ('interest', 'Interest'),
        ('fee', 'Fee'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alpaca_account = models.ForeignKey(AlpacaAccount, on_delete=models.CASCADE, related_name='activities')
    
    # Activity details
    alpaca_activity_id = models.CharField(max_length=100, unique=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    symbol = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=8, null=True, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    
    # Timestamps
    activity_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'alpaca_activities'
        verbose_name = 'Alpaca Activity'
        verbose_name_plural = 'Alpaca Activities'
        ordering = ['-activity_date']
    
    def __str__(self):
        return f"{self.activity_type}: {self.symbol or 'N/A'} - {self.activity_date}"
