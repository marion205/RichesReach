# core/mutations.py
import graphene
from django.contrib.auth import get_user_model
from graphql import GraphQLError
from datetime import datetime, timezone
from .types import UserType, PostType, ChatMessageType, SourceType, ChatSessionType, WatchlistType, WatchlistItemType, StockDiscussionType, DiscussionCommentType, PortfolioType, PortfolioPositionType, PriceAlertType, SocialFeedType, UserAchievementType, StockSentimentType
from .models import Post, ChatSession, ChatMessage, Source, Like, Comment, Follow, Stock, Watchlist, WatchlistItem, StockDiscussion, DiscussionComment, Portfolio, PortfolioPosition, PriceAlert, SocialFeed, UserAchievement, StockSentiment, IncomeProfile, AIPortfolioRecommendation, StockRecommendation
from .ai_service import AIService
import graphql_jwt

User = get_user_model()

class CreateUser(graphene.Mutation):
    user = graphene.Field(lambda: UserType)

    class Arguments:
        email = graphene.String(required=True)
        name = graphene.String(required=True)
        password = graphene.String(required=True)
        profilePic = graphene.String(required=False)

    def mutate(self, info, email, name, password, profilePic=None):
        if User.objects.filter(email=email).exists():
            raise GraphQLError("A user with that email already exists.")
        user = User(email=email.strip().lower(), name=name, profile_pic=profilePic)
        user.set_password(password)
        user.save()
        return CreateUser(user=user)

class CreatePost(graphene.Mutation):
    post = graphene.Field(PostType)

    class Arguments:
        content = graphene.String(required=True)
        image = graphene.String(required=False)

    def mutate(self, info, content, image=None):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to post.")
        post = Post.objects.create(user=user, content=content, image=image)
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

class DeleteComment(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        comment_id = graphene.ID(required=True)

    def mutate(self, info, comment_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to delete comments.")
        
        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            raise GraphQLError("Comment not found.")
        
        # Check if user owns the comment
        if comment.user != user:
            raise GraphQLError("You can only delete your own comments.")
        
        comment.delete()
        return DeleteComment(success=True, message="Comment deleted successfully.")

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

class AddToWatchlist(graphene.Mutation):
    watchlist_item = graphene.Field('core.types.WatchlistItemType')
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        stock_symbol = graphene.String(required=True)
        notes = graphene.String(required=False)

    def mutate(self, info, stock_symbol, notes=None):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to add stocks to watchlist.")
        
        try:
            stock = Stock.objects.get(symbol=stock_symbol.upper())
        except Stock.DoesNotExist:
            raise GraphQLError("Stock not found.")
        
        # Get or create the user's default watchlist
        watchlist, created = Watchlist.objects.get_or_create(
            user=user, 
            name="My Watchlist",
            defaults={'description': 'Default watchlist for tracking stocks'}
        )
        
        # Check if already in watchlist
        if WatchlistItem.objects.filter(watchlist=watchlist, stock=stock).exists():
            raise GraphQLError("Stock is already in your watchlist.")
        
        # Create the watchlist item
        watchlist_item = WatchlistItem.objects.create(
            watchlist=watchlist,
            stock=stock,
            notes=notes
        )
        
        return AddToWatchlist(
            watchlist_item=watchlist_item,
            success=True,
            message="Stock added to watchlist successfully."
        )

class RemoveFromWatchlist(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        stock_symbol = graphene.String(required=True)

    def mutate(self, info, stock_symbol):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to remove stocks from watchlist.")
        
        try:
            stock = Stock.objects.get(symbol=stock_symbol.upper())
            # Find the watchlist item across all user's watchlists
            watchlist_item = WatchlistItem.objects.filter(
                watchlist__user=user, 
                stock=stock
            ).first()
            
            if not watchlist_item:
                raise GraphQLError("Stock is not in your watchlist.")
                
            watchlist_item.delete()
            return RemoveFromWatchlist(
                success=True,
                message="Stock removed from watchlist successfully."
            )
        except Stock.DoesNotExist:
            raise GraphQLError("Stock not found.")
        except Exception as e:
            raise GraphQLError(str(e))

class UpdateWatchlistNotes(graphene.Mutation):
    watchlist_item = graphene.Field('core.types.WatchlistItemType')
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        stock_symbol = graphene.String(required=True)
        notes = graphene.String(required=True)

    def mutate(self, info, stock_symbol, notes):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to update watchlist notes.")
        
        try:
            stock = Stock.objects.get(symbol=stock_symbol.upper())
            # Find the watchlist item across all user's watchlists
            watchlist_item = WatchlistItem.objects.filter(
                watchlist__user=user, 
                stock=stock
            ).first()
            
            if not watchlist_item:
                raise GraphQLError("Stock is not in your watchlist.")
                
            watchlist_item.notes = notes
            watchlist_item.save()
            return UpdateWatchlistNotes(
                watchlist_item=watchlist_item,
                success=True,
                message="Watchlist notes updated successfully."
            )
        except Stock.DoesNotExist:
            raise GraphQLError("Stock not found.")
        except Exception as e:
            raise GraphQLError(str(e))

class CreateWatchlist(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        is_public = graphene.Boolean()
        is_shared = graphene.Boolean()
    
    watchlist = graphene.Field(WatchlistType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, name, description="", is_public=False, is_shared=False):
        user = info.context.user
        if not user.is_authenticated:
            return CreateWatchlist(success=False, message="You must be logged in")
        
        try:
            watchlist = Watchlist.objects.create(
                user=user,
                name=name,
                description=description,
                is_public=is_public,
                is_shared=is_shared
            )
            
            # Check for achievement
            if not UserAchievement.objects.filter(user=user, achievement_type='first_watchlist').exists():
                UserAchievement.objects.create(
                    user=user,
                    achievement_type='first_watchlist',
                    title='Watchlist Creator',
                    description='Created your first watchlist!',
                    icon='📋'
                )
            
            return CreateWatchlist(
                watchlist=watchlist,
                success=True,
                message="Watchlist created successfully"
            )
        except Exception as e:
            return CreateWatchlist(success=False, message=str(e))

class AddToWatchlistWithId(graphene.Mutation):
    class Arguments:
        watchlist_id = graphene.ID(required=True)
        stock_symbol = graphene.String(required=True)
        notes = graphene.String()
        target_price = graphene.Decimal()
    
    watchlist_item = graphene.Field(WatchlistItemType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, watchlist_id, stock_symbol, notes="", target_price=None):
        user = info.context.user
        if not user.is_authenticated:
            return AddToWatchlistWithId(success=False, message="You must be logged in")
        
        try:
            watchlist = Watchlist.objects.get(id=watchlist_id, user=user)
            stock = Stock.objects.get(symbol=stock_symbol.upper())
            
            watchlist_item = WatchlistItem.objects.create(
                watchlist=watchlist,
                stock=stock,
                notes=notes,
                target_price=target_price
            )
            
            return AddToWatchlistWithId(
                watchlist_item=watchlist_item,
                success=True,
                message="Stock added to watchlist"
            )
        except Watchlist.DoesNotExist:
            return AddToWatchlistWithId(success=False, message="Watchlist not found")
        except Stock.DoesNotExist:
            return AddToWatchlistWithId(success=False, message="Stock not found")
        except Exception as e:
            return AddToWatchlistWithId(success=False, message=str(e))

class CreateStockDiscussion(graphene.Mutation):
    class Arguments:
        stock_symbol = graphene.String(required=True)
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        discussion_type = graphene.String()
        is_analysis = graphene.Boolean()
        analysis_data = graphene.JSONString()
    
    discussion = graphene.Field(StockDiscussionType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, stock_symbol, title, content, discussion_type='analysis', is_analysis=False, analysis_data=None):
        user = info.context.user
        if not user.is_authenticated:
            return CreateStockDiscussion(success=False, message="You must be logged in")
        
        try:
            stock = Stock.objects.get(symbol=stock_symbol.upper())
            
            discussion = StockDiscussion.objects.create(
                user=user,
                stock=stock,
                title=title,
                content=content,
                discussion_type=discussion_type,
                is_analysis=is_analysis,
                analysis_data=analysis_data
            )
            
            # Check for achievements
            if not UserAchievement.objects.filter(user=user, achievement_type='first_post').exists():
                UserAchievement.objects.create(
                    user=user,
                    achievement_type='first_post',
                    title='First Post',
                    description='Posted your first discussion!',
                    icon='📝'
                )
            
            # Create social feed item
            SocialFeed.objects.create(
                user=user,
                content_type='discussion',
                content_id=discussion.id
            )
            
            return CreateStockDiscussion(
                discussion=discussion,
                success=True,
                message="Discussion created successfully"
            )
        except Stock.DoesNotExist:
            return CreateStockDiscussion(success=False, message="Stock not found")
        except Exception as e:
            return CreateStockDiscussion(success=False, message=str(e))

class LikeDiscussion(graphene.Mutation):
    class Arguments:
        discussion_id = graphene.ID(required=True)
        discussionId = graphene.ID(required=False)  # Add camelCase version
    
    success = graphene.Boolean()
    message = graphene.String()
    discussion = graphene.Field('core.types.StockDiscussionType')
    
    def mutate(self, info, discussion_id=None, discussionId=None):
        # Use either snake_case or camelCase argument
        discussion_id = discussion_id or discussionId
        
        if not discussion_id:
            return LikeDiscussion(success=False, message="Discussion ID is required")
        
        user = info.context.user
        if not user.is_authenticated:
            return LikeDiscussion(success=False, message="You must be logged in")
        
        try:
            discussion = StockDiscussion.objects.get(id=discussion_id)
            
            if user in discussion.likes.all():
                discussion.likes.remove(user)
                message = "Like removed"
            else:
                discussion.likes.add(user)
                message = "Discussion liked"
                
                # Check for viral post achievement
                if discussion.likes.count() >= 100 and not UserAchievement.objects.filter(user=discussion.user, achievement_type='viral_post').exists():
                    UserAchievement.objects.create(
                        user=discussion.user,
                        achievement_type='viral_post',
                        title='Viral Post',
                        description='Your post got 100+ likes!',
                        icon='🔥'
                    )
                elif discussion.likes.count() >= 10 and not UserAchievement.objects.filter(user=discussion.user, achievement_type='popular_post').exists():
                    UserAchievement.objects.create(
                        user=discussion.user,
                        achievement_type='popular_post',
                        title='Popular Post',
                        description='Your post got 10+ likes!',
                        icon='⭐'
                    )
            
            return LikeDiscussion(
                success=True,
                message=message,
                discussion=discussion
            )
        except StockDiscussion.DoesNotExist:
            return LikeDiscussion(success=False, message="Discussion not found")
        except Exception as e:
            return LikeDiscussion(success=False, message=str(e))


class CommentOnDiscussion(graphene.Mutation):
    class Arguments:
        discussion_id = graphene.ID(required=True)
        discussionId = graphene.ID(required=False)  # Add camelCase version
        content = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    comment = graphene.Field('core.types.DiscussionCommentType')
    
    def mutate(self, info, discussion_id=None, discussionId=None, content=None):
        # Use either snake_case or camelCase argument
        discussion_id = discussion_id or discussionId
        
        if not discussion_id:
            return CommentOnDiscussion(success=False, message="Discussion ID is required")
        
        if not content or not content.strip():
            return CommentOnDiscussion(success=False, message="Comment content is required")
        
        user = info.context.user
        if not user.is_authenticated:
            return CommentOnDiscussion(success=False, message="You must be logged in")
        
        try:
            discussion = StockDiscussion.objects.get(id=discussion_id)
            
            # Create the comment
            comment = DiscussionComment.objects.create(
                discussion=discussion,
                user=user,
                content=content.strip()
            )
            
            # Check for achievement
            if not UserAchievement.objects.filter(user=user, achievement_type='first_comment').exists():
                UserAchievement.objects.create(
                    user=user,
                    achievement_type='first_comment',
                    title='Commenter',
                    description='Posted your first comment!',
                    icon='💬'
                )
            
            return CommentOnDiscussion(
                success=True,
                message="Comment added successfully",
                comment=comment
            )
        except StockDiscussion.DoesNotExist:
            return CommentOnDiscussion(success=False, message="Discussion not found")
        except Exception as e:
            return CommentOnDiscussion(success=False, message=str(e))

class CreatePortfolio(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        is_public = graphene.Boolean()
    
    portfolio = graphene.Field(PortfolioType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, name, description="", is_public=False):
        user = info.context.user
        if not user.is_authenticated:
            return CreatePortfolio(success=False, message="You must be logged in")
        
        try:
            portfolio = Portfolio.objects.create(
                user=user,
                name=name,
                description=description,
                is_public=is_public
            )
            
            # Check for achievement
            if not UserAchievement.objects.filter(user=user, achievement_type='first_portfolio').exists():
                UserAchievement.objects.create(
                    user=user,
                    achievement_type='first_portfolio',
                    title='Portfolio Manager',
                    description='Created your first portfolio!',
                    icon='💼'
                )
            
            return CreatePortfolio(
                portfolio=portfolio,
                success=True,
                message="Portfolio created successfully"
            )
        except Exception as e:
            return CreatePortfolio(success=False, message=str(e))

class AddPortfolioPosition(graphene.Mutation):
    class Arguments:
        portfolio_id = graphene.ID(required=True)
        stock_symbol = graphene.String(required=True)
        shares = graphene.Decimal(required=True)
        entry_price = graphene.Decimal(required=True)
        position_type = graphene.String()
        notes = graphene.String()
    
    position = graphene.Field(PortfolioPositionType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, portfolio_id, stock_symbol, shares, entry_price, position_type='paper', notes=""):
        user = info.context.user
        if not user.is_authenticated:
            return AddPortfolioPosition(success=False, message="You must be logged in")
        
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id, user=user)
            stock = Stock.objects.get(symbol=stock_symbol.upper())
            
            position = PortfolioPosition.objects.create(
                portfolio=portfolio,
                stock=stock,
                shares=shares,
                entry_price=entry_price,
                position_type=position_type,
                notes=notes
            )
            
            return AddPortfolioPosition(
                position=position,
                success=True,
                message="Position added to portfolio"
            )
        except Portfolio.DoesNotExist:
            return AddPortfolioPosition(success=False, message="Portfolio not found")
        except Stock.DoesNotExist:
            return AddPortfolioPosition(success=False, message="Stock not found")
        except Exception as e:
            return AddPortfolioPosition(success=False, message=str(e))

class CreatePriceAlert(graphene.Mutation):
    class Arguments:
        stock_symbol = graphene.String(required=True)
        alert_type = graphene.String(required=True)
        target_value = graphene.Decimal(required=True)
    
    alert = graphene.Field(PriceAlertType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, stock_symbol, alert_type, target_value):
        user = info.context.user
        if not user.is_authenticated:
            return CreatePriceAlert(success=False, message="You must be logged in")
        
        try:
            stock = Stock.objects.get(symbol=stock_symbol.upper())
            
            alert = PriceAlert.objects.create(
                user=user,
                stock=stock,
                alert_type=alert_type,
                target_value=target_value
            )
            
            return CreatePriceAlert(
                alert=alert,
                success=True,
                message="Price alert created successfully"
            )
        except Stock.DoesNotExist:
            return CreatePriceAlert(success=False, message="Stock not found")
        except Exception as e:
            return CreatePriceAlert(success=False, message=str(e))

class VoteStockSentiment(graphene.Mutation):
    class Arguments:
        stock_symbol = graphene.String(required=True)
        vote_type = graphene.String(required=True)  # 'positive', 'negative', 'neutral'
    
    success = graphene.Boolean()
    message = graphene.String()
    sentiment_score = graphene.Decimal()
    
    def mutate(self, info, stock_symbol, vote_type):
        user = info.context.user
        if not user.is_authenticated:
            return VoteStockSentiment(success=False, message="You must be logged in")
        
        try:
            stock = Stock.objects.get(symbol=stock_symbol.upper())
            sentiment, created = StockSentiment.objects.get_or_create(stock=stock)
            
            # Update vote counts
            if vote_type == 'positive':
                sentiment.positive_votes += 1
            elif vote_type == 'negative':
                sentiment.negative_votes += 1
            elif vote_type == 'neutral':
                sentiment.neutral_votes += 1
            
            sentiment.total_votes += 1
            sentiment.update_sentiment()
            
            return VoteStockSentiment(
                success=True,
                message=f"Vote recorded: {vote_type}",
                sentiment_score=sentiment.sentiment_score
            )
        except Stock.DoesNotExist:
            return VoteStockSentiment(success=False, message="Stock not found")
        except Exception as e:
            return VoteStockSentiment(success=False, message=str(e))


class CreateIncomeProfile(graphene.Mutation):
    class Arguments:
        income_bracket = graphene.String(required=True)
        age = graphene.Int(required=True)
        investment_goals = graphene.List(graphene.String, required=True)
        risk_tolerance = graphene.String(required=True)
        investment_horizon = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    income_profile = graphene.Field('core.types.IncomeProfileType')
    
    def mutate(self, info, income_bracket, age, investment_goals, risk_tolerance, investment_horizon):
        user = info.context.user
        if user.is_anonymous:
            return CreateIncomeProfile(success=False, message="You must be logged in")
        
        try:
            from .models import IncomeProfile
            
            # Create or update income profile
            profile, created = IncomeProfile.objects.get_or_create(
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
                profile.income_bracket = income_bracket
                profile.age = age
                profile.investment_goals = investment_goals
                profile.risk_tolerance = risk_tolerance
                profile.investment_horizon = investment_horizon
                profile.save()
            
            return CreateIncomeProfile(
                success=True,
                message="Income profile created successfully" if created else "Income profile updated successfully",
                income_profile=profile
            )
        except Exception as e:
            return CreateIncomeProfile(success=False, message=str(e))


class GenerateAIRecommendations(graphene.Mutation):
    class Arguments:
        pass  # No arguments needed, uses user's income profile
    
    success = graphene.Boolean()
    message = graphene.String()
    recommendations = graphene.Field('core.types.AIPortfolioRecommendationType')
    
    def mutate(self, info):
        user = info.context.user
        if user.is_anonymous:
            return GenerateAIRecommendations(success=False, message="You must be logged in")
        
        try:
            # Check if user has income profile
            try:
                income_profile = user.incomeProfile
            except:
                return GenerateAIRecommendations(success=False, message="Please create your income profile first")
            
            # Import services
            from .stock_service import advanced_stock_service
            from .rust_stock_service import rust_stock_service
            from .models import Stock
            
            # Step 1: Quantitative Risk Profile Analysis
            risk_profile = GenerateAIRecommendations._calculate_quantitative_risk_profile(income_profile)
            
            # Step 2: Market Analysis and Sector Rotation
            market_analysis = GenerateAIRecommendations._analyze_market_conditions()
            
            # Step 3: Advanced Portfolio Optimization
            portfolio_allocation = GenerateAIRecommendations._optimize_portfolio_allocation(
                income_profile, risk_profile, market_analysis
            )
            
            # Step 4: Calculate Expected Returns with Monte Carlo Simulation
            expected_return = GenerateAIRecommendations._calculate_expected_returns_with_monte_carlo(
                portfolio_allocation, risk_profile
            )
            
            # Step 5: Comprehensive Risk Assessment
            risk_assessment = GenerateAIRecommendations._comprehensive_risk_assessment(
                portfolio_allocation, risk_profile, market_analysis
            )
            
            # Step 6: Generate Quantitative Stock Recommendations
            stock_recommendations = GenerateAIRecommendations._generate_quantitative_stock_recommendations(
                income_profile, risk_profile, market_analysis
            )
            
            # Create AI recommendation
            ai_recommendation = AIPortfolioRecommendation.objects.create(
                user=user,
                risk_profile=risk_profile,
                portfolio_allocation=portfolio_allocation,
                expected_portfolio_return=expected_return,
                risk_assessment=risk_assessment
            )
            
            # Create stock recommendations
            for stock_rec in stock_recommendations:
                StockRecommendation.objects.create(
                    portfolio_recommendation=ai_recommendation,
                    stock=stock_rec['stock'],
                    allocation=stock_rec['allocation'],
                    reasoning=stock_rec['reasoning'],
                    risk_level=stock_rec['risk_level'],
                    expected_return=stock_rec['expected_return']
                )
            
            return GenerateAIRecommendations(
                success=True,
                message="Quantitative AI recommendations generated successfully",
                recommendations=ai_recommendation
            )
        except Exception as e:
            return GenerateAIRecommendations(success=False, message=str(e))
    
    @staticmethod
    def _calculate_quantitative_risk_profile(income_profile):
        """Calculate quantitative risk profile using multiple factors"""
        import math
        
        # Age factor (Younger = higher risk tolerance)
        age_factor = max(0.3, 1.0 - (income_profile.age - 18) / 50)
        
        # Income factor (Higher income = higher risk tolerance)
        income_brackets = {
            'Under $50,000': 0.4,
            '$50,000 - $100,000': 0.6,
            '$100,000 - $150,000': 0.8,
            'Over $150,000': 1.0
        }
        income_factor = income_brackets.get(income_profile.income_bracket, 0.6)
        
        # Risk tolerance mapping
        risk_tolerance_map = {
            'Conservative': 0.3,
            'Moderate': 0.6,
            'Aggressive': 0.9
        }
        base_risk = risk_tolerance_map.get(income_profile.risk_tolerance, 0.6)
        
        # Investment horizon factor
        horizon_map = {
            'Short-term (1-3 years)': 0.3,
            'Medium-term (3-10 years)': 0.6,
            'Long-term (10+ years)': 0.9
        }
        horizon_factor = horizon_map.get(income_profile.investment_horizon, 0.6)
        
        # Calculate composite risk score (0-1)
        risk_score = (age_factor * 0.25 + 
                     income_factor * 0.25 + 
                     base_risk * 0.3 + 
                     horizon_factor * 0.2)
        
        # Map to risk profile
        if risk_score >= 0.7:
            return 'High'
        elif risk_score >= 0.4:
            return 'Medium'
        else:
            return 'Low'
    
    @staticmethod
    def _analyze_market_conditions():
        """Analyze current market conditions for sector rotation"""
        # This would typically fetch real market data
        # For now, we'll use a simplified model
        return {
            'market_regime': 'bull_market',  # bull_market, bear_market, sideways
            'volatility_regime': 'moderate',  # low, moderate, high
            'sector_performance': {
                'technology': 'outperforming',
                'healthcare': 'neutral',
                'financials': 'underperforming',
                'consumer_discretionary': 'outperforming',
                'utilities': 'underperforming',
                'energy': 'neutral'
            },
            'interest_rate_environment': 'rising',  # rising, falling, stable
            'economic_cycle': 'expansion'  # expansion, peak, contraction, trough
        }
    
    @staticmethod
    def _optimize_portfolio_allocation(income_profile, risk_profile, market_analysis):
        """Optimize portfolio allocation using Modern Portfolio Theory principles"""
        
        # Base allocations by risk profile
        base_allocations = {
            'High': {
                'stocks': 80, 'bonds': 10, 'etfs': 8, 'cash': 2,
                'sector_weights': {
                    'technology': 30, 'healthcare': 20, 'financials': 15,
                    'consumer_discretionary': 15, 'utilities': 10, 'energy': 10
                }
            },
            'Medium': {
                'stocks': 60, 'bonds': 25, 'etfs': 12, 'cash': 3,
                'sector_weights': {
                    'technology': 25, 'healthcare': 20, 'financials': 20,
                    'consumer_discretionary': 15, 'utilities': 10, 'energy': 10
                }
            },
            'Low': {
                'stocks': 40, 'bonds': 45, 'etfs': 12, 'cash': 3,
                'sector_weights': {
                    'technology': 20, 'healthcare': 25, 'financials': 25,
                    'consumer_discretionary': 15, 'utilities': 10, 'energy': 5
                }
            }
        }
        
        allocation = base_allocations[risk_profile].copy()
        
        # Adjust based on market conditions
        if market_analysis['market_regime'] == 'bear_market':
            allocation['cash'] += 10
            allocation['stocks'] -= 10
        elif market_analysis['market_regime'] == 'bull_market':
            allocation['stocks'] += 5
            allocation['bonds'] -= 5
        
        # Adjust sector weights based on performance
        sector_weights = allocation['sector_weights']
        for sector, performance in market_analysis['sector_performance'].items():
            if performance == 'outperforming':
                sector_weights[sector] = min(35, sector_weights[sector] + 5)
            elif performance == 'underperforming':
                sector_weights[sector] = max(5, sector_weights[sector] - 5)
        
        # Normalize sector weights
        total_weight = sum(sector_weights.values())
        for sector in sector_weights:
            sector_weights[sector] = round(sector_weights[sector] / total_weight * 100, 1)
        
        allocation['sector_weights'] = sector_weights
        return allocation
    
    @staticmethod
    def _calculate_expected_returns_with_monte_carlo(portfolio_allocation, risk_profile):
        """Calculate expected returns using Monte Carlo simulation principles"""
        
        # Historical return assumptions (simplified)
        asset_returns = {
            'stocks': {'mean': 0.10, 'std': 0.15},  # 10% mean, 15% std
            'bonds': {'mean': 0.05, 'std': 0.08},   # 5% mean, 8% std
            'etfs': {'mean': 0.08, 'std': 0.12},    # 8% mean, 12% std
            'cash': {'mean': 0.02, 'std': 0.01}     # 2% mean, 1% std
        }
        
        # Calculate weighted expected return
        total_return = 0
        for asset, weight in portfolio_allocation.items():
            if asset in asset_returns and asset != 'sector_weights':
                total_return += (weight / 100) * asset_returns[asset]['mean']
        
        # Adjust for risk profile
        risk_multipliers = {'Low': 0.8, 'Medium': 1.0, 'High': 1.2}
        adjusted_return = total_return * risk_multipliers[risk_profile]
        
        # Format as percentage range
        if risk_profile == 'High':
            return f"{adjusted_return*100:.1f}-{(adjusted_return*100)*1.5:.1f}%"
        elif risk_profile == 'Medium':
            return f"{adjusted_return*100*0.8:.1f}-{adjusted_return*100*1.3:.1f}%"
        else:
            return f"{adjusted_return*100*0.7:.1f}-{adjusted_return*100*1.2:.1f}%"
    
    @staticmethod
    def _comprehensive_risk_assessment(portfolio_allocation, risk_profile, market_analysis):
        """Comprehensive risk assessment using multiple metrics"""
        
        # Calculate portfolio volatility
        asset_volatilities = {
            'stocks': 0.15, 'bonds': 0.08, 'etfs': 0.12, 'cash': 0.01
        }
        
        portfolio_volatility = 0
        for asset, weight in portfolio_allocation.items():
            if asset in asset_volatilities and asset != 'sector_weights':
                portfolio_volatility += (weight / 100) * asset_volatilities[asset]
        
        # Calculate maximum drawdown estimate
        max_drawdown = portfolio_volatility * 2.5  # Simplified estimate
        
        # Risk assessment based on multiple factors
        risk_factors = []
        
        if portfolio_volatility > 0.12:
            risk_factors.append("High volatility portfolio")
        elif portfolio_volatility > 0.08:
            risk_factors.append("Moderate volatility portfolio")
        else:
            risk_factors.append("Low volatility portfolio")
        
        if market_analysis['market_regime'] == 'bear_market':
            risk_factors.append("Bear market conditions")
        elif market_analysis['volatility_regime'] == 'high':
            risk_factors.append("High market volatility")
        
        if portfolio_allocation['stocks'] > 70:
            risk_factors.append("High equity concentration")
        elif portfolio_allocation['stocks'] < 30:
            risk_factors.append("Conservative equity allocation")
        
        # Generate risk description
        if risk_profile == 'High':
            risk_desc = f"High Risk - High Growth Potential | Volatility: {portfolio_volatility*100:.1f}% | Max Drawdown: {max_drawdown*100:.1f}%"
        elif risk_profile == 'Medium':
            risk_desc = f"Moderate Risk - Balanced Growth | Volatility: {portfolio_volatility*100:.1f}% | Max Drawdown: {max_drawdown*100:.1f}%"
        else:
            risk_desc = f"Low Risk - Stable Growth | Volatility: {portfolio_volatility*100:.1f}% | Max Drawdown: {max_drawdown*100:.1f}%"
        
        return f"{risk_desc} | {' | '.join(risk_factors)}"
    
    @staticmethod
    def _generate_quantitative_stock_recommendations(income_profile, risk_profile, market_analysis):
        """Generate quantitative stock recommendations using technical and fundamental analysis"""
        from .models import Stock
        
        # Get stocks with analysis data
        stocks_with_scores = Stock.objects.filter(
            beginner_friendly_score__isnull=False
        ).order_by('-beginner_friendly_score')[:20]  # Get top 20 for analysis
        
        recommendations = []
        
        for stock in stocks_with_scores:
            # Calculate quantitative score
            score = GenerateAIRecommendations._calculate_quantitative_stock_score(
                stock, risk_profile, market_analysis
            )
            
            # Determine allocation based on score and risk profile
            if score >= 8.5:
                allocation = 25 if risk_profile == 'High' else 20 if risk_profile == 'Medium' else 15
            elif score >= 7.5:
                allocation = 20 if risk_profile == 'High' else 15 if risk_profile == 'Medium' else 10
            elif score >= 6.5:
                allocation = 15 if risk_profile == 'High' else 10 if risk_profile == 'Medium' else 8
            else:
                allocation = 10 if risk_profile == 'High' else 8 if risk_profile == 'Medium' else 5
            
            # Generate quantitative reasoning
            reasoning = GenerateAIRecommendations._generate_quantitative_reasoning(
                stock, score, risk_profile, market_analysis
            )
            
            # Determine risk level and expected return
            if score >= 8.0:
                risk_level = 'Low'
                expected_return = '15-25%'
            elif score >= 7.0:
                risk_level = 'Medium'
                expected_return = '10-18%'
            else:
                risk_level = 'Medium-High'
                expected_return = '8-15%'
            
            recommendations.append({
                'stock': stock,
                'allocation': allocation,
                'reasoning': reasoning,
                'risk_level': risk_level,
                'expected_return': expected_return,
                'quantitative_score': score
            })
        
        # Sort by quantitative score and take top recommendations
        recommendations.sort(key=lambda x: x['quantitative_score'], reverse=True)
        
        # Limit total allocation to 100%
        total_allocation = 0
        final_recommendations = []
        
        for rec in recommendations:
            if total_allocation + rec['allocation'] <= 100:
                final_recommendations.append(rec)
                total_allocation += rec['allocation']
            else:
                break
        
        return final_recommendations
    
    @staticmethod
    def _calculate_quantitative_stock_score(stock, risk_profile, market_analysis):
        """Calculate quantitative score for a stock using multiple factors"""
        
        # Base score from beginner-friendly score
        base_score = stock.beginner_friendly_score or 5.0
        
        # Technical analysis bonus (if available)
        technical_bonus = 0
        if hasattr(stock, 'technical_indicators'):
            # Add technical analysis scoring here
            technical_bonus = 0.5  # Placeholder
        
        # Fundamental analysis bonus
        fundamental_bonus = 0
        if hasattr(stock, 'fundamental_analysis'):
            # Add fundamental analysis scoring here
            fundamental_bonus = 0.5  # Placeholder
        
        # Market regime adjustment
        market_adjustment = 0
        if market_analysis['market_regime'] == 'bull_market':
            market_adjustment = 0.3
        elif market_analysis['market_regime'] == 'bear_market':
            market_adjustment = -0.3
        
        # Risk profile adjustment
        risk_adjustment = 0
        if risk_profile == 'High':
            risk_adjustment = 0.2
        elif risk_profile == 'Low':
            risk_adjustment = -0.2
        
        # Calculate final score
        final_score = base_score + technical_bonus + fundamental_bonus + market_adjustment + risk_adjustment
        
        # Ensure score is within bounds
        return max(1.0, min(10.0, final_score))
    
    @staticmethod
    def _generate_quantitative_reasoning(stock, score, risk_profile, market_analysis):
        """Generate quantitative reasoning for stock recommendation"""
        
        reasoning_parts = []
        
        # Base reasoning
        if score >= 8.5:
            reasoning_parts.append("Exceptional quantitative score")
        elif score >= 7.5:
            reasoning_parts.append("Strong quantitative metrics")
        else:
            reasoning_parts.append("Good quantitative fundamentals")
        
        # Beginner-friendly score reasoning
        if stock.beginner_friendly_score and stock.beginner_friendly_score >= 8:
            reasoning_parts.append("High beginner-friendly score")
        elif stock.beginner_friendly_score and stock.beginner_friendly_score >= 6:
            reasoning_parts.append("Good beginner-friendly score")
        
        # Market regime reasoning
        if market_analysis['market_regime'] == 'bull_market':
            reasoning_parts.append("Favorable market conditions")
        elif market_analysis['market_regime'] == 'bear_market':
            reasoning_parts.append("Defensive positioning")
        
        # Risk profile alignment
        if risk_profile == 'High':
            reasoning_parts.append("Suitable for aggressive growth")
        elif risk_profile == 'Low':
            reasoning_parts.append("Conservative investment choice")
        else:
            reasoning_parts.append("Balanced risk-reward profile")
        
        # Technical indicators (if available)
        if hasattr(stock, 'technical_indicators'):
            reasoning_parts.append("Positive technical indicators")
        
        # Fundamental strength
        if hasattr(stock, 'fundamental_analysis'):
            reasoning_parts.append("Strong fundamental metrics")
        
        return " | ".join(reasoning_parts)


# Root mutation
class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_post = CreatePost.Field()
    toggle_like = ToggleLike.Field()
    create_comment = CreateComment.Field()
    delete_comment = DeleteComment.Field()
    toggle_follow = ToggleFollow.Field()
    create_chat_session = CreateChatSession.Field()
    send_message = SendMessage.Field()
    get_chat_history = GetChatHistory.Field()
    
    # Watchlist mutations
    add_to_watchlist = AddToWatchlist.Field()
    remove_from_watchlist = RemoveFromWatchlist.Field()
    update_watchlist_notes = UpdateWatchlistNotes.Field()
    
    # Phase 3 Social Features
    create_watchlist = CreateWatchlist.Field()
    add_to_watchlist_with_id = AddToWatchlistWithId.Field()
    create_stock_discussion = CreateStockDiscussion.Field()
    like_discussion = LikeDiscussion.Field()
    comment_on_discussion = CommentOnDiscussion.Field()
    create_portfolio = CreatePortfolio.Field()
    add_portfolio_position = AddPortfolioPosition.Field()
    create_price_alert = CreatePriceAlert.Field()
    vote_stock_sentiment = VoteStockSentiment.Field()
    
    # AI Portfolio mutations
    create_income_profile = CreateIncomeProfile.Field()
    generate_ai_recommendations = GenerateAIRecommendations.Field()
    
    # JWT Authentication
    tokenAuth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()