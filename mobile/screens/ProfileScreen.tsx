import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
  Image,
  SafeAreaView,
  Dimensions,
} from 'react-native';
import { gql, useQuery, useMutation, useApolloClient } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { GET_MY_PORTFOLIOS } from '../graphql/portfolioQueries';

const GET_ME = gql`
  query GetMe {
    me {
      id
      name
      email
      profilePic
      followersCount
      followingCount
      isFollowingUser
      isFollowedByUser
      hasPremiumAccess
      subscriptionTier
    }
  }
`;

const GET_USER_PORTFOLIO = gql`
  query GetUserPortfolio($userId: ID!) {
    portfolios(userId: $userId) {
      id
      name
      description
      isPublic
      createdAt
      positions {
        id
        stock {
          symbol
          companyName
        }
        shares
        entryPrice
        currentPrice
        positionType
        currentValue
      }
    }
  }
`;

const GET_MY_WATCHLIST = gql`
  query GetMyWatchlist {
    myWatchlist {
      id
      stock {
        symbol
        companyName
        currentPrice
      }
      notes
      targetPrice
      addedAt
    }
  }
`;

const GET_PORTFOLIO_VALUE = gql`
  query GetPortfolioValue {
    portfolioValue
  }
`;

const TOGGLE_FOLLOW = gql`
  mutation ToggleFollow($userId: ID!) {
    toggleFollow(userId: $userId) {
      user {
        id
        followers_count
        following_count
        is_following_user
        is_followed_by_user
      }
      following
    }
  }
`;

type User = {
  id: string;
  name: string;
  email: string;
  profilePic?: string;
  followersCount: number;
  followingCount: number;
  isFollowingUser: boolean;
  isFollowedByUser: boolean;
};

interface ProfileScreenProps {
  navigateTo?: (screen: string) => void;
  onLogout?: () => void;
}

const { width } = Dimensions.get('window');

const ProfileScreen: React.FC<ProfileScreenProps> = ({ navigateTo, onLogout }) => {
  const { data: meData, loading: meLoading, error: meError } = useQuery(GET_ME);
  const { data: portfoliosData, loading: portfoliosLoading, refetch: refetchPortfolios } = useQuery(GET_MY_PORTFOLIOS, {
    notifyOnNetworkStatusChange: true,
    fetchPolicy: 'cache-and-network'
  });
  const { data: watchlistData, loading: watchlistLoading } = useQuery(GET_MY_WATCHLIST, {
    skip: !meData?.me?.id,
  });
  const [toggleFollow] = useMutation(TOGGLE_FOLLOW);
  const [refreshing, setRefreshing] = useState(false);
  const client = useApolloClient();

  const user: User | null = meData?.me ? {
    id: meData.me.id,
    name: meData.me.name,
    email: meData.me.email,
    profilePic: meData.me.profilePic,
    followersCount: meData.me.followersCount || 0,
    followingCount: meData.me.followingCount || 0,
    isFollowingUser: meData.me.isFollowingUser || false,
    isFollowedByUser: meData.me.isFollowedByUser || false
  } : null;

  const handleToggleFollow = async () => {
    if (!user) return;
    
    try {
      await toggleFollow({
        variables: { userId: user.id },
      });
      await client.resetStore();
    } catch (error) {
      // Failed to toggle follow
      Alert.alert('Error', 'Failed to follow/unfollow user. Please try again.');
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      // Refetch user, portfolio, and watchlist data
      await Promise.all([
        client.refetchQueries({
          include: [GET_ME, GET_MY_PORTFOLIOS, GET_MY_WATCHLIST]
        })
      ]);
    } catch (error) {
      // Failed to refresh
    } finally {
      setRefreshing(false);
    }
  };

  // Get real portfolio value from saved portfolio data
  const portfolioValue = portfoliosData?.myPortfolios?.totalValue || 0;

  const investmentGoals = portfoliosData?.myPortfolios?.totalPortfolios || 0;

  const handleLogout = async () => {
    try {
      await client.clearStore();
      await AsyncStorage.removeItem('token');
      if (onLogout) {
        onLogout();
      }
    } catch (error) {
      // Logout error
      Alert.alert('Error', 'Failed to logout properly. Please try again.');
    }
  };

  if (meLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Icon name="refresh-cw" size={32} color="#34C759" />
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (meError) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#FF3B30" />
          <Text style={styles.errorTitle}>Error Loading Profile</Text>
          <Text style={styles.errorText}>
            Unable to load your profile data. Please try again.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="user-x" size={48} color="#FF3B30" />
          <Text style={styles.errorTitle}>Profile Not Found</Text>
          <Text style={styles.errorText}>
            Unable to find your profile information.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <TouchableOpacity onPress={() => navigateTo?.('home')}>
            <Icon name="arrow-left" size={24} color="#333" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Profile</Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity 
            style={styles.refreshButton}
            onPress={handleRefresh}
            disabled={refreshing}
          >
            <Icon 
              name="refresh-cw" 
              size={16} 
              color={refreshing ? "#C7C7CC" : "#34C759"} 
              style={refreshing ? styles.spinningIcon : {}} 
            />
          </TouchableOpacity>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
            <Icon name="power" size={16} color="#ff4757" />
            <Text style={styles.logoutButtonText}>Logout</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <TouchableOpacity 
            style={styles.profileImageContainer}
            onPress={() => navigateTo?.('stock')}
            activeOpacity={0.8}
          >
            {user.profilePic ? (
              <Image source={{ uri: user.profilePic }} style={styles.profileImage} />
            ) : (
              <View style={styles.profileImagePlaceholder}>
                <Text style={styles.profileImageText}>{user.name.charAt(0).toUpperCase()}</Text>
              </View>
            )}
            <View style={styles.editProfileButton}>
              <Icon name="edit" size={16} color="#fff" />
            </View>
          </TouchableOpacity>
          
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{user.name}</Text>
            <Text style={styles.profileEmail}>{user.email}</Text>
            <Text style={styles.profileJoinDate}>Member since {new Date().getFullYear()}</Text>
            
            <View style={styles.statsContainer}>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{user.followersCount}</Text>
                <Text style={styles.statLabel}>Followers</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{user.followingCount}</Text>
                <Text style={styles.statLabel}>Following</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Profile Actions */}
        <View style={styles.profileActions}>
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => navigateTo?.('stock')}
          >
            <Icon name="edit" size={20} color="#34C759" />
            <Text style={styles.actionButtonText}>Manage Stocks</Text>
            <Icon name="chevron-right" size={16} color="#C7C7CC" style={styles.actionArrow} />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => navigateTo?.('home')}
          >
            <Icon name="settings" size={20} color="#007AFF" />
            <Text style={styles.actionButtonText}>News Preferences</Text>
            <Icon name="chevron-right" size={16} color="#C7C7CC" style={styles.actionArrow} />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => navigateTo?.('social')}
          >
            <Icon name="help-circle" size={20} color="#FF9500" />
            <Text style={styles.actionButtonText}>Discussion Hub</Text>
            <Icon name="chevron-right" size={16} color="#C7C7CC" style={styles.actionArrow} />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => navigateTo?.('onboarding')}
          >
            <Icon name="user-plus" size={20} color="#AF52DE" />
            <Text style={styles.actionButtonText}>Update Investment Profile</Text>
            <Icon name="chevron-right" size={16} color="#C7C7CC" style={styles.actionArrow} />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.actionButton, styles.premiumButton]}
            onPress={() => navigateTo?.('premium-analytics')}
          >
            <Icon name="star" size={20} color="#FFD700" />
            <Text style={[styles.actionButtonText, styles.premiumButtonText]}>Premium Analytics</Text>
            <Icon name="chevron-right" size={16} color="#FFD700" style={styles.actionArrow} />
          </TouchableOpacity>
        </View>

        {/* Profile Stats */}
        <View style={styles.profileStats}>
          <TouchableOpacity 
            style={styles.statCard}
            onPress={() => navigateTo?.('portfolio-management')}
            disabled={portfoliosLoading}
          >
            <Icon name="trending-up" size={24} color="#34C759" />
            <Text style={styles.statCardTitle}>Portfolio Value</Text>
            {portfoliosLoading || watchlistLoading ? (
              <View style={styles.loadingValue}>
                <Icon name="refresh-cw" size={16} color="#C7C7CC" style={styles.spinningIcon} />
                <Text style={styles.loadingValueText}>Loading...</Text>
              </View>
            ) : (
              <Text style={styles.statCardValue}>
                ${portfolioValue > 0 ? portfolioValue.toLocaleString() : '0.00'}
              </Text>
            )}
            <Text style={styles.statCardSubtitle}>
              {portfolioValue > 0 ? 'Based on your saved portfolio' : 'Add stocks to your portfolio to see value'}
            </Text>
            <View style={styles.statCardArrow}>
              <Icon name="chevron-right" size={16} color="#C7C7CC" />
            </View>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.statCard}
            onPress={() => navigateTo?.('portfolio-management')}
            disabled={portfoliosLoading}
          >
            <Icon name="crosshair" size={24} color="#007AFF" />
            <Text style={styles.statCardTitle}>Portfolios</Text>
            {portfoliosLoading ? (
              <View style={styles.loadingValue}>
                <Icon name="refresh-cw" size={16} color="#C7C7CC" style={styles.spinningIcon} />
                <Text style={styles.loadingValueText}>Loading...</Text>
              </View>
            ) : (
              <Text style={styles.statCardValue}>{investmentGoals}</Text>
            )}
            <Text style={styles.statCardSubtitle}>
              {investmentGoals > 0 ? 'Active portfolios' : 'Create your first portfolio'}
            </Text>
            <View style={styles.statCardArrow}>
              <Icon name="chevron-right" size={16} color="#C7C7CC" />
            </View>
          </TouchableOpacity>
        </View>

        {/* My Portfolios */}
        <View style={styles.portfolioHoldings}>
          <Text style={styles.sectionTitle}>My Portfolios</Text>
          {portfoliosLoading ? (
            <View style={styles.loadingContainer}>
              <Icon name="refresh-cw" size={24} color="#C7C7CC" style={styles.spinningIcon} />
              <Text style={styles.loadingText}>Loading portfolios...</Text>
            </View>
          ) : portfoliosData?.myPortfolios?.portfolios && portfoliosData.myPortfolios.portfolios.length > 0 ? (
            portfoliosData.myPortfolios.portfolios.map((portfolio: any) => (
              <View key={portfolio.name} style={styles.portfolioCard}>
                <View style={styles.portfolioHeader}>
                  <Text style={styles.portfolioName}>{portfolio.name}</Text>
                  <Text style={styles.portfolioValue}>
                    ${portfolio.totalValue.toLocaleString()}
                  </Text>
                </View>
                <View style={styles.portfolioStats}>
                  <Text style={styles.portfolioStatsText}>
                    {portfolio.holdingsCount} holdings
                  </Text>
                </View>
                {portfolio.holdings && portfolio.holdings.length > 0 && (
                  <View style={styles.holdingsList}>
                    {portfolio.holdings.slice(0, 3).map((holding: any) => (
                      <View key={holding.id} style={styles.holdingItem}>
                        <View style={styles.holdingInfo}>
                          <Text style={styles.stockSymbol}>{holding.stock.symbol}</Text>
                          <Text style={styles.stockName}>{holding.stock.companyName}</Text>
                        </View>
                        <View style={styles.holdingDetails}>
                          <Text style={styles.sharesText}>{holding.shares} shares</Text>
                          <Text style={styles.priceText}>
                            ${holding.totalValue ? holding.totalValue.toLocaleString() : '0.00'}
                          </Text>
                        </View>
                      </View>
                    ))}
                    {portfolio.holdings.length > 3 && (
                      <Text style={styles.moreHoldingsText}>
                        +{portfolio.holdings.length - 3} more holdings
                      </Text>
                    )}
                  </View>
                )}
              </View>
            ))
          ) : (
            <View style={styles.emptyPortfolioContainer}>
              <Icon name="briefcase" size={48} color="#C7C7CC" />
              <Text style={styles.emptyPortfolioTitle}>No Portfolios Yet</Text>
              <Text style={styles.emptyPortfolioSubtitle}>
                Create your first portfolio to start tracking your investments
              </Text>
              <TouchableOpacity 
                style={styles.createPortfolioButton}
                onPress={() => navigateTo?.('ai-portfolio')}
              >
                <Icon name="plus" size={16} color="#fff" />
                <Text style={styles.createPortfolioButtonText}>Create Portfolio</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Watchlist Stocks */}
        <View style={styles.portfolioHoldings}>
          <Text style={styles.sectionTitle}>Watchlist Stocks</Text>
          {watchlistLoading ? (
            <View style={styles.loadingContainer}>
              <Icon name="refresh-cw" size={24} color="#C7C7CC" style={styles.spinningIcon} />
              <Text style={styles.loadingText}>Loading watchlist...</Text>
            </View>
          ) : watchlistData?.myWatchlist && watchlistData.myWatchlist.length > 0 ? (
            watchlistData.myWatchlist.map((watchlistItem: any) => (
              <View key={watchlistItem.id} style={styles.portfolioCard}>
                <View style={styles.portfolioHeader}>
                  <Text style={styles.stockSymbol}>{watchlistItem.stock.symbol}</Text>
                  <Text style={styles.portfolioDate}>
                    Added {new Date(watchlistItem.addedAt).toLocaleDateString()}
                  </Text>
                </View>
                <View style={styles.holdingItem}>
                  <View style={styles.holdingInfo}>
                    <Text style={styles.stockName}>{watchlistItem.stock.companyName}</Text>
                    <Text style={styles.stockNotes}>
                      {watchlistItem.notes || 'No notes added'}
                    </Text>
                  </View>
                  <View style={styles.holdingDetails}>
                    <Text style={styles.priceText}>${watchlistItem.stock.currentPrice}</Text>
                    {watchlistItem.targetPrice && (
                      <Text style={styles.targetPriceText}>
                        Target: ${watchlistItem.targetPrice}
                      </Text>
                    )}
                  </View>
                </View>
              </View>
            ))
          ) : (
            <View style={styles.emptyPortfolioContainer}>
              <Icon name="eye" size={48} color="#C7C7CC" />
              <Text style={styles.emptyPortfolioTitle}>No Watchlist Stocks</Text>
              <Text style={styles.emptyPortfolioSubtitle}>
                Add stocks to your watchlist to start tracking their performance
              </Text>
              <TouchableOpacity 
                style={styles.createPortfolioButton}
                onPress={() => navigateTo?.('stock')}
              >
                <Icon name="plus" size={16} color="#fff" />
                <Text style={styles.createPortfolioButtonText}>Add Stocks</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          
          <View style={styles.quickActionsGrid}>
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigateTo?.('stock')}
            >
              <Icon name="plus" size={24} color="#34C759" />
              <Text style={styles.quickActionText}>Add Stock</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigateTo?.('portfolio')}
            >
              <Icon name="bar-chart-2" size={24} color="#007AFF" />
              <Text style={styles.quickActionText}>View Portfolio</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigateTo?.('ai-portfolio')}
            >
              <Icon name="cpu" size={24} color="#FF9500" />
              <Text style={styles.quickActionText}>AI Analysis</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.quickActionButton}
              onPress={() => navigateTo?.('home')}
            >
              <Icon name="bookmark" size={24} color="#5856D6" />
              <Text style={styles.quickActionText}>News Feed</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  refreshButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#F2F2F7',
  },
  spinningIcon: {
    transform: [{ rotate: '360deg' }],
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: '#FFF5F5',
  },
  logoutButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ff4757',
  },
  content: {
    flex: 1,
  },
  profileHeader: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 24,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  profileImageContainer: {
    position: 'relative',
    marginBottom: 16,
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  profileImagePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#34C759',
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileImageText: {
    fontSize: 36,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  editProfileButton: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: '#34C759',
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  profileInfo: {
    alignItems: 'center',
  },
  profileName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  profileEmail: {
    fontSize: 16,
    color: '#8E8E93',
    marginBottom: 8,
  },
  profileJoinDate: {
    fontSize: 14,
    color: '#C7C7CC',
    marginBottom: 20,
  },
  statsContainer: {
    flexDirection: 'row',
    gap: 32,
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  statLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 4,
  },
  profileActions: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
  },
  actionButtonText: {
    fontSize: 16,
    color: '#1C1C1E',
    fontWeight: '500',
    flex: 1,
  },
  actionArrow: {
    marginLeft: 'auto',
  },
  profileStats: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  statCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
  },
  statCardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 8,
    marginBottom: 4,
  },
  statCardValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#34C759',
    marginBottom: 4,
  },
  statCardSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  statCardArrow: {
    position: 'absolute',
    top: 16,
    right: 16,
  },
  loadingValue: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  loadingValueText: {
    fontSize: 16,
    color: '#C7C7CC',
    fontWeight: '500',
  },
  quickActions: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  quickActionButton: {
    width: (width - 64) / 2,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  quickActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 8,
    textAlign: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  portfolioHoldings: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  portfolioCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  portfolioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  portfolioName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  portfolioDate: {
    fontSize: 12,
    color: '#8E8E93',
  },
  holdingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
  },
  holdingInfo: {
    flex: 1,
  },
  stockSymbol: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  stockName: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 2,
  },
  holdingDetails: {
    alignItems: 'flex-end',
  },
  sharesText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  priceText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#34C759',
    marginTop: 2,
  },
  noHoldingsText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  emptyPortfolioContainer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  emptyPortfolioTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyPortfolioSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  createPortfolioButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#34C759',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
  },
  createPortfolioButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  stockNotes: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 2,
    fontStyle: 'italic',
  },
  targetPriceText: {
    fontSize: 12,
    color: '#007AFF',
    marginTop: 2,
    fontWeight: '500',
  },
  portfolioValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#34C759',
  },
  portfolioStats: {
    marginTop: 8,
  },
  portfolioStatsText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  holdingsList: {
    marginTop: 12,
  },
  moreHoldingsText: {
    fontSize: 12,
    color: '#8E8E93',
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  premiumButton: {
    backgroundColor: '#FFF8E1',
    borderWidth: 1,
    borderColor: '#FFD700',
  },
  premiumButtonText: {
    color: '#B8860B',
    fontWeight: '600',
  },
});

export default ProfileScreen;
