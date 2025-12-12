# RichesReach Smart Contracts

## 📦 **Contracts**

- **ERC4626Vault.sol** - ERC-4626 standardized vault with auto-compounding
- **veREACHToken.sol** - Vote-escrowed REACH token for governance and revenue sharing

## 🚀 **Quick Start**

### **Installation**:
```bash
npm install
```

### **Compile**:
```bash
npm run compile
```

### **Test**:
```bash
npm run test
```

### **Deploy to Testnet**:
```bash
# Set up .env file with PRIVATE_KEY and RPC URLs
npm run deploy:amoy
```

### **Deploy to Mainnet**:
```bash
npm run deploy:mainnet
```

## 🔧 **Configuration**

1. Copy `.env.example` to `.env`
2. Add your private key and RPC URLs
3. Add block explorer API keys for verification

## 📋 **Deployment Steps**

### **1. Testnet Deployment (Polygon Amoy)**:
```bash
# Install dependencies
npm install

# Compile contracts
npm run compile

# Run tests
npm run test

# Deploy to testnet
npm run deploy:amoy
```

### **2. Verify Contracts**:
```bash
npx hardhat verify --network polygonAmoy <CONTRACT_ADDRESS> <CONSTRUCTOR_ARGS>
```

### **3. Mainnet Deployment**:
```bash
# Deploy to mainnet (after testnet testing)
npm run deploy:mainnet
```

## 🧪 **Testing**

### **Run All Tests**:
```bash
npm run test
```

### **Test Coverage**:
```bash
npm run coverage
```

## 🔐 **Security**

- All contracts use OpenZeppelin libraries
- ReentrancyGuard protection
- Access control with Ownable
- Comprehensive test coverage

## 📚 **Documentation**

- `veREACH_TOKENOMICS.md` - Tokenomics design
- `AUDIT_PREPARATION_PACKAGE.md` - Audit preparation
- `MAINNET_LAUNCH_CHECKLIST.md` - Launch checklist

## 🎯 **Next Steps**

1. Deploy to testnet
2. Test all functions
3. Security audit
4. Mainnet deployment

