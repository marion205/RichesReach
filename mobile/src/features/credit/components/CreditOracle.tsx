/**
 * Predictive Credit Oracle - Crowdsourced Insights with Bias Detection (Enhanced UI 2025)
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { CreditOracle as CreditOracleType, OracleInsight } from '../types/CreditTypes';
import { LinearGradient } from 'expo-linear-gradient';

interface CreditOracleProps {
  oracle: CreditOracleType;
  onInsightPress?: (insight: OracleInsight) => void;
}

export const CreditOracle: React.FC<CreditOracleProps> = ({
  oracle,
  onInsightPress,
}) => {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'trend': return 'trending-up';
      case 'warning': return 'alert-triangle';
      case 'opportunity': return 'zap';
      case 'local': return 'map-pin';
      default: return 'info';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'trend': return '#5AC8FA';
      case 'warning': return '#FF6B6B';
      case 'opportunity': return '#34C759';
      case 'local': return '#AF52DE';
      default: return '#007AFF';
    }
  };

  const getSectionColor = (section: string) => {
    if (section.includes('Warnings')) return '#FF6B6B';
    if (section.includes('Opportunities')) return '#34C759';
    if (section.includes('Local')) return '#AF52DE';
    return '#007AFF';
  };

  const getConfidenceGradient = (confidence: number): [string, string] => {
    if (confidence >= 0.8) return ['#34C759', '#2E9E4B'];
    if (confidence >= 0.6) return ['#FF9500', '#D87A00'];
    return ['#FF3B30', '#D63028'];
  };

  const renderInsight = (insight: OracleInsight, sectionColor: string) => (
    <TouchableOpacity
      key={insight.id}
      style={styles.insightCard}
      onPress={() => onInsightPress?.(insight)}
      activeOpacity={0.8}
    >
      <LinearGradient
        colors={['rgba(255,255,255,0.95)', 'rgba(255,255,255,0.85)']}
        style={StyleSheet.absoluteFill}
      />
      <View style={styles.insightHeader}>
        <View style={[styles.insightIcon, { backgroundColor: getTypeColor(insight.type) + '25' }]}>
          <Icon name={getTypeIcon(insight.type)} size={24} color={getTypeColor(insight.type)} />
        </View>
        <View style={styles.insightContent}>
          <View style={styles.insightTitleRow}>
            <Text style={styles.insightTitle}>{insight.title}</Text>
            {insight.location && (
              <View style={[styles.locationBadge, { borderColor: sectionColor + '50' }]}>
                <Icon name="map-pin" size={12} color={sectionColor} />
                <Text style={[styles.locationText, { color: sectionColor }]}>{insight.location}</Text>
              </View>
            )}
          </View>
          <Text style={styles.insightDescription}>{insight.description}</Text>
          <View style={styles.insightMeta}>
            <View style={styles.confidenceBox}>
              <Text style={styles.confidenceLabel}>Confidence</Text>
              <View style={styles.confidenceBarContainer}>
                <View style={styles.confidenceBar}>
                  <LinearGradient
                    colors={getConfidenceGradient(insight.confidence)}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={[
                      styles.confidenceFill,
                      { width: `${insight.confidence * 100}%` },
                    ]}
                  />
                </View>
                <Text style={[styles.confidenceValue, { color: getConfidenceGradient(insight.confidence)[0] }]}>
                  {Math.round(insight.confidence * 100)}%
                </Text>
              </View>
            </View>
            <Text style={styles.timeHorizon}>{insight.timeHorizon}</Text>
          </View>
          {insight.biasCheck && insight.biasCheck.detected && (
            <LinearGradient
              colors={['#E3F2FD', '#D1E9FF']}
              style={styles.biasBox}
            >
              <Icon name="shield-check" size={16} color="#007AFF" />
              <Text style={styles.biasText}>
                {insight.biasCheck.adjusted ? 'Bias Detected & Adjusted' : 'Bias Detected'}
              </Text>
            </LinearGradient>
          )}
          <LinearGradient
            colors={['#FFF8E1', '#FFEFD5']}
            style={styles.recommendationBox}
          >
            <Icon name="star" size={16} color="#FFB800" />
            <Text style={styles.recommendationText}>{insight.recommendation}</Text>
          </LinearGradient>
        </View>
      </View>
    </TouchableOpacity>
  );

  const renderSection = (title: string, emoji: string, insights: OracleInsight[]) => {
    if (insights.length === 0) return null;

    const color = getSectionColor(title);
    return (
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionEmoji}>{emoji}</Text>
          <Text style={[styles.sectionTitle, { color }]}>{title}</Text>
        </View>
        {insights.map((insight) => renderInsight(insight, color))}
      </View>
    );
  };

  return (
    <ScrollView contentContainerStyle={styles.scrollContainer}>
      <View style={styles.container}>
        <LinearGradient
          colors={['#FFFFFF', '#F0F4F8']}
          style={styles.headerGradient}
        >
          <View style={styles.header}>
            <View style={styles.titleContainer}>
              <Text style={styles.title}>Credit Oracle</Text>
              <Text style={styles.subtitle}>AI-Powered Predictive Insights from Collective Intelligence</Text>
            </View>
            <Icon name="eye" size={32} color="#007AFF" /> {/* Oracle "vision" icon */}
          </View>
          <View style={styles.lastUpdatedBox}>
            <Text style={styles.lastUpdatedLabel}>Last Updated</Text>
            <Text style={styles.lastUpdatedTime}>
              {new Date(oracle.lastUpdated).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </Text>
          </View>
        </LinearGradient>

        {renderSection('Warnings', '⚠️', oracle.warnings)}
        {renderSection('Opportunities', '✨', oracle.opportunities)}
        {renderSection('Local Trends', '📍', oracle.localTrends)}
        {renderSection('Insights', '💡', oracle.insights)}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  scrollContainer: {
    flexGrow: 1,
    backgroundColor: '#F0F4F8',
    padding: 16,
  },
  container: {
    backgroundColor: 'transparent',
    borderRadius: 24,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 8,
  },
  headerGradient: {
    padding: 24,
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  titleContainer: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B6B6B',
    lineHeight: 20,
  },
  lastUpdatedBox: {
    alignItems: 'flex-end',
    marginTop: 16,
    paddingHorizontal: 24,
  },
  lastUpdatedLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  lastUpdatedTime: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  section: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionEmoji: {
    fontSize: 20,
    marginRight: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
  },
  insightCard: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    backgroundColor: 'rgba(255,255,255,0.5)', // For glassmorphism base
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 4,
    borderWidth: 0.5,
    borderColor: 'rgba(255,255,255,0.8)',
    overflow: 'hidden',
  },
  insightHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    width: '100%',
  },
  insightIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    flexShrink: 0,
  },
  insightContent: {
    flex: 1,
    minWidth: 0, // Allows flex to shrink properly
  },
  insightTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  insightTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A1A',
    flex: 1,
    flexShrink: 1,
  },
  locationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'transparent',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
  },
  locationText: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
  },
  insightDescription: {
    fontSize: 14,
    color: '#6B6B6B',
    lineHeight: 20,
    marginBottom: 12,
  },
  insightMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  confidenceBox: {
    flex: 1,
  },
  confidenceLabel: {
    fontSize: 12,
    color: '#8E8E93',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  confidenceBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  confidenceBar: {
    flex: 1,
    height: 6,
    backgroundColor: '#E0E0E0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    borderRadius: 3,
  },
  confidenceValue: {
    fontSize: 14,
    fontWeight: 'bold',
    minWidth: 40,
    textAlign: 'right',
  },
  timeHorizon: {
    fontSize: 13,
    color: '#6B6B6B',
    fontWeight: '500',
  },
  biasBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 10,
    borderRadius: 12,
    marginBottom: 12,
  },
  biasText: {
    fontSize: 13,
    color: '#007AFF',
    fontWeight: '600',
  },
  recommendationBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    padding: 12,
    borderRadius: 12,
  },
  recommendationText: {
    flex: 1,
    fontSize: 14,
    color: '#1A1A1A',
    lineHeight: 20,
  },
});
