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
from .tax_service import TaxService
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
        tax_service = TaxService()
        user = request.user
        
        # Get real portfolio data
        portfolio_data = tax_service.get_user_portfolio_data(user)
        if "error" in portfolio_data:
            return JsonResponse({
                "status": "error", 
                "message": f"Could not retrieve portfolio data: {portfolio_data['error']}"
            }, status=500)
        
        # Get tax loss harvesting opportunities
        opportunities = tax_service.get_tax_loss_harvesting_opportunities(user)
        
        # Calculate total potential savings
        total_potential_savings = sum(opp["potential_tax_savings"] for opp in opportunities)
        
        # Get user's tax bracket (using default income for now)
        tax_bracket = tax_service.calculate_tax_bracket(85000)  # TODO: Get real user income
        
        return JsonResponse({
            "status": "success",
            "recommendations": opportunities,
            "total_potential_savings": total_potential_savings,
            "tax_bracket": tax_bracket["marginal_rate"],
            "realized_gains": portfolio_data.get("realized_gains", {}).get("total_realized_gains", 0),
            "portfolio_summary": {
                "total_value": portfolio_data["total_portfolio_value"],
                "stock_positions": len(portfolio_data.get("stock_positions", [])),
                "crypto_positions": len(portfolio_data.get("crypto_positions", []))
            }
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
        tax_service = TaxService()
        user = request.user
        
        # Get real portfolio data
        portfolio_data = tax_service.get_user_portfolio_data(user)
        if "error" in portfolio_data:
            return JsonResponse({
                "status": "error", 
                "message": f"Could not retrieve portfolio data: {portfolio_data['error']}"
            }, status=500)
        
        strategies = []
        
        # Analyze all positions for optimization opportunities
        all_positions = portfolio_data.get("stock_positions", []) + portfolio_data.get("crypto_positions", [])
        
        for position in all_positions:
            if position["unrealized_gain"] > 0:  # Only analyze gain positions
                # Check if position is close to long-term status
                if not position["is_long_term"] and position["holding_period"] > 300:  # Close to 1 year
                    days_to_long_term = 365 - position["holding_period"]
                    if days_to_long_term > 0:
                        # Calculate tax savings from waiting
                        current_tax = tax_service.calculate_capital_gains_tax(
                            position["unrealized_gain"], 
                            False,  # Short-term
                            85000  # Default income
                        )
                        long_term_tax = tax_service.calculate_capital_gains_tax(
                            position["unrealized_gain"], 
                            True,  # Long-term
                            85000  # Default income
                        )
                        
                        tax_savings = current_tax["tax_amount"] - long_term_tax["tax_amount"]
                        
                        if tax_savings > 0:
                            strategies.append({
                                "symbol": position["symbol"],
                                "type": position.get("type", "STOCK"),
                                "strategy": "WAIT_FOR_LONG_TERM",
                                "current_tax_rate": current_tax["tax_rate"],
                                "long_term_tax_rate": long_term_tax["tax_rate"],
                                "days_to_wait": days_to_long_term,
                                "tax_savings": tax_savings,
                                "unrealized_gain": position["unrealized_gain"],
                                "recommendation": f"Wait {days_to_long_term} days to qualify for long-term capital gains rate (save ${tax_savings:,.2f})"
                            })
        
        # Tax bracket optimization
        tax_bracket = tax_service.calculate_tax_bracket(85000)  # TODO: Get real user income
        
        if tax_bracket["room_for_gains"] > 0:
            strategies.append({
                "strategy": "TAX_BRACKET_OPTIMIZATION",
                "recommendation": f"Consider realizing gains while in {tax_bracket['marginal_rate']*100:.0f}% bracket",
                "current_bracket": f"{tax_bracket['marginal_rate']*100:.0f}%",
                "room_for_gains": tax_bracket["room_for_gains"],
                "potential_savings": f"Up to {tax_bracket['marginal_rate']*100:.0f}% on additional gains"
            })
        
        return JsonResponse({
            "status": "success",
            "strategies": strategies,
            "current_tax_bracket": tax_bracket["marginal_rate"],
            "portfolio_summary": {
                "total_value": portfolio_data["total_portfolio_value"],
                "total_positions": len(all_positions),
                "gain_positions": len([p for p in all_positions if p["unrealized_gain"] > 0])
            }
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
        tax_service = TaxService()
        user = request.user
        
        # Get target allocation from request parameters or use default
        target_allocation = {
            "stocks": float(request.GET.get("stocks", 0.60)),
            "crypto": float(request.GET.get("crypto", 0.20)),
            "cash": float(request.GET.get("cash", 0.20))
        }
        
        # Get real portfolio data
        portfolio_data = tax_service.get_user_portfolio_data(user)
        if "error" in portfolio_data:
            return JsonResponse({
                "status": "error", 
                "message": f"Could not retrieve portfolio data: {portfolio_data['error']}"
            }, status=500)
        
        # Get tax-efficient rebalancing recommendations
        rebalancing_data = tax_service.get_tax_efficient_rebalancing(user, target_allocation)
        
        return JsonResponse({
            "status": "success",
            "rebalancing_actions": rebalancing_data.get("rebalancing_actions", []),
            "current_allocation": rebalancing_data.get("current_allocation", {}),
            "target_allocation": rebalancing_data.get("target_allocation", {}),
            "total_tax_impact": rebalancing_data.get("tax_impact", {}).get("total_taxes", 0),
            "rebalancing_efficiency": "HIGH" if rebalancing_data.get("tax_impact", {}).get("total_taxes", 0) < 1000 else "MEDIUM"
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
        tax_service = TaxService()
        user = request.user
        
        # Get user income from request or use default
        user_income = float(request.GET.get("income", 85000))  # TODO: Get from user profile
        
        # Get real portfolio data
        portfolio_data = tax_service.get_user_portfolio_data(user)
        if "error" in portfolio_data:
            return JsonResponse({
                "status": "error", 
                "message": f"Could not retrieve portfolio data: {portfolio_data['error']}"
            }, status=500)
        
        # Calculate projected gains from portfolio
        all_positions = portfolio_data.get("stock_positions", []) + portfolio_data.get("crypto_positions", [])
        projected_gains = sum(pos["unrealized_gain"] for pos in all_positions if pos["unrealized_gain"] > 0)
        
        # Calculate tax bracket information
        tax_bracket = tax_service.calculate_tax_bracket(user_income)
        
        analysis = {
            "current_situation": {
                "taxable_income": user_income,
                "current_bracket": f"{tax_bracket['marginal_rate']*100:.0f}%",
                "marginal_rate": f"{tax_bracket['marginal_rate']*100:.0f}%",
                "effective_rate": f"{tax_bracket['effective_rate']*100:.0f}%"
            },
            "bracket_proximity": {
                "next_bracket_threshold": tax_bracket.get("next_bracket_threshold"),
                "distance_to_next": tax_bracket.get("room_for_gains", 0),
                "room_for_gains": tax_bracket.get("room_for_gains", 0)
            },
            "optimization_strategies": []
        }
        
        # Generate optimization strategies based on real data
        if projected_gains > 0:
            if user_income + projected_gains > (tax_bracket.get("next_bracket_threshold") or float('inf')):
                analysis["optimization_strategies"].append({
                    "strategy": "DEFER_GAINS",
                    "description": "Consider deferring some gains to next year to stay in current bracket",
                    "potential_savings": min(projected_gains, tax_bracket.get("room_for_gains", 0)) * 0.02,  # 2% bracket difference
                    "priority": "HIGH"
                })
            
            if user_income < 44725:  # Lower bracket threshold
                analysis["optimization_strategies"].append({
                    "strategy": "REALIZE_GAINS",
                    "description": "Consider realizing gains while in lower tax bracket",
                    "potential_savings": min(projected_gains, 44725 - user_income) * 0.10,  # 10% bracket difference
                    "priority": "HIGH"
                })
        
        # Roth IRA optimization
        if user_income < 138000:  # Roth IRA income limit
            analysis["optimization_strategies"].append({
                "strategy": "ROTH_CONVERSION",
                "description": "Consider Roth IRA conversion while in current tax bracket",
                "potential_savings": "Tax-free growth on converted amount",
                "priority": "MEDIUM"
            })
        
        return JsonResponse({
            "status": "success",
            "analysis": analysis,
            "tax_brackets": tax_service.tax_brackets_2024,
            "recommendations": analysis["optimization_strategies"],
            "portfolio_summary": {
                "total_value": portfolio_data["total_portfolio_value"],
                "projected_gains": projected_gains,
                "total_positions": len(all_positions)
            }
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
        tax_service = TaxService()
        user = request.user
        
        # Get real portfolio data
        portfolio_data = tax_service.get_user_portfolio_data(user)
        if "error" in portfolio_data:
            return JsonResponse({
                "status": "error", 
                "message": f"Could not retrieve portfolio data: {portfolio_data['error']}"
            }, status=500)
        
        # Get all optimization opportunities
        loss_harvesting_opps = tax_service.get_tax_loss_harvesting_opportunities(user)
        rebalancing_data = tax_service.get_tax_efficient_rebalancing(user, {"stocks": 0.60, "crypto": 0.20, "cash": 0.20})
        
        # Calculate total potential savings
        loss_harvesting_savings = sum(opp["potential_tax_savings"] for opp in loss_harvesting_opps)
        rebalancing_tax_impact = rebalancing_data.get("tax_impact", {}).get("total_taxes", 0)
        
        # Count opportunities by priority
        high_priority = len([opp for opp in loss_harvesting_opps if opp["priority"] == "HIGH"])
        medium_priority = len([opp for opp in loss_harvesting_opps if opp["priority"] == "MEDIUM"])
        low_priority = len([opp for opp in loss_harvesting_opps if opp["priority"] == "LOW"])
        
        # Calculate tax efficiency score
        total_value = portfolio_data["total_portfolio_value"]
        total_gains = sum(pos["unrealized_gain"] for pos in portfolio_data.get("stock_positions", []) + portfolio_data.get("crypto_positions", []) if pos["unrealized_gain"] > 0)
        tax_efficiency_score = min(100, max(0, 100 - (total_gains / total_value * 100) if total_value > 0 else 100))
        
        # Build key opportunities list
        key_opportunities = []
        
        # Add loss harvesting opportunities
        for opp in loss_harvesting_opps[:3]:  # Top 3
            key_opportunities.append({
                "type": "TAX_LOSS_HARVESTING",
                "description": f"Realize ${abs(opp['unrealized_loss']):,.2f} loss on {opp['symbol']}",
                "potential_savings": opp["potential_tax_savings"],
                "priority": opp["priority"],
                "deadline": "December 31, 2024"
            })
        
        # Add rebalancing opportunities
        rebalancing_actions = rebalancing_data.get("rebalancing_actions", [])
        if rebalancing_actions:
            key_opportunities.append({
                "type": "TAX_EFFICIENT_REBALANCING",
                "description": f"Rebalance portfolio with ${rebalancing_tax_impact:,.2f} tax impact",
                "potential_savings": -rebalancing_tax_impact,  # Negative because it's a cost
                "priority": "MEDIUM",
                "deadline": "Ongoing"
            })
        
        summary = {
            "total_potential_savings": loss_harvesting_savings,
            "high_priority_actions": high_priority,
            "medium_priority_actions": medium_priority,
            "low_priority_actions": low_priority,
            "next_deadline": "December 31, 2024",
            "key_opportunities": key_opportunities,
            "estimated_annual_savings": loss_harvesting_savings,
            "tax_efficiency_score": tax_efficiency_score,
            "portfolio_summary": {
                "total_value": total_value,
                "total_positions": len(portfolio_data.get("stock_positions", []) + portfolio_data.get("crypto_positions", [])),
                "unrealized_gains": total_gains,
                "unrealized_losses": sum(pos["unrealized_gain"] for pos in portfolio_data.get("stock_positions", []) + portfolio_data.get("crypto_positions", []) if pos["unrealized_gain"] < 0)
            }
        }
        
        return JsonResponse({
            "status": "success",
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Tax optimization summary error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
