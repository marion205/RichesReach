/**
 * Mainnet Configuration for DeFi Fortress
 *
 * Chain configs, contract addresses, block explorers, and gas settings
 * for Ethereum, Polygon, Arbitrum, and Base mainnets.
 *
 * IMPORTANT: RPC keys should come from environment variables in production.
 * Never commit real API keys to source control.
 *
 * Part of Phase 4: Mainnet Migration
 */

// ---- RPC Key Resolution ----

const ALCHEMY_KEY = process.env.EXPO_PUBLIC_ALCHEMY_KEY || 'demo';

// ---- Chain Configurations ----

export interface ChainConfig {
  chainId: number;
  chainIdHex: string;
  chainIdWC: string;
  name: string;
  shortName: string;
  rpcUrl: string;
  rpcFallbackUrl: string;
  blockExplorer: string;
  blockExplorerApi: string;
  nativeCurrency: {
    name: string;
    symbol: string;
    decimals: number;
  };
  // Aave V3 contract addresses
  aavePoolAddressesProvider: string;
  aavePoolFallback: string;
  // Gas settings
  gasBuffer: number; // Multiplier for gas estimation (e.g., 1.2 = 20% buffer)
  maxGasPriceGwei: number; // Circuit breaker threshold
  // Supported tokens for DeFi
  supportedTokens: Record<string, TokenConfig>;
}

export interface TokenConfig {
  address: string;
  decimals: number;
  symbol: string;
  name: string;
  coingeckoId?: string;
  isStablecoin: boolean;
}

// ---- Ethereum Mainnet ----

export const ETHEREUM_CONFIG: ChainConfig = {
  chainId: 1,
  chainIdHex: '0x1',
  chainIdWC: 'eip155:1',
  name: 'Ethereum Mainnet',
  shortName: 'ethereum',
  rpcUrl: `https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}`,
  rpcFallbackUrl: 'https://rpc.ankr.com/eth',
  blockExplorer: 'https://etherscan.io',
  blockExplorerApi: 'https://api.etherscan.io/api',
  nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
  aavePoolAddressesProvider: '0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e',
  aavePoolFallback: '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
  gasBuffer: 1.2,
  maxGasPriceGwei: 200,
  supportedTokens: {
    USDC: { address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', decimals: 6, symbol: 'USDC', name: 'USD Coin', coingeckoId: 'usd-coin', isStablecoin: true },
    USDT: { address: '0xdAC17F958D2ee523a2206206994597C13D831ec7', decimals: 6, symbol: 'USDT', name: 'Tether USD', coingeckoId: 'tether', isStablecoin: true },
    DAI: { address: '0x6B175474E89094C44Da98b954EedeAC495271d0F', decimals: 18, symbol: 'DAI', name: 'Dai', coingeckoId: 'dai', isStablecoin: true },
    WETH: { address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', decimals: 18, symbol: 'WETH', name: 'Wrapped Ether', coingeckoId: 'weth', isStablecoin: false },
    WBTC: { address: '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', decimals: 8, symbol: 'WBTC', name: 'Wrapped BTC', coingeckoId: 'wrapped-bitcoin', isStablecoin: false },
    stETH: { address: '0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84', decimals: 18, symbol: 'stETH', name: 'Lido Staked ETH', coingeckoId: 'staked-ether', isStablecoin: false },
  },
};

// ---- Polygon Mainnet ----

export const POLYGON_CONFIG: ChainConfig = {
  chainId: 137,
  chainIdHex: '0x89',
  chainIdWC: 'eip155:137',
  name: 'Polygon',
  shortName: 'polygon',
  rpcUrl: `https://polygon-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}`,
  rpcFallbackUrl: 'https://polygon-rpc.com',
  blockExplorer: 'https://polygonscan.com',
  blockExplorerApi: 'https://api.polygonscan.com/api',
  nativeCurrency: { name: 'MATIC', symbol: 'MATIC', decimals: 18 },
  aavePoolAddressesProvider: '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
  aavePoolFallback: '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
  gasBuffer: 1.3,
  maxGasPriceGwei: 500,
  supportedTokens: {
    USDC: { address: '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359', decimals: 6, symbol: 'USDC', name: 'USD Coin', coingeckoId: 'usd-coin', isStablecoin: true },
    USDT: { address: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', decimals: 6, symbol: 'USDT', name: 'Tether USD', coingeckoId: 'tether', isStablecoin: true },
    DAI: { address: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', decimals: 18, symbol: 'DAI', name: 'Dai', coingeckoId: 'dai', isStablecoin: true },
    WETH: { address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', decimals: 18, symbol: 'WETH', name: 'Wrapped Ether', coingeckoId: 'weth', isStablecoin: false },
    WMATIC: { address: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', decimals: 18, symbol: 'WMATIC', name: 'Wrapped MATIC', coingeckoId: 'wmatic', isStablecoin: false },
  },
};

// ---- Arbitrum One ----

export const ARBITRUM_CONFIG: ChainConfig = {
  chainId: 42161,
  chainIdHex: '0xa4b1',
  chainIdWC: 'eip155:42161',
  name: 'Arbitrum One',
  shortName: 'arbitrum',
  rpcUrl: `https://arb-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}`,
  rpcFallbackUrl: 'https://arb1.arbitrum.io/rpc',
  blockExplorer: 'https://arbiscan.io',
  blockExplorerApi: 'https://api.arbiscan.io/api',
  nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
  aavePoolAddressesProvider: '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
  aavePoolFallback: '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
  gasBuffer: 1.1,
  maxGasPriceGwei: 10,
  supportedTokens: {
    USDC: { address: '0xaf88d065e77c8cC2239327C5EDb3A432268e5831', decimals: 6, symbol: 'USDC', name: 'USD Coin', coingeckoId: 'usd-coin', isStablecoin: true },
    USDT: { address: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9', decimals: 6, symbol: 'USDT', name: 'Tether USD', coingeckoId: 'tether', isStablecoin: true },
    DAI: { address: '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1', decimals: 18, symbol: 'DAI', name: 'Dai', coingeckoId: 'dai', isStablecoin: true },
    WETH: { address: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1', decimals: 18, symbol: 'WETH', name: 'Wrapped Ether', coingeckoId: 'weth', isStablecoin: false },
    WBTC: { address: '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f', decimals: 8, symbol: 'WBTC', name: 'Wrapped BTC', coingeckoId: 'wrapped-bitcoin', isStablecoin: false },
  },
};

// ---- Base ----

export const BASE_CONFIG: ChainConfig = {
  chainId: 8453,
  chainIdHex: '0x2105',
  chainIdWC: 'eip155:8453',
  name: 'Base',
  shortName: 'base',
  rpcUrl: `https://base-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}`,
  rpcFallbackUrl: 'https://mainnet.base.org',
  blockExplorer: 'https://basescan.org',
  blockExplorerApi: 'https://api.basescan.org/api',
  nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
  aavePoolAddressesProvider: '0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D',
  aavePoolFallback: '0xA238Dd80C259a72e81d7e4664a9801593F98d1c5',
  gasBuffer: 1.1,
  maxGasPriceGwei: 5,
  supportedTokens: {
    USDC: { address: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', decimals: 6, symbol: 'USDC', name: 'USD Coin', coingeckoId: 'usd-coin', isStablecoin: true },
    WETH: { address: '0x4200000000000000000000000000000000000006', decimals: 18, symbol: 'WETH', name: 'Wrapped Ether', coingeckoId: 'weth', isStablecoin: false },
    cbETH: { address: '0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22', decimals: 18, symbol: 'cbETH', name: 'Coinbase Staked ETH', coingeckoId: 'coinbase-wrapped-staked-eth', isStablecoin: false },
  },
};

// ---- Sepolia Testnet (preserved for dev) ----

export const SEPOLIA_CONFIG: ChainConfig = {
  chainId: 11155111,
  chainIdHex: '0xaa36a7',
  chainIdWC: 'eip155:11155111',
  name: 'Ethereum Sepolia',
  shortName: 'sepolia',
  rpcUrl: `https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_KEY}`,
  rpcFallbackUrl: 'https://rpc.sepolia.org',
  blockExplorer: 'https://sepolia.etherscan.io',
  blockExplorerApi: 'https://api-sepolia.etherscan.io/api',
  nativeCurrency: { name: 'Sepolia Ether', symbol: 'SEP', decimals: 18 },
  aavePoolAddressesProvider: '0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e',
  aavePoolFallback: '0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951',
  gasBuffer: 1.5,
  maxGasPriceGwei: 1000,
  supportedTokens: {
    USDC: { address: '0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8', decimals: 6, symbol: 'USDC', name: 'Test USDC', isStablecoin: true },
    WETH: { address: '0xC558DBdd856501FCd9aaF1E62eae57A9F0629a3c', decimals: 18, symbol: 'WETH', name: 'Test WETH', isStablecoin: false },
  },
};

// ---- Lookup Maps ----

export const MAINNET_CHAINS: Record<string, ChainConfig> = {
  ethereum: ETHEREUM_CONFIG,
  polygon: POLYGON_CONFIG,
  arbitrum: ARBITRUM_CONFIG,
  base: BASE_CONFIG,
};

export const ALL_CHAINS: Record<string, ChainConfig> = {
  ...MAINNET_CHAINS,
  sepolia: SEPOLIA_CONFIG,
};

export function getChainConfig(chainIdOrName: number | string): ChainConfig | null {
  if (typeof chainIdOrName === 'string') {
    return ALL_CHAINS[chainIdOrName] || null;
  }
  return Object.values(ALL_CHAINS).find(c => c.chainId === chainIdOrName) || null;
}

export function getChainByWC(chainIdWC: string): ChainConfig | null {
  return Object.values(ALL_CHAINS).find(c => c.chainIdWC === chainIdWC) || null;
}

export function isMainnet(chainId: number): boolean {
  return Object.values(MAINNET_CHAINS).some(c => c.chainId === chainId);
}

export function getExplorerTxUrl(chainId: number, txHash: string): string {
  const config = getChainConfig(chainId);
  if (!config) return '';
  return `${config.blockExplorer}/tx/${txHash}`;
}

export function getExplorerAddressUrl(chainId: number, address: string): string {
  const config = getChainConfig(chainId);
  if (!config) return '';
  return `${config.blockExplorer}/address/${address}`;
}

// ---- Transaction Limit Tiers ----

export type UserTier = 'starter' | 'growth' | 'premium';

export const TRANSACTION_TIERS: Record<UserTier, {
  perTxLimitUsd: number;
  dailyLimitUsd: number;
  monthlyLimitUsd: number;
  maxBorrowUsd: number;
  label: string;
}> = {
  starter: {
    perTxLimitUsd: 100,
    dailyLimitUsd: 500,
    monthlyLimitUsd: 2_000,
    maxBorrowUsd: 50,
    label: 'Starter',
  },
  growth: {
    perTxLimitUsd: 1_000,
    dailyLimitUsd: 5_000,
    monthlyLimitUsd: 25_000,
    maxBorrowUsd: 500,
    label: 'Growth',
  },
  premium: {
    perTxLimitUsd: 10_000,
    dailyLimitUsd: 50_000,
    monthlyLimitUsd: 200_000,
    maxBorrowUsd: 5_000,
    label: 'Premium',
  },
};

// ---- Default Network Selection ----

/**
 * Which network to use by default.
 * Controlled by DEFI_MAINNET_ENABLED feature flag.
 */
export function getDefaultChain(mainnetEnabled: boolean): ChainConfig {
  return mainnetEnabled ? ETHEREUM_CONFIG : SEPOLIA_CONFIG;
}
