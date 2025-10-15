// AAVE v3 Pool Address Resolver
// Uses the PoolAddressesProvider to get the current Pool address dynamically
import { Contract, utils, providers } from 'ethers';

const POOL_ADDRESSES_PROVIDER_ABI = [
  {
    "type": "function",
    "name": "getPool",
    "inputs": [],
    "outputs": [{"name": "", "type": "address"}],
    "stateMutability": "view"
  }
] as const;

export async function getAAVEPoolAddress(rpcUrl: string): Promise<string> {
  try {
    const provider = new providers.JsonRpcProvider(rpcUrl);
    const providerContract = new Contract(
      '0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e', // Sepolia PoolAddressesProvider
      POOL_ADDRESSES_PROVIDER_ABI,
      provider
    );
    
    const poolAddress = await providerContract.getPool();
    console.log('✅ AAVE Pool address resolved:', poolAddress);
    return poolAddress;
  } catch (error) {
    console.error('❌ Failed to resolve AAVE Pool address:', error);
    // Fallback to known address
    return '0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951';
  }
}

export async function getAAVEPoolAddressWithCache(rpcUrl: string): Promise<string> {
  // Simple in-memory cache to avoid repeated calls
  const cacheKey = `aave_pool_${rpcUrl}`;
  const cached = (global as any)[cacheKey];
  
  if (cached && Date.now() - cached.timestamp < 300000) { // 5 minute cache
    return cached.address;
  }
  
  const address = await getAAVEPoolAddress(rpcUrl);
  (global as any)[cacheKey] = {
    address,
    timestamp: Date.now()
  };
  
  return address;
}
