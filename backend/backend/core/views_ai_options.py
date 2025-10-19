"""
AI Options REST API Views
"""
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
import json
from datetime import datetime, timedelta
import random

@csrf_exempt  # dev only; swap for proper CSRF/JWT middleware later
def ai_options_recommendations(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    symbol = (body.get("symbol") or "AAPL").upper()
    risk = (body.get("user_risk_tolerance") or body.get("riskTolerance") or "medium").lower()
    pv = float(body.get("portfolio_value") or body.get("portfolioValue") or 10000)
    horizon = int(body.get("time_horizon") or body.get("timeHorizon") or 30)
    max_recs = int(body.get("max_recommendations") or body.get("maxRecommendations") or 5)

    # Generate mock recommendations based on risk tolerance
    exp1 = (datetime.utcnow() + timedelta(days=horizon)).strftime("%Y-%m-%d")
    exp2 = (datetime.utcnow() + timedelta(days=horizon+14)).strftime("%Y-%m-%d")
    exp3 = (datetime.utcnow() + timedelta(days=horizon+30)).strftime("%Y-%m-%d")
    
    # Base price for calculations
    base_price = 150.0 + random.uniform(-10, 10)
    
    recs = []
    
    if risk == "low":
        # Conservative strategies
        recs.extend([
            {
                "strategy_name": "Cash Secured Put",
                "strategy_type": "income",
                "confidence_score": 85,
                "symbol": symbol,
                "current_price": base_price,
                "options": [{
                    "type": "put",
                    "action": "sell",
                    "strike": round(base_price * 0.95, 2),
                    "expiration": exp1,
                    "premium": round(base_price * 0.02, 2),
                    "quantity": 1
                }],
                "analytics": {
                    "max_profit": round(base_price * 0.02, 2),
                    "max_loss": round(base_price * 0.95, 2),
                    "probability_of_profit": 0.68,
                    "expected_return": 0.018,
                    "breakeven": round(base_price * 0.95, 2)
                },
                "reasoning": {
                    "market_outlook": "Neutral to slightly bullish",
                    "strategy_rationale": "Generate income while providing downside protection",
                    "risk_factors": ["Stock could be assigned", "Limited upside participation"],
                    "key_benefits": ["Income generation", "Lower cost basis if assigned", "Defined risk"]
                },
                "risk_score": 25,
                "days_to_expiration": horizon,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "strategy_name": "Covered Call",
                "strategy_type": "income",
                "confidence_score": 80,
                "symbol": symbol,
                "current_price": base_price,
                "options": [{
                    "type": "call",
                    "action": "sell",
                    "strike": round(base_price * 1.05, 2),
                    "expiration": exp1,
                    "premium": round(base_price * 0.015, 2),
                    "quantity": 1
                }],
                "analytics": {
                    "max_profit": round(base_price * 0.065, 2),
                    "max_loss": round(base_price * 0.95, 2),
                    "probability_of_profit": 0.72,
                    "expected_return": 0.015,
                    "breakeven": round(base_price * 0.985, 2)
                },
                "reasoning": {
                    "market_outlook": "Neutral to slightly bearish",
                    "strategy_rationale": "Generate income from existing stock position",
                    "risk_factors": ["Stock could be called away", "Limited upside participation"],
                    "key_benefits": ["Income generation", "Downside protection", "High probability of profit"]
                },
                "risk_score": 20,
                "days_to_expiration": horizon,
                "created_at": datetime.utcnow().isoformat()
            }
        ])
    
    elif risk == "medium":
        # Moderate strategies
        recs.extend([
            {
                "strategy_name": "Iron Condor",
                "strategy_type": "neutral",
                "confidence_score": 75,
                "symbol": symbol,
                "current_price": base_price,
                "options": [
                    {
                        "type": "call",
                        "action": "sell",
                        "strike": round(base_price * 1.03, 2),
                        "expiration": exp2,
                        "premium": round(base_price * 0.01, 2),
                        "quantity": 1
                    },
                    {
                        "type": "call",
                        "action": "buy",
                        "strike": round(base_price * 1.08, 2),
                        "expiration": exp2,
                        "premium": round(base_price * 0.005, 2),
                        "quantity": 1
                    },
                    {
                        "type": "put",
                        "action": "sell",
                        "strike": round(base_price * 0.97, 2),
                        "expiration": exp2,
                        "premium": round(base_price * 0.01, 2),
                        "quantity": 1
                    },
                    {
                        "type": "put",
                        "action": "buy",
                        "strike": round(base_price * 0.92, 2),
                        "expiration": exp2,
                        "premium": round(base_price * 0.005, 2),
                        "quantity": 1
                    }
                ],
                "analytics": {
                    "max_profit": round(base_price * 0.01, 2),
                    "max_loss": round(base_price * 0.04, 2),
                    "probability_of_profit": 0.65,
                    "expected_return": 0.12,
                    "breakeven": round(base_price * 0.99, 2)
                },
                "reasoning": {
                    "market_outlook": "Neutral",
                    "strategy_rationale": "Profit from low volatility and range-bound movement",
                    "risk_factors": ["Large moves can cause significant losses", "Complex position management"],
                    "key_benefits": ["Defined risk", "High probability of profit", "Works in low volatility"]
                },
                "risk_score": 45,
                "days_to_expiration": horizon + 14,
                "created_at": datetime.utcnow().isoformat()
            }
        ])
    
    else:  # high risk
        # Aggressive strategies
        recs.extend([
            {
                "strategy_name": "Long Straddle",
                "strategy_type": "volatility",
                "confidence_score": 70,
                "symbol": symbol,
                "current_price": base_price,
                "options": [
                    {
                        "type": "call",
                        "action": "buy",
                        "strike": round(base_price, 2),
                        "expiration": exp3,
                        "premium": round(base_price * 0.03, 2),
                        "quantity": 1
                    },
                    {
                        "type": "put",
                        "action": "buy",
                        "strike": round(base_price, 2),
                        "expiration": exp3,
                        "premium": round(base_price * 0.03, 2),
                        "quantity": 1
                    }
                ],
                "analytics": {
                    "max_profit": float('inf'),
                    "max_loss": round(base_price * 0.06, 2),
                    "probability_of_profit": 0.35,
                    "expected_return": 0.25,
                    "breakeven": round(base_price * 1.06, 2)
                },
                "reasoning": {
                    "market_outlook": "High volatility expected",
                    "strategy_rationale": "Profit from large moves in either direction",
                    "risk_factors": ["Time decay", "High cost", "Low probability of profit"],
                    "key_benefits": ["Unlimited upside", "Works in both directions", "High reward potential"]
                },
                "risk_score": 80,
                "days_to_expiration": horizon + 30,
                "created_at": datetime.utcnow().isoformat()
            }
        ])

    # Limit to requested number of recommendations
    recs = recs[:max_recs]

    # Generate market analysis
    market_analysis = {
        "symbol": symbol,
        "current_price": base_price,
        "volatility": 0.25 + random.uniform(-0.05, 0.05),
        "implied_volatility": 0.28 + random.uniform(-0.03, 0.03),
        "volume": random.randint(1000000, 5000000),
        "market_cap": random.randint(1000000000, 3000000000),
        "sector": "Technology",
        "sentiment_score": random.uniform(-0.5, 0.5),
        "trend_direction": random.choice(["bullish", "bearish", "neutral"]),
        "support_levels": [round(base_price * 0.95, 2), round(base_price * 0.90, 2)],
        "resistance_levels": [round(base_price * 1.05, 2), round(base_price * 1.10, 2)],
        "dividend_yield": random.uniform(0.01, 0.03),
        "beta": random.uniform(0.8, 1.5)
    }

    return JsonResponse({
        "symbol": symbol,
        "current_price": base_price,
        "recommendations": recs,
        "market_analysis": market_analysis,
        "generated_at": datetime.utcnow().isoformat(),
        "total_recommendations": len(recs)
    })
