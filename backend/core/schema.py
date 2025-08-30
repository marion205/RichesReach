# core/schema.py
import graphene
import graphql_jwt
from .queries import Query
from .mutations import Mutation

schema = graphene.Schema(query=Query, mutation=Mutation)