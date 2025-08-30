# core/types.py
import graphene
from graphene_django.types import DjangoObjectType
from django.contrib.auth import get_user_model
from .models import Post, ChatSession, ChatMessage, Source

User = get_user_model()

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "email", "name")

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ("id", "user", "content", "created_at")

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