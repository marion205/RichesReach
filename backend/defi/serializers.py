from rest_framework import serializers

# Sepolia Testnet Assets - Verified from AAVE faucet
ALLOWED_ASSETS = {
    "USDC": {"address": "0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8", "decimals": 6},
    "AAVE-USDC": {"address": "0x94717b03B39f321c354429f417b4e558c8f7e9d1", "decimals": 6},
    "WETH": {"address": "0xfff9976782d46CC05630D1f6eBAb18b2324d6B14", "decimals": 18},
}

class TxValidateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["deposit","borrow","repay"])
    wallet_address = serializers.RegexField(regex=r"^0x[a-fA-F0-9]{40}$")
    data = serializers.DictField()

    def validate(self, attrs):
        t = attrs["type"]
        d = attrs["data"]
        symbol = d.get("symbol")
        if symbol not in ALLOWED_ASSETS:
            raise serializers.ValidationError("Asset not allowed")
        try:
            amt = float(d.get("amountHuman") or d.get("amount") or "0")
        except Exception:
            raise serializers.ValidationError("Invalid amount")
        if amt <= 0:
            raise serializers.ValidationError("Amount must be > 0")
        if t in ("borrow","repay"):
            if d.get("rateMode") not in (1,2):
                raise serializers.ValidationError("rateMode must be 1 or 2")
        # Daily cap example (USD notionals; enforce in view using prices)
        attrs["cap_usd"] = 5000.0
        return attrs
