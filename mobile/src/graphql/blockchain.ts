import { gql } from '@apollo/client';

export const GET_USER_NFTS = gql`
  query GetUserNFTs($address: String!, $chain: String) {
    userNFTs(address: $address, chain: $chain) {
      id
      tokenId
      contractAddress
      name
      description
      imageUrl
      collectionName
      chain
      attributes {
        traitType
        value
      }
      floorPrice
      lastSalePrice
    }
  }
`;

export const GET_GOVERNANCE_PROPOSALS = gql`
  query GetGovernanceProposals($daoAddress: String!) {
    governanceProposals(daoAddress: $daoAddress) {
      id
      title
      description
      proposer
      startBlock
      endBlock
      votesFor
      votesAgainst
      abstainVotes
      totalVotes
      quorum
      status
      hasVoted
      userVote
      actions {
        target
        value
        signature
        calldata
      }
    }
  }
`;

export const GET_YIELD_OPPORTUNITIES = gql`
  query GetYieldOpportunities($chain: String, $asset: String) {
    yieldOpportunities(chain: $chain, asset: $asset) {
      protocol
      asset
      apy
      tvl
      risk
      strategy
      minDeposit
      chain
      contractAddress
    }
  }
`;

