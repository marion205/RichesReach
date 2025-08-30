# core/types.py
import graphene
from graphene_django.types import DjangoObjectType
from django.contrib.auth import get_user_model
from .models import Post, ChatSession, ChatMessage, Source, Like, Comment, Follow

User = get_user_model()

class UserType(DjangoObjectType):
    followers_count = graphene.Int()
    following_count = graphene.Int()
    is_following_user = graphene.Boolean()
    is_followed_by_user = graphene.Boolean()
    
    class Meta:
        model = User
        fields = ("id", "email", "name")
    
    def resolve_followers_count(self, info):
        return self.followers_count
    
    def resolve_following_count(self, info):
        return self.following_count
    
    def resolve_is_following_user(self, info):
        user = info.context.user
        return self.is_following(user)
    
    def resolve_is_followed_by_user(self, info):
        user = info.context.user
        return self.is_followed_by(user)

class PostType(DjangoObjectType):
    likes_count = graphene.Int()
    comments_count = graphene.Int()
    is_liked_by_user = graphene.Boolean()
    
    class Meta:
        model = Post
        fields = ("id", "user", "content", "created_at")
    
    def resolve_likes_count(self, info):
        return self.likes_count
    
    def resolve_comments_count(self, info):
        return self.comments_count
    
    def resolve_is_liked_by_user(self, info):
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