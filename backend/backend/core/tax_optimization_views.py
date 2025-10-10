#!/usr/bin/env python3
"""
Tax Optimization Premium Features
Premium tier tax optimization tools for RichesReach AI
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .premium_models import require_premium_feature
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

@require_premium_feature('tax_loss_harvesting')
@login_required
@require_http_methods(["GET"])
def tax_loss_harvesting(request):
    """
    Tax-loss harvesting recommendations
    Identifies opportunities to realize losses to offset gains
    """
    try:
        # Mock implementation - replace with real tax logic
        user_portfolio = {
            "positions": [
                {"symbol": "AAPL", "shares": 100, "cost_basis": 150.00, "current_price": 140.00, "unrealized_loss": -1000.00},
                {"symbol": "TSLA", "shares": 50, "cost_basis": 200.00, "current_price": 180.00, "unrealized_loss": -1000.00},
                {"symbol": "MSFT", "shares": 75, "cost_basis": 300.00, "current_price": 320.00, "unrealized_gain": 1500.00},
            ],
            "realized_gains": 5000.00,
            "tax_bracket": 0.22
        }
        
        recommendations = []
        
        # Find positions with unrealized losses
        for position in user_portfolio["positions"]:
            if position["unrealized_loss"] < 0:
                potential_tax_savings = abs(position["unrealized_loss"]) * user_portfolio["tax_bracket"]
                recommendations.append({
                    "symbol": position["symbol"],
                    "action": "SELL",
                    "shares": position["shares"],
                    "unrealized_loss": position["unrealized_loss"],
                    "potential_tax_savings": potential_tax_savings,
                    "reason": f"Realize loss to offset ${position['unrealized_loss']:,.2f} in gains",
                    "priority": "HIGH" if abs(position["unrealized_loss"]) > 1000 else "MEDIUM"
                })
        
        # Sort by potential tax savings
        recommendations.sort(key=lambda x: x["potential_tax_savings"], reverse=True)
        
        return JsonResponse({
            "status": "success",
            "recommendations": recommendations,
            "total_potential_savings": sum(r["potential_tax_savings"] for r in recommendations),
            "tax_bracket": user_portfolio["tax_bracket"],
            "realized_gains": user_portfolio["realized_gains"]
        })
        
    except Exception as e:
        logger.error(f"Tax loss harvesting error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_premium_feature('capital_gains_optimization')
@login_required
@require_http_methods(["GET"])
def capital_gains_optimization(request):
    """
    Capital gains optimization strategies
    Optimizes timing and method of realizing gains
    """
    try:
        # Mock implementation - replace with real optimization logic
        user_data = {
            "income": 100000,
            "tax_bracket": 0.22,
            "long_term_positions": [
                {"symbol": "AAPL", "shares": 100, "cost_basis": 100.00, "current_price": 150.00, "holding_period": 400},
                {"symbol": "GOOGL", "shares": 50, "cost_basis": 2000.00, "current_price": 2500.00, "holding_period": 200},
            ],
            "short_term_positions": [
                {"symbol": "TSLA", "shares": 25, "cost_basis": 200.00, "current_price": 220.00, "holding_period": 100},
            ]
        }
        
        strategies = []
        
        # Long-term vs short-term optimization
        for position in user_data["long_term_positions"]:
            if position["holding_period"] < 365:
                days_to_long_term = 365 - position["holding_period"]
                strategies.append({
                    "symbol": position["symbol"],
                    "strategy": "WAIT_FOR_LONG_TERM",
                    "current_tax_rate": 0.22,  # Short-term rate
                    "long_term_tax_rate": 0.15,  # Long-term rate
                    "days_to_wait": days_to_long_term,
                    "tax_savings": (position["current_price"] - position["cost_basis"]) * position["shares"] * (0.22 - 0.15),
                    "recommendation": f"Wait {days_to_long_term} days to qualify for long-term capital gains rate"
                })
        
        # Tax bracket optimization
        current_income = user_data["income"]
        if current_income < 40000:  # 0% long-term rate
            strategies.append({
                "strategy": "TAX_BRACKET_OPTIMIZATION",
                "recommendation": "Consider realizing gains while in 0% long-term capital gains bracket",
                "current_bracket": "0%",
                "potential_savings": "Up to 15% on long-term gains"
            })
        
        return JsonResponse({
            "status": "success",
            "strategies": strategies,
            "current_tax_bracket": user_data["tax_bracket"],
            "income": user_data["income"]
        })
        
    except Exception as e:
        logger.error(f"Capital gains optimization error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_premium_feature('tax_efficient_rebalancing')
@login_required
@require_http_methods(["GET"])
def tax_efficient_rebalancing(request):
    """
    Tax-efficient portfolio rebalancing
    Minimizes tax impact while maintaining target allocation
    """
    try:
        # Mock implementation - replace with real rebalancing logic
        portfolio = {
            "current_allocation": {
                "stocks": 0.70,
                "bonds": 0.20,
                "cash": 0.10
            },
            "target_allocation": {
                "stocks": 0.60,
                "bonds": 0.30,
                "cash": 0.10
            },
            "positions": [
                {"symbol": "VTI", "type": "stocks", "value": 70000, "cost_basis": 60000, "unrealized_gain": 10000},
                {"symbol": "BND", "type": "bonds", "value": 20000, "cost_basis": 20000, "unrealized_gain": 0},
                {"symbol": "CASH", "type": "cash", "value": 10000, "cost_basis": 10000, "unrealized_gain": 0},
            ],
            "total_value": 100000
        }
        
        rebalancing_actions = []
        
        # Calculate rebalancing needs
        target_stocks = portfolio["total_value"] * portfolio["target_allocation"]["stocks"]
        target_bonds = portfolio["total_value"] * portfolio["target_allocation"]["bonds"]
        
        current_stocks = sum(p["value"] for p in portfolio["positions"] if p["type"] == "stocks")
        current_bonds = sum(p["value"] for p in portfolio["positions"] if p["type"] == "bonds")
        
        stocks_to_sell = current_stocks - target_stocks
        bonds_to_buy = target_bonds - current_bonds
        
        if stocks_to_sell > 0:
            # Find positions with lowest tax impact
            stock_positions = [p for p in portfolio["positions"] if p["type"] == "stocks"]
            stock_positions.sort(key=lambda x: x["unrealized_gain"])  # Sell lowest gains first
            
            for position in stock_positions:
                if stocks_to_sell <= 0:
                    break
                
                sell_amount = min(stocks_to_sell, position["value"])
                sell_percentage = sell_amount / position["value"]
                shares_to_sell = int(position["value"] / position["value"] * sell_percentage * 100)  # Mock calculation
                
                rebalancing_actions.append({
                    "action": "SELL",
                    "symbol": position["symbol"],
                    "shares": shares_to_sell,
                    "value": sell_amount,
                    "tax_impact": position["unrealized_gain"] * sell_percentage * 0.15,  # Long-term rate
                    "reason": "Rebalance to target allocation"
                })
                
                stocks_to_sell -= sell_amount
        
        if bonds_to_buy > 0:
            rebalancing_actions.append({
                "action": "BUY",
                "symbol": "BND",
                "value": bonds_to_buy,
                "tax_impact": 0,
                "reason": "Rebalance to target allocation"
            })
        
        return JsonResponse({
            "status": "success",
            "rebalancing_actions": rebalancing_actions,
            "current_allocation": portfolio["current_allocation"],
            "target_allocation": portfolio["target_allocation"],
            "total_tax_impact": sum(action["tax_impact"] for action in rebalancing_actions),
            "rebalancing_efficiency": "HIGH" if sum(action["tax_impact"] for action in rebalancing_actions) < 1000 else "MEDIUM"
        })
        
    except Exception as e:
        logger.error(f"Tax efficient rebalancing error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_premium_feature('tax_bracket_analysis')
@login_required
@require_http_methods(["GET"])
def tax_bracket_analysis(request):
    """
    Tax bracket analysis and optimization
    Analyzes current tax situation and provides optimization strategies
    """
    try:
        # Mock implementation - replace with real tax analysis
        user_data = {
            "income": 85000,
            "filing_status": "single",
            "deductions": 12000,
            "taxable_income": 73000,
            "current_tax_bracket": 0.22,
            "marginal_rate": 0.22,
            "effective_rate": 0.15,
            "projected_gains": 15000,
            "projected_dividends": 3000
        }
        
        # Tax bracket thresholds for 2024 (single filer)
        brackets = [
            {"min": 0, "max": 11000, "rate": 0.10},
            {"min": 11000, "max": 44725, "rate": 0.12},
            {"min": 44725, "max": 95375, "rate": 0.22},
            {"min": 95375, "max": 182050, "rate": 0.24},
        ]
        
        analysis = {
            "current_situation": {
                "taxable_income": user_data["taxable_income"],
                "current_bracket": f"{user_data['current_tax_bracket']*100:.0f}%",
                "marginal_rate": f"{user_data['marginal_rate']*100:.0f}%",
                "effective_rate": f"{user_data['effective_rate']*100:.0f}%"
            },
            "bracket_proximity": {
                "next_bracket_threshold": 95375,
                "distance_to_next": 95375 - user_data["taxable_income"],
                "room_for_gains": max(0, 95375 - user_data["taxable_income"])
            },
            "optimization_strategies": []
        }
        
        # Generate optimization strategies
        if user_data["taxable_income"] + user_data["projected_gains"] > 95375:
            analysis["optimization_strategies"].append({
                "strategy": "DEFER_GAINS",
                "description": "Consider deferring some gains to next year to stay in current bracket",
                "potential_savings": (user_data["projected_gains"] - analysis["bracket_proximity"]["room_for_gains"]) * (0.24 - 0.22),
                "priority": "HIGH"
            })
        
        if user_data["taxable_income"] < 44725:
            analysis["optimization_strategies"].append({
                "strategy": "REALIZE_GAINS",
                "description": "Consider realizing gains while in lower tax bracket",
                "potential_savings": min(user_data["projected_gains"], 44725 - user_data["taxable_income"]) * (0.22 - 0.12),
                "priority": "HIGH"
            })
        
        # Roth IRA optimization
        if user_data["income"] < 138000:  # Roth IRA income limit
            analysis["optimization_strategies"].append({
                "strategy": "ROTH_CONVERSION",
                "description": "Consider Roth IRA conversion while in current tax bracket",
                "potential_savings": "Tax-free growth on converted amount",
                "priority": "MEDIUM"
            })
        
        return JsonResponse({
            "status": "success",
            "analysis": analysis,
            "tax_brackets": brackets,
            "recommendations": analysis["optimization_strategies"]
        })
        
    except Exception as e:
        logger.error(f"Tax bracket analysis error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_premium_feature('tax_optimization_summary')
@login_required
@require_http_methods(["GET"])
def tax_optimization_summary(request):
    """
    Comprehensive tax optimization summary
    Provides overview of all tax optimization opportunities
    """
    try:
        # Mock implementation - replace with real summary logic
        summary = {
            "total_potential_savings": 3500,
            "high_priority_actions": 3,
            "medium_priority_actions": 2,
            "low_priority_actions": 1,
            "next_deadline": "December 31, 2024",
            "key_opportunities": [
                {
                    "type": "TAX_LOSS_HARVESTING",
                    "description": "Realize $2,000 in losses to offset gains",
                    "potential_savings": 440,
                    "priority": "HIGH",
                    "deadline": "December 31, 2024"
                },
                {
                    "type": "CAPITAL_GAINS_OPTIMIZATION",
                    "description": "Wait 45 days for long-term capital gains rate",
                    "potential_savings": 1200,
                    "priority": "HIGH",
                    "deadline": "45 days"
                },
                {
                    "type": "TAX_BRACKET_OPTIMIZATION",
                    "description": "Defer $5,000 in gains to next year",
                    "potential_savings": 100,
                    "priority": "MEDIUM",
                    "deadline": "December 31, 2024"
                }
            ],
            "estimated_annual_savings": 3500,
            "tax_efficiency_score": 85
        }
        
        return JsonResponse({
            "status": "success",
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Tax optimization summary error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
