import graphene
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UnusualActivityType(graphene.ObjectType):
    """Unusual options activity data point"""
    contractSymbol = graphene.String()
    strike = graphene.Float()
    expiration = graphene.String()
    optionType = graphene.String()
    volume = graphene.Int()
    openInterest = graphene.Int()
    volumeVsOI = graphene.Float()
    lastPrice = graphene.Float()
    bid = graphene.Float()
    ask = graphene.Float()
    impliedVolatility = graphene.Float()
    unusualVolumePercent = graphene.Float()
    sweepCount = graphene.Int()
    blockSize = graphene.Int()
    isDarkPool = graphene.Boolean()


class LargestTradeType(graphene.ObjectType):
    """Largest options trade"""
    contractSymbol = graphene.String()
    size = graphene.Int()
    price = graphene.Float()
    time = graphene.String()
    isCall = graphene.Boolean()
    isSweep = graphene.Boolean()
    isBlock = graphene.Boolean()


class OptionsFlowType(graphene.ObjectType):
    """Options flow data for a symbol"""
    symbol = graphene.String()
    timestamp = graphene.String()
    unusualActivity = graphene.List(UnusualActivityType)
    putCallRatio = graphene.Float()
    totalCallVolume = graphene.Int()
    totalPutVolume = graphene.Int()
    largestTrades = graphene.List(LargestTradeType)


class ScannedOptionType(graphene.ObjectType):
    """Scanned option result"""
    symbol = graphene.String()
    contractSymbol = graphene.String()
    strike = graphene.Float()
    expiration = graphene.String()
    optionType = graphene.String()
    bid = graphene.Float()
    ask = graphene.Float()
    volume = graphene.Int()
    impliedVolatility = graphene.Float()
    delta = graphene.Float()
    theta = graphene.Float()
    score = graphene.Int()
    opportunity = graphene.String()

