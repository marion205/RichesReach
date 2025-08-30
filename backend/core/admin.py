from django.contrib import admin
from .models import User, Post, ChatSession, ChatMessage, Source

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
