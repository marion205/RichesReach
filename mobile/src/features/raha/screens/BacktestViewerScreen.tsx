import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useBacktestRun, useUserBacktests, BacktestRun } from '../hooks/useBacktest';
import { LineChart } from 'react-native-chart-kit';

const { width } = Dimensions.get('window');

interface BacktestViewerScreenProps {
  backtestId?: string;
  navigateTo?: (screen: string, params?: any) => void;
  onBack?: () => void;
}

export default function BacktestViewerScreen({ backtestId, navigateTo, onBack }: BacktestViewerScreenProps = {}) {
  // Custom navigation helper (not using React Navigation)
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else if (navigateTo) {
      navigateTo('pro-labs');
    } else if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal('pro-labs');
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen('pro-labs');
      }
    }
  };

  const { backtest, loading, refetch } = useBacktestRun(backtestId || '');
  const { backtests, loading: loadingList } = useUserBacktests();

  const [selectedBacktest, setSelectedBacktest] = useState<BacktestRun | null>(
    backtest || null
  );

  React.useEffect(() => {
    if (backtest) {
      setSelectedBacktest(backtest);
    }
  }, [backtest]);

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  const formatPercentage = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${(value * 100).toFixed(2)}%`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return '#10B981';
      case 'RUNNING':
        return '#3B82F6';
      case 'FAILED':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  const renderEquityCurve = useCallback(() => {
    if (!selectedBacktest?.equityCurve || selectedBacktest.equityCurve.length === 0) {
      return (
        <View style={styles.emptyChart}>
          <Icon name="bar-chart-2" size={48} color="#9CA3AF" />
          <Text style={styles.emptyChartText}>No equity curve data</Text>
        </View>
      );
    }

    const equityData = selectedBacktest.equityCurve.map(point => point.equity);
    const labels = selectedBacktest.equityCurve.map((point, index) => {
      if (index === 0 || index === equityData.length - 1 || index % Math.floor(equityData.length / 5) === 0) {
        return new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      }
      return '';
    });

    const minEquity = Math.min(...equityData);
    const maxEquity = Math.max(...equityData);
    const range = maxEquity - minEquity;
    const padding = range * 0.1;

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Equity Curve</Text>
        <LineChart
          data={{
            labels: labels,
            datasets: [
              {
                data: equityData,
                color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
                strokeWidth: 2,
              },
            ],
          }}
          width={width - 64}
          height={220}
          chartConfig={{
            backgroundColor: '#FFFFFF',
            backgroundGradientFrom: '#FFFFFF',
            backgroundGradientTo: '#FFFFFF',
            decimalPlaces: 0,
            color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
            labelColor: (opacity = 1) => `rgba(107, 114, 128, ${opacity})`,
            style: {
              borderRadius: 16,
            },
            propsForDots: {
              r: '4',
              strokeWidth: '2',
              stroke: '#3B82F6',
            },
          }}
          bezier
          style={styles.chart}
          withVerticalLabels={true}
          withHorizontalLabels={true}
          withInnerLines={true}
          withOuterLines={false}
          withDots={false}
          withShadow={false}
        />
        <View style={styles.chartStats}>
          <View style={styles.chartStat}>
            <Text style={styles.chartStatLabel}>Start</Text>
            <Text style={styles.chartStatValue}>
              {formatCurrency(equityData[0])}
            </Text>
          </View>
          <View style={styles.chartStat}>
            <Text style={styles.chartStatLabel}>End</Text>
            <Text style={styles.chartStatValue}>
              {formatCurrency(equityData[equityData.length - 1])}
            </Text>
          </View>
          <View style={styles.chartStat}>
            <Text style={styles.chartStatLabel}>Return</Text>
            <Text style={[styles.chartStatValue, {
              color: equityData[equityData.length - 1] >= equityData[0] ? '#10B981' : '#EF4444',
            }]}>
              {formatPercentage((equityData[equityData.length - 1] - equityData[0]) / equityData[0])}
            </Text>
          </View>
        </View>
      </View>
    );
  }, [selectedBacktest]);

  const renderMetrics = useCallback(() => {
    if (!selectedBacktest?.metrics) {
      return null;
    }

    const metrics = selectedBacktest.metrics;

    return (
      <View style={styles.metricsContainer}>
        <Text style={styles.sectionTitle}>Performance Metrics</Text>
        
        <View style={styles.metricsGrid}>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Win Rate</Text>
            <Text style={styles.metricValue}>
              {metrics.winRate ? `${(metrics.winRate * 100).toFixed(1)}%` : 'N/A'}
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Sharpe Ratio</Text>
            <Text style={styles.metricValue}>
              {metrics.sharpeRatio ? metrics.sharpeRatio.toFixed(2) : 'N/A'}
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Max Drawdown</Text>
            <Text style={[styles.metricValue, { color: '#EF4444' }]}>
              {metrics.maxDrawdown ? formatPercentage(metrics.maxDrawdown) : 'N/A'}
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Expectancy</Text>
            <Text style={[styles.metricValue, {
              color: (metrics.expectancy || 0) >= 0 ? '#10B981' : '#EF4444',
            }]}>
              {metrics.expectancy ? `${metrics.expectancy.toFixed(2)}R` : 'N/A'}
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Total Trades</Text>
            <Text style={styles.metricValue}>
              {metrics.totalTrades || 0}
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Profit Factor</Text>
            <Text style={[styles.metricValue, {
              color: (metrics.profitFactor || 0) >= 1 ? '#10B981' : '#EF4444',
            }]}>
              {metrics.profitFactor ? metrics.profitFactor.toFixed(2) : 'N/A'}
            </Text>
          </View>
        </View>

        <View style={styles.detailMetrics}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Winning Trades:</Text>
            <Text style={styles.detailValue}>{metrics.winningTrades || 0}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Losing Trades:</Text>
            <Text style={styles.detailValue}>{metrics.losingTrades || 0}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Avg Win:</Text>
            <Text style={[styles.detailValue, { color: '#10B981' }]}>
              {metrics.avgWin ? formatCurrency(metrics.avgWin) : 'N/A'}
            </Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Avg Loss:</Text>
            <Text style={[styles.detailValue, { color: '#EF4444' }]}>
              {metrics.avgLoss ? formatCurrency(metrics.avgLoss) : 'N/A'}
            </Text>
          </View>
        </View>
      </View>
    );
  }, [selectedBacktest]);

  if (loading && !selectedBacktest) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Loading backtest...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Show list view if no specific backtest is selected
  if (!selectedBacktest) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={handleBack}
            >
              <Icon name="arrow-left" size={24} color="#111827" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Backtest Results</Text>
            <View style={{ width: 24 }} />
          </View>

          {loadingList ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#3B82F6" />
              <Text style={styles.loadingText}>Loading backtests...</Text>
            </View>
          ) : backtests.length > 0 ? (
            <View style={styles.listContainer}>
              {backtests.map((bt) => (
                <TouchableOpacity
                  key={bt.id}
                  style={styles.backtestCard}
                  onPress={() => setSelectedBacktest(bt)}
                >
                  <View style={styles.backtestHeader}>
                    <View>
                      <Text style={styles.backtestName}>
                        {bt.strategyVersion?.strategy?.name || 'Strategy'}
                      </Text>
                      <Text style={styles.backtestSymbol}>{bt.symbol}</Text>
                    </View>
                    <View style={[styles.statusBadge, { backgroundColor: getStatusColor(bt.status) + '20' }]}>
                      <Text style={[styles.statusText, { color: getStatusColor(bt.status) }]}>
                        {bt.status}
                      </Text>
                    </View>
                  </View>
                  <View style={styles.backtestMeta}>
                    <Text style={styles.backtestDate}>
                      {new Date(bt.startDate).toLocaleDateString()} - {new Date(bt.endDate).toLocaleDateString()}
                    </Text>
                    {bt.metrics?.winRate && (
                      <Text style={styles.backtestWinRate}>
                        Win Rate: {(bt.metrics.winRate * 100).toFixed(1)}%
                      </Text>
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          ) : (
            <View style={styles.emptyContainer}>
              <Icon name="bar-chart-2" size={64} color="#9CA3AF" />
              <Text style={styles.emptyText}>No backtests yet</Text>
              <Text style={styles.emptySubtext}>
                Run a backtest from a strategy detail page to see results here
              </Text>
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={handleBack}
          >
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Backtest Results</Text>
          <View style={{ width: 24 }} />
        </View>

        {/* Backtest Info */}
        <View style={styles.infoCard}>
          <View style={styles.infoHeader}>
            <View>
              <Text style={styles.infoTitle}>
                {selectedBacktest.strategyVersion?.strategy?.name || 'Strategy'}
              </Text>
              <Text style={styles.infoSubtitle}>{selectedBacktest.symbol}</Text>
            </View>
            <View style={[styles.statusBadge, { backgroundColor: getStatusColor(selectedBacktest.status) + '20' }]}>
              <Text style={[styles.statusText, { color: getStatusColor(selectedBacktest.status) }]}>
                {selectedBacktest.status}
              </Text>
            </View>
          </View>

          <View style={styles.infoMeta}>
            <View style={styles.infoMetaItem}>
              <Icon name="calendar" size={14} color="#6B7280" />
              <Text style={styles.infoMetaText}>
                {new Date(selectedBacktest.startDate).toLocaleDateString()} - {new Date(selectedBacktest.endDate).toLocaleDateString()}
              </Text>
            </View>
            <View style={styles.infoMetaItem}>
              <Icon name="clock" size={14} color="#6B7280" />
              <Text style={styles.infoMetaText}>
                {selectedBacktest.timeframe}
              </Text>
            </View>
          </View>
        </View>

        {/* Equity Curve */}
        {renderEquityCurve()}

        {/* Metrics */}
        {renderMetrics()}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6B7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    marginTop: 16,
    fontSize: 16,
    color: '#EF4444',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  backButton: {
    padding: 8,
  },
  backButtonText: {
    fontSize: 16,
    color: '#3B82F6',
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  infoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  infoSubtitle: {
    fontSize: 14,
    color: '#6B7280',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  infoMeta: {
    flexDirection: 'row',
    gap: 16,
  },
  infoMetaItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  infoMetaText: {
    marginLeft: 6,
    fontSize: 12,
    color: '#6B7280',
  },
  chartContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  chartStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  chartStat: {
    alignItems: 'center',
  },
  chartStatLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  chartStatValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  emptyChart: {
    height: 220,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
  },
  emptyChartText: {
    marginTop: 12,
    fontSize: 14,
    color: '#9CA3AF',
  },
  metricsContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  metricCard: {
    flex: 1,
    minWidth: '30%',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  detailMetrics: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  detailLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  listContainer: {
    gap: 12,
  },
  backtestCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  backtestHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  backtestName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  backtestSymbol: {
    fontSize: 14,
    color: '#6B7280',
  },
  backtestMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  backtestDate: {
    fontSize: 12,
    color: '#6B7280',
  },
  backtestWinRate: {
    fontSize: 12,
    fontWeight: '600',
    color: '#10B981',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 32,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
});

