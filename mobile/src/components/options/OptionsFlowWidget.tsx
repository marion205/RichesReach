import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery } from '@apollo/client';
import { GET_OPTIONS_FLOW } from '../../graphql/tradingQueries';

interface OptionsFlowWidgetProps {
  symbol: string;
}

interface UnusualActivity {
  contractSymbol: string;
  strike: number;
  expiration: string;
  optionType: 'call' | 'put';
  volume: number;
  openInterest: number;
  volumeVsOI: number;
  lastPrice: number;
  bid: number;
  ask: number;
  impliedVolatility: number;
  unusualVolumePercent: number;
  sweepCount: number;
  blockSize: number;
  isDarkPool: boolean;
}

export default function OptionsFlowWidget({ symbol }: OptionsFlowWidgetProps) {
  const [filter, setFilter] = useState<'all' | 'calls' | 'puts' | 'sweeps' | 'blocks'>('all');
  const { data, loading, error } = useQuery(GET_OPTIONS_FLOW, {
    variables: { symbol },
    skip: !symbol,
    fetchPolicy: 'cache-and-network',
    pollInterval: 30000, // Poll every 30 seconds for updates
    errorPolicy: 'all',
  });

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color="#007AFF" />
        <Text style={styles.loadingText}>Loading options flow...</Text>
      </View>
    );
  }

  if (error || !data?.optionsFlow) {
    // Fallback to mock data for demo
    return <OptionsFlowWidgetMock symbol={symbol} filter={filter} setFilter={setFilter} />;
  }

  const flow = data.optionsFlow;
  const unusualActivity = flow.unusualActivity || [];
  const filteredActivity = unusualActivity.filter((item: UnusualActivity) => {
    if (filter === 'calls') return item.optionType === 'call';
    if (filter === 'puts') return item.optionType === 'put';
    if (filter === 'sweeps') return item.sweepCount > 0;
    if (filter === 'blocks') return item.blockSize > 0;
    return true;
  });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="activity" size={18} color="#007AFF" />
        <Text style={styles.title}>Options Flow & Unusual Activity</Text>
      </View>

      {/* Summary Metrics */}
      <View style={styles.metricsRow}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Put/Call Ratio</Text>
          <Text style={styles.metricValue}>{flow.putCallRatio?.toFixed(2) || 'N/A'}</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Call Volume</Text>
          <Text style={[styles.metricValue, styles.callVolume]}>
            {flow.totalCallVolume?.toLocaleString() || '0'}
          </Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Put Volume</Text>
          <Text style={[styles.metricValue, styles.putVolume]}>
            {flow.totalPutVolume?.toLocaleString() || '0'}
          </Text>
        </View>
      </View>

      {/* Filter Buttons */}
      <View style={styles.filterRow}>
        {(['all', 'calls', 'puts', 'sweeps', 'blocks'] as const).map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterButton, filter === f && styles.filterButtonActive]}
            onPress={() => setFilter(f)}
          >
            <Text style={[styles.filterText, filter === f && styles.filterTextActive]}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Unusual Activity List */}
      <ScrollView style={styles.activityList} showsVerticalScrollIndicator={false}>
        {filteredActivity.length === 0 ? (
          <View style={styles.emptyState}>
            <Icon name="info" size={24} color="#9CA3AF" />
            <Text style={styles.emptyText}>No unusual activity detected</Text>
          </View>
        ) : (
          filteredActivity.map((item: UnusualActivity, index: number) => (
            <View key={index} style={styles.activityCard}>
              <View style={styles.activityHeader}>
                <View style={styles.activityType}>
                  <Text style={[styles.optionType, item.optionType === 'call' ? styles.callType : styles.putType]}>
                    {item.optionType.toUpperCase()}
                  </Text>
                  <Text style={styles.strike}>${item.strike}</Text>
                  <Text style={styles.expiration}>{item.expiration}</Text>
                </View>
                <View style={styles.activityBadges}>
                  {item.isDarkPool && (
                    <View style={styles.darkPoolBadge}>
                      <Icon name="eye-off" size={10} color="#6B7280" />
                      <Text style={styles.badgeText}>Dark Pool</Text>
                    </View>
                  )}
                  {item.sweepCount > 0 && (
                    <View style={styles.sweepBadge}>
                      <Text style={styles.badgeText}>Sweep</Text>
                    </View>
                  )}
                  {item.blockSize > 0 && (
                    <View style={styles.blockBadge}>
                      <Text style={styles.badgeText}>Block</Text>
                    </View>
                  )}
                </View>
              </View>

              <View style={styles.activityMetrics}>
                <View style={styles.metricItem}>
                  <Text style={styles.metricLabel}>Volume</Text>
                  <Text style={styles.metricValue}>{item.volume.toLocaleString()}</Text>
                </View>
                <View style={styles.metricItem}>
                  <Text style={styles.metricLabel}>Unusual %</Text>
                  <Text style={[styles.metricValue, item.unusualVolumePercent > 200 && styles.highlight]}>
                    +{item.unusualVolumePercent.toFixed(0)}%
                  </Text>
                </View>
                <View style={styles.metricItem}>
                  <Text style={styles.metricLabel}>Last Price</Text>
                  <Text style={styles.metricValue}>${item.lastPrice.toFixed(2)}</Text>
                </View>
                <View style={styles.metricItem}>
                  <Text style={styles.metricLabel}>IV</Text>
                  <Text style={styles.metricValue}>{(item.impliedVolatility * 100).toFixed(1)}%</Text>
                </View>
              </View>
            </View>
          ))
        )}
      </ScrollView>
    </View>
  );
}

// Mock component for demo when API is unavailable
function OptionsFlowWidgetMock({
  symbol,
  filter,
  setFilter,
}: {
  symbol: string;
  filter: string;
  setFilter: (f: 'all' | 'calls' | 'puts' | 'sweeps' | 'blocks') => void;
}) {
  const mockActivity: UnusualActivity[] = [
    {
      contractSymbol: `${symbol}240119C00150000`,
      strike: 150,
      expiration: '2024-01-19',
      optionType: 'call',
      volume: 15234,
      openInterest: 45000,
      volumeVsOI: 0.34,
      lastPrice: 2.45,
      bid: 2.40,
      ask: 2.50,
      impliedVolatility: 0.28,
      unusualVolumePercent: 245,
      sweepCount: 3,
      blockSize: 500,
      isDarkPool: false,
    },
    {
      contractSymbol: `${symbol}240119P00145000`,
      strike: 145,
      expiration: '2024-01-19',
      optionType: 'put',
      volume: 8900,
      openInterest: 12000,
      volumeVsOI: 0.74,
      lastPrice: 1.20,
      bid: 1.15,
      ask: 1.25,
      impliedVolatility: 0.32,
      unusualVolumePercent: 180,
      sweepCount: 0,
      blockSize: 0,
      isDarkPool: true,
    },
  ];

  const filteredActivity = mockActivity.filter((item) => {
    if (filter === 'calls') return item.optionType === 'call';
    if (filter === 'puts') return item.optionType === 'put';
    if (filter === 'sweeps') return item.sweepCount > 0;
    if (filter === 'blocks') return item.blockSize > 0;
    return true;
  });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="activity" size={18} color="#007AFF" />
        <Text style={styles.title}>Options Flow & Unusual Activity</Text>
        <View style={styles.demoBadge}>
          <Text style={styles.demoText}>DEMO</Text>
        </View>
      </View>

      <View style={styles.metricsRow}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Put/Call Ratio</Text>
          <Text style={styles.metricValue}>0.58</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Call Volume</Text>
          <Text style={[styles.metricValue, styles.callVolume]}>15,234</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Put Volume</Text>
          <Text style={[styles.metricValue, styles.putVolume]}>8,900</Text>
        </View>
      </View>

      <View style={styles.filterRow}>
        {(['all', 'calls', 'puts', 'sweeps', 'blocks'] as const).map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterButton, filter === f && styles.filterButtonActive]}
            onPress={() => setFilter(f)}
          >
            <Text style={[styles.filterText, filter === f && styles.filterTextActive]}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.activityList} showsVerticalScrollIndicator={false}>
        {filteredActivity.map((item, index) => (
          <View key={index} style={styles.activityCard}>
            <View style={styles.activityHeader}>
              <View style={styles.activityType}>
                <Text style={[styles.optionType, item.optionType === 'call' ? styles.callType : styles.putType]}>
                  {item.optionType.toUpperCase()}
                </Text>
                <Text style={styles.strike}>${item.strike}</Text>
                <Text style={styles.expiration}>{item.expiration}</Text>
              </View>
              <View style={styles.activityBadges}>
                {item.isDarkPool && (
                  <View style={styles.darkPoolBadge}>
                    <Icon name="eye-off" size={10} color="#6B7280" />
                    <Text style={styles.badgeText}>Dark Pool</Text>
                  </View>
                )}
                {item.sweepCount > 0 && (
                  <View style={styles.sweepBadge}>
                    <Text style={styles.badgeText}>Sweep</Text>
                  </View>
                )}
                {item.blockSize > 0 && (
                  <View style={styles.blockBadge}>
                    <Text style={styles.badgeText}>Block</Text>
                  </View>
                )}
              </View>
            </View>

            <View style={styles.activityMetrics}>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Volume</Text>
                <Text style={styles.metricValue}>{item.volume.toLocaleString()}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Unusual %</Text>
                <Text style={[styles.metricValue, item.unusualVolumePercent > 200 && styles.highlight]}>
                  +{item.unusualVolumePercent.toFixed(0)}%
                </Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Last Price</Text>
                <Text style={styles.metricValue}>${item.lastPrice.toFixed(2)}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>IV</Text>
                <Text style={styles.metricValue}>{(item.impliedVolatility * 100).toFixed(1)}%</Text>
              </View>
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginLeft: 8,
  },
  demoBadge: {
    marginLeft: 'auto',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  demoText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#92400E',
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#F3F4F6',
    marginBottom: 12,
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  callVolume: {
    color: '#059669',
  },
  putVolume: {
    color: '#DC2626',
  },
  filterRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  filterButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
  },
  filterText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
  filterTextActive: {
    color: '#FFFFFF',
  },
  activityList: {
    maxHeight: 400,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 8,
  },
  activityCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  activityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  activityType: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  optionType: {
    fontSize: 11,
    fontWeight: '700',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  callType: {
    backgroundColor: '#D1FAE5',
    color: '#059669',
  },
  putType: {
    backgroundColor: '#FEE2E2',
    color: '#DC2626',
  },
  strike: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  expiration: {
    fontSize: 12,
    color: '#6B7280',
  },
  activityBadges: {
    flexDirection: 'row',
    gap: 6,
  },
  darkPoolBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    gap: 4,
  },
  sweepBadge: {
    backgroundColor: '#DBEAFE',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  blockBadge: {
    backgroundColor: '#E0E7FF',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#374151',
  },
  activityMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  metricItem: {
    alignItems: 'center',
  },
  highlight: {
    color: '#DC2626',
    fontWeight: '700',
  },
});

