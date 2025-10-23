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
  Image,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
import { useTheme } from '../theme/PersonalizedThemes';

const { width } = Dimensions.get('window');

interface Trader {
  id: string;
  name: string;
  avatar: string;
  username: string;
  bio: string;
  totalReturn: number;
  monthlyReturn: number;
  winRate: number;
  totalTrades: number;
  followers: number;
  isFollowing: boolean;
  isVerified: boolean;
  riskLevel: 'low' | 'medium' | 'high';
  tradingStyle: 'scalping' | 'swing' | 'position' | 'day_trading';
  portfolioValue: number;
  recentTrades: Trade[];
  performance: PerformanceMetrics;
}

interface Trade {
  id: string;
  symbol: string;
  type: 'buy' | 'sell';
  quantity: number;
  price: number;
  timestamp: string;
  profit: number;
  profitPercentage: number;
  isCopied: boolean;
}

interface PerformanceMetrics {
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
  alpha: number;
  beta: number;
  calmarRatio: number;
}

interface CollectiveFund {
  id: string;
  name: string;
  description: string;
  totalValue: number;
  memberCount: number;
  performance: number;
  riskLevel: 'low' | 'medium' | 'high';
  minimumInvestment: number;
  isJoined: boolean;
  managers: Trader[];
  recentActivity: string[];
  rules: string[];
  category: 'growth' | 'income' | 'balanced' | 'aggressive' | 'conservative';
}

interface SocialTradingProps {
  onTraderPress: (trader: Trader) => void;
  onCopyTrade: (trade: Trade) => void;
  onJoinFund: (fund: CollectiveFund) => void;
}

export default function SocialTrading({ onTraderPress, onCopyTrade, onJoinFund }: SocialTradingProps) {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<'traders' | 'funds' | 'leaderboard'>('traders');
  const [traders, setTraders] = useState<Trader[]>([]);
  const [collectiveFunds, setCollectiveFunds] = useState<CollectiveFund[]>([]);
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
      const mockTraders: Trader[] = [
        {
          id: '1',
          name: 'Marcus "The Oracle" Johnson',
          avatar: 'https://via.placeholder.com/60',
          username: '@marcus_oracle',
          bio: 'BIPOC wealth builder | 15+ years trading | Focus on tech & AI stocks',
          totalReturn: 247.3,
          monthlyReturn: 12.5,
          winRate: 78.5,
          totalTrades: 1247,
          followers: 15420,
          isFollowing: false,
          isVerified: true,
          riskLevel: 'medium',
          tradingStyle: 'swing',
          portfolioValue: 2500000,
          recentTrades: [
            {
              id: '1',
              symbol: 'NVDA',
              type: 'buy',
              quantity: 100,
              price: 450.25,
              timestamp: '2 hours ago',
              profit: 1250.00,
              profitPercentage: 2.78,
              isCopied: false,
            },
          ],
          performance: {
            sharpeRatio: 1.85,
            maxDrawdown: -12.3,
            volatility: 18.5,
            alpha: 8.2,
            beta: 1.1,
            calmarRatio: 2.1,
          },
        },
        {
          id: '2',
          name: 'Aisha "Tech Queen" Williams',
          avatar: 'https://via.placeholder.com/60',
          username: '@aisha_tech',
          bio: 'Tech sector specialist | Crypto enthusiast | Building generational wealth',
          totalReturn: 189.7,
          monthlyReturn: 8.9,
          winRate: 72.1,
          totalTrades: 892,
          followers: 9876,
          isFollowing: true,
          isVerified: true,
          riskLevel: 'high',
          tradingStyle: 'day_trading',
          portfolioValue: 1800000,
          recentTrades: [],
          performance: {
            sharpeRatio: 1.45,
            maxDrawdown: -18.7,
            volatility: 24.2,
            alpha: 6.8,
            beta: 1.3,
            calmarRatio: 1.6,
          },
        },
      ];

      const mockFunds: CollectiveFund[] = [
        {
          id: '1',
          name: 'BIPOC Growth Collective',
          description: 'Diversified growth fund managed by top BIPOC traders',
          totalValue: 12500000,
          memberCount: 1247,
          performance: 18.5,
          riskLevel: 'medium',
          minimumInvestment: 1000,
          isJoined: false,
          managers: [mockTraders[0], mockTraders[1]],
          recentActivity: [
            'Added 2.5% to tech allocation',
            'New member: Sarah joined with $5K',
            'Monthly performance report published',
          ],
          rules: [
            'Minimum $1K investment',
            'No withdrawals for 30 days',
            'Vote on major allocation changes',
          ],
          category: 'growth',
        },
        {
          id: '2',
          name: 'Crypto Wealth Pool',
          description: 'High-risk, high-reward crypto fund for experienced investors',
          totalValue: 3200000,
          memberCount: 456,
          performance: 35.2,
          riskLevel: 'high',
          minimumInvestment: 5000,
          isJoined: true,
          managers: [],
          recentActivity: [
            'Added new DeFi tokens',
            'Rebalanced to 60% BTC, 40% altcoins',
          ],
          rules: [
            'Minimum $5K investment',
            'High risk tolerance required',
            'Monthly rebalancing',
          ],
          category: 'aggressive',
        },
      ];
      
      setTraders(mockTraders);
      setCollectiveFunds(mockFunds);
    } catch (error) {
      console.error('Error loading data:', error);
      Alert.alert('Error', 'Failed to load social trading data');
    } finally {
      setLoading(false);
    }
  };

  const followTrader = async (traderId: string) => {
    try {
      setTraders(prev => 
        prev.map(trader => 
          trader.id === traderId 
            ? { ...trader, isFollowing: !trader.isFollowing }
            : trader
        )
      );
    } catch (error) {
      console.error('Error following trader:', error);
    }
  };

  const copyTrade = async (trade: Trade) => {
    try {
      Alert.alert(
        'Copy Trade',
        `Copy ${trade.symbol} ${trade.type} trade for $${trade.price}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Copy Trade', 
            onPress: () => {
              onCopyTrade(trade);
              Alert.alert('Success', 'Trade copied successfully!');
            }
          },
        ]
      );
    } catch (error) {
      console.error('Error copying trade:', error);
    }
  };

  const joinFund = async (fundId: string) => {
    try {
      setCollectiveFunds(prev => 
        prev.map(fund => 
          fund.id === fundId 
            ? { ...fund, isJoined: !fund.isJoined }
            : fund
        )
      );
      
      const fund = collectiveFunds.find(f => f.id === fundId);
      if (fund) {
        onJoinFund(fund);
      }
    } catch (error) {
      console.error('Error joining fund:', error);
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return '#34C759';
      case 'medium': return '#FF9500';
      case 'high': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  const getPerformanceColor = (performance: number) => {
    return performance > 0 ? '#34C759' : '#FF3B30';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator
          size="large"
          color="#3B82F6"
          style={styles.loadingAnimation}
        />
        <Text style={styles.loadingText}>Loading social trading data...</Text>
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
        <Text style={styles.headerTitle}>Social Trading</Text>
        <Text style={styles.headerSubtitle}>Copy the best, build together</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        {[
          { id: 'traders', name: 'Top Traders', icon: '👑' },
          { id: 'funds', name: 'Collective Funds', icon: '🤝' },
          { id: 'leaderboard', name: 'Leaderboard', icon: '🏆' },
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
        {activeTab === 'traders' && (
          <View style={styles.tradersList}>
            {traders.map((trader) => (
              <TraderCard
                key={trader.id}
                trader={trader}
                onPress={() => onTraderPress(trader)}
                onFollow={() => followTrader(trader.id)}
                onCopyTrade={copyTrade}
                getRiskColor={getRiskColor}
                getPerformanceColor={getPerformanceColor}
              />
            ))}
          </View>
        )}

        {activeTab === 'funds' && (
          <View style={styles.fundsList}>
            {collectiveFunds.map((fund) => (
              <CollectiveFundCard
                key={fund.id}
                fund={fund}
                onJoin={() => joinFund(fund.id)}
                getRiskColor={getRiskColor}
                getPerformanceColor={getPerformanceColor}
              />
            ))}
          </View>
        )}

        {activeTab === 'leaderboard' && (
          <View style={styles.leaderboardList}>
            {traders.map((trader, index) => (
              <LeaderboardItem
                key={trader.id}
                trader={trader}
                rank={index + 1}
                onPress={() => onTraderPress(trader)}
                getPerformanceColor={getPerformanceColor}
              />
            ))}
          </View>
        )}
      </ScrollView>
    </Animated.View>
  );
}

// Trader Card Component
function TraderCard({ 
  trader, 
  onPress, 
  onFollow, 
  onCopyTrade, 
  getRiskColor, 
  getPerformanceColor 
}: any) {
  return (
    <TouchableOpacity style={styles.traderCard} onPress={onPress}>
      <View intensity={20} style={styles.traderBlur}>
        {/* Header */}
        <View style={styles.traderHeader}>
          <Image source={{ uri: trader.avatar }} style={styles.traderAvatar} />
          <View style={styles.traderInfo}>
            <View style={styles.traderNameRow}>
              <Text style={styles.traderName}>{trader.name}</Text>
              {trader.isVerified && (
                <Text style={styles.verifiedIcon}>✓</Text>
              )}
            </View>
            <Text style={styles.traderUsername}>{trader.username}</Text>
            <Text style={styles.traderBio} numberOfLines={2}>
              {trader.bio}
            </Text>
          </View>
          
          <TouchableOpacity
            style={[
              styles.followButton,
              trader.isFollowing && styles.followingButton,
            ]}
            onPress={onFollow}
          >
            <Text style={[
              styles.followButtonText,
              trader.isFollowing && styles.followingButtonText,
            ]}>
              {trader.isFollowing ? 'Following' : 'Follow'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Performance Stats */}
        <View style={styles.performanceStats}>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: getPerformanceColor(trader.totalReturn) }]}>
              {trader.totalReturn > 0 ? '+' : ''}{trader.totalReturn}%
            </Text>
            <Text style={styles.statLabel}>Total Return</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: getPerformanceColor(trader.monthlyReturn) }]}>
              {trader.monthlyReturn > 0 ? '+' : ''}{trader.monthlyReturn}%
            </Text>
            <Text style={styles.statLabel}>Monthly</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{trader.winRate}%</Text>
            <Text style={styles.statLabel}>Win Rate</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{trader.followers.toLocaleString()}</Text>
            <Text style={styles.statLabel}>Followers</Text>
          </View>
        </View>

        {/* Risk Level */}
        <View style={styles.riskLevel}>
          <Text style={styles.riskLabel}>Risk Level:</Text>
          <View style={[styles.riskBadge, { backgroundColor: getRiskColor(trader.riskLevel) }]}>
            <Text style={styles.riskText}>{trader.riskLevel.toUpperCase()}</Text>
          </View>
        </View>

        {/* Recent Trades */}
        {trader.recentTrades.length > 0 && (
          <View style={styles.recentTrades}>
            <Text style={styles.recentTradesTitle}>Recent Trades</Text>
            {trader.recentTrades.map((trade: Trade) => (
              <TradeItem
                key={trade.id}
                trade={trade}
                onCopy={() => onCopyTrade(trade)}
                getPerformanceColor={getPerformanceColor}
              />
            ))}
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

// Trade Item Component
function TradeItem({ trade, onCopy, getPerformanceColor }: any) {
  return (
    <View style={styles.tradeItem}>
      <View style={styles.tradeInfo}>
        <Text style={styles.tradeSymbol}>{trade.symbol}</Text>
        <Text style={styles.tradeType}>{trade.type.toUpperCase()}</Text>
        <Text style={styles.tradePrice}>${trade.price}</Text>
      </View>
      
      <View style={styles.tradePerformance}>
        <Text style={[styles.tradeProfit, { color: getPerformanceColor(trade.profit) }]}>
          {trade.profit > 0 ? '+' : ''}${(trade.profit || 0).toFixed(2)}
        </Text>
        <Text style={[styles.tradePercentage, { color: getPerformanceColor(trade.profitPercentage) }]}>
          {trade.profitPercentage > 0 ? '+' : ''}{trade.profitPercentage}%
        </Text>
      </View>
      
      <TouchableOpacity style={styles.copyButton} onPress={onCopy}>
        <Text style={styles.copyButtonText}>Copy</Text>
      </TouchableOpacity>
    </View>
  );
}

// Collective Fund Card Component
function CollectiveFundCard({ fund, onJoin, getRiskColor, getPerformanceColor }: any) {
  return (
    <TouchableOpacity style={styles.fundCard}>
      <View intensity={20} style={styles.fundBlur}>
        {/* Header */}
        <View style={styles.fundHeader}>
          <View style={styles.fundInfo}>
            <Text style={styles.fundName}>{fund.name}</Text>
            <Text style={styles.fundDescription} numberOfLines={2}>
              {fund.description}
            </Text>
          </View>
          
          <TouchableOpacity
            style={[
              styles.joinButton,
              fund.isJoined && styles.joinedButton,
            ]}
            onPress={onJoin}
          >
            <Text style={[
              styles.joinButtonText,
              fund.isJoined && styles.joinedButtonText,
            ]}>
              {fund.isJoined ? 'Joined' : 'Join'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Fund Stats */}
        <View style={styles.fundStats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>${((fund.totalValue || 0) / 1000000).toFixed(1)}M</Text>
            <Text style={styles.statLabel}>Total Value</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{fund.memberCount.toLocaleString()}</Text>
            <Text style={styles.statLabel}>Members</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: getPerformanceColor(fund.performance) }]}>
              {fund.performance > 0 ? '+' : ''}{fund.performance}%
            </Text>
            <Text style={styles.statLabel}>Performance</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>${fund.minimumInvestment.toLocaleString()}</Text>
            <Text style={styles.statLabel}>Min. Investment</Text>
          </View>
        </View>

        {/* Risk Level */}
        <View style={styles.riskLevel}>
          <Text style={styles.riskLabel}>Risk Level:</Text>
          <View style={[styles.riskBadge, { backgroundColor: getRiskColor(fund.riskLevel) }]}>
            <Text style={styles.riskText}>{fund.riskLevel.toUpperCase()}</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// Leaderboard Item Component
function LeaderboardItem({ trader, rank, onPress, getPerformanceColor }: any) {
  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1: return '🥇';
      case 2: return '🥈';
      case 3: return '🥉';
      default: return `#${rank}`;
    }
  };

  return (
    <TouchableOpacity style={styles.leaderboardItem} onPress={onPress}>
      <View style={styles.rankContainer}>
        <Text style={styles.rankIcon}>{getRankIcon(rank)}</Text>
      </View>
      
      <Image source={{ uri: trader.avatar }} style={styles.leaderboardAvatar} />
      
      <View style={styles.leaderboardInfo}>
        <Text style={styles.leaderboardName}>{trader.name}</Text>
        <Text style={styles.leaderboardUsername}>{trader.username}</Text>
      </View>
      
      <View style={styles.leaderboardPerformance}>
        <Text style={[styles.leaderboardReturn, { color: getPerformanceColor(trader.totalReturn) }]}>
          {trader.totalReturn > 0 ? '+' : ''}{trader.totalReturn}%
        </Text>
        <Text style={styles.leaderboardFollowers}>
          {trader.followers.toLocaleString()} followers
        </Text>
      </View>
    </TouchableOpacity>
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
  tradersList: {
    padding: 16,
  },
  traderCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  traderBlur: {
    padding: 20,
  },
  traderHeader: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  traderAvatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    marginRight: 12,
  },
  traderInfo: {
    flex: 1,
  },
  traderNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  traderName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  verifiedIcon: {
    fontSize: 16,
    color: '#007AFF',
    marginLeft: 6,
  },
  traderUsername: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  traderBio: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  followButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: '#667eea',
  },
  followingButton: {
    backgroundColor: '#34C759',
  },
  followButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  followingButtonText: {
    color: 'white',
  },
  performanceStats: {
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
  riskLevel: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  riskLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  riskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  riskText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  recentTrades: {
    marginTop: 16,
  },
  recentTradesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  tradeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  tradeInfo: {
    flex: 1,
  },
  tradeSymbol: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  tradeType: {
    fontSize: 12,
    color: '#666',
  },
  tradePrice: {
    fontSize: 12,
    color: '#666',
  },
  tradePerformance: {
    alignItems: 'flex-end',
    marginRight: 12,
  },
  tradeProfit: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  tradePercentage: {
    fontSize: 12,
  },
  copyButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    backgroundColor: '#667eea',
  },
  copyButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  fundsList: {
    padding: 16,
  },
  fundCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  fundBlur: {
    padding: 20,
  },
  fundHeader: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  fundInfo: {
    flex: 1,
  },
  fundName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  fundDescription: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  joinButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: '#667eea',
  },
  joinedButton: {
    backgroundColor: '#34C759',
  },
  joinButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  joinedButtonText: {
    color: 'white',
  },
  fundStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  leaderboardList: {
    padding: 16,
  },
  leaderboardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  rankContainer: {
    width: 40,
    alignItems: 'center',
  },
  rankIcon: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  leaderboardAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
  },
  leaderboardInfo: {
    flex: 1,
  },
  leaderboardName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  leaderboardUsername: {
    fontSize: 12,
    color: '#666',
  },
  leaderboardPerformance: {
    alignItems: 'flex-end',
  },
  leaderboardReturn: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  leaderboardFollowers: {
    fontSize: 12,
    color: '#666',
  },
});
