import React, { useState, useMemo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Dimensions,
  FlatList,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery } from '@apollo/client';
import { GET_STRATEGY_DASHBOARD } from '../../../graphql/raha';
import type {
  ExtendedQueryStrategyDashboardQuery,
} from '../../../generated/graphql';
import { BarChart } from 'react-native-chart-kit';
import logger from '../../../utils/logger';
import { optimizedFlatListProps, createItemLayout } from '../../../utils/performanceOptimizations';

const { width } = Dimensions.get('window');

interface StrategyDashboardScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
  onBack?: () => void;
}

interface StrategyData {
  strategy_id: string;
  strategy_name: string;
  strategy_version_id: string;
  category: string;
  enabled: boolean;
  total_signals: number;
  metrics: {
    win_rate: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    total_pnl_dollars: number;
    total_pnl_percent: number;
    sharpe_ratio?: number;
    sortino_ratio?: number;
    max_drawdown?: number;
    expectancy: number;
    avg_win: number;
    avg_loss: number;
  };
  latest_backtest?: {
    id: string;
    symbol: string;
    completed_at: string;
  };
  equity_curve: Array<{ timestamp: string; equity: number }>;
}

export default function StrategyDashboardScreen({
  navigateTo,
  onBack,
}: StrategyDashboardScreenProps = {}) {
  const [selectedPeriod, setSelectedPeriod] = useState<'daily' | 'weekly' | 'monthly' | 'all'>(
    'all',
  );
  const [selectedMetric, setSelectedMetric] = useState<'win_rate' | 'pnl' | 'sharpe'>('win_rate');

  // ✅ Now using typed query (returns JSONString array, so we parse it)
  const { data, loading, error, refetch } = useQuery<ExtendedQueryStrategyDashboardQuery>(
    GET_STRATEGY_DASHBOARD
  );

  const strategies: StrategyData[] = useMemo(() => {
    if (!data?.strategyDashboard) {
      return [];
    }

    try {
      const parsed = data.strategyDashboard.map((item: string) => {
        const parsedItem = JSON.parse(item);
        // Ensure all required fields have defaults
        return {
          strategy_id: parsedItem.strategy_id || '',
          strategy_name: parsedItem.strategy_name || 'Unknown Strategy',
          strategy_version_id: parsedItem.strategy_version_id || '',
          category: parsedItem.category || 'N/A',
          enabled: parsedItem.enabled !== undefined ? parsedItem.enabled : false,
          total_signals: parsedItem.total_signals || 0,
          metrics: parsedItem.metrics || {
            win_rate: 0,
            total_trades: 0,
            winning_trades: 0,
            losing_trades: 0,
            total_pnl_dollars: 0,
            total_pnl_percent: 0,
            sharpe_ratio: null,
            sortino_ratio: null,
            max_drawdown: null,
            expectancy: 0,
            avg_win: 0,
            avg_loss: 0,
          },
          latest_backtest: parsedItem.latest_backtest || null,
          equity_curve: parsedItem.equity_curve || [],
        };
      });
      logger.log('📊 Parsed strategies:', parsed.length, parsed);
      return parsed;
    } catch (e) {
      logger.error('Error parsing dashboard data:', e);
      return [];
    }
  }, [data]);

  const handleBack = useCallback(() => {
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
  }, [onBack, navigateTo]);

  // Memoized render function for strategy list items
  const renderStrategyItem = useCallback(
    ({ item: strategy }: { item: StrategyData }) => (
      <TouchableOpacity
        style={styles.strategyCard}
        onPress={() => {
          if (navigateTo) {
            navigateTo('raha-strategy-detail', {
              strategyId: strategy.strategy_id,
            });
          }
        }}
      >
        <View style={styles.strategyHeader}>
          <View style={styles.strategyHeaderLeft}>
            <Text style={styles.strategyName}>{strategy.strategy_name || 'Unknown Strategy'}</Text>
            <Text style={styles.strategyCategory}>{strategy.category || 'N/A'}</Text>
          </View>
          <View style={styles.strategyHeaderRight}>
            <View style={[styles.statusBadge, strategy.enabled && styles.statusBadgeActive]}>
              <Text style={[styles.statusText, strategy.enabled && styles.statusTextActive]}>
                {strategy.enabled ? 'Active' : 'Inactive'}
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.strategyMetrics}>
          <View style={styles.metricRow}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Win Rate</Text>
              <Text style={styles.metricValue}>
                {strategy.metrics?.win_rate?.toFixed(1) || '0.0'}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Total Trades</Text>
              <Text style={styles.metricValue}>{strategy.metrics?.total_trades || 0}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>P&L</Text>
              <Text
                style={[
                  styles.metricValue,
                  {
                    color: (strategy.metrics?.total_pnl_dollars || 0) >= 0 ? '#10B981' : '#EF4444',
                  },
                ]}
              >
                ${(strategy.metrics?.total_pnl_dollars || 0).toFixed(2)}
              </Text>
            </View>
          </View>

          {strategy.metrics?.sharpe_ratio && (
            <View style={styles.metricRow}>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Sharpe Ratio</Text>
                <Text style={styles.metricValue}>{strategy.metrics.sharpe_ratio.toFixed(2)}</Text>
              </View>
            </View>
          )}
        </View>
      </TouchableOpacity>
    ),
    [navigateTo],
  );

  // Item layout for fixed-height strategy cards
  const strategyItemLayout = useMemo(() => createItemLayout(150), []);

  // Prepare chart data
  const winRateData = useMemo(() => {
    if (strategies.length === 0) {
      return null;
    }

    return {
      labels: strategies.map(s => (s.strategy_name || 'Unknown').substring(0, 10)),
      datasets: [
        {
          data: strategies.map(s => s.metrics?.win_rate || 0),
        },
      ],
    };
  }, [strategies]);

  const pnlData = useMemo(() => {
    if (strategies.length === 0) {
      return null;
    }

    return {
      labels: strategies.map(s => (s.strategy_name || 'Unknown').substring(0, 10)),
      datasets: [
        {
          data: strategies.map(s => s.metrics?.total_pnl_dollars || 0),
        },
      ],
    };
  }, [strategies]);

  const equityCurveData = useMemo(() => {
    // Combine all equity curves for comparison
    const allCurves: Array<{
      strategy: string;
      data: Array<{ timestamp: string; equity: number }>;
    }> = [];

    strategies.forEach(strategy => {
      if (strategy.equity_curve && strategy.equity_curve.length > 0) {
        allCurves.push({
          strategy: strategy.strategy_name,
          data: strategy.equity_curve,
        });
      }
    });

    return allCurves;
  }, [strategies]);

  const chartConfig = {
    backgroundColor: '#FFFFFF',
    backgroundGradientFrom: '#FFFFFF',
    backgroundGradientTo: '#FFFFFF',
    decimalPlaces: 1,
    color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(17, 24, 39, ${opacity})`,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: '#3B82F6',
    },
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Strategy Dashboard</Text>
          <View style={{ width: 24 }} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Loading dashboard data...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Strategy Dashboard</Text>
          <View style={{ width: 24 }} />
        </View>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#EF4444" />
          <Text style={styles.errorTitle}>Error Loading Dashboard</Text>
          <Text style={styles.errorText}>{error.message}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  if (strategies.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Strategy Dashboard</Text>
          <View style={{ width: 24 }} />
        </View>
        <View style={styles.emptyContainer}>
          <Icon name="trending-up" size={48} color="#9CA3AF" />
          <Text style={styles.emptyTitle}>No Strategies Enabled</Text>
          <Text style={styles.emptyText}>
            Enable strategies in the Strategy Store to see performance analytics here.
          </Text>
          <TouchableOpacity
            style={styles.emptyButton}
            onPress={() => {
              if (navigateTo) {
                navigateTo('pro-labs', { view: 'strategies' });
              }
            }}
          >
            <Text style={styles.emptyButtonText}>Go to Strategy Store</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <Icon name="arrow-left" size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Strategy Dashboard</Text>
        <TouchableOpacity onPress={() => refetch()}>
          <Icon name="refresh-cw" size={24} color="#3B82F6" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Summary Cards */}
        <View style={styles.summarySection}>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryLabel}>Total Strategies</Text>
            <Text style={styles.summaryValue}>{strategies.length}</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryLabel}>Total Signals</Text>
            <Text style={styles.summaryValue}>
              {strategies.reduce((sum, s) => sum + (s.total_signals || 0), 0)}
            </Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryLabel}>Avg Win Rate</Text>
            <Text style={styles.summaryValue}>
              {strategies.length > 0
                ? `${(
                    strategies.reduce((sum, s) => sum + (s.metrics?.win_rate || 0), 0) /
                    strategies.length
                  ).toFixed(1)}%`
                : '0%'}
            </Text>
          </View>
        </View>

        {/* Metric Selector */}
        <View style={styles.metricSelector}>
          <TouchableOpacity
            style={[
              styles.metricButton,
              selectedMetric === 'win_rate' && styles.metricButtonActive,
            ]}
            onPress={() => setSelectedMetric('win_rate')}
          >
            <Text
              style={[
                styles.metricButtonText,
                selectedMetric === 'win_rate' && styles.metricButtonTextActive,
              ]}
            >
              Win Rate
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.metricButton, selectedMetric === 'pnl' && styles.metricButtonActive]}
            onPress={() => setSelectedMetric('pnl')}
          >
            <Text
              style={[
                styles.metricButtonText,
                selectedMetric === 'pnl' && styles.metricButtonTextActive,
              ]}
            >
              P&L
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.metricButton, selectedMetric === 'sharpe' && styles.metricButtonActive]}
            onPress={() => setSelectedMetric('sharpe')}
          >
            <Text
              style={[
                styles.metricButtonText,
                selectedMetric === 'sharpe' && styles.metricButtonTextActive,
              ]}
            >
              Sharpe
            </Text>
          </TouchableOpacity>
        </View>

        {/* Charts */}
        {selectedMetric === 'win_rate' && winRateData && (
          <View style={styles.chartContainer}>
            <Text style={styles.chartTitle}>Win Rate Comparison</Text>
            <BarChart
              data={winRateData}
              width={width - 32}
              height={220}
              chartConfig={chartConfig}
              verticalLabelRotation={30}
              showValuesOnTopOfBars
              fromZero
            />
          </View>
        )}

        {selectedMetric === 'pnl' && pnlData && (
          <View style={styles.chartContainer}>
            <Text style={styles.chartTitle}>Total P&L Comparison</Text>
            <BarChart
              data={pnlData}
              width={width - 32}
              height={220}
              chartConfig={{
                ...chartConfig,
                color: (opacity = 1) => `rgba(16, 185, 129, ${opacity})`,
              }}
              verticalLabelRotation={30}
              showValuesOnTopOfBars
            />
          </View>
        )}

        {selectedMetric === 'sharpe' && strategies.some(s => s.metrics?.sharpe_ratio) && (
          <View style={styles.chartContainer}>
            <Text style={styles.chartTitle}>Sharpe Ratio Comparison</Text>
            <BarChart
              data={{
                labels: strategies.map(s => (s.strategy_name || 'Unknown').substring(0, 10)),
                datasets: [
                  {
                    data: strategies.map(s => s.metrics?.sharpe_ratio || 0),
                  },
                ],
              }}
              width={width - 32}
              height={220}
              chartConfig={{
                ...chartConfig,
                color: (opacity = 1) => `rgba(139, 92, 246, ${opacity})`,
              }}
              verticalLabelRotation={30}
              showValuesOnTopOfBars
            />
          </View>
        )}

        {/* Strategy List */}
        <View style={styles.strategiesSection}>
          <Text style={styles.sectionTitle}>Strategy Performance</Text>

          {strategies.map(strategy => (
            <TouchableOpacity
              key={strategy.strategy_id}
              style={styles.strategyCard}
              onPress={() => {
                if (navigateTo) {
                  navigateTo('raha-strategy-detail', {
                    strategyId: strategy.strategy_id,
                  });
                }
              }}
            >
              <View style={styles.strategyHeader}>
                <View style={styles.strategyHeaderLeft}>
                  <Text style={styles.strategyName}>
                    {strategy.strategy_name || 'Unknown Strategy'}
                  </Text>
                  <Text style={styles.strategyCategory}>{strategy.category || 'N/A'}</Text>
                </View>
                <View style={styles.strategyHeaderRight}>
                  <View style={[styles.statusBadge, strategy.enabled && styles.statusBadgeActive]}>
                    <Text style={[styles.statusText, strategy.enabled && styles.statusTextActive]}>
                      {strategy.enabled ? 'Active' : 'Inactive'}
                    </Text>
                  </View>
                </View>
              </View>

              <View style={styles.strategyMetrics}>
                <View style={styles.metricRow}>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Win Rate</Text>
                    <Text style={styles.metricValue}>
                      {strategy.metrics?.win_rate?.toFixed(1) || '0.0'}%
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Total Trades</Text>
                    <Text style={styles.metricValue}>{strategy.metrics?.total_trades || 0}</Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>P&L</Text>
                    <Text
                      style={[
                        styles.metricValue,
                        (strategy.metrics?.total_pnl_dollars || 0) >= 0
                          ? styles.positiveValue
                          : styles.negativeValue,
                      ]}
                    >
                      ${(strategy.metrics?.total_pnl_dollars || 0).toFixed(2)}
                    </Text>
                  </View>
                </View>

                {strategy.metrics?.sharpe_ratio && (
                  <View style={styles.metricRow}>
                    <View style={styles.metricItem}>
                      <Text style={styles.metricLabel}>Sharpe</Text>
                      <Text style={styles.metricValue}>
                        {strategy.metrics.sharpe_ratio.toFixed(2)}
                      </Text>
                    </View>
                    <View style={styles.metricItem}>
                      <Text style={styles.metricLabel}>Expectancy</Text>
                      <Text style={styles.metricValue}>
                        ${(strategy.metrics?.expectancy || 0).toFixed(2)}
                      </Text>
                    </View>
                    {strategy.metrics?.max_drawdown && (
                      <View style={styles.metricItem}>
                        <Text style={styles.metricLabel}>Max DD</Text>
                        <Text style={styles.metricValue}>
                          {(strategy.metrics.max_drawdown * 100).toFixed(1)}%
                        </Text>
                      </View>
                    )}
                  </View>
                )}
              </View>

              {strategy.latest_backtest && (
                <View style={styles.backtestInfo}>
                  <Icon name="bar-chart-2" size={14} color="#6B7280" />
                  <Text style={styles.backtestText}>
                    Latest backtest: {strategy.latest_backtest.symbol} (
                    {new Date(strategy.latest_backtest.completed_at).toLocaleDateString()})
                  </Text>
                </View>
              )}
            </TouchableOpacity>
          ))}
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  emptyButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  emptyButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  summarySection: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  metricSelector: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 8,
  },
  metricButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
  },
  metricButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  metricButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6B7280',
  },
  metricButtonTextActive: {
    color: '#FFFFFF',
  },
  chartContainer: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginBottom: 24,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  strategiesSection: {
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  strategyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  strategyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  strategyHeaderLeft: {
    flex: 1,
  },
  strategyName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  strategyCategory: {
    fontSize: 12,
    color: '#6B7280',
  },
  strategyHeaderRight: {
    marginLeft: 12,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: '#F3F4F6',
  },
  statusBadgeActive: {
    backgroundColor: '#D1FAE5',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280',
  },
  statusTextActive: {
    color: '#065F46',
  },
  strategyMetrics: {
    marginTop: 12,
  },
  metricRow: {
    flexDirection: 'row',
    marginBottom: 12,
    gap: 12,
  },
  metricItem: {
    flex: 1,
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  positiveValue: {
    color: '#10B981',
  },
  negativeValue: {
    color: '#EF4444',
  },
  backtestInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 6,
  },
  backtestText: {
    fontSize: 12,
    color: '#6B7280',
  },
});
