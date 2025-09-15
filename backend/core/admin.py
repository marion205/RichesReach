from django.contrib import admin
from .models import User, Post, ChatSession, ChatMessage, Source, Like, Comment, Follow, Stock, StockData, Watchlist
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
