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

from .models import User, Post, Comment, ChatSession, ChatMessage, IncomeProfile, AIPortfolioRecommendation, Stock, Watchlist, WatchlistItem, Portfolio, StockDiscussion, DiscussionComment
from .types import UserType, PostType, CommentType, ChatSessionType, ChatMessageType
from .portfolio_types import CreatePortfolio, CreatePortfolioHolding, UpdatePortfolioHolding, UpdateHoldingShares, RemovePortfolioHolding
from .auth_utils import RateLimiter, SecurityUtils
# from .websocket_service import websocket_service  # Temporarily disabled for local development
from .ml_mutations import GenerateMLPortfolioRecommendation, GetMLMarketAnalysis, GetMLServiceStatus, GenerateInstitutionalPortfolioRecommendation
from .monitoring_types import MonitoringMutations


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
    """Generate AI portfolio recommendations based on user's income profile using ML/AI"""
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
            except Exception:
                return GenerateAIRecommendations(
                    success=False,
                    message="Please create an income profile first to generate AI recommendations.",
                    recommendations=[]
                )
            
            risk_tolerance = income_profile.risk_tolerance

            # -------------------- ML/AI Stock Recommendations --------------------
            from core.ml_stock_recommender import MLStockRecommender
            
            # Initialize ML recommender
            ml_recommender = MLStockRecommender()
            
            # Generate ML-based recommendations based on user's risk tolerance
            if risk_tolerance == 'Conservative':
                # Use beginner-friendly stocks for conservative investors
                ml_recommendations = ml_recommender.get_beginner_friendly_stocks(user, limit=4)
                risk_assessment_text = "Conservative portfolio focused on capital preservation with steady growth."
            elif risk_tolerance == 'Moderate':
                # Use general ML recommendations for moderate investors
                ml_recommendations = ml_recommender.generate_ml_recommendations(user, limit=4)
                risk_assessment_text = "Balanced portfolio with growth potential and moderate risk."
            else:  # Aggressive
                # Use general ML recommendations for aggressive investors
                ml_recommendations = ml_recommender.generate_ml_recommendations(user, limit=4)
                risk_assessment_text = "Aggressive growth portfolio with high potential returns and significant volatility."
            
            # Convert ML recommendations to the expected format
            recommended_stocks = []
            total_allocation = 0
            
            for i, rec in enumerate(ml_recommendations):
                # Calculate allocation based on confidence score and risk tolerance
                base_allocation = 25.0  # Start with equal allocation
                confidence_multiplier = rec.confidence_score
                
                if risk_tolerance == 'Conservative':
                    # Conservative: more equal distribution, lower volatility
                    allocation = base_allocation * (0.8 + 0.4 * confidence_multiplier)
                elif risk_tolerance == 'Moderate':
                    # Moderate: balanced distribution
                    allocation = base_allocation * (0.9 + 0.2 * confidence_multiplier)
                else:  # Aggressive
                    # Aggressive: weight towards higher confidence
                    allocation = base_allocation * (0.7 + 0.6 * confidence_multiplier)
                
                total_allocation += allocation
                
                recommended_stocks.append({
                    'symbol': rec.stock.symbol,
                    'companyName': rec.stock.company_name or f"{rec.stock.symbol} Corp",
                    'allocation': round(allocation, 1),
                    'reasoning': rec.reasoning,
                    'riskLevel': rec.risk_level,
                    'expectedReturn': rec.expected_return,
                    'confidence': rec.confidence_score,
                    'recommendation': 'BUY',
                    'targetPrice': float(rec.stock.current_price) * (1 + rec.expected_return) if rec.stock.current_price else None,
                    'currentPrice': float(rec.stock.current_price) if rec.stock.current_price else None,
                })
            
            # Normalize allocations to sum to 100%
            if total_allocation > 0:
                for stock in recommended_stocks:
                    stock['allocation'] = round((stock['allocation'] / total_allocation) * 100, 1)
            
            # Calculate expected portfolio return
            expected_return = sum(
                stock['expectedReturn'] * (stock['allocation'] / 100.0) 
                for stock in recommended_stocks
            ) if recommended_stocks else _normalize_to_decimal(6.5)
            
            # Debug logging
            print(f"🔍 Generated {len(recommended_stocks)} stock recommendations:")
            for stock in recommended_stocks:
                print(f"  {stock['symbol']}: expectedReturn={stock['expectedReturn']}, allocation={stock['allocation']}%, confidence={stock['confidence']}")

            # -------------------- compute portfolio analytics --------------------
            total_value, num_holdings = _compute_portfolio_totals(user)

            # EV weighted by allocation (falls back to confidence when provided)
            expected_impact = _compute_expected_impact(recommended_stocks, total_value)

            vol = _fallback_volatility(risk_tolerance)
            mdd = _fallback_max_drawdown(risk_tolerance)

            # Portfolio allocation base (keep original keys for compatibility)
            base_allocation = {
                'stocks': sum(float(s.get('allocation', 0.0)) for s in recommended_stocks),
                'bonds': 0 if risk_tolerance == 'Aggressive' else 10,
                'cash': 0
            }

            # Set numHoldings to the number of recommended stocks if no actual holdings
            if num_holdings == 0:
                num_holdings = len(recommended_stocks)

            # Enrich with analytics (so GraphQL types that already expose JSON can surface it)
            portfolio_allocation = {
                **base_allocation,
                'analytics': {
                    'totalValue': total_value,
                    'numHoldings': num_holdings,
                    'expectedImpact': expected_impact,  # ev_return_decimal, ev_change_for_total_value, ev_per_10k
                    'risk': {
                        'volatility_estimate': vol,        # percent number, e.g., 12.8
                        'max_drawdown_pct': mdd,           # percent number, e.g., 32.0
                    },
                }
            }

            # Create the AI recommendation record
            recommendation = AIPortfolioRecommendation.objects.create(
                user=user,
                risk_profile=risk_tolerance,
                portfolio_allocation=portfolio_allocation,
                recommended_stocks=recommended_stocks,
                expected_portfolio_return=expected_return,  # decimal (e.g., 0.088)
                risk_assessment=risk_assessment_text
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


# Add other mutations here...
class AddToWatchlist(graphene.Mutation):
    """Add a stock to user's watchlist"""
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        symbol = graphene.String(required=True)
        company_name = graphene.String()
        notes = graphene.String()

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


class Mutation(graphene.ObjectType):
    # Auth mutations
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    revoke_token = graphql_jwt.Revoke.Field()
    
    # AI/ML mutations
    generate_ai_recommendations = GenerateAIRecommendations.Field()
    
    # Watchlist mutations
    add_to_watchlist = AddToWatchlist.Field()
    remove_from_watchlist = RemoveFromWatchlist.Field()
    
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
