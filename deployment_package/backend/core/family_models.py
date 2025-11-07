"""
Database models for Family Sharing feature
"""

from django.db import models
from django.contrib.auth import get_user_model
import json

User = get_user_model()


class FamilyGroup(models.Model):
    """
    Family group for sharing Constellation Orb
    """
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_family_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Shared Orb settings
    shared_orb_enabled = models.BooleanField(default=True)
    shared_orb_net_worth = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    shared_orb_last_synced = models.DateTimeField(null=True, blank=True)
    
    # Family settings (stored as JSON)
    settings = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'family_groups'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (Owner: {self.owner.username})"
    
    def get_settings(self):
        """Get settings with defaults"""
        defaults = {
            'allowTeenAccounts': True,
            'requireApproval': False,
            'syncFrequency': 'realtime',
        }
        defaults.update(self.settings or {})
        return defaults
    
    def set_settings(self, **kwargs):
        """Update settings"""
        current = self.get_settings()
        current.update(kwargs)
        self.settings = current
        self.save(update_fields=['settings'])


class FamilyMember(models.Model):
    """
    Member of a family group
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('member', 'Member'),
        ('teen', 'Teen'),
    ]
    
    id = models.CharField(max_length=100, primary_key=True)
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='family_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(null=True, blank=True)
    
    # Permissions (stored as JSON for flexibility)
    permissions = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'family_members'
        unique_together = [['family_group', 'user']]
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} in {self.family_group.name} ({self.role})"
    
    def get_permissions(self):
        """Get permissions with defaults based on role"""
        defaults = {
            'canViewOrb': True,
            'canEditGoals': False,
            'canViewDetails': True,
            'canInvite': False,
        }
        
        if self.role == 'owner':
            defaults.update({
                'canViewOrb': True,
                'canEditGoals': True,
                'canViewDetails': True,
                'canInvite': True,
            })
        elif self.role == 'teen':
            defaults.update({
                'canViewOrb': True,
                'canEditGoals': False,
                'canViewDetails': False,
                'canInvite': False,
                'spendingLimit': 0,
            })
        
        # Merge with stored permissions
        stored = self.permissions or {}
        defaults.update(stored)
        return defaults
    
    def set_permissions(self, **kwargs):
        """Update permissions"""
        current = self.get_permissions()
        current.update(kwargs)
        self.permissions = current
        self.save(update_fields=['permissions'])


class FamilyInvite(models.Model):
    """
    Invitation to join a family group
    """
    id = models.CharField(max_length=100, primary_key=True)
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        related_name='invites'
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, default='member')
    invite_code = models.CharField(max_length=50, unique=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invites'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invites'
    )
    
    class Meta:
        db_table = 'family_invites'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invite to {self.email} for {self.family_group.name}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_accepted(self):
        return self.accepted_at is not None


class OrbSyncEvent(models.Model):
    """
    Event log for orb synchronization across family members
    """
    EVENT_TYPES = [
        ('gesture', 'Gesture'),
        ('update', 'Update'),
        ('view', 'View'),
    ]
    
    id = models.CharField(max_length=100, primary_key=True)
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        related_name='sync_events'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orb_sync_events'
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Event data (stored as JSON)
    data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'orb_sync_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['family_group', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} by {self.user.username} at {self.timestamp}"

