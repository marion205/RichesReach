import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Image,
  StyleSheet,
  Dimensions,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import logger from '../../../utils/logger';

const { width, height } = Dimensions.get('window');

interface SocialPost {
  id: string;
  user: {
    username: string;
    avatar: string;
    isBipoc: boolean;
  };
  content: string;
  postType: 'meme_launch' | 'raid_join' | 'trade_share' | 'yield_farm' | 'educational' | 'general';
  memeCoin?: {
    name: string;
    symbol: string;
    price: number;
    change: number;
  };
  raid?: {
    name: string;
    target: number;
    current: number;
    participants: number;
  };
  imageUrl?: string;
  videoUrl?: string;
  likes: number;
  shares: number;
  comments: number;
  views: number;
  isSpotlight: boolean;
  createdAt: string;
}

interface SocialFeedProps {
  onPostPress?: (post: SocialPost) => void;
  onUserPress?: (user: SocialPost['user']) => void;
  onMemePress?: (meme: SocialPost['memeCoin']) => void;
  onRaidPress?: (raid: SocialPost['raid']) => void;
}

const SocialFeed: React.FC<SocialFeedProps> = ({
  onPostPress,
  onUserPress,
  onMemePress,
  onRaidPress,
}) => {
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  // Mock data for demonstration
  const mockPosts: SocialPost[] = [
    {
      id: '1',
      user: {
        username: '@BIPOCTrader',
        avatar: 'https://via.placeholder.com/50',
        isBipoc: true,
      },
      content: 'Just launched $COMMUNITY! Moon mission for BIPOC wealth! 🚀',
      postType: 'meme_launch',
      memeCoin: {
        name: 'CommunityCoin',
        symbol: 'COMMUNITY',
        price: 0.0001,
        change: 12.5,
      },
      imageUrl: 'https://via.placeholder.com/300x200',
      likes: 45,
      shares: 12,
      comments: 8,
      views: 234,
      isSpotlight: true,
      createdAt: '2m ago',
    },
    {
      id: '2',
      user: {
        username: '@YieldFarmer',
        avatar: 'https://via.placeholder.com/50',
        isBipoc: false,
      },
      content: 'Staking $ETH in AAVE pool for 8.5% APY! Auto-compound enabled 💰',
      postType: 'yield_farm',
      likes: 23,
      shares: 5,
      comments: 3,
      views: 156,
      isSpotlight: false,
      createdAt: '5m ago',
    },
    {
      id: '3',
      user: {
        username: '@RaidLeader',
        avatar: 'https://via.placeholder.com/50',
        isBipoc: true,
      },
      content: 'Starting a raid on $FROG! Target: $10k. Join the community pump! 🐸',
      postType: 'raid_join',
      raid: {
        name: 'Frog Raid',
        target: 10000,
        current: 3500,
        participants: 23,
      },
      likes: 67,
      shares: 18,
      comments: 12,
      views: 445,
      isSpotlight: true,
      createdAt: '8m ago',
    },
  ];

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setPosts(mockPosts);
    } catch (error) {
      logger.error('Error loading posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPosts();
    setRefreshing(false);
  };

  const handlePostPress = (post: SocialPost) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onPostPress?.(post);
  };

  const handleUserPress = (user: SocialPost['user']) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onUserPress?.(user);
  };

  const handleMemePress = (meme: SocialPost['memeCoin']) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onMemePress?.(meme);
  };

  const handleRaidPress = (raid: SocialPost['raid']) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onRaidPress?.(raid);
  };

  const renderPost = (post: SocialPost) => (
    <TouchableOpacity
      key={post.id}
      style={styles.postCard}
      onPress={() => handlePostPress(post)}
      activeOpacity={0.8}
    >
      {/* User Header */}
      <View style={styles.postHeader}>
        <TouchableOpacity
          style={styles.userInfo}
          onPress={() => handleUserPress(post.user)}
        >
          <Image source={{ uri: post.user.avatar }} style={styles.avatar} />
          <View style={styles.userDetails}>
            <Text style={styles.username}>{post.user.username}</Text>
            <Text style={styles.timestamp}>{post.createdAt}</Text>
          </View>
        </TouchableOpacity>
        
        {post.isSpotlight && (
          <View style={styles.spotlightBadge}>
            <Text style={styles.spotlightText}>🌟 BIPOC Spotlight</Text>
          </View>
        )}
      </View>

      {/* Post Content */}
      <Text style={styles.postContent}>{post.content}</Text>

      {/* Meme Coin Info */}
      {post.memeCoin && (
        <TouchableOpacity
          style={styles.memeInfo}
          onPress={() => handleMemePress(post.memeCoin!)}
        >
          <LinearGradient
            colors={['#FF6B6B', '#FF8E8E']}
            style={styles.memeGradient}
          >
            <Text style={styles.memeSymbol}>${post.memeCoin.symbol}</Text>
            <Text style={styles.memePrice}>${post.memeCoin.price.toFixed(4)}</Text>
            <Text style={[
              styles.memeChange,
              { color: post.memeCoin.change >= 0 ? '#4ECDC4' : '#FF6B6B' }
            ]}>
              {post.memeCoin.change >= 0 ? '+' : ''}{post.memeCoin.change}%
            </Text>
          </LinearGradient>
        </TouchableOpacity>
      )}

      {/* Raid Info */}
      {post.raid && (
        <TouchableOpacity
          style={styles.raidInfo}
          onPress={() => handleRaidPress(post.raid!)}
        >
          <LinearGradient
            colors={['#4ECDC4', '#44A08D']}
            style={styles.raidGradient}
          >
            <Text style={styles.raidName}>{post.raid.name}</Text>
            <View style={styles.raidProgress}>
              <View style={styles.raidProgressBar}>
                <View style={[
                  styles.raidProgressFill,
                  { width: `${(post.raid.current / post.raid.target) * 100}%` }
                ]} />
              </View>
              <Text style={styles.raidProgressText}>
                ${post.raid.current.toLocaleString()} / ${post.raid.target.toLocaleString()}
              </Text>
            </View>
            <Text style={styles.raidParticipants}>
              {post.raid.participants} participants
            </Text>
          </LinearGradient>
        </TouchableOpacity>
      )}

      {/* Post Image */}
      {post.imageUrl && (
        <Image source={{ uri: post.imageUrl }} style={styles.postImage} />
      )}

      {/* Engagement Stats */}
      <View style={styles.engagementStats}>
        <Text style={styles.statsText}>
          👀 {post.views} views
        </Text>
        <Text style={styles.statsText}>
          ❤️ {post.likes} likes
        </Text>
        <Text style={styles.statsText}>
          🔄 {post.shares} shares
        </Text>
        <Text style={styles.statsText}>
          💬 {post.comments} comments
        </Text>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionButtons}>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>❤️ Like</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>🔄 Share</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>💬 Comment</Text>
        </TouchableOpacity>
        {post.memeCoin && (
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryAction]}
            onPress={() => handleMemePress(post.memeCoin!)}
          >
            <Text style={styles.primaryActionText}>🚀 Trade</Text>
          </TouchableOpacity>
        )}
        {post.raid && (
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryAction]}
            onPress={() => handleRaidPress(post.raid!)}
          >
            <Text style={styles.primaryActionText}>⚔️ Join Raid</Text>
          </TouchableOpacity>
        )}
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading social feed...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.feedHeader}>
        <Text style={styles.feedTitle}>🔥 Social Trading Feed</Text>
        <Text style={styles.feedSubtitle}>Real-time meme launches & raids</Text>
      </View>

      {posts.map(renderPost)}

      <View style={styles.feedFooter}>
        <Text style={styles.footerText}>
          Pull to refresh for new posts! 🔄
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
  feedHeader: {
    padding: 20,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  feedTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
  },
  feedSubtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginTop: 4,
  },
  postCard: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  postHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
  },
  userDetails: {
    flex: 1,
  },
  username: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  timestamp: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  spotlightBadge: {
    backgroundColor: '#FFD700',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  spotlightText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
  },
  postContent: {
    fontSize: 16,
    color: '#333',
    lineHeight: 22,
    marginBottom: 12,
  },
  memeInfo: {
    marginBottom: 12,
  },
  memeGradient: {
    padding: 12,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  memeSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFF',
  },
  memePrice: {
    fontSize: 16,
    color: '#FFF',
  },
  memeChange: {
    fontSize: 16,
    fontWeight: '600',
  },
  raidInfo: {
    marginBottom: 12,
  },
  raidGradient: {
    padding: 12,
    borderRadius: 12,
  },
  raidName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFF',
    marginBottom: 8,
  },
  raidProgress: {
    marginBottom: 8,
  },
  raidProgressBar: {
    height: 8,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  raidProgressFill: {
    height: '100%',
    backgroundColor: '#FFF',
    borderRadius: 4,
  },
  raidProgressText: {
    fontSize: 12,
    color: '#FFF',
    textAlign: 'center',
  },
  raidParticipants: {
    fontSize: 12,
    color: '#FFF',
    textAlign: 'center',
  },
  postImage: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    marginBottom: 12,
  },
  engagementStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
  },
  statsText: {
    fontSize: 12,
    color: '#666',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  actionButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#F0F0F0',
  },
  actionButtonText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  primaryAction: {
    backgroundColor: '#4ECDC4',
  },
  primaryActionText: {
    color: '#FFF',
    fontWeight: '600',
  },
  feedFooter: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
});

export default SocialFeed;