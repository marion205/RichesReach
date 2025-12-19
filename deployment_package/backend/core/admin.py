from django.contrib import admin
from .models import (
    User, Post, ChatSession, ChatMessage, Source, Like, Comment, Follow, 
    Stock, StockData, Watchlist, SecurityEvent, BiometricSettings, 
    ComplianceStatus, SecurityScore, DeviceTrust, AccessPolicy, 
    SupplyChainVendor, ComplianceAutomation
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_active', 'is_staff', 'last_login')
    list_filter = ('is_active', 'is_staff', 'last_login')
    search_fields = ('email', 'name')
    ordering = ('-last_login',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'user__name', 'user__email')
    ordering = ('-created_at',)

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at', 'updated_at', 'message_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__name', 'user__email')
    ordering = ('-updated_at',)
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'content_preview', 'created_at', 'confidence', 'tokens_used')
    list_filter = ('role', 'created_at', 'confidence')
    search_fields = ('content', 'session__title', 'session__user__name')
    ordering = ('-created_at',)
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'message_preview')
    search_fields = ('title', 'url', 'snippet')
    
    def message_preview(self, obj):
        return obj.message.content[:50] + '...' if obj.message.content else 'No content'
    message_preview.short_description = 'Message'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__name', 'user__email', 'post__content')
    ordering = ('-created_at',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'content_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'user__name', 'user__email', 'post__content')
    ordering = ('-created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__name', 'follower__email', 'following__name', 'following__email')
    ordering = ('-created_at',)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company_name', 'sector', 'market_cap', 'pe_ratio', 'beginner_friendly_score', 'last_updated')
    list_filter = ('sector', 'beginner_friendly_score', 'last_updated')
    search_fields = ('symbol', 'company_name', 'sector')
    ordering = ('symbol',)
    readonly_fields = ('last_updated',)

@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    list_display = ('stock', 'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume')
    list_filter = ('date', 'stock__sector')
    search_fields = ('stock__symbol', 'stock__company_name')
    ordering = ('-date', 'stock__symbol')

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'added_at')
    list_filter = ('added_at', 'user', 'stock__sector')
    search_fields = ('user__username', 'stock__symbol', 'notes')
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)

@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'threat_level', 'resolved', 'created_at')
    list_filter = ('threat_level', 'resolved', 'event_type', 'created_at')
    search_fields = ('user__email', 'description', 'event_type')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(BiometricSettings)
class BiometricSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'face_id_enabled', 'voice_id_enabled', 'behavioral_id_enabled', 'device_fingerprint_enabled', 'location_tracking_enabled')
    list_filter = ('face_id_enabled', 'voice_id_enabled', 'behavioral_id_enabled', 'device_fingerprint_enabled', 'location_tracking_enabled')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'last_updated')

@admin.register(ComplianceStatus)
class ComplianceStatusAdmin(admin.ModelAdmin):
    list_display = ('standard', 'status', 'score', 'last_audit_date', 'next_audit_date')
    list_filter = ('status', 'standard')
    search_fields = ('standard', 'status', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(SecurityScore)
class SecurityScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'calculated_at')
    list_filter = ('calculated_at',)
    search_fields = ('user__email',)
    ordering = ('-calculated_at',)
    readonly_fields = ('calculated_at',)


@admin.register(DeviceTrust)
class DeviceTrustAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_id', 'trust_score', 'is_trusted', 'last_verified')
    list_filter = ('is_trusted', 'last_verified')
    search_fields = ('user__email', 'device_id')
    readonly_fields = ('first_seen', 'created_at', 'updated_at')


@admin.register(AccessPolicy)
class AccessPolicyAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'resource', 'policy_type')
    list_filter = ('policy_type', 'resource')
    search_fields = ('user__email', 'action', 'resource')


@admin.register(SupplyChainVendor)
class SupplyChainVendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor_type', 'status', 'risk_score', 'last_audit_date')
    list_filter = ('vendor_type', 'status', 'risk_score')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ComplianceAutomation)
class ComplianceAutomationAdmin(admin.ModelAdmin):
    list_display = ('standard', 'check_name', 'check_type', 'status', 'last_run')
    list_filter = ('standard', 'check_type', 'status')
    search_fields = ('check_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
