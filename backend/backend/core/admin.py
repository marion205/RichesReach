# Temporarily disable admin.py for testing
# This file will be re-enabled once the model issues are resolved

# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.contrib.auth.models import User
# from .models import User, Post, ChatSession, ChatMessage, Source, Like, Comment, Follow, Stock, StockData, Watchlist

# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ('email', 'name', 'is_active', 'is_staff', 'last_login')
#     list_filter = ('is_active', 'is_staff', 'last_login')
#     search_fields = ('email', 'name')
#     ordering = ('-last_login',)

# @admin.register(Post)
# class PostAdmin(admin.ModelAdmin):
#     list_display = ('user', 'content', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('content', 'user__name', 'user__email')
#     ordering = ('-created_at',)

# @admin.register(ChatSession)
# class ChatSessionAdmin(admin.ModelAdmin):
#     list_display = ('user', 'created_at', 'message_count')
#     list_filter = ('created_at',)
#     search_fields = ('user__name', 'user__email')

# @admin.register(ChatMessage)
# class ChatMessageAdmin(admin.ModelAdmin):
#     list_display = ('session', 'role', 'content', 'created_at')
#     list_filter = ('role', 'created_at')
#     search_fields = ('content', 'session__user__name')

# @admin.register(Source)
# class SourceAdmin(admin.ModelAdmin):
#     list_display = ('name', 'url', 'is_active')
#     list_filter = ('is_active',)
#     search_fields = ('name', 'url')

# @admin.register(Like)
# class LikeAdmin(admin.ModelAdmin):
#     list_display = ('user', 'post', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('user__name', 'post__content')

# @admin.register(Comment)
# class CommentAdmin(admin.ModelAdmin):
#     list_display = ('user', 'post', 'content', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('content', 'user__name', 'post__content')

# @admin.register(Follow)
# class FollowAdmin(admin.ModelAdmin):
#     list_display = ('follower', 'following', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('follower__name', 'following__name')

# @admin.register(Stock)
# class StockAdmin(admin.ModelAdmin):
#     list_display = ('symbol', 'name', 'sector', 'market_cap')
#     list_filter = ('sector', 'market_cap')
#     search_fields = ('symbol', 'name', 'sector')

# @admin.register(StockData)
# class StockDataAdmin(admin.ModelAdmin):
#     list_display = ('stock', 'date', 'open_price', 'close_price', 'volume')
#     list_filter = ('date', 'stock__sector')
#     search_fields = ('stock__symbol', 'stock__name')

# @admin.register(Watchlist)
# class WatchlistAdmin(admin.ModelAdmin):
#     list_display = ('user', 'name', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('name', 'user__name')