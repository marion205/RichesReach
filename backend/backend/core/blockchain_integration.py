"""
Blockchain Integration Service - DeFi-Hybrid Features
====================================================

This service integrates blockchain technology into RichesReach, creating a seamless
bridge between traditional finance and decentralized finance. Key features include:

1. Tokenized Portfolios - Convert traditional portfolios into tradeable tokens
2. DeFi-Enhanced SBLOC - Use SBLOC as collateral for DeFi lending
3. On-Chain Governance - Community-driven decision making with $REACH token
4. Cross-Chain Compatibility - Support for multiple blockchains
5. Smart Contract Automation - Automated tax optimization and rebalancing
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac
import time

from web3 import Web3
from eth_account import Account
from eth_typing import Address
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# =============================================================================
# Data Models
# =============================================================================

class BlockchainNetwork(str, Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    SOLANA = "solana"

class TokenStandard(str, Enum):
    """Token standards."""
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"
    SPL = "SPL"  # Solana

class DeFiProtocol(str, Enum):
    """Supported DeFi protocols."""
    AAVE = "aave"
    COMPOUND = "compound"
    UNISWAP = "uniswap"
    CURVE = "curve"
    MAKER = "maker"
    LIDO = "lido"

@dataclass
class TokenizedPortfolio:
    """A tokenized portfolio representation."""
    id: str
    user_id: str
    name: str
    description: str
    total_supply: int
    token_price: float
    underlying_assets: Dict[str, float]  # asset -> percentage
    network: BlockchainNetwork
    token_address: Optional[str] = None
    contract_address: Optional[str] = None
    created_at: datetime = None
    last_rebalanced: Optional[datetime] = None
    performance_metrics: Dict[str, float] = None

@dataclass
class DeFiPosition:
    """A DeFi position (lending, borrowing, staking)."""
    id: str
    user_id: str
    protocol: DeFiProtocol
    position_type: str  # 'lending', 'borrowing', 'staking', 'liquidity'
    asset: str
    amount: float
    apy: float
    collateral_ratio: Optional[float] = None
    liquidation_threshold: Optional[float] = None
    network: BlockchainNetwork = BlockchainNetwork.ETHEREUM
    created_at: datetime = None

@dataclass
class GovernanceProposal:
    """A governance proposal for the $REACH token."""
    id: str
    title: str
    description: str
    proposal_type: str  # 'feature', 'parameter', 'treasury', 'partnership'
    proposer: str
    votes_for: int = 0
    votes_against: int = 0
    total_votes: int = 0
    quorum: int = 0
    start_time: datetime = None
    end_time: datetime = None
    status: str = 'active'  # 'active', 'passed', 'failed', 'executed'
    execution_data: Optional[Dict[str, Any]] = None

@dataclass
class CrossChainTransaction:
    """A cross-chain transaction."""
    id: str
    user_id: str
    from_network: BlockchainNetwork
    to_network: BlockchainNetwork
    asset: str
    amount: float
    status: str  # 'pending', 'completed', 'failed'
    tx_hash: Optional[str] = None
    bridge_protocol: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None

# =============================================================================
# Blockchain Integration Service
# =============================================================================

class BlockchainIntegrationService:
    """
    Main service for blockchain integration features.
    
    This service handles:
    - Portfolio tokenization
    - DeFi protocol integration
    - Cross-chain transactions
    - Governance mechanisms
    - Smart contract interactions
    """
    
    def __init__(self):
        # Initialize Web3 connections for different networks
        self.networks = {
            BlockchainNetwork.ETHEREUM: Web3(Web3.HTTPProvider(settings.ETHEREUM_RPC_URL)),
            BlockchainNetwork.POLYGON: Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL)),
            BlockchainNetwork.ARBITRUM: Web3(Web3.HTTPProvider(settings.ARBITRUM_RPC_URL)),
            BlockchainNetwork.OPTIMISM: Web3(Web3.HTTPProvider(settings.OPTIMISM_RPC_URL)),
            BlockchainNetwork.BASE: Web3(Web3.HTTPProvider(settings.BASE_RPC_URL)),
        }
        
        # DeFi protocol configurations
        self.defi_protocols = {
            DeFiProtocol.AAVE: {
                'lending_pool': settings.AAVE_LENDING_POOL_ADDRESS,
                'data_provider': settings.AAVE_DATA_PROVIDER_ADDRESS,
            },
            DeFiProtocol.COMPOUND: {
                'comptroller': settings.COMPOUND_COMPTROLLER_ADDRESS,
                'c_token_factory': settings.COMPOUND_CTOKEN_FACTORY_ADDRESS,
            },
        }
        
        # Smart contract ABIs (simplified)
        self.contract_abis = {
            'ERC20': self._get_erc20_abi(),
            'PortfolioToken': self._get_portfolio_token_abi(),
            'Governance': self._get_governance_abi(),
        }
        
        # Tokenized portfolios cache
        self.tokenized_portfolios: Dict[str, TokenizedPortfolio] = {}
        self.defi_positions: Dict[str, DeFiPosition] = {}
        self.governance_proposals: Dict[str, GovernanceProposal] = {}
    
    # =========================================================================
    # Portfolio Tokenization
    # =========================================================================
    
    async def tokenize_portfolio(self, user_id: str, portfolio_data: Dict[str, Any]) -> TokenizedPortfolio:
        """
        Tokenize a user's portfolio into tradeable tokens.
        
        This creates an ERC-20 token representing a slice of the user's portfolio,
        allowing for fractional ownership and peer-to-peer trading.
        """
        try:
            # Calculate portfolio value and allocation
            total_value = portfolio_data.get('total_value', 0)
            allocation = portfolio_data.get('allocation', {})
            
            # Create tokenized portfolio
            portfolio_id = str(uuid.uuid4())
            tokenized_portfolio = TokenizedPortfolio(
                id=portfolio_id,
                user_id=user_id,
                name=f"{portfolio_data.get('name', 'Portfolio')} Token",
                description=f"Tokenized representation of {portfolio_data.get('name', 'portfolio')}",
                total_supply=1000000,  # 1M tokens
                token_price=total_value / 1000000,  # Price per token
                underlying_assets=allocation,
                network=BlockchainNetwork.POLYGON,  # Use Polygon for lower fees
                created_at=datetime.now(timezone.utc),
                performance_metrics={
                    'total_return': portfolio_data.get('total_return', 0),
                    'volatility': portfolio_data.get('volatility', 0),
                    'sharpe_ratio': portfolio_data.get('sharpe_ratio', 0),
                }
            )
            
            # Deploy smart contract for the tokenized portfolio
            contract_address = await self._deploy_portfolio_token_contract(tokenized_portfolio)
            tokenized_portfolio.contract_address = contract_address
            
            # Store in cache
            self.tokenized_portfolios[portfolio_id] = tokenized_portfolio
            
            logger.info(f"Portfolio tokenized successfully: {portfolio_id}")
            return tokenized_portfolio
            
        except Exception as e:
            logger.error(f"Error tokenizing portfolio: {e}")
            raise
    
    async def trade_portfolio_tokens(self, token_id: str, buyer_id: str, seller_id: str, amount: int) -> Dict[str, Any]:
        """
        Execute a trade of portfolio tokens between users.
        """
        try:
            portfolio = self.tokenized_portfolios.get(token_id)
            if not portfolio:
                raise ValueError("Portfolio not found")
            
            # Calculate trade value
            trade_value = amount * portfolio.token_price
            
            # Execute the trade on-chain
            tx_hash = await self._execute_token_trade(
                portfolio.contract_address,
                buyer_id,
                seller_id,
                amount
            )
            
            return {
                'success': True,
                'tx_hash': tx_hash,
                'trade_value': trade_value,
                'amount': amount,
                'token_price': portfolio.token_price,
            }
            
        except Exception as e:
            logger.error(f"Error trading portfolio tokens: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_portfolio_token_price(self, token_id: str) -> float:
        """
        Get current price of a portfolio token.
        """
        try:
            portfolio = self.tokenized_portfolios.get(token_id)
            if not portfolio:
                return 0.0
            
            # Update price based on underlying asset performance
            updated_price = await self._calculate_updated_token_price(portfolio)
            portfolio.token_price = updated_price
            
            return updated_price
            
        except Exception as e:
            logger.error(f"Error getting token price: {e}")
            return 0.0
    
    # =========================================================================
    # DeFi Integration
    # =========================================================================
    
    async def create_defi_position(self, user_id: str, protocol: DeFiProtocol, 
                                 position_type: str, asset: str, amount: float) -> DeFiPosition:
        """
        Create a DeFi position (lending, borrowing, staking).
        """
        try:
            position_id = str(uuid.uuid4())
            
            # Get current APY for the protocol and asset
            apy = await self._get_protocol_apy(protocol, asset, position_type)
            
            # Create DeFi position
            position = DeFiPosition(
                id=position_id,
                user_id=user_id,
                protocol=protocol,
                position_type=position_type,
                asset=asset,
                amount=amount,
                apy=apy,
                network=BlockchainNetwork.ETHEREUM,
                created_at=datetime.now(timezone.utc)
            )
            
            # Execute the DeFi transaction
            tx_hash = await self._execute_defi_transaction(position)
            position.tx_hash = tx_hash
            
            # Store position
            self.defi_positions[position_id] = position
            
            logger.info(f"DeFi position created: {position_id}")
            return position
            
        except Exception as e:
            logger.error(f"Error creating DeFi position: {e}")
            raise
    
    async def use_sbloc_as_defi_collateral(self, user_id: str, sbloc_amount: float, 
                                         borrow_asset: str, borrow_amount: float) -> DeFiPosition:
        """
        Use SBLOC (Securities-Based Line of Credit) as collateral for DeFi borrowing.
        
        This is a revolutionary feature that bridges traditional finance with DeFi.
        """
        try:
            # Create a synthetic representation of SBLOC on-chain
            sbloc_token_address = await self._mint_sbloc_token(user_id, sbloc_amount)
            
            # Use SBLOC token as collateral in DeFi protocol
            position = await self.create_defi_position(
                user_id=user_id,
                protocol=DeFiProtocol.AAVE,
                position_type='borrowing',
                asset=borrow_asset,
                amount=borrow_amount
            )
            
            # Set collateral ratio based on SBLOC value
            position.collateral_ratio = sbloc_amount / borrow_amount
            position.liquidation_threshold = 0.8  # 80% LTV
            
            logger.info(f"SBLOC used as DeFi collateral: {position.id}")
            return position
            
        except Exception as e:
            logger.error(f"Error using SBLOC as DeFi collateral: {e}")
            raise
    
    async def get_defi_yield_opportunities(self, user_id: str, risk_tolerance: str) -> List[Dict[str, Any]]:
        """
        Get personalized DeFi yield opportunities based on user's risk tolerance.
        """
        try:
            opportunities = []
            
            # Get current DeFi rates across protocols
            for protocol in DeFiProtocol:
                rates = await self._get_protocol_rates(protocol)
                
                for asset, rate in rates.items():
                    # Filter based on risk tolerance
                    if self._matches_risk_tolerance(asset, rate, risk_tolerance):
                        opportunities.append({
                            'protocol': protocol.value,
                            'asset': asset,
                            'apy': rate['apy'],
                            'risk_level': rate['risk_level'],
                            'minimum_amount': rate['minimum_amount'],
                            'description': f"Lend {asset} on {protocol.value} for {rate['apy']:.2f}% APY",
                        })
            
            # Sort by APY and risk-adjusted returns
            opportunities.sort(key=lambda x: x['apy'], reverse=True)
            
            return opportunities[:10]  # Return top 10 opportunities
            
        except Exception as e:
            logger.error(f"Error getting DeFi yield opportunities: {e}")
            return []
    
    # =========================================================================
    # Governance System
    # =========================================================================
    
    async def create_governance_proposal(self, proposer: str, title: str, 
                                       description: str, proposal_type: str) -> GovernanceProposal:
        """
        Create a governance proposal for the $REACH token.
        """
        try:
            proposal_id = str(uuid.uuid4())
            
            proposal = GovernanceProposal(
                id=proposal_id,
                title=title,
                description=description,
                proposal_type=proposal_type,
                proposer=proposer,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc) + timedelta(days=7),  # 7-day voting period
                quorum=1000000,  # 1M $REACH tokens required for quorum
            )
            
            # Deploy proposal on-chain
            await self._deploy_governance_proposal(proposal)
            
            # Store proposal
            self.governance_proposals[proposal_id] = proposal
            
            logger.info(f"Governance proposal created: {proposal_id}")
            return proposal
            
        except Exception as e:
            logger.error(f"Error creating governance proposal: {e}")
            raise
    
    async def vote_on_proposal(self, proposal_id: str, voter: str, 
                             vote: bool, voting_power: int) -> bool:
        """
        Vote on a governance proposal.
        """
        try:
            proposal = self.governance_proposals.get(proposal_id)
            if not proposal:
                raise ValueError("Proposal not found")
            
            if proposal.status != 'active':
                raise ValueError("Proposal is not active")
            
            if datetime.now(timezone.utc) > proposal.end_time:
                raise ValueError("Voting period has ended")
            
            # Record vote
            if vote:
                proposal.votes_for += voting_power
            else:
                proposal.votes_against += voting_power
            
            proposal.total_votes += voting_power
            
            # Check if proposal has passed
            if proposal.total_votes >= proposal.quorum:
                if proposal.votes_for > proposal.votes_against:
                    proposal.status = 'passed'
                else:
                    proposal.status = 'failed'
            
            # Execute vote on-chain
            await self._execute_governance_vote(proposal_id, voter, vote, voting_power)
            
            logger.info(f"Vote recorded for proposal {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error voting on proposal: {e}")
            return False
    
    async def get_governance_proposals(self, status: str = 'active') -> List[GovernanceProposal]:
        """
        Get governance proposals by status.
        """
        try:
            proposals = list(self.governance_proposals.values())
            
            if status:
                proposals = [p for p in proposals if p.status == status]
            
            # Sort by creation time
            proposals.sort(key=lambda x: x.start_time, reverse=True)
            
            return proposals
            
        except Exception as e:
            logger.error(f"Error getting governance proposals: {e}")
            return []
    
    # =========================================================================
    # Cross-Chain Operations
    # =========================================================================
    
    async def bridge_assets(self, user_id: str, from_network: BlockchainNetwork,
                          to_network: BlockchainNetwork, asset: str, amount: float) -> CrossChainTransaction:
        """
        Bridge assets between different blockchain networks.
        """
        try:
            transaction_id = str(uuid.uuid4())
            
            transaction = CrossChainTransaction(
                id=transaction_id,
                user_id=user_id,
                from_network=from_network,
                to_network=to_network,
                asset=asset,
                amount=amount,
                status='pending',
                created_at=datetime.now(timezone.utc)
            )
            
            # Execute cross-chain bridge
            tx_hash = await self._execute_cross_chain_bridge(transaction)
            transaction.tx_hash = tx_hash
            
            # Monitor transaction status
            asyncio.create_task(self._monitor_cross_chain_transaction(transaction))
            
            logger.info(f"Cross-chain transaction initiated: {transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Error bridging assets: {e}")
            raise
    
    async def get_cross_chain_balances(self, user_id: str) -> Dict[BlockchainNetwork, Dict[str, float]]:
        """
        Get user's balances across all supported networks.
        """
        try:
            balances = {}
            
            for network in BlockchainNetwork:
                if network in self.networks:
                    network_balances = await self._get_network_balances(user_id, network)
                    balances[network] = network_balances
            
            return balances
            
        except Exception as e:
            logger.error(f"Error getting cross-chain balances: {e}")
            return {}
    
    # =========================================================================
    # Smart Contract Automation
    # =========================================================================
    
    async def setup_automated_rebalancing(self, user_id: str, portfolio_id: str, 
                                        rebalance_threshold: float) -> bool:
        """
        Set up automated portfolio rebalancing using smart contracts.
        """
        try:
            # Deploy rebalancing contract
            contract_address = await self._deploy_rebalancing_contract(
                user_id, portfolio_id, rebalance_threshold
            )
            
            # Set up monitoring
            asyncio.create_task(self._monitor_rebalancing_conditions(
                contract_address, rebalance_threshold
            ))
            
            logger.info(f"Automated rebalancing set up for portfolio {portfolio_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up automated rebalancing: {e}")
            return False
    
    async def setup_automated_tax_harvesting(self, user_id: str, portfolio_id: str) -> bool:
        """
        Set up automated tax loss harvesting using smart contracts.
        """
        try:
            # Deploy tax harvesting contract
            contract_address = await self._deploy_tax_harvesting_contract(
                user_id, portfolio_id
            )
            
            # Set up monitoring
            asyncio.create_task(self._monitor_tax_harvesting_opportunities(
                contract_address
            ))
            
            logger.info(f"Automated tax harvesting set up for portfolio {portfolio_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up automated tax harvesting: {e}")
            return False
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    async def _deploy_portfolio_token_contract(self, portfolio: TokenizedPortfolio) -> str:
        """Deploy a smart contract for a tokenized portfolio."""
        # This would deploy an actual smart contract
        # For now, return a mock address
        return f"0x{hashlib.sha256(portfolio.id.encode()).hexdigest()[:40]}"
    
    async def _execute_token_trade(self, contract_address: str, buyer: str, 
                                 seller: str, amount: int) -> str:
        """Execute a token trade on-chain."""
        # This would execute an actual smart contract transaction
        # For now, return a mock transaction hash
        return f"0x{hashlib.sha256(f'{contract_address}{buyer}{seller}{amount}'.encode()).hexdigest()}"
    
    async def _calculate_updated_token_price(self, portfolio: TokenizedPortfolio) -> float:
        """Calculate updated token price based on underlying assets."""
        # This would fetch real-time prices and calculate the updated value
        # For now, return a mock calculation
        base_price = portfolio.token_price
        performance = portfolio.performance_metrics.get('total_return', 0)
        return base_price * (1 + performance / 100)
    
    async def _get_protocol_apy(self, protocol: DeFiProtocol, asset: str, position_type: str) -> float:
        """Get current APY for a DeFi protocol and asset."""
        # This would fetch real-time APY from the protocol
        # For now, return mock APYs
        mock_apys = {
            (DeFiProtocol.AAVE, 'USDC', 'lending'): 3.5,
            (DeFiProtocol.AAVE, 'ETH', 'lending'): 2.1,
            (DeFiProtocol.COMPOUND, 'USDC', 'lending'): 3.2,
            (DeFiProtocol.COMPOUND, 'ETH', 'lending'): 1.8,
        }
        return mock_apys.get((protocol, asset, position_type), 2.0)
    
    async def _execute_defi_transaction(self, position: DeFiPosition) -> str:
        """Execute a DeFi transaction."""
        # This would execute an actual DeFi transaction
        # For now, return a mock transaction hash
        return f"0x{hashlib.sha256(f'{position.id}{position.protocol}{position.amount}'.encode()).hexdigest()}"
    
    async def _mint_sbloc_token(self, user_id: str, amount: float) -> str:
        """Mint a synthetic SBLOC token on-chain."""
        # This would mint an actual synthetic token representing SBLOC
        # For now, return a mock token address
        return f"0x{hashlib.sha256(f'sbloc{user_id}{amount}'.encode()).hexdigest()[:40]}"
    
    async def _get_protocol_rates(self, protocol: DeFiProtocol) -> Dict[str, Dict[str, Any]]:
        """Get current rates for a DeFi protocol."""
        # This would fetch real-time rates from the protocol
        # For now, return mock rates
        return {
            'USDC': {'apy': 3.5, 'risk_level': 'low', 'minimum_amount': 100},
            'ETH': {'apy': 2.1, 'risk_level': 'medium', 'minimum_amount': 0.1},
            'WBTC': {'apy': 1.8, 'risk_level': 'medium', 'minimum_amount': 0.01},
        }
    
    def _matches_risk_tolerance(self, asset: str, rate: Dict[str, Any], risk_tolerance: str) -> bool:
        """Check if an asset matches the user's risk tolerance."""
        risk_mapping = {
            'low': ['low'],
            'medium': ['low', 'medium'],
            'high': ['low', 'medium', 'high'],
        }
        return rate['risk_level'] in risk_mapping.get(risk_tolerance, ['low'])
    
    async def _deploy_governance_proposal(self, proposal: GovernanceProposal) -> None:
        """Deploy a governance proposal on-chain."""
        # This would deploy an actual governance proposal contract
        pass
    
    async def _execute_governance_vote(self, proposal_id: str, voter: str, 
                                     vote: bool, voting_power: int) -> None:
        """Execute a governance vote on-chain."""
        # This would execute an actual governance vote
        pass
    
    async def _execute_cross_chain_bridge(self, transaction: CrossChainTransaction) -> str:
        """Execute a cross-chain bridge transaction."""
        # This would execute an actual cross-chain bridge
        # For now, return a mock transaction hash
        return f"0x{hashlib.sha256(f'{transaction.id}{transaction.from_network}{transaction.to_network}'.encode()).hexdigest()}"
    
    async def _monitor_cross_chain_transaction(self, transaction: CrossChainTransaction) -> None:
        """Monitor a cross-chain transaction until completion."""
        # This would monitor the actual transaction
        # For now, simulate completion after 5 minutes
        await asyncio.sleep(300)
        transaction.status = 'completed'
        transaction.completed_at = datetime.now(timezone.utc)
    
    async def _get_network_balances(self, user_id: str, network: BlockchainNetwork) -> Dict[str, float]:
        """Get user's balances on a specific network."""
        # This would fetch actual balances from the blockchain
        # For now, return mock balances
        return {
            'ETH': 1.5,
            'USDC': 1000.0,
            'WBTC': 0.05,
        }
    
    async def _deploy_rebalancing_contract(self, user_id: str, portfolio_id: str, 
                                         threshold: float) -> str:
        """Deploy an automated rebalancing contract."""
        # This would deploy an actual rebalancing contract
        # For now, return a mock address
        return f"0x{hashlib.sha256(f'rebalancing{user_id}{portfolio_id}'.encode()).hexdigest()[:40]}"
    
    async def _monitor_rebalancing_conditions(self, contract_address: str, threshold: float) -> None:
        """Monitor rebalancing conditions and execute when needed."""
        # This would monitor actual rebalancing conditions
        pass
    
    async def _deploy_tax_harvesting_contract(self, user_id: str, portfolio_id: str) -> str:
        """Deploy an automated tax harvesting contract."""
        # This would deploy an actual tax harvesting contract
        # For now, return a mock address
        return f"0x{hashlib.sha256(f'taxharvest{user_id}{portfolio_id}'.encode()).hexdigest()[:40]}"
    
    async def _monitor_tax_harvesting_opportunities(self, contract_address: str) -> None:
        """Monitor tax harvesting opportunities and execute when beneficial."""
        # This would monitor actual tax harvesting opportunities
        pass
    
    def _get_erc20_abi(self) -> List[Dict[str, Any]]:
        """Get ERC-20 ABI."""
        return [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
    
    def _get_portfolio_token_abi(self) -> List[Dict[str, Any]]:
        """Get Portfolio Token ABI."""
        return [
            {
                "constant": True,
                "inputs": [],
                "name": "getPortfolioValue",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "newAllocation", "type": "uint256[]"}],
                "name": "rebalance",
                "outputs": [],
                "type": "function"
            }
        ]
    
    def _get_governance_abi(self) -> List[Dict[str, Any]]:
        """Get Governance ABI."""
        return [
            {
                "constant": False,
                "inputs": [
                    {"name": "proposalId", "type": "uint256"},
                    {"name": "support", "type": "bool"}
                ],
                "name": "vote",
                "outputs": [],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "proposalId", "type": "uint256"}],
                "name": "getProposal",
                "outputs": [
                    {"name": "id", "type": "uint256"},
                    {"name": "proposer", "type": "address"},
                    {"name": "startBlock", "type": "uint256"},
                    {"name": "endBlock", "type": "uint256"},
                    {"name": "forVotes", "type": "uint256"},
                    {"name": "againstVotes", "type": "uint256"}
                ],
                "type": "function"
            }
        ]

# =============================================================================
# Global Instance
# =============================================================================

blockchain_service = BlockchainIntegrationService()
