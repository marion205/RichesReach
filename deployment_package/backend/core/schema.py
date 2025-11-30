# core/schema.py
import logging
import graphene
from django.contrib.auth import get_user_model

# Import base Query and Mutation
from .queries import Query
try:
    from .mutations import Mutation
except (ImportError, SyntaxError):
    # Create empty Mutation class if mutations can't be imported
    class Mutation(graphene.ObjectType):
        pass

# Import all types to ensure they're registered
from .types import *
from .benchmark_types import BenchmarkSeriesType, BenchmarkDataPointType
from .broker_types import BrokerAccountType, BrokerOrderType, BrokerPositionType

# Import premium queries and mutations
try:
    from .premium_types import PremiumQueries, PremiumMutations, ProfileInput, AIRecommendationsType
except (ImportError, SyntaxError):
    # Create empty classes if premium_types can't be imported
    class PremiumQueries(graphene.ObjectType):
        pass
    class PremiumMutations(graphene.ObjectType):
        pass
    ProfileInput = None
    AIRecommendationsType = None

# Import other feature modules (optional - create empty if not available)
try:
    from .broker_queries import BrokerQueries
except (ImportError, SyntaxError):
    class BrokerQueries(graphene.ObjectType):
        pass

try:
    from .broker_mutations import BrokerMutations
except (ImportError, SyntaxError):
    class BrokerMutations(graphene.ObjectType):
        pass

try:
    from .banking_queries import BankingQueries
except (ImportError, SyntaxError):
    class BankingQueries(graphene.ObjectType):
        pass

try:
    from .banking_mutations import BankingMutations
except (ImportError, SyntaxError):
    class BankingMutations(graphene.ObjectType):
        pass

try:
    from .sbloc_queries import SBLOCQueries
except (ImportError, SyntaxError):
    class SBLOCQueries(graphene.ObjectType):
        pass

try:
    from .sbloc_mutations import SBLOCMutations
except (ImportError, SyntaxError):
    class SBLOCMutations(graphene.ObjectType):
        pass

try:
    from .paper_trading_types import PaperTradingQueries, PaperTradingMutations
except (ImportError, SyntaxError):
    class PaperTradingQueries(graphene.ObjectType):
        pass
    class PaperTradingMutations(graphene.ObjectType):
        pass

try:
    from .social_types import SocialQueries, SocialMutations
except (ImportError, SyntaxError):
    class SocialQueries(graphene.ObjectType):
        pass
    class SocialMutations(graphene.ObjectType):
        pass

try:
    from .privacy_types import PrivacyQueries, PrivacyMutations
except (ImportError, SyntaxError):
    class PrivacyQueries(graphene.ObjectType):
        pass
    class PrivacyMutations(graphene.ObjectType):
        pass

try:
    from .ai_insights_types import AIInsightsQueries, AIInsightsMutations
except (ImportError, SyntaxError):
    class AIInsightsQueries(graphene.ObjectType):
        pass
    class AIInsightsMutations(graphene.ObjectType):
        pass

try:
    from .ai_scans_types import AIScansQueries
except (ImportError, SyntaxError):
    class AIScansQueries(graphene.ObjectType):
        pass

logger = logging.getLogger(__name__)
User = get_user_model()

# -------------------- QUERY --------------------
# Base Query has resolve_me which will be available in ExtendedQuery
# The resolve_me in queries.py should work, but let's ensure it uses proper context

try:
    from .risk_management_types import RiskManagementQueries
except (ImportError, SyntaxError):
    class RiskManagementQueries(graphene.ObjectType):
        pass

class ExtendedQuery(PremiumQueries, BrokerQueries, BankingQueries, SBLOCQueries, PaperTradingQueries, SocialQueries, PrivacyQueries, AIInsightsQueries, AIScansQueries, RiskManagementQueries, Query, graphene.ObjectType):
    """
    Final Query type exposed by the schema.

    - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
    - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
    - Adds Broker, Banking, and SBLOC queries
    - The base Query class has resolve_me which will be available here
    """
    
    # Legacy aliases for backward compatibility with mobile app
    # These map old field names to new canonical names
    
    alpaca_account = graphene.Field(
        BrokerAccountType,
        user_id=graphene.Int(required=True),
        name='alpacaAccount',
        description="Deprecated alias for brokerAccount. Use brokerAccount instead."
    )
    
    trading_account = graphene.Field(
        BrokerAccountType,
        name='tradingAccount',
        description="Deprecated alias for brokerAccount. Use brokerAccount instead."
    )
    
    trading_positions = graphene.List(
        BrokerPositionType,
        name='tradingPositions',
        description="Deprecated alias for brokerPositions. Use brokerPositions instead."
    )
    
    trading_orders = graphene.List(
        BrokerOrderType,
        status=graphene.String(),
        limit=graphene.Int(),
        name='tradingOrders',
        description="Deprecated alias for brokerOrders. Use brokerOrders instead."
    )
    
    # Note: stockChartData resolver will be implemented to return proper chart data
    # For now, this field exists to prevent GraphQL schema errors
    stock_chart_data = graphene.JSONString(
        symbol=graphene.String(required=True),
        timeframe=graphene.String(required=True),
        name='stockChartData',
        description="Get stock chart data (OHLCV) for a symbol and timeframe. Returns JSON with data array, currentPrice, change, changePercent."
    )
    
    def resolve_alpaca_account(self, info, user_id):
        """Legacy alias: resolve alpacaAccount by delegating to brokerAccount"""
        # For now, just return the current user's broker account
        # The old API took user_id, but new API uses authenticated user
        user = info.context.user
        if not user.is_authenticated:
            return None
        return self.resolve_broker_account(info)
    
    def resolve_trading_account(self, info):
        """Legacy alias: resolve tradingAccount by delegating to brokerAccount"""
        return self.resolve_broker_account(info)
    
    def resolve_trading_positions(self, info, **kwargs):
        """Legacy alias: resolve tradingPositions by delegating to brokerPositions"""
        return self.resolve_broker_positions(info)
    
    def resolve_trading_orders(self, info, status=None, limit=None):
        """Legacy alias: resolve tradingOrders by delegating to brokerOrders"""
        return self.resolve_broker_orders(info, status=status, limit=limit or 50)
    
    def resolve_stock_chart_data(self, info, symbol, timeframe):
        """Resolve stockChartData - returns chart data in the format expected by frontend"""
        # TODO: Implement proper chart data fetching from market data APIs
        # For now, return None to prevent errors but allow the query to succeed
        logger.warning(f"stockChartData called for {symbol} with timeframe {timeframe} - returning None (not yet fully implemented)")
        return None


# ------------------- MUTATION ------------------

class ExtendedMutation(PremiumMutations, BrokerMutations, BankingMutations, SBLOCMutations, PaperTradingMutations, SocialMutations, PrivacyMutations, AIInsightsMutations, Mutation, graphene.ObjectType):
    """
    Final Mutation type exposed by the schema.

    - Includes base mutations (create_user, add_to_watchlist, etc.)
    - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
    - Includes Broker, Banking, and SBLOC mutations
    """
    pass


# -------------------- SCHEMA --------------------

# Collect all types that need explicit registration
try:
    from .sbloc_types import SBLOCBankType, SBLOCSessionType
    SBLOC_TYPES_AVAILABLE = True
except ImportError:
    SBLOC_TYPES_AVAILABLE = False
    SBLOCBankType = None
    SBLOCSessionType = None

# Import Rust types explicitly to ensure they're registered
try:
    from .types import RustOptionsAnalysisType, ForexAnalysisType, SentimentAnalysisType, CorrelationAnalysisType
    RUST_TYPES_AVAILABLE = True
except ImportError:
    RUST_TYPES_AVAILABLE = False
    RustOptionsAnalysisType = None
    ForexAnalysisType = None
    SentimentAnalysisType = None
    CorrelationAnalysisType = None

schema_types = [BenchmarkSeriesType, BenchmarkDataPointType]
if ProfileInput:
    # InputObjectType doesn't need to be in types, but ensure it's imported
    pass
if AIRecommendationsType:
    schema_types.append(AIRecommendationsType)
if SBLOC_TYPES_AVAILABLE and SBLOCBankType:
    schema_types.append(SBLOCBankType)
    if SBLOCSessionType:
        schema_types.append(SBLOCSessionType)
if RUST_TYPES_AVAILABLE and RustOptionsAnalysisType:
    schema_types.append(RustOptionsAnalysisType)
    if ForexAnalysisType:
        schema_types.append(ForexAnalysisType)
    if SentimentAnalysisType:
        schema_types.append(SentimentAnalysisType)
    if CorrelationAnalysisType:
        schema_types.append(CorrelationAnalysisType)

schema = graphene.Schema(
    query=ExtendedQuery,
    mutation=ExtendedMutation,
    types=schema_types
)
