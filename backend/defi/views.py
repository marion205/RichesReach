from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django_ratelimit.decorators import ratelimit
from django.conf import settings
from web3 import Web3
from .serializers import TxValidateSerializer, ALLOWED_ASSETS
from .abis import AAVE_POOL_ABI  # add your ABI array

w3 = Web3(Web3.HTTPProvider(settings.RPC_SEPOLIA))
POOL = w3.eth.contract(address=Web3.to_checksum_address(settings.AAVE_POOL_ADDRESS), abi=AAVE_POOL_ABI)

def usd_price(symbol: str) -> float:
    # Sepolia testnet prices (conservative placeholders)
    prices = {
        "USDC": 1.0,
        "AAVE-USDC": 1.0,
        "WETH": 3000.0,
    }
    return prices.get(symbol, 1.0)

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='30/m', block=True)  # 30 requests/min per IP -> 429 on abuse
def validate_transaction(request):
    s = TxValidateSerializer(data=request.data)
    if not s.is_valid():
        return Response({"isValid": False, "reason": s.errors}, status=200)
    t = s.validated_data["type"]
    wallet = s.validated_data["wallet_address"]
    d = s.validated_data["data"]
    symbol = d["symbol"]
    amount = float(d.get("amountHuman") or d.get("amount"))
    price = usd_price(symbol)
    notional_usd = amount * price
    if notional_usd > s.validated_data["cap_usd"]:
        return Response({"isValid": False, "reason": f"Exceeds daily cap ${s.validated_data['cap_usd']}."})

    # Truth source: AAVE account data (base units; network specific)
    try:
        (total_collateral, total_debt, available_borrows, clt, ltv, hf) = POOL.functions.getUserAccountData(
            Web3.to_checksum_address(wallet)
        ).call()
    except Exception as e:
        return Response({"isValid": False, "reason": f"AAVE query failed: {e}"}, status=200)

    # Basic HF check on borrows: block if HF is too low
    if t == "borrow":
        # AAVE returns HF scaled by 1e18 (network-dependent). Treat "0" as no debt.
        if hf != 0 and hf < 1_000_000_000_000_000_000:  # < 1.0
            return Response({"isValid": False, "reason": "Health Factor too low to borrow."}, status=200)

    return Response({"isValid": True, "riskData": {
        "ltv": int(ltv), "healthFactor": str(hf), "availableBorrowsBase": str(available_borrows)
    }})


@api_view(['GET'])
@permission_classes([AllowAny])
def aave_user_data(request):
    addr = request.query_params.get('address')
    if not addr or not Web3.is_address(addr):
        return Response({"error": "invalid address"}, status=400)
    try:
        (total_collateral_base, total_debt_base, available_borrows_base,
         current_liquidation_threshold, ltv, health_factor) = POOL.functions.getUserAccountData(
            Web3.to_checksum_address(addr)
        ).call()
        # Return as strings/ints; frontend will format
        return Response({
            "totalCollateralBase": str(total_collateral_base),
            "totalDebtBase": str(total_debt_base),
            "availableBorrowsBase": str(available_borrows_base),
            "currentLiquidationThreshold": int(current_liquidation_threshold),
            "ltv": int(ltv),
            "healthFactor": str(health_factor)  # ray (1e18) or 0 when no debt
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)
