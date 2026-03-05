"""
glass_box.py
============
Glass Box reasoning layer: synthesises sizing + signal into a short narrative
("position thesis") so users see exactly why a position is sized the way it is.

Usage
-----
    from .glass_box import format_position_thesis, attach_position_theses
    from .position_sizer import SizingResult, PortfolioSizingResult
    from .signal_formatter import SignalOutput

    # Single position
    thesis = format_position_thesis(sizing_result, signal_output, regime_ic=meta.get("regime_ic"))

    # After size_portfolio when you have signal_output per symbol
    symbol_to_signal = {s["symbol"]: s["signal_output"] for s in scored_stocks if s.get("signal_output")}
    attach_position_theses(portfolio_result, symbol_to_signal, regime_ic=regime_ic)
    # portfolio_result.positions[].position_thesis is now set
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def format_position_thesis(
    result: Any,
    signal_output: Optional[Dict[str, Any]] = None,
    regime_ic: Optional[Dict[str, float]] = None,
) -> str:
    """
    Produce a short narrative explaining why this position is sized the way it is.

    Uses sizing_notes, sector, regime, signal reasons, and (when provided)
    regime_ic to say e.g. "Expansion regime scores your model's highest IC (+0.051)".

    Parameters
    ----------
    result : SizingResult
        Output of VolTargetSizer.size() or a single entry from size_portfolio().
    signal_output : dict or SignalOutput, optional
        Structured signal (reasons, regime, fss_score). If None, narrative
        omits signal-component detail.
    regime_ic : dict[str, float], optional
        Mean IC per regime from model bundle. When provided, narrative can
        cite e.g. "Expansion regime scores your model's highest IC (+0.051)".

    Returns
    -------
    str
        Two to four sentences for UI (e.g. "We are holding 4.2% NVDA. ...").
    """
    symbol = getattr(result, "symbol", "?")
    weight = getattr(result, "weight", 0.0)
    sector = getattr(result, "sector", "Unknown")
    notes = getattr(result, "sizing_notes", []) or []
    coverage_penalty = getattr(result, "coverage_penalty_applied", False)

    # Opening: position size
    if weight <= 0:
        return _thesis_zero_position(result, signal_output)
    pct = weight * 100
    parts = [f"We are holding {pct:.1f}% {symbol}."]

    # Sector cap if relevant (from notes or sector)
    notes_lower = " ".join(notes).lower()
    if sector and sector != "Unknown":
        if "sector cap" in notes_lower or "trimmed" in notes_lower:
            parts.append(f"Sizing is constrained by the 25% sector cap ({sector}).")
        else:
            parts.append(f"Sector: {sector}.")

    # Regime + regime_ic
    regime = "Unknown"
    if signal_output:
        regime = (signal_output.get("regime") or "Unknown").strip()
    if regime_ic and regime in regime_ic:
        ic_val = regime_ic[regime]
        if ic_val > 0:
            parts.append(
                f"The {regime} regime scores your model's highest IC ({ic_val:+.3f}), "
                "so sizing is at full strength in this regime."
            )
        else:
            parts.append(
                f"In {regime} the model has no demonstrated edge (IC {ic_val:+.3f}), "
                "so position size is reduced."
            )
    else:
        parts.append(f"The current regime is {regime}.")

    # Signal components (trend, fundamentals, capital flow, risk)
    if signal_output:
        reasons = signal_output.get("reasons") or []
        fss_score = signal_output.get("fss_score")
        if fss_score is not None:
            if reasons and len(reasons) >= 3:
                parts.append(
                    f"FSS composite score is {fss_score:.0f}; all four signal components "
                    "(trend, fundamentals, capital flow, risk) are above threshold."
                )
            elif reasons:
                parts.append(f"FSS composite score is {fss_score:.0f}; " + " ".join(reasons[:2]) + ".")
            else:
                parts.append(f"FSS composite score is {fss_score:.0f}; signal supports this size.")
        elif reasons:
            parts.append(" ".join(reasons[:2]) + ".")

    # Earnings coverage
    if coverage_penalty:
        parts.append("Earnings data is missing for this ticker, so sizing is slightly reduced.")

    return " ".join(parts)


def _thesis_zero_position(result: Any, signal_output: Optional[Dict[str, Any]]) -> str:
    """Narrative when weight is zero."""
    symbol = getattr(result, "symbol", "?")
    notes = getattr(result, "sizing_notes", []) or []
    notes_lower = " ".join(notes).lower()
    if "no position" in notes_lower or "long-only" in notes_lower:
        return (
            f"No position in {symbol}. The signal is not bullish (long-only; "
            "we do not size on neutral or bearish)."
        )
    if "below minimum" in notes_lower:
        return (
            f"No position in {symbol}. Signal strength is below threshold after "
            "applying direction, confidence, regime, and coverage multipliers."
        )
    if "sector cap" in notes_lower or "zeroed" in notes_lower:
        return (
            f"No position in {symbol}. Portfolio or sector concentration cap "
            "would be exceeded; this name was trimmed to zero."
        )
    return f"No position in {symbol}. Sizing rules produced zero weight."


def attach_position_theses(
    portfolio_result: Any,
    symbol_to_signal_output: Dict[str, Any],
    regime_ic: Optional[Dict[str, float]] = None,
) -> None:
    """
    Set position_thesis on each position in portfolio_result using the
    corresponding signal_output per symbol. Mutates portfolio_result.positions
    in place (each SizingResult must have position_thesis field).

    Parameters
    ----------
    portfolio_result : PortfolioSizingResult
        Return value of size_portfolio().
    symbol_to_signal_output : dict[str, SignalOutput]
        Map symbol -> signal_output (e.g. from scored_stocks with signal_output).
    regime_ic : dict[str, float], optional
        From ModelRegistry.metadata().get("regime_ic").
    """
    for pos in getattr(portfolio_result, "positions", []):
        sym = getattr(pos, "symbol", "")
        sig = symbol_to_signal_output.get(sym) if symbol_to_signal_output else None
        thesis = format_position_thesis(pos, sig, regime_ic=regime_ic)
        if hasattr(pos, "position_thesis"):
            pos.position_thesis = thesis
        else:
            try:
                object.__setattr__(pos, "position_thesis", thesis)
            except Exception:
                logger.debug("Could not set position_thesis on %s", sym)
