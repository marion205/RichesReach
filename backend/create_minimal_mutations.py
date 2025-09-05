#!/usr/bin/env python3
"""
Create a minimal working mutations.py with only essential mutations
"""

def create_minimal_mutations():
    """Create a minimal mutations.py that only includes working mutations"""
    
    minimal_mutations = '''# core/mutations.py
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import graphql_jwt
from graphql import GraphQLError
import secrets
import hashlib

from .models import User, Post, Comment, ChatSession, ChatMessage
from .types import UserType, PostType, CommentType, ChatSessionType, ChatMessageType
from .auth_utils import RateLimiter, PasswordValidator, SecurityUtils, AccountLockout

class CreateUser(graphene.Mutation):
    """Enhanced user creation with security features"""
    user = graphene.Field(lambda: UserType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        name = graphene.String(required=True)
        profilePic = graphene.String()

    def mutate(self, info, username, email, password, name, profilePic=None):
        # Rate limiting
        rate_limiter = RateLimiter('user_creation', max_attempts=5, window_minutes=60)
        if not rate_limiter.allow_request(info.context.META.get('REMOTE_ADDR', 'unknown')):
            raise GraphQLError("Too many user creation attempts. Please try again later.")
        
        # Validate password strength
        password_validator = PasswordValidator()
        is_valid, suggestions = password_validator.validate_password(password)
        if not is_valid:
            raise GraphQLError(f"Password is too weak. {suggestions}")
        
        # Validate name
        name = name.strip()
        if not name or len(name) < 2:
            raise GraphQLError("Please enter a valid name.")
        
        try:
            # Create user with email verification required
            user = User(
                email=email, 
                name=name, 
                profile_pic=profilePic,
                is_active=False  # Require email verification
            )
            user.set_password(password)
            user.save()
            
            # Generate email verification token
            verification_token = SecurityUtils.generate_secure_token()
            cache_key = f"email_verification_{verification_token}"
            cache.set(cache_key, user.id, timeout=86400)  # 24 hours
            
            # Send verification email
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            send_mail(
                'Verify your RichesReach account',
                f'Please click the link to verify your account: {verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return CreateUser(
                user=user,
                success=True,
                message="User created successfully. Please check your email to verify your account."
            )
        except Exception as e:
            return CreateUser(success=False, message=str(e))

class ForgotPassword(graphene.Mutation):
    """Send password reset email"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)

    def mutate(self, info, email):
        # Rate limiting
        rate_limiter = RateLimiter('password_reset', max_attempts=3, window_minutes=60)
        if not rate_limiter.allow_request(info.context.META.get('REMOTE_ADDR', 'unknown')):
            raise GraphQLError("Too many password reset attempts. Please try again later.")
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            reset_token = SecurityUtils.generate_secure_token()
            cache_key = f"password_reset_{reset_token}"
            cache.set(cache_key, user.id, timeout=3600)  # 1 hour
            
            # Send reset email
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            send_mail(
                'Reset your RichesReach password',
                f'Click the link to reset your password: {reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return ForgotPassword(
                success=True,
                message="Password reset email sent. Please check your inbox."
            )
        except User.DoesNotExist:
            return ForgotPassword(
                success=True,
                message="If an account with that email exists, a password reset email has been sent."
            )
        except Exception as e:
            return ForgotPassword(success=False, message=str(e))

class ResetPassword(graphene.Mutation):
    """Reset password with token"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        token = graphene.String(required=True)
        new_password = graphene.String(required=True)

    def mutate(self, info, token, new_password):
        # Rate limiting
        rate_limiter = RateLimiter('password_reset_confirm', max_attempts=5, window_minutes=60)
        if not rate_limiter.allow_request(info.context.META.get('REMOTE_ADDR', 'unknown')):
            raise GraphQLError("Too many password reset attempts. Please try again later.")
        
        # Validate password strength
        password_validator = PasswordValidator()
        is_valid, suggestions = password_validator.validate_password(new_password)
        if not is_valid:
            raise GraphQLError(f"Password is too weak. {suggestions}")
        
        try:
            cache_key = f"password_reset_{token}"
            user_id = cache.get(cache_key)
            
            if not user_id:
                raise GraphQLError("Invalid or expired reset token.")
            
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.clear_failed_logins()  # Clear any failed login attempts
            user.save()
            
            # Delete the reset token
            cache.delete(cache_key)
            
            return ResetPassword(
                success=True,
                message="Password reset successfully. You can now log in with your new password."
            )
        except User.DoesNotExist:
            raise GraphQLError("Invalid reset token.")
        except Exception as e:
            return ResetPassword(success=False, message=str(e))

class ChangePassword(graphene.Mutation):
    """Change password for authenticated user"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        current_password = graphene.String(required=True)
        new_password = graphene.String(required=True)

    def mutate(self, info, current_password, new_password):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to change your password.")
        
        # Rate limiting
        rate_limiter = RateLimiter('password_change', max_attempts=5, window_minutes=60)
        if not rate_limiter.allow_request(info.context.META.get('REMOTE_ADDR', 'unknown')):
            raise GraphQLError("Too many password change attempts. Please try again later.")
        
        # Validate current password
        if not user.check_password(current_password):
            raise GraphQLError("Current password is incorrect.")
        
        # Validate new password strength
        password_validator = PasswordValidator()
        is_valid, suggestions = password_validator.validate_password(new_password)
        if not is_valid:
            raise GraphQLError(f"New password is too weak. {suggestions}")
        
        try:
            user.set_password(new_password)
            user.save()
            
            return ChangePassword(
                success=True,
                message="Password changed successfully."
            )
        except Exception as e:
            return ChangePassword(success=False, message=str(e))

class VerifyEmail(graphene.Mutation):
    """Verify email with token"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        token = graphene.String(required=True)

    def mutate(self, info, token):
        try:
            cache_key = f"email_verification_{token}"
            user_id = cache.get(cache_key)
            
            if not user_id:
                raise GraphQLError("Invalid or expired verification token.")
            
            user = User.objects.get(id=user_id)
            user.email_verified = True
            user.is_active = True
            user.save()
            
            # Delete the verification token
            cache.delete(cache_key)
            
            return VerifyEmail(
                success=True,
                message="Email verified successfully. Your account is now active."
            )
        except User.DoesNotExist:
            raise GraphQLError("Invalid verification token.")
        except Exception as e:
            return VerifyEmail(success=False, message=str(e))

class ResendVerificationEmail(graphene.Mutation):
    """Resend email verification"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)

    def mutate(self, info, email):
        # Rate limiting
        rate_limiter = RateLimiter('resend_verification', max_attempts=3, window_minutes=60)
        if not rate_limiter.allow_request(info.context.META.get('REMOTE_ADDR', 'unknown')):
            raise GraphQLError("Too many verification email requests. Please try again later.")
        
        try:
            user = User.objects.get(email=email)
            
            if user.email_verified:
                return ResendVerificationEmail(
                    success=True,
                    message="Email is already verified."
                )
            
            # Generate new verification token
            verification_token = SecurityUtils.generate_secure_token()
            cache_key = f"email_verification_{verification_token}"
            cache.set(cache_key, user.id, timeout=86400)  # 24 hours
            
            # Send verification email
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            send_mail(
                'Verify your RichesReach account',
                f'Please click the link to verify your account: {verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return ResendVerificationEmail(
                success=True,
                message="Verification email sent. Please check your inbox."
            )
        except User.DoesNotExist:
            return ResendVerificationEmail(
                success=True,
                message="If an account with that email exists, a verification email has been sent."
            )
        except Exception as e:
            return ResendVerificationEmail(success=False, message=str(e))

class EnhancedTokenAuth(graphene.Mutation):
    """Enhanced token authentication with security features"""
    token = graphene.String()
    user = graphene.Field(lambda: UserType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        # Rate limiting
        rate_limiter = RateLimiter('login', max_attempts=5, window_minutes=15)
        client_ip = info.context.META.get('REMOTE_ADDR', 'unknown')
        
        if not rate_limiter.allow_request(client_ip):
            raise GraphQLError("Too many login attempts. Please try again later.")
        
        try:
            user = User.objects.get(email=email)
            
            # Check if account is locked
            if user.is_locked():
                raise GraphQLError("Account is temporarily locked due to too many failed login attempts.")
            
            # Authenticate user
            if user.check_password(password):
                # Clear failed login attempts
                user.clear_failed_logins()
                user.last_login_ip = client_ip
                user.save()
                
                # Generate JWT token
                token = graphql_jwt.utils.jwt_encode(
                    graphql_jwt.utils.jwt_payload(user)
                )
                
                return EnhancedTokenAuth(
                    token=token,
                    user=user,
                    success=True,
                    message="Login successful"
                )
            else:
                # Record failed login attempt
                user.record_failed_login()
                user.save()
                
                # Check if account should be locked
                if user.failed_login_attempts >= 5:
                    user.lock_account(minutes=30)
                    user.save()
                    raise GraphQLError("Account locked due to too many failed login attempts. Please try again in 30 minutes.")
                
                raise GraphQLError("Invalid email or password.")
                
        except User.DoesNotExist:
            raise GraphQLError("Invalid email or password.")
        except Exception as e:
            return EnhancedTokenAuth(success=False, message=str(e))

# Basic mutations for core functionality
class CreatePost(graphene.Mutation):
    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        content = graphene.String(required=True)

    def mutate(self, info, content):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to create a post.")
        
        try:
            post = Post.objects.create(user=user, content=content)
            return CreatePost(post=post, success=True, message="Post created successfully")
        except Exception as e:
            return CreatePost(success=False, message=str(e))

class ToggleLike(graphene.Mutation):
    post = graphene.Field(PostType)
    liked = graphene.Boolean()
    success = graphene.Boolean()

    class Arguments:
        post_id = graphene.ID(required=True)

    def mutate(self, info, post_id):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to like posts.")
        
        try:
            post = Post.objects.get(id=post_id)
            if user in post.likes.all():
                post.likes.remove(user)
                liked = False
            else:
                post.likes.add(user)
                liked = True
            
            return ToggleLike(post=post, liked=liked, success=True)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found")
        except Exception as e:
            return ToggleLike(success=False, liked=False)

class CreateComment(graphene.Mutation):
    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        post_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    def mutate(self, info, post_id, content):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to comment.")
        
        try:
            post = Post.objects.get(id=post_id)
            comment = Comment.objects.create(user=user, post=post, content=content)
            return CreateComment(comment=comment, success=True, message="Comment created successfully")
        except Post.DoesNotExist:
            raise GraphQLError("Post not found")
        except Exception as e:
            return CreateComment(success=False, message=str(e))

class DeleteComment(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        comment_id = graphene.ID(required=True)

    def mutate(self, info, comment_id):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in.")
        
        try:
            comment = Comment.objects.get(id=comment_id)
            if comment.user != user:
                raise GraphQLError("You can only delete your own comments.")
            
            comment.delete()
            return DeleteComment(success=True, message="Comment deleted successfully")
        except Comment.DoesNotExist:
            raise GraphQLError("Comment not found")
        except Exception as e:
            return DeleteComment(success=False, message=str(e))

class ToggleFollow(graphene.Mutation):
    user = graphene.Field(UserType)
    following = graphene.Boolean()
    success = graphene.Boolean()

    class Arguments:
        user_id = graphene.ID(required=True)

    def mutate(self, info, user_id):
        current_user = info.context.user
        if not current_user.is_authenticated:
            raise GraphQLError("You must be logged in to follow users.")
        
        try:
            target_user = User.objects.get(id=user_id)
            if current_user == target_user:
                raise GraphQLError("You cannot follow yourself.")
            
            if target_user in current_user.following.all():
                current_user.following.remove(target_user)
                following = False
            else:
                current_user.following.add(target_user)
                following = True
            
            return ToggleFollow(user=target_user, following=following, success=True)
        except User.DoesNotExist:
            raise GraphQLError("User not found")
        except Exception as e:
            return ToggleFollow(success=False, following=False)

class CreateChatSession(graphene.Mutation):
    session = graphene.Field(ChatSessionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        title = graphene.String()

    def mutate(self, info, title=None):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to create a chat session.")
        
        try:
            if not title:
                title = f"Chat {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            
            session = ChatSession.objects.create(user=user, title=title)
            return CreateChatSession(session=session, success=True, message="Chat session created")
        except Exception as e:
            return CreateChatSession(success=False, message=str(e))

class SendMessage(graphene.Mutation):
    message = graphene.Field(ChatMessageType)
    session = graphene.Field(ChatSessionType)
    success = graphene.Boolean()

    class Arguments:
        session_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    def mutate(self, info, session_id, content):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to send messages.")
        
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            message = ChatMessage.objects.create(session=session, content=content)
            return SendMessage(message=message, session=session, success=True)
        except ChatSession.DoesNotExist:
            raise GraphQLError("Chat session not found")
        except Exception as e:
            return SendMessage(success=False)

class GetChatHistory(graphene.Mutation):
    messages = graphene.List(ChatMessageType)
    session = graphene.Field(ChatSessionType)
    success = graphene.Boolean()

    class Arguments:
        session_id = graphene.ID(required=True)

    def mutate(self, info, session_id):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to view chat history.")
        
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            messages = ChatMessage.objects.filter(session=session).order_by('created_at')
            return GetChatHistory(messages=messages, session=session, success=True)
        except ChatSession.DoesNotExist:
            raise GraphQLError("Chat session not found")
        except Exception as e:
            return GetChatHistory(success=False)

class Mutation(graphene.ObjectType):
    # User management
    create_user = CreateUser.Field()
    
    # Authentication
    tokenAuth = graphql_jwt.ObtainJSONWebToken.Field()
    enhanced_token_auth = EnhancedTokenAuth.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    
    # Enhanced Authentication
    forgot_password = ForgotPassword.Field()
    reset_password = ResetPassword.Field()
    change_password = ChangePassword.Field()
    verify_email = VerifyEmail.Field()
    resend_verification_email = ResendVerificationEmail.Field()
    
    # Social features
    create_post = CreatePost.Field()
    toggle_like = ToggleLike.Field()
    create_comment = CreateComment.Field()
    delete_comment = DeleteComment.Field()
    toggle_follow = ToggleFollow.Field()
    
    # Chat features
    create_chat_session = CreateChatSession.Field()
    send_message = SendMessage.Field()
    get_chat_history = GetChatHistory.Field()
'''
    
    with open('core/mutations.py', 'w') as f:
        f.write(minimal_mutations)
    
    print("✅ Created minimal mutations.py with only working mutations")

if __name__ == "__main__":
    create_minimal_mutations()
