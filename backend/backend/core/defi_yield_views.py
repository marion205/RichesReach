from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .defi_yield_service import DeFiYieldService

@require_http_methods(["GET"])
def get_yield_pools(request):
    """Get available yield farming pools"""
    try:
        chain = request.GET.get('chain', 'ethereum')
        
        defi_service = DeFiYieldService()
        result = defi_service.get_yield_pools(chain)
        
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
def stake_tokens(request):
    """Stake tokens in a yield pool"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['pool_id', 'amount', 'user_address']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Stake tokens
        defi_service = DeFiYieldService()
        result = defi_service.stake_tokens(
            pool_id=data['pool_id'],
            amount=data['amount'],
            user_address=data['user_address']
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

@csrf_exempt
@require_http_methods(["POST"])
def unstake_tokens(request):
    """Unstake tokens from a yield pool"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['pool_id', 'amount', 'user_address']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Unstake tokens
        defi_service = DeFiYieldService()
        result = defi_service.unstake_tokens(
            pool_id=data['pool_id'],
            amount=data['amount'],
            user_address=data['user_address']
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

@require_http_methods(["GET"])
def get_user_stakes(request, user_address):
    """Get user's current stakes"""
    try:
        defi_service = DeFiYieldService()
        result = defi_service.get_user_stakes(user_address)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)