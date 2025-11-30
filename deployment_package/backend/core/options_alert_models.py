"""
Options Alert Models - Store user alerts for options price, IV, and expiration
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class OptionsAlert(models.Model):
    """User alert for options price, IV, or expiration"""
    
    ALERT_TYPE_CHOICES = [
        ('PRICE', 'Price'),
        ('IV', 'Implied Volatility'),
        ('EXPIRATION', 'Expiration'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('TRIGGERED', 'Triggered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='options_alerts')
    symbol = models.CharField(max_length=10)
    strike = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiration = models.CharField(max_length=20, null=True, blank=True)
    option_type = models.CharField(max_length=4, null=True, blank=True)  # CALL or PUT
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    target_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)  # Price or IV target
    direction = models.CharField(max_length=10, null=True, blank=True)  # 'above' or 'below' for price/IV
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    triggered_at = models.DateTimeField(null=True, blank=True)
    notification_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'options_alerts'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['symbol', 'status']),
            models.Index(fields=['alert_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.symbol} {self.alert_type} alert"


class OptionsAlertNotification(models.Model):
    """Notification sent when an alert is triggered"""
    
    alert = models.ForeignKey(OptionsAlert, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20)  # 'push', 'email', 'in_app'
    sent_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    
    class Meta:
        db_table = 'options_alert_notifications'
        indexes = [
            models.Index(fields=['alert', 'sent_at']),
        ]

