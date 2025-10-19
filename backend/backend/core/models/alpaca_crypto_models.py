"""
Alpaca Crypto-specific models for cryptocurrency trading and management
"""
from django.db import models
from django.utils import timezone
import uuid

class AlpacaCryptoAccount(models.Model):
    """Model to track Alpaca crypto accounts"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='alpaca_crypto_account')
    alpaca_crypto_account_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Account details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    account_type = models.CharField(max_length=50, default='crypto')
    
    # Crypto-specific settings
    trading_enabled = models.BooleanField(default=True)
    transfers_enabled = models.BooleanField(default=False)  # On-chain transfers
    max_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=200000.00)
    
    # State eligibility
    user_state = models.CharField(max_length=2, blank=True)  # US state code
    is_eligible = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    alpaca_created_at = models.DateTimeField(null=True, blank=True)
    alpaca_updated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'alpaca_crypto_accounts'
        verbose_name = 'Alpaca Crypto Account'
        verbose_name_plural = 'Alpaca Crypto Accounts'
    
    def __str__(self):
        return f"{self.user.username} - Crypto Account ({self.status})"
    
    @property
    def is_approved(self):
        return self.status == 'APPROVED'
    
    def save(self, *args, **kwargs):
        # Auto-set eligibility based on state
        if self.user_state:
            from ..services.alpaca_crypto_service import AlpacaCryptoService
            service = AlpacaCryptoService()
            self.is_eligible = service.is_crypto_eligible(self.user_state)
        super().save(*args, **kwargs)

class AlpacaCryptoOrder(models.Model):
    """Model to track Alpaca crypto trading orders"""
    
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
    alpaca_crypto_account = models.ForeignKey(AlpacaCryptoAccount, on_delete=models.CASCADE, related_name='crypto_orders')
    
    # Order details
    alpaca_order_id = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=20)  # e.g., BTC/USD, ETH/USDT
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    side = models.CharField(max_length=10, choices=ORDER_SIDES)
    
    # Quantity and pricing
    quantity = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)  # For qty-based orders
    notional = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)  # For notional orders
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)  # Limit price
    stop_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)  # Stop price
    time_in_force = models.CharField(max_length=10, choices=TIME_IN_FORCE, default='day')
    
    # Status and execution
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    filled_quantity = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    filled_notional = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    average_fill_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Fees
    commission = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    commission_asset = models.CharField(max_length=10, default='USD')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    filled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'alpaca_crypto_orders'
        verbose_name = 'Alpaca Crypto Order'
        verbose_name_plural = 'Alpaca Crypto Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        qty_or_notional = f"{self.quantity}" if self.quantity else f"${self.notional}"
        return f"{self.side.upper()} {qty_or_notional} {self.symbol} @ {self.price or 'Market'}"

class AlpacaCryptoBalance(models.Model):
    """Model to track Alpaca crypto balances"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alpaca_crypto_account = models.ForeignKey(AlpacaCryptoAccount, on_delete=models.CASCADE, related_name='crypto_balances')
    
    # Balance details
    asset = models.CharField(max_length=20)  # e.g., BTC, ETH, USD
    quantity = models.DecimalField(max_digits=30, decimal_places=18)  # High precision for crypto
    available_quantity = models.DecimalField(max_digits=30, decimal_places=18)  # Available for trading
    locked_quantity = models.DecimalField(max_digits=30, decimal_places=18, default=0)  # Locked in orders
    
    # Market value (in USD)
    market_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    cost_basis = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    unrealized_pl = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alpaca_crypto_balances'
        verbose_name = 'Alpaca Crypto Balance'
        verbose_name_plural = 'Alpaca Crypto Balances'
        unique_together = ['alpaca_crypto_account', 'asset']
    
    def __str__(self):
        return f"{self.asset}: {self.quantity} (Available: {self.available_quantity})"

class AlpacaCryptoActivity(models.Model):
    """Model to track Alpaca crypto account activities"""
    
    ACTIVITY_TYPES = [
        ('fill', 'Fill'),
        ('partial_fill', 'Partial Fill'),
        ('cancel', 'Cancel'),
        ('expire', 'Expire'),
        ('reject', 'Reject'),
        ('cfee', 'Commission Fee'),
        ('cint', 'Interest'),
        ('cdiv', 'Dividend'),
        ('cwd', 'Withdrawal'),
        ('csp', 'Deposit'),
        ('ctra', 'Transfer'),
        ('csto', 'Stock Split'),
        ('cact', 'Stock Action'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alpaca_crypto_account = models.ForeignKey(AlpacaCryptoAccount, on_delete=models.CASCADE, related_name='crypto_activities')
    
    # Activity details
    alpaca_activity_id = models.CharField(max_length=100, unique=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    symbol = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    
    # Additional crypto-specific fields
    asset = models.CharField(max_length=20, blank=True)  # Asset involved
    transaction_id = models.CharField(max_length=100, blank=True)  # Blockchain transaction ID
    
    # Timestamps
    activity_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'alpaca_crypto_activities'
        verbose_name = 'Alpaca Crypto Activity'
        verbose_name_plural = 'Alpaca Crypto Activities'
        ordering = ['-activity_date']
    
    def __str__(self):
        return f"{self.activity_type}: {self.symbol or self.asset} - {self.activity_date}"

class AlpacaCryptoTransfer(models.Model):
    """Model to track on-chain crypto transfers"""
    
    TRANSFER_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alpaca_crypto_account = models.ForeignKey(AlpacaCryptoAccount, on_delete=models.CASCADE, related_name='crypto_transfers')
    
    # Transfer details
    alpaca_transfer_id = models.CharField(max_length=100, unique=True)
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES)
    asset = models.CharField(max_length=20)  # e.g., BTC, ETH
    quantity = models.DecimalField(max_digits=30, decimal_places=18)
    
    # Addresses
    from_address = models.CharField(max_length=100, blank=True)
    to_address = models.CharField(max_length=100, blank=True)
    
    # Blockchain details
    transaction_id = models.CharField(max_length=100, blank=True)  # Blockchain TX ID
    block_height = models.BigIntegerField(null=True, blank=True)
    confirmations = models.IntegerField(default=0)
    required_confirmations = models.IntegerField(default=3)
    
    # Status and fees
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    network_fee = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    network_fee_asset = models.CharField(max_length=20, default='USD')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'alpaca_crypto_transfers'
        verbose_name = 'Alpaca Crypto Transfer'
        verbose_name_plural = 'Alpaca Crypto Transfers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transfer_type.title()} {self.quantity} {self.asset} - {self.status}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_confirmed(self):
        return self.confirmations >= self.required_confirmations
