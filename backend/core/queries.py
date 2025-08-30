import graphene
from django.contrib.auth import get_user_model
from .types import UserType, PostType, ChatSessionType, ChatMessageType, CommentType
from .models import Post, ChatSession, ChatMessage, Comment, User

User = get_user_model()

class Query(graphene.ObjectType):
    all_users = graphene.List(UserType)
    me = graphene.Field(UserType)
    wall_posts = graphene.List(PostType)
    user = graphene.Field(UserType, id=graphene.ID(required=True))
    user_posts = graphene.List(PostType, user_id=graphene.ID(required=True))
    post_comments = graphene.List(CommentType, post_id=graphene.ID(required=True))
    
    # Chat queries
    my_chat_sessions = graphene.List(ChatSessionType)
    chat_session = graphene.Field(ChatSessionType, id=graphene.ID(required=True))
    chat_messages = graphene.List(ChatMessageType, session_id=graphene.ID(required=True))

    def resolve_all_users(root, info):
        return User.objects.all()

    def resolve_me(root, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        return user

    def resolve_wall_posts(self, info):
        return Post.objects.select_related("user").order_by("-created_at")
    
    def resolve_my_chat_sessions(self, info):
        user = info.context.user
        if user.is_anonymous:
            return []
        return ChatSession.objects.filter(user=user).order_by('-updated_at')
    
    def resolve_chat_session(self, info, id):
        user = info.context.user
        if user.is_anonymous:
            return None
        try:
            return ChatSession.objects.get(id=id, user=user)
        except ChatSession.DoesNotExist:
            return None
    
    def resolve_chat_messages(self, info, session_id):
        user = info.context.user
        if user.is_anonymous:
            return []
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            return session.messages.all()
        except ChatSession.DoesNotExist:
            return []
    
    def resolve_user(self, info, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return None
    
    def resolve_user_posts(self, info, user_id):
        try:
            user = User.objects.get(id=user_id)
            return user.posts.all().order_by('-created_at')
        except User.DoesNotExist:
            return []
    
    def resolve_post_comments(self, info, post_id):
        try:
            post = Post.objects.get(id=post_id)
            return post.comments.all()
        except Post.DoesNotExist:
            return []