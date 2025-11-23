"""
Paper Trading Models - Simulated trading without real money
"""
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class PaperTradingAccount(models.Model):
    """Paper trading account for simulated trading"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='paper_account')
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('100000.00'))
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('100000.00'))
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('100000.00'))
    realized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    unrealized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_pnl_percent = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.00'))
    
    # Statistics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'paper_trading_accounts'
        verbose_name = 'Paper Trading Account'
        verbose_name_plural = 'Paper Trading Accounts'
    
    def __str__(self):
        return f"{self.user.email} - Paper Account (${self.current_balance:,.2f})"
    
    def update_statistics(self):
        """Update win rate and P&L statistics"""
        if self.total_trades > 0:
            self.win_rate = (Decimal(self.winning_trades) / Decimal(self.total_trades)) * Decimal('100.00')
        
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
        if self.initial_balance > 0:
            self.total_pnl_percent = (self.total_pnl / self.initial_balance) * Decimal('100.00')
        
        self.save()


class PaperTradingPosition(models.Model):
    """Paper trading positions (simulated holdings)"""
    account = models.ForeignKey(PaperTradingAccount, on_delete=models.CASCADE, related_name='positions')
    stock = models.ForeignKey('core.Stock', on_delete=models.CASCADE, related_name='paper_positions')
    shares = models.IntegerField(default=0)
    average_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cost_basis = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    market_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    unrealized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    unrealized_pnl_percent = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'paper_trading_positions'
        unique_together = [['account', 'stock']]
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['stock']),
        ]
        verbose_name = 'Paper Trading Position'
        verbose_name_plural = 'Paper Trading Positions'
    
    def __str__(self):
        return f"{self.account.user.email} - {self.stock.symbol} ({self.shares} shares)"
    
    def update_pnl(self, current_price: Decimal):
        """Update P&L based on current price"""
        self.current_price = current_price
        self.market_value = current_price * Decimal(self.shares)
        self.unrealized_pnl = self.market_value - self.cost_basis
        if self.cost_basis > 0:
            self.unrealized_pnl_percent = (self.unrealized_pnl / self.cost_basis) * Decimal('100.00')
        self.save()


class PaperTradingOrder(models.Model):
    """Paper trading orders (simulated trades)"""
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('FILLED', 'Filled'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
        ('STOP', 'Stop'),
        ('STOP_LIMIT', 'Stop Limit'),
    ]
    
    SIDE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    account = models.ForeignKey(PaperTradingAccount, on_delete=models.CASCADE, related_name='orders')
    stock = models.ForeignKey('core.Stock', on_delete=models.CASCADE, related_name='paper_orders')
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='MARKET')
    quantity = models.IntegerField(default=0)
    limit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stop_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Execution details
    filled_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    filled_quantity = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    filled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'paper_trading_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'status']),
            models.Index(fields=['stock', 'status']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Paper Trading Order'
        verbose_name_plural = 'Paper Trading Orders'
    
    def __str__(self):
        return f"{self.account.user.email} - {self.side} {self.quantity} {self.stock.symbol} @ {self.status}"


class PaperTradingTrade(models.Model):
    """Paper trading trade history (completed trades for P&L calculation)"""
    account = models.ForeignKey(PaperTradingAccount, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey('core.Stock', on_delete=models.CASCADE, related_name='paper_trades')
    side = models.CharField(max_length=4)  # BUY or SELL
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # P&L (for closed positions)
    realized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    realized_pnl_percent = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.00'))
    
    # Link to orders
    buy_order = models.ForeignKey(PaperTradingOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='buy_trades')
    sell_order = models.ForeignKey(PaperTradingOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='sell_trades')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'paper_trading_trades'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'created_at']),
            models.Index(fields=['stock', 'created_at']),
        ]
        verbose_name = 'Paper Trading Trade'
        verbose_name_plural = 'Paper Trading Trades'
    
    def __str__(self):
        return f"{self.account.user.email} - {self.side} {self.quantity} {self.stock.symbol} @ ${self.price}"

