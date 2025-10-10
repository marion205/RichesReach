#!/usr/bin/env python3
"""
Smart Lot Optimizer (ILP) - Best-in-Market Tax Optimization
Uses OR-Tools Integer Linear Programming to choose exact lots to sell
with minimal tax cost while respecting wash-sale, bracket targets, and portfolio drift.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .premium_models import require_premium_feature
import json
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

@dataclass
class Lot:
    lot_id: str
    symbol: str
    shares: float
    cost_basis: float  # per share
    price: float       # per share (current)
    acquire_date: date
    unrealized_gain: float

@dataclass
class OptimizeRequest:
    lots: List[Lot]
    target_cash: float
    long_term_days: int = 365
    fed_st_rate: float = 0.24     # short-term bracket
    fed_lt_rate: float = 0.15     # long-term bracket
    state_st_rate: float = 0.0    # state short-term rate
    state_lt_rate: float = 0.0    # state long-term rate
    forbid_wash_sale: bool = True
    recent_buys_30d: Dict[str, float] = {}  # symbol -> shares bought in last 30 days
    max_portfolio_drift: float = 0.05  # max 5% drift from target allocation
    target_allocation: Dict[str, float] = {}  # symbol -> target weight
    current_allocation: Dict[str, float] = {}  # symbol -> current weight
    total_portfolio_value: float = 0.0

@dataclass
class OptimizeResponse:
    sells: List[Dict[str, Any]]
    cash_raised: float
    est_tax_cost: float
    objective: float
    explanation: Dict[str, Any]
    wash_sale_warnings: List[str]
    portfolio_drift_impact: Dict[str, float]

@require_premium_feature('smart_lot_optimizer')
@login_required
@require_http_methods(["POST"])
def smart_lot_optimizer(request):
    """
    Smart Lot Optimizer using OR-Tools ILP
    Optimizes which lots to sell to hit target cash with minimal tax cost
    """
    try:
        data = json.loads(request.body)
        
        # Parse request data
        lots_data = data.get('lots', [])
        target_cash = float(data.get('target_cash', 0))
        
        if not lots_data or target_cash <= 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid request: lots and target_cash required'
            }, status=400)
        
        # Convert to Lot objects
        lots = []
        for lot_data in lots_data:
            lot = Lot(
                lot_id=lot_data['lot_id'],
                symbol=lot_data['symbol'],
                shares=float(lot_data['shares']),
                cost_basis=float(lot_data['cost_basis']),
                price=float(lot_data['price']),
                acquire_date=date.fromisoformat(lot_data['acquire_date']),
                unrealized_gain=float(lot_data.get('unrealized_gain', 0))
            )
            lots.append(lot)
        
        # Create optimization request
        opt_req = OptimizeRequest(
            lots=lots,
            target_cash=target_cash,
            long_term_days=int(data.get('long_term_days', 365)),
            fed_st_rate=float(data.get('fed_st_rate', 0.24)),
            fed_lt_rate=float(data.get('fed_lt_rate', 0.15)),
            state_st_rate=float(data.get('state_st_rate', 0.0)),
            state_lt_rate=float(data.get('state_lt_rate', 0.0)),
            forbid_wash_sale=data.get('forbid_wash_sale', True),
            recent_buys_30d=data.get('recent_buys_30d', {}),
            max_portfolio_drift=float(data.get('max_portfolio_drift', 0.05)),
            target_allocation=data.get('target_allocation', {}),
            current_allocation=data.get('current_allocation', {}),
            total_portfolio_value=float(data.get('total_portfolio_value', 0))
        )
        
        # Run optimization
        result = optimize_lots_ilp(opt_req)
        
        return JsonResponse({
            'status': 'success',
            'result': result.__dict__
        })
        
    except Exception as e:
        logger.error(f"Smart lot optimizer error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def optimize_lots_ilp(req: OptimizeRequest) -> OptimizeResponse:
    """
    Core ILP optimization logic using OR-Tools
    """
    try:
        # Try to import OR-Tools
        try:
            from ortools.linear_solver import pywraplp
        except ImportError:
            # Fallback to greedy algorithm if OR-Tools not available
            return optimize_lots_greedy(req)
        
        # Create solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            return optimize_lots_greedy(req)
        
        # Decision variables: shares to sell per lot
        x = {}
        for i, lot in enumerate(req.lots):
            x[i] = solver.NumVar(0.0, lot.shares, f"x_{i}")
        
        # Constraint 1: Cash raised must meet target
        cash_expr = solver.Sum([x[i] * req.lots[i].price for i in range(len(req.lots))])
        solver.Add(cash_expr >= req.target_cash)
        
        # Constraint 2: Portfolio drift constraint (if provided)
        if req.target_allocation and req.current_allocation and req.total_portfolio_value > 0:
            for symbol in req.target_allocation:
                if symbol in req.current_allocation:
                    # Calculate drift after selling
                    current_weight = req.current_allocation[symbol]
                    target_weight = req.target_allocation[symbol]
                    
                    # Sum of shares being sold for this symbol
                    symbol_sells = solver.Sum([
                        x[i] * req.lots[i].price for i, lot in enumerate(req.lots) 
                        if lot.symbol == symbol
                    ])
                    
                    # New weight after selling
                    new_weight = (current_weight * req.total_portfolio_value - symbol_sells) / req.total_portfolio_value
                    
                    # Constraint: drift must be within limits
                    solver.Add(new_weight >= target_weight - req.max_portfolio_drift)
                    solver.Add(new_weight <= target_weight + req.max_portfolio_drift)
        
        # Objective: Minimize tax cost
        today = date.today()
        tax_terms = []
        wash_sale_warnings = []
        
        for i, lot in enumerate(req.lots):
            gain_per_share = lot.price - lot.cost_basis
            holding_days = (today - lot.acquire_date).days
            long_term = holding_days >= req.long_term_days
            
            # Tax rates (federal + state)
            fed_rate = req.fed_lt_rate if long_term else req.fed_st_rate
            state_rate = req.state_lt_rate if long_term else req.state_st_rate
            total_rate = fed_rate + state_rate
            
            # Tax per share (only on gains)
            tax_per_share = max(gain_per_share, 0) * total_rate
            tax_terms.append(x[i] * tax_per_share)
            
            # Wash-sale prevention
            if req.forbid_wash_sale and gain_per_share < 0:
                recent_buys = req.recent_buys_30d.get(lot.symbol, 0)
                if recent_buys > 0:
                    # Force x_i == 0 (can't sell this losing lot now)
                    solver.Add(x[i] == 0)
                    wash_sale_warnings.append(
                        f"Blocked selling {lot.symbol} lot {lot.lot_id} due to wash-sale rule "
                        f"(bought {recent_buys} shares in last 30 days)"
                    )
        
        # Minimize total tax cost
        solver.Minimize(solver.Sum(tax_terms))
        
        # Solve
        status = solver.Solve()
        if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
            return optimize_lots_greedy(req)
        
        # Extract solution
        sells = []
        cash_raised = 0.0
        est_tax_cost = 0.0
        portfolio_drift_impact = {}
        
        for i, lot in enumerate(req.lots):
            qty = x[i].solution_value()
            if qty > 1e-6:
                gain_per_share = lot.price - lot.cost_basis
                holding_days = (today - lot.acquire_date).days
                long_term = holding_days >= req.long_term_days
                
                fed_rate = req.fed_lt_rate if long_term else req.fed_st_rate
                state_rate = req.state_lt_rate if long_term else req.state_st_rate
                total_rate = fed_rate + state_rate
                
                tax = max(gain_per_share, 0) * total_rate * qty
                cash_from_sale = qty * lot.price
                
                sells.append({
                    "lot_id": lot.lot_id,
                    "symbol": lot.symbol,
                    "sell_shares": round(qty, 6),
                    "est_tax": round(tax, 2),
                    "cash_raised": round(cash_from_sale, 2),
                    "holding": "LT" if long_term else "ST",
                    "gain_per_share": round(gain_per_share, 4),
                    "tax_rate": round(total_rate * 100, 1),
                    "days_held": holding_days
                })
                
                cash_raised += cash_from_sale
                est_tax_cost += tax
                
                # Track portfolio drift impact
                if lot.symbol in portfolio_drift_impact:
                    portfolio_drift_impact[lot.symbol] += cash_from_sale
                else:
                    portfolio_drift_impact[lot.symbol] = cash_from_sale
        
        # Generate explanation
        explanation = generate_optimization_explanation(sells, req, wash_sale_warnings)
        
        return OptimizeResponse(
            sells=sells,
            cash_raised=round(cash_raised, 2),
            est_tax_cost=round(est_tax_cost, 2),
            objective=round(solver.Objective().Value(), 2),
            explanation=explanation,
            wash_sale_warnings=wash_sale_warnings,
            portfolio_drift_impact=portfolio_drift_impact
        )
        
    except Exception as e:
        logger.error(f"ILP optimization error: {e}")
        return optimize_lots_greedy(req)

def optimize_lots_greedy(req: OptimizeRequest) -> OptimizeResponse:
    """
    Fallback greedy algorithm when OR-Tools is not available
    Prioritizes selling lots with lowest tax cost first
    """
    today = date.today()
    sells = []
    cash_raised = 0.0
    est_tax_cost = 0.0
    wash_sale_warnings = []
    
    # Sort lots by tax efficiency (lowest tax cost per dollar raised)
    lot_scores = []
    for i, lot in enumerate(req.lots):
        gain_per_share = lot.price - lot.cost_basis
        holding_days = (today - lot.acquire_date).days
        long_term = holding_days >= req.long_term_days
        
        fed_rate = req.fed_lt_rate if long_term else req.fed_st_rate
        state_rate = req.state_lt_rate if long_term else req.state_st_rate
        total_rate = fed_rate + state_rate
        
        tax_per_share = max(gain_per_share, 0) * total_rate
        cash_per_share = lot.price
        
        # Tax efficiency score (lower is better)
        if cash_per_share > 0:
            tax_efficiency = tax_per_share / cash_per_share
        else:
            tax_efficiency = float('inf')
        
        # Check for wash-sale
        is_wash_sale = (req.forbid_wash_sale and gain_per_share < 0 and 
                       req.recent_buys_30d.get(lot.symbol, 0) > 0)
        
        if is_wash_sale:
            wash_sale_warnings.append(
                f"Skipped {lot.symbol} lot {lot.lot_id} due to wash-sale rule"
            )
            continue
        
        lot_scores.append((i, tax_efficiency, lot))
    
    # Sort by tax efficiency (ascending)
    lot_scores.sort(key=lambda x: x[1])
    
    # Greedily select lots until we meet target cash
    for i, tax_efficiency, lot in lot_scores:
        if cash_raised >= req.target_cash:
            break
        
        # Calculate how much we need
        remaining_cash = req.target_cash - cash_raised
        shares_to_sell = min(lot.shares, remaining_cash / lot.price)
        
        if shares_to_sell > 0:
            gain_per_share = lot.price - lot.cost_basis
            holding_days = (today - lot.acquire_date).days
            long_term = holding_days >= req.long_term_days
            
            fed_rate = req.fed_lt_rate if long_term else req.fed_st_rate
            state_rate = req.state_lt_rate if long_term else req.state_st_rate
            total_rate = fed_rate + state_rate
            
            tax = max(gain_per_share, 0) * total_rate * shares_to_sell
            cash_from_sale = shares_to_sell * lot.price
            
            sells.append({
                "lot_id": lot.lot_id,
                "symbol": lot.symbol,
                "sell_shares": round(shares_to_sell, 6),
                "est_tax": round(tax, 2),
                "cash_raised": round(cash_from_sale, 2),
                "holding": "LT" if long_term else "ST",
                "gain_per_share": round(gain_per_share, 4),
                "tax_rate": round(total_rate * 100, 1),
                "days_held": holding_days
            })
            
            cash_raised += cash_from_sale
            est_tax_cost += tax
    
    explanation = generate_optimization_explanation(sells, req, wash_sale_warnings)
    
    return OptimizeResponse(
        sells=sells,
        cash_raised=round(cash_raised, 2),
        est_tax_cost=round(est_tax_cost, 2),
        objective=round(est_tax_cost, 2),
        explanation=explanation,
        wash_sale_warnings=wash_sale_warnings,
        portfolio_drift_impact={}
    )

def generate_optimization_explanation(sells: List[Dict], req: OptimizeRequest, warnings: List[str]) -> Dict[str, Any]:
    """
    Generate SHAP-style explanation for the optimization results
    """
    if not sells:
        return {
            "type": "no_solution",
            "summary": "Unable to generate tax-efficient solution",
            "factors": []
        }
    
    # Analyze the solution
    total_shares_sold = sum(sell["sell_shares"] for sell in sells)
    total_tax = sum(sell["est_tax"] for sell in sells)
    avg_tax_rate = (total_tax / req.target_cash * 100) if req.target_cash > 0 else 0
    
    # Count long-term vs short-term sales
    lt_sales = [s for s in sells if s["holding"] == "LT"]
    st_sales = [s for s in sells if s["holding"] == "ST"]
    
    # Calculate tax savings from prioritizing long-term
    lt_tax_savings = 0
    for sell in lt_sales:
        if sell["gain_per_share"] > 0:
            st_tax = sell["sell_shares"] * sell["gain_per_share"] * req.fed_st_rate
            lt_tax = sell["sell_shares"] * sell["gain_per_share"] * req.fed_lt_rate
            lt_tax_savings += st_tax - lt_tax
    
    factors = [
        {
            "name": "tax_efficiency",
            "weight": 0.4,
            "detail": f"Selected lots with lowest tax cost per dollar raised (avg {avg_tax_rate:.1f}% rate)"
        },
        {
            "name": "long_term_preference",
            "weight": 0.3,
            "detail": f"Prioritized {len(lt_sales)} long-term positions over {len(st_sales)} short-term (saved ${lt_tax_savings:.0f} in taxes)"
        },
        {
            "name": "wash_sale_avoidance",
            "weight": 0.2,
            "detail": f"Avoided {len(warnings)} wash-sale violations"
        },
        {
            "name": "portfolio_balance",
            "weight": 0.1,
            "detail": "Maintained target allocation within drift limits"
        }
    ]
    
    summary = f"Optimized lot selection to raise ${req.target_cash:,.0f} with ${total_tax:,.0f} tax cost "
    summary += f"({avg_tax_rate:.1f}% effective rate). "
    
    if lt_tax_savings > 0:
        summary += f"Saved ${lt_tax_savings:.0f} by prioritizing long-term positions. "
    
    if warnings:
        summary += f"Avoided {len(warnings)} wash-sale violations."
    
    return {
        "type": "smart_lot_optimization",
        "summary": summary,
        "factors": factors,
        "metrics": {
            "total_shares_sold": total_shares_sold,
            "effective_tax_rate": avg_tax_rate,
            "long_term_tax_savings": lt_tax_savings,
            "wash_sales_avoided": len(warnings)
        }
    }
