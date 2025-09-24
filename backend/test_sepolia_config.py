#!/usr/bin/env python3
"""
Test script to verify Sepolia configuration is working
"""

import sys
import os
sys.path.append('backend')

# Test frontend configuration
print("🧪 Testing Sepolia Configuration")
print("=" * 40)

# Test backend configuration
try:
    from backend.defi.serializers import ALLOWED_ASSETS
    print("✅ Backend assets loaded:")
    for symbol, info in ALLOWED_ASSETS.items():
        print(f"   {symbol}: {info['address']} ({info['decimals']} decimals)")
except Exception as e:
    print(f"❌ Backend assets error: {e}")

# Test frontend configuration
try:
    import json
    with open('mobile/src/config/testnetConfig.ts', 'r') as f:
        content = f.read()
        if '0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8' in content:
            print("✅ Frontend USDC address found")
        if '0xfff9976782d46CC05630D1f6eBAb18b2324d6B14' in content:
            print("✅ Frontend WETH address found")
        if 'nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM' in content:
            print("✅ Frontend Alchemy key found")
        if '42421cf8-2df7-45c6-9475-df4f4b115ffc' in content:
            print("✅ Frontend WalletConnect Project ID found")
except Exception as e:
    print(f"❌ Frontend config error: {e}")

# Test WalletConnect configuration
try:
    with open('mobile/src/blockchain/wallet/walletConnect.ts', 'r') as f:
        content = f.read()
        if '42421cf8-2df7-45c6-9475-df4f4b115ffc' in content:
            print("✅ WalletConnect Project ID configured")
except Exception as e:
    print(f"❌ WalletConnect config error: {e}")

print("\n🎉 Configuration test complete!")
print("\n📋 Next steps:")
print("1. Get testnet tokens from app.aave.com (Testnet mode)")
print("2. Get Sepolia ETH from sepoliafaucet.com")
print("3. Start the mobile app: cd mobile && npm start")
print("4. Connect wallet to Sepolia network")
print("5. Test the Aave integration!")
