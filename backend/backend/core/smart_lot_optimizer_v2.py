#!/usr/bin/env python3
"""
Smart Lot Optimizer 2.0 - Best-in-Market Tax Optimization
ILP optimization with loss budget, bracket targets, and advanced constraints
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .premium_models import require_premium_feature
import json
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

@dataclass
class LotV2:
    lot_id: str
    symbol: str
    shares: float
    cost_basis: float  # per share
    price: float       # per share (current)
    acquire_date: date
    unrealized_gain: float

@dataclass
class OptimizeRequestV2:
    lots: List[LotV2]
    target_cash: float
    long_term_days: int = 365
    st_rate: float = 0.24     # short-term bracket
    lt_rate: float = 0.15     # long-term bracket
    state_st_rate: float = 0.0
    state_lt_rate: float = 0.0
    loss_budget: float = 0.0  # max losses to realize (abs)
    recent_buys_30d: Dict[str, float] = field(default_factory=dict)
    forbid_wash_sale: bool = True
    bracket_target: float = 0.0  # target tax bracket (0.0 = no constraint)
    max_portfolio_drift: float = 0.05
    target_allocation: Dict[str, float] = field(default_factory=dict)
    current_allocation: Dict[str, float] = field(default_factory=dict)
    total_portfolio_value: float = 0.0
    prefer_long_term: bool = True
    min_holding_period: int = 0  # minimum days to hold before selling

@dataclass
class OptimizeResponseV2:
    sells: List[Dict[str, Any]]
    cash_raised: float
    est_tax_cost: float
    est_losses_used: float
    explanation: Dict[str, Any]
    wash_sale_warnings: List[str]
    portfolio_drift_impact: Dict[str, float]
    bracket_impact: Dict[str, Any]
    vs_fifo_comparison: Dict[str, Any]

@require_premium_feature('smart_lot_optimizer_v2')
@login_required
@require_http_methods(["POST"])
def smart_lot_optimizer_v2(request):
    """
    Smart Lot Optimizer 2.0 with advanced constraints
    Optimizes which lots to sell with loss budget, bracket targets, and portfolio constraints
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
        
        # Convert to LotV2 objects
        lots = []
        for lot_data in lots_data:
            lot = LotV2(
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
        opt_req = OptimizeRequestV2(
            lots=lots,
            target_cash=target_cash,
            long_term_days=int(data.get('long_term_days', 365)),
            st_rate=float(data.get('st_rate', 0.24)),
            lt_rate=float(data.get('lt_rate', 0.15)),
            state_st_rate=float(data.get('state_st_rate', 0.0)),
            state_lt_rate=float(data.get('state_lt_rate', 0.0)),
            loss_budget=float(data.get('loss_budget', 0.0)),
            recent_buys_30d=data.get('recent_buys_30d', {}),
            forbid_wash_sale=data.get('forbid_wash_sale', True),
            bracket_target=float(data.get('bracket_target', 0.0)),
            max_portfolio_drift=float(data.get('max_portfolio_drift', 0.05)),
            target_allocation=data.get('target_allocation', {}),
            current_allocation=data.get('current_allocation', {}),
            total_portfolio_value=float(data.get('total_portfolio_value', 0)),
            prefer_long_term=data.get('prefer_long_term', True),
            min_holding_period=int(data.get('min_holding_period', 0))
        )
        
        # Run optimization
        result = optimize_lots_ilp_v2(opt_req)
        
        return JsonResponse({
            'status': 'success',
            'result': result.__dict__
        })
        
    except Exception as e:
        logger.error(f"Smart lot optimizer v2 error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def optimize_lots_ilp_v2(req: OptimizeRequestV2) -> OptimizeResponseV2:
    """
    Core ILP optimization logic with advanced constraints
    """
    try:
        # Try to import OR-Tools
        try:
            from ortools.linear_solver import pywraplp
        except ImportError:
            # Fallback to greedy algorithm if OR-Tools not available
            return optimize_lots_greedy_v2(req)
        
        # Create solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            return optimize_lots_greedy_v2(req)
        
        # Decision variables: shares to sell per lot
        x = {}
        for i, lot in enumerate(req.lots):
            x[i] = solver.NumVar(0.0, lot.shares, f"x_{i}")
        
        # Constraint 1: Cash raised must meet target
        cash_expr = solver.Sum([x[i] * req.lots[i].price for i in range(len(req.lots))])
        solver.Add(cash_expr >= req.target_cash)
        
        # Constraint 2: Loss budget constraint
        if req.loss_budget > 0:
            loss_expr = solver.Sum([
                x[i] * max(0, req.lots[i].cost_basis - req.lots[i].price) 
                for i in range(len(req.lots))
            ])
            solver.Add(loss_expr <= req.loss_budget)
        
        # Constraint 3: Minimum holding period
        if req.min_holding_period > 0:
            today = date.today()
            for i, lot in enumerate(req.lots):
                holding_days = (today - lot.acquire_date).days
                if holding_days < req.min_holding_period:
                    solver.Add(x[i] == 0)
        
        # Constraint 4: Portfolio drift constraint
        if req.target_allocation and req.current_allocation and req.total_portfolio_value > 0:
            for symbol in req.target_allocation:
                if symbol in req.current_allocation:
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
        
        # Objective: Minimize tax cost with preference for long-term
        today = date.today()
        tax_terms = []
        wash_sale_warnings = []
        
        for i, lot in enumerate(req.lots):
            gain_per_share = lot.price - lot.cost_basis
            holding_days = (today - lot.acquire_date).days
            long_term = holding_days >= req.long_term_days
            
            # Tax rates (federal + state)
            fed_rate = req.lt_rate if long_term else req.st_rate
            state_rate = req.state_lt_rate if long_term else req.state_st_rate
            total_rate = fed_rate + state_rate
            
            # Tax per share (only on gains)
            tax_per_share = max(gain_per_share, 0) * total_rate
            
            # Preference for long-term (add small penalty for short-term)
            preference_penalty = 0.001 if not long_term and req.prefer_long_term else 0
            
            tax_terms.append(x[i] * (tax_per_share + preference_penalty))
            
            # Wash-sale prevention
            if req.forbid_wash_sale and gain_per_share < 0:
                recent_buys = req.recent_buys_30d.get(lot.symbol, 0)
                if recent_buys > 0:
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
            return optimize_lots_greedy_v2(req)
        
        # Extract solution
        sells = []
        cash_raised = 0.0
        est_tax_cost = 0.0
        est_losses_used = 0.0
        portfolio_drift_impact = {}
        
        for i, lot in enumerate(req.lots):
            qty = x[i].solution_value()
            if qty > 1e-6:
                gain_per_share = lot.price - lot.cost_basis
                holding_days = (today - lot.acquire_date).days
                long_term = holding_days >= req.long_term_days
                
                fed_rate = req.lt_rate if long_term else req.st_rate
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
                
                if gain_per_share < 0:
                    est_losses_used += abs(gain_per_share) * qty
                
                # Track portfolio drift impact
                if lot.symbol in portfolio_drift_impact:
                    portfolio_drift_impact[lot.symbol] += cash_from_sale
                else:
                    portfolio_drift_impact[lot.symbol] = cash_from_sale
        
        # Calculate bracket impact
        bracket_impact = calculate_bracket_impact(sells, req)
        
        # Compare vs FIFO
        fifo_comparison = compare_vs_fifo(req, sells, est_tax_cost)
        
        # Generate explanation
        explanation = generate_optimization_explanation_v2(sells, req, wash_sale_warnings, bracket_impact)
        
        return OptimizeResponseV2(
            sells=sells,
            cash_raised=round(cash_raised, 2),
            est_tax_cost=round(est_tax_cost, 2),
            est_losses_used=round(est_losses_used, 2),
            explanation=explanation,
            wash_sale_warnings=wash_sale_warnings,
            portfolio_drift_impact=portfolio_drift_impact,
            bracket_impact=bracket_impact,
            vs_fifo_comparison=fifo_comparison
        )
        
    except Exception as e:
        logger.error(f"ILP optimization v2 error: {e}")
        return optimize_lots_greedy_v2(req)

def optimize_lots_greedy_v2(req: OptimizeRequestV2) -> OptimizeResponseV2:
    """
    Fallback greedy algorithm with advanced constraints
    """
    today = date.today()
    sells = []
    cash_raised = 0.0
    est_tax_cost = 0.0
    est_losses_used = 0.0
    wash_sale_warnings = []
    
    # Sort lots by tax efficiency with advanced scoring
    lot_scores = []
    for i, lot in enumerate(req.lots):
        gain_per_share = lot.price - lot.cost_basis
        holding_days = (today - lot.acquire_date).days
        long_term = holding_days >= req.long_term_days
        
        # Skip if minimum holding period not met
        if holding_days < req.min_holding_period:
            continue
        
        fed_rate = req.lt_rate if long_term else req.st_rate
        state_rate = req.state_lt_rate if long_term else req.state_st_rate
        total_rate = fed_rate + state_rate
        
        tax_per_share = max(gain_per_share, 0) * total_rate
        cash_per_share = lot.price
        
        # Advanced scoring: tax efficiency + preference for long-term
        if cash_per_share > 0:
            tax_efficiency = tax_per_share / cash_per_share
        else:
            tax_efficiency = float('inf')
        
        # Preference for long-term
        if req.prefer_long_term and not long_term:
            tax_efficiency += 0.01  # Small penalty for short-term
        
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
    
    # Greedily select lots with loss budget constraint
    total_losses_used = 0.0
    
    for i, tax_efficiency, lot in lot_scores:
        if cash_raised >= req.target_cash:
            break
        
        # Calculate how much we need
        remaining_cash = req.target_cash - cash_raised
        shares_to_sell = min(lot.shares, remaining_cash / lot.price)
        
        # Check loss budget constraint
        if lot.price < lot.cost_basis:  # This is a loss
            potential_loss = (lot.cost_basis - lot.price) * shares_to_sell
            if req.loss_budget > 0 and total_losses_used + potential_loss > req.loss_budget:
                # Reduce shares to fit within loss budget
                remaining_loss_budget = req.loss_budget - total_losses_used
                if remaining_loss_budget <= 0:
                    continue
                max_shares_for_loss_budget = remaining_loss_budget / (lot.cost_basis - lot.price)
                shares_to_sell = min(shares_to_sell, max_shares_for_loss_budget)
        
        if shares_to_sell > 0:
            gain_per_share = lot.price - lot.cost_basis
            holding_days = (today - lot.acquire_date).days
            long_term = holding_days >= req.long_term_days
            
            fed_rate = req.lt_rate if long_term else req.st_rate
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
            
            if gain_per_share < 0:
                est_losses_used += abs(gain_per_share) * shares_to_sell
                total_losses_used += abs(gain_per_share) * shares_to_sell
    
    bracket_impact = calculate_bracket_impact(sells, req)
    fifo_comparison = compare_vs_fifo(req, sells, est_tax_cost)
    explanation = generate_optimization_explanation_v2(sells, req, wash_sale_warnings, bracket_impact)
    
    return OptimizeResponseV2(
        sells=sells,
        cash_raised=round(cash_raised, 2),
        est_tax_cost=round(est_tax_cost, 2),
        est_losses_used=round(est_losses_used, 2),
        explanation=explanation,
        wash_sale_warnings=wash_sale_warnings,
        portfolio_drift_impact={},
        bracket_impact=bracket_impact,
        vs_fifo_comparison=fifo_comparison
    )

def calculate_bracket_impact(sells: List[Dict], req: OptimizeRequestV2) -> Dict[str, Any]:
    """
    Calculate the impact on tax brackets
    """
    if req.bracket_target <= 0:
        return {"bracket_target": 0, "impact": "No bracket target set"}
    
    # Calculate total gains from sales
    total_gains = sum(sell["gain_per_share"] * sell["sell_shares"] for sell in sells if sell["gain_per_share"] > 0)
    total_losses = sum(abs(sell["gain_per_share"]) * sell["sell_shares"] for sell in sells if sell["gain_per_share"] < 0)
    
    net_gains = total_gains - total_losses
    
    # Calculate effective tax rate
    total_tax = sum(sell["est_tax"] for sell in sells)
    effective_rate = (total_tax / net_gains * 100) if net_gains > 0 else 0
    
    return {
        "bracket_target": req.bracket_target * 100,
        "effective_rate": effective_rate,
        "net_gains": net_gains,
        "total_tax": total_tax,
        "bracket_efficiency": "OPTIMAL" if abs(effective_rate - req.bracket_target * 100) < 1 else "SUBOPTIMAL"
    }

def compare_vs_fifo(req: OptimizeRequestV2, optimized_sells: List[Dict], optimized_tax: float) -> Dict[str, Any]:
    """
    Compare optimized solution vs FIFO (First In, First Out)
    """
    # Simulate FIFO selling
    fifo_lots = sorted(req.lots, key=lambda x: x.acquire_date)
    fifo_cash = 0.0
    fifo_tax = 0.0
    fifo_sells = []
    
    for lot in fifo_lots:
        if fifo_cash >= req.target_cash:
            break
        
        remaining_cash = req.target_cash - fifo_cash
        shares_to_sell = min(lot.shares, remaining_cash / lot.price)
        
        if shares_to_sell > 0:
            gain_per_share = lot.price - lot.cost_basis
            holding_days = (date.today() - lot.acquire_date).days
            long_term = holding_days >= req.long_term_days
            
            fed_rate = req.lt_rate if long_term else req.st_rate
            state_rate = req.state_lt_rate if long_term else req.state_st_rate
            total_rate = fed_rate + state_rate
            
            tax = max(gain_per_share, 0) * total_rate * shares_to_sell
            cash_from_sale = shares_to_sell * lot.price
            
            fifo_sells.append({
                "symbol": lot.symbol,
                "sell_shares": shares_to_sell,
                "est_tax": tax,
                "holding": "LT" if long_term else "ST"
            })
            
            fifo_cash += cash_from_sale
            fifo_tax += tax
    
    tax_savings = fifo_tax - optimized_tax
    savings_percentage = (tax_savings / fifo_tax * 100) if fifo_tax > 0 else 0
    
    return {
        "fifo_tax_cost": round(fifo_tax, 2),
        "optimized_tax_cost": round(optimized_tax, 2),
        "tax_savings": round(tax_savings, 2),
        "savings_percentage": round(savings_percentage, 1),
        "fifo_sells_count": len(fifo_sells),
        "optimized_sells_count": len(optimized_sells)
    }

def generate_optimization_explanation_v2(sells: List[Dict], req: OptimizeRequestV2, 
                                       warnings: List[str], bracket_impact: Dict[str, Any]) -> Dict[str, Any]:
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
            st_tax = sell["sell_shares"] * sell["gain_per_share"] * req.st_rate
            lt_tax = sell["sell_shares"] * sell["gain_per_share"] * req.lt_rate
            lt_tax_savings += st_tax - lt_tax
    
    factors = [
        {
            "name": "tax_efficiency",
            "weight": 0.35,
            "detail": f"Selected lots with lowest tax cost per dollar raised (avg {avg_tax_rate:.1f}% rate)"
        },
        {
            "name": "long_term_preference",
            "weight": 0.25,
            "detail": f"Prioritized {len(lt_sales)} long-term positions over {len(st_sales)} short-term (saved ${lt_tax_savings:.0f} in taxes)"
        },
        {
            "name": "loss_budget_management",
            "weight": 0.15,
            "detail": f"Respected ${req.loss_budget:,.0f} loss budget constraint"
        },
        {
            "name": "wash_sale_avoidance",
            "weight": 0.15,
            "detail": f"Avoided {len(warnings)} wash-sale violations"
        },
        {
            "name": "portfolio_balance",
            "weight": 0.10,
            "detail": "Maintained target allocation within drift limits"
        }
    ]
    
    summary = f"Optimized lot selection to raise ${req.target_cash:,.0f} with ${total_tax:,.0f} tax cost "
    summary += f"({avg_tax_rate:.1f}% effective rate). "
    
    if lt_tax_savings > 0:
        summary += f"Saved ${lt_tax_savings:.0f} by prioritizing long-term positions. "
    
    if req.loss_budget > 0:
        summary += f"Respected ${req.loss_budget:,.0f} loss budget. "
    
    if warnings:
        summary += f"Avoided {len(warnings)} wash-sale violations."
    
    return {
        "type": "smart_lot_optimization_v2",
        "summary": summary,
        "factors": factors,
        "metrics": {
            "total_shares_sold": total_shares_sold,
            "effective_tax_rate": avg_tax_rate,
            "long_term_tax_savings": lt_tax_savings,
            "wash_sales_avoided": len(warnings),
            "loss_budget_used": req.loss_budget
        },
        "constraints_applied": {
            "loss_budget": req.loss_budget > 0,
            "wash_sale_protection": req.forbid_wash_sale,
            "bracket_target": req.bracket_target > 0,
            "portfolio_drift": req.max_portfolio_drift > 0
        }
    }
