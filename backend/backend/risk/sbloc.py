# SBLOC Risk Engine with Tiered Thresholds + Hysteresis + Haircuts + Stress Test
from decimal import Decimal
from typing import Literal, List, Dict, Any
from dataclasses import dataclass

Tier = Literal['SAFE', 'WARN', 'TOP_UP', 'AT_RISK', 'LIQUIDATE']
HAIRCUT = { 'LOW': 0.6, 'MEDIUM': 0.5, 'HIGH': 0.4, 'EXTREME': 0.3 }

@dataclass
class StressTestResult:
    shock: float
    ltvPct: float
    tier: Tier

def haircut_value(value_usd: float, vol_tier: str) -> Decimal:
    """Apply volatility-based haircut to collateral value"""
    return Decimal(str(value_usd)) * Decimal(str(HAIRCUT.get(vol_tier, 0.5)))

def ltv(collateral_usd: Decimal, loan_usd: Decimal) -> Decimal:
    """Calculate Loan-to-Value ratio as percentage"""
    if collateral_usd == 0:
        return Decimal('0')
    return (loan_usd / collateral_usd) * 100

def ltv_tier(ltv_pct: Decimal, previous: Tier = None) -> Tier:
    """Determine risk tier with hysteresis to prevent flickering"""
    x = float(ltv_pct)
    
    # Hysteresis: require 1% movement to change tier
    if x < 35 - (1 if previous == 'WARN' else 0):
        return 'SAFE'
    if x < 40 - (1 if previous == 'TOP_UP' else 0):
        return 'WARN'
    if x < 45 - (1 if previous == 'AT_RISK' else 0):
        return 'TOP_UP'
    if x < 50 - (1 if previous == 'LIQUIDATE' else 0):
        return 'AT_RISK'
    return 'LIQUIDATE'

def stress_test(coll_usd: float, loan_usd: float, shocks: List[float] = None) -> List[StressTestResult]:
    """Run stress test with market shock scenarios"""
    if shocks is None:
        shocks = [-0.2, -0.3, -0.5]  # 20%, 30%, 50% market drops
    
    results = []
    for shock in shocks:
        stressed_collateral = Decimal(str(coll_usd)) * Decimal(str(1 + shock))
        stressed_ltv = ltv(stressed_collateral, Decimal(str(loan_usd)))
        tier = ltv_tier(stressed_ltv, None)
        
        results.append(StressTestResult(
            shock=shock,
            ltvPct=float(stressed_ltv),
            tier=tier
        ))
    
    return results

def calculate_margin_call_amount(collateral_usd: float, loan_usd: float, target_ltv: float = 40.0) -> float:
    """Calculate how much to repay to reach target LTV"""
    current_ltv = float(ltv(Decimal(str(collateral_usd)), Decimal(str(loan_usd))))
    
    if current_ltv <= target_ltv:
        return 0.0
    
    # Solve: (loan_usd - repay) / collateral_usd = target_ltv / 100
    repay_amount = loan_usd - (collateral_usd * target_ltv / 100)
    return max(0.0, repay_amount)

def calculate_additional_collateral_needed(collateral_usd: float, loan_usd: float, target_ltv: float = 40.0) -> float:
    """Calculate additional collateral needed to reach target LTV"""
    current_ltv = float(ltv(Decimal(str(collateral_usd)), Decimal(str(loan_usd))))
    
    if current_ltv <= target_ltv:
        return 0.0
    
    # Solve: loan_usd / (collateral_usd + additional) = target_ltv / 100
    required_collateral = loan_usd * 100 / target_ltv
    additional_needed = required_collateral - collateral_usd
    return max(0.0, additional_needed)

def get_risk_color(tier: Tier) -> str:
    """Get UI color for risk tier"""
    colors = {
        'SAFE': '#10B981',      # Green
        'WARN': '#F59E0B',      # Yellow
        'TOP_UP': '#EF4444',    # Red
        'AT_RISK': '#DC2626',   # Dark Red
        'LIQUIDATE': '#7C2D12'  # Very Dark Red
    }
    return colors.get(tier, '#6B7280')

def get_risk_message(tier: Tier, ltv_pct: float) -> str:
    """Get user-friendly risk message"""
    messages = {
        'SAFE': f"Portfolio is healthy at {ltv_pct:.1f}% LTV",
        'WARN': f"Monitor closely - LTV at {ltv_pct:.1f}%",
        'TOP_UP': f"Consider adding collateral - LTV at {ltv_pct:.1f}%",
        'AT_RISK': f"Immediate action needed - LTV at {ltv_pct:.1f}%",
        'LIQUIDATE': f"Liquidation risk - LTV at {ltv_pct:.1f}%"
    }
    return messages.get(tier, "Unknown risk level")
