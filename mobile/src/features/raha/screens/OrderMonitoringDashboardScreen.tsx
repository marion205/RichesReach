/**
 * Order Monitoring Dashboard
 * Real-time order status, trade history, P&L tracking, and risk monitoring
 */
import React, { useState, useMemo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
  FlatList,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery } from '@apollo/client';
import { GET_ORDER_DASHBOARD } from '../../../graphql/orders';
import logger from '../../../utils/logger';
import type {
  ExtendedQuery,
  OrderDashboardType,
} from '../../../generated/graphql';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { LoadMoreButton } from '../../../components/LoadMoreButton';
import { optimizedFlatListProps, createItemLayout } from '../../../utils/performanceOptimizations';

const { width } = Dimensions.get('window');

interface OrderMonitoringDashboardScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
  onBack?: () => void;
}

export default function OrderMonitoringDashboardScreen({
  navigateTo,
  onBack,
}: OrderMonitoringDashboardScreenProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [ordersOffset, setOrdersOffset] = useState(0);
  const [filledOrdersOffset, setFilledOrdersOffset] = useState(0);
  const [rahaOrdersOffset, setRahaOrdersOffset] = useState(0);
  const [loadingMoreOrders, setLoadingMoreOrders] = useState(false);
  const [loadingMoreFilled, setLoadingMoreFilled] = useState(false);
  const [loadingMoreRaha, setLoadingMoreRaha] = useState(false);

  const PAGE_SIZE = 20;

  // ✅ Typed query (now using generated types!)
  type OrderDashboardQuery = Pick<ExtendedQuery, 'orderDashboard'>;
  
  const { data, loading, error, refetch, fetchMore } = useQuery<OrderDashboardQuery>(GET_ORDER_DASHBOARD, {
    variables: {
      ordersLimit: PAGE_SIZE,
      ordersOffset: 0,
      filledOrdersLimit: PAGE_SIZE,
      filledOrdersOffset: 0,
      rahaOrdersLimit: PAGE_SIZE,
      rahaOrdersOffset: 0,
    },
    pollInterval: 30000, // Poll every 30 seconds for real-time updates
    fetchPolicy: 'cache-and-network',
    nextFetchPolicy: 'cache-first', // Use cache for subsequent loads
    notifyOnNetworkStatusChange: true,
    errorPolicy: 'all',
  });

  const dashboard = useMemo(() => data?.orderDashboard, [data?.orderDashboard]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    setOrdersOffset(0);
    setFilledOrdersOffset(0);
    setRahaOrdersOffset(0);
    await refetch({
      ordersOffset: 0,
      filledOrdersOffset: 0,
      rahaOrdersOffset: 0,
    });
    setRefreshing(false);
  }, [refetch]);

  // Load more orders
  const loadMoreOrders = useCallback(async () => {
    if (loadingMoreOrders || !dashboard?.ordersHasMore) {
      return;
    }

    setLoadingMoreOrders(true);
    const newOffset = ordersOffset + PAGE_SIZE;

    try {
      await fetchMore({
        variables: {
          ordersLimit: PAGE_SIZE,
          ordersOffset: newOffset,
          filledOrdersLimit: PAGE_SIZE,
          filledOrdersOffset: filledOrdersOffset,
          rahaOrdersLimit: PAGE_SIZE,
          rahaOrdersOffset: rahaOrdersOffset,
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult?.orderDashboard) {
            return prev;
          }
          return {
            ...prev,
            orderDashboard: {
              ...prev.orderDashboard,
              orders: [
                ...(prev.orderDashboard.orders || []),
                ...(fetchMoreResult.orderDashboard.orders || []),
              ],
              ordersHasMore: fetchMoreResult.orderDashboard.ordersHasMore,
            },
          };
        },
      });
      setOrdersOffset(newOffset);
    } catch (err) {
      logger.error('Error loading more orders:', err);
    } finally {
      setLoadingMoreOrders(false);
    }
  }, [
    fetchMore,
    dashboard?.ordersHasMore,
    ordersOffset,
    filledOrdersOffset,
    rahaOrdersOffset,
    loadingMoreOrders,
  ]);

  // Load more filled orders
  const loadMoreFilledOrders = useCallback(async () => {
    if (loadingMoreFilled || !dashboard?.filledOrdersHasMore) {
      return;
    }

    setLoadingMoreFilled(true);
    const newOffset = filledOrdersOffset + PAGE_SIZE;

    try {
      await fetchMore({
        variables: {
          ordersLimit: PAGE_SIZE,
          ordersOffset: ordersOffset,
          filledOrdersLimit: PAGE_SIZE,
          filledOrdersOffset: newOffset,
          rahaOrdersLimit: PAGE_SIZE,
          rahaOrdersOffset: rahaOrdersOffset,
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult?.orderDashboard) {
            return prev;
          }
          return {
            ...prev,
            orderDashboard: {
              ...prev.orderDashboard,
              filledOrders: [
                ...(prev.orderDashboard.filledOrders || []),
                ...(fetchMoreResult.orderDashboard.filledOrders || []),
              ],
              filledOrdersHasMore: fetchMoreResult.orderDashboard.filledOrdersHasMore,
            },
          };
        },
      });
      setFilledOrdersOffset(newOffset);
    } catch (err) {
      logger.error('Error loading more filled orders:', err);
    } finally {
      setLoadingMoreFilled(false);
    }
  }, [
    fetchMore,
    dashboard?.filledOrdersHasMore,
    ordersOffset,
    filledOrdersOffset,
    rahaOrdersOffset,
    loadingMoreFilled,
  ]);

  // Load more RAHA orders
  const loadMoreRahaOrders = useCallback(async () => {
    if (loadingMoreRaha || !dashboard?.rahaOrdersHasMore) {
      return;
    }

    setLoadingMoreRaha(true);
    const newOffset = rahaOrdersOffset + PAGE_SIZE;

    try {
      await fetchMore({
        variables: {
          ordersLimit: PAGE_SIZE,
          ordersOffset: ordersOffset,
          filledOrdersLimit: PAGE_SIZE,
          filledOrdersOffset: filledOrdersOffset,
          rahaOrdersLimit: PAGE_SIZE,
          rahaOrdersOffset: newOffset,
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult?.orderDashboard) {
            return prev;
          }
          return {
            ...prev,
            orderDashboard: {
              ...prev.orderDashboard,
              rahaOrders: [
                ...(prev.orderDashboard.rahaOrders || []),
                ...(fetchMoreResult.orderDashboard.rahaOrders || []),
              ],
              rahaOrdersHasMore: fetchMoreResult.orderDashboard.rahaOrdersHasMore,
            },
          };
        },
      });
      setRahaOrdersOffset(newOffset);
    } catch (err) {
      logger.error('Error loading more RAHA orders:', err);
    } finally {
      setLoadingMoreRaha(false);
    }
  }, [
    fetchMore,
    dashboard?.rahaOrdersHasMore,
    ordersOffset,
    filledOrdersOffset,
    rahaOrdersOffset,
    loadingMoreRaha,
  ]);

  // Memoize format functions to prevent recreation on every render
  const formatCurrency = useCallback((value: number | null | undefined) => {
    if (value === null || value === undefined) {
      return '$0.00';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  }, []);

  const formatPercent = useCallback((value: number | null | undefined) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '0.00%';
    }
    const numValue = typeof value === 'number' ? value : parseFloat(String(value));
    if (isNaN(numValue)) {
      return '0.00%';
    }
    return `${numValue >= 0 ? '+' : ''}${numValue.toFixed(2)}%`;
  }, []);

  // Memoize status color function
  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'FILLED':
        return '#10B981'; // Green
      case 'PARTIALLY_FILLED':
        return '#F59E0B'; // Amber
      case 'NEW':
      case 'ACCEPTED':
      case 'PENDING_NEW':
        return '#3B82F6'; // Blue
      case 'CANCELED':
      case 'REJECTED':
      case 'EXPIRED':
        return '#6B7280'; // Gray
      default:
        return '#6B7280';
    }
  }, []);

  if (loading && !data) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1D4ED8" />
          <Text style={styles.loadingText}>Loading order dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#EF4444" />
          <Text style={styles.errorText}>Error loading dashboard</Text>
          <Text style={styles.errorDetail}>{error.message}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Memoize dashboard data to prevent unnecessary recalculations
  const metrics = useMemo(() => dashboard?.metrics, [dashboard?.metrics]);
  const riskStatus = useMemo(() => dashboard?.riskStatus, [dashboard?.riskStatus]);
  const activeOrders = useMemo(() => dashboard?.activeOrders || [], [dashboard?.activeOrders]);
  const filledOrders = useMemo(() => dashboard?.filledOrders || [], [dashboard?.filledOrders]);
  const positions = useMemo(() => dashboard?.positions || [], [dashboard?.positions]);
  const rahaOrders = useMemo(() => dashboard?.rahaOrders || [], [dashboard?.rahaOrders]);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={onBack}>
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Order Monitor</Text>
          <View style={{ width: 24 }} />
        </View>

        {/* Risk Status Banner */}
        {riskStatus && (
          <View
            style={[
              styles.riskBanner,
              riskStatus.dailyLimitWarning || riskStatus.positionLimitWarning
                ? styles.riskBannerWarning
                : styles.riskBannerNormal,
            ]}
          >
            <Icon
              name={
                riskStatus.dailyLimitWarning || riskStatus.positionLimitWarning
                  ? 'alert-triangle'
                  : 'shield'
              }
              size={20}
              color={
                riskStatus.dailyLimitWarning || riskStatus.positionLimitWarning
                  ? '#F59E0B'
                  : '#10B981'
              }
            />
            <View style={styles.riskBannerContent}>
              <Text style={styles.riskBannerTitle}>
                {riskStatus.dailyLimitWarning || riskStatus.positionLimitWarning
                  ? 'Approaching Limits'
                  : 'Risk Status: Normal'}
              </Text>
              <Text style={styles.riskBannerText}>
                Daily: {formatCurrency(riskStatus.dailyNotionalUsed)} /{' '}
                {formatCurrency(riskStatus.dailyNotionalLimit)} • Positions:{' '}
                {riskStatus.activePositionsCount} / {riskStatus.maxPositions}
              </Text>
            </View>
          </View>
        )}

        {/* Performance Metrics */}
        {metrics && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Performance</Text>
            <View style={styles.metricsGrid}>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Total P&L</Text>
                <Text
                  style={[
                    styles.metricValue,
                    {
                      color: (metrics.totalPnl || 0) >= 0 ? '#10B981' : '#EF4444',
                    },
                  ]}
                >
                  {formatCurrency(metrics.totalPnl)}
                </Text>
                <Text
                  style={[
                    styles.metricSubtext,
                    {
                      color: (metrics.totalPnlPercent || 0) >= 0 ? '#10B981' : '#EF4444',
                    },
                  ]}
                >
                  {formatPercent(metrics.totalPnlPercent)}
                </Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Win Rate</Text>
                <Text style={styles.metricValue}>
                  {metrics.winRate != null && !isNaN(metrics.winRate)
                    ? metrics.winRate.toFixed(1)
                    : '0.0'}
                  %
                </Text>
                <Text style={styles.metricSubtext}>
                  {metrics.winningTrades || 0}W / {metrics.losingTrades || 0}L
                </Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Profit Factor</Text>
                <Text style={styles.metricValue}>
                  {metrics.profitFactor != null && !isNaN(metrics.profitFactor)
                    ? metrics.profitFactor.toFixed(2)
                    : '0.00'}
                </Text>
                <Text style={styles.metricSubtext}>Avg Win: {formatCurrency(metrics.avgWin)}</Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Total Trades</Text>
                <Text style={styles.metricValue}>{metrics.totalTrades || 0}</Text>
                <Text style={styles.metricSubtext}>
                  Largest: {formatCurrency(metrics.largestWin)}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Active Orders */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Active Orders ({activeOrders.length})</Text>
            {activeOrders.length > 0 && (
              <TouchableOpacity onPress={() => refetch()}>
                <Icon name="refresh-cw" size={18} color="#6B7280" />
              </TouchableOpacity>
            )}
          </View>
          {activeOrders.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="check-circle" size={48} color="#9CA3AF" />
              <Text style={styles.emptyStateText}>No active orders</Text>
            </View>
          ) : (
            <FlatList
              data={activeOrders}
              renderItem={renderActiveOrder}
              keyExtractor={item => item.id}
              scrollEnabled={false}
              {...optimizedFlatListProps}
              getItemLayout={orderItemLayout}
              ListEmptyComponent={
                <View style={styles.emptyState}>
                  <Icon name="check-circle" size={48} color="#9CA3AF" />
                  <Text style={styles.emptyStateText}>No active orders</Text>
                </View>
              }
            />
          )}
        </View>

        {/* Recent Trades */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Trades ({filledOrders.length})</Text>
          {filledOrders.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="trending-up" size={48} color="#9CA3AF" />
              <Text style={styles.emptyStateText}>No completed trades yet</Text>
            </View>
          ) : (
            <>
              <FlatList
                data={filledOrders}
                renderItem={renderFilledOrder}
                keyExtractor={item => item.id}
                scrollEnabled={false}
                {...optimizedFlatListProps}
                getItemLayout={tradeItemLayout}
                ListEmptyComponent={
                  <View style={styles.emptyState}>
                    <Icon name="trending-up" size={48} color="#9CA3AF" />
                    <Text style={styles.emptyStateText}>No completed trades yet</Text>
                  </View>
                }
              />
              <LoadMoreButton
                onPress={loadMoreFilledOrders}
                loading={loadingMoreFilled}
                hasMore={dashboard?.filledOrdersHasMore || false}
                label="Load More Trades"
              />
            </>
          )}
        </View>

        {/* RAHA Auto-Trades */}
        {rahaOrders.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>RAHA Auto-Trades ({rahaOrders.length})</Text>
              <Icon name="zap" size={20} color="#F59E0B" />
            </View>
            <>
              <FlatList
                data={rahaOrders}
                renderItem={renderRahaOrder}
                keyExtractor={item => item.id}
                scrollEnabled={false}
                {...optimizedFlatListProps}
                getItemLayout={rahaOrderItemLayout}
              />
              <LoadMoreButton
                onPress={loadMoreRahaOrders}
                loading={loadingMoreRaha}
                hasMore={dashboard?.rahaOrdersHasMore || false}
                label="Load More RAHA Trades"
              />
            </>
          </View>
        )}

        {/* Positions */}
        {positions.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Open Positions ({positions.length})</Text>
            {positions.map((position: any) => (
              <View key={position.id} style={styles.positionCard}>
                <View style={styles.positionHeader}>
                  <Text style={styles.positionSymbol}>{position.symbol}</Text>
                  <Text
                    style={[
                      styles.positionPnl,
                      {
                        color: (position.unrealizedPl || 0) >= 0 ? '#10B981' : '#EF4444',
                      },
                    ]}
                  >
                    {formatCurrency(position.unrealizedPl)} (
                    {formatPercent(position.unrealizedPlpc)})
                  </Text>
                </View>
                <View style={styles.positionDetails}>
                  <View style={styles.positionDetailRow}>
                    <Text style={styles.positionDetailLabel}>Qty:</Text>
                    <Text style={styles.positionDetailValue}>{position.qty}</Text>
                  </View>
                  <View style={styles.positionDetailRow}>
                    <Text style={styles.positionDetailLabel}>Avg Entry:</Text>
                    <Text style={styles.positionDetailValue}>
                      {formatCurrency(position.avgEntryPrice)}
                    </Text>
                  </View>
                  <View style={styles.positionDetailRow}>
                    <Text style={styles.positionDetailLabel}>Current:</Text>
                    <Text style={styles.positionDetailValue}>
                      {formatCurrency(position.currentPrice)}
                    </Text>
                  </View>
                  <View style={styles.positionDetailRow}>
                    <Text style={styles.positionDetailLabel}>Value:</Text>
                    <Text style={styles.positionDetailValue}>
                      {formatCurrency(position.marketValue)}
                    </Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#6B7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#EF4444',
    marginTop: 16,
  },
  errorDetail: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 20,
    backgroundColor: '#1D4ED8',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingBottom: 32,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  riskBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    margin: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  riskBannerNormal: {
    backgroundColor: '#ECFDF5',
    borderColor: '#10B981',
  },
  riskBannerWarning: {
    backgroundColor: '#FFFBEB',
    borderColor: '#F59E0B',
  },
  riskBannerContent: {
    flex: 1,
    marginLeft: 12,
  },
  riskBannerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  riskBannerText: {
    fontSize: 14,
    color: '#6B7280',
  },
  section: {
    backgroundColor: '#FFFFFF',
    marginTop: 16,
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
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
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 2,
  },
  metricSubtext: {
    fontSize: 12,
    color: '#6B7280',
  },
  emptyState: {
    alignItems: 'center',
    padding: 32,
  },
  emptyStateText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6B7280',
  },
  orderCard: {
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  orderSymbolContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  orderSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  orderSideBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  orderSideText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  rahaBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    gap: 4,
  },
  rahaBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#92400E',
  },
  rahaBadgeSmall: {
    backgroundColor: '#FEF3C7',
    padding: 4,
    borderRadius: 4,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
  },
  orderDetails: {
    gap: 4,
  },
  orderDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  orderDetailLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  orderDetailValue: {
    fontSize: 12,
    fontWeight: '500',
    color: '#111827',
  },
  tradeCard: {
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  tradeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  tradeSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  tradeTime: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  tradeSideContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tradeSideBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  tradeSideText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  tradeDetails: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 8,
  },
  tradeDetailRow: {
    flexDirection: 'row',
    gap: 4,
  },
  tradeDetailLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  tradeDetailValue: {
    fontSize: 12,
    fontWeight: '500',
    color: '#111827',
  },
  rahaOrderCard: {
    backgroundColor: '#FFFBEB',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#FCD34D',
  },
  rahaOrderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  rahaOrderSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  rahaOrderStatus: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  rahaOrderStatusText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#92400E',
  },
  rahaSignalInfo: {
    marginBottom: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#FDE68A',
  },
  rahaSignalText: {
    fontSize: 12,
    color: '#92400E',
    marginBottom: 4,
  },
  rahaStrategyText: {
    fontSize: 11,
    color: '#A16207',
  },
  rahaOrderDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rahaOrderDetail: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  rahaOrderTime: {
    fontSize: 11,
    color: '#6B7280',
  },
  positionCard: {
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  positionSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  positionPnl: {
    fontSize: 14,
    fontWeight: '600',
  },
  positionDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
  },
  positionDetailRow: {
    flexDirection: 'row',
    gap: 4,
  },
  positionDetailLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  positionDetailValue: {
    fontSize: 12,
    fontWeight: '500',
    color: '#111827',
  },
});
