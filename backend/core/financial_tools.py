# core/financial_tools.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
import math

# -----------------------------
# Debt Snowball (deterministic)
# -----------------------------
@dataclass
class Debt:
    name: str
    balance: float
    apr: float           # as percent, e.g. 19.99
    min_payment: float

def debt_snowball_plan(debts_in: List[Dict], extra_payment: float = 0.0, max_months: int = 600) -> Dict:
    """
    Pure, deterministic snowball.
    - Orders by smallest balance first.
    - Applies min payments to all, then extra to the smallest active debt.
    - Rolls freed minimums automatically as debts are paid off.
    Returns a compact summary plus the first few schedule lines for UX.
    """
    debts = [Debt(d['name'], float(d['balance']), float(d.get('apr', 0.0)), float(d.get('minPayment', 0.0))) for d in debts_in]
    # Filter out zero/negative balances
    debts = [d for d in debts if d.balance > 0]
    if not debts:
        return {"monthsToDebtFree": 0, "totalInterest": 0.0, "payoffOrder": [], "schedulePreview": []}

    # Sort by smallest balance (snowball)
    debts.sort(key=lambda d: d.balance)

    month = 0
    total_interest = 0.0
    schedule_preview = []
    payoff_order: List[str] = []
    # Track which debt is the current target index
    target_idx = 0

    while month < max_months and any(d.balance > 0.005 for d in debts):
        month += 1

        # 1) interest accrual
        month_interest = 0.0
        for d in debts:
            if d.balance <= 0:
                continue
            r = (d.apr / 100.0) / 12.0
            interest = d.balance * r
            d.balance += interest
            month_interest += interest
        total_interest += month_interest

        # 2) minimum payments
        paid_this_month = 0.0
        for d in debts:
            if d.balance <= 0:
                continue
            pay = min(d.min_payment, d.balance)
            d.balance -= pay
            paid_this_month += pay

        # 3) target extra (snowball to smallest active)
        # move target_idx forward if paid off
        while target_idx < len(debts) and debts[target_idx].balance <= 0.005:
            if debts[target_idx].name not in payoff_order:
                payoff_order.append(debts[target_idx].name)
            target_idx += 1

        if target_idx < len(debts) and debts[target_idx].balance > 0.005:
            addl = min(extra_payment, debts[target_idx].balance)
            debts[target_idx].balance -= addl
            paid_this_month += addl
            if debts[target_idx].balance <= 0.005 and debts[target_idx].name not in payoff_order:
                payoff_order.append(debts[target_idx].name)

        # record a compact line (first 12 months for preview)
        if month <= 12:
            preview_line = {
                "month": month,
                "totalPaid": round(paid_this_month, 2),
                "interestPaid": round(month_interest, 2),
                "balances": [{ "name": d.name, "balance": round(max(d.balance, 0.0), 2) } for d in debts],
            }
            schedule_preview.append(preview_line)

        # resort only by remaining balance to preserve snowball targeting if needed
        debts.sort(key=lambda d: max(d.balance, 0.0))

    # Finalize
    remaining = sum(max(d.balance, 0.0) for d in debts)
    if remaining > 0.005:
        # hit max_months cap: return partial but deterministic
        status = "incomplete"
    else:
        status = "complete"

    return {
        "status": status,
        "monthsToDebtFree": month if status == "complete" else None,
        "totalInterest": round(total_interest, 2),
        "payoffOrder": payoff_order,
        "schedulePreview": schedule_preview,
    }


# ------------------------------------
# Credit Utilization Optimizer (simple)
# ------------------------------------
def credit_utilization_optimizer(cards: List[Dict], target_util: float = 0.30) -> Dict:
    """
    Given cards [{name, limit, balance, apr?}], return the minimum cash
    needed to reach target total utilization and a suggested allocation.
    Allocation priority: higher APR first, then higher utilization.
    """
    cleaned = []
    total_limit = 0.0
    total_balance = 0.0
    for c in cards:
        limit = float(c.get("limit", 0.0))
        bal = float(c.get("balance", 0.0))
        apr = float(c.get("apr", 0.0))
        if limit <= 0:
            continue
        total_limit += limit
        total_balance += max(bal, 0.0)
        cleaned.append({"name": c["name"], "limit": limit, "balance": max(bal, 0.0), "apr": apr})

    if total_limit <= 0:
        return {"currentUtilization": 0.0, "targetUtilization": target_util, "amountToPay": 0.0, "allocation": []}

    current_util = total_balance / total_limit
    needed = max(0.0, total_balance - target_util * total_limit)
    if needed <= 0.005:
        return {
            "currentUtilization": round(current_util, 4),
            "targetUtilization": target_util,
            "amountToPay": 0.0,
            "allocation": [],
            "note": "Already at or under target utilization.",
        }

    # Sort priority: APR desc, then per-card utilization desc
    def card_key(c):
        card_util = (c["balance"] / c["limit"]) if c["limit"] > 0 else 0.0
        return (-c["apr"], -card_util)

    cleaned.sort(key=card_key)

    remaining = needed
    allocation = []
    for c in cleaned:
        if remaining <= 0.005:
            break
        # try to push each card down to min(target_util, current total target) proportionally;
        # for simplicity, pay down the full card first (greedy) then move on
        pay = min(c["balance"], remaining)
        if pay > 0:
            allocation.append({"name": c["name"], "pay": round(pay, 2)})
            c["balance"] -= pay
            remaining -= pay

    return {
        "currentUtilization": round(current_util, 4),
        "targetUtilization": target_util,
        "amountToPay": round(needed, 2),
        "allocation": allocation,
    }


# ------------------------------------------------------
# "Should I buy this luxury item?" (deterministic check)
# ------------------------------------------------------
def loan_payment(principal: float, apr_percent: float, months: int) -> float:
    if months <= 0:
        return principal
    r = (apr_percent / 100.0) / 12.0
    if r == 0:
        return principal / months
    return principal * (r / (1 - math.pow(1 + r, -months)))

def should_buy_luxury_item(
    take_home_monthly: float,
    fixed_bills_monthly: float,
    debt_payments_monthly: float,
    current_wants_monthly: float,
    savings_balance: float,
    item_price: float,
    pay_method: str = "cash",     # "cash" or "finance"
    finance_months: int = 0,
    finance_apr: float = 0.0,
    emergency_fund_months_target: float = 3.0
) -> Dict:
    """
    Deterministic affordability guardrails:
      1) Emergency fund: savings >= target * (fixed + debt)
      2) 50/30/20 rule budget bands (on take-home pay)
      3) Debt ratio sanity: (debt payments / take-home) <= 36% (soft)
      4) If financing, payment must fit inside 'wants' band without breaking savings band.
    Returns BUY / WAIT / AVOID + reasons and key numbers.
    """
    take = float(take_home_monthly)
    needs_cap = 0.50 * take
    wants_cap = 0.30 * take
    save_cap  = 0.20 * take

    needs_now = float(fixed_bills_monthly) + float(debt_payments_monthly)
    wants_now = float(current_wants_monthly)
    savings = float(savings_balance)

    # Emergency fund check
    monthly_core = float(fixed_bills_monthly) + float(debt_payments_monthly)
    emergency_needed = emergency_fund_months_target * monthly_core
    has_emergency = savings >= emergency_needed

    # Debt-to-income sanity (soft)
    dti = (float(debt_payments_monthly) / take) if take > 0 else 1.0
    dti_ok = dti <= 0.36

    # Compute item impact
    reasons = []
    decision = "WAIT"

    if pay_method == "cash":
        # cash comes out of savings; keep emergency fund intact
        new_savings = savings - item_price
        if new_savings < emergency_needed:
            reasons.append("Buying in cash would dip below your emergency fund target.")
        else:
            reasons.append("You can pay cash without breaking your emergency fund.")
        # also check wants band (treat as a one-off, but we still nudge)
        if wants_now > wants_cap:
            reasons.append("Your current 'wants' spending already exceeds 30% band.")
    else:
        # finance path
        pmt = loan_payment(item_price, finance_apr, max(1, finance_months))
        new_wants = wants_now + pmt
        if new_wants > wants_cap:
            reasons.append(f"Financed monthly payment (~${pmt:.2f}) exceeds your 30% 'wants' band.")
        else:
            reasons.append(f"Financed monthly payment (~${pmt:.2f}) fits inside your 30% 'wants' band.")
        # ensure emergency fund intact (no immediate cash hit assumed)
        if not has_emergency:
            reasons.append("Build emergency fund before adding a new payment.")

    # Global rules to pick decision
    if not has_emergency:
        decision = "AVOID"
        reasons.insert(0, "Emergency fund below target.")
    elif not dti_ok:
        decision = "WAIT"
        reasons.insert(0, "Debt-to-income is high; pay down debt first.")
    else:
        if pay_method == "cash":
            if savings - item_price >= emergency_needed and wants_now <= wants_cap:
                decision = "BUY"
            else:
                decision = "WAIT"
        else:
            pmt = loan_payment(item_price, finance_apr, max(1, finance_months))
            if (wants_now + pmt) <= wants_cap:
                decision = "BUY"
            else:
                decision = "WAIT"

    return {
        "decision": decision,
        "reasons": reasons,
        "bands": {
            "needsCap": round(needs_cap, 2),
            "wantsCap": round(wants_cap, 2),
            "savingsCap": round(save_cap, 2),
        },
        "current": {
            "needsNow": round(needs_now, 2),
            "wantsNow": round(wants_now, 2),
            "dti": round(dti, 3),
            "hasEmergencyFund": has_emergency,
            "emergencyTarget": round(emergency_needed, 2),
            "savings": round(savings, 2),
        },
        "item": {
            "price": round(item_price, 2),
            "payMethod": pay_method,
            "financeMonths": finance_months,
            "financeApr": finance_apr,
            "estMonthlyPayment": round(loan_payment(item_price, finance_apr, max(1, finance_months)) if pay_method != "cash" else 0.0, 2),
        },
    }
