"""
Risk Scoring Service

Provides a deterministic risk audit for DeFi pools using:
- Calmar ratio (return / max drawdown)
- TVL stability (volatility of TVL)
- Optional integrity checks (ERC-4626 compliance, issuer scores)

Designed to plug into defi_validation_service as a "Risk Guardian".
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
import statistics


class Recommendation(str, Enum):
    HOLD = "HOLD"
    REBALANCE = "REBALANCE"
    EXIT = "EXIT"


@dataclass(frozen=True)
class RiskConfig:
    # Calmar thresholds
    min_calmar_hold: float = 1.0
    min_calmar_rebalance: float = 0.6

    # Drawdown thresholds
    max_drawdown_hold: float = 0.07
    max_drawdown_rebalance: float = 0.12

    # TVL stability thresholds (0..1)
    min_tvl_stability_hold: float = 0.70
    min_tvl_stability_rebalance: float = 0.50

    # Weighting for overall score
    w_calmar: float = 0.45
    w_drawdown: float = 0.30
    w_tvl_stability: float = 0.25


@dataclass(frozen=True)
class FinancialIntegrity:
    altman_z_score: Optional[float]
    beneish_m_score: Optional[float]
    is_erc4626_compliant: bool


@dataclass(frozen=True)
class RiskMetrics:
    calmar_ratio: float
    max_drawdown: float
    volatility: float
    tvl_stability: float


@dataclass(frozen=True)
class VaultAuditResult:
    vault_address: str
    protocol: str
    symbol: str
    apy: float
    integrity: FinancialIntegrity
    risk: RiskMetrics
    overall_score: float
    recommendation: Recommendation
    explanation: str


def pct_change(series: List[float]) -> List[float]:
    if len(series) < 2:
        return []
    out: List[float] = []
    for i in range(1, len(series)):
        prev = series[i - 1]
        cur = series[i]
        if prev == 0:
            continue
        out.append((cur / prev) - 1.0)
    return out


def max_drawdown(nav: List[float]) -> float:
    if not nav:
        return 0.0
    peak = nav[0]
    max_dd = 0.0
    for x in nav:
        if x > peak:
            peak = x
        dd = (peak - x) / peak if peak else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def annualized_return_from_nav(nav: List[float], periods_per_year: int = 365) -> float:
    if len(nav) < 2 or nav[0] <= 0:
        return 0.0
    total_return = (nav[-1] / nav[0]) - 1.0
    n_periods = len(nav) - 1
    try:
        return (1.0 + total_return) ** (periods_per_year / n_periods) - 1.0
    except Exception:
        return 0.0


def calmar_ratio(nav: List[float], periods_per_year: int = 365) -> float:
    dd = max_drawdown(nav)
    if dd <= 0:
        return 10.0
    ann_ret = annualized_return_from_nav(nav, periods_per_year=periods_per_year)
    return ann_ret / dd


def volatility(returns: List[float]) -> float:
    if len(returns) < 2:
        return 0.0
    return statistics.pstdev(returns)


def tvl_stability_score(tvl_series: List[float]) -> float:
    tvl = [x for x in tvl_series if x is not None and x > 0]
    if len(tvl) < 3:
        return 0.5
    mean = statistics.mean(tvl)
    std = statistics.pstdev(tvl)
    if mean <= 0:
        return 0.0
    cov = std / mean
    score = max(0.0, min(1.0, 1.0 - (cov / 0.50)))
    return score


def normalize_score_0_100(value: float, low: float, high: float) -> float:
    if high <= low:
        return 50.0
    x = (value - low) / (high - low)
    x = max(0.0, min(1.0, x))
    return 100.0 * x


def overall_score(cfg: RiskConfig, calmar: float, max_dd: float, tvl_stability: float) -> float:
    calmar_score = normalize_score_0_100(calmar, low=0.0, high=3.0)
    dd_score = normalize_score_0_100(1.0 - max_dd, low=1.0 - 0.25, high=1.0)
    tvl_score = 100.0 * max(0.0, min(1.0, tvl_stability))

    total = (
        cfg.w_calmar * calmar_score +
        cfg.w_drawdown * dd_score +
        cfg.w_tvl_stability * tvl_score
    )
    return round(total, 2)


def recommendation(cfg: RiskConfig, calmar: float, max_dd: float, tvl_stability: float) -> Tuple[Recommendation, str]:
    if (
        calmar < cfg.min_calmar_rebalance
        or max_dd > cfg.max_drawdown_rebalance
        or tvl_stability < cfg.min_tvl_stability_rebalance
    ):
        return Recommendation.EXIT, "Risk fell below safe thresholds."

    if (
        calmar < cfg.min_calmar_hold
        or max_dd > cfg.max_drawdown_hold
        or tvl_stability < cfg.min_tvl_stability_hold
    ):
        return Recommendation.REBALANCE, "Performance or stability suggests a safer alternative."

    return Recommendation.HOLD, "Vault meets Fortress-grade thresholds."


def build_nav_from_apy_series(apy_series: List[float], periods_per_year: int = 365) -> List[float]:
    if not apy_series:
        return []
    nav = [1.0]
    for apy in apy_series:
        daily_return = max(0.0, apy) / 100.0 / periods_per_year
        nav.append(nav[-1] * (1.0 + daily_return))
    return nav


def audit_vault(
    *,
    vault_address: str,
    protocol: str,
    symbol: str,
    apy: float,
    nav_history: List[float],
    tvl_history: List[float],
    is_erc4626_compliant: bool,
    altman_z_score: Optional[float] = None,
    beneish_m_score: Optional[float] = None,
    cfg: Optional[RiskConfig] = None,
) -> VaultAuditResult:
    cfg = cfg or RiskConfig()

    returns = pct_change(nav_history)
    max_dd = max_drawdown(nav_history)
    calmar = calmar_ratio(nav_history)
    vol = volatility(returns)
    tvl_stability = tvl_stability_score(tvl_history)

    overall = overall_score(cfg, calmar=calmar, max_dd=max_dd, tvl_stability=tvl_stability)
    rec, rec_reason = recommendation(cfg, calmar=calmar, max_dd=max_dd, tvl_stability=tvl_stability)

    explanation = (
        f"{rec_reason} Calmar={calmar:.2f}, "
        f"MaxDD={max_dd:.2%}, TVLStability={tvl_stability:.2f}, "
        f"Overall={overall:.1f}."
    )

    return VaultAuditResult(
        vault_address=vault_address,
        protocol=protocol,
        symbol=symbol,
        apy=apy,
        integrity=FinancialIntegrity(
            altman_z_score=altman_z_score,
            beneish_m_score=beneish_m_score,
            is_erc4626_compliant=is_erc4626_compliant,
        ),
        risk=RiskMetrics(
            calmar_ratio=calmar,
            max_drawdown=max_dd,
            volatility=vol,
            tvl_stability=tvl_stability,
        ),
        overall_score=overall,
        recommendation=rec,
        explanation=explanation,
    )
