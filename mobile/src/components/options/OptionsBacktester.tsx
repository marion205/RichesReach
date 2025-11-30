import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { LineChart } from 'react-native-chart-kit';
import { Dimensions } from 'react-native';

const screenWidth = Dimensions.get('window').width;

interface OptionsBacktesterProps {
  symbol: string;
  underlyingPrice: number;
}

interface Strategy {
  name: string;
  legs: Array<{
    optionType: 'call' | 'put';
    action: 'buy' | 'sell';
    strike: number;
    expiration: string;
    quantity: number;
    premium: number;
  }>;
}

export default function OptionsBacktester({ symbol, underlyingPrice }: OptionsBacktesterProps) {
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [backtesting, setBacktesting] = useState(false);
  const [results, setResults] = useState<any>(null);

  // Mock backtesting results (would use real historical data in production)
  const runBacktest = () => {
    setBacktesting(true);
    
    // Simulate backtesting
    setTimeout(() => {
      const mockResults = {
        totalTrades: 45,
        winningTrades: 28,
        losingTrades: 17,
        winRate: 62.2,
        totalReturn: 12.5,
        maxDrawdown: -8.3,
        sharpeRatio: 1.8,
        avgReturnPerTrade: 0.28,
        bestTrade: 8.5,
        worstTrade: -3.2,
        equityCurve: Array.from({ length: 30 }, (_, i) => ({
          date: new Date(Date.now() - (30 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          value: 10000 + (i * 150) + Math.random() * 200 - 100,
        })),
      };
      setResults(mockResults);
      setBacktesting(false);
    }, 2000);
  };

  const chartData = useMemo(() => {
    if (!results?.equityCurve) return null;
    
    return {
      labels: results.equityCurve.filter((_: any, i: number) => i % 5 === 0).map((p: any) => {
        const date = new Date(p.date);
        return `${date.getMonth() + 1}/${date.getDate()}`;
      }),
      datasets: [{
        data: results.equityCurve.map((p: any) => p.value),
        color: (opacity = 1) => `rgba(5, 150, 105, ${opacity})`,
        strokeWidth: 2,
      }],
    };
  }, [results]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="trending-up" size={18} color="#007AFF" />
        <Text style={styles.title}>Options Strategy Backtester</Text>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Strategy Input */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Strategy Configuration</Text>
          
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Start Date</Text>
            <TextInput
              style={styles.input}
              value={startDate}
              onChangeText={setStartDate}
              placeholder="YYYY-MM-DD"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>End Date</Text>
            <TextInput
              style={styles.input}
              value={endDate}
              onChangeText={setEndDate}
              placeholder="YYYY-MM-DD"
            />
          </View>

          <TouchableOpacity
            style={[styles.backtestButton, backtesting && styles.backtestButtonDisabled]}
            onPress={runBacktest}
            disabled={backtesting}
          >
            {backtesting ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <>
                <Icon name="play" size={16} color="#FFFFFF" />
                <Text style={styles.backtestButtonText}>Run Backtest</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Results */}
        {results && (
          <View style={styles.resultsSection}>
            <Text style={styles.sectionTitle}>Backtest Results</Text>

            {/* Performance Metrics */}
            <View style={styles.metricsGrid}>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Win Rate</Text>
                <Text style={[styles.metricValue, styles.positiveValue]}>
                  {results.winRate.toFixed(1)}%
                </Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Total Return</Text>
                <Text style={[styles.metricValue, styles.positiveValue]}>
                  {results.totalReturn > 0 ? '+' : ''}{results.totalReturn.toFixed(1)}%
                </Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Sharpe Ratio</Text>
                <Text style={styles.metricValue}>{results.sharpeRatio.toFixed(2)}</Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Max Drawdown</Text>
                <Text style={[styles.metricValue, styles.negativeValue]}>
                  {results.maxDrawdown.toFixed(1)}%
                </Text>
              </View>
            </View>

            {/* Trade Statistics */}
            <View style={styles.statsCard}>
              <Text style={styles.statsTitle}>Trade Statistics</Text>
              <View style={styles.statsRow}>
                <Text style={styles.statsLabel}>Total Trades:</Text>
                <Text style={styles.statsValue}>{results.totalTrades}</Text>
              </View>
              <View style={styles.statsRow}>
                <Text style={styles.statsLabel}>Winning Trades:</Text>
                <Text style={[styles.statsValue, styles.positiveValue]}>{results.winningTrades}</Text>
              </View>
              <View style={styles.statsRow}>
                <Text style={styles.statsLabel}>Losing Trades:</Text>
                <Text style={[styles.statsValue, styles.negativeValue]}>{results.losingTrades}</Text>
              </View>
              <View style={styles.statsRow}>
                <Text style={styles.statsLabel}>Avg Return/Trade:</Text>
                <Text style={styles.statsValue}>
                  {results.avgReturnPerTrade > 0 ? '+' : ''}{results.avgReturnPerTrade.toFixed(2)}%
                </Text>
              </View>
              <View style={styles.statsRow}>
                <Text style={styles.statsLabel}>Best Trade:</Text>
                <Text style={[styles.statsValue, styles.positiveValue]}>
                  +{results.bestTrade.toFixed(2)}%
                </Text>
              </View>
              <View style={styles.statsRow}>
                <Text style={styles.statsLabel}>Worst Trade:</Text>
                <Text style={[styles.statsValue, styles.negativeValue]}>
                  {results.worstTrade.toFixed(2)}%
                </Text>
              </View>
            </View>

            {/* Equity Curve */}
            {chartData && (
              <View style={styles.chartCard}>
                <Text style={styles.chartTitle}>Equity Curve</Text>
                <LineChart
                  data={chartData}
                  width={screenWidth - 64}
                  height={220}
                  chartConfig={{
                    backgroundColor: '#FFFFFF',
                    backgroundGradientFrom: '#FFFFFF',
                    backgroundGradientTo: '#FFFFFF',
                    decimalPlaces: 0,
                    color: (opacity = 1) => `rgba(5, 150, 105, ${opacity})`,
                    labelColor: (opacity = 1) => `rgba(107, 114, 128, ${opacity})`,
                    style: { borderRadius: 16 },
                    propsForDots: { r: '0' },
                  }}
                  bezier
                  style={styles.chart}
                />
              </View>
            )}
          </View>
        )}

        {!results && !backtesting && (
          <View style={styles.emptyState}>
            <Icon name="bar-chart-2" size={48} color="#D1D5DB" />
            <Text style={styles.emptyText}>Configure strategy and run backtest</Text>
            <Text style={styles.emptySubtext}>
              Test your options strategy against historical data
            </Text>
          </View>
        )}
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
    maxHeight: 800,
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
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#111827',
    backgroundColor: '#FFFFFF',
  },
  backtestButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  backtestButtonDisabled: {
    opacity: 0.6,
  },
  backtestButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  resultsSection: {
    marginTop: 20,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  metricCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  positiveValue: {
    color: '#059669',
  },
  negativeValue: {
    color: '#DC2626',
  },
  statsCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  statsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  statsLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  statsValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  chartCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 8,
    textAlign: 'center',
  },
});

