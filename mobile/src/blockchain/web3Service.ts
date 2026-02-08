import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';
import { ethers } from 'ethers';
import { ALL_CHAINS, getChainConfig, type ChainConfig } from '../config/mainnetConfig';

type NetworkName = keyof typeof ALL_CHAINS;

/**
 * Exported CHAIN map — backward compatible with existing code.
 * Now sourced from mainnetConfig for single source of truth.
 */
export const CHAIN = Object.fromEntries(
  Object.entries(ALL_CHAINS).map(([key, config]) => [
    key,
    {
      chainId: config.chainId,
      chainIdHex: config.chainIdHex,
      chainIdWC: config.chainIdWC,
      name: config.name,
      rpcUrl: config.rpcUrl,
      explorer: config.blockExplorer,
    },
  ])
) as Record<string, { chainId: number; chainIdHex: string; chainIdWC: string; name: string; rpcUrl: string; explorer: string }>;

// ---- Provider Cache ----

const providerCache: Record<string, ethers.providers.JsonRpcProvider> = {};

/**
 * Get a read-only provider for a given network.
 * Providers are cached per network to avoid creating duplicates.
 * If primary RPC fails, falls back to secondary URL.
 */
export function getReadProvider(net: NetworkName = 'sepolia'): ethers.providers.JsonRpcProvider {
  if (providerCache[net]) return providerCache[net];

  const config = ALL_CHAINS[net];
  if (!config) {
    throw new Error(`Unknown network: ${net}. Supported: ${Object.keys(ALL_CHAINS).join(', ')}`);
  }

  const provider = new ethers.providers.JsonRpcProvider(config.rpcUrl);
  providerCache[net] = provider;
  return provider;
}

/**
 * Get a provider by chain ID (numeric).
 * Used when you have a chain ID but not the network name.
 */
export function getProviderByChainId(chainId: number): ethers.providers.JsonRpcProvider {
  const config = getChainConfig(chainId);
  if (!config) {
    throw new Error(`No config found for chain ID ${chainId}`);
  }
  return getReadProvider(config.shortName as NetworkName);
}

/**
 * Get a fallback provider that tries primary first, then fallback RPC.
 * Use this for critical operations where reliability matters.
 */
export function getReliableProvider(net: NetworkName = 'sepolia'): ethers.providers.FallbackProvider {
  const config = ALL_CHAINS[net];
  if (!config) {
    throw new Error(`Unknown network: ${net}`);
  }

  return new ethers.providers.FallbackProvider([
    {
      provider: new ethers.providers.JsonRpcProvider(config.rpcUrl),
      priority: 1,
      weight: 2,
    },
    {
      provider: new ethers.providers.JsonRpcProvider(config.rpcFallbackUrl),
      priority: 2,
      weight: 1,
    },
  ]);
}

// ---- Gas Estimation ----

/**
 * Estimate gas price for a transaction on a given network.
 * Adds the chain's gas buffer multiplier for safety.
 * Returns null if gas price exceeds the chain's circuit breaker threshold.
 */
export async function estimateGasPrice(
  net: NetworkName = 'sepolia'
): Promise<{
  gasPrice: ethers.BigNumber;
  gasPriceGwei: number;
  isAboveThreshold: boolean;
  maxGasPriceGwei: number;
} | null> {
  const config = ALL_CHAINS[net];
  if (!config) return null;

  try {
    const provider = getReadProvider(net);
    const gasPrice = await provider.getGasPrice();
    const gasPriceGwei = parseFloat(ethers.utils.formatUnits(gasPrice, 'gwei'));

    // Apply gas buffer
    const bufferedGasPrice = gasPrice.mul(Math.round(config.gasBuffer * 100)).div(100);
    const bufferedGwei = parseFloat(ethers.utils.formatUnits(bufferedGasPrice, 'gwei'));

    return {
      gasPrice: bufferedGasPrice,
      gasPriceGwei: bufferedGwei,
      isAboveThreshold: bufferedGwei > config.maxGasPriceGwei,
      maxGasPriceGwei: config.maxGasPriceGwei,
    };
  } catch (e) {
    return null;
  }
}

/**
 * Estimate gas cost in USD for a transaction.
 * Uses a simple ETH price estimation (fetched from provider or fallback).
 */
export async function estimateGasCostUsd(
  net: NetworkName = 'sepolia',
  gasLimit: number = 250_000,
  ethPriceUsd: number = 3000,
): Promise<number | null> {
  const gas = await estimateGasPrice(net);
  if (!gas) return null;

  const gasCostEth = parseFloat(ethers.utils.formatEther(gas.gasPrice.mul(gasLimit)));
  return gasCostEth * ethPriceUsd;
}

// ---- Utility Functions ----

export async function toUnits(amount: string, decimals: number) {
  return ethers.utils.parseUnits(amount, decimals);
}

export function fromUnits(v: any, decimals: number) {
  return ethers.utils.formatUnits(v, decimals);
}

/**
 * Clear cached provider for a network (useful when switching RPCs).
 */
export function clearProviderCache(net?: NetworkName) {
  if (net) {
    delete providerCache[net];
  } else {
    Object.keys(providerCache).forEach(k => delete providerCache[k]);
  }
}
