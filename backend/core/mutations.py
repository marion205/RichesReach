# core/mutations.py
import graphene
from django.contrib.auth import get_user_model
from graphql import GraphQLError
from datetime import datetime, timezone
from .types import UserType, PostType, ChatMessageType, SourceType, ChatSessionType
from .models import Post, ChatSession, ChatMessage, Source, Like, Comment, Follow
from .ai_service import AIService
import graphql_jwt

User = get_user_model()

class CreateUser(graphene.Mutation):
    user = graphene.Field(lambda: UserType)

    class Arguments:
        email = graphene.String(required=True)
        name = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, name, password):
        if User.objects.filter(email=email).exists():
            raise GraphQLError("A user with that email already exists.")
        user = User(email=email.strip().lower(), name=name)
        user.set_password(password)
        user.save()
        return CreateUser(user=user)

class CreatePost(graphene.Mutation):
    post = graphene.Field(PostType)

    class Arguments:
        content = graphene.String(required=True)

    def mutate(self, info, content):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to post.")
        post = Post.objects.create(user=user, content=content)
        return CreatePost(post=post)

class ToggleLike(graphene.Mutation):
    post = graphene.Field(PostType)
    liked = graphene.Boolean()

    class Arguments:
        post_id = graphene.ID(required=True)

    def mutate(self, info, post_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to like posts.")
        
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found.")
        
        # Check if user already liked the post
        existing_like = Like.objects.filter(user=user, post=post).first()
        
        if existing_like:
            # Unlike
            existing_like.delete()
            liked = False
        else:
            # Like
            Like.objects.create(user=user, post=post)
            liked = True
        
        return ToggleLike(post=post, liked=liked)

class CreateComment(graphene.Mutation):
    comment = graphene.Field('core.types.CommentType')

    class Arguments:
        post_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    def mutate(self, info, post_id, content):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to comment.")
        
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found.")
        
        comment = Comment.objects.create(user=user, post=post, content=content)
        return CreateComment(comment=comment)

class ToggleFollow(graphene.Mutation):
    user = graphene.Field(UserType)
    following = graphene.Boolean()

    class Arguments:
        user_id = graphene.ID(required=True)

    def mutate(self, info, user_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to follow users.")
        
        try:
            user_to_follow = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User not found.")
        
        if user == user_to_follow:
            raise GraphQLError("Cannot follow yourself.")
        
        # Check if already following
        existing_follow = Follow.objects.filter(follower=user, following=user_to_follow).first()
        
        if existing_follow:
            # Unfollow
            existing_follow.delete()
            following = False
        else:
            # Follow
            Follow.objects.create(follower=user, following=user_to_follow)
            following = True
        
        return ToggleFollow(user=user_to_follow, following=following)

class CreateChatSession(graphene.Mutation):
    session = graphene.Field(ChatSessionType)

    class Arguments:
        title = graphene.String(required=False)

    def mutate(self, info, title=None):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to create chat session.")
        
        if not title:
            title = f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        session = ChatSession.objects.create(user=user, title=title)
        return CreateChatSession(session=session)

class SendMessage(graphene.Mutation):
    message = graphene.Field(ChatMessageType)
    session = graphene.Field(ChatSessionType)

    class Arguments:
        session_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    def mutate(self, info, session_id, content):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to send messages.")
        
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            raise GraphQLError("Chat session not found.")
        
        # Save user message
        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=content
        )
        
        # Generate AI response
        ai_service = AIService()
        
        # Get conversation history for context
        previous_messages = []
        for msg in session.messages.all()[:10]:  # Last 10 messages for context
            previous_messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # Add current user message
        previous_messages.append({
            'role': 'user',
            'content': content
        })
        
        # Get user context for AI
        user_context = f"User: {user.name} (ID: {user.id})"
        
        # Get AI response
        ai_response = ai_service.get_chat_response(previous_messages, user_context)
        
        # Save AI response
        ai_message = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response['content'],
            confidence=ai_response['confidence'],
            tokens_used=ai_response['tokens_used']
        )
        
        # Generate session title if this is the first message
        if session.messages.count() == 2:  # User message + AI response
            title = ai_service.generate_session_title(content)
            session.title = title
            session.save()
        
        # Update session timestamp
        session.save()  # This updates the updated_at field
        
        return SendMessage(message=ai_message, session=session)

class GetChatHistory(graphene.Mutation):
    messages = graphene.List(ChatMessageType)
    session = graphene.Field(ChatSessionType)

    class Arguments:
        session_id = graphene.ID(required=True)

    def mutate(self, info, session_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to view chat history.")
        
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            raise GraphQLError("Chat session not found.")
        
        messages = session.messages.all()
        return GetChatHistory(messages=messages, session=session)

# Root mutation
class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_post = CreatePost.Field()
    toggle_like = ToggleLike.Field()
    create_comment = CreateComment.Field()
    toggle_follow = ToggleFollow.Field()
    create_chat_session = CreateChatSession.Field()
    send_message = SendMessage.Field()
    get_chat_history = GetChatHistory.Field()
    
    # JWT Authentication
    tokenAuth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()