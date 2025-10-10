"""
Premium Subscription Models
Models for managing premium features and subscriptions
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import uuid

class PremiumSubscription(models.Model):
    """Premium subscription model"""
    
    SUBSCRIPTION_TIERS = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('trial', 'Trial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='premium_subscription')
    tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIERS, default='basic')
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='trial')
    
    # Subscription dates
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Billing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    billing_cycle = models.CharField(max_length=20, default='monthly')  # monthly, annual
    
    # Features
    features = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'premium_subscriptions'
    
    def __str__(self):
        return f"{self.user.email} - {self.tier} ({self.status})"
    
    @property
    def is_active(self):
        """Check if subscription is active"""
        if self.status == 'active':
            return self.end_date is None or self.end_date > timezone.now()
        elif self.status == 'trial':
            return self.trial_end_date is None or self.trial_end_date > timezone.now()
        return False
    
    @property
    def is_trial(self):
        """Check if user is on trial"""
        return self.status == 'trial' and self.is_active
    
    @property
    def days_remaining(self):
        """Get days remaining in subscription"""
        if self.status == 'trial' and self.trial_end_date:
            delta = self.trial_end_date - timezone.now()
            return max(0, delta.days)
        elif self.status == 'active' and self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return None
    
    def get_available_features(self):
        """Get list of available features for this tier"""
        feature_map = {
            'basic': [
                'basic_portfolio_tracking',
                'basic_market_data',
                'basic_ai_recommendations',
            ],
            'premium': [
                'basic_portfolio_tracking',
                'basic_market_data',
                'basic_ai_recommendations',
                'advanced_ai_recommendations',
                'tax_loss_harvesting',
                'capital_gains_optimization',
                'tax_efficient_rebalancing',
                'tax_bracket_analysis',
                'priority_support',
            ],
            'pro': [
                'basic_portfolio_tracking',
                'basic_market_data',
                'basic_ai_recommendations',
                'advanced_ai_recommendations',
                'tax_loss_harvesting',
                'capital_gains_optimization',
                'tax_efficient_rebalancing',
                'tax_bracket_analysis',
                'priority_support',
                'advanced_analytics',
                'custom_portfolio_models',
                'api_access',
            ],
            'enterprise': [
                'basic_portfolio_tracking',
                'basic_market_data',
                'basic_ai_recommendations',
                'advanced_ai_recommendations',
                'tax_loss_harvesting',
                'capital_gains_optimization',
                'tax_efficient_rebalancing',
                'tax_bracket_analysis',
                'priority_support',
                'advanced_analytics',
                'custom_portfolio_models',
                'api_access',
                'white_label',
                'dedicated_support',
                'custom_integrations',
            ]
        }
        return feature_map.get(self.tier, [])
    
    def has_feature(self, feature_name):
        """Check if user has access to a specific feature"""
        return feature_name in self.get_available_features()
    
    def upgrade_to_premium(self):
        """Upgrade user to premium tier"""
        self.tier = 'premium'
        self.status = 'active'
        self.monthly_price = 29.99
        self.annual_price = 299.99
        self.end_date = timezone.now() + timedelta(days=30)
        self.save()
    
    def start_trial(self, days=14):
        """Start a trial subscription"""
        self.status = 'trial'
        self.trial_end_date = timezone.now() + timedelta(days=days)
        self.save()

class FeatureUsage(models.Model):
    """Track feature usage for analytics and billing"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feature_usage')
    feature_name = models.CharField(max_length=100)
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_usage'
        unique_together = ['user', 'feature_name']
    
    def __str__(self):
        return f"{self.user.email} - {self.feature_name} ({self.usage_count})"
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.save()

class PremiumFeature(models.Model):
    """Define premium features and their requirements"""
    
    FEATURE_TYPES = [
        ('tax_optimization', 'Tax Optimization'),
        ('advanced_analytics', 'Advanced Analytics'),
        ('ai_features', 'AI Features'),
        ('api_access', 'API Access'),
        ('support', 'Support'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField()
    feature_type = models.CharField(max_length=50, choices=FEATURE_TYPES)
    required_tier = models.CharField(max_length=20, choices=PremiumSubscription.SUBSCRIPTION_TIERS)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'premium_features'
    
    def __str__(self):
        return self.display_name

# Premium feature decorator
def require_premium_feature(feature_name):
    """Decorator to require premium feature access"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            try:
                subscription = request.user.premium_subscription
                if not subscription.has_feature(feature_name):
                    return JsonResponse({
                        'error': 'Premium feature required',
                        'feature': feature_name,
                        'required_tier': 'premium',
                        'upgrade_url': '/premium/upgrade'
                    }, status=403)
            except PremiumSubscription.DoesNotExist:
                return JsonResponse({
                    'error': 'Premium subscription required',
                    'feature': feature_name,
                    'required_tier': 'premium',
                    'upgrade_url': '/premium/upgrade'
                }, status=403)
            
            # Track feature usage
            FeatureUsage.objects.get_or_create(
                user=request.user,
                feature_name=feature_name
            )[0].increment_usage()
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
