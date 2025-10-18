import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { LineChart } from 'react-native-chart-kit';
import { POOL_ANALYTICS_QUERY } from '../graphql/queries_actual_schema';

const screenWidth = Dimensions.get('window').width;

interface PoolAnalyticsPoint {
  date: string;
  feeApy: number;
  ilEstimate: number;
  netApy: number;
}

interface PoolAnalyticsScreenProps {
  route: {
    params: {
      poolId: string;
      poolSymbol: string;
    };
  };
}

export default function PoolAnalyticsScreen({ route }: PoolAnalyticsScreenProps) {
  const { poolId, poolSymbol } = route.params;
  const [selectedMetric, setSelectedMetric] = useState<'netApy' | 'feeApy' | 'ilEstimate'>('netApy');
  const [timeframe, setTimeframe] = useState<30 | 90 | 365>(30);

  const { data, loading, error } = useQuery(POOL_ANALYTICS_QUERY, {
    variables: { poolId, days: timeframe },
    fetchPolicy: 'cache-and-network',
  });

  const analytics: PoolAnalyticsPoint[] = data?.poolAnalytics || [];

  const getChartData = () => {
    if (!analytics.length) return null;

    const labels = analytics.map(point => {
      const date = new Date(point.date);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    });

    const values = analytics.map(point => point[selectedMetric]);

    return {
      labels: labels.slice(-7), // Show last 7 data points
      datasets: [
        {
          data: values.slice(-7),
          color: (opacity = 1) => {
            switch (selectedMetric) {
              case 'netApy': return `rgba(16, 185, 129, ${opacity})`; // Green
              case 'feeApy': return `rgba(59, 130, 246, ${opacity})`; // Blue
              case 'ilEstimate': return `rgba(239, 68, 68, ${opacity})`; // Red
              default: return `rgba(59, 130, 246, ${opacity})`;
            }
          },
          strokeWidth: 2,
        },
      ],
    };
  };

  const getMetricLabel = (metric: string) => {
    switch (metric) {
      case 'netApy': return 'Net APY';
      case 'feeApy': return 'Fee APY';
      case 'ilEstimate': return 'IL Estimate';
      default: return metric;
    }
  };

  const getMetricColor = (metric: string) => {
    switch (metric) {
      case 'netApy': return '#10B981';
      case 'feeApy': return '#3B82F6';
      case 'ilEstimate': return '#EF4444';
      default: return '#3B82F6';
    }
  };

  const chartData = getChartData();

  if (loading) {
    return (
      <View style={styles.center}>
        <Text style={styles.loadingText}>Loading analytics...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Failed to load analytics</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{poolSymbol} Analytics</Text>
        <Text style={styles.subtitle}>Performance metrics and trends</Text>
      </View>

      {/* Timeframe Selector */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Timeframe</Text>
        <View style={styles.timeframeSelector}>
          {[30, 90, 365].map((days) => (
            <TouchableOpacity
              key={days}
              style={[
                styles.timeframeButton,
                timeframe === days && styles.selectedTimeframeButton
              ]}
              onPress={() => setTimeframe(days as 30 | 90 | 365)}
            >
              <Text style={[
                styles.timeframeButtonText,
                timeframe === days && styles.selectedTimeframeButtonText
              ]}>
                {days}D
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Metric Selector */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Metric</Text>
        <View style={styles.metricSelector}>
          {(['netApy', 'feeApy', 'ilEstimate'] as const).map((metric) => (
            <TouchableOpacity
              key={metric}
              style={[
                styles.metricButton,
                selectedMetric === metric && styles.selectedMetricButton
              ]}
              onPress={() => setSelectedMetric(metric)}
            >
              <Text style={[
                styles.metricButtonText,
                selectedMetric === metric && styles.selectedMetricButtonText
              ]}>
                {getMetricLabel(metric)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Chart */}
      {chartData && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {getMetricLabel(selectedMetric)} Over Time
          </Text>
          <View style={styles.chartContainer}>
            <LineChart
              data={chartData}
              width={screenWidth - 40}
              height={220}
              yAxisSuffix="%"
              chartConfig={{
                backgroundColor: '#FFFFFF',
                backgroundGradientFrom: '#FFFFFF',
                backgroundGradientTo: '#FFFFFF',
                decimalPlaces: 2,
                color: (opacity = 1) => getMetricColor(selectedMetric),
                labelColor: (opacity = 1) => '#64748B',
                style: {
                  borderRadius: 16,
                },
                propsForDots: {
                  r: '4',
                  strokeWidth: '2',
                  stroke: getMetricColor(selectedMetric),
                },
              }}
              bezier
              style={styles.chart}
            />
          </View>
        </View>
      )}

      {/* Current Metrics */}
      {analytics.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Current Metrics</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricCardLabel}>Net APY</Text>
              <Text style={[styles.metricCardValue, { color: '#10B981' }]}>
                {analytics[analytics.length - 1]?.netApy?.toFixed(2)}%
              </Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricCardLabel}>Fee APY</Text>
              <Text style={[styles.metricCardValue, { color: '#3B82F6' }]}>
                {analytics[analytics.length - 1]?.feeApy?.toFixed(2)}%
              </Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricCardLabel}>IL Estimate</Text>
              <Text style={[styles.metricCardValue, { color: '#EF4444' }]}>
                {analytics[analytics.length - 1]?.ilEstimate?.toFixed(2)}%
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* No Data Message */}
      {!analytics.length && (
        <View style={styles.center}>
          <Text style={styles.noDataText}>No analytics data available</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#64748B',
  },
  errorText: {
    fontSize: 16,
    color: '#EF4444',
  },
  noDataText: {
    fontSize: 16,
    color: '#64748B',
  },
  header: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1E293B',
  },
  subtitle: {
    fontSize: 16,
    color: '#64748B',
    marginTop: 4,
  },
  section: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 16,
  },
  timeframeSelector: {
    flexDirection: 'row',
    gap: 12,
  },
  timeframeButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  selectedTimeframeButton: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  timeframeButtonText: {
    fontSize: 14,
    color: '#64748B',
  },
  selectedTimeframeButtonText: {
    color: '#FFFFFF',
  },
  metricSelector: {
    flexDirection: 'row',
    gap: 12,
  },
  metricButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  selectedMetricButton: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  metricButtonText: {
    fontSize: 14,
    color: '#64748B',
  },
  selectedMetricButtonText: {
    color: '#FFFFFF',
  },
  chartContainer: {
    alignItems: 'center',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  metricCard: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  metricCardLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 8,
  },
  metricCardValue: {
    fontSize: 18,
    fontWeight: 'bold',
  },
});
