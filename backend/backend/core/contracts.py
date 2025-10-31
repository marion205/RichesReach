"""
API Response Contracts
======================
Structured contracts for API responses to ensure consistency and enable caching.

These contracts define the shape of responses from AI services,
making them predictable and cacheable.
"""

from __future__ import annotations

from typing import Literal, List, Dict, Any, Optional

# Optional Pydantic import
try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback to dataclass if Pydantic not available
    from dataclasses import dataclass as BaseModel
    Field = lambda **kwargs: None
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


if PYDANTIC_AVAILABLE:
    class MicroViz(BaseModel):
        """Micro visualization data."""
        type: Literal["delta_goal_time", "portfolio_health", "risk_level"]
        value_months: Optional[int] = None
        value_percent: Optional[float] = None
        value_label: Optional[str] = None


    class Reason(BaseModel):
        """Reasoning for an action recommendation."""
        headline: str = Field(..., max_length=100, description="One sentence, one visual")
        drivers: List[str] = Field(..., max_items=3, description="Key drivers")
        micro_viz: MicroViz = Field(..., description="Visualization data")


    class Limits(BaseModel):
        """Safety limits and constraints."""
        max_order_usd: Optional[float] = None
        suitability: Literal["ok", "caution", "restricted"] = "ok"
        risk_level: Optional[Literal["low", "medium", "high"]] = None


    class Contract(BaseModel):
        """
        Standard contract for AI decision responses.
        
        This ensures all AI responses follow a consistent structure,
        making them cacheable and easier to consume.
        """
        action: Literal["deposit", "rebalance", "learn", "wait"]
        confidence: float = Field(..., ge=0.0, le=1.0)
        reason: Reason
        limits: Limits
        
        @validator('confidence')
        def confidence_valid(cls, v):
            """Ensure confidence is in valid range."""
            if not 0.0 <= v <= 1.0:
                raise ValueError('confidence must be between 0 and 1')
            return round(v, 3)
else:
    # Fallback implementations without Pydantic
    from dataclasses import dataclass
    
    @dataclass
    class MicroViz:
        type: str
        value_months: Optional[int] = None
        value_percent: Optional[float] = None
        value_label: Optional[str] = None
    
    @dataclass
    class Reason:
        headline: str
        drivers: List[str]
        micro_viz: 'MicroViz'
    
    @dataclass
    class Limits:
        max_order_usd: Optional[float] = None
        suitability: str = "ok"
        risk_level: Optional[str] = None
    
    @dataclass
    class Contract:
        action: str
        confidence: float
        reason: Reason
        limits: Limits


def validate_contract(response: Dict[str, Any]) -> Contract:
    """
    Validate a response matches the contract.
    
    Args:
        response: Response dictionary
        
    Returns:
        Validated Contract instance
        
    Raises:
        ValidationError: If response doesn't match contract
    """
    return Contract(**response)


# Example contract response
CONTRACT_EXAMPLE = {
    "action": "deposit",
    "confidence": 0.83,
    "reason": {
        "headline": "Calm market. $25 today moves your goal 4 months sooner.",
        "drivers": [
            "Volatility low",
            "Allocation underweight stocks",
            "Income steady"
        ],
        "micro_viz": {
            "type": "delta_goal_time",
            "value_months": 4
        }
    },
    "limits": {
        "max_order_usd": 200,
        "suitability": "ok"
    }
}

