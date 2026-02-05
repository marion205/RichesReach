"""
Python wrapper for the Rust edge_physics engine with graceful fallback

This module provides a unified interface to the high-performance Rust engine.
If Rust bindings are not available, it falls back to pure Python implementations.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import Rust bindings
try:
    import edge_physics
    RUST_AVAILABLE = True
    logger.info("✅ Rust edge_physics engine loaded successfully")
except ImportError:
    RUST_AVAILABLE = False
    logger.warning("⚠️ Rust edge_physics not available, using Python fallback")


@dataclass
class GreeksResult:
    """Result of Greeks calculation"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "delta": self.delta,
            "gamma": self.gamma,
            "theta": self.theta,
            "vega": self.vega,
            "rho": self.rho,
        }


class HighPerformanceBlackScholes:
    """
    Black-Scholes Greeks calculator with Rust acceleration.
    Falls back to Python if Rust bindings unavailable.
    """
    
    def __init__(self, spot: float, risk_free_rate: float = 0.045):
        """Initialize calculator"""
        self.spot = spot
        self.risk_free_rate = risk_free_rate
        self.rust_enabled = RUST_AVAILABLE
        
        if self.rust_enabled:
            try:
                self.rust_calc = edge_physics.BlackScholesCalc(spot, risk_free_rate)
                logger.debug(f"Rust calculator initialized for spot=${spot}")
            except Exception as e:
                logger.warning(f"Failed to initialize Rust calculator: {e}, falling back to Python")
                self.rust_enabled = False
    
    def call_greeks(self, strike: float, ttm_days: int, volatility: float) -> GreeksResult:
        """Calculate Greeks for a call option"""
        if self.rust_enabled:
            try:
                greeks = self.rust_calc.call_greeks(strike, ttm_days, volatility)
                return GreeksResult(
                    delta=greeks.delta,
                    gamma=greeks.gamma,
                    theta=greeks.theta,
                    vega=greeks.vega,
                    rho=greeks.rho,
                )
            except Exception as e:
                logger.error(f"Rust calculation failed: {e}, falling back to Python")
                self.rust_enabled = False
        
        # Python fallback
        return self._call_greeks_python(strike, ttm_days, volatility)
    
    def put_greeks(self, strike: float, ttm_days: int, volatility: float) -> GreeksResult:
        """Calculate Greeks for a put option"""
        if self.rust_enabled:
            try:
                greeks = self.rust_calc.put_greeks(strike, ttm_days, volatility)
                return GreeksResult(
                    delta=greeks.delta,
                    gamma=greeks.gamma,
                    theta=greeks.theta,
                    vega=greeks.vega,
                    rho=greeks.rho,
                )
            except Exception as e:
                logger.error(f"Rust calculation failed: {e}, falling back to Python")
                self.rust_enabled = False
        
        # Python fallback
        return self._put_greeks_python(strike, ttm_days, volatility)
    
    def _call_greeks_python(self, strike: float, ttm_days: int, volatility: float) -> GreeksResult:
        """Python fallback for call Greeks"""
        import math
        from scipy.stats import norm
        
        ttm_years = ttm_days / 365.25
        
        if ttm_years <= 0 or volatility <= 0:
            return GreeksResult(delta=0, gamma=0, theta=0, vega=0, rho=0)
        
        d1 = (math.log(self.spot / strike) + (self.risk_free_rate + 0.5 * volatility ** 2) * ttm_years) / (volatility * math.sqrt(ttm_years))
        d2 = d1 - volatility * math.sqrt(ttm_years)
        
        delta = norm.cdf(d1)
        gamma = norm.pdf(d1) / (self.spot * volatility * math.sqrt(ttm_years))
        vega = self.spot * norm.pdf(d1) * math.sqrt(ttm_years) / 100.0
        theta = (-self.spot * norm.pdf(d1) * volatility / (2.0 * math.sqrt(ttm_years)) 
                 - self.risk_free_rate * strike * math.exp(-self.risk_free_rate * ttm_years) * norm.cdf(d2)) / 365.25
        rho = strike * ttm_years * math.exp(-self.risk_free_rate * ttm_years) * norm.cdf(d2) / 100.0
        
        return GreeksResult(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)
    
    def _put_greeks_python(self, strike: float, ttm_days: int, volatility: float) -> GreeksResult:
        """Python fallback for put Greeks"""
        import math
        from scipy.stats import norm
        
        ttm_years = ttm_days / 365.25
        
        if ttm_years <= 0 or volatility <= 0:
            return GreeksResult(delta=0, gamma=0, theta=0, vega=0, rho=0)
        
        d1 = (math.log(self.spot / strike) + (self.risk_free_rate + 0.5 * volatility ** 2) * ttm_years) / (volatility * math.sqrt(ttm_years))
        d2 = d1 - volatility * math.sqrt(ttm_years)
        
        delta = norm.cdf(d1) - 1.0  # Put delta
        gamma = norm.pdf(d1) / (self.spot * volatility * math.sqrt(ttm_years))
        vega = self.spot * norm.pdf(d1) * math.sqrt(ttm_years) / 100.0
        theta = (-self.spot * norm.pdf(d1) * volatility / (2.0 * math.sqrt(ttm_years)) 
                 + self.risk_free_rate * strike * math.exp(-self.risk_free_rate * ttm_years) * (1.0 - norm.cdf(d2))) / 365.25
        rho = -strike * ttm_years * math.exp(-self.risk_free_rate * ttm_years) * (1.0 - norm.cdf(d2)) / 100.0
        
        return GreeksResult(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)


class HighPerformanceRepairEngine:
    """
    Repair engine with Rust acceleration for position monitoring.
    Falls back to Python if Rust bindings unavailable.
    """
    
    def __init__(self):
        """Initialize repair engine"""
        self.rust_enabled = RUST_AVAILABLE
        
        if self.rust_enabled:
            try:
                self.rust_engine = edge_physics.RepairEngineWrapper()
                logger.info("✅ Rust repair engine initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Rust repair engine: {e}")
                self.rust_enabled = False
    
    def analyze_position(
        self,
        position_id: str,
        ticker: str,
        strategy_type: str,
        current_delta: float,
        current_gamma: float,
        current_theta: float,
        current_vega: float,
        current_price: float,
        max_loss: float,
        unrealized_pnl: float,
        days_to_expiration: int,
        account_equity: float,
    ) -> Optional[Dict[str, Any]]:
        """Analyze position using Rust engine"""
        if self.rust_enabled:
            try:
                plan = self.rust_engine.analyze_position(
                    position_id=position_id,
                    ticker=ticker,
                    strategy_type=strategy_type,
                    current_delta=current_delta,
                    current_gamma=current_gamma,
                    current_theta=current_theta,
                    current_vega=current_vega,
                    current_price=current_price,
                    max_loss=max_loss,
                    unrealized_pnl=unrealized_pnl,
                    days_to_expiration=days_to_expiration,
                    account_equity=account_equity,
                )
                
                if plan is None:
                    return None
                
                return plan.to_dict()
            except Exception as e:
                logger.error(f"Rust analysis failed: {e}")
                self.rust_enabled = False
        
        # Python fallback (simple logic)
        if abs(current_delta) < 0.25:
            return None
        
        loss_ratio = abs(unrealized_pnl) / max(account_equity, 1.0)
        if loss_ratio < 0.10:
            return None
        
        return {
            "position_id": position_id,
            "ticker": ticker,
            "repair_type": "BEAR_CALL_SPREAD" if current_delta > 0 else "BULL_PUT_SPREAD",
            "delta_drift_pct": abs(current_delta),
            "repair_credit": max(50.0, min(500.0, abs(unrealized_pnl) * 0.3)),
            "new_max_loss": max_loss - (abs(unrealized_pnl) * 0.3),
            "priority": self._calculate_priority(abs(current_delta), loss_ratio),
            "confidence_boost": min(0.15, abs(current_delta) * 0.3),
        }
    
    def find_hedge_strikes(
        self,
        position_id: str,
        ticker: str,
        strategy_type: str,
        current_delta: float,
        current_gamma: float,
        current_theta: float,
        current_vega: float,
        current_price: float,
        max_loss: float,
        unrealized_pnl: float,
        days_to_expiration: int,
        underlying_price: float,
        iv: float,
    ) -> Tuple[float, float]:
        """Find hedge strikes using Rust engine"""
        if self.rust_enabled:
            try:
                return self.rust_engine.find_hedge_strikes(
                    position_id=position_id,
                    ticker=ticker,
                    strategy_type=strategy_type,
                    current_delta=current_delta,
                    current_gamma=current_gamma,
                    current_theta=current_theta,
                    current_vega=current_vega,
                    current_price=current_price,
                    max_loss=max_loss,
                    unrealized_pnl=unrealized_pnl,
                    days_to_expiration=days_to_expiration,
                    underlying_price=underlying_price,
                    iv=iv,
                )
            except Exception as e:
                logger.error(f"Rust hedge calculation failed: {e}")
                self.rust_enabled = False
        
        # Python fallback
        if current_delta > 0:
            return (round(underlying_price), round(underlying_price + 5))
        else:
            return (round(underlying_price - 5), round(underlying_price - 10))
    
    def _calculate_priority(self, delta_drift: float, loss_ratio: float) -> str:
        """Calculate priority level"""
        risk_score = delta_drift * 0.6 + loss_ratio * 0.4
        
        if risk_score > 0.40:
            return "CRITICAL"
        elif risk_score > 0.30:
            return "HIGH"
        elif risk_score > 0.20:
            return "MEDIUM"
        else:
            return "LOW"


def get_engine_status() -> Dict[str, Any]:
    """Get current engine status (Rust vs Python)"""
    return {
        "rust_available": RUST_AVAILABLE,
        "edge_physics_version": getattr(edge_physics, "__version__", "unknown") if RUST_AVAILABLE else "N/A",
        "mode": "production" if RUST_AVAILABLE else "compatibility",
    }
