import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  Alert,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import MockUserService, { MockUser } from '../../user/services/MockUserService';

interface UserPortfoliosScreenProps {
  userId: string;
  onNavigate: (screen: string, params?: any) => void;
}

const UserPortfoliosScreen: React.FC<UserPortfoliosScreenProps> = ({ userId, onNavigate }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [user, setUser] = useState<MockUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mockUserService = MockUserService.getInstance();

  // Load user profile from mock service
  const loadUserProfile = () => {
    setLoading(true);
    setError(null);
    try {
      const userProfile = mockUserService.getUserById(userId);
      if (userProfile) {
        setUser(userProfile);
      } else {
        setError('User not found');
      }
    } catch (err) {
      setError('Failed to load user profile');
      console.error('Error loading user profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      loadUserProfile();
    } catch (error) {
      console.error('Error refreshing profile:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Load user profile when component mounts
  useEffect(() => {
    loadUserProfile();
  }, [userId]);

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading portfolios...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !user) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="pie-chart" size={48} color="#FF3B30" />
          <Text style={styles.errorTitle}>Portfolios Not Found</Text>
          <Text style={styles.errorText}>
            Unable to load this user's portfolios.
          </Text>
          <TouchableOpacity
            style={styles.backButtonAction}
            onPress={() => onNavigate('social')}
          >
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const publicPortfolios = user.portfolios?.filter(p => p.isPublic) || [];

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => onNavigate('social')}
        >
          <Icon name="arrow-left" size={24} color="#007AFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{user.name}'s Portfolios</Text>
        <View style={styles.headerRight} />
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* User Info */}
        <View style={styles.userInfo}>
          <View style={styles.userAvatar}>
            <Icon name="user" size={24} color="#007AFF" />
          </View>
          <View style={styles.userDetails}>
            <Text style={styles.userName}>{user.name}</Text>
            <Text style={styles.userLevel}>{user.experienceLevel} Investor</Text>
            <Text style={styles.userStats}>
              {user.followersCount} followers • {user.followingCount} following
            </Text>
          </View>
        </View>

        {/* Portfolios Section */}
        <View style={styles.portfoliosSection}>
          <View style={styles.sectionHeader}>
            <Icon name="pie-chart" size={20} color="#34C759" />
            <Text style={styles.sectionTitle}>Public Portfolios</Text>
          </View>

          {publicPortfolios.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="pie-chart" size={48} color="#8E8E93" />
              <Text style={styles.emptyTitle}>No Public Portfolios</Text>
              <Text style={styles.emptyText}>
                This user hasn't shared any public portfolios yet.
              </Text>
            </View>
          ) : (
            <View style={styles.portfoliosList}>
              {publicPortfolios.map((portfolio) => (
                <TouchableOpacity
                  key={portfolio.id}
                  style={styles.portfolioCard}
                  onPress={() => {
                    // Navigate to portfolio detail or show more info
                    Alert.alert(
                      portfolio.name,
                      `Total Value: $${portfolio.totalValue ? portfolio.totalValue.toLocaleString() : '0.00'}\nReturn: ${portfolio.totalReturnPercent >= 0 ? '+' : ''}${portfolio.totalReturnPercent.toFixed(2)}%`,
                      [{ text: 'OK' }]
                    );
                  }}
                >
                  <View style={styles.portfolioHeader}>
                    <Text style={styles.portfolioName}>{portfolio.name}</Text>
                    <View style={[
                      styles.portfolioReturn,
                      { backgroundColor: portfolio.totalReturnPercent >= 0 ? '#E8F5E8' : '#FFE8E8' }
                    ]}>
                      <Text style={[
                        styles.portfolioReturnText,
                        { color: portfolio.totalReturnPercent >= 0 ? '#34C759' : '#FF3B30' }
                      ]}>
                        {portfolio.totalReturnPercent >= 0 ? '+' : ''}{portfolio.totalReturnPercent.toFixed(1)}%
                      </Text>
                    </View>
                  </View>
                  
                  <View style={styles.portfolioStats}>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>${portfolio.totalValue ? portfolio.totalValue.toLocaleString() : '0.00'}</Text>
                      <Text style={styles.statLabel}>Total Value</Text>
                    </View>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>${portfolio.totalReturn ? portfolio.totalReturn.toLocaleString() : '0.00'}</Text>
                      <Text style={styles.statLabel}>Total Return</Text>
                    </View>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>{portfolio.holdings?.length || 0}</Text>
                      <Text style={styles.statLabel}>Holdings</Text>
                    </View>
                  </View>

                  {portfolio.description && (
                    <Text style={styles.portfolioDescription} numberOfLines={2}>
                      {portfolio.description}
                    </Text>
                  )}

                  <View style={styles.portfolioFooter}>
                    <View style={styles.portfolioMeta}>
                      <Icon name="calendar" size={14} color="#8E8E93" />
                      <Text style={styles.portfolioDate}>
                        Updated {new Date(portfolio.lastUpdated).toLocaleDateString()}
                      </Text>
                    </View>
                    <Icon name="chevron-right" size={16} color="#8E8E93" />
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => onNavigate('user-profile', { userId: user.id })}
          >
            <Icon name="user" size={16} color="#007AFF" />
            <Text style={styles.actionButtonText}>View Profile</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.actionButton, styles.followButton]}
            onPress={() => {
              // Handle follow/unfollow
              Alert.alert('Follow', `Follow ${user.name}?`);
            }}
          >
            <Icon name="user-plus" size={16} color="#34C759" />
            <Text style={[styles.actionButtonText, styles.followButtonText]}>Follow</Text>
          </TouchableOpacity>
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
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
  },
  headerRight: {
    width: 40,
  },
  content: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FF3B30',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 24,
  },
  backButtonAction: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  backButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    marginBottom: 8,
  },
  userAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#E5E5EA',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 4,
  },
  userLevel: {
    fontSize: 14,
    color: '#8E8E93',
    textTransform: 'capitalize',
    marginBottom: 2,
  },
  userStats: {
    fontSize: 12,
    color: '#8E8E93',
  },
  portfoliosSection: {
    backgroundColor: '#FFFFFF',
    marginBottom: 8,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginLeft: 8,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#8E8E93',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  portfoliosList: {
    padding: 16,
  },
  portfolioCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
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
    color: '#000000',
    flex: 1,
  },
  portfolioReturn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  portfolioReturnText: {
    fontSize: 14,
    fontWeight: '600',
  },
  portfolioStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
  },
  portfolioDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 18,
    marginBottom: 12,
  },
  portfolioFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  portfolioMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  portfolioDate: {
    fontSize: 12,
    color: '#8E8E93',
    marginLeft: 4,
  },
  actionButtons: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    backgroundColor: '#FFFFFF',
  },
  followButton: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    marginLeft: 6,
  },
  followButtonText: {
    color: '#FFFFFF',
  },
});

export default UserPortfoliosScreen;
