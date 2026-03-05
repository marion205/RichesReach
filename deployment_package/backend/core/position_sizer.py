"""
position_sizer.py
=================
Track 2 — Execution & Sizing.

Translates a directional signal (Bullish / Neutral / Bearish) + confidence
into a concrete position size as a fraction of investable capital.

Two sizing methods are provided:

1. **VolTargetSizer** (primary)
   Targets a fixed annualised volatility contribution from each position.
   Each stock is sized so that, if held at that weight, it contributes
   exactly `target_vol_pct` of annualised portfolio volatility.

       w = target_vol / stock_annual_vol

   Then scaled by a composite signal multiplier:
     direction × confidence × FSS score × ML score
     × stability_multiplier  (penalises single-fold IC dominance)
     × regime_gate           (reduces exposure when technical alpha turns off)
     × coverage_multiplier   (reduces size when earnings data is missing)

2. **KellySizer** (secondary / power-user)
   Quarter-Kelly fraction based on estimated edge (IC) and odds.
   Conservative (0.25× Kelly) to avoid the overbetting pathology.

       f* = 0.25 × (p × b − q) / b
       where p = P(win), b = avg_win/avg_loss, q = 1 − p

Both sizers return a `SizingResult` with:
  - `weight`           : fraction of portfolio to allocate (0.0–1.0)
  - `shares`           : integer share count given portfolio_value + current_price
  - `method`           : "vol_target" | "kelly" | "zero"
  - `sizing_notes`     : list of plain-English notes explaining the sizing decision
  - `risk_contribution`: expected annualised vol contribution of this position

Portfolio-level helper `size_portfolio()` enforces:
  - Gross exposure cap (default 95%)
  - Sector concentration cap (default 25% per sector)
  - Correlation bucket cap (groups highly-correlated tickers, caps bucket exposure)

Usage
-----
    from .position_sizer import VolTargetSizer, SizingInput, ModelStats

    stats = ModelStats(mean_ic=0.014, std_ic=0.037)   # from walk-forward CV
    sizer = VolTargetSizer(
        target_vol_pct=0.02,
        max_position_pct=0.08,
        model_stats=stats,
        regime="Expansion",   # from FSS engine / market regime model
    )
    result = sizer.size(SizingInput(
        symbol="AAPL",
        signal="Bullish",
        confidence="High",
        fss_score=72.5,
        ml_score=7.4,
        annual_vol=0.28,
        portfolio_value=100_000,
        current_price=185.50,
        sector="Technology",
        earnings_coverage=True,   # earnings data available for this ticker
    ))
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model statistics (from walk-forward CV)
# ---------------------------------------------------------------------------

@dataclass
class ModelStats:
    """
    Summary statistics from the walk-forward cross-validation run.
    Used to compute the stability multiplier and regime gate.

    Attributes
    ----------
    mean_ic : float
        Mean OOS Spearman IC across all folds.
    std_ic : float
        Standard deviation of IC across folds — captures fold-to-fold instability.
    fold_ics : list[float], optional
        Per-fold IC values (in chronological order).  Used to detect
        single-fold dominance (e.g. one fold contributing all positive IC).
    regime_ic : dict[str, float], optional
        IC by regime label.  When provided, stability_for_regime() uses the
        regime-specific IC mean instead of the global mean, which prevents the
        regime gate and stability multiplier from double-penalising the same
        underlying "model degrades in bear regimes" fact.
        Keys should match _REGIME_GATE keys (e.g. "Crisis", "Expansion").
    """
    mean_ic: float = 0.014
    std_ic: float = 0.037
    fold_ics: List[float] = field(default_factory=list)
    regime_ic: Dict[str, float] = field(default_factory=dict)

    def stability_multiplier(self) -> float:
        """
        Global stability: penalise strategies that only work in one fold.

        Formula: clamp(mean_ic / (std_ic + ε), 0, 1)

        Interpretation:
          mean_ic=0.014, std_ic=0.037 → 0.014/0.037 = 0.38
            → conservative when std >> mean (regime-fragile signal)
          mean_ic=0.05, std_ic=0.02   → clamped to 1.0
            → full sizing when signal is consistently positive

        NOTE: Use stability_for_regime() in VolTargetSizer instead of this
        method when a regime is known, to avoid double-penalising with
        the regime gate multiplier.

        Range: 0.0 – 1.0
        """
        eps = 1e-6
        raw = self.mean_ic / (self.std_ic + eps)
        return max(0.0, min(1.0, raw))

    def stability_for_regime(self, regime: str) -> float:
        """
        Regime-aware stability multiplier.  Orthogonalises the stability
        signal from the regime gate to prevent double-penalising.

        Logic
        -----
        Two cases:

        1. regime_ic is populated (preferred):
           Use the IC for this specific regime as the numerator.
           This measures "is the model stable *within* this regime?" rather
           than "is the model stable across all regimes including bear ones?"
           The regime gate then handles the *current* regime penalty separately.

           If regime_ic[regime] ≤ 0: return 0.0 (no edge in this regime)
           Otherwise: clamp(regime_ic[regime] / (std_ic + ε), 0, 1)

        2. regime_ic not populated (fallback):
           Use global stability_multiplier() but clamp its lower bound to
           the regime gate value.  This prevents the compound product
           stability × regime_gate from going below regime_gate alone —
           i.e. the stability penalty can only add information *on top of*
           what the regime gate already captures, not repeat it.

           Combined floor: max(global_stability, regime_gate × 0.8)
           The 0.8 factor allows a small additional penalty if the global
           IC is truly unstable even within the current regime.

        Range: 0.0 – 1.0
        """
        regime_gate = _regime_gate_multiplier(regime)

        if self.regime_ic:
            # Exact or partial regime match in regime_ic dict
            ic_val = self.regime_ic.get(regime)
            if ic_val is None:
                # Try case-insensitive
                for k, v in self.regime_ic.items():
                    if k.lower() == regime.lower():
                        ic_val = v
                        break
            if ic_val is not None:
                if ic_val <= 0.0:
                    return 0.0   # signal has no edge in this regime
                eps = 1e-6
                raw = float(ic_val) / (self.std_ic + eps)
                return max(0.0, min(1.0, raw))

        # Fallback: global stability with regime-gate floor
        global_stab = self.stability_multiplier()
        # Allow global stability to reduce below regime_gate only by 20%
        floor = regime_gate * 0.8
        return max(floor, global_stab)

    def single_fold_dominance(self) -> bool:
        """
        Returns True if one fold is doing almost all the work.
        Heuristic: max(|IC|) > 3 × mean(|IC|) across folds with >1 fold.
        """
        if len(self.fold_ics) < 2:
            return False
        abs_ics = [abs(x) for x in self.fold_ics]
        avg_abs = sum(abs_ics) / len(abs_ics)
        if avg_abs < 1e-8:
            return False
        return max(abs_ics) > 3.0 * avg_abs


# ---------------------------------------------------------------------------
# Regime gate
# ---------------------------------------------------------------------------

# Regimes where momentum/technical features are known to underperform
_REGIME_GATE: Dict[str, float] = {
    # High-rate / value-rotation regimes: momentum underperforms
    "Deflation":         0.50,   # bear + low vol: reduce exposure
    "Crisis":            0.25,   # bear + high vol: minimal exposure
    "value_rotation":    0.55,   # regime label from ML service
    "bear_market":       0.50,
    "high_volatility":   0.65,
    # Momentum-friendly regimes: full exposure allowed
    "Expansion":         1.00,
    "Parabolic":         0.85,   # momentum works but reversal risk elevated
    "early_bull_market": 1.00,
    "late_bull_market":  0.90,
    "recovery":          0.95,
    "sideways_consolidation": 0.70,
    "correction":        0.75,
    "bubble_formation":  0.60,
    "Unknown":           0.80,   # conservative when regime unknown
}


def _regime_gate_multiplier(regime: str) -> float:
    """
    Look up the regime gate multiplier.
    Normalises regime string: case-insensitive, strips whitespace.
    Falls back to 0.80 for unrecognised regimes.
    """
    clean = regime.strip()
    # Exact match first
    if clean in _REGIME_GATE:
        return _REGIME_GATE[clean]
    # Case-insensitive match
    lower = clean.lower()
    for key, val in _REGIME_GATE.items():
        if key.lower() == lower:
            return val
    # Partial match (e.g. "Expansion regime" contains "Expansion")
    # Guard: require non-empty strings on both sides to avoid "" matching everything
    for key, val in _REGIME_GATE.items():
        if lower and key and (key.lower() in lower or lower in key.lower()):
            return val
    return 0.80


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SizingInput:
    """All inputs needed to compute a position size."""
    symbol: str
    signal: str                   # "Bullish" | "Neutral" | "Bearish"
    confidence: str               # "High" | "Medium" | "Low"
    fss_score: float              # 0–100
    annual_vol: float             # annualised realized vol of this stock (e.g. 0.28 = 28%)
    portfolio_value: float        # total investable capital in dollars
    current_price: float          # latest price per share

    # Optional ML signal
    ml_score: Optional[float] = None          # 0–10 (None if model not trained)
    predicted_return: Optional[float] = None  # vol-adjusted prediction

    # Regime context (from FSS engine or ML market regime model)
    regime: str = "Unknown"

    # Sector (for concentration caps)
    sector: str = "Unknown"

    # Earnings coverage flag — True if earnings data was fetched for this ticker
    earnings_coverage: bool = False

    # Optional manual override — bypasses all multipliers
    override_weight: Optional[float] = None


@dataclass
class SizingResult:
    """Output of a sizing calculation."""
    symbol: str
    weight: float                 # fraction of portfolio (0.0–max_position_pct)
    shares: int                   # integer share count (floor)
    dollar_amount: float          # weight × portfolio_value
    method: str                   # "vol_target" | "kelly" | "zero"
    sizing_notes: List[str] = field(default_factory=list)
    risk_contribution: float = 0.0  # expected annualised vol contribution
    sector: str = "Unknown"


# ---------------------------------------------------------------------------
# Signal → multiplier mapping
# ---------------------------------------------------------------------------

_SIGNAL_BASE: Dict[str, float] = {
    "Bullish": 1.0,
    "Neutral": 0.0,   # no position on neutral — long-only
    "Bearish": 0.0,   # no short positions for retail
}

_CONFIDENCE_SCALE: Dict[str, float] = {
    "High":   1.25,
    "Medium": 1.00,
    "Low":    0.60,
}

# Coverage multiplier: penalise missing earnings data
# Earnings data provides ~30% of expected alpha in fundamental regimes.
# When missing, confidence degrades: High→Medium equivalent, Medium→Low equivalent.
_COVERAGE_SCALE: Dict[bool, float] = {
    True:  1.00,   # earnings data present → no penalty
    False: 0.75,   # earnings data missing → 25% reduction
}

def _fss_multiplier(fss_score: float) -> float:
    """Map FSS [40, 80] linearly to [0.85, 1.15]. Flat outside that band."""
    clipped = max(40.0, min(80.0, fss_score))
    return 0.85 + (clipped - 40.0) / 40.0 * 0.30


# ---------------------------------------------------------------------------
# Vol-Target Sizer (primary)
# ---------------------------------------------------------------------------

class VolTargetSizer:
    """
    Size each position so its standalone volatility contribution equals
    `target_vol_pct` of the portfolio, then adjust by a composite
    signal multiplier that incorporates:

      1. Signal direction (Bullish=1, Neutral/Bearish=0)
      2. Confidence level (High/Medium/Low)
      3. FSS score (component confluence)
      4. ML model score (when available)
      5. Stability multiplier (penalises single-fold IC dominance)
      6. Regime gate (reduces exposure in value-rotation / crisis regimes)
      7. Coverage multiplier (reduces size when earnings data is missing)

    Parameters
    ----------
    target_vol_pct : float
        Target annualised vol contribution per position (default 2%).
    max_position_pct : float
        Hard cap on any single position (default 8%).
    min_position_pct : float
        Minimum position size once signal clears threshold (default 1%).
    model_stats : ModelStats, optional
        Walk-forward CV statistics used for stability multiplier.
        Defaults to ModelStats() which uses mean_ic=0.014, std_ic=0.037.
    regime : str, optional
        Current market regime for the regime gate.  Can be overridden
        per-stock via SizingInput.regime (stock-level takes priority).
    """

    def __init__(
        self,
        target_vol_pct: float = 0.02,
        max_position_pct: float = 0.08,
        min_position_pct: float = 0.01,
        model_stats: Optional[ModelStats] = None,
        regime: str = "Unknown",
    ):
        if not 0 < target_vol_pct < 1:
            raise ValueError("target_vol_pct must be between 0 and 1")
        if not 0 < max_position_pct <= 1:
            raise ValueError("max_position_pct must be between 0 and 1")

        self.target_vol_pct = target_vol_pct
        self.max_position_pct = max_position_pct
        self.min_position_pct = min_position_pct
        self.model_stats = model_stats or ModelStats()
        self.regime = regime

    def size(self, inp: SizingInput) -> SizingResult:
        """Compute position size for one stock."""
        notes: List[str] = []

        # --- Override path --------------------------------------------------
        if inp.override_weight is not None:
            w = max(0.0, min(self.max_position_pct, float(inp.override_weight)))
            notes.append(f"Manual override: weight={w:.1%}")
            return self._finalise(inp, w, "vol_target", notes)

        # --- Zero out non-bullish signals ------------------------------------
        base = _SIGNAL_BASE.get(inp.signal, 0.0)
        if base == 0.0:
            notes.append(f"Signal={inp.signal} → no position (long-only)")
            return self._zero(inp, notes)

        # --- Base vol-target weight ------------------------------------------
        stock_vol = max(inp.annual_vol, 0.05)   # floor at 5% — avoids absurd weights
        raw_weight = self.target_vol_pct / stock_vol
        notes.append(
            f"Vol-target base: {self.target_vol_pct:.0%} target ÷ "
            f"{stock_vol:.0%} stock vol = {raw_weight:.1%} raw weight"
        )

        # --- Individual multipliers ------------------------------------------
        conf_scale     = _CONFIDENCE_SCALE.get(inp.confidence, 1.0)
        fss_scale      = _fss_multiplier(inp.fss_score)
        ml_scale       = self._ml_scale(inp)
        regime_str     = inp.regime if inp.regime != "Unknown" else self.regime
        regime_scale   = _regime_gate_multiplier(regime_str)
        # Use regime-aware stability to avoid double-penalising with regime_scale.
        # stability_for_regime() measures "is the model stable *within* this regime?"
        # while regime_scale measures "is this regime favourable for the strategy?"
        # These are orthogonal questions; using global std_ic for both would penalise
        # the same "model degrades in bear regimes" fact twice.
        stability      = self.model_stats.stability_for_regime(regime_str)
        coverage_scale = _COVERAGE_SCALE.get(inp.earnings_coverage, 0.75)

        total_scale = (
            base
            * conf_scale
            * fss_scale
            * ml_scale
            * stability
            * regime_scale
            * coverage_scale
        )

        notes.append(
            f"Multipliers: dir={base:.2f} × conf({inp.confidence})={conf_scale:.2f} "
            f"× FSS({inp.fss_score:.0f})={fss_scale:.2f} × ML={ml_scale:.2f} "
            f"× stability[{regime_str}]={stability:.2f} × regime={regime_scale:.2f} "
            f"× coverage={'✓' if inp.earnings_coverage else '✗'}={coverage_scale:.2f} "
            f"→ total={total_scale:.3f}×"
        )

        # Dominance warning
        if self.model_stats.single_fold_dominance():
            notes.append(
                "⚠ Single-fold dominance detected — stability multiplier "
                f"already applied ({stability:.2f}×). Consider widening the universe."
            )

        # Coverage note — clarify this is orthogonal to FSS confidence.
        # FSS confidence measures component confluence (T/F/C/R alignment).
        # Coverage measures data completeness. They are independent signals.
        if not inp.earnings_coverage:
            notes.append(
                "⚠ Earnings data unavailable — position size reduced by 25% (coverage=0.75×). "
                "FSS confidence reflects price/volume signal strength independently. "
                "Add ticker to earnings cache to restore full sizing."
            )

        adjusted_weight = raw_weight * total_scale

        # --- Hard caps -------------------------------------------------------
        if adjusted_weight > self.max_position_pct:
            notes.append(
                f"Capped at max {self.max_position_pct:.0%} "
                f"(uncapped was {adjusted_weight:.1%})"
            )
            adjusted_weight = self.max_position_pct

        if adjusted_weight < self.min_position_pct:
            notes.append(
                f"Below minimum {self.min_position_pct:.0%} → zero "
                f"(signal too weak after all multipliers)"
            )
            return self._zero(inp, notes)

        return self._finalise(inp, adjusted_weight, "vol_target", notes)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _ml_scale(self, inp: SizingInput) -> float:
        """Scale factor from ML model signal. Range: 0.85–1.25 (1.0 if no model)."""
        if inp.ml_score is not None:
            ml = float(inp.ml_score)
            if ml >= 8.0:  return 1.25
            if ml >= 7.0:  return 1.10
            if ml >= 6.0:  return 1.00
            return 0.85    # 5–6: weak bullish → slight reduction
        return 1.0

    def _finalise(
        self,
        inp: SizingInput,
        weight: float,
        method: str,
        notes: List[str],
    ) -> SizingResult:
        dollar_amount = weight * inp.portfolio_value
        shares = int(math.floor(dollar_amount / inp.current_price)) if inp.current_price > 0 else 0
        risk_contribution = weight * max(inp.annual_vol, 0.0)

        if shares == 0 and weight > 0:
            notes.append(
                f"⚠ 0 shares: ${dollar_amount:,.0f} allocation < "
                f"${inp.current_price:.2f} share price"
            )

        return SizingResult(
            symbol=inp.symbol,
            weight=round(weight, 4),
            shares=shares,
            dollar_amount=round(dollar_amount, 2),
            method=method,
            sizing_notes=notes,
            risk_contribution=round(risk_contribution, 4),
            sector=inp.sector,
        )

    def _zero(self, inp: SizingInput, notes: List[str]) -> SizingResult:
        return SizingResult(
            symbol=inp.symbol,
            weight=0.0,
            shares=0,
            dollar_amount=0.0,
            method="zero",
            sizing_notes=notes,
            risk_contribution=0.0,
            sector=inp.sector,
        )


# ---------------------------------------------------------------------------
# Kelly Sizer (secondary — power-user / institutional mode)
# ---------------------------------------------------------------------------

class KellySizer:
    """
    Quarter-Kelly position sizer.

    Uses the Spearman IC from the walk-forward CV as the edge estimate.
    Applies the same stability multiplier and regime gate as VolTargetSizer.

    Parameters
    ----------
    model_stats : ModelStats
        Walk-forward CV statistics (IC mean, std, per-fold ICs).
    avg_win_loss_ratio : float
        avg_winner / avg_loser magnitude (default 1.5).
    kelly_fraction : float
        Fractional Kelly multiplier (default 0.25 = quarter Kelly).
    max_position_pct : float
        Hard cap (default 5%).
    regime : str
        Current market regime for the regime gate.
    """

    def __init__(
        self,
        model_stats: Optional[ModelStats] = None,
        avg_win_loss_ratio: float = 1.5,
        kelly_fraction: float = 0.25,
        max_position_pct: float = 0.05,
        regime: str = "Unknown",
    ):
        self.model_stats = model_stats or ModelStats()
        self.b = max(1.01, float(avg_win_loss_ratio))
        self.kelly_fraction = float(kelly_fraction)
        self.max_position_pct = float(max_position_pct)
        self.regime = regime

    def size(self, inp: SizingInput) -> SizingResult:
        notes: List[str] = []

        base = _SIGNAL_BASE.get(inp.signal, 0.0)
        if base == 0.0:
            notes.append(f"Signal={inp.signal} → no position")
            return SizingResult(
                symbol=inp.symbol, weight=0.0, shares=0,
                dollar_amount=0.0, method="zero", sizing_notes=notes,
                sector=inp.sector,
            )

        ic = max(0.0, self.model_stats.mean_ic)
        p = 0.5 + ic / 2.0
        q = 1.0 - p
        b = self.b

        full_kelly = (p * b - q) / b
        fractional_kelly = self.kelly_fraction * full_kelly
        notes.append(
            f"Kelly: IC={ic:.3f} → p={p:.3f}, b={b:.2f} "
            f"→ full Kelly={full_kelly:.3f} × {self.kelly_fraction}× "
            f"= {fractional_kelly:.3f}"
        )

        # Apply regime-aware stability, regime gate, coverage, confidence.
        # stability_for_regime() is used (not global stability_multiplier()) to
        # avoid double-penalising with regime_scale — same fix as VolTargetSizer.
        regime_str     = inp.regime if inp.regime != "Unknown" else self.regime
        regime_scale   = _regime_gate_multiplier(regime_str)
        stability      = self.model_stats.stability_for_regime(regime_str)
        coverage_scale = _COVERAGE_SCALE.get(inp.earnings_coverage, 0.75)
        conf_scale     = _CONFIDENCE_SCALE.get(inp.confidence, 1.0)

        weight = fractional_kelly * conf_scale * stability * regime_scale * coverage_scale
        weight = max(0.0, min(self.max_position_pct, weight))

        notes.append(
            f"Scaled: conf({inp.confidence})={conf_scale:.2f} × "
            f"stability[{regime_str}]={stability:.2f} × regime={regime_scale:.2f} × "
            f"coverage={coverage_scale:.2f} → {weight:.1%}"
        )

        dollar_amount = weight * inp.portfolio_value
        shares = int(math.floor(dollar_amount / inp.current_price)) if inp.current_price > 0 else 0
        risk_contribution = weight * max(inp.annual_vol, 0.0)

        return SizingResult(
            symbol=inp.symbol,
            weight=round(weight, 4),
            shares=shares,
            dollar_amount=round(dollar_amount, 2),
            method="kelly",
            sizing_notes=notes,
            risk_contribution=round(risk_contribution, 4),
            sector=inp.sector,
        )


# ---------------------------------------------------------------------------
# Portfolio-level helper: size a ranked list of signals
# ---------------------------------------------------------------------------

@dataclass
class PortfolioSizingResult:
    """Aggregated result for a full portfolio."""
    positions: List[SizingResult]
    total_invested_pct: float          # sum of all weights
    total_risk_contribution: float     # sum of vol contributions (pre-correlation)
    cash_pct: float                    # 1 - total_invested_pct
    sector_weights: Dict[str, float]   # sector → total weight
    concentration_warnings: List[str]


def size_portfolio(
    signals: List[SizingInput],
    sizer: Optional[VolTargetSizer] = None,
    max_portfolio_invested_pct: float = 0.95,
    max_single_sector_pct: float = 0.25,
    max_corr_bucket_pct: float = 0.30,
    corr_buckets: Optional[Dict[str, str]] = None,
) -> PortfolioSizingResult:
    """
    Apply a sizer to a ranked list of SizingInputs and enforce portfolio-level
    constraints:

      1. Gross exposure cap  (default 95% — 5% cash buffer)
      2. Sector concentration cap  (default 25% per sector)
      3. Correlation bucket cap  (default 30% per corr-bucket)

    Parameters
    ----------
    signals : list[SizingInput]
        Stocks to size, sorted by signal strength descending.
    sizer : VolTargetSizer, optional
        Defaults to VolTargetSizer() with default parameters.
    max_portfolio_invested_pct : float
        Hard stop on total gross exposure.
    max_single_sector_pct : float
        Max weight in any single GICS sector (default 25%).
    max_corr_bucket_pct : float
        Max weight in any correlation bucket (default 30%).
        Correlation buckets group stocks that historically move together
        (e.g. AI/mega-cap, energy, banks).
    corr_buckets : dict[symbol, bucket_name], optional
        Mapping of ticker → bucket label.  If None, falls back to sector.
        Example: {"NVDA": "AI_mega", "MSFT": "AI_mega", "GOOGL": "AI_mega",
                  "JPM": "Banks", "GS": "Banks"}

    Returns
    -------
    PortfolioSizingResult
    """
    if sizer is None:
        sizer = VolTargetSizer()

    positions: List[SizingResult] = []
    total_weight = 0.0
    sector_weights: Dict[str, float] = {}
    bucket_weights: Dict[str, float] = {}
    warnings: List[str] = []

    for inp in signals:
        result = sizer.size(inp)

        if result.weight == 0.0:
            positions.append(result)
            continue

        # --- 1. Gross exposure cap ------------------------------------------
        remaining = max_portfolio_invested_pct - total_weight
        if result.weight > remaining:
            trimmed = max(0.0, remaining)
            if trimmed < sizer.min_position_pct:
                result.sizing_notes.append(
                    f"Trimmed to zero: only {remaining:.1%} capacity left "
                    f"(portfolio at {total_weight:.1%} invested)"
                )
                positions.append(_zero_result(inp, result.sizing_notes))
                continue
            result = _trim_result(inp, result, trimmed, "portfolio capacity")

        # --- 2. Sector concentration cap ------------------------------------
        sector = inp.sector or "Unknown"
        sector_used = sector_weights.get(sector, 0.0)
        sector_remaining = max_single_sector_pct - sector_used
        if result.weight > sector_remaining:
            trimmed = max(0.0, sector_remaining)
            if trimmed < sizer.min_position_pct:
                msg = (
                    f"Sector cap: {sector} already at {sector_used:.1%} "
                    f"(max {max_single_sector_pct:.0%}) → zeroed"
                )
                result.sizing_notes.append(msg)
                warnings.append(f"{inp.symbol}: {msg}")
                positions.append(_zero_result(inp, result.sizing_notes))
                continue
            msg = f"Sector cap ({sector} at {sector_used:.1%}+{result.weight:.1%} > {max_single_sector_pct:.0%})"
            result = _trim_result(inp, result, trimmed, msg)
            warnings.append(f"{inp.symbol}: trimmed by sector cap ({sector})")

        # --- 3. Correlation bucket cap --------------------------------------
        bucket = (corr_buckets or {}).get(inp.symbol, sector)
        bucket_used = bucket_weights.get(bucket, 0.0)
        bucket_remaining = max_corr_bucket_pct - bucket_used
        if result.weight > bucket_remaining:
            trimmed = max(0.0, bucket_remaining)
            if trimmed < sizer.min_position_pct:
                msg = (
                    f"Corr-bucket cap: '{bucket}' already at {bucket_used:.1%} "
                    f"(max {max_corr_bucket_pct:.0%}) → zeroed"
                )
                result.sizing_notes.append(msg)
                warnings.append(f"{inp.symbol}: {msg}")
                positions.append(_zero_result(inp, result.sizing_notes))
                continue
            msg = f"Corr-bucket cap ('{bucket}' at {bucket_used:.1%})"
            result = _trim_result(inp, result, trimmed, msg)
            warnings.append(f"{inp.symbol}: trimmed by corr-bucket cap ('{bucket}')")

        # --- Accumulate weights ----------------------------------------------
        positions.append(result)
        total_weight  += result.weight
        sector_weights[sector] = sector_weights.get(sector, 0.0) + result.weight
        bucket_weights[bucket] = bucket_weights.get(bucket, 0.0) + result.weight

    total_risk = sum(p.risk_contribution for p in positions)
    cash_pct   = max(0.0, 1.0 - total_weight)

    # Sector summary warning
    for sec, wt in sector_weights.items():
        if wt > max_single_sector_pct * 0.90:
            warnings.append(
                f"Sector '{sec}' at {wt:.1%} — approaching {max_single_sector_pct:.0%} cap"
            )

    return PortfolioSizingResult(
        positions=positions,
        total_invested_pct=round(total_weight, 4),
        total_risk_contribution=round(total_risk, 4),
        cash_pct=round(cash_pct, 4),
        sector_weights={k: round(v, 4) for k, v in sector_weights.items()},
        concentration_warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _trim_result(
    inp: SizingInput,
    result: SizingResult,
    trimmed: float,
    reason: str,
) -> SizingResult:
    """Return a new SizingResult with weight trimmed to `trimmed`."""
    result.sizing_notes.append(
        f"Trimmed from {result.weight:.1%} to {trimmed:.1%} ({reason})"
    )
    dollar_amount = trimmed * inp.portfolio_value
    shares = int(math.floor(dollar_amount / inp.current_price)) if inp.current_price > 0 else 0
    return SizingResult(
        symbol=inp.symbol,
        weight=round(trimmed, 4),
        shares=shares,
        dollar_amount=round(dollar_amount, 2),
        method=result.method,
        sizing_notes=result.sizing_notes,
        risk_contribution=round(trimmed * max(inp.annual_vol, 0.0), 4),
        sector=inp.sector,
    )


def _zero_result(inp: SizingInput, notes: List[str]) -> SizingResult:
    return SizingResult(
        symbol=inp.symbol, weight=0.0, shares=0,
        dollar_amount=0.0, method="zero",
        sizing_notes=notes, risk_contribution=0.0,
        sector=inp.sector,
    )
