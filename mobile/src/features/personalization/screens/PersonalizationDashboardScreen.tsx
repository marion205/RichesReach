import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  ScrollView, 
  ActivityIndicator, 
  Alert,
  Dimensions
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';

const { width } = Dimensions.get('window');

export default function PersonalizationDashboardScreen() {
  const navigation = useNavigation<any>();
  const [loading, setLoading] = useState(false);
  const [engagementProfile, setEngagementProfile] = useState({
    engagement_level: 'high',
    engagement_score: 0.85,
    learning_style: 'visual',
    optimal_session_duration: 25,
    best_engagement_times: ['09:00', '19:00'],
    preferred_content_types: ['learning', 'trading', 'community']
  });

  const [behaviorPatterns, setBehaviorPatterns] = useState([
    {
      id: '1',
      type: 'usage_timing',
      description: 'You typically engage in morning learning sessions',
      frequency: 0.8,
      confidence: 0.9,
      triggers: ['morning_time', 'weekday'],
      predicted_actions: ['morning_notification', 'morning_content']
    },
    {
      id: '2',
      type: 'content_preference',
      description: 'You prefer visual learning with interactive elements',
      frequency: 0.7,
      confidence: 0.85,
      triggers: ['visual_content', 'interactive_elements'],
      predicted_actions: ['visual_content_priority', 'interactive_enhancement']
    },
    {
      id: '3',
      type: 'learning_style',
      description: 'You learn best through hands-on practice and examples',
      frequency: 0.9,
      confidence: 0.95,
      triggers: ['practical_examples', 'hands_on_practice'],
      predicted_actions: ['practical_content', 'example_heavy_modules']
    }
  ]);

  const [contentRecommendations, setContentRecommendations] = useState([
    {
      id: '1',
      type: 'learning_module',
      title: 'Advanced Options Strategies',
      description: 'Perfect for your visual learning style and current skill level',
      relevance_score: 0.92,
      confidence: 0.88,
      reasoning: 'Matches your learning patterns and interests'
    },
    {
      id: '2',
      type: 'trading_signal',
      title: 'Tech Sector Analysis',
      description: 'Based on your trading history and market preferences',
      relevance_score: 0.87,
      confidence: 0.82,
      reasoning: 'Aligns with your trading behavior patterns'
    },
    {
      id: '3',
      type: 'community_post',
      title: 'BIPOC Investment Strategies Discussion',
      description: 'Active community discussion matching your interests',
      relevance_score: 0.79,
      confidence: 0.75,
      reasoning: 'Based on your community engagement patterns'
    }
  ]);

  const [churnPrediction, setChurnPrediction] = useState({
    churn_risk: 'low',
    churn_probability: 0.15,
    risk_factors: [],
    intervention_recommendations: ['Continue current engagement'],
    confidence: 0.85
  });

  const getEngagementColor = (level: string) => {
    switch (level) {
      case 'very_high': return '#10B981';
      case 'high': return '#3B82F6';
      case 'medium': return '#F59E0B';
      case 'low': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getChurnColor = (risk: string) => {
    switch (risk) {
      case 'low': return '#10B981';
      case 'medium': return '#F59E0B';
      case 'high': return '#EF4444';
      case 'critical': return '#DC2626';
      default: return '#6B7280';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10B981';
    if (confidence >= 0.6) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={['#8B5CF6', '#7C3AED']}
        style={styles.headerGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.headerContent}>
          <Ionicons name="analytics" size={32} color="#fff" />
          <Text style={styles.headerTitle}>Personalization Dashboard</Text>
          <Text style={styles.headerSubtitle}>Your AI-powered learning profile</Text>
        </View>
      </LinearGradient>

      {/* Engagement Profile */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📊 Engagement Profile</Text>
        <View style={styles.profileCard}>
          <View style={styles.profileRow}>
            <Text style={styles.profileLabel}>Engagement Level</Text>
            <View style={[styles.badge, { backgroundColor: getEngagementColor(engagementProfile.engagement_level) }]}>
              <Text style={styles.badgeText}>{engagementProfile.engagement_level.toUpperCase()}</Text>
            </View>
          </View>
          <View style={styles.profileRow}>
            <Text style={styles.profileLabel}>Engagement Score</Text>
            <Text style={styles.profileValue}>{(engagementProfile.engagement_score * 100).toFixed(0)}%</Text>
          </View>
          <View style={styles.profileRow}>
            <Text style={styles.profileLabel}>Learning Style</Text>
            <Text style={styles.profileValue}>{engagementProfile.learning_style}</Text>
          </View>
          <View style={styles.profileRow}>
            <Text style={styles.profileLabel}>Optimal Session</Text>
            <Text style={styles.profileValue}>{engagementProfile.optimal_session_duration} min</Text>
          </View>
          <View style={styles.profileRow}>
            <Text style={styles.profileLabel}>Best Times</Text>
            <Text style={styles.profileValue}>{engagementProfile.best_engagement_times.join(', ')}</Text>
          </View>
        </View>
      </View>

      {/* Behavior Patterns */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🔍 Behavior Patterns</Text>
        {behaviorPatterns.map((pattern) => (
          <View key={pattern.id} style={styles.patternCard}>
            <View style={styles.patternHeader}>
              <Text style={styles.patternType}>{pattern.type.replace('_', ' ').toUpperCase()}</Text>
              <View style={[styles.confidenceBadge, { backgroundColor: getConfidenceColor(pattern.confidence) }]}>
                <Text style={styles.confidenceText}>{(pattern.confidence * 100).toFixed(0)}%</Text>
              </View>
            </View>
            <Text style={styles.patternDescription}>{pattern.description}</Text>
            <View style={styles.patternMeta}>
              <Text style={styles.patternFrequency}>Frequency: {(pattern.frequency * 100).toFixed(0)}%</Text>
              <Text style={styles.patternTriggers}>Triggers: {pattern.triggers.join(', ')}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Content Recommendations */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🎯 Personalized Recommendations</Text>
        {contentRecommendations.map((rec) => (
          <TouchableOpacity key={rec.id} style={styles.recommendationCard}>
            <View style={styles.recommendationHeader}>
              <View style={styles.recommendationIcon}>
                <Ionicons 
                  name={
                    rec.type === 'learning_module' ? 'book' :
                    rec.type === 'trading_signal' ? 'trending-up' :
                    rec.type === 'community_post' ? 'people' : 'star'
                  } 
                  size={20} 
                  color="#8B5CF6" 
                />
              </View>
              <View style={styles.recommendationInfo}>
                <Text style={styles.recommendationTitle}>{rec.title}</Text>
                <Text style={styles.recommendationDescription}>{rec.description}</Text>
              </View>
              <View style={[styles.relevanceBadge, { backgroundColor: getConfidenceColor(rec.relevance_score) }]}>
                <Text style={styles.relevanceText}>{(rec.relevance_score * 100).toFixed(0)}%</Text>
              </View>
            </View>
            <Text style={styles.recommendationReasoning}>{rec.reasoning}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Churn Prediction */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>⚠️ Retention Analysis</Text>
        <View style={styles.churnCard}>
          <View style={styles.churnHeader}>
            <Text style={styles.churnLabel}>Churn Risk</Text>
            <View style={[styles.churnBadge, { backgroundColor: getChurnColor(churnPrediction.churn_risk) }]}>
              <Text style={styles.churnBadgeText}>{churnPrediction.churn_risk.toUpperCase()}</Text>
            </View>
          </View>
          <View style={styles.churnRow}>
            <Text style={styles.churnLabel}>Probability</Text>
            <Text style={styles.churnValue}>{(churnPrediction.churn_probability * 100).toFixed(1)}%</Text>
          </View>
          <View style={styles.churnRow}>
            <Text style={styles.churnLabel}>Confidence</Text>
            <Text style={styles.churnValue}>{(churnPrediction.confidence * 100).toFixed(0)}%</Text>
          </View>
          {churnPrediction.intervention_recommendations.length > 0 && (
            <View style={styles.interventionSection}>
              <Text style={styles.interventionTitle}>Recommendations:</Text>
              {churnPrediction.intervention_recommendations.map((rec, index) => (
                <Text key={index} style={styles.interventionText}>• {rec}</Text>
              ))}
            </View>
          )}
        </View>
      </View>

      {/* Personalization Settings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>⚙️ Personalization Settings</Text>
        <View style={styles.settingsCard}>
          <TouchableOpacity 
            style={styles.settingItem}
            onPress={() => navigation.navigate('notification-center')}
          >
            <Ionicons name="notifications" size={24} color="#8B5CF6" />
            <Text style={styles.settingText}>Smart Notifications</Text>
            <Ionicons name="chevron-forward" size={20} color="#8E8E93" />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.settingItem}
            onPress={() => navigation.navigate('dynamic-content')}
          >
            <Ionicons name="refresh" size={24} color="#8B5CF6" />
            <Text style={styles.settingText}>Content Adaptation</Text>
            <Ionicons name="chevron-forward" size={20} color="#8E8E93" />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.settingItem}
            onPress={() => navigation.navigate('behavioral-analytics')}
          >
            <Ionicons name="analytics" size={24} color="#8B5CF6" />
            <Text style={styles.settingText}>Behavior Tracking</Text>
            <Ionicons name="chevron-forward" size={20} color="#8E8E93" />
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#f8f9fa' 
  },
  headerGradient: {
    paddingVertical: 30,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
    marginBottom: 20,
    alignItems: 'center',
  },
  headerContent: {
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#fff',
    marginTop: 10,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#e0e0ff',
    marginTop: 5,
    textAlign: 'center',
  },
  
  section: {
    marginBottom: 24,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    color: '#1f2937',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12,
  },
  
  profileCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  profileRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  profileLabel: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
  },
  profileValue: {
    fontSize: 16,
    color: '#1f2937',
    fontWeight: '600',
  },
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
  
  patternCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  patternHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  patternType: {
    fontSize: 14,
    fontWeight: '700',
    color: '#8B5CF6',
  },
  confidenceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  confidenceText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  patternDescription: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
    marginBottom: 8,
  },
  patternMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  patternFrequency: {
    fontSize: 12,
    color: '#6B7280',
  },
  patternTriggers: {
    fontSize: 12,
    color: '#6B7280',
  },
  
  recommendationCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  recommendationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  recommendationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  recommendationInfo: {
    flex: 1,
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 4,
  },
  recommendationDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 18,
  },
  relevanceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  relevanceText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  recommendationReasoning: {
    fontSize: 12,
    color: '#8B5CF6',
    fontStyle: 'italic',
  },
  
  churnCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  churnHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  churnLabel: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
  },
  churnValue: {
    fontSize: 16,
    color: '#1f2937',
    fontWeight: '600',
  },
  churnRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  churnBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  churnBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
  interventionSection: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
  },
  interventionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  interventionText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  
  settingsCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  settingText: {
    flex: 1,
    fontSize: 16,
    color: '#374151',
    marginLeft: 12,
  },
});
