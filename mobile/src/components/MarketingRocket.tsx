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
  TextInput,
  Share,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
import { useTheme } from '../theme/PersonalizedThemes';

const { width } = Dimensions.get('window');

interface ContentCampaign {
  id: string;
  title: string;
  type: 'tiktok' | 'instagram' | 'youtube' | 'blog';
  status: 'active' | 'paused' | 'completed';
  views: number;
  engagement: number;
  conversion: number;
  budget: number;
  spent: number;
}

interface BetaTester {
  id: string;
  name: string;
  email: string;
  demographics: string;
  feedback: string;
  rating: number;
  status: 'active' | 'inactive' | 'completed';
}

interface ViralMetric {
  metric: string;
  value: number;
  target: number;
  trend: 'up' | 'down' | 'stable';
}

interface MarketingRocketProps {
  onNavigate?: (screen: string, params?: any) => void;
  onCampaignPress?: (campaign: ContentCampaign) => void;
  onTesterPress?: (tester: BetaTester) => void;
}

export default function MarketingRocket({ onNavigate, onCampaignPress, onTesterPress }: MarketingRocketProps) {
  const handleCampaignPress = onCampaignPress || (() => {});
  const handleTesterPress = onTesterPress || (() => {});
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<'overview' | 'content' | 'beta' | 'viral'>('overview');
  const [contentCampaigns, setContentCampaigns] = useState<ContentCampaign[]>([]);
  const [betaTesters, setBetaTesters] = useState<BetaTester[]>([]);
  const [viralMetrics, setViralMetrics] = useState<ViralMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [shareText, setShareText] = useState('');
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const rocketAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    loadData();
    startEntranceAnimation();
    startRocketAnimation();
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

  const startRocketAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(rocketAnim, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(rocketAnim, {
          toValue: 0,
          duration: 2000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Simulate API calls
      const mockContentCampaigns: ContentCampaign[] = [
        {
          id: '1',
          title: 'BIPOC Wealth Building Series',
          type: 'tiktok',
          status: 'active',
          views: 125000,
          engagement: 8.5,
          conversion: 3.2,
          budget: 5000,
          spent: 3200,
        },
        {
          id: '2',
          title: 'AI Trading Explained',
          type: 'youtube',
          status: 'active',
          views: 45000,
          engagement: 12.3,
          conversion: 5.8,
          budget: 3000,
          spent: 1800,
        },
        {
          id: '3',
          title: 'Financial Literacy Reels',
          type: 'instagram',
          status: 'paused',
          views: 78000,
          engagement: 6.7,
          conversion: 2.1,
          budget: 2000,
          spent: 1200,
        },
        {
          id: '4',
          title: 'Wealth Building Blog',
          type: 'blog',
          status: 'completed',
          views: 15000,
          engagement: 15.2,
          conversion: 8.9,
          budget: 1000,
          spent: 1000,
        },
      ];
      
      const mockBetaTesters: BetaTester[] = [
        {
          id: '1',
          name: 'Sarah Johnson',
          email: 'sarah@example.com',
          demographics: '25-34, Female, Urban',
          feedback: 'Love the AI insights! The interface is intuitive.',
          rating: 5,
          status: 'active',
        },
        {
          id: '2',
          name: 'Marcus Williams',
          email: 'marcus@example.com',
          demographics: '35-44, Male, Suburban',
          feedback: 'Great educational content. Need more crypto features.',
          rating: 4,
          status: 'active',
        },
        {
          id: '3',
          name: 'Elena Rodriguez',
          email: 'elena@example.com',
          demographics: '25-34, Female, Urban',
          feedback: 'The community features are amazing!',
          rating: 5,
          status: 'completed',
        },
      ];
      
      const mockViralMetrics: ViralMetric[] = [
        {
          metric: 'Viral Coefficient',
          value: 1.8,
          target: 2.0,
          trend: 'up',
        },
        {
          metric: 'Referral Rate',
          value: 15.2,
          target: 20.0,
          trend: 'up',
        },
        {
          metric: 'Social Shares',
          value: 1250,
          target: 2000,
          trend: 'stable',
        },
        {
          metric: 'User-Generated Content',
          value: 89,
          target: 100,
          trend: 'up',
        },
      ];
      
      setContentCampaigns(mockContentCampaigns);
      setBetaTesters(mockBetaTesters);
      setViralMetrics(mockViralMetrics);
    } catch (error) {
      console.error('Error loading marketing data:', error);
      Alert.alert('Error', 'Failed to load marketing data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#34C759';
      case 'paused': return '#FF9500';
      case 'completed': return '#007AFF';
      case 'inactive': return '#8E8E93';
      default: return '#8E8E93';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return '🟢';
      case 'paused': return '🟡';
      case 'completed': return '🔵';
      case 'inactive': return '⚪';
      default: return '⚪';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return '📈';
      case 'down': return '📉';
      case 'stable': return '➡️';
      default: return '➡️';
    }
  };

  const getPlatformIcon = (type: string) => {
    switch (type) {
      case 'tiktok': return '🎵';
      case 'instagram': return '📷';
      case 'youtube': return '📺';
      case 'blog': return '📝';
      default: return '📱';
    }
  };

  const handleShare = async () => {
    try {
      const result = await Share.share({
        message: shareText || 'Check out RichesReach - the AI-powered wealth platform!',
        url: 'https://www.richesreach.com',
      });
      if (result.action === Share.sharedAction) {
        Alert.alert('Success', 'Content shared successfully!');
      }
    } catch (error: any) {
      Alert.alert('Error', error.message);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator
          size="large"
          color="#F59E0B"
          style={styles.loadingAnimation}
        />
        <Text style={styles.loadingText}>Launching marketing rocket...</Text>
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
        <Text style={styles.headerTitle}>Marketing Rocket</Text>
        <Text style={styles.headerSubtitle}>Launch your content empire</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        {[
          { id: 'overview', name: 'Overview', icon: '🚀' },
          { id: 'content', name: 'Content', icon: '📱' },
          { id: 'beta', name: 'Beta Blitz', icon: '🧪' },
          { id: 'viral', name: 'Viral Growth', icon: '📈' },
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
        {activeTab === 'overview' && (
          <View style={styles.overviewContent}>
            {/* Marketing Dashboard */}
            <View style={styles.marketingDashboardCard}>
              <View style={styles.marketingDashboardBlur}>
                <View style={styles.marketingDashboardHeader}>
                  <Text style={styles.marketingDashboardTitle}>Marketing Dashboard</Text>
                  <Animated.View
                    style={[
                      styles.rocketIcon,
                      {
                        transform: [{ translateY: rocketAnim }],
                      },
                    ]}
                  >
                    <Text style={styles.rocketEmoji}>🚀</Text>
                  </Animated.View>
                </View>
                
                <View style={styles.marketingMetrics}>
                  <View style={styles.marketingMetric}>
                    <Text style={styles.marketingMetricValue}>2.3M</Text>
                    <Text style={styles.marketingMetricLabel}>Total Reach</Text>
                  </View>
                  <View style={styles.marketingMetric}>
                    <Text style={styles.marketingMetricValue}>15.2%</Text>
                    <Text style={styles.marketingMetricLabel}>Conversion Rate</Text>
                  </View>
                  <View style={styles.marketingMetric}>
                    <Text style={styles.marketingMetricValue}>$12.5K</Text>
                    <Text style={styles.marketingMetricLabel}>ROI</Text>
                  </View>
                </View>
              </View>
            </View>

            {/* Content Performance */}
            <View style={styles.contentPerformanceCard}>
              <Text style={styles.contentPerformanceTitle}>Content Performance</Text>
              <View style={styles.contentPerformanceChart}>
                <ActivityIndicator
                  size="small"
                  color="#F59E0B"
                  style={styles.contentPerformanceAnimation}
                />
              </View>
            </View>

            {/* Quick Actions */}
            <View style={styles.quickActionsCard}>
              <Text style={styles.quickActionsTitle}>Quick Actions</Text>
              <View style={styles.quickActionsGrid}>
                <TouchableOpacity style={styles.quickActionButton}>
                  <Text style={styles.quickActionIcon}>📱</Text>
                  <Text style={styles.quickActionText}>Create Post</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.quickActionButton}>
                  <Text style={styles.quickActionIcon}>📊</Text>
                  <Text style={styles.quickActionText}>Analytics</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.quickActionButton}>
                  <Text style={styles.quickActionIcon}>👥</Text>
                  <Text style={styles.quickActionText}>Invite Testers</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.quickActionButton}>
                  <Text style={styles.quickActionIcon}>🎯</Text>
                  <Text style={styles.quickActionText}>Target Audience</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}

        {activeTab === 'content' && (
          <View style={styles.contentTabContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Content Campaigns</Text>
              <Text style={styles.sectionSubtitle}>
                Multi-platform content strategy
              </Text>
            </View>

            {contentCampaigns.map((campaign) => (
              <ContentCampaignCard
                key={campaign.id}
                campaign={campaign}
                onPress={() => handleCampaignPress(campaign)}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
                getPlatformIcon={getPlatformIcon}
              />
            ))}
          </View>
        )}

        {activeTab === 'beta' && (
          <View style={styles.betaTabContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Beta Testers</Text>
              <Text style={styles.sectionSubtitle}>
                1K diverse testers program
              </Text>
            </View>

            {betaTesters.map((tester) => (
              <BetaTesterCard
                key={tester.id}
                tester={tester}
                onPress={() => handleTesterPress(tester)}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
              />
            ))}

            <View style={styles.betaInviteCard}>
              <Text style={styles.betaInviteTitle}>Invite Beta Testers</Text>
              <TextInput
                style={styles.betaInviteInput}
                placeholder="Enter email addresses (comma separated)"
                placeholderTextColor="#999"
                multiline
                numberOfLines={3}
              />
              <TouchableOpacity style={styles.betaInviteButton}>
                <LinearGradient
                  colors={['#667eea', '#764ba2']}
                  style={styles.betaInviteGradient}
                >
                  <Text style={styles.betaInviteButtonText}>Send Invites</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {activeTab === 'viral' && (
          <View style={styles.viralTabContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Viral Growth Metrics</Text>
              <Text style={styles.sectionSubtitle}>
                Track viral growth loops
              </Text>
            </View>

            {viralMetrics.map((metric) => (
              <ViralMetricCard
                key={metric.metric}
                metric={metric}
                getTrendIcon={getTrendIcon}
              />
            ))}

            <View style={styles.viralShareCard}>
              <Text style={styles.viralShareTitle}>Share & Grow</Text>
              <TextInput
                style={styles.viralShareInput}
                placeholder="Customize your share message..."
                placeholderTextColor="#999"
                value={shareText}
                onChangeText={setShareText}
                multiline
                numberOfLines={3}
              />
              <TouchableOpacity style={styles.viralShareButton} onPress={handleShare}>
                <LinearGradient
                  colors={['#34C759', '#30D158']}
                  style={styles.viralShareGradient}
                >
                  <Text style={styles.viralShareButtonText}>Share Now</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
    </Animated.View>
  );
}

// Content Campaign Card Component
function ContentCampaignCard({ campaign, onPress, getStatusColor, getStatusIcon, getPlatformIcon }: any) {
  return (
    <TouchableOpacity style={styles.campaignCard} onPress={onPress}>
      <View style={styles.campaignBlur}>
        <View style={styles.campaignHeader}>
          <View style={styles.campaignInfo}>
            <Text style={styles.campaignPlatform}>{getPlatformIcon(campaign.type)}</Text>
            <Text style={styles.campaignTitle}>{campaign.title}</Text>
          </View>
          <View style={[styles.campaignStatus, { backgroundColor: getStatusColor(campaign.status) }]}>
            <Text style={styles.campaignStatusText}>{campaign.status.toUpperCase()}</Text>
          </View>
        </View>

        <View style={styles.campaignMetrics}>
          <View style={styles.campaignMetric}>
            <Text style={styles.campaignMetricLabel}>Views</Text>
            <Text style={styles.campaignMetricValue}>{campaign.views.toLocaleString()}</Text>
          </View>
          <View style={styles.campaignMetric}>
            <Text style={styles.campaignMetricLabel}>Engagement</Text>
            <Text style={styles.campaignMetricValue}>{campaign.engagement}%</Text>
          </View>
          <View style={styles.campaignMetric}>
            <Text style={styles.campaignMetricLabel}>Conversion</Text>
            <Text style={styles.campaignMetricValue}>{campaign.conversion}%</Text>
          </View>
        </View>

        <View style={styles.campaignBudget}>
          <Text style={styles.campaignBudgetLabel}>Budget: ${campaign.budget.toLocaleString()}</Text>
          <Text style={styles.campaignBudgetSpent}>Spent: ${campaign.spent.toLocaleString()}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// Beta Tester Card Component
function BetaTesterCard({ tester, onPress, getStatusColor, getStatusIcon }: any) {
  return (
    <TouchableOpacity style={styles.testerCard} onPress={onPress}>
      <View style={styles.testerBlur}>
        <View style={styles.testerHeader}>
          <View style={styles.testerInfo}>
            <Text style={styles.testerName}>{tester.name}</Text>
            <Text style={styles.testerEmail}>{tester.email}</Text>
            <Text style={styles.testerDemographics}>{tester.demographics}</Text>
          </View>
          <View style={[styles.testerStatus, { backgroundColor: getStatusColor(tester.status) }]}>
            <Text style={styles.testerStatusText}>{tester.status.toUpperCase()}</Text>
          </View>
        </View>

        <View style={styles.testerFeedback}>
          <Text style={styles.testerFeedbackText}>"{tester.feedback}"</Text>
        </View>

        <View style={styles.testerRating}>
          <Text style={styles.testerRatingLabel}>Rating:</Text>
          <Text style={styles.testerRatingValue}>{'⭐'.repeat(tester.rating)}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// Viral Metric Card Component
function ViralMetricCard({ metric, getTrendIcon }: any) {
  const progress = (metric.value / metric.target) * 100;
  
  return (
    <View style={styles.viralMetricCard}>
      <View style={styles.viralMetricBlur}>
        <View style={styles.viralMetricHeader}>
          <Text style={styles.viralMetricName}>{metric.metric}</Text>
          <Text style={styles.viralMetricTrend}>{getTrendIcon(metric.trend)}</Text>
        </View>

        <View style={styles.viralMetricValue}>
          <Text style={styles.viralMetricCurrent}>{metric.value}</Text>
          <Text style={styles.viralMetricTarget}>/ {metric.target}</Text>
        </View>

        <View style={styles.viralMetricProgress}>
          <View style={styles.viralMetricProgressBar}>
            <View
              style={[
                styles.viralMetricProgressFill,
                { width: `${Math.min(progress, 100)}%` },
              ]}
            />
          </View>
          <Text style={styles.viralMetricProgressText}>{(progress || 0).toFixed(1)}%</Text>
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
  overviewContent: {
    padding: 16,
  },
  marketingDashboardCard: {
    marginBottom: 20,
    borderRadius: 16,
    overflow: 'hidden',
  },
  marketingDashboardBlur: {
    padding: 24,
  },
  marketingDashboardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  marketingDashboardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  rocketIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(102, 126, 234, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  rocketEmoji: {
    fontSize: 20,
  },
  marketingMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  marketingMetric: {
    alignItems: 'center',
  },
  marketingMetricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  marketingMetricLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  contentPerformanceCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  contentPerformanceTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  contentPerformanceChart: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  contentPerformanceAnimation: {
    width: 300,
    height: 150,
  },
  quickActionsCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
  },
  quickActionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickActionButton: {
    width: '48%',
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  quickActionIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  quickActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
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
  contentTabContent: {
    padding: 16,
  },
  campaignCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  campaignBlur: {
    padding: 20,
  },
  campaignHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  campaignInfo: {
    flex: 1,
  },
  campaignPlatform: {
    fontSize: 20,
    marginBottom: 4,
  },
  campaignTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  campaignStatus: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  campaignStatusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  campaignMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  campaignMetric: {
    alignItems: 'center',
  },
  campaignMetricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  campaignMetricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  campaignBudget: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
  },
  campaignBudgetLabel: {
    fontSize: 14,
    color: '#1a1a1a',
  },
  campaignBudgetSpent: {
    fontSize: 14,
    color: '#666',
  },
  betaTabContent: {
    padding: 16,
  },
  testerCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  testerBlur: {
    padding: 20,
  },
  testerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  testerInfo: {
    flex: 1,
  },
  testerName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  testerEmail: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  testerDemographics: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  testerStatus: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  testerStatusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  testerFeedback: {
    marginBottom: 12,
  },
  testerFeedbackText: {
    fontSize: 14,
    color: '#1a1a1a',
    fontStyle: 'italic',
  },
  testerRating: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  testerRatingLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  testerRatingValue: {
    fontSize: 16,
  },
  betaInviteCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginTop: 16,
  },
  betaInviteTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  betaInviteInput: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#1a1a1a',
    marginBottom: 16,
    textAlignVertical: 'top',
  },
  betaInviteButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  betaInviteGradient: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  betaInviteButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  viralTabContent: {
    padding: 16,
  },
  viralMetricCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  viralMetricBlur: {
    padding: 20,
  },
  viralMetricHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  viralMetricName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  viralMetricTrend: {
    fontSize: 20,
  },
  viralMetricValue: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 12,
  },
  viralMetricCurrent: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  viralMetricTarget: {
    fontSize: 16,
    color: '#666',
    marginLeft: 8,
  },
  viralMetricProgress: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viralMetricProgressBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
    marginRight: 12,
  },
  viralMetricProgressFill: {
    height: '100%',
    backgroundColor: '#34C759',
    borderRadius: 4,
  },
  viralMetricProgressText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  viralShareCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginTop: 16,
  },
  viralShareTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  viralShareInput: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#1a1a1a',
    marginBottom: 16,
    textAlignVertical: 'top',
  },
  viralShareButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  viralShareGradient: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  viralShareButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});
