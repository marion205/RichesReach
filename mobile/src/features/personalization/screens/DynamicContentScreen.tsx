import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface AdaptedContent {
  id: string;
  type: 'article' | 'video' | 'quiz' | 'module' | 'challenge';
  title: string;
  originalContent: string;
  adaptedContent: string;
  adaptationReason: string;
  personalizationScore: number;
  timestamp: string;
}

interface PersonalizedContent {
  id: string;
  type: 'recommendation' | 'notification' | 'learning_path' | 'trading_signal';
  title: string;
  content: string;
  personalizationFactors: string[];
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  timestamp: string;
}

interface ContentRecommendation {
  id: string;
  title: string;
  type: string;
  reason: string;
  matchScore: number;
  estimatedEngagement: number;
  category: string;
}

interface PersonalizationSettings {
  enableDynamicContent: boolean;
  enablePersonalizedRecommendations: boolean;
  enableAdaptiveLearning: boolean;
  enableBehavioralInsights: boolean;
  personalizationLevel: 'basic' | 'advanced' | 'maximum';
}

const DynamicContentScreen: React.FC = () => {
  const [adaptedContent, setAdaptedContent] = useState<AdaptedContent[]>([]);
  const [personalizedContent, setPersonalizedContent] = useState<PersonalizedContent[]>([]);
  const [recommendations, setRecommendations] = useState<ContentRecommendation[]>([]);
  const [settings, setSettings] = useState<PersonalizationSettings>({
    enableDynamicContent: true,
    enablePersonalizedRecommendations: true,
    enableAdaptiveLearning: true,
    enableBehavioralInsights: true,
    personalizationLevel: 'advanced',
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'adapted' | 'personalized' | 'recommendations' | 'settings'>('adapted');

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Mock adapted content data
      const mockAdaptedContent: AdaptedContent[] = [
        {
          id: '1',
          type: 'article',
          title: 'Options Trading Basics',
          originalContent: 'Standard options trading introduction',
          adaptedContent: 'Visual-heavy options trading guide with interactive examples',
          adaptationReason: 'User prefers visual learning style',
          personalizationScore: 92,
          timestamp: '2024-01-15T10:30:00Z',
        },
        {
          id: '2',
          type: 'quiz',
          title: 'Risk Management Assessment',
          originalContent: 'Text-based risk assessment quiz',
          adaptedContent: 'Interactive scenario-based risk assessment with real examples',
          adaptationReason: 'User learns better through practical examples',
          personalizationScore: 88,
          timestamp: '2024-01-15T09:15:00Z',
        },
        {
          id: '3',
          type: 'module',
          title: 'Portfolio Diversification',
          originalContent: 'General diversification strategies',
          adaptedContent: 'Personalized diversification plan based on user\'s current portfolio',
          adaptationReason: 'Tailored to user\'s specific holdings and risk profile',
          personalizationScore: 95,
          timestamp: '2024-01-14T16:45:00Z',
        },
      ];

      // Mock personalized content data
      const mockPersonalizedContent: PersonalizedContent[] = [
        {
          id: '1',
          type: 'recommendation',
          title: 'AI Trading Coach Session',
          content: 'Based on your recent trading patterns, we recommend a session on risk management',
          personalizationFactors: ['Recent trading behavior', 'Risk tolerance', 'Learning progress'],
          confidence: 87,
          priority: 'high',
          timestamp: '2024-01-15T14:30:00Z',
        },
        {
          id: '2',
          type: 'notification',
          title: 'Market Opportunity Alert',
          content: 'AAPL options showing unusual activity - matches your trading preferences',
          personalizationFactors: ['Trading history', 'Preferred stocks', 'Options activity'],
          confidence: 76,
          priority: 'medium',
          timestamp: '2024-01-15T13:20:00Z',
        },
        {
          id: '3',
          type: 'learning_path',
          title: 'Advanced Options Strategies',
          content: 'You\'re ready for advanced strategies based on your progress',
          personalizationFactors: ['Learning completion', 'Skill assessment', 'Interest patterns'],
          confidence: 91,
          priority: 'high',
          timestamp: '2024-01-15T11:45:00Z',
        },
      ];

      // Mock recommendations data
      const mockRecommendations: ContentRecommendation[] = [
        {
          id: '1',
          title: 'Options Greeks Explained',
          type: 'Video Tutorial',
          reason: 'Matches your learning style and current skill level',
          matchScore: 94,
          estimatedEngagement: 85,
          category: 'Education',
        },
        {
          id: '2',
          title: 'Weekly Market Analysis',
          type: 'Article',
          reason: 'Based on your portfolio holdings and interests',
          matchScore: 89,
          estimatedEngagement: 78,
          category: 'Market Analysis',
        },
        {
          id: '3',
          title: 'Risk Management Challenge',
          type: 'Interactive Challenge',
          reason: 'Addresses your recent trading patterns',
          matchScore: 92,
          estimatedEngagement: 82,
          category: 'Practice',
        },
        {
          id: '4',
          title: 'Community Discussion: AAPL',
          type: 'Community Post',
          reason: 'Matches your stock interests and engagement patterns',
          matchScore: 87,
          estimatedEngagement: 75,
          category: 'Community',
        },
      ];

      setAdaptedContent(mockAdaptedContent);
      setPersonalizedContent(mockPersonalizedContent);
      setRecommendations(mockRecommendations);
    } catch (error) {
      console.error('Error loading dynamic content data:', error);
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

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'article': return 'document-text';
      case 'video': return 'play-circle';
      case 'quiz': return 'help-circle';
      case 'module': return 'book';
      case 'challenge': return 'trophy';
      case 'recommendation': return 'bulb';
      case 'notification': return 'notifications';
      case 'learning_path': return 'map';
      case 'trading_signal': return 'trending-up';
      default: return 'document';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#F44336';
      case 'medium': return '#FF9800';
      case 'low': return '#4CAF50';
      default: return '#666';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Education': return '#2196F3';
      case 'Market Analysis': return '#4CAF50';
      case 'Practice': return '#FF9800';
      case 'Community': return '#9C27B0';
      default: return '#666';
    }
  };

  const renderAdaptedContent = () => (
    <View style={styles.tabContent}>
      {adaptedContent.map((content) => (
        <View key={content.id} style={styles.contentCard}>
          <View style={styles.contentHeader}>
            <View style={styles.contentIcon}>
              <Ionicons name={getTypeIcon(content.type)} size={20} color="#007AFF" />
            </View>
            <View style={styles.contentInfo}>
              <Text style={styles.contentTitle}>{content.title}</Text>
              <Text style={styles.contentType}>{content.type.toUpperCase()}</Text>
            </View>
            <View style={styles.scoreBadge}>
              <Text style={styles.scoreText}>{content.personalizationScore}%</Text>
            </View>
          </View>
          
          <View style={styles.adaptationSection}>
            <Text style={styles.adaptationLabel}>Original:</Text>
            <Text style={styles.adaptationText}>{content.originalContent}</Text>
          </View>
          
          <View style={styles.adaptationSection}>
            <Text style={styles.adaptationLabel}>Adapted:</Text>
            <Text style={styles.adaptationText}>{content.adaptedContent}</Text>
          </View>
          
          <View style={styles.reasonContainer}>
            <Ionicons name="information-circle" size={16} color="#007AFF" />
            <Text style={styles.reasonText}>{content.adaptationReason}</Text>
          </View>
        </View>
      ))}
    </View>
  );

  const renderPersonalizedContent = () => (
    <View style={styles.tabContent}>
      {personalizedContent.map((content) => (
        <View key={content.id} style={styles.contentCard}>
          <View style={styles.contentHeader}>
            <View style={styles.contentIcon}>
              <Ionicons name={getTypeIcon(content.type)} size={20} color="#007AFF" />
            </View>
            <View style={styles.contentInfo}>
              <Text style={styles.contentTitle}>{content.title}</Text>
              <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(content.priority) }]}>
                <Text style={styles.priorityText}>{content.priority.toUpperCase()}</Text>
              </View>
            </View>
            <View style={styles.confidenceBadge}>
              <Text style={styles.confidenceText}>{content.confidence}%</Text>
            </View>
          </View>
          
          <Text style={styles.contentDescription}>{content.content}</Text>
          
          <View style={styles.factorsContainer}>
            <Text style={styles.factorsLabel}>Personalization Factors:</Text>
            <View style={styles.factorsList}>
              {content.personalizationFactors.map((factor, index) => (
                <View key={index} style={styles.factorTag}>
                  <Text style={styles.factorText}>{factor}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>
      ))}
    </View>
  );

  const renderRecommendations = () => (
    <View style={styles.tabContent}>
      {recommendations.map((rec) => (
        <View key={rec.id} style={styles.recommendationCard}>
          <View style={styles.recommendationHeader}>
            <View style={styles.recommendationInfo}>
              <Text style={styles.recommendationTitle}>{rec.title}</Text>
              <Text style={styles.recommendationType}>{rec.type}</Text>
            </View>
            <View style={[styles.categoryBadge, { backgroundColor: getCategoryColor(rec.category) }]}>
              <Text style={styles.categoryText}>{rec.category}</Text>
            </View>
          </View>
          
          <Text style={styles.recommendationReason}>{rec.reason}</Text>
          
          <View style={styles.metricsContainer}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Match Score</Text>
              <Text style={styles.metricValue}>{rec.matchScore}%</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Est. Engagement</Text>
              <Text style={styles.metricValue}>{rec.estimatedEngagement}%</Text>
            </View>
          </View>
          
          <TouchableOpacity style={styles.viewButton}>
            <Text style={styles.viewButtonText}>View Content</Text>
          </TouchableOpacity>
        </View>
      ))}
    </View>
  );

  const renderSettings = () => (
    <View style={styles.tabContent}>
      <View style={styles.settingsCard}>
        <Text style={styles.settingsTitle}>Personalization Settings</Text>
        
        <View style={styles.settingItem}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Dynamic Content Adaptation</Text>
            <Text style={styles.settingDescription}>Automatically adapt content based on your preferences</Text>
          </View>
          <Switch
            value={settings.enableDynamicContent}
            onValueChange={(value) => setSettings({...settings, enableDynamicContent: value})}
            trackColor={{ false: '#e1e5e9', true: '#007AFF' }}
            thumbColor={settings.enableDynamicContent ? '#fff' : '#f4f3f4'}
          />
        </View>
        
        <View style={styles.settingItem}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Personalized Recommendations</Text>
            <Text style={styles.settingDescription}>Receive content recommendations tailored to you</Text>
          </View>
          <Switch
            value={settings.enablePersonalizedRecommendations}
            onValueChange={(value) => setSettings({...settings, enablePersonalizedRecommendations: value})}
            trackColor={{ false: '#e1e5e9', true: '#007AFF' }}
            thumbColor={settings.enablePersonalizedRecommendations ? '#fff' : '#f4f3f4'}
          />
        </View>
        
        <View style={styles.settingItem}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Adaptive Learning</Text>
            <Text style={styles.settingDescription}>Learning paths that adapt to your progress</Text>
          </View>
          <Switch
            value={settings.enableAdaptiveLearning}
            onValueChange={(value) => setSettings({...settings, enableAdaptiveLearning: value})}
            trackColor={{ false: '#e1e5e9', true: '#007AFF' }}
            thumbColor={settings.enableAdaptiveLearning ? '#fff' : '#f4f3f4'}
          />
        </View>
        
        <View style={styles.settingItem}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Behavioral Insights</Text>
            <Text style={styles.settingDescription}>Use behavior patterns to improve recommendations</Text>
          </View>
          <Switch
            value={settings.enableBehavioralInsights}
            onValueChange={(value) => setSettings({...settings, enableBehavioralInsights: value})}
            trackColor={{ false: '#e1e5e9', true: '#007AFF' }}
            thumbColor={settings.enableBehavioralInsights ? '#fff' : '#f4f3f4'}
          />
        </View>
      </View>
      
      <View style={styles.settingsCard}>
        <Text style={styles.settingsTitle}>Personalization Level</Text>
        <View style={styles.levelContainer}>
          {(['basic', 'advanced', 'maximum'] as const).map((level) => (
            <TouchableOpacity
              key={level}
              style={[
                styles.levelButton,
                settings.personalizationLevel === level && styles.activeLevelButton
              ]}
              onPress={() => setSettings({...settings, personalizationLevel: level})}
            >
              <Text style={[
                styles.levelButtonText,
                settings.personalizationLevel === level && styles.activeLevelButtonText
              ]}>
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading dynamic content...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Dynamic Content</Text>
        <Text style={styles.subtitle}>AI-powered content adaptation and personalization</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'adapted' && styles.activeTab]}
          onPress={() => setActiveTab('adapted')}
        >
          <Text style={[styles.tabText, activeTab === 'adapted' && styles.activeTabText]}>
            Adapted
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'personalized' && styles.activeTab]}
          onPress={() => setActiveTab('personalized')}
        >
          <Text style={[styles.tabText, activeTab === 'personalized' && styles.activeTabText]}>
            Personalized
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'recommendations' && styles.activeTab]}
          onPress={() => setActiveTab('recommendations')}
        >
          <Text style={[styles.tabText, activeTab === 'recommendations' && styles.activeTabText]}>
            Recommendations
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'settings' && styles.activeTab]}
          onPress={() => setActiveTab('settings')}
        >
          <Text style={[styles.tabText, activeTab === 'settings' && styles.activeTabText]}>
            Settings
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
        {activeTab === 'adapted' && renderAdaptedContent()}
        {activeTab === 'personalized' && renderPersonalizedContent()}
        {activeTab === 'recommendations' && renderRecommendations()}
        {activeTab === 'settings' && renderSettings()}
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
    paddingVertical: 12,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 14,
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
  contentCard: {
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
  contentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  contentIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  contentInfo: {
    flex: 1,
  },
  contentTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  contentType: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  scoreBadge: {
    backgroundColor: '#E8F5E8',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  scoreText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4CAF50',
  },
  adaptationSection: {
    marginBottom: 12,
  },
  adaptationLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  adaptationText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  reasonContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F8FF',
    padding: 12,
    borderRadius: 8,
  },
  reasonText: {
    fontSize: 14,
    color: '#333',
    marginLeft: 8,
    flex: 1,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  priorityText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  confidenceBadge: {
    backgroundColor: '#FFF3E0',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FF9800',
  },
  contentDescription: {
    fontSize: 14,
    color: '#333',
    marginBottom: 12,
    lineHeight: 20,
  },
  factorsContainer: {
    marginTop: 8,
  },
  factorsLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  factorsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  factorTag: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  factorText: {
    fontSize: 12,
    color: '#1976D2',
    fontWeight: '500',
  },
  recommendationCard: {
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
  recommendationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  recommendationInfo: {
    flex: 1,
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  recommendationType: {
    fontSize: 12,
    color: '#666',
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  recommendationReason: {
    fontSize: 14,
    color: '#333',
    marginBottom: 12,
    lineHeight: 20,
  },
  metricsContainer: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  metricItem: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  viewButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  viewButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  settingsCard: {
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
  settingsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingInfo: {
    flex: 1,
    marginRight: 16,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 14,
    color: '#666',
  },
  levelContainer: {
    flexDirection: 'row',
    marginTop: 8,
  },
  levelButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e1e5e9',
    alignItems: 'center',
    marginHorizontal: 4,
  },
  activeLevelButton: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  levelButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#666',
  },
  activeLevelButtonText: {
    color: '#fff',
  },
});

export default DynamicContentScreen;
