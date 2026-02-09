# RichesReach Smart Contracts

## 📦 **Contracts**

- **ERC4626Vault.sol** - ERC-4626 standardized vault with auto-compounding
- **veREACHToken.sol** - Vote-escrowed REACH token for governance and revenue sharing
- **RepairForwarder.sol** - Meta-tx forwarder for Auto-Pilot repairs (user signs once; relayer submits and pays gas)

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

## 🔄 **RepairForwarder (relayer flow)**

Used so the backend relayer can submit repair txs on behalf of users (user signs EIP-712 once; relayer pays gas).

### **1. Start local node** (optional, for local testing)
```bash
cd contracts && npx hardhat node
```

### **2. Deploy RepairForwarder**
In a **separate terminal** (from project root or `contracts/`):
```bash
# Local (requires `npx hardhat node` in another terminal)
npm run deploy:repair-forwarder:local

# Polygon Amoy testnet
npm run deploy:repair-forwarder:amoy
```
Set `REPAIR_FORWARDER_ADDRESS` in the backend `.env` to the printed address.

### **3. Approve forwarder on a vault**
Each user must approve the RepairForwarder on each **source** vault (ERC-4626 shares) they want to repair from:
```bash
# Local
VAULT_ADDRESS=0x... npm run approve-forwarder:local

# Amoy testnet
VAULT_ADDRESS=0x... npm run approve-forwarder:amoy
```
- `VAULT_ADDRESS` – the ERC-4626 vault to allow repairs from.
- Optional: `FORWARDER_ADDRESS` to override the one in `deployments/<network>.json`.
- Optional: `APPROVE_AMOUNT` (default: max uint256).

Backend relayer also needs: `RELAYER_PRIVATE_KEY`, `RELAYER_RPC_URL` (or `ETHEREUM_RPC_URL`).  
**Note:** With web3 v7, the relayer must pass an explicit `nonce` when building the transaction (`repair_relayer.py` does this via `get_transaction_count(relayer_acct.address)`).

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

