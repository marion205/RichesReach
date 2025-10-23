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
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
import { useTheme } from '../theme/PersonalizedThemes';

const { width } = Dimensions.get('window');

// Move categories outside component to ensure it's always available - Version 2.2
const WEALTH_CIRCLES_CATEGORIES = [
  { id: 'all', name: 'All Circles', icon: '🌟', color: '#667eea' },
  { id: 'investment', name: 'Investment', icon: '📈', color: '#34C759' },
  { id: 'education', name: 'Education', icon: '🎓', color: '#007AFF' },
  { id: 'entrepreneurship', name: 'Entrepreneurship', icon: '🚀', color: '#FF9500' },
  { id: 'real_estate', name: 'Real Estate', icon: '🏠', color: '#5856D6' },
  { id: 'crypto', name: 'Crypto', icon: '₿', color: '#FF3B30' },
  { id: 'tax_optimization', name: 'Tax Optimization', icon: '💰', color: '#30D158' },
];

interface WealthCircle {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  totalValue: number;
  performance: number;
  category: 'investment' | 'education' | 'entrepreneurship' | 'real_estate' | 'crypto' | 'tax_optimization';
  isPrivate: boolean;
  isJoined: boolean;
  members: CircleMember[];
  recentActivity: CircleActivity[];
  rules: string[];
  tags: string[];
  createdBy: string;
  createdAt: string;
}

interface CircleMember {
  id: string;
  name: string;
  avatar: string;
  role: 'founder' | 'moderator' | 'member';
  portfolioValue: number;
  performance: number;
  isOnline: boolean;
  lastActive: string;
}

interface CircleActivity {
  id: string;
  type: 'trade' | 'insight' | 'discussion' | 'achievement' | 'milestone';
  user: CircleMember;
  content: string;
  timestamp: string;
  likes: number;
  comments: number;
  isLiked: boolean;
}

interface WealthCircles2Props {
  onCirclePress: (circle: WealthCircle) => void;
  onCreateCircle: () => void;
  onJoinCircle: (circleId: string) => void;
}

export default function WealthCircles2({ onCirclePress, onCreateCircle, onJoinCircle }: WealthCircles2Props) {
  console.log('🚀 WealthCircles2: Component rendering - Version 2.3');
  
  try {
    const theme = useTheme();
  // Force component refresh - Version 2.1 - Fixed prop mismatch
  const [circles, setCircles] = useState<WealthCircle[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  // Force component refresh - Version 2.3 - Direct constant usage
  const categories = [
    { id: 'all', name: 'All Circles', icon: '🌟', color: '#667eea' },
    { id: 'investment', name: 'Investment', icon: '📈', color: '#34C759' },
    { id: 'education', name: 'Education', icon: '🎓', color: '#007AFF' },
    { id: 'entrepreneurship', name: 'Entrepreneurship', icon: '🚀', color: '#FF9500' },
    { id: 'real_estate', name: 'Real Estate', icon: '🏠', color: '#5856D6' },
    { id: 'crypto', name: 'Crypto', icon: '₿', color: '#FF3B30' },
    { id: 'tax_optimization', name: 'Tax Optimization', icon: '💰', color: '#30D158' },
  ];

  // Debug log to ensure categories is available
  console.log('🔍 WealthCircles2: categories available:', categories.length);

  useEffect(() => {
    loadCircles();
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

  const loadCircles = async () => {
    try {
      setLoading(true);
      
      // Use real API endpoint
      const response = await fetch('http://127.0.0.1:8000/api/wealth-circles/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await AsyncStorage.getItem('authToken')}`,
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const apiCircles = await response.json();
      
      // Transform API data to match component interface
      const transformedCircles: WealthCircle[] = apiCircles.map((circle: any) => ({
        id: circle.id,
        name: circle.name,
        description: circle.description || 'Building wealth through community support',
        memberCount: circle.members || 0,
        totalValue: 0, // Not provided by API
        performance: 0, // Not provided by API
        category: circle.category || 'investment',
        isPrivate: false,
        isJoined: false,
        members: circle.activity?.map((activity: any) => ({
          id: activity.user || 'unknown',
          name: activity.user || 'Anonymous',
          avatar: 'https://via.placeholder.com/40',
          role: 'member',
          portfolioValue: 0,
          performance: 0,
          isOnline: false,
          lastActive: activity.timestamp || 'Unknown',
        })) || [],
        recentActivity: circle.recentActivity || [],
        tags: [circle.category || 'investment'],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }));
      
      setCircles(transformedCircles);
      
      // Fallback to mock data if API fails
      const mockCircles: WealthCircle[] = [
        {
          id: '1',
          name: 'BIPOC Wealth Builders',
          description: 'Building generational wealth through smart investing and community support',
          memberCount: 1247,
          totalValue: 12500000,
          performance: 12.5,
          category: 'investment',
          isPrivate: false,
          isJoined: true,
          members: [
            {
              id: '1',
              name: 'Marcus Johnson',
              avatar: 'https://via.placeholder.com/40',
              role: 'founder',
              portfolioValue: 250000,
              performance: 15.2,
              isOnline: true,
              lastActive: '2 minutes ago',
            },
            {
              id: '2',
              name: 'Aisha Williams',
              avatar: 'https://via.placeholder.com/40',
              role: 'moderator',
              portfolioValue: 180000,
              performance: 11.8,
              isOnline: true,
              lastActive: '5 minutes ago',
            },
          ],
          recentActivity: [
            {
              id: '1',
              type: 'trade',
              user: {
                id: '1',
                name: 'Marcus Johnson',
                avatar: 'https://via.placeholder.com/40',
                role: 'founder',
                portfolioValue: 250000,
                performance: 15.2,
                isOnline: true,
                lastActive: '2 minutes ago',
              },
              content: 'Just opened a position in $NVDA - AI is the future!',
              timestamp: '2 minutes ago',
              likes: 23,
              comments: 5,
              isLiked: false,
            },
          ],
          rules: [
            'Be respectful and supportive',
            'Share knowledge, not just gains',
            'No financial advice without disclaimers',
          ],
          tags: ['BIPOC', 'Wealth Building', 'Investment', 'Community'],
          createdBy: 'Marcus Johnson',
          createdAt: '2024-01-15',
        },
        {
          id: '2',
          name: 'Black Entrepreneurs Network',
          description: 'Connecting Black entrepreneurs and sharing business strategies',
          memberCount: 892,
          totalValue: 8500000,
          performance: 18.3,
          category: 'entrepreneurship',
          isPrivate: false,
          isJoined: false,
          members: [],
          recentActivity: [],
          rules: [
            'Focus on business growth',
            'Share actionable strategies',
            'Support fellow entrepreneurs',
          ],
          tags: ['Entrepreneurship', 'Business', 'Black Owned', 'Growth'],
          createdBy: 'Sarah Davis',
          createdAt: '2024-02-01',
        },
        {
          id: '3',
          name: 'Crypto Wealth Circle',
          description: 'Advanced crypto strategies and DeFi opportunities',
          memberCount: 456,
          totalValue: 3200000,
          performance: 25.7,
          category: 'crypto',
          isPrivate: true,
          isJoined: true,
          members: [],
          recentActivity: [],
          rules: [
            'High risk tolerance required',
            'Share research, not shilling',
            'DYOR always',
          ],
          tags: ['Crypto', 'DeFi', 'Advanced', 'High Risk'],
          createdBy: 'David Chen',
          createdAt: '2024-01-20',
        },
        {
          id: '4',
          name: 'Tax Optimization Masters',
          description: 'Advanced tax strategies for wealth preservation and growth',
          memberCount: 234,
          totalValue: 1800000,
          performance: 8.9,
          category: 'tax_optimization',
          isPrivate: false,
          isJoined: false,
          members: [
            {
              id: '3',
              name: 'Dr. Maria Rodriguez',
              avatar: 'https://via.placeholder.com/40',
              role: 'founder',
              portfolioValue: 320000,
              performance: 12.1,
              isOnline: true,
              lastActive: '1 hour ago',
            },
          ],
          recentActivity: [
            {
              id: '2',
              type: 'insight',
              user: {
                id: '3',
                name: 'Dr. Maria Rodriguez',
                avatar: 'https://via.placeholder.com/40',
                role: 'founder',
                portfolioValue: 320000,
                performance: 12.1,
                isOnline: true,
                lastActive: '1 hour ago',
              },
              content: 'Tax loss harvesting strategies for Q4 - maximize your deductions!',
              timestamp: '1 hour ago',
              likes: 15,
              comments: 3,
              isLiked: true,
            },
          ],
          rules: [
            'Share proven tax strategies',
            'No illegal tax avoidance',
            'Consult professionals for complex situations',
          ],
          tags: ['Tax Optimization', 'Wealth Preservation', 'CPA', 'Strategy'],
          createdBy: 'Dr. Maria Rodriguez',
          createdAt: '2024-01-10',
        },
        {
          id: '5',
          name: 'Real Estate Investors United',
          description: 'Building wealth through smart real estate investments',
          memberCount: 567,
          totalValue: 4500000,
          performance: 15.2,
          category: 'real_estate',
          isPrivate: false,
          isJoined: true,
          members: [
            {
              id: '4',
              name: 'James Thompson',
              avatar: 'https://via.placeholder.com/40',
              role: 'moderator',
              portfolioValue: 180000,
              performance: 14.8,
              isOnline: false,
              lastActive: '3 hours ago',
            },
          ],
          recentActivity: [
            {
              id: '3',
              type: 'milestone',
              user: {
                id: '4',
                name: 'James Thompson',
                avatar: 'https://via.placeholder.com/40',
                role: 'moderator',
                portfolioValue: 180000,
                performance: 14.8,
                isOnline: false,
                lastActive: '3 hours ago',
              },
              content: 'Just closed on my 5th rental property! 🏠',
              timestamp: '3 hours ago',
              likes: 28,
              comments: 7,
              isLiked: false,
            },
          ],
          rules: [
            'Share market insights and opportunities',
            'Respect local market conditions',
            'Due diligence always required',
          ],
          tags: ['Real Estate', 'Rental Properties', 'REITs', 'Investment'],
          createdBy: 'James Thompson',
          createdAt: '2024-01-05',
        },
        {
          id: '6',
          name: 'Financial Education Hub',
          description: 'Learn the fundamentals of wealth building and financial literacy',
          memberCount: 1234,
          totalValue: 2100000,
          performance: 6.8,
          category: 'education',
          isPrivate: false,
          isJoined: false,
          members: [
            {
              id: '5',
              name: 'Professor Lisa Chen',
              avatar: 'https://via.placeholder.com/40',
              role: 'founder',
              portfolioValue: 95000,
              performance: 9.2,
              isOnline: true,
              lastActive: '30 minutes ago',
            },
          ],
          recentActivity: [
            {
              id: '4',
              type: 'discussion',
              user: {
                id: '5',
                name: 'Professor Lisa Chen',
                avatar: 'https://via.placeholder.com/40',
                role: 'founder',
                portfolioValue: 95000,
                performance: 9.2,
                isOnline: true,
                lastActive: '30 minutes ago',
              },
              content: 'New lesson posted: Understanding compound interest and time value of money',
              timestamp: '30 minutes ago',
              likes: 42,
              comments: 12,
              isLiked: true,
            },
          ],
          rules: [
            'Ask questions, share knowledge',
            'Be patient with beginners',
            'Focus on education, not advice',
          ],
          tags: ['Education', 'Financial Literacy', 'Learning', 'Beginners'],
          createdBy: 'Professor Lisa Chen',
          createdAt: '2023-12-15',
        },
      ];
      
      setCircles(mockCircles);
    } catch (error) {
      console.error('Error loading circles:', error);
      Alert.alert('Error', 'Failed to load wealth circles');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadCircles();
    setRefreshing(false);
  };

  const filteredCircles = selectedCategory === 'all' 
    ? circles 
    : circles.filter(circle => circle.category === selectedCategory);

  const getCategoryIcon = (category: string) => {
    if (!categories || !Array.isArray(categories)) {
      console.log('⚠️ getCategoryIcon: categories not available');
      return '🌟';
    }
    const cat = categories.find(c => c.id === category);
    return cat ? cat.icon : '🌟';
  };

  const getCategoryColor = (category: string) => {
    if (!categories || !Array.isArray(categories)) {
      console.log('⚠️ getCategoryColor: categories not available');
      return '#667eea';
    }
    const cat = categories.find(c => c.id === category);
    return cat ? cat.color : '#667eea';
  };

  const getCategoryName = (category: string) => {
    if (!categories || !Array.isArray(categories)) {
      console.log('⚠️ getCategoryName: categories not available');
      return 'Unknown';
    }
    const cat = categories.find(c => c.id === category);
    return cat ? cat.name : 'Unknown';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator
          size="large"
          color="#8B5CF6"
          style={styles.loadingAnimation}
        />
        <Text style={styles.loadingText}>Loading wealth circles...</Text>
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
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>Wealth Circles</Text>
          <Text style={styles.headerSubtitle}>Connect, learn, and grow together</Text>
        </View>
        
        <TouchableOpacity style={styles.createButton} onPress={onCreateCircle}>
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={styles.createButtonGradient}
          >
            <Text style={styles.createButtonText}>+ Create</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>

      {/* Category Filter */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.categoryFilter}
        contentContainerStyle={styles.categoryFilterContent}
      >
        {categories && Array.isArray(categories) ? categories.map((category) => (
          <TouchableOpacity
            key={category.id}
            style={[
              styles.categoryButton,
              selectedCategory === category.id && styles.categoryButtonActive,
              { borderColor: category.color }
            ]}
            onPress={() => setSelectedCategory(category.id)}
          >
            <Text style={styles.categoryIcon}>{category.icon}</Text>
            <Text style={[
              styles.categoryText,
              selectedCategory === category.id && styles.categoryTextActive
            ]}>
              {category.name}
            </Text>
          </TouchableOpacity>
        )) : null}
      </ScrollView>

      {/* Circles List */}
      <FlatList
        data={filteredCircles}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.currentTheme.colors.primary}
          />
        }
        renderItem={({ item }) => (
          <CircleCard
            circle={item}
            onPress={() => onCirclePress(item)}
            onJoin={() => onJoinCircle(item.id)}
            getCategoryIcon={getCategoryIcon}
            getCategoryColor={getCategoryColor}
            getCategoryName={getCategoryName}
          />
        )}
        contentContainerStyle={styles.circlesList}
      />
    </Animated.View>
  );
  } catch (error) {
    console.error('❌ WealthCircles2: Error in component:', error);
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Error loading wealth circles</Text>
      </View>
    );
  }
}

// Circle Card Component
function CircleCard({ 
  circle, 
  onPress, 
  onJoin, 
  getCategoryIcon, 
  getCategoryColor,
  getCategoryName
}: any) {
  const theme = useTheme();
  
  return (
    <TouchableOpacity style={styles.circleCard} onPress={onPress}>
      <View intensity={20} style={styles.circleBlur}>
        {/* Header */}
        <View style={styles.circleHeader}>
          <View style={styles.circleInfo}>
            <View style={styles.circleTitleRow}>
              <Text style={styles.circleName}>{circle.name}</Text>
              {circle.isPrivate && (
                <View style={styles.privateBadge}>
                  <Text style={styles.privateIcon}>🔒</Text>
                </View>
              )}
            </View>
            <Text style={styles.circleDescription} numberOfLines={2}>
              {circle.description}
            </Text>
          </View>
          
          <View style={styles.circleStats}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{circle.memberCount.toLocaleString()}</Text>
              <Text style={styles.statLabel}>Members</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>${((circle.totalValue || 0) / 1000000).toFixed(1)}M</Text>
              <Text style={styles.statLabel}>Total Value</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: circle.performance > 0 ? '#34C759' : '#FF3B30' }]}>
                {circle.performance > 0 ? '+' : ''}{circle.performance}%
              </Text>
              <Text style={styles.statLabel}>Performance</Text>
            </View>
          </View>
        </View>

        {/* Category and Tags */}
        <View style={styles.circleMeta}>
          <View style={[styles.categoryBadge, { backgroundColor: getCategoryColor(circle.category) }]}>
            <Text style={styles.categoryBadgeIcon}>{getCategoryIcon(circle.category)}</Text>
            <Text style={styles.categoryBadgeText}>
              {getCategoryName(circle.category)}
            </Text>
          </View>
          
          <View style={styles.tagsContainer}>
            {circle.tags.slice(0, 3).map((tag: string, index: number) => (
              <View key={index} style={styles.tag}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Recent Activity */}
        {circle.recentActivity.length > 0 && (
          <View style={styles.recentActivity}>
            <Text style={styles.recentActivityTitle}>Recent Activity</Text>
            {circle.recentActivity.slice(0, 2).map((activity: CircleActivity) => (
              <ActivityItem key={activity.id} activity={activity} />
            ))}
          </View>
        )}

        {/* Members Preview */}
        {circle.members.length > 0 && (
          <View style={styles.membersPreview}>
            <Text style={styles.membersTitle}>Top Members</Text>
            <View style={styles.membersList}>
              {circle.members.slice(0, 3).map((member: CircleMember) => (
                <View key={member.id} style={styles.memberItem}>
                  <Image source={{ uri: member.avatar }} style={styles.memberAvatar} />
                  <View style={styles.memberInfo}>
                    <Text style={styles.memberName}>{member.name}</Text>
                    <Text style={styles.memberRole}>{member.role}</Text>
                  </View>
                  {member.isOnline && <View style={styles.onlineIndicator} />}
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Action Button */}
        <View style={styles.circleActions}>
          {circle.isJoined ? (
            <TouchableOpacity style={styles.joinedButton}>
              <Text style={styles.joinedButtonText}>✓ Joined</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={styles.joinButton} onPress={onJoin}>
              <LinearGradient
                colors={[getCategoryColor(circle.category), `${getCategoryColor(circle.category)}80`]}
                style={styles.joinButtonGradient}
              >
                <Text style={styles.joinButtonText}>Join Circle</Text>
              </LinearGradient>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
}

// Activity Item Component
function ActivityItem({ activity }: { activity: CircleActivity }) {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'trade': return '📈';
      case 'insight': return '💡';
      case 'discussion': return '💬';
      case 'achievement': return '🏆';
      case 'milestone': return '🎯';
      default: return '📊';
    }
  };

  return (
    <View style={styles.activityItem}>
      <Text style={styles.activityIcon}>{getActivityIcon(activity.type)}</Text>
      <View style={styles.activityContent}>
        <Text style={styles.activityUser}>{activity.user.name}</Text>
        <Text style={styles.activityText} numberOfLines={1}>
          {activity.content}
        </Text>
        <View style={styles.activityMeta}>
          <Text style={styles.activityTime}>{activity.timestamp}</Text>
          <View style={styles.activityStats}>
            <Text style={styles.activityStat}>👍 {activity.likes}</Text>
            <Text style={styles.activityStat}>💬 {activity.comments}</Text>
          </View>
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerLeft: {
    flex: 1,
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
  createButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  createButtonGradient: {
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  createButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  categoryFilter: {
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  categoryFilterContent: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  categoryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 12,
    borderRadius: 20,
    borderWidth: 1,
    backgroundColor: 'white',
  },
  categoryButtonActive: {
    backgroundColor: '#f0f0f0',
  },
  categoryIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  categoryText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  categoryTextActive: {
    color: '#1a1a1a',
    fontWeight: '600',
  },
  circlesList: {
    padding: 16,
  },
  circleCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  circleBlur: {
    padding: 20,
  },
  circleHeader: {
    marginBottom: 16,
  },
  circleInfo: {
    marginBottom: 12,
  },
  circleTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  circleName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    flex: 1,
  },
  privateBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  privateIcon: {
    fontSize: 12,
  },
  circleDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  circleStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
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
  circleMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginRight: 12,
  },
  categoryBadgeIcon: {
    fontSize: 14,
    marginRight: 4,
  },
  categoryBadgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  tagsContainer: {
    flexDirection: 'row',
    flex: 1,
  },
  tag: {
    backgroundColor: 'rgba(102, 126, 234, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    marginRight: 6,
  },
  tagText: {
    fontSize: 10,
    color: '#667eea',
    fontWeight: '500',
  },
  recentActivity: {
    marginBottom: 16,
  },
  recentActivityTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  activityIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  activityContent: {
    flex: 1,
  },
  activityUser: {
    fontSize: 12,
    fontWeight: '600',
    color: '#667eea',
  },
  activityText: {
    fontSize: 12,
    color: '#666',
    marginVertical: 2,
  },
  activityMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  activityTime: {
    fontSize: 10,
    color: '#999',
  },
  activityStats: {
    flexDirection: 'row',
  },
  activityStat: {
    fontSize: 10,
    color: '#999',
    marginLeft: 8,
  },
  membersPreview: {
    marginBottom: 16,
  },
  membersTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  membersList: {
    flexDirection: 'row',
  },
  memberItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
    position: 'relative',
  },
  memberAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
  },
  memberInfo: {
    marginLeft: 8,
  },
  memberName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  memberRole: {
    fontSize: 10,
    color: '#666',
  },
  onlineIndicator: {
    position: 'absolute',
    top: 0,
    right: 0,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#34C759',
    borderWidth: 1,
    borderColor: 'white',
  },
  circleActions: {
    alignItems: 'center',
  },
  joinedButton: {
    backgroundColor: '#34C759',
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 20,
  },
  joinedButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  joinButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  joinButtonGradient: {
    paddingHorizontal: 24,
    paddingVertical: 10,
  },
  joinButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
});
