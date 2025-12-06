"""
GraphQL Queries for Advanced Blockchain Features
NFTs, DAO Governance, Yield Aggregators
"""
import graphene
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class NFTType(graphene.ObjectType):
    """GraphQL type for NFT"""
    id = graphene.String()
    tokenId = graphene.String()
    contractAddress = graphene.String()
    name = graphene.String()
    description = graphene.String()
    imageUrl = graphene.String()
    collectionName = graphene.String()
    chain = graphene.String()
    attributes = graphene.List(graphene.JSONString)
    floorPrice = graphene.Float()
    lastSalePrice = graphene.Float()


class GovernanceProposalType(graphene.ObjectType):
    """GraphQL type for governance proposal"""
    id = graphene.String()
    title = graphene.String()
    description = graphene.String()
    proposer = graphene.String()
    startBlock = graphene.Int()
    endBlock = graphene.Int()
    votesFor = graphene.Float()
    votesAgainst = graphene.Float()
    abstainVotes = graphene.Float()
    totalVotes = graphene.Float()
    quorum = graphene.Float()
    status = graphene.String()
    hasVoted = graphene.Boolean()
    userVote = graphene.String()
    actions = graphene.List(graphene.JSONString)


class UserVotingPowerType(graphene.ObjectType):
    """GraphQL type for user voting power"""
    votingPower = graphene.Float()
    delegatedTo = graphene.String()
    delegators = graphene.List(graphene.String)
    proposalsVoted = graphene.Int()


class YieldOpportunityType(graphene.ObjectType):
    """GraphQL type for yield opportunity"""
    protocol = graphene.String()
    asset = graphene.String()
    apy = graphene.Float()
    tvl = graphene.Float()
    risk = graphene.String()
    strategy = graphene.String()
    minDeposit = graphene.Float()
    chain = graphene.String()
    contractAddress = graphene.String()


class UserYieldPositionType(graphene.ObjectType):
    """GraphQL type for user yield position"""
    id = graphene.String()
    protocol = graphene.String()
    asset = graphene.String()
    amount = graphene.Float()
    apy = graphene.Float()
    earned = graphene.Float()
    chain = graphene.String()


class BlockchainQueries(graphene.ObjectType):
    """GraphQL queries for advanced blockchain features"""
    
    user_nfts = graphene.List(
        NFTType,
        address=graphene.String(required=True),
        chain=graphene.String(),
        description="Get user's NFTs"
    )
    userNFTs = graphene.List(
        NFTType,
        address=graphene.String(required=True),
        chain=graphene.String(),
        description="Get user's NFTs (camelCase alias)"
    )
    
    governance_proposals = graphene.List(
        GovernanceProposalType,
        daoAddress=graphene.String(required=True),
        description="Get governance proposals for a DAO"
    )
    governanceProposals = graphene.List(
        GovernanceProposalType,
        daoAddress=graphene.String(required=True),
        description="Get governance proposals (camelCase alias)"
    )
    
    user_voting_power = graphene.Field(
        UserVotingPowerType,
        daoAddress=graphene.String(required=True),
        userAddress=graphene.String(required=True),
        description="Get user's voting power in a DAO"
    )
    userVotingPower = graphene.Field(
        UserVotingPowerType,
        daoAddress=graphene.String(required=True),
        userAddress=graphene.String(required=True),
        description="Get user's voting power (camelCase alias)"
    )
    
    yield_opportunities = graphene.List(
        YieldOpportunityType,
        chain=graphene.String(),
        asset=graphene.String(),
        description="Get available yield opportunities"
    )
    yieldOpportunities = graphene.List(
        YieldOpportunityType,
        chain=graphene.String(),
        asset=graphene.String(),
        description="Get available yield opportunities (camelCase alias)"
    )
    
    user_yield_positions = graphene.List(
        UserYieldPositionType,
        userAddress=graphene.String(required=True),
        description="Get user's yield positions"
    )
    userYieldPositions = graphene.List(
        UserYieldPositionType,
        userAddress=graphene.String(required=True),
        description="Get user's yield positions (camelCase alias)"
    )
    
    def resolve_user_nfts(self, info, address, chain=None):
        """Get user's NFTs"""
        try:
            # In production, this would query NFT APIs (OpenSea, Alchemy, etc.)
            # For now, return empty list - would be populated by actual NFT data
            return []
        except Exception as e:
            logger.error(f"Error fetching NFTs: {e}", exc_info=True)
            return []
    
    def resolve_userNFTs(self, info, address, chain=None):
        """CamelCase alias for user_nfts"""
        return self.resolve_user_nfts(info, address, chain)
    
    def resolve_governance_proposals(self, info, daoAddress):
        """Get governance proposals"""
        try:
            # In production, this would query on-chain governance contracts
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error fetching governance proposals: {e}", exc_info=True)
            return []
    
    def resolve_governanceProposals(self, info, daoAddress):
        """CamelCase alias for governance_proposals"""
        return self.resolve_governance_proposals(info, daoAddress)
    
    def resolve_user_voting_power(self, info, daoAddress, userAddress):
        """Get user's voting power"""
        try:
            # In production, this would query on-chain data
            return UserVotingPowerType(
                votingPower=0.0,
                delegatedTo=None,
                delegators=[],
                proposalsVoted=0
            )
        except Exception as e:
            logger.error(f"Error fetching voting power: {e}", exc_info=True)
            return UserVotingPowerType(
                votingPower=0.0,
                delegatedTo=None,
                delegators=[],
                proposalsVoted=0
            )
    
    def resolve_userVotingPower(self, info, daoAddress, userAddress):
        """CamelCase alias for user_voting_power"""
        return self.resolve_user_voting_power(info, daoAddress, userAddress)
    
    def resolve_yield_opportunities(self, info, chain=None, asset=None):
        """Get yield opportunities"""
        try:
            # In production, this would aggregate from multiple DeFi protocols
            # For now, return empty list - would be populated by actual yield data
            return []
        except Exception as e:
            logger.error(f"Error fetching yield opportunities: {e}", exc_info=True)
            return []
    
    def resolve_yieldOpportunities(self, info, chain=None, asset=None):
        """CamelCase alias for yield_opportunities"""
        return self.resolve_yield_opportunities(info, chain, asset)
    
    def resolve_user_yield_positions(self, info, userAddress):
        """Get user's yield positions"""
        try:
            # In production, this would query on-chain positions
            return []
        except Exception as e:
            logger.error(f"Error fetching yield positions: {e}", exc_info=True)
            return []
    
    def resolve_userYieldPositions(self, info, userAddress):
        """CamelCase alias for user_yield_positions"""
        return self.resolve_user_yield_positions(info, userAddress)

