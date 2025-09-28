// Sepolia Testnet Configuration for AAVE v3
export const SEPOLIA_CONFIG = {
  // Network details
  chainId: 11155111,
  chainIdHex: '0xaa36a7',
  chainIdWC: 'eip155:11155111',
  name: 'Ethereum Sepolia',
  rpcUrl: 'https://eth-sepolia.g.alchemy.com/v2/nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM',
  explorer: 'https://sepolia.etherscan.io',
  
  // AAVE v3 Configuration
  poolAddressesProvider: '0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e',
  poolAddress: '0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951', // Resolved from provider
  
  // Testnet Asset Addresses (Sepolia) - Verified from AAVE faucet
  assets: {
    USDC: { 
      address: '0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8', 
      decimals: 6,
      symbol: 'USDC',
      name: 'USD Coin (AAVE Faucet)'
    },
    'AAVE-USDC': { 
      address: '0x94717b03B39f321c354429f417b4e558c8f7e9d1', 
      decimals: 6,
      symbol: 'AAVE-USDC',
      name: 'AAVE USDC Token'
    },
    WETH: { 
      address: '0xfff9976782d46CC05630D1f6eBAb18b2324d6B14', 
      decimals: 18,
      symbol: 'WETH',
      name: 'Wrapped Ether'
    }
  }
};

// Polygon Amoy Configuration (for reference)
export const AMOY_CONFIG = {
  chainId: 80002,
  chainIdHex: '0x13882',
  chainIdWC: 'eip155:80002',
  name: 'Polygon Amoy',
  rpcUrl: 'https://polygon-amoy.g.alchemy.com/v2/<ALCHEMY_KEY>',
  explorer: 'https://amoy.polygonscan.com',
  
  assets: {
    USDC: { 
      address: '0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582', 
      decimals: 6,
      symbol: 'USDC',
      name: 'USD Coin'
    }
  }
};

// Environment variables (configured)
export const ENV = {
  WALLETCONNECT_PROJECT_ID: '42421cf8-2df7-45c6-9475-df4f4b115ffc',
  ALCHEMY_KEY: 'nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM',
  BACKEND_BASE_URL: process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000'
};
