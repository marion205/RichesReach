# core/schema.py
import graphene
try:
    import graphql_jwt
except ImportError:
    graphql_jwt = None  # Make it optional for testing

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
    from .premium_types import PremiumQueries, PremiumMutations
except (ImportError, SyntaxError):
    # Create empty classes if premium_types can't be imported
    class PremiumQueries(graphene.ObjectType):
        pass
    class PremiumMutations(graphene.ObjectType):
        pass

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


# -------------------- QUERY --------------------

class ExtendedQuery(PremiumQueries, BrokerQueries, BankingQueries, SBLOCQueries, Query, graphene.ObjectType):
    """
    Final Query type exposed by the schema.

    - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
    - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
    - Adds Broker, Banking, and SBLOC queries
    """
    pass


# ------------------- MUTATION ------------------

class ExtendedMutation(PremiumMutations, BrokerMutations, BankingMutations, SBLOCMutations, Mutation, graphene.ObjectType):
    """
    Final Mutation type exposed by the schema.

    - Includes base mutations (create_user, add_to_watchlist, etc.)
    - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
    - Includes Broker, Banking, and SBLOC mutations
    """
    pass


# -------------------- SCHEMA --------------------

schema = graphene.Schema(
    query=ExtendedQuery,
    mutation=ExtendedMutation,
    types=[]  # Let Graphene auto-discover types
)