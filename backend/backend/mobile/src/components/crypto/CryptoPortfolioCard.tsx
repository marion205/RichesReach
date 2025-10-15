/**
 * Crypto Portfolio Card — Pro
 * - FlatList holdings (fast, smooth)
 * - Allocation bars with animation
 * - Timeframe P&L chips
 * - Pull-to-refresh
 * - Mask toggle applies everywhere
 * - A11y labels, safe number handling
 */

import React, { useMemo, useRef, useEffect, useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Animated,
  Easing,
  FlatList,
  RefreshControl,
  Platform,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import CryptoIcon from './CryptoIcon';
import Svg, { Path, Circle } from 'react-native-svg';
import { SkeletonPortfolioCard } from '../common/Skeleton';

type Holding = {
  cryptocurrency?: { symbol?: string };
  quantity?: number | string;
  current_value?: number;
  unrealized_pnl_percentage?: number;
};

type Analytics = {
  portfolio_volatility?: number; // 0..1
  sharpe_ratio?: number;
  max_drawdown?: number; // %
  diversification_score?: number; // %
  sector_allocation?: Record<string, number>; // { LOW: 25, MEDIUM: 40 ... }
  best_performer?: { symbol: string; pnl_percentage: number };
  worst_performer?: { symbol: string; pnl_percentage: number };
};

interface CryptoPortfolioCardProps {
  portfolio: {
    total_value_usd?: number;
    total_pnl?: number;
    total_pnl_percentage?: number;
    // Optional timeframe fields:
    total_pnl_1d?: number;
    total_pnl_pct_1d?: number;
    total_pnl_1w?: number;
    total_pnl_pct_1w?: number;
    total_pnl_1m?: number;
    total_pnl_pct_1m?: number;
    holdings?: Holding[];
  } | null;
  analytics?: Analytics | null;
  loading: boolean;
  onRefresh: () => void;
  onPressHolding?: (symbol: string) => void;
  onStartTrading?: () => void;
  hideBalances?: boolean;
  onToggleHideBalances?: (next: boolean) => void;
  ltvState?: 'SAFE'|'CAUTION'|'AT_RISK'|'DANGER';
  initialHideBalances?: boolean;
  // Asset icons - can be local assets or URLs from GET_SUPPORTED_CURRENCIES
  assetIcons?: Record<string, any>; // local assets: { BTC: require('...'), ETH: require('...') }
  supportedCurrencies?: Array<{ symbol: string; iconUrl?: string; name?: string }>; // from GraphQL
}

const UI = {
  bg: '#F2F2F7',
  card: '#FFFFFF',
  text: '#111827',
  sub: '#8E8E93',
  primary: '#007AFF',
  success: '#34C759',
  danger: '#FF3B30',
  violet: '#8B5CF6',
  border: '#E5E5EA',
  wash: '#F3F4F6',
};

const tierColor = (tier: string) => {
  switch (tier) {
    case 'LOW': return UI.success;
    case 'MEDIUM': return '#FF9500';
    case 'HIGH': return UI.danger;
    case 'EXTREME': return UI.violet;
    default: return UI.sub;
  }
};

const numberOr = (v: unknown, d = 0) => (typeof v === 'number' && isFinite(v) ? v : d);

const formatCurrency = (v: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(numberOr(v));

const formatPctSigned = (v: number) => `${v >= 0 ? '+' : ''}${numberOr(v).toFixed(2)}%`;

// Simple sparkline component using react-native-svg
const Sparkline: React.FC<{ 
  data: number[]; 
  width?: number; 
  height?: number; 
  color?: string;
  positive?: boolean;
}> = ({ data, width = 40, height = 20, color, positive }) => {
  if (!data || data.length < 2) {
    return <View style={{ width, height, backgroundColor: UI.wash, borderRadius: 4 }} />;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  const lineColor = color || (positive ? UI.success : UI.danger);
  
  return (
    <Svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <Path
        d={`M ${points}`}
        stroke={lineColor}
        strokeWidth="1.5"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
};

// LTV ratio display component
const LTVDisplay: React.FC<{ ltvState: string; ltvRatio?: number }> = ({ ltvState, ltvRatio }) => {
  if (ltvState === 'SAFE' || !ltvRatio) return null;
  
  const getLTVColor = (state: string) => {
    switch (state) {
      case 'CAUTION': return '#F59E0B';
      case 'AT_RISK': return '#EF4444';
      case 'DANGER': return '#7C3AED';
      default: return UI.sub;
    }
  };

  const getLTVLabel = (state: string) => {
    switch (state) {
      case 'CAUTION': return 'Caution';
      case 'AT_RISK': return 'At Risk';
      case 'DANGER': return 'Danger';
      default: return 'Unknown';
    }
  };

  return (
    <View style={styles.ltvDisplay}>
      <View style={[styles.ltvChip, { backgroundColor: getLTVColor(ltvState) + '15', borderColor: getLTVColor(ltvState) + '40' }]}>
        <Icon name="alert-triangle" size={12} color={getLTVColor(ltvState)} />
        <Text style={[styles.ltvText, { color: getLTVColor(ltvState) }]}>
          LTV: {(ltvRatio * 100).toFixed(1)}% • {getLTVLabel(ltvState)}
        </Text>
      </View>
    </View>
  );
};

const CryptoPortfolioCard: React.FC<CryptoPortfolioCardProps> = ({
  portfolio,
  analytics,
  loading,
  onRefresh,
  onPressHolding,
  onStartTrading,
  hideBalances,
  initialHideBalances,
  onToggleHideBalances,
  ltvState,
  assetIcons = {},
  supportedCurrencies = [],
}) => {
  /* -------------------------- state -------------------------- */
  const [timeframe, setTimeframe] = useState<'1D'|'1W'|'1M'|'ALL'>('ALL');
  const [mask, setMask] = useState<boolean>(!!initialHideBalances || !!hideBalances);

  useEffect(() => {
    if (typeof hideBalances === 'boolean') setMask(hideBalances);
  }, [hideBalances]);

  /* ---------------------- refresh animation --------------------- */
  const spin = useRef(new Animated.Value(0)).current;
  const spinAnim = useCallback(() => {
    spin.setValue(0);
    Animated.timing(spin, {
      toValue: 1,
      duration: 700,
      easing: Easing.inOut(Easing.linear),
      useNativeDriver: true,
    }).start();
  }, [spin]);

  const spinStyle = {
    transform: [
      {
        rotate: spin.interpolate({
          inputRange: [0, 1],
          outputRange: ['0deg', '360deg'],
        }),
      },
    ],
  };

  const onPressRefresh = () => {
    spinAnim();
    onRefresh();
  };

  /* -------------------------- helpers -------------------------- */
  const masked = useCallback((text: string) => (mask ? '•••••' : text), [mask]);

  const totalValue = numberOr(portfolio?.total_value_usd);

  const pickPnl = useCallback(() => {
    if (!portfolio) return { abs: 0, pct: 0 };
    const map = {
      '1D': { abs: portfolio.total_pnl_1d, pct: portfolio.total_pnl_pct_1d },
      '1W': { abs: portfolio.total_pnl_1w, pct: portfolio.total_pnl_pct_1w },
      '1M': { abs: portfolio.total_pnl_1m, pct: portfolio.total_pnl_pct_1m },
      'ALL':{ abs: portfolio.total_pnl, pct: portfolio.total_pnl_percentage },
    } as const;
    const sel = map[timeframe] ?? map.ALL;
    const abs = numberOr(sel.abs, numberOr(portfolio.total_pnl));
    const pct = numberOr(sel.pct, numberOr(portfolio.total_pnl_percentage));
    return { abs, pct };
  }, [portfolio, timeframe]);

  const { abs: totalPnlAbs, pct: totalPnlPct } = pickPnl();

  const colorPnL = (v: number) => (v >= 0 ? UI.success : UI.danger);

  const holdings = useMemo(() => portfolio?.holdings ?? [], [portfolio]);

  const toggleMask = () => {
    const next = !mask;
    setMask(next);
    onToggleHideBalances?.(next);
  };

  // Asset icon helper
  const getAssetIcon = useCallback((symbol: string) => {
    const upperSymbol = symbol.toUpperCase();
    
    // First try local asset icons
    if (assetIcons[upperSymbol]) {
      return { type: 'local', source: assetIcons[upperSymbol] };
    }
    
    // Then try supported currencies from GraphQL
    const currency = supportedCurrencies.find(c => c.symbol?.toUpperCase() === upperSymbol);
    if (currency?.iconUrl) {
      return { type: 'url', source: { uri: currency.iconUrl } };
    }
    
    return null;
  }, [assetIcons, supportedCurrencies]);

  // Generate mock sparkline data (in real app, this would come from price history)
  const generateSparklineData = useCallback((symbol: string, pnlPct: number) => {
    // Generate 7 data points representing 7-day price movement
    const basePrice = 100;
    const volatility = Math.abs(pnlPct) / 100 || 0.1;
    const trend = pnlPct > 0 ? 1 : -1;
    
    return Array.from({ length: 7 }, (_, i) => {
      const randomFactor = (Math.random() - 0.5) * volatility * 2;
      const trendFactor = (i / 6) * trend * volatility * 0.5;
      return basePrice + randomFactor + trendFactor;
    });
  }, []);

  /* ----------------------- renderers ----------------------- */
  const renderHolding = useCallback(
    ({ item }: { item: Holding }) => {
      const symbol = (item?.cryptocurrency?.symbol || 'UNK').toUpperCase();
      const qty = numberOr(Number(item?.quantity), 0);
      const value = numberOr(item?.current_value, 0);
      const pnlPct = numberOr(item?.unrealized_pnl_percentage, 0);
      
      const iconInfo = getAssetIcon(symbol);
      const sparklineData = generateSparklineData(symbol, pnlPct);

      return (
        <TouchableOpacity
          style={styles.holdingRow}
          activeOpacity={0.85}
          onPress={() => onPressHolding?.(symbol)}
          accessibilityRole="button"
          accessibilityLabel={`Open ${symbol} details`}
        >
          <View style={styles.holdingLeft}>
            <View style={styles.holdingIcon}>
              <CryptoIcon 
                symbol={symbol} 
                size={32}
                style={styles.assetIcon}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.holdingName}>{symbol}</Text>
              <Text style={styles.holdingSub}>{qty.toFixed(6)} coins</Text>
            </View>
          </View>

          <View style={styles.holdingRight}>
            <View style={styles.holdingValueRow}>
              <Text style={styles.holdingValue}>{masked(formatCurrency(value))}</Text>
              <Sparkline 
                data={sparklineData} 
                positive={pnlPct >= 0}
                color={colorPnL(pnlPct)}
              />
            </View>
            <Text style={[styles.holdingPct, { color: colorPnL(pnlPct) }]}>
              {formatPctSigned(pnlPct)}
            </Text>
          </View>
        </TouchableOpacity>
      );
    },
    [onPressHolding, masked, getAssetIcon, generateSparklineData]
  );

  const keyExtractor = useCallback((item: Holding, idx: number) => {
    const sym = (item?.cryptocurrency?.symbol || 'UNK').toUpperCase();
    const q = String(item?.quantity ?? 0);
    return `${sym}-${q}-${idx}`;
  }, []);

  const ItemSeparator = useCallback(() => <View style={styles.sep} />, []);
  const ListEmpty = useCallback(() => (
    <View style={styles.emptyInline}>
      <Icon name="inbox" size={28} color={UI.sub} />
      <Text style={styles.sub}>No holdings yet</Text>
    </View>
  ), []);

  /* ----------------------- allocation bars ----------------------- */
  const AllocBar: React.FC<{ color: string; pct: number }> = ({ color, pct }) => {
    const widthAnim = useRef(new Animated.Value(0)).current;

    useEffect(() => {
      Animated.timing(widthAnim, {
        toValue: Math.max(0, Math.min(100, pct)),
        duration: 600,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: false, // width animation needs layout
      }).start();
    }, [pct, widthAnim]);

    const style = {
      width: widthAnim.interpolate({
        inputRange: [0, 100],
        outputRange: ['0%', '100%'],
      }),
      backgroundColor: color,
    } as const;

    return (
      <View style={styles.barTrack}>
        <Animated.View style={[styles.barFill, style]} />
      </View>
    );
  };

  /* ----------------------- conditional UI ----------------------- */
  if (loading) return <SkeletonPortfolioCard />;

  if (!portfolio) {
    return (
      <View style={styles.emptyCard}>
        <Icon name="pie-chart" size={44} color={UI.sub} />
        <Text style={styles.emptyTitle}>No Crypto Holdings</Text>
        <Text style={styles.emptySub}>Start trading crypto to build your portfolio.</Text>
        <TouchableOpacity
          style={styles.ctaButton}
          onPress={onStartTrading}
          accessibilityRole="button"
          accessibilityLabel="Start Trading"
        >
          <Text style={styles.ctaText}>Start Trading</Text>
        </TouchableOpacity>
      </View>
    );
  }

  /* =============================== UI =============================== */
  return (
    <View style={styles.container}>
      {/* Summary */}
      <View style={styles.card}>
        <View style={styles.cardAccent} />
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Portfolio Value</Text>

          <View style={styles.summaryHeaderRight}>
            {/* Refresh */}
            <TouchableOpacity
              onPress={onPressRefresh}
              accessibilityRole="button"
              accessibilityLabel="Refresh portfolio"
            >
              <Animated.View style={spinStyle}>
                <Icon name="refresh-cw" size={18} color={UI.primary} />
              </Animated.View>
            </TouchableOpacity>

            {/* LTV State Chip */}
            {ltvState && (
              <View style={[
                styles.stateChip,
                ltvState === 'SAFE' && { backgroundColor:'#ECFDF5', borderColor:'#A7F3D0' },
                ltvState === 'CAUTION' && { backgroundColor:'#FFFBEB', borderColor:'#FCD34D' },
                ltvState === 'AT_RISK' && { backgroundColor:'#FEF2F2', borderColor:'#FCA5A5' },
                ltvState === 'DANGER' && { backgroundColor:'#F5F3FF', borderColor:'#DDD6FE' },
              ]}>
                <View style={[
                  styles.stateDot,
                  ltvState === 'SAFE' && { backgroundColor:'#10B981' },
                  ltvState === 'CAUTION' && { backgroundColor:'#F59E0B' },
                  ltvState === 'AT_RISK' && { backgroundColor:'#EF4444' },
                  ltvState === 'DANGER' && { backgroundColor:'#7C3AED' },
                ]}/>
                <Text style={[
                  styles.stateText,
                  ltvState === 'SAFE' && { color:'#065F46' },
                  ltvState === 'CAUTION' && { color:'#92400E' },
                  ltvState === 'AT_RISK' && { color:'#991B1B' },
                  ltvState === 'DANGER' && { color:'#4C1D95' },
                ]}>
                  {ltvState.replace('_',' ')}
                </Text>
              </View>
            )}

            {/* Hide/Show balances */}
            <TouchableOpacity
              onPress={toggleMask}
              accessibilityRole="button"
              accessibilityLabel={mask ? 'Show balances' : 'Hide balances'}
            >
              <Icon name={mask ? 'eye-off' : 'eye'} size={18} color={UI.sub} />
            </TouchableOpacity>
          </View>
        </View>

        <Text style={styles.totalValue}>{masked(formatCurrency(totalValue))}</Text>

        {/* LTV Display */}
        {ltvState && ltvState !== 'SAFE' && (
          <LTVDisplay ltvState={ltvState} ltvRatio={0.75} />
        )}

        {/* Timeframe switcher */}
        <View style={styles.tfRow}>
          {(['1D','1W','1M','ALL'] as const).map(tf => {
            const active = timeframe === tf;
            return (
              <TouchableOpacity
                key={tf}
                onPress={() => setTimeframe(tf)}
                style={[styles.tfPill, active && styles.tfPillActive]}
                accessibilityRole="button"
                accessibilityLabel={`Set timeframe ${tf}`}
              >
                <Text style={[styles.tfText, active && styles.tfTextActive]}>{tf}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.chipsRow}>
          <View style={[styles.chip, { backgroundColor: '#F1F8F2', borderColor: '#D7F2DA' }]}>
            <Icon name="plus-circle" size={14} color={UI.success} />
            <Text style={[styles.chipText, { color: UI.success }]}>
              {masked(formatCurrency(totalPnlAbs))}
            </Text>
          </View>
          <View style={[styles.chip, { backgroundColor: '#FFF5F5', borderColor: '#FFE1E1' }]}>
            <Icon
              name={totalPnlPct >= 0 ? 'trending-up' : 'trending-down'}
              size={14}
              color={colorPnL(totalPnlPct)}
            />
            <Text style={[styles.chipText, { color: colorPnL(totalPnlPct) }]}>
              {formatPctSigned(totalPnlPct)}
            </Text>
          </View>
        </View>
      </View>

      {/* Risk Metrics */}
      {analytics && (
        <View style={styles.card}>
          <View style={styles.cardHeaderTight}>
            <Text style={styles.sectionTitle}>Risk & Quality</Text>
          </View>

          <View style={styles.metricsGrid}>
            <Metric label="Volatility" value={`${(numberOr(analytics.portfolio_volatility) * 100).toFixed(1)}%`} />
            <Metric label="Sharpe" value={numberOr(analytics.sharpe_ratio).toFixed(2)} />
            <Metric label="Max DD" value={`${numberOr(analytics.max_drawdown).toFixed(1)}%`} danger />
            <Metric label="Diversification" value={`${numberOr(analytics.diversification_score).toFixed(0)}%`} />
          </View>
        </View>
      )}

      {/* Holdings */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.sectionTitle}>Holdings</Text>
          <Text style={styles.sub}>{holdings.length} assets</Text>
        </View>

        <FlatList
          data={holdings}
          keyExtractor={keyExtractor}
          renderItem={renderHolding}
          ItemSeparatorComponent={ItemSeparator}
          ListEmptyComponent={ListEmpty}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={false}
              onRefresh={onRefresh}
              tintColor={Platform.OS === 'ios' ? UI.primary : undefined}
              colors={[UI.primary]}
              title="Refreshing…"
            />
          }
          // Make list height adapt to content within card without scrolling the whole screen weirdly
          scrollEnabled={false}
        />
      </View>

      {/* Allocation */}
      {!!analytics?.sector_allocation && (
        <View style={styles.card}>
          <View style={styles.cardHeaderTight}>
            <Text style={styles.sectionTitle}>Allocation by Risk Tier</Text>
          </View>

          {Object.entries(analytics.sector_allocation).map(([tier, pct]) => {
            const pctNum = numberOr(pct);
            const col = tierColor(tier);
            return (
              <View key={tier} style={styles.allocRow}>
                <View style={styles.allocLeft}>
                  <View style={[styles.dot, { backgroundColor: col }]} />
                  <Text style={styles.allocLabel}>{tier}</Text>
                </View>
                <Text style={styles.allocPct}>{pctNum.toFixed(1)}%</Text>
                <AllocBar color={col} pct={pctNum} />
              </View>
            );
          })}
        </View>
      )}

      {/* Performance */}
      {(analytics?.best_performer || analytics?.worst_performer) && (
        <View style={styles.card}>
          <View style={styles.cardHeaderTight}>
            <Text style={styles.sectionTitle}>Performance</Text>
          </View>

          {analytics?.best_performer && (
            <PerfRow
              icon="trending-up"
              color={UI.success}
              label="Best"
              value={`${analytics.best_performer.symbol.toUpperCase()}  ${formatPctSigned(numberOr(analytics.best_performer.pnl_percentage))}`}
            />
          )}
          {analytics?.worst_performer && (
            <PerfRow
              icon="trending-down"
              color={UI.danger}
              label="Worst"
              value={`${analytics.worst_performer.symbol.toUpperCase()}  ${formatPctSigned(numberOr(analytics.worst_performer.pnl_percentage))}`}
            />
          )}
        </View>
      )}
    </View>
  );
};

/* --------------------------- subcomponents --------------------------- */

const Metric = ({ label, value, danger }: { label: string; value: string; danger?: boolean }) => (
  <View style={styles.metric}>
    <Text style={styles.metricLabel}>{label}</Text>
    <Text style={[styles.metricValue, danger && { color: UI.danger }]}>{value}</Text>
  </View>
);

const PerfRow = ({ icon, color, label, value }: { icon: string; color: string; label: string; value: string }) => (
  <View style={styles.perfRow}>
    <View style={styles.perfLeft}>
      <Icon name={icon as any} size={16} color={color} />
      <Text style={styles.perfLabel}>{label}</Text>
    </View>
    <Text style={styles.perfVal}>{value}</Text>
  </View>
);

/* ------------------------------- styles ------------------------------ */

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 16 },

  /* cards */
  card: {
    backgroundColor: UI.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 2,
    elevation: 1,
  },
  cardAccent: {
    position: 'absolute',
    left: 0, top: 0, bottom: 0,
    width: 3,
    borderTopLeftRadius: 12,
    borderBottomLeftRadius: 12,
    backgroundColor: UI.primary,
  },
  cardHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8,
  },
  summaryHeaderRight: { flexDirection:'row', alignItems:'center', gap:12 },
  stateChip: { flexDirection:'row', alignItems:'center', gap:6, paddingHorizontal:10, paddingVertical:4, borderRadius:12, borderWidth:1 },
  stateDot: { width:6, height:6, borderRadius:3 },
  stateText: { fontSize:12, fontWeight:'800' },
  cardHeaderTight: { marginBottom: 8 },
  cardTitle: { fontSize: 14, fontWeight: '600', color: UI.sub },

  sectionTitle: { fontSize: 16, fontWeight: '700', color: UI.text },
  sub: { fontSize: 13, color: UI.sub },

  /* summary */
  totalValue: { fontSize: 30, fontWeight: '800', color: UI.text, marginVertical: 6 },

  /* timeframe switcher */
  tfRow: { flexDirection: 'row', gap: 8, marginTop: 6, marginBottom: 6 },
  tfPill: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 14, backgroundColor: UI.wash },
  tfPillActive: { backgroundColor: UI.primary + '15', borderWidth: 1, borderColor: UI.primary + '55' },
  tfText: { fontSize: 12, color: UI.sub, fontWeight: '600' },
  tfTextActive: { color: UI.primary },

  chipsRow: { flexDirection: 'row', gap: 8, marginTop: 4 },
  chip: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    borderRadius: 16, paddingHorizontal: 10, paddingVertical: 6, borderWidth: 1,
  },
  chipText: { fontSize: 13, fontWeight: '700' },

  /* loading / empty */
  emptyCard: { backgroundColor: UI.card, borderRadius: 12, padding: 24, alignItems: 'center', gap: 10 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: UI.text, marginTop: 4 },
  emptySub: { fontSize: 14, color: UI.sub, textAlign: 'center' },
  ctaButton: { marginTop: 10, backgroundColor: UI.primary, paddingHorizontal: 18, paddingVertical: 10, borderRadius: 10 },
  ctaText: { color: '#fff', fontWeight: '700' },

  /* metrics */
  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginTop: 4 },
  metric: { width: '48%', marginTop: 10 },
  metricLabel: { fontSize: 12, color: UI.sub, marginBottom: 2 },
  metricValue: { fontSize: 18, fontWeight: '700', color: UI.text },

  /* holdings */
  sep: { height: 1, backgroundColor: UI.wash },
  emptyInline: { alignItems: 'center', paddingVertical: 20, gap: 8 },

  holdingRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12 },
  holdingLeft: { flexDirection: 'row', alignItems: 'center', flex: 1, gap: 10 },
  holdingIcon: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center' },
  holdingIconText: { fontSize: 13, fontWeight: '800', color: UI.primary },
  holdingName: { fontSize: 15, fontWeight: '700', color: UI.text },
  holdingSub: { fontSize: 12, color: UI.sub, marginTop: 2 },
  holdingRight: { alignItems: 'flex-end' },
  holdingValueRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  holdingValue: { fontSize: 15, fontWeight: '700', color: UI.text },
  holdingPct: { fontSize: 12, fontWeight: '700', marginTop: 2 },
  assetIcon: { width: 32, height: 32, borderRadius: 16 },

  /* allocation */
  allocRow: { marginTop: 10 },
  allocLeft: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  dot: { width: 10, height: 10, borderRadius: 5, backgroundColor: UI.sub },
  allocLabel: { fontSize: 14, color: UI.text },
  allocPct: { position: 'absolute', right: 0, top: 0, fontSize: 13, color: UI.sub },
  barTrack: { height: 8, backgroundColor: UI.wash, borderRadius: 6, overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: 6 },

  /* performance */
  perfRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8 },
  perfLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  perfLabel: { fontSize: 14, color: UI.text, fontWeight: '600' },
  perfVal: { fontSize: 14, fontWeight: '700', color: UI.text },

  /* LTV display */
  ltvDisplay: { marginTop: 8, marginBottom: 4 },
  ltvChip: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    gap: 6, 
    paddingHorizontal: 10, 
    paddingVertical: 6, 
    borderRadius: 12, 
    borderWidth: 1,
    alignSelf: 'flex-start'
  },
  ltvText: { fontSize: 12, fontWeight: '700' },
});

export default CryptoPortfolioCard;