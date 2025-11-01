import React, { useCallback, useMemo, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, ListRenderItem, Animated, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { HoldingRow } from './HoldingRow';
import { SkeletonHoldings } from './SkeletonHoldings';
import { useFadeIn } from '../utils/animationUtils';
import { measureRenderStart } from '../utils/performanceTests';

export interface Holding {
  symbol: string;
  quantity: number;
  currentPrice: number;
  totalValue: number;
  change: number;
  changePercent: number;
  name?: string; // Optional company name
}

interface PortfolioHoldingsProps {
  holdings: Holding[];
  onStockPress: (symbol: string) => void;
  onAddHoldings?: () => void; // Callback for empty state action
  onBuy?: (holding: Holding) => void; // Phase 2: Buy action
  onSell?: (holding: Holding) => void; // Phase 2: Sell action
  loading?: boolean; // Phase 3: Show skeleton while loading
}

const PortfolioHoldings: React.FC<PortfolioHoldingsProps> = ({ 
  holdings, 
  onStockPress,
  onAddHoldings,
  onBuy,
  onSell,
  loading = false,
}) => {
  // Phase 3: Fade-in animation
  const fadeOpacity = useFadeIn(300);

  // Phase 3: Performance measurement
  useEffect(() => {
    const endMeasurement = measureRenderStart('PortfolioHoldings');
    return endMeasurement;
  }, [holdings]);

  // Calculate total portfolio value (precomputed for performance)
  const totalValue = useMemo(
    () => holdings.reduce((sum, h) => sum + (h.totalValue || 0), 0),
    [holdings]
  );

  // Phase 3: Show skeleton while loading
  if (loading) {
    return <SkeletonHoldings count={holdings.length || 3} />;
  }

  // Empty state - Steve Jobs style: Inspiring, not discouraging
  if (!holdings || holdings.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <View style={styles.emptyIllustration}>
          <Icon name="trending-up" size={64} color="#007AFF" />
        </View>
        <Text style={styles.emptyTitle}>Your portfolio journey starts here</Text>
        <Text style={styles.emptySubtitle}>
          Add your first stock to begin tracking your investment performance
        </Text>
        {onAddHoldings && (
          <TouchableOpacity 
            style={styles.emptyActionButton}
            onPress={onAddHoldings}
            activeOpacity={0.8}
          >
            <Icon name="plus" size={20} color="#FFFFFF" />
            <Text style={styles.emptyActionText}>Add Your First Stock</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  // Memoized render function for performance
  const renderHolding: ListRenderItem<Holding> = useCallback(
    ({ item, index }) => {
      const allocationPercent = totalValue > 0 ? ((item.totalValue || 0) / totalValue) * 100 : 0;
      return (
        <HoldingRow
          holding={item}
          allocationPercent={allocationPercent}
          onPress={onStockPress}
          onBuy={onBuy}
          onSell={onSell}
          isLast={index === holdings.length - 1}
        />
      );
    },
    [totalValue, onStockPress, onBuy, onSell, holdings.length]
  );

  return (
    <Animated.View style={[styles.container, { opacity: fadeOpacity }]}>
      {/* Header with total value */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Portfolio Holdings</Text>
          <Text style={styles.count}>{holdings.length} {holdings.length === 1 ? 'holding' : 'holdings'}</Text>
        </View>
        {totalValue > 0 && (
          <View style={styles.totalContainer}>
            <Text style={styles.totalLabel}>Total</Text>
            <Text style={styles.totalValue}>${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Text>
          </View>
        )}
      </View>

      {/* Holdings list - Virtualized for performance */}
      <FlatList
        data={holdings}
        keyExtractor={(item) => item.symbol}
        renderItem={renderHolding}
        scrollEnabled={false} // Disable scroll since parent ScrollView handles it
        removeClippedSubviews={true}
        initialNumToRender={10}
        maxToRenderPerBatch={5}
        windowSize={5}
        ListEmptyComponent={null} // Empty state handled above
      />
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginVertical: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E5EA',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000',
    marginBottom: 4,
  },
  count: {
    fontSize: 15,
    color: '#8E8E93',
  },
  totalContainer: {
    alignItems: 'flex-end',
  },
  totalLabel: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 2,
  },
  totalValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 48,
    backgroundColor: '#fff',
    borderRadius: 16,
    marginVertical: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  emptyIllustration: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: '#F0F8FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#000',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 24,
  },
  emptyActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  emptyActionText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

export default PortfolioHoldings;
