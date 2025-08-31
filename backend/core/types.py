# core/types.py
import graphene
from graphene_django.types import DjangoObjectType
from django.contrib.auth import get_user_model
from .models import Post, ChatSession, ChatMessage, Source, Like, Comment, Follow, Stock, StockData, Watchlist

User = get_user_model()

class UserType(DjangoObjectType):
    followersCount = graphene.Int()
    followingCount = graphene.Int()
    isFollowingUser = graphene.Boolean()
    isFollowedByUser = graphene.Boolean()
    
    class Meta:
        model = User
        fields = ("id", "email", "name", "profile_pic")
    
    def resolve_followersCount(self, info):
        return self.followers_count
    
    def resolve_followingCount(self, info):
        return self.following_count
    
    def resolve_isFollowingUser(self, info):
        user = info.context.user
        return user.is_following(self)  # Check if current user follows this user
    
    def resolve_isFollowedByUser(self, info):
        user = info.context.user
        return self.is_followed_by(user)

class PostType(DjangoObjectType):
    likesCount = graphene.Int()
    commentsCount = graphene.Int()
    isLikedByUser = graphene.Boolean()
    
    class Meta:
        model = Post
        fields = ("id", "user", "content", "image", "created_at")
    
    def resolve_likesCount(self, info):
        return self.likes_count
    
    def resolve_commentsCount(self, info):
        return self.comments_count
    
    def resolve_isLikedByUser(self, info):
        user = info.context.user
        return self.is_liked_by(user)

class ChatSessionType(DjangoObjectType):
    class Meta:
        model = ChatSession
        fields = ("id", "user", "title", "created_at", "updated_at")

class SourceType(DjangoObjectType):
    class Meta:
        model = Source
        fields = ("id", "title", "url", "snippet")

class ChatMessageType(DjangoObjectType):
    sources = graphene.List(SourceType)
    
    class Meta:
        model = ChatMessage
        fields = ("id", "session", "role", "content", "created_at", "confidence", "tokens_used")
    
    def resolve_sources(self, info):
        return self.sources.all()

class LikeType(DjangoObjectType):
    class Meta:
        model = Like
        fields = ("id", "user", "post", "created_at")

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = ("id", "user", "post", "content", "created_at")

class FollowType(DjangoObjectType):
    class Meta:
        model = Follow
        fields = ("id", "follower", "following", "created_at")

class StockType(DjangoObjectType):
    current_price = graphene.Float()
    price_change = graphene.Float()
    price_change_percent = graphene.Float()
    
    class Meta:
        model = Stock
        fields = ("id", "symbol", "company_name", "sector", "market_cap", "pe_ratio", 
                 "dividend_yield", "debt_ratio", "volatility", "beginner_friendly_score", 
                 "last_updated")
    
    def resolve_current_price(self, info):
        # This will be populated by the Alpha Vantage API
        return None
    
    def resolve_price_change(self, info):
        # This will be populated by the Alpha Vantage API
        return None
    
    def resolve_price_change_percent(self, info):
        # This will be populated by the Alpha Vantage API
        return None

class StockDataType(DjangoObjectType):
    class Meta:
        model = StockData
        fields = ("id", "stock", "date", "open_price", "high_price", "low_price", 
                 "close_price", "volume")

class WatchlistType(DjangoObjectType):
    class Meta:
        model = Watchlist
        fields = ("id", "user", "stock", "added_at", "notes")