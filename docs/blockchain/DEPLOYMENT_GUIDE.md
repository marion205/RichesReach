# Blockchain Deployment Guide

This guide covers deploying RichesReach smart contracts to testnet and mainnet.

## Prerequisites

1. **Node.js** (v18+)
2. **Hardhat** installed globally or in project
3. **Environment Variables** configured in `.env`
4. **Private Keys** for deployment accounts (stored securely)

## Environment Setup

Create a `.env` file in the project root:

```env
# Testnet
TESTNET_PRIVATE_KEY=your_testnet_private_key
POLYGON_AMOY_RPC_URL=https://rpc-amoy.polygon.technology
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-arbitrum.publicnode.com
OPTIMISM_SEPOLIA_RPC_URL=https://sepolia.optimism.io
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org

# Mainnet (use with caution!)
MAINNET_PRIVATE_KEY=your_mainnet_private_key
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
OPTIMISM_RPC_URL=https://mainnet.optimism.io
BASE_RPC_URL=https://mainnet.base.org

# Block Explorers API Keys (for verification)
POLYGONSCAN_API_KEY=your_key
ARBISCAN_API_KEY=your_key
OPTIMISTIC_ETHERSCAN_API_KEY=your_key
BASESCAN_API_KEY=your_key
```

## Testnet Deployment

### Quick Start

```bash
./scripts/deploy/testnet_deploy.sh
```

### Manual Deployment

Deploy to a specific testnet:

```bash
# Polygon Amoy
npx hardhat run scripts/deploy.js --network polygon-amoy

# Arbitrum Sepolia
npx hardhat run scripts/deploy.js --network arbitrum-sepolia

# Optimism Sepolia
npx hardhat run scripts/deploy.js --network optimism-sepolia

# Base Sepolia
npx hardhat run scripts/deploy.js --network base-sepolia
```

## Mainnet Deployment

⚠️ **WARNING**: Mainnet deployment is irreversible. Test thoroughly on testnet first!

### Quick Start

```bash
./scripts/deploy/mainnet_deploy.sh
```

The script will:
1. Ask for confirmation
2. Deploy to each network sequentially
3. Save deployment addresses to a log file
4. Verify contracts on block explorers

### Manual Deployment

```bash
# Polygon
npx hardhat run scripts/deploy.js --network polygon

# Arbitrum
npx hardhat run scripts/deploy.js --network arbitrum

# Optimism
npx hardhat run scripts/deploy.js --network optimism

# Base
npx hardhat run scripts/deploy.js --network base
```

## Contract Verification

After deployment, verify contracts on block explorers:

```bash
./scripts/deploy/verify_contracts.sh deployments/latest.json
```

Or verify manually:

```bash
npx hardhat verify --network <network> <CONTRACT_ADDRESS> <CONSTRUCTOR_ARGS>
```

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Contracts audited (for mainnet)
- [ ] Environment variables configured
- [ ] Private keys secured
- [ ] Gas estimation completed
- [ ] Deployment scripts tested on testnet

### During Deployment

- [ ] Monitor gas prices
- [ ] Verify each contract address
- [ ] Save deployment logs
- [ ] Test contract interactions

### Post-Deployment

- [ ] Verify contracts on block explorers
- [ ] Update contract addresses in code
- [ ] Test all contract functions
- [ ] Update documentation
- [ ] Notify team of new addresses

## Contract Addresses

After deployment, update these files with new addresses:

- `mobile/src/services/Web3Service.ts`
- `mobile/src/services/AccountAbstractionService.ts`
- `deployment_package/backend/core/blockchain_views.py`

## Troubleshooting

### Common Issues

1. **Out of Gas**: Increase gas limit in Hardhat config
2. **Nonce Issues**: Reset nonce or wait for pending transactions
3. **Verification Fails**: Check constructor arguments match deployment
4. **Network Errors**: Verify RPC URLs are correct

### Getting Help

- Check Hardhat documentation
- Review deployment logs
- Test on testnet first
- Contact team for assistance

## Security Best Practices

1. **Never commit private keys** to version control
2. **Use hardware wallets** for mainnet deployments
3. **Test thoroughly** on testnet before mainnet
4. **Get audits** for production contracts
5. **Use multi-sig wallets** for important contracts
6. **Monitor deployments** in real-time
7. **Keep deployment logs** for reference

## Next Steps

After deployment:

1. Update frontend with new contract addresses
2. Test all contract interactions
3. Monitor contract activity
4. Set up monitoring and alerts
5. Document any issues or learnings

---

**Last Updated**: December 4, 2025

