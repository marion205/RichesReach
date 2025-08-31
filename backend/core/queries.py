import graphene
from django.contrib.auth import get_user_model
from .types import UserType, PostType, ChatSessionType, ChatMessageType, CommentType
from .models import Post, ChatSession, ChatMessage, Comment, User
import django.db.models as models

User = get_user_model()

class Query(graphene.ObjectType):
    all_users = graphene.List(UserType)
    search_users = graphene.List(UserType, query=graphene.String(required=False))
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
        user = info.context.user
        if user.is_anonymous:
            return []
        # Exclude current user and return users they don't follow
        return User.objects.exclude(id=user.id).exclude(
            id__in=user.following.values_list('following', flat=True)
        )[:20]  # Limit to 20 users

    def resolve_search_users(root, info, query=None):
        user = info.context.user
        if user.is_anonymous:
            return []
        
        if query:
            # Search by name or email
            users = User.objects.filter(
                models.Q(name__icontains=query) | 
                models.Q(email__icontains=query)
            ).exclude(id=user.id)
        else:
            # Return users not followed by current user
            users = User.objects.exclude(id=user.id).exclude(
                id__in=user.following.values_list('following', flat=True)
            )
        
        return users[:20]  # Limit results

    def resolve_me(root, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        return user

    def resolve_wall_posts(self, info):
        user = info.context.user
        if user.is_anonymous:
            return []
        
        # Get users that the current user follows
        following_users = user.following.values_list('following', flat=True)
        
        # Return posts from followed users + current user's own posts
        return Post.objects.filter(
            user__in=list(following_users) + [user]
        ).select_related("user").order_by("-created_at")
    
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