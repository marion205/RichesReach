/**
 * Social Trading Features
 * Copy trading, social signals, and community features
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  FlatList,
  ActivityIndicator,
  Alert,
  RefreshControl,
  Share,
} from 'react-native';
import { useQuery, useMutation, gql } from '@apollo/client';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { globalNavigate } from '../navigation/NavigationService';
import NewsFeed from '../features/social/components/NewsFeed';

// GraphQL Queries and Mutations
const GET_SOCIAL_FEEDS = gql`
  query GetSocialFeeds($limit: Int, $offset: Int) {
    socialFeeds(limit: $limit, offset: $offset) {
      id
      user {
        id
        username
        avatar
        verified
        followerCount
        winRate
      }
      content
      type
      timestamp
      likes
      comments
      shares
      tradeData {
        symbol
        side
        quantity
        price
        pnl
      }
      performance {
        totalReturn
        winRate
        sharpeRatio
      }
    }
  }
`;

const GET_TOP_TRADERS = gql`
  query GetTopTraders($period: String!) {
    topTraders(period: $period) {
      id
      username
      avatar
      verified
      followerCount
      performance {
        totalReturn
        winRate
        sharpeRatio
        maxDrawdown
        totalTrades
      }
      recentTrades {
        symbol
        side
        quantity
        price
        timestamp
        pnl
      }
    }
  }
`;

const FOLLOW_TRADER = gql`
  mutation FollowTrader($traderId: ID!) {
    followTrader(traderId: $traderId) {
      success
      message
    }
  }
`;

const COPY_TRADE = gql`
  mutation CopyTrade($tradeId: ID!, $amount: Float!) {
    copyTrade(tradeId: $tradeId, amount: $amount) {
      success
      message
      copiedTrade {
        id
        symbol
        side
        quantity
        price
      }
    }
  }
`;

const LIKE_POST = gql`
  mutation LikePost($postId: ID!) {
    likePost(postId: $postId) {
      success
      likes
    }
  }
`;

const GET_SWING_SIGNALS = gql`
  query GetSwingSignals($limit: Int) {
    swingSignals(limit: $limit) {
      id
      symbol
      signalType
      entryPrice
      targetPrice
      stopPrice
      mlScore
      confidence
      timeframe
      reasoning
      thesis
      isActive
      createdAt
      triggeredAt
      createdBy
      riskRewardRatio
      daysSinceTriggered
      isLikedByUser
      userLikeCount
      isValidated
      validationPrice
      validationTimestamp
      technicalIndicators {
        name
        value
        signal
        strength
        description
      }
      patterns {
        name
        confidence
        signal
        description
        timeframe
      }
      features
      hftIntegration {
        scalpingEnabled
        momentumStrategy
        arbitrageEnabled
        marketMakingStrategy
        latencyTarget
        maxOrdersPerSecond
      }
    }
  }
`;

interface User {
  id: string;
  username: string;
  avatar: string;
  verified: boolean;
  followerCount: number;
  winRate: number;
}

interface TradeData {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  pnl: number;
}

interface Performance {
  totalReturn: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown?: number;
  totalTrades?: number;
}

interface SocialPost {
  id: string;
  user: User;
  content: string;
  type: 'trade' | 'analysis' | 'question' | 'achievement';
  timestamp: string;
  likes: number;
  comments: number;
  shares: number;
  tradeData?: TradeData;
  performance?: Performance;
}

interface TopTrader {
  id: string;
  username: string;
  avatar: string;
  verified: boolean;
  followerCount: number;
  performance: Performance;
  recentTrades: TradeData[];
}

interface SocialTradingProps {
  userId: string;
  onTraderSelect?: (trader: TopTrader) => void;
  onTradeCopy?: (trade: TradeData) => void;
  initialTab?: 'feed' | 'traders' | 'signals' | 'news';
}

export const SocialTrading: React.FC<SocialTradingProps> = ({
  userId,
  onTraderSelect,
  onTradeCopy,
  initialTab = 'feed',
}) => {
  const [activeTab, setActiveTab] = useState<'feed' | 'traders' | 'signals' | 'news'>(initialTab);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('1M');

  const { data: feedsData, loading: feedsLoading, error: feedsError, refetch: refetchFeeds } = useQuery(
    GET_SOCIAL_FEEDS,
    {
      variables: { limit: 20, offset: 0 },
      errorPolicy: 'all',
      fetchPolicy: 'cache-and-network',
    }
  );

  const { data: tradersData, loading: tradersLoading, error: tradersError, refetch: refetchTraders } = useQuery(
    GET_TOP_TRADERS,
    {
      variables: { period: selectedPeriod },
      errorPolicy: 'all',
      fetchPolicy: 'cache-and-network',
    }
  );

  const { data: signalsData, loading: signalsLoading, error: signalsError, refetch: refetchSignals } = useQuery(
    GET_SWING_SIGNALS,
    {
      variables: { limit: 50 },
      errorPolicy: 'all',
      fetchPolicy: 'cache-and-network',
    }
  );

  // Timeout handling for loading states
  const [feedsLoadingTimeout, setFeedsLoadingTimeout] = useState(false);
  const [tradersLoadingTimeout, setTradersLoadingTimeout] = useState(false);
  const [signalsLoadingTimeout, setSignalsLoadingTimeout] = useState(false);

  useEffect(() => {
    if (feedsLoading && !feedsData) {
      const timer = setTimeout(() => setFeedsLoadingTimeout(true), 2000);
      return () => clearTimeout(timer);
    } else {
      setFeedsLoadingTimeout(false);
    }
  }, [feedsLoading, feedsData]);

  useEffect(() => {
    if (tradersLoading && !tradersData) {
      const timer = setTimeout(() => setTradersLoadingTimeout(true), 2000);
      return () => clearTimeout(timer);
    } else {
      setTradersLoadingTimeout(false);
    }
  }, [tradersLoading, tradersData]);

  useEffect(() => {
    if (signalsLoading && !signalsData) {
      const timer = setTimeout(() => setSignalsLoadingTimeout(true), 2000);
      return () => clearTimeout(timer);
    } else {
      setSignalsLoadingTimeout(false);
    }
  }, [signalsLoading, signalsData]);

  // Mock data generators
  const getMockFeeds = () => [
    {
      id: 'mock-feed-1',
      user: {
        id: 'user1',
        username: 'TradingPro',
        avatar: 'https://i.pravatar.cc/150?img=1',
        verified: true,
        followerCount: 12500,
        winRate: 68.5,
      },
      content: 'Just closed a great position on AAPL. Up 12% in 3 days! 📈',
      type: 'trade',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      likes: 234,
      comments: 45,
      shares: 12,
      tradeData: {
        symbol: 'AAPL',
        side: 'BUY',
        quantity: 100,
        price: 175.50,
        pnl: 2100.00,
      },
      performance: {
        totalReturn: 28.5,
        winRate: 68.5,
        sharpeRatio: 1.85,
      },
    },
    {
      id: 'mock-feed-2',
      user: {
        id: 'user2',
        username: 'CryptoMaster',
        avatar: 'https://i.pravatar.cc/150?img=2',
        verified: true,
        followerCount: 8900,
        winRate: 72.3,
      },
      content: 'Market analysis: Tech stocks showing strong momentum. Bullish on Q4 earnings.',
      type: 'analysis',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      likes: 189,
      comments: 32,
      shares: 8,
      performance: {
        totalReturn: 35.2,
        winRate: 72.3,
        sharpeRatio: 2.1,
      },
    },
    {
      id: 'mock-feed-3',
      user: {
        id: 'user3',
        username: 'OptionsGuru',
        avatar: 'https://i.pravatar.cc/150?img=3',
        verified: false,
        followerCount: 5600,
        winRate: 65.8,
      },
      content: 'Options strategy working well today. Covered calls generating steady income.',
      type: 'trade',
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      likes: 156,
      comments: 28,
      shares: 5,
      tradeData: {
        symbol: 'TSLA',
        side: 'SELL',
        quantity: 50,
        price: 245.80,
        pnl: 890.50,
      },
      performance: {
        totalReturn: 22.4,
        winRate: 65.8,
        sharpeRatio: 1.65,
      },
    },
  ];

  const getMockTraders = () => [
    {
      id: 'trader1',
      username: 'TradingPro',
      avatar: 'https://i.pravatar.cc/150?img=1',
      verified: true,
      followerCount: 12500,
      performance: {
        totalReturn: 28.5,
        winRate: 68.5,
        sharpeRatio: 1.85,
        maxDrawdown: -8.2,
        totalTrades: 245,
      },
      recentTrades: [
        { symbol: 'AAPL', side: 'BUY', quantity: 100, price: 175.50, timestamp: new Date().toISOString(), pnl: 2100.00 },
        { symbol: 'MSFT', side: 'BUY', quantity: 75, price: 385.20, timestamp: new Date().toISOString(), pnl: 1450.00 },
        { symbol: 'NVDA', side: 'SELL', quantity: 50, price: 495.80, timestamp: new Date().toISOString(), pnl: -320.50 },
      ],
    },
    {
      id: 'trader2',
      username: 'CryptoMaster',
      avatar: 'https://i.pravatar.cc/150?img=2',
      verified: true,
      followerCount: 8900,
      performance: {
        totalReturn: 35.2,
        winRate: 72.3,
        sharpeRatio: 2.1,
        maxDrawdown: -6.5,
        totalTrades: 189,
      },
      recentTrades: [
        { symbol: 'GOOGL', side: 'BUY', quantity: 80, price: 142.30, timestamp: new Date().toISOString(), pnl: 1890.00 },
        { symbol: 'AMZN', side: 'BUY', quantity: 60, price: 148.50, timestamp: new Date().toISOString(), pnl: 1120.00 },
      ],
    },
    {
      id: 'trader3',
      username: 'OptionsGuru',
      avatar: 'https://i.pravatar.cc/150?img=3',
      verified: false,
      followerCount: 5600,
      performance: {
        totalReturn: 22.4,
        winRate: 65.8,
        sharpeRatio: 1.65,
        maxDrawdown: -10.2,
        totalTrades: 312,
      },
      recentTrades: [
        { symbol: 'TSLA', side: 'SELL', quantity: 50, price: 245.80, timestamp: new Date().toISOString(), pnl: 890.50 },
        { symbol: 'META', side: 'BUY', quantity: 90, price: 325.40, timestamp: new Date().toISOString(), pnl: 1560.00 },
      ],
    },
  ];

  const getMockSignals = () => [
    {
      id: 'signal1',
      symbol: 'AAPL',
      signalType: 'LONG',
      mlScore: 0.85,
      entryPrice: 175.50,
      targetPrice: 192.00,
      stopPrice: 168.00,
      riskRewardRatio: '2.5:1',
      reasoning: 'Strong Q4 earnings outlook, bullish technical pattern, positive analyst sentiment.',
      timeframe: '2-4 weeks',
      hftIntegration: true,
      isLikedByUser: false,
      userLikeCount: 124,
    },
    {
      id: 'signal2',
      symbol: 'MSFT',
      signalType: 'LONG',
      mlScore: 0.78,
      entryPrice: 385.20,
      targetPrice: 410.00,
      stopPrice: 370.00,
      riskRewardRatio: '1.6:1',
      reasoning: 'Cloud revenue growth accelerating, AI integration driving demand.',
      timeframe: '3-5 weeks',
      hftIntegration: false,
      isLikedByUser: true,
      userLikeCount: 89,
    },
    {
      id: 'signal3',
      symbol: 'TSLA',
      signalType: 'SHORT',
      mlScore: 0.72,
      entryPrice: 245.80,
      targetPrice: 220.00,
      stopPrice: 260.00,
      riskRewardRatio: '1.8:1',
      reasoning: 'Overbought conditions, potential resistance at $250, profit-taking expected.',
      timeframe: '1-2 weeks',
      hftIntegration: true,
      isLikedByUser: false,
      userLikeCount: 67,
    },
  ];

  // Use mock data immediately if loading, timeout, or error - optimistic loading
  const effectiveFeeds = useMemo(() => {
    if (feedsData?.socialFeeds?.length) {
      return feedsData.socialFeeds;
    }
    return getMockFeeds();
  }, [feedsData, feedsLoadingTimeout, feedsError]);

  const effectiveTraders = useMemo(() => {
    if (tradersData?.topTraders?.length) {
      return tradersData.topTraders;
    }
    return getMockTraders();
  }, [tradersData, tradersLoadingTimeout, tradersError]);

  const effectiveSignals = useMemo(() => {
    if (signalsData?.swingSignals?.length) {
      return signalsData.swingSignals;
    }
    return getMockSignals();
  }, [signalsData, signalsLoadingTimeout, signalsError]);

  const [followTrader] = useMutation(FOLLOW_TRADER);
  const [copyTrade] = useMutation(COPY_TRADE);
  const [likePost] = useMutation(LIKE_POST);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([refetchFeeds(), refetchTraders(), refetchSignals()]);
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleFollowTrader = async (traderId: string) => {
    try {
      const result = await followTrader({ variables: { traderId } });
      if (result.data?.followTrader?.success) {
        Alert.alert('Success', 'You are now following this trader!');
        refetchTraders();
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to follow trader');
    }
  };

  const handleCopyTrade = async (tradeId: string, amount: number) => {
    try {
      const result = await copyTrade({ variables: { tradeId, amount } });
      if (result.data?.copyTrade?.success) {
        Alert.alert('Success', 'Trade copied successfully!');
        onTradeCopy?.(result.data.copyTrade.copiedTrade);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to copy trade');
    }
  };

  const handleLikePost = async (postId: string) => {
    try {
      await likePost({ variables: { postId } });
      refetchFeeds();
    } catch (error) {
      console.error('Error liking post:', error);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const getPerformanceColor = (returnValue: number) => {
    if (returnValue > 0) return '#34C759'; // iOS green
    if (returnValue < 0) return '#FF3B30'; // iOS red
    return '#8e8e93'; // iOS gray
  };

  const renderSocialPost = ({ item }: { item: SocialPost }) => (
    <View style={styles.postCard}>
      {/* User Header */}
      <View style={styles.postHeader}>
        <Image source={{ uri: item.user.avatar }} style={styles.avatar} />
        <View style={styles.userInfo}>
          <View style={styles.usernameRow}>
            <Text style={styles.username}>{item.user.username}</Text>
            {item.user.verified && (
              <View style={styles.verifiedBadge}>
                <Ionicons name="checkmark-circle" size={14} color="#6366F1" />
              </View>
            )}
          </View>
          <Text style={styles.userStats}>
            {item.user.followerCount.toLocaleString()} followers · {item.user.winRate}% win
          </Text>
        </View>
        <View style={styles.timestampPill}>
          <Text style={styles.timestamp}>{formatTimestamp(item.timestamp)}</Text>
        </View>
      </View>

      {/* Post Content */}
      <Text style={styles.postContent}>{item.content}</Text>

      {/* Trade Data */}
      {item.tradeData && (
        <View style={styles.tradeCard}>
          <View style={styles.tradeHeader}>
            <View style={styles.tradeSymbolWrap}>
              <Text style={styles.tradeSymbol}>{item.tradeData.symbol}</Text>
              <View style={[
                styles.tradeSide,
                { backgroundColor: item.tradeData.side === 'BUY' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)' }
              ]}>
                <Text style={[styles.tradeSideText, { color: item.tradeData.side === 'BUY' ? '#10B981' : '#EF4444' }]}>{item.tradeData.side}</Text>
              </View>
            </View>
            <Text style={[
              styles.tradePnl,
              { color: getPerformanceColor(item.tradeData.pnl) }
            ]}>
              {item.tradeData.pnl >= 0 ? '+' : ''}${item.tradeData.pnl.toFixed(2)}
            </Text>
          </View>
          <Text style={styles.tradeDetail}>
            {item.tradeData.quantity} shares @ ${item.tradeData.price}
          </Text>
          <TouchableOpacity
            style={styles.copyButton}
            onPress={() => handleCopyTrade(item.id, 1000)}
            activeOpacity={0.85}
          >
            <Ionicons name="copy-outline" size={14} color="#FFFFFF" />
            <Text style={styles.copyButtonText}>Copy Trade</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Performance Stats */}
      {item.performance && (
        <View style={styles.performanceCard}>
          <View style={styles.performanceStats}>
            <View style={styles.performanceStat}>
              <Text style={styles.performanceLabel}>Return</Text>
              <Text style={[
                styles.performanceValue,
                { color: getPerformanceColor(item.performance.totalReturn) }
              ]}>
                {item.performance.totalReturn > 0 ? '+' : ''}{item.performance.totalReturn.toFixed(1)}%
              </Text>
            </View>
            <View style={styles.performanceDivider} />
            <View style={styles.performanceStat}>
              <Text style={styles.performanceLabel}>Win Rate</Text>
              <Text style={styles.performanceValue}>
                {item.performance.winRate.toFixed(1)}%
              </Text>
            </View>
            <View style={styles.performanceDivider} />
            <View style={styles.performanceStat}>
              <Text style={styles.performanceLabel}>Sharpe</Text>
              <Text style={styles.performanceValue}>
                {item.performance.sharpeRatio.toFixed(2)}
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Post Actions */}
      <View style={styles.postActions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleLikePost(item.id)}
          activeOpacity={0.7}
        >
          <Ionicons name="heart-outline" size={18} color="#64748B" />
          <Text style={styles.actionText}>{item.likes}</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => Alert.alert('Comments', `View and add comments for this post. (${item.comments} comments)`, [{ text: 'OK' }])}
          activeOpacity={0.7}
        >
          <Ionicons name="chatbubble-outline" size={18} color="#64748B" />
          <Text style={styles.actionText}>{item.comments}</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={async () => {
            try {
              await Share.share({
                message: item.content || `Check out this trade from RichesReach${item.tradeData ? `: ${item.tradeData.side} ${item.tradeData.quantity} ${item.tradeData.symbol} @ $${item.tradeData.price}` : ''}`,
                title: 'RichesReach',
              });
            } catch {
              Alert.alert('Share', 'Sharing is not available.');
            }
          }}
          activeOpacity={0.7}
        >
          <Ionicons name="share-outline" size={18} color="#64748B" />
          <Text style={styles.actionText}>{item.shares}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderTopTrader = ({ item }: { item: TopTrader }) => (
    <TouchableOpacity
      style={styles.traderCard}
      onPress={() => onTraderSelect?.(item)}
      activeOpacity={0.85}
    >
      <View style={styles.traderHeader}>
        <View style={styles.traderAvatarWrap}>
          <Image source={{ uri: item.avatar }} style={styles.traderAvatar} />
          {item.verified && (
            <View style={styles.traderVerifiedDot}>
              <Ionicons name="checkmark" size={8} color="#FFFFFF" />
            </View>
          )}
        </View>
        <View style={styles.traderInfo}>
          <Text style={styles.traderName}>{item.username}</Text>
          <Text style={styles.traderFollowers}>
            {item.followerCount.toLocaleString()} followers
          </Text>
        </View>
        <TouchableOpacity
          style={styles.followButton}
          onPress={() => handleFollowTrader(item.id)}
          activeOpacity={0.85}
        >
          <Ionicons name="person-add-outline" size={14} color="#FFFFFF" />
          <Text style={styles.followButtonText}>Follow</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.traderPerformance}>
        <View style={styles.traderStat}>
          <Text style={styles.traderStatLabel}>Return</Text>
          <Text style={[
            styles.traderStatValue,
            { color: getPerformanceColor(item.performance.totalReturn) }
          ]}>
            {item.performance.totalReturn > 0 ? '+' : ''}{item.performance.totalReturn.toFixed(1)}%
          </Text>
        </View>
        <View style={styles.traderStatDivider} />
        <View style={styles.traderStat}>
          <Text style={styles.traderStatLabel}>Win Rate</Text>
          <Text style={styles.traderStatValue}>
            {item.performance.winRate.toFixed(1)}%
          </Text>
        </View>
        <View style={styles.traderStatDivider} />
        <View style={styles.traderStat}>
          <Text style={styles.traderStatLabel}>Sharpe</Text>
          <Text style={styles.traderStatValue}>
            {item.performance.sharpeRatio.toFixed(2)}
          </Text>
        </View>
      </View>

      <View style={styles.recentTrades}>
        <Text style={styles.recentTradesTitle}>Recent Trades</Text>
        {item.recentTrades.slice(0, 3).map((trade, index) => (
          <View key={index} style={styles.recentTrade}>
            <Text style={styles.recentTradeSymbol}>{trade.symbol}</Text>
            <View style={[styles.recentTradeSidePill, { backgroundColor: trade.side === 'BUY' ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)' }]}>
              <Text style={[
                styles.recentTradeSide,
                { color: trade.side === 'BUY' ? '#10B981' : '#EF4444' }
              ]}>
                {trade.side}
              </Text>
            </View>
            <Text style={[
              styles.recentTradePnl,
              { color: getPerformanceColor(trade.pnl) }
            ]}>
              {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
            </Text>
          </View>
        ))}
      </View>
    </TouchableOpacity>
  );

  const renderSignal = ({ item }: { item: any }) => (
    <TouchableOpacity style={styles.signalCard}>
      <View style={styles.signalHeader}>
        <View style={styles.signalSymbol}>
          <Text style={styles.signalSymbolText}>{item.symbol}</Text>
          <Text style={[
            styles.signalType,
            item.signalType === 'LONG' ? styles.longSignal : styles.shortSignal
          ]}>
            {item.signalType}
          </Text>
        </View>
        <View style={styles.signalScore}>
          <Text style={styles.signalScoreText}>
            {(item.mlScore * 100).toFixed(0)}%
          </Text>
          <Text style={styles.signalScoreLabel}>ML Score</Text>
        </View>
      </View>

      <View style={styles.signalPrices}>
        <View style={styles.priceItem}>
          <Text style={styles.priceLabel}>Entry</Text>
          <Text style={styles.priceValue}>${item.entryPrice}</Text>
        </View>
        <View style={styles.priceItem}>
          <Text style={styles.priceLabel}>Target</Text>
          <Text style={styles.priceValue}>${item.targetPrice}</Text>
        </View>
        <View style={styles.priceItem}>
          <Text style={styles.priceLabel}>Stop</Text>
          <Text style={styles.priceValue}>${item.stopPrice}</Text>
        </View>
        <View style={styles.priceItem}>
          <Text style={styles.priceLabel}>R:R</Text>
          <Text style={styles.priceValue}>{item.riskRewardRatio}</Text>
        </View>
      </View>

      <Text style={styles.signalReasoning}>{item.reasoning}</Text>
      
      {item.hftIntegration && (
        <View style={styles.hftBadge}>
          <Ionicons name="flash" size={12} color="#0F0" />
          <Text style={styles.hftText}>HFT Enabled</Text>
        </View>
      )}

      <View style={styles.signalFooter}>
        <Text style={styles.signalTimeframe}>{item.timeframe}</Text>
        <View style={styles.signalActions}>
          <TouchableOpacity style={styles.likeButton}>
            <Ionicons 
              name={item.isLikedByUser ? "heart" : "heart-outline"} 
              size={16} 
              color={item.isLikedByUser ? "#FF3B30" : "#8E8E93"} 
            />
            <Text style={styles.likeCount}>{item.userLikeCount}</Text>
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'feed':
        return (
          <FlatList
            data={effectiveFeeds}
            renderItem={renderSocialPost}
            keyExtractor={(item) => item.id}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
            showsVerticalScrollIndicator={false}
          />
        );
      case 'traders':
        return (
          <View style={styles.tradersContainer}>
            <View style={styles.periodSelector}>
              {['1W', '1M', '3M', '1Y'].map((period) => (
                <TouchableOpacity
                  key={period}
                  style={[
                    styles.periodButton,
                    selectedPeriod === period && styles.activePeriodButton,
                  ]}
                  onPress={() => setSelectedPeriod(period)}
                >
                  <Text style={[
                    styles.periodButtonText,
                    selectedPeriod === period && styles.activePeriodButtonText,
                  ]}>
                    {period}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            <FlatList
              data={effectiveTraders}
              renderItem={renderTopTrader}
              keyExtractor={(item) => item.id}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              showsVerticalScrollIndicator={false}
            />
          </View>
        );
      case 'signals':
        return (
          <View style={styles.signalsContainer}>
            <FlatList
              data={effectiveSignals}
              renderItem={renderSignal}
              keyExtractor={(item) => item.id}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              showsVerticalScrollIndicator={false}
              ListEmptyComponent={
                <View style={styles.emptyContainer}>
                  <Text style={styles.emptyText}>No signals available</Text>
                </View>
              }
            />
          </View>
        );
      case 'news':
        return <NewsFeed />;
      default:
        return null;
    }
  };

  // Always render content - never show blocking loading screen
  // Mock data ensures feeds, traders, and signals are always available

  return (
    <View style={styles.container}>
      {/* Header */}
      <LinearGradient
        colors={['#0F172A', '#1E293B', '#1E3A5F']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View style={styles.headerLeft}>
            <View style={styles.headerIconWrap}>
              <Ionicons name="people" size={20} color="#818CF8" />
            </View>
            <View>
              <Text style={styles.headerTitle}>Social Trading</Text>
              <Text style={styles.headerSubtitle}>Connect · Copy · Profit</Text>
            </View>
          </View>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setActiveTab('traders')}
            activeOpacity={0.8}
          >
            <Ionicons name="search-outline" size={22} color="#94A3B8" />
          </TouchableOpacity>
        </View>
      </LinearGradient>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        {[
          { key: 'feed', label: 'Feed', icon: 'home-outline', activeIcon: 'home' },
          { key: 'traders', label: 'Traders', icon: 'trophy-outline', activeIcon: 'trophy' },
          { key: 'signals', label: 'Signals', icon: 'trending-up-outline', activeIcon: 'trending-up' },
          { key: 'news', label: 'News', icon: 'newspaper-outline', activeIcon: 'newspaper' },
        ].map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              style={[
                styles.tabButton,
                isActive && styles.activeTabButton,
              ]}
              onPress={() => setActiveTab(tab.key as any)}
              activeOpacity={0.8}
            >
              <Ionicons
                name={(isActive ? tab.activeIcon : tab.icon) as any}
                size={18}
                color={isActive ? '#FFFFFF' : '#64748B'}
              />
              <Text style={[
                styles.tabText,
                isActive && styles.activeTabText,
              ]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Tab Content */}
      <View style={styles.content}>
        {renderTabContent()}
      </View>
    </View>
  );
};

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
  },
  loadingText: {
    color: '#0F172A',
    marginTop: 12,
    fontSize: 16,
    fontWeight: '600',
  },

  /* ============ HEADER ============ */
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 18,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(129,140,248,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(129,140,248,0.25)',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '900',
    color: '#F1F5F9',
    letterSpacing: -0.3,
  },
  headerSubtitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
    marginTop: 2,
  },
  headerButton: {
    width: 40,
    height: 40,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.10)',
  },

  /* ============ TABS ============ */
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 6,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(148,163,184,0.15)',
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: 'transparent',
    gap: 6,
  },
  activeTabButton: {
    backgroundColor: '#6366F1',
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  tabText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '700',
  },
  activeTabText: {
    color: '#FFFFFF',
    fontWeight: '800',
  },

  /* ============ CONTENT ============ */
  content: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },

  /* ============ POST CARD ============ */
  postCard: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginVertical: 6,
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.15)',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 2,
  },
  postHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 10,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: 'rgba(99,102,241,0.15)',
  },
  userInfo: {
    flex: 1,
  },
  usernameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  username: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  verifiedBadge: {
    width: 18,
    height: 18,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(99,102,241,0.10)',
  },
  userStats: {
    fontSize: 12,
    color: '#94A3B8',
    fontWeight: '600',
    marginTop: 2,
  },
  timestampPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
    backgroundColor: '#F1F5F9',
  },
  timestamp: {
    fontSize: 11,
    color: '#94A3B8',
    fontWeight: '700',
  },
  postContent: {
    fontSize: 15,
    color: '#0F172A',
    lineHeight: 22,
    marginBottom: 12,
    fontWeight: '500',
  },

  /* TRADE CARD */
  tradeCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.15)',
  },
  tradeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  tradeSymbolWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  tradeSymbol: {
    fontSize: 18,
    fontWeight: '900',
    color: '#0F172A',
    letterSpacing: -0.2,
  },
  tradeSide: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  tradeSideText: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  tradeDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  tradeDetail: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: '600',
    marginBottom: 10,
  },
  tradePnl: {
    fontSize: 16,
    fontWeight: '900',
  },
  copyButton: {
    backgroundColor: '#6366F1',
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 12,
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  copyButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
  },

  /* PERFORMANCE */
  performanceCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.12)',
  },
  performanceTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#64748B',
    marginBottom: 8,
  },
  performanceStats: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  performanceStat: {
    alignItems: 'center',
    flex: 1,
  },
  performanceDivider: {
    width: 1,
    height: 28,
    backgroundColor: 'rgba(148,163,184,0.20)',
  },
  performanceLabel: {
    fontSize: 10,
    color: '#94A3B8',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
    marginBottom: 4,
  },
  performanceValue: {
    fontSize: 16,
    fontWeight: '900',
    color: '#0F172A',
  },

  /* POST ACTIONS */
  postActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(148,163,184,0.12)',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 10,
    gap: 6,
  },
  actionText: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: '700',
  },

  /* ============ TRADERS ============ */
  tradersContainer: {
    flex: 1,
  },
  periodSelector: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(148,163,184,0.12)',
  },
  periodButton: {
    paddingHorizontal: 18,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.20)',
  },
  activePeriodButton: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 2,
  },
  periodButtonText: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: '700',
  },
  activePeriodButtonText: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  traderCard: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginVertical: 6,
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.15)',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 2,
  },
  traderHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
    gap: 12,
  },
  traderAvatarWrap: {
    position: 'relative',
  },
  traderAvatar: {
    width: 50,
    height: 50,
    borderRadius: 18,
    borderWidth: 2,
    borderColor: 'rgba(99,102,241,0.15)',
  },
  traderVerifiedDot: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#6366F1',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  traderInfo: {
    flex: 1,
  },
  traderNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  traderName: {
    fontSize: 17,
    fontWeight: '800',
    color: '#0F172A',
  },
  traderFollowers: {
    fontSize: 13,
    color: '#94A3B8',
    fontWeight: '600',
    marginTop: 2,
  },
  followButton: {
    backgroundColor: '#6366F1',
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  followButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
  },
  traderPerformance: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    marginBottom: 14,
    paddingVertical: 12,
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.12)',
  },
  traderStat: {
    alignItems: 'center',
    flex: 1,
  },
  traderStatDivider: {
    width: 1,
    height: 28,
    backgroundColor: 'rgba(148,163,184,0.20)',
  },
  traderStatLabel: {
    fontSize: 10,
    color: '#94A3B8',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
    marginBottom: 4,
  },
  traderStatValue: {
    fontSize: 16,
    fontWeight: '900',
    color: '#0F172A',
  },
  recentTrades: {
    marginTop: 4,
  },
  recentTradesTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    marginBottom: 8,
  },
  recentTrade: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  recentTradeSymbol: {
    fontSize: 14,
    color: '#0F172A',
    fontWeight: '700',
    flex: 1,
  },
  recentTradeSidePill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    marginHorizontal: 8,
  },
  recentTradeSide: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  recentTradePnl: {
    fontSize: 14,
    fontWeight: '800',
    minWidth: 70,
    textAlign: 'right',
  },

  /* ============ SIGNALS ============ */
  signalsContainer: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  comingSoon: {
    fontSize: 16,
    color: '#94A3B8',
    fontStyle: 'italic',
  },
  signalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.15)',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 2,
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  signalSymbol: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  signalSymbolText: {
    fontSize: 18,
    fontWeight: '900',
    color: '#0F172A',
    letterSpacing: -0.2,
  },
  signalType: {
    fontSize: 11,
    fontWeight: '800',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    overflow: 'hidden',
    letterSpacing: 0.3,
  },
  longSignal: {
    backgroundColor: 'rgba(16,185,129,0.15)',
    color: '#10B981',
  },
  shortSignal: {
    backgroundColor: 'rgba(239,68,68,0.15)',
    color: '#EF4444',
  },
  signalScore: {
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    backgroundColor: 'rgba(16,185,129,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.15)',
  },
  signalScoreText: {
    fontSize: 16,
    fontWeight: '900',
    color: '#10B981',
  },
  signalScoreLabel: {
    fontSize: 9,
    color: '#10B981',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  signalPrices: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    paddingVertical: 10,
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    paddingHorizontal: 8,
  },
  priceItem: {
    alignItems: 'center',
    flex: 1,
  },
  priceLabel: {
    fontSize: 10,
    color: '#94A3B8',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
    marginBottom: 4,
  },
  priceValue: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
  },
  signalReasoning: {
    fontSize: 14,
    color: '#334155',
    marginBottom: 12,
    lineHeight: 20,
    fontWeight: '500',
  },
  hftBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(16,185,129,0.12)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
    alignSelf: 'flex-start',
    marginBottom: 12,
    gap: 4,
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.20)',
  },
  hftText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#10B981',
  },
  signalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: 'rgba(148,163,184,0.12)',
  },
  signalTimeframe: {
    fontSize: 12,
    color: '#94A3B8',
    fontWeight: '600',
  },
  signalActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  likeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F8FAFC',
    gap: 4,
  },
  likeCount: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '700',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    fontSize: 16,
    color: '#94A3B8',
    fontWeight: '600',
  },
});

export default SocialTrading;