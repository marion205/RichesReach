"""
Comprehensive unit tests for Blockchain Queries (NFTs, Governance, Yield)
"""
import unittest
from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from core.blockchain_queries import BlockchainQueries

User = get_user_model()


class BlockchainQueriesTestCase(TestCase):
    """Test suite for blockchain queries"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.queries = BlockchainQueries()
        
        self.mock_info = Mock()
        self.mock_info.context = Mock()
        self.mock_info.context.user = self.user
    
    def test_resolve_user_nfts_returns_list(self):
        """Test user NFTs resolver returns list"""
        result = self.queries.resolve_user_nfts(
            self.mock_info,
            address='0x1234567890123456789012345678901234567890',
            chain='ethereum'
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        # Currently returns empty list (would be populated by NFT API in production)
        self.assertEqual(len(result), 0)
    
    def test_resolve_user_nfts_different_chains(self):
        """Test user NFTs resolver with different chains"""
        address = '0x1234567890123456789012345678901234567890'
        
        for chain in ['ethereum', 'polygon', 'arbitrum', 'optimism', 'base']:
            result = self.queries.resolve_user_nfts(
                self.mock_info,
                address=address,
                chain=chain
            )
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
    
    def test_resolve_user_nfts_camelcase_alias(self):
        """Test camelCase alias for user NFTs"""
        result = self.queries.resolve_userNFTs(
            self.mock_info,
            address='0x1234567890123456789012345678901234567890',
            chain='ethereum'
        )
        
        # Should return same as resolve_user_nfts
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
    
    def test_resolve_governance_proposals_returns_list(self):
        """Test governance proposals resolver returns list"""
        dao_address = '0x1234567890123456789012345678901234567890'
        
        result = self.queries.resolve_governance_proposals(
            self.mock_info,
            daoAddress=dao_address
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        # Currently returns empty list (would be populated by on-chain queries in production)
        self.assertEqual(len(result), 0)
    
    def test_resolve_governance_proposals_camelcase_alias(self):
        """Test camelCase alias for governance proposals"""
        dao_address = '0x1234567890123456789012345678901234567890'
        
        result = self.queries.resolve_governanceProposals(
            self.mock_info,
            daoAddress=dao_address
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
    
    def test_resolve_user_voting_power_returns_structure(self):
        """Test user voting power resolver returns proper structure"""
        dao_address = '0x1234567890123456789012345678901234567890'
        user_address = '0x9876543210987654321098765432109876543210'
        
        result = self.queries.resolve_user_voting_power(
            self.mock_info,
            daoAddress=dao_address,
            userAddress=user_address
        )
        
        self.assertIsNotNone(result)
        # Check structure
        self.assertIsInstance(result.votingPower, (int, float))
        self.assertIsInstance(result.delegatedTo, (str, type(None)))
        self.assertIsInstance(result.delegators, list)
        self.assertIsInstance(result.proposalsVoted, int)
        
        # Default values
        self.assertEqual(result.votingPower, 0.0)
        self.assertIsNone(result.delegatedTo)
        self.assertEqual(len(result.delegators), 0)
        self.assertEqual(result.proposalsVoted, 0)
    
    def test_resolve_user_voting_power_camelcase_alias(self):
        """Test camelCase alias for user voting power"""
        dao_address = '0x1234567890123456789012345678901234567890'
        user_address = '0x9876543210987654321098765432109876543210'
        
        result = self.queries.resolve_userVotingPower(
            self.mock_info,
            daoAddress=dao_address,
            userAddress=user_address
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result.votingPower, (int, float))
    
    def test_resolve_yield_opportunities_returns_list(self):
        """Test yield opportunities resolver returns list"""
        result = self.queries.resolve_yield_opportunities(
            self.mock_info,
            chain='ethereum',
            asset='ETH'
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        # Currently returns empty list (would be populated by yield aggregator in production)
        self.assertEqual(len(result), 0)
    
    def test_resolve_yield_opportunities_no_filters(self):
        """Test yield opportunities resolver without filters"""
        result = self.queries.resolve_yield_opportunities(
            self.mock_info,
            chain=None,
            asset=None
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
    
    def test_resolve_yield_opportunities_camelcase_alias(self):
        """Test camelCase alias for yield opportunities"""
        result = self.queries.resolve_yieldOpportunities(
            self.mock_info,
            chain='ethereum',
            asset='ETH'
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
    
    def test_resolve_user_yield_positions_returns_list(self):
        """Test user yield positions resolver returns list"""
        user_address = '0x1234567890123456789012345678901234567890'
        
        result = self.queries.resolve_user_yield_positions(
            self.mock_info,
            userAddress=user_address
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        # Currently returns empty list (would be populated by on-chain queries in production)
        self.assertEqual(len(result), 0)
    
    def test_resolve_user_yield_positions_camelcase_alias(self):
        """Test camelCase alias for user yield positions"""
        user_address = '0x1234567890123456789012345678901234567890'
        
        result = self.queries.resolve_userYieldPositions(
            self.mock_info,
            userAddress=user_address
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
    
    def test_error_handling_in_nft_resolver(self):
        """Test error handling in NFT resolver"""
        # Should handle errors gracefully
        with patch('core.blockchain_queries.logger') as mock_logger:
            result = self.queries.resolve_user_nfts(
                self.mock_info,
                address='invalid_address',
                chain='ethereum'
            )
            
            # Should return empty list on error, not crash
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
    
    def test_error_handling_in_governance_resolver(self):
        """Test error handling in governance resolver"""
        with patch('core.blockchain_queries.logger') as mock_logger:
            result = self.queries.resolve_governance_proposals(
                self.mock_info,
                daoAddress='invalid_address'
            )
            
            # Should return empty list on error, not crash
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
    
    def test_error_handling_in_voting_power_resolver(self):
        """Test error handling in voting power resolver"""
        with patch('core.blockchain_queries.logger') as mock_logger:
            result = self.queries.resolve_user_voting_power(
                self.mock_info,
                daoAddress='invalid_address',
                userAddress='invalid_address'
            )
            
            # Should return default structure on error, not crash
            self.assertIsNotNone(result)
            self.assertIsInstance(result.votingPower, (int, float))
            self.assertEqual(result.votingPower, 0.0)


if __name__ == '__main__':
    unittest.main()

