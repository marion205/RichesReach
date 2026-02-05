# options_risk_sizer.py
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple


# ============================================================================
# Data Models
# ============================================================================

@dataclass(frozen=True)
class Greeks:
    """
    Portfolio-level or trade-level Greeks.

    NOTE: Keep units consistent across your system.
    - If your valuation engine outputs greeks "per 1 contract", use that here.
    - If your system outputs greeks "per share", multiply appropriately before passing in.
    """
    delta: float = 0.0
    vega: float = 0.0
    theta: float = 0.0
    gamma: float = 0.0


@dataclass(frozen=True)
class PortfolioSnapshot:
    """
    Current portfolio risk state.
    - equity: account equity in dollars
    - greeks_total: aggregate greeks across all open positions
    - sector_exposure_pct: fraction (0..1) exposure by sector (risk-weighted or notional-weighted)
    - ticker_exposure_pct: optional fraction (0..1) exposure by ticker
    """
    equity: float
    greeks_total: Greeks
    sector_exposure_pct: Dict[str, float]
    ticker_exposure_pct: Optional[Dict[str, float]] = None


@dataclass(frozen=True)
class TradeCandidate:
    """
    Output of your Strategy Router / Valuation Engine (PER 1 CONTRACT).

    Required:
    - pop: probability of profit (0..1)
    - max_profit: max profit per contract in $
    - max_loss: max loss per contract in $ (positive)
    - greeks_per_contract: greeks for 1 contract
    - sector: e.g. "Tech"
    - ticker: e.g. "AAPL"

    Optional:
    - corr_to_portfolio: 0..1 (estimated correlation to portfolio PnL or dominant exposures)
    - edge_score: for reporting only (0..10 or 0..100)
    """
    pop: float
    max_profit: float
    max_loss: float
    greeks_per_contract: Greeks
    sector: str
    ticker: str
    corr_to_portfolio: float = 0.0
    edge_score: float = 0.0


@dataclass
class RiskCaps:
    """
    Hard caps + policy defaults.
    Tune these after you see real user PnL + tail behavior.
    """
    # Per-trade risk caps
    max_trade_risk_pct: float = 0.02        # 2% equity max risk per trade
    min_trade_risk_pct: float = 0.0025      # 0.25% equity min "meaningful" risk (optional)

    # Portfolio Greek caps (absolute)
    max_portfolio_abs_delta: float = 300.0
    max_portfolio_abs_vega: float = 800.0
    max_portfolio_abs_gamma: float = 80.0

    # Sector concentration caps
    sector_soft_cap_pct: float = 0.25       # penalize size above 25%
    sector_hard_cap_pct: float = 0.40       # block above 40%

    # Ticker concentration caps (optional)
    ticker_soft_cap_pct: float = 0.12
    ticker_hard_cap_pct: float = 0.20

    # Correlation caps (0..1)
    corr_soft: float = 0.50
    corr_hard: float = 0.85

    # Basic sanity
    min_max_loss_dollars: float = 25.0      # reject if max_loss per contract is too small/invalid


@dataclass
class KellyConfig:
    """
    Fractional Kelly controls.
    - kelly_fraction: typically 0.10 to 0.25
    - kelly_cap_pct: additional cap on Kelly fraction (before per-trade hard caps)
    """
    kelly_fraction: float = 0.10
    kelly_cap_pct: float = 0.05            # never allocate >5% equity by Kelly alone


@dataclass
class SizeDecision:
    contracts: int
    risk_amount: float
    kelly_full: float
    kelly_fractional: float
    risk_budget_trade_cap: float
    limiting_factors: Dict[str, str]
    warnings: Tuple[str, ...]
    risk_report: Dict


# ============================================================================
# Risk Sizer
# ============================================================================

class OptionsRiskSizer:
    """
    Fractional Kelly + Portfolio Guardrails.

    Output is deterministic and UI-friendly:
      - recommended contracts
      - risk amount
      - what limited size (Kelly, Greek caps, concentration, correlation, experience gating)
    """

    def __init__(self, caps: RiskCaps | None = None, kelly: KellyConfig | None = None):
        self.caps = caps or RiskCaps()
        self.kelly = kelly or KellyConfig()

    # ---------- Public API ----------

    def size_trade(
        self,
        portfolio: PortfolioSnapshot,
        trade: TradeCandidate,
        *,
        user_experience_level: str = "basic",   # basic | intermediate | pro
        allow_zero_contracts: bool = True
    ) -> SizeDecision:
        limiting: Dict[str, str] = {}
        warnings = []

        # Basic validation
        if portfolio.equity <= 0:
            return self._reject("Invalid account equity.", portfolio, trade)

        if trade.max_loss <= 0 or trade.max_loss < self.caps.min_max_loss_dollars:
            return self._reject("Invalid/too-small max_loss per contract.", portfolio, trade)

        p = self._clamp(trade.pop, 0.0, 1.0)
        if p <= 0.0:
            return self._reject("PoP <= 0 (no edge).", portfolio, trade)

        b = abs(trade.max_profit / trade.max_loss) if trade.max_loss != 0 else 0.0
        if b <= 0.0:
            return self._reject("Win/Loss ratio <= 0.", portfolio, trade)

        # 1) Full Kelly
        kelly_full = self._kelly_fraction(p, b)
        if kelly_full <= 0:
            return self._reject("Kelly <= 0 (negative EV or too low PoP).", portfolio, trade)

        # 2) Fractional Kelly + cap
        kelly_fractional = max(0.0, kelly_full * self.kelly.kelly_fraction)
        kelly_fractional = min(kelly_fractional, self.kelly.kelly_cap_pct)

        # 3) Dollar risk from Kelly
        kelly_dollar_risk = portfolio.equity * kelly_fractional

        # 4) Per-trade hard cap + (optional) minimum floor
        trade_risk_cap = portfolio.equity * self.caps.max_trade_risk_pct
        min_risk_floor = portfolio.equity * self.caps.min_trade_risk_pct

        target_risk = min(kelly_dollar_risk, trade_risk_cap)

        if target_risk < min_risk_floor:
            warnings.append(
                f"Kelly suggests small risk (${target_risk:.2f}) below minimum floor "
                f"(${min_risk_floor:.2f})."
            )

        base_contracts = math.floor(target_risk / trade.max_loss)
        if base_contracts <= 0:
            if allow_zero_contracts:
                return self._reject("Sizer recommends 0 contracts under risk caps.", portfolio, trade)
            base_contracts = 1

        limiting["kelly"] = f"Base contracts from fractional Kelly risk: {base_contracts}"

        # 5) Greek caps limiter
        contracts_greek_limited, greek_reason = self._limit_by_greeks(
            portfolio_greeks=portfolio.greeks_total,
            trade_greeks=trade.greeks_per_contract,
            desired_contracts=base_contracts
        )
        if contracts_greek_limited < base_contracts:
            limiting["greeks"] = greek_reason

        contracts = contracts_greek_limited

        # 6) Concentration / correlation penalties (and blocks)
        sector_penalty, sector_msg, sector_block = self._sector_penalty(portfolio, trade)
        if sector_block:
            return self._reject(sector_msg, portfolio, trade)

        ticker_penalty, ticker_msg, ticker_block = self._ticker_penalty(portfolio, trade)
        if ticker_block:
            return self._reject(ticker_msg, portfolio, trade)

        corr_penalty, corr_msg, corr_block = self._correlation_penalty(trade.corr_to_portfolio)
        if corr_block:
            return self._reject(corr_msg, portfolio, trade)

        combined_penalty = sector_penalty * ticker_penalty * corr_penalty
        if combined_penalty < 1.0:
            limiting["concentration"] = (
                f"Penalties: sector={sector_penalty:.2f}, ticker={ticker_penalty:.2f}, corr={corr_penalty:.2f} "
                f"(combined={combined_penalty:.2f})"
            )

        penalized_contracts = math.floor(contracts * combined_penalty)

        # Experience gating (optional)
        exp_penalty, exp_msg = self._experience_penalty(user_experience_level, trade)
        if exp_penalty < 1.0:
            limiting["experience"] = exp_msg
            penalized_contracts = math.floor(penalized_contracts * exp_penalty)

        if penalized_contracts <= 0:
            if allow_zero_contracts:
                return self._reject("After guardrails/penalties, recommended size is 0 contracts.", portfolio, trade)
            penalized_contracts = 1

        contracts = penalized_contracts

        # Final risk amount
        risk_amount = contracts * trade.max_loss

        # Final safety clamp: should never exceed trade_risk_cap
        if risk_amount > trade_risk_cap + 1e-9:
            contracts = max(0, math.floor(trade_risk_cap / trade.max_loss))
            risk_amount = contracts * trade.max_loss
            limiting["hard_cap"] = "Clamped to max_trade_risk_pct"

        report = self._build_risk_report(
            portfolio=portfolio,
            trade=trade,
            contracts=contracts,
            kelly_full=kelly_full,
            kelly_fractional=kelly_fractional,
            base_contracts=base_contracts,
            penalties={
                "sector_penalty": sector_penalty,
                "ticker_penalty": ticker_penalty,
                "corr_penalty": corr_penalty,
                "experience_penalty": exp_penalty,
            },
            messages={
                "sector_msg": sector_msg,
                "ticker_msg": ticker_msg,
                "corr_msg": corr_msg,
                "experience_msg": exp_msg,
                "edge_score": str(trade.edge_score),
            },
            risk_amount=risk_amount,
            trade_risk_cap=trade_risk_cap,
        )

        return SizeDecision(
            contracts=contracts,
            risk_amount=risk_amount,
            kelly_full=kelly_full,
            kelly_fractional=kelly_fractional,
            risk_budget_trade_cap=trade_risk_cap,
            limiting_factors=limiting,
            warnings=tuple(warnings),
            risk_report=report,
        )

    # ---------- Core math ----------

    @staticmethod
    def _kelly_fraction(p: float, b: float) -> float:
        """
        Kelly for asymmetric win/loss:
          f* = (p*(b+1) - 1) / b
        p = probability of win
        b = win/loss ratio (profit/loss)
        """
        if b <= 0:
            return 0.0
        return (p * (b + 1.0) - 1.0) / b

    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, x))

    # ---------- Guardrails ----------

    def _limit_by_greeks(
        self,
        portfolio_greeks: Greeks,
        trade_greeks: Greeks,
        desired_contracts: int
    ) -> Tuple[int, str]:
        """
        Find max contracts allowed by Greek caps:
          |G_port + n*G_trade| <= cap_abs
        """
        caps = self.caps

        def max_n(current: float, per: float, cap_abs: float) -> int:
            if per == 0:
                return desired_contracts

            # Solve bounds:
            # -cap_abs <= current + n*per <= cap_abs
            upper = (cap_abs - current) / per
            lower = (-cap_abs - current) / per
            lo = math.ceil(min(lower, upper))
            hi = math.floor(max(lower, upper))

            lo = max(lo, 0)
            if hi < lo:
                return 0
            return min(desired_contracts, hi)

        n_delta = max_n(portfolio_greeks.delta, trade_greeks.delta, caps.max_portfolio_abs_delta)
        n_vega = max_n(portfolio_greeks.vega, trade_greeks.vega, caps.max_portfolio_abs_vega)
        n_gamma = max_n(portfolio_greeks.gamma, trade_greeks.gamma, caps.max_portfolio_abs_gamma)

        allowed = min(desired_contracts, n_delta, n_vega, n_gamma)

        if allowed < desired_contracts:
            return allowed, f"Limited by Greek caps: allowed={allowed} (delta={n_delta}, vega={n_vega}, gamma={n_gamma})"
        return desired_contracts, "Within Greek caps"

    def _sector_penalty(self, portfolio: PortfolioSnapshot, trade: TradeCandidate) -> Tuple[float, str, bool]:
        caps = self.caps
        current = portfolio.sector_exposure_pct.get(trade.sector, 0.0)

        if current >= caps.sector_hard_cap_pct:
            return 0.0, f"Blocked: sector {trade.sector} at {current:.0%} (>= {caps.sector_hard_cap_pct:.0%}).", True

        if current <= caps.sector_soft_cap_pct:
            return 1.0, f"Sector {trade.sector} exposure {current:.0%} (no penalty).", False

        t = (current - caps.sector_soft_cap_pct) / (caps.sector_hard_cap_pct - caps.sector_soft_cap_pct)
        penalty = max(0.5, 1.0 - 0.5 * t)
        return penalty, f"Sector {trade.sector} exposure {current:.0%} (penalty {penalty:.2f}).", False

    def _ticker_penalty(self, portfolio: PortfolioSnapshot, trade: TradeCandidate) -> Tuple[float, str, bool]:
        caps = self.caps
        if not portfolio.ticker_exposure_pct:
            return 1.0, "Ticker exposure unavailable (no penalty).", False

        current = portfolio.ticker_exposure_pct.get(trade.ticker, 0.0)

        if current >= caps.ticker_hard_cap_pct:
            return 0.0, f"Blocked: ticker {trade.ticker} at {current:.0%} (>= {caps.ticker_hard_cap_pct:.0%}).", True

        if current <= caps.ticker_soft_cap_pct:
            return 1.0, f"Ticker {trade.ticker} exposure {current:.0%} (no penalty).", False

        t = (current - caps.ticker_soft_cap_pct) / (caps.ticker_hard_cap_pct - caps.ticker_soft_cap_pct)
        penalty = max(0.6, 1.0 - 0.4 * t)
        return penalty, f"Ticker {trade.ticker} exposure {current:.0%} (penalty {penalty:.2f}).", False

    def _correlation_penalty(self, corr: float) -> Tuple[float, str, bool]:
        caps = self.caps
        c = self._clamp(corr, 0.0, 1.0)

        if c >= caps.corr_hard:
            return 0.0, f"Blocked: correlation {c:.2f} (>= {caps.corr_hard:.2f}).", True

        if c <= caps.corr_soft:
            return 1.0, f"Correlation {c:.2f} (no penalty).", False

        t = (c - caps.corr_soft) / (caps.corr_hard - caps.corr_soft)
        penalty = max(0.5, 1.0 - 0.5 * t)
        return penalty, f"Correlation {c:.2f} (penalty {penalty:.2f}).", False

    def _experience_penalty(self, level: str, trade: TradeCandidate) -> Tuple[float, str]:
        """
        Optional: reduce size for users who can't actively manage high gamma/vega trades.
        Replace with your Router's complexity tiers later.
        """
        lvl = (level or "basic").lower()
        g = trade.greeks_per_contract

        if lvl == "pro":
            return 1.0, "Pro tier (no experience penalty)."

        gamma_risky = abs(g.gamma) > 2.0
        vega_risky = abs(g.vega) > 25.0

        if lvl == "basic" and (gamma_risky or vega_risky):
            return 0.6, "Basic tier: reduced size due to higher gamma/vega management needs."
        if lvl == "intermediate" and (gamma_risky or vega_risky):
            return 0.8, "Intermediate tier: slight reduction due to elevated gamma/vega."
        return 1.0, "Experience level compatible (no penalty)."

    # ---------- Reporting / Reject ----------

    def _reject(self, reason: str, portfolio: PortfolioSnapshot, trade: TradeCandidate) -> SizeDecision:
        report = self._build_risk_report(
            portfolio=portfolio,
            trade=trade,
            contracts=0,
            kelly_full=0.0,
            kelly_fractional=0.0,
            base_contracts=0,
            penalties={},
            messages={"reject_reason": reason},
            risk_amount=0.0,
            trade_risk_cap=(portfolio.equity * self.caps.max_trade_risk_pct) if portfolio.equity > 0 else 0.0,
        )
        return SizeDecision(
            contracts=0,
            risk_amount=0.0,
            kelly_full=0.0,
            kelly_fractional=0.0,
            risk_budget_trade_cap=report.get("trade_caps", {}).get("trade_risk_cap", 0.0),
            limiting_factors={"rejected": reason},
            warnings=(reason,),
            risk_report=report,
        )

    def _build_risk_report(
        self,
        *,
        portfolio: PortfolioSnapshot,
        trade: TradeCandidate,
        contracts: int,
        kelly_full: float,
        kelly_fractional: float,
        base_contracts: int,
        penalties: Dict[str, float],
        messages: Dict[str, str],
        risk_amount: float,
        trade_risk_cap: float
    ) -> Dict:
        g0 = portfolio.greeks_total
        gt = trade.greeks_per_contract

        g_after = Greeks(
            delta=g0.delta + contracts * gt.delta,
            vega=g0.vega + contracts * gt.vega,
            theta=g0.theta + contracts * gt.theta,
            gamma=g0.gamma + contracts * gt.gamma,
        )

        return {
            "summary": {
                "ticker": trade.ticker,
                "sector": trade.sector,
                "contracts": contracts,
                "risk_amount": risk_amount,
                "risk_pct_equity": (risk_amount / portfolio.equity) if portfolio.equity else 0.0,
            },
            "kelly": {
                "pop": trade.pop,
                "b_win_loss": (trade.max_profit / trade.max_loss) if trade.max_loss else 0.0,
                "kelly_full": kelly_full,
                "kelly_fractional": kelly_fractional,
                "base_contracts_from_kelly": base_contracts,
            },
            "trade_economics": {
                "max_profit_per_contract": trade.max_profit,
                "max_loss_per_contract": trade.max_loss,
                "max_profit_total": contracts * trade.max_profit,
                "max_loss_total": contracts * trade.max_loss,
            },
            "trade_caps": {
                "trade_risk_cap": trade_risk_cap,
                "max_trade_risk_pct": self.caps.max_trade_risk_pct,
                "min_trade_risk_pct": self.caps.min_trade_risk_pct,
            },
            "portfolio_greeks": {
                "before": asdict(g0),
                "trade_per_contract": asdict(gt),
                "after": asdict(g_after),
                "caps": {
                    "max_portfolio_abs_delta": self.caps.max_portfolio_abs_delta,
                    "max_portfolio_abs_vega": self.caps.max_portfolio_abs_vega,
                    "max_portfolio_abs_gamma": self.caps.max_portfolio_abs_gamma,
                },
            },
            "concentration": {
                "sector_exposure_current": portfolio.sector_exposure_pct.get(trade.sector, 0.0),
                "sector_soft_cap": self.caps.sector_soft_cap_pct,
                "sector_hard_cap": self.caps.sector_hard_cap_pct,
                "ticker_exposure_current": (portfolio.ticker_exposure_pct or {}).get(trade.ticker, 0.0) if portfolio.ticker_exposure_pct else None,
                "ticker_soft_cap": self.caps.ticker_soft_cap_pct,
                "ticker_hard_cap": self.caps.ticker_hard_cap_pct,
                "corr_to_portfolio": trade.corr_to_portfolio,
                "corr_soft": self.caps.corr_soft,
                "corr_hard": self.caps.corr_hard,
            },
            "penalties": penalties,
            "messages": messages,
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    sizer = OptionsRiskSizer()

    portfolio = PortfolioSnapshot(
        equity=25_000,
        greeks_total=Greeks(delta=120, vega=-200, theta=35, gamma=10),
        sector_exposure_pct={"Tech": 0.28, "Financials": 0.10},
        ticker_exposure_pct={"SPY": 0.08, "QQQ": 0.14},
    )

    trade = TradeCandidate(
        pop=0.66,
        max_profit=160.0,
        max_loss=100.0,  # Changed: favorable risk/reward
        greeks_per_contract=Greeks(delta=8, vega=18, theta=2.2, gamma=0.7),
        sector="Tech",
        ticker="QQQ",
        corr_to_portfolio=0.62,
        edge_score=8.4,
    )

    decision = sizer.size_trade(portfolio, trade, user_experience_level="basic")
    print("Contracts:", decision.contracts)
    print("Risk $:", decision.risk_amount)
    print("Limiting factors:", decision.limiting_factors)
    print("Warnings:", decision.warnings)
    print("Risk report summary:", decision.risk_report["summary"])
