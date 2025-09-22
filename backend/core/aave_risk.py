from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, getcontext
from typing import List, Tuple, Dict, Iterable, Literal

# Higher precision for USD math
getcontext().prec = 28

Tier = Literal['SAFE', 'WARN', 'TOP_UP', 'AT_RISK', 'LIQUIDATE']

@dataclass
class StressTestHFResult:
    shock: float
    collateral_usd: float
    debt_usd: float
    ltv_weighted: float
    liq_threshold_weighted: float
    available_borrow_usd: float
    health_factor: float
    tier: Tier

# ---------- internal helpers ----------

D = lambda x: x if isinstance(x, Decimal) else Decimal(str(x))

def _value_weighted(
    items: Iterable[Tuple[Decimal, Decimal]],  # (value_usd, weight)
) -> Decimal:
    """
    Compute value-weighted average of 'weight' with 'value_usd' weights.
    Returns 0 if total value is 0.
    """
    tot_val = Decimal("0")
    acc = Decimal("0")
    for v, w in items:
        v = D(v)
        w = D(w)
        if v <= 0:
            continue
        tot_val += v
        acc += v * w
    return acc / tot_val if tot_val > 0 else Decimal("0")

def _sum(values: Iterable[Tuple[Decimal, Decimal]]) -> Decimal:
    """
    Sum over (amount, price) -> Σ(amount * price)
    """
    s = Decimal("0")
    for amt, price in values:
        s += D(amt) * D(price)
    return s

# ---------- AAVE math primitives (exported) ----------

def total_collateral_usd(
    supplies: Iterable[Tuple[object, Decimal, bool]],  # (reserve, quantity, use_as_collateral)
    prices_usd: Dict[str, Decimal],
) -> Tuple[Decimal, Decimal]:
    """
    Returns (collateral_usd, weighted_liq_threshold).
    Only includes supplies with use_as_collateral=True and reserves that allow collateral.
    Weighted by collateral USD value.
    reserve fields used: reserve.can_be_collateral (bool), reserve.cryptocurrency.symbol (str),
                         reserve.liquidation_threshold (0..1 Decimal), reserve.ltv (0..1 Decimal)
    """
    rows: List[Tuple[Decimal, Decimal]] = []  # (value_usd, liq_threshold)
    coll_usd = Decimal("0")
    for reserve, qty, use_col in supplies:
        if not use_col or not getattr(reserve, "can_be_collateral", False):
            continue
        sym = reserve.cryptocurrency.symbol
        px = D(prices_usd.get(sym, 0))
        if px <= 0:
            continue
        val = D(qty) * px
        if val <= 0:
            continue
        coll_usd += val
        rows.append((val, D(getattr(reserve, "liquidation_threshold", 0))))

    w_liq = _value_weighted(rows) if rows else Decimal("0")
    return coll_usd, w_liq


def weighted_ltv(
    supplies: Iterable[Tuple[object, Decimal, bool]],
    prices_usd: Dict[str, Decimal],
) -> Decimal:
    """
    Value-weighted LTV across enabled collateral supplies.
    """
    rows: List[Tuple[Decimal, Decimal]] = []  # (value_usd, ltv)
    for reserve, qty, use_col in supplies:
        if not use_col or not getattr(reserve, "can_be_collateral", False):
            continue
        sym = reserve.cryptocurrency.symbol
        px = D(prices_usd.get(sym, 0))
        if px <= 0:
            continue
        val = D(qty) * px
        if val <= 0:
            continue
        rows.append((val, D(getattr(reserve, "ltv", 0))))
    return _value_weighted(rows) if rows else Decimal("0")


def total_debt_usd(
    borrows: Iterable[Tuple[object, Decimal]],  # (reserve, amount)
    prices_usd: Dict[str, Decimal],
) -> Decimal:
    """
    Sum of debts in USD across borrow positions.
    reserve fields used: reserve.cryptocurrency.symbol
    """
    pairs: List[Tuple[Decimal, Decimal]] = []
    for reserve, amount in borrows:
        sym = reserve.cryptocurrency.symbol
        px = D(prices_usd.get(sym, 0))
        pairs.append((D(amount), px))
    return _sum(pairs)


def available_borrow_usd(
    collateral_usd: Decimal,
    w_ltv: Decimal,   # 0..1
    debt_usd: Decimal,
) -> Decimal:
    """
    Headroom to borrow before hitting LTV wall (not liquidation threshold).
    """
    cap = D(collateral_usd) * D(w_ltv)
    headroom = cap - D(debt_usd)
    return headroom if headroom > 0 else Decimal("0")


def health_factor(
    collateral_usd: Decimal,
    w_liq_threshold: Decimal,  # 0..1
    debt_usd: Decimal,
) -> Decimal:
    """
    HF = (collateral_usd * weighted_liquidation_threshold) / debt_usd
    If debt is 0, return a very large number to mean 'safe'.
    """
    debt = D(debt_usd)
    if debt <= 0:
        return Decimal("999999999")  # effectively infinite
    return (D(collateral_usd) * D(w_liq_threshold)) / debt


# ---------- tiers (AAVE semantics) ----------

# default bands
HF_BANDS = {
    'SAFE': (Decimal("2.00"), Decimal("9999999")),  # HF > 2.00
    'WARN': (Decimal("1.20"), Decimal("2.00")),
    'TOP_UP': (Decimal("1.05"), Decimal("1.20")),
    'AT_RISK': (Decimal("1.00"), Decimal("1.05")),
    'LIQUIDATE': (Decimal("-1e18"), Decimal("1.00")),  # HF <= 1.00
}

# hysteresis in HF units (e.g. 0.05 means need 0.05 cross to change tier)
HF_HYST = Decimal("0.05")

def hf_tier(hf: Decimal, previous: Tier | None = None) -> Tier:
    x = D(hf)
    # widen boundaries depending on previous tier to avoid flicker
    bands = HF_BANDS.copy()

    if previous == 'SAFE':
        bands['SAFE'] = (bands['SAFE'][0] - HF_HYST, bands['SAFE'][1])
    elif previous == 'WARN':
        bands['WARN'] = (bands['WARN'][0] - HF_HYST, bands['WARN'][1] + HF_HYST)
    elif previous == 'TOP_UP':
        bands['TOP_UP'] = (bands['TOP_UP'][0] - HF_HYST, bands['TOP_UP'][1] + HF_HYST)
    elif previous == 'AT_RISK':
        bands['AT_RISK'] = (bands['AT_RISK'][0] - HF_HYST, bands['AT_RISK'][1] + HF_HYST)
    elif previous == 'LIQUIDATE':
        bands['LIQUIDATE'] = (bands['LIQUIDATE'][0], bands['LIQUIDATE'][1] + HF_HYST)

    for tier, (lo, hi) in bands.items():
        if lo < x <= hi:
            return tier  # type: ignore
    return 'SAFE'


# ---------- stress testing ----------

def stress_test_hf(
    supplies: Iterable[Tuple[object, Decimal, bool]],
    borrows: Iterable[Tuple[object, Decimal]],
    prices_usd: Dict[str, Decimal],
    shocks: List[float] | None = None,
    prev_tier: Tier | None = None,
) -> List[StressTestHFResult]:
    """
    Apply uniform price shocks (percentage) across ALL assets.
    Recomputes HF, weighted LTV/liq threshold, and headroom per scenario.
    """
    shocks = shocks or [-0.2, -0.3, -0.5]

    # Precompute weighted parameters and base values
    w_ltv = weighted_ltv(supplies, prices_usd)
    base_coll, w_liq = total_collateral_usd(supplies, prices_usd)
    base_debt = total_debt_usd(borrows, prices_usd)

    out: List[StressTestHFResult] = []
    for s in shocks:
        m = Decimal(str(1 + s))
        # shock both collateral and borrowed asset prices proportionally
        shocked_prices = {k: D(v) * m for k, v in prices_usd.items()}

        coll, liq = total_collateral_usd(supplies, shocked_prices)
        debt = total_debt_usd(borrows, shocked_prices)

        avail = available_borrow_usd(coll, w_ltv, debt)
        hf = health_factor(coll, liq, debt)
        tier = hf_tier(hf, prev_tier)

        out.append(StressTestHFResult(
            shock=s,
            collateral_usd=float(coll),
            debt_usd=float(debt),
            ltv_weighted=float(w_ltv),
            liq_threshold_weighted=float(liq),
            available_borrow_usd=float(avail),
            health_factor=float(hf),
            tier=tier,
        ))
        prev_tier = tier

    return out


# ---------- "what would it take" calculators ----------

def repay_to_target_hf(
    collateral_usd: Decimal,
    w_liq_threshold: Decimal,
    debt_usd: Decimal,
    target_hf: Decimal = Decimal("1.20"),
) -> Decimal:
    """
    Solve for repay >= 0 such that HF' = target:
      target_hf = (collateral * w_liq) / (debt - repay)
      -> repay = debt - (collateral * w_liq) / target_hf
    """
    debt = D(debt_usd)
    num = D(collateral_usd) * D(w_liq_threshold)
    if target_hf <= 0:
        return Decimal("0")
    repay = debt - (num / D(target_hf))
    if repay <= 0:
        return Decimal("0")
    if repay > debt:
        repay = debt
    return repay


def add_collateral_to_target_hf(
    collateral_usd: Decimal,
    w_liq_threshold: Decimal,
    debt_usd: Decimal,
    target_hf: Decimal = Decimal("1.20"),
) -> Decimal:
    """
    Solve for delta_coll >= 0 such that HF' = target:
      target_hf = ((collateral + delta) * w_liq) / debt
      -> delta = (target_hf * debt / w_liq) - collateral
    """
    if w_liq_threshold <= 0:
        return Decimal("0")
    needed = (D(target_hf) * D(debt_usd) / D(w_liq_threshold)) - D(collateral_usd)
    return needed if needed > 0 else Decimal("0")


# ---------- UI glue (colors/messages) ----------

def risk_color(tier: Tier) -> str:
    return {
        'SAFE': '#10B981',      # Green
        'WARN': '#F59E0B',      # Yellow
        'TOP_UP': '#EF4444',    # Red
        'AT_RISK': '#DC2626',   # Dark Red
        'LIQUIDATE': '#7C2D12', # Very Dark Red
    }.get(tier, '#6B7280')

def risk_message(tier: Tier, hf: float) -> str:
    msg = {
        'SAFE': f"Healthy. Health Factor {hf:.2f}",
        'WARN': f"Monitor closely. Health Factor {hf:.2f}",
        'TOP_UP': f"Consider adding collateral/repaying. Health Factor {hf:.2f}",
        'AT_RISK': f"Immediate action recommended. Health Factor {hf:.2f}",
        'LIQUIDATE': f"Liquidation risk—HF ≤ 1.00 (current {hf:.2f})",
    }
    return msg.get(tier, f"Status: {hf:.2f}")


# ---------- Legacy compatibility helpers ----------

def calculate_lending_account_data(supplies: List[object], borrows: List[object], prices: Dict[str, Decimal]) -> object:
    """
    Legacy compatibility function for the existing GraphQL resolver.
    Converts SupplyPosition and BorrowPosition objects to the format expected by the risk functions.
    """
    from decimal import Decimal
    
    # Convert SupplyPosition objects to tuples
    supplies_for_risk = []
    for sp in supplies:
        supplies_for_risk.append((sp.reserve, sp.quantity, sp.use_as_collateral))
    
    # Convert BorrowPosition objects to tuples
    borrows_for_risk = []
    for bp in borrows:
        borrows_for_risk.append((bp.reserve, bp.amount))
    
    # Calculate risk metrics
    total_coll_usd, weighted_liq_threshold = total_collateral_usd(supplies_for_risk, prices)
    total_dbt_usd = total_debt_usd(borrows_for_risk, prices)
    
    hf = health_factor(total_coll_usd, weighted_liq_threshold, total_dbt_usd)
    hf_tier_name = hf_tier(hf)
    
    # Calculate weighted LTV for available borrow
    weighted_ltv_value = weighted_ltv(supplies_for_risk, prices)
    avail_borrow_usd = available_borrow_usd(total_coll_usd, weighted_ltv_value, total_dbt_usd)
    
    # Return a simple object with the calculated values
    class LendingAccountData:
        def __init__(self, collateral_usd, debt_usd, health_factor, health_factor_tier, 
                     available_borrow_usd, weighted_ltv, weighted_liquidation_threshold, 
                     supplies, borrows):
            self.total_collateral_usd = collateral_usd
            self.total_debt_usd = debt_usd
            self.health_factor = health_factor
            self.health_factor_tier = health_factor_tier
            self.available_borrow_usd = available_borrow_usd
            self.weighted_ltv = weighted_ltv
            self.weighted_liquidation_threshold = weighted_liquidation_threshold
            self.supplies = supplies
            self.borrows = borrows
    
    return LendingAccountData(
        total_collateral_usd=total_coll_usd,
        total_debt_usd=total_dbt_usd,
        health_factor=hf,
        health_factor_tier=hf_tier_name,
        available_borrow_usd=avail_borrow_usd,
        weighted_ltv=weighted_ltv_value,
        weighted_liquidation_threshold=weighted_liq_threshold,
        supplies=supplies,
        borrows=borrows
    )