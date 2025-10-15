"""
Temporary models that match the existing database schema
"""
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Temporary User model matching existing database schema"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    
    # Additional fields for institutional features
    hasPremiumAccess = models.BooleanField(default=False)
    subscriptionTier = models.CharField(max_length=20, default='BASIC', choices=[
        ('BASIC', 'Basic'),
        ('PREMIUM', 'Premium'),
        ('ENTERPRISE', 'Enterprise'),
    ])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']
    
    def __str__(self):
        return self.email
