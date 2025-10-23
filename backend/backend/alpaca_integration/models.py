"""
Alpaca Integration Models - OAuth Tokens Only
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AlpacaOAuthToken(models.Model):
    """Model to store OAuth tokens for Alpaca Connect"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alpaca_oauth_tokens')
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True)
    token_type = models.CharField(max_length=20, default='Bearer')
    expires_at = models.DateTimeField()
    scope = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alpaca_oauth_tokens'
    
    def __str__(self):
        return f"{self.user.email} - OAuth Token"
