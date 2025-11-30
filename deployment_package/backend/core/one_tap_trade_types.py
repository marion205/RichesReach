# core/one_tap_trade_types.py
import graphene
from decimal import Decimal


class OneTapLegType(graphene.ObjectType):
    """GraphQL type for one-tap trade leg"""
    action = graphene.String(required=True)  # "buy" or "sell"
    option_type = graphene.String(required=True)  # "call" or "put"
    strike = graphene.Float(required=True)
    expiration = graphene.String(required=True)
    quantity = graphene.Int(required=True)
    premium = graphene.Float(required=True)


class OneTapTradeType(graphene.ObjectType):
    """GraphQL type for one-tap trade recommendation"""
    strategy = graphene.String(required=True)
    entry_price = graphene.Float(required=True)
    expected_edge = graphene.Float(required=True)
    confidence = graphene.Float(required=True)
    take_profit = graphene.Float(required=True)
    stop_loss = graphene.Float(required=True)
    reasoning = graphene.String(required=True)
    max_loss = graphene.Float(required=True)
    max_profit = graphene.Float(required=True)
    probability_of_profit = graphene.Float(required=True)
    symbol = graphene.String(required=True)
    legs = graphene.List(OneTapLegType, required=True)
    strategy_type = graphene.String(required=True)
    days_to_expiration = graphene.Int(required=True)
    total_cost = graphene.Float(required=True)
    total_credit = graphene.Float(required=True)

