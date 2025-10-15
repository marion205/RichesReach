import React, { useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  FlatList,
  Dimensions,
  Animated,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { LineChart } from 'react-native-chart-kit';
import { useQuery } from '@apollo/client';
import { GET_BENCHMARK_SERIES, GET_AVAILABLE_BENCHMARKS, BenchmarkSeries } from '../../../graphql/benchmarkQueries';
// Optional gradient (falls back if not installed)
let LinearGradient: any = View;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  LinearGradient = require('react-native-linear-gradient').default;
} catch (_) { /* fallback to View */ }

// ---------- Types ----------
const { width } = Dimensions.get('window');

interface PortfolioComparisonProps {
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  portfolioHistory: Array<{ date: string; value: number }>;
}

interface Benchmark {
  id: string;
  name: string;
  symbol: string;
  returnPercent: number; // 1Y annualized
  color: string;
  icon: string;
  description: string;
  spark?: number[]; // optional mini-series for sparkline
  data?: BenchmarkSeries; // real benchmark data
}

// ---------- Component ----------
const PortfolioComparison: React.FC<PortfolioComparisonProps> = ({
  totalValue,
  totalReturn,
  totalReturnPercent,
  portfolioHistory,
}) => {
  const [selectedTimeframe, setSelectedTimeframe] =
    useState<'1M' | '3M' | '6M' | '1Y'>('3M');
  const [showChart, setShowChart] = useState(true);
  const fade = useRef(new Animated.Value(1)).current;

  // ---- Skeleton (very light) ----
  const isLoading = !portfolioHistory || portfolioHistory.length === 0;

  // ---- Real Benchmark Data ----
  const benchmarkSymbols = ['SPY', 'QQQ', 'DIA', 'VTI'];
  
  // Map selected timeframe to GraphQL timeframe
  const getGraphQLTimeframe = (timeframe: string) => {
    switch (timeframe) {
      case '1M': return '1M';
      case '3M': return '3M';
      case '6M': return '6M';
      case '1Y': return '1Y';
      default: return '1Y';
    }
  };

  const graphQLTimeframe = getGraphQLTimeframe(selectedTimeframe);

  // Fetch real benchmark data for each symbol
  const { data: spyData } = useQuery(GET_BENCHMARK_SERIES, {
    variables: { symbol: 'SPY', timeframe: graphQLTimeframe },
    skip: !selectedTimeframe,
  });
  
  const { data: qqqData } = useQuery(GET_BENCHMARK_SERIES, {
    variables: { symbol: 'QQQ', timeframe: graphQLTimeframe },
    skip: !selectedTimeframe,
  });
  
  const { data: diaData } = useQuery(GET_BENCHMARK_SERIES, {
    variables: { symbol: 'DIA', timeframe: graphQLTimeframe },
    skip: !selectedTimeframe,
  });
  
  const { data: vtiData } = useQuery(GET_BENCHMARK_SERIES, {
    variables: { symbol: 'VTI', timeframe: graphQLTimeframe },
    skip: !selectedTimeframe,
  });

  // Create benchmarks with real data
  const benchmarks: Benchmark[] = useMemo(() => {
    const benchmarkConfigs = [
      { 
        id: 'sp500', 
        name: 'S&P 500', 
        symbol: 'SPY', 
        color: '#0A84FF', 
        icon: 'trending-up',
        description: 'The 500 largest US companies',
        data: spyData?.benchmarkSeries
      },
      { 
        id: 'nasdaq', 
        name: 'NASDAQ', 
        symbol: 'QQQ', 
        color: '#34C759', 
        icon: 'activity',
        description: 'Technology-heavy index',
        data: qqqData?.benchmarkSeries
      },
      { 
        id: 'dow', 
        name: 'Dow Jones', 
        symbol: 'DIA', 
        color: '#FF9F0A', 
        icon: 'bar-chart',
        description: '30 large US companies',
        data: diaData?.benchmarkSeries
      },
      { 
        id: 'total', 
        name: 'Total Market', 
        symbol: 'VTI', 
        color: '#AF52DE', 
        icon: 'pie-chart',
        description: 'Entire US stock market',
        data: vtiData?.benchmarkSeries
      },
    ];

    return benchmarkConfigs.map(config => {
      const realReturn = config.data?.totalReturnPercent || 0;
      const sparkData = config.data?.dataPoints?.map(dp => dp.value) || [];
      
      return {
        ...config,
        returnPercent: realReturn,
        spark: sparkData.length > 0 ? sparkData : undefined,
      };
    });
  }, [spyData, qqqData, diaData, vtiData]);

  // ---- Helpers ----
  const getBenchmarkReturn = (benchmark: Benchmark) => {
    // Use real data if available, otherwise fallback to calculated values
    if (benchmark.data?.totalReturnPercent !== undefined) {
      return benchmark.data.totalReturnPercent;
    }
    
    // Fallback calculation (shouldn't be needed with real data)
    const annualReturn = benchmark.returnPercent;
    switch (selectedTimeframe) {
      case '1M': return annualReturn / 12;
      case '3M': return annualReturn / 4;
      case '6M': return annualReturn / 2;
      default:   return annualReturn;
    }
  };

  const filteredSeries = useMemo(() => {
    const n = portfolioHistory?.length ?? 0;
    if (n === 0) return [];
    const take = selectedTimeframe === '1M' ? 4
              : selectedTimeframe === '3M' ? 8
              : selectedTimeframe === '6M' ? 12
              : n;
    return portfolioHistory.slice(-Math.max(2, Math.min(take, n)));
  }, [portfolioHistory, selectedTimeframe]);

  const timeframePerf = useMemo(() => {
    if (filteredSeries.length < 2) {
      const start = totalValue - totalReturn;
      return { startValue: start, endValue: totalValue, pct: totalReturnPercent, amt: totalReturn };
    }
    const startValue = filteredSeries[0].value;
    const endValue = filteredSeries[filteredSeries.length - 1].value;
    const amt = endValue - startValue;
    const pct = startValue > 0 ? (amt / startValue) * 100 : 0;
    return { startValue, endValue, pct, amt };
  }, [filteredSeries, totalReturn, totalReturnPercent, totalValue]);

  const fmtPct = (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
  const fmtMoney = (v: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v);
  const perfColor = (v: number) => (v > 0 ? '#34C759' : v < 0 ? '#FF3B30' : '#8E8E93');

  // ---- Chart data (portfolio + 2 benchmarks) ----
  const chartData = useMemo(() => {
    if (filteredSeries.length === 0) return { labels: [], datasets: [] as any[] };

    const start = filteredSeries[0].value || 1;
    const labels = filteredSeries.map(p => {
      const d = new Date(p.date);
      return `${d.getMonth() + 1}/${d.getDate()}`;
    });

    const portfolio = filteredSeries.map(p => p.value);
    const makeRef = (benchmark: Benchmark) => {
      const tfPct = getBenchmarkReturn(benchmark) / 100;
      const L = filteredSeries.length;
      return filteredSeries.map((_, i) => start * (1 + tfPct * (i / Math.max(1, L - 1))));
    };

    // Create benchmark datasets from real data
    const benchmarkDatasets = benchmarks.slice(0, 2).map((benchmark, index) => {
      const color = benchmark.color;
      const rgb = color.startsWith('#') ? 
        parseInt(color.slice(1), 16) : 
        parseInt(color, 16);
      const r = (rgb >> 16) & 255;
      const g = (rgb >> 8) & 255;
      const b = rgb & 255;
      
      return {
        data: makeRef(benchmark),
        color: (o = 1) => `rgba(${r},${g},${b},${o})`,
        strokeWidth: 2,
      };
    });

    return {
      labels,
      datasets: [
        { data: portfolio, color: (o = 1) => `rgba(10,132,255,${o})`, strokeWidth: 3 },
        ...benchmarkDatasets,
      ],
    };
  }, [filteredSeries, selectedTimeframe, benchmarks]);

  // ---- Animate on timeframe change ----
  const flipFade = () => {
    Animated.sequence([
      Animated.timing(fade, { toValue: 0, duration: 120, useNativeDriver: true }),
      Animated.timing(fade, { toValue: 1, duration: 120, useNativeDriver: true }),
    ]).start();
  };

  // ---- Derived insights ----
  const bestBenchmark = useMemo(() => {
    const mapped = benchmarks.map(b => ({
      ...b,
      tf: getBenchmarkReturn(b),
      diff: timeframePerf.pct - getBenchmarkReturn(b),
    }));
    return mapped.sort((a, b) => b.tf - a.tf)[0];
  }, [benchmarks, selectedTimeframe, timeframePerf.pct]);

  // Get SPY benchmark for comparison
  const spyBenchmark = benchmarks.find(b => b.symbol === 'SPY');
  const spyReturn = spyBenchmark ? getBenchmarkReturn(spyBenchmark) : 0;
  
  const beating = timeframePerf.pct > spyReturn;
  const insightText = beating
    ? `Outperforming S&P 500 by ${fmtPct(timeframePerf.pct - spyReturn)}. Staying diversified is working.`
    : `Lagging S&P 500 by ${fmtPct(spyReturn - timeframePerf.pct)}. Consider tilting toward leaders or rebalancing.`;

  // ---- Simple error guard for the chart ----
  const ChartSafe = () => {
    try {
      if (!showChart) return null;
      if (!chartData.datasets?.length) {
        return (
          <View style={styles.chartEmpty}>
            <Text style={styles.chartEmptyText}>Chart unavailable</Text>
          </View>
        );
      }
      return (
        <View style={styles.chartContainer}>
          <Text style={styles.chartTitle}>Portfolio vs Benchmarks</Text>
          <LineChart
            data={chartData}
            width={width - 40}
            height={220}
            bezier
            style={styles.chart}
            chartConfig={{
              backgroundColor: '#FFFFFF',
              backgroundGradientFrom: '#FFFFFF',
              backgroundGradientTo: '#FFFFFF',
              decimalPlaces: 0,
              color: (o = 1) => `rgba(0,0,0,${o})`,
              labelColor: (o = 1) => `rgba(0,0,0,${o})`,
              formatYLabel: (y: string) => {
                const n = Number(y);
                if (isNaN(n)) return y;
                if (Math.abs(n) >= 1000) return `$${(n / 1000).toFixed(1)}k`;
                return `$${n.toFixed(0)}`;
              },
              propsForBackgroundLines: { strokeDasharray: '3 3' },
              propsForDots: { r: '3', strokeWidth: '2', stroke: '#0A84FF' },
            }}
          />
          <View style={styles.chartLegend}>
            <Legend swatch="#0A84FF" label="Your Portfolio" />
            <Legend swatch="#34C759" label="S&P 500" />
            <Legend swatch="#FF9F0A" label="NASDAQ" />
          </View>
        </View>
      );
    } catch {
      return (
        <View style={styles.chartEmpty}>
          <Text style={styles.chartEmptyText}>Something went wrong rendering the chart.</Text>
        </View>
      );
    }
  };

  // ---- Render ----
  if (isLoading) {
    return <SkeletonCard />;
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Icon name="bar-chart-2" size={20} color="#007AFF" />
          <Text style={styles.title}>Portfolio Comparison</Text>
        </View>
        <TouchableOpacity onPress={() => setShowChart(s => !s)} style={styles.toggleBtn}>
          <Icon name={showChart ? 'chevron-up' : 'chevron-down'} size={16} color="#007AFF" />
          <Text style={styles.toggleText}>{showChart ? 'Hide' : 'Show'} Chart</Text>
        </TouchableOpacity>
      </View>

      {/* Summary */}
      <LinearGradient
        colors={LinearGradient === View ? ['#F8F9FA', '#F8F9FA'] : ['#EAF3FF', '#FFFFFF']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.summaryCard}
      >
        <View style={styles.summaryHeader}>
          <Text style={styles.summaryTitle}>Your Performance</Text>

          <View style={styles.timeframeBar}>
            {(['1M', '3M', '6M', '1Y'] as const).map(tf => {
              const active = selectedTimeframe === tf;
              return (
                <TouchableOpacity
                  key={tf}
                  onPress={() => { if (tf !== selectedTimeframe) { setSelectedTimeframe(tf); flipFade(); } }}
                  style={[styles.tfBtn, active && styles.tfBtnActive]}
                >
                  <Text style={[styles.tfText, active && styles.tfTextActive]}>{tf}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <Animated.View style={[styles.summaryRow, { opacity: fade }]}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Total Return</Text>
            <Text style={[styles.summaryValue, { color: perfColor(timeframePerf.pct) }]}>
              {fmtPct(timeframePerf.pct)}
            </Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Return Amount</Text>
            <Text style={[styles.summaryValue, { color: perfColor(timeframePerf.amt) }]}>
              {fmtMoney(timeframePerf.amt)}
            </Text>
          </View>
        </Animated.View>
      </LinearGradient>

      {/* Chart */}
      <ChartSafe />

      {/* Benchmarks Carousel */}
      <View style={styles.benchHeader}>
        <Text style={styles.benchTitle}>Market Benchmarks</Text>
      </View>
      <FlatList
        data={benchmarks}
        keyExtractor={(b) => b.id}
        horizontal
        showsHorizontalScrollIndicator={false}
        snapToInterval={CARD_W + 12}
        decelerationRate="fast"
        contentContainerStyle={{ paddingHorizontal: 12 }}
        renderItem={({ item }) => {
          const adj = getBenchmarkReturn(item);
          const diff = timeframePerf.pct - adj;
          const outperform = diff > 0.01;
          return (
            <View style={[styles.benchCard, { borderColor: item.color }]}>
              <View style={styles.benchHeaderRow}>
                <View style={styles.benchLeft}>
                  <View style={[styles.benchIcon, { backgroundColor: item.color }]}>
                    <Icon name={item.icon} size={16} color="#fff" />
                  </View>
                  <View style={{ marginLeft: 8 }}>
                    <Text style={styles.benchName}>{item.name}</Text>
                    <Text style={styles.benchSymbol}>{item.symbol}</Text>
                  </View>
                </View>
                <View style={styles.benchRight}>
                  {outperform && (
                    <View style={styles.badge}>
                      <Icon name="check" size={10} color="#fff" />
                      <Text style={styles.badgeText}>Outperform</Text>
                    </View>
                  )}
                  <Text style={[styles.benchReturn, { color: perfColor(adj) }]}>{fmtPct(adj)}</Text>
                </View>
              </View>

              {/* Mini Sparkline */}
              {item.spark && (
                <LineChart
                  data={{ labels: new Array(item.spark.length).fill(''), datasets: [{ data: item.spark }] }}
                  width={CARD_W - 32}
                  height={70}
                  withDots={false}
                  withInnerLines={false}
                  withOuterLines={false}
                  withVerticalLabels={false}
                  withHorizontalLabels={false}
                  chartConfig={{
                    backgroundColor: '#FFFFFF',
                    backgroundGradientFrom: '#FFFFFF',
                    backgroundGradientTo: '#FFFFFF',
                    decimalPlaces: 0,
                    color: () => item.color,
                  }}
                  style={{ marginTop: 4 }}
                />
              )}

              <View style={styles.benchRow}>
                <View style={styles.compItem}>
                  <Text style={styles.compLabel}>Your Portf.</Text>
                  <Text style={[styles.compValue, { color: perfColor(timeframePerf.pct) }]}>
                    {fmtPct(timeframePerf.pct)}
                  </Text>
                </View>
                <View style={styles.compItem}>
                  <Text style={styles.compLabel}>Difference</Text>
                  <Text style={[styles.compValue, { color: perfColor(diff) }]}>{fmtPct(diff)}</Text>
                </View>
              </View>

              <Text style={styles.benchDesc}>{item.description}</Text>
            </View>
          );
        }}
      />

      {/* Insights */}
      <View style={styles.insights}>
        <View style={styles.insightsHeader}>
          <Icon name="info" size={16} color="#8E8E93" />
          <Text style={styles.insightsTitle}>Performance Insights</Text>
        </View>
        <Text style={styles.insightText}>
          {insightText}{' '}
          <Text style={styles.insightSub}>
            Best  in period: {bestBenchmark?.name} ({fmtPct(bestBenchmark?.tf ?? 0)}).
          </Text>
        </Text>
      </View>
    </View>
  );
};

// ---------- Small bits ----------
const CARD_W = Math.min(260, width * 0.75);

const Legend = ({ swatch, label }: { swatch: string; label: string }) => (
  <View style={styles.legendItem}>
    <View style={[styles.legendSwatch, { backgroundColor: swatch }]} />
    <Text style={styles.legendText}>{label}</Text>
  </View>
);

// Light skeleton without external libs
const SkeletonCard = () => {
  const pulse = useRef(new Animated.Value(0.6)).current;
  React.useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 700, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0.6, duration: 700, useNativeDriver: true }),
      ])
    ).start();
  }, [pulse]);

  return (
    <Animated.View style={[styles.container, { opacity: pulse }]}>
      <View style={styles.skBlock} />
      <View style={[styles.skBlock, { height: 140, marginTop: 12 }]} />
      <View style={[styles.skRow]}>
        <View style={[styles.skChip]} />
        <View style={[styles.skChip]} />
        <View style={[styles.skChip]} />
      </View>
    </Animated.View>
  );
};

// ---------- Styles ----------
const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },

  // Header
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  title: { fontSize: 18, fontWeight: '700', color: '#1C1C1E' },
  toggleBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 8, paddingVertical: 4 },
  toggleText: { color: '#007AFF', fontWeight: '600' },

  // Summary
  summaryCard: { borderRadius: 12, padding: 14, marginBottom: 12 },
  summaryHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  summaryTitle: { fontSize: 16, fontWeight: '700', color: '#1C1C1E' },
  timeframeBar: { flexDirection: 'row', backgroundColor: '#fff', borderRadius: 8, padding: 2, borderWidth: 1, borderColor: '#E5E5EA' },
  tfBtn: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 6 },
  tfBtnActive: { backgroundColor: '#007AFF' },
  tfText: { fontSize: 12, color: '#8E8E93', fontWeight: '600' },
  tfTextActive: { color: '#fff' },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between' },
  summaryItem: { alignItems: 'center', flex: 1 },
  summaryLabel: { fontSize: 12, color: '#8E8E93', marginBottom: 2 },
  summaryValue: { fontSize: 18, fontWeight: '700' },

  // Chart
  chartContainer: { backgroundColor: '#F8F9FA', borderRadius: 12, padding: 16, marginTop: 4, marginBottom: 12 },
  chartTitle: { fontSize: 16, fontWeight: '600', color: '#1C1C1E', textAlign: 'center', marginBottom: 12 },
  chart: { borderRadius: 12 },
  chartLegend: { flexDirection: 'row', justifyContent: 'center', gap: 14, marginTop: 8 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendSwatch: { width: 10, height: 10, borderRadius: 6 },
  legendText: { fontSize: 12, color: '#8E8E93' },
  chartEmpty: { backgroundColor: '#F8F9FA', borderRadius: 12, padding: 28, alignItems: 'center', marginBottom: 12 },
  chartEmptyText: { color: '#8E8E93' },

  // Benchmarks
  benchHeader: { marginTop: 2, marginBottom: 6 },
  benchTitle: { fontSize: 16, fontWeight: '700', color: '#1C1C1E' },
  benchCard: {
    width: CARD_W,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  benchHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  benchLeft: { flexDirection: 'row', alignItems: 'center' },
  benchRight: { alignItems: 'flex-end' },
  benchIcon: { width: 30, height: 30, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  benchName: { fontSize: 14, fontWeight: '600', color: '#1C1C1E' },
  benchSymbol: { fontSize: 12, color: '#8E8E93' },
  benchReturn: { fontSize: 16, fontWeight: '700', marginTop: 4 },
  benchRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
  compItem: { alignItems: 'center', flex: 1 },
  compLabel: { fontSize: 11, color: '#8E8E93' },
  compValue: { fontSize: 14, fontWeight: '700' },
  benchDesc: { fontSize: 12, color: '#8E8E93', lineHeight: 16, marginTop: 8 },

  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#34C759',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginBottom: 4,
  },
  badgeText: { color: '#fff', fontSize: 10, fontWeight: '700' },

  // Insights
  insights: {
    backgroundColor: '#FFF8E1',
    borderRadius: 12,
    padding: 14,
    borderLeftWidth: 4,
    borderLeftColor: '#FFD60A',
    marginTop: 12,
  },
  insightsHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  insightsTitle: { fontSize: 14, fontWeight: '700', color: '#1C1C1E' },
  insightText: { fontSize: 13, color: '#1C1C1E', lineHeight: 18 },
  insightSub: { fontWeight: '600' },

  // Skeleton
  skBlock: { height: 80, backgroundColor: '#EEE', borderRadius: 12 },
  skRow: { flexDirection: 'row', gap: 8, marginTop: 12 },
  skChip: { flex: 1, height: 44, backgroundColor: '#EEE', borderRadius: 8 },
});

export default PortfolioComparison;