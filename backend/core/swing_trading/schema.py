"""
Swing Trading GraphQL Schema
"""
import graphene
from .graphql_queries import SwingTradingQuery
from .graphql_mutations import SwingTradingMutation


class SwingTradingSchema(graphene.Schema):
    """Swing Trading GraphQL Schema"""
    
    query = SwingTradingQuery
    mutation = SwingTradingMutation


# Create the schema instance
swing_trading_schema = SwingTradingSchema()
