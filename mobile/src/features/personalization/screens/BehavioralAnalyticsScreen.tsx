import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface BehaviorPattern {
  id: string;
  type: 'engagement' | 'learning' | 'trading' | 'social';
  pattern: string;
  frequency: number;
  impact: 'positive' | 'negative' | 'neutral';
  recommendation: string;
}

interface EngagementProfile {
  userId: string;
  totalSessions: number;
  averageSessionTime: number;
  preferredFeatures: string[];
  learningStyle: string;
  riskTolerance: string;
  engagementScore: number;
  lastActive: string;
}

interface ChurnPrediction {
  userId: string;
  churnProbability: number;
  riskFactors: string[];
  retentionStrategies: string[];
  nextAction: string;
}

const { width } = Dimensions.get('window');

const BehavioralAnalyticsScreen: React.FC = () => {
  const [behaviorPatterns, setBehaviorPatterns] = useState<BehaviorPattern[]>([]);
  const [engagementProfile, setEngagementProfile] = useState<EngagementProfile | null>(null);
  const [churnPrediction, setChurnPrediction] = useState<ChurnPrediction | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'patterns' | 'profile' | 'churn'>('patterns');

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Mock behavior patterns data
      const mockPatterns: BehaviorPattern[] = [
        {
          id: '1',
          type: 'engagement',
          pattern: 'Peak activity between 9-11 AM and 7-9 PM',
          frequency: 85,
          impact: 'positive',
          recommendation: 'Schedule important notifications during peak hours',
        },
        {
          id: '2',
          type: 'learning',
          pattern: 'Prefers video content over text-based learning',
          frequency: 72,
          impact: 'positive',
          recommendation: 'Prioritize video tutorials and interactive content',
        },
        {
          id: '3',
          type: 'trading',
          pattern: 'Tends to make trades during market volatility',
          frequency: 68,
          impact: 'negative',
          recommendation: 'Provide risk management reminders during volatile periods',
        },
        {
          id: '4',
          type: 'social',
          pattern: 'Engages more with community features on weekends',
          frequency: 91,
          impact: 'positive',
          recommendation: 'Increase community content and challenges on weekends',
        },
      ];

      // Mock engagement profile
      const mockProfile: EngagementProfile = {
        userId: 'demo-user',
        totalSessions: 47,
        averageSessionTime: 23,
        preferredFeatures: ['AI Trading Coach', 'Market Commentary', 'Peer Progress'],
        learningStyle: 'Visual Learner',
        riskTolerance: 'Moderate',
        engagementScore: 78,
        lastActive: '2024-01-15T14:30:00Z',
      };

      // Mock churn prediction
      const mockChurn: ChurnPrediction = {
        userId: 'demo-user',
        churnProbability: 15,
        riskFactors: ['Decreased session frequency', 'Lower feature engagement'],
        retentionStrategies: ['Personalized content recommendations', 'Gamification elements'],
        nextAction: 'Send personalized learning path',
      };

      setBehaviorPatterns(mockPatterns);
      setEngagementProfile(mockProfile);
      setChurnPrediction(mockChurn);
    } catch (error) {
      console.error('Error loading behavioral analytics data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'positive': return '#4CAF50';
      case 'negative': return '#F44336';
      case 'neutral': return '#FF9800';
      default: return '#666';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'engagement': return 'trending-up';
      case 'learning': return 'school';
      case 'trading': return 'bar-chart';
      case 'social': return 'people';
      default: return 'analytics';
    }
  };

  const renderPatterns = () => (
    <View style={styles.tabContent}>
      {behaviorPatterns.map((pattern) => (
        <View key={pattern.id} style={styles.patternCard}>
          <View style={styles.patternHeader}>
            <View style={styles.patternIcon}>
              <Ionicons name={getTypeIcon(pattern.type)} size={20} color="#007AFF" />
            </View>
            <View style={styles.patternInfo}>
              <Text style={styles.patternType}>{pattern.type.toUpperCase()}</Text>
              <Text style={styles.patternFrequency}>{pattern.frequency}% frequency</Text>
            </View>
            <View style={[styles.impactBadge, { backgroundColor: getImpactColor(pattern.impact) }]}>
              <Text style={styles.impactText}>{pattern.impact}</Text>
            </View>
          </View>
          
          <Text style={styles.patternDescription}>{pattern.pattern}</Text>
          
          <View style={styles.recommendationContainer}>
            <Ionicons name="bulb" size={16} color="#FF9800" />
            <Text style={styles.recommendationText}>{pattern.recommendation}</Text>
          </View>
        </View>
      ))}
    </View>
  );

  const renderProfile = () => (
    <View style={styles.tabContent}>
      {engagementProfile && (
        <>
          {/* Profile Overview */}
          <View style={styles.profileCard}>
            <Text style={styles.profileTitle}>Engagement Profile</Text>
            <View style={styles.profileStats}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{engagementProfile.totalSessions}</Text>
                <Text style={styles.statLabel}>Total Sessions</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{engagementProfile.averageSessionTime}m</Text>
                <Text style={styles.statLabel}>Avg Session</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{engagementProfile.engagementScore}%</Text>
                <Text style={styles.statLabel}>Engagement</Text>
              </View>
            </View>
          </View>

          {/* Learning Style */}
          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>Learning Style</Text>
            <Text style={styles.infoValue}>{engagementProfile.learningStyle}</Text>
          </View>

          {/* Risk Tolerance */}
          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>Risk Tolerance</Text>
            <Text style={styles.infoValue}>{engagementProfile.riskTolerance}</Text>
          </View>

          {/* Preferred Features */}
          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>Preferred Features</Text>
            <View style={styles.featuresList}>
              {engagementProfile.preferredFeatures.map((feature, index) => (
                <View key={index} style={styles.featureTag}>
                  <Text style={styles.featureText}>{feature}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Last Active */}
          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>Last Active</Text>
            <Text style={styles.infoValue}>
              {new Date(engagementProfile.lastActive).toLocaleString()}
            </Text>
          </View>
        </>
      )}
    </View>
  );

  const renderChurn = () => (
    <View style={styles.tabContent}>
      {churnPrediction && (
        <>
          {/* Churn Probability */}
          <View style={styles.churnCard}>
            <Text style={styles.churnTitle}>Churn Risk Assessment</Text>
            <View style={styles.probabilityContainer}>
              <Text style={styles.probabilityValue}>{churnPrediction.churnProbability}%</Text>
              <Text style={styles.probabilityLabel}>Churn Probability</Text>
            </View>
            <View style={styles.riskBar}>
              <View 
                style={[
                  styles.riskFill, 
                  { 
                    width: `${churnPrediction.churnProbability}%`,
                    backgroundColor: churnPrediction.churnProbability > 50 ? '#F44336' : 
                                   churnPrediction.churnProbability > 25 ? '#FF9800' : '#4CAF50'
                  }
                ]} 
              />
            </View>
          </View>

          {/* Risk Factors */}
          <View style={styles.factorsCard}>
            <Text style={styles.factorsTitle}>Risk Factors</Text>
            {churnPrediction.riskFactors.map((factor, index) => (
              <View key={index} style={styles.factorItem}>
                <Ionicons name="warning" size={16} color="#F44336" />
                <Text style={styles.factorText}>{factor}</Text>
              </View>
            ))}
          </View>

          {/* Retention Strategies */}
          <View style={styles.strategiesCard}>
            <Text style={styles.strategiesTitle}>Retention Strategies</Text>
            {churnPrediction.retentionStrategies.map((strategy, index) => (
              <View key={index} style={styles.strategyItem}>
                <Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
                <Text style={styles.strategyText}>{strategy}</Text>
              </View>
            ))}
          </View>

          {/* Next Action */}
          <View style={styles.actionCard}>
            <Text style={styles.actionTitle}>Recommended Action</Text>
            <Text style={styles.actionText}>{churnPrediction.nextAction}</Text>
            <TouchableOpacity style={styles.actionButton}>
              <Text style={styles.actionButtonText}>Take Action</Text>
            </TouchableOpacity>
          </View>
        </>
      )}
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading behavioral analytics...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Behavioral Analytics</Text>
        <Text style={styles.subtitle}>AI-powered insights into user behavior patterns</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'patterns' && styles.activeTab]}
          onPress={() => setActiveTab('patterns')}
        >
          <Text style={[styles.tabText, activeTab === 'patterns' && styles.activeTabText]}>
            Patterns
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'profile' && styles.activeTab]}
          onPress={() => setActiveTab('profile')}
        >
          <Text style={[styles.tabText, activeTab === 'profile' && styles.activeTabText]}>
            Profile
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'churn' && styles.activeTab]}
          onPress={() => setActiveTab('churn')}
        >
          <Text style={[styles.tabText, activeTab === 'churn' && styles.activeTabText]}>
            Churn Risk
          </Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {activeTab === 'patterns' && renderPatterns()}
        {activeTab === 'profile' && renderProfile()}
        {activeTab === 'churn' && renderChurn()}
      </ScrollView>
    </View>
  );
};

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
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e5e9',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e5e9',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  tabContent: {
    padding: 16,
  },
  patternCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  patternHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  patternIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  patternInfo: {
    flex: 1,
  },
  patternType: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  patternFrequency: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  impactBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  impactText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  patternDescription: {
    fontSize: 14,
    color: '#333',
    marginBottom: 12,
    lineHeight: 20,
  },
  recommendationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF8E1',
    padding: 12,
    borderRadius: 8,
  },
  recommendationText: {
    fontSize: 14,
    color: '#333',
    marginLeft: 8,
    flex: 1,
  },
  profileCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  profileTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  profileStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  infoCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  infoValue: {
    fontSize: 14,
    color: '#333',
  },
  featuresList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  featureTag: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  featureText: {
    fontSize: 12,
    color: '#1976D2',
    fontWeight: '500',
  },
  churnCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  churnTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  probabilityContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  probabilityValue: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  probabilityLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  riskBar: {
    height: 8,
    backgroundColor: '#e1e5e9',
    borderRadius: 4,
    overflow: 'hidden',
  },
  riskFill: {
    height: '100%',
    borderRadius: 4,
  },
  factorsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  factorsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  factorItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  factorText: {
    fontSize: 14,
    color: '#333',
    marginLeft: 8,
    flex: 1,
  },
  strategiesCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  strategiesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  strategyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  strategyText: {
    fontSize: 14,
    color: '#333',
    marginLeft: 8,
    flex: 1,
  },
  actionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  actionText: {
    fontSize: 14,
    color: '#333',
    marginBottom: 16,
  },
  actionButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default BehavioralAnalyticsScreen;
