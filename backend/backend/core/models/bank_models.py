"""
Bank-related models for Yodlee integration
"""
from django.db import models
from django.utils import timezone
import uuid

class BankLink(models.Model):
    """Model to track bank connections via Yodlee"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ERROR', 'Error'),
        ('EXPIRED', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='bank_links')
    yodlee_account_id = models.CharField(max_length=100, unique=True, help_text="Yodlee's unique account ID", default='')
    bank_name = models.CharField(max_length=255, default='')
    account_type = models.CharField(max_length=50, default='')  # checking, savings, credit, etc.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.bank_name} - {self.user.username} ({self.status})"

class BankAccount(models.Model):
    """Model to track individual bank accounts"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('CHECKING', 'Checking'),
        ('SAVINGS', 'Savings'),
        ('CREDIT', 'Credit Card'),
        ('LOAN', 'Loan'),
        ('INVESTMENT', 'Investment'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_link = models.ForeignKey(BankLink, on_delete=models.CASCADE, related_name='accounts')
    yodlee_account_id = models.CharField(max_length=100, unique=True, help_text="Yodlee's unique account ID", default='')
    account_name = models.CharField(max_length=255, default='')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='CHECKING')
    account_number_masked = models.CharField(max_length=50, help_text="Masked account number", default='')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.account_name} - {self.bank_link.bank_name}"
