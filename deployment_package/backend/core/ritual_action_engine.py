"""
Ritual Action Engine
Generates a single actionable suggestion for the Ritual Dawn experience
based on portfolio state and market conditions.
"""

import logging

logger = logging.getLogger(__name__)


def generate_ritual_action(
    portfolio_data: dict,
    market_data: dict,
    user_level: str = "beginner",
) -> dict:
    """
    Analyze portfolio and market data to produce one focused action suggestion.

    Args:
        portfolio_data: Dict with keys has_portfolio, total_value, holdings_count,
                        top_holding, top_holding_pct, holdings (list), is_concentrated.
        market_data: Dict with keys change_percent, volatility, sentiment, indices.
        user_level: One of 'beginner', 'intermediate', 'advanced'.

    Returns:
        Dict with action_type, headline, detail, action_label, target_screen, urgency.
    """
    has_portfolio = portfolio_data.get("has_portfolio", False)
    holdings = portfolio_data.get("holdings", [])
    holdings_count = portfolio_data.get("holdings_count", 0)
    top_holding = portfolio_data.get("top_holding", "")
    top_holding_pct = portfolio_data.get("top_holding_pct", 0)
    is_concentrated = portfolio_data.get("is_concentrated", False)
    is_weekend = market_data.get("is_weekend", False)

    volatility = market_data.get("volatility", 0)
    market_change = abs(market_data.get("change_percent", 0))

    # 0. Weekend mode — markets closed; suggest weekly recap / plan ahead
    if is_weekend:
        return {
            "action_type": "review",
            "headline": "Markets are closed. Use this time to review.",
            "detail": (
                "Catch up on your portfolio, review your goals, "
                "or explore a short lesson so you're ready when markets reopen."
            ),
            "action_label": "Review my week",
            "target_screen": "portfolio-management",
            "urgency": "low",
        }

    # 1. No portfolio at all
    if not has_portfolio or holdings_count == 0:
        return {
            "action_type": "opportunity",
            "headline": "You have capital but no positions.",
            "detail": (
                "Your first investment is the hardest — and the most important. "
                "Start with one position that aligns with your conviction."
            ),
            "action_label": "Build your first position",
            "target_screen": "Stocks",
            "urgency": "medium",
        }

    # 2. Check for large overnight moves on individual holdings
    big_movers = [
        h for h in holdings
        if abs(h.get("change_percent", 0)) >= 5
    ]
    if big_movers:
        mover = big_movers[0]
        symbol = mover.get("symbol", "")
        change_pct = mover.get("change_percent", 0)
        direction = "gained" if change_pct > 0 else "dropped"
        abs_pct = abs(change_pct)

        if change_pct < -5:
            return {
                "action_type": "risk_flag",
                "headline": f"{symbol} {direction} {abs_pct:.1f}% overnight.",
                "detail": (
                    "A move this size warrants attention. "
                    "Check whether the thesis still holds or if risk management is needed."
                ),
                "action_label": f"Review {symbol}",
                "target_screen": "StockDetail",
                "urgency": "high",
            }
        else:
            return {
                "action_type": "opportunity",
                "headline": f"{symbol} {direction} {abs_pct:.1f}% overnight.",
                "detail": (
                    "Strong momentum. Consider whether to lock in gains "
                    "or let your conviction ride."
                ),
                "action_label": f"Review {symbol}",
                "target_screen": "StockDetail",
                "urgency": "medium",
            }

    # 3. Concentration risk
    if is_concentrated or top_holding_pct > 40:
        return {
            "action_type": "risk_flag",
            "headline": f"{top_holding} is {top_holding_pct:.0f}% of your portfolio.",
            "detail": (
                "High concentration amplifies both gains and losses. "
                "Review whether this weighting matches your risk tolerance."
            ),
            "action_label": "Review allocation",
            "target_screen": "portfolio-management",
            "urgency": "medium",
        }

    # 4. Elevated market volatility
    volatility_elevated = (
        (isinstance(volatility, (int, float)) and volatility > 0.02)
        or market_change > 2
    )
    if volatility_elevated:
        return {
            "action_type": "review",
            "headline": "Volatility is elevated today.",
            "detail": (
                "Larger-than-usual market swings can create both risk and opportunity. "
                "Confirm your positions are sized appropriately."
            ),
            "action_label": "Check positions",
            "target_screen": "portfolio-management",
            "urgency": "medium",
        }

    # 5. Everything calm — no action needed
    return {
        "action_type": "no_action",
        "headline": "Portfolio aligned. No action needed today.",
        "detail": (
            "Markets are calm and your positions are balanced. "
            "Sometimes the best move is no move at all."
        ),
        "action_label": "Stay the course",
        "target_screen": None,
        "urgency": "low",
    }
