# options_adapter.py
"""
Adapter functions to connect the 4 phases seamlessly.

Converts:
  - Router output → TradeCandidate (for Sizer input)
  - User Portfolio DB → PortfolioSnapshot (for Sizer input)
  - Sizer output → SizerOutput (for Flight Manual input)
"""

from typing import Dict, List, Optional
from options_risk_sizer import TradeCandidate, Greeks, PortfolioSnapshot, PortfolioImpact
from options_flight_manual import SizerOutput, PortfolioImpact


# ============================================================================
# Router Output → TradeCandidate Adapter
# ============================================================================

def router_candidate_to_trade_candidate(
    candidate: Dict,
    ticker: str,
    sector: str = "Tech",
    corr_to_portfolio: float = 0.5
) -> TradeCandidate:
    """
    Convert Strategy Router candidate to TradeCandidate for Risk Sizer.

    Args:
        candidate: Dict from router.route_regime()["top_3_strategies"][i]
            Expected keys:
            - strategy_name: str
            - legs: List[Dict] with {option_type, strike, bid, ask, long_short}
            - valuation: Dict with {max_profit, max_loss, pop, ...}
            - composite_score: float (0-100)
            - greeks_per_contract: Dict or Greeks object

        ticker: Stock ticker
        sector: Sector classification (optional; would be looked up by ticker normally)
        corr_to_portfolio: Estimated correlation to user's portfolio

    Returns:
        TradeCandidate ready for OptionsRiskSizer.size_trade()
    """

    # Extract valuation metrics from candidate
    valuation = candidate.get("valuation", {})
    max_profit = valuation.get("max_profit", 100.0)
    max_loss = valuation.get("max_loss", 200.0)
    pop = valuation.get("pop", 0.50)

    # Extract/construct Greeks
    greeks_dict = candidate.get("greeks_per_contract", {})
    if isinstance(greeks_dict, Greeks):
        greeks_per_contract = greeks_dict
    else:
        greeks_per_contract = Greeks(
            delta=greeks_dict.get("delta", 0.0),
            vega=greeks_dict.get("vega", 0.0),
            theta=greeks_dict.get("theta", 0.0),
            gamma=greeks_dict.get("gamma", 0.0),
        )

    # Build TradeCandidate
    return TradeCandidate(
        pop=pop,
        max_profit=max_profit,
        max_loss=max_loss,
        greeks_per_contract=greeks_per_contract,
        sector=sector,
        ticker=ticker,
        corr_to_portfolio=corr_to_portfolio,
        edge_score=candidate.get("composite_score", 0.0),
    )


# ============================================================================
# User Portfolio DB → PortfolioSnapshot Adapter
# ============================================================================

def build_portfolio_snapshot_from_db(
    user_id: int,
    equity: float,
    db_session=None
) -> PortfolioSnapshot:
    """
    Convert user portfolio from database to PortfolioSnapshot.

    This is a placeholder. In your real implementation, you would:
      1. Query Portfolio model for this user
      2. Query PortfolioPosition for all open trades
      3. Aggregate Greeks across all positions
      4. Calculate sector/ticker exposure percentages

    Args:
        user_id: User ID
        equity: Current account equity in $
        db_session: ORM session (Django/SQLAlchemy)

    Returns:
        PortfolioSnapshot ready for OptionsRiskSizer.size_trade()
    """

    # PLACEHOLDER: This would be replaced with real DB queries
    # Example implementation outline:
    #
    # portfolio = Portfolio.objects.get(user_id=user_id)
    # positions = PortfolioPosition.objects.filter(portfolio=portfolio, is_closed=False)
    #
    # greeks_total = Greeks()
    # sector_exposure = {}
    # ticker_exposure = {}
    #
    # for pos in positions:
    #     greeks_total.delta += pos.delta * pos.quantity
    #     greeks_total.vega += pos.vega * pos.quantity
    #     ... (aggregate sector/ticker exposure)
    #
    # return PortfolioSnapshot(
    #     equity=equity,
    #     greeks_total=greeks_total,
    #     sector_exposure_pct=sector_exposure,
    #     ticker_exposure_pct=ticker_exposure,
    # )

    # For now, return a default empty portfolio
    return PortfolioSnapshot(
        equity=equity,
        greeks_total=Greeks(delta=0, vega=0, theta=0, gamma=0),
        sector_exposure_pct={},
        ticker_exposure_pct={},
    )


# ============================================================================
# Sizer Output → SizerOutput Adapter
# ============================================================================

def size_decision_to_sizer_output(
    size_decision,  # SizeDecision from OptionsRiskSizer.size_trade()
    trade_candidate: TradeCandidate
) -> SizerOutput:
    """
    Convert OptionsRiskSizer.SizeDecision to Flight Manual's SizerOutput format.

    Args:
        size_decision: SizeDecision from sizer.size_trade()
        trade_candidate: Original TradeCandidate (for context)

    Returns:
        SizerOutput ready for FlightManualEngine.generate_flight_manual()
    """

    return SizerOutput(
        contracts=size_decision.contracts,
        risk_amount=size_decision.risk_amount,
        kelly_full=size_decision.kelly_full,
        kelly_fractional=size_decision.kelly_fractional,
        limiting_factors=size_decision.limiting_factors,
        warnings=size_decision.warnings,
    )


def size_decision_to_portfolio_impact(
    size_decision,  # SizeDecision from OptionsRiskSizer.size_trade()
    portfolio: PortfolioSnapshot,
    trade_candidate: TradeCandidate
) -> PortfolioImpact:
    """
    Convert size decision to portfolio impact for Flight Manual.

    Args:
        size_decision: SizeDecision from sizer.size_trade()
        portfolio: Original PortfolioSnapshot
        trade_candidate: Original TradeCandidate

    Returns:
        PortfolioImpact ready for FlightManualEngine.generate_flight_manual()
    """

    # Calculate Greeks impact
    delta_after = portfolio.greeks_total.delta + size_decision.contracts * trade_candidate.greeks_per_contract.delta
    vega_after = portfolio.greeks_total.vega + size_decision.contracts * trade_candidate.greeks_per_contract.vega
    theta_after = portfolio.greeks_total.theta + size_decision.contracts * trade_candidate.greeks_per_contract.theta
    gamma_after = portfolio.greeks_total.gamma + size_decision.contracts * trade_candidate.greeks_per_contract.gamma

    return PortfolioImpact(
        portfolio_equity=portfolio.equity,
        greeks_before_delta=portfolio.greeks_total.delta,
        greeks_after_delta=delta_after,
        greeks_before_vega=portfolio.greeks_total.vega,
        greeks_after_vega=vega_after,
        greeks_before_theta=portfolio.greeks_total.theta,
        greeks_after_theta=theta_after,
        sector_concentration_pct=portfolio.sector_exposure_pct.get(trade_candidate.sector, 0.0),
        ticker_concentration_pct=portfolio.ticker_exposure_pct.get(trade_candidate.ticker, 0.0) if portfolio.ticker_exposure_pct else 0.0,
    )


# ============================================================================
# Full Pipeline Adapter
# ============================================================================

def pipeline_runner(
    user_id: int,
    ticker: str,
    regime_detected: str,
    router_candidates: List[Dict],
    portfolio_equity: float,
    user_experience_level: str = "basic",
    db_session=None
):
    """
    Single entry point that chains: Router Candidates → Sizer → Flight Manual inputs

    This ties the entire pipeline together in one readable function.

    Args:
        user_id: User ID
        ticker: Stock ticker
        regime_detected: Regime from RegimeDetector (e.g., "MEAN_REVERSION")
        router_candidates: List of Dict from StrategyRouter.route_regime()["top_3_strategies"]
        portfolio_equity: User's current account equity
        user_experience_level: "basic" | "intermediate" | "pro"
        db_session: ORM session for database queries

    Returns:
        List of tuples: (TradeCandidate, SizeDecision, SizerOutput, PortfolioImpact)
        Ready to be converted to FlightManual objects
    """

    from options_risk_sizer import OptionsRiskSizer

    # Build user portfolio state
    portfolio_snapshot = build_portfolio_snapshot_from_db(user_id, portfolio_equity, db_session)

    # Initialize sizer
    sizer = OptionsRiskSizer()

    # Process each candidate
    results = []

    for candidate in router_candidates:
        # Convert router candidate → trade candidate
        trade_candidate = router_candidate_to_trade_candidate(
            candidate,
            ticker=ticker,
            sector="Tech",  # Placeholder; would lookup by ticker
            corr_to_portfolio=0.5  # Placeholder; would calculate from portfolio
        )

        # Size the trade
        size_decision = sizer.size_trade(
            portfolio_snapshot,
            trade_candidate,
            user_experience_level=user_experience_level,
        )

        # Convert outputs to Flight Manual inputs
        sizer_output = size_decision_to_sizer_output(size_decision, trade_candidate)
        portfolio_impact = size_decision_to_portfolio_impact(size_decision, portfolio_snapshot, trade_candidate)

        results.append((trade_candidate, size_decision, sizer_output, portfolio_impact))

    return results
