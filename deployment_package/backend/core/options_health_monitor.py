"""
Edge Factory Health & Integrity Monitor

Runs pre-flight checks to ensure market data and regime logic are reliable
before presenting trade plans to users.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    is_healthy: bool
    data_freshness: str
    logic_confidence: float
    active_alerts: List[str]


class EdgeFactoryHealthMonitor:
    def __init__(self, data_fetcher, regime_detector=None):
        self.fetcher = data_fetcher
        self.regime_detector = regime_detector
        self.logger = logging.getLogger("EdgeFactoryHealth")

    def run_pre_flight_check(
        self,
        ticker: str,
        market_data,
        regime_state: Optional[Dict] = None,
        last_regime_change: Optional[datetime] = None,
        pop_deviation_pct: Optional[float] = None,
    ) -> HealthStatus:
        alerts: List[str] = []

        # 1) Skew staleness check
        skew_last_update = None
        if hasattr(self.fetcher, "get_skew_last_update"):
            skew_last_update = self.fetcher.get_skew_last_update(ticker)

        if skew_last_update is None:
            if getattr(market_data, "skew", 0.0) == 0.0:
                alerts.append("SKEW_STALE: Skew missing or zero—default to conservative mode.")
        else:
            if datetime.utcnow() - skew_last_update > timedelta(hours=26):
                alerts.append("SKEW_STALE: Skew older than 26h—default to conservative mode.")

        # 2) Bid/ask spread sanity
        avg_spread = self._estimate_avg_spread(market_data)
        if avg_spread is not None and market_data.current_price:
            if avg_spread > (market_data.current_price * 0.05):
                alerts.append("LIQUIDITY_SHOCK: Option spreads too wide for reliable routing.")

        # 3) Hysteresis stuck detection
        if last_regime_change is not None:
            days_since_change = (datetime.utcnow() - last_regime_change).days
            if days_since_change >= 20:
                if market_data.iv_rank > 0.7 or market_data.realized_vol > 0.35:
                    alerts.append("REGIME_STUCK: Regime unchanged during high volatility.")

        # 4) PoP drift check (optional)
        if pop_deviation_pct is not None and pop_deviation_pct > 0.10:
            alerts.append("POP_DRIFT: PoP deviating >10% from historical performance.")

        is_healthy = len(alerts) == 0
        return HealthStatus(
            is_healthy=is_healthy,
            data_freshness="GREEN" if is_healthy else "YELLOW",
            logic_confidence=1.0 if is_healthy else 0.7,
            active_alerts=alerts,
        )

    def _estimate_avg_spread(self, market_data) -> Optional[float]:
        try:
            option_chain = market_data.option_chain
            if not option_chain:
                return None

            spreads = []
            for expiry in option_chain.values():
                for strike_data in expiry.values():
                    for side in ("call", "put"):
                        leg = strike_data.get(side, {})
                        bid = leg.get("bid")
                        ask = leg.get("ask")
                        if bid is None or ask is None:
                            continue
                        spread = float(ask) - float(bid)
                        if spread >= 0:
                            spreads.append(spread)

            if not spreads:
                return None
            return sum(spreads) / len(spreads)
        except Exception as e:
            self.logger.error(f"Error computing spread sanity: {e}")
            return None
