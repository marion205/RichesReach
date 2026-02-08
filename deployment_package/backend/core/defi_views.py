"""
DeFi REST API Views

Provides REST endpoints for DeFi operations that the mobile app's
HybridTransactionService calls directly (outside of GraphQL).

Endpoints:
  POST /defi/validate-transaction/  — validate before on-chain tx
  POST /defi/record-transaction/    — record confirmed on-chain tx
"""
import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ValidateTransactionView(View):
    """
    POST /defi/validate-transaction/

    Called by HybridTransactionService before sending on-chain transactions.
    Body: { type, data: { symbol, amountHuman, ... }, wallet_address }
    Returns: { isValid, reason, warnings }
    """

    def post(self, request):
        try:
            body = json.loads(request.body)
            tx_type = body.get('type', '')
            data = body.get('data', {})
            wallet_address = body.get('wallet_address', '')

            # Extract user from JWT or session
            user = request.user
            if not user or not user.is_authenticated:
                # For testnet, allow unauthenticated validation with reduced limits
                # Phase 4 will enforce authentication
                logger.info("Unauthenticated DeFi validation request")

            from .defi_validation_service import validate_transaction

            result = validate_transaction(
                user=user if user and user.is_authenticated else None,
                tx_type=tx_type,
                wallet_address=wallet_address,
                symbol=data.get('symbol', data.get('amountHuman', '')),
                amount_human=data.get('amountHuman', '0'),
                chain_id=data.get('chainId', 11155111),
                pool_id=data.get('poolId', ''),
                rate_mode=data.get('rateMode', 2),
            )

            return JsonResponse(result.to_dict())

        except json.JSONDecodeError:
            return JsonResponse({
                'isValid': False,
                'reason': 'Invalid JSON body',
                'warnings': [],
            }, status=400)
        except Exception as e:
            logger.error(f"Validate transaction error: {e}")
            return JsonResponse({
                'isValid': False,
                'reason': str(e),
                'warnings': [],
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RecordTransactionView(View):
    """
    POST /defi/record-transaction/

    Called by HybridTransactionService after tx is confirmed on-chain.
    Body: { poolId, chainId, wallet, txHash, amount, action }
    Returns: { success, message }
    """

    def post(self, request):
        try:
            body = json.loads(request.body)

            user = request.user
            if not user or not user.is_authenticated:
                logger.info("Unauthenticated DeFi record request")

            from .defi_validation_service import confirm_transaction

            result = confirm_transaction(
                tx_hash=body.get('txHash', ''),
                pool_id=body.get('poolId', ''),
                user=user if user and user.is_authenticated else None,
                wallet_address=body.get('wallet', ''),
                chain_id=body.get('chainId', 11155111),
                amount_human=str(body.get('amount', '0')),
                action=body.get('action', 'deposit'),
                gas_used=body.get('gasUsed'),
            )

            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON body',
            }, status=400)
        except Exception as e:
            logger.error(f"Record transaction error: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e),
            }, status=500)
