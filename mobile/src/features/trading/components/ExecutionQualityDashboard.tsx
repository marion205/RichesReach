import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const GET_EXECUTION_QUALITY_STATS = gql`
  query GetExecutionQualityStats($signalType: String!, $days: Int!) {
    executionQualityStats(signalType: $signalType, days: $days) {
      avgSlippagePct
      avgQualityScore
      chasedCount
      totalFills
      improvementTips
      periodDays
    }
  }
`;

interface ExecutionQualityStats {
  avgSlippagePct: number;
  avgQualityScore: number;
  chasedCount: number;
  totalFills: number;
  improvementTips: string[];
  periodDays: number;
}

interface ExecutionQualityDashboardProps {
  signalType?: 'day_trading' | 'swing_trading';
  days?: number;
}

const C = {
  bg: '#0A0A0A',
  card: '#1A1A1A',
  text: '#FFFFFF',
  sub: '#888888',
  primary: '#00D4FF',
  success: '#00FF88',
  danger: '#FF4444',
  warning: '#FFAA00',
};

export default function ExecutionQualityDashboard({ 
  signalType = 'day_trading', 
  days = 30 
}: ExecutionQualityDashboardProps) {
  const { data, loading, error, refetch } = useQuery<{ executionQualityStats: ExecutionQualityStats }>(
    GET_EXECUTION_QUALITY_STATS,
    {
      variables: { signalType, days },
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    }
  );

  const stats = data?.executionQualityStats;

  // Mock data fallback for development when backend is unavailable
  const getMockStats = (): ExecutionQualityStats => ({
    avgSlippagePct: 0.18, // Good slippage
    avgQualityScore: 7.5, // Good quality
    chasedCount: 3,
    totalFills: 24,
    improvementTips: [
      'Consider using limit orders to reduce slippage',
      'Avoid chasing price movements - wait for pullbacks',
      'Your execution quality is improving - keep it up!',
    ],
    periodDays: days,
  });

  // Use mock data if there's an error or no data (for development)
  const effectiveStats = stats || (error ? getMockStats() : null);

  if (loading && !effectiveStats) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={C.primary} />
      </View>
    );
  }

  if (!effectiveStats) {
    return (
      <View style={styles.container}>
        <Text style={[styles.emptyText, { color: C.sub }]}>
          No execution data available yet. Start trading to see your execution quality metrics.
        </Text>
      </View>
    );
  }

  const qualityColor = effectiveStats.avgQualityScore >= 8 ? C.success : 
                       effectiveStats.avgQualityScore >= 6 ? C.warning : C.danger;
  
  // Show warning banner if using mock data
  const isUsingMockData = !stats && error;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Mock Data Warning Banner */}
      {isUsingMockData && (
        <View style={[styles.mockBanner, { backgroundColor: C.warning + '20', borderLeftColor: C.warning }]}>
          <Icon name="alert-triangle" size={16} color={C.warning} />
          <Text style={[styles.mockBannerText, { color: C.warning }]}>
            Using mock data - Backend unavailable
          </Text>
        </View>
      )}

      {/* Header */}
      <View style={styles.header}>
        <Icon name="activity" size={24} color={C.primary} />
        <Text style={[styles.title, { color: C.text }]}>Execution Quality</Text>
        <TouchableOpacity onPress={() => refetch()}>
          <Icon name="refresh-cw" size={20} color={C.primary} />
        </TouchableOpacity>
      </View>

      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        {/* Average Slippage */}
        <View style={[styles.statCard, { backgroundColor: C.card }]}>
          <View style={styles.statHeader}>
            <Icon name="trending-down" size={18} color={C.warning} />
            <Text style={[styles.statLabel, { color: C.sub }]}>Avg Slippage</Text>
          </View>
          <Text style={[styles.statValue, { color: C.text }]}>
            {effectiveStats.avgSlippagePct.toFixed(2)}%
          </Text>
          <Text style={[styles.statSubtext, { color: C.sub }]}>
            {effectiveStats.avgSlippagePct < 0.2 ? 'Excellent' : 
             effectiveStats.avgSlippagePct < 0.5 ? 'Good' : 'Needs Improvement'}
          </Text>
        </View>

        {/* Quality Score */}
        <View style={[styles.statCard, { backgroundColor: C.card }]}>
          <View style={styles.statHeader}>
            <Icon name="star" size={18} color={qualityColor} />
            <Text style={[styles.statLabel, { color: C.sub }]}>Quality Score</Text>
          </View>
          <Text style={[styles.statValue, { color: qualityColor }]}>
            {effectiveStats.avgQualityScore.toFixed(1)}/10
          </Text>
          <Text style={[styles.statSubtext, { color: C.sub }]}>
            {effectiveStats.avgQualityScore >= 8 ? 'Excellent' : 
             effectiveStats.avgQualityScore >= 6 ? 'Good' : 'Needs Work'}
          </Text>
        </View>

        {/* Chased Count */}
        <View style={[styles.statCard, { backgroundColor: C.card }]}>
          <View style={styles.statHeader}>
            <Icon name="alert-triangle" size={18} color={C.danger} />
            <Text style={[styles.statLabel, { color: C.sub }]}>Price Chased</Text>
          </View>
          <Text style={[styles.statValue, { color: C.danger }]}>
            {effectiveStats.chasedCount}
          </Text>
          <Text style={[styles.statSubtext, { color: C.sub }]}>
            {effectiveStats.totalFills > 0 
              ? `${((effectiveStats.chasedCount / effectiveStats.totalFills) * 100).toFixed(0)}% of trades`
              : 'No data'}
          </Text>
        </View>

        {/* Total Fills */}
        <View style={[styles.statCard, { backgroundColor: C.card }]}>
          <View style={styles.statHeader}>
            <Icon name="check-circle" size={18} color={C.success} />
            <Text style={[styles.statLabel, { color: C.sub }]}>Total Fills</Text>
          </View>
          <Text style={[styles.statValue, { color: C.text }]}>
            {effectiveStats.totalFills}
          </Text>
          <Text style={[styles.statSubtext, { color: C.sub }]}>
            Last {effectiveStats.periodDays} days
          </Text>
        </View>
      </View>

      {/* Improvement Tips */}
      {effectiveStats.improvementTips && effectiveStats.improvementTips.length > 0 && (
        <View style={[styles.tipsCard, { backgroundColor: C.card }]}>
          <View style={styles.tipsHeader}>
            <Icon name="lightbulb" size={20} color={C.primary} />
            <Text style={[styles.tipsTitle, { color: C.text }]}>Coaching Tips</Text>
          </View>
          {effectiveStats.improvementTips.map((tip, index) => (
            <View key={index} style={styles.tipItem}>
              <Icon name="chevron-right" size={16} color={C.primary} />
              <Text style={[styles.tipText, { color: C.sub }]}>{tip}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Period Selector */}
      <View style={styles.periodSelector}>
        {[7, 30, 90, 365].map((period) => (
          <TouchableOpacity
            key={period}
            style={[
              styles.periodButton,
              { backgroundColor: days === period ? C.primary : C.card },
            ]}
            onPress={() => refetch({ days: period })}
          >
            <Text
              style={[
                styles.periodText,
                { color: days === period ? C.text : C.sub },
              ]}
            >
              {period === 7 ? '7D' : period === 30 ? '30D' : period === 90 ? '90D' : '1Y'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: C.bg,
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    flex: 1,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    minWidth: '47%',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2A2A2A',
  },
  statHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  statSubtext: {
    fontSize: 11,
  },
  tipsCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2A2A2A',
    marginBottom: 20,
  },
  tipsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 8,
  },
  tipText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
  periodSelector: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  periodButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  periodText: {
    fontSize: 13,
    fontWeight: '600',
  },
  card: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
    alignItems: 'center',
    gap: 8,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: C.primary,
    borderRadius: 6,
  },
  retryText: {
    color: C.text,
    fontSize: 13,
    fontWeight: '600',
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    padding: 20,
  },
  mockBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    borderLeftWidth: 4,
  },
  mockBannerText: {
    fontSize: 12,
    fontWeight: '600',
    flex: 1,
  },
});

