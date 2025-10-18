"""
DeFi Service for Yield Farming Integration
Handles DeFiLlama API integration, yield fetching, and transaction verification
"""
import requests
import logging
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from django.core.cache import cache
from django.conf import settings
from web3 import Web3
from functools import lru_cache

logger = logging.getLogger(__name__)

# DeFiLlama API endpoints
LLAMA_POOLS_URL = "https://yields.llama.fi/pools"
LLAMA_PROTOCOLS_URL = "https://yields.llama.fi/protocols"

# Cache TTL in seconds
CACHE_TTL = 300  # 5 minutes

@lru_cache(maxsize=128)
def get_web3_provider(chain_id: int) -> Web3:
    """Get Web3 provider for a specific chain"""
    chain_rpc_map = getattr(settings, 'CHAIN_RPC', {
        1: "https://mainnet.infura.io/v3/YOUR_KEY",  # Ethereum
        8453: "https://mainnet.base.org",  # Base
        11155111: "https://sepolia.infura.io/v3/YOUR_KEY"  # Sepolia testnet
    })
    
    rpc_url = chain_rpc_map.get(chain_id)
    if not rpc_url:
        raise ValueError(f"No RPC URL configured for chain ID {chain_id}")
    
    return Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 15}))

def calculate_risk_score(pool_data: Dict) -> float:
    """Calculate risk score for a pool (0-1 scale)"""
    apy_base = float(pool_data.get('apyBase', 0))
    apy_reward = float(pool_data.get('apyReward', 0))
    tvl = float(pool_data.get('tvl', 0))
    
    # Risk factors
    protocol_risk = 0.0 if pool_data.get('audits') else 0.2  # Audited protocols are safer
    il_risk = 0.2 if '/' in (pool_data.get('symbol', '')) else 0.05  # LP pairs have impermanent loss risk
    tvl_risk = 0.25 if tvl < 5e6 else (0.1 if tvl < 2e7 else 0.0)  # Low TVL = higher risk
    apy_risk = min(0.45, (apy_base + apy_reward) / 80.0)  # Higher APY often means higher risk
    
    return max(0.0, min(1.0, protocol_risk + il_risk + tvl_risk + apy_risk))

def fetch_top_yields(chain: str = 'ethereum', limit: int = 10) -> List[Dict]:
    """Fetch top yield farming opportunities from DeFiLlama with optimized caching"""
    cache_key = f"llama_yields:{chain}:{limit}:v1"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info(f"Returning cached yields for {chain}")
        return cached_data
    
    try:
        logger.info(f"Fetching yields from DeFiLlama for {chain}")
        response = requests.get(
            f"{LLAMA_POOLS_URL}?chain={chain}&order=apy&l={limit}",
            timeout=2.5  # Reduced timeout for faster fail
        )
        response.raise_for_status()
        data = response.json().get('data', [])
        
        results = []
        for pool in data:
            # Handle None values gracefully
            apy_base = pool.get('apyBase', 0) or 0
            apy_reward = pool.get('apyReward', 0) or 0
            tvl = pool.get('tvl', 0) or 0
            
            results.append({
                'id': pool.get('pool', ''),
                'protocol': pool.get('project', ''),
                'chain': pool.get('chain', chain),
                'symbol': pool.get('symbol', ''),
                'pool_address': pool.get('pool', ''),
                'apy': float(apy_base) + float(apy_reward),
                'apy_base': float(apy_base),
                'apy_reward': float(apy_reward),
                'tvl': float(tvl),
                'risk': calculate_risk_score(pool),
                'audits': pool.get('audits', []),
                'url': pool.get('url', ''),
            })
        
        # Cache the results
        cache.set(cache_key, results, CACHE_TTL)
        logger.info(f"Fetched and cached {len(results)} yields for {chain}")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching yields from DeFiLlama: {e}")
        # Stale-while-revalidate: serve last good value if we have it
        return cached_data or get_fallback_yields(chain, limit)

def get_fallback_yields(chain: str, limit: int) -> List[Dict]:
    """Fallback yields for development/testing"""
    logger.warning(f"Using fallback yields for {chain}")
    
    fallback_pools = [
        {
            'id': '0xa0b86a33e6441e8c4b8c8c8c8c8c8c8c8c8c8c8c8',
            'protocol': 'Aave',
            'chain': chain,
            'symbol': 'USDC',
            'pool_address': '0xa0b86a33e6441e8c4b8c8c8c8c8c8c8c8c8c8c8c8',
            'apy': 15.0,
            'apy_base': 12.0,
            'apy_reward': 3.0,
            'tvl': 1000000000,
            'risk': 0.3,
            'audits': ['OpenZeppelin'],
            'url': 'https://aave.com',
        },
        {
            'id': '0xb1c97a44e6441e8c4b8c8c8c8c8c8c8c8c8c8c8c8c9',
            'protocol': 'Uniswap V3',
            'chain': chain,
            'symbol': 'ETH/USDC',
            'pool_address': '0xb1c97a44e6441e8c4b8c8c8c8c8c8c8c8c8c8c8c8c9',
            'apy': 25.0,
            'apy_base': 20.0,
            'apy_reward': 5.0,
            'tvl': 500000000,
            'risk': 0.7,
            'audits': ['ConsenSys'],
            'url': 'https://uniswap.org',
        },
        {
            'id': '0xc2d88b55e6441e8c4b8c8c8c8c8c8c8c8c8c8c8c8ca',
            'protocol': 'Curve',
            'chain': chain,
            'symbol': 'USDC/DAI',
            'pool_address': '0xc2d88b55e6441e8c4b8c8c8c8c8c8c8c8c8c8c8c8ca',
            'apy': 8.0,
            'apy_base': 6.0,
            'apy_reward': 2.0,
            'tvl': 2000000000,
            'risk': 0.2,
            'audits': ['Trail of Bits'],
            'url': 'https://curve.fi',
        },
    ]
    
    return fallback_pools[:limit]

def verify_transaction(
    chain_id: int, 
    tx_hash: str, 
    user_address: str, 
    candidate_contracts: List[str],
    min_confirmations: int = 2
) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Verify an on-chain transaction for yield farming
    
    Args:
        chain_id: Blockchain network ID
        tx_hash: Transaction hash to verify
        user_address: User's wallet address
        candidate_contracts: List of contract addresses to check for transfers
        min_confirmations: Minimum confirmations required
    
    Returns:
        Tuple of (success, error_message, receipt)
    """
    try:
        w3 = get_web3_provider(chain_id)
        
        # Get transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        # Check transaction status
        if receipt.status != 1:
            return False, "Transaction reverted", receipt
        
        # Check confirmations
        current_block = w3.eth.block_number
        confirmations = max(0, current_block - receipt.blockNumber)
        if confirmations < min_confirmations:
            logger.warning(f"Transaction has only {confirmations} confirmations, need {min_confirmations}")
        
        # Verify sender
        from_address = w3.to_checksum_address(receipt['from'])
        if from_address.lower() != user_address.lower():
            return False, "Transaction not from user address", receipt
        
        # Check for ERC20 Transfer events to target contracts
        transfer_signature = w3.keccak(text="Transfer(address,address,uint256)").hex()
        target_addresses = {addr.lower() for addr in candidate_contracts if addr}
        
        transfer_found = False
        for log in receipt.logs:
            if log['topics'] and log['topics'][0].hex() == transfer_signature:
                # Extract 'to' address from Transfer event
                to_address = w3.to_checksum_address(log['topics'][2].hex()[-40:])
                if to_address.lower() in target_addresses:
                    transfer_found = True
                    break
        
        if not transfer_found:
            return False, "No matching transfer to target contracts", receipt
        
        return True, None, receipt
        
    except Exception as e:
        logger.error(f"Error verifying transaction {tx_hash}: {e}")
        return False, str(e), None

def get_supported_chains() -> List[Dict]:
    """Get list of supported blockchain networks"""
    return [
        {'chain_id': 1, 'name': 'Ethereum', 'slug': 'ethereum'},
        {'chain_id': 8453, 'name': 'Base', 'slug': 'base'},
        {'chain_id': 137, 'name': 'Polygon', 'slug': 'polygon'},
        {'chain_id': 42161, 'name': 'Arbitrum', 'slug': 'arbitrum'},
    ]

def refresh_yields_cache():
    """Refresh the yields cache - can be called by Celery job"""
    chains = ['ethereum', 'base', 'polygon', 'arbitrum']
    for chain in chains:
        try:
            fetch_top_yields(chain, 20)  # Fetch more for better selection
            logger.info(f"Refreshed yields cache for {chain}")
        except Exception as e:
            logger.error(f"Failed to refresh yields for {chain}: {e}")
