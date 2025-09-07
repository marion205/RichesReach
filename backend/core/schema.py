# core/schema.py
import graphene
import graphql_jwt
from .queries import Query
from .mutations import Mutation
from .types import *  # Ensure all types are imported
from .premium_types import PremiumQueries, PremiumMutations

# Create schema with explicit introspection (legacy)
schema = graphene.Schema(
    query=Query, 
    mutation=Mutation,
    types=[]  # Let Graphene auto-discover types
)

# Add premium features to the main schema
class ExtendedQuery(Query, PremiumQueries):
    pass

class ExtendedMutation(Mutation, PremiumMutations):
    pass

# Create extended schema with premium features
extended_schema = graphene.Schema(
    query=ExtendedQuery,
    mutation=ExtendedMutation,
    types=[]
)

# Use the extended schema as the main schema
schema = extended_schema