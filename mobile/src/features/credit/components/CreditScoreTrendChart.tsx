/**
 * Credit Score Trend Chart Component
 * Shows historical credit score trends over time
 */

import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
// Note: react-native-chart-kit needs to be installed
// For now, using a simple text-based visualization
// import { LineChart } from 'react-native-chart-kit';
import { CreditScore } from '../types/CreditTypes';

interface CreditScoreTrendChartProps {
  scores: CreditScore[];
}

const { width } = Dimensions.get('window');
const CHART_WIDTH = width - 40;

export const CreditScoreTrendChart: React.FC<CreditScoreTrendChartProps> = ({
  scores,
}) => {
  if (!scores || scores.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No credit score history yet</Text>
        <Text style={styles.emptySubtext}>Start tracking to see your progress</Text>
      </View>
    );
  }

  // Sort by date
  const sortedScores = [...scores].sort((a, b) => 
    new Date(a.lastUpdated).getTime() - new Date(b.lastUpdated).getTime()
  );

  // Prepare chart data
  const labels = sortedScores.map(score => {
    const date = new Date(score.lastUpdated);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });

  const data = sortedScores.map(score => score.score);

  const chartData = {
    labels: labels.length > 7 ? labels.filter((_, i) => i % Math.ceil(labels.length / 7) === 0) : labels,
    datasets: [
      {
        data,
        color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
        strokeWidth: 2,
      },
    ],
  };

  const chartConfig = {
    backgroundColor: '#FFFFFF',
    backgroundGradientFrom: '#FFFFFF',
    backgroundGradientTo: '#F8F9FA',
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: '#007AFF',
    },
  };

  // Calculate trend
  const firstScore = sortedScores[0]?.score || 0;
  const lastScore = sortedScores[sortedScores.length - 1]?.score || 0;
  const trend = lastScore - firstScore;
  const trendText = trend > 0 ? `+${trend}` : `${trend}`;
  const trendColor = trend > 0 ? '#34C759' : trend < 0 ? '#FF3B30' : '#8E8E93';

  // Simple bar chart visualization (fallback if chart-kit not available)
  const maxScore = Math.max(...data, 800);
  const minScore = Math.min(...data, 300);
  const range = maxScore - minScore || 100;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Credit Score Trend</Text>
        <View style={styles.trendContainer}>
          <Text style={[styles.trendText, { color: trendColor }]}>
            {trendText} points
          </Text>
          <Text style={styles.trendLabel}>over {sortedScores.length} {sortedScores.length === 1 ? 'month' : 'months'}</Text>
        </View>
      </View>
      
      {/* Simple bar chart visualization */}
      <View style={styles.chartContainer}>
        <View style={styles.barChart}>
          {data.map((score, index) => {
            const height = ((score - minScore) / range) * 150;
            return (
              <View key={index} style={styles.barColumn}>
                <View style={[styles.bar, { height: Math.max(height, 10) }]} />
                <Text style={styles.barLabel}>{score}</Text>
                {index % Math.ceil(data.length / 7) === 0 && (
                  <Text style={styles.barDateLabel}>{labels[index]}</Text>
                )}
              </View>
            );
          })}
        </View>
      </View>
      
      <View style={styles.statsContainer}>
        <View style={styles.stat}>
          <Text style={styles.statLabel}>Current</Text>
          <Text style={styles.statValue}>{lastScore}</Text>
        </View>
        <View style={styles.stat}>
          <Text style={styles.statLabel}>Highest</Text>
          <Text style={styles.statValue}>{Math.max(...data)}</Text>
        </View>
        <View style={styles.stat}>
          <Text style={styles.statLabel}>Average</Text>
          <Text style={styles.statValue}>
            {Math.round(data.reduce((a, b) => a + b, 0) / data.length)}
          </Text>
        </View>
      </View>
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
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  trendContainer: {
    alignItems: 'flex-end',
  },
  trendText: {
    fontSize: 16,
    fontWeight: '700',
  },
  trendLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 2,
  },
  chartContainer: {
    marginVertical: 8,
    height: 200,
    justifyContent: 'flex-end',
  },
  barChart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-around',
    height: 180,
    paddingHorizontal: 8,
  },
  barColumn: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginHorizontal: 2,
  },
  bar: {
    width: '80%',
    backgroundColor: '#007AFF',
    borderRadius: 4,
    minHeight: 4,
  },
  barLabel: {
    fontSize: 10,
    color: '#1C1C1E',
    marginTop: 4,
    fontWeight: '600',
  },
  barDateLabel: {
    fontSize: 8,
    color: '#8E8E93',
    marginTop: 2,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  stat: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#8E8E93',
  },
});

