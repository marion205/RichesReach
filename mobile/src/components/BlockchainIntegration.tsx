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
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
import { useTheme } from '../theme/PersonalizedThemes';
import UI from '../shared/constants';
import SmartWalletCard from './blockchain/SmartWalletCard';
import RiskMonitorCard from './blockchain/RiskMonitorCard';
import ReferralProgramCard from './blockchain/ReferralProgramCard';
import IntentSwapCard from './blockchain/IntentSwapCard';
import ERC4626VaultCard from './blockchain/ERC4626VaultCard';
import NFTGallery from '../features/blockchain/components/NFTGallery';

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
  onGovernanceVote,
}: BlockchainIntegrationProps = {}) {
  const navigation = useNavigation<any>();
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<'tokenized' | 'defi' | 'governance' | 'bridge' | 'nfts'>('tokenized');
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
            AAPL: 15,
            GOOGL: 12,
            TSLA: 8,
            NVDA: 10,
            Bonds: 25,
            Cash: 10,
            Crypto: 20,
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
            NVDA: 25,
            AMD: 15,
            TSLA: 20,
            PLTR: 10,
            CRWD: 15,
            NET: 15,
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
            },
          },
        ],
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
            },
          },
        ],
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
            },
          },
        ],
      );
    } catch (error) {
      console.error('Error voting on proposal:', error);
    }
  };

  const getNetworkColor = (network: string) => {
    switch (network) {
      case 'Ethereum':
        return '#627EEA';
      case 'Polygon':
        return '#8247E5';
      case 'Arbitrum':
        return '#28A0F0';
      case 'Optimism':
        return '#FF0420';
      case 'Base':
        return '#0052FF';
      default:
        return '#8E8E93';
    }
  };

  const getProtocolIcon = (protocol: string) => {
    switch (protocol) {
      case 'Aave':
        return '🦄';
      case 'Compound':
        return '🔗';
      case 'Uniswap':
        return '🦄';
      case 'Lido':
        return '🏛️';
      default:
        return '🔷';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={UI.colors.primary} style={styles.loadingAnimation} />
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
      <View style={styles.tabNavigationWrapper}>
        <View style={styles.tabNavigation}>
          {[
            { id: 'tokenized', name: 'Tokenized', icon: '🪙' },
            { id: 'defi', name: 'DeFi', icon: '🌊' },
            { id: 'governance', name: 'Governance', icon: '🗳️' },
            { id: 'bridge', name: 'Bridge', icon: '🌉' },
            { id: 'nfts', name: 'NFTs', icon: '🖼️' },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <TouchableOpacity
                key={tab.id}
                style={[styles.tabButton, isActive && styles.tabButtonActive]}
                onPress={() => setActiveTab(tab.id as any)}
                activeOpacity={0.85}
              >
                <Text style={[styles.tabIcon, isActive && styles.tabIconActive]}>{tab.icon}</Text>
                <Text style={[styles.tabText, isActive && styles.tabTextActive]}>{tab.name}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.contentContainer}
      >
        {/* Tokenized Tab */}
        {activeTab === 'tokenized' && (
          <>
            <SmartWalletCard />
            <RiskMonitorCard />

            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Tokenized Portfolios</Text>
              <Text style={styles.sectionSubtitle}>
                Convert your portfolio into tradeable tokens
              </Text>
            </View>

            <View style={styles.tokenizedContent}>
              {tokenizedPortfolios.map((portfolio) => (
                <TokenizedPortfolioCard
                  key={portfolio.id}
                  portfolio={portfolio}
                  onTokenize={() => tokenizePortfolio(portfolio)}
                  getNetworkColor={getNetworkColor}
                />
              ))}
            </View>
          </>
        )}

        {/* DeFi Tab */}
        {activeTab === 'defi' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>DeFi Tools</Text>
              <Text style={styles.sectionSubtitle}>
                Vaults, swaps, and on-chain yield
              </Text>
            </View>

            <View style={styles.defiContent}>
              <ERC4626VaultCard />
              <IntentSwapCard />

              <View style={styles.sectionHeaderInline}>
                <Text style={styles.sectionTitleInline}>DeFi Positions</Text>
                <Text style={styles.sectionSubtitleInline}>
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
                    activeOpacity={0.9}
                    onPress={() =>
                      createDeFiPosition(opportunity.protocol, opportunity.type, opportunity.asset)
                    }
                  >
                    <Text style={styles.opportunityIcon}>
                      {getProtocolIcon(opportunity.protocol)}
                    </Text>
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
          </>
        )}

        {/* Governance Tab */}
        {activeTab === 'governance' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Governance</Text>
              <Text style={styles.sectionSubtitle}>
                Earn & vote with your RichesReach community
              </Text>
            </View>

            <View style={styles.governanceContent}>
              <ReferralProgramCard />

              <View style={styles.sectionHeaderInline}>
                <Text style={styles.sectionTitleInline}>Governance Proposals</Text>
                <Text style={styles.sectionSubtitleInline}>
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
          </>
        )}

        {/* NFTs Tab */}
        {activeTab === 'nfts' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>NFT Gallery</Text>
              <Text style={styles.sectionSubtitle}>
                View and manage your NFT collection
              </Text>
            </View>

            <View style={styles.nftContent}>
              <NFTGallery
                walletAddress={undefined} // Would get from connected wallet
                chain="ethereum"
                onNFTSelect={(nft) => {
                  Alert.alert('NFT Selected', `Selected: ${nft.name || `#${nft.tokenId}`}`);
                }}
              />
            </View>
          </>
        )}

        {/* Bridge Tab */}
        {activeTab === 'bridge' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Cross-Chain Bridge</Text>
              <Text style={styles.sectionSubtitle}>
                Move assets between blockchain networks
              </Text>
            </View>

            <View style={styles.bridgeContent}>
              <View style={styles.bridgeCard}>
                <View style={styles.bridgeInner}>
                  <Text style={styles.bridgeTitle}>Bridge Assets</Text>
                  <Text style={styles.bridgeDescription}>
                    Transfer your assets between different blockchain networks
                    with low fees and fast settlement.
                  </Text>

                  <View style={styles.bridgeNetworks}>
                    {['Ethereum', 'Polygon', 'Arbitrum', 'Optimism', 'Base'].map((network) => (
                      <View key={network} style={styles.networkItem}>
                        <View
                          style={[
                            styles.networkDot,
                            { backgroundColor: getNetworkColor(network) },
                          ]}
                        />
                        <Text style={styles.networkName}>{network}</Text>
                      </View>
                    ))}
                  </View>

                  <TouchableOpacity
                    style={styles.bridgeButton}
                    activeOpacity={0.9}
                    onPress={() => {
                      console.log('Start Bridge pressed');

                      const parentNav = navigation.getParent?.();

                      if (parentNav) {
                        console.log('Found parent navigator, navigating via tab');
                        try {
                          parentNav.navigate('Home' as never, {
                            screen: 'bridge-screen',
                          } as never);
                          console.log('✅ Navigated via Home tab -> bridge-screen');
                          return;
                        } catch (homeError) {
                          console.log('Home tab navigation failed, trying Invest:', homeError);
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
                        try {
                          navigation.navigate('bridge-screen' as never);
                          console.log('✅ Direct navigation succeeded');
                          return;
                        } catch (directError) {
                          console.log('Direct navigation also failed:', directError);
                        }
                      }

                      try {
                        const { globalNavigate } = require('../navigation/NavigationService');
                        console.log('Using globalNavigate fallback');
                        globalNavigate('Home', { screen: 'bridge-screen' });
                      } catch (globalError) {
                        console.error('All navigation methods failed:', globalError);
                        Alert.alert(
                          'Navigation Error',
                          'Unable to open bridge screen. Please try again.',
                        );
                      }
                    }}
                  >
                    <LinearGradient
                      colors={[UI.colors.primary, '#0051D5']}
                      style={styles.bridgeButtonGradient}
                    >
                      <Text style={styles.bridgeButtonText}>Start Bridge</Text>
                    </LinearGradient>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </>
        )}
      </ScrollView>
    </Animated.View>
  );
}

// Tokenized Portfolio Card Component
function TokenizedPortfolioCard({ portfolio, onTokenize, getNetworkColor }: any) {
  return (
    <View style={styles.portfolioCard}>
      <View style={styles.portfolioInner}>
        <View style={styles.portfolioHeader}>
          <View style={styles.portfolioInfo}>
            <Text style={styles.portfolioName}>{portfolio.name}</Text>
            <Text style={styles.portfolioDescription} numberOfLines={2}>
              {portfolio.description}
            </Text>
          </View>

          <View
            style={[
              styles.networkBadge,
              { backgroundColor: getNetworkColor(portfolio.network) },
            ]}
          >
            <Text style={styles.networkBadgeText}>{portfolio.network}</Text>
          </View>
        </View>

        <View style={styles.portfolioStats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>${portfolio.tokenPrice}</Text>
            <Text style={styles.statLabel}>Token Price</Text>
          </View>
          <View style={styles.statItem}>
            <Text
              style={[
                styles.statValue,
                { color: portfolio.performance > 0 ? UI.colors.success : UI.colors.error },
              ]}
            >
              {portfolio.performance > 0 ? '+' : ''}
              {portfolio.performance}%
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

        <TouchableOpacity style={styles.tokenizeButton} onPress={onTokenize} activeOpacity={0.9}>
          <LinearGradient colors={[UI.colors.primary, '#0051D5']} style={styles.tokenizeButtonGradient}>
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
      <View style={styles.positionInner}>
        <View style={styles.positionHeader}>
          <Text style={styles.positionIcon}>{getProtocolIcon(position.protocol)}</Text>
          <View style={styles.positionInfo}>
            <Text style={styles.positionTitle}>
              {position.protocol} - {position.asset}
            </Text>
            <Text style={styles.positionType}>{position.type}</Text>
          </View>
          <View
            style={[
              styles.networkBadge,
              { backgroundColor: getNetworkColor(position.network) },
            ]}
          >
            <Text style={styles.networkBadgeText}>{position.network}</Text>
          </View>
        </View>

        <View style={styles.positionStats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>
              {position.amount} {position.asset}
            </Text>
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
  const votePercentage =
    proposal.totalVotes > 0 ? (proposal.votesFor / proposal.totalVotes) * 100 : 0;

  return (
    <View style={styles.proposalCard}>
      <View style={styles.proposalInner}>
        <View style={styles.proposalHeader}>
          <Text style={styles.proposalTitle}>{proposal.title}</Text>
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: proposal.status === 'active' ? UI.colors.success : UI.colors.textSecondary },
            ]}
          >
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
                activeOpacity={0.9}
              >
                <Text style={styles.voteButtonText}>Vote For</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.voteButton, styles.voteAgainstButton]}
                onPress={() => onVote(false)}
                activeOpacity={0.9}
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

// Use UI constants for consistent design
const cardShadow = UI.shadows.md;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: UI.colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: UI.colors.background,
  },
  loadingAnimation: {
    width: 120,
    height: 120,
    marginBottom: UI.spacing.md,
  },
  loadingText: {
    ...UI.typography.body,
    color: UI.colors.textSecondary,
    textAlign: 'center',
  },
  header: {
    paddingHorizontal: UI.layout.containerPadding,
    paddingTop: 18,
    paddingBottom: UI.spacing.sm,
  },
  headerTitle: {
    ...UI.typography.h2,
    color: UI.colors.text,
  },
  headerSubtitle: {
    ...UI.typography.caption,
    color: UI.colors.textSecondary,
    marginTop: UI.spacing.xs,
  },
  tabNavigationWrapper: {
    paddingHorizontal: UI.layout.containerPadding,
    marginTop: UI.spacing.sm,
    marginBottom: UI.spacing.xs,
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: UI.colors.border,
    borderRadius: UI.borderRadius.full,
    padding: UI.spacing.xs,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: UI.spacing.sm,
    borderRadius: UI.borderRadius.full,
  },
  tabButtonActive: {
    backgroundColor: UI.colors.surface,
    ...cardShadow,
  },
  tabIcon: {
    fontSize: 15,
    marginRight: UI.spacing.xs,
  },
  tabIconActive: {
    opacity: 1,
  },
  tabText: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
    fontWeight: '500',
  },
  tabTextActive: {
    color: UI.colors.text,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: UI.layout.containerPadding,
    paddingTop: UI.spacing.sm,
    paddingBottom: UI.spacing.xl + 100, // Extra padding to ensure all content is visible
    flexGrow: 1,
  },
  sectionHeader: {
    marginTop: UI.spacing.sm,
    marginBottom: UI.spacing.sm,
  },
  sectionHeaderInline: {
    marginTop: UI.spacing.md,
    marginBottom: UI.spacing.sm,
  },
  sectionTitle: {
    ...UI.typography.h3,
    color: UI.colors.text,
  },
  sectionSubtitle: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
    marginTop: UI.spacing.xs,
  },
  sectionTitleInline: {
    fontSize: 18,
    fontWeight: '600',
    color: UI.colors.text,
  },
  sectionSubtitleInline: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
    marginTop: 2,
  },
  tokenizedContent: {
    marginTop: 8,
  },
  portfolioCard: {
    marginBottom: UI.spacing.md,
    borderRadius: UI.borderRadius.xl,
    backgroundColor: UI.colors.surface,
    ...cardShadow,
  },
  portfolioInner: {
    padding: UI.spacing.md + 2,
  },
  portfolioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  portfolioInfo: {
    flex: 1,
    paddingRight: 8,
  },
  portfolioName: {
    fontSize: 17,
    fontWeight: '700',
    color: UI.colors.text,
    marginBottom: UI.spacing.xs,
  },
  portfolioDescription: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
    lineHeight: 19,
  },
  networkBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
  },
  networkBadgeText: {
    color: UI.colors.surface,
    fontSize: 11,
    fontWeight: '600',
  },
  portfolioStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: 15,
    fontWeight: '700',
    color: UI.colors.text,
  },
  statLabel: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
    marginTop: 2,
  },
  ownedTokens: {
    backgroundColor: '#DCFCE7',
    paddingVertical: 10,
    paddingHorizontal: UI.spacing.sm,
    borderRadius: UI.borderRadius.lg,
    marginBottom: 14,
  },
  ownedTokensText: {
    ...UI.typography.small,
    color: '#166534',
    fontWeight: '600',
    textAlign: 'center',
  },
  tokenizeButton: {
    borderRadius: 999,
    overflow: 'hidden',
  },
  tokenizeButtonGradient: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  tokenizeButtonText: {
    color: UI.colors.surface,
    fontSize: 15,
    fontWeight: '600',
  },
  defiContent: {
    marginTop: 8,
  },
  positionCard: {
    marginBottom: 14,
    borderRadius: UI.borderRadius.xl,
    backgroundColor: UI.colors.surface,
    ...cardShadow,
  },
  positionInner: {
    padding: UI.spacing.md + 2,
  },
  positionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  positionIcon: {
    fontSize: 24,
    marginRight: 10,
  },
  positionInfo: {
    flex: 1,
  },
  positionTitle: {
    ...UI.typography.body,
    fontWeight: '600',
    color: UI.colors.text,
  },
  positionType: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
    marginTop: 2,
  },
  positionStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  defiOpportunities: {
    marginTop: 20,
  },
  opportunitiesTitle: {
    ...UI.typography.h3,
    fontSize: 18,
    color: UI.colors.text,
    marginBottom: UI.spacing.sm,
  },
  opportunityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: UI.colors.surface,
    padding: 14,
    borderRadius: UI.borderRadius.lg,
    marginBottom: 10,
    ...cardShadow,
  },
  opportunityIcon: {
    fontSize: 24,
    marginRight: 10,
  },
  opportunityInfo: {
    flex: 1,
  },
  opportunityTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: UI.colors.text,
  },
  opportunityType: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
    marginTop: 2,
    textTransform: 'capitalize',
  },
  opportunityApy: {
    fontSize: 15,
    fontWeight: '700',
    color: UI.colors.success,
  },
  governanceContent: {
    marginTop: 8,
  },
  proposalCard: {
    marginBottom: 14,
    borderRadius: UI.borderRadius.xl,
    backgroundColor: UI.colors.surface,
    ...cardShadow,
  },
  proposalInner: {
    padding: UI.spacing.md + 2,
  },
  proposalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  proposalTitle: {
    ...UI.typography.body,
    fontWeight: '600',
    color: UI.colors.text,
    flex: 1,
    marginRight: UI.spacing.sm,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
  },
  statusBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
  },
  proposalDescription: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
    lineHeight: 19,
    marginBottom: UI.spacing.sm,
  },
  votingStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  voteItem: {
    alignItems: 'center',
    flex: 1,
  },
  voteLabel: {
    fontSize: 11,
    color: UI.colors.textSecondary,
  },
  voteValue: {
    fontSize: 15,
    fontWeight: '700',
    color: UI.colors.text,
    marginTop: 2,
  },
  progressBar: {
    height: 6,
    backgroundColor: UI.colors.border,
    borderRadius: UI.borderRadius.full,
    marginBottom: UI.spacing.sm,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: UI.colors.success,
    borderRadius: UI.borderRadius.full,
  },
  proposalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timeRemaining: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
  },
  voteButtons: {
    flexDirection: 'row',
  },
  voteButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 999,
    marginLeft: 8,
  },
  voteForButton: {
    backgroundColor: UI.colors.success,
  },
  voteAgainstButton: {
    backgroundColor: UI.colors.error,
  },
  voteButtonText: {
    color: UI.colors.surface,
    fontSize: 13,
    fontWeight: '600',
  },
  bridgeContent: {
    marginTop: 8,
  },
  nftContent: {
    marginTop: 8,
    minHeight: 400, // Ensure minimum height for NFT gallery
  },
  bridgeCard: {
    borderRadius: UI.borderRadius.xl,
    backgroundColor: UI.colors.surface,
    ...cardShadow,
  },
  bridgeInner: {
    padding: UI.spacing.md + 2,
  },
  bridgeTitle: {
    ...UI.typography.h3,
    fontSize: 18,
    color: UI.colors.text,
    marginBottom: 6,
  },
  bridgeDescription: {
    ...UI.typography.small,
    color: UI.colors.textSecondary,
    lineHeight: 19,
    marginBottom: UI.spacing.md,
  },
  bridgeNetworks: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 18,
  },
  networkItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
    marginBottom: 8,
  },
  networkDot: {
    width: 10,
    height: 10,
    borderRadius: 999,
    marginRight: 6,
  },
  networkName: {
    ...UI.typography.small,
    color: UI.colors.text,
  },
  bridgeButton: {
    borderRadius: 999,
    overflow: 'hidden',
  },
  bridgeButtonGradient: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  bridgeButtonText: {
    color: UI.colors.surface,
    fontSize: 15,
    fontWeight: '600',
  },
});
