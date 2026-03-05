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

   Then scaled by a signal multiplier (0.0–1.5) derived from FSS score
   and ML confidence, and hard-capped by concentration limits.

2. **KellySizer** (secondary / power-user)
   Half-Kelly fraction based on estimated edge (IC) and odds.
   Conservative (0.25× Kelly) to avoid the overbetting pathology.

       f* = 0.25 × (p × b − q) / b
       where p = P(win), b = avg_win/avg_loss, q = 1 − p

Both sizersreturn a `SizingResult` with:
  - `weight`          : fraction of portfolio to allocate (0.0–1.0)
  - `shares`          : integer share count given portfolio_value + current_price
  - `method`          : "vol_target" | "kelly" | "zero"
  - `sizing_notes`    : list of plain-English notes explaining the sizing decision
  - `risk_contribution`: expected annualised vol contribution of this position

Usage
-----
    from .position_sizer import VolTargetSizer, SizingInput

    sizer = VolTargetSizer(target_vol_pct=0.02, max_position_pct=0.08)
    result = sizer.size(SizingInput(
        symbol="AAPL",
        signal="Bullish",
        confidence="High",
        fss_score=72.5,
        ml_score=7.4,
        annual_vol=0.28,          # realized annualised vol of the stock
        portfolio_value=100_000,
        current_price=185.50,
    ))
    # result.weight = 0.071, result.shares = 38
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

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
    ml_score: Optional[float] = None        # 0–10 (None if model not trained)
    predicted_return: Optional[float] = None  # vol-adjusted prediction (None if unavailable)

    # Optional override — if provided, bypasses signal-multiplier calculation
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


# ---------------------------------------------------------------------------
# Signal → multiplier mapping
# ---------------------------------------------------------------------------

# Base multipliers by signal direction
_SIGNAL_BASE: dict[str, float] = {
    "Bullish": 1.0,
    "Neutral": 0.0,   # no position on neutral signal
    "Bearish": 0.0,   # no short positions for retail (long-only)
}

# Confidence scaling applied on top of base
_CONFIDENCE_SCALE: dict[str, float] = {
    "High":   1.25,
    "Medium": 1.00,
    "Low":    0.60,
}

# FSS score bonus/penalty: score mapped linearly from [40,80] → [0.85, 1.15]
def _fss_multiplier(fss_score: float) -> float:
    """Scale between 0.85 (FSS=40) and 1.15 (FSS=80). Flat outside that band."""
    clipped = max(40.0, min(80.0, fss_score))
    return 0.85 + (clipped - 40.0) / 40.0 * 0.30   # 0.85 → 1.15


# ---------------------------------------------------------------------------
# Vol-Target Sizer (primary)
# ---------------------------------------------------------------------------

class VolTargetSizer:
    """
    Size each position so its standalone volatility contribution equals
    `target_vol_pct` of the portfolio, then adjust by signal strength.

    Parameters
    ----------
    target_vol_pct : float
        Target annualised vol contribution per position (default 2% = 0.02).
        A 50-stock equal-vol portfolio at 2% per stock → ~14% portfolio vol
        (assuming ~0.3 avg correlation), which is roughly market-like.
    max_position_pct : float
        Hard cap on any single position (default 8%).
    min_position_pct : float
        Minimum position size once signal clears threshold (default 1%).
        Prevents death-by-a-thousand-tiny-positions.
    """

    def __init__(
        self,
        target_vol_pct: float = 0.02,
        max_position_pct: float = 0.08,
        min_position_pct: float = 0.01,
    ):
        if not 0 < target_vol_pct < 1:
            raise ValueError("target_vol_pct must be between 0 and 1")
        if not 0 < max_position_pct <= 1:
            raise ValueError("max_position_pct must be between 0 and 1")

        self.target_vol_pct = target_vol_pct
        self.max_position_pct = max_position_pct
        self.min_position_pct = min_position_pct

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
        stock_vol = max(inp.annual_vol, 0.05)  # floor at 5% to avoid absurd sizes
        raw_weight = self.target_vol_pct / stock_vol
        notes.append(
            f"Vol-target base: {self.target_vol_pct:.0%} target ÷ "
            f"{stock_vol:.0%} stock vol = {raw_weight:.1%} raw weight"
        )

        # --- Signal multiplier (confidence × FSS score) ---------------------
        conf_scale  = _CONFIDENCE_SCALE.get(inp.confidence, 1.0)
        fss_scale   = _fss_multiplier(inp.fss_score)
        ml_scale    = self._ml_scale(inp)
        total_scale = base * conf_scale * fss_scale * ml_scale

        notes.append(
            f"Signal multiplier: {base:.2f} (dir) × {conf_scale:.2f} (conf={inp.confidence}) "
            f"× {fss_scale:.2f} (FSS={inp.fss_score:.0f}) × {ml_scale:.2f} (ML) "
            f"= {total_scale:.2f}×"
        )

        adjusted_weight = raw_weight * total_scale

        # --- Hard caps ------------------------------------------------------
        if adjusted_weight > self.max_position_pct:
            notes.append(
                f"Capped at max {self.max_position_pct:.0%} "
                f"(uncapped was {adjusted_weight:.1%})"
            )
            adjusted_weight = self.max_position_pct

        if adjusted_weight < self.min_position_pct:
            notes.append(
                f"Below minimum {self.min_position_pct:.0%} → zero "
                f"(signal too weak after scaling)"
            )
            return self._zero(inp, notes)

        return self._finalise(inp, adjusted_weight, "vol_target", notes)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _ml_scale(self, inp: SizingInput) -> float:
        """
        Scale factor from ML model signal. Range: 0.75–1.25.
        If no ML score available, returns 1.0 (neutral).
        """
        if inp.ml_score is not None:
            # ml_score is 0–10; 5 = neutral, >7 = bullish, >8 = strong
            ml = float(inp.ml_score)
            if ml >= 8.0:
                return 1.25
            if ml >= 7.0:
                return 1.10
            if ml >= 6.0:
                return 1.00
            return 0.85   # 5–6: weak bullish → slight reduction
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
        )


# ---------------------------------------------------------------------------
# Kelly Sizer (secondary — power-user / institutional mode)
# ---------------------------------------------------------------------------

class KellySizer:
    """
    Quarter-Kelly position sizer.

    Uses the Spearman IC from the walk-forward CV as the edge estimate.
    IC = rank correlation between predictions and realised returns; this
    maps to a win probability via: p ≈ 0.5 + IC/2 (rank-based approximation).

    Quarter-Kelly (0.25×) is used because:
      - Full Kelly maximises geometric growth but produces extreme drawdowns.
      - Half-Kelly halves the drawdown for ~75% of the geometric growth.
      - Quarter-Kelly is the institutional standard when IC estimates are noisy.

    Parameters
    ----------
    ic : float
        Mean OOS Spearman IC from walk-forward CV (e.g. 0.014).
    avg_win_loss_ratio : float
        Ratio of average winner to average loser (default 1.5).
        Can be estimated from decile_spread / abs(bottom_decile_return).
    kelly_fraction : float
        Fractional Kelly multiplier (default 0.25 = quarter Kelly).
    max_position_pct : float
        Hard cap (default 5%).
    """

    def __init__(
        self,
        ic: float = 0.014,
        avg_win_loss_ratio: float = 1.5,
        kelly_fraction: float = 0.25,
        max_position_pct: float = 0.05,
    ):
        self.ic = max(0.0, float(ic))
        self.b = max(1.01, float(avg_win_loss_ratio))
        self.kelly_fraction = float(kelly_fraction)
        self.max_position_pct = float(max_position_pct)

    def size(self, inp: SizingInput) -> SizingResult:
        notes: List[str] = []

        base = _SIGNAL_BASE.get(inp.signal, 0.0)
        if base == 0.0:
            notes.append(f"Signal={inp.signal} → no position")
            return SizingResult(
                symbol=inp.symbol, weight=0.0, shares=0,
                dollar_amount=0.0, method="zero", sizing_notes=notes,
            )

        # Win probability from IC: p ≈ 0.5 + IC/2
        p = 0.5 + self.ic / 2.0
        q = 1.0 - p
        b = self.b

        # Full Kelly: f* = (p*b - q) / b
        full_kelly = (p * b - q) / b
        fractional_kelly = self.kelly_fraction * full_kelly
        notes.append(
            f"Kelly: IC={self.ic:.3f} → p={p:.3f}, b={b:.2f} "
            f"→ full Kelly={full_kelly:.3f} × {self.kelly_fraction}× "
            f"= {fractional_kelly:.3f}"
        )

        # Scale by confidence
        conf_scale = _CONFIDENCE_SCALE.get(inp.confidence, 1.0)
        weight = fractional_kelly * conf_scale
        weight = max(0.0, min(self.max_position_pct, weight))

        if weight > 0:
            notes.append(f"After confidence ({inp.confidence} {conf_scale:.2f}×): {weight:.1%}")

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
        )


# ---------------------------------------------------------------------------
# Portfolio-level helper: size a ranked list of signals
# ---------------------------------------------------------------------------

@dataclass
class PortfolioSizingResult:
    """Aggregated result for a full portfolio."""
    positions: List[SizingResult]
    total_invested_pct: float     # sum of all weights
    total_risk_contribution: float  # sum of vol contributions (pre-correlation)
    cash_pct: float               # 1 - total_invested_pct
    concentration_warnings: List[str]


def size_portfolio(
    signals: List[SizingInput],
    sizer: Optional[VolTargetSizer] = None,
    max_portfolio_invested_pct: float = 0.95,
    max_single_sector_pct: float = 0.30,
) -> PortfolioSizingResult:
    """
    Apply a sizer to a ranked list of SizingInputs and enforce portfolio-level
    constraints.

    Parameters
    ----------
    signals : list[SizingInput]
        Stocks to size, ideally sorted by signal strength descending.
    sizer : VolTargetSizer, optional
        If None, creates a default VolTargetSizer(target_vol_pct=0.02).
    max_portfolio_invested_pct : float
        Hard stop on total gross exposure (default 95% — keep 5% cash buffer).
    max_single_sector_pct : float
        Not enforced here (requires sector data); placeholder for future use.

    Returns
    -------
    PortfolioSizingResult
    """
    if sizer is None:
        sizer = VolTargetSizer()

    positions: List[SizingResult] = []
    total_weight = 0.0
    warnings: List[str] = []

    for inp in signals:
        result = sizer.size(inp)

        # Check remaining capacity
        remaining = max_portfolio_invested_pct - total_weight
        if result.weight > remaining:
            trimmed = max(0.0, remaining)
            if trimmed < sizer.min_position_pct:
                result.sizing_notes.append(
                    f"Trimmed to zero: only {remaining:.1%} capacity left "
                    f"(portfolio at {total_weight:.1%} invested)"
                )
                result = SizingResult(
                    symbol=inp.symbol, weight=0.0, shares=0,
                    dollar_amount=0.0, method="zero",
                    sizing_notes=result.sizing_notes,
                )
            else:
                result.sizing_notes.append(
                    f"Trimmed from {result.weight:.1%} to {trimmed:.1%} "
                    f"(portfolio capacity constraint)"
                )
                # Recompute shares with trimmed weight
                dollar_amount = trimmed * inp.portfolio_value
                shares = int(math.floor(dollar_amount / inp.current_price)) if inp.current_price > 0 else 0
                result = SizingResult(
                    symbol=inp.symbol,
                    weight=round(trimmed, 4),
                    shares=shares,
                    dollar_amount=round(dollar_amount, 2),
                    method=result.method,
                    sizing_notes=result.sizing_notes,
                    risk_contribution=round(trimmed * max(inp.annual_vol, 0.0), 4),
                )

        positions.append(result)
        total_weight += result.weight

    total_risk = sum(p.risk_contribution for p in positions)
    cash_pct = max(0.0, 1.0 - total_weight)

    if total_weight > max_portfolio_invested_pct:
        warnings.append(
            f"Total invested {total_weight:.1%} exceeds limit {max_portfolio_invested_pct:.1%}"
        )

    return PortfolioSizingResult(
        positions=positions,
        total_invested_pct=round(total_weight, 4),
        total_risk_contribution=round(total_risk, 4),
        cash_pct=round(cash_pct, 4),
        concentration_warnings=warnings,
    )
