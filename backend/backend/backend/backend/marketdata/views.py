# marketdata/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import logging
from .service import MarketDataService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def ai_options_recommendations(request):
    """AI options recommendations endpoint with real market data"""
    try:
        body = json.loads(request.body or "{}")
        symbol = body.get("symbol", "AAPL").upper()
        portfolio_value = body.get("portfolio_value", 10000)
        time_horizon = body.get("time_horizon", 30)
        user_risk_tolerance = body.get("user_risk_tolerance", "medium")
        max_recommendations = body.get("max_recommendations", 5)
        
        logger.info(f"AI options request for {symbol}: ${portfolio_value}, {time_horizon}d, {user_risk_tolerance}")
        
        # Get real market data
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
        return JsonResponse({
            "ok": False,
            "error": str(e),
            "recommendations": []
        }, status=500)

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
def market_data_status(request):
    """Get market data service status"""
    try:
        service = MarketDataService()
        provider_status = service.get_provider_status()
        
        return JsonResponse({
            "status": "operational",
            "providers": provider_status,
            "cache_available": service.redis_client is not None if hasattr(service, 'redis_client') else False
        })
        
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "error": str(e)
        }, status=500)