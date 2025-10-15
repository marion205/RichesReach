// Testnet configuration for Polygon Amoy
// Use this for testing before going to mainnet

import { CHAIN } from './web3Service';

export const TESTNET_CHAIN = {
  polygonAmoy: {
    chainIdHex: '0x13882',        // 80002 (Amoy testnet)
    chainIdWC: 'eip155:80002',
    rpcUrl: 'https://polygon-amoy.g.alchemy.com/v2/<ALCHEMY_KEY>',
    explorer: 'https://amoy.polygonscan.com'
  }
} as const;

// Testnet AAVE Pool Address (Polygon Amoy)
export const TESTNET_AAVE_POOL = '0x6C9fB0D5bD9429eb0Cd11661Fd4f3C5c5De81F8c';

// Testnet Asset Addresses (Polygon Amoy)
export const TESTNET_ASSETS = {
  USDC: { address: '0x41E94Eb019C0762f9BfF9fE4e6C21d348E0E9a6', decimals: 6 },
  WETH: { address: '0x7c68C7866A64FA2160F78EEaE1220FF21e0a5140', decimals: 18 },
  WMATIC: { address: '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889', decimals: 18 },
};

// Testnet Backend URL (adjust to your setup)
export const TESTNET_BACKEND = 'http://127.0.0.1:8000';

// How to get testnet tokens:
// 1. USDC: Use AAVE testnet faucet or swap on testnet DEX
// 2. WETH: Wrap ETH from testnet faucet
// 3. WMATIC: Wrap MATIC from testnet faucet
// 4. Testnet faucets: https://faucet.polygon.technology/ (select Amoy)
