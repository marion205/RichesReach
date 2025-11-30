"""
GraphQL types and resolvers for risk management calculations
"""
import graphene
from .graphql_utils import get_user_from_context


class PositionSizeType(graphene.ObjectType):
    """Position size calculation result"""
    positionSize = graphene.Int()
    dollarRisk = graphene.Float()
    positionValue = graphene.Float()
    positionPct = graphene.Float()
    riskPerTradePct = graphene.Float()
    method = graphene.String()
    riskPerShare = graphene.Float()
    maxSharesFixedRisk = graphene.Int()
    maxSharesPosition = graphene.Int()


class DynamicStopType(graphene.ObjectType):
    """Dynamic stop loss calculation result"""
    stopPrice = graphene.Float()
    stopDistance = graphene.Float()
    riskPercentage = graphene.Float()
    method = graphene.String()
    atrStop = graphene.Float()
    srStop = graphene.Float()
    pctStop = graphene.Float()


class TargetPriceType(graphene.ObjectType):
    """Target price calculation result"""
    targetPrice = graphene.Float()
    rewardDistance = graphene.Float()
    riskRewardRatio = graphene.Float()
    method = graphene.String()
    rrTarget = graphene.Float()
    atrTarget = graphene.Float()
    srTarget = graphene.Float()


class RiskManagementQueries(graphene.ObjectType):
    """Risk management calculation queries"""
    
    calculatePositionSize = graphene.Field(
        PositionSizeType,
        accountEquity=graphene.Float(required=True),
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskPerTrade=graphene.Float(),
        maxPositionPct=graphene.Float(),
        confidence=graphene.Float(),
        description="Calculate optimal position size based on risk parameters"
    )
    
    calculateDynamicStop = graphene.Field(
        DynamicStopType,
        entryPrice=graphene.Float(required=True),
        atr=graphene.Float(required=True),
        atrMultiplier=graphene.Float(),
        supportLevel=graphene.Float(),
        resistanceLevel=graphene.Float(),
        signalType=graphene.String(),
        description="Calculate dynamic stop loss based on ATR and support/resistance"
    )
    
    calculateTargetPrice = graphene.Field(
        TargetPriceType,
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskRewardRatio=graphene.Float(),
        atr=graphene.Float(),
        resistanceLevel=graphene.Float(),
        supportLevel=graphene.Float(),
        signalType=graphene.String(),
        description="Calculate target price based on risk/reward ratio and technical levels"
    )
    
    def resolve_calculatePositionSize(
        self, info,
        accountEquity: float,
        entryPrice: float,
        stopPrice: float,
        riskPerTrade: float = None,
        maxPositionPct: float = None,
        confidence: float = None
    ):
        """Calculate position size"""
        from decimal import Decimal
        
        # Default risk per trade: 1% if not specified
        risk_per_trade_pct = Decimal(str(riskPerTrade)) if riskPerTrade else Decimal('0.01')
        max_position_pct = Decimal(str(maxPositionPct)) if maxPositionPct else Decimal('0.10')  # 10% max
        
        # Calculate risk per share
        risk_per_share = abs(entryPrice - stopPrice)
        if risk_per_share == 0:
            return PositionSizeType(
                positionSize=0,
                dollarRisk=0.0,
                positionValue=0.0,
                positionPct=0.0,
                riskPerTradePct=float(risk_per_trade_pct),
                method="invalid",
                riskPerShare=0.0,
                maxSharesFixedRisk=0,
                maxSharesPosition=0
            )
        
        # Calculate max dollars at risk
        account_equity = Decimal(str(accountEquity))
        max_dollars_at_risk = account_equity * risk_per_trade_pct
        
        # Calculate shares based on fixed risk
        max_shares_fixed_risk = int(float(max_dollars_at_risk) / risk_per_share)
        
        # Calculate shares based on max position size
        max_position_value = account_equity * max_position_pct
        max_shares_position = int(float(max_position_value) / entryPrice)
        
        # Use the smaller of the two
        position_size = min(max_shares_fixed_risk, max_shares_position)
        
        # Calculate actual values
        dollar_risk = float(position_size * risk_per_share)
        position_value = float(position_size * entryPrice)
        position_pct = float((position_value / account_equity) * 100) if account_equity > 0 else 0.0
        
        # Adjust for confidence if provided
        if confidence and 0 < confidence < 1:
            position_size = int(position_size * confidence)
            dollar_risk = float(position_size * risk_per_share)
            position_value = float(position_size * entryPrice)
            position_pct = float((position_value / account_equity) * 100) if account_equity > 0 else 0.0
        
        method = "fixed_risk" if max_shares_fixed_risk <= max_shares_position else "max_position"
        
        return PositionSizeType(
            positionSize=position_size,
            dollarRisk=dollar_risk,
            positionValue=position_value,
            positionPct=position_pct,
            riskPerTradePct=float(risk_per_trade_pct * 100),  # Convert to percentage
            method=method,
            riskPerShare=float(risk_per_share),
            maxSharesFixedRisk=max_shares_fixed_risk,
            maxSharesPosition=max_shares_position
        )
    
    def resolve_calculateDynamicStop(
        self, info,
        entryPrice: float,
        atr: float,
        atrMultiplier: float = None,
        supportLevel: float = None,
        resistanceLevel: float = None,
        signalType: str = None
    ):
        """Calculate dynamic stop loss"""
        # Default ATR multiplier: 2.0
        atr_multiplier = atrMultiplier if atrMultiplier else 2.0
        
        # Determine if long or short based on signal type
        is_long = signalType != "SHORT" if signalType else True
        
        # Calculate ATR-based stop
        atr_stop_distance = atr * atr_multiplier
        if is_long:
            atr_stop = entryPrice - atr_stop_distance
        else:
            atr_stop = entryPrice + atr_stop_distance
        
        # Calculate support/resistance stop
        sr_stop = None
        if is_long and supportLevel:
            sr_stop = supportLevel * 0.995  # 0.5% below support
        elif not is_long and resistanceLevel:
            sr_stop = resistanceLevel * 1.005  # 0.5% above resistance
        
        # Calculate percentage-based stop (2% default)
        pct_stop_distance = entryPrice * 0.02
        if is_long:
            pct_stop = entryPrice - pct_stop_distance
        else:
            pct_stop = entryPrice + pct_stop_distance
        
        # Choose the best stop (closest to entry for long, farthest for short)
        stops = [s for s in [atr_stop, sr_stop, pct_stop] if s is not None]
        if is_long:
            stop_price = max(stops)  # Highest stop (closest to entry)
        else:
            stop_price = min(stops)  # Lowest stop (closest to entry)
        
        stop_distance = abs(entryPrice - stop_price)
        risk_percentage = (stop_distance / entryPrice) * 100 if entryPrice > 0 else 0.0
        
        # Determine method
        if sr_stop and abs(stop_price - sr_stop) < abs(stop_price - atr_stop):
            method = "support_resistance"
        elif abs(stop_price - atr_stop) < abs(stop_price - pct_stop):
            method = "atr"
        else:
            method = "percentage"
        
        return DynamicStopType(
            stopPrice=stop_price,
            stopDistance=stop_distance,
            riskPercentage=risk_percentage,
            method=method,
            atrStop=atr_stop,
            srStop=sr_stop if sr_stop else None,
            pctStop=pct_stop
        )
    
    def resolve_calculateTargetPrice(
        self, info,
        entryPrice: float,
        stopPrice: float,
        riskRewardRatio: float = None,
        atr: float = None,
        resistanceLevel: float = None,
        supportLevel: float = None,
        signalType: str = None
    ):
        """Calculate target price"""
        # Calculate risk distance
        risk_distance = abs(entryPrice - stopPrice)
        
        # Default risk/reward ratio: 2:1
        rr_ratio = riskRewardRatio if riskRewardRatio else 2.0
        
        # Determine if long or short
        is_long = signalType != "SHORT" if signalType else entryPrice > stopPrice
        
        # Calculate R:R-based target
        reward_distance = risk_distance * rr_ratio
        if is_long:
            rr_target = entryPrice + reward_distance
        else:
            rr_target = entryPrice - reward_distance
        
        # Calculate ATR-based target (if ATR provided)
        atr_target = None
        if atr:
            atr_target_distance = atr * 2.0  # 2x ATR
            if is_long:
                atr_target = entryPrice + atr_target_distance
            else:
                atr_target = entryPrice - atr_target_distance
        
        # Calculate support/resistance target
        sr_target = None
        if is_long and resistanceLevel:
            sr_target = resistanceLevel * 0.995  # Just below resistance
        elif not is_long and supportLevel:
            sr_target = supportLevel * 1.005  # Just above support
        
        # Choose the best target
        targets = [t for t in [rr_target, atr_target, sr_target] if t is not None]
        if is_long:
            target_price = min(targets)  # Lowest target (most conservative)
        else:
            target_price = max(targets)  # Highest target (most conservative)
        
        # Calculate final reward distance
        final_reward_distance = abs(target_price - entryPrice)
        final_rr_ratio = final_reward_distance / risk_distance if risk_distance > 0 else 0.0
        
        # Determine method
        if sr_target and abs(target_price - sr_target) < abs(target_price - rr_target):
            method = "support_resistance"
        elif atr_target and abs(target_price - atr_target) < abs(target_price - rr_target):
            method = "atr"
        else:
            method = "risk_reward"
        
        return TargetPriceType(
            targetPrice=target_price,
            rewardDistance=final_reward_distance,
            riskRewardRatio=final_rr_ratio,
            method=method,
            rrTarget=rr_target,
            atrTarget=atr_target if atr_target else None,
            srTarget=sr_target if sr_target else None
        )

