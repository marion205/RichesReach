# Admin Configuration for MemeQuest Database Models

## 🔧 **DJANGO ADMIN CONFIGURATION**

### **Core Admin Features:**
- **Enhanced User Management**: Extended user admin with MemeQuest profile
- **Meme Coin Management**: Complete meme coin and template management
- **Social Feed Administration**: Social posts and engagement management
- **Raid Coordination**: Raid management and participation tracking
- **DeFi Yield Farming**: Yield pools and positions administration
- **Voice Command Analytics**: Voice command history and analytics
- **BIPOC Community Features**: Community-specific admin tools

---

## 🛠️ **ADMIN CONFIGURATION IMPLEMENTATION**

### **Admin Configuration**
```python
# backend/backend/core/admin.py
"""
Django Admin Configuration for MemeQuest
=======================================

This module provides comprehensive admin interface for:
1. Enhanced user management with MemeQuest profiles
2. Meme coin and template management
3. Social trading posts and engagement
4. Raid coordination and participation
5. DeFi yield farming administration
6. Voice command analytics and management
7. BIPOC community features and analytics
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import (
    MemeTemplate, MemeCoin, SocialPost, PostEngagement, Raid, RaidParticipation,
    YieldPool, YieldPosition, YieldTransaction, VoiceCommand, UserProfile,
    UserAchievement, MemeQuestAnalytics
)

# =============================================================================
# Meme Template Admin
# =============================================================================

@admin.register(MemeTemplate)
class MemeTemplateAdmin(admin.ModelAdmin):
    """Admin interface for meme templates."""
    list_display = [
        'name', 'cultural_theme', 'is_active', 'created_at', 'template_preview'
    ]
    list_filter = ['cultural_theme', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'cultural_theme']
    readonly_fields = ['created_at', 'updated_at', 'template_preview']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'cultural_theme')
        }),
        ('Visual Content', {
            'fields': ('image_url', 'template_preview', 'ai_prompt')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def template_preview(self, obj):
        """Display template image preview."""
        if obj.image_url:
            return format_html(
                '<img src="{}" width="100" height="100" style="border-radius: 10px;" />',
                obj.image_url
            )
        return "No image"
    template_preview.short_description = 'Preview'

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related()

# =============================================================================
# Meme Coin Admin
# =============================================================================

@admin.register(MemeCoin)
class MemeCoinAdmin(admin.ModelAdmin):
    """Admin interface for meme coins."""
    list_display = [
        'name', 'symbol', 'creator', 'status', 'current_price', 
        'market_cap', 'holders', 'graduation_progress', 'created_at'
    ]
    list_filter = ['status', 'network', 'ai_generated', 'created_at']
    search_fields = ['name', 'symbol', 'creator__username', 'contract_address']
    readonly_fields = [
        'created_at', 'updated_at', 'graduated_at', 'graduation_progress',
        'market_cap', 'holders', 'volume_24h'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'symbol', 'creator', 'template', 'description')
        }),
        ('Blockchain Data', {
            'fields': ('network', 'contract_address', 'status')
        }),
        ('Bonding Curve', {
            'fields': (
                'initial_price', 'current_price', 'total_supply',
                'bonding_curve_active', 'graduation_threshold'
            )
        }),
        ('Market Data', {
            'fields': ('market_cap', 'holders', 'volume_24h', 'graduation_progress'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('image_url', 'cultural_theme', 'ai_generated', 'performance_metrics'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'graduated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('creator', 'template')

    def graduation_progress(self, obj):
        """Display graduation progress as progress bar."""
        progress = float(obj.graduation_progress)
        color = 'green' if progress >= 100 else 'orange' if progress >= 50 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 5px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 5px; '
            'display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">'
            '{}%</div></div>',
            min(progress, 100), color, progress
        )
    graduation_progress.short_description = 'Graduation Progress'

# =============================================================================
# Social Post Admin
# =============================================================================

@admin.register(SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    """Admin interface for social posts."""
    list_display = [
        'user', 'post_type', 'content_preview', 'likes', 'shares', 
        'comments', 'is_spotlight', 'xp_reward', 'created_at'
    ]
    list_filter = ['post_type', 'is_spotlight', 'created_at']
    search_fields = ['user__username', 'content', 'meme_coin__name']
    readonly_fields = ['created_at', 'updated_at', 'engagement_summary']
    fieldsets = (
        ('Post Information', {
            'fields': ('user', 'post_type', 'content')
        }),
        ('Media Content', {
            'fields': ('image_url', 'video_url')
        }),
        ('Related Objects', {
            'fields': ('meme_coin', 'raid', 'yield_position'),
            'classes': ('collapse',)
        }),
        ('Engagement Metrics', {
            'fields': ('likes', 'shares', 'comments', 'views', 'engagement_summary'),
            'classes': ('collapse',)
        }),
        ('Gamification', {
            'fields': ('xp_reward', 'is_spotlight')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_preview(self, obj):
        """Display content preview."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def engagement_summary(self, obj):
        """Display engagement summary."""
        total = obj.likes + obj.shares + obj.comments
        return format_html(
            '<strong>Total: {}</strong><br>'
            'Likes: {} | Shares: {} | Comments: {} | Views: {}',
            total, obj.likes, obj.shares, obj.comments, obj.views
        )
    engagement_summary.short_description = 'Engagement Summary'

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('user', 'meme_coin', 'raid')

# =============================================================================
# Post Engagement Admin
# =============================================================================

@admin.register(PostEngagement)
class PostEngagementAdmin(admin.ModelAdmin):
    """Admin interface for post engagements."""
    list_display = ['post', 'user', 'engagement_type', 'created_at']
    list_filter = ['engagement_type', 'created_at']
    search_fields = ['post__content', 'user__username']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('post', 'user')

# =============================================================================
# Raid Admin
# =============================================================================

@admin.register(Raid)
class RaidAdmin(admin.ModelAdmin):
    """Admin interface for raids."""
    list_display = [
        'name', 'meme_coin', 'leader', 'status', 'target_amount', 
        'current_amount', 'progress_bar', 'participants_count', 'start_time'
    ]
    list_filter = ['status', 'start_time']
    search_fields = ['name', 'leader__username', 'meme_coin__name']
    readonly_fields = ['created_at', 'updated_at', 'progress_bar', 'participants_count']
    fieldsets = (
        ('Raid Information', {
            'fields': ('name', 'meme_coin', 'leader', 'status')
        }),
        ('Raid Parameters', {
            'fields': ('target_amount', 'current_amount')
        }),
        ('Gamification', {
            'fields': ('xp_reward', 'success_bonus')
        }),
        ('Timestamps', {
            'fields': ('start_time', 'end_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def progress_bar(self, obj):
        """Display progress bar for raid completion."""
        if obj.target_amount > 0:
            progress = float(obj.current_amount / obj.target_amount * 100)
            color = 'green' if progress >= 100 else 'orange' if progress >= 50 else 'red'
            return format_html(
                '<div style="width: 200px; background-color: #f0f0f0; border-radius: 5px;">'
                '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 5px; '
                'display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">'
                '{}%</div></div>',
                min(progress, 100), color, progress
            )
        return "No target set"
    progress_bar.short_description = 'Progress'

    def participants_count(self, obj):
        """Display number of participants."""
        count = obj.participations.count()
        return format_html(
            '<a href="{}?raid__id__exact={}">{} participants</a>',
            reverse('admin:core_raidparticipation_changelist'),
            obj.id,
            count
        )
    participants_count.short_description = 'Participants'

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('meme_coin', 'leader').prefetch_related('participations')

# =============================================================================
# Raid Participation Admin
# =============================================================================

@admin.register(RaidParticipation)
class RaidParticipationAdmin(admin.ModelAdmin):
    """Admin interface for raid participations."""
    list_display = ['raid', 'user', 'amount', 'xp_earned', 'created_at']
    list_filter = ['created_at']
    search_fields = ['raid__name', 'user__username']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('raid', 'user')

# =============================================================================
# Yield Pool Admin
# =============================================================================

@admin.register(YieldPool)
class YieldPoolAdmin(admin.ModelAdmin):
    """Admin interface for yield pools."""
    list_display = [
        'name', 'protocol', 'apy', 'risk_level', 'tvl', 'min_stake', 
        'max_stake', 'is_community_pool', 'creator', 'created_at'
    ]
    list_filter = ['protocol', 'risk_level', 'is_community_pool', 'auto_compound', 'cross_chain']
    search_fields = ['name', 'description', 'creator__username']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Pool Information', {
            'fields': ('name', 'description', 'protocol', 'creator')
        }),
        ('Yield Metrics', {
            'fields': ('apy', 'tvl', 'risk_level')
        }),
        ('Pool Parameters', {
            'fields': ('tokens', 'min_stake', 'max_stake', 'fees', 'lock_period')
        }),
        ('Features', {
            'fields': ('auto_compound', 'cross_chain', 'is_community_pool')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('creator')

# =============================================================================
# Yield Position Admin
# =============================================================================

@admin.register(YieldPosition)
class YieldPositionAdmin(admin.ModelAdmin):
    """Admin interface for yield positions."""
    list_display = [
        'user', 'pool', 'strategy', 'amount_staked', 'current_apy', 
        'earned_yield', 'total_value', 'auto_compound', 'created_at'
    ]
    list_filter = ['strategy', 'auto_compound', 'created_at']
    search_fields = ['user__username', 'pool__name']
    readonly_fields = ['created_at', 'updated_at', 'last_harvest']
    fieldsets = (
        ('Position Information', {
            'fields': ('user', 'pool', 'strategy')
        }),
        ('Position Data', {
            'fields': ('amount_staked', 'tokens_staked', 'current_apy')
        }),
        ('Yield Data', {
            'fields': ('earned_yield', 'total_value', 'last_harvest')
        }),
        ('Risk & Management', {
            'fields': ('risk_score', 'auto_compound')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('user', 'pool')

# =============================================================================
# Yield Transaction Admin
# =============================================================================

@admin.register(YieldTransaction)
class YieldTransactionAdmin(admin.ModelAdmin):
    """Admin interface for yield transactions."""
    list_display = [
        'user', 'pool', 'transaction_type', 'amount', 'status', 
        'transaction_hash', 'gas_used', 'created_at'
    ]
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['user__username', 'pool__name', 'transaction_hash']
    readonly_fields = ['created_at', 'confirmed_at']
    fieldsets = (
        ('Transaction Information', {
            'fields': ('user', 'pool', 'position', 'transaction_type')
        }),
        ('Transaction Data', {
            'fields': ('amount', 'tokens')
        }),
        ('Blockchain Data', {
            'fields': ('transaction_hash', 'gas_used', 'gas_price', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('user', 'pool', 'position')

# =============================================================================
# Voice Command Admin
# =============================================================================

@admin.register(VoiceCommand)
class VoiceCommandAdmin(admin.ModelAdmin):
    """Admin interface for voice commands."""
    list_display = [
        'user', 'command_type', 'original_command_preview', 'parsed_intent', 
        'confidence', 'processed', 'created_at'
    ]
    list_filter = ['command_type', 'processed', 'created_at']
    search_fields = ['user__username', 'original_command', 'parsed_intent']
    readonly_fields = ['created_at', 'processed_at']
    fieldsets = (
        ('Command Information', {
            'fields': ('user', 'command_type', 'original_command')
        }),
        ('Processing Data', {
            'fields': ('parsed_intent', 'parameters', 'confidence')
        }),
        ('Processing Status', {
            'fields': ('processed', 'result', 'error_message')
        }),
        ('Context', {
            'fields': ('current_screen', 'active_tab'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )

    def original_command_preview(self, obj):
        """Display command preview."""
        return obj.original_command[:50] + '...' if len(obj.original_command) > 50 else obj.original_command
    original_command_preview.short_description = 'Command'

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('user')

# =============================================================================
# User Profile Admin
# =============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for user profiles."""
    list_display = [
        'user', 'current_streak', 'total_xp', 'level', 'wallet_connected', 
        'is_bipoc', 'total_memes_created', 'last_active'
    ]
    list_filter = ['wallet_connected', 'is_bipoc', 'voice_enabled', 'last_active']
    search_fields = ['user__username', 'user__email', 'wallet_address']
    readonly_fields = ['created_at', 'updated_at', 'last_active']
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('MemeQuest Data', {
            'fields': ('current_streak', 'total_xp', 'level')
        }),
        ('Wallet Information', {
            'fields': ('wallet_address', 'wallet_connected', 'preferred_network')
        }),
        ('Voice Preferences', {
            'fields': ('voice_enabled', 'selected_voice', 'voice_speed', 'voice_emotion')
        }),
        ('BIPOC Community', {
            'fields': ('is_bipoc', 'cultural_theme', 'community_contributions')
        }),
        ('Analytics', {
            'fields': (
                'total_memes_created', 'total_raids_joined', 'total_yield_earned',
                'total_social_posts'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('user')

# =============================================================================
# User Achievement Admin
# =============================================================================

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """Admin interface for user achievements."""
    list_display = ['user', 'achievement_type', 'title', 'xp_reward', 'created_at']
    list_filter = ['achievement_type', 'created_at']
    search_fields = ['user__username', 'title', 'description']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Achievement Information', {
            'fields': ('user', 'achievement_type', 'title', 'description')
        }),
        ('Visual Content', {
            'fields': ('icon_url',)
        }),
        ('Rewards', {
            'fields': ('xp_reward',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('user')

# =============================================================================
# MemeQuest Analytics Admin
# =============================================================================

@admin.register(MemeQuestAnalytics)
class MemeQuestAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for MemeQuest analytics."""
    list_display = [
        'date', 'daily_active_users', 'memes_created', 'raids_joined', 
        'yield_positions_opened', 'total_volume', 'bipoc_users_active'
    ]
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('User Metrics', {
            'fields': ('daily_active_users', 'new_users', 'returning_users')
        }),
        ('MemeQuest Metrics', {
            'fields': (
                'memes_created', 'raids_joined', 'yield_positions_opened',
                'social_posts_created', 'voice_commands_processed'
            )
        }),
        ('Engagement Metrics', {
            'fields': ('total_likes', 'total_shares', 'total_comments', 'total_views')
        }),
        ('Revenue Metrics', {
            'fields': ('total_volume', 'total_fees', 'total_yield_earned')
        }),
        ('BIPOC Community', {
            'fields': ('bipoc_users_active', 'bipoc_content_created', 'community_contributions')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# =============================================================================
# Extended User Admin
# =============================================================================

class UserProfileInline(admin.StackedInline):
    """Inline admin for user profile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'MemeQuest Profile'
    fieldsets = (
        ('MemeQuest Data', {
            'fields': ('current_streak', 'total_xp', 'level')
        }),
        ('Wallet Information', {
            'fields': ('wallet_address', 'wallet_connected', 'preferred_network')
        }),
        ('Voice Preferences', {
            'fields': ('voice_enabled', 'selected_voice', 'voice_speed', 'voice_emotion')
        }),
        ('BIPOC Community', {
            'fields': ('is_bipoc', 'cultural_theme', 'community_contributions')
        }),
    )

class ExtendedUserAdmin(UserAdmin):
    """Extended user admin with MemeQuest profile."""
    inlines = (UserProfileInline,)
    
    def get_list_display(self, request):
        """Add MemeQuest fields to user list display."""
        display = list(super().get_list_display(request))
        display.extend(['get_current_streak', 'get_total_xp', 'get_is_bipoc'])
        return display
    
    def get_current_streak(self, obj):
        """Display current streak."""
        if hasattr(obj, 'profile'):
            return obj.profile.current_streak
        return 0
    get_current_streak.short_description = 'Streak'
    
    def get_total_xp(self, obj):
        """Display total XP."""
        if hasattr(obj, 'profile'):
            return obj.profile.total_xp
        return 0
    get_total_xp.short_description = 'XP'
    
    def get_is_bipoc(self, obj):
        """Display BIPOC status."""
        if hasattr(obj, 'profile'):
            return '🌟' if obj.profile.is_bipoc else ''
        return ''
    get_is_bipoc.short_description = 'BIPOC'

# Unregister default User admin and register extended version
admin.site.unregister(User)
admin.site.register(User, ExtendedUserAdmin)

# =============================================================================
# Admin Site Configuration
# =============================================================================

# Customize admin site
admin.site.site_header = "RichesReach AI - MemeQuest Administration"
admin.site.site_title = "MemeQuest Admin"
admin.site.index_title = "Welcome to MemeQuest Administration"

# Add custom admin actions
@admin.action(description='Mark selected posts as spotlight')
def mark_as_spotlight(modeladmin, request, queryset):
    """Mark selected posts as spotlight."""
    updated = queryset.update(is_spotlight=True)
    modeladmin.message_user(request, f'{updated} posts marked as spotlight.')

@admin.action(description='Award XP to selected users')
def award_xp(modeladmin, request, queryset):
    """Award XP to selected users."""
    xp_amount = request.POST.get('xp_amount', 100)
    for user in queryset:
        if hasattr(user, 'profile'):
            user.profile.total_xp += int(xp_amount)
            user.profile.save()
    modeladmin.message_user(request, f'Awarded {xp_amount} XP to {queryset.count()} users.')

# Add actions to relevant admins
SocialPostAdmin.actions = [mark_as_spotlight]
ExtendedUserAdmin.actions = [award_xp]
```

---

## 🎯 **ADMIN CUSTOMIZATION**

### **Custom Admin Templates**
```html
<!-- backend/backend/templates/admin/base_site.html -->
{% extends "admin/base.html" %}
{% load i18n %}

{% block title %}{{ title }} | {% trans 'MemeQuest Admin' %}{% endblock %}

{% block branding %}
<h1 id="site-name">
    <a href="{% url 'admin:index' %}">
        🚀 RichesReach AI - MemeQuest Administration
    </a>
</h1>
{% endblock %}

{% block nav-global %}{% endblock %}
```

### **Admin Dashboard Widgets**
```python
# backend/backend/core/admin_widgets.py
from django.contrib.admin import AdminSite
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

class MemeQuestAdminSite(AdminSite):
    """Custom admin site with MemeQuest dashboard."""
    
    def index(self, request, extra_context=None):
        """Custom admin index with MemeQuest statistics."""
        extra_context = extra_context or {}
        
        # Get statistics
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        stats = {
            'total_users': User.objects.count(),
            'active_users_today': UserProfile.objects.filter(last_active__date=today).count(),
            'total_memes': MemeCoin.objects.count(),
            'active_memes': MemeCoin.objects.filter(status='active').count(),
            'total_posts': SocialPost.objects.count(),
            'posts_today': SocialPost.objects.filter(created_at__date=today).count(),
            'total_raids': Raid.objects.count(),
            'active_raids': Raid.objects.filter(status='active').count(),
            'total_yield_positions': YieldPosition.objects.count(),
            'total_voice_commands': VoiceCommand.objects.count(),
            'bipoc_users': UserProfile.objects.filter(is_bipoc=True).count(),
        }
        
        extra_context['memequest_stats'] = stats
        return super().index(request, extra_context)

# Use custom admin site
admin_site = MemeQuestAdminSite(name='memequest_admin')
```

---

## 🚀 **NEXT STEPS**

1. **Run database migrations** to create all tables
2. **Set up admin interface** with custom configurations
3. **Add sample data** for testing admin features
4. **Configure admin permissions** for different user roles
5. **Test admin functionality** with all models
6. **Add custom admin actions** for bulk operations
7. **Set up admin analytics** and reporting

This comprehensive admin configuration will provide **complete management** of all MemeQuest features with **enhanced user experience**! 🔧🚀