// AAVE v3 Pool Address Resolver
// Uses the PoolAddressesProvider to get the current Pool address dynamically.
// Phase 4: supports Ethereum, Polygon, Arbitrum, Base, and Sepolia.

import { Contract, providers } from 'ethers';
import { getChainConfig, ALL_CHAINS, type ChainConfig } from '../config/mainnetConfig';

// ---- ABI ----

const POOL_ADDRESSES_PROVIDER_ABI = [
  {
    type: 'function',
    name: 'getPool',
    inputs: [],
    outputs: [{ name: '', type: 'address' }],
    stateMutability: 'view',
  },
] as const;

// ---- In-memory cache ----

interface CacheEntry {
  address: string;
  timestamp: number;
}

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
const poolAddressCache: Record<string, CacheEntry> = {};

// ---- Core Resolver ----

/**
 * Resolve the Aave V3 Pool contract address for a given chain.
 *
 * Uses the on-chain PoolAddressesProvider registry to look up the latest
 * Pool proxy address. Falls back to a known hardcoded address if the
 * on-chain call fails.
 *
 * @param chainIdOrRpcUrl - Numeric chain ID (1, 137, 42161, 8453, 11155111)
 *                          or an RPC URL string (legacy usage).
 */
export async function getAAVEPoolAddress(
  chainIdOrRpcUrl: number | string,
): Promise<string> {
  // Resolve chain config
  const config = resolveChainConfig(chainIdOrRpcUrl);
  if (!config) {
    console.warn(`⚠️ No Aave config for input: ${chainIdOrRpcUrl}. Using Sepolia fallback.`);
    return '0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951';
  }

  const { rpcUrl, aavePoolAddressesProvider, aavePoolFallback, chainId, shortName } = config;

  try {
    const provider = new providers.JsonRpcProvider(rpcUrl);
    const providerContract = new Contract(
      aavePoolAddressesProvider,
      POOL_ADDRESSES_PROVIDER_ABI,
      provider,
    );

    const poolAddress: string = await providerContract.getPool();
    console.log(`✅ AAVE Pool resolved on ${shortName} (${chainId}): ${poolAddress}`);
    return poolAddress;
  } catch (error) {
    console.error(`❌ Failed to resolve AAVE Pool on ${shortName}:`, error);
    // Fallback to known address from mainnetConfig
    console.log(`↩️  Using fallback pool address for ${shortName}: ${aavePoolFallback}`);
    return aavePoolFallback;
  }
}

/**
 * Cached version of getAAVEPoolAddress.
 * Avoids repeated RPC calls by caching resolved addresses for 5 minutes.
 */
export async function getAAVEPoolAddressWithCache(
  chainIdOrRpcUrl: number | string,
): Promise<string> {
  const cacheKey = String(chainIdOrRpcUrl);
  const cached = poolAddressCache[cacheKey];

  if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
    return cached.address;
  }

  const address = await getAAVEPoolAddress(chainIdOrRpcUrl);

  poolAddressCache[cacheKey] = {
    address,
    timestamp: Date.now(),
  };

  return address;
}

/**
 * Get the Aave V3 PoolAddressesProvider address for a chain.
 * Useful for other resolver contracts (e.g., UiPoolDataProvider).
 */
export function getAAVEPoolAddressesProvider(chainId: number): string {
  const config = getChainConfig(chainId);
  if (!config) {
    console.warn(`⚠️ No config for chain ${chainId}, returning Sepolia provider`);
    return '0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e';
  }
  return config.aavePoolAddressesProvider;
}

/**
 * Get the known fallback Pool proxy address for a chain.
 * These are the current deployed Pool addresses from Aave V3 docs.
 */
export function getAAVEPoolFallback(chainId: number): string {
  const config = getChainConfig(chainId);
  if (!config) {
    return '0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951'; // Sepolia
  }
  return config.aavePoolFallback;
}

/**
 * Clear the pool address cache. Useful when switching networks.
 */
export function clearPoolAddressCache(chainIdOrRpcUrl?: number | string): void {
  if (chainIdOrRpcUrl !== undefined) {
    delete poolAddressCache[String(chainIdOrRpcUrl)];
  } else {
    Object.keys(poolAddressCache).forEach((key) => delete poolAddressCache[key]);
  }
}

/**
 * List all chains that have Aave V3 deployment configured.
 */
export function getSupportedAaveChains(): Array<{
  chainId: number;
  name: string;
  shortName: string;
}> {
  return Object.values(ALL_CHAINS)
    .filter((c) => c.aavePoolAddressesProvider && c.aavePoolAddressesProvider !== '')
    .map((c) => ({
      chainId: c.chainId,
      name: c.name,
      shortName: c.shortName,
    }));
}

// ---- Internal Helpers ----

function resolveChainConfig(chainIdOrRpcUrl: number | string): ChainConfig | null {
  if (typeof chainIdOrRpcUrl === 'number') {
    return getChainConfig(chainIdOrRpcUrl);
  }

  // Legacy: caller passed an RPC URL string — try to match it to a known chain
  const rpc = chainIdOrRpcUrl.toLowerCase();
  for (const config of Object.values(ALL_CHAINS)) {
    if (
      config.rpcUrl.toLowerCase().includes(rpc) ||
      rpc.includes(config.shortName)
    ) {
      return config;
    }
  }

  // If it looks like a raw RPC URL, build a minimal config for Sepolia fallback
  if (rpc.startsWith('http')) {
    return {
      ...ALL_CHAINS.sepolia,
      rpcUrl: chainIdOrRpcUrl,
    };
  }

  return null;
}
