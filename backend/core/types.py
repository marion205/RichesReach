# core/types.py
import graphene
from graphene_django.types import DjangoObjectType
from django.contrib.auth import get_user_model
from .models import Post

User = get_user_model()

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "email", "name")

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ("id", "user", "content", "created_at")

# ---- Add these non-Django GraphQL types for the chatbot ----
class SourceType(graphene.ObjectType):
    title = graphene.String()
    url = graphene.String()
    snippet = graphene.String()

class ChatMessageType(graphene.ObjectType):
    id = graphene.ID(required=True)
    role = graphene.String(required=True)      # "assistant" | "user"
    content = graphene.String(required=True)
    created_at = graphene.DateTime()
    confidence = graphene.Float()
    sources = graphene.List(SourceType)