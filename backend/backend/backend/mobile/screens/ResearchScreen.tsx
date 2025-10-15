import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { AdvancedChart } from '../src/components';
import { UI } from '../src/shared/constants';

// Null-safe helper functions
const safeFixed = (val: any, dp = 2, fallback = '—') =>
  Number.isFinite(val) ? Number(val).toFixed(dp) : fallback;

const safePct = (val: any, dp = 0, fallback = '—') =>
  Number.isFinite(val) ? `${Number(val * 100).toFixed(dp)}%` : fallback;

const safeMoney = (val: any, dp = 2, fallback = '—') =>
  Number.isFinite(val) ? `$${Number(val).toFixed(dp)}` : fallback;

// UI Primitives
const SectionCard: React.FC<{title?: string; right?: React.ReactNode; children: React.ReactNode}> = ({ title, right, children }) => (
  <View style={styles.card}>
    {(title || right) && (
      <View style={styles.sectionHeader}>
        {title ? <Text style={styles.sectionTitle}>{title}</Text> : <View />}
        {right}
      </View>
    )}
    {children}
  </View>
);

const Badge: React.FC<{label: string; tone?: 'neutral'|'success'|'danger'|'warn'}> = ({ label, tone='neutral' }) => {
  const bg = tone==='success' ? '#DCFCE7' : tone==='danger' ? '#FEE2E2' : tone==='warn' ? '#FEF3C7' : '#E5E7EB';
  const fg = tone==='success' ? '#166534' : tone==='danger' ? '#991B1B' : tone==='warn' ? '#92400E' : '#374151';
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.badgeText, { color: fg }]}>{label}</Text>
    </View>
  );
};

const Segmented: React.FC<{options: string[]; value: string; onChange: (v: string)=>void}> = ({ options, value, onChange }) => (
  <View style={styles.segmented}>
    {options.map(opt => {
      const active = opt === value;
      return (
        <TouchableOpacity key={opt} onPress={() => onChange(opt)} style={[styles.segment, active && styles.segmentActive]}>
          <Text style={[styles.segmentText, active && styles.segmentTextActive]}>{opt}</Text>
        </TouchableOpacity>
      );
    })}
  </View>
);

const MetricRow: React.FC<{label: string; value?: string | number; monospace?: boolean}> = ({ label, value='—', monospace }) => (
  <View style={styles.metricRow}>
    <Text style={styles.metricLabel}>{label}</Text>
    <Text style={[styles.metricValue, monospace && { fontVariant: ['tabular-nums'] }]} numberOfLines={1}>{value}</Text>
  </View>
);

const RESEARCH_QUERY = gql`
  query Research($s: String!) {
    researchHub(symbol: $s) {
      symbol

      company: snapshot {
        name
        sector
        marketCap
        country
        website
      }

      quote {
        currentPrice: price
        change: chg
        changePercent: chgPct
        high
        low
        volume
      }

      technicals: technical {
        rsi
        macd
        macdhistogram
        movingAverage50
        movingAverage200
        supportLevel
        resistanceLevel
        impliedVolatility
      }

      sentiment {
        sentiment_label: label
        sentiment_score: score
        article_count
        confidence
      }

      macro {
        vix
        market_sentiment: marketSentiment
        risk_appetite: riskAppetite
      }

      marketRegime {
        market_regime
        confidence
        recommended_strategy
      }

      peers
      updatedAt
    }
  }
`;

const CHART_QUERY = gql`
  query Chart(
    $s: String!,
    $tf: String = "1D",
    $iv: String = "1D",
    $limit: Int = 180,
    $inds: [String!] = ["SMA20","SMA50","EMA12","EMA26","RSI","MACD","BB"]
  ) {
    stockChartData(
      symbol: $s,
      timeframe: $tf,
      interval: $iv,
      limit: $limit,
      indicators: $inds
    ) {
      symbol
      interval
      limit
      currentPrice
      change
      changePercent
      data {
        timestamp
        open
        high
        low
        close
        volume
      }
      indicators {
        SMA20
        SMA50
        EMA12
        EMA26
        BB_upper
        BB_middle
        BB_lower
        RSI14
        MACD
        MACD_signal
        MACD_hist
      }
    }
  }
`;

const ResearchScreen: React.FC = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [chartInterval, setChartInterval] = useState('1D');

  const { data: researchData, loading: researchLoading, error: researchError, refetch: refetchResearch } = useQuery(RESEARCH_QUERY, {
    variables: { s: symbol },
    skip: !symbol,
  });

  const { data: chartData, loading: chartLoading, error: chartError, refetch: refetchChart } = useQuery(CHART_QUERY, {
    variables: {
      s: symbol,
      tf: chartInterval,
      iv: chartInterval,
      limit: 180,
      inds: ["SMA20","SMA50","EMA12","EMA26","RSI","MACD","BB"],
    },
    skip: !symbol,
    fetchPolicy: 'cache-and-network',
    nextFetchPolicy: 'cache-first',
    errorPolicy: 'all',
  });

  const research = researchData?.researchHub;
  const chart = chartData?.stockChartData;

  const formatMarketCap = (cap: number) => {
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`;
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(1)}B`;
    if (cap >= 1e6) return `$${(cap / 1e6).toFixed(1)}M`;
    return `$${cap.toLocaleString()}`;
  };

  const getSentimentColor = (label: string) => {
    switch (label) {
      case 'BULLISH': return '#22C55E';
      case 'BEARISH': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case 'BULL': return '#22C55E';
      case 'BEAR': return '#EF4444';
      default: return '#F59E0B';
    }
  };

  if (researchLoading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Research Hub</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={UI.colors.accent} />
          <Text style={styles.loadingText}>Loading research data...</Text>
        </View>
      </View>
    );
  }

  if (researchError) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Research Hub</Text>
        </View>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color={UI.colors.error} />
          <Text style={styles.errorText}>Failed to load research data</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => refetchResearch()}>
            <Icon name="refresh-cw" size={16} color={UI.colors.accent} />
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Research Hub</Text>
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            value={symbol}
            onChangeText={(t) => setSymbol(t.toUpperCase().trim())}
            placeholder="Enter symbol (e.g., AAPL)"
            placeholderTextColor={UI.colors.sub}
            autoCapitalize="characters"
          />
          <TouchableOpacity style={styles.searchButton} onPress={() => refetchResearch()}>
            <Icon name="search" size={20} color={UI.colors.accent} />
          </TouchableOpacity>
        </View>
      </View>

      {research && (
        <>
          {/* Company Header */}
          <SectionCard>
            <View style={styles.companyHeader}>
              <View style={{ flex: 1, paddingRight: 12 }}>
                <Text style={styles.companyName}>
                  {research?.company?.name ?? 'N/A'} <Text style={styles.symbol}>({research?.symbol ?? 'N/A'})</Text>
                </Text>
                <Text style={styles.sector}>
                  {research?.company?.sector ?? 'N/A'} • {formatMarketCap(research?.company?.marketCap ?? 0)}
                </Text>
                {!!research?.company?.website && (
                  <Text style={styles.website} numberOfLines={1}>{research.company.website}</Text>
                )}
              </View>
              <View style={styles.priceContainer}>
                <Text style={styles.currentPrice}>
                  {safeMoney(research?.quote?.currentPrice, 2)}
                </Text>
                <Text style={[
                  styles.change,
                  { color: (research?.quote?.change ?? 0) >= 0 ? '#22C55E' : '#EF4444' }
                ]}>
                  {(research?.quote?.change ?? 0) >= 0 ? '+' : ''}
                  {safeFixed(research?.quote?.change, 2)} ({safeFixed(research?.quote?.changePercent, 2)}%)
                </Text>
              </View>
            </View>
          </SectionCard>

          {/* Advanced Chart */}
          <SectionCard
            title="Price Chart"
            right={
              <Segmented
                options={['1D','1W','1M','3M','1Y']}
                value={chartInterval}
                onChange={(v) => setChartInterval(v)}
              />
            }
          >
            {chartLoading ? (
              <View style={styles.chartLoading}>
                <ActivityIndicator size="small" color={UI.colors.accent} />
              </View>
            ) : chart && chart.data?.length ? (
              <>
                <AdvancedChart data={chart.data} indicators={chart.indicators || {}} width={350} height={220} />
                <View style={styles.legend}>
                  <View style={styles.legendDot} />
                  <Text style={styles.legendText}>SMA20</Text>
                  <View style={styles.legendDot} />
                  <Text style={styles.legendText}>SMA50</Text>
                  <View style={styles.legendDot} />
                  <Text style={styles.legendText}>EMA12</Text>
                  <View style={styles.legendDot} />
                  <Text style={styles.legendText}>EMA26</Text>
                  <View style={styles.legendDot} />
                  <Text style={styles.legendText}>BB</Text>
                </View>
              </>
            ) : (
              <View style={styles.chartLoading}>
                <Text style={{ color: UI.colors.sub }}>No chart data</Text>
              </View>
            )}
            {chartError && <Text style={styles.errorInline}>{chartError.message}</Text>}
          </SectionCard>

          {/* Key Metrics Cards */}
          <View style={styles.metricsGrid}>
            <SectionCard title="Technicals">
              <MetricRow label="RSI (14)" value={safeFixed(research?.technicals?.rsi, 1)} />
              <MetricRow label="MACD" value={safeFixed(research?.technicals?.macd, 3)} monospace />
              <MetricRow label="MA 50" value={safeMoney(research?.technicals?.movingAverage50)} />
            </SectionCard>

            <SectionCard title="Sentiment" right={
              <Badge
                label={research?.sentiment?.sentiment_label || 'NEUTRAL'}
                tone={research?.sentiment?.sentiment_label === 'BULLISH' ? 'success' : research?.sentiment?.sentiment_label === 'BEARISH' ? 'danger' : 'neutral'}
              />
            }>
              <MetricRow label="Score" value={safeFixed(research?.sentiment?.sentiment_score, 2)} />
              <MetricRow label="Articles" value={research?.sentiment?.article_count ?? '—'} />
              <MetricRow label="Confidence" value={safePct(research?.sentiment?.confidence, 0)} />
            </SectionCard>

            <SectionCard title="Macro">
              <MetricRow label="VIX" value={safeFixed(research?.macro?.vix, 1)} />
              <MetricRow label="Market Sentiment" value={research?.macro?.market_sentiment ?? '—'} />
              <MetricRow label="Risk Appetite" value={safePct(research?.macro?.risk_appetite, 0)} />
            </SectionCard>

            <SectionCard title="Market Regime" right={
              <Badge
                label={research?.marketRegime?.market_regime || 'NEUTRAL'}
                tone={research?.marketRegime?.market_regime === 'BULL' ? 'success' : research?.marketRegime?.market_regime === 'BEAR' ? 'danger' : 'warn'}
              />
            }>
              <MetricRow label="Confidence" value={safePct(research?.marketRegime?.confidence, 0)} />
              <MetricRow label="Strategy" value={research?.marketRegime?.recommended_strategy ?? '—'} />
            </SectionCard>

            <SectionCard title="Options Snapshot">
              <MetricRow label="Implied Vol" value={safePct(research?.technicals?.impliedVolatility, 1)} />
              <MetricRow label="Support" value={safeMoney(research?.technicals?.supportLevel)} />
              <MetricRow label="Resistance" value={safeMoney(research?.technicals?.resistanceLevel)} />
            </SectionCard>
          </View>

          {/* Peers */}
          <SectionCard title="Peer Companies">
            <View style={styles.peersContainer}>
              {(research?.peers || []).map((peer: string) => (
                <TouchableOpacity
                  key={peer}
                  style={styles.peerChip}
                  onPress={() => {
                    setSymbol(peer);
                    refetchResearch({ s: peer });
                    refetchChart?.({ s: peer, tf: chartInterval, iv: chartInterval, limit: 180 });
                  }}
                >
                  <Text style={styles.peerText}>{peer}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </SectionCard>

          {/* Last Updated */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              Last updated: {research?.updatedAt ? new Date(research.updatedAt).toLocaleString() : '—'}
            </Text>
          </View>
        </>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: UI.colors.background,
  },
  header: {
    padding: 16,
    backgroundColor: UI.colors.background,
    borderBottomWidth: 1,
    borderBottomColor: UI.colors.border,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: UI.colors.text,
    marginBottom: 16,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  searchInput: {
    flex: 1,
    height: 40,
    borderWidth: 1,
    borderColor: UI.colors.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    color: UI.colors.text,
    backgroundColor: UI.colors.secondary,
  },
  searchButton: {
    marginLeft: 8,
    padding: 8,
    backgroundColor: UI.colors.accent,
    borderRadius: 8,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    marginTop: 16,
    color: UI.colors.sub,
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorText: {
    marginTop: 16,
    color: UI.colors.error,
    fontSize: 16,
    textAlign: 'center',
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: UI.colors.secondary,
    borderRadius: 8,
  },
  retryText: {
    marginLeft: 8,
    color: UI.colors.accent,
    fontWeight: '600',
  },
  card: {
    backgroundColor: UI.colors.background,
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
    elevation: 2,
  },
  companyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  companyName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: UI.colors.text,
  },
  sector: {
    fontSize: 14,
    color: UI.colors.sub,
    marginTop: 4,
  },
  marketCap: {
    fontSize: 14,
    color: UI.colors.sub,
    marginTop: 2,
  },
  priceContainer: {
    alignItems: 'flex-end',
  },
  currentPrice: {
    fontSize: 24,
    fontWeight: 'bold',
    color: UI.colors.text,
  },
  change: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 4,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: UI.colors.text,
  },
  intervalSelector: {
    flexDirection: 'row',
  },
  intervalButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginLeft: 4,
    borderRadius: 6,
    backgroundColor: UI.colors.secondary,
  },
  intervalButtonActive: {
    backgroundColor: UI.colors.accent,
  },
  intervalText: {
    fontSize: 12,
    color: UI.colors.sub,
    fontWeight: '600',
  },
  intervalTextActive: {
    color: UI.colors.background,
  },
  chartLoading: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
  },
  metricCard: {
    width: '48%',
    backgroundColor: UI.colors.background,
    margin: '1%',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
    elevation: 2,
  },
  metricTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: UI.colors.text,
    marginBottom: 12,
  },
  metricItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 14,
    color: UI.colors.sub,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: UI.colors.text,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: UI.colors.text,
    marginBottom: 12,
  },
  peersContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  peerChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: UI.colors.secondary,
    borderRadius: 16,
  },
  peerText: {
    fontSize: 14,
    color: UI.colors.accent,
    fontWeight: '600',
  },
  footer: {
    padding: 16,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: UI.colors.sub,
  },
  // New UI component styles
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  symbol: { 
    color: UI.colors.sub, 
    fontSize: 16, 
    fontWeight: '600' 
  },
  website: { 
    color: UI.colors.accent, 
    fontSize: 12, 
    marginTop: 6 
  },
  segmented: {
    flexDirection: 'row',
    backgroundColor: UI.colors.secondary,
    borderRadius: 8,
    padding: 2,
  },
  segment: { 
    paddingVertical: 6, 
    paddingHorizontal: 10, 
    borderRadius: 6 
  },
  segmentActive: { 
    backgroundColor: UI.colors.accent 
  },
  segmentText: { 
    fontSize: 12, 
    color: UI.colors.sub, 
    fontWeight: '600' 
  },
  segmentTextActive: { 
    color: UI.colors.background 
  },
  legend: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    marginTop: 10, 
    flexWrap: 'wrap' 
  },
  legendDot: { 
    width: 8, 
    height: 8, 
    borderRadius: 4, 
    backgroundColor: UI.colors.sub, 
    marginRight: 6, 
    marginLeft: 12 
  },
  legendText: { 
    color: UI.colors.sub, 
    fontSize: 12, 
    marginRight: 6 
  },
  badge: { 
    paddingHorizontal: 8, 
    paddingVertical: 4, 
    borderRadius: 999 
  },
  badgeText: { 
    fontSize: 12, 
    fontWeight: '700' 
  },
  metricRow: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    paddingVertical: 6 
  },
  errorInline: { 
    color: UI.colors.error, 
    marginTop: 8, 
    fontSize: 12 
  },
});

export default ResearchScreen;

