/**
 * Predictive Credit Oracle - Crowdsourced Insights with Bias Detection
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { CreditOracle as CreditOracleType, OracleInsight } from '../types/CreditTypes';

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
      case 'warning': return '#FF9500';
      case 'opportunity': return '#34C759';
      case 'local': return '#AF52DE';
      default: return '#8E8E93';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#34C759';
    if (confidence >= 0.6) return '#FF9500';
    return '#FF3B30';
  };

  const renderInsight = (insight: OracleInsight) => (
    <TouchableOpacity
      key={insight.id}
      style={styles.insightCard}
      onPress={() => onInsightPress?.(insight)}
      activeOpacity={0.7}
    >
      <View style={styles.insightHeader}>
        <View style={[styles.insightIcon, { backgroundColor: getTypeColor(insight.type) + '20' }]}>
          <Icon name={getTypeIcon(insight.type)} size={20} color={getTypeColor(insight.type)} />
        </View>
        <View style={styles.insightContent}>
          <View style={styles.insightTitleRow}>
            <Text style={styles.insightTitle}>{insight.title}</Text>
            {insight.location && (
              <View style={styles.locationBadge}>
                <Icon name="map-pin" size={10} color="#8E8E93" />
                <Text style={styles.locationText}>{insight.location}</Text>
              </View>
            )}
          </View>
          <Text style={styles.insightDescription}>{insight.description}</Text>
          <View style={styles.insightMeta}>
            <View style={styles.confidenceBox}>
              <Text style={styles.confidenceLabel}>CONFIDENCE</Text>
              <View style={styles.confidenceBarContainer}>
                <View style={styles.confidenceBar}>
                  <View 
                    style={[
                      styles.confidenceFill,
                      { 
                        width: `${insight.confidence * 100}%`,
                        backgroundColor: getConfidenceColor(insight.confidence)
                      }
                    ]} 
                  />
                </View>
                <Text style={[styles.confidenceValue, { color: getConfidenceColor(insight.confidence) }]}>
                  {Math.round(insight.confidence * 100)}%
                </Text>
              </View>
            </View>
            <Text style={styles.timeHorizon}>{insight.timeHorizon}</Text>
          </View>
          {insight.biasCheck && insight.biasCheck.detected && (
            <View style={styles.biasBox}>
              <Icon name="shield" size={14} color="#007AFF" />
              <Text style={styles.biasText}>
                {insight.biasCheck.adjusted ? 'Bias detected & adjusted' : 'Bias detected'}
              </Text>
            </View>
          )}
          <View style={styles.recommendationBox}>
            <Icon name="help-circle" size={14} color="#FFD700" />
            <Text style={styles.recommendationText}>{insight.recommendation}</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Text style={styles.title}>Credit Oracle</Text>
          <Text style={styles.subtitle}>
            Predictive insights powered by collective intelligence
          </Text>
        </View>
        <View style={styles.lastUpdatedBox}>
          <Text style={styles.lastUpdatedLabel}>Updated</Text>
          <Text style={styles.lastUpdatedTime} numberOfLines={1}>
            {new Date(oracle.lastUpdated).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </Text>
        </View>
      </View>

      {/* Warnings */}
      {oracle.warnings.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚠️ Warnings</Text>
          {oracle.warnings.map(renderInsight)}
        </View>
      )}

      {/* Opportunities */}
      {oracle.opportunities.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>✨ Opportunities</Text>
          {oracle.opportunities.map(renderInsight)}
        </View>
      )}

      {/* Local Trends */}
      {oracle.localTrends.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📍 Local Trends</Text>
          {oracle.localTrends.map(renderInsight)}
        </View>
      )}

      {/* General Insights */}
      {oracle.insights.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>💡 Insights</Text>
          {oracle.insights.map(renderInsight)}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 20,
  },
  titleContainer: {
    flex: 1,
    marginRight: 16,
    paddingRight: 0,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    color: '#8E8E93',
  },
  lastUpdatedBox: {
    alignItems: 'flex-end',
    flexShrink: 0,
    minWidth: 60,
  },
  lastUpdatedLabel: {
    fontSize: 10,
    color: '#8E8E93',
    marginBottom: 2,
  },
  lastUpdatedTime: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1C1C1E',
    textAlign: 'right',
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  insightCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#E5E5EA',
  },
  insightHeader: {
    flexDirection: 'row',
    gap: 12,
  },
  insightIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  insightContent: {
    flex: 1,
  },
  insightTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  insightTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1C1C1E',
    flex: 1,
  },
  locationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  locationText: {
    fontSize: 10,
    color: '#8E8E93',
  },
  insightDescription: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
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
    gap: 6,
  },
  confidenceLabel: {
    fontSize: 10,
    color: '#8E8E93',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  confidenceBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  confidenceBar: {
    flex: 1,
    height: 4,
    backgroundColor: '#E5E5EA',
    borderRadius: 2,
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    borderRadius: 2,
  },
  confidenceValue: {
    fontSize: 12,
    fontWeight: '700',
    minWidth: 40,
    textAlign: 'right',
  },
  timeHorizon: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '600',
  },
  biasBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#E3F2FD',
    padding: 8,
    borderRadius: 6,
    marginBottom: 8,
  },
  biasText: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '600',
  },
  recommendationBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#FFF8E1',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#FFD700',
    marginTop: 8,
  },
  recommendationText: {
    flex: 1,
    fontSize: 13,
    color: '#1C1C1E',
    lineHeight: 18,
  },
});

