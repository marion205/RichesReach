# policy.py
from decimal import Decimal
from typing import TypedDict, Literal

RT = Literal["Conservative", "Moderate", "Aggressive"]

class Profile(TypedDict):
    incomeBracket: str
    age: int
    investmentGoals: list[str]
    riskTolerance: RT
    investmentHorizon: str
    liquidCashUSD: Decimal  # <-- add this on the server from user or bank link if available
    monthlyContributionUSD: Decimal

class Policy(TypedDict):
    cash_floor_usd: Decimal
    max_single_name_pct: Decimal
    sector_cap_pct: Decimal
    turnover_budget_pct: Decimal
    prefer_etfs: bool
    exclude_microcap: bool
    exclude_high_iv: bool

def policy_from_profile(p: Profile) -> Policy:
    rt = p["riskTolerance"]
    horizon = p["investmentHorizon"]
    # income/horizon shape policy only (guardrails), not alpha
    cash_floor = Decimal("1000")
    if "Emergency Fund" in p.get("investmentGoals", []):
        cash_floor = Decimal("2000")
    if p["incomeBracket"].startswith("Under") or "Under $30,000" in p["incomeBracket"]:
        cash_floor = max(cash_floor, Decimal("1500"))

    prefer_etfs = True if rt == "Conservative" or "1-3 years" in horizon else False
    return {
        "cash_floor_usd": cash_floor,
        "max_single_name_pct": Decimal("0.12") if rt=="Aggressive" else (Decimal("0.08") if rt=="Moderate" else Decimal("0.05")),
        "sector_cap_pct": Decimal("0.35"),
        "turnover_budget_pct": Decimal("0.10") if rt=="Aggressive" else Decimal("0.06"),
        "prefer_etfs": prefer_etfs,
        "exclude_microcap": True,
        "exclude_high_iv": rt != "Aggressive",
    }

def passes_emergency_floor(p: Profile) -> bool:
    return p["liquidCashUSD"] >= policy_from_profile(p)["cash_floor_usd"]
