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
    
    success = graphene.Boolean()
    message = graphene.String()
    like_count = graphene.Int()
    
    def mutate(self, info, discussion_id):
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
                like_count=discussion.likes.count()
            )
        except StockDiscussion.DoesNotExist:
            return LikeDiscussion(success=False, message="Discussion not found")
        except Exception as e:
            return LikeDiscussion(success=False, message=str(e))

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
            
            # Generate AI recommendations based on profile
            risk_profile = GenerateAIRecommendations._determine_risk_profile(income_profile)
            portfolio_allocation = GenerateAIRecommendations._generate_portfolio_allocation(income_profile, risk_profile)
            expected_return = GenerateAIRecommendations._calculate_expected_return(income_profile, risk_profile)
            risk_assessment = GenerateAIRecommendations._assess_risk(income_profile, risk_profile)
            
            # Create AI recommendation
            ai_recommendation = AIPortfolioRecommendation.objects.create(
                user=user,
                risk_profile=risk_profile,
                portfolio_allocation=portfolio_allocation,
                expected_portfolio_return=expected_return,
                risk_assessment=risk_assessment
            )
            
            # Generate stock recommendations
            GenerateAIRecommendations._generate_stock_recommendations(ai_recommendation, income_profile, risk_profile)
            
            return GenerateAIRecommendations(
                success=True,
                message="AI recommendations generated successfully",
                recommendations=ai_recommendation
            )
        except Exception as e:
            return GenerateAIRecommendations(success=False, message=str(e))
    
    @staticmethod
    def _determine_risk_profile(income_profile):
        """Determine risk profile based on income profile"""
        age_factor = 1.0 if income_profile.age < 30 else 0.8 if income_profile.age < 50 else 0.6
        income_factor = 1.0 if 'Over $150,000' in income_profile.income_bracket else 0.8 if '$100,000' in income_profile.income_bracket else 0.6
        
        if income_profile.risk_tolerance == 'Aggressive':
            base_risk = 'High'
        elif income_profile.risk_tolerance == 'Moderate':
            base_risk = 'Medium'
        else:
            base_risk = 'Low'
        
        # Adjust based on age and income
        if age_factor < 0.7 and base_risk == 'High':
            return 'Medium'
        elif age_factor < 0.7 and base_risk == 'Medium':
            return 'Low'
        else:
            return base_risk
    
    @staticmethod
    def _generate_portfolio_allocation(income_profile, risk_profile):
        """Generate portfolio allocation based on risk profile"""
        if risk_profile == 'High':
            return {'stocks': 80, 'bonds': 15, 'etfs': 5, 'cash': 0}
        elif risk_profile == 'Medium':
            return {'stocks': 60, 'bonds': 30, 'etfs': 10, 'cash': 0}
        else:
            return {'stocks': 40, 'bonds': 50, 'etfs': 10, 'cash': 0}
    
    @staticmethod
    def _calculate_expected_return(income_profile, risk_profile):
        """Calculate expected portfolio return"""
        if risk_profile == 'High':
            return '12-18%'
        elif risk_profile == 'Medium':
            return '8-12%'
        else:
            return '5-8%'
    
    @staticmethod
    def _assess_risk(income_profile, risk_profile):
        """Assess overall portfolio risk"""
        if risk_profile == 'High':
            return 'High Risk - High Growth Potential'
        elif risk_profile == 'Medium':
            return 'Moderate Risk - Balanced Growth'
        else:
            return 'Low Risk - Stable Growth'
    
    @staticmethod
    def _generate_stock_recommendations(ai_recommendation, income_profile, risk_profile):
        """Generate specific stock recommendations"""
        from .models import Stock
        
        # Get top stocks based on beginner-friendly score
        top_stocks = Stock.objects.filter(
            beginner_friendly_score__isnull=False
        ).order_by('-beginner_friendly_score')[:5]
        
        # Create stock recommendations
        for i, stock in enumerate(top_stocks):
            allocation = 20 if i < 3 else 10  # Top 3 stocks get 20%, others get 10%
            reasoning = f"High beginner-friendly score ({stock.beginner_friendly_score}) and strong fundamentals"
            risk_level = 'Low' if stock.beginner_friendly_score > 7 else 'Medium'
            expected_return = '15-25%' if stock.beginner_friendly_score > 7 else '10-15%'
            
            StockRecommendation.objects.create(
                portfolio_recommendation=ai_recommendation,
                stock=stock,
                allocation=allocation,
                reasoning=reasoning,
                risk_level=risk_level,
                expected_return=expected_return
            )


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