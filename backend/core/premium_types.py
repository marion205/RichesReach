"""
Premium GraphQL Types and Mutations
"""

import graphene
from graphene_django import DjangoObjectType
from .premium_analytics import PremiumAnalyticsService
from .models import User
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Premium Analytics Types
class PortfolioMetricsType(graphene.ObjectType):
    """Advanced portfolio performance metrics"""
    total_value = graphene.Float()
    total_cost = graphene.Float()
    total_return = graphene.Float()
    total_return_percent = graphene.Float()
    volatility = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown = graphene.Float()
    beta = graphene.Float()
    alpha = graphene.Float()
    holdings = graphene.List('core.premium_types.HoldingDetailType')
    sector_allocation = graphene.JSONString()
    risk_metrics = graphene.JSONString()

class HoldingDetailType(graphene.ObjectType):
    """Detailed holding information"""
    symbol = graphene.String()
    company_name = graphene.String()
    shares = graphene.Int()
    current_price = graphene.Float()
    total_value = graphene.Float()
    cost_basis = graphene.Float()
    return_amount = graphene.Float()
    return_percent = graphene.Float()
    sector = graphene.String()

class StockScreeningResultType(graphene.ObjectType):
    """Advanced stock screening result"""
    symbol = graphene.String()
    company_name = graphene.String()
    sector = graphene.String()
    market_cap = graphene.Float()
    pe_ratio = graphene.Float()
    beginner_friendly_score = graphene.Int()
    current_price = graphene.Float()
    ml_score = graphene.Float()
    risk_level = graphene.String()
    growth_potential = graphene.String()

class AIRecommendationType(graphene.ObjectType):
    """AI-powered investment recommendation"""
    symbol = graphene.String()
    company_name = graphene.String()
    recommendation = graphene.String()  # Buy, Sell, Hold
    confidence = graphene.Float()
    reasoning = graphene.String()
    target_price = graphene.Float()
    current_price = graphene.Float()
    expected_return = graphene.Float()

class PortfolioAnalysisType(graphene.ObjectType):
    """Portfolio analysis results"""
    total_value = graphene.Float()
    num_holdings = graphene.Int()
    sector_breakdown = graphene.JSONString()
    risk_score = graphene.Float()
    diversification_score = graphene.Float()

class RiskAssessmentType(graphene.ObjectType):
    """Risk assessment results"""
    overall_risk = graphene.String()
    concentration_risk = graphene.String()
    sector_risk = graphene.String()
    volatility_estimate = graphene.Float()
    recommendations = graphene.List(graphene.String)

class MarketOutlookType(graphene.ObjectType):
    """AI-powered market outlook"""
    overall_sentiment = graphene.String()
    confidence = graphene.Float()
    key_factors = graphene.List(graphene.String)
    risks = graphene.List(graphene.String)

class AIRecommendationsType(graphene.ObjectType):
    """Complete AI recommendations package"""
    portfolio_analysis = graphene.Field(PortfolioAnalysisType)
    buy_recommendations = graphene.List(AIRecommendationType)
    sell_recommendations = graphene.List(AIRecommendationType)
    rebalance_suggestions = graphene.JSONString()
    risk_assessment = graphene.Field(RiskAssessmentType)
    market_outlook = graphene.Field(MarketOutlookType)

# Premium Queries
class PremiumQueries(graphene.ObjectType):
    """Premium feature queries"""
    
    premium_portfolio_metrics = graphene.Field(
        PortfolioMetricsType,
        portfolio_name=graphene.String(description="Specific portfolio name (optional)")
    )
    
    advanced_stock_screening = graphene.List(
        StockScreeningResultType,
        sector=graphene.String(description="Filter by sector"),
        min_market_cap=graphene.Float(description="Minimum market cap"),
        max_market_cap=graphene.Float(description="Maximum market cap"),
        min_pe_ratio=graphene.Float(description="Minimum P/E ratio"),
        max_pe_ratio=graphene.Float(description="Maximum P/E ratio"),
        min_beginner_score=graphene.Int(description="Minimum beginner score"),
        sort_by=graphene.String(description="Sort by: ml_score, market_cap"),
        limit=graphene.Int(description="Limit results (default: 50)")
    )
    
    ai_recommendations = graphene.Field(
        AIRecommendationsType,
        risk_tolerance=graphene.String(description="Risk tolerance: low, medium, high")
    )
    
    def resolve_premium_portfolio_metrics(self, info, portfolio_name=None):
        """Get advanced portfolio metrics"""
        user = info.context.user
        logger.info(f"Premium portfolio metrics request - User: {user}, Anonymous: {user.is_anonymous if user else 'No user'}")
        
        # For testing purposes, use user ID 1 (test@example.com) if no user is authenticated
        user_id = user.id if user and not user.is_anonymous else 1
        
        # Check if user has premium subscription (only for authenticated users)
        if user and not user.is_anonymous and not self._has_premium_access(user):
            logger.warning(f"User {user.id} does not have premium access")
            raise Exception("Premium subscription required")
        
        # For unauthenticated requests, allow access to demo data
        analytics_service = PremiumAnalyticsService()
        result = analytics_service.get_portfolio_performance_metrics(user_id, portfolio_name)
        logger.info(f"Portfolio metrics result for user {user_id}: {type(result)}")
        return result
    
    def resolve_advanced_stock_screening(self, info, **kwargs):
        """Advanced stock screening with filters"""
        user = info.context.user
        
        # Check if user has premium subscription (only if authenticated)
        if user and not user.is_anonymous and not self._has_premium_access(user):
            raise Exception("Premium subscription required")
        
        # Build filters from kwargs
        filters = {k: v for k, v in kwargs.items() if v is not None}
        
        analytics_service = PremiumAnalyticsService()
        return analytics_service.get_advanced_stock_screening(filters)
    
    def resolve_ai_recommendations(self, info, risk_tolerance="medium"):
        """Get AI-powered investment recommendations"""
        user = info.context.user
        logger.info(f"AI recommendations request - User: {user}, Anonymous: {user.is_anonymous if user else 'No user'}")
        
        # For testing purposes, use user ID 1 (test@example.com) if no user is authenticated
        user_id = user.id if user and not user.is_anonymous else 1
        
        # Check if user has premium subscription
        if user and not user.is_anonymous and not self._has_premium_access(user):
            logger.warning(f"User {user.id} does not have premium access")
            raise Exception("Premium subscription required")
        
        analytics_service = PremiumAnalyticsService()
        result = analytics_service.get_ai_recommendations(user_id, risk_tolerance)
        logger.info(f"AI recommendations result for user {user_id}: {type(result)}")
        return result
    
    def _has_premium_access(self, user):
        """Check if user has premium subscription"""
        # Allow test@example.com to have premium access
        if user and user.email == 'test@example.com':
            return True
        
        # For testing purposes, allow all authenticated users
        # In production, you'd check against a subscription model
        if user and not user.is_anonymous:
            return True
            
        return False

# Premium Mutations
class SubscribeToPremium(graphene.Mutation):
    """Subscribe to premium features"""
    
    class Arguments:
        plan_type = graphene.String(required=True, description="Plan type: basic, pro, elite")
        payment_method = graphene.String(required=True, description="Payment method ID")
    
    success = graphene.Boolean()
    message = graphene.String()
    subscription_id = graphene.String()
    
    def mutate(self, info, plan_type, payment_method):
        user = info.context.user
        if not user or user.is_anonymous:
            return SubscribeToPremium(
                success=False,
                message="Authentication required"
            )
        
        # Validate plan type
        valid_plans = ["basic", "pro", "elite"]
        if plan_type not in valid_plans:
            return SubscribeToPremium(
                success=False,
                message="Invalid plan type"
            )
        
        try:
            # In production, you'd integrate with Stripe/PayPal
            # For now, simulate successful subscription
            subscription_id = f"sub_{user.id}_{plan_type}_{datetime.now().strftime('%Y%m%d')}"
            
            # Store subscription in user profile or separate model
            # user.subscription_plan = plan_type
            # user.subscription_active = True
            # user.save()
            
            return SubscribeToPremium(
                success=True,
                message=f"Successfully subscribed to {plan_type} plan",
                subscription_id=subscription_id
            )
            
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return SubscribeToPremium(
                success=False,
                message="Failed to create subscription"
            )

class CancelPremiumSubscription(graphene.Mutation):
    """Cancel premium subscription"""
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info):
        user = info.context.user
        if not user or user.is_anonymous:
            return CancelPremiumSubscription(
                success=False,
                message="Authentication required"
            )
        
        try:
            # In production, you'd cancel with payment provider
            # user.subscription_active = False
            # user.save()
            
            return CancelPremiumSubscription(
                success=True,
                message="Subscription cancelled successfully"
            )
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return CancelPremiumSubscription(
                success=False,
                message="Failed to cancel subscription"
            )

class PremiumMutations(graphene.ObjectType):
    """Premium feature mutations"""
    
    subscribe_to_premium = SubscribeToPremium.Field()
    cancel_premium_subscription = CancelPremiumSubscription.Field()
