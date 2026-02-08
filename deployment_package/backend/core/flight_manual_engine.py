"""
Flight Manual Engine
Provides educational content for repair strategies.
"""
from __future__ import annotations

from typing import Any, Dict


DEFAULT_FLIGHT_MANUAL: Dict[str, Any] = {
    "title": "Repair Playbook",
    "description": "Step-by-step guidance for repairing an options position.",
    "mathematical_explanation": "Adjust risk/reward to restore edge and reduce tail risk.",
    "example_setup": {},
    "historical_success_rate": 0.72,
    "edge_percentage": 12.0,
    "avg_credit_collected": 120.0,
    "risk_metrics": {
        "max_loss_reduction_pct": 15.0,
        "breakeven_improvement_pct": 5.0,
        "delta_reduction": 0.12,
    },
    "related_videos": [],
    "related_articles": [],
}


REPAIR_FLIGHT_MANUALS: Dict[str, Dict[str, Any]] = {
    "roll_unbalanced_side": {
        "title": "Roll the Unbalanced Side",
        "description": "Roll the tested side out or away to rebalance delta and reduce gamma risk.",
        "mathematical_explanation": "Moving strikes widens the breakeven zone and reduces directional exposure.",
        "example_setup": {
            "current": "Sell 240/245 put spread",
            "repair": "Buy back 240/245 and sell 235/240 for a credit",
        },
        "historical_success_rate": 0.74,
        "edge_percentage": 13.5,
        "avg_credit_collected": 140.0,
        "risk_metrics": {
            "max_loss_reduction_pct": 18.0,
            "breakeven_improvement_pct": 7.0,
            "delta_reduction": 0.18,
        },
        "related_videos": ["https://www.youtube.com/watch?v=roll-options"],
        "related_articles": ["https://www.investopedia.com/terms/r/roll.asp"],
    },
    "roll_out": {
        "title": "Roll Out in Time",
        "description": "Extend duration to give the position time to recover while maintaining a net credit.",
        "mathematical_explanation": "Longer DTE lowers gamma and increases time premium collection.",
        "example_setup": {
            "current": "45 DTE credit spread",
            "repair": "Roll to 60-75 DTE at similar delta",
        },
        "historical_success_rate": 0.71,
        "edge_percentage": 11.0,
        "avg_credit_collected": 110.0,
        "risk_metrics": {
            "max_loss_reduction_pct": 12.0,
            "breakeven_improvement_pct": 4.0,
            "delta_reduction": 0.1,
        },
        "related_videos": [],
        "related_articles": [],
    },
    "iron_condor_adjust": {
        "title": "Iron Condor Adjustment",
        "description": "Recenter the condor by rolling the tested side and reducing exposure.",
        "mathematical_explanation": "Adjusting strikes rebalances delta and improves risk-defined range.",
        "example_setup": {
            "current": "Sell 240/245 puts, 260/265 calls",
            "repair": "Roll puts to 235/240 and calls to 265/270",
        },
        "historical_success_rate": 0.69,
        "edge_percentage": 10.5,
        "avg_credit_collected": 125.0,
        "risk_metrics": {
            "max_loss_reduction_pct": 14.0,
            "breakeven_improvement_pct": 6.0,
            "delta_reduction": 0.15,
        },
        "related_videos": [],
        "related_articles": [],
    },
    "hedge": {
        "title": "Protective Hedge",
        "description": "Add a hedge (long option or spread) to cap tail risk during adverse moves.",
        "mathematical_explanation": "Long gamma hedges offset adverse delta and reduce convexity risk.",
        "example_setup": {
            "current": "Short credit spread",
            "repair": "Buy a cheap out-of-the-money option for protection",
        },
        "historical_success_rate": 0.67,
        "edge_percentage": 9.0,
        "avg_credit_collected": 85.0,
        "risk_metrics": {
            "max_loss_reduction_pct": 22.0,
            "breakeven_improvement_pct": 3.0,
            "delta_reduction": 0.2,
        },
        "related_videos": [],
        "related_articles": [],
    },
}


def get_flight_manual_by_repair_type(repair_type: str) -> Dict[str, Any]:
    """
    Return Flight Manual content for a given repair type.
    """
    normalized = (repair_type or "").strip().lower()
    if not normalized:
        return DEFAULT_FLIGHT_MANUAL

    manual = REPAIR_FLIGHT_MANUALS.get(normalized)
    if manual:
        return manual

    # Fallback: generate a reasonable default
    fallback = dict(DEFAULT_FLIGHT_MANUAL)
    fallback["title"] = f"{repair_type.title()} Repair"
    fallback["description"] = f"Guide for executing {repair_type}."
    return fallback
