"""
Risk Management - Citadel-grade risk controls for retail investors
"""
from django.utils import timezone
from decimal import Decimal
from .signal_performance_models import UserRiskBudget

def get_user_risk_budget(user):
    """Get or create risk budget for a user"""
    budget, created = UserRiskBudget.objects.get_or_create(user=user)
    budget.reset_daily_risk()  # Reset if needed
    return budget

def calculate_position_size(user, symbol, entry_price, stop_price, mode='SAFE'):
    """
    Calculate safe position size based on user's risk budget and account value.
    
    Returns:
        dict with 'shares', 'dollars_at_risk', 'risk_pct', 'allowed'
    """
    budget = get_user_risk_budget(user)
    budget.reset_daily_risk()
    
    # Check circuit breaker
    if budget.trading_paused:
        return {
            'shares': 0,
            'dollars_at_risk': Decimal('0.00'),
            'risk_pct': Decimal('0.00'),
            'allowed': False,
            'reason': budget.pause_reason or 'Trading paused due to daily loss limit'
        }
    
    # Check daily risk budget
    if budget.daily_risk_used_pct >= budget.max_daily_risk_pct:
        return {
            'shares': 0,
            'dollars_at_risk': Decimal('0.00'),
            'risk_pct': Decimal('0.00'),
            'allowed': False,
            'reason': f'Daily risk limit reached ({budget.daily_risk_used_pct:.2f}% / {budget.max_daily_risk_pct:.2f}%)'
        }
    
    # Calculate risk per share
    risk_per_share = abs(entry_price - stop_price)
    if risk_per_share == 0:
        return {
            'shares': 0,
            'dollars_at_risk': Decimal('0.00'),
            'risk_pct': Decimal('0.00'),
            'allowed': False,
            'reason': 'Invalid stop price'
        }
    
    # Determine risk per trade percentage
    risk_per_trade_pct = Decimal('0.005') if mode == 'SAFE' else Decimal('0.012')  # 0.5% or 1.2%
    
    # Calculate position size based on account value and risk
    account_value = budget.account_value or Decimal('10000.00')  # Default $10k if not set
    max_dollars_at_risk = account_value * risk_per_trade_pct
    
    # Calculate shares
    shares = int(max_dollars_at_risk / risk_per_share)
    
    # Apply position size limits
    max_position_value = account_value * (budget.max_position_size_pct / 100)
    max_shares_by_value = int(max_position_value / entry_price)
    shares = min(shares, max_shares_by_value)
    
    # Minimum position size
    min_position_value = account_value * (budget.min_position_size_pct / 100)
    min_shares = int(min_position_value / entry_price)
    if shares < min_shares:
        shares = min_shares
    
    # Calculate actual risk
    dollars_at_risk = Decimal(str(shares)) * risk_per_share
    risk_pct = (dollars_at_risk / account_value) * 100
    
    # Check if this would exceed daily limit
    new_daily_risk = budget.daily_risk_used_pct + risk_pct
    if new_daily_risk > budget.max_daily_risk_pct:
        # Reduce shares to fit within limit
        remaining_risk_pct = budget.max_daily_risk_pct - budget.daily_risk_used_pct
        if remaining_risk_pct > 0:
            max_dollars_at_risk = account_value * (remaining_risk_pct / 100)
            shares = int(max_dollars_at_risk / risk_per_share)
            dollars_at_risk = Decimal(str(shares)) * risk_per_share
            risk_pct = remaining_risk_pct
        else:
            return {
                'shares': 0,
                'dollars_at_risk': Decimal('0.00'),
                'risk_pct': Decimal('0.00'),
                'allowed': False,
                'reason': 'Daily risk limit would be exceeded'
            }
    
    return {
        'shares': shares,
        'dollars_at_risk': dollars_at_risk,
        'risk_pct': risk_pct,
        'allowed': True,
        'reason': None
    }

def record_trade_risk(user, dollars_at_risk, pnl_dollars=None):
    """Record a trade's risk usage and update daily PnL"""
    budget = get_user_risk_budget(user)
    budget.reset_daily_risk()
    
    # Update risk used
    account_value = budget.account_value or Decimal('10000.00')
    risk_pct = (dollars_at_risk / account_value) * 100
    budget.daily_risk_used_pct += risk_pct
    
    # Update PnL if provided
    if pnl_dollars is not None:
        pnl_pct = (pnl_dollars / account_value) * 100
        budget.daily_pnl_pct += pnl_pct
    
    budget.save()
    
    # Check circuit breaker
    budget.check_circuit_breaker()
    
    return budget

