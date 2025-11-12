import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  ScrollView,
  Alert,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
import { useTheme } from '../theme/PersonalizedThemes';

const { width } = Dimensions.get('window');

interface TokenizedPortfolio {
  id: string;
  name: string;
  description: string;
  tokenPrice: number;
  totalSupply: number;
  performance: number;
  underlyingAssets: { [key: string]: number };
  network: string;
  isOwned: boolean;
  ownedTokens: number;
}

interface DeFiPosition {
  id: string;
  protocol: string;
  type: 'lending' | 'borrowing' | 'staking' | 'liquidity';
  asset: string;
  amount: number;
  apy: number;
  value: number;
  network: string;
}

interface GovernanceProposal {
  id: string;
  title: string;
  description: string;
  type: string;
  votesFor: number;
  votesAgainst: number;
  totalVotes: number;
  timeRemaining: string;
  status: 'active' | 'passed' | 'failed';
  hasVoted: boolean;
}

interface BlockchainIntegrationProps {
  onPortfolioTokenize?: (portfolio: any) => void;
  onDeFiPositionCreate?: (position: DeFiPosition) => void;
  onGovernanceVote?: (proposalId: string, vote: boolean) => void;
}

export default function BlockchainIntegration({ 
  onPortfolioTokenize, 
  onDeFiPositionCreate, 
  onGovernanceVote 
}: BlockchainIntegrationProps = {}) {
  const navigation = useNavigation<any>();
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<'tokenized' | 'defi' | 'governance' | 'bridge'>('tokenized');
  const [tokenizedPortfolios, setTokenizedPortfolios] = useState<TokenizedPortfolio[]>([]);
  const [defiPositions, setDefiPositions] = useState<DeFiPosition[]>([]);
  const [governanceProposals, setGovernanceProposals] = useState<GovernanceProposal[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    loadData();
    startEntranceAnimation();
  }, []);

  const startEntranceAnimation = () => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Simulate API calls
      const mockTokenizedPortfolios: TokenizedPortfolio[] = [
        {
          id: '1',
          name: 'BIPOC Growth Fund Token',
          description: 'Tokenized representation of diversified BIPOC growth portfolio',
          tokenPrice: 1.25,
          totalSupply: 1000000,
          performance: 18.5,
          underlyingAssets: {
            'AAPL': 15,
            'GOOGL': 12,
            'TSLA': 8,
            'NVDA': 10,
            'Bonds': 25,
            'Cash': 10,
            'Crypto': 20,
          },
          network: 'Polygon',
          isOwned: true,
          ownedTokens: 5000,
        },
        {
          id: '2',
          name: 'Tech Innovation Token',
          description: 'High-growth tech stocks tokenized for fractional ownership',
          tokenPrice: 2.45,
          totalSupply: 500000,
          performance: 32.1,
          underlyingAssets: {
            'NVDA': 25,
            'AMD': 15,
            'TSLA': 20,
            'PLTR': 10,
            'CRWD': 15,
            'NET': 15,
          },
          network: 'Ethereum',
          isOwned: false,
          ownedTokens: 0,
        },
      ];

      const mockDeFiPositions: DeFiPosition[] = [
        {
          id: '1',
          protocol: 'Aave',
          type: 'lending',
          asset: 'USDC',
          amount: 10000,
          apy: 3.5,
          value: 10000,
          network: 'Ethereum',
        },
        {
          id: '2',
          protocol: 'Compound',
          type: 'borrowing',
          asset: 'ETH',
          amount: 2.5,
          apy: 2.1,
          value: 5000,
          network: 'Ethereum',
        },
        {
          id: '3',
          protocol: 'Lido',
          type: 'staking',
          asset: 'ETH',
          amount: 5.0,
          apy: 4.2,
          value: 10000,
          network: 'Ethereum',
        },
      ];

      const mockGovernanceProposals: GovernanceProposal[] = [
        {
          id: '1',
          title: 'Add Polygon Network Support',
          description: 'Proposal to add Polygon network support for lower transaction fees',
          type: 'feature',
          votesFor: 1250000,
          votesAgainst: 450000,
          totalVotes: 1700000,
          timeRemaining: '3 days left',
          status: 'active',
          hasVoted: false,
        },
        {
          id: '2',
          title: 'Increase Referral Rewards',
          description: 'Proposal to increase referral rewards from $25 to $50',
          type: 'parameter',
          votesFor: 890000,
          votesAgainst: 210000,
          totalVotes: 1100000,
          timeRemaining: '1 day left',
          status: 'active',
          hasVoted: true,
        },
      ];
      
      setTokenizedPortfolios(mockTokenizedPortfolios);
      setDefiPositions(mockDeFiPositions);
      setGovernanceProposals(mockGovernanceProposals);
    } catch (error) {
      console.error('Error loading blockchain data:', error);
      Alert.alert('Error', 'Failed to load blockchain integration data');
    } finally {
      setLoading(false);
    }
  };

  const tokenizePortfolio = async (portfolio: any) => {
    try {
      Alert.alert(
        'Tokenize Portfolio',
        `Convert your portfolio into tradeable tokens? This will create ${portfolio.name} tokens.`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Tokenize', 
            onPress: () => {
              if (onPortfolioTokenize) {
                onPortfolioTokenize(portfolio);
              }
              Alert.alert('Success', 'Portfolio tokenized successfully!');
            }
          },
        ]
      );
    } catch (error) {
      console.error('Error tokenizing portfolio:', error);
    }
  };

  const createDeFiPosition = async (protocol: string, type: string, asset: string) => {
    try {
      Alert.alert(
        'Create DeFi Position',
        `Create a ${type} position for ${asset} on ${protocol}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Create', 
            onPress: () => {
              const position: DeFiPosition = {
                id: Date.now().toString(),
                protocol,
                type: type as any,
                asset,
                amount: 1000,
                apy: 3.5,
                value: 1000,
                network: 'Ethereum',
              };
              if (onDeFiPositionCreate) {
                onDeFiPositionCreate(position);
              }
              Alert.alert('Success', 'DeFi position created successfully!');
            }
          },
        ]
      );
    } catch (error) {
      console.error('Error creating DeFi position:', error);
    }
  };

  const voteOnProposal = async (proposalId: string, vote: boolean) => {
    try {
      Alert.alert(
        'Vote on Proposal',
        `Vote ${vote ? 'FOR' : 'AGAINST'} this proposal?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Vote', 
            onPress: () => {
              if (onGovernanceVote) {
                onGovernanceVote(proposalId, vote);
              }
              Alert.alert('Success', 'Vote recorded successfully!');
            }
          },
        ]
      );
    } catch (error) {
      console.error('Error voting on proposal:', error);
    }
  };

  const getNetworkColor = (network: string) => {
    switch (network) {
      case 'Ethereum': return '#627EEA';
      case 'Polygon': return '#8247E5';
      case 'Arbitrum': return '#28A0F0';
      case 'Optimism': return '#FF0420';
      case 'Base': return '#0052FF';
      default: return '#8E8E93';
    }
  };

  const getProtocolIcon = (protocol: string) => {
    switch (protocol) {
      case 'Aave': return '🦄';
      case 'Compound': return '🔗';
      case 'Uniswap': return '🦄';
      case 'Lido': return '🏛️';
      default: return '🔷';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator
          size="large"
          color="#8B5CF6"
          style={styles.loadingAnimation}
        />
        <Text style={styles.loadingText}>Loading blockchain features...</Text>
      </View>
    );
  }

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Blockchain Integration</Text>
        <Text style={styles.headerSubtitle}>DeFi meets traditional finance</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        {[
          { id: 'tokenized', name: 'Tokenized', icon: '🪙' },
          { id: 'defi', name: 'DeFi', icon: '🌊' },
          { id: 'governance', name: 'Governance', icon: '🗳️' },
          { id: 'bridge', name: 'Bridge', icon: '🌉' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.id}
            style={[
              styles.tabButton,
              activeTab === tab.id && styles.tabButtonActive,
            ]}
            onPress={() => setActiveTab(tab.id as any)}
          >
            <Text style={styles.tabIcon}>{tab.icon}</Text>
            <Text style={[
              styles.tabText,
              activeTab === tab.id && styles.tabTextActive,
            ]}>
              {tab.name}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {activeTab === 'tokenized' && (
          <View style={styles.tokenizedContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Tokenized Portfolios</Text>
              <Text style={styles.sectionSubtitle}>
                Convert your portfolio into tradeable tokens
              </Text>
            </View>
            
            {tokenizedPortfolios.map((portfolio) => (
              <TokenizedPortfolioCard
                key={portfolio.id}
                portfolio={portfolio}
                onTokenize={() => tokenizePortfolio(portfolio)}
                getNetworkColor={getNetworkColor}
              />
            ))}
          </View>
        )}

        {activeTab === 'defi' && (
          <View style={styles.defiContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>DeFi Positions</Text>
              <Text style={styles.sectionSubtitle}>
                Lend, borrow, and stake across protocols
              </Text>
            </View>
            
            {defiPositions.map((position) => (
              <DeFiPositionCard
                key={position.id}
                position={position}
                getProtocolIcon={getProtocolIcon}
                getNetworkColor={getNetworkColor}
              />
            ))}
            
            <View style={styles.defiOpportunities}>
              <Text style={styles.opportunitiesTitle}>Yield Opportunities</Text>
              {[
                { protocol: 'Aave', asset: 'USDC', apy: 3.5, type: 'lending' },
                { protocol: 'Compound', asset: 'ETH', apy: 2.1, type: 'lending' },
                { protocol: 'Lido', asset: 'ETH', apy: 4.2, type: 'staking' },
              ].map((opportunity, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.opportunityCard}
                  onPress={() => createDeFiPosition(opportunity.protocol, opportunity.type, opportunity.asset)}
                >
                  <Text style={styles.opportunityIcon}>{getProtocolIcon(opportunity.protocol)}</Text>
                  <View style={styles.opportunityInfo}>
                    <Text style={styles.opportunityTitle}>
                      {opportunity.protocol} - {opportunity.asset}
                    </Text>
                    <Text style={styles.opportunityType}>{opportunity.type}</Text>
                  </View>
                  <Text style={styles.opportunityApy}>{opportunity.apy}% APY</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {activeTab === 'governance' && (
          <View style={styles.governanceContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Governance Proposals</Text>
              <Text style={styles.sectionSubtitle}>
                Vote on platform decisions with $REACH tokens
              </Text>
            </View>
            
            {governanceProposals.map((proposal) => (
              <GovernanceProposalCard
                key={proposal.id}
                proposal={proposal}
                onVote={(vote) => voteOnProposal(proposal.id, vote)}
              />
            ))}
          </View>
        )}

        {activeTab === 'bridge' && (
          <View style={styles.bridgeContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Cross-Chain Bridge</Text>
              <Text style={styles.sectionSubtitle}>
                Move assets between blockchain networks
              </Text>
            </View>
            
            <View style={styles.bridgeCard}>
              <View intensity={20} style={styles.bridgeBlur}>
                <Text style={styles.bridgeTitle}>Bridge Assets</Text>
                <Text style={styles.bridgeDescription}>
                  Transfer your assets between different blockchain networks
                  with low fees and fast settlement.
                </Text>
                
                <View style={styles.bridgeNetworks}>
                  {['Ethereum', 'Polygon', 'Arbitrum', 'Optimism', 'Base'].map((network) => (
                    <View key={network} style={styles.networkItem}>
                      <View style={[styles.networkDot, { backgroundColor: getNetworkColor(network) }]} />
                      <Text style={styles.networkName}>{network}</Text>
                    </View>
                  ))}
                </View>
                
                <TouchableOpacity 
                  style={styles.bridgeButton}
                  onPress={() => {
                    console.log('Start Bridge pressed');
                    
                    // Strategy: Use parent navigator to navigate across tabs
                    // This avoids the React Navigation warning about screens not in current navigator
                    
                    // Get the parent navigator (the tab navigator)
                    const parentNav = navigation.getParent?.();
                    
                    if (parentNav) {
                      console.log('Found parent navigator, navigating via tab');
                      // Try Home tab first (bridge-screen is in HomeStack)
                      try {
                        parentNav.navigate('Home' as never, {
                          screen: 'bridge-screen',
                        } as never);
                        console.log('✅ Navigated via Home tab -> bridge-screen');
                        return;
                      } catch (homeError) {
                        console.log('Home tab navigation failed, trying Invest:', homeError);
                        // Try Invest tab (bridge-screen is also in InvestStack)
                        try {
                          parentNav.navigate('Invest' as never, {
                            screen: 'bridge-screen',
                          } as never);
                          console.log('✅ Navigated via Invest tab -> bridge-screen');
                          return;
                        } catch (investError) {
                          console.error('Both tab navigations failed:', { homeError, investError });
                        }
                      }
                    } else {
                      console.log('No parent navigator found, trying direct navigation');
                      // Fallback: try direct navigation (might work if in same stack)
                      try {
                        navigation.navigate('bridge-screen' as never);
                        console.log('✅ Direct navigation succeeded');
                        return;
                      } catch (directError) {
                        console.log('Direct navigation also failed:', directError);
                      }
                    }
                    
                    // Final fallback: use globalNavigate
                    try {
                      const { globalNavigate } = require('../navigation/NavigationService');
                      console.log('Using globalNavigate fallback');
                      globalNavigate('Home', { screen: 'bridge-screen' });
                    } catch (globalError) {
                      console.error('All navigation methods failed:', globalError);
                      Alert.alert(
                        'Navigation Error',
                        'Unable to open bridge screen. Please try again.'
                      );
                    }
                  }}
                >
                  <LinearGradient
                    colors={['#667eea', '#764ba2']}
                    style={styles.bridgeButtonGradient}
                  >
                    <Text style={styles.bridgeButtonText}>Start Bridge</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}
      </ScrollView>
    </Animated.View>
  );
}

// Tokenized Portfolio Card Component
function TokenizedPortfolioCard({ portfolio, onTokenize, getNetworkColor }: any) {
  return (
    <View style={styles.portfolioCard}>
      <View intensity={20} style={styles.portfolioBlur}>
        <View style={styles.portfolioHeader}>
          <View style={styles.portfolioInfo}>
            <Text style={styles.portfolioName}>{portfolio.name}</Text>
            <Text style={styles.portfolioDescription} numberOfLines={2}>
              {portfolio.description}
            </Text>
          </View>
          
          <View style={[styles.networkBadge, { backgroundColor: getNetworkColor(portfolio.network) }]}>
            <Text style={styles.networkBadgeText}>{portfolio.network}</Text>
          </View>
        </View>

        <View style={styles.portfolioStats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>${portfolio.tokenPrice}</Text>
            <Text style={styles.statLabel}>Token Price</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: portfolio.performance > 0 ? '#34C759' : '#FF3B30' }]}>
              {portfolio.performance > 0 ? '+' : ''}{portfolio.performance}%
            </Text>
            <Text style={styles.statLabel}>Performance</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{portfolio.totalSupply.toLocaleString()}</Text>
            <Text style={styles.statLabel}>Total Supply</Text>
          </View>
        </View>

        {portfolio.isOwned && (
          <View style={styles.ownedTokens}>
            <Text style={styles.ownedTokensText}>
              You own {portfolio.ownedTokens.toLocaleString()} tokens
            </Text>
          </View>
        )}

        <TouchableOpacity style={styles.tokenizeButton} onPress={onTokenize}>
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={styles.tokenizeButtonGradient}
          >
            <Text style={styles.tokenizeButtonText}>
              {portfolio.isOwned ? 'Trade Tokens' : 'Buy Tokens'}
            </Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// DeFi Position Card Component
function DeFiPositionCard({ position, getProtocolIcon, getNetworkColor }: any) {
  return (
    <View style={styles.positionCard}>
      <View intensity={20} style={styles.positionBlur}>
        <View style={styles.positionHeader}>
          <Text style={styles.positionIcon}>{getProtocolIcon(position.protocol)}</Text>
          <View style={styles.positionInfo}>
            <Text style={styles.positionTitle}>
              {position.protocol} - {position.asset}
            </Text>
            <Text style={styles.positionType}>{position.type}</Text>
          </View>
          <View style={[styles.networkBadge, { backgroundColor: getNetworkColor(position.network) }]}>
            <Text style={styles.networkBadgeText}>{position.network}</Text>
          </View>
        </View>

        <View style={styles.positionStats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{position.amount} {position.asset}</Text>
            <Text style={styles.statLabel}>Amount</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{position.apy}%</Text>
            <Text style={styles.statLabel}>APY</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>${position.value.toLocaleString()}</Text>
            <Text style={styles.statLabel}>Value</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

// Governance Proposal Card Component
function GovernanceProposalCard({ proposal, onVote }: any) {
  const votePercentage = proposal.totalVotes > 0 
    ? (proposal.votesFor / proposal.totalVotes) * 100 
    : 0;

  return (
    <View style={styles.proposalCard}>
      <View intensity={20} style={styles.proposalBlur}>
        <View style={styles.proposalHeader}>
          <Text style={styles.proposalTitle}>{proposal.title}</Text>
          <View style={[styles.statusBadge, { backgroundColor: proposal.status === 'active' ? '#34C759' : '#8E8E93' }]}>
            <Text style={styles.statusBadgeText}>{proposal.status}</Text>
          </View>
        </View>

        <Text style={styles.proposalDescription} numberOfLines={3}>
          {proposal.description}
        </Text>

        <View style={styles.votingStats}>
          <View style={styles.voteItem}>
            <Text style={styles.voteLabel}>For</Text>
            <Text style={styles.voteValue}>{proposal.votesFor.toLocaleString()}</Text>
          </View>
          <View style={styles.voteItem}>
            <Text style={styles.voteLabel}>Against</Text>
            <Text style={styles.voteValue}>{proposal.votesAgainst.toLocaleString()}</Text>
          </View>
          <View style={styles.voteItem}>
            <Text style={styles.voteLabel}>Total</Text>
            <Text style={styles.voteValue}>{proposal.totalVotes.toLocaleString()}</Text>
          </View>
        </View>

        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${votePercentage}%` }]} />
        </View>

        <View style={styles.proposalFooter}>
          <Text style={styles.timeRemaining}>{proposal.timeRemaining}</Text>
          
          {!proposal.hasVoted && proposal.status === 'active' && (
            <View style={styles.voteButtons}>
              <TouchableOpacity
                style={[styles.voteButton, styles.voteForButton]}
                onPress={() => onVote(true)}
              >
                <Text style={styles.voteButtonText}>Vote For</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.voteButton, styles.voteAgainstButton]}
                onPress={() => onVote(false)}
              >
                <Text style={styles.voteButtonText}>Vote Against</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingAnimation: {
    width: 120,
    height: 120,
    marginBottom: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  header: {
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabButtonActive: {
    borderBottomColor: '#667eea',
  },
  tabIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  tabText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#667eea',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  sectionHeader: {
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  tokenizedContent: {
    padding: 16,
  },
  portfolioCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  portfolioBlur: {
    padding: 20,
  },
  portfolioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  portfolioInfo: {
    flex: 1,
  },
  portfolioName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  portfolioDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  networkBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  networkBadgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  portfolioStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  ownedTokens: {
    backgroundColor: 'rgba(52, 199, 89, 0.1)',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  ownedTokensText: {
    fontSize: 14,
    color: '#34C759',
    fontWeight: '600',
    textAlign: 'center',
  },
  tokenizeButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  tokenizeButtonGradient: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  tokenizeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  defiContent: {
    padding: 16,
  },
  positionCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  positionBlur: {
    padding: 20,
  },
  positionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  positionIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  positionInfo: {
    flex: 1,
  },
  positionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  positionType: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  positionStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  defiOpportunities: {
    marginTop: 20,
  },
  opportunitiesTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  opportunityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  opportunityIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  opportunityInfo: {
    flex: 1,
  },
  opportunityTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  opportunityType: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  opportunityApy: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#34C759',
  },
  governanceContent: {
    padding: 16,
  },
  proposalCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  proposalBlur: {
    padding: 20,
  },
  proposalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  proposalTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
    flex: 1,
    marginRight: 12,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusBadgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  proposalDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 16,
  },
  votingStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  voteItem: {
    alignItems: 'center',
  },
  voteLabel: {
    fontSize: 12,
    color: '#666',
  },
  voteValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginTop: 2,
  },
  progressBar: {
    height: 6,
    backgroundColor: '#f0f0f0',
    borderRadius: 3,
    marginBottom: 16,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#34C759',
    borderRadius: 3,
  },
  proposalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timeRemaining: {
    fontSize: 14,
    color: '#666',
  },
  voteButtons: {
    flexDirection: 'row',
  },
  voteButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    marginLeft: 8,
  },
  voteForButton: {
    backgroundColor: '#34C759',
  },
  voteAgainstButton: {
    backgroundColor: '#FF3B30',
  },
  voteButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  bridgeContent: {
    padding: 16,
  },
  bridgeCard: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  bridgeBlur: {
    padding: 20,
  },
  bridgeTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  bridgeDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 20,
  },
  bridgeNetworks: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 20,
  },
  networkItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
    marginBottom: 8,
  },
  networkDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 6,
  },
  networkName: {
    fontSize: 14,
    color: '#1a1a1a',
  },
  bridgeButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  bridgeButtonGradient: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  bridgeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

