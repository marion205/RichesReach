import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';
import { ethers } from 'ethers';
import { SEPOLIA_CONFIG, AMOY_CONFIG } from '../config/testnetConfig';

type Network = 'sepolia'|'polygon'|'arbitrum';

export const CHAIN = {
  sepolia: {
    chainId: 11155111,
    chainIdHex: '0xaa36a7',
    chainIdWC: 'eip155:11155111',
    name: 'Ethereum Sepolia',
    rpcUrl: 'https://eth-sepolia.g.alchemy.com/v2/<ALCHEMY_KEY>',
    explorer: 'https://sepolia.etherscan.io'
  },
  polygon: {
    chainId: 137,
    chainIdHex: '0x89',
    chainIdWC: 'eip155:137',
    name: 'Polygon Mainnet',
    rpcUrl: 'https://polygon-mainnet.g.alchemy.com/v2/<ALCHEMY_KEY>',
    explorer: 'https://polygonscan.com'
  },
  arbitrum: {
    chainId: 42161,
    chainIdHex: '0xa4b1',
    chainIdWC: 'eip155:42161',
    name: 'Arbitrum One',
    rpcUrl: 'https://arb-mainnet.g.alchemy.com/v2/<ALCHEMY_KEY>',
    explorer: 'https://arbiscan.io'
  }
} as const;

let readProvider: ethers.providers.JsonRpcProvider | null = null;

/**
 * Read provider for fast, cheap RPC reads. All writes happen via WalletConnect (or injected provider).
 */
export function getReadProvider(net: Network = 'sepolia') {
  if (!readProvider) readProvider = new ethers.providers.JsonRpcProvider(CHAIN[net].rpcUrl);
  return readProvider;
}

/**
 * Utility to format units safely.
 */
export async function toUnits(amount: string, decimals: number) {
  return ethers.utils.parseUnits(amount, decimals);
}

export function fromUnits(v: any, decimals: number) {
  return ethers.utils.formatUnits(v, decimals);
}
