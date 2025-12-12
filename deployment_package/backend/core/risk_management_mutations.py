"""
GraphQL Mutations for Risk Management
- Create position
- Check position exits
- Update risk settings
"""
import graphene
import logging
from .graphql_utils import get_user_from_context
from graphene.types import JSONString

logger = logging.getLogger(__name__)


class PositionResultType(graphene.ObjectType):
    """Position creation result"""
    symbol = graphene.String()
    side = graphene.String()
    entryPrice = graphene.Float()
    quantity = graphene.Int()
    entryTime = graphene.String()
    stopLossPrice = graphene.Float()
    takeProfitPrice = graphene.Float()
    maxHoldUntil = graphene.String()
    atrStopPrice = graphene.Float()


class CreatePositionResultType(graphene.ObjectType):
    """Result of creating a position"""
    success = graphene.Boolean()
    message = graphene.String()
    position = graphene.Field(PositionResultType)


class ExitedPositionType(graphene.ObjectType):
    """Exited position information"""
    symbol = graphene.String()
    side = graphene.String()
    entryPrice = graphene.Float()
    exitPrice = graphene.Float()
    quantity = graphene.Int()
    pnl = graphene.Float()
    exitReason = graphene.String()
    exitTime = graphene.String()


class CheckExitsResultType(graphene.ObjectType):
    """Result of checking position exits"""
    success = graphene.Boolean()
    message = graphene.String()
    exitedPositions = graphene.List(ExitedPositionType)


class UpdateRiskSettingsResultType(graphene.ObjectType):
    """Result of updating risk settings"""
    success = graphene.Boolean()
    message = graphene.String()
    currentSettings = graphene.Field('core.risk_management_queries.RiskSummaryType')


class CreatePosition(graphene.Mutation):
    """Create a new position with risk management"""
    class Arguments:
        symbol = graphene.String(required=True)
        side = graphene.String(required=True)
        price = graphene.Float(required=True)
        quantity = graphene.Int()
        atr = graphene.Float(required=True)
        sector = graphene.String()
        confidence = graphene.Float()
    
    Output = CreatePositionResultType
    
    def mutate(self, info, symbol, side, price, atr, quantity=None, sector=None, confidence=None):
        """Create a new position"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return CreatePositionResultType(
                    success=False,
                    message="Authentication required"
                )
            
            # In production, this would create position in database
            # Calculate position size based on risk parameters
            if quantity is None:
                # Calculate optimal quantity based on ATR and risk
                account_value = 100000.0  # Would get from user account
                risk_per_trade = 0.01  # 1% risk per trade
                max_risk = account_value * risk_per_trade
                stop_distance = atr * 2.0  # 2x ATR stop
                quantity = int(max_risk / stop_distance) if stop_distance > 0 else 0
            
            # Calculate stop and target prices
            stop_loss = price - (atr * 2.0) if side == "LONG" else price + (atr * 2.0)
            take_profit = price + (atr * 4.0) if side == "LONG" else price - (atr * 4.0)
            
            position = PositionResultType(
                symbol=symbol,
                side=side,
                entryPrice=price,
                quantity=quantity,
                entryTime="2024-01-01T12:00:00Z",
                stopLossPrice=stop_loss,
                takeProfitPrice=take_profit,
                maxHoldUntil="2024-01-08T12:00:00Z",
                atrStopPrice=stop_loss
            )
            
            return CreatePositionResultType(
                success=True,
                message=f"Position created: {quantity} shares of {symbol}",
                position=position
            )
        except Exception as e:
            logger.error(f"Error creating position: {e}", exc_info=True)
            return CreatePositionResultType(
                success=False,
                message=str(e)
            )


class CheckPositionExits(graphene.Mutation):
    """Check if any positions should be exited"""
    class Arguments:
        currentPrices = JSONString()
    
    Output = CheckExitsResultType
    
    def mutate(self, info, currentPrices=None):
        """Check if positions should be exited"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return CheckExitsResultType(
                    success=False,
                    message="Authentication required",
                    exitedPositions=[]
                )
            
            # In production, this would check positions against current prices
            # For now, return empty list
            return CheckExitsResultType(
                success=True,
                message="Position exit check completed",
                exitedPositions=[]
            )
        except Exception as e:
            logger.error(f"Error checking position exits: {e}", exc_info=True)
            return CheckExitsResultType(
                success=False,
                message=str(e),
                exitedPositions=[]
            )
    
class UpdateRiskSettings(graphene.Mutation):
    """Update risk management settings"""
    class Arguments:
        accountValue = graphene.Float()
        riskLevel = graphene.String()
    
    Output = UpdateRiskSettingsResultType
    
    def mutate(self, info, accountValue=None, riskLevel=None):
        """Update risk settings"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return UpdateRiskSettingsResultType(
                    success=False,
                    message="Authentication required"
                )
            
            # In production, this would update settings in database
            from .risk_management_queries import RiskSummaryType, RiskLimitsType
            
            current_settings = RiskSummaryType(
                accountValue=accountValue or 100000.0,
                dailyPnl=0.0,
                dailyPnlPct=0.0,
                dailyTrades=0,
                activePositions=0,
                totalExposure=0.0,
                exposurePct=0.0,
                sectorExposure={},
                riskLevel=riskLevel or "MODERATE",
                riskLimits=RiskLimitsType(
                    maxPositionSize=10000.0,
                    maxDailyLoss=2000.0,
                    maxConcurrentTrades=10,
                    maxSectorExposure=0.5
                )
            )
            
            return UpdateRiskSettingsResultType(
                success=True,
                message="Risk settings updated",
                currentSettings=current_settings
            )
        except Exception as e:
            logger.error(f"Error updating risk settings: {e}", exc_info=True)
            return UpdateRiskSettingsResultType(
                success=False,
                message=str(e)
            )

