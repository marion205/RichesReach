# richesreach/schema.py
import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello from RichesReach GraphQL!")

schema = graphene.Schema(query=Query)