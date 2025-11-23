/**
 * SHAP Feature Importance Chart
 * Visualizes SHAP values showing which features drive predictions
 */
import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { BarChart } from 'react-native-chart-kit';
import { useColorScheme } from 'react-native';

const { width } = Dimensions.get('window');

interface SHAPFeature {
  name: string;
  value: number;
  absValue: number;
}

interface SHAPFeatureImportanceChartProps {
  features: SHAPFeature[];
  prediction?: number;
  title?: string;
}

export default function SHAPFeatureImportanceChart({
  features,
  prediction,
  title = 'Feature Importance (SHAP Values)',
}: SHAPFeatureImportanceChartProps) {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  
  // Sort by absolute value and take top 10
  const topFeatures = [...features]
    .sort((a, b) => b.absValue - a.absValue)
    .slice(0, 10);
  
  if (topFeatures.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={[styles.title, { color: isDark ? '#fff' : '#000' }]}>{title}</Text>
        <Text style={[styles.noData, { color: isDark ? '#999' : '#666' }]}>
          No feature importance data available
        </Text>
      </View>
    );
  }
  
  // Prepare chart data
  const labels = topFeatures.map(f => {
    // Truncate long names
    const name = f.name.length > 15 ? f.name.substring(0, 15) + '...' : f.name;
    return name;
  });
  const values = topFeatures.map(f => f.value);
  const colors = topFeatures.map(f => f.value >= 0 ? '#00cc99' : '#ff4444');
  
  const chartData = {
    labels,
    datasets: [
      {
        data: values,
        color: (opacity = 1) => {
          // Return color based on value
          return values.map((v, i) => colors[i] + Math.floor(opacity * 255).toString(16).padStart(2, '0'));
        },
      },
    ],
  };
  
  const chartConfig = {
    backgroundColor: isDark ? '#1a1a1a' : '#ffffff',
    backgroundGradientFrom: isDark ? '#1a1a1a' : '#ffffff',
    backgroundGradientTo: isDark ? '#2a2a2a' : '#f5f5f5',
    decimalPlaces: 3,
    color: (opacity = 1) => (isDark ? `rgba(255, 255, 255, ${opacity})` : `rgba(0, 0, 0, ${opacity})`),
    labelColor: (opacity = 1) => (isDark ? `rgba(255, 255, 255, ${opacity})` : `rgba(0, 0, 0, ${opacity})`),
    style: {
      borderRadius: 16,
    },
    propsForBackgroundLines: {
      strokeDasharray: '',
      stroke: isDark ? '#333' : '#e0e0e0',
    },
    barPercentage: 0.7,
  };
  
  return (
    <View style={[styles.container, { backgroundColor: isDark ? '#1a1a1a' : '#ffffff' }]}>
      <Text style={[styles.title, { color: isDark ? '#fff' : '#000' }]}>{title}</Text>
      
      {prediction !== undefined && (
        <View style={styles.predictionBadge}>
          <Text style={styles.predictionLabel}>Prediction:</Text>
          <Text style={[styles.predictionValue, prediction >= 0 ? styles.profit : styles.loss]}>
            {prediction >= 0 ? '+' : ''}{(prediction * 100).toFixed(2)}%
          </Text>
        </View>
      )}
      
      <BarChart
        data={chartData}
        width={width - 64}
        height={300}
        yAxisLabel=""
        yAxisSuffix=""
        chartConfig={chartConfig}
        style={styles.chart}
        showValuesOnTopOfBars
        fromZero
        withInnerLines={false}
        withVerticalLabels={true}
        withHorizontalLabels={true}
        segments={4}
      />
      
      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: '#00cc99' }]} />
          <Text style={[styles.legendText, { color: isDark ? '#fff' : '#000' }]}>Positive Impact</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: '#ff4444' }]} />
          <Text style={[styles.legendText, { color: isDark ? '#fff' : '#000' }]}>Negative Impact</Text>
        </View>
      </View>
      
      {/* Top 3 Features Summary */}
      <View style={styles.summary}>
        <Text style={[styles.summaryTitle, { color: isDark ? '#fff' : '#000' }]}>Top Drivers:</Text>
        {topFeatures.slice(0, 3).map((feature, idx) => (
          <View key={idx} style={styles.summaryItem}>
            <Text style={[styles.summaryFeature, { color: isDark ? '#fff' : '#000' }]}>
              {idx + 1}. {feature.name}
            </Text>
            <Text style={[
              styles.summaryValue,
              feature.value >= 0 ? styles.profit : styles.loss
            ]}>
              {feature.value >= 0 ? '+' : ''}{feature.value.toFixed(4)}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    borderRadius: 12,
    marginVertical: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  predictionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    padding: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(0, 204, 153, 0.1)',
  },
  predictionLabel: {
    fontSize: 14,
    marginRight: 8,
    color: '#666',
  },
  predictionValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  profit: {
    color: '#00cc99',
  },
  loss: {
    color: '#ff4444',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 12,
    gap: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 6,
  },
  legendText: {
    fontSize: 12,
  },
  summary: {
    marginTop: 16,
    padding: 12,
    borderRadius: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.05)',
  },
  summaryTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  summaryItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  summaryFeature: {
    fontSize: 13,
    flex: 1,
  },
  summaryValue: {
    fontSize: 13,
    fontWeight: '600',
  },
  noData: {
    fontSize: 14,
    textAlign: 'center',
    padding: 20,
  },
});

