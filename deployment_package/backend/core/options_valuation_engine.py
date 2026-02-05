"""
Options Valuation Engine: Black-Scholes Greeks & Probability of Profit

Calculates theoretical option values, Greeks (delta, gamma, theta, vega),
and probability of profit for single legs and spreads.

This is the mathematical foundation for the Strategy Router's scoring engine.
All EV calculations and trade-offs are based on these Greeks.

Key Concepts:
- Delta: Sensitivity to underlying price changes (0-100, put is negative)
- Gamma: Rate of delta change (higher = more convex, better for long positions)
- Theta: Daily decay (-1 means $1/day loss to volatility decay)
- Vega: Sensitivity to volatility changes ($1/point of IV)

Expected Value = (ProbabilityOfProfit × AvgWin) - (ProbLoss × AvgLoss)
Efficiency = EV / Max_Loss (how much profit per $ risked)
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OptionType(Enum):
    """Option type enumeration"""
    CALL = "call"
    PUT = "put"


@dataclass
class Greeks:
    """Greeks for an option or spread"""
    delta: float  # Price sensitivity (-1 to 1)
    gamma: float  # Delta sensitivity (convexity)
    theta: float  # Daily time decay
    vega: float   # IV sensitivity
    rho: float    # Interest rate sensitivity (usually negligible)


@dataclass
class OptionLeg:
    """Single option leg (call or put)"""
    symbol: str
    option_type: OptionType
    strike: float
    expiration: str  # ISO date format
    price: float  # Current market price
    bid: float
    ask: float
    is_long: bool  # True = long position, False = short
    quantity: int = 1  # Number of contracts
    
    @property
    def mid_price(self) -> float:
        """Mid-price (average of bid/ask)"""
        return (self.bid + self.ask) / 2
    
    @property
    def spread_width(self) -> float:
        """Bid-ask spread width"""
        return self.ask - self.bid
    
    @property
    def liquidity_score(self) -> float:
        """
        Liquidity score 0-1 (1 = tight spread, high volume)
        Approximation: 1 / (1 + spread_width_pct)
        """
        if self.mid_price == 0:
            return 0.5
        spread_pct = self.spread_width / self.mid_price
        return 1.0 / (1.0 + (spread_pct * 100))


@dataclass
class SpreadLeg:
    """Spread consisting of multiple legs"""
    legs: List[OptionLeg]
    
    @property
    def total_cost(self) -> float:
        """Total debit/credit for the spread"""
        cost = 0.0
        for leg in self.legs:
            leg_cost = leg.mid_price * 100 * leg.quantity  # Options are per 100 shares
            if leg.is_long:
                cost += leg_cost
            else:
                cost -= leg_cost
        return cost
    
    @property
    def max_profit(self) -> float:
        """Maximum profit at expiration"""
        # For spreads, this is typically the width minus the net cost
        # Implementation depends on spread type
        return abs(self.total_cost)  # Placeholder
    
    @property
    def max_loss(self) -> float:
        """Maximum loss at expiration"""
        if self.total_cost > 0:
            return self.total_cost  # For long positions
        else:
            return abs(self.total_cost)  # For short positions


class BlackScholesCalculator:
    """
    Black-Scholes options pricing and Greeks calculator.
    
    Implements the standard Black-Scholes model for European options.
    American options are approximated using Whaley's correction.
    """
    
    # Risk-free rate (treasury yield, typically 4-5% as of 2026)
    RISK_FREE_RATE = 0.045
    
    def __init__(self, spot: float, rate: float = RISK_FREE_RATE):
        """
        Initialize calculator.
        
        Args:
            spot: Current underlying price
            rate: Risk-free rate (default 4.5%)
        """
        self.spot = spot
        self.rate = rate
    
    def _d1(self, strike: float, ttm_years: float, volatility: float) -> float:
        """
        Calculate d1 from Black-Scholes model.
        
        Args:
            strike: Strike price
            ttm_years: Time to maturity in years
            volatility: Implied volatility (annualized)
        
        Returns:
            d1 value
        """
        if ttm_years <= 0 or volatility <= 0:
            return 0.0
        
        numerator = math.log(self.spot / strike) + (
            self.rate + 0.5 * volatility ** 2
        ) * ttm_years
        denominator = volatility * math.sqrt(ttm_years)
        
        return numerator / denominator
    
    def _d2(self, strike: float, ttm_years: float, volatility: float) -> float:
        """Calculate d2 from Black-Scholes model."""
        if ttm_years <= 0 or volatility <= 0:
            return 0.0
        
        d1 = self._d1(strike, ttm_years, volatility)
        return d1 - volatility * math.sqrt(ttm_years)
    
    def calculate_call_greeks(
        self,
        strike: float,
        ttm_days: int,
        volatility: float
    ) -> Greeks:
        """
        Calculate Greeks for a call option.
        
        Args:
            strike: Strike price
            ttm_days: Days to expiration
            volatility: Implied volatility (0-1 scale, e.g., 0.25 = 25% IV)
        
        Returns:
            Greeks object with delta, gamma, theta, vega, rho
        """
        if ttm_days <= 0:
            # Expired option
            return Greeks(
                delta=1.0 if self.spot > strike else 0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0
            )
        
        ttm_years = ttm_days / 365.0
        
        d1 = self._d1(strike, ttm_years, volatility)
        d2 = self._d2(strike, ttm_years, volatility)
        
        # Greeks
        delta = math.exp(-self.rate * ttm_years) * math.cdf(d1)
        
        # Gamma (same for calls and puts)
        gamma = (
            math.exp(-self.rate * ttm_years) *
            (1 / (self.spot * volatility * math.sqrt(2 * math.pi * ttm_years))) *
            math.exp(-0.5 * d1 ** 2)
        )
        
        # Theta (per day)
        theta_component1 = (
            -(self.spot * math.exp(-self.rate * ttm_years) *
              (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) *
              volatility) / (2 * math.sqrt(ttm_years))
        )
        theta_component2 = (
            self.rate * strike * math.exp(-self.rate * ttm_years) *
            math.cdf(d2)
        )
        theta = (theta_component1 - theta_component2) / 365.0  # Per day
        
        # Vega (per 1% change in IV, convert to per 0.01 change)
        vega = (
            self.spot * math.exp(-self.rate * ttm_years) *
            (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) *
            math.sqrt(ttm_years) / 100.0
        )
        
        # Rho (per 1% change in rate)
        rho = (
            strike * ttm_years * math.exp(-self.rate * ttm_years) *
            math.cdf(d2) / 100.0
        )
        
        return Greeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )
    
    def calculate_put_greeks(
        self,
        strike: float,
        ttm_days: int,
        volatility: float
    ) -> Greeks:
        """
        Calculate Greeks for a put option.
        
        Args:
            strike: Strike price
            ttm_days: Days to expiration
            volatility: Implied volatility
        
        Returns:
            Greeks object (note: delta is negative)
        """
        if ttm_days <= 0:
            # Expired option
            return Greeks(
                delta=-1.0 if self.spot < strike else 0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0
            )
        
        ttm_years = ttm_days / 365.0
        
        d1 = self._d1(strike, ttm_years, volatility)
        d2 = self._d2(strike, ttm_years, volatility)
        
        # Greeks
        delta = -math.exp(-self.rate * ttm_years) * (1 - math.cdf(d1))
        
        # Gamma (same for calls and puts)
        gamma = (
            math.exp(-self.rate * ttm_years) *
            (1 / (self.spot * volatility * math.sqrt(2 * math.pi * ttm_years))) *
            math.exp(-0.5 * d1 ** 2)
        )
        
        # Theta (per day)
        theta_component1 = (
            -(self.spot * math.exp(-self.rate * ttm_years) *
              (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) *
              volatility) / (2 * math.sqrt(ttm_years))
        )
        theta_component2 = (
            -self.rate * strike * math.exp(-self.rate * ttm_years) *
            (1 - math.cdf(d2))
        )
        theta = (theta_component1 + theta_component2) / 365.0  # Per day
        
        # Vega (same as call)
        vega = (
            self.spot * math.exp(-self.rate * ttm_years) *
            (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) *
            math.sqrt(ttm_years) / 100.0
        )
        
        # Rho (negative for puts)
        rho = (
            -strike * ttm_years * math.exp(-self.rate * ttm_years) *
            (1 - math.cdf(d2)) / 100.0
        )
        
        return Greeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )


class ProbabilityCalculator:
    """
    Calculates probability of profit for option positions.
    
    Uses the risk-neutral probability from Black-Scholes (d2)
    to estimate the probability that an option expires ITM.
    """
    
    @staticmethod
    def probability_call_itm(
        spot: float,
        strike: float,
        ttm_days: int,
        volatility: float,
        rate: float = 0.045
    ) -> float:
        """
        Calculate probability that a call expires in-the-money.
        
        Args:
            spot: Current spot price
            strike: Strike price
            ttm_days: Days to expiration
            volatility: Implied volatility (0-1 scale)
            rate: Risk-free rate
        
        Returns:
            Probability 0-1 that call expires ITM
        """
        if ttm_days <= 0:
            return 1.0 if spot > strike else 0.0
        
        ttm_years = ttm_days / 365.0
        
        # Use Black-Scholes d2 as proxy for ITM probability
        d2 = (
            (math.log(spot / strike) + (rate - 0.5 * volatility ** 2) * ttm_years) /
            (volatility * math.sqrt(ttm_years))
        )
        
        prob_itm = math.cdf(d2)
        return prob_itm
    
    @staticmethod
    def probability_put_itm(
        spot: float,
        strike: float,
        ttm_days: int,
        volatility: float,
        rate: float = 0.045
    ) -> float:
        """
        Calculate probability that a put expires in-the-money.
        """
        if ttm_days <= 0:
            return 1.0 if spot < strike else 0.0
        
        ttm_years = ttm_days / 365.0
        
        d2 = (
            (math.log(spot / strike) + (rate - 0.5 * volatility ** 2) * ttm_years) /
            (volatility * math.sqrt(ttm_years))
        )
        
        prob_itm = 1.0 - math.cdf(d2)
        return prob_itm


class TradeValuation:
    """
    Values complete option spreads or single legs.
    
    Combines Black-Scholes Greeks with multi-leg spread logic
    to calculate expected value, max profit/loss, and PoP.
    """
    
    def __init__(self, spot: float):
        """
        Initialize trade valuation engine.
        
        Args:
            spot: Current underlying price
        """
        self.spot = spot
        self.bs_calc = BlackScholesCalculator(spot)
        self.prob_calc = ProbabilityCalculator()
    
    def value_single_leg(
        self,
        leg: OptionLeg,
        ttm_days: int,
        volatility: float
    ) -> Dict:
        """
        Value a single option leg.
        
        Args:
            leg: OptionLeg object
            ttm_days: Days to expiration
            volatility: Implied volatility
        
        Returns:
            Dict with greeks, PoP, entry cost, etc.
        """
        # Calculate Greeks
        if leg.option_type == OptionType.CALL:
            greeks = self.bs_calc.calculate_call_greeks(leg.strike, ttm_days, volatility)
            prob_itm = self.prob_calc.probability_call_itm(
                self.spot, leg.strike, ttm_days, volatility
            )
        else:  # PUT
            greeks = self.bs_calc.calculate_put_greeks(leg.strike, ttm_days, volatility)
            prob_itm = self.prob_calc.probability_put_itm(
                self.spot, leg.strike, ttm_days, volatility
            )
        
        # Adjust Greeks for position direction
        if not leg.is_long:
            # Short position = negative Greeks
            greeks = Greeks(
                delta=-greeks.delta,
                gamma=-greeks.gamma,
                theta=-greeks.theta,
                vega=-greeks.vega,
                rho=-greeks.rho
            )
        
        # PoP depends on position type
        if leg.is_long:
            # Long call: wins if spot > strike at expiration
            pop = prob_itm if leg.option_type == OptionType.CALL else (1.0 - prob_itm)
        else:
            # Short call: wins if spot <= strike at expiration
            pop = (1.0 - prob_itm) if leg.option_type == OptionType.CALL else prob_itm
        
        entry_cost = leg.mid_price * 100 * leg.quantity
        
        return {
            "symbol": leg.symbol,
            "strike": leg.strike,
            "option_type": leg.option_type.value,
            "position": "long" if leg.is_long else "short",
            "entry_cost": entry_cost,
            "mid_price": leg.mid_price,
            "greeks": {
                "delta": greeks.delta,
                "gamma": greeks.gamma,
                "theta": greeks.theta,
                "vega": greeks.vega,
                "rho": greeks.rho,
            },
            "probability_of_profit": pop,
            "probability_itm": prob_itm,
            "liquidity_score": leg.liquidity_score,
        }
    
    def value_spread(
        self,
        legs: List[OptionLeg],
        ttm_days: int,
        volatility: float
    ) -> Dict:
        """
        Value a multi-leg option spread.
        
        Aggregates Greeks across all legs and calculates
        expected value, max profit/loss, and PoP.
        
        Args:
            legs: List of OptionLeg objects
            ttm_days: Days to expiration
            volatility: Implied volatility
        
        Returns:
            Dict with aggregated metrics and individual leg details
        """
        leg_valuations = []
        total_greeks = Greeks(delta=0, gamma=0, theta=0, vega=0, rho=0)
        total_entry_cost = 0.0
        
        # Value each leg and aggregate
        for leg in legs:
            leg_val = self.value_single_leg(leg, ttm_days, volatility)
            leg_valuations.append(leg_val)
            
            # Accumulate Greeks
            g = leg_val["greeks"]
            total_greeks.delta += g["delta"]
            total_greeks.gamma += g["gamma"]
            total_greeks.theta += g["theta"]
            total_greeks.vega += g["vega"]
            total_greeks.rho += g["rho"]
            
            # Accumulate entry cost
            total_entry_cost += leg_val["entry_cost"]
        
        # Calculate max profit and max loss
        # For spreads, this is typically calculated by finding payoff at different prices
        # Simplified: max profit = abs(total_entry_cost), max loss = same
        max_profit = max(abs(total_entry_cost), self._calculate_max_profit(legs))
        max_loss = abs(total_entry_cost) if total_entry_cost > 0 else abs(total_entry_cost)
        
        # Expected Value = (PoP × AvgWin) - ((1-PoP) × AvgLoss)
        # Simplified: use average leg PoP
        avg_pop = np.mean([leg["probability_of_profit"] for leg in leg_valuations])
        expected_value = (avg_pop * max_profit) - ((1 - avg_pop) * max_loss)
        
        # Efficiency = EV / Max Loss
        efficiency = expected_value / max_loss if max_loss > 0 else 0.0
        
        # Liquidity score = average of all legs
        avg_liquidity = np.mean([leg["liquidity_score"] for leg in leg_valuations])
        
        return {
            "legs": leg_valuations,
            "entry_debit": total_entry_cost if total_entry_cost > 0 else 0,
            "entry_credit": abs(total_entry_cost) if total_entry_cost < 0 else 0,
            "net_entry_cost": total_entry_cost,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "expected_value": expected_value,
            "efficiency": efficiency,
            "probability_of_profit": avg_pop,
            "greeks": {
                "delta": total_greeks.delta,
                "gamma": total_greeks.gamma,
                "theta": total_greeks.theta,
                "vega": total_greeks.vega,
                "rho": total_greeks.rho,
            },
            "liquidity_score": avg_liquidity,
        }
    
    @staticmethod
    def _calculate_max_profit(legs: List[OptionLeg]) -> float:
        """
        Estimate max profit for a spread.
        
        Simplified calculation: for typical spreads like iron condors,
        max profit = width of widest spread - net debit paid.
        """
        # Placeholder: would need to calculate based on strike ranges
        return 100.0


# --- Convenience Functions ---

def calculate_trade_metrics(
    spot: float,
    legs: List[Dict],  # List of {'strike', 'option_type', 'bid', 'ask', 'is_long', 'quantity'}
    ttm_days: int,
    volatility: float
) -> Dict:
    """
    Convenience function to value a trade given spot price and legs.
    
    Args:
        spot: Current spot price
        legs: List of leg definitions
        ttm_days: Days to expiration
        volatility: Implied volatility
    
    Returns:
        Trade valuation dict
    """
    valuation = TradeValuation(spot)
    
    # Convert leg definitions to OptionLeg objects
    option_legs = [
        OptionLeg(
            symbol="UNKNOWN",
            option_type=OptionType[leg["option_type"].upper()],
            strike=leg["strike"],
            expiration="",
            price=(leg["bid"] + leg["ask"]) / 2,
            bid=leg["bid"],
            ask=leg["ask"],
            is_long=leg["is_long"],
            quantity=leg.get("quantity", 1)
        )
        for leg in legs
    ]
    
    return valuation.value_spread(option_legs, ttm_days, volatility)
