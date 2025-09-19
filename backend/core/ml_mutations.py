# core/ml_mutations.py
"""
Institutional-Grade ML Mutations for Portfolio Recommendations
- Point-in-time data discipline
- Constrained optimization (cvxpy if available)
- Transaction-cost & turnover awareness
- Risk metrics (vol, VaR/CVaR), audit trail, idempotency
"""
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import graphene
from graphql import GraphQLError
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from .models import (
    AIPortfolioRecommendation,
    StockRecommendation,
    Stock,
    IncomeProfile,
)

# Optional, used if available
try:
    from .models import StockPriceSnapshot  # point-in-time OHLCV/corporate-action-adjusted
except Exception:
    StockPriceSnapshot = None  # Fallback safely if your project doesn't include it

# Optional deps (robust optimizer)
try:
    import numpy as np
    import cvxpy as cp
except Exception:
    np = None
    cp = None

# Services
from .ai_service import AIService
from .auth_utils import RateLimiter, get_ml_mutation_context
from .ml_settings import MLServiceStatus

logger = logging.getLogger(__name__)
User = get_user_model()


# ---------- GraphQL Types & Inputs ----------

class MarketRegimeEnum(graphene.Enum):
    BULL = "bull"
    BEAR = "bear"
    VOLATILE = "volatile"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


class OptimizationConstraintsInput(graphene.InputObjectType):
    max_weight_per_name = graphene.Float(default_value=0.10)  # 10%
    max_sector_weight = graphene.Float(default_value=0.30)    # 30%
    max_turnover = graphene.Float(default_value=0.25)         # 25% of NAV per rebalance
    min_liquidity_score = graphene.Float(default_value=0.0)
    target_beta = graphene.Float(default_value=None)          # optional
    risk_aversion = graphene.Float(default_value=5.0)         # lambda in ER - λ*Risk
    cost_aversion = graphene.Float(default_value=1.0)         # γ for t-cost penalty
    cvar_confidence = graphene.Float(default_value=0.95)      # CVaR level
    long_only = graphene.Boolean(default_value=True)


class RiskMetricsType(graphene.ObjectType):
    volatility = graphene.Float()
    var95 = graphene.Float()
    cvar95 = graphene.Float()
    beta = graphene.Float()
    tracking_error = graphene.Float()
    factor_exposures = graphene.JSONString()
    constraint_report = graphene.JSONString()


class MLPortfolioRecommendationType(DjangoObjectType):
    """Enhanced AI Portfolio Recommendation with ML insights and audit metadata"""
    ml_confidence = graphene.Float()
    ml_market_regime = graphene.String()
    ml_expected_return_range = graphene.String()
    ml_risk_score = graphene.Float()
    ml_optimization_method = graphene.String()
    market_conditions = graphene.JSONString()
    user_profile_analysis = graphene.JSONString()
    audit_blob = graphene.JSONString()

    class Meta:
        model = AIPortfolioRecommendation
        fields = '__all__'


# ---------- Utility / Domain Helpers ----------

@dataclass
class UniverseItem:
    id: int
    symbol: str
    name: str
    sector: Optional[str]
    price: float
    liquidity_score: float  # proxy from ADV/turnover/etc.


def _now_iso() -> str:
    return timezone.now().isoformat()


def _sha256(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _as_of_date(arg: Optional[date]) -> date:
    return arg or timezone.now().date()


def _get_prev_weights(user: User) -> Dict[str, float]:
    """
    Retrieve previous portfolio weights for turnover control.
    Implement to pull last saved recommendation weights or live portfolio.
    """
    try:
        rec = (AIPortfolioRecommendation.objects
               .filter(user=user)
               .order_by('-created_at')
               .first())
        if not rec or not rec.portfolio_allocation:
            return {}
        alloc = rec.portfolio_allocation  # expected dict like {"AAPL": 0.05, ...}
        # Normalize if needed
        total = sum(alloc.values()) or 1.0
        return {k: float(v) / total for k, v in alloc.items()}
    except Exception:
        return {}


def _estimate_tcost(weights_new: Dict[str, float],
                    weights_prev: Dict[str, float],
                    spreads: Dict[str, float],
                    impacts: Dict[str, float]) -> float:
    """
    Simple linear + square-root market impact model.
    tcost ≈ Σ (|Δw| * spread + sqrt(|Δw|) * impact)
    """
    cost = 0.0
    for sym, w_new in weights_new.items():
        w_old = weights_prev.get(sym, 0.0)
        dw = abs(w_new - w_old)
        spread = spreads.get(sym, 0.0005)   # 5 bps default
        impact = impacts.get(sym, 0.0015)   # 15 bps default (square-root)
        cost += dw * spread + (dw ** 0.5) * impact
    # Include names we are exiting completely
    for sym, w_old in weights_prev.items():
        if sym not in weights_new:
            dw = abs(0.0 - w_old)
            spread = spreads.get(sym, 0.0005)
            impact = impacts.get(sym, 0.0015)
            cost += dw * spread + (dw ** 0.5) * impact
    return float(cost)


def _parametric_var_cvar(mu: float, sigma: float, z: float = 1.65) -> Tuple[float, float]:
    """
    Simple Normal VaR/CVaR estimation for 95% (z≈1.65).
    VaR ≈ -(μ - zσ), CVaR ≈ -(μ - σ * φ(z)/(1-α)), where φ is pdf at z.
    Returns positive numbers for loss magnitudes.
    """
    try:
        # Avoid SciPy dependency; use closed forms
        import math
        phi = (1.0 / (math.sqrt(2.0 * math.pi))) * math.exp(-0.5 * z * z)
        alpha = 0.95
        var = max(0.0, -(mu - z * sigma))
        cvar = max(0.0, -(mu - sigma * (phi / (1 - alpha))))
        return float(var), float(cvar)
    except Exception:
        return max(0.0, -(mu - z * sigma)), max(0.0, -(mu - 1.8 * sigma))


def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
    s = sum(max(0.0, x) for x in weights.values())
    if s <= 0:
        return {}
    return {k: max(0.0, v) / s for k, v in weights.items()}


# ---------- Data Access (Point-in-time) ----------

def fetch_universe_pti(
    symbols: Optional[List[str]],
    as_of: date,
    min_liquidity: float,
) -> List[UniverseItem]:
    """
    Point-in-time universe with liquidity proxy. Falls back to live Stock if no snapshots exist.
    """
    universe: List[UniverseItem] = []

    if StockPriceSnapshot:
        qs = StockPriceSnapshot.objects.filter(as_of__lte=as_of)
        if symbols:
            qs = qs.filter(symbol__in=[s.upper() for s in symbols])
        # Grab latest snapshot per symbol as_of
        qs = (qs.order_by('symbol', '-as_of')
                .distinct('symbol')
                .values('stock_id', 'symbol', 'company_name', 'sector', 'close', 'adv_score'))
        for row in qs:
            liq = float(row.get('adv_score') or 0.0)
            if liq < min_liquidity:
                continue
            universe.append(UniverseItem(
                id=row['stock_id'],
                symbol=row['symbol'],
                name=row['company_name'],
                sector=row.get('sector'),
                price=float(row.get('close') or 0.0),
                liquidity_score=liq,
            ))
    else:
        # Fallback: live table (NOT point-in-time, but allows service continuity)
        qs = Stock.objects.all()
        if symbols:
            qs = qs.filter(symbol__in=[s.upper() for s in symbols])
        qs = qs.values('id', 'symbol', 'company_name', 'sector', 'current_price', 'avg_daily_dollar_volume')
        for row in qs:
            liq = float(row.get('avg_daily_dollar_volume') or 0.0)
            if liq < min_liquidity:
                continue
            price = float(row.get('current_price') or 0.0)
            if price <= 0:
                continue
            universe.append(UniverseItem(
                id=row['id'],
                symbol=row['symbol'],
                name=row['company_name'],
                sector=row.get('sector'),
                price=price,
                liquidity_score=liq,
            ))

    return universe


# ---------- Mutation ----------

class GenerateInstitutionalPortfolioRecommendation(graphene.Mutation):
    """
    Institutional-grade ML portfolio construction with constraints, costs, and audit.
    """
    class Arguments:
        as_of = graphene.Date(required=False)
        universe = graphene.List(graphene.String, required=False)  # optional symbol filter
        constraints = OptimizationConstraintsInput(required=False)
        model_version = graphene.String(required=True)
        feature_view_version = graphene.String(required=True)
        idempotency_key = graphene.String(required=False)
        include_market_analysis = graphene.Boolean(required=True, default_value=True)
        dry_run = graphene.Boolean(required=False, default_value=False)

    success = graphene.Boolean()
    message = graphene.String()
    recommendation = graphene.Field(MLPortfolioRecommendationType)
    risk_metrics = graphene.Field(RiskMetricsType)
    optimizer_status = graphene.String()
    audit_id = graphene.String()

    @staticmethod
    def _idempotency_cache_key(user_id: int, idem_key: str) -> str:
        return f"ml_rec_idem:{user_id}:{idem_key}"

    @transaction.atomic
    def mutate(
        self,
        info,
        model_version: str,
        feature_view_version: str,
        as_of: Optional[date] = None,
        universe: Optional[List[str]] = None,
        constraints: Optional[OptimizationConstraintsInput] = None,
        idempotency_key: Optional[str] = None,
        include_market_analysis: bool = True,
        dry_run: bool = False,
    ):
        try:
            # Get ML mutation context with authentication
            context = get_ml_mutation_context(info)
            user = context['user']
            
            # Check permissions for institutional ML
            if not context['permissions']['institutional_ml']:
                return GenerateInstitutionalPortfolioRecommendation(
                    success=False, 
                    message="Premium subscription required for institutional ML features."
                )
            
            # Rate limiting
            limited, message, retry_after = RateLimiter.is_rate_limited(
                info.context, 'institutional_ml', 10, 1  # 10 requests per hour
            )
            if limited:
                return GenerateInstitutionalPortfolioRecommendation(
                    success=False, message=message
                )
            
            # Record attempt
            RateLimiter.record_attempt(info.context, 'institutional_ml', 1)
            
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return GenerateInstitutionalPortfolioRecommendation(
                success=False, message="Authentication failed."
            )


        # Idempotency: short-circuit on same inputs
        idem = idempotency_key or _sha256({
            "u": user.id,
            "model": model_version,
            "fv": feature_view_version,
            "universe": sorted(universe or []),
            "as_of": str(as_of or ""),
            "constraints": dict(constraints) if constraints else {},
        })
        cache_key = self._idempotency_cache_key(user.id, idem)
        cached = cache.get(cache_key)
        if cached:
            try:
                rec = AIPortfolioRecommendation.objects.get(id=cached)
                return GenerateInstitutionalPortfolioRecommendation(
                    success=True,
                    message="Returning idempotent recommendation.",
                    recommendation=rec,
                    risk_metrics=None,
                    optimizer_status="cache_hit",
                    audit_id=str(rec.id),
                )
            except Exception:
                pass  # cache drift; continue

        # User profile
        try:
            profile: IncomeProfile = user.incomeProfile
        except IncomeProfile.DoesNotExist:
            return GenerateInstitutionalPortfolioRecommendation(
                success=False, message="Create your income profile first."
            )

        ai = AIService()
        as_of_final = _as_of_date(as_of)

        # Universe (point-in-time, liquidity-filtered)
        min_liq = (constraints.min_liquidity_score if constraints else 0.0)
        uni = fetch_universe_pti(universe, as_of_final, min_liq)

        if len(uni) < 8:
            return GenerateInstitutionalPortfolioRecommendation(
                success=False, message="Universe too small after filters."
            )

        # ML scoring & expected return estimates (deterministic if seeded inside AIService)
        scored = ai.score_stocks_ml(
            [{"id": u.id, "symbol": u.symbol, "price": u.price, "sector": u.sector,
              "liquidity_score": u.liquidity_score} for u in uni],
            {
                "age": profile.age,
                "income_bracket": profile.income_bracket,
                "investment_goals": profile.investment_goals,
                "risk_tolerance": profile.risk_tolerance,
                "investment_horizon": profile.investment_horizon,
            }
        ) or []

        # Align scores to universe & build arrays
        id_by_sym = {u.symbol: u.id for u in uni}
        by_sym = {u.symbol: u for u in uni}
        symbols = [u.symbol for u in uni]
        mu_vec = []
        sector_by_sym = {}
        spreads = {}
        impacts = {}

        for u in uni:
            srow = next((s for s in scored if s.get("symbol") == u.symbol), None)
            exp_ret = float(srow.get("expected_return", 0.08)) if srow else 0.08  # 8% baseline annualized
            # Convert to per-period (assume annual -> per unit; optimizer is relative)
            mu_vec.append(exp_ret)
            sector_by_sym[u.symbol] = (u.sector or "Unknown")
            # Simple microstructure proxies (could be learned in AIService)
            spreads[u.symbol] = max(0.0002, min(0.0020, 1.0 / max(1e4, u.liquidity_score)))
            impacts[u.symbol] = max(0.0005, min(0.0040, 5.0 / max(1e6, u.liquidity_score)))

        # Risk model (covariance): from service if available else shrinkage diag
        cov = ai.get_factor_covariance(symbols=symbols, as_of=str(as_of_final)) or {}
        if np is not None and cov and "cov" in cov and cov["cov"]:
            Sigma = np.array(cov["cov"], dtype=float)
            # Guard: PSD enforcement (diagonal load)
            try:
                # add epsilon to diagonal if needed
                eps = max(1e-6, 1e-8 * float(np.trace(Sigma)))
                Sigma = Sigma + eps * np.eye(Sigma.shape[0])
            except Exception:
                pass
        elif np is not None:
            # Fallback: diag using volatility from AIService or heuristic 20%-40%
            vols = []
            for s in symbols:
                v = ai.get_symbol_volatility(s, as_of=str(as_of_final)) or 0.25
                vols.append(float(v))
            Sigma = np.diag(np.square(np.array(vols, dtype=float)))
        else:
            Sigma = None  # triggers heuristic optimizer

        # Previous weights for turnover control
        w_prev = _get_prev_weights(user)

        # Constraints
        c = constraints or OptimizationConstraintsInput()
        long_only = bool(c.long_only)
        max_w = float(c.max_weight_per_name or 0.10)
        max_sector = float(c.max_sector_weight or 0.30)
        max_turnover = float(c.max_turnover or 0.25)
        risk_lambda = float(c.risk_aversion or 5.0)
        cost_gamma = float(c.cost_aversion or 1.0)
        target_beta = c.target_beta

        # Optimizer
        optimizer_status = "heuristic"
        weights: Dict[str, float] = {}

        if np is not None and cp is not None and Sigma is not None:
            try:
                n = len(symbols)
                w = cp.Variable(n)

                mu = np.array(mu_vec, dtype=float)
                Sigma_cp = cp.psd_wrap(Sigma)

                # Objective: maximize mu·w - λ*wᵀΣw - γ*tcost(w, w_prev)
                quad_risk = cp.quad_form(w, Sigma_cp)

                # t-cost: use linearization via auxiliary variable u ≈ |w - w_prev|
                u = cp.Variable(n)
                w_prev_vec = np.array([w_prev.get(sym, 0.0) for sym in symbols], dtype=float)
                constraints_list = [
                    w >= 0.0 if long_only else w >= -0.10,  # allow modest shorts if needed
                    cp.sum(w) == 1.0,
                    u >= w - w_prev_vec,
                    u >= -(w - w_prev_vec),
                    cp.sum(u) <= max_turnover + 1e-9,
                    w <= max_w + 1e-9,
                ]

                # Sector caps
                if max_sector < 0.999:
                    sectors = list({sector_by_sym[s] for s in symbols})
                    for sec in sectors:
                        idx = [i for i, s in enumerate(symbols) if sector_by_sym[s] == sec]
                        if idx:
                            constraints_list.append(cp.sum(w[idx]) <= max_sector + 1e-9)

                # Optional beta target (requires service beta exposures)
                beta_vec = ai.get_symbol_beta_vector(symbols, as_of=str(as_of_final))  # list or None
                if target_beta is not None and beta_vec:
                    beta_vec = np.array(beta_vec, dtype=float)
                    constraints_list.append(beta_vec @ w <= float(target_beta) + 0.05)
                    constraints_list.append(beta_vec @ w >= max(0.0, float(target_beta) - 0.05))

                # Linearized transaction costs
                spreads_vec = np.array([spreads[s] for s in symbols], dtype=float)
                impacts_vec = np.array([impacts[s] for s in symbols], dtype=float)
                # Approximate sqrt(|Δw|) with piecewise-linear upper bound: use u and weights
                tcost = spreads_vec @ u + cp.sum(cp.sqrt(u) * impacts_vec)

                objective = cp.Maximize(mu @ w - risk_lambda * quad_risk - cost_gamma * tcost)
                prob = cp.Problem(objective, constraints_list)
                prob.solve(solver=cp.OSQP, warm_start=True, max_iter=20000)

                if w.value is not None and prob.status in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
                    raw = {symbols[i]: float(max(0.0, w.value[i])) for i in range(n)}
                    weights = _normalize(raw)
                    optimizer_status = f"cvxpy/{prob.status}"
                else:
                    optimizer_status = f"cvxpy_failed/{prob.status}"
            except Exception as e:
                logger.exception("Optimizer failed; falling back: %s", e)

        if not weights:
            # Heuristic fallback: rank by (μ / diag(Σ)) with caps + sector caps + turnover
            # Works without numpy/cvxpy
            pairs = []
            for sym, er in zip(symbols, mu_vec):
                risk = 0.05
                try:
                    if Sigma is not None and np is not None:
                        idx = symbols.index(sym)
                        risk = float(np.sqrt(max(1e-8, Sigma[idx, idx])))
                except Exception:
                    pass
                score = er / max(1e-4, risk)
                pairs.append((sym, score))

            pairs.sort(key=lambda x: x[1], reverse=True)
            alloc: Dict[str, float] = {}
            sector_usage: Dict[str, float] = {}

            for sym, _ in pairs:
                sec = sector_by_sym[sym]
                # Greedy add while respecting caps
                can_add = max_w
                if sector_usage.get(sec, 0.0) + can_add > max_sector:
                    can_add = max(0.0, max_sector - sector_usage.get(sec, 0.0))
                if can_add <= 0:
                    continue
                alloc[sym] = can_add
                sector_usage[sec] = sector_usage.get(sec, 0.0) + can_add
                if sum(alloc.values()) >= 1.0 - 1e-6:
                    break

            weights = _normalize(alloc)
            optimizer_status = optimizer_status or "heuristic"

        # Risk metrics (parametric)
        vol = 0.0
        te = None
        if np is not None and Sigma is not None and weights:
            w_vec = np.array([weights.get(s, 0.0) for s in symbols], dtype=float)
            vol = float(np.sqrt(max(1e-12, w_vec.T @ Sigma @ w_vec)))
        exp_return = float(sum(weights.get(s, 0.0) * mu for s, mu in zip(symbols, mu_vec)))
        var95, cvar95 = _parametric_var_cvar(exp_return, vol, z=1.65)

        # Transaction cost estimate
        tcost_est = _estimate_tcost(weights, w_prev, spreads, impacts)

        # Market analysis (cached by service)
        market_analysis = ai.get_enhanced_market_analysis() if include_market_analysis else {}
        regime = market_analysis.get('ml_regime_prediction', {}).get('regime', 'unknown')

        # Prepare persistence structures
        recommended_stocks = []
        for sym, wgt in sorted(weights.items(), key=lambda kv: kv[1], reverse=True):
            try:
                stock_obj = Stock.objects.get(id=id_by_sym[sym])
                recommended_stocks.append({
                    "symbol": sym,
                    "companyName": stock_obj.company_name,
                    "allocation": round(100.0 * wgt, 2),
                    "reasoning": f"ML score & optimizer selection (sector={stock_obj.sector or 'N/A'})",
                    "riskLevel": "Low" if vol < 0.15 else "Medium" if vol < 0.30 else "High",
                    "expectedReturn": round(100.0 * (next(
                        (s.get("expected_return", 0.08) for s in scored if s.get("symbol") == sym), 0.08
                    )), 2)
                })
            except Stock.DoesNotExist:
                continue

        # Risk assessment string (human-readable)
        constraint_report = {
            "max_weight_per_name": max_w,
            "max_sector_weight": max_sector,
            "max_turnover": max_turnover,
            "long_only": long_only,
            "beta_target": target_beta,
            "optimizer_status": optimizer_status,
        }
        risk_assessment = (
            f"Vol={vol:.4f} | VaR95={var95:.4f} | CVaR95={cvar95:.4f} | "
            f"TCost≈{tcost_est:.4f} | Regime={regime}"
        )

        # Portfolio allocation saved as {symbol: weight}
        allocation_dict = {sym: round(float(w), 6) for sym, w in weights.items()}

        # Audit blob (for reproducibility)
        audit_blob = {
            "idempotency_key": idem,
            "as_of": str(as_of_final),
            "model_version": model_version,
            "feature_view_version": feature_view_version,
            "universe_count": len(symbols),
            "inputs_hash": _sha256({
                "symbols": symbols,
                "mu": mu_vec,
                "cov_hash": _sha256(cov) if cov else None,
                "constraints": dict(constraints) if constraints else {},
            }),
            "prev_weights_nonzero": len([1 for v in w_prev.values() if v > 1e-6]),
            "optimizer_status": optimizer_status,
            "tcost_est": tcost_est,
            "created_at": _now_iso(),
        }

        if dry_run:
            return GenerateInstitutionalPortfolioRecommendation(
                success=True,
                message="Dry run successful.",
                recommendation=None,
                risk_metrics=RiskMetricsType(
                    volatility=vol,
                    var95=var95,
                    cvar95=cvar95,
                    beta=None,
                    tracking_error=te,
                    factor_exposures=cov.get("factors", {}) if isinstance(cov, dict) else {},
                    constraint_report=json.dumps(constraint_report),
                ),
                optimizer_status=optimizer_status,
                audit_id=None,
            )

        # Persist recommendation atomically
        rec = AIPortfolioRecommendation.objects.create(
            user=user,
            risk_profile="High" if vol > 0.30 else "Medium" if vol > 0.15 else "Low",
            portfolio_allocation=allocation_dict,
            recommended_stocks=recommended_stocks,
            expected_portfolio_return=round(100.0 * exp_return, 2),
            risk_assessment=risk_assessment,
        )
        # Store extended audit on flexible field names if your model allows extra JSON;
        # if not, keep it in risk_assessment or attach a separate Audit model.
        try:
            # If your model has a flexible JSONField like 'metadata' or similar, set it here.
            if hasattr(rec, "metadata"):
                rec.metadata = audit_blob
                rec.save(update_fields=["metadata"])
        except Exception:
            pass

        # Cache idempotency (short TTL; you can persist longer if desired)
        cache.set(cache_key, rec.id, timeout=15 * 60)

        # Return
        return GenerateInstitutionalPortfolioRecommendation(
            success=True,
            message="Institutional-grade ML recommendation generated.",
            recommendation=rec,
            risk_metrics=RiskMetricsType(
                volatility=vol,
                var95=var95,
                cvar95=cvar95,
                beta=None,
                tracking_error=te,
                factor_exposures=cov.get("factors", {}) if isinstance(cov, dict) else {},
                constraint_report=json.dumps(constraint_report),
            ),
            optimizer_status=optimizer_status,
            audit_id=str(rec.id),
        )


# ---------- Legacy mutations for backward compatibility ----------

class GenerateMLPortfolioRecommendation(graphene.Mutation):
    """
    Legacy ML portfolio recommendation (backward compatibility)
    """
    class Arguments:
        use_advanced_ml = graphene.Boolean(default_value=True)
        include_market_analysis = graphene.Boolean(default_value=True)
        include_risk_optimization = graphene.Boolean(default_value=True)
        idempotency_key = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()
    recommendation = graphene.Field(MLPortfolioRecommendationType)
    market_analysis = graphene.JSONString()
    ml_insights = graphene.JSONString()

    def mutate(self, info, **kwargs):
        # Delegate to institutional version with default constraints
        constraints = OptimizationConstraintsInput(
            max_weight_per_name=0.15,
            max_sector_weight=0.40,
            max_turnover=0.50,
            risk_aversion=3.0,
            cost_aversion=0.5,
        )
        
        result = GenerateInstitutionalPortfolioRecommendation().mutate(
            info,
            model_version="legacy_v1",
            feature_view_version="legacy_v1",
            constraints=constraints,
            **kwargs
        )
        
        # Transform response to legacy format
        if result.success:
            return GenerateMLPortfolioRecommendation(
                success=True,
                message=result.message,
                recommendation=result.recommendation,
                market_analysis={},
                ml_insights={"optimizer_status": result.optimizer_status}
            )
        else:
            return GenerateMLPortfolioRecommendation(
                success=False,
                message=result.message
            )


class GetMLMarketAnalysis(graphene.Mutation):
    """
    Get ML-enhanced market analysis (cached).
    """
    class Arguments:
        include_regime_prediction = graphene.Boolean(default_value=True)
        include_sector_analysis = graphene.Boolean(default_value=True)
        include_economic_indicators = graphene.Boolean(default_value=True)

    success = graphene.Boolean()
    message = graphene.String()
    market_analysis = graphene.JSONString()
    ml_predictions = graphene.JSONString()

    def mutate(self, info, **kwargs):
        try:
            # Get ML mutation context with authentication
            context = get_ml_mutation_context(info)
            
            # Check permissions for basic ML
            if not context['permissions']['basic_ml']:
                return GetMLMarketAnalysis(
                    success=False,
                    message="Authentication required for ML market analysis",
                )
            
            ai_service = AIService()
            analysis = ai_service.get_enhanced_market_analysis()
            
            preds = {}
            if kwargs.get('include_regime_prediction', True):
                preds["regime_prediction"] = analysis.get("ml_regime_prediction", {})
            if kwargs.get('include_sector_analysis', True):
                preds["sector_analysis"] = analysis.get("sector_performance", {})
            if kwargs.get('include_economic_indicators', True):
                preds["economic_indicators"] = analysis.get("economic_indicators", {})

            return GetMLMarketAnalysis(
                success=True,
                message="OK",
                market_analysis=analysis,
                ml_predictions=preds,
            )
        except GraphQLError:
            raise
        except Exception as e:
            logger.exception("Error getting ML market analysis")
            return GetMLMarketAnalysis(
                success=False,
                message=f"Error generating ML market analysis: {str(e)}"
            )


class GetMLServiceStatus(graphene.Mutation):
    """
    Get status of ML services.
    """
    success = graphene.Boolean()
    message = graphene.String()
    service_status = graphene.JSONString()

    def mutate(self, info):
        try:
            # Get ML mutation context with authentication
            context = get_ml_mutation_context(info)
            
            # Check permissions for basic ML
            if not context['permissions']['basic_ml']:
                return GetMLServiceStatus(
                    success=False,
                    message="Authentication required for ML service status",
                )
            
            # Get comprehensive ML service status
            status = MLServiceStatus.get_health_check()
            
            return GetMLServiceStatus(
                success=True,
                message="OK",
                service_status=status,
            )
        except GraphQLError:
            raise
        except Exception as e:
            logger.exception("Error getting ML service status")
            return GetMLServiceStatus(
                success=False,
                message=f"Error retrieving ML service status: {str(e)}",
            )


# ---------- Schema hook ----------

class Mutation(graphene.ObjectType):
    # Institutional-grade mutations
    generate_institutional_portfolio_recommendation = GenerateInstitutionalPortfolioRecommendation.Field()
    
    # Legacy mutations for backward compatibility
    generate_ml_portfolio_recommendation = GenerateMLPortfolioRecommendation.Field()
    get_ml_market_analysis = GetMLMarketAnalysis.Field()
    get_ml_service_status = GetMLServiceStatus.Field()
