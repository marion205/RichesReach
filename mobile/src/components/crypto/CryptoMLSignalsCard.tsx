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
  GENERATE_ML_PREDICTION,
  GET_CRYPTO_RECOMMENDATIONS
} from '../../cryptoQueries';
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

/* ------------------------------- Recommendation Card ------------------------------ */

const RecommendationCard: React.FC<{ recommendation: any }> = ({ recommendation }) => {
  const getRecommendationColor = (rec: string) => {
    switch (rec?.toUpperCase()) {
      case 'BUY': return '#10B981';
      case 'SELL': return '#EF4444';
      case 'HOLD': return '#6B7280';
      default: return '#6B7280';
    }
  };

  const getRecommendationIcon = (rec: string) => {
    switch (rec?.toUpperCase()) {
      case 'BUY': return 'trending-up';
      case 'SELL': return 'trending-down';
      case 'HOLD': return 'pause';
      default: return 'help-circle';
    }
  };

  const getVolatilityColor = (tier: string) => {
    switch (tier?.toUpperCase()) {
      case 'LOW': return '#10B981';
      case 'MEDIUM': return '#F59E0B';
      case 'HIGH': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const rec = recommendation.recommendation || 'HOLD';
  const recColor = getRecommendationColor(rec);
  const recIcon = getRecommendationIcon(rec);
  const volColor = getVolatilityColor(recommendation.volatilityTier);

  return (
    <TouchableOpacity style={styles.recCard} activeOpacity={0.9}>
      <View style={styles.recHeader}>
        <View style={styles.recLeft}>
          <View style={styles.recSymbol}>
            <Text style={styles.recSymbolText}>{recommendation.symbol}</Text>
          </View>
          <View style={styles.recInfo}>
            <Text style={styles.recPrice}>${(recommendation.priceUsd || 0).toFixed(2)}</Text>
            <Text style={styles.recScore}>Score: {(recommendation.score || 0).toFixed(1)}</Text>
          </View>
        </View>
        
        <View style={styles.recRight}>
          <View style={[styles.recBadge, { backgroundColor: recColor + '15', borderColor: recColor + '40' }]}>
            <Icon name={recIcon} size={14} color={recColor} />
            <Text style={[styles.recBadgeText, { color: recColor }]}>{rec}</Text>
          </View>
          <View style={styles.recMeta}>
            <Text style={[styles.recVolatility, { color: volColor }]}>
              {recommendation.volatilityTier || 'UNKNOWN'}
            </Text>
            <Text style={styles.recConfidence}>
              {(recommendation.probability || 0).toFixed(0)}% confidence
            </Text>
          </View>
        </View>
      </View>
      
      {recommendation.rationale && (
        <Text style={styles.recRationale} numberOfLines={2}>
          {recommendation.rationale}
        </Text>
      )}
    </TouchableOpacity>
  );
};

/* ------------------------------- Component ------------------------------ */

const CryptoMLSignalsCard: React.FC<Props> = ({ initialSymbol = 'BTC', pollInterval }) => {
  const [selectedSymbol, setSelectedSymbol] = useState(initialSymbol);
  
  console.log('[CryptoMLSignalsCard] Initial symbol:', initialSymbol);
  console.log('[CryptoMLSignalsCard] Selected symbol:', selectedSymbol);
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
    fetchPolicy: 'cache-first', // Use cache first for better performance
    notifyOnNetworkStatusChange: false, // Reduce unnecessary re-renders
    errorPolicy: 'all',
    // Remove polling - let user manually refresh
    onCompleted: (data) => {
      console.log('[CryptoMLSignalsCard] Query completed with data:', data);
    },
    onError: (error) => {
      console.log('[CryptoMLSignalsCard] Query error:', error);
    }
  });

  const [generatePrediction] = useMutation(GENERATE_ML_PREDICTION, {
    errorPolicy: 'all',
  });

  // Get crypto recommendations - only when user explicitly requests them
  const [showRecommendations, setShowRecommendations] = useState(false);
  const { data: recommendationsData, loading: recommendationsLoading, refetch: refetchRecommendations } = useQuery(
    GET_CRYPTO_RECOMMENDATIONS,
    { 
      variables: { limit: 6, symbols: (finalSymbols || []).slice(0, 10) },
      skip: !showRecommendations, // Only fetch when user wants to see recommendations
      fetchPolicy: 'cache-first',
      errorPolicy: 'ignore' // Don't show errors for recommendations
    }
  );

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
  
  const finalSymbols = mergedSymbols.length > 0 ? mergedSymbols : top5Symbols;


  // quick qty lookup
  const qtyBySymbol: Record<string, number> = ownedRows.reduce((acc: any, h: any) => {
    const s = h?.cryptocurrency?.symbol;
    if (s) acc[s] = (acc[s] ?? 0) + parseFloat(h?.quantity ?? 0);
    return acc;
  }, {});

  // build a price lookup for auto-selection
  const symbolToPrice: Record<string, number> = Object.fromEntries(
    (currenciesData?.supportedCurrencies ?? []).map((c: any) => [c.symbol, 0]) // CryptocurrencyType doesn't have priceUsd
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
    
    console.log('[CryptoMLSignalsCard] Signal data:', s);
    console.log('[CryptoMLSignalsCard] Signal loading:', signalLoading);
    console.log('[CryptoMLSignalsCard] Signal error:', signalError);
    
    // Use real data from the backend
    if (s.predictionType) {
      console.log('[CryptoMLSignalsCard] Using real data for', selectedSymbol);
      return {
        predictionType: s.predictionType,
        probability: clamp01(s.probability),
        confidenceLevel: (s.confidenceLevel || 'LOW').toUpperCase(),
        sentiment: s.probability > 0.6 ? 'Bullish' : s.probability < 0.4 ? 'Bearish' : 'Neutral',
        sentimentDescription: s.probability > 0.6 ? 'Positive market sentiment detected.' : s.probability < 0.4 ? 'Negative market sentiment detected.' : 'Neutral market conditions.',
        featuresUsed: (() => {
          try {
            if (typeof s.featuresUsed === 'string') {
              return JSON.parse(s.featuresUsed);
            }
            return s.featuresUsed || {};
          } catch (e) {
            console.warn('[CryptoMLSignalsCard] Failed to parse featuresUsed:', e);
            return {};
          }
        })(),
        createdAt: s.createdAt || new Date().toISOString(),
        expiresAt: s.expiresAt || new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString(),
        explanation: s.explanation || 'Model output available. Awaiting more data for richer rationale.',
      };
    }
    
    console.log('[CryptoMLSignalsCard] No real data available for', selectedSymbol);
    // Return null if no real data available
    return null;
  }, [signalData, signalLoading, signalError, selectedSymbol]);

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
      console.log('[CryptoMLSignalsCard] Generate prediction response:', res.data);
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

  const symList = (finalSymbols && finalSymbols.length > 0) ? finalSymbols.slice(0, 12) : ['BTC', 'ETH', 'ADA', 'SOL', 'DOT'];

  const bigDay = useMemo(() => {
    // Showcase badge if probability of a move is high (tune threshold as you like)
    return signal && signal.probability >= 0.7;
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
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false} 
          style={styles.symbolRow}
          contentContainerStyle={{ paddingRight: 20 }}
        >
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
      ) : signal ? (
        <View style={styles.card}>
          <View style={styles.rowBetween}>
            <View style={styles.rowCenter}>
              {(() => {
                const tone = confidenceTone(signal?.confidenceLevel);
                return <>
                  <Icon name={tone.icon} size={22} color={tone.color} />
                  <Text style={styles.title}>{signal?.predictionType}</Text>
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
              <Text style={[styles.prob, { color: probTone(signal?.probability) }]}>{pctStr(signal?.probability)}</Text>
              {/* small progress bar */}
              <View style={styles.progress}>
                <View style={[styles.progressFill, { width: `${clamp01(signal?.probability) * 100}%` }]} />
              </View>
            </View>

            <View style={{ flex: 1, alignItems: 'flex-end' }}>
              <Text style={styles.sub}>Confidence</Text>
              {(() => {
                const tone = confidenceTone(signal?.confidenceLevel);
                return (
                  <View style={styles.confBadge}>
                    <Icon name={tone.icon} size={14} color={tone.color} />
                    <Text style={[styles.confText, { color: tone.color }]}>{signal?.confidenceLevel}</Text>
                  </View>
                );
              })()}
              <Text style={styles.sentiment}>{signal?.sentiment}</Text>
              <Text style={styles.sentimentSub} numberOfLines={2}>{signal?.sentimentDescription}</Text>
            </View>
          </View>

          {/* Explanation */}
          <View style={{ marginTop: 12 }}>
            <Text style={styles.h6}>AI Analysis</Text>
            <Text style={styles.body}>{signal?.explanation}</Text>
          </View>

          {/* Key factors */}
          {signal?.featuresUsed && Object.keys(signal.featuresUsed).length > 0 && (
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
            <Text style={styles.meta}>Generated: {signal?.createdAt ? new Date(signal.createdAt).toLocaleString() : 'N/A'}</Text>
            <Text style={styles.meta}>Expires: {signal?.expiresAt ? new Date(signal.expiresAt).toLocaleString() : 'N/A'}</Text>
          </View>
        </View>
      ) : (
        <View style={styles.card}>
          <View style={styles.rowBetween}>
            <View style={styles.rowCenter}>
              <Icon name="help-circle" size={22} color="#6B7280" />
              <Text style={styles.title}>No Signal Data</Text>
            </View>
            <TouchableOpacity onPress={onRefresh} activeOpacity={0.7} accessibilityLabel="Refresh">
              <Animated.View style={spinStyle}>
                <Icon name="refresh-cw" size={20} color="#007AFF" />
              </Animated.View>
            </TouchableOpacity>
          </View>
          
          <View style={styles.rowSplit}>
            <View style={{ flex: 1 }}>
              <Text style={styles.sub}>Status</Text>
              <Text style={[styles.prob, { color: '#6B7280' }]}>Waiting...</Text>
            </View>
            <View style={{ flex: 1, alignItems: 'flex-end' }}>
              <Text style={styles.sub}>Action</Text>
              <Text style={styles.sentiment}>Generate prediction above</Text>
            </View>
          </View>
          
          <View style={{ marginTop: 12 }}>
            <Text style={styles.h6}>Debug Info</Text>
            <Text style={styles.body}>
              Signal Loading: {signalLoading ? 'Yes' : 'No'}{'\n'}
              Has Signal Data: {signalData ? 'Yes' : 'No'}{'\n'}
              Error: {signalError?.message || 'None'}
            </Text>
          </View>
        </View>
      )}

      {/* Crypto Recommendations Section - On Demand */}
      <View style={styles.section}>
        <View style={styles.rowBetween}>
          <Text style={styles.sectionTitle}>AI Recommendations</Text>
          {!showRecommendations ? (
            <TouchableOpacity 
              onPress={() => setShowRecommendations(true)} 
              style={styles.loadRecommendationsBtn}
              activeOpacity={0.7}
            >
              <Icon name="zap" size={16} color="#007AFF" />
              <Text style={styles.loadRecommendationsText}>Load AI Picks</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity onPress={() => refetchRecommendations()} activeOpacity={0.7}>
              <Animated.View style={spinStyle}>
                <Icon name="refresh-cw" size={18} color="#007AFF" />
              </Animated.View>
            </TouchableOpacity>
          )}
        </View>
        
        {!showRecommendations ? (
          <View style={styles.card}>
            <View style={styles.empty}>
              <Icon name="zap" size={32} color="#6B7280" />
              <Text style={styles.emptyTitle}>AI-Powered Recommendations</Text>
              <Text style={styles.emptySub}>Tap "Load AI Picks" to get personalized crypto recommendations</Text>
            </View>
          </View>
        ) : recommendationsLoading ? (
          <View style={styles.card}>
            <View style={styles.rowCenter}>
              <ActivityIndicator size="small" color="#007AFF" />
              <Text style={[styles.body, { marginLeft: 8 }]}>Loading AI recommendations...</Text>
            </View>
          </View>
        ) : recommendationsData?.cryptoRecommendations?.length > 0 ? (
          <View style={styles.recommendationsList}>
            {recommendationsData.cryptoRecommendations.map((rec: any, index: number) => (
              <RecommendationCard key={`${rec.symbol}-${index}`} recommendation={rec} />
            ))}
          </View>
        ) : (
          <View style={styles.card}>
            <View style={styles.empty}>
              <Icon name="trending-up" size={32} color="#6B7280" />
              <Text style={styles.emptyTitle}>No Recommendations</Text>
              <Text style={styles.emptySub}>Check back later for AI-powered crypto recommendations</Text>
            </View>
          </View>
        )}
      </View>

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

  // Recommendations
  recommendationsList: { gap: 12 },
  recCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 4, shadowOffset: { width: 0, height: 2 }, elevation: 1 },
  recHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 },
  recLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  recSymbol: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  recSymbolText: { fontSize: 14, fontWeight: '800', color: '#1D4ED8' },
  recInfo: { flex: 1 },
  recPrice: { fontSize: 16, fontWeight: '700', color: '#111827' },
  recScore: { fontSize: 12, color: '#6B7280', marginTop: 2 },
  recRight: { alignItems: 'flex-end' },
  recBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12, borderWidth: 1, marginBottom: 6 },
  recBadgeText: { fontSize: 12, fontWeight: '700' },
  recMeta: { alignItems: 'flex-end' },
  recVolatility: { fontSize: 11, fontWeight: '600', marginBottom: 2 },
  recConfidence: { fontSize: 10, color: '#6B7280' },
  recRationale: { fontSize: 13, color: '#6B7280', lineHeight: 18, marginTop: 4 },

  // Load recommendations button
  loadRecommendationsBtn: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    gap: 6, 
    paddingHorizontal: 12, 
    paddingVertical: 8, 
    backgroundColor: '#EFF6FF', 
    borderRadius: 8, 
    borderWidth: 1, 
    borderColor: '#DBEAFE' 
  },
  loadRecommendationsText: { 
    fontSize: 14, 
    fontWeight: '600', 
    color: '#007AFF' 
  },

  // Error states
  errorContainer: { alignItems: 'center', paddingVertical: 24, paddingHorizontal: 16 },
  errorTitle: { fontSize: 16, fontWeight: '700', color: '#111827', marginTop: 8, marginBottom: 4 },
  errorText: { fontSize: 14, color: '#6B7280', textAlign: 'center', marginBottom: 16 },
  retryButton: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 16, paddingVertical: 8, backgroundColor: '#F3F4F6', borderRadius: 8 },
  retryText: { fontSize: 14, fontWeight: '600', color: '#007AFF' },
});

export default CryptoMLSignalsCard;