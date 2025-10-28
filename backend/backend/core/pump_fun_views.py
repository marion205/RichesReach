from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .pump_fun_service import PumpFunService

@csrf_exempt
@require_http_methods(["POST"])
def launch_meme_coin(request):
    """Launch a new meme coin on Pump.fun"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'symbol', 'description', 'template', 'cultural_theme']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Launch meme coin
        pump_service = PumpFunService()
        result = pump_service.launch_meme_coin(
            name=data['name'],
            symbol=data['symbol'],
            description=data['description'],
            template_id=data['template'],
            cultural_theme=data['cultural_theme']
        )
        
        if result['success']:
            return JsonResponse(result, status=201)
        else:
            return JsonResponse(result, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_bonding_curve(request, contract_address):
    """Get bonding curve data for a meme coin"""
    try:
        pump_service = PumpFunService()
        result = pump_service.get_bonding_curve(contract_address)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def execute_trade(request):
    """Execute a trade on Pump.fun"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['contract_address', 'amount']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Execute trade
        pump_service = PumpFunService()
        result = pump_service.execute_trade(
            contract_address=data['contract_address'],
            amount=data['amount'],
            trade_type=data.get('trade_type', 'buy')
        )
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)