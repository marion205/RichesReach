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
import { useQuery, useMutation } from '@apollo/client';
import { GET_DAY_TRADING_PICKS, LOG_DAY_TRADING_OUTCOME } from '../../../graphql/dayTrading';

type TradingMode = 'SAFE' | 'AGGRESSIVE';
type Side = 'LONG' | 'SHORT';

interface DayTradingPick {
  symbol: string;
  side: Side;
  score: number;
  features: {
    momentum15m: number;
    rvol10m: number;
    vwapDist: number;
    breakoutPct: number;
    spreadBps: number;
    catalystScore: number;
  };
  risk: {
    atr5m: number;
    sizeShares: number;
    stop: number;
    targets: number[];
    timeStopMin: number;
  };
  notes: string;
}

interface DayTradingData {
  asOf: string;
  mode: TradingMode;
  picks: DayTradingPick[];
  universeSize: number;
  qualityThreshold: number;
}

export default function DayTradingScreen({ navigateTo }: { navigateTo?: (screen: string) => void }) {
  const [mode, setMode] = useState<TradingMode>('SAFE');
  const [refreshing, setRefreshing] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch({ mode });
    } finally {
      setRefreshing(false);
    }
  }, [mode, refetch]);

  const handleModeChange = useCallback(
    async (newMode: TradingMode) => {
      if (newMode === mode) return;
      setMode(newMode);
      // refetch immediately on toggle for snappy UX
      await refetch({ mode: newMode });
    },
    [mode, refetch],
  );

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
      }, 60_000);
    }
    return () => {
      stopPolling?.();
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [mode, isMarketHours, refetch, startPolling, stopPolling]);

  // ---- UI color system ----
  const C = useMemo(
    () => ({
      bg: '#F5F5F7',
      card: '#FFFFFF',
      text: '#222222',
      sub: '#6B7280',
      border: '#E5E7EB',
      primary: '#0A84FF',
      safe: '#2EBD85',
      aggressive: '#FF9500',
      long: '#2EBD85',
      short: '#FF453A',
      warnBg: '#FFF7E6',
      warnBorder: '#FFE2AD',
      warnText: '#8A6D3B',
    }),
    [],
  );

  const getModeColor = (m: TradingMode) => (m === 'SAFE' ? C.safe : C.aggressive);
  const getSideColor = (side: Side) => (side === 'LONG' ? C.long : C.short);
  const getScoreColor = (score: number) => (score >= 2 ? C.long : score >= 1 ? C.aggressive : C.short);

  // robust entry computation (use atr around stop; invert for SHORT)
  const computeEntry = (pick: DayTradingPick) =>
    pick.side === 'LONG' ? pick.risk.stop + pick.risk.atr5m : Math.max(0, pick.risk.stop - pick.risk.atr5m);

  const handleTradeExecution = useCallback(
    (pick: DayTradingPick) => {
      const entry = computeEntry(pick);
      const primaryTarget = pick.risk.targets?.[0] ?? entry;
      Alert.alert(
        'Execute Trade',
        `Execute ${pick.side} ${pick.symbol}?\n\nEntry: $${entry.toFixed(2)}\nStop: $${pick.risk.stop.toFixed(
          2,
        )}\nTarget: $${Number(primaryTarget).toFixed(2)}\nSize: ${pick.risk.size_shares} shares`,
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
                      sizeShares: pick.risk.sizeShares,
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

  // ---- renderers ----
  const renderPick = useCallback(
    ({ item }: { item: DayTradingPick }) => {
      const entry = computeEntry(item);
      const target = item.risk.targets?.[0] ?? entry;
      return (
        <View style={[styles.card, { backgroundColor: C.card, borderColor: C.border }]}>
          {/* Header */}
          <View style={styles.pickHeader}>
            <View style={styles.pickSymbolWrap}>
              <Text style={[styles.pickSymbol, { color: C.text }]} accessibilityRole="text" accessibilityLabel={`Symbol ${item.symbol}`}>
                {item.symbol}
              </Text>
              <View style={[styles.badge, { backgroundColor: getSideColor(item.side) }]}>
                <Text style={styles.badgeText}>{item.side}</Text>
              </View>
            </View>
            <View style={styles.pickScoreWrap}>
              <Text style={[styles.scoreValue, { color: getScoreColor(item.score) }]}>{item.score.toFixed(2)}</Text>
              <Text style={[styles.scoreLabel, { color: C.sub }]}>Score</Text>
            </View>
          </View>

          {/* Features */}
          <View style={styles.block}>
            <Text style={[styles.blockTitle, { color: C.text }]}>Key Features</Text>
            <View style={styles.grid}>
              <KV label="Momentum" value={item.features.momentum15m.toFixed(3)} />
              <KV label="RVOL" value={`${item.features.rvol10m.toFixed(2)}x`} />
              <KV label="VWAP" value={item.features.vwapDist.toFixed(3)} />
              <KV label="Breakout" value={item.features.breakoutPct.toFixed(3)} />
            </View>
          </View>

          {/* Risk */}
          <View style={styles.block}>
            <Text style={[styles.blockTitle, { color: C.text }]}>Risk Management</Text>
            <View style={styles.grid}>
              <KV label="Size" value={`${item.risk.sizeShares} shares`} />
              <KV label="Entry" value={`$${entry.toFixed(2)}`} />
              <KV label="Stop" value={`$${item.risk.stop.toFixed(2)}`} />
              <KV label="Target" value={`$${Number(target).toFixed(2)}`} />
              <KV label="Time Stop" value={`${item.risk.timeStopMin} min`} />
              <KV label="ATR(5m)" value={`${item.risk.atr5m.toFixed(2)}`} />
            </View>
          </View>

          {item.notes ? <Text style={[styles.notes, { color: C.sub }]}>{item.notes}</Text> : null}

          <TouchableOpacity
            style={[styles.executeBtn, { backgroundColor: getSideColor(item.side) }]}
            onPress={() => handleTradeExecution(item)}
            accessibilityRole="button"
            accessibilityLabel={`Execute ${item.side} ${item.symbol}`}
          >
            <Text style={styles.executeBtnText}>Execute {item.side} Trade</Text>
          </TouchableOpacity>
        </View>
      );
    },
    [C, getScoreColor, getSideColor, handleTradeExecution],
  );

  // ---- header / top ----
  const Header = (
    <View>
      <View style={[styles.header, { backgroundColor: C.card, borderBottomColor: C.border }]}>
        <View style={styles.headerRow}>
          <View style={styles.headerLeft}>
            {navigateTo && (
              <TouchableOpacity style={styles.backBtn} onPress={() => navigateTo('trading')} accessibilityRole="button" accessibilityLabel="Back">
                <Text style={[styles.backText, { color: C.primary }]}>Back</Text>
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
                <Text style={styles.pillBtnText}>Risk</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.pillBtn, { backgroundColor: '#9C27B0' }]} onPress={() => navigateTo('ml-system')}>
                <Text style={styles.pillBtnText}>ML</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>

      {/* Mode Toggle */}
      <View style={[styles.modeWrap, { backgroundColor: C.card, shadowColor: '#000' }]}>
        <View style={styles.modeHeader}>
          <Text style={[styles.modeTitle, { color: C.text }]}>Trading Mode</Text>
          <TouchableOpacity
            style={styles.infoDot}
            onPress={() =>
              Alert.alert(
                'Trading Modes',
                'SAFE: Conservative picks with tighter thresholds and liquidity filters.\n\nAGGRESSIVE: Higher-variance picks with looser filters and broader universe.\n\nPosition sizing/time-stop differ by mode.',
              )
            }
          >
            <Text style={{ fontWeight: '700' }}>i</Text>
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
      <View style={[styles.infoStrip, { backgroundColor: '#E7F1FF' }]}>
        <Text style={[styles.infoText, { color: '#0F62FE' }]}>
          {mode === 'SAFE'
            ? '0.5% risk per trade • 45 min time-stop • Large-cap/liquid universe'
            : '1.2% risk per trade • 25 min time-stop • Extended universe'}
        </Text>
      </View>

      {/* Market Status */}
      {dayTradingData && (
        <View style={[styles.marketBox, { backgroundColor: C.card }]}>
          <Text style={[styles.marketText, { color: C.sub }]}>
            Last Updated: {new Date(dayTradingData.asOf).toLocaleTimeString()}
          </Text>
          <Text style={[styles.marketText, { color: C.sub }]}>
            Universe: {dayTradingData.universeSize} • Threshold: {dayTradingData.qualityThreshold}
          </Text>
        </View>
      )}
    </View>
  );

  // ---- states ----
  if (loading && !dayTradingData) {
    return (
      <View style={[styles.container, { backgroundColor: C.bg }]}>
        <ActivityIndicator size="small" color={C.primary} style={{ marginTop: 48 }} />
        <Text style={[styles.loadingText, { color: C.sub }]}>Loading day trading picks…</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, { backgroundColor: C.bg }]}>
        <Text style={[styles.errorText, { color: C.short }]}>
          Error loading picks: {error.message}
        </Text>
        <TouchableOpacity style={[styles.retryBtn, { backgroundColor: C.primary }]} onPress={onRefresh}>
          <Text style={styles.retryBtnText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const picks = dayTradingData?.picks ?? [];

  return (
    <View style={[styles.container, { backgroundColor: C.bg }]}>
      <FlatList
        data={picks}
        keyExtractor={(item, idx) => `${item.symbol}-${item.side}-${idx}`}
        ListHeaderComponent={Header}
        renderItem={renderPick}
        contentContainerStyle={{ paddingBottom: 24 }}
        refreshControl={<RefreshControl refreshing={refreshing || networkStatus === 4} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.emptyWrap}>
            <Text style={[styles.emptyTitle, { color: C.sub }]}>No qualifying picks for {mode} mode</Text>
            <Text style={[styles.emptySub, { color: '#9CA3AF' }]}>
              Quality threshold not met or market conditions unsuitable
            </Text>
          </View>
        }
      />

      {/* Disclaimer (no emoji to avoid overflow/bleed) */}
      <View style={[styles.disclaimer, { borderLeftColor: C.warnBorder, backgroundColor: C.warnBg }]}>
        <Text style={[styles.disclaimerText, { color: C.warnText }]}>
          Day trading involves significant risk. Only trade with capital you can afford to lose. Past performance does
          not guarantee future results.
        </Text>
      </View>
    </View>
  );
}

/* ============ Small subcomponent ============ */
function KV({ label, value }: { label: string; value: string }) {
  return (
    <View style={{ width: '48%', marginBottom: 8 }}>
      <Text style={{ fontSize: 12, color: '#6B7280' }}>{label}</Text>
      <Text style={{ fontSize: 14, fontWeight: '700', color: '#1F2937' }}>{value}</Text>
    </View>
  );
}

/* ============ Styles ============ */
const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { padding: 20, borderBottomWidth: 1 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  backBtn: { marginRight: 12, paddingVertical: 6, paddingHorizontal: 10 },
  backText: { fontSize: 16, fontWeight: '600' },
  headerText: { flex: 1 },
  title: { fontSize: 22, fontWeight: '800' },
  subtitle: { fontSize: 14, marginTop: 4 },
  headerRight: { flexDirection: 'row', gap: 8 },
  pillBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 18 },
  pillBtnText: { color: '#fff', fontSize: 13, fontWeight: '700' },

  modeWrap: {
    marginHorizontal: 20,
    marginTop: 16,
    borderRadius: 8,
    padding: 14,
    shadowOpacity: 0.08,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  modeHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  modeTitle: { fontSize: 16, fontWeight: '800' },
  infoDot: {
    width: 22, height: 22, borderRadius: 11, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F2F2F2',
  },
  modeGroup: { flexDirection: 'row', backgroundColor: '#F5F5F5', borderRadius: 6, padding: 4 },
  modeBtn: { flex: 1, paddingVertical: 10, borderRadius: 6, alignItems: 'center' },
  modeBtnText: { fontSize: 15, fontWeight: '700' },
  modeBtnTextActive: { color: '#fff' },

  infoStrip: { marginHorizontal: 20, marginTop: 10, padding: 10, borderRadius: 8 },
  infoText: { fontSize: 13, textAlign: 'center', fontWeight: '600' },

  marketBox: { marginHorizontal: 20, marginTop: 10, padding: 12, borderRadius: 8 },
  marketText: { fontSize: 12, textAlign: 'center' },

  card: {
    borderWidth: 1,
    marginHorizontal: 20,
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  pickHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  pickSymbolWrap: { flexDirection: 'row', alignItems: 'center' },
  pickSymbol: { fontSize: 20, fontWeight: '800', marginRight: 8 },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: '800' },
  pickScoreWrap: { alignItems: 'center' },
  scoreValue: { fontSize: 18, fontWeight: '800' },
  scoreLabel: { fontSize: 11 },

  block: { marginBottom: 14 },
  blockTitle: { fontSize: 14, fontWeight: '800', marginBottom: 8 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },

  notes: { fontSize: 13, fontStyle: 'italic', marginBottom: 14 },

  executeBtn: { paddingVertical: 12, borderRadius: 8, alignItems: 'center' },
  executeBtnText: { color: '#fff', fontSize: 15, fontWeight: '800' },

  emptyWrap: { padding: 40, alignItems: 'center' },
  emptyTitle: { fontSize: 16, fontWeight: '700', textAlign: 'center', marginBottom: 6 },
  emptySub: { fontSize: 13, textAlign: 'center' },

  disclaimer: {
    marginHorizontal: 20,
    marginVertical: 16,
    padding: 12,
    borderLeftWidth: 4,
    borderRadius: 8,
  },
  disclaimerText: { fontSize: 12, lineHeight: 18 },

  loadingText: { fontSize: 14, textAlign: 'center', marginTop: 12 },
  errorText: { fontSize: 14, textAlign: 'center', marginTop: 32, marginHorizontal: 20 },
  retryBtn: { marginTop: 16, paddingVertical: 10, paddingHorizontal: 24, borderRadius: 8, alignSelf: 'center' },
  retryBtnText: { color: '#fff', fontSize: 15, fontWeight: '800' },
});