# 🚀 RichesReach Hybrid Aave Integration - Runbook

## 📋 **Quick Reference**

### **Emergency Contacts**
- **Backend Issues**: Check server logs and restart if needed
- **Blockchain Issues**: Check RPC provider status and switch if needed
- **User Issues**: Check transaction hashes on explorer

### **Key URLs**
- **Backend**: `http://192.168.1.151:8123` (dev) / `https://api.richesreach.com` (prod)
- **Explorer**: `https://polygonscan.com` (mainnet) / `https://amoy.polygonscan.com` (testnet)
- **Aave Protocol**: `https://app.aave.com`

---

## 🔧 **1. RPC Key Rotation**

### **When to Rotate**
- Rate limits exceeded
- RPC provider issues
- Security concerns

### **How to Rotate**
```bash
# 1. Get new key from Alchemy/Infura
# 2. Update backend settings
cd backend
# Edit defi/settings.py
RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/NEW_KEY_HERE"

# 3. Update frontend
cd ../mobile
# Edit src/blockchain/web3Service.ts
rpcUrl: 'https://polygon-mainnet.g.alchemy.com/v2/NEW_KEY_HERE'

# 4. Restart services
cd ../backend
python manage.py runserver
cd ../mobile
npm start
```

### **Test New Key**
```bash
# Test backend connection
curl -X POST http://192.168.1.151:8123/defi/validate-transaction/ \
  -H "Content-Type: application/json" \
  -d '{"type":"deposit","wallet_address":"0x0000000000000000000000000000000000000001","data":{"symbol":"USDC","amountHuman":"100"}}'

# Should return: {"isValid": true, "riskData": {...}}
```

---

## 🔧 **2. Network Changes**

### **Switch to Testnet**
```typescript
// mobile/src/blockchain/web3Service.ts
export const CHAIN = {
  polygon: {
    chainIdHex: '0x13882',        // 80002 (Amoy testnet)
    chainIdWC: 'eip155:80002',
    rpcUrl: 'https://polygon-amoy.g.alchemy.com/v2/<KEY>',
    explorer: 'https://amoy.polygonscan.com'
  }
};

// mobile/src/screens/ProductionAaveCard.tsx
const AAVE_POOL_ADDRESS = '0x6C9fB0D5bD9429eb0Cd11661Fd4f3C5c5De81F8c'; // Amoy
const ASSETS = {
  USDC: { address: '0x41E94Eb019C0762f9BfF9fE4e6C21d348E0E9a6', decimals: 6 },
  WETH: { address: '0x7c68C7866A64FA2160F78EEaE1220FF21e0a5140', decimals: 18 },
};
```

### **Switch to Mainnet**
```typescript
// mobile/src/blockchain/web3Service.ts
export const CHAIN = {
  polygon: {
    chainIdHex: '0x89',           // 137 (Polygon mainnet)
    chainIdWC: 'eip155:137',
    rpcUrl: 'https://polygon-mainnet.g.alchemy.com/v2/<KEY>',
    explorer: 'https://polygonscan.com'
  }
};

// mobile/src/screens/ProductionAaveCard.tsx
const AAVE_POOL_ADDRESS = '0x794a61358D6845594F94dc1DB02A252b5b4814aD'; // Mainnet
const ASSETS = {
  USDC: { address: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', decimals: 6 },
  WETH: { address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', decimals: 18 },
};
```

---

## 🔧 **3. Adding New Assets**

### **Backend Configuration**
```python
# backend/defi/serializers.py
ALLOWED_ASSETS = {
    "USDC": {"address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "decimals": 6},
    "WETH": {"address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", "decimals": 18},
    "WMATIC": {"address": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", "decimals": 18},
    "NEW_ASSET": {"address": "0x...", "decimals": 18},  # Add new asset
}

# backend/defi/settings.py
def usd_price(symbol: str) -> float:
    prices = {
        "USDC": 1.0,
        "WETH": 3000.0,
        "WMATIC": 0.8,
        "NEW_ASSET": 100.0,  # Add price
    }
    return prices.get(symbol, 1.0)
```

### **Frontend Configuration**
```typescript
// mobile/src/screens/ProductionAaveCard.tsx
const ASSETS = {
  USDC: { address: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', decimals: 6 },
  WETH: { address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', decimals: 18 },
  WMATIC: { address: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', decimals: 18 },
  NEW_ASSET: { address: '0x...', decimals: 18 },  // Add new asset
};
```

### **Test New Asset**
```bash
# Test validation
curl -X POST http://192.168.1.151:8123/defi/validate-transaction/ \
  -H "Content-Type: application/json" \
  -d '{"type":"deposit","wallet_address":"0x0000000000000000000000000000000000000001","data":{"symbol":"NEW_ASSET","amountHuman":"100"}}'
```

---

## 🔧 **4. Monitoring & Alerts**

### **Key Metrics to Monitor**
- **Transaction Success Rate**: Should be > 95%
- **Health Factor Distribution**: Monitor user risk levels
- **Rate Limit Hits**: Should be < 1% of requests
- **Error Rates**: Should be < 5%

### **Log Monitoring**
```bash
# Backend logs
tail -f backend/server.log | grep "ERROR\|WARN"

# Transaction logs
tail -f backend/server.log | grep "Transaction update"

# Rate limit logs
tail -f backend/server.log | grep "rate limit"
```

### **Health Checks**
```bash
# Backend health
curl http://192.168.1.151:8123/health/

# Validation endpoint
curl -X POST http://192.168.1.151:8123/defi/validate-transaction/ \
  -H "Content-Type: application/json" \
  -d '{"type":"deposit","wallet_address":"0x0000000000000000000000000000000000000001","data":{"symbol":"USDC","amountHuman":"100"}}'

# Should return: {"isValid": true, "riskData": {...}}
```

---

## 🔧 **5. Troubleshooting**

### **Common Issues**

#### **"Transaction failed" errors**
1. Check RPC provider status
2. Verify asset addresses are correct
3. Check user has sufficient balance
4. Verify Aave pool is accessible

#### **"Health Factor too low" errors**
1. Check user's current positions
2. Verify price feeds are working
3. Check Aave protocol status
4. Review risk parameters

#### **"Asset not allowed" errors**
1. Check asset is in ALLOWED_ASSETS
2. Verify asset address is correct
3. Check backend configuration

#### **Rate limit errors**
1. Check rate limit configuration
2. Verify IP-based limiting is working
3. Consider increasing limits if needed

### **Debug Commands**
```bash
# Check backend status
cd backend
python manage.py check

# Run tests
python manage.py test defi.tests.test_validation

# Check database
python manage.py shell
>>> from defi.models import *
>>> # Check data integrity
```

---

## 🔧 **6. Deployment Checklist**

### **Pre-Deployment**
- [ ] All tests passing
- [ ] Configuration updated for production
- [ ] RPC keys rotated and tested
- [ ] Asset addresses verified
- [ ] Rate limits configured
- [ ] CORS settings updated

### **Deployment**
- [ ] Backend deployed and healthy
- [ ] Frontend built and deployed
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Documentation updated

### **Post-Deployment**
- [ ] Smoke tests passing
- [ ] User transactions working
- [ ] Monitoring data flowing
- [ ] Error rates normal
- [ ] Performance acceptable

---

## 🔧 **7. Emergency Procedures**

### **If Backend is Down**
1. Check server status
2. Restart backend service
3. Check database connectivity
4. Verify RPC provider status
5. Check logs for errors

### **If Blockchain is Down**
1. Check RPC provider status
2. Switch to backup RPC provider
3. Check network status
4. Verify Aave protocol status
5. Notify users if needed

### **If High Error Rate**
1. Check recent deployments
2. Review error logs
3. Check external dependencies
4. Consider rolling back
5. Notify team

---

## 📞 **Support Contacts**

- **Technical Issues**: Check logs and runbook first
- **User Issues**: Check transaction hashes on explorer
- **Blockchain Issues**: Check RPC provider status
- **Security Issues**: Follow security procedures

**Remember: Always test changes on testnet first! 🚀**
