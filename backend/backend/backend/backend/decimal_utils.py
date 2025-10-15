# Decimal precision utilities for financial calculations
from decimal import Decimal, ROUND_DOWN, ROUND_UP, getcontext
from typing import Dict, Tuple, Optional
import json

# Set high precision for financial calculations
getcontext().prec = 28

# Minimum trade sizes and precision by symbol
CRYPTO_SPECS = {
    'BTC': {'min_qty': Decimal('0.00001'), 'step': Decimal('0.00001'), 'price_step': Decimal('0.01')},
    'ETH': {'min_qty': Decimal('0.0001'), 'step': Decimal('0.0001'), 'price_step': Decimal('0.01')},
    'SOL': {'min_qty': Decimal('0.01'), 'step': Decimal('0.01'), 'price_step': Decimal('0.001')},
    'ADA': {'min_qty': Decimal('1'), 'step': Decimal('1'), 'price_step': Decimal('0.0001')},
    'DOT': {'min_qty': Decimal('0.1'), 'step': Decimal('0.1'), 'price_step': Decimal('0.01')},
    'MATIC': {'min_qty': Decimal('1'), 'step': Decimal('1'), 'price_step': Decimal('0.0001')},
    'AVAX': {'min_qty': Decimal('0.1'), 'step': Decimal('0.1'), 'price_step': Decimal('0.01')},
    'LINK': {'min_qty': Decimal('0.1'), 'step': Decimal('0.1'), 'price_step': Decimal('0.01')},
    'UNI': {'min_qty': Decimal('0.1'), 'step': Decimal('0.1'), 'price_step': Decimal('0.01')},
    'AAVE': {'min_qty': Decimal('0.01'), 'step': Decimal('0.01'), 'price_step': Decimal('0.01')},
}

def validate_quantity(symbol: str, quantity: str) -> Tuple[bool, str, Decimal]:
    """Validate and normalize crypto quantity with proper precision"""
    try:
        qty = Decimal(quantity)
        if symbol not in CRYPTO_SPECS:
            return False, f"Unsupported symbol: {symbol}", Decimal('0')
        
        spec = CRYPTO_SPECS[symbol]
        
        # Check minimum quantity
        if qty < spec['min_qty']:
            return False, f"Quantity below minimum: {spec['min_qty']}", Decimal('0')
        
        # Check step precision
        if qty % spec['step'] != 0:
            return False, f"Invalid quantity precision. Step: {spec['step']}", Decimal('0')
        
        # Normalize to proper precision
        normalized = qty.quantize(spec['step'], rounding=ROUND_DOWN)
        return True, "Valid", normalized
        
    except Exception as e:
        return False, f"Invalid quantity format: {str(e)}", Decimal('0')

def validate_price(symbol: str, price: str) -> Tuple[bool, str, Decimal]:
    """Validate and normalize crypto price with proper precision"""
    try:
        px = Decimal(price)
        if symbol not in CRYPTO_SPECS:
            return False, f"Unsupported symbol: {symbol}", Decimal('0')
        
        spec = CRYPTO_SPECS[symbol]
        
        # Check minimum price
        if px <= 0:
            return False, "Price must be positive", Decimal('0')
        
        # Check step precision
        if px % spec['price_step'] != 0:
            return False, f"Invalid price precision. Step: {spec['price_step']}", Decimal('0')
        
        # Normalize to proper precision
        normalized = px.quantize(spec['price_step'], rounding=ROUND_DOWN)
        return True, "Valid", normalized
        
    except Exception as e:
        return False, f"Invalid price format: {str(e)}", Decimal('0')

def calculate_trade_value(quantity: Decimal, price: Decimal) -> Decimal:
    """Calculate trade value with proper rounding"""
    return (quantity * price).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

def calculate_fees(trade_value: Decimal, fee_rate: Decimal = Decimal('0.001')) -> Decimal:
    """Calculate trading fees with proper rounding"""
    return (trade_value * fee_rate).quantize(Decimal('0.01'), rounding=ROUND_UP)

def calculate_slippage(trade_value: Decimal, slippage_bps: int = 50) -> Decimal:
    """Calculate estimated slippage in USD"""
    slippage_rate = Decimal(slippage_bps) / Decimal('10000')
    return (trade_value * slippage_rate).quantize(Decimal('0.01'), rounding=ROUND_UP)

def format_decimal(value: Decimal, precision: int = 2) -> str:
    """Format decimal for display with proper precision"""
    return f"{value:.{precision}f}"

def decimal_to_json(value: Decimal) -> str:
    """Convert decimal to JSON-safe string"""
    return str(value)

def json_to_decimal(value: str) -> Decimal:
    """Convert JSON string back to decimal"""
    return Decimal(value)

# Portfolio value calculations with proper precision
def calculate_portfolio_value(holdings: list) -> Dict[str, Decimal]:
    """Calculate portfolio metrics with decimal precision"""
    total_value = Decimal('0')
    total_cost = Decimal('0')
    total_pnl = Decimal('0')
    
    for holding in holdings:
        qty = Decimal(str(holding.get('quantity', 0)))
        current_price = Decimal(str(holding.get('current_price', 0)))
        cost_basis = Decimal(str(holding.get('cost_basis', 0)))
        
        current_value = qty * current_price
        cost_value = qty * cost_basis
        
        total_value += current_value
        total_cost += cost_value
        total_pnl += current_value - cost_value
    
    return {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_pnl': total_pnl,
        'total_pnl_pct': (total_pnl / total_cost * 100) if total_cost > 0 else Decimal('0')
    }

# SBLOC calculations with proper precision
def calculate_ltv(collateral_value: Decimal, loan_amount: Decimal) -> Decimal:
    """Calculate Loan-to-Value ratio with proper precision"""
    if collateral_value == 0:
        return Decimal('0')
    return (loan_amount / collateral_value * 100).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

def calculate_collateral_required(loan_amount: Decimal, target_ltv: Decimal = Decimal('40')) -> Decimal:
    """Calculate required collateral for target LTV"""
    if target_ltv == 0:
        return Decimal('0')
    return (loan_amount / target_ltv * 100).quantize(Decimal('0.01'), rounding=ROUND_UP)

def calculate_loan_capacity(collateral_value: Decimal, target_ltv: Decimal = Decimal('40')) -> Decimal:
    """Calculate maximum loan capacity for given collateral"""
    return (collateral_value * target_ltv / 100).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
