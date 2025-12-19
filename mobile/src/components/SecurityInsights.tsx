/**
 * Security Insights Component
 * Displays AI-powered security insights, recommendations, and gamification
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from 'react-native-vector-icons/Feather';
import { SECURITY_INSIGHTS } from '../graphql/queries_corrected';
import { useAuth } from '../contexts/AuthContext';

interface SecurityInsight {
  securityScore: number;
  strengths: string[];
  recommendations: Array<{
    priority: 'high' | 'medium' | 'low';
    action: string;
    impact: string;
  }>;
  trend: 'improving' | 'stable' | 'declining';
  badges: string[];
}

export const SecurityInsights: React.FC = () => {
  const { user } = useAuth();
  const [insights, setInsights] = useState<SecurityInsight | null>(null);
  
  const { data, loading, error, refetch } = useQuery(SECURITY_INSIGHTS, {
    skip: !user?.id,
    fetchPolicy: 'cache-and-network',
  });

  useEffect(() => {
    if (data) {
      // Calculate insights from data
      const score = data.securityScore?.score || 0;
      const recentEvents = data.securityEvents || [];
      const zeroTrust = data.zeroTrustSummary;
      
      // Generate insights
      const calculatedInsights: SecurityInsight = {
        securityScore: score,
        strengths: [],
        recommendations: [],
        trend: 'stable',
        badges: [],
      };

      // Strengths
      if (score >= 80) {
        calculatedInsights.strengths.push('Excellent security score');
        calculatedInsights.badges.push('Security Champion');
      }
      if (recentEvents.length === 0) {
        calculatedInsights.strengths.push('No unresolved security events');
        calculatedInsights.badges.push('Fortress Master');
      }
      if (zeroTrust?.averageTrustScore >= 80) {
        calculatedInsights.strengths.push('High device trust');
        calculatedInsights.badges.push('Zero Trust Hero');
      }

      // Recommendations
      if (score < 70) {
        calculatedInsights.recommendations.push({
          priority: 'high',
          action: 'Enable biometric authentication',
          impact: 'Improve security score by 10 points',
        });
      }
      if (recentEvents.length > 0) {
        calculatedInsights.recommendations.push({
          priority: 'high',
          action: `Resolve ${recentEvents.length} security event(s)`,
          impact: 'Improve security score by 5 points per event',
        });
      }
      if (zeroTrust?.requiresMfa) {
        calculatedInsights.recommendations.push({
          priority: 'medium',
          action: 'Enable MFA for sensitive actions',
          impact: 'Increase account security',
        });
      }

      // Trend (simplified - would use historical data in production)
      if (score >= 80) {
        calculatedInsights.trend = 'improving';
      } else if (score < 60) {
        calculatedInsights.trend = 'declining';
      }

      setInsights(calculatedInsights);
    }
  }, [data]);

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4A90E2" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Error loading security insights</Text>
      </View>
    );
  }

  if (!insights) {
    return null;
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#4CAF50';
    if (score >= 60) return '#FF9800';
    return '#F44336';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'trending-up';
      case 'declining':
        return 'trending-down';
      default:
        return 'minus';
    }
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Security Score Card */}
      <LinearGradient
        colors={['#4A90E2', '#357ABD']}
        style={styles.scoreCard}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.scoreHeader}>
          <Text style={styles.scoreLabel}>Security Score</Text>
          <View style={styles.trendContainer}>
            <Icon
              name={getTrendIcon(insights.trend)}
              size={20}
              color="#FFF"
              style={styles.trendIcon}
            />
            <Text style={styles.trendText}>
              {insights.trend.charAt(0).toUpperCase() + insights.trend.slice(1)}
            </Text>
          </View>
        </View>
        <View style={styles.scoreValueContainer}>
          <Text style={[styles.scoreValue, { color: getScoreColor(insights.securityScore) }]}>
            {insights.securityScore}
          </Text>
          <Text style={styles.scoreMax}>/100</Text>
        </View>
        <View style={styles.scoreBar}>
          <View
            style={[
              styles.scoreBarFill,
              {
                width: `${insights.securityScore}%`,
                backgroundColor: getScoreColor(insights.securityScore),
              },
            ]}
          />
        </View>
      </LinearGradient>

      {/* Badges Section */}
      {insights.badges.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🏆 Achievements</Text>
          <View style={styles.badgesContainer}>
            {insights.badges.map((badge, index) => (
              <View key={index} style={styles.badge}>
                <Icon name="award" size={24} color="#FFD700" />
                <Text style={styles.badgeText}>{badge}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Strengths Section */}
      {insights.strengths.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>✅ Strengths</Text>
          {insights.strengths.map((strength, index) => (
            <View key={index} style={styles.strengthItem}>
              <Icon name="check-circle" size={20} color="#4CAF50" />
              <Text style={styles.strengthText}>{strength}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Recommendations Section */}
      {insights.recommendations.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>💡 Recommendations</Text>
          {insights.recommendations.map((rec, index) => (
            <View
              key={index}
              style={[
                styles.recommendationItem,
                rec.priority === 'high' && styles.recommendationHigh,
              ]}
            >
              <View style={styles.recommendationHeader}>
                <Icon
                  name={rec.priority === 'high' ? 'alert-circle' : 'info'}
                  size={20}
                  color={rec.priority === 'high' ? '#F44336' : '#FF9800'}
                />
                <Text style={styles.recommendationPriority}>
                  {rec.priority.toUpperCase()} PRIORITY
                </Text>
              </View>
              <Text style={styles.recommendationAction}>{rec.action}</Text>
              <Text style={styles.recommendationImpact}>{rec.impact}</Text>
            </View>
          ))}
        </View>
      )}

      {/* AI Insights Footer */}
      <View style={styles.aiFooter}>
        <Icon name="cpu" size={16} color="#4A90E2" />
        <Text style={styles.aiFooterText}>
          Insights powered by AI security analysis
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    paddingTop: 16,
  },
  scoreCard: {
    margin: 16,
    padding: 24,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  scoreHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  scoreLabel: {
    fontSize: 16,
    color: '#FFF',
    fontWeight: '600',
  },
  trendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  trendIcon: {
    marginRight: 4,
  },
  trendText: {
    fontSize: 14,
    color: '#FFF',
    fontWeight: '500',
  },
  scoreValueContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 12,
  },
  scoreValue: {
    fontSize: 64,
    fontWeight: 'bold',
    color: '#FFF',
  },
  scoreMax: {
    fontSize: 24,
    color: '#FFF',
    opacity: 0.8,
    marginLeft: 8,
  },
  scoreBar: {
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  scoreBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  section: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: '#FFF',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    color: '#333',
  },
  badgesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF9E6',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FFD700',
  },
  badgeText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  strengthItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  strengthText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#333',
  },
  recommendationItem: {
    backgroundColor: '#FFF9E6',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
  },
  recommendationHigh: {
    backgroundColor: '#FFEBEE',
    borderLeftColor: '#F44336',
  },
  recommendationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  recommendationPriority: {
    marginLeft: 8,
    fontSize: 12,
    fontWeight: '600',
    color: '#F44336',
  },
  recommendationAction: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  recommendationImpact: {
    fontSize: 12,
    color: '#666',
  },
  aiFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    marginBottom: 16,
  },
  aiFooterText: {
    marginLeft: 8,
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  errorText: {
    color: '#F44336',
    textAlign: 'center',
    margin: 16,
  },
});

