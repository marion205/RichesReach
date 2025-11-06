# core/schema.py
import graphene
import graphql_jwt
from .queries import Query
from .mutations import Mutation
from .types import * # Ensure all types are imported
from .premium_types import PremiumQueries, PremiumMutations
from .broker_queries import BrokerQueries
from .broker_mutations import BrokerMutations
from .banking_queries import BankingQueries
from .banking_mutations import BankingMutations
# Create schema with explicit introspection (legacy)
schema = graphene.Schema(
query=Query, 
mutation=Mutation,
types=[] # Let Graphene auto-discover types
)
# Add premium features, broker features, and banking features to the main schema
class ExtendedQuery(Query, PremiumQueries, BrokerQueries, BankingQueries):
    pass
class ExtendedMutation(Mutation, PremiumMutations, BrokerMutations, BankingMutations):
    pass
# Create extended schema with premium features, broker features, and banking features
extended_schema = graphene.Schema(
query=ExtendedQuery,
mutation=ExtendedMutation,
types=[]
)
# Use the extended schema as the main schema
schema = extended_schema