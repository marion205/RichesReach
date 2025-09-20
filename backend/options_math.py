# Enhanced options math with correct N(d2) implementation and full distribution analysis
from dataclasses import dataclass
from math import log, sqrt, exp
from typing import Literal, Optional, List, Dict, Tuple
from scipy.stats import norm
from scipy.optimize import brentq
import numpy as np

OptionType = Literal["call", "put"]

@dataclass(frozen=True)
class BSParams:
    S: float         # underlying price
    K: float         # strike
    T: float         # years to expiry
    r: float         # risk-free (cont. comp)
    q: float = 0.0   # dividend yield (cont. comp)

def _d1(params: BSParams, sigma: float) -> float:
    S, K, T, r, q = params.S, params.K, params.T, params.r, params.q
    return (log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))

def _d2(params: BSParams, sigma: float) -> float:
    return _d1(params, sigma) - sigma * sqrt(params.T)

def bs_price(params: BSParams, sigma: float, kind: OptionType) -> float:
    """Black–Scholes–Merton with continuous dividend yield q."""
    S, K, T, r, q = params.S, params.K, params.T, params.r, params.q
    d1, d2 = _d1(params, sigma), _d2(params, sigma)
    df_r, df_q = exp(-r*T), exp(-q*T)
    if kind == "call":
        return df_q * S * norm.cdf(d1) - df_r * K * norm.cdf(d2)
    else:
        return df_r * K * norm.cdf(-d2) - df_q * S * norm.cdf(-d1)

def bs_delta(params: BSParams, sigma: float, kind: OptionType) -> float:
    d1 = _d1(params, sigma)
    sign = 1.0 if kind == "call" else -1.0
    return exp(-params.q*params.T) * (norm.cdf(sign*d1) * sign)

def prob_itm(params: BSParams, sigma: float, kind: OptionType) -> float:
    """
    Risk-neutral probability an option finishes ITM at expiry.
    Uses N(d2) for calls, N(-d2) for puts.
    """
    d2 = _d2(params, sigma)
    return norm.cdf(d2) if kind == "call" else norm.cdf(-d2)

def implied_vol(
    params: BSParams,
    kind: OptionType,
    mkt_price: float,
    *,
    lo: float = 1e-6,
    hi: float = 5.0,
    tol: float = 1e-7,
    max_iter: int = 100
) -> Optional[float]:
    """
    Robust Brent root finder for IV. Returns None if no solution in [lo, hi].
    """
    def f(sig: float) -> float:
        return bs_price(params, sig, kind) - mkt_price

    try:
        # Ensure bracket contains a sign change; expand if needed
        a, b = lo, hi
        fa, fb = f(a), f(b)
        if fa * fb > 0:
            # Expand hi a bit if needed
            b2 = min(10.0, hi * 2)
            fb = f(b2)
            if fa * fb > 0:
                return None
            b = b2
        return brentq(f, a, b, xtol=tol, maxiter=max_iter)
    except Exception:
        return None

def calculate_greeks(params: BSParams, sigma: float, kind: OptionType) -> Dict[str, float]:
    """Calculate all option Greeks"""
    S, K, T, r, q = params.S, params.K, params.T, params.r, params.q
    d1 = _d1(params, sigma)
    d2 = _d2(params, sigma)
    
    # Common terms
    sqrt_T = sqrt(T)
    df_r = exp(-r * T)
    df_q = exp(-q * T)
    n_d1 = norm.pdf(d1)
    n_d2 = norm.pdf(d2)
    
    if kind == "call":
        cdf_d1 = norm.cdf(d1)
        cdf_d2 = norm.cdf(d2)
        cdf_neg_d1 = norm.cdf(-d1)
        cdf_neg_d2 = norm.cdf(-d2)
    else:
        cdf_d1 = norm.cdf(-d1)
        cdf_d2 = norm.cdf(-d2)
        cdf_neg_d1 = norm.cdf(d1)
        cdf_neg_d2 = norm.cdf(d2)
    
    # Delta
    delta = df_q * cdf_d1 if kind == "call" else df_q * (cdf_d1 - 1)
    
    # Gamma (same for calls and puts)
    gamma = (df_q * n_d1) / (S * sigma * sqrt_T)
    
    # Theta
    if kind == "call":
        theta = (-S * df_q * n_d1 * sigma / (2 * sqrt_T) - 
                 r * K * df_r * cdf_d2 + q * S * df_q * cdf_d1)
    else:
        theta = (-S * df_q * n_d1 * sigma / (2 * sqrt_T) + 
                 r * K * df_r * cdf_neg_d2 - q * S * df_q * cdf_neg_d1)
    
    # Vega (same for calls and puts)
    vega = S * df_q * n_d1 * sqrt_T
    
    # Rho
    if kind == "call":
        rho = K * T * df_r * cdf_d2
    else:
        rho = -K * T * df_r * cdf_neg_d2
    
    return {
        'delta': float(delta),
        'gamma': float(gamma),
        'theta': float(theta),
        'vega': float(vega),
        'rho': float(rho)
    }

def expected_shortfall(returns: np.ndarray, confidence_level: float = 0.05) -> float:
    """Calculate Expected Shortfall (Conditional VaR)"""
    var = np.percentile(returns, confidence_level * 100)
    return np.mean(returns[returns <= var])

def value_at_risk(returns: np.ndarray, confidence_level: float = 0.05) -> float:
    """Calculate Value at Risk"""
    return np.percentile(returns, confidence_level * 100)

def kelly_size(win_prob: float, win_loss_ratio: float, cap: float = 0.02) -> float:
    """Capped Kelly position sizing"""
    f = win_prob - (1 - win_prob) / win_loss_ratio
    return max(0, min(cap, f))

def position_size(prob_up: float, r_up: float = 1.0, r_down: float = 0.7, 
                 es_limit: float = 0.04, current_es: float = 0.025) -> float:
    """Calculate position size with ES guardrail"""
    k = kelly_size(prob_up, r_up / (1 - r_down), 0.03)
    scale = 0.5 if current_es > es_limit else 1.0
    return k * scale

def generate_return_distribution(S: float, sigma: float, T: float, 
                               n_simulations: int = 10000) -> np.ndarray:
    """Generate Monte Carlo return distribution"""
    dt = T / 252  # Daily time step
    n_steps = int(T * 252)
    
    returns = []
    for _ in range(n_simulations):
        S_t = S
        for _ in range(n_steps):
            dW = np.random.normal(0, np.sqrt(dt))
            S_t *= (1 + sigma * dW)
        returns.append((S_t - S) / S)
    
    return np.array(returns)

def calculate_probability_bins(returns: np.ndarray, bins: List[float] = None) -> Dict[str, float]:
    """Calculate probability of returns in specified bins"""
    if bins is None:
        bins = [-0.1, -0.05, -0.02, 0, 0.02, 0.05, 0.1, 0.2, 0.5]
    
    probs = {}
    for i in range(len(bins) - 1):
        bin_name = f"{bins[i]:.1%} to {bins[i+1]:.1%}"
        prob = np.mean((returns >= bins[i]) & (returns < bins[i+1]))
        probs[bin_name] = float(prob)
    
    return probs

def calculate_implied_volatility_surface(strikes: List[float], expirations: List[float], 
                                       S: float, r: float, market_prices: List[List[float]]) -> np.ndarray:
    """Calculate implied volatility surface"""
    iv_surface = np.zeros((len(expirations), len(strikes)))
    
    for i, T in enumerate(expirations):
        for j, K in enumerate(strikes):
            if i < len(market_prices) and j < len(market_prices[i]):
                try:
                    params = BSParams(S=S, K=K, T=T, r=r)
                    iv = implied_vol(params, "call", market_prices[i][j])
                    iv_surface[i, j] = iv if iv is not None else np.nan
                except:
                    iv_surface[i, j] = np.nan
    
    return iv_surface