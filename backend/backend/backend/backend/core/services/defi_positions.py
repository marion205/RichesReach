"""
DeFi Position Management Service
Protocol adapters for on-chain position tracking
"""
from decimal import Decimal
from web3 import Web3
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def w3(chain_id: int) -> Web3:
    """Get Web3 instance for a given chain_id from settings."""
    return Web3(Web3.HTTPProvider(settings.CHAIN_RPC[chain_id], request_kwargs={"timeout": 15}))

def compute_position_snapshot(pos) -> dict:
    """
    Strategy:
      - If pool has gauge/masterchef -> read staked balance + pending rewards via ABI.
      - Else if LP token only -> read balanceOf() on staking contract (if known).
      - Compute realized_apy heuristic from rewards over trailing 30d.
    """
    chain_id = pos.pool.chain.chain_id
    web3 = w3(chain_id)

    # Example generic ERC20 staking:
    # lp_token = Web3.to_checksum_address(pos.pool.lp_token_addr)  # add to model if you store it
    # staking  = Web3.to_checksum_address(pos.pool.gauge_address or pos.pool.router_address)
    # staked_raw = erc20.balanceOf(staking, account=pos.wallet)  # or gauge.balanceOf(user)

    # Placeholder safe defaults (fill with adapters per protocol):
    return {
        "staked_lp": pos.staked_lp,
        "rewards_earned": pos.rewards_earned,
        "realized_apy": pos.realized_apy,
    }

# Protocol-specific adapters
def compute_aave_position(pos) -> dict:
    """Aave V3 position adapter"""
    try:
        chain_id = pos.pool.chain.chain_id
        web3 = w3(chain_id)
        
        # Aave V3 Pool ABI (simplified)
        AAVE_POOL_ABI = [
            "function getUserAccountData(address user) view returns (uint256 totalCollateralETH, uint256 totalDebtETH, uint256 availableBorrowsETH, uint256 currentLiquidationThreshold, uint256 ltv, uint256 healthFactor)"
        ]
        
        # Get Aave pool address (would be stored in pos.pool.pool_address)
        pool_contract = web3.eth.contract(
            address=Web3.to_checksum_address(pos.pool.pool_address),
            abi=AAVE_POOL_ABI
        )
        
        # Get user account data
        account_data = pool_contract.functions.getUserAccountData(
            Web3.to_checksum_address(pos.wallet)
        ).call()
        
        total_collateral_eth = account_data[0]
        total_debt_eth = account_data[1]
        
        return {
            "staked_lp": Decimal(str(total_collateral_eth)) / Decimal('1e18'),
            "rewards_earned": pos.rewards_earned,  # Would need incentives contract
            "realized_apy": pos.realized_apy,
        }
        
    except Exception as e:
        logger.error(f"Aave position computation failed: {e}")
        return None

def compute_curve_position(pos) -> dict:
    """Curve gauge position adapter"""
    try:
        chain_id = pos.pool.chain.chain_id
        web3 = w3(chain_id)
        
        # Curve Gauge ABI (simplified)
        CURVE_GAUGE_ABI = [
            "function balanceOf(address user) view returns (uint256)",
            "function claimable_tokens(address user) view returns (uint256)"
        ]
        
        if not pos.pool.gauge_address:
            return None
            
        gauge_contract = web3.eth.contract(
            address=Web3.to_checksum_address(pos.pool.gauge_address),
            abi=CURVE_GAUGE_ABI
        )
        
        # Get staked balance
        staked_balance = gauge_contract.functions.balanceOf(
            Web3.to_checksum_address(pos.wallet)
        ).call()
        
        # Get claimable rewards
        claimable_rewards = gauge_contract.functions.claimable_tokens(
            Web3.to_checksum_address(pos.wallet)
        ).call()
        
        return {
            "staked_lp": Decimal(str(staked_balance)) / Decimal('1e18'),
            "rewards_earned": pos.rewards_earned + Decimal(str(claimable_rewards)) / Decimal('1e18'),
            "realized_apy": pos.realized_apy,
        }
        
    except Exception as e:
        logger.error(f"Curve position computation failed: {e}")
        return None

def compute_uniswap_position(pos) -> dict:
    """Uniswap V3 position adapter"""
    try:
        chain_id = pos.pool.chain.chain_id
        web3 = w3(chain_id)
        
        # Uniswap V3 NonfungiblePositionManager ABI (simplified)
        UNISWAP_NFT_ABI = [
            "function balanceOf(address owner) view returns (uint256)",
            "function tokenOfOwnerByIndex(address owner, uint256 index) view returns (uint256)"
        ]
        
        # This is simplified - in reality you'd need to track individual NFT positions
        # and calculate fees earned from each position
        
        return {
            "staked_lp": pos.staked_lp,
            "rewards_earned": pos.rewards_earned,
            "realized_apy": pos.realized_apy,
        }
        
    except Exception as e:
        logger.error(f"Uniswap position computation failed: {e}")
        return None

# Protocol router
PROTOCOL_ADAPTERS = {
    'aave': compute_aave_position,
    'curve': compute_curve_position,
    'uniswap': compute_uniswap_position,
}

def compute_position_snapshot(pos) -> dict:
    """Main position computation with protocol routing"""
    protocol_slug = pos.pool.protocol.slug.lower()
    
    # Try protocol-specific adapter first
    if protocol_slug in PROTOCOL_ADAPTERS:
        result = PROTOCOL_ADAPTERS[protocol_slug](pos)
        if result:
            return result
    
    # Fallback to generic computation
    return {
        "staked_lp": pos.staked_lp,
        "rewards_earned": pos.rewards_earned,
        "realized_apy": pos.realized_apy,
    }
