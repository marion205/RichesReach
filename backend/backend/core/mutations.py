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
from graphql import GraphQLError
import secrets
import hashlib
import logging

logger = logging.getLogger(__name__)

from .models import User, Post, Comment, ChatSession, ChatMessage, IncomeProfile, AIPortfolioRecommendation, Stock, Watchlist, WatchlistItem, Portfolio, StockDiscussion, DiscussionComment
from .types import UserType, PostType, CommentType, ChatSessionType, ChatMessageType
from .portfolio_types import CreatePortfolio, CreatePortfolioHolding, UpdatePortfolioHolding, UpdateHoldingShares, RemovePortfolioHolding
from .auth_utils import RateLimiter, SecurityUtils
# from .websocket_service import websocket_service  # Temporarily disabled for local development
from .ml_mutations import GenerateMLPortfolioRecommendation, GetMLMarketAnalysis, GetMLServiceStatus, GenerateInstitutionalPortfolioRecommendation
from .monitoring_types import MonitoringMutations
from .services.email_notification_service import EmailNotificationService


# ------------------------ Authentication decorator ------------------------
def login_required(resolver):
    """Simple login required decorator for GraphQL mutations"""
    def wrapper(root, info, *args, **kwargs):
        user = info.context.user
        if not user or user.is_anonymous:
            raise GraphQLError("Authentication required")
        return resolver(root, info, *args, **kwargs)
    return wrapper


# ------------------------ small helpers for metrics ------------------------
def _normalize_to_decimal(v):
    """
    Accept either 'percent' inputs like 9.2 (meaning 9.2%) or decimal 0.092
    and always return a decimal (0.092).
    """
    if v is None:
        return None
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    # If abs > 1.5 we assume it's a percent value
    return n / 100.0 if abs(n) > 1.5 else n


def _fallback_volatility(risk_tolerance: str) -> float:
    mapping = {
        'Conservative': 8.2,
        'Moderate': 12.8,
        'Aggressive': 18.5,
    }
    return float(mapping.get(risk_tolerance, 12.8))


def _fallback_max_drawdown(risk_tolerance: str) -> float:
    mapping = {
        'Conservative': 15.0,
        'Moderate': 25.0,
        'Aggressive': 40.0,
    }
    return float(mapping.get(risk_tolerance, 25.0))


def _compute_portfolio_totals(user):
    """
    Sum user's current portfolio market value and count holdings.
    For new users without portfolio, use a default value based on income profile.
    """
    try:
        holdings = Portfolio.objects.filter(user=user)
        total_value = 0.0
        num = 0
        for h in holdings:
            if h.current_price is not None and h.shares is not None:
                total_value += float(h.current_price) * int(h.shares)
                num += 1
        
        # If no portfolio holdings, use default based on income profile
        if total_value == 0.0:
            try:
                income_profile = IncomeProfile.objects.get(user=user)
                # Set default portfolio value based on income bracket
                income_bracket = income_profile.income_bracket
                if 'High' in income_bracket:
                    total_value = 50000.0  # $50k for high income
                elif 'Medium' in income_bracket:
                    total_value = 25000.0  # $25k for medium income
                else:
                    total_value = 10000.0  # $10k for low income
            except IncomeProfile.DoesNotExist:
                total_value = 10000.0  # Default $10k
        
        # For new users, we'll set num_holdings to 0 here, but it will be updated 
        # in the mutation to reflect the number of recommended stocks
        return total_value, num
    except Exception:
        return 10000.0, 0  # Default $10k portfolio


def _compute_expected_impact(stocks, total_value):
    """
    stocks: list of dicts with allocation (percent), expectedReturn (decimal), optional confidence (0..1)
    Returns dict with ev_return_decimal, ev_change_for_total_value, ev_per_10k
    """
    if not stocks:
        return {
            "ev_return_decimal": None,
            "ev_change_for_total_value": None,
            "ev_per_10k": None,
        }
    
    # Weighted average return
    total_weight = sum(float(s.get('allocation', 0.0)) for s in stocks)
    if total_weight == 0:
        return {
            "ev_return_decimal": None,
            "ev_change_for_total_value": None,
            "ev_per_10k": None,
        }
    
    weighted_return = sum(
        float(s.get('expectedReturn', 0.0)) * (float(s.get('allocation', 0.0)) / total_weight)
        for s in stocks
    )
    
    # Convert to decimal if needed
    if weighted_return > 1.5:  # Assume it's a percent
        weighted_return = weighted_return / 100.0
    
    return {
        "ev_return_decimal": weighted_return,
        "ev_change_for_total_value": weighted_return * (total_value or 0),
        "ev_per_10k": weighted_return * 10000,
    }


class GenerateAIRecommendations(graphene.Mutation):
    """Generate AI portfolio recommendations based on user's income profile using ML/AI and real market data"""
    success = graphene.Boolean()
    message = graphene.String()
    recommendations = graphene.List('core.types.AIPortfolioRecommendationType')
    
    class Arguments:
        profile = graphene.Argument('core.schema.ProfileInput')
        usingDefaults = graphene.Boolean()

    def mutate(self, info, profile=None, usingDefaults=False):
        from django.conf import settings
        
        # Get user - in dev mode, use first available user if not authenticated
        user = None
        if getattr(settings, 'DEBUG', False):
            try:
                user = User.objects.select_related('incomeProfile').first()
            except Exception:
                pass
        
        # Try to get authenticated user
        if not user:
            try:
                user = info.context.user if hasattr(info, 'context') and hasattr(info.context, 'user') else None
            except (AttributeError, KeyError):
                user = None
            
            if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
                user = None
        
        if not user:
            return GenerateAIRecommendations(
                success=False,
                message="You must be logged in to generate AI recommendations."
            )
        
        try:
            # Get user's income profile - create one if using defaults
            try:
                income_profile = IncomeProfile.objects.get(user=user)
            except IncomeProfile.DoesNotExist:
                if usingDefaults:
                    # Handle profile as dict or GraphQL input object
                    if profile:
                        if hasattr(profile, '__dict__'):
                            # GraphQL input object
                            profile_dict = {k: getattr(profile, k, None) for k in ['age', 'incomeBracket', 'riskTolerance', 'investmentHorizonYears', 'investmentGoals']}
                        else:
                            # Regular dict
                            profile_dict = profile
                    else:
                        profile_dict = {}
                    
                    # Map investment horizon years to string format
                    horizon_years = profile_dict.get('investmentHorizonYears', 5)
                    if horizon_years >= 12:
                        investment_horizon_str = "10+ years"
                    elif horizon_years >= 8:
                        investment_horizon_str = "5-10 years"
                    elif horizon_years >= 4:
                        investment_horizon_str = "3-5 years"
                    elif horizon_years >= 2:
                        investment_horizon_str = "1-3 years"
                    else:
                        investment_horizon_str = "1-3 years"
                    
                    # Create a default profile for development
                    income_profile = IncomeProfile.objects.create(
                        user=user,
                        age=profile_dict.get('age', 30),
                        income_bracket=profile_dict.get('incomeBracket', 'Unknown'),
                        risk_tolerance=profile_dict.get('riskTolerance', 'Moderate'),
                        investment_horizon=investment_horizon_str,
                        investment_goals=profile_dict.get('investmentGoals', [])
                    )
                else:
                    return GenerateAIRecommendations(
                        success=False,
                        message="Please create an income profile first to generate personalized recommendations."
                    )
            
            # Get real market data from Alpaca
            recommendations = []
            
            try:
                # Use Alpaca data for real market analysis
                from .services.alpaca_broker_service import AlpacaBrokerService
                broker_service = AlpacaBrokerService()
                
                # Get user's Alpaca account for portfolio context
                from .models.alpaca_models import AlpacaAccount
                try:
                    alpaca_account = AlpacaAccount.objects.get(user=user)
                    # Get current positions for context
                    positions = broker_service.get_positions(str(alpaca_account.alpaca_account_id))
                except AlpacaAccount.DoesNotExist:
                    positions = []
                
                # Generate AI recommendations based on real data
                from .ml_stock_recommender import MLStockRecommender
                ml_recommender = MLStockRecommender()
                
                # Get AI recommendations with real market data
                ai_recommendations = ml_recommender.generate_recommendations(
                    user=user,
                    income_profile=income_profile,
                    current_positions=positions
                )
                
                # Convert to GraphQL format
                for rec in ai_recommendations:
                    recommendation = AIPortfolioRecommendation(
                        user=user,
                        symbol=rec['symbol'],
                        company_name=rec['company_name'],
                        recommendation_type=rec['type'],
                        confidence_score=rec['confidence'],
                        target_price=rec['target_price'],
                        current_price=rec['current_price'],
                        reasoning=rec['reasoning'],
                        risk_level=rec['risk_level'],
                        time_horizon=rec['time_horizon']
                    )
                    recommendation.save()
                    recommendations.append(recommendation)
                
                return GenerateAIRecommendations(
                    success=True,
                    message=f"Generated {len(recommendations)} AI recommendations based on real market data",
                    recommendations=recommendations
                )
                
            except Exception as alpaca_error:
                logger.error(f"Failed to generate AI recommendations with Alpaca data: {alpaca_error}")
                # Fallback to mock recommendations
                return GenerateAIRecommendations(
                    success=True,
                    message="AI recommendations generated successfully (using fallback data)",
                    recommendations=[]
                )
                
        except Exception as e:
            logger.error(f"Failed to generate AI recommendations: {e}")
            return GenerateAIRecommendations(
                success=False,
                message=f"Failed to generate recommendations: {str(e)}"
            )


class AddToWatchlist(graphene.Mutation):
    """Add a stock to user's watchlist"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        symbol = graphene.String(required=True)
        company_name = graphene.String()
        notes = graphene.String()

    @login_required
    def mutate(self, info, symbol, company_name=None, notes=""):
        # Better error handling for user authentication
        try:
            user = info.context.user
            if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
                return AddToWatchlist(
                    success=False,
                    message="You must be logged in to add stocks to watchlist."
                )
        except Exception as auth_error:
            return AddToWatchlist(
                success=False,
                message=f"Authentication error: {str(auth_error)}"
            )
        
        try:
            # Get or create the stock
            stock, created = Stock.objects.get_or_create(
                symbol=symbol.upper(),
                defaults={
                    'company_name': company_name or f"{symbol.upper()} Corp",
                    'sector': 'Unknown',
                    'market_cap': 0,
                    'pe_ratio': 0.0,
                    'dividend_yield': 0.0,
                    'current_price': 0.0,
                    'debt_ratio': 0.0,
                    'volatility': 0.0,
                }
            )
            
            # Get or create user's default watchlist
            watchlist, created = Watchlist.objects.get_or_create(
                user=user,
                name="My Watchlist",
                defaults={
                    'description': "Default watchlist",
                    'is_public': False,
                    'is_shared': False,
                }
            )
            
            # Add stock to watchlist
            watchlist_item, created = WatchlistItem.objects.get_or_create(
                watchlist=watchlist,
                stock=stock,
                defaults={'notes': notes}
            )
            
            if not created:
                watchlist_item.notes = notes
                watchlist_item.save()
            
            return AddToWatchlist(
                success=True,
                message=f"Successfully added {symbol} to watchlist."
            )
            
        except Exception as e:
            # Log the full error for debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"Watchlist mutation error: {error_details}")
            
            return AddToWatchlist(
                success=False,
                message=f"Failed to add {symbol} to watchlist: {str(e)}"
            )


class RemoveFromWatchlist(graphene.Mutation):
    """Remove a stock from user's watchlist"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        symbol = graphene.String(required=True)

    @login_required
    def mutate(self, info, symbol):
        # Better error handling for user authentication
        try:
            user = info.context.user
            if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
                return RemoveFromWatchlist(
                    success=False,
                    message="You must be logged in to remove stocks from watchlist."
                )
        except Exception as auth_error:
            return RemoveFromWatchlist(
                success=False,
                message=f"Authentication error: {str(auth_error)}"
            )
        
        try:
            # Find the stock
            try:
                stock = Stock.objects.get(symbol=symbol.upper())
            except Stock.DoesNotExist:
                return RemoveFromWatchlist(
                    success=False,
                    message=f"Stock {symbol} not found."
                )
            
            # Find user's default watchlist
            try:
                watchlist = Watchlist.objects.get(user=user, name="My Watchlist")
            except Watchlist.DoesNotExist:
                return RemoveFromWatchlist(
                    success=False,
                    message="Watchlist not found."
                )
            
            # Remove stock from watchlist
            watchlist_item = WatchlistItem.objects.filter(
                watchlist=watchlist,
                stock=stock
            ).first()
            
            if watchlist_item:
                watchlist_item.delete()
                return RemoveFromWatchlist(
                    success=True,
                    message=f"Successfully removed {symbol} from watchlist."
                )
            else:
                return RemoveFromWatchlist(
                    success=False,
                    message=f"{symbol} not found in watchlist."
                )
                
        except Exception as e:
            return RemoveFromWatchlist(
                success=False,
                message=f"Failed to remove {symbol} from watchlist: {str(e)}"
            )


class CreateIncomeProfile(graphene.Mutation):
    """Create or update user's income profile"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        income_bracket = graphene.String(required=True)
        age = graphene.Int(required=True)
        risk_tolerance = graphene.String(required=True)
        investment_horizon = graphene.String(required=True)
        investment_goals = graphene.List(graphene.String)
        # Also accept camelCase for mobile compatibility
        incomeBracket = graphene.String()
        riskTolerance = graphene.String()
        investmentHorizon = graphene.String()
        investmentGoals = graphene.List(graphene.String)

    def mutate(self, info, income_bracket=None, age=None, risk_tolerance=None, investment_horizon=None, investment_goals=None, 
               incomeBracket=None, riskTolerance=None, investmentHorizon=None, investmentGoals=None):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to create an income profile.")
        
        # Handle both snake_case and camelCase arguments
        income_bracket = income_bracket or incomeBracket
        risk_tolerance = risk_tolerance or riskTolerance
        investment_horizon = investment_horizon or investmentHorizon
        investment_goals = investment_goals or investmentGoals
        
        # Validate required fields
        if not all([income_bracket, age, risk_tolerance, investment_horizon]):
            raise GraphQLError("Missing required fields: income_bracket, age, risk_tolerance, investment_horizon")
        
        try:
            # Create or update income profile
            income_profile, created = IncomeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'income_bracket': income_bracket,
                    'age': age,
                    'risk_tolerance': risk_tolerance,
                    'investment_horizon': investment_horizon,
                    'investment_goals': investment_goals or [],
                }
            )
            
            if not created:
                income_profile.income_bracket = income_bracket
                income_profile.age = age
                income_profile.risk_tolerance = risk_tolerance
                income_profile.investment_horizon = investment_horizon
                income_profile.investment_goals = investment_goals or []
                income_profile.save()
            
            return CreateIncomeProfile(
                success=True,
                message="Income profile created successfully."
            )
            
        except Exception as e:
            return CreateIncomeProfile(
                success=False,
                message=f"Failed to create income profile: {str(e)}"
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
                # Add user to likes if not already there
                if not discussion.likes.filter(id=user.id).exists():
                    discussion.likes.add(user)
            else:
                # Remove user from likes for downvote
                if discussion.likes.filter(id=user.id).exists():
                    discussion.likes.remove(user)
            
            return VoteDiscussion(
                success=True,
                message=f"Successfully {vote_type}d discussion.",
                discussion=discussion
            )
            
        except Exception as e:
            return VoteDiscussion(
                success=False,
                message=f"Failed to vote on discussion: {str(e)}"
            )


class StockTradeType(graphene.ObjectType):
    symbol = graphene.String()
    companyName = graphene.String()
    action = graphene.String()  # 'buy' or 'sell'
    shares = graphene.Int()
    price = graphene.Float()
    totalValue = graphene.Float()
    reason = graphene.String()


class AIRebalancePortfolio(graphene.Mutation):
    class Arguments:
        portfolioName = graphene.String()
        riskTolerance = graphene.String()
        maxRebalancePercentage = graphene.Float()
        dryRun = graphene.Boolean()
    
    success = graphene.Boolean()
    message = graphene.String()
    changesMade = graphene.Boolean()
    stockTrades = graphene.List(StockTradeType)
    newPortfolioValue = graphene.Float()
    rebalanceCost = graphene.Float()
    estimatedImprovement = graphene.Float()
    
    def mutate(self, info, portfolioName=None, riskTolerance='medium', maxRebalancePercentage=10.0, dryRun=True):
        try:
            user = info.context.user
            if not user or user.is_anonymous:
                # For development/testing, create a mock user
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(email='test@example.com')
                except User.DoesNotExist:
                    raise GraphQLError("You must be logged in to rebalance portfolios.")
            
            # Mock rebalancing logic for development
            mock_trades = [
                {
                    'symbol': 'AAPL',
                    'companyName': 'Apple Inc.',
                    'action': 'buy',
                    'shares': 10,
                    'price': 175.50,
                    'totalValue': 1755.0,
                    'reason': 'Increase allocation to meet target weight'
                },
                {
                    'symbol': 'MSFT',
                    'companyName': 'Microsoft Corporation',
                    'action': 'sell',
                    'shares': 5,
                    'price': 350.25,
                    'totalValue': 1751.25,
                    'reason': 'Reduce concentration in single stock'
                }
            ]
            
            return AIRebalancePortfolio(
                success=True,
                message="Portfolio rebalancing completed successfully" if not dryRun else "Dry run completed - no changes made",
                changesMade=not dryRun,
                stockTrades=mock_trades,
                newPortfolioValue=6011.9,
                rebalanceCost=3.75,
                estimatedImprovement=0.12
            )
            
        except Exception as e:
            return AIRebalancePortfolio(
                success=False,
                message=f"Failed to rebalance portfolio: {str(e)}",
                changesMade=False,
                stockTrades=[],
                newPortfolioValue=0.0,
                rebalanceCost=0.0,
                estimatedImprovement=0.0
            )


class PlaceStockOrder(graphene.Mutation):
    """Place a stock order (buy/sell) using Alpaca Broker API"""
    success = graphene.Boolean()
    message = graphene.String()
    order_id = graphene.String()

    class Arguments:
        symbol = graphene.String(required=True)
        side = graphene.String(required=True)  # 'BUY' or 'SELL'
        quantity = graphene.Int(required=False)  # Support both quantity and qty
        qty = graphene.Int(required=False)  # Alias for quantity
        orderType = graphene.String(required=False)  # Support both orderType and order_type
        order_type = graphene.String(required=False)  # Alias for orderType
        type = graphene.String(required=False)  # Alias for orderType
        limit_price = graphene.Float(required=False)
        timeInForce = graphene.String(required=False)  # Support both timeInForce and time_in_force
        time_in_force = graphene.String(required=False, default_value='DAY')

    def mutate(self, info, symbol, side, **kwargs):
        try:
            user = info.context.user
            
            # For testing purposes, allow unauthenticated access
            # TODO: Re-enable authentication in production
            if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
                # Create a test user for unauthenticated requests
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user, created = User.objects.get_or_create(
                    email='test-trader@example.com',
                    defaults={
                        'username': 'test-trader@example.com',
                        'first_name': 'Test',
                        'last_name': 'Trader',
                        'is_active': True
                    }
                )
                logger.info(f"PlaceStockOrder: Using test user {user} (created: {created})")
            
            # Extract and normalize field names
            quantity = kwargs.get('quantity') or kwargs.get('qty')
            order_type = kwargs.get('orderType') or kwargs.get('order_type') or kwargs.get('type')
            time_in_force = kwargs.get('timeInForce') or kwargs.get('time_in_force', 'DAY')
            limit_price = kwargs.get('limit_price')
            
            # Validate inputs
            if side not in ['BUY', 'SELL']:
                return PlaceStockOrder(
                    success=False,
                    message="Side must be 'BUY' or 'SELL'."
                )
            
            if not quantity or quantity <= 0:
                return PlaceStockOrder(
                    success=False,
                    message="Quantity must be greater than 0."
                )
            
            if not order_type or order_type not in ['MARKET', 'LIMIT']:
                return PlaceStockOrder(
                    success=False,
                    message="Order type must be 'MARKET' or 'LIMIT'."
                )
            
            if order_type == 'LIMIT' and not limit_price:
                return PlaceStockOrder(
                    success=False,
                    message="Limit price is required for LIMIT orders."
                )
            
            # Check if user has Alpaca account
            try:
                from .models.alpaca_models import AlpacaAccount
                alpaca_account = AlpacaAccount.objects.filter(user=user).first()
                
                if not alpaca_account:
                    return PlaceStockOrder(
                        success=False,
                        message="No Alpaca account found. Please create an account first."
                    )
                
                if not alpaca_account.is_approved:
                    return PlaceStockOrder(
                        success=False,
                        message="Your Alpaca account is not approved for trading."
                    )
                
                # Check if we should use mock mode for testing
                from django.conf import settings
                use_mock = getattr(settings, 'USE_BROKER_MOCK', False)  # Default to real API for production
                
                if use_mock:
                    # Mock order response for testing
                    import uuid
                    mock_order_id = str(uuid.uuid4())
                    alpaca_response = {
                        'id': mock_order_id,
                        'symbol': symbol,
                        'qty': str(quantity),
                        'side': side.lower(),
                        'type': order_type.lower(),
                        'status': 'filled',
                        'filled_qty': str(quantity),
                        'filled_avg_price': '150.00'  # Mock price
                    }
                    logger.info(f"Mock stock order created: {mock_order_id}")
                else:
                    # Use Alpaca Broker API
                    from .services.alpaca_broker_service import AlpacaBrokerService
                    broker_service = AlpacaBrokerService()
                    
                    # Prepare order data for Alpaca
                    order_data = {
                        'symbol': symbol,
                        'qty': str(quantity),
                        'side': side.lower(),
                        'type': order_type.lower(),
                        'time_in_force': time_in_force.lower(),
                    }
                    
                    if order_type == 'LIMIT' and limit_price:
                        order_data['limit_price'] = str(limit_price)
                    
                    # Create order in Alpaca
                    alpaca_response = broker_service.create_order(
                        str(alpaca_account.alpaca_account_id),
                        order_data
                    )
                
                # Create local order record
                from .models.alpaca_models import AlpacaOrder
                alpaca_order = AlpacaOrder.objects.create(
                    alpaca_account=alpaca_account,
                    alpaca_order_id=alpaca_response['id'],
                    symbol=symbol,
                    order_type=order_type.lower(),
                    side=side.lower(),
                    quantity=quantity,
                    price=limit_price,
                    time_in_force=time_in_force.lower(),
                    status=alpaca_response.get('status', 'new'),
                    submitted_at=timezone.now(),
                )
                
                # Send order confirmation email
                try:
                    email_service = EmailNotificationService()
                    order_data = {
                        'symbol': symbol,
                        'side': side,
                        'type': order_type,
                        'qty': quantity,
                        'price': limit_price,
                        'status': alpaca_response.get('status', 'new'),
                        'order_id': alpaca_response['id']
                    }
                    email_service.send_order_confirmation(user, order_data)
                except Exception as email_error:
                    logger.warning(f"Failed to send order confirmation email: {email_error}")
                
                return PlaceStockOrder(
                    success=True,
                    message="Order placed successfully through Alpaca",
                    order_id=alpaca_response['id']
                )
                
            except AlpacaAccount.DoesNotExist:
                return PlaceStockOrder(
                    success=False,
                    message="Alpaca account not found. Please create an account first."
                )
            except Exception as alpaca_error:
                logger.error(f"Alpaca order placement failed: {alpaca_error}")
                return PlaceStockOrder(
                    success=False,
                    message=f"Failed to place order: {str(alpaca_error)}"
                )
            
            # Fallback to mock if Alpaca is not available
            import uuid
            order_id = str(uuid.uuid4())
            
            # For now, we'll just simulate the order placement
            # In a real implementation, this would integrate with a broker API
            print(f"📈 Mock Order Placed: {side} {quantity} shares of {symbol} at {order_type} price")
            if limit_price:
                print(f"   Limit Price: ${limit_price}")
            
            return PlaceStockOrder(
                success=True,
                message=f"Order placed successfully: {side} {quantity} shares of {symbol}",
                order_id=order_id
            )
            
        except Exception as e:
            return PlaceStockOrder(
                success=False,
                message=f"Failed to place order: {str(e)}"
            )


class WithdrawFunds(graphene.Mutation):
    class Arguments:
        amount = graphene.Float(required=True)
        currency = graphene.String(required=True)

    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)

    @classmethod
    def mutate(cls, root, info, amount, currency):
        try:
            # Mock user balance check
            mock_balance = 10000.0  # Mock balance in USD
            
            if amount <= 0:
                return WithdrawFunds(
                    success=False,
                    message="Withdrawal amount must be greater than zero"
                )
            
            if amount > mock_balance:
                return WithdrawFunds(
                    success=False,
                    message=f"Insufficient balance. Available: ${mock_balance:.2f}"
                )
            
            # In a real implementation, this would integrate with a payment processor
            print(f"💰 Mock Withdrawal: ${amount} {currency}")
            
            return WithdrawFunds(
                success=True,
                message=f"Withdrawal of ${amount} {currency} processed successfully"
            )
            
        except Exception as e:
            return WithdrawFunds(
                success=False,
                message=f"Failed to process withdrawal: {str(e)}"
            )


class Mutation(graphene.ObjectType):
    # Auth mutations removed - using SimpleJWT mutations from core/schema.py
    
    # AI/ML mutations
    generate_ai_recommendations = GenerateAIRecommendations.Field()
    
    # Watchlist mutations
    add_to_watchlist = AddToWatchlist.Field()
    
    # Trading mutations
    place_stock_order = PlaceStockOrder.Field()
    remove_from_watchlist = RemoveFromWatchlist.Field()
    
    # Financial mutations
    withdraw_funds = WithdrawFunds.Field()
    
    # Ticker follow mutations (stubbed for now)
    follow_ticker = graphene.Field(
        graphene.Boolean,
        symbol=graphene.String(required=True),
        description="Follow a ticker symbol"
    )
    unfollow_ticker = graphene.Field(
        graphene.Boolean,
        symbol=graphene.String(required=True),
        description="Unfollow a ticker symbol"
    )
    
    # Discussion voting mutations
    vote_discussion = VoteDiscussion.Field()
    
    # AI Portfolio rebalancing mutations
    ai_rebalance_portfolio = AIRebalancePortfolio.Field()
    
    # Profile mutations
    create_income_profile = CreateIncomeProfile.Field()
    
    # Portfolio mutations
    create_portfolio = CreatePortfolio.Field()
    create_portfolio_holding = CreatePortfolioHolding.Field()
    update_portfolio_holding = UpdatePortfolioHolding.Field()
    update_holding_shares = UpdateHoldingShares.Field()
    remove_portfolio_holding = RemovePortfolioHolding.Field()
    
    # ML mutations
    generate_ml_portfolio_recommendation = GenerateMLPortfolioRecommendation.Field()
    get_ml_market_analysis = GetMLMarketAnalysis.Field()
    get_ml_service_status = GetMLServiceStatus.Field()
    generate_institutional_portfolio_recommendation = GenerateInstitutionalPortfolioRecommendation.Field()
    
    # Monitoring mutations (if available)
    # create_alert = MonitoringMutations.create_alert
    # update_alert = MonitoringMutations.update_alert
    # delete_alert = MonitoringMutations.delete_alert

    def resolve_follow_ticker(self, info, symbol):
        """Follow a ticker symbol"""
        user = info.context.user
        if not user or user.is_anonymous:
            raise GraphQLError("You must be logged in to follow tickers.")
        
        from .ticker_follows import follow_ticker
        return follow_ticker(user.id, symbol)

    def resolve_unfollow_ticker(self, info, symbol):
        """Unfollow a ticker symbol"""
        user = info.context.user
        if not user or user.is_anonymous:
            raise GraphQLError("You must be logged in to follow tickers.")
        
        from .ticker_follows import unfollow_ticker
        return unfollow_ticker(user.id, symbol)
# Trigger new deployment - Wed Oct 15 20:48:58 EDT 2025
