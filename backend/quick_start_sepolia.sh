#!/bin/bash

# 🚀 Quick Start Script for Sepolia Testnet
# This script helps you get started with the Aave v3 integration on Sepolia

echo "🚀 Starting RichesReach Aave v3 Integration on Sepolia Testnet"
echo "=============================================================="

# Check if we're in the right directory
if [ ! -f "mobile/package.json" ]; then
    echo "❌ Error: Please run this script from the RichesReach root directory"
    exit 1
fi

echo ""
echo "📋 Prerequisites Checklist:"
echo "1. ✅ WalletConnect Project ID from cloud.reown.com"
echo "2. ✅ Alchemy API key from alchemy.com"
echo "3. ✅ Sepolia ETH for gas (get from sepoliafaucet.com)"
echo "4. ✅ Testnet tokens from Aave faucet (app.aave.com)"
echo ""

# Check if API keys are configured
echo "🔍 Checking configuration..."

if grep -q "<ALCHEMY_KEY>" mobile/src/config/testnetConfig.ts; then
    echo "⚠️  Please update your Alchemy key in mobile/src/config/testnetConfig.ts"
fi

if grep -q "<WALLETCONNECT_PROJECT_ID>" mobile/src/blockchain/wallet/walletConnect.ts; then
    echo "⚠️  Please update your WalletConnect Project ID in mobile/src/blockchain/wallet/walletConnect.ts"
fi

echo ""
echo "🔧 Configuration Steps:"
echo "1. Update mobile/src/config/testnetConfig.ts with your Alchemy key"
echo "2. Update mobile/src/blockchain/wallet/walletConnect.ts with your Project ID"
echo "3. Get testnet tokens from app.aave.com (Sepolia mode)"
echo "4. Get Sepolia ETH from sepoliafaucet.com"
echo ""

# Start backend
echo "🚀 Starting backend server..."
cd backend
python3 final_complete_server.py &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🚀 Starting mobile app..."
cd ../mobile
npm start &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "Backend: http://192.168.1.151:8123"
echo "Frontend: Expo will show QR code"
echo ""
echo "📱 Next Steps:"
echo "1. Scan QR code with Expo Go app"
echo "2. Connect wallet to Sepolia network"
echo "3. Test the Aave integration!"
echo ""
echo "🔗 Useful Links:"
echo "- Aave Faucet: https://app.aave.com (Testnet mode)"
echo "- Sepolia Faucet: https://sepoliafaucet.com"
echo "- Sepolia Explorer: https://sepolia.etherscan.io"
echo ""
echo "🛑 To stop servers:"
echo "kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Keep script running
wait
