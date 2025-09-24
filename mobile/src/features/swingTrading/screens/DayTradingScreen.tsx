import React, { useMemo, useCallback, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, RefreshControl, Alert, FlatList, SafeAreaView,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { GET_DAY_TRADING_PICKS, LOG_DAY_TRADING_OUTCOME } from '../../../graphql/dayTrading';
import Icon from 'react-native-vector-icons/Feather';

type Side = 'LONG' | 'SHORT';
type TradingMode = 'SAFE' | 'AGGRESSIVE';

interface Features {
  momentum_15m: number; rvol_10m: number; vwap_dist: number; breakout_pct: number; spread_bps: number; catalyst_score: number;
}
interface Risk { atr_5m: number; size_shares: number; stop: number; targets: number[]; time_stop_min: number; }
interface DayTradingPick { symbol: string; side: Side; score: number; features: Features; risk: Risk; notes: string; }
interface DayTradingData { as_of: string; mode: TradingMode; picks: DayTradingPick[]; universe_size: number; quality_threshold: number; }

const C = {
  bg: '#F5F6FA', card: '#FFFFFF', line: '#E9EAF0', text: '#111827', sub: '#6B7280',
  primary: '#0E7AFE', green: '#22C55E', red: '#EF4444', amber: '#F59E0B', shadow: 'rgba(16,24,40,0.08)',
};

export default function DayTradingScreen({ navigateTo }: { navigateTo?: (s: string) => void }) {
  const [mode, setMode] = useState<TradingMode>('SAFE');
  const [refreshing, setRefreshing] = useState(false);

  const { data, loading, error, refetch, networkStatus } = useQuery<{ dayTradingPicks: DayTradingData }>(
    GET_DAY_TRADING_PICKS,
    { variables: { mode }, fetchPolicy: 'cache-and-network', notifyOnNetworkStatusChange: true, errorPolicy: 'all' }
  );
  const [logOutcome] = useMutation(LOG_DAY_TRADING_OUTCOME);

  const dayTradingData = data?.dayTradingPicks ?? null;
  const picks = useMemo(() => dayTradingData?.picks ?? [], [dayTradingData]);

  const modeMeta = useMemo(() => (
    mode === 'SAFE'
      ? { bg: '#E8FFF2', txt: '#065F46', info: '0.5% risk per trade • 45 min time stop • liquid names' }
      : { bg: '#FFF7E6', txt: '#7C2D12', info: '1.2% risk per trade • 25 min time stop • extended universe' }
  ), [mode]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try { await refetch({ mode }); } finally { setRefreshing(false); }
  }, [refetch, mode]);

  const getSideColor = (s: Side) => (s === 'LONG' ? C.green : C.red);
  const getScoreColor = (score: number) => (score >= 2 ? C.green : score >= 1 ? C.amber : C.red);

  const handleExecute = useCallback((pick: DayTradingPick) => {
    const entryApprox = (pick.risk.stop + pick.risk.atr_5m).toFixed(2);
    const tgt = pick.risk.targets?.[0]?.toFixed(2);
    Alert.alert(
      'Confirm Trade',
      `Execute ${pick.side} ${pick.symbol}?\nEntry≈ $${entryApprox}\nStop: $${pick.risk.stop.toFixed(2)}\nTarget: $${tgt ?? '—'}`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Execute', onPress: () => Alert.alert('Order accepted', 'Simulated execution complete.') },
      ]
    );
  }, []);

  const renderHeader = useCallback(() => (
    <View style={s.header}>
      <View style={s.hLeft}>
        {navigateTo ? (
          <TouchableOpacity style={s.back} onPress={() => navigateTo('trading')} testID="back-btn">
            <Icon name="arrow-left" size={24} color="#6B7280" />
          </TouchableOpacity>
        ) : <View />}
        <View>
          <Text style={s.title}>Daily Top-3 Picks</Text>
          <Text style={s.subtitle}>Intraday opportunities</Text>
        </View>
      </View>
      {navigateTo ? (
        <View style={s.hBtns}>
          <TouchableOpacity style={[s.badgeBtn, { backgroundColor: '#E6EEFF' }]} onPress={() => navigateTo('risk-management')}>
            <Text style={[s.badgeTxt, { color: '#1D4ED8' }]}>Risk</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[s.badgeBtn, { backgroundColor: '#F5E8FF' }]} onPress={() => navigateTo('ml-system')}>
            <Text style={[s.badgeTxt, { color: '#7C3AED' }]}>ML</Text>
          </TouchableOpacity>
        </View>
      ) : null}
      <View style={[s.modeInfo, { backgroundColor: modeMeta.bg }]}>
        <View style={s.rowSpace}>
          <Text style={[s.modeTitle, { color: modeMeta.txt }]}>Mode</Text>
          <View style={s.modeRow}>
            {(['SAFE', 'AGGRESSIVE'] as const).map(m => (
              <TouchableOpacity
                key={m}
                onPress={() => setMode(m)}
                style={[s.modePill, mode === m && { backgroundColor: C.primary }]}
                testID={`mode-${m}`}
              >
                <Text style={[s.modePillTxt, mode === m && { color: '#fff' }]}>{m}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        <Text style={[s.modeSub, { color: modeMeta.txt }]}>{modeMeta.info}</Text>
      </View>

      {dayTradingData && (
        <View style={s.metaBar}>
          <Text style={s.meta}>Updated {new Date(dayTradingData.as_of).toLocaleTimeString()}</Text>
          <Text style={s.meta}>Universe {dayTradingData.universe_size} • Threshold {dayTradingData.quality_threshold}</Text>
        </View>
      )}
    </View>
  ), [navigateTo, dayTradingData, mode, modeMeta]);

  const renderItem = useCallback(({ item }: { item: DayTradingPick }) => (
    <View style={s.card}>
      <View style={s.cardTop}>
        <View style={s.symRow}>
          <Text style={s.sym}>{item.symbol}</Text>
          <View style={[s.sideChip, { backgroundColor: getSideColor(item.side) }]}>
            <Text style={s.sideChipTxt}>{item.side}</Text>
          </View>
        </View>
        <View style={s.scoreCol}>
          <Text style={[s.score, { color: getScoreColor(item.score) }]}>{item.score.toFixed(2)}</Text>
          <Text style={s.scoreLbl}>Score</Text>
        </View>
      </View>

      <View style={s.section}>
        <Text style={s.sectionTitle}>Key Features</Text>
        <View style={s.grid}>
          <KV k="Momentum" v={item.features.momentum_15m.toFixed(3)} />
          <KV k="RVOL" v={`${item.features.rvol_10m.toFixed(2)}×`} />
          <KV k="VWAP Dist" v={item.features.vwap_dist.toFixed(3)} />
          <KV k="Breakout" v={item.features.breakout_pct.toFixed(3)} />
        </View>
      </View>

      <View style={s.section}>
        <Text style={s.sectionTitle}>Risk</Text>
        <View style={s.grid}>
          <KV k="Size" v={`${item.risk.size_shares} sh`} />
          <KV k="Stop" v={`$${item.risk.stop.toFixed(2)}`} />
          <KV k="Target" v={item.risk.targets?.[0] ? `$${item.risk.targets[0].toFixed(2)}` : '—'} />
          <KV k="Time Stop" v={`${item.risk.time_stop_min}m`} />
        </View>
      </View>

      {item.notes ? <Text style={s.notes}>{item.notes}</Text> : null}

      <TouchableOpacity onPress={() => handleExecute(item)} style={[s.primary, { backgroundColor: getSideColor(item.side) }]} testID="execute-btn">
        <Text style={s.primaryTxt}>Execute {item.side} Trade</Text>
      </TouchableOpacity>
    </View>
  ), [handleExecute]);

  if (loading && !dayTradingData) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: C.bg }}>
        <View style={{ padding: 20 }}><Text style={{ textAlign: 'center', color: C.sub }}>Loading day trading picks…</Text></View>
      </SafeAreaView>
    );
  }
  if (error) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: C.bg }}>
        <View style={{ padding: 20 }}>
          <Text style={{ textAlign: 'center', color: C.red }}>Error: {error.message}</Text>
          <TouchableOpacity style={[s.primary, { backgroundColor: C.primary }]} onPress={onRefresh}><Text style={s.primaryTxt}>Retry</Text></TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.bg }}>
      <FlatList
        data={picks}
        keyExtractor={(it) => `${it.symbol}-${it.side}`}
        renderItem={renderItem}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={
          <View style={{ padding: 20, alignItems: 'center' }}>
            <Text style={{ color: C.sub }}>No qualifying picks for {mode}</Text>
            <Text style={{ color: C.sub, fontSize: 12, marginTop: 6 }}>Quality threshold not met or market not suitable</Text>
          </View>
        }
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 12, paddingTop: 8 }}
        refreshControl={<RefreshControl refreshing={refreshing || networkStatus === 4} onRefresh={onRefresh} />}
        removeClippedSubviews
        windowSize={7}
        initialNumToRender={4}
        maxToRenderPerBatch={6}
        testID="picks-list"
      />
      <View style={s.disclaimer}>
        <Text style={s.disclaimerTxt}>
          Day trading is high risk. Never trade money you cannot afford to lose. Past performance does not guarantee future results.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const KV = ({ k, v }: { k: string; v: string }) => (
  <View style={{ width: '48%', marginBottom: 6 }}>
    <Text style={{ fontSize: 12, color: C.sub }}>{k}</Text>
    <Text style={{ fontSize: 14, fontWeight: '700', color: C.text }}>{v}</Text>
  </View>
);

const s = StyleSheet.create({
  header: { backgroundColor: C.card, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line, padding: 12, marginBottom: 8 },
  hLeft: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  back: { padding: 8, marginRight: 8 },
  title: { fontSize: 20, fontWeight: '800', color: C.text },
  subtitle: { color: C.sub, marginTop: 2 },
  hBtns: { flexDirection: 'row', gap: 8, marginTop: 8 },
  badgeBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  badgeTxt: { fontWeight: '700' },
  modeInfo: { marginTop: 8, borderRadius: 10, padding: 10 },
  rowSpace: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  modeTitle: { fontSize: 12, fontWeight: '800' },
  modeRow: { flexDirection: 'row', gap: 8 },
  modePill: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999, backgroundColor: '#E8ECF6' },
  modePillTxt: { fontWeight: '700', color: '#5B6473' },
  modeSub: { fontSize: 12, marginTop: 6 },
  metaBar: { marginTop: 6, alignItems: 'center', gap: 2 },
  meta: { fontSize: 12, color: C.sub },
  card: { backgroundColor: C.card, borderRadius: 12, padding: 14, marginBottom: 8, shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 6, shadowOffset: { width: 0, height: 2 } },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  symRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sym: { fontSize: 18, fontWeight: '800', color: C.text },
  sideChip: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  sideChipTxt: { color: '#fff', fontWeight: '700', fontSize: 12 },
  scoreCol: { alignItems: 'center' },
  score: { fontSize: 18, fontWeight: '800' },
  scoreLbl: { fontSize: 12, color: C.sub },
  section: { marginTop: 10 },
  sectionTitle: { fontWeight: '700', color: C.text, marginBottom: 6 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  notes: { color: C.sub, fontStyle: 'italic', marginTop: 4 },
  primary: { marginTop: 12, paddingVertical: 12, borderRadius: 10, alignItems: 'center' },
  primaryTxt: { color: '#fff', fontWeight: '800' },
  disclaimer: { paddingHorizontal: 16, paddingBottom: 8 },
  disclaimerTxt: { fontSize: 11, color: C.sub, lineHeight: 16, textAlign: 'center' },
});
