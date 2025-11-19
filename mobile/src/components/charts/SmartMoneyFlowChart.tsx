/**
 * Chart 2: "Smart Money Flow"
 * Unusual options volume + sweep indicator overlay on price chart
 */
import React, { useMemo } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { useColorScheme } from 'react-native';

const { width } = Dimensions.get('window');

interface OptionsFlowDataPoint {
  date: string;
  price: number;
  unusualVolumePercent: number;
  sweepCount: number;
  putCallRatio: number;
}

interface SmartMoneyFlowChartProps {
  symbol: string;
  priceData: Array<{ date: string; price: number }>;
  optionsFlowData: OptionsFlowDataPoint[];
}

export default function SmartMoneyFlowChart({
  symbol,
  priceData,
  optionsFlowData,
}: SmartMoneyFlowChartProps) {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  const mergedData = useMemo(() => {
    const dataMap = new Map<string, OptionsFlowDataPoint>();
    optionsFlowData.forEach((opt) => dataMap.set(opt.date, opt));
    return priceData.map((price) => {
      const options = dataMap.get(price.date);
      return {
        date: price.date,
        price: price.price,
        unusualVolume: options?.unusualVolumePercent || 0,
        sweepCount: options?.sweepCount || 0,
        putCallRatio: options?.putCallRatio || 1.0,
        hasSignal: (options?.unusualVolumePercent || 0) > 20 || (options?.sweepCount || 0) > 0,
      };
    });
  }, [priceData, optionsFlowData]);

  if (mergedData.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={[styles.title, { color: isDark ? '#fff' : '#000' }]}>Smart Money Flow</Text>
        <Text style={[styles.subtitle, { color: isDark ? '#999' : '#666' }]}>No data available</Text>
      </View>
    );
  }

  const latest = mergedData[mergedData.length - 1];
  const recentSignals = mergedData.slice(-10).filter((d) => d.hasSignal).length;

  const chartLabels = mergedData.slice(-20).map((d) => {
    const date = new Date(d.date);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });

  const priceDataForChart = mergedData.slice(-20).map((d) => d.price);

  const chartData = {
    labels: chartLabels,
    datasets: [{ data: priceDataForChart, color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`, strokeWidth: 3 }],
  };

  return (
    <View style={[styles.container, { backgroundColor: isDark ? '#1a1a1a' : '#fff' }]}>
      <View style={styles.header}>
        <View>
          <Text style={[styles.title, { color: isDark ? '#fff' : '#000' }]}>Smart Money Flow</Text>
          <Text style={[styles.subtitle, { color: isDark ? '#999' : '#666' }]}>Institutional options activity on {symbol}</Text>
        </View>
      </View>

      <View style={styles.metricsContainer}>
        <View style={styles.metric}>
          <Text style={[styles.metricLabel, { color: isDark ? '#999' : '#666' }]}>Unusual Volume</Text>
          <Text style={[styles.metricValue, { color: latest.unusualVolume > 30 ? '#22c55e' : latest.unusualVolume > 15 ? '#f59e0b' : '#6b7280' }]}>
            {latest.unusualVolume.toFixed(1)}%
          </Text>
        </View>
        <View style={styles.metric}>
          <Text style={[styles.metricLabel, { color: isDark ? '#999' : '#666' }]}>Sweeps (24h)</Text>
          <Text style={[styles.metricValue, { color: latest.sweepCount > 0 ? '#22c55e' : '#6b7280' }]}>{latest.sweepCount}</Text>
        </View>
        <View style={styles.metric}>
          <Text style={[styles.metricLabel, { color: isDark ? '#999' : '#666' }]}>Put/Call</Text>
          <Text style={[styles.metricValue, { color: latest.putCallRatio < 0.7 ? '#22c55e' : latest.putCallRatio > 1.3 ? '#ef4444' : '#6b7280' }]}>
            {latest.putCallRatio.toFixed(2)}
          </Text>
        </View>
      </View>

      <View style={styles.chartContainer}>
        <LineChart
          data={chartData}
          width={width - 40}
          height={220}
          chartConfig={{
            backgroundColor: isDark ? '#1a1a1a' : '#ffffff',
            backgroundGradientFrom: isDark ? '#1a1a1a' : '#ffffff',
            backgroundGradientTo: isDark ? '#1a1a1a' : '#ffffff',
            decimalPlaces: 2,
            color: (opacity = 1) => (isDark ? `rgba(255, 255, 255, ${opacity})` : `rgba(0, 0, 0, ${opacity})`),
            labelColor: (opacity = 1) => (isDark ? `rgba(255, 255, 255, ${opacity})` : `rgba(0, 0, 0, ${opacity})`),
            style: { borderRadius: 16 },
            propsForDots: { r: '4', strokeWidth: '2' },
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

      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#22c55e' }]} />
          <Text style={[styles.legendText, { color: isDark ? '#999' : '#666' }]}>Unusual Volume</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#f59e0b' }]} />
          <Text style={[styles.legendText, { color: isDark ? '#999' : '#666' }]}>Sweep Detected</Text>
        </View>
      </View>

      {recentSignals >= 3 && (
        <View style={[styles.insight, { backgroundColor: isDark ? '#1e3a2e' : '#d1fae5' }]}>
          <Text style={[styles.insightText, { color: isDark ? '#4ade80' : '#065f46' }]}>
            🎯 Strong Smart Money Activity: {recentSignals} signals in last 10 days. Institutions are positioning.
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, borderRadius: 16, marginVertical: 8, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 8, elevation: 3 },
  header: { marginBottom: 16 },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 4 },
  subtitle: { fontSize: 14, fontWeight: '400' },
  metricsContainer: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 16, paddingVertical: 12, borderRadius: 12, backgroundColor: 'rgba(0, 0, 0, 0.03)' },
  metric: { alignItems: 'center' },
  metricLabel: { fontSize: 12, fontWeight: '500', marginBottom: 4 },
  metricValue: { fontSize: 18, fontWeight: '700' },
  chartContainer: { alignItems: 'center', marginBottom: 12, position: 'relative' },
  chart: { marginVertical: 8, borderRadius: 16 },
  legend: { flexDirection: 'row', justifyContent: 'center', marginTop: 8, flexWrap: 'wrap' },
  legendItem: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 12, marginVertical: 4 },
  legendDot: { width: 12, height: 12, borderRadius: 6, marginRight: 6 },
  legendText: { fontSize: 12, fontWeight: '500' },
  insight: { padding: 12, borderRadius: 12, marginTop: 12 },
  insightText: { fontSize: 13, fontWeight: '600', lineHeight: 18 },
});

