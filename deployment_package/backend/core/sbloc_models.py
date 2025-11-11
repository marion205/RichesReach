"""
Django Models for SBLOC (Securities-Based Line of Credit) Operations
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class SBLOCBank(models.Model):
    """SBLOC Bank Provider"""
    
    # External ID from aggregator (if using aggregator service)
    external_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Bank information
    name = models.CharField(max_length=255)
    logo_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Loan terms
    min_apr = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, help_text="Minimum APR as decimal (0.065 = 6.5%)")
    max_apr = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, help_text="Maximum APR as decimal")
    min_ltv = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, help_text="Minimum LTV as decimal (0.5 = 50%)")
    max_ltv = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, help_text="Maximum LTV as decimal")
    
    # Additional information
    notes = models.TextField(null=True, blank=True)
    regions = models.JSONField(default=list, help_text="List of regions (e.g., ['US', 'EU', 'CA'])")
    min_loan_usd = models.IntegerField(null=True, blank=True, help_text="Minimum loan amount in USD")
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Display priority (higher = shown first)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sbloc_banks'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['is_active', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.name} (SBLOC)"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'name': self.name,
            'logoUrl': self.logo_url,
            'minApr': float(self.min_apr) if self.min_apr else None,
            'maxApr': float(self.max_apr) if self.max_apr else None,
            'minLtv': float(self.min_ltv) if self.min_ltv else None,
            'maxLtv': float(self.max_ltv) if self.max_ltv else None,
            'notes': self.notes,
            'regions': self.regions or [],
            'minLoanUsd': int(self.min_loan_usd) if self.min_loan_usd else None,
        }


class SBLOCSession(models.Model):
    """SBLOC Application Session"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sbloc_sessions')
    bank = models.ForeignKey(SBLOCBank, on_delete=models.CASCADE, related_name='sessions')
    
    # Session information
    amount_usd = models.IntegerField(help_text="Requested loan amount in USD")
    session_id = models.CharField(max_length=255, unique=True, help_text="External session ID")
    application_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Aggregator response (if using aggregator service)
    aggregator_response = models.JSONField(default=dict, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'sbloc_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        return f"SBLOC Session {self.session_id} - {self.user.email} - {self.bank.name}"
    
    def mark_completed(self):
        """Mark session as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_cancelled(self):
        """Mark session as cancelled"""
        self.status = 'CANCELLED'
        self.save()
    
    def mark_failed(self, error_message=None):
        """Mark session as failed"""
        self.status = 'FAILED'
        if error_message:
            if not self.aggregator_response:
                self.aggregator_response = {}
            self.aggregator_response['error'] = error_message
        self.save()

