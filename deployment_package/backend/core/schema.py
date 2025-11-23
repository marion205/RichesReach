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
    from .social_types import SocialQueries
except (ImportError, SyntaxError):
    class SocialQueries(graphene.ObjectType):
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

logger = logging.getLogger(__name__)
User = get_user_model()

# -------------------- QUERY --------------------
# Base Query has resolve_me which will be available in ExtendedQuery
# The resolve_me in queries.py should work, but let's ensure it uses proper context

class ExtendedQuery(PremiumQueries, BrokerQueries, BankingQueries, SBLOCQueries, PaperTradingQueries, SocialQueries, PrivacyQueries, AIInsightsQueries, Query, graphene.ObjectType):
    """
    Final Query type exposed by the schema.

    - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
    - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
    - Adds Broker, Banking, and SBLOC queries
    - The base Query class has resolve_me which will be available here
    """
    pass


# ------------------- MUTATION ------------------

class ExtendedMutation(PremiumMutations, BrokerMutations, BankingMutations, SBLOCMutations, PaperTradingMutations, PrivacyMutations, AIInsightsMutations, Mutation, graphene.ObjectType):
    """
    Final Mutation type exposed by the schema.

    - Includes base mutations (create_user, add_to_watchlist, etc.)
    - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
    - Includes Broker, Banking, and SBLOC mutations
    """
    pass


# -------------------- SCHEMA --------------------

# Collect all types that need explicit registration
schema_types = [BenchmarkSeriesType, BenchmarkDataPointType]
if ProfileInput:
    # InputObjectType doesn't need to be in types, but ensure it's imported
    pass
if AIRecommendationsType:
    schema_types.append(AIRecommendationsType)

schema = graphene.Schema(
    query=ExtendedQuery,
    mutation=ExtendedMutation,
    types=schema_types  # Explicitly register types that need it
)
