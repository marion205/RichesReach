# 🚀 **Sepolia Testnet Setup Guide - Option A**

## **Complete Aave v3 Integration on Ethereum Sepolia**

This guide sets up the full Aave v3 experience on Sepolia testnet with real testnet tokens and the official Aave protocol.

---

## **🔧 Step 1: Get API Keys**

### **1.1 WalletConnect Project ID**
1. Go to [cloud.reown.com](https://cloud.reown.com)
2. Create a new project
3. Copy your Project ID
4. Add to your environment variables

### **1.2 Alchemy RPC Key**
1. Go to [alchemy.com](https://alchemy.com)
2. Create a new app for "Ethereum Sepolia"
3. Copy your API key
4. Add to your environment variables

---

## **🔧 Step 2: Environment Configuration**

### **Frontend (.env)**
```bash
# WalletConnect / Reown
WALLETCONNECT_PROJECT_ID=your_project_id_here

# RPCs
RPC_SEPOLIA=https://eth-sepolia.g.alchemy.com/v2/your_alchemy_key_here

# Backend
BACKEND_BASE_URL=http://192.168.1.151:8123
```

### **Backend (settings.py)**
```python
# Aave Configuration
AAVE_POOL_ADDRESSES_PROVIDER = "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e"
AAVE_POOL_ADDRESS = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"
RPC_URL = "https://eth-sepolia.g.alchemy.com/v2/your_alchemy_key_here"
```

---

## **🔧 Step 3: Update Configuration Files**

### **3.1 Update testnetConfig.ts**
```typescript
// Replace <ALCHEMY_KEY> with your actual key
rpcUrl: 'https://eth-sepolia.g.alchemy.com/v2/YOUR_ACTUAL_KEY_HERE',
```

### **3.2 Update WalletConnect**
```typescript
// Replace <WALLETCONNECT_PROJECT_ID> with your actual project ID
projectId: 'YOUR_ACTUAL_PROJECT_ID_HERE',
```

---

## **🔧 Step 4: Get Testnet Tokens**

### **4.1 Aave Faucet**
1. Go to [app.aave.com](https://app.aave.com)
2. Switch to "Testnet mode" (Sepolia)
3. Connect your wallet
4. Use the faucet to get testnet tokens:
   - **USDC**: 1000 tokens
   - **WETH**: 0.1 tokens
   - **USDT**: 1000 tokens
   - **DAI**: 1000 tokens

### **4.2 Sepolia ETH for Gas**
1. Go to [sepoliafaucet.com](https://sepoliafaucet.com)
2. Get Sepolia ETH for transaction fees
3. You'll need ~0.1 ETH for testing

---

## **🔧 Step 5: Test the Integration**

### **5.1 Start Backend**
```bash
cd backend
python3 final_complete_server.py
```

### **5.2 Start Frontend**
```bash
cd mobile
npm start
```

### **5.3 Test Flow**
1. **Connect Wallet**: Connect to Sepolia network
2. **Supply Assets**: Supply USDC to Aave
3. **Borrow Assets**: Borrow WETH against USDC
4. **View Transactions**: Check Sepolia Etherscan
5. **Test Health Factor**: Verify risk calculations

---

## **🔧 Step 6: Verify Everything Works**

### **6.1 Check Aave Pool Resolution**
```typescript
// Should log: ✅ Aave Pool address resolved: 0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951
```

### **6.2 Check Wallet Connection**
- Wallet should connect to Sepolia network
- Address should be displayed correctly

### **6.3 Check Transaction Flow**
- Toast notifications should appear
- Explorer links should open Sepolia Etherscan
- Button should disable during transactions

### **6.4 Check Backend Validation**
```bash
curl -X POST http://192.168.1.151:8123/defi/validate-transaction/ \
  -H "Content-Type: application/json" \
  -d '{"type":"deposit","wallet_address":"0x0000000000000000000000000000000000000001","data":{"symbol":"USDC","amountHuman":"100"}}'
```

---

## **🎯 What You Get**

### **Real Aave v3 Integration**
- ✅ **Official Aave Protocol**: Real Aave v3 on Sepolia
- ✅ **Dynamic Pool Resolution**: Always gets current Pool address
- ✅ **Testnet Tokens**: Real testnet USDC, WETH, USDT, DAI
- ✅ **Health Factor**: Real Aave risk calculations
- ✅ **Liquidation**: Real Aave liquidation mechanics

### **Production-Ready Features**
- ✅ **Toast Notifications**: Real-time transaction feedback
- ✅ **Explorer Links**: Direct links to Sepolia Etherscan
- ✅ **Button Safety**: Prevents double-clicks during transactions
- ✅ **Error Handling**: Graceful error management
- ✅ **Rate Limiting**: 30 requests/minute protection

### **Developer Experience**
- ✅ **Hot Reload**: Changes reflect immediately
- ✅ **Console Logs**: Detailed debugging information
- ✅ **Error Messages**: Clear, actionable error feedback
- ✅ **Testnet Safety**: No real money at risk

---

## **🚀 Next Steps**

### **Immediate Testing**
1. **Fill in API keys** in configuration files
2. **Get testnet tokens** from Aave faucet
3. **Test complete flow** on Sepolia
4. **Verify all features** work correctly

### **Production Deployment**
1. **Switch to mainnet** when ready
2. **Update asset addresses** to mainnet
3. **Update RPC URLs** to mainnet
4. **Deploy with real tokens**

---

## **🔍 Troubleshooting**

### **Common Issues**

#### **"Failed to resolve Aave Pool address"**
- Check RPC URL is correct
- Verify Alchemy key is valid
- Check network connectivity

#### **"Wallet connection failed"**
- Check WalletConnect Project ID
- Verify wallet supports Sepolia
- Check network switching

#### **"Transaction failed"**
- Check you have Sepolia ETH for gas
- Verify token addresses are correct
- Check Aave Pool is accessible

#### **"Health Factor too low"**
- This is expected behavior
- Aave blocks dangerous transactions
- Supply more collateral or borrow less

---

## **🎉 You're Ready!**

Your hybrid Aave integration now has:
- **Real Aave v3 protocol** on Sepolia testnet
- **Dynamic pool resolution** for always-current addresses
- **Production-ready UX** with toasts and explorer links
- **Enterprise security** with validation and rate limiting
- **Complete testnet environment** for safe testing

**Start testing with real Aave v3 on Sepolia! 🚀**
