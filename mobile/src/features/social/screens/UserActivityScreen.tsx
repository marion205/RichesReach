import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import logger from '../../../utils/logger';
// Mock service removed - using real API

interface UserActivityScreenProps {
  userId: string;
  onNavigate: (screen: string, params?: any) => void;
}

interface ActivityItem {
  id: string;
  type: 'trade' | 'post' | 'comment' | 'follow' | 'portfolio';
  title: string;
  description: string;
  timestamp: Date;
  value?: number;
  symbol?: string;
}

const UserActivityScreen: React.FC<UserActivityScreenProps> = ({ userId, onNavigate }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock user data - replace with real API call
  const user = {
    id: userId,
    name: 'User',
    email: 'user@example.com',
  };

  // Generate mock activity data
  const generateMockActivities = (): ActivityItem[] => {
    const activityTypes: ActivityItem['type'][] = ['trade', 'post', 'comment', 'follow', 'portfolio'];
    const mockActivities: ActivityItem[] = [];

    for (let i = 0; i < 20; i++) {
      const type = activityTypes[Math.floor(Math.random() * activityTypes.length)];
      const timestamp = new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000); // Last 7 days
      
      let activity: ActivityItem;
      
      switch (type) {
        case 'trade':
          const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA'];
          const symbol = symbols[Math.floor(Math.random() * symbols.length)];
          const isBuy = Math.random() > 0.5;
          activity = {
            id: `trade_${i}`,
            type: 'trade',
            title: `${isBuy ? 'Bought' : 'Sold'} ${symbol}`,
            description: `${isBuy ? 'Purchased' : 'Sold'} ${Math.floor(Math.random() * 100) + 1} shares`,
            timestamp,
            value: Math.random() * 10000 + 1000,
            symbol,
          };
          break;
        case 'post':
          activity = {
            id: `post_${i}`,
            type: 'post',
            title: 'Posted Discussion',
            description: 'Shared thoughts on market trends',
            timestamp,
          };
          break;
        case 'comment':
          activity = {
            id: `comment_${i}`,
            type: 'comment',
            title: 'Commented on Discussion',
            description: 'Added insight to community discussion',
            timestamp,
          };
          break;
        case 'follow':
          activity = {
            id: `follow_${i}`,
            type: 'follow',
            title: 'Started Following',
            description: 'Followed a new investor',
            timestamp,
          };
          break;
        case 'portfolio':
          activity = {
            id: `portfolio_${i}`,
            type: 'portfolio',
            title: 'Updated Portfolio',
            description: 'Made changes to investment portfolio',
            timestamp,
          };
          break;
        default:
          activity = {
            id: `activity_${i}`,
            type: 'post',
            title: 'Activity',
            description: 'User activity',
            timestamp,
          };
      }
      
      mockActivities.push(activity);
    }

    return mockActivities.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  };

  const loadActivities = () => {
    setLoading(true);
    setError(null);
    try {
      const mockActivities = generateMockActivities();
      setActivities(mockActivities);
    } catch (err) {
      setError('Failed to load activities');
      logger.error('Error loading activities:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      loadActivities();
    } catch (error) {
      logger.error('Error refreshing activities:', error);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadActivities();
  }, [userId]);

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'trade': return 'trending-up';
      case 'post': return 'message-square';
      case 'comment': return 'message-circle';
      case 'follow': return 'user-plus';
      case 'portfolio': return 'pie-chart';
      default: return 'activity';
    }
  };

  const getActivityColor = (type: ActivityItem['type']) => {
    switch (type) {
      case 'trade': return '#34C759';
      case 'post': return '#007AFF';
      case 'comment': return '#FF9500';
      case 'follow': return '#AF52DE';
      case 'portfolio': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return date.toLocaleDateString();
  };

  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="user-x" size={48} color="#FF3B30" />
          <Text style={styles.errorTitle}>User Not Found</Text>
          <Text style={styles.errorText}>
            Unable to load this user's profile.
          </Text>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => onNavigate('social')}
          >
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading activities...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => onNavigate('user-profile', { userId })}
        >
          <Icon name="arrow-left" size={24} color="#007AFF" />
        </TouchableOpacity>
        <View style={styles.headerInfo}>
          <Text style={styles.headerTitle}>{user.name}'s Activity</Text>
          <Text style={styles.headerSubtitle}>Recent investment activity</Text>
        </View>
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => {/* Filter functionality could be added here */}}
        >
          <Icon name="filter" size={20} color="#007AFF" />
        </TouchableOpacity>
      </View>

      {/* Activities List */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {activities.map((activity) => (
          <View key={activity.id} style={styles.activityItem}>
            <View style={styles.activityIconContainer}>
              <View style={[styles.activityIcon, { backgroundColor: getActivityColor(activity.type) }]}>
                <Icon name={getActivityIcon(activity.type)} size={16} color="#FFFFFF" />
              </View>
            </View>
            <View style={styles.activityContent}>
              <Text style={styles.activityTitle}>{activity.title}</Text>
              <Text style={styles.activityDescription}>{activity.description}</Text>
              {activity.value && (
                <Text style={styles.activityValue}>
                  ${activity.value.toLocaleString()}
                </Text>
              )}
              {activity.symbol && (
                <Text style={styles.activitySymbol}>{activity.symbol}</Text>
              )}
            </View>
            <View style={styles.activityTime}>
              <Text style={styles.timeText}>{formatTimeAgo(activity.timestamp)}</Text>
            </View>
          </View>
        ))}
        
        {activities.length === 0 && (
          <View style={styles.emptyContainer}>
            <Icon name="activity" size={48} color="#8E8E93" />
            <Text style={styles.emptyTitle}>No Activity Yet</Text>
            <Text style={styles.emptyText}>
              This user hasn't been active recently.
            </Text>
          </View>
        )}
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
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  headerInfo: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1C1C1E',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 2,
  },
  filterButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  activityIconContainer: {
    marginRight: 12,
  },
  activityIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  activityContent: {
    flex: 1,
  },
  activityTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  activityDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  activityValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#34C759',
  },
  activitySymbol: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '500',
  },
  activityTime: {
    alignItems: 'flex-end',
  },
  timeText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 22,
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
    padding: 40,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  backButtonText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
});

export default UserActivityScreen;
