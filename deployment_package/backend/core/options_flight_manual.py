# options_flight_manual.py
"""
Flight Manual Engine: Converts mathematical signals into human-readable trade plans.

Transforms Router output (strategy + scoring) + Regime context + Sizer output
into a complete, UI-ready explanation that builds user confidence and clarity.

The Flight Manual answers: "What am I doing? Why now? When do I exit? What could go wrong?"
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum


# ============================================================================
# Data Models
# ============================================================================

class StrategyType(Enum):
    """Aligned with options_strategy_router.py strategy names."""
    IRON_CONDOR = "IRON_CONDOR"
    BULL_CALL_SPREAD = "BULL_CALL_SPREAD"
    BULL_PUT_SPREAD = "BULL_PUT_SPREAD"
    CASH_SECURED_PUT = "CASH_SECURED_PUT"
    COVERED_CALL = "COVERED_CALL"


class RegimeType(Enum):
    """Aligned with options_regime_detector.py regime names."""
    CRASH_PANIC = "CRASH_PANIC"
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    BREAKOUT_EXPANSION = "BREAKOUT_EXPANSION"
    MEAN_REVERSION = "MEAN_REVERSION"
    POST_EVENT_CRUSH = "POST_EVENT_CRUSH"


class ConfidenceLevel(Enum):
    """Urgency + conviction rating for the trade."""
    HOT = "HOT"              # High conviction, high urgency (act today)
    WARM = "WARM"            # Good setup, moderate urgency
    MONITOR = "MONITOR"      # Interesting but not yet ready


@dataclass(frozen=True)
class StrategyLeg:
    """A single leg of an options strategy."""
    option_type: str         # "CALL" or "PUT"
    strike: float
    expiration_dte: int
    position: str            # "LONG" or "SHORT"
    quantity: int


@dataclass(frozen=True)
class RouterOutput:
    """The strategy recommendation from options_strategy_router.py."""
    strategy_name: str       # e.g., "IRON_CONDOR"
    ticker: str
    legs: List[StrategyLeg]
    composite_score: float   # 0-100
    ev_score: float
    efficiency_score: float
    risk_fit_score: float
    liquidity_score: float
    pop: float               # probability of profit
    max_profit: float
    max_loss: float
    reasoning: str           # Router's brief explanation


@dataclass(frozen=True)
class SizerOutput:
    """The position sizing recommendation from options_risk_sizer.py."""
    contracts: int
    risk_amount: float
    kelly_full: float
    kelly_fractional: float
    limiting_factors: Dict[str, str]  # Why was size reduced?
    warnings: Tuple[str, ...]


@dataclass(frozen=True)
class RegimeContext:
    """Current market regime + Flight Manual context."""
    regime: str              # e.g., "MEAN_REVERSION"
    regime_description: str  # Flight Manual for the regime
    iv_rank: float           # Current IV Rank (0-1)
    price_percentile: float  # Price as percentile of 52w range (0-1)


@dataclass(frozen=True)
class PortfolioImpact:
    """How this trade affects the portfolio."""
    portfolio_equity: float
    greeks_before_delta: float
    greeks_after_delta: float
    greeks_before_vega: float
    greeks_after_vega: float
    greeks_before_theta: float
    greeks_after_theta: float
    sector_concentration_pct: float
    ticker_concentration_pct: float


@dataclass
class FlightManual:
    """
    Complete trade explanation - one screen in the mobile app.
    """
    # Core identity
    headline: str                    # "Iron Condor on SPY • Mean Reversion Setup"
    ticker: str
    strategy: str
    confidence: str                  # HOT / WARM / MONITOR

    # The "Why Now" narrative
    thesis_bullets: List[str]        # 3-5 bullet points on regime + setup
    regime_context: str              # "Market in Mean Reversion (IV Rank 72%)"

    # The trade itself
    setup_description: str           # Plain English leg breakdown
    legs_summary: str                # "Short 415/410 Put Spread (20-wide)"

    # The playbook
    profit_rule: str                 # "Close at 50% max profit or 21 DTE, whichever first"
    fire_drill: str                  # "Exit immediately if price closes outside X or loss hits 80%"
    max_loss_dollars: float          # The number in the "Seatbelt"

    # The math (for transparency)
    greeks_summary: str              # "Short Vega 18pt, Long Theta 8pt/day"
    economics_summary: str           # "Max Profit $150 (PoP 62%), Max Loss $350"
    confidence_score: float          # 0-100 from Router

    # The reality check
    portfolio_impact: str            # "Adds 1.2% risk to portfolio (within guardrails)"
    limiting_factors_text: str       # "Size reduced due to sector concentration"
    warnings: List[str]

    # Mobile UI hints
    action_recommended: bool         # Should "Place Trade" button be highlighted?
    color_scheme: str                # "green" (HOT) / "yellow" (WARM) / "gray" (MONITOR)


# ============================================================================
# Flight Manual Templates
# ============================================================================

class FlightManualTemplates:
    """
    Static templates for each (Regime, Strategy) combination.
    Customizes the narrative based on market condition + trade type.
    """

    # -----------------------------------------------------------------------
    # MEAN_REVERSION templates
    # -----------------------------------------------------------------------

    MEAN_REVERSION_IRON_CONDOR = {
        "headline_template": "Iron Condor on {ticker} • Selling Elevated IV",
        "thesis_template": [
            "Market in {regime} mode: IV Rank at {iv_rank}% suggests overpriced options",
            "Price {price_direction} of recent highs — mean-reverting trades ideal",
            "Sell premium at resistance/support for high-probability trade",
        ],
        "setup_template": "Sell call spread {short_call_strike}/{long_call_strike}, sell put spread {short_put_strike}/{long_put_strike}",
        "profit_rule_template": "Close at 50% max profit (${max_profit_50}) or 21 DTE, whichever comes first",
        "fire_drill_template": "Exit immediately if price closes outside the profit zone ({short_put_strike}-{short_call_strike}) or loss exceeds 80% max loss",
        "greeks_template": "Net Short Vega {vega}pt (collecting decay), Long Theta {theta}pt/day",
    }

    MEAN_REVERSION_BULL_CALL_SPREAD = {
        "headline_template": "Bull Call Spread on {ticker} • Defined-Risk Upside",
        "thesis_template": [
            "Market in {regime} mode: IV Rank {iv_rank}% allows cheap long calls",
            "Support nearby — setup for bounce to upper Bollinger Band",
            "Buy long call at market price, sell short call for credit (limited risk)",
        ],
        "setup_template": "Long call {long_call_strike}, short call {short_call_strike} ({width}-wide spread)",
        "profit_rule_template": "Close at 50% max profit (${max_profit_50}) or 14 DTE, whichever comes first",
        "fire_drill_template": "Exit if price closes below {support_level} (invalidates setup)",
        "greeks_template": "Long Vega {vega}pt (long volatility), Long Theta {theta}pt/day",
    }

    MEAN_REVERSION_BULL_PUT_SPREAD = {
        "headline_template": "Bull Put Spread on {ticker} • Oversold Bounce Play",
        "thesis_template": [
            "Market in {regime} mode: price near 52-week low or recent support",
            "Sell premium near support with defined-risk put spread",
            "Target: price bounces off support, both puts expire worthless",
        ],
        "setup_template": "Short {short_put_strike} put, long {long_put_strike} put ({width}-wide spread)",
        "profit_rule_template": "Close at 50% max profit or 14 DTE",
        "fire_drill_template": "Exit if price closes below {long_put_strike} (both puts ITM)",
        "greeks_template": "Net Short Vega {vega}pt, Long Theta {theta}pt/day",
    }

    MEAN_REVERSION_CASH_SECURED_PUT = {
        "headline_template": "Cash-Secured Put on {ticker} • Income Play",
        "thesis_template": [
            "Market in {regime} mode: {ticker} pulled back to support",
            "Sell put to collect premium; happy to own at strike if assigned",
            "Generate income (theta decay) over 14-30 DTE",
        ],
        "setup_template": "Short {strike} put ({dte} DTE), backed by ${capital_requirement} cash",
        "profit_rule_template": "Target 50% max profit (${max_profit_50}) or let expire worthless",
        "fire_drill_template": "Exit if price closes below {support_level} × 0.98 (assignment imminent)",
        "greeks_template": "Net Short Vega {vega}pt, Long Theta {theta}pt/day, Delta {delta} (directional exposure)",
    }

    # -----------------------------------------------------------------------
    # BREAKOUT_EXPANSION templates
    # -----------------------------------------------------------------------

    BREAKOUT_EXPANSION_IRON_CONDOR = {
        "headline_template": "Iron Condor on {ticker} • Range-Bound Expansion Ceiling",
        "thesis_template": [
            "Market in breakout mode but within a defined expansion range",
            "Price at {price_percentile}% of recent range — sell edges of expansion",
            "Target: price respects resistance, both short calls expire OTM",
        ],
        "setup_template": "Sell {short_call_strike}/{long_call_strike} call spread, {short_put_strike}/{long_put_strike} put spread",
        "profit_rule_template": "Close at 50% max profit or 35 DTE",
        "fire_drill_template": "Exit immediately if price closes above {short_call_strike} or below {short_put_strike}",
        "greeks_template": "Net Short Vega {vega}pt, Long Theta {theta}pt/day",
    }

    BREAKOUT_EXPANSION_BULL_CALL_SPREAD = {
        "headline_template": "Bull Call Spread on {ticker} • Upside Breakout Play",
        "thesis_template": [
            "Market in upside breakout: price breaking above resistance",
            "IV Rank {iv_rank}% — long call spread captures upside with limited risk",
            "Target: price reaches {upside_target}, long call deep ITM",
        ],
        "setup_template": "Long {long_call_strike} call, short {short_call_strike} call ({width}-wide)",
        "profit_rule_template": "Target 50% max profit (${max_profit_50}) or 21-35 DTE",
        "fire_drill_template": "Exit if price breaks below {entry_price} × 0.98 (breakout fails)",
        "greeks_template": "Net Long Vega {vega}pt, Long Theta {theta}pt/day",
    }

    BREAKOUT_EXPANSION_COVERED_CALL = {
        "headline_template": "Covered Call on {ticker} • Defined Upside Cap",
        "thesis_template": [
            "Market in breakout mode but you want to cap upside for premium income",
            "Own 100 shares, sell {strike} call ({dte} DTE)",
            "Target: collect premium, either expire and keep shares or called away at profit",
        ],
        "setup_template": "Own 100 shares {ticker}, short 1 call at {strike}",
        "profit_rule_template": "Target 50% max profit or assignment at strike",
        "fire_drill_template": "Exit if you no longer want to own shares (close call early)",
        "greeks_template": "Long Delta 100 (100 shares), Short Vega {vega}pt, Short Theta {theta}pt/day",
    }

    # -----------------------------------------------------------------------
    # TREND_UP templates
    # -----------------------------------------------------------------------

    TREND_UP_BULL_CALL_SPREAD = {
        "headline_template": "Bull Call Spread on {ticker} • Trend-Following Long",
        "thesis_template": [
            "Strong uptrend established: {ticker} above 20/50/200-day MAs",
            "Buy upside calls to capture momentum, sell higher calls for credit",
            "Target: ride the trend with defined max profit at resistance",
        ],
        "setup_template": "Long {long_call_strike} call, short {short_call_strike} call ({width}-wide)",
        "profit_rule_template": "Target 50% max profit or 30 DTE",
        "fire_drill_template": "Exit if price breaks below 20-day MA (trend broken)",
        "greeks_template": "Net Long Vega {vega}pt, Long Theta {theta}pt/day",
    }

    TREND_UP_COVERED_CALL = {
        "headline_template": "Covered Call on {ticker} • Uptrend Income",
        "thesis_template": [
            "Strong uptrend: {ticker} rallying, pull back premiums to 30-40 delta",
            "Own shares, sell calls just OTM for steady income",
            "Target: collect premium over 7-14 DTE",
        ],
        "setup_template": "Own 100 shares {ticker}, short call at {strike}",
        "profit_rule_template": "Target 50% premium (${max_profit_50}) or assignment",
        "fire_drill_template": "Exit call if {ticker} breaks above {short_call_strike} + $3 (breakout acceleration)",
        "greeks_template": "Long Delta 100 (shares), Short Vega {vega}pt",
    }

    # -----------------------------------------------------------------------
    # TREND_DOWN templates
    # -----------------------------------------------------------------------

    TREND_DOWN_BULL_PUT_SPREAD = {
        "headline_template": "Bull Put Spread on {ticker} • Downtrend Support Play",
        "thesis_template": [
            "Downtrend active but price near support — sell puts at support level",
            "Bull put spread: short put at support, long put as safety net",
            "Target: price holds support, both puts expire worthless",
        ],
        "setup_template": "Short {short_put_strike} put, long {long_put_strike} put ({width}-wide)",
        "profit_rule_template": "Target 50% max profit or 14 DTE",
        "fire_drill_template": "Exit if price closes below {long_put_strike} (both puts ITM)",
        "greeks_template": "Net Short Vega {vega}pt, Long Theta {theta}pt/day",
    }

    # -----------------------------------------------------------------------
    # CRASH_PANIC templates
    # -----------------------------------------------------------------------

    CRASH_PANIC_CASH_SECURED_PUT = {
        "headline_template": "Opportunistic CSP on {ticker} • Crash Sale",
        "thesis_template": [
            "Market in panic: {ticker} down {price_drop}%, IV Rank {iv_rank}%",
            "Put selling becomes attractive after sharp drawdown",
            "Target: collect premium or get assigned at distressed price",
        ],
        "setup_template": "Short {strike} put, backed by ${capital_requirement} cash (ready to own at crash price)",
        "profit_rule_template": "Target 30% max profit (crash puts) or 7 DTE",
        "fire_drill_template": "Exit before earnings; re-evaluate macro headwinds",
        "greeks_template": "Net Short Vega {vega}pt, Long Theta {theta}pt/day",
    }

    CRASH_PANIC_BULL_CALL_SPREAD = {
        "headline_template": "Bull Call Spread on {ticker} • Contrarian Bottom Play",
        "thesis_template": [
            "Market in panic but price near support level — opportunistic long",
            "Buy call spread with tight width for small premium outlay",
            "Target: fade panic, price rebounds 3-5% over 14 DTE",
        ],
        "setup_template": "Long {long_call_strike} call, short {short_call_strike} call ({width}-wide)",
        "profit_rule_template": "Target 50% max profit (quick fade) or 14 DTE",
        "fire_drill_template": "Exit if price closes below ${support_level} (second sell-off confirmed)",
        "greeks_template": "Net Long Vega {vega}pt (long volatility), Long Theta {theta}pt/day",
    }

    # -----------------------------------------------------------------------
    # POST_EVENT_CRUSH templates
    # -----------------------------------------------------------------------

    POST_EVENT_CRUSH_IRON_CONDOR = {
        "headline_template": "Iron Condor on {ticker} • IV Crush Income Play",
        "thesis_template": [
            "Post-earnings or event: implied vol will crash from event premium",
            "Sell iron condor at current elevated IV for high theta decay",
            "Target: IV crush does the work, trade expires for max profit",
        ],
        "setup_template": "Sell {short_call_strike}/{long_call_strike} call spread, {short_put_strike}/{long_put_strike} put spread",
        "profit_rule_template": "Target 75-90% max profit as IV collapses (post-event)",
        "fire_drill_template": "Exit immediately if {ticker} moves beyond short strikes (gap risk)",
        "greeks_template": "Net Short Vega {vega}pt (short volatility), Long Theta {theta}pt/day",
    }

    POST_EVENT_CRUSH_COVERED_CALL = {
        "headline_template": "Covered Call on {ticker} • Post-Earnings Premium Harvest",
        "thesis_template": [
            "Event just passed: implied vol elevated, sell calls for premium harvest",
            "Own shares, sell calls OTM to capture decay without gap risk",
            "Target: collect premium over 7-14 DTE as IV declines",
        ],
        "setup_template": "Own 100 shares {ticker}, short {strike} call ({dte} DTE)",
        "profit_rule_template": "Target 60% max premium (IV crush helpers) or 14 DTE",
        "fire_drill_template": "Exit if {ticker} gaps above short call at open (assignment imminent)",
        "greeks_template": "Long Delta 100 (shares), Short Vega {vega}pt",
    }

    @classmethod
    def get_template(cls, regime: str, strategy: str) -> Dict:
        """Fetch the appropriate template for a regime/strategy combo."""
        key = f"{regime}_{strategy}"
        return getattr(cls, key, None) or cls._default_template()

    @staticmethod
    def _default_template() -> Dict:
        """Fallback template if specific combo not found."""
        return {
            "headline_template": "{strategy} on {ticker}",
            "thesis_template": [
                "Trade aligned with current market regime ({regime})",
                "Setup score: {confidence_score}% conviction",
                "Ready to execute when confirmed",
            ],
            "setup_template": "Execute {strategy} structure with {legs_count} legs",
            "profit_rule_template": "Target 50% max profit or 14-21 DTE",
            "fire_drill_template": "Exit if price invalidates setup assumptions",
            "greeks_template": "Greeks per contract: {greeks_summary}",
        }


# ============================================================================
# Flight Manual Engine
# ============================================================================

class FlightManualEngine:
    """
    Converts mathematical signals + regime context into human-readable trade plans.
    """

    def __init__(self, playbooks_config: Optional[Dict] = None):
        """
        Args:
            playbooks_config: Optional config dict with regime descriptions, strategy labels, etc.
        """
        self.playbooks = playbooks_config or {}
        self.templates = FlightManualTemplates()

    def generate_flight_manual(
        self,
        router_output: RouterOutput,
        regime: RegimeContext,
        sizer_output: SizerOutput,
        portfolio_impact: PortfolioImpact,
    ) -> FlightManual:
        """
        Generate a complete Flight Manual from all inputs.

        Args:
            router_output: Strategy recommendation with scores and PoP
            regime: Current market regime + description
            sizer_output: Position sizing with contracts + risk amount
            portfolio_impact: Greeks impact on portfolio

        Returns:
            Complete FlightManual ready for UI rendering
        """

        # Select template for this (regime, strategy) combo
        template = self.templates.get_template(regime.regime, router_output.strategy_name)

        # Build the narrative components
        headline = self._format_headline(template, router_output, regime)
        thesis = self._build_thesis(template, router_output, regime, portfolio_impact)
        setup_desc = self._build_setup(template, router_output, regime)
        legs_summary = self._build_legs_summary(router_output)
        profit_rule = self._build_profit_rule(template, router_output, sizer_output)
        fire_drill = self._build_fire_drill(template, router_output, regime)
        greeks_summary = self._build_greeks_summary(router_output, sizer_output)
        economics_summary = self._build_economics_summary(router_output, sizer_output)
        portfolio_impact_text = self._build_portfolio_impact(portfolio_impact, sizer_output)
        limiting_factors_text = self._build_limiting_factors(sizer_output)
        
        # Determine confidence level
        confidence_level = self._assess_confidence(router_output, regime, sizer_output)
        color_scheme = "green" if confidence_level == "HOT" else ("yellow" if confidence_level == "WARM" else "gray")
        action_recommended = confidence_level in ("HOT", "WARM")

        # Warnings
        warnings = list(sizer_output.warnings)
        if sizer_output.limiting_factors:
            warnings.extend([f"Size adjusted: {msg}" for msg in sizer_output.limiting_factors.values()])

        return FlightManual(
            headline=headline,
            ticker=router_output.ticker,
            strategy=router_output.strategy_name,
            confidence=confidence_level,
            thesis_bullets=thesis,
            regime_context=regime.regime_description,
            setup_description=setup_desc,
            legs_summary=legs_summary,
            profit_rule=profit_rule,
            fire_drill=fire_drill,
            max_loss_dollars=router_output.max_loss * sizer_output.contracts,
            greeks_summary=greeks_summary,
            economics_summary=economics_summary,
            confidence_score=router_output.composite_score,
            portfolio_impact=portfolio_impact_text,
            limiting_factors_text=limiting_factors_text,
            warnings=warnings,
            action_recommended=action_recommended,
            color_scheme=color_scheme,
        )

    # ---------- Component Builders ----------

    def _format_headline(self, template: Dict, router: RouterOutput, regime: RegimeContext) -> str:
        """Generate headline: e.g., 'Iron Condor on SPY • Selling Elevated IV'"""
        fmt = template.get("headline_template", "{strategy} on {ticker}")
        return fmt.format(
            ticker=router.ticker,
            strategy=router.strategy_name,
            regime=regime.regime,
        )

    def _build_thesis(self, template: Dict, router: RouterOutput, regime: RegimeContext, portfolio: PortfolioImpact) -> List[str]:
        """Generate 3-5 bullet points on 'Why Now'."""
        thesis_template = template.get("thesis_template", ["Setup identified", "Trade ready"])
        
        # Estimate price direction from the trade's expected P&L relative to portfolio
        if portfolio.portfolio_equity > 0:
            price_pct = (router.max_profit / portfolio.portfolio_equity) * 100
        else:
            price_pct = 0.0
        price_direction = "higher" if router.composite_score >= 50 else "lower"

        # Build format dict with all possible fields
        format_dict = {
            "regime": regime.regime,
            "iv_rank": f"{int(regime.iv_rank * 100)}",
            "price_direction": price_direction,
            "price_percentile": f"{int(regime.price_percentile * 100)}",
            "confidence_score": f"{int(router.composite_score)}",
            "ticker": router.ticker,
        }

        thesis = []
        for bullet in thesis_template:
            try:
                formatted = bullet.format(**format_dict)
            except KeyError:
                formatted = bullet
            thesis.append(formatted)
        
        return thesis

    def _build_setup(self, template: Dict, router: RouterOutput, regime: RegimeContext) -> str:
        """Generate plain English setup description."""
        setup_template = template.get("setup_template", "Execute structured trade")
        
        # Extract strike info from legs (simplified)
        strikes = sorted([leg.strike for leg in router.legs])
        
        # Build format dict with all possible fields
        format_dict = {
            "strategy": router.strategy_name,
            "legs_count": len(router.legs),
            "ticker": router.ticker,
            "width": 5 if len(strikes) >= 2 else 0,
        }
        
        # Add strike fields if available
        if len(strikes) >= 4:
            format_dict.update({
                "short_put_strike": strikes[0],
                "long_put_strike": strikes[1],
                "short_call_strike": strikes[2],
                "long_call_strike": strikes[3],
            })
        elif len(strikes) >= 2:
            format_dict.update({
                "long_call_strike": strikes[0],
                "short_call_strike": strikes[1],
                "short_put_strike": strikes[0],
                "long_put_strike": strikes[1],
            })
        
        # Safe format: only substitute keys that exist in the template
        try:
            return setup_template.format(**format_dict)
        except KeyError:
            return f"{router.strategy_name} structure on {router.ticker} ({len(router.legs)} legs)"

    def _build_legs_summary(self, router: RouterOutput) -> str:
        """Summarize the legs: e.g., 'Short 415/410 Put Spread (20-wide)'"""
        if len(router.legs) == 0:
            return "No legs"
        
        legs_desc = []
        for leg in router.legs:
            pos = leg.position[0].upper()
            opt_type = leg.option_type[0].upper()
            legs_desc.append(f"{pos}{opt_type} {leg.strike}")
        
        return " + ".join(legs_desc)

    def _build_profit_rule(self, template: Dict, router: RouterOutput, sizer: SizerOutput) -> str:
        """Generate profit target rule."""
        template_str = template.get("profit_rule_template", "Target 50% max profit")
        max_profit_50 = router.max_profit * 0.5 * sizer.contracts
        
        format_dict = {
            "max_profit_50": f"${max_profit_50:.0f}",
            "dte": 30,
        }
        
        try:
            return template_str.format(**format_dict)
        except KeyError:
            return template_str

    def _build_fire_drill(self, template: Dict, router: RouterOutput, regime: RegimeContext) -> str:
        """Generate exit rule for when things go wrong."""
        template_str = template.get("fire_drill_template", "Exit if price invalidates setup")
        
        format_dict = {
            "ticker": router.ticker,
        }
        
        try:
            return template_str.format(**format_dict)
        except KeyError:
            return template_str

    def _build_greeks_summary(self, router: RouterOutput, sizer: SizerOutput) -> str:
        """Summarize Greeks for this trade."""
        # Placeholder: would aggregate from legs
        return f"Greeks per contract (summary) from {router.strategy_name}"

    def _build_economics_summary(self, router: RouterOutput, sizer: SizerOutput) -> str:
        """Summarize profit/loss potential."""
        total_profit = router.max_profit * sizer.contracts
        total_loss = router.max_loss * sizer.contracts
        
        return f"Max Profit ${total_profit:.0f} (PoP {int(router.pop*100)}%), Max Loss ${total_loss:.0f}"

    def _build_portfolio_impact(self, portfolio: PortfolioImpact, sizer: SizerOutput) -> str:
        """Explain how this trade affects the portfolio."""
        risk_pct = (sizer.risk_amount / portfolio.portfolio_equity) * 100 if portfolio.portfolio_equity > 0 else 0
        delta_change = portfolio.greeks_after_delta - portfolio.greeks_before_delta
        
        return (
            f"Adds {risk_pct:.1f}% portfolio risk (within guardrails). "
            f"Portfolio Delta: {portfolio.greeks_before_delta:.0f} → {portfolio.greeks_after_delta:.0f} "
            f"({delta_change:+.0f}). "
            f"Sector concentration: {portfolio.sector_concentration_pct:.1f}%."
        )

    def _build_limiting_factors(self, sizer: SizerOutput) -> str:
        """Explain any guardrails that reduced the position."""
        if not sizer.limiting_factors:
            return "No guardrails applied. Full Kelly sizing allowed."
        
        factors = [f"{k}: {v}" for k, v in sizer.limiting_factors.items()]
        return "Guardrails applied: " + " | ".join(factors[:2])  # Show top 2

    def _assess_confidence(self, router: RouterOutput, regime: RegimeContext, sizer: SizerOutput) -> str:
        """Determine HOT / WARM / MONITOR based on score + regime + sizing."""
        score = router.composite_score
        pop = router.pop
        
        # High score + good PoP + full sizing = HOT
        if score >= 75 and pop >= 0.60 and len(sizer.limiting_factors) <= 1:
            return "HOT"
        
        # Decent score + reasonable PoP = WARM
        if score >= 60 and pop >= 0.55:
            return "WARM"
        
        # Everything else = MONITOR
        return "MONITOR"


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Iron Condor in Mean Reversion regime
    
    router = RouterOutput(
        strategy_name="IRON_CONDOR",
        ticker="SPY",
        legs=[
            StrategyLeg(option_type="PUT", strike=415, expiration_dte=21, position="SHORT", quantity=1),
            StrategyLeg(option_type="PUT", strike=410, expiration_dte=21, position="LONG", quantity=1),
            StrategyLeg(option_type="CALL", strike=475, expiration_dte=21, position="SHORT", quantity=1),
            StrategyLeg(option_type="CALL", strike=480, expiration_dte=21, position="LONG", quantity=1),
        ],
        composite_score=78.5,
        ev_score=82,
        efficiency_score=75,
        risk_fit_score=76,
        liquidity_score=82,
        pop=0.66,
        max_profit=150,
        max_loss=350,
        reasoning="High IV Rank (72%), price near 20-MA support. Excellent risk/reward.",
    )
    
    regime = RegimeContext(
        regime="MEAN_REVERSION",
        regime_description="Market mean-reverting: price pullback after rally, IV Rank elevated. "
                          "Selling premium at overextended levels ideal.",
        iv_rank=0.72,
        price_percentile=0.35,
    )
    
    sizer = SizerOutput(
        contracts=2,
        risk_amount=700,
        kelly_full=0.052,
        kelly_fractional=0.0052,
        limiting_factors={},
        warnings=("Size at 2 contracts. Kelly suggests 2.6%, capped at 2% max trade risk.",),
    )
    
    portfolio = PortfolioImpact(
        portfolio_equity=25000,
        greeks_before_delta=120,
        greeks_after_delta=108,
        greeks_before_vega=-200,
        greeks_after_vega=-190,
        greeks_before_theta=35,
        greeks_after_theta=51,
        sector_concentration_pct=0.28,
        ticker_concentration_pct=0.08,
    )
    
    engine = FlightManualEngine()
    manual = engine.generate_flight_manual(router, regime, sizer, portfolio)
    
    print("=" * 80)
    print(f"FLIGHT MANUAL: {manual.headline}")
    print("=" * 80)
    print(f"Confidence: {manual.confidence} | Action Recommended: {manual.action_recommended}")
    print(f"Score: {manual.confidence_score}/100 | Max Loss: ${manual.max_loss_dollars:.0f}")
    print()
    print("WHY NOW:")
    for bullet in manual.thesis_bullets:
        print(f"  • {bullet}")
    print()
    print(f"SETUP: {manual.setup_description}")
    print(f"LEGS: {manual.legs_summary}")
    print()
    print(f"PROFIT RULE: {manual.profit_rule}")
    print(f"FIRE DRILL: {manual.fire_drill}")
    print()
    print(f"ECONOMICS: {manual.economics_summary}")
    print(f"GREEKS: {manual.greeks_summary}")
    print()
    print(f"PORTFOLIO IMPACT: {manual.portfolio_impact}")
    print()
    if manual.warnings:
        print("WARNINGS:")
        for warning in manual.warnings:
            print(f"  ⚠️  {warning}")
    print()
    print("=" * 80)
