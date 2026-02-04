"""
Social-domain root fields: users, posts, chat.
Composed into ExtendedQuery; resolvers use DataLoader for user where applicable.
"""
import logging

import django.db.models as models
from django.db.models import Prefetch
import graphene

from core.models import ChatSession, ChatMessage, Comment, Post, User

logger = logging.getLogger(__name__)


class SocialQuery(graphene.ObjectType):
    """
    Root fields for social: all_users, search_users, wall_posts, all_posts,
    user, user_posts, post_comments, my_chat_sessions, chat_session, chat_messages.
    """

    all_users = graphene.List("core.types.UserType")
    search_users = graphene.List("core.types.UserType", query=graphene.String(required=False))
    wall_posts = graphene.List("core.types.PostType")
    all_posts = graphene.List("core.types.PostType")
    user = graphene.Field("core.types.UserType", id=graphene.ID(required=True))
    user_posts = graphene.List("core.types.PostType", user_id=graphene.ID(required=True))
    post_comments = graphene.List("core.types.CommentType", post_id=graphene.ID(required=True))
    my_chat_sessions = graphene.List("core.types.ChatSessionType")
    chat_session = graphene.Field("core.types.ChatSessionType", id=graphene.ID(required=True))
    chat_messages = graphene.List("core.types.ChatMessageType", session_id=graphene.ID(required=True))

    def resolve_all_users(self, info):
        user = getattr(info.context, "user", None)
        if not user or getattr(user, "is_anonymous", True):
            return []
        return list(
            User.objects.exclude(id=user.id).exclude(
                id__in=user.following.values_list("following", flat=True)
            )[:20]
        )

    def resolve_search_users(self, info, query=None):
        user = getattr(info.context, "user", None)
        if not user or getattr(user, "is_anonymous", True):
            return []
        if query:
            users = User.objects.filter(
                models.Q(name__icontains=query) | models.Q(email__icontains=query)
            ).exclude(id=user.id)
        else:
            users = User.objects.exclude(id=user.id).exclude(
                id__in=user.following.values_list("following", flat=True)
            )
        return list(users[:20])

    def resolve_wall_posts(self, info):
        user = getattr(info.context, "user", None)
        if not user or getattr(user, "is_anonymous", True):
            return []
        following_users = user.following.values_list("following", flat=True)
        comments_prefetch = Prefetch(
            "comments",
            queryset=Comment.objects.select_related("user").order_by("-created_at"),
        )
        return list(
            Post.objects.filter(user__in=list(following_users) + [user])
            .select_related("user")
            .prefetch_related(comments_prefetch, "likes")
            .order_by("-created_at")
        )

    def resolve_all_posts(self, info):
        return list(Post.objects.select_related("user").order_by("-created_at")[:100])

    def resolve_user(self, info, id):
        """Get a user by ID (uses DataLoader when attached to context)."""
        try:
            from core.graphql.dataloaders import get_loaders_for_context
            loaders = get_loaders_for_context(info.context)
            if loaders and getattr(loaders, "user_loader", None):
                return loaders.user_loader.load(int(id))
        except Exception:
            pass
        from core.dataloaders import get_user_loader
        return get_user_loader().load(int(id))

    def resolve_user_posts(self, info, user_id):
        try:
            posts = (
                Post.objects.filter(user_id=user_id)
                .select_related("user")
                .prefetch_related("comments")
                .order_by("-created_at")
            )
            return list(posts)
        except (ValueError, TypeError):
            return []

    def resolve_post_comments(self, info, post_id):
        try:
            from core.models import Comment
            return list(
                Comment.objects.filter(post_id=post_id)
                .select_related("user", "post")
                .order_by("-created_at")
            )
        except (ValueError, TypeError):
            return []

    def resolve_my_chat_sessions(self, info):
        user = getattr(info.context, "user", None)
        if not user or getattr(user, "is_anonymous", True):
            return []
        return list(
            ChatSession.objects.filter(user=user)
            .select_related("user")
            .order_by("-updated_at")
        )

    def resolve_chat_session(self, info, id):
        user = getattr(info.context, "user", None)
        if not user or getattr(user, "is_anonymous", True):
            return None
        try:
            return ChatSession.objects.select_related("user").get(id=id, user=user)
        except ChatSession.DoesNotExist:
            return None

    def resolve_chat_messages(self, info, session_id):
        user = getattr(info.context, "user", None)
        if not user or getattr(user, "is_anonymous", True):
            return []
        try:
            from core.models import ChatMessage
            return list(
                ChatMessage.objects.filter(session_id=session_id, session__user=user)
                .select_related("session", "session__user")
                .order_by("created_at")
            )
        except (ValueError, TypeError):
            return []
