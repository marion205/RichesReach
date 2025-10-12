from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from graphene_django.views import GraphQLView
import os
import json

# GraphQL view
graphql_view = csrf_exempt(GraphQLView.as_view(graphiql=True))

def stock_viewer(request):
    """Simple view to serve the stock viewer HTML page"""
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'stock_viewer.html')
    with open(html_file_path, 'r') as f:
        html_content = f.read()
    return HttpResponse(html_content)

def ai_stock_dashboard(request):
    """AI-powered stock dashboard with ML recommendations"""
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'ai_stock_dashboard.html')
    with open(html_file_path, 'r') as f:
        html_content = f.read()
    return HttpResponse(html_content)

def industry_stock_page(request):
    """Industry-standard AI/ML stock analysis platform"""
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'industry_standard_stock_page.html')
    with open(html_file_path, 'r') as f:
        html_content = f.read()
    return HttpResponse(html_content)

@csrf_exempt
def ai_options_recommendations(request):
    """AI Options Recommendations REST endpoint"""
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        return HttpResponseBadRequest(f"Invalid JSON: {str(e)}")

    # Extract parameters from payload
    symbol = payload.get("symbol", "AAPL")
    portfolio_value = payload.get("portfolio_value", 10000)
    risk_tolerance = payload.get("risk_tolerance", "moderate")
    
    # TODO: Implement real AI recommendations service
    recommendations = [
        {
            "strategy": "Covered Call",
            "symbol": symbol,
            "strike": 150.0,
            "expiration": "2024-01-19",
            "premium": 2.50,
            "max_profit": 250.0,
            "max_loss": -1000.0,
            "probability_of_profit": 0.65,
            "description": f"Generate income on {symbol} while maintaining upside potential"
        },
        {
            "strategy": "Protective Put",
            "symbol": symbol,
            "strike": 145.0,
            "expiration": "2024-01-19",
            "premium": 1.80,
            "max_profit": "unlimited",
            "max_loss": -180.0,
            "probability_of_profit": 0.45,
            "description": f"Protect {symbol} position from downside risk"
        },
        {
            "strategy": "Iron Condor",
            "symbol": symbol,
            "strikes": [140, 145, 155, 160],
            "expiration": "2024-01-19",
            "premium": 1.20,
            "max_profit": 120.0,
            "max_loss": -380.0,
            "probability_of_profit": 0.70,
            "description": f"Neutral strategy on {symbol} with defined risk/reward"
        }
    ]
    
    data = {
        "message": "AI options recommendations generated successfully",
        "input": {
            "symbol": symbol,
            "portfolio_value": portfolio_value,
            "risk_tolerance": risk_tolerance
        },
        "recommendations": recommendations,
        "market_analysis": {
            "current_price": 147.50,
            "implied_volatility": 0.25,
            "market_sentiment": "bullish",
            "recommended_allocation": "5-10% of portfolio"
        }
    }
    
    return JsonResponse(data, status=200)