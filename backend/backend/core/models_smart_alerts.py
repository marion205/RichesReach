from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

class AlertThreshold(models.Model):
    """User-customizable thresholds for smart alerts"""
    
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='alert_thresholds')
    alert_type = models.CharField(max_length=50, help_text="Type of alert (e.g., 'performance_underperformance')")
    
    # Threshold values
    performance_diff_threshold = models.FloatField(default=2.0, help_text="Alert if under/outperforming by this %")
    sharpe_min_threshold = models.FloatField(default=0.5, help_text="Minimum acceptable Sharpe ratio")
    volatility_max_threshold = models.FloatField(default=20.0, help_text="Maximum acceptable volatility %")
    drawdown_max_threshold = models.FloatField(default=-15.0, help_text="Maximum acceptable drawdown %")
    var95_max_threshold = models.FloatField(default=-3.0, help_text="Maximum acceptable 95% VaR %")
    tech_weight_max_threshold = models.FloatField(default=0.35, help_text="Maximum tech sector weight")
    cash_min_threshold = models.FloatField(default=0.02, help_text="Minimum cash position %")
    cash_max_threshold = models.FloatField(default=0.20, help_text="Maximum cash position %")
    concentration_max_threshold = models.FloatField(default=0.15, help_text="Maximum single stock concentration %")
    sector_concentration_max_threshold = models.FloatField(default=0.40, help_text="Maximum sector concentration %")
    trading_frequency_max_threshold = models.IntegerField(default=10, help_text="Maximum trades per 30 days")
    expense_ratio_max_threshold = models.FloatField(default=0.90, help_text="Maximum expense ratio %")
    
    # Cooldown periods (in hours)
    cooldown_period = models.IntegerField(default=168, help_text="Hours before same alert can trigger again")
    
    # Enable/disable specific alert types
    enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'alert_type']
        indexes = [
            models.Index(fields=['user', 'alert_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.alert_type}"

class AlertDeliveryPreference(models.Model):
    """User preferences for alert delivery methods"""
    
    DELIVERY_METHODS = [
        ('in_app', 'In-App Only'),
        ('push', 'Push Notifications'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('all', 'All Methods'),
    ]
    
    PRIORITY_LEVELS = [
        ('critical', 'Critical'),
        ('important', 'Important'),
        ('informational', 'Informational'),
    ]
    
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='alert_delivery_preferences')
    alert_category = models.CharField(max_length=50, help_text="Alert category (e.g., 'performance', 'risk')")
    priority_level = models.CharField(max_length=20, choices=PRIORITY_LEVELS)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='in_app')
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=True)
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='08:00')
    
    # Frequency settings
    max_alerts_per_day = models.IntegerField(default=10, help_text="Maximum alerts per day for this category")
    digest_frequency = models.CharField(max_length=20, default='daily', 
                                      choices=[('immediate', 'Immediate'), ('daily', 'Daily'), ('weekly', 'Weekly')])
    
    enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'alert_category', 'priority_level']
        indexes = [
            models.Index(fields=['user', 'alert_category']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.alert_category} ({self.priority_level})"

class SmartAlert(models.Model):
    """Generated smart alerts with full context and delivery tracking"""
    
    URGENCY_LEVELS = [
        ('critical', 'Critical - Do Now'),
        ('important', 'Important - Review Soon'),
        ('informational', 'Informational - FYI/Coaching'),
    ]
    
    PRIORITY_LEVELS = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='smart_alerts')
    alert_id = models.CharField(max_length=100, unique=True, help_text="Unique alert identifier")
    
    # Alert content
    alert_type = models.CharField(max_length=50, help_text="Type of alert")
    urgency_level = models.CharField(max_length=20, choices=URGENCY_LEVELS, default='informational')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    category = models.CharField(max_length=50, help_text="Alert category")
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    coaching_tip = models.TextField()
    trigger_reason = models.TextField(help_text="Why this alert was triggered now")
    
    # Alert data
    details = models.JSONField(default=dict, help_text="Structured alert data")
    suggested_actions = models.JSONField(default=list, help_text="List of suggested actions")
    actionable = models.BooleanField(default=True)
    
    # Context
    portfolio_id = models.CharField(max_length=50, null=True, blank=True)
    timeframe = models.CharField(max_length=10, default='1M')
    data_source = models.CharField(max_length=50, default='yodlee', help_text="Source of data (yodlee, calculated, etc.)")
    
    # Delivery tracking
    delivered_in_app = models.BooleanField(default=False)
    delivered_push = models.BooleanField(default=False)
    delivered_email = models.BooleanField(default=False)
    delivered_sms = models.BooleanField(default=False)
    
    # User interaction
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    # Timing
    triggered_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this alert expires")
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'triggered_at']),
            models.Index(fields=['user', 'urgency_level', 'acknowledged']),
            models.Index(fields=['alert_type', 'triggered_at']),
        ]
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.urgency_level})"
    
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def mark_acknowledged(self):
        self.acknowledged = True
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['acknowledged', 'acknowledged_at'])
    
    def mark_dismissed(self):
        self.dismissed = True
        self.dismissed_at = timezone.now()
        self.save(update_fields=['dismissed', 'dismissed_at'])

class AlertDeliveryHistory(models.Model):
    """Track delivery attempts and results for each alert"""
    
    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    alert = models.ForeignKey(SmartAlert, on_delete=models.CASCADE, related_name='delivery_history')
    delivery_method = models.CharField(max_length=20, choices=AlertDeliveryPreference.DELIVERY_METHODS)
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    
    # Delivery details
    delivery_attempted_at = models.DateTimeField(auto_now_add=True)
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # External service tracking
    external_id = models.CharField(max_length=100, null=True, blank=True, 
                                 help_text="ID from external service (push notification, email, etc.)")
    
    class Meta:
        indexes = [
            models.Index(fields=['alert', 'delivery_method']),
            models.Index(fields=['status', 'delivery_attempted_at']),
        ]
    
    def __str__(self):
        return f"{self.alert.title} - {self.delivery_method} ({self.status})"

class AlertSuppression(models.Model):
    """Track alert suppressions to prevent spam"""
    
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='alert_suppressions')
    alert_type = models.CharField(max_length=50)
    last_triggered_at = models.DateTimeField()
    suppression_until = models.DateTimeField(help_text="Suppress this alert type until this time")
    trigger_count = models.IntegerField(default=1, help_text="Number of times this alert has been triggered")
    
    # Context for suppression
    portfolio_id = models.CharField(max_length=50, null=True, blank=True)
    suppression_reason = models.CharField(max_length=100, default='cooldown_period')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'alert_type', 'portfolio_id']
        indexes = [
            models.Index(fields=['user', 'alert_type']),
            models.Index(fields=['suppression_until']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.alert_type} (suppressed until {self.suppression_until})"
    
    def is_suppressed(self):
        return timezone.now() < self.suppression_until

class MLAnomalyDetection(models.Model):
    """ML-driven anomaly detection results"""
    
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='ml_anomalies')
    anomaly_type = models.CharField(max_length=50, help_text="Type of anomaly detected")
    
    # Anomaly details
    anomaly_score = models.FloatField(help_text="Anomaly score (0-1, higher = more anomalous)")
    confidence = models.FloatField(help_text="ML model confidence (0-1)")
    description = models.TextField(help_text="Description of the anomaly")
    
    # Context
    detected_at = models.DateTimeField(auto_now_add=True)
    time_window = models.CharField(max_length=20, default='30d', help_text="Time window analyzed")
    baseline_period = models.CharField(max_length=20, default='90d', help_text="Baseline period for comparison")
    
    # Data used for detection
    input_data = models.JSONField(default=dict, help_text="Data used for anomaly detection")
    model_version = models.CharField(max_length=20, default='v1.0')
    
    # Alert generation
    alert_generated = models.BooleanField(default=False)
    alert = models.ForeignKey(SmartAlert, on_delete=models.SET_NULL, null=True, blank=True, 
                            related_name='ml_anomaly')
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'detected_at']),
            models.Index(fields=['anomaly_type', 'anomaly_score']),
        ]
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.anomaly_type} (score: {self.anomaly_score:.3f})"
