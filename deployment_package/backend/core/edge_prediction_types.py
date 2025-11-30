# core/edge_prediction_types.py
import graphene
from decimal import Decimal


class EdgePredictionType(graphene.ObjectType):
    """GraphQL type for edge prediction (mispricing forecast)"""
    strike = graphene.Float(required=True)
    expiration = graphene.String(required=True)
    option_type = graphene.String(required=True)  # "call" or "put"
    current_edge = graphene.Float(required=True)  # Current edge % (mispricing)
    predicted_edge_15min = graphene.Float(required=True)  # Predicted edge in 15min
    predicted_edge_1hr = graphene.Float(required=True)  # Predicted edge in 1hr
    predicted_edge_1day = graphene.Float(required=True)  # Predicted edge in 1day
    confidence = graphene.Float(required=True)  # 0-100%
    explanation = graphene.String(required=True)  # "IV crush expected post-earnings"
    edge_change_dollars = graphene.Float(required=True)  # Expected $ change per contract
    current_premium = graphene.Float(required=True)  # Current option premium
    predicted_premium_15min = graphene.Float(required=True)  # Predicted premium in 15min
    predicted_premium_1hr = graphene.Float(required=True)  # Predicted premium in 1hr

