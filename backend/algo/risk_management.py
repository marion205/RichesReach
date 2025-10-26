"""
Advanced Risk Management System
Comprehensive position sizing, risk controls, and portfolio management
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import math

from ..broker.adapters.base import Broker, OrderSide, OrderType
from ..market.providers.base import MarketDataProvider


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class PositionStatus(Enum):
    """Position status enumeration"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"
    PENDING = "PENDING"


@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_position_size: float  # Maximum position size as % of portfolio
    max_daily_loss: float    # Maximum daily loss as % of portfolio
    max_drawdown: float      # Maximum drawdown as % of portfolio
    position_timeout: int   # Position timeout in minutes
    stop_loss_atr_multiplier: float  # ATR multiplier for stop loss
    take_profit_atr_multiplier: float  # ATR multiplier for take profit
    max_correlation: float  # Maximum correlation between positions
    max_sector_exposure: float  # Maximum sector exposure as % of portfolio


@dataclass
class PositionRisk:
    """Position risk metrics"""
    symbol: str
    side: str
    quantity: int
    entry_price: float
    current_price: float
    
    # Risk metrics
    unrealized_pnl: float
    unrealized_pnl_percent: float
    risk_amount: float
    risk_percent: float
    
    # Position sizing
    position_value: float
    position_percent: float
    leverage: float
    
    # Stop loss and take profit
    stop_loss: float
    take_profit: float
    stop_loss_distance: float
    take_profit_distance: float
    
    # Time-based risk
    time_in_position: int  # minutes
    time_risk_score: float
    
    # Volatility risk
    volatility_risk: float
    atr_risk: float
    
    # Overall risk score
    overall_risk_score: float
    risk_level: RiskLevel


@dataclass
class PortfolioRisk:
    """Portfolio-level risk metrics"""
    total_value: float
    cash: float
    buying_power: float
    
    # Risk metrics
    total_risk: float
    total_exposure: float
    portfolio_beta: float
    
    # Diversification metrics
    position_count: int
    sector_diversification: Dict[str, float]
    correlation_risk: float
    
    # Performance metrics
    daily_pnl: float
    daily_pnl_percent: float
    max_drawdown: float
    sharpe_ratio: float
    
    # Risk limits
    risk_limit_status: Dict[str, bool]
    risk_alerts: List[str]


class AdvancedRiskManager:
    """Advanced risk management system"""
    
    def __init__(self, broker: Broker, market_data_provider: MarketDataProvider):
        self.broker = broker
        self.market_data_provider = market_data_provider
        self.logger = logging.getLogger(__name__)
        
        # Risk parameters by trading mode
        self.risk_parameters = {
            "SAFE": RiskParameters(
                max_position_size=0.05,      # 5% max position
                max_daily_loss=0.02,         # 2% max daily loss
                max_drawdown=0.05,           # 5% max drawdown
                position_timeout=120,        # 2 hours timeout
                stop_loss_atr_multiplier=2.0,
                take_profit_atr_multiplier=3.0,
                max_correlation=0.7,
                max_sector_exposure=0.3
            ),
            "AGGRESSIVE": RiskParameters(
                max_position_size=0.10,      # 10% max position
                max_daily_loss=0.05,         # 5% max daily loss
                max_drawdown=0.10,           # 10% max drawdown
                position_timeout=60,         # 1 hour timeout
                stop_loss_atr_multiplier=1.5,
                take_profit_atr_multiplier=2.0,
                max_correlation=0.8,
                max_sector_exposure=0.4
            )
        }
        
        # Risk monitoring
        self.risk_alerts = []
        self.risk_history = []
        self.position_history = []
        
        # Risk limits tracking
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.current_drawdown = 0.0
        
    async def calculate_position_size(
        self, 
        symbol: str, 
        side: str, 
        entry_price: float, 
        stop_loss: float,
        mode: str = "SAFE"
    ) -> Tuple[int, Dict[str, Any]]:
        """Calculate optimal position size based on risk parameters"""
        
        try:
            risk_params = self.risk_parameters[mode]
            
            # Get account information
            account = await self.broker.get_account()
            portfolio_value = account.portfolio_value
            
            # Calculate risk amount
            risk_amount = portfolio_value * risk_params.max_position_size
            
            # Calculate stop loss distance
            stop_loss_distance = abs(entry_price - stop_loss)
            if stop_loss_distance == 0:
                stop_loss_distance = entry_price * 0.02  # Default 2% stop
            
            # Calculate position size
            position_size = int(risk_amount / stop_loss_distance)
            
            # Apply additional risk controls
            position_size = await self._apply_position_limits(
                symbol, position_size, entry_price, mode
            )
            
            # Calculate position metrics
            position_value = position_size * entry_price
            position_percent = position_value / portfolio_value
            
            # Risk metrics
            risk_metrics = {
                "position_size": position_size,
                "position_value": position_value,
                "position_percent": position_percent,
                "risk_amount": risk_amount,
                "stop_loss_distance": stop_loss_distance,
                "max_loss": position_size * stop_loss_distance,
                "leverage": position_value / account.cash if account.cash > 0 else 0
            }
            
            return position_size, risk_metrics
            
        except Exception as e:
            self.logger.error(f"❌ Position sizing failed for {symbol}: {e}")
            return 0, {}
    
    async def _apply_position_limits(
        self, 
        symbol: str, 
        position_size: int, 
        entry_price: float, 
        mode: str
    ) -> int:
        """Apply additional position limits and checks"""
        
        risk_params = self.risk_parameters[mode]
        
        # Get current positions
        positions = await self.broker.get_positions()
        
        # Check existing position in same symbol
        existing_position = next((p for p in positions if p.symbol == symbol), None)
        if existing_position:
            # Reduce size if position already exists
            position_size = min(position_size, existing_position.qty // 2)
        
        # Check sector exposure
        sector_exposure = await self._calculate_sector_exposure(symbol, positions)
        if sector_exposure > risk_params.max_sector_exposure:
            position_size = int(position_size * 0.5)  # Reduce by 50%
        
        # Check correlation with existing positions
        correlation_risk = await self._calculate_correlation_risk(symbol, positions)
        if correlation_risk > risk_params.max_correlation:
            position_size = int(position_size * 0.7)  # Reduce by 30%
        
        # Check daily loss limits
        if self.daily_pnl < -risk_params.max_daily_loss:
            position_size = int(position_size * 0.3)  # Reduce by 70%
        
        # Minimum position size
        position_size = max(1, position_size)
        
        # Maximum position size (safety limit)
        max_position_value = 10000  # $10k max position
        max_position_size = int(max_position_value / entry_price)
        position_size = min(position_size, max_position_size)
        
        return position_size
    
    async def calculate_stop_loss_and_targets(
        self, 
        symbol: str, 
        side: str, 
        entry_price: float, 
        atr: float,
        mode: str = "SAFE"
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit levels"""
        
        risk_params = self.risk_parameters[mode]
        
        # Calculate stop loss distance
        stop_loss_distance = atr * risk_params.stop_loss_atr_multiplier
        
        # Calculate take profit distance
        take_profit_distance = atr * risk_params.take_profit_atr_multiplier
        
        # Calculate levels based on side
        if side.upper() == "LONG":
            stop_loss = entry_price - stop_loss_distance
            take_profit_1 = entry_price + take_profit_distance
            take_profit_2 = entry_price + (take_profit_distance * 1.5)
        else:  # SHORT
            stop_loss = entry_price + stop_loss_distance
            take_profit_1 = entry_price - take_profit_distance
            take_profit_2 = entry_price - (take_profit_distance * 1.5)
        
        return {
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "stop_loss_distance": stop_loss_distance,
            "take_profit_distance": take_profit_distance,
            "risk_reward_ratio": take_profit_distance / stop_loss_distance
        }
    
    async def assess_position_risk(self, symbol: str) -> Optional[PositionRisk]:
        """Assess risk for a specific position"""
        
        try:
            # Get position from broker
            positions = await self.broker.get_positions()
            position = next((p for p in positions if p.symbol == symbol), None)
            
            if not position:
                return None
            
            # Get current quote
            quotes = await self.market_data_provider.get_quotes([symbol])
            if symbol not in quotes:
                return None
            
            current_price = quotes[symbol].price
            
            # Calculate basic metrics
            unrealized_pnl = (current_price - position.avg_entry_price) * position.qty
            if position.side.upper() == "SHORT":
                unrealized_pnl = -unrealized_pnl
            
            unrealized_pnl_percent = unrealized_pnl / (position.avg_entry_price * position.qty)
            
            # Calculate position value and percentage
            position_value = current_price * position.qty
            account = await self.broker.get_account()
            position_percent = position_value / account.portfolio_value
            
            # Calculate risk metrics
            risk_amount = abs(unrealized_pnl)
            risk_percent = abs(unrealized_pnl_percent)
            
            # Calculate stop loss and take profit (mock for now)
            stop_loss = position.avg_entry_price * 0.95  # 5% stop loss
            take_profit = position.avg_entry_price * 1.10  # 10% take profit
            
            stop_loss_distance = abs(current_price - stop_loss)
            take_profit_distance = abs(take_profit - current_price)
            
            # Time-based risk
            time_in_position = 60  # Mock - would calculate from entry time
            time_risk_score = min(1.0, time_in_position / 120)  # Risk increases over time
            
            # Volatility risk
            volatility_risk = 0.02  # Mock - would calculate from historical data
            atr_risk = volatility_risk * 2  # ATR-based risk
            
            # Overall risk score
            overall_risk_score = (
                risk_percent * 0.3 +
                time_risk_score * 0.2 +
                volatility_risk * 10 * 0.2 +
                position_percent * 0.3
            )
            
            # Determine risk level
            if overall_risk_score < 0.3:
                risk_level = RiskLevel.LOW
            elif overall_risk_score < 0.6:
                risk_level = RiskLevel.MEDIUM
            elif overall_risk_score < 0.8:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.EXTREME
            
            return PositionRisk(
                symbol=symbol,
                side=position.side,
                quantity=position.qty,
                entry_price=position.avg_entry_price,
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percent=unrealized_pnl_percent,
                risk_amount=risk_amount,
                risk_percent=risk_percent,
                position_value=position_value,
                position_percent=position_percent,
                leverage=position_value / account.cash if account.cash > 0 else 0,
                stop_loss=stop_loss,
                take_profit=take_profit,
                stop_loss_distance=stop_loss_distance,
                take_profit_distance=take_profit_distance,
                time_in_position=time_in_position,
                time_risk_score=time_risk_score,
                volatility_risk=volatility_risk,
                atr_risk=atr_risk,
                overall_risk_score=overall_risk_score,
                risk_level=risk_level
            )
            
        except Exception as e:
            self.logger.error(f"❌ Position risk assessment failed for {symbol}: {e}")
            return None
    
    async def assess_portfolio_risk(self, mode: str = "SAFE") -> PortfolioRisk:
        """Assess portfolio-level risk"""
        
        try:
            # Get account and positions
            account = await self.broker.get_account()
            positions = await self.broker.get_positions()
            
            # Calculate basic metrics
            total_value = account.portfolio_value
            cash = account.cash
            buying_power = account.buying_power
            
            # Calculate total risk and exposure
            total_risk = 0.0
            total_exposure = 0.0
            
            for position in positions:
                quotes = await self.market_data_provider.get_quotes([position.symbol])
                if position.symbol in quotes:
                    current_price = quotes[position.symbol].price
                    position_value = current_price * position.qty
                    total_exposure += position_value
                    
                    # Calculate risk (simplified)
                    risk_percent = 0.05  # Assume 5% risk per position
                    total_risk += position_value * risk_percent
            
            # Calculate portfolio beta (simplified)
            portfolio_beta = 1.0  # Mock - would calculate from historical data
            
            # Calculate diversification metrics
            position_count = len(positions)
            sector_diversification = await self._calculate_sector_diversification(positions)
            correlation_risk = await self._calculate_portfolio_correlation(positions)
            
            # Calculate performance metrics
            daily_pnl = self.daily_pnl
            daily_pnl_percent = daily_pnl / total_value if total_value > 0 else 0
            
            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = daily_pnl_percent / 0.02 if daily_pnl_percent > 0 else 0  # Assume 2% daily volatility
            
            # Check risk limits
            risk_params = self.risk_parameters[mode]
            risk_limit_status = {
                "daily_loss_limit": abs(daily_pnl_percent) <= risk_params.max_daily_loss,
                "drawdown_limit": self.current_drawdown <= risk_params.max_drawdown,
                "position_size_limit": all(p.qty * p.avg_entry_price / total_value <= risk_params.max_position_size for p in positions),
                "sector_exposure_limit": all(sector_diversification.values()) <= risk_params.max_sector_exposure
            }
            
            # Generate risk alerts
            risk_alerts = []
            if not risk_limit_status["daily_loss_limit"]:
                risk_alerts.append("Daily loss limit exceeded")
            if not risk_limit_status["drawdown_limit"]:
                risk_alerts.append("Drawdown limit exceeded")
            if not risk_limit_status["position_size_limit"]:
                risk_alerts.append("Position size limit exceeded")
            if not risk_limit_status["sector_exposure_limit"]:
                risk_alerts.append("Sector exposure limit exceeded")
            
            return PortfolioRisk(
                total_value=total_value,
                cash=cash,
                buying_power=buying_power,
                total_risk=total_risk,
                total_exposure=total_exposure,
                portfolio_beta=portfolio_beta,
                position_count=position_count,
                sector_diversification=sector_diversification,
                correlation_risk=correlation_risk,
                daily_pnl=daily_pnl,
                daily_pnl_percent=daily_pnl_percent,
                max_drawdown=self.max_drawdown,
                sharpe_ratio=sharpe_ratio,
                risk_limit_status=risk_limit_status,
                risk_alerts=risk_alerts
            )
            
        except Exception as e:
            self.logger.error(f"❌ Portfolio risk assessment failed: {e}")
            return None
    
    async def _calculate_sector_exposure(self, symbol: str, positions: List) -> float:
        """Calculate sector exposure for a symbol"""
        
        # Mock sector mapping
        sector_mapping = {
            "AAPL": "Technology",
            "MSFT": "Technology", 
            "GOOGL": "Technology",
            "TSLA": "Automotive",
            "NVDA": "Technology",
            "META": "Technology"
        }
        
        sector = sector_mapping.get(symbol, "Other")
        
        # Calculate total exposure in this sector
        total_value = 0.0
        sector_value = 0.0
        
        for position in positions:
            if position.symbol in sector_mapping:
                if sector_mapping[position.symbol] == sector:
                    sector_value += position.qty * position.avg_entry_price
                total_value += position.qty * position.avg_entry_price
        
        return sector_value / total_value if total_value > 0 else 0
    
    async def _calculate_sector_diversification(self, positions: List) -> Dict[str, float]:
        """Calculate sector diversification"""
        
        sector_mapping = {
            "AAPL": "Technology",
            "MSFT": "Technology",
            "GOOGL": "Technology", 
            "TSLA": "Automotive",
            "NVDA": "Technology",
            "META": "Technology"
        }
        
        sector_values = {}
        total_value = 0.0
        
        for position in positions:
            sector = sector_mapping.get(position.symbol, "Other")
            value = position.qty * position.avg_entry_price
            
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += value
            total_value += value
        
        # Convert to percentages
        sector_percentages = {}
        for sector, value in sector_values.items():
            sector_percentages[sector] = value / total_value if total_value > 0 else 0
        
        return sector_percentages
    
    async def _calculate_correlation_risk(self, symbol: str, positions: List) -> float:
        """Calculate correlation risk with existing positions"""
        
        # Mock correlation calculation
        # In reality, would use historical price correlation
        
        correlated_symbols = {
            "AAPL": ["MSFT", "GOOGL", "NVDA"],
            "MSFT": ["AAPL", "GOOGL", "NVDA"],
            "GOOGL": ["AAPL", "MSFT", "NVDA"],
            "TSLA": ["NVDA"],
            "NVDA": ["AAPL", "MSFT", "GOOGL", "TSLA"]
        }
        
        correlated_positions = 0
        total_positions = len(positions)
        
        if symbol in correlated_symbols:
            for position in positions:
                if position.symbol in correlated_symbols[symbol]:
                    correlated_positions += 1
        
        return correlated_positions / total_positions if total_positions > 0 else 0
    
    async def _calculate_portfolio_correlation(self, positions: List) -> float:
        """Calculate overall portfolio correlation"""
        
        # Mock portfolio correlation calculation
        # In reality, would calculate correlation matrix
        
        symbols = [p.symbol for p in positions]
        
        # Technology stocks tend to be correlated
        tech_symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "META"]
        tech_count = sum(1 for s in symbols if s in tech_symbols)
        
        if len(symbols) <= 1:
            return 0.0
        
        # Simple correlation estimate
        correlation = tech_count / len(symbols)
        return correlation
    
    async def generate_risk_alerts(self, portfolio_risk: PortfolioRisk) -> List[str]:
        """Generate risk alerts based on portfolio risk"""
        
        alerts = []
        
        # Daily loss alerts
        if portfolio_risk.daily_pnl_percent < -0.02:  # 2% daily loss
            alerts.append(f"⚠️ Daily loss: {portfolio_risk.daily_pnl_percent:.2%}")
        
        # Drawdown alerts
        if portfolio_risk.max_drawdown > 0.05:  # 5% drawdown
            alerts.append(f"⚠️ Drawdown: {portfolio_risk.max_drawdown:.2%}")
        
        # Position concentration alerts
        if portfolio_risk.position_count > 10:
            alerts.append(f"⚠️ Too many positions: {portfolio_risk.position_count}")
        
        # Sector concentration alerts
        for sector, exposure in portfolio_risk.sector_diversification.items():
            if exposure > 0.4:  # 40% sector exposure
                alerts.append(f"⚠️ {sector} exposure: {exposure:.2%}")
        
        # Correlation alerts
        if portfolio_risk.correlation_risk > 0.7:
            alerts.append(f"⚠️ High correlation: {portfolio_risk.correlation_risk:.2%}")
        
        return alerts
    
    async def execute_risk_management(self, mode: str = "SAFE") -> Dict[str, Any]:
        """Execute risk management actions"""
        
        try:
            # Assess portfolio risk
            portfolio_risk = await self.assess_portfolio_risk(mode)
            
            # Generate alerts
            alerts = await self.generate_risk_alerts(portfolio_risk)
            
            # Risk management actions
            actions = []
            
            # Check if we need to close positions
            if portfolio_risk.daily_pnl_percent < -0.05:  # 5% daily loss
                actions.append("CLOSE_ALL_POSITIONS")
            
            # Check if we need to reduce position sizes
            if portfolio_risk.correlation_risk > 0.8:
                actions.append("REDUCE_CORRELATED_POSITIONS")
            
            # Check if we need to stop trading
            if portfolio_risk.max_drawdown > 0.10:  # 10% drawdown
                actions.append("STOP_TRADING")
            
            return {
                "portfolio_risk": portfolio_risk,
                "alerts": alerts,
                "actions": actions,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Risk management execution failed: {e}")
            return {"error": str(e)}


# Factory function
async def create_risk_manager(alpaca_api_key: str, alpaca_secret: str, polygon_api_key: str) -> AdvancedRiskManager:
    """Create risk manager with real providers"""
    from ..broker.adapters.alpaca_paper import AlpacaPaperBroker
    from ..market.providers.polygon import PolygonProvider
    
    broker = AlpacaPaperBroker(
        api_key_id=alpaca_api_key,
        api_secret_key=alpaca_secret
    )
    
    market_provider = PolygonProvider(api_key=polygon_api_key)
    
    return AdvancedRiskManager(broker, market_provider)
