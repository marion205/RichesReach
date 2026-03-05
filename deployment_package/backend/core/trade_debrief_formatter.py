"""
trade_debrief_formatter.py
==========================
LLM synthesis layer for the AI Trade Debrief feature.

Takes a TradeDebriefReport (structured analytics) and returns a
TradeDebriefOutput (narrative + structured sections) via the existing
AI service (OpenAI / Anthropic — whichever is configured).

Output contract
---------------
TradeDebriefOutput:
    narrative       : str     — 3–5 sentence plain-English paragraph
    headline        : str     — one punchy sentence (e.g. "You're leaving money on the table.")
    top_insight     : str     — single most impactful behavioural finding
    recommendations : list    — 2–4 actionable bullet points
    stats_summary   : dict    — key numbers for the UI card
    pattern_codes   : list    — machine-readable flags (e.g. ["EARLY_EXIT_BIAS"])
    data_source     : str     — "broker" | "paper" | "mixed" | "none"
    has_enough_data : bool
    generated_at    : str

Usage
-----
    from .trade_debrief_formatter import format_trade_debrief
    output = format_trade_debrief(report)   # report: TradeDebriefReport

    # Or build everything in one call:
    from .trade_debrief_formatter import build_debrief
    output = build_debrief(user, lookback_days=90)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output type
# ---------------------------------------------------------------------------

@dataclass
class TradeDebriefOutput:
    headline: str
    narrative: str
    top_insight: str
    recommendations: List[str]
    stats_summary: Dict[str, Any]
    pattern_codes: List[str]
    data_source: str
    has_enough_data: bool
    generated_at: str
    # Raw report fields surfaced for UI cards
    total_trades: int = 0
    win_rate_pct: float = 0.0
    total_pnl: float = 0.0
    best_sector: Optional[str] = None
    worst_sector: Optional[str] = None
    counterfactual_extra_pnl: float = 0.0
    lookback_days: int = 90
    # Underlying report (set by build_debrief so callers avoid a second build_report call)
    report: Optional[Any] = None


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(report) -> str:
    """
    Build the LLM prompt from a TradeDebriefReport.
    Uses JSON to pass structured data so the model can reason over it precisely.
    """
    from .trade_debrief_service import TradeDebriefReport  # local import to avoid circular

    # Serialise report to a clean dict (drop complex nested objects for brevity)
    sector_bullets = "\n".join(
        f"  - {s.sector}: {s.trades} trades, {s.win_rate:.0%} win rate, "
        f"P&L ${s.total_pnl:+,.0f}"
        for s in report.sector_stats[:6]
    ) or "  - No sector data"

    flag_bullets = "\n".join(
        f"  - [{f.severity.upper()}] {f.code}: {f.description}"
        f"{f' (estimated impact: ${f.impact_dollars:,.0f})' if f.impact_dollars else ''}"
        for f in report.pattern_flags
    ) or "  - No patterns detected"

    hold_section = ""
    if report.hold_time:
        h = report.hold_time
        hold_section = (
            f"Hold-time analysis:\n"
            f"  - Average winner hold: {h.avg_winner_hold_hours:.1f}h\n"
            f"  - Average loser hold: {h.avg_loser_hold_hours:.1f}h\n"
        )

    counterfactual = ""
    if report.counterfactual_extra_pnl > 50:
        counterfactual = (
            f"Counterfactual: if behavioural biases were corrected, "
            f"estimated additional P&L = ${report.counterfactual_extra_pnl:,.0f}\n"
        )

    prompt = f"""You are an AI trading coach at RichesReach. Analyse the user's trading data and produce a structured debrief.

TRADING DATA (last {report.lookback_days} days)
================================================
Total trades:        {report.total_trades}
Win rate:            {report.win_rate * 100:.1f}%
Total realised P&L:  ${report.total_realised_pnl:+,.2f} ({report.total_pnl_percent:+.1f}%)
Average win:         ${report.avg_win_dollars:,.2f}
Average loss:        ${report.avg_loss_dollars:,.2f}
Profit factor:       {report.profit_factor:.2f}
Largest win:         ${report.largest_win:,.2f}
Largest loss:        ${report.largest_loss:,.2f}
Data source:         {report.data_source} trades
Signal-linked:       {report.signal_linked_count} trades matched to system signals

{hold_section}
{counterfactual}
Sector breakdown:
{sector_bullets}

Behavioural pattern flags:
{flag_bullets}

Best sector:  {report.best_sector or 'N/A'}
Worst sector: {report.worst_sector or 'N/A'}

INSTRUCTIONS
============
Respond with a valid JSON object (no markdown fences) with EXACTLY these keys:

{{
  "headline": "One punchy sentence summarising the biggest finding (max 15 words)",
  "narrative": "3-5 sentences explaining what the data shows, written directly to the user (use 'you'). Be specific — cite numbers. Do NOT give financial advice or specific buy/sell recommendations.",
  "top_insight": "The single most impactful pattern or behaviour you identified (1-2 sentences)",
  "recommendations": ["Action 1", "Action 2", "Action 3"]
}}

Rules:
- Write as if talking to a retail investor who wants honest, direct feedback
- Cite specific numbers from the data
- recommendations must be concrete process improvements (e.g. "Set a rule: hold winners until target 1 before considering an exit")
- Do NOT recommend specific stocks, options strategies, or financial instruments
- If there is not enough data (fewer than {5} trades), say so in the narrative and keep recommendations general
- Tone: honest coach, not cheerleader
"""
    return prompt


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def _call_llm(prompt: str) -> Dict[str, Any]:
    """
    Call the AI service and return parsed JSON dict.
    Falls back to a rule-based fallback if LLM is unavailable.
    """
    try:
        from .ai_service import AIService
        service = AIService()
        result  = service.get_chat_response(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.4,
        )
        raw = result.get("content", "")
        if not raw:
            raise ValueError("empty LLM response")

        # Strip any accidental markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        return json.loads(raw)

    except Exception as exc:
        logger.warning("trade_debrief: LLM call failed (%s), using rule-based fallback", exc)
        return {}


# ---------------------------------------------------------------------------
# Rule-based fallback narrative
# ---------------------------------------------------------------------------

def _rule_based_narrative(report) -> Dict[str, Any]:
    """
    Build a simple narrative without LLM when AI is unavailable.
    Less nuanced but always works.
    """
    if not report.has_enough_data:
        return {
            "headline": "Not enough trades to detect patterns yet.",
            "narrative": (
                f"You have {report.total_trades} trades in the last "
                f"{report.lookback_days} days. We need at least 5 completed "
                "trades to surface meaningful patterns. Keep trading and "
                "check back once you have more history."
            ),
            "top_insight": "More data needed for pattern analysis.",
            "recommendations": [
                "Complete at least 5 trades to unlock full debrief analysis.",
                "Consider using paper trading to build history faster.",
            ],
        }

    # Choose headline based on most severe flag
    high_flags = [f for f in report.pattern_flags if f.severity == "high"]
    if high_flags:
        headline = f"Key pattern detected: {high_flags[0].code.replace('_', ' ').title()}."
    elif report.win_rate >= 0.55:
        headline = f"Solid {report.win_rate * 100:.0f}% win rate — but P&L could be higher."
    elif report.win_rate < 0.40:
        headline = f"Win rate of {report.win_rate * 100:.0f}% is below target — let's find why."
    else:
        headline = "Mixed results — patterns in your trades tell the real story."

    # Narrative
    parts = [
        f"Across your last {report.total_trades} trades you've realised "
        f"${report.total_realised_pnl:+,.0f} ({report.total_pnl_percent:+.1f}%) "
        f"with a {report.win_rate * 100:.0f}% win rate and profit factor of {report.profit_factor:.2f}."
    ]
    if report.hold_time and report.hold_time.avg_winner_hold_hours < report.hold_time.avg_loser_hold_hours * 0.7:
        parts.append(
            f"You hold winners for an average of "
            f"{report.hold_time.avg_winner_hold_hours:.0f}h, "
            f"but losers for {report.hold_time.avg_loser_hold_hours:.0f}h — "
            "a classic sign of cutting profits too early while letting losses run."
        )
    if report.best_sector:
        best = next((s for s in report.sector_stats if s.sector == report.best_sector), None)
        if best:
            parts.append(
                f"Your best results are in {report.best_sector} "
                f"({best.win_rate * 100:.0f}% win rate across {best.trades} trades)."
            )
    if report.counterfactual_extra_pnl > 50:
        parts.append(
            f"Fixing your exit timing could unlock an estimated "
            f"${report.counterfactual_extra_pnl:,.0f} in additional P&L."
        )

    top_insight = (
        high_flags[0].description if high_flags
        else (parts[1] if len(parts) > 1 else parts[0])
    )

    recommendations = []
    for flag in report.pattern_flags[:3]:
        if flag.code == "EARLY_EXIT_BIAS":
            recommendations.append(
                "Set a rule: hold winners until the first price target before considering an exit."
            )
        elif flag.code == "LATE_EXIT_LOSERS":
            recommendations.append(
                "Use a hard time-stop: if a trade hasn't worked within your expected hold period, close it."
            )
        elif flag.code == "SECTOR_CONCENTRATION":
            recommendations.append(
                f"Diversify beyond {report.sector_stats[0].sector} — "
                "aim for no more than 40% of trades in a single sector."
            )
        elif flag.code == "MOMENTUM_SPIKE_BUYING":
            recommendations.append(
                "Avoid entering immediately after a large short-term spike — wait for a pullback or confirmation."
            )
        elif flag.code == "TARGET_EXIT_MISS":
            recommendations.append(
                "Trust the signal targets: let at least partial size run to target 1 before trimming."
            )

    if not recommendations:
        recommendations.append("Keep tracking trades — patterns will become clearer with more data.")

    return {
        "headline": headline,
        "narrative": " ".join(parts),
        "top_insight": top_insight,
        "recommendations": recommendations[:4],
    }


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def format_trade_debrief(report) -> TradeDebriefOutput:
    """
    Convert a TradeDebriefReport → TradeDebriefOutput.
    Tries LLM first; falls back to rule-based narrative on failure.
    """
    # Always try LLM if there's data
    llm_result: Dict[str, Any] = {}
    if report.total_trades > 0:
        prompt     = _build_prompt(report)
        llm_result = _call_llm(prompt)

    # Fall back if LLM returned empty or incomplete
    required_keys = {"headline", "narrative", "top_insight", "recommendations"}
    if not llm_result or not required_keys.issubset(llm_result.keys()):
        llm_result = _rule_based_narrative(report)

    stats_summary = {
        "total_trades":    report.total_trades,
        "win_rate_pct":    round(report.win_rate * 100, 1),
        "total_pnl":       report.total_realised_pnl,
        "total_pnl_pct":   report.total_pnl_percent,
        "profit_factor":   report.profit_factor,
        "avg_win":         report.avg_win_dollars,
        "avg_loss":        report.avg_loss_dollars,
        "largest_win":     report.largest_win,
        "largest_loss":    report.largest_loss,
        "best_sector":     report.best_sector,
        "worst_sector":    report.worst_sector,
        "lookback_days":   report.lookback_days,
        "data_source":     report.data_source,
    }
    if report.hold_time:
        stats_summary["avg_winner_hold_hours"] = report.hold_time.avg_winner_hold_hours
        stats_summary["avg_loser_hold_hours"]  = report.hold_time.avg_loser_hold_hours

    return TradeDebriefOutput(
        headline=str(llm_result.get("headline", "")),
        narrative=str(llm_result.get("narrative", "")),
        top_insight=str(llm_result.get("top_insight", "")),
        recommendations=list(llm_result.get("recommendations", [])),
        stats_summary=stats_summary,
        pattern_codes=[f.code for f in report.pattern_flags],
        data_source=report.data_source,
        has_enough_data=report.has_enough_data,
        generated_at=report.generated_at,
        total_trades=report.total_trades,
        win_rate_pct=round(report.win_rate * 100, 1),
        total_pnl=report.total_realised_pnl,
        best_sector=report.best_sector,
        worst_sector=report.worst_sector,
        counterfactual_extra_pnl=report.counterfactual_extra_pnl,
        lookback_days=report.lookback_days,
    )


def build_debrief(user, lookback_days: int = 90) -> TradeDebriefOutput:
    """
    Convenience function: build report + format in one call.
    Attaches the raw report to the output so callers (e.g. GraphQL resolver)
    can use sector_stats / pattern_flags without running the service twice.

    Parameters
    ----------
    user : Django User
    lookback_days : int

    Returns
    -------
    TradeDebriefOutput
        With .report set to the TradeDebriefReport used for formatting.
    """
    from .trade_debrief_service import TradeDebriefService
    service = TradeDebriefService()
    report = service.build_report(user, lookback_days=lookback_days)
    output = format_trade_debrief(report)
    output.report = report
    return output
