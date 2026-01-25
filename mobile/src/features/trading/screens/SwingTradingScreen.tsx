import React, { useCallback, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { GET_SWING_TRADING_PICKS } from '../../../graphql/swingTrading';
import Icon from 'react-native-vector-icons/Feather';
import { ExecutionSuggestionCard } from '../components/ExecutionSuggestionCard';
import * as Haptics from 'expo-haptics';
import logger from '../../../utils/logger';

type SwingStrategy = 'MOMENTUM' | 'BREAKOUT' | 'MEAN_REVERSION';
type Side = 'LONG' | 'SHORT';

interface SwingTradingPick {
  symbol: string;
  side: Side;
  strategy: string;
  score: number;
  entryPrice: number;
  features: {
    momentum5d?: number;
    rvol5d?: number;
    atr1d?: number;
    breakoutStrength?: number;
    rsi?: number;
    distFromMA20?: number;
    reversionPotential?: number;
    high20d?: number;
  };
  risk: {
    atr1d: number;
    sizeShares: number;
    stop: number;
    targets: number[];
    holdDays: number;
  };
  notes: string;
}

interface SwingTradingData {
  asOf: string;
  strategy: string;
  picks: SwingTradingPick[];
  universeSize: number;
  universeSource?: string;
}

const C = {
  bg: '#0A0A0A',
  card: '#1A1A1A',
  text: '#FFFFFF',
  sub: '#888888',
  primary: '#00D4FF',
  success: '#00FF88',
  danger: '#FF4444',
  warning: '#FFAA00',
};

export default function SwingTradingScreen() {
  const [strategy, setStrategy] = useState<SwingStrategy>('MOMENTUM');
  const [refreshing, setRefreshing] = useState(false);

  const { data, loading, error, refetch } = useQuery(GET_SWING_TRADING_PICKS, {
    variables: { strategy },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const swingData: SwingTradingData | null = data?.swingTradingPicks ?? null;
  const picks = useMemo(() => {
    return swingData?.picks || [];
  }, [swingData?.picks]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch();
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (err) {
      logger.error('Refresh failed:', err);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setRefreshing(false);
    }
  }, [refetch]);

  const switchStrategy = useCallback(async (newStrategy: SwingStrategy) => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setStrategy(newStrategy);
  }, []);

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const formatPercent = (pct: number) => {
    const sign = pct >= 0 ? '+' : '';
    return `${sign}${(pct * 100).toFixed(2)}%`;
  };

  const getStrategyLabel = (s: string) => {
    switch (s) {
      case 'MOMENTUM': return 'Momentum';
      case 'BREAKOUT': return 'Breakout';
      case 'MEAN_REVERSION': return 'Mean Reversion';
      default: return s;
    }
  };

  const getStrategyDescription = (s: SwingStrategy) => {
    switch (s) {
      case 'MOMENTUM':
        return 'Catch multi-day moves • 3-day hold';
      case 'BREAKOUT':
        return 'Enter on EOD breakouts • 4-day hold';
      case 'MEAN_REVERSION':
        return 'Fade extremes • 2-day hold';
      default:
        return '';
    }
  };

  const renderPick = ({ item: pick }: { item: SwingTradingPick }) => {
    const isLong = pick.side === 'LONG';
    const stopDistance = Math.abs((pick.entryPrice - pick.risk.stop) / pick.entryPrice);
    const target1Distance = Math.abs((pick.risk.targets[0] - pick.entryPrice) / pick.entryPrice);

    return (
      <View style={styles.pickCard}>
        <View style={styles.pickHeader}>
          <View style={styles.symbolRow}>
            <Text style={styles.symbol}>{pick.symbol}</Text>
            <View style={[styles.sideBadge, isLong ? styles.longBadge : styles.shortBadge]}>
              <Text style={styles.sideText}>{pick.side}</Text>
            </View>
          </View>
          <View style={styles.scoreRow}>
            <Icon name="trending-up" size={16} color={C.primary} />
            <Text style={styles.score}>{pick.score.toFixed(1)}</Text>
          </View>
        </View>

        <View style={styles.priceRow}>
          <View>
            <Text style={styles.priceLabel}>Entry</Text>
            <Text style={styles.priceValue}>{formatPrice(pick.entryPrice)}</Text>
          </View>
          <View>
            <Text style={styles.priceLabel}>Stop</Text>
            <Text style={[styles.priceValue, styles.stopPrice]}>
              {formatPrice(pick.risk.stop)}
            </Text>
          </View>
          <View>
            <Text style={styles.priceLabel}>Target 1</Text>
            <Text style={[styles.priceValue, styles.targetPrice]}>
              {formatPrice(pick.risk.targets[0])}
            </Text>
          </View>
        </View>

        <View style={styles.metricsRow}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Hold</Text>
            <Text style={styles.metricValue}>{pick.risk.holdDays}d</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Risk</Text>
            <Text style={styles.metricValue}>{formatPercent(stopDistance)}</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Reward</Text>
            <Text style={styles.metricValue}>{formatPercent(target1Distance)}</Text>
          </View>
          {pick.features.momentum5d && (
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>5d Mom</Text>
              <Text style={styles.metricValue}>
                {formatPercent(pick.features.momentum5d)}
              </Text>
            </View>
          )}
        </View>

        {pick.notes && (
          <Text style={styles.notes}>{pick.notes}</Text>
        )}

        {/* Execution Suggestion */}
        <ExecutionSuggestionCard 
          suggestion={null}
          isRefreshing={false}
        />
      </View>
    );
  };

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Icon name="trending-down" size={48} color={C.sub} />
      <Text style={styles.emptyText}>No swing setups found</Text>
      <Text style={styles.emptySubtext}>
        No stocks meet our {getStrategyLabel(strategy).toLowerCase()} criteria right now.
        Check back later or try a different strategy.
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Swing Trading</Text>
        <Text style={styles.subtitle}>2-5 Day Holds</Text>
      </View>

      {/* Strategy Selector */}
      <View style={styles.strategySelector}>
        {(['MOMENTUM', 'BREAKOUT', 'MEAN_REVERSION'] as SwingStrategy[]).map((s) => (
          <TouchableOpacity
            key={s}
            style={[styles.strategyButton, strategy === s && styles.strategyButtonActive]}
            onPress={() => switchStrategy(s)}
          >
            <Text style={[styles.strategyText, strategy === s && styles.strategyTextActive]}>
              {getStrategyLabel(s)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Strategy Info */}
      <View style={styles.infoStrip}>
        <Icon name="info" size={14} color={C.primary} />
        <Text style={styles.infoText}>{getStrategyDescription(strategy)}</Text>
      </View>

      {/* Picks List */}
      {loading && !data ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={C.primary} />
          <Text style={styles.loadingText}>Scanning for swing setups...</Text>
        </View>
      ) : error ? (
        <View style={styles.emptyContainer}>
          <Icon name="alert-circle" size={48} color={C.danger} />
          <Text style={styles.emptyText}>Error loading picks</Text>
          <Text style={styles.emptySubtext}>{error.message}</Text>
        </View>
      ) : (
        <FlatList
          data={picks}
          renderItem={renderPick}
          keyExtractor={(item) => item.symbol}
          ListEmptyComponent={renderEmpty}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={C.primary}
            />
          }
          contentContainerStyle={styles.listContent}
        />
      )}

      {/* Footer Info */}
      {swingData && (
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Updated {new Date(swingData.asOf).toLocaleTimeString()} •{' '}
            {swingData.universeSource === 'DYNAMIC_MOVERS' ? 'Dynamic Discovery' : 'Core Universe'}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: C.bg,
  },
  header: {
    padding: 20,
    paddingTop: 60,
    backgroundColor: C.card,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: C.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: C.sub,
  },
  strategySelector: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
    backgroundColor: C.card,
  },
  strategyButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#2A2A2A',
    alignItems: 'center',
  },
  strategyButtonActive: {
    backgroundColor: C.primary,
  },
  strategyText: {
    fontSize: 14,
    fontWeight: '600',
    color: C.sub,
  },
  strategyTextActive: {
    color: C.bg,
  },
  infoStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: C.card,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  infoText: {
    fontSize: 12,
    color: C.sub,
    marginLeft: 8,
    flex: 1,
  },
  listContent: {
    padding: 16,
  },
  pickCard: {
    backgroundColor: C.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2A2A2A',
  },
  pickHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  symbolRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  symbol: {
    fontSize: 20,
    fontWeight: 'bold',
    color: C.text,
  },
  sideBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  longBadge: {
    backgroundColor: C.success + '20',
  },
  shortBadge: {
    backgroundColor: C.danger + '20',
  },
  sideText: {
    fontSize: 11,
    fontWeight: '600',
    color: C.text,
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  score: {
    fontSize: 16,
    fontWeight: '600',
    color: C.primary,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  priceLabel: {
    fontSize: 11,
    color: C.sub,
    marginBottom: 4,
  },
  priceValue: {
    fontSize: 14,
    fontWeight: '600',
    color: C.text,
  },
  stopPrice: {
    color: C.danger,
  },
  targetPrice: {
    color: C.success,
  },
  metricsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 8,
  },
  metric: {
    flex: 1,
  },
  metricLabel: {
    fontSize: 10,
    color: C.sub,
    marginBottom: 2,
  },
  metricValue: {
    fontSize: 12,
    fontWeight: '600',
    color: C.text,
  },
  notes: {
    fontSize: 11,
    color: C.sub,
    marginTop: 8,
    fontStyle: 'italic',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 14,
    color: C.sub,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: C.text,
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: C.sub,
    textAlign: 'center',
    lineHeight: 20,
  },
  footer: {
    padding: 12,
    backgroundColor: C.card,
    borderTopWidth: 1,
    borderTopColor: '#2A2A2A',
  },
  footerText: {
    fontSize: 11,
    color: C.sub,
    textAlign: 'center',
  },
});

