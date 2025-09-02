# core/schema.py
import graphene
import graphql_jwt
from .queries import Query
from .mutations import Mutation
from .types import *  # Ensure all types are imported

# Create schema with explicit introspection
schema = graphene.Schema(
    query=Query, 
    mutation=Mutation,
    types=[]  # Let Graphene auto-discover types
)