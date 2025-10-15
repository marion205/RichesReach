# backend/core/views_ai.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def ai_options_recommendations(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        body = {}
    
    symbol = body.get("symbol", "AAPL").upper()
    portfolio_value = body.get("portfolio_value", 10000)
    time_horizon = body.get("time_horizon", 30)
    user_risk_tolerance = body.get("user_risk_tolerance", "medium")
    max_recommendations = body.get("max_recommendations", 5)
    
    logger.info(f"AI options request for {symbol}: ${portfolio_value}, {time_horizon}d, {user_risk_tolerance}")
    
    # Get real market data
    try:
        from .market_data_service import MarketDataService
        service = MarketDataService()
        
        # Get current quote
        try:
            quote_data = service.get_quote(symbol)
            current_price = quote_data.get("price", 100.0)
            provider = quote_data.get("provider", "unknown")
        except Exception as e:
            logger.warning(f"Failed to get quote for {symbol}: {e}")
            current_price = 100.0  # Fallback
            provider = "fallback"
        
        # Get options chain
        try:
            options_data = service.get_options_chain(symbol, limit=20)
            contracts = options_data.get("contracts", [])
            options_provider = options_data.get("provider", "unknown")
        except Exception as e:
            logger.warning(f"Failed to get options for {symbol}: {e}")
            contracts = []
            options_provider = "fallback"
        
        # Generate recommendations based on real data
        recommendations = _generate_options_recommendations(
            symbol=symbol,
            current_price=current_price,
            contracts=contracts,
            portfolio_value=portfolio_value,
            time_horizon=time_horizon,
            risk_tolerance=user_risk_tolerance,
            max_recommendations=max_recommendations
        )
        
        return JsonResponse({
            "ok": True,
            "symbol": symbol,
            "current_price": current_price,
            "data_providers": {
                "quote": provider,
                "options": options_provider
            },
            "recommendations": recommendations,
            "market_data_available": len(contracts) > 0
        })
        
    except Exception as e:
        logger.error(f"AI options recommendations error: {e}")
        # Fallback to basic recommendations
        return JsonResponse({
            "ok": True,
            "symbol": symbol,
            "current_price": 100.0,
            "data_providers": {
                "quote": "fallback",
                "options": "fallback"
            },
            "recommendations": [
                {
                    "strategy": "Cash-secured Put",
                    "symbol": symbol,
                    "expirationDays": time_horizon,
                    "strike": "ATM-1",
                    "rationale": "Income with downside buffer"
                },
                {
                    "strategy": "Covered Call",
                    "symbol": symbol,
                    "expirationDays": time_horizon,
                    "strike": "OTM+1",
                    "rationale": "Harvest premium"
                }
            ],
            "market_data_available": False
        })

def _generate_options_recommendations(symbol, current_price, contracts, portfolio_value, 
                                    time_horizon, risk_tolerance, max_recommendations):
    """Generate options recommendations based on market data and user profile"""
    
    recommendations = []
    
    # Filter contracts by time horizon (approximate)
    relevant_contracts = []
    for contract in contracts:
        if contract.get("expiration"):
            # Simple filtering - in real implementation, parse expiration dates
            relevant_contracts.append(contract)
    
    # If we have real options data, use it
    if relevant_contracts:
        # Generate recommendations based on real options
        for i, contract in enumerate(relevant_contracts[:max_recommendations]):
            contract_type = contract.get("type", "CALL")
            strike = contract.get("strike", current_price)
            expiration = contract.get("expiration", "2024-12-20")
            
            if contract_type == "CALL" and strike > current_price:
                # Out-of-the-money call
                strategy = "Call Debit Spread" if risk_tolerance == "high" else "Covered Call"
                rationale = f"Bullish play with {strike} strike"
            elif contract_type == "PUT" and strike < current_price:
                # Out-of-the-money put
                strategy = "Put Credit Spread" if risk_tolerance == "low" else "Cash-Secured Put"
                rationale = f"Bearish hedge or income generation"
            else:
                # At-the-money or in-the-money
                strategy = "Straddle" if risk_tolerance == "high" else "Covered Call"
                rationale = f"Volatility play at {strike} strike"
            
            recommendations.append({
                "strategy": strategy,
                "symbol": symbol,
                "expirationDays": time_horizon,
                "strike": f"${strike}",
                "rationale": rationale,
                "contractType": contract_type,
                "bid": contract.get("bid"),
                "ask": contract.get("ask"),
                "volume": contract.get("volume"),
                "openInterest": contract.get("open_interest")
            })
    
    # If no real options data, generate mock recommendations
    if not recommendations:
        mock_strategies = [
            {
                "strategy": "Covered Call",
                "symbol": symbol,
                "expirationDays": time_horizon,
                "strike": f"${current_price * 1.02:.0f}",
                "rationale": "Income generation with upside participation"
            },
            {
                "strategy": "Cash-Secured Put",
                "symbol": symbol,
                "expirationDays": time_horizon,
                "strike": f"${current_price * 0.98:.0f}",
                "rationale": "Income with potential stock acquisition"
            }
        ]
        
        if risk_tolerance == "high":
            mock_strategies.append({
                "strategy": "Call Debit Spread",
                "symbol": symbol,
                "expirationDays": time_horizon,
                "strike": f"${current_price * 1.01:.0f}/${current_price * 1.05:.0f}",
                "rationale": "Leveraged bullish play with defined risk"
            })
        
        recommendations = mock_strategies[:max_recommendations]
    
    return recommendations

@csrf_exempt
def ai_status(request):
    """AI status endpoint for feature flag checking"""
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)
    
    return JsonResponse({
        "ai_enabled": settings.USE_OPENAI,
        "model": settings.OPENAI_MODEL if settings.USE_OPENAI else None,
        "fallback_enabled": settings.OPENAI_ENABLE_FALLBACK,
        "environment": "development" if settings.DEBUG else "production",
        "status": "operational"
    }, status=200)

@csrf_exempt
def cache_status(request):
    """Cache status and management endpoint"""
    if request.method == "GET":
        # Get cache statistics
        try:
            from .market_data_service import MarketDataService
            service = MarketDataService()
            stats = service.get_cache_stats()
            return JsonResponse(stats, status=200)
        except Exception as e:
            logger.error(f"Cache status error: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    elif request.method == "POST":
        # Clear cache
        try:
            body = json.loads(request.body.decode("utf-8"))
            pattern = body.get("pattern", None)
            
            from .market_data_service import MarketDataService
            service = MarketDataService()
            result = service.clear_cache(pattern)
            return JsonResponse(result, status=200)
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    else:
        return JsonResponse({"error": "GET or POST only"}, status=405)
