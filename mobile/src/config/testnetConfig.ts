// Testnet Configuration for Web3 Services
// Supports Sepolia (Ethereum) and Amoy (Polygon) testnets

export const SEPOLIA_CONFIG = {
  chainId: 11155111,
  name: 'Sepolia',
  rpcUrl: 'https://sepolia.infura.io/v3/YOUR_INFURA_KEY',
  blockExplorer: 'https://sepolia.etherscan.io',
  nativeCurrency: {
    name: 'Sepolia Ether',
    symbol: 'SEP',
    decimals: 18,
  },
};

export const AMOY_CONFIG = {
  chainId: 80002,
  name: 'Amoy',
  rpcUrl: 'https://rpc-amoy.polygon.technology',
  blockExplorer: 'https://amoy.polygonscan.com',
  nativeCurrency: {
    name: 'MATIC',
    symbol: 'MATIC',
    decimals: 18,
  },
};

// Default testnet configuration
export const DEFAULT_TESTNET = SEPOLIA_CONFIG;

// Network configurations mapping
export const TESTNET_CONFIGS = {
  sepolia: SEPOLIA_CONFIG,
  amoy: AMOY_CONFIG,
};

