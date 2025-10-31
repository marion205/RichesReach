"""
Why Not - Policy Rejection Messages
====================================
Simple, clear explanations when orders are blocked.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class WhyNotResponse(BaseModel):
    """Response when policy blocks an order"""
    blocked: bool = True
    reason: str  # One sentence explanation
    fix: Optional[str] = None  # Suggested fix
    current_value: Optional[float] = None
    max_allowed: Optional[float] = None


def why_not_guardrail(
    violation_type: str,
    current_value: float,
    max_allowed: float,
    suggestion: Optional[str] = None,
) -> WhyNotResponse:
    """
    Generate "Why not" message for guardrail violations.
    
    Args:
        violation_type: Type of violation (e.g., "max_loss", "leverage", "concentration")
        current_value: Current value that exceeds limit
        max_allowed: Maximum allowed value
        suggestion: Optional suggestion to fix
        
    Returns:
        WhyNotResponse with explanation
    """
    messages = {
        "max_loss": {
            "reason": f"Max loss ${current_value:.2f} exceeds limit ${max_allowed:.2f} per trade.",
            "fix": f"Reduce size to ${max_allowed:.2f} or less.",
        },
        "leverage": {
            "reason": f"Leverage {current_value:.1f}:1 exceeds limit {max_allowed:.1f}:1.",
            "fix": "Reduce position size or add cash to account.",
        },
        "concentration": {
            "reason": f"Futures concentration {current_value:.1%} exceeds limit {max_allowed:.1%} of portfolio.",
            "fix": "Reduce futures exposure or increase account value.",
        },
        "suitability": {
            "reason": "Account doesn't meet minimum suitability requirements for futures trading.",
            "fix": suggestion or "Complete suitability assessment or increase account value to $5,000+.",
        },
        "margin": {
            "reason": f"Insufficient margin: ${current_value:.2f} required, ${max_allowed:.2f} available.",
            "fix": "Add cash to account or reduce position size.",
        },
    }
    
    msg = messages.get(violation_type, {
        "reason": f"{violation_type} limit exceeded.",
        "fix": suggestion or "Adjust order parameters.",
    })
    
    return WhyNotResponse(
        blocked=True,
        reason=msg["reason"],
        fix=msg["fix"],
        current_value=current_value,
        max_allowed=max_allowed,
    )


def why_not_suitability(
    score: int,
    min_score: int,
    experience: int,
    min_experience: int,
) -> WhyNotResponse:
    """Generate suitability "Why not" message"""
    reasons = []
    fixes = []
    
    if score < min_score:
        reasons.append(f"Suitability score {score} below minimum {min_score}")
        fixes.append("Complete suitability assessment or wait for approval")
    
    if experience < min_experience:
        reasons.append(f"Experience level {experience} below minimum {min_experience}")
        fixes.append("Gain more trading experience or complete education modules")
    
    reason = ". ".join(reasons) + "."
    fix = "; ".join(fixes) if fixes else None
    
    return WhyNotResponse(
        blocked=True,
        reason=reason,
        fix=fix,
        current_value=float(score),
        max_allowed=float(min_score),
    )

