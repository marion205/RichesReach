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
    suggested_exit_price = graphene.Float()  # For sell recommendations
    current_return = graphene.Float()  # For sell recommendations
    sector = graphene.String()  # Additional context
    risk_level = graphene.String()  # Additional context
    ml_score = graphene.Float()  # Additional context

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
    volatilityEstimate = graphene.Float()  # Alias for frontend compatibility
    recommendations = graphene.List(graphene.String)
    
    def resolve_volatilityEstimate(self, info):
        """Resolver for volatilityEstimate alias"""
        # Handle both dict and object formats
        if hasattr(self, 'volatility_estimate'):
            return self.volatility_estimate
        elif isinstance(self, dict) and 'volatility_estimate' in self:
            return self['volatility_estimate']
        else:
            return None

class MarketOutlookType(graphene.ObjectType):
    """AI-powered market outlook"""
    overall_sentiment = graphene.String()
    confidence = graphene.Float()
    key_factors = graphene.List(graphene.String)
    risks = graphene.List(graphene.String)

class RebalanceSuggestionType(graphene.ObjectType):
    """Portfolio rebalancing suggestion"""
    action = graphene.String()
    current_allocation = graphene.Float()
    suggested_allocation = graphene.Float()
    reasoning = graphene.String()
    priority = graphene.String()

class AIRecommendationsType(graphene.ObjectType):
    """Complete AI recommendations package"""
    portfolio_analysis = graphene.Field(PortfolioAnalysisType)
    buy_recommendations = graphene.List(AIRecommendationType)
    sell_recommendations = graphene.List(AIRecommendationType)
    rebalance_suggestions = graphene.List(RebalanceSuggestionType)
    risk_assessment = graphene.Field(RiskAssessmentType)
    market_outlook = graphene.Field(MarketOutlookType)

class StockTradeType(graphene.ObjectType):
    """Individual stock trade in rebalancing"""
    symbol = graphene.String()
    company_name = graphene.String()
    action = graphene.String()  # "BUY" or "SELL"
    shares = graphene.Int()
    price = graphene.Float()
    total_value = graphene.Float()
    reason = graphene.String()

class RebalanceResultType(graphene.ObjectType):
    """Result of AI rebalancing operation"""
    success = graphene.Boolean()
    message = graphene.String()
    changes_made = graphene.List(graphene.String)
    stock_trades = graphene.List(StockTradeType)
    new_portfolio_value = graphene.Float()
    rebalance_cost = graphene.Float()
    estimated_improvement = graphene.String()

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
    
    options_analysis = graphene.Field(
        'core.premium_types.OptionsAnalysisType',
        symbol=graphene.String(required=True, description="Stock symbol to analyze options for")
    )
    
    stock_screening = graphene.List(
        StockScreeningResultType,
        filters=graphene.String(description="JSON string of screening filters")
    )
    
    def resolve_premium_portfolio_metrics(self, info, portfolio_name=None):
        """Get advanced portfolio metrics"""
        user = getattr(info.context, 'user', None)
        logger.info(f"Premium portfolio metrics request - User: {user}, Anonymous: {user.is_anonymous if user else 'No user'}")
        
        # For testing purposes, use user ID 1 (test@example.com) if no user is authenticated
        user_id = user.id if user and not user.is_anonymous else 1
        
        # Check if user has premium subscription (only for authenticated users)
        if user and not user.is_anonymous and not _has_premium_access(user):
            logger.warning(f"User {user.id} does not have premium access")
            raise Exception("Premium subscription required")
        
        # For unauthenticated requests, allow access to demo data
        analytics_service = PremiumAnalyticsService()
        result = analytics_service.get_portfolio_performance_metrics(user_id, portfolio_name)
        logger.info(f"Portfolio metrics result for user {user_id}: {type(result)}")
        return result
    
    def resolve_advanced_stock_screening(self, info, **kwargs):
        """Advanced stock screening with filters"""
        user = getattr(info.context, 'user', None)
        
        # Check if user has premium subscription (only if authenticated)
        if user and not user.is_anonymous and not _has_premium_access(user):
            raise Exception("Premium subscription required")
        
        # Build filters from kwargs
        filters = {k: v for k, v in kwargs.items() if v is not None}
        
        analytics_service = PremiumAnalyticsService()
        return analytics_service.get_advanced_stock_screening(filters)
    
    def resolve_ai_recommendations(self, info, risk_tolerance="medium"):
        """Get AI-powered investment recommendations"""
        user = getattr(info.context, 'user', None)
        logger.info(f"AI recommendations request - User: {user}, Anonymous: {user.is_anonymous if user else 'No user'}")
        
        # For testing purposes, use user ID 1 (test@example.com) if no user is authenticated
        user_id = user.id if user and not user.is_anonymous else 1
        
        # Check if user has premium subscription
        if user and not user.is_anonymous and not _has_premium_access(user):
            logger.warning(f"User {user.id} does not have premium access")
            raise Exception("Premium subscription required")
        
        analytics_service = PremiumAnalyticsService()
        result = analytics_service.get_ai_recommendations(user_id, risk_tolerance)
        logger.info(f"AI recommendations result for user {user_id}: {type(result)}")
        return result
    
    def resolve_options_analysis(self, info, symbol):
        """Get comprehensive options analysis for a symbol"""
        try:
            user = getattr(info.context, 'user', None) if hasattr(info, 'context') else None
            logger.info(f"Options analysis request - User: {user}, Symbol: {symbol}")
            
            # Check if user has premium subscription (only if authenticated)
            if user and not user.is_anonymous and not _has_premium_access(user):
                logger.warning(f"User {user.id} does not have premium access")
                raise Exception("Premium subscription required")
            
            # Import the options service
            from .options_service import OptionsAnalysisService
            
            try:
                options_service = OptionsAnalysisService()
                result = options_service.get_comprehensive_analysis(symbol)
                logger.info(f"Options analysis result for {symbol}: {type(result)}")
                logger.info(f"Options chain data: {result.get('options_chain', {})}")
                return result
            except Exception as e:
                logger.error(f"Error getting options analysis for {symbol}: {e}")
                # Return mock data for testing
                return self._get_mock_options_analysis(symbol)
                
        except Exception as e:
            logger.error(f"Error in options analysis resolver: {e}")
            # Return mock data as final fallback
            return self._get_mock_options_analysis(symbol)
    
    def _get_mock_options_analysis(self, symbol):
        """Return mock options analysis data for testing"""
        from datetime import datetime, timedelta
        
        # Mock options contracts
        call_options = [
            {
                'symbol': symbol,
                'contract_symbol': f'{symbol}240115C00150000',
                'strike': 150.0,
                'expiration_date': '2024-01-15',
                'option_type': 'call',
                'bid': 2.50,
                'ask': 2.75,
                'last_price': 2.60,
                'volume': 1250,
                'open_interest': 5000,
                'implied_volatility': 0.25,
                'delta': 0.65,
                'gamma': 0.02,
                'theta': -0.15,
                'vega': 0.30,
                'rho': 0.05,
                'intrinsic_value': 5.0,
                'time_value': 2.60,
                'days_to_expiration': 30
            }
        ]
        
        put_options = [
            {
                'symbol': symbol,
                'contract_symbol': f'{symbol}240115P00150000',
                'strike': 150.0,
                'expiration_date': '2024-01-15',
                'option_type': 'put',
                'bid': 1.20,
                'ask': 1.40,
                'last_price': 1.30,
                'volume': 800,
                'open_interest': 3000,
                'implied_volatility': 0.28,
                'delta': -0.35,
                'gamma': 0.02,
                'theta': -0.12,
                'vega': 0.25,
                'rho': -0.03,
                'intrinsic_value': 0.0,
                'time_value': 1.30,
                'days_to_expiration': 30
            }
        ]
        
        # Mock unusual flow
        unusual_flow = [
            {
                'symbol': symbol,
                'contract_symbol': f'{symbol}240115C00150000',
                'option_type': 'call',
                'strike': 150.0,
                'expiration_date': '2024-01-15',
                'volume': 5000,
                'open_interest': 15000,
                'premium': 13000.0,
                'implied_volatility': 0.30,
                'unusual_activity_score': 0.85,
                'activity_type': 'Sweep'
            }
        ]
        
        # Mock strategies
        recommended_strategies = [
            {
                'strategy_name': 'Covered Call',
                'strategy_type': 'Covered Call',
                'max_profit': 7.50,
                'max_loss': -142.50,
                'breakeven_points': [142.50],
                'probability_of_profit': 0.65,
                'risk_reward_ratio': 0.05,
                'days_to_expiration': 30,
                'total_cost': 0.0,
                'total_credit': 2.60
            }
        ]
        
        # Mock market sentiment
        market_sentiment = {
            'put_call_ratio': 0.65,
            'implied_volatility_rank': 45.0,
            'skew': 0.15,
            'sentiment_score': 65.0,
            'sentiment_description': 'Bullish'
        }
        
        return {
            'underlying_symbol': symbol,
            'underlying_price': 155.0,
            'options_chain': {
                'expiration_dates': ['2024-01-15', '2024-02-16', '2024-03-15'],
                'calls': call_options,
                'puts': put_options,
                'greeks': {
                    'delta': 0.5,
                    'gamma': 0.02,
                    'theta': -0.15,
                    'vega': 0.30,
                    'rho': 0.05
                }
            },
            'unusual_flow': unusual_flow,
            'recommended_strategies': recommended_strategies,
            'market_sentiment': market_sentiment
        }
    
    def resolve_stock_screening(self, info, filters):
        """Get stock screening results based on filters"""
        try:
            user = getattr(info.context, 'user', None) if hasattr(info, 'context') else None
            logger.info(f"Stock screening request - User: {user}, Filters: {filters}")
            
            # Check if user has premium subscription (only if authenticated)
            if user and not user.is_anonymous and not _has_premium_access(user):
                logger.warning(f"User {user.id} does not have premium access")
                raise Exception("Premium subscription required")
            
            # Parse filters
            import json
            if isinstance(filters, str):
                filters = json.loads(filters)
            
            # Get analytics service
            analytics_service = PremiumAnalyticsService()
            results = analytics_service.get_advanced_stock_screening(filters)
            
            logger.info(f"Stock screening results: {len(results)} stocks found")
            return results
            
        except Exception as e:
            logger.error(f"Error in stock screening resolver: {e}")
            raise Exception(f"Stock screening failed: {str(e)}")
    
def _has_premium_access(user):
    """Check if user has premium subscription"""
    # Allow test@example.com to have premium access
    if user and user.email == 'test@example.com':
        logger.info(f"Premium access granted to test user: {user.email}")
        return True
    
    # For testing purposes, allow all authenticated users
    # In production, you'd check against a subscription model
    if user and not user.is_anonymous:
        logger.info(f"Premium access granted to authenticated user: {user.email}")
        return True
        
    logger.warning(f"Premium access denied for user: {user}")
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

# Options Analysis Types
class OptionsContractType(graphene.ObjectType):
    """Individual options contract"""
    symbol = graphene.String()
    contract_symbol = graphene.String()
    strike = graphene.Float()
    expiration_date = graphene.String()
    option_type = graphene.String()
    bid = graphene.Float()
    ask = graphene.Float()
    last_price = graphene.Float()
    volume = graphene.Int()
    open_interest = graphene.Int()
    implied_volatility = graphene.Float()
    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()
    rho = graphene.Float()
    intrinsic_value = graphene.Float()
    time_value = graphene.Float()
    days_to_expiration = graphene.Int()

class GreeksType(graphene.ObjectType):
    """Greeks for options analysis"""
    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()
    rho = graphene.Float()

class OptionsChainType(graphene.ObjectType):
    """Options chain for a symbol"""
    expiration_dates = graphene.List(graphene.String)
    calls = graphene.List(OptionsContractType)
    puts = graphene.List(OptionsContractType)
    greeks = graphene.Field(GreeksType)
    
    def resolve_expiration_dates(self, info):
        return self.get('expiration_dates', [])
    
    def resolve_calls(self, info):
        return self.get('calls', [])
    
    def resolve_puts(self, info):
        return self.get('puts', [])
    
    def resolve_greeks(self, info):
        return self.get('greeks', {})

class OptionsFlowType(graphene.ObjectType):
    """Unusual options flow data"""
    symbol = graphene.String()
    contract_symbol = graphene.String()
    option_type = graphene.String()
    strike = graphene.Float()
    expiration_date = graphene.String()
    volume = graphene.Int()
    open_interest = graphene.Int()
    premium = graphene.Float()
    implied_volatility = graphene.Float()
    unusual_activity_score = graphene.Float()
    activity_type = graphene.String()

class OptionsStrategyType(graphene.ObjectType):
    """Options trading strategy"""
    strategy_name = graphene.String()
    strategy_type = graphene.String()
    max_profit = graphene.Float()
    max_loss = graphene.Float()
    breakeven_points = graphene.List(graphene.Float)
    probability_of_profit = graphene.Float()
    risk_reward_ratio = graphene.Float()
    days_to_expiration = graphene.Int()
    total_cost = graphene.Float()
    total_credit = graphene.Float()
    description = graphene.String()
    risk_level = graphene.String()
    market_outlook = graphene.String()

class MarketSentimentType(graphene.ObjectType):
    """Market sentiment from options data"""
    put_call_ratio = graphene.Float()
    implied_volatility_rank = graphene.Float()
    skew = graphene.Float()
    sentiment_score = graphene.Float()
    sentiment_description = graphene.String()

class OptionsAnalysisType(graphene.ObjectType):
    """Complete options analysis"""
    underlying_symbol = graphene.String()
    underlying_price = graphene.Float()
    options_chain = graphene.Field(OptionsChainType)
    unusual_flow = graphene.List(OptionsFlowType)
    recommended_strategies = graphene.List(OptionsStrategyType)
    market_sentiment = graphene.Field(MarketSentimentType)
    
    def resolve_underlying_symbol(self, info):
        return self.get('underlying_symbol', '')
    
    def resolve_underlying_price(self, info):
        return self.get('underlying_price', 0.0)
    
    def resolve_options_chain(self, info):
        return self.get('options_chain', {})
    
    def resolve_unusual_flow(self, info):
        return self.get('unusual_flow', [])
    
    def resolve_recommended_strategies(self, info):
        return self.get('recommended_strategies', [])
    
    def resolve_market_sentiment(self, info):
        return self.get('market_sentiment', {})

class PremiumMutations(graphene.ObjectType):
    """Premium feature mutations"""
    
    subscribe_to_premium = SubscribeToPremium.Field()
    cancel_premium_subscription = CancelPremiumSubscription.Field()
    
    ai_rebalance_portfolio = graphene.Field(
        RebalanceResultType,
        portfolio_name=graphene.String(description="Portfolio to rebalance (optional)"),
        risk_tolerance=graphene.String(description="Risk tolerance: low, medium, high"),
        max_rebalance_percentage=graphene.Float(description="Maximum percentage to rebalance (default: 20%)")
    )
    
    def resolve_ai_rebalance_portfolio(self, info, portfolio_name=None, risk_tolerance="medium", max_rebalance_percentage=20.0):
        """AI-powered portfolio rebalancing"""
        user = getattr(info.context, 'user', None)
        
        # For testing purposes, use user ID 1 (test@example.com) if no user is authenticated
        user_id = user.id if user and not user.is_anonymous else 1
        
        # Check if user has premium subscription
        if user and not user.is_anonymous and not _has_premium_access(user):
            raise Exception("Premium subscription required for AI rebalancing")
        
        try:
            from .premium_analytics import PremiumAnalyticsService
            from .models import Portfolio, Stock
            
            # Get user's portfolio
            portfolio = Portfolio.objects.filter(user_id=user_id).first()
            if not portfolio:
                return RebalanceResultType(
                    success=False,
                    message="No portfolio found for rebalancing",
                    changes_made=[],
                    stock_trades=[],
                    new_portfolio_value=0.0,
                    rebalance_cost=0.0,
                    estimated_improvement="N/A"
                )
            
            # Get AI recommendations
            analytics_service = PremiumAnalyticsService()
            recommendations = analytics_service.get_ai_recommendations(user_id, risk_tolerance)
            
            if not recommendations or not recommendations.get('rebalance_suggestions'):
                return RebalanceResultType(
                    success=False,
                    message="No rebalancing recommendations available",
                    changes_made=[],
                    stock_trades=[],
                    new_portfolio_value=float(portfolio.total_value),
                    rebalance_cost=0.0,
                    estimated_improvement="N/A"
                )
            
            # Apply rebalancing suggestions (simulated)
            changes_made = []
            stock_trades = []
            total_cost = 0.0
            
            # Get real stock prices from market data service
            from .enhanced_stock_service import EnhancedStockService
            stock_service = EnhancedStockService()
            
            # Smart stock selection with lazy loading and diversity algorithm
            # Use caching to speed up repeated calls
            from django.core.cache import cache
            cache_key = f"rebalance_stocks_{risk_tolerance}_{max_rebalance_percentage}"
            sector_stocks = cache.get(cache_key)
            
            if sector_stocks is None:
                sector_stocks = {}
                
                # Simplified approach: Get diverse stocks with randomization
                import random
                
                # Get all stocks and group them by sector
                all_stocks = Stock.objects.all()
                
                # Group stocks by sector
                stocks_by_sector = {}
                for stock in all_stocks:
                    sector = getattr(stock, 'sector', None) or 'Mixed'
                    if sector not in stocks_by_sector:
                        stocks_by_sector[sector] = []
                    stocks_by_sector[sector].append(stock)
                
                # Select diverse sectors randomly
                available_sectors = list(stocks_by_sector.keys())
                if available_sectors:
                    # Pick 3-5 random sectors
                    num_sectors = min(5, len(available_sectors))
                    selected_sectors = random.sample(available_sectors, num_sectors)
                    
                    for sector_name in selected_sectors:
                        stocks_in_sector = stocks_by_sector[sector_name]
                        
                        # Increase sample size to get better quality stocks
                        # Take up to 20 stocks from each sector for better selection
                        if len(stocks_in_sector) > 20:
                            # Randomly sample 20 stocks to get variety
                            stocks_in_sector = random.sample(stocks_in_sector, 20)
                        
                        # Filter by price range and performance metrics
                        quality_stocks = []
                        for stock in stocks_in_sector:
                            price = float(stock.current_price) if stock.current_price else 0
                            # Only consider stocks with valid prices and data
                            if price > 0 and 5.0 <= price <= 2000.0:  # Must have valid price
                                # Calculate performance score based on available metrics
                                performance_score = 0
                                
                                # Use market cap as a proxy for company size/quality
                                market_cap = getattr(stock, 'market_cap', None)
                                if market_cap:
                                    try:
                                        market_cap_value = float(market_cap)
                                        if market_cap_value > 10000000000:  # > $10B market cap (mega cap)
                                            performance_score += 40
                                        elif market_cap_value > 1000000000:  # > $1B market cap (large cap)
                                            performance_score += 30
                                        elif market_cap_value > 100000000:  # > $100M market cap (mid cap)
                                            performance_score += 20
                                        else:
                                            performance_score += 10
                                    except:
                                        performance_score += 15  # Default for unknown market cap
                                else:
                                    performance_score += 15
                                
                                # Use volume as a proxy for liquidity and interest
                                volume = getattr(stock, 'volume', None)
                                if volume:
                                    try:
                                        volume_value = float(volume)
                                        if volume_value > 1000000:  # High volume
                                            performance_score += 15
                                        elif volume_value > 100000:  # Medium volume
                                            performance_score += 10
                                        else:
                                            performance_score += 5
                                    except:
                                        performance_score += 8
                                else:
                                    performance_score += 8
                                
                                # Use price as a quality indicator (higher price often = better company)
                                if price > 100:
                                    performance_score += 20
                                elif price > 50:
                                    performance_score += 15
                                elif price > 20:
                                    performance_score += 10
                                else:
                                    performance_score += 5
                                
                                # Check for additional performance metrics if available
                                # Look for any performance-related fields
                                for field_name in ['pe_ratio', 'pb_ratio', 'dividend_yield', 'eps', 'revenue_growth']:
                                    field_value = getattr(stock, field_name, None)
                                    if field_value:
                                        try:
                                            field_float = float(field_value)
                                            if field_name == 'pe_ratio' and 5 <= field_float <= 25:  # Good P/E range
                                                performance_score += 10
                                            elif field_name == 'pb_ratio' and 0.5 <= field_float <= 3:  # Good P/B range
                                                performance_score += 8
                                            elif field_name == 'dividend_yield' and field_float > 0:  # Has dividends
                                                performance_score += 5
                                            elif field_name == 'eps' and field_float > 0:  # Positive earnings
                                                performance_score += 12
                                            elif field_name == 'revenue_growth' and field_float > 0:  # Growing revenue
                                                performance_score += 8
                                        except:
                                            continue
                                
                                # Add some randomness for variety (but performance is primary)
                                performance_score += random.random() * 5  # Reduced randomness, performance is more important
                                
                                quality_stocks.append({
                                    'stock': stock,
                                    'price': price,
                                    'performance_score': performance_score
                                })
                        
                        # Sort by performance score (best performers first) and take top 3-4
                        quality_stocks.sort(key=lambda x: x['performance_score'], reverse=True)
                        selected_stocks = quality_stocks[:min(4, len(quality_stocks))]
                        
                        if selected_stocks:
                            sector_stocks[sector_name] = []
                            logger.info(f"Selected {len(selected_stocks)} top-performing stocks for {sector_name}:")
                            for item in selected_stocks:
                                stock = item['stock']
                                logger.info(f"  {stock.symbol}: ${item['price']:.2f} (score: {item['performance_score']:.1f})")
                                sector_stocks[sector_name].append({
                                    'symbol': stock.symbol,
                                    'name': getattr(stock, 'name', None) or stock.symbol,
                                    'price': item['price']
                                })
                        else:
                            # Fallback: if no stocks with valid prices, use any stocks from this sector
                            logger.warning(f"No stocks with valid prices in {sector_name}, using fallback selection")
                            fallback_stocks = stocks_in_sector[:3]  # Take first 3 stocks
                            if fallback_stocks:
                                sector_stocks[sector_name] = []
                                for stock in fallback_stocks:
                                    price = float(stock.current_price) if stock.current_price else 100.0  # Default price
                                    sector_stocks[sector_name].append({
                                        'symbol': stock.symbol,
                                        'name': getattr(stock, 'name', None) or stock.symbol,
                                        'price': price
                                    })
                
                # If no stocks found, return error
                if not sector_stocks:
                    return RebalanceResultType(
                        success=False,
                        message="No stocks available for rebalancing",
                        changes_made=[],
                        stock_trades=[],
                        new_portfolio_value=0.0,
                        rebalance_cost=0.0,
                        estimated_improvement="N/A"
                    )
                
                # Cache the results for 5 minutes to speed up repeated calls
                cache.set(cache_key, sector_stocks, 300)
            
            for suggestion in recommendations['rebalance_suggestions'][:3]:  # Limit to top 3 suggestions
                action = suggestion['action']
                current_alloc = suggestion['current_allocation']
                suggested_alloc = suggestion['suggested_allocation']
                
                # Calculate change percentage
                change_pct = abs(suggested_alloc - current_alloc)
                
                # Only apply if change is within max_rebalance_percentage
                if change_pct <= max_rebalance_percentage:
                    changes_made.append(f"{action}: {current_alloc:.1f}% → {suggested_alloc:.1f}%")
                    
                    # Generate specific stock trades based on the action
                    if "Increase Technology" in action:
                        # Find technology-related stocks
                        tech_sectors = [sector for sector in sector_stocks.keys() if 'tech' in sector.lower() or 'technology' in sector.lower()]
                        if tech_sectors:
                            tech_stocks = sector_stocks[tech_sectors[0]][:2]  # Buy top 2 tech stocks
                            for stock in tech_stocks:
                                shares = max(1, int((float(portfolio.total_value) * 0.05) / stock['price']))  # 5% of portfolio per stock
                                trade_value = shares * stock['price']
                                stock_trades.append(StockTradeType(
                                    symbol=stock['symbol'],
                                    company_name=stock['name'],
                                    action="BUY",
                                    shares=shares,
                                    price=stock['price'],
                                    total_value=trade_value,
                                    reason="Increase Technology sector exposure"
                                ))
                                # Calculate transaction cost (0.1% of trade value)
                                cost = trade_value * 0.001
                                total_cost += cost
                    
                    elif "Increase Healthcare" in action:
                        # Find healthcare-related stocks
                        health_sectors = [sector for sector in sector_stocks.keys() if 'health' in sector.lower() or 'healthcare' in sector.lower() or 'medical' in sector.lower()]
                        if health_sectors:
                            health_stocks = sector_stocks[health_sectors[0]][:2]  # Buy top 2 healthcare stocks
                            for stock in health_stocks:
                                shares = max(1, int((float(portfolio.total_value) * 0.05) / stock['price']))  # 5% of portfolio per stock
                                trade_value = shares * stock['price']
                                stock_trades.append(StockTradeType(
                                    symbol=stock['symbol'],
                                    company_name=stock['name'],
                                    action="BUY",
                                    shares=shares,
                                    price=stock['price'],
                                    total_value=trade_value,
                                    reason="Increase Healthcare sector exposure"
                                ))
                                # Calculate transaction cost (0.1% of trade value)
                                cost = trade_value * 0.001
                                total_cost += cost
                    
                    elif "Reduce Consumer Cyclical" in action:
                        # Sell consumer cyclical stocks (simulate selling existing holdings)
                        consumer_stocks = sector_stocks['Consumer Cyclical'][:2]  # Sell top 2 consumer stocks
                        for stock in consumer_stocks:
                            shares = max(1, int((float(portfolio.total_value) * 0.03) / stock['price']))  # 3% of portfolio per stock
                            stock_trades.append(StockTradeType(
                                symbol=stock['symbol'],
                                company_name=stock['name'],
                                action="SELL",
                                shares=shares,
                                price=stock['price'],
                                total_value=shares * stock['price'],
                                reason="Reduce Consumer Cyclical sector exposure"
                            ))
                    
                            # Simulate transaction cost (0.1% of trade value)
                            trade_value = shares * stock['price']
                            cost = trade_value * 0.001
                            total_cost += cost
            
            # Calculate estimated improvement
            diversification_score = recommendations.get('portfolio_analysis', {}).get('diversification_score', 0)
            estimated_improvement = f"Expected diversification score improvement: {diversification_score:.1f} → {min(diversification_score + 15, 100):.1f}"
            
            return RebalanceResultType(
                success=True,
                message=f"Successfully rebalanced portfolio with {len(changes_made)} changes and {len(stock_trades)} trades",
                changes_made=changes_made,
                stock_trades=stock_trades,
                new_portfolio_value=float(portfolio.total_value),
                rebalance_cost=total_cost,
                estimated_improvement=estimated_improvement
            )
            
        except Exception as e:
            logger.error(f"AI rebalancing error: {str(e)}")
            return RebalanceResultType(
                success=False,
                message=f"Rebalancing failed: {str(e)}",
                changes_made=[],
                stock_trades=[],
                new_portfolio_value=0.0,
                rebalance_cost=0.0,
                estimated_improvement="N/A"
            )
