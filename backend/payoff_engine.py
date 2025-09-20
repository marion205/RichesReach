# Payoff engine for complex option strategies
from dataclasses import dataclass
from typing import Literal, List, Dict
import numpy as np

LegType = Literal["call", "put"]
Action   = Literal["buy", "sell"]

@dataclass(frozen=True)
class OptionLeg:
    kind: LegType
    action: Action
    strike: float
    premium: float      # per unit
    quantity: int       # positive integer
    multiplier: int = 100

def leg_payoff_at_expiry(S: float, leg: OptionLeg) -> float:
    """Payoff at expiry (excluding carrying costs/fees)."""
    q = leg.quantity * leg.multiplier
    if leg.kind == "call":
        intrinsic = max(0.0, S - leg.strike)
    else:
        intrinsic = max(0.0, leg.strike - S)

    payoff_long = intrinsic - leg.premium
    payoff_short = -payoff_long

    return q * (payoff_long if leg.action == "buy" else payoff_short)

def strategy_profile(legs: List[OptionLeg], S_grid: np.ndarray) -> Dict[str, np.ndarray]:
    """Vectorized payoff across price grid."""
    total = np.zeros_like(S_grid, dtype=float)
    per_leg = {}
    for i, leg in enumerate(legs):
        leg_pay = np.array([leg_payoff_at_expiry(S, leg) for S in S_grid])
        per_leg[f"leg_{i}"] = leg_pay
        total += leg_pay
    return {"S": S_grid, "total": total, **per_leg}

def summary_from_profile(profile: Dict[str, np.ndarray]) -> Dict[str, float]:
    """Derive max profit/loss and breakevens from a payoff profile."""
    S = profile["S"]
    P = profile["total"]
    idx_max = int(P.argmax())
    idx_min = int(P.argmin())
    max_profit = float(P[idx_max])
    max_loss   = float(P[idx_min])
    # Breakevens where payoff crosses zero (linear segments between grid points)
    zeros = []
    for i in range(len(S)-1):
        if P[i] == 0:
            zeros.append(S[i])
        elif (P[i] < 0 and P[i+1] > 0) or (P[i] > 0 and P[i+1] < 0):
            # linear interpolation
            s0, s1 = S[i], S[i+1]
            p0, p1 = P[i], P[i+1]
            s_be = s0 + (0 - p0) * (s1 - s0) / (p1 - p0)
            zeros.append(float(s_be))
    return {
        "max_profit": max_profit,
        "max_loss": max_loss,
        "breakevens": sorted(set(round(z, 4) for z in zeros)),
        "argmax_S": float(S[idx_max]),
        "argmin_S": float(S[idx_min]),
    }

def covered_call(current_price: float, stock_qty: int, call_strike: float, call_premium: float):
    """
    Stock + short call (1 call per 100 shares).
    Represent stock P/L as a synthetic 'leg' with zero strike and linear payoff.
    """
    # Represent stock via dense grid math (not an option leg)
    S_grid = np.linspace(max(0.01, current_price*0.5), current_price*1.5, 1201)
    # Option leg (sell call)
    legs = [OptionLeg(kind="call", action="sell", strike=call_strike, premium=call_premium, quantity=stock_qty // 100)]
    prof = strategy_profile(legs, S_grid)
    # Add stock P/L: (S - entry) * qty
    stock_pl = (S_grid - current_price) * stock_qty
    prof["total"] = prof["total"] + stock_pl
    return prof, summary_from_profile(prof)

def vertical_call_spread(K_long: float, prem_long: float, K_short: float, prem_short: float, qty: int = 1):
    S_grid = np.linspace(max(0.01, K_long*0.5), K_short*1.5, 1201)
    legs: List[OptionLeg] = [
        OptionLeg("call","buy",  K_long,  prem_long,  qty),
        OptionLeg("call","sell", K_short, prem_short, qty)
    ]
    prof = strategy_profile(legs, S_grid)
    return prof, summary_from_profile(prof)

def vertical_put_spread(K_long: float, prem_long: float, K_short: float, prem_short: float, qty: int = 1):
    S_grid = np.linspace(max(0.01, K_short*0.5), K_long*1.5, 1201)
    legs: List[OptionLeg] = [
        OptionLeg("put","buy",  K_long,  prem_long,  qty),
        OptionLeg("put","sell", K_short, prem_short, qty)
    ]
    prof = strategy_profile(legs, S_grid)
    return prof, summary_from_profile(prof)

def iron_condor(Kp_buy: float, Kp_sell: float, Kc_sell: float, Kc_buy: float,
                prem_p_buy: float, prem_p_sell: float, prem_c_sell: float, prem_c_buy: float, qty: int = 1):
    assert Kp_buy < Kp_sell < Kc_sell < Kc_buy
    S_grid = np.linspace(max(0.01, Kp_buy*0.6), Kc_buy*1.4, 1601)
    legs: List[OptionLeg] = [
        OptionLeg("put","buy",  Kp_buy,  prem_p_buy,  qty),
        OptionLeg("put","sell", Kp_sell, prem_p_sell, qty),
        OptionLeg("call","sell",Kc_sell, prem_c_sell, qty),
        OptionLeg("call","buy", Kc_buy,  prem_c_buy,  qty),
    ]
    prof = strategy_profile(legs, S_grid)
    return prof, summary_from_profile(prof)

def straddle(K: float, prem_call: float, prem_put: float, qty: int = 1):
    """Long straddle: buy call and put at same strike"""
    S_grid = np.linspace(max(0.01, K*0.5), K*1.5, 1201)
    legs: List[OptionLeg] = [
        OptionLeg("call","buy", K, prem_call, qty),
        OptionLeg("put","buy",  K, prem_put,  qty)
    ]
    prof = strategy_profile(legs, S_grid)
    return prof, summary_from_profile(prof)

def strangle(K_call: float, K_put: float, prem_call: float, prem_put: float, qty: int = 1):
    """Long strangle: buy call and put at different strikes"""
    assert K_put < K_call
    S_grid = np.linspace(max(0.01, K_put*0.5), K_call*1.5, 1201)
    legs: List[OptionLeg] = [
        OptionLeg("call","buy", K_call, prem_call, qty),
        OptionLeg("put","buy",  K_put,  prem_put,  qty)
    ]
    prof = strategy_profile(legs, S_grid)
    return prof, summary_from_profile(prof)

def butterfly_call(K1: float, K2: float, K3: float, 
                  prem1: float, prem2: float, prem3: float, qty: int = 1):
    """Call butterfly: buy K1, sell 2x K2, buy K3"""
    assert K1 < K2 < K3
    S_grid = np.linspace(max(0.01, K1*0.5), K3*1.5, 1201)
    legs: List[OptionLeg] = [
        OptionLeg("call","buy",  K1, prem1, qty),
        OptionLeg("call","sell", K2, prem2, qty*2),
        OptionLeg("call","buy",  K3, prem3, qty)
    ]
    prof = strategy_profile(legs, S_grid)
    return prof, summary_from_profile(prof)

def calculate_risk_metrics(profile: Dict[str, np.ndarray]) -> Dict[str, float]:
    """Calculate additional risk metrics from payoff profile"""
    S = profile["S"]
    P = profile["total"]
    
    # Find profit zone
    profit_mask = P > 0
    if np.any(profit_mask):
        profit_zone = S[profit_mask]
        profit_width = float(profit_zone.max() - profit_zone.min())
    else:
        profit_width = 0.0
    
    # Calculate probability of profit (assuming log-normal distribution)
    # This is a simplified calculation - in practice you'd use the actual distribution
    prob_profit = float(np.mean(P > 0))
    
    # Calculate expected value (simplified)
    expected_value = float(np.mean(P))
    
    # Calculate standard deviation
    std_dev = float(np.std(P))
    
    return {
        "profit_zone_width": profit_width,
        "prob_profit": prob_profit,
        "expected_value": expected_value,
        "std_dev": std_dev,
        "sharpe_ratio": expected_value / std_dev if std_dev > 0 else 0
    }
