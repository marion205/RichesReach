/**
 * Chart 1: "Consumer Spending Surge"
 * Dual-axis chart showing category/ticker spending growth vs stock price
 * This is your competitive moat visualization!
 */
import React, { useMemo } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { useColorScheme } from 'react-native';

const { width } = Dimensions.get('window');

interface SpendingDataPoint {
  date: string;
  spending: number;
  spendingChange: number; // % change
  price: number;
  priceChange: number; // % change
}

interface ConsumerSpendingSurgeChartProps {
  symbol: string;
  spendingData: SpendingDataPoint[];
  category?: string;
}

export default function ConsumerSpendingSurgeChart({
  symbol,
  spendingData,
  category,
}: ConsumerSpendingSurgeChartProps) {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  // Process data for dual-axis chart
  const chartData = useMemo(() => {
    if (!spendingData || spendingData.length === 0) {
      return null;
    }

    const labels = spendingData.map((d) => {
      const date = new Date(d.date);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    });

    const spendingChanges = spendingData.map((d) => d.spendingChange * 100); // Convert to %
    const priceChanges = spendingData.map((d) => d.priceChange * 100); // Convert to %

    return {
      labels: labels.slice(-12), // Last 12 data points
      datasets: [
        {
          data: spendingChanges.slice(-12),
          color: (opacity = 1) => `rgba(34, 197, 94, ${opacity})`, // Green for spending
          strokeWidth: 3,
        },
        {
          data: priceChanges.slice(-12),
          color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`, // Blue for price
          strokeWidth: 3,
        },
      ],
    };
  }, [spendingData]);

  if (!chartData) {
    return (
      <View style={styles.container}>
        <Text style={[styles.title, { color: isDark ? '#fff' : '#000' }]}>
          Consumer Spending Surge
        </Text>
        <Text style={[styles.subtitle, { color: isDark ? '#999' : '#666' }]}>
          No data available
        </Text>
      </View>
    );
  }

  const latestSpending = spendingData[spendingData.length - 1];
  const spendingGrowth = latestSpending.spendingChange * 100;
  const priceGrowth = latestSpending.priceChange * 100;
  const correlation = spendingGrowth > 0 && priceGrowth > 0 ? 'positive' : 'negative';

  return (
    <View style={[styles.container, { backgroundColor: isDark ? '#1a1a1a' : '#fff' }]}>
      <View style={styles.header}>
        <View>
          <Text style={[styles.title, { color: isDark ? '#fff' : '#000' }]}>
            Consumer Spending Surge
          </Text>
          <Text style={[styles.subtitle, { color: isDark ? '#999' : '#666' }]}>
            {category ? `${category} spending vs ${symbol} price` : `${symbol} spending vs price`}
          </Text>
        </View>
      </View>

      {/* Key Metrics */}
      <View style={styles.metricsContainer}>
        <View style={styles.metric}>
          <Text style={[styles.metricLabel, { color: isDark ? '#999' : '#666' }]}>
            Spending Growth
          </Text>
          <Text
            style={[
              styles.metricValue,
              { color: spendingGrowth >= 0 ? '#22c55e' : '#ef4444' },
            ]}
          >
            {spendingGrowth >= 0 ? '+' : ''}
            {spendingGrowth.toFixed(1)}%
          </Text>
        </View>
        <View style={styles.metric}>
          <Text style={[styles.metricLabel, { color: isDark ? '#999' : '#666' }]}>
            Price Change
          </Text>
          <Text
            style={[
              styles.metricValue,
              { color: priceGrowth >= 0 ? '#22c55e' : '#ef4444' },
            ]}
          >
            {priceGrowth >= 0 ? '+' : ''}
            {priceGrowth.toFixed(1)}%
          </Text>
        </View>
        <View style={styles.metric}>
          <Text style={[styles.metricLabel, { color: isDark ? '#999' : '#666' }]}>
            Correlation
          </Text>
          <Text
            style={[
              styles.metricValue,
              { color: correlation === 'positive' ? '#22c55e' : '#ef4444' },
            ]}
          >
            {correlation === 'positive' ? '✓ Aligned' : '✗ Diverged'}
          </Text>
        </View>
      </View>

      {/* Dual-Axis Chart */}
      <View style={styles.chartContainer}>
        <LineChart
          data={chartData}
          width={width - 40}
          height={220}
          chartConfig={{
            backgroundColor: isDark ? '#1a1a1a' : '#ffffff',
            backgroundGradientFrom: isDark ? '#1a1a1a' : '#ffffff',
            backgroundGradientTo: isDark ? '#1a1a1a' : '#ffffff',
            decimalPlaces: 1,
            color: (opacity = 1) => (isDark ? `rgba(255, 255, 255, ${opacity})` : `rgba(0, 0, 0, ${opacity})`),
            labelColor: (opacity = 1) => (isDark ? `rgba(255, 255, 255, ${opacity})` : `rgba(0, 0, 0, ${opacity})`),
            style: {
              borderRadius: 16,
            },
            propsForDots: {
              r: '4',
              strokeWidth: '2',
            },
          }}
          bezier
          style={styles.chart}
          withVerticalLabels={true}
          withHorizontalLabels={true}
          withInnerLines={true}
          withOuterLines={false}
          withShadow={false}
        />
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#22c55e' }]} />
          <Text style={[styles.legendText, { color: isDark ? '#999' : '#666' }]}>
            Spending Growth (%)
          </Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#3b82f6' }]} />
          <Text style={[styles.legendText, { color: isDark ? '#999' : '#666' }]}>
            Stock Price Change (%)
          </Text>
        </View>
      </View>

      {/* Insight */}
      {correlation === 'positive' && spendingGrowth > 15 && (
        <View style={[styles.insight, { backgroundColor: isDark ? '#1e3a2e' : '#d1fae5' }]}>
          <Text style={[styles.insightText, { color: isDark ? '#4ade80' : '#065f46' }]}>
            🚀 Strong Signal: {spendingGrowth.toFixed(1)}% spending surge aligns with{' '}
            {priceGrowth.toFixed(1)}% price growth. Consumer demand is driving stock performance.
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    borderRadius: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    fontWeight: '400',
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(0, 0, 0, 0.03)',
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  chartContainer: {
    alignItems: 'center',
    marginBottom: 12,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 8,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 6,
  },
  legendText: {
    fontSize: 12,
    fontWeight: '500',
  },
  insight: {
    padding: 12,
    borderRadius: 12,
    marginTop: 12,
  },
  insightText: {
    fontSize: 13,
    fontWeight: '600',
    lineHeight: 18,
  },
});

