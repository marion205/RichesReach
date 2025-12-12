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

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function fmt5(n?: number | null) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  if (n === 0) return '—'; // Show dash for zero values (likely no data)
  return n.toFixed(5);
}

function fmt2(n?: number | null) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return n.toFixed(2);
}

function safeNum(n: any): number | null {
  if (n === null || n === undefined) return null;
  const v = Number(n);
  return Number.isFinite(v) ? v : null;
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
  // volatility seems like fraction (e.g., 0.01 = 1%); handle unknowns safely.
  const v = volFraction ?? 0;
  // Conservative thresholds (can tune later with ATR once you expose it)
  if (v < 0.006) return { label: 'Calm', color: '#10B981' };
  if (v < 0.015) return { label: 'Normal', color: '#F59E0B' };
  return { label: 'Wild', color: '#EF4444' };
}

function executionLabel(spread: number | null, mid: number | null): { label: ExecLabel; color: string; bps: number | null } {
  if (!spread || !mid || mid <= 0) return { label: 'Normal', color: '#6B7280', bps: null };
  // bps = (spread / mid) * 10000
  const bps = (spread / mid) * 10000;
  // Conservative thresholds (tight for major FX is very low)
  if (bps <= 1.2) return { label: 'Tight', color: '#10B981', bps };
  if (bps <= 3.0) return { label: 'Normal', color: '#F59E0B', bps };
  return { label: 'Wide', color: '#EF4444', bps };
}

export default function RustForexWidget({ defaultPair = 'EURUSD', size = 'large' }: RustForexWidgetProps) {
  const isCompact = size === 'compact';

  const [pair, setPair] = useState(defaultPair);
  const [inputValue, setInputValue] = useState(defaultPair);

  const [showExplain, setShowExplain] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (Platform.OS === 'android') {
      // Enable LayoutAnimation on Android
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

    // Confidence heuristic (simple + stable):
    // - clearer trend helps
    // - calm/normal volatility helps
    // - tight spreads helps
    // - correlation can reduce confidence if extreme (optional)
    let confidence = 55;
    if (tLabel !== 'Sideways') confidence += 10;
    if (v.label === 'Calm') confidence += 10;
    if (v.label === 'Wild') confidence -= 10;
    if (ex.label === 'Tight') confidence += 10;
    if (ex.label === 'Wide') confidence -= 10;
    if (corr !== null && Math.abs(corr) > 0.8) confidence -= 6;

    confidence = clamp(confidence, 20, 92);

    // "Next best move" zones:
    // Use support/resistance when available, otherwise fallback to mid-based ranges.
    const price = mid ?? bid ?? ask ?? null;

    // A small adaptive "buffer" using volatility fraction if present.
    // bufferPct is small; it just creates a range feel without pretending to be precise.
    const bufferPct = clamp((vol ?? 0.01) * 0.35, 0.0004, 0.004); // 0.04% .. 0.40%
    const buffer = price ? price * bufferPct : null;

    const entry =
      support && resistance
        ? tLabel === 'Up'
          ? { low: support - (buffer ?? 0), high: support + (buffer ?? 0) }
          : tLabel === 'Down'
            ? { low: resistance - (buffer ?? 0), high: resistance + (buffer ?? 0) }
            : { low: (price ?? 0) - (buffer ?? 0), high: (price ?? 0) + (buffer ?? 0) }
        : price && buffer
          ? { low: price - buffer, high: price + buffer }
          : null;

    const target =
      support && resistance
        ? tLabel === 'Up'
          ? { low: resistance - (buffer ?? 0), high: resistance + (buffer ?? 0) }
          : tLabel === 'Down'
            ? { low: support - (buffer ?? 0), high: support + (buffer ?? 0) }
            : null
        : null;

    const stop =
      entry && buffer
        ? tLabel === 'Up'
          ? { low: entry.low - buffer * 1.6, high: entry.low - buffer * 0.9 }
          : tLabel === 'Down'
            ? { low: entry.high + buffer * 0.9, high: entry.high + buffer * 1.6 }
            : { low: entry.low - buffer * 1.2, high: entry.low - buffer * 0.6 }
        : null;

    const headline = (() => {
      const pairPretty = analysis?.pair
        ? `${analysis.pair.slice(0, 3)}/${analysis.pair.slice(3)}`
        : 'This pair';

      const trendPhrase =
        tLabel === 'Up' ? 'trending up' : tLabel === 'Down' ? 'trending down' : 'moving sideways';

      const volPhrase =
        v.label === 'Calm' ? 'calm' : v.label === 'Normal' ? 'steady' : 'wild';

      return `${pairPretty} is ${volPhrase} and ${trendPhrase}.`;
    })();

    const subline = `Volatility ${v.label} • Trend ${tLabel} • Execution ${ex.label}`;

    const actionTitle = (() => {
      if (tLabel === 'Up') return 'If you trade: wait for a pullback';
      if (tLabel === 'Down') return 'If you trade: wait for a bounce';
      return 'If you trade: stay patient';
    })();

    const actionNote = (() => {
      if (ex.label === 'Wide') return 'Spreads are wide — avoid market orders.';
      if (v.label === 'Wild') return 'Volatility is high — size smaller.';
      if (tLabel === 'Sideways') return 'Sideways market — fewer clean setups.';
      return 'Conditions look reasonable — stay disciplined.';
    })();

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
      entry,
      stop,
      target,
      explainBullets,
    };
  }, [analysis]);

  // Loading / Error / Empty (keep it premium)
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

  // Compact mode: premium mini read (bid/ask + tiny mood dot)
  if (isCompact) {
    return (
      <View style={styles.compactWrap}>
        <View style={styles.compactTop}>
          <View style={[styles.dot, { backgroundColor: computed.tColor }]} />
          <Text style={styles.compactPair}>
            {analysis.pair.slice(0, 3)}/{analysis.pair.slice(3)}
          </Text>
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

  // Large mode: Jobs-style "story" UI
  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.topHeader}>
        <View style={styles.topHeaderLeft}>
          <View style={[styles.dot, { backgroundColor: computed.tColor }]} />
          <Text style={styles.topTitle}>Today's Read</Text>
        </View>

        <TouchableOpacity
          onPress={() => {
            refetch({ pair });
          }}
          style={styles.refreshBtn}
          activeOpacity={0.8}
        >
          <Icon name="refresh-ccw" size={16} color="#0B0B0F" />
        </TouchableOpacity>
      </View>

      {/* Hero sentence */}
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
            <Text style={[styles.pillText, { color: computed.tColor }]}>{computed.tLabel}</Text>
          </View>
        </View>

        <View style={styles.lightCard}>
          <Text style={styles.lightTitle}>Volatility</Text>
          <View style={[styles.pill, { backgroundColor: computed.vColor + '22' }]}>
            <Text style={[styles.pillText, { color: computed.vColor }]}>{computed.vLabel}</Text>
          </View>
        </View>

        <View style={styles.lightCard}>
          <Text style={styles.lightTitle}>Execution</Text>
          <View style={[styles.pill, { backgroundColor: computed.exColor + '22' }]}>
            <Text style={[styles.pillText, { color: computed.exColor }]}>{computed.exLabel}</Text>
          </View>
        </View>
      </View>

      {/* Next best move */}
      <View style={styles.actionCard}>
        <View style={styles.actionHeader}>
          <Text style={styles.actionTitle}>{computed.actionTitle}</Text>
          <View style={styles.confBadge}>
            <Text style={styles.confLabel}>Confidence</Text>
            <Text style={styles.confValue}>{computed.confidence}%</Text>
          </View>
        </View>

        <Text style={styles.actionNote}>{computed.actionNote}</Text>

        <View style={styles.zonesRow}>
          <View style={styles.zone}>
            <Text style={styles.zoneLabel}>Entry zone</Text>
            <Text style={styles.zoneValue}>
              {computed.entry ? `${computed.entry.low.toFixed(5)} – ${computed.entry.high.toFixed(5)}` : '—'}
            </Text>
          </View>
          <View style={styles.zone}>
            <Text style={styles.zoneLabel}>Stop zone</Text>
            <Text style={styles.zoneValue}>
              {computed.stop ? `${computed.stop.low.toFixed(5)} – ${computed.stop.high.toFixed(5)}` : '—'}
            </Text>
          </View>
        </View>

        <View style={[styles.zone, { marginTop: 10 }]}>
          <Text style={styles.zoneLabel}>Target zone</Text>
          <Text style={styles.zoneValue}>
            {computed.target ? `${computed.target.low.toFixed(5)} – ${computed.target.high.toFixed(5)}` : '—'}
          </Text>
        </View>

        <View style={styles.microRow}>
          <View style={styles.microItem}>
            <Text style={styles.microLabel}>Pip value</Text>
            <Text style={styles.microValue}>${fmt2(safeNum(analysis.pipValue))}</Text>
          </View>
          <View style={styles.microItem}>
            <Text style={styles.microLabel}>Exec cost</Text>
            <Text style={styles.microValue}>
              {computed.exBps !== null ? `${computed.exBps.toFixed(2)} bps` : '—'}
            </Text>
          </View>
          <View style={styles.microItem}>
            <Text style={styles.microLabel}>24h corr</Text>
            <Text style={styles.microValue}>
              {computed.corr !== null ? computed.corr.toFixed(2) : '—'}
            </Text>
          </View>
        </View>
      </View>

      {/* Explain drawer */}
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => {
          LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
          setShowExplain((v) => !v);
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
              setShowDetails((v) => !v);
            }}
            style={styles.detailsToggle}
            activeOpacity={0.85}
          >
            <Text style={styles.detailsToggleText}>
              {showDetails ? 'Hide details' : 'Show details'}
            </Text>
            <Icon name={showDetails ? 'minus' : 'plus'} size={16} color="#111827" />
          </TouchableOpacity>

          {showDetails && (
            <View style={styles.detailsBox}>
              <Text style={styles.detailLine}>
                <Text style={styles.detailKey}>Pair: </Text>
                {analysis.pair.slice(0, 3)}/{analysis.pair.slice(3)}
              </Text>
              <Text style={styles.detailLine}>
                <Text style={styles.detailKey}>Trend raw: </Text>
                {analysis.trend ?? '—'}
              </Text>
              <Text style={styles.detailLine}>
                <Text style={styles.detailKey}>Volatility raw: </Text>
                {computed.vol !== null ? `${(computed.vol * 100).toFixed(3)}%` : '—'}
              </Text>
              <Text style={styles.detailLine}>
                <Text style={styles.detailKey}>Support: </Text>
                {computed.support !== null ? computed.support.toFixed(5) : '—'}
              </Text>
              <Text style={styles.detailLine}>
                <Text style={styles.detailKey}>Resistance: </Text>
                {computed.resistance !== null ? computed.resistance.toFixed(5) : '—'}
              </Text>
              <Text style={styles.detailLine}>
                <Text style={styles.detailKey}>Timestamp: </Text>
                {analysis.timestamp ?? '—'}
              </Text>
            </View>
          )}

          <Text style={styles.disclaimer}>
            Educational insights — not financial advice.
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FDFDFD',
    borderRadius: 24,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 32,
    elevation: 20,
    borderWidth: 1,
    borderColor: '#E8E8ED',
  },
  containerCompact: {
    padding: 0,
    borderWidth: 0,
    backgroundColor: 'transparent',
  },

  // Loading skeleton
  skeletonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  skeletonText: {
    marginLeft: 10,
    color: '#58606E',
    fontWeight: '600',
  },

  // Error
  inlineHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  inlineHeaderText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#1F1F1F',
  },
  muted: {
    marginTop: 6,
    color: '#69707F',
    fontWeight: '600',
  },

  // Compact mode – premium mini card
  compactWrap: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 16,
    elevation: 10,
    borderWidth: 1,
    borderColor: '#ECECF2',
  },
  compactTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  compactPair: {
    fontSize: 15,
    fontWeight: '800',
    color: '#1F1F1F',
    letterSpacing: -0.3,
  },
  compactPrices: {
    flexDirection: 'row',
    gap: 12,
  },
  compactPriceItem: {
    flex: 1,
    backgroundColor: '#F8F9FF',
    borderRadius: 16,
    paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#E2E8FF',
  },
  compactLabel: {
    fontSize: 11,
    color: '#69707F',
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  compactValue: {
    marginTop: 6,
    fontSize: 16,
    fontWeight: '900',
    color: '#1F1F1F',
  },
  compactFooter: {
    marginTop: 12,
    alignItems: 'center',
  },
  compactFooterText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#69707F',
    textAlign: 'center',
  },
  compactNoData: {
    marginTop: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  compactNoDataText: {
    fontSize: 11,
    color: '#8B949E',
    fontWeight: '600',
    fontStyle: 'italic',
  },

  // Header
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  topHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  topTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#1F1F2E',
    letterSpacing: -0.4,
  },
  refreshBtn: {
    width: 42,
    height: 42,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 6,
    borderWidth: 1,
    borderColor: '#ECECF2',
  },

  heroLine: {
    marginTop: 16,
    fontSize: 24,
    fontWeight: '800',
    color: '#1F1F1F',
    lineHeight: 30,
    letterSpacing: -0.6,
  },
  heroSubline: {
    marginTop: 8,
    fontSize: 14,
    color: '#58606E',
    fontWeight: '600',
    letterSpacing: -0.2,
  },

  // Search
  searchContainer: {
    marginTop: 20,
  },
  searchLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#58606E',
    marginBottom: 10,
    letterSpacing: 0.4,
  },
  searchRow: {
    flexDirection: 'row',
    gap: 12,
  },
  searchInput: {
    flex: 1,
    height: 48,
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    paddingHorizontal: 18,
    fontSize: 16,
    fontWeight: '700',
    color: '#1F1F1F',
    borderWidth: 1.5,
    borderColor: '#E2E6F0',
  },
  searchButton: {
    width: 48,
    height: 48,
    backgroundColor: '#1F1F1F',
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Prices Grid cards (prices, lights)
  prices: {
    marginTop: 20,
    flexDirection: 'row',
    gap: 14,
  },
  priceCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingVertical: 18,
    paddingHorizontal: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 8,
    borderWidth: 1,
    borderColor: '#ECECF2',
  },
  priceLabel: {
    fontSize: 12,
    color: '#69707F',
    fontWeight: '700',
    letterSpacing: 0.6,
  },
  priceValue: {
    marginTop: 8,
    fontSize: 18,
    fontWeight: '900',
    color: '#1F1F1F',
  },

  lightsRow: {
    marginTop: 16,
    flexDirection: 'row',
    gap: 14,
  },
  lightCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 8,
    borderWidth: 1,
    borderColor: '#ECECF2',
  },
  lightTitle: {
    fontSize: 12,
    color: '#69707F',
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  pill: {
    marginTop: 12,
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: '#F1F5FF', // fallback - will be overridden by inline style
    alignSelf: 'center',
    minWidth: 80,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pillText: {
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 0.4,
    textAlign: 'center',
  },

  // Action Card – premium glass feel
  actionCard: {
    marginTop: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.72)',
    borderRadius: 24,
    padding: 22,
    borderWidth: 1,
    borderColor: '#E8E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.08,
    shadowRadius: 30,
    elevation: 16,
  },
  actionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  actionTitle: {
    flex: 1,
    fontSize: 17,
    fontWeight: '800',
    color: '#1F1F1F',
    lineHeight: 24,
  },
  confBadge: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 6,
    borderWidth: 1,
    borderColor: '#ECECF2',
  },
  confLabel: {
    fontSize: 11,
    color: '#69707F',
    fontWeight: '700',
  },
  confValue: {
    marginTop: 3,
    fontSize: 16,
    fontWeight: '900',
    color: '#1F1F1F',
  },
  actionNote: {
    marginTop: 14,
    fontSize: 14,
    color: '#555E70',
    fontWeight: '600',
    lineHeight: 20,
  },

  zonesRow: {
    marginTop: 18,
    flexDirection: 'row',
    gap: 14,
  },
  zone: {
    flex: 1,
    backgroundColor: 'rgba(240, 245, 255, 0.6)',
    borderRadius: 18,
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderWidth: 1.5,
    borderColor: '#DDE5FF',
  },
  zoneLabel: {
    fontSize: 12,
    color: '#69707F',
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  zoneValue: {
    marginTop: 8,
    fontSize: 15,
    fontWeight: '900',
    color: '#1F1F1F',
  },

  microRow: {
    marginTop: 18,
    flexDirection: 'row',
    gap: 12,
  },
  microItem: {
    flex: 1,
    backgroundColor: '#FAFBFF',
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E8F5',
  },
  microLabel: {
    fontSize: 11,
    color: '#69707F',
    fontWeight: '700',
  },
  microValue: {
    marginTop: 6,
    fontSize: 14,
    fontWeight: '900',
    color: '#1F1F1F',
  },

  // Explain drawer
  explainToggle: {
    marginTop: 20,
    backgroundColor: '#F5F7FF',
    borderRadius: 20,
    paddingVertical: 16,
    paddingHorizontal: 18,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E6F0',
  },
  explainToggleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  explainToggleText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#1F1F1F',
  },
  explainCard: {
    marginTop: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 22,
    borderWidth: 1,
    borderColor: '#ECECF2',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.06,
    shadowRadius: 20,
    elevation: 12,
  },
  bulletRow: {
    flexDirection: 'row',
    gap: 14,
    marginBottom: 16,
    alignItems: 'flex-start',
  },
  bulletDot: {
    width: 9,
    height: 9,
    borderRadius: 4.5,
    backgroundColor: '#3B82F6',
    marginTop: 7,
  },
  bulletText: {
    flex: 1,
    fontSize: 14.5,
    color: '#444C5C',
    fontWeight: '600',
    lineHeight: 22,
  },

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
  detailsToggleText: {
    fontSize: 12,
    fontWeight: '900',
    color: '#111827',
  },
  detailsBox: {
    marginTop: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#F1F1F4',
    padding: 12,
  },
  detailLine: {
    fontSize: 12,
    color: '#52525B',
    fontWeight: '700',
    marginBottom: 6,
  },
  detailKey: {
    color: '#1F1F1F',
    fontWeight: '900',
  },

  disclaimer: {
    marginTop: 20,
    fontSize: 12,
    color: '#8B949E',
    fontWeight: '600',
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
