# richesreach/schema.py
import graphene
from core.crypto_graphql import Query as CryptoQuery, Mutation as CryptoMutation
# from marketdata.schema import MarketDataQuery, MarketDataMutation

class Query(CryptoQuery, graphene.ObjectType):
    pass

class Mutation(CryptoMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)