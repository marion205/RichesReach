"""
GraphQL types for benchmark data
"""
import graphene
from datetime import datetime
from typing import List, Optional


class BenchmarkDataPointType(graphene.ObjectType):
    """Individual data point in a benchmark series"""
    timestamp = graphene.String(required=True)
    value = graphene.Float(required=True)
    change = graphene.Float()
    changePercent = graphene.Float()


class BenchmarkSeriesType(graphene.ObjectType):
    """Benchmark series data for a given symbol and timeframe"""
    symbol = graphene.String(required=True)
    name = graphene.String(required=True)
    timeframe = graphene.String(required=True)
    dataPoints = graphene.List(BenchmarkDataPointType, required=True)
    startValue = graphene.Float(required=True)
    endValue = graphene.Float(required=True)
    totalReturn = graphene.Float(required=True)
    totalReturnPercent = graphene.Float(required=True)
    volatility = graphene.Float()

