"""
GraphQL types for portfolio history data
"""
import graphene
from datetime import datetime
from typing import List, Optional


class PortfolioHistoryDataPointType(graphene.ObjectType):
    """Individual data point in portfolio history"""
    date = graphene.String(required=True)
    value = graphene.Float(required=True)
    change = graphene.Float()
    changePercent = graphene.Float()

