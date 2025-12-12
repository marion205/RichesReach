"""
GraphQL Queries for Risk Management
- Risk summary
- Active positions
"""
import graphene
import logging
from .graphql_utils import get_user_from_context
from graphene.types import JSONString

logger = logging.getLogger(__name__)


class RiskLimitsType(graphene.ObjectType):
    """Risk limits configuration"""
    maxPositionSize = graphene.Float()
    maxDailyLoss = graphene.Float()
    maxConcurrentTrades = graphene.Int()
    maxSectorExposure = graphene.Float()


class RiskSummaryType(graphene.ObjectType):
    """Risk summary for user's account"""
    accountValue = graphene.Float()
    dailyPnl = graphene.Float()
    dailyPnlPct = graphene.Float()
    dailyTrades = graphene.Int()
    activePositions = graphene.Int()
    totalExposure = graphene.Float()
    exposurePct = graphene.Float()
    sectorExposure = JSONString()
    riskLevel = graphene.String()
    riskLimits = graphene.Field(RiskLimitsType)


class PositionType(graphene.ObjectType):
    """Active position information"""
    symbol = graphene.String()
    side = graphene.String()
    entryPrice = graphene.Float()
    quantity = graphene.Int()
    entryTime = graphene.String()
    stopLossPrice = graphene.Float()
    takeProfitPrice = graphene.Float()
    maxHoldUntil = graphene.String()
    atrStopPrice = graphene.Float()
    currentPnl = graphene.Float()
    timeRemainingMinutes = graphene.Int()


# Extend RiskManagementQueries
class RiskManagementQueriesExtended(graphene.ObjectType):
    """Extended risk management queries"""
    
    riskSummary = graphene.Field(
        RiskSummaryType,
        description="Get risk summary for user's account"
    )
    
    getActivePositions = graphene.List(
        PositionType,
        description="Get active positions"
    )
    
    def resolve_riskSummary(self, info):
        """Get risk summary"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return None
            
            # In production, this would query from database
            # For now, return mock data
            return RiskSummaryType(
                accountValue=100000.0,
                dailyPnl=1250.0,
                dailyPnlPct=1.25,
                dailyTrades=5,
                activePositions=3,
                totalExposure=45000.0,
                exposurePct=45.0,
                sectorExposure={"Technology": 0.3, "Healthcare": 0.15},
                riskLevel="MODERATE",
                riskLimits=RiskLimitsType(
                    maxPositionSize=10000.0,
                    maxDailyLoss=2000.0,
                    maxConcurrentTrades=10,
                    maxSectorExposure=0.5
                )
            )
        except Exception as e:
            logger.error(f"Error resolving risk summary: {e}", exc_info=True)
            return None
    
    def resolve_getActivePositions(self, info):
        """Get active positions"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return []
            
            # In production, this would query from database
            # For now, return mock data
            return [
                PositionType(
                    symbol="AAPL",
                    side="LONG",
                    entryPrice=150.0,
                    quantity=100,
                    entryTime="2024-01-01T10:00:00Z",
                    stopLossPrice=145.0,
                    takeProfitPrice=160.0,
                    maxHoldUntil="2024-01-08T10:00:00Z",
                    atrStopPrice=144.5,
                    currentPnl=500.0,
                    timeRemainingMinutes=4320
                ),
                PositionType(
                    symbol="MSFT",
                    side="LONG",
                    entryPrice=380.0,
                    quantity=50,
                    entryTime="2024-01-01T11:00:00Z",
                    stopLossPrice=370.0,
                    takeProfitPrice=400.0,
                    maxHoldUntil="2024-01-08T11:00:00Z",
                    atrStopPrice=369.0,
                    currentPnl=750.0,
                    timeRemainingMinutes=4260
                )
            ]
        except Exception as e:
            logger.error(f"Error resolving active positions: {e}", exc_info=True)
            return []

