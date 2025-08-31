import graphene
from django.contrib.auth import get_user_model
from .types import UserType, PostType, ChatSessionType, ChatMessageType, CommentType, StockType, StockDataType, WatchlistType
from .models import Post, ChatSession, ChatMessage, Comment, User, Stock, StockData, Watchlist
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
    
    # Stock queries
    stocks = graphene.List(StockType, search=graphene.String(required=False))
    stock = graphene.Field(StockType, symbol=graphene.String(required=True))
    my_watchlist = graphene.List(WatchlistType)
    beginner_friendly_stocks = graphene.List(StockType)

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
            return post.comments.all().order_by('-created_at')
        except Post.DoesNotExist:
            return []
    
    def resolve_stocks(self, info, search=None):
        """Get all stocks or search by symbol/company name"""
        if search:
            return Stock.objects.filter(
                models.Q(symbol__icontains=search.upper()) |
                models.Q(company_name__icontains=search)
            )[:50]  # Limit search results
        return Stock.objects.all()[:100]  # Limit to 100 stocks
    
    def resolve_stock(self, info, symbol):
        """Get a specific stock by symbol"""
        try:
            return Stock.objects.get(symbol=symbol.upper())
        except Stock.DoesNotExist:
            return None
    
    def resolve_my_watchlist(self, info):
        """Get current user's watchlist"""
        user = info.context.user
        if user.is_anonymous:
            return []
        return Watchlist.objects.filter(user=user).select_related('stock').order_by('-added_at')
    
    def resolve_beginner_friendly_stocks(self, info):
        """Get stocks suitable for beginner investors (under $30k/year)"""
        return Stock.objects.filter(
            beginner_friendly_score__gte=80,  # High beginner-friendly score
            market_cap__gte=100000000000,    # Large cap companies (>$100B)
        ).order_by('-beginner_friendly_score')[:20]