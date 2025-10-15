"""
Risk Management System for Day Trading
Implements position limits, stop losses, and risk controls
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"

class PositionStatus(Enum):
    """Position status"""
    ACTIVE = "ACTIVE"
    STOPPED_OUT = "STOPPED_OUT"
    PROFIT_TAKEN = "PROFIT_TAKEN"
    TIME_STOPPED = "TIME_STOPPED"
    MANUAL_CLOSE = "MANUAL_CLOSE"

@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_position_size: float  # Maximum position size as % of account
    max_daily_loss: float     # Maximum daily loss as % of account
    max_concurrent_trades: int  # Maximum number of concurrent trades
    stop_loss_pct: float      # Stop loss percentage
    take_profit_pct: float    # Take profit percentage
    max_hold_time_minutes: int  # Maximum hold time in minutes
    atr_multiplier: float     # ATR multiplier for dynamic stops
    max_sector_exposure: float  # Maximum exposure to single sector
    max_correlation_exposure: float  # Maximum exposure to correlated positions

@dataclass
class Position:
    """Trading position with risk management"""
    symbol: str
    side: str  # "LONG" or "SHORT"
    entry_price: float
    quantity: int
    entry_time: datetime
    stop_loss_price: float
    take_profit_price: float
    max_hold_until: datetime
    atr_stop_price: float
    status: PositionStatus = PositionStatus.ACTIVE
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: Optional[float] = None
    risk_reason: Optional[str] = None

class RiskManager:
    """Main risk management system"""
    
    def __init__(self, account_value: float = 100000.0, risk_level: RiskLevel = RiskLevel.MODERATE):
        self.account_value = account_value
        self.risk_level = risk_level
        self.positions: Dict[str, Position] = {}
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.max_daily_trades = 20
        
        # Risk parameters based on risk level
        self.risk_params = self._get_risk_parameters()
        
        # Sector exposure tracking
        self.sector_exposure: Dict[str, float] = {}
        
        # Correlation tracking (simplified)
        self.correlation_groups = {
            "tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"],
            "finance": ["JPM", "BAC", "WFC", "GS", "MS"],
            "energy": ["XOM", "CVX", "COP", "EOG"],
            "healthcare": ["JNJ", "PFE", "UNH", "ABBV", "LLY"],
            "consumer": ["WMT", "PG", "KO", "PEP", "MCD"]
        }
        
    def _get_risk_parameters(self) -> RiskParameters:
        """Get risk parameters based on risk level"""
        if self.risk_level == RiskLevel.CONSERVATIVE:
            return RiskParameters(
                max_position_size=0.05,      # 5% max position
                max_daily_loss=0.02,         # 2% max daily loss
                max_concurrent_trades=3,     # Max 3 concurrent trades
                stop_loss_pct=0.015,         # 1.5% stop loss
                take_profit_pct=0.03,        # 3% take profit
                max_hold_time_minutes=60,    # 1 hour max hold
                atr_multiplier=2.0,          # 2x ATR for stops
                max_sector_exposure=0.15,    # 15% max sector exposure
                max_correlation_exposure=0.20 # 20% max correlated exposure
            )
        elif self.risk_level == RiskLevel.MODERATE:
            return RiskParameters(
                max_position_size=0.08,      # 8% max position
                max_daily_loss=0.03,         # 3% max daily loss
                max_concurrent_trades=5,     # Max 5 concurrent trades
                stop_loss_pct=0.02,          # 2% stop loss
                take_profit_pct=0.04,        # 4% take profit
                max_hold_time_minutes=90,    # 1.5 hours max hold
                atr_multiplier=1.5,          # 1.5x ATR for stops
                max_sector_exposure=0.20,    # 20% max sector exposure
                max_correlation_exposure=0.25 # 25% max correlated exposure
            )
        else:  # AGGRESSIVE
            return RiskParameters(
                max_position_size=0.12,      # 12% max position
                max_daily_loss=0.05,         # 5% max daily loss
                max_concurrent_trades=8,     # Max 8 concurrent trades
                stop_loss_pct=0.025,         # 2.5% stop loss
                take_profit_pct=0.06,        # 6% take profit
                max_hold_time_minutes=120,   # 2 hours max hold
                atr_multiplier=1.2,          # 1.2x ATR for stops
                max_sector_exposure=0.25,    # 25% max sector exposure
                max_correlation_exposure=0.30 # 30% max correlated exposure
            )
    
    def can_open_position(self, symbol: str, side: str, price: float, quantity: int, 
                         sector: str = "unknown") -> Tuple[bool, str]:
        """Check if position can be opened based on risk rules"""
        
        # Check daily loss limit
        if self.daily_pnl <= -self.risk_params.max_daily_loss * self.account_value:
            return False, "Daily loss limit exceeded"
        
        # Check daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            return False, "Daily trade limit exceeded"
        
        # Check concurrent position limit
        if len(self.positions) >= self.risk_params.max_concurrent_trades:
            return False, "Maximum concurrent positions reached"
        
        # Check position size
        position_value = price * quantity
        max_position_value = self.risk_params.max_position_size * self.account_value
        
        if position_value > max_position_value:
            return False, f"Position size too large: ${position_value:,.0f} > ${max_position_value:,.0f}"
        
        # Check sector exposure
        current_sector_exposure = self.sector_exposure.get(sector, 0.0)
        new_sector_exposure = (current_sector_exposure + position_value) / self.account_value
        
        if new_sector_exposure > self.risk_params.max_sector_exposure:
            return False, f"Sector exposure too high: {new_sector_exposure:.1%} > {self.risk_params.max_sector_exposure:.1%}"
        
        # Check correlation exposure
        correlation_exposure = self._calculate_correlation_exposure(symbol, position_value)
        if correlation_exposure > self.risk_params.max_correlation_exposure:
            return False, f"Correlation exposure too high: {correlation_exposure:.1%} > {self.risk_params.max_correlation_exposure:.1%}"
        
        return True, "Position approved"
    
    def _calculate_correlation_exposure(self, symbol: str, position_value: float) -> float:
        """Calculate exposure to correlated positions"""
        total_correlated_value = 0.0
        
        for group_name, symbols in self.correlation_groups.items():
            if symbol in symbols:
                for pos_symbol, position in self.positions.items():
                    if pos_symbol in symbols and position.status == PositionStatus.ACTIVE:
                        total_correlated_value += position.entry_price * position.quantity
        
        return (total_correlated_value + position_value) / self.account_value
    
    def calculate_position_size(self, symbol: str, price: float, atr: float, 
                              confidence: float = 1.0) -> int:
        """Calculate optimal position size based on risk parameters"""
        
        # Base position size from risk parameters
        max_position_value = self.risk_params.max_position_size * self.account_value
        
        # Adjust for confidence (higher confidence = larger position)
        confidence_multiplier = min(confidence * 1.5, 1.0)
        adjusted_position_value = max_position_value * confidence_multiplier
        
        # Adjust for volatility (higher ATR = smaller position)
        volatility_multiplier = max(0.5, 1.0 - (atr / price) * 10)
        final_position_value = adjusted_position_value * volatility_multiplier
        
        # Calculate quantity
        quantity = int(final_position_value / price)
        
        # Ensure minimum quantity
        return max(1, quantity)
    
    def create_position(self, symbol: str, side: str, price: float, quantity: int,
                       atr: float, sector: str = "unknown") -> Tuple[Optional[Position], Optional[str]]:
        """Create a new position with risk management"""
        
        # Check if position can be opened
        can_open, reason = self.can_open_position(symbol, side, price, quantity, sector)
        if not can_open:
            logger.warning(f"Cannot open position for {symbol}: {reason}")
            return None, reason
        
        # Calculate stop loss and take profit
        if side == "LONG":
            stop_loss_price = price * (1 - self.risk_params.stop_loss_pct)
            take_profit_price = price * (1 + self.risk_params.take_profit_pct)
            atr_stop_price = price - (atr * self.risk_params.atr_multiplier)
        else:  # SHORT
            stop_loss_price = price * (1 + self.risk_params.stop_loss_pct)
            take_profit_price = price * (1 - self.risk_params.take_profit_pct)
            atr_stop_price = price + (atr * self.risk_params.atr_multiplier)
        
        # Use the more conservative stop loss
        final_stop_loss = max(stop_loss_price, atr_stop_price) if side == "LONG" else min(stop_loss_price, atr_stop_price)
        
        # Calculate max hold time
        max_hold_until = datetime.now() + timedelta(minutes=self.risk_params.max_hold_time_minutes)
        
        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_loss_price=final_stop_loss,
            take_profit_price=take_profit_price,
            max_hold_until=max_hold_until,
            atr_stop_price=atr_stop_price
        )
        
        # Add to positions
        self.positions[symbol] = position
        
        # Update sector exposure
        position_value = price * quantity
        self.sector_exposure[sector] = self.sector_exposure.get(sector, 0.0) + position_value
        
        # Update daily trades
        self.daily_trades += 1
        
        logger.info(f"Created position: {symbol} {side} {quantity} @ ${price:.2f}, Stop: ${final_stop_loss:.2f}, Target: ${take_profit_price:.2f}")
        
        return position, None
    
    def check_position_exits(self, current_prices: Dict[str, float]) -> List[Position]:
        """Check all positions for exit conditions"""
        exited_positions = []
        
        for symbol, position in self.positions.items():
            if position.status != PositionStatus.ACTIVE:
                continue
                
            current_price = current_prices.get(symbol, position.entry_price)
            exit_reason = self._check_exit_conditions(position, current_price)
            
            if exit_reason:
                self._close_position(position, current_price, exit_reason)
                exited_positions.append(position)
        
        return exited_positions
    
    def _check_exit_conditions(self, position: Position, current_price: float) -> Optional[str]:
        """Check if position should be exited"""
        
        # Check time stop
        if datetime.now() > position.max_hold_until:
            return "TIME_STOPPED"
        
        # Check stop loss
        if position.side == "LONG":
            if current_price <= position.stop_loss_price:
                return "STOPPED_OUT"
            if current_price >= position.take_profit_price:
                return "PROFIT_TAKEN"
        else:  # SHORT
            if current_price >= position.stop_loss_price:
                return "STOPPED_OUT"
            if current_price <= position.take_profit_price:
                return "PROFIT_TAKEN"
        
        return None
    
    def _close_position(self, position: Position, exit_price: float, reason: str):
        """Close a position and update tracking"""
        position.status = PositionStatus(reason)
        position.exit_price = exit_price
        position.exit_time = datetime.now()
        
        # Calculate P&L
        if position.side == "LONG":
            position.pnl = (exit_price - position.entry_price) * position.quantity
        else:  # SHORT
            position.pnl = (position.entry_price - exit_price) * position.quantity
        
        position.risk_reason = reason
        
        # Update daily P&L
        self.daily_pnl += position.pnl
        
        # Update sector exposure
        position_value = position.entry_price * position.quantity
        self.sector_exposure[position.symbol] = max(0, self.sector_exposure.get(position.symbol, 0) - position_value)
        
        logger.info(f"Closed position: {position.symbol} @ ${exit_price:.2f}, P&L: ${position.pnl:.2f}, Reason: {reason}")
    
    def get_risk_summary(self) -> Dict:
        """Get current risk summary"""
        active_positions = [p for p in self.positions.values() if p.status == PositionStatus.ACTIVE]
        total_exposure = sum(p.entry_price * p.quantity for p in active_positions)
        
        return {
            "account_value": self.account_value,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_pct": self.daily_pnl / self.account_value,
            "daily_trades": self.daily_trades,
            "active_positions": len(active_positions),
            "total_exposure": total_exposure,
            "exposure_pct": total_exposure / self.account_value,
            "sector_exposure": self.sector_exposure,
            "risk_level": self.risk_level.value,
            "risk_limits": {
                "max_position_size": self.risk_params.max_position_size,
                "max_daily_loss": self.risk_params.max_daily_loss,
                "max_concurrent_trades": self.risk_params.max_concurrent_trades,
                "max_sector_exposure": self.risk_params.max_sector_exposure
            }
        }
    
    def reset_daily_tracking(self):
        """Reset daily tracking (call at start of trading day)"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.sector_exposure.clear()
        logger.info("Daily risk tracking reset")

# Global risk manager instance
risk_manager = RiskManager()

def get_risk_manager() -> RiskManager:
    """Get the global risk manager instance"""
    return risk_manager

def update_account_value(new_value: float):
    """Update account value for risk calculations"""
    risk_manager.account_value = new_value
    logger.info(f"Account value updated to ${new_value:,.2f}")

def set_risk_level(level: RiskLevel):
    """Set risk level"""
    risk_manager.risk_level = level
    risk_manager.risk_params = risk_manager._get_risk_parameters()
    logger.info(f"Risk level set to {level.value}")
