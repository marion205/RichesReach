# core/mutations.py
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

from .models import User, Post, Comment, ChatSession, ChatMessage, IncomeProfile, AIPortfolioRecommendation, Stock, Watchlist, Portfolio, StockDiscussion, DiscussionComment
from .types import UserType, PostType, CommentType, ChatSessionType, ChatMessageType
from .portfolio_types import CreatePortfolio, CreatePortfolioHolding, UpdatePortfolioHolding, UpdateHoldingShares, RemovePortfolioHolding
from .auth_utils import RateLimiter, PasswordValidator, SecurityUtils, AccountLockout
from .websocket_service import websocket_service

class CreateUser(graphene.Mutation):
    """Enhanced user creation with security features"""
    user = graphene.Field(lambda: UserType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        name = graphene.String(required=True)
        profilePic = graphene.String()

    def mutate(self, info, email, password, name, profilePic=None):
        # Rate limiting (temporarily disabled for testing)
        # is_limited, attempts_remaining, reset_time = RateLimiter.is_rate_limited(
        #     info.context, action='user_creation', max_attempts=5, window_minutes=60
        # )
        # if is_limited:
        #     raise GraphQLError(f"Too many user creation attempts. Please try again after {reset_time}.")
        
        # Validate password strength
        password_validation = PasswordValidator.validate_password(password)
        if not password_validation['is_valid']:
            suggestions = ', '.join(password_validation['suggestions'])
            raise GraphQLError(f"Password is too weak. {suggestions}")
        
        # Validate name
        name = name.strip()
        if not name or len(name) < 2:
            raise GraphQLError("Please enter a valid name.")
        
        try:
            # Record the attempt for rate limiting
            RateLimiter.record_attempt(info.context, action='user_creation', window_minutes=60)
            
            # Create user with email verification required
            user = User(
                email=email, 
                name=name, 
                profile_pic=profilePic,
                is_active=True  # Set to True for testing (email verification disabled)
            )
            user.set_password(password)
            user.save()
            
            # Generate email verification token
            verification_token = SecurityUtils.generate_secure_token()
            cache_key = f"email_verification_{verification_token}"
            cache.set(cache_key, user.id, timeout=86400)  # 24 hours
            
            # Send verification email (disabled for testing)
            # verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            # send_mail(
            #     'Verify your RichesReach account',
            #     f'Please click the link to verify your account: {verification_url}',
            #     settings.DEFAULT_FROM_EMAIL,
            #     [email],
            #     fail_silently=False,
            # )
            
            return CreateUser(
                user=user,
                success=True,
                message="User created successfully. Please check your email to verify your account."
            )
        except Exception as e:
            return CreateUser(success=False, message=str(e))

# Removed broken ForgotPassword class - will be reimplemented later

class CreateIncomeProfile(graphene.Mutation):
    """Create or update user's income profile"""
    success = graphene.Boolean()
    message = graphene.String()
    incomeProfile = graphene.Field('core.types.IncomeProfileType')

    class Arguments:
        income_bracket = graphene.String(required=True)
        age = graphene.Int(required=True)
        investment_goals = graphene.List(graphene.String, required=True)
        risk_tolerance = graphene.String(required=True)
        investment_horizon = graphene.String(required=True)

    def mutate(self, info, income_bracket, age, investment_goals, risk_tolerance, investment_horizon):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to create an income profile.")
        
        try:
            # Create or update income profile
            income_profile, created = IncomeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'income_bracket': income_bracket,
                    'age': age,
                    'investment_goals': investment_goals,
                    'risk_tolerance': risk_tolerance,
                    'investment_horizon': investment_horizon
                }
            )
            
            if not created:
                # Update existing profile
                income_profile.income_bracket = income_bracket
                income_profile.age = age
                income_profile.investment_goals = investment_goals
                income_profile.risk_tolerance = risk_tolerance
                income_profile.investment_horizon = investment_horizon
                income_profile.save()
            
            return CreateIncomeProfile(
                success=True,
                message="Income profile created successfully!",
                incomeProfile=income_profile
            )
            
        except Exception as e:
            return CreateIncomeProfile(
                success=False,
                message=f"Failed to create income profile: {str(e)}",
                incomeProfile=None
            )

class GenerateAIRecommendations(graphene.Mutation):
    """Generate AI portfolio recommendations based on user's income profile"""
    success = graphene.Boolean()
    message = graphene.String()
    recommendations = graphene.List('core.types.AIPortfolioRecommendationType')

    def mutate(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to generate AI recommendations.")
        
        try:
            # Get user's income profile
            try:
                income_profile = user.incomeProfile
            except:
                return GenerateAIRecommendations(
                    success=False,
                    message="Please create an income profile first to generate AI recommendations.",
                    recommendations=[]
                )
            
            # Generate sample recommendations based on risk tolerance
            risk_tolerance = income_profile.risk_tolerance
            age = income_profile.age
            investment_goals = income_profile.investment_goals
            
            # Sample stock recommendations based on risk tolerance
            if risk_tolerance == 'Conservative':
                recommended_stocks = [
                    {
                        'symbol': 'VTI',
                        'companyName': 'Vanguard Total Stock Market ETF',
                        'allocation': 40.0,
                        'reasoning': 'Broad market exposure with low volatility',
                        'riskLevel': 'Low',
                        'expectedReturn': 7.5
                    },
                    {
                        'symbol': 'BND',
                        'companyName': 'Vanguard Total Bond Market ETF',
                        'allocation': 35.0,
                        'reasoning': 'Stable income generation',
                        'riskLevel': 'Low',
                        'expectedReturn': 4.2
                    },
                    {
                        'symbol': 'VXUS',
                        'companyName': 'Vanguard Total International Stock ETF',
                        'allocation': 15.0,
                        'reasoning': 'International diversification',
                        'riskLevel': 'Medium',
                        'expectedReturn': 8.1
                    },
                    {
                        'symbol': 'REIT',
                        'companyName': 'Real Estate Investment Trust ETF',
                        'allocation': 10.0,
                        'reasoning': 'Real estate exposure for income',
                        'riskLevel': 'Medium',
                        'expectedReturn': 6.8
                    }
                ]
                expected_return = 6.5
                risk_assessment = "Conservative portfolio focused on capital preservation with steady growth."
                
            elif risk_tolerance == 'Moderate':
                recommended_stocks = [
                    {
                        'symbol': 'SPY',
                        'companyName': 'SPDR S&P 500 ETF Trust',
                        'allocation': 50.0,
                        'reasoning': 'Core large-cap exposure',
                        'riskLevel': 'Medium',
                        'expectedReturn': 9.2
                    },
                    {
                        'symbol': 'QQQ',
                        'companyName': 'Invesco QQQ Trust',
                        'allocation': 25.0,
                        'reasoning': 'Technology and growth exposure',
                        'riskLevel': 'Medium-High',
                        'expectedReturn': 11.5
                    },
                    {
                        'symbol': 'VXUS',
                        'companyName': 'Vanguard Total International Stock ETF',
                        'allocation': 15.0,
                        'reasoning': 'International diversification',
                        'riskLevel': 'Medium',
                        'expectedReturn': 8.1
                    },
                    {
                        'symbol': 'BND',
                        'companyName': 'Vanguard Total Bond Market ETF',
                        'allocation': 10.0,
                        'reasoning': 'Income and stability',
                        'riskLevel': 'Low',
                        'expectedReturn': 4.2
                    }
                ]
                expected_return = 8.8
                risk_assessment = "Balanced portfolio with growth potential and moderate risk."
                
            else:  # Aggressive
                recommended_stocks = [
                    {
                        'symbol': 'QQQ',
                        'companyName': 'Invesco QQQ Trust',
                        'allocation': 40.0,
                        'reasoning': 'High-growth technology exposure',
                        'riskLevel': 'High',
                        'expectedReturn': 12.5
                    },
                    {
                        'symbol': 'ARKK',
                        'companyName': 'ARK Innovation ETF',
                        'allocation': 25.0,
                        'reasoning': 'Disruptive innovation companies',
                        'riskLevel': 'Very High',
                        'expectedReturn': 15.2
                    },
                    {
                        'symbol': 'SPY',
                        'companyName': 'SPDR S&P 500 ETF Trust',
                        'allocation': 20.0,
                        'reasoning': 'Core market exposure',
                        'riskLevel': 'Medium',
                        'expectedReturn': 9.2
                    },
                    {
                        'symbol': 'VXUS',
                        'companyName': 'Vanguard Total International Stock ETF',
                        'allocation': 15.0,
                        'reasoning': 'International growth opportunities',
                        'riskLevel': 'Medium-High',
                        'expectedReturn': 8.1
                    }
                ]
                expected_return = 11.8
                risk_assessment = "Aggressive growth portfolio with high potential returns and significant volatility."
            
            # Create the AI recommendation
            recommendation = AIPortfolioRecommendation.objects.create(
                user=user,
                risk_profile=risk_tolerance,
                portfolio_allocation={
                    'stocks': sum(stock['allocation'] for stock in recommended_stocks),
                    'bonds': 0 if risk_tolerance == 'Aggressive' else 10,
                    'cash': 0
                },
                recommended_stocks=recommended_stocks,
                expected_portfolio_return=expected_return,
                risk_assessment=risk_assessment
            )
            
            return GenerateAIRecommendations(
                success=True,
                message="AI recommendations generated successfully!",
                recommendations=[recommendation]
            )
            
        except Exception as e:
            return GenerateAIRecommendations(
                success=False,
                message=f"Failed to generate AI recommendations: {str(e)}",
                recommendations=[]
            )

class AddToWatchlist(graphene.Mutation):
    """Add a stock to user's watchlist"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        stock_symbol = graphene.String(required=True)
        notes = graphene.String(required=False)

    def mutate(self, info, stock_symbol, notes=None):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to add stocks to your watchlist.")
        
        try:
            # Get or create the stock
            stock, created = Stock.objects.get_or_create(
                symbol=stock_symbol.upper(),
                defaults={
                    'name': f'{stock_symbol.upper()} Inc.',  # Default name
                    'sector': 'Unknown',
                    'industry': 'Unknown',
                    'market_cap': 0,
                    'pe_ratio': 0,
                    'dividend_yield': 0,
                    'beginner_friendly_score': 5
                }
            )
            
            # Use get_or_create to handle duplicates gracefully
            watchlist_item, created = Watchlist.objects.get_or_create(
                user=user,
                stock=stock,
                defaults={
                    'notes': notes or ""
                }
            )
            
            if created:
                return AddToWatchlist(
                    success=True,
                    message=f"{stock_symbol} has been added to your watchlist."
                )
            else:
                # Update notes if provided
                if notes:
                    watchlist_item.notes = notes
                    watchlist_item.save()
                
                return AddToWatchlist(
                    success=False,
                    message=f"{stock_symbol} is already in your watchlist."
                )
            
        except Exception as e:
            return AddToWatchlist(
                success=False,
                message=f"Failed to add {stock_symbol} to watchlist: {str(e)}"
            )

class RemoveFromWatchlist(graphene.Mutation):
    """Remove a stock from user's watchlist"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        stock_symbol = graphene.String(required=True)

    def mutate(self, info, stock_symbol):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to remove stocks from your watchlist.")
        
        try:
            # Find the stock
            try:
                stock = Stock.objects.get(symbol=stock_symbol.upper())
            except Stock.DoesNotExist:
                return RemoveFromWatchlist(
                    success=False,
                    message=f"Stock {stock_symbol} not found."
                )
            
            # Remove from watchlist
            watchlist_item = Watchlist.objects.filter(user=user, stock=stock).first()
            if watchlist_item:
                watchlist_item.delete()
                return RemoveFromWatchlist(
                    success=True,
                    message=f"{stock_symbol} has been removed from your watchlist."
                )
            else:
                return RemoveFromWatchlist(
                    success=False,
                    message=f"{stock_symbol} is not in your watchlist."
                )
                
        except Exception as e:
            return RemoveFromWatchlist(
                success=False,
                message=f"Failed to remove {stock_symbol} from watchlist: {str(e)}"
            )

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


class SavePortfolio(graphene.Mutation):
    """Save user's portfolio holdings"""
    success = graphene.Boolean()
    message = graphene.String()
    portfolio = graphene.List('core.types.PortfolioType')

    class Arguments:
        stock_ids = graphene.List(graphene.ID, required=True)
        shares_list = graphene.List(graphene.Int, required=True)
        notes_list = graphene.List(graphene.String, required=False)
        current_prices = graphene.List(graphene.Float, required=False)

    def mutate(self, info, stock_ids, shares_list, notes_list=None, current_prices=None):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to save your portfolio.")
        
        if len(stock_ids) != len(shares_list):
            return SavePortfolio(
                success=False,
                message="Number of stock IDs must match number of shares."
            )
        
        if notes_list and len(notes_list) != len(stock_ids):
            return SavePortfolio(
                success=False,
                message="Number of notes must match number of stocks."
            )
        
        if current_prices and len(current_prices) != len(stock_ids):
            return SavePortfolio(
                success=False,
                message="Number of current prices must match number of stocks."
            )
        
        try:
            saved_portfolios = []
            
            for i, stock_id in enumerate(stock_ids):
                shares = shares_list[i]
                notes = notes_list[i] if notes_list else ""
                current_price = current_prices[i] if current_prices else None
                
                # Skip if shares is 0 or negative
                if shares <= 0:
                    continue
                
                try:
                    stock = Stock.objects.get(id=stock_id)
                except Stock.DoesNotExist:
                    continue
                
                # Use get_or_create to handle existing portfolio entries
                portfolio_item, created = Portfolio.objects.get_or_create(
                    user=user,
                    stock=stock,
                    defaults={
                        'shares': shares,
                        'notes': notes,
                        'current_price': current_price,
                        'average_price': current_price or 0  # Set average_price to current_price or 0
                    }
                )
                
                if not created:
                    # Update existing entry
                    portfolio_item.shares = shares
                    portfolio_item.notes = notes
                    if current_price:
                        portfolio_item.current_price = current_price
                    portfolio_item.save()
                
                saved_portfolios.append(portfolio_item)
            
            return SavePortfolio(
                success=True,
                message=f"Portfolio saved successfully with {len(saved_portfolios)} holdings.",
                portfolio=saved_portfolios
            )
            
        except Exception as e:
            return SavePortfolio(
                success=False,
                message=f"Failed to save portfolio: {str(e)}"
            )


class CreateStockDiscussion(graphene.Mutation):
    """Create a new stock discussion post (Reddit-style)"""
    success = graphene.Boolean()
    message = graphene.String()
    discussion = graphene.Field('core.types.StockDiscussionType')

    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        stock_symbol = graphene.String(required=False)  # Optional - like Reddit posts
        discussion_type = graphene.String(required=False)
        visibility = graphene.String(required=False)  # public or followers

    def mutate(self, info, title, content, stock_symbol=None, discussion_type='general', visibility='followers'):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to create a discussion.")
        
        if len(title.strip()) < 5:
            return CreateStockDiscussion(
                success=False,
                message="Title must be at least 5 characters long."
            )
        
        # Check if content has media tags (images/videos)
        has_media = '[IMAGE:' in content or '[VIDEO:' in content
        content_without_media = content.replace('[IMAGE:', '').replace('[VIDEO:', '').strip()
        
        if not has_media and len(content.strip()) < 10:
            return CreateStockDiscussion(
                success=False,
                message="Content must be at least 10 characters long or include an image/video."
            )
        
        try:
            stock = None
            if stock_symbol:
                # Get or create the stock (like in watchlist)
                stock, created = Stock.objects.get_or_create(
                    symbol=stock_symbol.upper(),
                    defaults={
                        'company_name': f'{stock_symbol.upper()} Inc.',  # Default name
                        'sector': 'Unknown',
                        'market_cap': 0,
                        'current_price': 0
                    }
                )
            
            # Validate visibility choice
            valid_visibility = ['public', 'followers']
            if visibility not in valid_visibility:
                visibility = 'followers'  # Default to followers
            
            discussion = StockDiscussion.objects.create(
                user=user,
                stock=stock,
                title=title.strip(),
                content=content.strip(),
                discussion_type=discussion_type or 'general',
                visibility=visibility
            )
            
            # Broadcast new discussion via WebSocket
            try:
                discussion_data = {
                    'id': discussion.id,
                    'title': discussion.title,
                    'content': discussion.content,
                    'user': {
                        'id': discussion.user.id,
                        'name': discussion.user.name,
                        'profilePic': discussion.user.profile_pic
                    },
                    'stock': {
                        'symbol': discussion.stock.symbol if discussion.stock else None,
                        'company_name': discussion.stock.company_name if discussion.stock else None
                    } if discussion.stock else None,
                    'discussion_type': discussion.discussion_type,
                    'visibility': discussion.visibility,
                    'score': discussion.score,
                    'comment_count': discussion.comment_count,
                    'created_at': discussion.created_at.isoformat()
                }
                websocket_service.broadcast_new_discussion(discussion_data)
            except Exception as e:
                # Don't fail the mutation if WebSocket broadcast fails
                print(f"WebSocket broadcast error: {e}")
            
            return CreateStockDiscussion(
                success=True,
                message="Discussion created successfully!",
                discussion=discussion
            )
            
        except Exception as e:
            return CreateStockDiscussion(
                success=False,
                message=f"Failed to create discussion: {str(e)}"
            )


class CreateDiscussionComment(graphene.Mutation):
    """Create a comment on a discussion (Reddit-style)"""
    success = graphene.Boolean()
    message = graphene.String()
    comment = graphene.Field('core.types.DiscussionCommentType')

    class Arguments:
        discussion_id = graphene.ID(required=True)
        content = graphene.String(required=True)
        parent_comment_id = graphene.ID(required=False)

    def mutate(self, info, discussion_id, content, parent_comment_id=None):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to comment.")
        
        if len(content.strip()) < 3:
            return CreateDiscussionComment(
                success=False,
                message="Comment must be at least 3 characters long."
            )
        
        try:
            try:
                discussion = StockDiscussion.objects.get(id=discussion_id)
            except StockDiscussion.DoesNotExist:
                return CreateDiscussionComment(
                    success=False,
                    message="Discussion not found."
                )
            
            parent_comment = None
            if parent_comment_id:
                try:
                    parent_comment = DiscussionComment.objects.get(id=parent_comment_id)
                except DiscussionComment.DoesNotExist:
                    return CreateDiscussionComment(
                        success=False,
                        message="Parent comment not found."
                    )
            
            comment = DiscussionComment.objects.create(
                user=user,
                discussion=discussion,
                parent_comment=parent_comment,
                content=content.strip()
            )
            
            return CreateDiscussionComment(
                success=True,
                message="Comment posted successfully!",
                comment=comment
            )
            
        except Exception as e:
            return CreateDiscussionComment(
                success=False,
                message=f"Failed to create comment: {str(e)}"
            )


class VoteDiscussion(graphene.Mutation):
    """Vote on a discussion (upvote/downvote)"""
    success = graphene.Boolean()
    message = graphene.String()
    discussion = graphene.Field('core.types.StockDiscussionType')

    class Arguments:
        discussion_id = graphene.ID(required=True)
        vote_type = graphene.String(required=True)  # 'upvote' or 'downvote'

    def mutate(self, info, discussion_id, vote_type):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to vote.")
        
        if vote_type not in ['upvote', 'downvote']:
            return VoteDiscussion(
                success=False,
                message="Vote type must be 'upvote' or 'downvote'."
            )
        
        try:
            try:
                discussion = StockDiscussion.objects.get(id=discussion_id)
            except StockDiscussion.DoesNotExist:
                return VoteDiscussion(
                    success=False,
                    message="Discussion not found."
                )
            
            if vote_type == 'upvote':
                discussion.upvotes += 1
            else:
                discussion.downvotes += 1
            
            discussion.save()
            
            return VoteDiscussion(
                success=True,
                message=f"Vote recorded successfully!",
                discussion=discussion
            )
            
        except Exception as e:
            return VoteDiscussion(
                success=False,
                message=f"Failed to vote: {str(e)}"
            )


class Mutation(graphene.ObjectType):
    # User management
    create_user = CreateUser.Field()
    create_income_profile = CreateIncomeProfile.Field()
    generate_ai_recommendations = GenerateAIRecommendations.Field()
    
    # Watchlist management
    add_to_watchlist = AddToWatchlist.Field()
    remove_from_watchlist = RemoveFromWatchlist.Field()
    
    # Portfolio management
    save_portfolio = SavePortfolio.Field()
    create_portfolio = CreatePortfolio.Field()
    create_portfolio_holding = CreatePortfolioHolding.Field()
    update_portfolio_holding = UpdatePortfolioHolding.Field()
    update_holding_shares = UpdateHoldingShares.Field()
    remove_portfolio_holding = RemovePortfolioHolding.Field()
    
    # Discussion management (Reddit-style)
    create_stock_discussion = CreateStockDiscussion.Field()
    create_discussion_comment = CreateDiscussionComment.Field()
    vote_discussion = VoteDiscussion.Field()
    
    # Authentication
    tokenAuth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    
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
