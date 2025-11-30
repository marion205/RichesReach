# core/iv_forecast_types.py
import graphene
from decimal import Decimal


class IVChangePointType(graphene.ObjectType):
    """GraphQL type for IV change point in heatmap"""
    strike = graphene.Float(required=True)
    expiration = graphene.String(required=True)
    current_iv = graphene.Float(required=True)
    predicted_iv_1hr = graphene.Float(required=True)
    predicted_iv_24hr = graphene.Float(required=True)
    iv_change_1hr_pct = graphene.Float(required=True)
    iv_change_24hr_pct = graphene.Float(required=True)
    confidence = graphene.Float(required=True)


class IVSurfaceForecastType(graphene.ObjectType):
    """GraphQL type for IV surface forecast"""
    symbol = graphene.String(required=True)
    current_iv = graphene.JSONString(required=True)  # expiration -> IV map
    predicted_iv_1hr = graphene.JSONString(required=True)
    predicted_iv_24hr = graphene.JSONString(required=True)
    confidence = graphene.Float(required=True)
    regime = graphene.String(required=True)
    iv_change_heatmap = graphene.List(IVChangePointType, required=True)
    timestamp = graphene.String(required=True)

