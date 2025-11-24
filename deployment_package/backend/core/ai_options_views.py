"""
Django views for AI Options API endpoints
Provides REST API for AI-Powered Options Recommendations
"""
import json
import logging
import asyncio
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .ai_options_engine import AIOptionsEngine

logger = logging.getLogger(__name__)

# Initialize AI engine
ai_engine = AIOptionsEngine()


def make_json_safe(obj):
    """Recursively convert inf values to safe numbers"""
    if isinstance(obj, float):
        if obj == float('inf'):
            return 999999.0
        elif obj == float('-inf'):
            return -999999.0
        elif obj != obj:  # NaN check
            return 0.0
        return obj
    elif isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    else:
        return obj


@method_decorator(csrf_exempt, name='dispatch')
class AIOptionsRecommendationsView(View):
    """
    Django view for AI Options Recommendations
    POST /api/ai-options/recommendations
    """
    
    def post(self, request):
        """Handle POST request for AI options recommendations"""
        try:
            # Parse request body
            body = json.loads(request.body)
            
            symbol = body.get('symbol', '').upper()
            user_risk_tolerance = body.get('user_risk_tolerance', 'medium')
            portfolio_value = float(body.get('portfolio_value', 10000))
            time_horizon = int(body.get('time_horizon', 30))
            max_recommendations = int(body.get('max_recommendations', 5))
            
            logger.info("=" * 50)
            logger.info(f" NEW REQUEST: AI Options Recommendations")
            logger.info(f" Symbol: {symbol}")
            logger.info(f" Risk Tolerance: {user_risk_tolerance}")
            logger.info(f" Portfolio Value: ${portfolio_value:,}")
            logger.info(f"⏰ Time Horizon: {time_horizon} days")
            logger.info(f" Max Recommendations: {max_recommendations}")
            logger.info("=" * 50)
            
            # Validate inputs
            if user_risk_tolerance not in ['low', 'medium', 'high']:
                return JsonResponse(
                    {'error': "user_risk_tolerance must be 'low', 'medium', or 'high'"},
                    status=400
                )
            
            if portfolio_value <= 0:
                return JsonResponse(
                    {'error': 'portfolio_value must be positive'},
                    status=400
                )
            
            if time_horizon <= 0:
                return JsonResponse(
                    {'error': 'time_horizon must be positive'},
                    status=400
                )
            
            # Generate recommendations (run async function in sync context)
            logger.info(" Starting AI recommendation generation...")
            recommendations = asyncio.run(
                ai_engine.generate_recommendations_legacy(
                    symbol=symbol,
                    user_risk_tolerance=user_risk_tolerance,
                    portfolio_value=portfolio_value,
                    time_horizon=time_horizon
                )
            )
            
            logger.info(f" Generated {len(recommendations)} raw recommendations")
            
            # Limit recommendations
            original_count = len(recommendations)
            recommendations = recommendations[:max_recommendations]
            logger.info(f" Limited recommendations from {original_count} to {len(recommendations)}")
            
            # Convert to dict format for API response - make everything JSON safe
            recommendations_dict = []
            for rec in recommendations:
                # rec is already a dict from legacy method
                rec_dict = {
                    'strategy_name': rec.get('strategy_name', 'Unknown Strategy'),
                    'strategy_type': rec.get('strategy_type', 'speculation'),
                    'confidence_score': make_json_safe(rec.get('confidence_score', 50.0)),
                    'symbol': rec.get('symbol', symbol),
                    'current_price': make_json_safe(rec.get('current_price', 100.0)),
                    'risk_score': make_json_safe(rec.get('risk_score', 50.0)),
                    'expected_return': make_json_safe(rec.get('expected_return', 0.1)),
                    'max_profit': make_json_safe(rec.get('max_profit', 0)),
                    'max_loss': make_json_safe(rec.get('max_loss', 0)),
                    'probability_of_profit': make_json_safe(rec.get('probability_of_profit', 0.5)),
                    'options': rec.get('options', []),
                    'reasoning': rec.get('reasoning', {}),
                    'risk_factors': rec.get('reasoning', {}).get('risk_factors', []),
                    'entry_strategy': '',
                    'exit_strategy': '',
                }
                recommendations_dict.append(rec_dict)
            
            # Get market analysis
            market_analysis = None
            try:
                # Try to get market analysis if available
                if recommendations_dict:
                    market_analysis = {
                        'symbol': symbol,
                        'current_price': recommendations_dict[0]['current_price'] if recommendations_dict else 0,
                        'volatility': 0.25,  # Placeholder
                        'sentiment': 'neutral',  # Placeholder
                    }
            except Exception as e:
                logger.warning(f"Could not generate market analysis: {e}")
            
            # Build response
            response_data = {
                'symbol': symbol,
                'risk_tolerance': user_risk_tolerance,
                'portfolio_value': portfolio_value,
                'time_horizon': time_horizon,
                'total_recommendations': len(recommendations_dict),
                'recommendations': recommendations_dict,
                'market_analysis': market_analysis,
            }
            
            logger.info(f"✅ Returning {len(recommendations_dict)} recommendations")
            
            return JsonResponse(response_data, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
        except Exception as e:
            logger.error(f"Error in AI Options Recommendations: {e}", exc_info=True)
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'},
                status=500
            )

