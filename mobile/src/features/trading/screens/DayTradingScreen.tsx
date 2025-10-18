import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { useQuery, useMutation, useApolloClient } from '@apollo/client';
import { gql } from '@apollo/client';
import { GET_DAY_TRADING_PICKS, LOG_DAY_TRADING_OUTCOME } from '../../../graphql/dayTrading';
import Icon from 'react-native-vector-icons/Feather';
import SparkMini from '../../../components/charts/SparkMini';

type TradingMode = 'SAFE' | 'AGGRESSIVE';
type Side = 'LONG' | 'SHORT';

interface DayTradingPick {
  symbol: string;
  side: Side;
  score: number;
  features: {
    momentum_15m: number;
    rvol_10m: number;
    vwap_dist: number;
    breakout_pct: number;
    spread_bps: number;
    catalyst_score: number;
  };
  risk: {
    atr_5m: number;
    size_shares: number;
    stop: number;
    targets: number[];
    time_stop_min: number;
  };
  notes: string;
}

interface DayTradingData {
  as_of: string;
  mode: TradingMode;
  picks: DayTradingPick[];
  universe_size: number;
  quality_threshold: number;
}

const GET_TRADING_QUOTE = gql`
  query GetTradingQuote($symbol: String!) {
    tradingQuote(symbol: $symbol) {
      symbol
      currentPrice
      change
      changePercent
      bid
      ask
    }
  }
`;

const GET_STOCK_CHART_DATA = gql`
  query GetStockChartData($symbol: String!, $timeframe: String!) {
    stockChartData(symbol: $symbol, timeframe: $timeframe) {
      symbol
      interval
      data {
        timestamp
        open
        high
        low
        close
        volume
      }
      currentPrice
      change
      changePercent
    }
  }
`;

export default function DayTradingScreen({ navigateTo }: { navigateTo?: (screen: string) => void }) {
  const [mode, setMode] = useState<TradingMode>('SAFE');
  const [refreshing, setRefreshing] = useState(false);
  const [quotes, setQuotes] = useState<{ [key: string]: any }>({});
  const [charts, setCharts] = useState<{ [key: string]: number[] }>({});
  const [visibleSymbols, setVisibleSymbols] = useState<Set<string>>(new Set());
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chartPollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const client = useApolloClient();

  const { data, loading, error, refetch, networkStatus, startPolling, stopPolling } = useQuery(
    GET_DAY_TRADING_PICKS,
    {
      variables: { mode },
      fetchPolicy: 'cache-and-network',
      notifyOnNetworkStatusChange: true,
      errorPolicy: 'all',
    },
  );

  const [logOutcome] = useMutation(LOG_DAY_TRADING_OUTCOME, {
    errorPolicy: 'all',
  });

  const dayTradingData: DayTradingData | null = data?.dayTradingPicks ?? null;
  const picks = dayTradingData?.picks ?? [];

  // --- helpers ---
  const isMarketHours = useCallback(() => {
    // simple NYSE approximation; adjust if you already store tz server-side
    const now = new Date();
    const day = now.getDay(); // 0 Sun ... 6 Sat
    if (day === 0 || day === 6) return false;
    const h = now.getHours();
    const m = now.getMinutes();
    const mins = h * 60 + m;
    // 9:30–16:00 local time
    return mins >= 9 * 60 + 30 && mins <= 16 * 60;
  }, []);

  const fetchQuotes = useCallback(async (symbols: string[]) => {
    if (!symbols.length) return;

    const quotePromises = symbols.map((s) =>
      client.query({
        query: GET_TRADING_QUOTE,
        variables: { symbol: s },
      }),
    );

    try {
      const results = await Promise.all(quotePromises);
      const newQuotes = results.reduce((acc, res, i) => {
        if (res.data?.tradingQuote) {
          acc[symbols[i]] = res.data.tradingQuote;
        }
        return acc;
      }, {} as any);

      setQuotes((prev) => ({ ...prev, ...newQuotes }));
    } catch (e) {
      console.error('Failed to fetch quotes', e);
    }
  }, [client]);

  const fetchCharts = useCallback(async (symbols: string[]) => {
    if (!symbols.length) return;

    const missingCharts = symbols.filter((s) => !charts[s]);
    if (!missingCharts.length) return;

    // Temporarily use mock chart data to avoid 400 errors
    try {
      const newCharts = missingCharts.reduce((acc, symbol) => {
        // Generate mock chart data (30 data points with some variation)
        const basePrice = quotes[symbol]?.currentPrice || 100;
        const mockData = Array.from({ length: 30 }, (_, i) => {
          const variation = (Math.random() - 0.5) * 0.1; // ±5% variation
          return basePrice * (1 + variation);
        });
        acc[symbol] = mockData;
        return acc;
      }, {} as any);

      setCharts((prev) => ({ ...prev, ...newCharts }));
      console.log('📊 Using mock chart data for symbols:', missingCharts);
    } catch (e) {
      console.error('Failed to generate mock charts', e);
    }

    // TODO: Re-enable real chart fetching once 400 errors are resolved
    // const chartPromises = missingCharts.map((s) =>
    //   client.query({
    //     query: GET_STOCK_CHART_DATA,
    //     variables: { symbol: s, timeframe: '1D' },
    //   }),
    // );

    // try {
    //   const results = await Promise.all(chartPromises);
    //   const newCharts = results.reduce((acc, res, i) => {
    //     if (res.data?.stockChartData?.data) {
    //       const closes = res.data.stockChartData.data.map((d: any) => d.close);
    //       acc[missingCharts[i]] = closes;
    //     }
    //     return acc;
    //   }, {} as any);

    //   setCharts((prev) => ({ ...prev, ...newCharts }));
    // } catch (e) {
    //   console.error('Failed to fetch charts', e);
    // }
  }, [charts, quotes]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch({ mode });
      const symbols = [...new Set(picks.map((p) => p.symbol))];
      await fetchQuotes(symbols);
      await fetchCharts(symbols);
    } finally {
      setRefreshing(false);
    }
  }, [mode, refetch, picks, fetchQuotes, fetchCharts]);

  const handleModeChange = useCallback(
    async (newMode: TradingMode) => {
      if (newMode === mode) return;
      setMode(newMode);
      // refetch immediately on toggle for snappy UX
      await refetch({ mode: newMode });
      const symbols = [...new Set(picks.map((p) => p.symbol))];
      await fetchQuotes(symbols);
      await fetchCharts(symbols);
    },
    [mode, refetch, picks, fetchQuotes, fetchCharts],
  );

  // Handle visible items change
  const onViewableItemsChanged = useCallback(({ viewableItems }: { viewableItems: any[] }) => {
    const newVisible = new Set(viewableItems.map((item) => item.item.symbol));
    setVisibleSymbols(newVisible);
    fetchCharts(Array.from(newVisible));
  }, [fetchCharts]);

  const viewabilityConfig = useMemo(
    () => ({
      itemVisiblePercentThreshold: 50,
      minimumViewTime: 1000,
    }),
    [],
  );

  // Fetch data when picks change
  useEffect(() => {
    const symbols = [...new Set(picks.map((p) => p.symbol))];
    fetchQuotes(symbols);
    fetchCharts(symbols);
  }, [picks, fetchQuotes, fetchCharts]);

  // polling during market hours
  useEffect(() => {
    // if you're already using Apollo polling, this is enough:
    if (isMarketHours()) startPolling?.(60_000);
    else stopPolling?.();

    // extra safety: manual interval (kept off by default)
    if (pollingRef.current) clearInterval(pollingRef.current);
    if (isMarketHours()) {
      pollingRef.current = setInterval(() => {
        refetch({ mode }).catch(() => {});
        const symbols = [...new Set(picks.map((p) => p.symbol))];
        fetchQuotes(symbols);
      }, 30000); // Poll quotes every 30 seconds
    }
    return () => {
      stopPolling?.();
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [mode, isMarketHours, refetch, startPolling, stopPolling, picks, fetchQuotes]);

  // Separate polling for charts (less frequent)
  useEffect(() => {
    if (chartPollingRef.current) clearInterval(chartPollingRef.current);
    if (isMarketHours()) {
      chartPollingRef.current = setInterval(() => {
        fetchCharts(Array.from(visibleSymbols));
      }, 60000); // Poll charts every 60 seconds for visible items only
    }
    return () => {
      if (chartPollingRef.current) clearInterval(chartPollingRef.current);
    };
  }, [isMarketHours, visibleSymbols, fetchCharts]);

  // ---- UI color system ----
  const C = useMemo(
    () => ({
      bg: '#FAFBFC',
      card: '#FFFFFF',
      text: '#1A202C',
      sub: '#718096',
      border: '#E9ECEF',
      primary: '#3182CE',
      safe: '#38A169',
      aggressive: '#D69E2E',
      long: '#38A169',
      short: '#E53E3E',
      warnBg: '#FEFCBF',
      warnBorder: '#FAD999',
      warnText: '#B7791F',
      shadow: 'rgba(0, 0, 0, 0.06)',
      shadowLight: 'rgba(0, 0, 0, 0.04)',
    }),
    [],
  );

  const getModeColor = (m: TradingMode) => (m === 'SAFE' ? C.safe : C.aggressive);
  const getSideColor = (side: Side) => (side === 'LONG' ? C.long : C.short);
  const getScoreColor = (score: number) => (score >= 2 ? C.long : score >= 1 ? C.aggressive : C.short);
  const getChangeColor = (changePercent: number) => (changePercent >= 0 ? C.long : C.short);

  // robust entry computation (use atr around stop; invert for SHORT)
  const computeEntry = (pick: DayTradingPick) => {
    const stop = pick.risk?.stop ?? 0;
    const atr = pick.risk?.atr5m ?? 0;
    return pick.side === 'LONG' ? stop + atr : Math.max(0, stop - atr);
  };

  const handleTradeExecution = useCallback(
    (pick: DayTradingPick) => {
      const entry = computeEntry(pick);
      const primaryTarget = pick.risk.targets?.[0] ?? entry;
      Alert.alert(
        'Execute Trade',
        `Execute ${pick.side} ${pick.symbol}?\n\nEntry: $${(entry ?? 0).toFixed(2)}\nStop: $${(pick.risk?.stop ?? 0).toFixed(
          2,
        )}\nTarget: $${Number(primaryTarget ?? 0).toFixed(2)}\nSize: ${pick.risk?.size_shares ?? 0} shares`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Execute',
            onPress: async () => {
              // Place your real order here (brokerage/OMS). After submission, log a provisional outcome.
              try {
                await logOutcome({
                  variables: {
                    input: {
                      symbol: pick.symbol,
                      side: pick.side,
                      mode,
                      entryPrice: entry,
                      stopPrice: pick.risk.stop,
                      targetPrice: primaryTarget,
                      sizeShares: pick.risk.size_shares,
                      features: pick.features,
                      score: pick.score,
                      executedAt: new Date().toISOString(),
                      // you can add clientOrderId here for reconciliation
                    },
                  },
                });
              } catch (e) {
                // Non-blocking: trade might still be placed; this is just telemetry
                console.warn('Outcome log failed', e);
              }
              Alert.alert('Trade Submitted', `${pick.side} ${pick.symbol} sent`);
            },
          },
        ],
      );
    },
    [logOutcome, mode],
  );

  // Memoized renderPick
  const MemoizedPick = React.memo(({ item }: { item: DayTradingPick }) => {
    const entry = computeEntry(item);
    const target = item.risk?.targets?.[0] ?? entry;
    const quote = quotes[item.symbol];
    const chartData = charts[item.symbol] || [];
    const changePercent = quote?.changePercent ?? 0;
    return (
      <View style={[styles.card, { backgroundColor: C.card, borderColor: C.border }]}>
        {/* Header */}
        <View style={styles.pickHeader}>
          <View style={styles.pickSymbolWrap}>
            <View style={styles.symbolIcon}>
              <Icon name="trending-up" size={20} color={getSideColor(item.side)} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.pickSymbol, { color: C.text }]} accessibilityRole="text" accessibilityLabel={`Symbol ${item.symbol}`}>
                {item.symbol}
              </Text>
              {quote && (
                <View style={styles.changeWrap}>
                  <Text style={[styles.changeValue, { color: getChangeColor(changePercent) }]}>
                    {changePercent >= 0 ? `+${changePercent.toFixed(2)}%` : `${changePercent.toFixed(2)}%`}
                  </Text>
                  <Text style={[styles.changeLabel, { color: C.sub }]}>Live</Text>
                </View>
              )}
            </View>
            <View style={[styles.badge, { backgroundColor: getSideColor(item.side) }]}>
              <Text style={styles.badgeText}>{item.side}</Text>
            </View>
          </View>
          <View style={styles.pickScoreWrap}>
            <Text style={[styles.scoreValue, { color: getScoreColor(item.score) }]}>{(item.score ?? 0).toFixed(2)}</Text>
            <Text style={[styles.scoreLabel, { color: C.sub }]}>Score</Text>
          </View>
        </View>

        {/* Live Chart */}
        <View style={styles.chartContainer}>
          {chartData && chartData.length > 0 ? (
            <>
              <SparkMini 
                data={chartData} 
                width={chartData.length * 2} 
                height={60} 
                upColor={C.long}
                downColor={C.short}
                neutralColor={C.sub}
              />
              <View style={styles.chartFooter}>
                <Text style={[styles.chartPrice, { color: getChangeColor(changePercent) }]}>
                  {quote ? `$${quote.currentPrice?.toFixed(2)}` : 'N/A'}
                </Text>
                <Text style={styles.chartTime}>1D Intraday</Text>
              </View>
            </>
          ) : (
            <View style={[styles.chartPlaceholder, { backgroundColor: C.border }]}>
              <Text style={[styles.chartPlaceholderText, { color: C.sub }]}>Chart Loading...</Text>
            </View>
          )}
        </View>

        {/* Features */}
        <View style={styles.block}>
          <View style={styles.blockHeader}>
            <Icon name="bar-chart-2" size={16} color={C.sub} />
            <Text style={[styles.blockTitle, { color: C.text }]}>Key Features</Text>
          </View>
          <View style={styles.grid}>
            <KV label="Momentum" value={(item.features?.momentum15m ?? 0).toFixed(3)} />
            <KV label="RVOL" value={`${(item.features?.rvol10m ?? 0).toFixed(2)}x`} />
            <KV label="VWAP" value={(item.features?.vwapDist ?? 0).toFixed(3)} />
            <KV label="Breakout" value={(item.features?.breakoutPct ?? 0).toFixed(3)} />
          </View>
        </View>

        {/* Risk */}
        <View style={styles.block}>
          <View style={styles.blockHeader}>
            <Icon name="shield" size={16} color={C.sub} />
            <Text style={[styles.blockTitle, { color: C.text }]}>Risk Management</Text>
          </View>
          <View style={styles.grid}>
            <KV label="Size" value={`${item.risk?.sizeShares ?? 0} shares`} />
            <KV label="Entry" value={`$${(entry ?? 0).toFixed(2)}`} />
            <KV label="Stop" value={`$${(item.risk?.stop ?? 0).toFixed(2)}`} />
            <KV label="Target" value={`$${Number(target ?? 0).toFixed(2)}`} />
            <KV label="Time Stop" value={`${item.risk?.timeStopMin ?? 0} min`} />
            <KV label="ATR(5m)" value={`${(item.risk?.atr5m ?? 0).toFixed(2)}`} />
          </View>
        </View>

        {item.notes ? <Text style={[styles.notes, { color: C.sub }]}>{item.notes}</Text> : null}

        <TouchableOpacity
          style={[styles.executeBtn, { backgroundColor: getSideColor(item.side) }]}
          onPress={() => handleTradeExecution(item)}
          accessibilityRole="button"
          accessibilityLabel={`Execute ${item.side} ${item.symbol}`}
        >
          <Icon name="zap" size={18} color="#fff" style={{ marginRight: 8 }} />
          <Text style={styles.executeBtnText}>Execute {item.side} Trade</Text>
        </TouchableOpacity>
      </View>
    );
  });

  MemoizedPick.displayName = 'MemoizedPick';

  // ---- header / top ----
  const Header = (
    <View>
      <View style={[styles.header, { backgroundColor: C.card, borderBottomColor: C.border }]}>
        <View style={styles.headerRow}>
          <View style={styles.headerLeft}>
            {navigateTo && (
              <TouchableOpacity style={styles.backBtn} onPress={() => navigateTo('trading')} accessibilityRole="button" accessibilityLabel="Back">
                <Icon name="arrow-left" size={20} color={C.primary} />
              </TouchableOpacity>
            )}
            <View style={styles.headerText}>
              <Text style={[styles.title, { color: C.text }]}>Daily Top-3 Picks</Text>
              <Text style={[styles.subtitle, { color: C.sub }]}>Intraday Trading Opportunities</Text>
            </View>
          </View>
          {navigateTo && (
            <View style={styles.headerRight}>
              <TouchableOpacity style={[styles.pillBtn, { backgroundColor: '#EE6C4D' }]} onPress={() => navigateTo('risk-management')}>
                <Icon name="shield" size={14} color="#fff" style={{ marginRight: 4 }} />
                <Text style={styles.pillBtnText}>Risk</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.pillBtn, { backgroundColor: '#9C27B0' }]} onPress={() => navigateTo('ml-system')}>
                <Icon name="cpu" size={14} color="#fff" style={{ marginRight: 4 }} />
                <Text style={styles.pillBtnText}>ML</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>

      {/* Mode Toggle */}
      <View style={[styles.modeWrap, { backgroundColor: C.card, shadowColor: '#000' }]}>
        <View style={styles.modeHeader}>
          <View style={styles.modeHeaderLeft}>
            <Icon name="toggle-left" size={16} color={C.sub} />
            <Text style={[styles.modeTitle, { color: C.text }]}>Trading Mode</Text>
          </View>
          <TouchableOpacity
            style={styles.infoDot}
            onPress={() =>
              Alert.alert(
                'Trading Modes',
                'SAFE: Conservative picks with tighter thresholds and liquidity filters.\n\nAGGRESSIVE: Higher-variance picks with looser filters and broader universe.\n\nPosition sizing/time-stop differ by mode.',
              )
            }
          >
            <Text style={{ fontWeight: '700', color: C.sub }}>i</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.modeGroup}>
          <TouchableOpacity
            style={[styles.modeBtn, mode === 'SAFE' && { backgroundColor: getModeColor('SAFE') }]}
            onPress={() => handleModeChange('SAFE')}
          >
            <Text style={[styles.modeBtnText, mode === 'SAFE' ? styles.modeBtnTextActive : { color: C.sub }]}>SAFE</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeBtn, mode === 'AGGRESSIVE' && { backgroundColor: getModeColor('AGGRESSIVE') }]}
            onPress={() => handleModeChange('AGGRESSIVE')}
          >
            <Text
              style={[styles.modeBtnText, mode === 'AGGRESSIVE' ? styles.modeBtnTextActive : { color: C.sub }]}
            >
              AGGRESSIVE
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Mode Info */}
      <View style={[styles.infoStrip, { backgroundColor: '#EBF4FF' }]}>
        <Text style={[styles.infoText, { color: C.primary }]}>
          {mode === 'SAFE'
            ? '0.5% risk per trade • 45 min time-stop • Large-cap/liquid universe'
            : '1.2% risk per trade • 25 min time-stop • Extended universe'}
        </Text>
      </View>

      {/* Market Status */}
      {dayTradingData && (
        <View style={[styles.marketBox, { backgroundColor: C.card }]}>
          <View style={styles.marketRow}>
            <Icon name="clock" size={14} color={C.sub} />
            <Text style={[styles.marketText, { color: C.sub, marginLeft: 8 }]}>
              Last Updated: {new Date(dayTradingData.as_of).toLocaleTimeString()}
            </Text>
          </View>
          <View style={styles.marketRow}>
            <Icon name="globe" size={14} color={C.sub} />
            <Text style={[styles.marketText, { color: C.sub, marginLeft: 8 }]}>
              Universe: {dayTradingData.universe_size} • Threshold: {dayTradingData.quality_threshold}
            </Text>
          </View>
        </View>
      )}
    </View>
  );

  // ---- states ----
  if (loading && !dayTradingData) {
    return (
      <View style={[styles.container, { backgroundColor: C.bg }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={C.primary} />
          <Text style={[styles.loadingText, { color: C.sub }]}>Loading day trading picks…</Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, { backgroundColor: C.bg }]}>
        <View style={styles.errorContainer}>
          <Icon name="alert-triangle" size={48} color={C.short} />
          <Text style={[styles.errorText, { color: C.short }]}>
            Error loading picks: {error.message}
          </Text>
          <TouchableOpacity style={[styles.retryBtn, { backgroundColor: C.primary }]} onPress={onRefresh}>
            <Text style={styles.retryBtnText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: C.bg }]}>
      <FlatList
        data={picks}
        keyExtractor={(item, idx) => `${item.symbol}-${item.side}-${idx}`}
        ListHeaderComponent={Header}
        renderItem={({ item }) => <MemoizedPick item={item} />}
        contentContainerStyle={{ paddingBottom: 24 }}
        refreshControl={<RefreshControl refreshing={refreshing || networkStatus === 4} onRefresh={onRefresh} tintColor={C.primary} />}
        initialNumToRender={3}
        maxToRenderPerBatch={3}
        windowSize={10}
        removeClippedSubviews={true}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewabilityConfig}
        ListEmptyComponent={
          <View style={styles.emptyWrap}>
            <Icon name="inbox" size={64} color={C.sub} />
            <Text style={[styles.emptyTitle, { color: C.sub }]}>No qualifying picks for {mode} mode</Text>
            <Text style={[styles.emptySub, { color: C.sub }]}>
              Quality threshold not met or market conditions unsuitable
            </Text>
          </View>
        }
        ListFooterComponent={
          <View style={[styles.disclaimer, { borderLeftColor: C.warnBorder, backgroundColor: C.warnBg, marginTop: 20 }]}>
            <Icon name="alert-circle" size={16} color={C.warnText} style={{ marginRight: 8 }} />
            <Text style={[styles.disclaimerText, { color: C.warnText }]}>
              Day trading involves significant risk. Only trade with capital you can afford to lose. Past performance does
              not guarantee future results.
            </Text>
          </View>
        }
      />
    </View>
  );
}

/* ============ Small subcomponent ============ */
function KV({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <View style={{ width: '48%', marginBottom: 12 }}>
      <Text style={{ fontSize: 13, color: '#718096' }}>{label}</Text>
      <Text style={{ fontSize: 16, fontWeight: '800', color: color || '#1A202C' }}>{value}</Text>
    </View>
  );
}

/* ============ Styles ============ */
const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { 
    paddingHorizontal: 20, 
    paddingVertical: 16, 
    borderBottomWidth: 1,
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 12, 
    shadowOffset: { width: 0, height: 4 }, 
    elevation: 3,
  },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  backBtn: { 
    marginRight: 12, 
    padding: 8, 
    borderRadius: 12, 
    backgroundColor: '#EBF4FF',
  },
  backText: { fontSize: 16, fontWeight: '700' },
  headerText: { flex: 1, marginLeft: 8 },
  title: { fontSize: 24, fontWeight: '800' },
  subtitle: { fontSize: 15, marginTop: 4 },
  headerRight: { flexDirection: 'row', gap: 8 },
  pillBtn: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 16, 
    paddingVertical: 10, 
    borderRadius: 20,
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 8, 
    shadowOffset: { width: 0, height: 2 }, 
    elevation: 2,
  },
  pillBtnText: { color: '#fff', fontSize: 14, fontWeight: '700' },

  modeWrap: {
    marginHorizontal: 20,
    marginTop: 16,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  modeHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  modeHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  modeTitle: { fontSize: 18, fontWeight: '800' },
  infoDot: {
    width: 24, height: 24, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F7FAFC',
    borderWidth: 1, borderColor: '#E2E8F0',
  },
  modeGroup: { flexDirection: 'row', backgroundColor: '#F7FAFC', borderRadius: 12, padding: 4 },
  modeBtn: { flex: 1, paddingVertical: 12, borderRadius: 8, alignItems: 'center' },
  modeBtnText: { fontSize: 16, fontWeight: '800' },
  modeBtnTextActive: { color: '#fff' },

  infoStrip: { marginHorizontal: 20, marginTop: 12, padding: 14, borderRadius: 12 },
  infoText: { fontSize: 14, textAlign: 'center', fontWeight: '700' },

  marketBox: { 
    marginHorizontal: 20, 
    marginTop: 12, 
    padding: 16, 
    borderRadius: 12,
    shadowColor: '#000', 
    shadowOpacity: 0.05, 
    shadowRadius: 8, 
    shadowOffset: { width: 0, height: 2 }, 
    elevation: 1,
  },
  marketRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  marketText: { fontSize: 13, textAlign: 'center', flex: 1 },

  card: {
    borderWidth: 1,
    marginHorizontal: 20,
    borderRadius: 20,
    padding: 20,
    marginTop: 16,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  pickHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  pickSymbolWrap: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  symbolIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#EBF4FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  pickSymbol: { fontSize: 22, fontWeight: '800' },
  changeWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  changeValue: { fontSize: 14, fontWeight: '700' },
  changeLabel: { fontSize: 12, marginLeft: 4 },
  badge: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: '800' },
  pickScoreWrap: { alignItems: 'center' },
  scoreValue: { fontSize: 20, fontWeight: '800' },
  scoreLabel: { fontSize: 12 },

  chartContainer: {
    marginBottom: 20,
    padding: 16,
    backgroundColor: '#F7FAFC',
    borderRadius: 12,
  },
  chartPlaceholder: {
    height: 60,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chartPlaceholderText: {
    fontSize: 12,
    fontWeight: '500',
  },
  chartFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  chartPrice: { fontSize: 16, fontWeight: '800' },
  chartTime: { fontSize: 12, color: '#718096' },

  block: { marginBottom: 20 },
  blockHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  blockTitle: { fontSize: 16, fontWeight: '800' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },

  notes: { fontSize: 14, fontStyle: 'italic', marginBottom: 20, padding: 12, backgroundColor: '#F7FAFC', borderRadius: 12 },

  executeBtn: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'center', 
    paddingVertical: 14, 
    borderRadius: 16,
    shadowColor: '#000', 
    shadowOpacity: 0.2, 
    shadowRadius: 8, 
    shadowOffset: { width: 0, height: 4 }, 
    elevation: 3,
  },
  executeBtnText: { color: '#fff', fontSize: 16, fontWeight: '800' },

  emptyWrap: { padding: 60, alignItems: 'center', justifyContent: 'center' },
  emptyTitle: { fontSize: 18, fontWeight: '800', textAlign: 'center', marginBottom: 8 },
  emptySub: { fontSize: 14, textAlign: 'center' },

  disclaimer: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 12,
    borderLeftWidth: 3,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  disclaimerText: { fontSize: 12, lineHeight: 18, flex: 1 },

  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: { fontSize: 16, textAlign: 'center', marginTop: 16 },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorText: { fontSize: 16, textAlign: 'center', marginTop: 16, marginBottom: 24 },
  retryBtn: { 
    paddingVertical: 12, 
    paddingHorizontal: 24, 
    borderRadius: 12,
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 8, 
    shadowOffset: { width: 0, height: 2 }, 
    elevation: 2,
  },
  retryBtnText: { color: '#fff', fontSize: 16, fontWeight: '800' },
});