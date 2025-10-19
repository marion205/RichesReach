/**
 * Crypto ML Signals Card – polished with auto-refresh
 */

import React, { useMemo, useRef, useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, Alert, Animated
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import {
  GET_SUPPORTED_CURRENCIES,
  GET_CRYPTO_ML_SIGNAL,
  GENERATE_ML_PREDICTION
} from '../../graphql/cryptoQueries';
import { gql } from '@apollo/client';

// Add this lightweight holdings query
const GET_CRYPTO_HOLDINGS = gql`
  query GetCryptoHoldings {
    cryptoPortfolio {
      holdings {
        cryptocurrency { symbol }
        quantity
      }
    }
  }
`;

type Props = { 
  initialSymbol?: string;
  pollInterval?: number; // ms
};

/* ------------------------------ Utilities ------------------------------ */

const clamp01 = (x?: number) => Math.max(0, Math.min(1, Number.isFinite(x ?? 0) ? (x as number) : 0));
const pctStr = (p?: number, digits = 1) => `${(clamp01(p) * 100).toFixed(digits)}%`;

const confidenceTone = (lvl?: string) => {
  switch ((lvl || '').toUpperCase()) {
    case 'HIGH': return { color: '#22C55E', icon: 'zap' };
    case 'MEDIUM': return { color: '#F59E0B', icon: 'activity' };
    case 'LOW': return { color: '#EF4444', icon: 'alert-circle' };
    default: return { color: '#6B7280', icon: 'help-circle' };
  }
};

const probTone = (p?: number) => {
  const v = clamp01(p);
  if (v >= 0.7) return '#22C55E';
  if (v >= 0.5) return '#F59E0B';
  return '#EF4444';
};

/* ------------------------------- Component ------------------------------ */

const CryptoMLSignalsCard: React.FC<Props> = ({ initialSymbol = 'BTC', pollInterval }) => {
  const [selectedSymbol, setSelectedSymbol] = useState(initialSymbol);
  const [generating, setGenerating] = useState(false);
  const [ownedOnly, setOwnedOnly] = useState(false);
  const topPicked = useRef(false);

  // Spin animation for refresh
  const spin = useRef(new Animated.Value(0)).current;
  const spinOnce = () => {
    spin.setValue(0);
    Animated.timing(spin, { toValue: 1, duration: 600, useNativeDriver: true }).start();
  };
  const spinStyle = { transform: [{ rotate: spin.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] }) }] };

  /* ------------------------------- Queries ------------------------------ */

  const { data: currenciesData } = useQuery(GET_SUPPORTED_CURRENCIES, {
    fetchPolicy: 'cache-first',
    errorPolicy: 'all',
  });

  const { data: holdingsData } = useQuery(GET_CRYPTO_HOLDINGS);

  const {
    data: signalData,
    loading: signalLoading,
    error: signalError,
    refetch: refetchSignal,
    networkStatus,
  } = useQuery(GET_CRYPTO_ML_SIGNAL, {
    variables: { symbol: selectedSymbol },
    skip: !selectedSymbol,
    fetchPolicy: 'cache-and-network',
    notifyOnNetworkStatusChange: true,
    errorPolicy: 'all',
    pollInterval,
  });

  const [generatePrediction] = useMutation(GENERATE_ML_PREDICTION, {
    errorPolicy: 'all',
  });

  // Derive owned + top 5 cryptocurrencies
  const ownedRows = holdingsData?.cryptoPortfolio?.holdings ?? [];
  const ownedSymbols: string[] = ownedRows
    .map((h: any) => h?.cryptocurrency?.symbol)
    .filter(Boolean);

  const supported = currenciesData?.supportedCurrencies ?? [];
  const supportedSymbols = supported.map((c: any) => c.symbol);
  
  // Top 5 cryptocurrencies by market cap (BTC, ETH, ADA, SOL, DOT)
  const top5Symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT'];
  
  // When ownedOnly is false, show top 5 + owned (deduped)
  // When ownedOnly is true, show only owned
  const mergedSymbols = ownedOnly 
    ? ownedSymbols 
    : Array.from(new Set([...top5Symbols, ...ownedSymbols]));
  
  const finalSymbols = mergedSymbols;

  // quick qty lookup
  const qtyBySymbol: Record<string, number> = ownedRows.reduce((acc: any, h: any) => {
    const s = h?.cryptocurrency?.symbol;
    if (s) acc[s] = (acc[s] ?? 0) + parseFloat(h?.quantity ?? 0);
    return acc;
  }, {});

  // build a price lookup for auto-selection
  const symbolToPrice: Record<string, number> = Object.fromEntries(
    (currenciesData?.supportedCurrencies ?? []).map((c: any) => [c.symbol, c.priceUsd ?? 0])
  );

  // auto-pick on mount / holdings change
  useEffect(() => {
    if (topPicked.current) return;
    const rows = holdingsData?.cryptoPortfolio?.holdings ?? [];
    if (!rows.length) return;

    const best = rows
      .map((h: any) => {
        const sym = h?.cryptocurrency?.symbol;
        const qty = parseFloat(h?.quantity ?? 0);
        const px = symbolToPrice[sym] ?? 0;
        return { sym, value: qty * px };
      })
      .filter(r => r.sym)
      .sort((a, b) => b.value - a.value)[0];

    if (best?.sym) {
      setSelectedSymbol(best.sym);
      topPicked.current = true;
    }
  }, [holdingsData, symbolToPrice]);

  const signal = useMemo(() => {
    const s = signalData?.cryptoMlSignal ?? {};
    // safe defaults to avoid client crashes
    return {
      predictionType: (s.predictionType || 'NEUTRAL').replace('_', ' '),
      probability: clamp01(s.probability),
      confidenceLevel: (s.confidenceLevel || 'LOW').toUpperCase(),
      sentiment: s.sentiment || 'Neutral',
      sentimentDescription: s.sentimentDescription || 'Neutral market conditions.',
      featuresUsed: s.featuresUsed || {},
      createdAt: s.createdAt || new Date().toISOString(),
      expiresAt: s.expiresAt || new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString(), // +6h
      explanation: s.explanation || 'Model output available. Awaiting more data for richer rationale.',
    };
  }, [signalData]);

  /* ------------------------------- Auto-refresh ------------------------------ */

  // auto-refresh (cleans up on unmount and on symbol change)
  useEffect(() => {
    if (!pollInterval || pollInterval < 10_000) return; // guard: min 10s
    let alive = true;
    const id = setInterval(async () => {
      if (!alive) return;
      try { await refetchSignal(); } catch {}
    }, pollInterval);
    return () => { alive = false; clearInterval(id); };
  }, [pollInterval, selectedSymbol, refetchSignal]);

  /* --------------------------------- UX --------------------------------- */

  const onRefresh = async () => {
    spinOnce();
    await refetchSignal();
  };

  const onGenerate = async () => {
    try {
      setGenerating(true);
      const res = await generatePrediction({ variables: { symbol: selectedSymbol } });
      const ok = res.data?.generateMlPrediction?.success;
      if (ok) {
        const p = clamp01(res.data.generateMlPrediction.probability);
        Alert.alert('Prediction Generated', `${selectedSymbol}: ${pctStr(p)} probability`);
        await refetchSignal();
      } else {
        Alert.alert('Error', res.data?.generateMlPrediction?.message || 'Failed to generate prediction.');
      }
    } catch (e) {
      Alert.alert('Error', 'Failed to generate prediction. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const symList = finalSymbols.slice(0, 12);

  const bigDay = useMemo(() => {
    // Showcase badge if probability of a move is high (tune threshold as you like)
    return signal.probability >= 0.7;
  }, [signal]);

  /* ------------------------------ Rendering ----------------------------- */

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Symbol Selection */}
      <View style={styles.section}>
        <View style={[styles.section, {flexDirection:'row', justifyContent:'space-between', alignItems:'center'}]}>
          <Text style={styles.sectionTitle}>Select Cryptocurrency</Text>
          <TouchableOpacity
            onPress={() => setOwnedOnly(v => !v)}
            style={[
              styles.ownedToggle,
              ownedOnly && styles.ownedToggleActive
            ]}
          >
            <Icon name="user-check" size={14} color={ownedOnly ? '#007AFF' : '#6B7280'} />
            <Text style={[styles.ownedToggleText, ownedOnly && { color:'#007AFF', fontWeight:'700' }]}>
              Owned
            </Text>
          </TouchableOpacity>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.symbolRow}>
          {symList.map((sym: string) => {
            const active = selectedSymbol === sym;
            const qty = qtyBySymbol[sym] || 0;
            const isOwned = qty > 0;
            return (
              <TouchableOpacity
                key={sym}
                style={[styles.pill, active && styles.pillActive]}
                onPress={() => setSelectedSymbol(sym)}
                activeOpacity={0.9}
              >
                <Text style={[styles.pillText, active && styles.pillTextActive]}>{sym}</Text>
                {isOwned && (
                  <View style={styles.ownedPill}>
                    <Icon name="check" size={10} color="#10B981" />
                    <Text style={styles.ownedPillText}>{qty.toFixed(3)}</Text>
                  </View>
                )}
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* Generate */}
      <TouchableOpacity style={[styles.primaryBtn, generating && { opacity: 0.7 }]} onPress={onGenerate} disabled={generating}>
        {generating ? <ActivityIndicator color="#fff" /> : <>
          <Icon name="cpu" size={18} color="#fff" />
          <Text style={styles.primaryBtnText}>Generate AI Prediction</Text>
        </>}
      </TouchableOpacity>

      {/* Card */}
      {signalLoading && networkStatus !== 7 ? (
        <View style={styles.card}>
          {/* Skeleton */}
          <View style={styles.rowBetween}>
            <View style={[styles.skelDot, { width: 120, height: 18 }]} />
            <View style={[styles.skelDot, { width: 20, height: 20, borderRadius: 10 }]} />
          </View>
          <View style={[styles.skelDot, { width: '60%', height: 30, marginTop: 16 }]} />
          <View style={[styles.skelDot, { width: '40%', height: 18, marginTop: 8 }]} />
          <View style={[styles.skelDot, { width: '100%', height: 64, marginTop: 16 }]} />
        </View>
      ) : signalError ? (
        <View style={styles.card}>
          <View style={styles.errorContainer}>
            <Icon name="alert-triangle" size={24} color="#EF4444" />
            <Text style={styles.errorTitle}>Error Loading Signal</Text>
            <Text style={styles.errorText}>{signalError.message}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={onRefresh}>
              <Icon name="refresh-cw" size={16} color="#007AFF" />
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : signalData?.cryptoMlSignal ? (
        <View style={styles.card}>
          <View style={styles.rowBetween}>
            <View style={styles.rowCenter}>
              {(() => {
                const tone = confidenceTone(signal.confidenceLevel);
                return <>
                  <Icon name={tone.icon} size={22} color={tone.color} />
                  <Text style={styles.title}>{signal.predictionType}</Text>
                </>;
              })()}
              {bigDay && (
                <View style={styles.badgeBigDay}>
                  <Icon name="zap" size={12} color="#7C3AED" />
                  <Text style={styles.badgeText}>BIG DAY</Text>
                </View>
              )}
            </View>
            <TouchableOpacity onPress={onRefresh} activeOpacity={0.7} accessibilityLabel="Refresh">
              <Animated.View style={spinStyle}>
                <Icon name="refresh-cw" size={20} color="#007AFF" />
              </Animated.View>
            </TouchableOpacity>
          </View>

          {/* Probability + Confidence */}
          <View style={styles.rowSplit}>
            <View style={{ flex: 1 }}>
              <Text style={styles.sub}>Probability</Text>
              <Text style={[styles.prob, { color: probTone(signal.probability) }]}>{pctStr(signal.probability)}</Text>
              {/* small progress bar */}
              <View style={styles.progress}>
                <View style={[styles.progressFill, { width: `${clamp01(signal.probability) * 100}%` }]} />
              </View>
            </View>

            <View style={{ flex: 1, alignItems: 'flex-end' }}>
              <Text style={styles.sub}>Confidence</Text>
              {(() => {
                const tone = confidenceTone(signal.confidenceLevel);
                return (
                  <View style={styles.confBadge}>
                    <Icon name={tone.icon} size={14} color={tone.color} />
                    <Text style={[styles.confText, { color: tone.color }]}>{signal.confidenceLevel}</Text>
                  </View>
                );
              })()}
              <Text style={styles.sentiment}>{signal.sentiment}</Text>
              <Text style={styles.sentimentSub} numberOfLines={2}>{signal.sentimentDescription}</Text>
            </View>
          </View>

          {/* Explanation */}
          <View style={{ marginTop: 12 }}>
            <Text style={styles.h6}>AI Analysis</Text>
            <Text style={styles.body}>{signal.explanation}</Text>
          </View>

          {/* Key factors */}
          {Object.keys(signal.featuresUsed || {}).length > 0 && (
            <View style={{ marginTop: 12 }}>
              <Text style={styles.h6}>Key Factors</Text>
              <View style={styles.tagsWrap}>
                {Object.entries(signal.featuresUsed).slice(0, 4).map(([k, v]) => (
                  <View key={k} style={styles.tag}>
                    <Text style={styles.tagKey}>{k.replace(/_/g, ' ').toUpperCase()}</Text>
                    <Text style={styles.tagVal}>{typeof v === 'number' ? v.toFixed(3) : String(v)}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Timestamps */}
          <View style={styles.footer}>
            <Text style={styles.meta}>Generated: {new Date(signal.createdAt).toLocaleString()}</Text>
            <Text style={styles.meta}>Expires: {new Date(signal.expiresAt).toLocaleString()}</Text>
          </View>
        </View>
      ) : (
        <View style={styles.empty}>
          <Icon name="zap" size={42} color="#9CA3AF" />
          <Text style={styles.emptyTitle}>No Signal Yet</Text>
          <Text style={styles.emptySub}>Generate an AI prediction for {selectedSymbol} to see insights.</Text>
        </View>
      )}

      {/* Risk note */}
      <View style={styles.notice}>
        <Icon name="alert-triangle" size={18} color="#B45309" />
        <Text style={styles.noticeText}>
          AI predictions are informational and not investment advice. Consider your risk tolerance.
        </Text>
      </View>
    </ScrollView>
  );
};

/* -------------------------------- Styles ------------------------------- */

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 20 },
  section: { marginBottom: 16 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#111827', marginBottom: 10 },
  symbolRow: { flexDirection: 'row' },
  pill: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: '#F3F4F6', marginRight: 8 },
  pillActive: { backgroundColor: '#007AFF' },
  pillText: { fontSize: 14, fontWeight: '600', color: '#6B7280' },
  pillTextActive: { color: '#fff' },
  ownedToggle: { flexDirection:'row', alignItems:'center', gap:6, paddingHorizontal:10, paddingVertical:6, borderRadius:14, backgroundColor:'#F3F4F6' },
  ownedToggleActive: { backgroundColor:'#EEF6FF', borderWidth:1, borderColor:'#BBD7FF' },
  ownedToggleText: { fontSize:12, color:'#6B7280', fontWeight:'600' },
  ownedPill: { marginTop:6, alignSelf:'center', flexDirection:'row', alignItems:'center', gap:4, paddingHorizontal:8, paddingVertical:2, borderRadius:10, backgroundColor:'#ECFDF5' },
  ownedPillText: { fontSize:10, color:'#065F46', fontWeight:'700' },

  primaryBtn: { backgroundColor: '#7C3AED', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 14, borderRadius: 12, marginBottom: 16, gap: 8 },
  primaryBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },

  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 18, shadowColor: '#000', shadowOpacity: 0.08, shadowRadius: 6, shadowOffset: { width: 0, height: 3 }, elevation: 2 },
  title: { marginLeft: 8, fontSize: 18, fontWeight: '700', color: '#111827' },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  rowCenter: { flexDirection: 'row', alignItems: 'center' },

  rowSplit: { flexDirection: 'row', justifyContent: 'space-between', gap: 16, marginTop: 8 },
  sub: { fontSize: 13, color: '#6B7280', marginBottom: 4 },
  prob: { fontSize: 26, fontWeight: '800' },

  progress: { height: 6, backgroundColor: '#E5E7EB', borderRadius: 3, overflow: 'hidden', marginTop: 8, width: '92%' },
  progressFill: { height: '100%', backgroundColor: '#10B981', borderRadius: 3 },

  confBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F3F4F6', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 14, gap: 6 },
  confText: { fontSize: 13, fontWeight: '700' },
  sentiment: { marginTop: 8, fontSize: 12, fontWeight: '700', color: '#374151' },
  sentimentSub: { fontSize: 12, color: '#6B7280', marginTop: 2, maxWidth: 180 },

  h6: { fontSize: 15, fontWeight: '700', color: '#111827', marginBottom: 6 },
  body: { fontSize: 14, color: '#6B7280', lineHeight: 20 },

  tagsWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  tag: { backgroundColor: '#F3F4F6', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
  tagKey: { fontSize: 11, fontWeight: '700', color: '#6B7280' },
  tagVal: { fontSize: 12, color: '#111827', marginTop: 2 },

  footer: { borderTopWidth: 1, borderTopColor: '#F3F4F6', marginTop: 12, paddingTop: 10, flexDirection: 'row', justifyContent: 'space-between' },
  meta: { fontSize: 12, color: '#6B7280' },

  empty: { alignItems: 'center', paddingVertical: 56, paddingHorizontal: 24 },
  emptyTitle: { marginTop: 10, fontSize: 18, fontWeight: '700', color: '#111827' },
  emptySub: { marginTop: 6, fontSize: 14, color: '#6B7280', textAlign: 'center' },

  notice: { flexDirection: 'row', backgroundColor: '#FFFBEB', borderWidth: 1, borderColor: '#FCD34D', borderRadius: 12, padding: 14, gap: 10, marginBottom: 20 },
  noticeText: { flex: 1, fontSize: 13, color: '#92400E' },

  // Skeleton dots
  skelDot: { backgroundColor: '#F3F4F6', borderRadius: 8 },
  badgeBigDay: { marginLeft: 8, flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, backgroundColor: '#F5F3FF' },
  badgeText: { fontSize: 10, fontWeight: '800', color: '#7C3AED' },

  // Error states
  errorContainer: { alignItems: 'center', paddingVertical: 24, paddingHorizontal: 16 },
  errorTitle: { fontSize: 16, fontWeight: '700', color: '#111827', marginTop: 8, marginBottom: 4 },
  errorText: { fontSize: 14, color: '#6B7280', textAlign: 'center', marginBottom: 16 },
  retryButton: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 16, paddingVertical: 8, backgroundColor: '#F3F4F6', borderRadius: 8 },
  retryText: { fontSize: 14, fontWeight: '600', color: '#007AFF' },
});

export default CryptoMLSignalsCard;