"""
Proof Narrator — Plain-English If/Then Explanation Generator

Converts metric-heavy audit results into human-readable narratives.
This is the "Explainability as a Product Feature" layer.

Generates three types of narration:
1. Recommendation narration: "IF [condition], THEN [action]"
2. Crisis narration: "What happened, what we did, what you should do"
3. Outcome narration: "Here's what happened after the repair"

Part of Trust-First Framework: Gap 6 — Explainability
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ProofNarrator:
    """
    Converts risk metrics and recommendations into plain-English
    if/then explanations that retail users can understand.
    """

    # ----- Recommendation Narration -----

    def narrate_recommendation(
        self,
        risk_metrics: Dict[str, Any],
        config: Dict[str, Any],
        recommendation: str,
        current_pool_info: Optional[Dict[str, Any]] = None,
        target_pool_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate plain-English explanation for a repair recommendation.

        Args:
            risk_metrics: {calmar_ratio, max_drawdown, tvl_stability, volatility}
            config: {min_calmar_hold, min_calmar_rebalance, max_drawdown_hold, ...}
            recommendation: 'HOLD', 'REBALANCE', or 'EXIT'
            current_pool_info: {protocol, symbol, apy, ...}
            target_pool_info: {protocol, symbol, apy, ...} (for REBALANCE/EXIT)

        Returns:
            dict with: if_then (str), plain_summary (str), before_after (dict)
        """
        calmar = risk_metrics.get('calmar_ratio', 0)
        max_dd = risk_metrics.get('max_drawdown', 0)
        tvl_stability = risk_metrics.get('tvl_stability', 0)

        min_calmar_hold = config.get('min_calmar_hold', 1.0)
        min_calmar_rebalance = config.get('min_calmar_rebalance', 0.6)
        max_dd_hold = config.get('max_drawdown_hold', 0.07)
        max_dd_rebalance = config.get('max_drawdown_rebalance', 0.12)
        min_tvl_hold = config.get('min_tvl_stability_hold', 0.70)
        min_tvl_rebalance = config.get('min_tvl_stability_rebalance', 0.50)

        current_name = self._pool_name(current_pool_info)
        target_name = self._pool_name(target_pool_info)

        if_then = self._build_if_then(
            recommendation, calmar, max_dd, tvl_stability,
            min_calmar_hold, min_calmar_rebalance,
            max_dd_hold, max_dd_rebalance,
            min_tvl_hold, min_tvl_rebalance,
            current_name,
        )

        plain_summary = self._build_plain_summary(
            recommendation, calmar, max_dd, tvl_stability,
            current_name, target_name,
            current_pool_info, target_pool_info,
        )

        before_after = self._build_before_after(
            risk_metrics, current_pool_info, target_pool_info,
        )

        return {
            'if_then': if_then,
            'plain_summary': plain_summary,
            'before_after': before_after,
        }

    def _build_if_then(
        self,
        recommendation: str,
        calmar: float, max_dd: float, tvl_stability: float,
        min_calmar_hold: float, min_calmar_rebalance: float,
        max_dd_hold: float, max_dd_rebalance: float,
        min_tvl_hold: float, min_tvl_rebalance: float,
        current_name: str,
    ) -> str:
        """Build the IF/THEN explanation string."""

        if recommendation == 'EXIT':
            # Find which metric triggered EXIT
            triggers = []
            if calmar < min_calmar_rebalance:
                triggers.append(
                    f"the Calmar ratio ({calmar:.2f}) fell below "
                    f"our safety minimum ({min_calmar_rebalance:.2f})"
                )
            if max_dd > max_dd_rebalance:
                triggers.append(
                    f"the max drawdown ({max_dd:.1%}) exceeded "
                    f"our risk ceiling ({max_dd_rebalance:.1%})"
                )
            if tvl_stability < min_tvl_rebalance:
                triggers.append(
                    f"liquidity stability ({tvl_stability:.2f}) dropped below "
                    f"our minimum ({min_tvl_rebalance:.2f})"
                )

            trigger_text = triggers[0] if triggers else "risk metrics fell below safe thresholds"
            return (
                f"IF {trigger_text}, "
                f"THEN we recommend exiting {current_name} to protect your capital."
            )

        elif recommendation == 'REBALANCE':
            triggers = []
            if calmar < min_calmar_hold:
                triggers.append(
                    f"the Calmar ratio ({calmar:.2f}) is below our preferred "
                    f"level ({min_calmar_hold:.2f})"
                )
            if max_dd > max_dd_hold:
                triggers.append(
                    f"the max drawdown ({max_dd:.1%}) is above our comfort zone "
                    f"({max_dd_hold:.1%})"
                )
            if tvl_stability < min_tvl_hold:
                triggers.append(
                    f"liquidity stability ({tvl_stability:.2f}) is below our "
                    f"target ({min_tvl_hold:.2f})"
                )

            trigger_text = triggers[0] if triggers else "performance metrics suggest room for improvement"
            return (
                f"IF {trigger_text}, "
                f"THEN we suggest moving to a vault with better risk-adjusted returns."
            )

        else:  # HOLD
            return (
                f"Your position in {current_name} meets all safety thresholds. "
                f"No action needed."
            )

    def _build_plain_summary(
        self,
        recommendation: str,
        calmar: float, max_dd: float, tvl_stability: float,
        current_name: str, target_name: str,
        current_pool_info: Optional[Dict], target_pool_info: Optional[Dict],
    ) -> str:
        """Build a 1-2 sentence plain summary."""

        if recommendation == 'EXIT':
            return (
                f"{current_name} is no longer meeting our safety standards. "
                f"We recommend moving your funds to protect against further losses."
            )

        elif recommendation == 'REBALANCE':
            if target_pool_info:
                target_apy = target_pool_info.get('apy', 0)
                current_apy = current_pool_info.get('apy', 0) if current_pool_info else 0
                apy_diff = target_apy - current_apy

                if apy_diff > 0:
                    return (
                        f"We found a safer option with better returns. "
                        f"{target_name} offers {apy_diff:.1f}% more APY "
                        f"with lower risk."
                    )

            return (
                f"Performance or stability of {current_name} suggests "
                f"a safer alternative is available."
            )

        else:  # HOLD
            return (
                f"{current_name} is performing within expected parameters. "
                f"Returns justify the risk."
            )

    def _build_before_after(
        self,
        risk_metrics: Dict[str, Any],
        current_pool_info: Optional[Dict],
        target_pool_info: Optional[Dict],
    ) -> Dict[str, Any]:
        """Build before/after comparison dict for display."""

        current = {
            'calmar': round(risk_metrics.get('calmar_ratio', 0), 2),
            'max_drawdown': f"{risk_metrics.get('max_drawdown', 0):.1%}",
            'tvl_stability': round(risk_metrics.get('tvl_stability', 0), 2),
            'apy': f"{(current_pool_info or {}).get('apy', 0):.1f}%",
        }

        target = {}
        if target_pool_info:
            target_risk = target_pool_info.get('risk_metrics', {})
            target = {
                'calmar': round(target_risk.get('calmar_ratio', 0), 2),
                'max_drawdown': f"{target_risk.get('max_drawdown', 0):.1%}",
                'tvl_stability': round(target_risk.get('tvl_stability', 0), 2),
                'apy': f"{target_pool_info.get('apy', 0):.1f}%",
            }

        return {'current': current, 'target': target}

    # ----- Crisis Narration -----

    def narrate_crisis(
        self,
        circuit_breaker_state: Dict[str, Any],
        portfolio_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a plain-English explanation for a circuit breaker event.

        Args:
            circuit_breaker_state: {state, reason, triggered_by, chain_id, ...}
            portfolio_data: Optional drawdown data from PortfolioRiskMonitor

        Returns:
            Human-readable crisis explanation string
        """
        reason = circuit_breaker_state.get('reason', 'Unknown')
        triggered_by = circuit_breaker_state.get('triggered_by', 'system')
        state = circuit_breaker_state.get('state', 'OPEN')

        # Build explanation based on trigger type
        if triggered_by == 'gas_spike':
            explanation = (
                f"Gas prices spiked on the network. "
                f"We paused all transactions to protect you from overpaying. "
                f"Your existing positions are safe — no funds are at risk. "
                f"Transactions will automatically resume when gas normalizes."
            )
        elif triggered_by == 'protocol_incident':
            explanation = (
                f"We detected a potential issue with a protocol. "
                f"All transactions have been paused as a precaution. "
                f"Your funds remain in their current positions. "
                f"We are monitoring the situation and will resume when safe."
            )
        elif triggered_by == 'admin':
            explanation = (
                f"Our team has temporarily paused DeFi transactions "
                f"for system maintenance. Your positions are unaffected. "
                f"We will resume operations shortly."
            )
        else:
            explanation = (
                f"DeFi transactions have been temporarily paused. "
                f"Reason: {reason}. "
                f"Your positions are safe. We will resume when conditions improve."
            )

        # Add portfolio context if available
        if portfolio_data and portfolio_data.get('breached'):
            drawdown_pct = portfolio_data.get('drawdown_pct', 0)
            explanation += (
                f" Additionally, your portfolio has drawn down {drawdown_pct:.1%} "
                f"from its peak. Auto-Pilot is evaluating protective actions."
            )

        # Add recovery info for HALF_OPEN state
        if state == 'HALF_OPEN':
            explanation += (
                " We are now in recovery mode — small transactions (up to $100) "
                "are allowed while we verify conditions are fully safe."
            )

        return explanation

    # ----- Outcome Narration -----

    def narrate_outcome(
        self,
        expected_apy_delta: float,
        actual_apy_delta: float,
        outcome_status: str,
        days_since_repair: int = 7,
        from_vault: str = '',
        to_vault: str = '',
    ) -> str:
        """
        Generate a post-mortem narrative for a completed repair.

        Args:
            expected_apy_delta: What we predicted
            actual_apy_delta: What actually happened
            outcome_status: 'beneficial', 'neutral', or 'underperformed'
            days_since_repair: Days since the repair was executed
            from_vault: Source vault name
            to_vault: Target vault name

        Returns:
            Human-readable outcome narrative
        """
        expected_pct = expected_apy_delta * 100
        actual_pct = actual_apy_delta * 100

        if outcome_status == 'beneficial':
            narrative = (
                f"{days_since_repair} days after moving from {from_vault} to {to_vault}, "
                f"the repair delivered {actual_pct:+.1f}% APY improvement "
                f"(we predicted {expected_pct:+.1f}%). "
                f"The move was beneficial for your portfolio."
            )
        elif outcome_status == 'neutral':
            narrative = (
                f"{days_since_repair} days after the move to {to_vault}, "
                f"APY changed by {actual_pct:+.1f}% "
                f"(we predicted {expected_pct:+.1f}%). "
                f"The outcome was roughly neutral — your risk exposure improved "
                f"even if yields were similar."
            )
        else:  # underperformed
            narrative = (
                f"{days_since_repair} days after the move to {to_vault}, "
                f"APY changed by {actual_pct:+.1f}% instead of the "
                f"predicted {expected_pct:+.1f}%. "
                f"The repair underperformed expectations. "
                f"We're factoring this into future recommendations."
            )

        return narrative

    # ----- Helpers -----

    def _pool_name(self, pool_info: Optional[Dict]) -> str:
        """Extract a human-readable pool name."""
        if not pool_info:
            return "your current vault"
        protocol = pool_info.get('protocol', '')
        symbol = pool_info.get('symbol', '')
        if protocol and symbol:
            return f"{protocol} {symbol}"
        return symbol or protocol or "the vault"


# Singleton
_proof_narrator = None


def get_proof_narrator() -> ProofNarrator:
    global _proof_narrator
    if _proof_narrator is None:
        _proof_narrator = ProofNarrator()
    return _proof_narrator
