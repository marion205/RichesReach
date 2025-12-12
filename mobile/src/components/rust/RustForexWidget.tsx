import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  TextInput,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE, API_RUST_BASE } from '../../config/api';

const GET_RUST_FOREX_ANALYSIS = gql`
  query GetRustForexAnalysis($pair: String!) {
    rustForexAnalysis(pair: $pair) {
      pair
      bid
      ask
      spread
      pipValue
      volatility
      trend
      supportLevel
      resistanceLevel
      correlation24h
      timestamp
    }
  }
`;

interface RustForexWidgetProps {
  defaultPair?: string;
  size?: 'large' | 'compact';
}

type TrendLabel = 'Up' | 'Down' | 'Sideways';
type VolLabel = 'Calm' | 'Normal' | 'Wild';
type ExecLabel = 'Tight' | 'Normal' | 'Wide';

// Deterministic response type matching backend
interface AlphaOracleResponse {
  symbol?: string;
  global_mood?: string;
  regime_headline?: string;
  regime_action?: string;
  ml_label?: string;
  ml_confidence?: number;
  explanation?: string;
  alpha_score?: number;
  conviction?: string;
  one_sentence?: string;
  position_sizing?: {
    quantity?: number;
    stop_loss_pct?: number;
    dollar_risk?: number;
    target_notional?: number;
  };
  risk_guard?: {
    allow?: boolean;
    adjusted?: {
      quantity?: number;
      dollar_risk?: number;
      target_notional?: number;
    };
    reason?: string;
  };
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function safeNum(n: any): number | null {
  if (n === null || n === undefined) return null;
  const v = Number(n);
  return Number.isFinite(v) ? v : null;
}

function fmt5(n?: number | null) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  if (n === 0) return '—';
  return n.toFixed(5);
}

function fmt2(n?: number | null) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  if (n === 0) return '—';
  return n.toFixed(2);
}

function formatTimeAgo(timestamp: number): string {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

function trendToLabel(trend: string | null | undefined): TrendLabel {
  if (!trend) return 'Sideways';
  if (trend === 'BULLISH') return 'Up';
  if (trend === 'BEARISH') return 'Down';
  return 'Sideways';
}

function trendColor(label: TrendLabel) {
  if (label === 'Up') return '#10B981';
  if (label === 'Down') return '#EF4444';
  return '#6B7280';
}

function volatilityLabel(volFraction: number | null): { label: VolLabel; color: string } {
  const v = volFraction ?? 0;
  if (v < 0.006) return { label: 'Calm', color: '#10B981' };
  if (v < 0.015) return { label: 'Normal', color: '#F59E0B' };
  return { label: 'Wild', color: '#EF4444' };
}

function executionLabel(spread: number | null, mid: number | null): { label: ExecLabel; color: string; bps: number | null } {
  if (!spread || !mid || mid <= 0) return { label: 'Normal', color: '#6B7280', bps: null };
  const bps = (spread / mid) * 10000;
  if (bps <= 1.2) return { label: 'Tight', color: '#10B981', bps };
  if (bps <= 3.0) return { label: 'Normal', color: '#F59E0B', bps };
  return { label: 'Wide', color: '#EF4444', bps };
}

/** ---- Alpha Oracle (REST) ---- */
// Rust backend runs on port 3001, Python/Django on 8000
// Use centralized API config for proper device/IP handling
const getRustApiUrl = () => {
  // Check for explicit Rust API URL override
  const rustUrl = process.env.EXPO_PUBLIC_RUST_API_URL;
  if (rustUrl) return rustUrl;
  
  // Derive from API_BASE (replace port 8000 with 3001)
  const base = API_BASE || 'http://localhost:8000';
  return base.replace(':8000', ':3001').replace('localhost', '127.0.0.1');
};

const API_BASE_URL = getRustApiUrl();
const EQUITY_STORAGE_KEY = 'rr_equity';

type AlphaOracleState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; payload: AlphaOracleResponse; timestamp: number };

function convictionColor(conv: string) {
  const c = (conv || '').toUpperCase();
  if (c.includes('STRONG')) return '#10B981';
  if (c === 'BUY' || c.includes('WEAK BUY')) return '#22C55E';
  if (c.includes('NEUTRAL')) return '#6B7280';
  if (c.includes('DUMP') || c.includes('SELL')) return '#EF4444';
  return '#6B7280';
}

export default function RustForexWidget({ defaultPair = 'EURUSD', size = 'large' }: RustForexWidgetProps) {
  const isCompact = size === 'compact';

  const [pair, setPair] = useState(defaultPair);
  const [inputValue, setInputValue] = useState(defaultPair);

  const [showExplain, setShowExplain] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  // Alpha Oracle UX: collapsed panel + single call
  const [showOracle, setShowOracle] = useState(false);
  const [equity, setEquity] = useState('25000');
  const [openPositions, setOpenPositions] = useState('0');
  const [oracle, setOracle] = useState<AlphaOracleState>({ status: 'idle' });

  // Load persisted equity on mount
  useEffect(() => {
    AsyncStorage.getItem(EQUITY_STORAGE_KEY).then((stored) => {
      if (stored) {
        setEquity(stored);
      }
    });
  }, []);

  useEffect(() => {
    if (Platform.OS === 'android') {
      // @ts-ignore
      if (UIManager.setLayoutAnimationEnabledExperimental) {
        // @ts-ignore
        UIManager.setLayoutAnimationEnabledExperimental(true);
      }
    }
  }, []);

  const { data, loading, error, refetch } = useQuery(GET_RUST_FOREX_ANALYSIS, {
    variables: { pair },
    skip: !pair,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const handleSearch = () => {
    const trimmed = inputValue.trim().toUpperCase();
    if (!trimmed) return;
    setPair(trimmed);
    setOracle({ status: 'idle' }); // reset oracle when pair changes
    refetch({ pair: trimmed });
  };

  const analysis = data?.rustForexAnalysis;

  const computed = useMemo(() => {
    const bid = safeNum(analysis?.bid);
    const ask = safeNum(analysis?.ask);
    const spread = safeNum(analysis?.spread);
    const vol = safeNum(analysis?.volatility);
    const support = safeNum(analysis?.supportLevel);
    const resistance = safeNum(analysis?.resistanceLevel);
    const corr = safeNum(analysis?.correlation24h);

    const mid = bid && ask ? (bid + ask) / 2 : null;

    const tLabel = trendToLabel(analysis?.trend);
    const tColor = trendColor(tLabel);

    const v = volatilityLabel(vol);
    const ex = executionLabel(spread, mid);

    let confidence = 55;
    if (tLabel !== 'Sideways') confidence += 10;
    if (v.label === 'Calm') confidence += 10;
    if (v.label === 'Wild') confidence -= 10;
    if (ex.label === 'Tight') confidence += 10;
    if (ex.label === 'Wide') confidence -= 10;
    if (corr !== null && Math.abs(corr) > 0.8) confidence -= 6;
    confidence = clamp(confidence, 20, 92);

    const pairPretty = analysis?.pair ? `${analysis.pair.slice(0, 3)}/${analysis.pair.slice(3)}` : 'This pair';
    const trendPhrase = tLabel === 'Up' ? 'trending up' : tLabel === 'Down' ? 'trending down' : 'moving sideways';
    const volPhrase = v.label === 'Calm' ? 'calm' : v.label === 'Normal' ? 'steady' : 'wild';

    const headline = `${pairPretty} is ${volPhrase} and ${trendPhrase}.`;
    const subline = `Volatility ${v.label} • Trend ${tLabel} • Execution ${ex.label}`;

    const actionTitle = tLabel === 'Up' ? 'If you trade: wait for a pullback' : tLabel === 'Down' ? 'If you trade: wait for a bounce' : 'If you trade: stay patient';
    const actionNote =
      ex.label === 'Wide' ? 'Spreads are wide — avoid market orders.' :
      v.label === 'Wild' ? 'Volatility is high — size smaller.' :
      tLabel === 'Sideways' ? 'Sideways market — fewer clean setups.' :
      'Conditions look reasonable — stay disciplined.';

    const explainBullets = [
      tLabel === 'Up'
        ? 'Price has been pushing higher more than it pulls back.'
        : tLabel === 'Down'
          ? 'Price has been pushing lower more than it bounces.'
          : 'Price is chopping — both sides are getting tested.',
      v.label === 'Calm'
        ? 'Moves are smaller and smoother today.'
        : v.label === 'Wild'
          ? 'Moves are bigger and faster today.'
          : 'Moves are normal for this pair.',
      ex.label === 'Tight'
        ? 'Execution cost is low (tight spread).'
        : ex.label === 'Wide'
          ? 'Execution cost is higher (wide spread).'
          : 'Execution cost is normal.',
    ];

    return {
      bid,
      ask,
      mid,
      spread,
      vol,
      support,
      resistance,
      corr,
      tLabel,
      tColor,
      vLabel: v.label,
      vColor: v.color,
      exLabel: ex.label,
      exColor: ex.color,
      exBps: ex.bps,
      confidence,
      headline,
      subline,
      actionTitle,
      actionNote,
      explainBullets,
      pairPretty,
    };
  }, [analysis]);

  async function askAlphaOracle() {
    if (!API_RUST_BASE) {
      setOracle({ status: 'error', message: 'Missing API_RUST_BASE URL' });
      return;
    }

    const eq = safeNum(equity);
    const openCount = Math.max(0, parseInt(openPositions || '0', 10));

    if (!eq || eq <= 0) {
      setOracle({ status: 'error', message: 'Equity must be a positive number.' });
      return;
    }

    // Get price from analysis - ensure we have a valid price
    const price = computed.mid ?? computed.bid ?? computed.ask;
    if (!price || price <= 0) {
      setOracle({ status: 'error', message: 'No valid price data available. Please wait for analysis to complete.' });
      return;
    }

    // Use price for entry_price
    const entry = price;

    // Persist equity
    AsyncStorage.setItem(EQUITY_STORAGE_KEY, equity);

    setOracle({ status: 'loading' });

    try {
      // Build features from current analysis (use defaults if missing)
      // For forex pairs, use "price" instead of "price_usd"
      const features: Record<string, number> = {};
      features.price = price; // Forex uses "price", not "price_usd"
      if (computed.vol !== null && computed.vol > 0) {
        features.volatility = computed.vol;
      } else {
        features.volatility = 0.01; // Default 1% volatility
      }

      const requestBody: any = {
        symbol: pair,
        features,
        equity: eq,
        entry_price: entry,
      };

      // Backend expects open_positions as array of OpenRiskPosition, but we'll send count for now
      // In production, fetch actual positions from portfolio
      if (openCount > 0) {
        // For now, send empty array - backend will handle it
        requestBody.open_positions = [];
      }

      const url = `${API_RUST_BASE}/v1/alpha/signal`;
      console.log('[RustForexWidget] Calling Alpha Oracle:', url);
      console.log('[RustForexWidget] Request body:', JSON.stringify(requestBody, null, 2));
      
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });
      
      console.log('[RustForexWidget] Response status:', res.status);
      console.log('[RustForexWidget] Response URL:', res.url);

      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg =
          (typeof json?.error === 'string' && json.error) ||
          (typeof json?.message === 'string' && json.message) ||
          `Request failed (${res.status})`;
        setOracle({ status: 'error', message: msg });
        return;
      }

      setOracle({ status: 'ready', payload: json as AlphaOracleResponse, timestamp: Date.now() });
    } catch (e: any) {
      setOracle({ status: 'error', message: e?.message || 'Network error' });
    }
  }

  // Loading/Error/Empty
  if (loading && !analysis) {
    return (
      <View style={[styles.container, isCompact && styles.containerCompact]}>
        <View style={styles.skeletonRow}>
          <ActivityIndicator size="small" color="#0B0B0F" />
          <Text style={styles.skeletonText}>Updating…</Text>
        </View>
      </View>
    );
  }

  if (error && !analysis) {
    return (
      <View style={[styles.container, isCompact && styles.containerCompact]}>
        <View style={styles.inlineHeader}>
          <Icon name="alert-triangle" size={16} color="#EF4444" />
          <Text style={styles.inlineHeaderText}>Can't load forex data</Text>
        </View>
        {!isCompact && <Text style={styles.muted}>Check your connection and try again.</Text>}
      </View>
    );
  }

  if (!analysis) {
    return (
      <View style={[styles.container, isCompact && styles.containerCompact]}>
        <Text style={styles.muted}>No data yet.</Text>
      </View>
    );
  }

  // Compact mode
  if (isCompact) {
    return (
      <View style={styles.compactWrap}>
        <View style={styles.compactTop}>
          <View style={[styles.dot, { backgroundColor: computed.tColor }]} />
          <Text style={styles.compactPair}>{computed.pairPretty}</Text>
        </View>

        <View style={styles.compactPrices}>
          <View style={styles.compactPriceItem}>
            <Text style={styles.compactLabel}>Bid</Text>
            <Text style={styles.compactValue}>{fmt5(computed.bid)}</Text>
          </View>
          <View style={styles.compactPriceItem}>
            <Text style={styles.compactLabel}>Ask</Text>
            <Text style={styles.compactValue}>{fmt5(computed.ask)}</Text>
          </View>
        </View>

        <View style={styles.compactFooter}>
          <Text style={styles.compactFooterText}>
            {computed.vLabel} • {computed.exLabel}
          </Text>
        </View>
      </View>
    );
  }

  // Large mode - deterministic parsing from root-level response
  const resp = oracle.status === 'ready' ? oracle.payload : null;

  const alphaScore = resp?.alpha_score ?? null;
  const conviction = resp?.conviction ?? '';
  const oneSentence = resp?.one_sentence ?? '';
  const regimeHeadline = resp?.regime_headline ?? '';
  const regimeAction = resp?.regime_action ?? '';
  const globalMood = resp?.global_mood ?? '';
  const mlExplanation = resp?.explanation ?? '';
  const mlConfidence = resp?.ml_confidence ?? null;

  const qty = resp?.position_sizing?.quantity ?? null;
  const stopLossPct = resp?.position_sizing?.stop_loss_pct ?? null;
  const riskUsd = resp?.position_sizing?.dollar_risk ?? null;
  const targetNotional = resp?.position_sizing?.target_notional ?? null;

  const guardAllow = resp?.risk_guard?.allow ?? null;
  const guardAdjusted = resp?.risk_guard?.adjusted ?? null;
  const guardReason = resp?.risk_guard?.reason ?? '';

  const alphaColor = convictionColor(conviction);
  const alphaBarPct = alphaScore !== null ? clamp((alphaScore / 10) * 100, 0, 100) : 0;

  // Jobs-grade "Why" section: 3 bullets (Macro, Micro, Risk)
  const whyBullets: string[] = [];
  if (regimeHeadline || globalMood) {
    whyBullets.push(`Macro: ${regimeHeadline || `${globalMood} market conditions`}`);
  }
  if (mlExplanation || mlConfidence !== null) {
    const microText = mlExplanation || `ML confidence: ${((mlConfidence ?? 0) * 100).toFixed(0)}%`;
    whyBullets.push(`Micro: ${microText}`);
  }
  if (guardAllow === true) {
    whyBullets.push('Risk: Approved full size');
  } else if (guardAllow === false && guardReason) {
    whyBullets.push(`Risk: ${guardReason}`);
  } else if (riskUsd !== null) {
    whyBullets.push(`Risk: $${riskUsd.toFixed(2)} at risk`);
  }

  // Professional messaging for neutral/dump states
  const isNeutralOrDump = conviction.toUpperCase().includes('NEUTRAL') || conviction.toUpperCase().includes('DUMP');
  const passMessage = isNeutralOrDump ? 'No clean edge right now. Stay patient.' : null;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.topHeader}>
        <View style={styles.topHeaderLeft}>
          <View style={[styles.dot, { backgroundColor: computed.tColor }]} />
          <Text style={styles.topTitle}>Today's Read</Text>
        </View>

        <TouchableOpacity
          onPress={() => refetch({ pair })}
          style={styles.refreshBtn}
          activeOpacity={0.8}
        >
          <Icon name="refresh-ccw" size={16} color="#0B0B0F" />
        </TouchableOpacity>
      </View>

      <Text style={styles.heroLine}>{computed.headline}</Text>
      <Text style={styles.heroSubline}>{computed.subline}</Text>

      {/* Search */}
      <View style={styles.searchContainer}>
        <Text style={styles.searchLabel}>Currency pair</Text>
        <View style={styles.searchRow}>
          <TextInput
            style={styles.searchInput}
            placeholder="EURUSD"
            value={inputValue}
            onChangeText={setInputValue}
            autoCapitalize="characters"
            autoCorrect={false}
            returnKeyType="search"
            onSubmitEditing={handleSearch}
          />
          <TouchableOpacity style={styles.searchButton} onPress={handleSearch} activeOpacity={0.85}>
            <Icon name="search" size={16} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Prices */}
      <View style={styles.prices}>
        <View style={styles.priceCard}>
          <Text style={styles.priceLabel}>Bid</Text>
          <Text style={styles.priceValue}>{fmt5(computed.bid)}</Text>
        </View>
        <View style={styles.priceCard}>
          <Text style={styles.priceLabel}>Ask</Text>
          <Text style={styles.priceValue}>{fmt5(computed.ask)}</Text>
        </View>
        <View style={styles.priceCard}>
          <Text style={styles.priceLabel}>Spread</Text>
          <Text style={styles.priceValue}>{computed.spread !== null ? computed.spread.toFixed(5) : '—'}</Text>
        </View>
      </View>

      {/* 3 traffic lights */}
      <View style={styles.lightsRow}>
        <View style={styles.lightCard}>
          <Text style={styles.lightTitle}>Trend</Text>
          <View style={[styles.pill, { backgroundColor: computed.tColor + '22' }]}>
            <Text 
              style={[styles.pillText, { color: computed.tColor }]}
              numberOfLines={1}
              adjustsFontSizeToFit
            >
              {computed.tLabel}
            </Text>
          </View>
        </View>

        <View style={styles.lightCard}>
          <Text style={styles.lightTitle}>Volatility</Text>
          <View style={[styles.pill, { backgroundColor: computed.vColor + '22' }]}>
            <Text 
              style={[styles.pillText, { color: computed.vColor }]}
              numberOfLines={1}
              adjustsFontSizeToFit
            >
              {computed.vLabel}
            </Text>
          </View>
        </View>

        <View style={styles.lightCard}>
          <Text style={styles.lightTitle}>Execution</Text>
          <View style={[styles.pill, { backgroundColor: computed.exColor + '22' }]}>
            <Text 
              style={[styles.pillText, { color: computed.exColor }]}
              numberOfLines={1}
              adjustsFontSizeToFit
            >
              {computed.exLabel}
            </Text>
          </View>
        </View>
      </View>

      {/* Alpha Oracle (collapsed by default) */}
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => {
          LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
          setShowOracle(v => !v);
        }}
        style={styles.oracleToggle}
      >
        <View style={styles.oracleToggleLeft}>
          <Icon name="zap" size={16} color="#0B0B0F" />
          <Text style={styles.oracleToggleText}>Alpha Oracle</Text>
          <View style={styles.oracleMiniBadge}>
            <Text style={styles.oracleMiniBadgeText}>1 tap</Text>
          </View>
        </View>
        <Icon name={showOracle ? 'chevron-up' : 'chevron-down'} size={18} color="#0B0B0F" />
      </TouchableOpacity>

      {showOracle && (
        <View style={styles.oracleCard}>
          <Text style={styles.oracleHeadline}>
            Turn the advanced system into one clear move.
          </Text>

          <View style={styles.oracleInputsRow}>
            <View style={styles.oracleInputWrap}>
              <Text style={styles.oracleLabel}>Equity</Text>
              <View style={styles.oracleInputRow}>
                <Text style={styles.oraclePrefix}>$</Text>
                <TextInput
                  value={equity}
                  onChangeText={setEquity}
                  keyboardType="numeric"
                  style={styles.oracleInput}
                  placeholder="25000"
                />
              </View>
            </View>

            <View style={styles.oracleInputWrap}>
              <Text style={styles.oracleLabel}>Open pos</Text>
              <TextInput
                value={openPositions}
                onChangeText={setOpenPositions}
                keyboardType="numeric"
                style={styles.oracleInputSolo}
                placeholder="0"
              />
            </View>
          </View>

          <TouchableOpacity
            onPress={askAlphaOracle}
            activeOpacity={0.88}
            style={styles.oracleBtn}
            disabled={oracle.status === 'loading'}
          >
            {oracle.status === 'loading' ? (
              <>
                <ActivityIndicator size="small" color="#FFFFFF" />
                <Text style={[styles.oracleBtnText, { marginLeft: 10 }]}>Asking…</Text>
              </>
            ) : (
              <>
                <Icon name="zap" size={16} color="#FFFFFF" />
                <Text style={styles.oracleBtnText}>Ask Alpha Oracle</Text>
              </>
            )}
          </TouchableOpacity>

          {oracle.status === 'error' && (
            <View style={styles.oracleError}>
              <Icon name="alert-circle" size={16} color="#EF4444" />
              <Text style={styles.oracleErrorText}>{oracle.message}</Text>
              <TouchableOpacity
                onPress={askAlphaOracle}
                style={styles.oracleRetryBtn}
                activeOpacity={0.8}
              >
                <Text style={styles.oracleRetryText}>Tap to retry</Text>
              </TouchableOpacity>
            </View>
          )}

          {oracle.status === 'ready' && (
            <View style={styles.oracleResult}>
              {/* Timestamp */}
              <Text style={styles.oracleTimestamp}>
                Updated {formatTimeAgo(oracle.timestamp)}
              </Text>

              {/* One sentence */}
              <Text style={styles.oracleOneSentence}>
                {oneSentence || 'Oracle response received.'}
              </Text>

              {/* Pass message for neutral/dump */}
              {passMessage && (
                <View style={styles.oraclePassMessage}>
                  <Text style={styles.oraclePassText}>{passMessage}</Text>
                </View>
              )}

              {/* Score + conviction */}
              <View style={styles.oracleScoreRow}>
                <View style={styles.oracleScoreLeft}>
                  <Text style={styles.oracleScoreLabel}>Alpha score</Text>
                  <Text style={styles.oracleScoreValue}>
                    {alphaScore !== null ? alphaScore.toFixed(1) : '—'}
                    <Text style={styles.oracleScoreOutOf}> / 10</Text>
                  </Text>
                </View>

                <View style={[styles.oracleConvictionPill, { backgroundColor: alphaColor + '22' }]}>
                  <Text style={[styles.oracleConvictionText, { color: alphaColor }]}>
                    {(conviction || 'NEUTRAL').toUpperCase()}
                  </Text>
                </View>
              </View>

              <View style={styles.oracleBarTrack}>
                <View style={[styles.oracleBarFill, { width: `${alphaBarPct}%`, backgroundColor: alphaColor }]} />
              </View>

              {/* Sizing + guard */}
              {!isNeutralOrDump && (
                <>
                  <View style={styles.oracleGrid}>
                    <View style={styles.oracleCell}>
                      <Text style={styles.oracleCellLabel}>Qty</Text>
                      <Text style={styles.oracleCellValue}>{qty !== null ? qty.toFixed(4) : '—'}</Text>
                    </View>
                    <View style={styles.oracleCell}>
                      <Text style={styles.oracleCellLabel}>Stop</Text>
                      <Text style={styles.oracleCellValue}>
                        {stopLossPct !== null && computed.mid ? `${(computed.mid * (1 - stopLossPct)).toFixed(5)}` : '—'}
                      </Text>
                    </View>
                    <View style={styles.oracleCell}>
                      <Text style={styles.oracleCellLabel}>Risk</Text>
                      <Text style={styles.oracleCellValue}>{riskUsd !== null ? `$${riskUsd.toFixed(2)}` : '—'}</Text>
                    </View>
                  </View>

                  {targetNotional !== null && (
                    <View style={styles.oracleNotional}>
                      <Text style={styles.oracleNotionalLabel}>Target size</Text>
                      <Text style={styles.oracleNotionalValue}>${targetNotional.toFixed(2)}</Text>
                    </View>
                  )}

                  <View style={styles.oracleGuardRow}>
                    <View style={[styles.oracleGuardDot, { backgroundColor: guardAllow === true ? '#10B981' : guardAllow === false ? '#EF4444' : '#6B7280' }]} />
                    <Text style={styles.oracleGuardText}>
                      {guardAllow === true ? 'RiskGuard: approved' : guardAllow === false ? 'RiskGuard: scaled/blocked' : 'RiskGuard: —'}
                    </Text>
                  </View>

                  {guardAllow === false && guardReason && (
                    <Text style={styles.oracleGuardReason}>
                      RiskGuard reduced size to protect your account.
                    </Text>
                  )}
                </>
              )}

              {/* Why section - Jobs-grade 3 bullets */}
              {whyBullets.length > 0 && (
                <View style={styles.oracleWhy}>
                  <Text style={styles.oracleWhyTitle}>Why?</Text>
                  {whyBullets.map((bullet, idx) => (
                    <View key={idx} style={styles.oracleWhyItem}>
                      <View style={styles.oracleWhyDot} />
                      <Text style={styles.oracleWhyText}>{bullet}</Text>
                    </View>
                  ))}
                </View>
              )}

              <Text style={styles.disclaimer}>
                Educational insights — not financial advice.
              </Text>
            </View>
          )}
        </View>
      )}

      {/* Explain drawer */}
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => {
          LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
          setShowExplain(v => !v);
        }}
        style={styles.explainToggle}
      >
        <View style={styles.explainToggleLeft}>
          <Icon name="info" size={16} color="#0B0B0F" />
          <Text style={styles.explainToggleText}>Explain it simply</Text>
        </View>
        <Icon name={showExplain ? 'chevron-up' : 'chevron-down'} size={18} color="#0B0B0F" />
      </TouchableOpacity>

      {showExplain && (
        <View style={styles.explainCard}>
          {computed.explainBullets.map((b, idx) => (
            <View key={`${idx}-${b}`} style={styles.bulletRow}>
              <View style={styles.bulletDot} />
              <Text style={styles.bulletText}>{b}</Text>
            </View>
          ))}

          <TouchableOpacity
            onPress={() => {
              LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
              setShowDetails(v => !v);
            }}
            style={styles.detailsToggle}
            activeOpacity={0.85}
          >
            <Text style={styles.detailsToggleText}>{showDetails ? 'Hide details' : 'Show details'}</Text>
            <Icon name={showDetails ? 'minus' : 'plus'} size={16} color="#111827" />
          </TouchableOpacity>

          {showDetails && (
            <View style={styles.detailsBox}>
              <Text style={styles.detailLine}><Text style={styles.detailKey}>Pair: </Text>{computed.pairPretty}</Text>
              <Text style={styles.detailLine}><Text style={styles.detailKey}>Trend raw: </Text>{analysis.trend ?? '—'}</Text>
              <Text style={styles.detailLine}><Text style={styles.detailKey}>Volatility raw: </Text>{computed.vol !== null ? `${(computed.vol * 100).toFixed(3)}%` : '—'}</Text>
              <Text style={styles.detailLine}><Text style={styles.detailKey}>Support: </Text>{computed.support !== null ? computed.support.toFixed(5) : '—'}</Text>
              <Text style={styles.detailLine}><Text style={styles.detailKey}>Resistance: </Text>{computed.resistance !== null ? computed.resistance.toFixed(5) : '—'}</Text>
              <Text style={styles.detailLine}><Text style={styles.detailKey}>Timestamp: </Text>{analysis.timestamp ?? '—'}</Text>
            </View>
          )}

          <Text style={styles.disclaimer}>Educational insights — not financial advice.</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F1F1F4',
  },
  containerCompact: {
    padding: 0,
    borderWidth: 0,
    backgroundColor: 'transparent',
  },

  skeletonRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10 },
  skeletonText: { marginLeft: 10, color: '#52525B', fontWeight: '600' },

  inlineHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  inlineHeaderText: { fontSize: 14, fontWeight: '800', color: '#111827' },
  muted: { marginTop: 6, color: '#71717A', fontWeight: '600' },

  compactWrap: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 10,
    borderWidth: 1,
    borderColor: '#F2F2F6',
  },
  compactTop: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  compactPair: { fontSize: 13, fontWeight: '900', color: '#0B0B0F' },
  compactPrices: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  compactPriceItem: {
    flex: 1,
    backgroundColor: '#FAFAFB',
    borderRadius: 12,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: '#F1F1F4',
  },
  compactLabel: { fontSize: 10, color: '#71717A', fontWeight: '700' },
  compactValue: { marginTop: 2, fontSize: 13, fontWeight: '900', color: '#0B0B0F' },
  compactFooter: { marginTop: 8, alignItems: 'center' },
  compactFooterText: { fontSize: 11, color: '#71717A', fontWeight: '700' },

  topHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  topHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  topTitle: { fontSize: 14, fontWeight: '900', color: '#0B0B0F' },
  refreshBtn: {
    width: 36, height: 36, borderRadius: 12, backgroundColor: '#FAFAFB',
    borderWidth: 1, borderColor: '#F1F1F4', alignItems: 'center', justifyContent: 'center',
  },

  dot: { width: 10, height: 10, borderRadius: 5 },

  heroLine: { marginTop: 10, fontSize: 18, fontWeight: '900', color: '#0B0B0F', letterSpacing: -0.2 },
  heroSubline: { marginTop: 6, fontSize: 13, color: '#71717A', fontWeight: '700' },

  searchContainer: { marginTop: 14 },
  searchLabel: { fontSize: 12, color: '#71717A', fontWeight: '700', marginBottom: 8 },
  searchRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  searchInput: {
    flex: 1, height: 44, backgroundColor: '#FFFFFF',
    borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 14,
    paddingHorizontal: 14, fontSize: 14, fontWeight: '700', color: '#0B0B0F',
  },
  searchButton: { width: 44, height: 44, backgroundColor: '#0B0B0F', borderRadius: 14, justifyContent: 'center', alignItems: 'center' },

  prices: { marginTop: 14, flexDirection: 'row', gap: 10 },
  priceCard: {
    flex: 1, backgroundColor: '#FAFAFB', borderRadius: 14,
    paddingVertical: 12, paddingHorizontal: 12, borderWidth: 1, borderColor: '#F1F1F4',
  },
  priceLabel: { fontSize: 11, color: '#71717A', fontWeight: '800' },
  priceValue: { marginTop: 5, fontSize: 15, fontWeight: '900', color: '#0B0B0F' },

  lightsRow: { marginTop: 12, flexDirection: 'row', gap: 10 },
  lightCard: { flex: 1, backgroundColor: '#FFFFFF', borderRadius: 14, padding: 12, borderWidth: 1, borderColor: '#F1F1F4' },
  lightTitle: { fontSize: 11, color: '#71717A', fontWeight: '900', marginBottom: 8 },
  pill: { 
    alignSelf: 'flex-start', 
    paddingHorizontal: 12, 
    paddingVertical: 6, 
    borderRadius: 999,
    minWidth: 70,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pillText: { 
    fontSize: 13, 
    fontWeight: '900',
    textAlign: 'center',
  },

  // Alpha Oracle
  oracleToggle: {
    marginTop: 12,
    backgroundColor: '#FAFAFB',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#F1F1F4',
    paddingVertical: 12,
    paddingHorizontal: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  oracleToggleLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  oracleToggleText: { fontSize: 13, fontWeight: '900', color: '#0B0B0F' },
  oracleMiniBadge: {
    marginLeft: 6,
    backgroundColor: '#0B0B0F',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
  },
  oracleMiniBadgeText: { color: '#FFFFFF', fontSize: 10, fontWeight: '900' },

  oracleCard: {
    marginTop: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: '#F1F1F4',
  },
  oracleHeadline: { fontSize: 12, color: '#52525B', fontWeight: '800', lineHeight: 18 },

  oracleInputsRow: { marginTop: 12, flexDirection: 'row', gap: 10 },
  oracleInputWrap: { flex: 1 },
  oracleLabel: { fontSize: 11, color: '#71717A', fontWeight: '900', marginBottom: 6 },
  oracleInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    borderRadius: 14,
    paddingHorizontal: 12,
    height: 44,
    gap: 8,
  },
  oraclePrefix: { fontSize: 13, fontWeight: '900', color: '#0B0B0F' },
  oracleInput: { flex: 1, height: 44, fontSize: 13, fontWeight: '900', color: '#0B0B0F' },
  oracleInputSolo: {
    height: 44,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    borderRadius: 14,
    paddingHorizontal: 12,
    fontSize: 13,
    fontWeight: '900',
    color: '#0B0B0F',
  },

  oracleBtn: {
    marginTop: 12,
    height: 50,
    borderRadius: 14,
    backgroundColor: '#0B0B0F',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  oracleBtnDisabled: {
    backgroundColor: '#9CA3AF',
    opacity: 0.8,
  },
  oracleBtnText: { marginLeft: 10, color: '#FFFFFF', fontWeight: '900', fontSize: 14 },
  oracleBtnTextDisabled: { color: '#FFFFFF' },

  oracleError: {
    marginTop: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FEE2E2',
    padding: 10,
    borderRadius: 14,
  },
  oracleErrorText: { flex: 1, color: '#B91C1C', fontWeight: '800', fontSize: 12 },
  oracleRetryBtn: {
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#EF4444',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  oracleRetryText: { color: '#FFFFFF', fontWeight: '900', fontSize: 11 },

  oracleResult: { marginTop: 12 },
  oracleTimestamp: { fontSize: 10, color: '#A1A1AA', fontWeight: '700', marginBottom: 8 },
  oracleOneSentence: { fontSize: 14, fontWeight: '900', color: '#0B0B0F', lineHeight: 20 },
  oraclePassMessage: {
    marginTop: 10,
    padding: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  oraclePassText: { fontSize: 13, color: '#52525B', fontWeight: '700', lineHeight: 18 },

  oracleScoreRow: { marginTop: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 },
  oracleScoreLeft: {},
  oracleScoreLabel: { fontSize: 11, color: '#71717A', fontWeight: '900' },
  oracleScoreValue: { marginTop: 4, fontSize: 18, fontWeight: '900', color: '#0B0B0F' },
  oracleScoreOutOf: { fontSize: 12, fontWeight: '900', color: '#71717A' },

  oracleConvictionPill: { paddingHorizontal: 10, paddingVertical: 7, borderRadius: 999 },
  oracleConvictionText: { fontSize: 11, fontWeight: '900', letterSpacing: 0.5 },

  oracleBarTrack: {
    marginTop: 10,
    height: 10,
    backgroundColor: '#F1F1F4',
    borderRadius: 999,
    overflow: 'hidden',
  },
  oracleBarFill: {
    height: 10,
    borderRadius: 999,
  },

  oracleGrid: { marginTop: 12, flexDirection: 'row', gap: 10 },
  oracleCell: {
    flex: 1,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    borderRadius: 14,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  oracleCellLabel: { fontSize: 10, color: '#71717A', fontWeight: '900' },
  oracleCellValue: { marginTop: 4, fontSize: 12, color: '#0B0B0F', fontWeight: '900' },

  oracleNotional: {
    marginTop: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: '#F8F9FF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8FF',
  },
  oracleNotionalLabel: { fontSize: 11, color: '#69707F', fontWeight: '900' },
  oracleNotionalValue: { marginTop: 4, fontSize: 14, fontWeight: '900', color: '#1F1F1F' },

  oracleGuardRow: { marginTop: 12, flexDirection: 'row', alignItems: 'center', gap: 8 },
  oracleGuardDot: { width: 10, height: 10, borderRadius: 5 },
  oracleGuardText: { color: '#52525B', fontWeight: '800', fontSize: 12 },
  oracleGuardReason: { marginTop: 6, color: '#71717A', fontWeight: '800', fontSize: 12, lineHeight: 18 },

  oracleWhy: {
    marginTop: 14,
    padding: 12,
    backgroundColor: '#FAFAFB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#F1F1F4',
  },
  oracleWhyTitle: { fontSize: 12, fontWeight: '900', color: '#0B0B0F', marginBottom: 8 },
  oracleWhyItem: { flexDirection: 'row', gap: 10, marginBottom: 8, alignItems: 'flex-start' },
  oracleWhyDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#0B0B0F', marginTop: 6 },
  oracleWhyText: { flex: 1, fontSize: 12, color: '#52525B', fontWeight: '700', lineHeight: 18 },

  // Explain drawer
  explainToggle: {
    marginTop: 12,
    backgroundColor: '#FAFAFB',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#F1F1F4',
    paddingVertical: 12,
    paddingHorizontal: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  explainToggleLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  explainToggleText: { fontSize: 13, fontWeight: '900', color: '#0B0B0F' },
  explainCard: {
    marginTop: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: '#F1F1F4',
  },
  bulletRow: { flexDirection: 'row', gap: 10, marginBottom: 10, alignItems: 'flex-start' },
  bulletDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#0B0B0F', marginTop: 6 },
  bulletText: { flex: 1, fontSize: 12, color: '#52525B', fontWeight: '700', lineHeight: 18 },

  detailsToggle: {
    marginTop: 2,
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderRadius: 12,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailsToggleText: { fontSize: 12, fontWeight: '900', color: '#111827' },
  detailsBox: { marginTop: 10, backgroundColor: '#FFFFFF', borderRadius: 12, borderWidth: 1, borderColor: '#F1F1F4', padding: 12 },
  detailLine: { fontSize: 12, color: '#52525B', fontWeight: '700', marginBottom: 6 },
  detailKey: { color: '#0B0B0F', fontWeight: '900' },

  disclaimer: { marginTop: 12, fontSize: 11, color: '#A1A1AA', fontWeight: '700', textAlign: 'center' },
});
