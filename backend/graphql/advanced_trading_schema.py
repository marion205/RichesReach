"""
Enhanced GraphQL Schema for Advanced Trading
Comprehensive schema for advanced orders, risk management, and ML features
"""

import graphene
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import logging

from ..algo.advanced_orders import AdvancedOrderType, OrderStatus
from ..algo.risk_management import RiskLevel
from ..broker.adapters.base import OrderSide, OrderType


# Enums
class AdvancedOrderTypeEnum(graphene.Enum):
    BRACKET = "BRACKET"
    OCO = "OCO"
    ICEBERG = "ICEBERG"
    TRAILING_STOP = "TRAILING_STOP"
    SCALE_IN = "SCALE_IN"
    SCALE_OUT = "SCALE_OUT"
    TWAP = "TWAP"
    VWAP = "VWAP"


class OrderStatusEnum(graphene.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class RiskLevelEnum(graphene.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class OrderSideEnum(graphene.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderTypeEnum(graphene.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


# Input Types
class BracketOrderInput(graphene.InputObjectType):
    symbol = graphene.String(required=True)
    side = OrderSideEnum(required=True)
    quantity = graphene.Int(required=True)
    entry_price = graphene.Float(required=True)
    stop_loss = graphene.Float(required=True)
    take_profit_1 = graphene.Float(required=True)
    take_profit_2 = graphene.Float()


class OCOOrderInput(graphene.InputObjectType):
    symbol = graphene.String(required=True)
    side = OrderSideEnum(required=True)
    quantity = graphene.Int(required=True)
    order_1_price = graphene.Float(required=True)
    order_1_type = OrderTypeEnum(required=True)
    order_2_price = graphene.Float(required=True)
    order_2_type = OrderTypeEnum(required=True)


class IcebergOrderInput(graphene.InputObjectType):
    symbol = graphene.String(required=True)
    side = OrderSideEnum(required=True)
    total_quantity = graphene.Int(required=True)
    visible_quantity = graphene.Int(required=True)
    price = graphene.Float(required=True)


class TrailingStopInput(graphene.InputObjectType):
    symbol = graphene.String(required=True)
    side = OrderSideEnum(required=True)
    quantity = graphene.Int(required=True)
    trail_amount = graphene.Float(required=True)
    trail_percent = graphene.Float()


class TWAPOrderInput(graphene.InputObjectType):
    symbol = graphene.String(required=True)
    side = OrderSideEnum(required=True)
    total_quantity = graphene.Int(required=True)
    duration_minutes = graphene.Int(required=True)
    price_limit = graphene.Float()


class VWAPOrderInput(graphene.InputObjectType):
    symbol = graphene.String(required=True)
    side = OrderSideEnum(required=True)
    total_quantity = graphene.Int(required=True)
    duration_minutes = graphene.Int(required=True)
    price_limit = graphene.Float()


class RiskAssessmentInput(graphene.InputObjectType):
    symbol = graphene.String(required=True)
    mode = graphene.String(default_value="SAFE")


# Output Types
class OrderExecutionResult(graphene.ObjectType):
    success = graphene.Boolean()
    order_id = graphene.String()
    message = graphene.String()
    execution_details = graphene.JSONString()


class BracketOrderType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    quantity = graphene.Int()
    entry_price = graphene.Float()
    stop_loss = graphene.Float()
    take_profit_1 = graphene.Float()
    take_profit_2 = graphene.Float()
    status = OrderStatusEnum()
    filled_quantity = graphene.Int()
    average_fill_price = graphene.Float()
    created_at = graphene.String()
    updated_at = graphene.String()


class OCOOrderType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    quantity = graphene.Int()
    order_1_price = graphene.Float()
    order_1_type = graphene.String()
    order_2_price = graphene.Float()
    order_2_type = graphene.String()
    status = OrderStatusEnum()
    active_order_id = graphene.String()
    created_at = graphene.String()
    updated_at = graphene.String()


class IcebergOrderType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    total_quantity = graphene.Int()
    visible_quantity = graphene.Int()
    price = graphene.Float()
    status = OrderStatusEnum()
    filled_quantity = graphene.Int()
    remaining_quantity = graphene.Int()
    created_at = graphene.String()
    updated_at = graphene.String()


class TrailingStopType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    quantity = graphene.Int()
    trail_amount = graphene.Float()
    trail_percent = graphene.Float()
    status = OrderStatusEnum()
    current_stop_price = graphene.Float()
    highest_price = graphene.Float()
    lowest_price = graphene.Float()
    created_at = graphene.String()
    updated_at = graphene.String()


class TWAPExecutionType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    total_quantity = graphene.Int()
    total_filled = graphene.Int()
    average_price = graphene.Float()
    duration_minutes = graphene.Int()
    execution_results = graphene.JSONString()
    completed_at = graphene.String()


class VWAPExecutionType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    total_quantity = graphene.Int()
    total_filled = graphene.Int()
    average_price = graphene.Float()
    duration_minutes = graphene.Int()
    execution_results = graphene.JSONString()
    completed_at = graphene.String()


class PositionRiskType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    quantity = graphene.Int()
    entry_price = graphene.Float()
    current_price = graphene.Float()
    unrealized_pnl = graphene.Float()
    unrealized_pnl_percent = graphene.Float()
    risk_amount = graphene.Float()
    risk_percent = graphene.Float()
    position_value = graphene.Float()
    position_percent = graphene.Float()
    leverage = graphene.Float()
    stop_loss = graphene.Float()
    take_profit = graphene.Float()
    stop_loss_distance = graphene.Float()
    take_profit_distance = graphene.Float()
    time_in_position = graphene.Int()
    time_risk_score = graphene.Float()
    volatility_risk = graphene.Float()
    atr_risk = graphene.Float()
    overall_risk_score = graphene.Float()
    risk_level = RiskLevelEnum()


class PortfolioRiskType(graphene.ObjectType):
    total_value = graphene.Float()
    cash = graphene.Float()
    buying_power = graphene.Float()
    total_risk = graphene.Float()
    total_exposure = graphene.Float()
    portfolio_beta = graphene.Float()
    position_count = graphene.Int()
    sector_diversification = graphene.JSONString()
    correlation_risk = graphene.Float()
    daily_pnl = graphene.Float()
    daily_pnl_percent = graphene.Float()
    max_drawdown = graphene.Float()
    sharpe_ratio = graphene.Float()
    risk_limit_status = graphene.JSONString()
    risk_alerts = graphene.List(graphene.String)


class AdvancedFeaturesType(graphene.ObjectType):
    symbol = graphene.String()
    timestamp = graphene.String()
    price_momentum = graphene.JSONString()
    volatility_features = graphene.JSONString()
    trend_features = graphene.JSONString()
    volume_profile = graphene.JSONString()
    order_flow = graphene.JSONString()
    liquidity_features = graphene.JSONString()
    oscillators = graphene.JSONString()
    trend_indicators = graphene.JSONString()
    volatility_indicators = graphene.JSONString()
    microstructure = graphene.JSONString()
    spread_analysis = graphene.JSONString()
    depth_analysis = graphene.JSONString()
    ml_features = graphene.JSONString()
    anomaly_scores = graphene.JSONString()
    pattern_recognition = graphene.JSONString()
    sector_correlation = graphene.JSONString()
    market_regime = graphene.JSONString()
    macro_features = graphene.JSONString()
    composite_score = graphene.Float()
    confidence_score = graphene.Float()
    risk_score = graphene.Float()


class PickScoreType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    base_score = graphene.Float()
    confidence_score = graphene.Float()
    risk_score = graphene.Float()
    ml_score = graphene.Float()
    ensemble_score = graphene.Float()
    score_lower_bound = graphene.Float()
    score_upper_bound = graphene.Float()
    feature_contributions = graphene.JSONString()
    model_used = graphene.String()
    prediction_confidence = graphene.Float()
    timestamp = graphene.String()


# Mutations
class PlaceBracketOrder(graphene.Mutation):
    class Arguments:
        input = BracketOrderInput(required=True)
    
    Output = OrderExecutionResult
    
    def mutate(self, info, input):
        try:
            # Mock bracket order placement
            order_id = f"BRACKET_{uuid.uuid4().hex[:8]}"
            
            return OrderExecutionResult(
                success=True,
                order_id=order_id,
                message=f"Bracket order placed for {input.symbol}",
                execution_details={
                    "symbol": input.symbol,
                    "side": input.side,
                    "quantity": input.quantity,
                    "entry_price": input.entry_price,
                    "stop_loss": input.stop_loss,
                    "take_profit_1": input.take_profit_1,
                    "take_profit_2": input.take_profit_2,
                    "status": "SUBMITTED",
                    "created_at": datetime.now().isoformat()
                }
            )
        except Exception as e:
            return OrderExecutionResult(
                success=False,
                message=f"Bracket order failed: {str(e)}"
            )


class PlaceOCOOrder(graphene.Mutation):
    class Arguments:
        input = OCOOrderInput(required=True)
    
    Output = OrderExecutionResult
    
    def mutate(self, info, input):
        try:
            # Mock OCO order placement
            order_id = f"OCO_{uuid.uuid4().hex[:8]}"
            
            return OrderExecutionResult(
                success=True,
                order_id=order_id,
                message=f"OCO order placed for {input.symbol}",
                execution_details={
                    "symbol": input.symbol,
                    "side": input.side,
                    "quantity": input.quantity,
                    "order_1_price": input.order_1_price,
                    "order_1_type": input.order_1_type,
                    "order_2_price": input.order_2_price,
                    "order_2_type": input.order_2_type,
                    "status": "SUBMITTED",
                    "created_at": datetime.now().isoformat()
                }
            )
        except Exception as e:
            return OrderExecutionResult(
                success=False,
                message=f"OCO order failed: {str(e)}"
            )


class PlaceIcebergOrder(graphene.Mutation):
    class Arguments:
        input = IcebergOrderInput(required=True)
    
    Output = OrderExecutionResult
    
    def mutate(self, info, input):
        try:
            # Mock iceberg order placement
            order_id = f"ICEBERG_{uuid.uuid4().hex[:8]}"
            
            return OrderExecutionResult(
                success=True,
                order_id=order_id,
                message=f"Iceberg order placed for {input.symbol}",
                execution_details={
                    "symbol": input.symbol,
                    "side": input.side,
                    "total_quantity": input.total_quantity,
                    "visible_quantity": input.visible_quantity,
                    "price": input.price,
                    "status": "SUBMITTED",
                    "created_at": datetime.now().isoformat()
                }
            )
        except Exception as e:
            return OrderExecutionResult(
                success=False,
                message=f"Iceberg order failed: {str(e)}"
            )


class PlaceTrailingStop(graphene.Mutation):
    class Arguments:
        input = TrailingStopInput(required=True)
    
    Output = OrderExecutionResult
    
    def mutate(self, info, input):
        try:
            # Mock trailing stop placement
            order_id = f"TRAILING_{uuid.uuid4().hex[:8]}"
            
            return OrderExecutionResult(
                success=True,
                order_id=order_id,
                message=f"Trailing stop placed for {input.symbol}",
                execution_details={
                    "symbol": input.symbol,
                    "side": input.side,
                    "quantity": input.quantity,
                    "trail_amount": input.trail_amount,
                    "trail_percent": input.trail_percent,
                    "status": "SUBMITTED",
                    "created_at": datetime.now().isoformat()
                }
            )
        except Exception as e:
            return OrderExecutionResult(
                success=False,
                message=f"Trailing stop failed: {str(e)}"
            )


class ExecuteTWAPOrder(graphene.Mutation):
    class Arguments:
        input = TWAPOrderInput(required=True)
    
    Output = TWAPExecutionType
    
    def mutate(self, info, input):
        try:
            # Mock TWAP execution
            execution_id = f"TWAP_{uuid.uuid4().hex[:8]}"
            
            # Simulate execution results
            execution_results = []
            total_filled = 0
            average_price = 0.0
            
            intervals = min(10, input.duration_minutes // 2)
            quantity_per_interval = input.total_quantity // intervals
            
            for i in range(intervals):
                # Mock price and fill
                price = 100.0 + (i * 0.5)  # Simulate price movement
                fill_quantity = quantity_per_interval
                
                execution_results.append({
                    "interval": i + 1,
                    "quantity": fill_quantity,
                    "price": price,
                    "order_id": f"TWAP_{i}_{uuid.uuid4().hex[:8]}",
                    "timestamp": datetime.now().isoformat()
                })
                
                total_filled += fill_quantity
                average_price += price * fill_quantity
            
            average_price = average_price / total_filled if total_filled > 0 else 0
            
            return TWAPExecutionType(
                symbol=input.symbol,
                side=input.side,
                total_quantity=input.total_quantity,
                total_filled=total_filled,
                average_price=average_price,
                duration_minutes=input.duration_minutes,
                execution_results=str(execution_results),
                completed_at=datetime.now().isoformat()
            )
        except Exception as e:
            return TWAPExecutionType(
                symbol=input.symbol,
                side=input.side,
                total_quantity=0,
                total_filled=0,
                average_price=0.0,
                duration_minutes=0,
                execution_results="[]",
                completed_at=datetime.now().isoformat()
            )


class ExecuteVWAPOrder(graphene.Mutation):
    class Arguments:
        input = VWAPOrderInput(required=True)
    
    Output = VWAPExecutionType
    
    def mutate(self, info, input):
        try:
            # Mock VWAP execution
            execution_id = f"VWAP_{uuid.uuid4().hex[:8]}"
            
            # Simulate execution results
            execution_results = []
            total_filled = 0
            average_price = 0.0
            
            intervals = min(10, input.duration_minutes)
            base_quantity = input.total_quantity // intervals
            
            for i in range(intervals):
                # Mock volume-weighted execution
                volume_weight = 1.0 + (i * 0.1)  # Simulate volume pattern
                price = 100.0 + (i * 0.3)  # Simulate price movement
                fill_quantity = int(base_quantity * volume_weight)
                
                execution_results.append({
                    "interval": i + 1,
                    "quantity": fill_quantity,
                    "price": price,
                    "volume_weight": volume_weight,
                    "order_id": f"VWAP_{i}_{uuid.uuid4().hex[:8]}",
                    "timestamp": datetime.now().isoformat()
                })
                
                total_filled += fill_quantity
                average_price += price * fill_quantity
            
            average_price = average_price / total_filled if total_filled > 0 else 0
            
            return VWAPExecutionType(
                symbol=input.symbol,
                side=input.side,
                total_quantity=input.total_quantity,
                total_filled=total_filled,
                average_price=average_price,
                duration_minutes=input.duration_minutes,
                execution_results=str(execution_results),
                completed_at=datetime.now().isoformat()
            )
        except Exception as e:
            return VWAPExecutionType(
                symbol=input.symbol,
                side=input.side,
                total_quantity=0,
                total_filled=0,
                average_price=0.0,
                duration_minutes=0,
                execution_results="[]",
                completed_at=datetime.now().isoformat()
            )


class CancelAdvancedOrder(graphene.Mutation):
    class Arguments:
        order_id = graphene.String(required=True)
    
    Output = OrderExecutionResult
    
    def mutate(self, info, order_id):
        try:
            # Mock order cancellation
            return OrderExecutionResult(
                success=True,
                order_id=order_id,
                message=f"Order {order_id} cancelled successfully"
            )
        except Exception as e:
            return OrderExecutionResult(
                success=False,
                message=f"Order cancellation failed: {str(e)}"
            )


# Queries
class GetAdvancedFeatures(graphene.Query):
    symbol = graphene.String(required=True)
    
    Output = AdvancedFeaturesType
    
    def resolve_symbol(self, info, symbol):
        # Mock advanced features
        return AdvancedFeaturesType(
            symbol=symbol,
            timestamp=datetime.now().isoformat(),
            price_momentum='{"momentum_5": 0.015, "momentum_10": 0.012, "momentum_20": 0.008}',
            volatility_features='{"volatility_5": 0.025, "volatility_10": 0.028, "volatility_20": 0.030}',
            trend_features='{"trend_slope": 0.001, "trend_r_squared": 0.75, "price_position": 0.65}',
            volume_profile='{"vwap_10": 100.5, "vwap_distance_10": 0.008, "volume_profile_skew": 0.2}',
            order_flow='{"buy_sell_ratio": 1.2, "net_order_flow": 0.15}',
            liquidity_features='{"volume_stability": 0.8, "volume_trend": 0.05}',
            oscillators='{"rsi_14": 65.5, "rsi_21": 68.2, "stoch_k": 75.0, "stoch_d": 72.0}',
            trend_indicators='{"macd_line": 0.12, "macd_signal": 0.08, "bb_position": 0.75, "bb_width": 0.15}',
            volatility_indicators='{"atr": 1.25, "atr_percent": 1.25, "atrp": 1.25}',
            microstructure='{"price_volume_correlation": 0.65}',
            spread_analysis='{"spread_absolute": 0.05, "spread_bps": 5.0, "spread_percent": 0.05}',
            depth_analysis='{"bid_depth": 1000, "ask_depth": 1200, "depth_imbalance": -0.09}',
            ml_features='{"price_skewness": 0.2, "price_kurtosis": 2.1, "volume_skewness": 0.8}',
            anomaly_scores='{"isolation_forest": 1}',
            pattern_recognition='{"support_distance": 0.05, "resistance_distance": 0.08, "breakout_strength": 0.012}',
            sector_correlation='{"tech_correlation": 0.75, "finance_correlation": 0.45}',
            market_regime='{"vix_level": 18.5, "treasury_yield": 4.2, "dollar_strength": 0.02}',
            macro_features='{"economic_sentiment": 0.65, "risk_appetite": 0.7, "liquidity_conditions": 0.8}',
            composite_score=0.78,
            confidence_score=0.85,
            risk_score=0.22
        )


class GetPickScore(graphene.Query):
    symbol = graphene.String(required=True)
    side = graphene.String(required=True)
    
    Output = PickScoreType
    
    def resolve_symbol(self, info, symbol, side):
        # Mock pick score
        return PickScoreType(
            symbol=symbol,
            side=side,
            base_score=0.75,
            confidence_score=0.82,
            risk_score=0.18,
            ml_score=0.78,
            ensemble_score=0.76,
            score_lower_bound=0.68,
            score_upper_bound=0.84,
            feature_contributions='{"momentum": 0.3, "volume": 0.25, "technical": 0.25, "microstructure": 0.2}',
            model_used="ensemble_model",
            prediction_confidence=0.85,
            timestamp=datetime.now().isoformat()
        )


class GetPositionRisk(graphene.Query):
    symbol = graphene.String(required=True)
    
    Output = PositionRiskType
    
    def resolve_symbol(self, info, symbol):
        # Mock position risk
        return PositionRiskType(
            symbol=symbol,
            side="LONG",
            quantity=100,
            entry_price=100.0,
            current_price=102.5,
            unrealized_pnl=250.0,
            unrealized_pnl_percent=0.025,
            risk_amount=250.0,
            risk_percent=0.025,
            position_value=10250.0,
            position_percent=0.05,
            leverage=1.0,
            stop_loss=95.0,
            take_profit=110.0,
            stop_loss_distance=7.5,
            take_profit_distance=7.5,
            time_in_position=45,
            time_risk_score=0.375,
            volatility_risk=0.02,
            atr_risk=0.04,
            overall_risk_score=0.35,
            risk_level=RiskLevel.MEDIUM
        )


class GetPortfolioRisk(graphene.Query):
    mode = graphene.String(default_value="SAFE")
    
    Output = PortfolioRiskType
    
    def resolve_mode(self, info, mode):
        # Mock portfolio risk
        return PortfolioRiskType(
            total_value=100000.0,
            cash=50000.0,
            buying_power=75000.0,
            total_risk=2500.0,
            total_exposure=50000.0,
            portfolio_beta=1.1,
            position_count=5,
            sector_diversification='{"Technology": 0.4, "Finance": 0.2, "Healthcare": 0.15, "Energy": 0.1, "Other": 0.15}',
            correlation_risk=0.65,
            daily_pnl=1250.0,
            daily_pnl_percent=0.0125,
            max_drawdown=0.03,
            sharpe_ratio=1.8,
            risk_limit_status='{"daily_loss_limit": true, "drawdown_limit": true, "position_size_limit": true, "sector_exposure_limit": true}',
            risk_alerts=[]
        )


# Schema
class AdvancedTradingMutations(graphene.ObjectType):
    place_bracket_order = PlaceBracketOrder.Field()
    place_oco_order = PlaceOCOOrder.Field()
    place_iceberg_order = PlaceIcebergOrder.Field()
    place_trailing_stop = PlaceTrailingStop.Field()
    execute_twap_order = ExecuteTWAPOrder.Field()
    execute_vwap_order = ExecuteVWAPOrder.Field()
    cancel_advanced_order = CancelAdvancedOrder.Field()


class AdvancedTradingQueries(graphene.ObjectType):
    get_advanced_features = GetAdvancedFeatures.Field()
    get_pick_score = GetPickScore.Field()
    get_position_risk = GetPositionRisk.Field()
    get_portfolio_risk = GetPortfolioRisk.Field()


# Export schema
advanced_trading_schema = graphene.Schema(
    query=AdvancedTradingQueries,
    mutation=AdvancedTradingMutations
)
