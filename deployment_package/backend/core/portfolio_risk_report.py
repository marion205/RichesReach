"""
portfolio_risk_report.py
========================
Output layer for regime-aware portfolio risk: converts regime gate multipliers
into human-readable risk report (sizing down %, projected drawdown context).

Use after regime is known (e.g. from FSS engine or market regime model).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .position_sizer import _regime_gate_multiplier


@dataclass
class PortfolioRiskReport:
    """
    Regime-based risk summary for UI or API.

    Attributes
    ----------
    regime : str
        Current market regime label.
    gate_multiplier : float
        Sizing multiplier from position_sizer (0.25–1.0).
    sizing_down_pct : float
        Percentage the portfolio is sized down vs full (e.g. 75 → "sizes down ~75%").
    narrative : str
        One- or two-sentence plain-English summary.
    """
    regime: str
    gate_multiplier: float
    sizing_down_pct: float
    narrative: str


# Approximate stress drawdown context by regime (for narrative only; not a forecast)
_REGIME_DRAWDOWN_CONTEXT = {
    "Crisis": "-25% to -40%",
    "Deflation": "-15% to -25%",
    "Parabolic": "-10% to -20%",
    "Expansion": "-5% to -15%",
    "Unknown": "-10% to -20%",
}


def build_portfolio_risk_report(regime: str) -> PortfolioRiskReport:
    """
    Build a PortfolioRiskReport from the current regime.

    Parameters
    ----------
    regime : str
        Current market regime (e.g. from FSS or regime detector).

    Returns
    -------
    PortfolioRiskReport
    """
    gate = _regime_gate_multiplier(regime)
    sizing_down_pct = round((1.0 - gate) * 100) if gate < 1.0 else 0.0
    drawdown_band = _REGIME_DRAWDOWN_CONTEXT.get(
        regime,
        _REGIME_DRAWDOWN_CONTEXT.get("Unknown", "-10% to -20%"),
    )
    if gate >= 0.95:
        narrative = (
            f"In {regime} regime the system allows full sizing. "
            f"Typical stress drawdowns in this regime: {drawdown_band}."
        )
    elif gate >= 0.7:
        narrative = (
            f"In {regime} regime the portfolio is sized down ~{sizing_down_pct}% to limit exposure. "
            f"Projected stress drawdown in this regime: {drawdown_band}."
        )
    else:
        narrative = (
            f"In {regime} regime the portfolio is sized down ~{sizing_down_pct}% (technical alpha is weak here). "
            f"Projected stress drawdown if unhedged: {drawdown_band}."
        )
    return PortfolioRiskReport(
        regime=regime,
        gate_multiplier=gate,
        sizing_down_pct=sizing_down_pct,
        narrative=narrative,
    )
