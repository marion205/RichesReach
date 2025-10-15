# scoring/beginner_score.py
from dataclasses import dataclass
from math import log10, tanh
from typing import Dict, List, Tuple, Any

Number = float

def _safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        if x in (None, "None", ""):
            return default
        return float(x)
    except Exception:
        return default

def _clamp(x: Number, lo: Number, hi: Number) -> Number:
    return max(lo, min(hi, x))

def _as_pct(yield_val: float) -> float:
    """Handle vendor inconsistencies: treat values > 1 as % already, else convert."""
    if yield_val != yield_val:  # NaN
        return 0.0
    return yield_val if yield_val > 1.0 else yield_val * 100.0

@dataclass
class Factor:
    name: str
    weight: float
    value: float
    contrib: float
    detail: str

@dataclass
class BeginnerScore:
    score: int                 # 0..100
    factors: List[Factor]      # explainability
    notes: List[str]           # any fallbacks / imputations

# Optional: sector baseline risk levels (extend as needed)
SECTOR_RISK = {
    "Utilities": 0.85, "Consumer Defensive": 0.85, "Healthcare": 0.8,
    "Financial Services": 0.7, "Technology": 0.65, "Consumer Cyclical": 0.6,
    "Energy": 0.55, "Basic Materials": 0.55, "Communication Services": 0.65,
    "Industrials": 0.65, "Real Estate": 0.7,
}

WELL_KNOWN = {"Apple","Microsoft","Amazon","Google","Alphabet","Tesla",
              "Johnson & Johnson","Procter & Gamble","Meta","NVIDIA"}

def compute_beginner_score(overview: Dict[str, Any],
                           market: Dict[str, Any],
                           user_budget: float = 1000.0) -> BeginnerScore:
    """
    overview: fundamentals blob (e.g., AlphaVantage 'OVERVIEW' or Polygon profile)
    market: real-time blob with price/volume/beta/avgDollarVolume/realizedVol etc.
    """
    notes: List[str] = []

    # ---------- Extract with safety ----------
    name = str(overview.get("Name") or overview.get("companyName") or "")
    sector = str(overview.get("Sector") or overview.get("sector") or "")
    pe = _safe_float(overview.get("PERatio"))
    cap_raw = _safe_float(overview.get("MarketCapitalization"))
    beta = _safe_float(overview.get("Beta") or market.get("beta"))
    div_raw = _safe_float(overview.get("DividendYield"))
    yield_pct = _as_pct(div_raw)  # normalize to percentage
    margin = _safe_float(overview.get("ProfitMargin") or overview.get("netProfitMargin"))
    roe = _safe_float(overview.get("ReturnOnEquityTTM") or overview.get("roe"))
    debt_to_equity = _safe_float(overview.get("DebtToEquity") or overview.get("debtToEquity"))
    price = _safe_float(market.get("price"), 0.0)
    avg_dollar_vol = _safe_float(market.get("avgDollarVolume"))
    ann_vol = _safe_float(market.get("annualizedVol") or market.get("realizedVol"))  # 0..?
    ann_vol = _clamp(ann_vol, 0.0, 1.2) if ann_vol == ann_vol else 0.5  # NaN => neutral
    if avg_dollar_vol != avg_dollar_vol:
        avg_dollar_vol = 5e7  # default $50M/day if unknown
        notes.append("avgDollarVolume missing -> defaulted to $50M/day")
    if cap_raw != cap_raw:
        cap_raw = 2e10      # default $20B
        notes.append("MarketCap missing -> defaulted to $20B")

    # ---------- Normalizations (bounded 0..1) ----------
    # Size (log-scaled): $1B→0.2, $10B→0.5, $100B→0.8, $1T→~1.0
    z_size = _clamp((log10(max(cap_raw, 1)) - 9) / (12 - 9), 0, 1)

    # Value (P/E sweet spot ~10–25). Use piecewise to avoid NaNs/negatives.
    if pe == pe and pe > 0:
        if pe < 8:   z_pe = 0.6
        elif pe <= 22: z_pe = 1.0
        elif pe <= 35: z_pe = 0.6
        elif pe <= 50: z_pe = 0.35
        else:         z_pe = 0.2
    else:
        z_pe = 0.4  # unknown pe → conservative
        notes.append("PE missing/non-positive -> conservative value score")

    # Dividend: reward sustainable range; taper outside 2–6%
    y = yield_pct
    if y <= 0: z_div = 0.0
    elif 2 <= y <= 6: z_div = 1.0
    else: z_div = _clamp(1 - abs(y - 4) / 10, 0.2, 0.8)

    # Sector comfort baseline
    z_sector = SECTOR_RISK.get(sector, 0.6)

    # Volatility & beta (inverted): lower vol/beta → higher beginner suitability
    z_vol = 1.0 - _clamp(ann_vol / 0.8, 0.0, 1.0)            # 0 vol ⇒ 1.0, 0.8 ⇒ 0.0
    z_beta = 1.0 - _clamp(abs(beta if beta == beta else 1.0) / 1.5, 0.0, 1.0)

    # Liquidity (dollar turnover): $10M/day ~0.3, $50M ~0.6, $200M+ ~1.0
    z_liq = _clamp((log10(max(avg_dollar_vol, 1)) - 7) / (8.3 - 7), 0.0, 1.0)

    # Quality: prefer profitable & efficient
    z_margin = _clamp(((_safe_float(margin, 0.0)) + 0.10) / 0.25, 0.0, 1.0)  # -10%..15% → 0..1
    z_roe = _clamp((_safe_float(roe, 0.0)) / 20.0, 0.0, 1.0)                 # 0..20% → 0..1
    z_quality = 0.6 * z_margin + 0.4 * z_roe

    # Leverage penalty (higher D/E → lower): 0.0 at 3.0+, 1.0 at 0.0
    de = _safe_float(debt_to_equity, 1.0)
    z_leverage = 1.0 - _clamp(de / 3.0, 0.0, 1.0)

    # Name familiarity (tiny boost only)
    z_fame = 1.0 if any(n.lower() in name.lower() for n in WELL_KNOWN) else 0.0

    # Budget-aware affordability factor
    # For beginners, we want stocks that are affordable relative to their budget
    # Higher score for stocks that allow for meaningful position sizes
    if price > 0 and user_budget > 0:
        # Calculate how many shares they could buy (minimum 1 share)
        max_shares = max(1, int(user_budget / price))
        position_value = max_shares * price
        
        # Score based on position size as % of budget
        position_pct = position_value / user_budget
        
        # Sweet spot: 5-20% of budget per stock (allows diversification)
        if 0.05 <= position_pct <= 0.20:
            z_affordability = 1.0
        elif 0.02 <= position_pct <= 0.30:
            z_affordability = 0.8
        elif 0.01 <= position_pct <= 0.50:
            z_affordability = 0.6
        elif position_pct <= 0.80:  # Still affordable but less ideal
            z_affordability = 0.4
        else:  # Too expensive or too cheap
            z_affordability = 0.2
    else:
        z_affordability = 0.5  # Neutral if price/budget unknown
        notes.append("Price or budget unknown -> neutral affordability score")

    # ---------- Weights tuned for BEGINNER suitability ----------
    weights = {
        "Size": 0.16, "Sector": 0.12, "Value(PE)": 0.10, "Dividend": 0.10,
        "Volatility": 0.16, "Beta": 0.08, "Liquidity": 0.10,
        "Quality": 0.12, "Leverage": 0.03, "Fame": 0.01, "Affordability": 0.12
    }

    # Compute weighted score in 0..1
    z_map = {
        "Size": z_size, "Sector": z_sector, "Value(PE)": z_pe, "Dividend": z_div,
        "Volatility": z_vol, "Beta": z_beta, "Liquidity": z_liq,
        "Quality": z_quality, "Leverage": z_leverage, "Fame": z_fame, "Affordability": z_affordability
    }
    raw = sum(weights[k] * z_map[k] for k in weights)

    # Smooth with tanh to avoid edge spiking, then map to 0..100
    smooth = 0.5 + 0.5 * tanh((raw - 0.55) * 2.2)  # center ~0.55
    score = int(round(_clamp(smooth, 0.0, 1.0) * 100))

    # Build explainability
    factors: List[Factor] = []
    for k in weights:
        factors.append(Factor(
            name=k,
            weight=weights[k],
            value=round(z_map[k], 3),
            contrib=round(weights[k] * z_map[k] * 100, 1),
            detail=(
                f"{k} z={z_map[k]:.2f} weight={weights[k]:.2f}"
            ),
        ))

    return BeginnerScore(score=score, factors=factors, notes=notes)
