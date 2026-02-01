/**
 * Transparency Dashboard Card
 * Public-facing dashboard showing last 50 signals with actual results.
 * Builds institutional-grade trust through transparency.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const TRANSPARENCY_DASHBOARD_QUERY = gql`
  query TransparencyDashboard($limit: Int) {
    transparencyDashboard(limit: $limit) {
      signals {
        id
        symbol
        action
        confidence
        entryPrice
        entryTimestamp
        exitPrice
        exitTimestamp
        pnl
        pnlPercent
        status
        reasoning
        tradingMode
        signalId
      }
      statistics {
        totalSignals
        closedSignals
        openSignals
        abstainedSignals
        winRate
        totalWins
        totalLosses
        avgWin
        avgLoss
        totalPnl
        profitFactor
        lastUpdated
      }
    }
  }
`;

const TRANSPARENCY_PERFORMANCE_QUERY = gql`
  query TransparencyPerformance($days: Int) {
    transparencyPerformance(days: $days) {
      periodDays
      totalSignals
      winRate
      totalPnl
      avgPnl
      sharpeRatio
      maxDrawdown
    }
  }
`;

interface TransparencyDashboardCardProps {
  style?: any;
  limit?: number;
}

export default function TransparencyDashboardCard({ style, limit = 50 }: TransparencyDashboardCardProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<30 | 90 | 180>(30);
  const [refreshing, setRefreshing] = useState(false);

  const { data, loading, error, refetch } = useQuery(TRANSPARENCY_DASHBOARD_QUERY, {
    variables: { limit },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const { data: performanceData } = useQuery(TRANSPARENCY_PERFORMANCE_QUERY, {
    variables: { days: selectedPeriod },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const dashboard = data?.transparencyDashboard;
  const performance = performanceData?.transparencyPerformance;
  const statistics = dashboard?.statistics;
  const signals = dashboard?.signals || [];
  
  // Determine trading mode badge (use first signal's mode, or default to PAPER)
  const tradingMode = signals.length > 0 ? (signals[0].tradingMode || 'PAPER') : 'PAPER';

  const formatCurrency = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '$0.00';
    return value >= 0 ? `+$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`;
  };

  const formatPercent = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '0.00%';
    return value >= 0 ? `+${(value * 100).toFixed(2)}%` : `${(value * 100).toFixed(2)}%`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CLOSED':
        return '#10B981'; // Green
      case 'OPEN':
        return '#F59E0B'; // Amber
      case 'ABSTAINED':
        return '#6B7280'; // Gray
      default:
        return '#6B7280';
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY':
        return '#10B981'; // Green
      case 'SELL':
        return '#EF4444'; // Red
      case 'ABSTAIN':
        return '#6B7280'; // Gray
      default:
        return '#6B7280';
    }
  };

  if (loading && !data) {
    return (
      <View style={[styles.container, style]}>
        <View style={styles.header}>
          <Icon name="eye" size={20} color="#1D4ED8" />
          <Text style={styles.title}>Transparency Dashboard</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#1D4ED8" />
          <Text style={styles.loadingText}>Loading performance data...</Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, style]}>
        <View style={styles.header}>
          <Icon name="eye" size={20} color="#1D4ED8" />
          <Text style={styles.title}>Transparency Dashboard</Text>
        </View>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={16} color="#EF4444" />
          <Text style={styles.errorText}>
            {error.graphQLErrors?.[0]?.message || error.networkError?.message || 'Failed to load dashboard'}
          </Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, style]}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Icon name="eye" size={20} color="#1D4ED8" />
        <Text style={styles.title}>Transparency Dashboard</Text>
        <Text style={styles.subtitle}>Public Performance Metrics</Text>
        <View style={styles.badgeContainer}>
          <View style={[
            styles.badge,
            { backgroundColor: tradingMode === 'LIVE' ? '#10B981' : '#F59E0B' }
          ]}>
            <Text style={styles.badgeText}>{tradingMode}</Text>
          </View>
        </View>
      </View>

      {/* Performance Summary */}
      {performance && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Performance Summary</Text>
            <View style={styles.periodSelector}>
              {[30, 90, 180].map((days) => (
                <TouchableOpacity
                  key={days}
                  style={[
                    styles.periodButton,
                    selectedPeriod === days && styles.periodButtonActive,
                  ]}
                  onPress={() => setSelectedPeriod(days as 30 | 90 | 180)}
                >
                  <Text
                    style={[
                      styles.periodButtonText,
                      selectedPeriod === days && styles.periodButtonTextActive,
                    ]}
                  >
                    {days}d
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Win Rate</Text>
              <Text style={[styles.metricValue, { color: '#10B981' }]}>
                {formatPercent(performance.winRate)}
              </Text>
              <Text style={styles.metricSubtext}>
                {performance.totalSignals} signals
              </Text>
            </View>

            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Total P&L</Text>
              <Text
                style={[
                  styles.metricValue,
                  { color: performance.totalPnl >= 0 ? '#10B981' : '#EF4444' },
                ]}
              >
                {formatCurrency(performance.totalPnl)}
              </Text>
              <Text style={styles.metricSubtext}>
                Avg: {formatCurrency(performance.avgPnl)}
              </Text>
            </View>

            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Sharpe Ratio</Text>
              <Text
                style={[
                  styles.metricValue,
                  { color: performance.sharpeRatio > 1 ? '#10B981' : '#EF4444' },
                ]}
              >
                {performance.sharpeRatio?.toFixed(2) || '0.00'}
              </Text>
              <Text style={styles.metricSubtext}>Risk-Adjusted</Text>
            </View>

            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Max Drawdown</Text>
              <Text style={[styles.metricValue, { color: '#EF4444' }]}>
                {formatPercent(performance.maxDrawdown)}
              </Text>
              <Text style={styles.metricSubtext}>Worst Period</Text>
            </View>
          </View>
        </View>
      )}

      {/* Statistics */}
      {statistics && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Overall Statistics</Text>
            <Text style={styles.lastUpdated}>
              Updated: {new Date(statistics.lastUpdated).toLocaleTimeString()}
            </Text>
          </View>

          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Total Signals</Text>
              <Text style={styles.statValue}>{statistics.totalSignals}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Closed</Text>
              <Text style={[styles.statValue, { color: '#10B981' }]}>
                {statistics.closedSignals}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Open</Text>
              <Text style={[styles.statValue, { color: '#F59E0B' }]}>
                {statistics.openSignals}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Abstained</Text>
              <Text style={[styles.statValue, { color: '#6B7280' }]}>
                {statistics.abstainedSignals}
              </Text>
            </View>
          </View>

          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Win Rate</Text>
              <Text style={[styles.statValue, { color: '#10B981' }]}>
                {formatPercent(statistics.winRate)}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Wins</Text>
              <Text style={[styles.statValue, { color: '#10B981' }]}>
                {statistics.totalWins}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Losses</Text>
              <Text style={[styles.statValue, { color: '#EF4444' }]}>
                {statistics.totalLosses}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Profit Factor</Text>
              <Text
                style={[
                  styles.statValue,
                  { color: statistics.profitFactor > 1 ? '#10B981' : '#EF4444' },
                ]}
              >
                {statistics.profitFactor?.toFixed(2) || '0.00'}
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Recent Signals */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Signals</Text>
          <Text style={styles.sectionSubtitle}>Last {signals.length} signals</Text>
        </View>

        {signals.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Icon name="inbox" size={32} color="#9CA3AF" />
            <Text style={styles.emptyText}>No signals recorded yet</Text>
            <Text style={styles.emptySubtext}>
              Signals will appear here as they are generated
            </Text>
          </View>
        ) : (
          signals.map((signal: any) => (
            <View key={signal.id} style={styles.signalCard}>
              <View style={styles.signalHeader}>
                <View style={styles.signalSymbolContainer}>
                  <Text style={styles.signalSymbol}>{signal.symbol}</Text>
                  <View
                    style={[
                      styles.actionBadge,
                      { backgroundColor: getActionColor(signal.action) },
                    ]}
                  >
                    <Text style={styles.actionText}>{signal.action}</Text>
                  </View>
                  <View
                    style={[
                      styles.statusBadge,
                      { backgroundColor: getStatusColor(signal.status) },
                    ]}
                  >
                    <Text style={styles.statusText}>{signal.status}</Text>
                  </View>
                </View>
                <Text style={styles.confidenceText}>
                  {(signal.confidence * 100).toFixed(0)}%
                </Text>
              </View>

              <View style={styles.signalDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Entry:</Text>
                  <Text style={styles.detailValue}>
                    ${signal.entryPrice?.toFixed(2) || 'N/A'}
                  </Text>
                  <Text style={styles.detailLabel}>Exit:</Text>
                  <Text style={styles.detailValue}>
                    ${signal.exitPrice?.toFixed(2) || 'N/A'}
                  </Text>
                </View>

                {signal.pnl !== null && signal.pnl !== undefined && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>P&L:</Text>
                    <Text
                      style={[
                        styles.detailValue,
                        { color: signal.pnl >= 0 ? '#10B981' : '#EF4444' },
                      ]}
                    >
                      {formatCurrency(signal.pnl)} ({formatPercent(signal.pnlPercent)})
                    </Text>
                  </View>
                )}

                {signal.reasoning && (
                  <View style={styles.reasoningContainer}>
                    <Text style={styles.reasoningLabel}>Reasoning:</Text>
                    <Text style={styles.reasoningText}>{signal.reasoning}</Text>
                  </View>
                )}

                <Text style={styles.timestamp}>
                  {new Date(signal.entryTimestamp).toLocaleString()}
                </Text>
              </View>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}

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
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginLeft: 8,
    flex: 1,
  },
  subtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 8,
  },
  loadingContainer: {
    padding: 20,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 8,
    color: '#6B7280',
    fontSize: 14,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FEF2F2',
    borderRadius: 8,
    marginTop: 8,
  },
  errorText: {
    marginLeft: 8,
    color: '#EF4444',
    fontSize: 14,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#6B7280',
  },
  lastUpdated: {
    fontSize: 10,
    color: '#9CA3AF',
  },
  periodSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  periodButton: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: '#F3F4F6',
  },
  periodButtonActive: {
    backgroundColor: '#1D4ED8',
  },
  periodButtonText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  periodButtonTextActive: {
    color: '#FFFFFF',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  metricCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
  },
  metricSubtext: {
    fontSize: 10,
    color: '#9CA3AF',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 12,
  },
  statItem: {
    flex: 1,
    minWidth: '22%',
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  signalCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#1D4ED8',
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  signalSymbolContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  signalSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
  },
  actionBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  actionText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  confidenceText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1D4ED8',
  },
  signalDetails: {
    gap: 4,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  detailLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  detailValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1F2937',
  },
  reasoningContainer: {
    marginTop: 8,
    padding: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 6,
  },
  reasoningLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
    fontWeight: '600',
  },
  reasoningText: {
    fontSize: 12,
    color: '#374151',
    lineHeight: 18,
  },
  timestamp: {
    fontSize: 10,
    color: '#9CA3AF',
    marginTop: 4,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 8,
    fontWeight: '500',
  },
  emptySubtext: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 4,
    textAlign: 'center',
  },
  badgeContainer: {
    marginTop: 4,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});

