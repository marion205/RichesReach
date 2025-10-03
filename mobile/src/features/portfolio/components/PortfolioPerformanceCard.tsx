import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  useColorScheme,
  Alert,
  PanResponder,
  GestureResponderEvent,
  PanResponderGestureState,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import Svg, { Line as SvgLine, Circle as SvgCircle, Rect as SvgRect, Text as SvgText } from 'react-native-svg';
import Icon from '@expo/vector-icons/Feather';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useQuery } from '@apollo/client';
import EducationalTooltip from '../../../components/common/EducationalTooltip';
import PortfolioEducationModal from './PortfolioEducationModal';
import { getTermExplanation } from '../../../shared/financialTerms';
import webSocketService, { PortfolioUpdate } from '../../../services/WebSocketService';
import { useOptimizedPolling } from '../../../hooks/useOptimizedPolling';
import { useOptimizedDataService } from '../../../services/OptimizedDataService';
import { 
  GET_BENCHMARK_SERIES, 
  GET_AVAILABLE_BENCHMARKS,
  BenchmarkSeries,
  extractBenchmarkValues,
  getBenchmarkSummary,
  calculateAlpha,
  formatBenchmarkSymbol,
  getBenchmarkColor
} from '../../../graphql/benchmarkQueries';
import BenchmarkSelector from './BenchmarkSelector';

const { width } = Dimensions.get('window');
const PREF_SHOW_BENCH = 'rr.pref.show_benchmark'; // NEW

type Props = {
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  benchmarkSymbol?: string;        // e.g., 'SPY'
  benchmarkSeries?: number[];      // optional: pass real benchmark series (same length as current timeframe)
  useRealBenchmarkData?: boolean;  // whether to fetch real benchmark data from GraphQL
};

const TABS = ['1D', '1W', '1M', '3M', '1Y', 'All'] as const;
type Timeframe = typeof TABS[number];

const fmtCompactUsd = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 2 }).format(n);

const fmtUsd = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(n);

const fmtPct = (p: number) => `${p >= 0 ? '+' : ''}${p.toFixed(2)}%`;

export default function PortfolioPerformanceCard({
  totalValue,
  totalReturn,
  totalReturnPercent,
  benchmarkSymbol = 'SPY',
  benchmarkSeries,
  useRealBenchmarkData = true,
}: Props) {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const [selectedBenchmarkSymbol, setSelectedBenchmarkSymbol] = useState<string>(benchmarkSymbol);

  const palette = {
    bg: isDark ? '#111214' : '#FFFFFF',
    text: isDark ? '#F5F6F8' : '#1C1C1E',
    sub: isDark ? '#A1A7AF' : '#6B7280',
    border: isDark ? '#23262B' : '#E5E7EB',
    grid: isDark ? '#2A2E34' : '#EDF0F2',
    green: '#22C55E',
    red: '#EF4444',
    accent: isDark ? '#3B82F6' : '#2563EB',
    bench: getBenchmarkColor(selectedBenchmarkSymbol, isDark),   // benchmark color based on selected symbol
    chipBg: isDark ? '#1A1C1F' : '#F3F4F6',
    chipActiveBg: isDark ? '#2B2F36' : '#111827',
    chipActiveText: '#FFFFFF',
    tooltipBg: isDark ? '#1C1F24' : '#0F172A',
    tooltipText: '#FFFFFF',
    tooltipBorder: isDark ? '#2E3440' : '#1F2937',
  };

  const [showEducationModal, setShowEducationModal] = useState(false);
  const [clickedElement, setClickedElement] = useState<string>('');
  const [tab, setTab] = useState<Timeframe>('1M');
  const [showBenchmark, setShowBenchmark] = useState<boolean>(true);

  // GraphQL queries for benchmark data
  const { data: benchmarkData, loading: benchmarkLoading, error: benchmarkError } = useQuery(
    GET_BENCHMARK_SERIES,
    {
      variables: { symbol: selectedBenchmarkSymbol, timeframe: tab },
      skip: !useRealBenchmarkData || !showBenchmark,
      fetchPolicy: 'cache-and-network',
    }
  );

  const { data: availableBenchmarksData } = useQuery(GET_AVAILABLE_BENCHMARKS, {
    skip: !useRealBenchmarkData,
  });

  const [liveTotalValue, setLiveTotalValue] = useState(totalValue);
  const [liveTotalReturn, setLiveTotalReturn] = useState(totalReturn);
  const [liveTotalReturnPercent, setLiveTotalReturnPercent] = useState(totalReturnPercent);
  const [isLiveData, setIsLiveData] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const wsRef = useRef(webSocketService);

  const curValue = isLiveData ? liveTotalValue : totalValue;
  const curReturn = isLiveData ? liveTotalReturn : totalReturn;
  const curReturnPct = isLiveData ? liveTotalReturnPercent : totalReturnPercent;

  const positive = curReturn >= 0 && curReturnPct >= 0;
  const accent = positive ? palette.green : palette.red;
  const trendIcon = positive ? 'trending-up' : 'trending-down';

  // NEW: hydrate persisted toggle on mount
  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(PREF_SHOW_BENCH);
        if (raw != null) setShowBenchmark(raw === '1');
      } catch {}
    })();
  }, []);

  // NEW: persist on change
  useEffect(() => {
    AsyncStorage.setItem(PREF_SHOW_BENCH, showBenchmark ? '1' : '0').catch(() => {});
  }, [showBenchmark]);

  // === Series generation (stub) ===
  const pointsForTab = (t: Timeframe) => {
    switch (t) {
      case '1D': return 24;   // hourly-ish
      case '1W': return 7;
      case '1M': return 30;
      case '3M': return 13;   // weekly points
      case '1Y': return 12;   // monthly points
      case 'All': return 60;  // arbitrary
    }
  };

  const genPortfolioSeries = useCallback(
    (points: number) => {
      const series: number[] = [];
      const base = curValue;
      const vol = 0.012;
      const drift = positive ? 0.0003 : -0.0002;
      for (let i = 0; i < points; i++) {
        const noise = (Math.random() - 0.5) * vol;
        const v = base * (1 + drift * i + noise * (0.6 + 0.4 * Math.sin(i * 0.3)));
        series.push(Math.max(v, base * 0.85));
      }
      series[series.length - 1] = curValue;
      return series;
    },
    [curValue, positive]
  );

  const genBenchmarkSeries = useCallback(
    (points: number) => {
      // Use real benchmark data if available
      if (useRealBenchmarkData && benchmarkData?.benchmarkSeries) {
        const realValues = extractBenchmarkValues(benchmarkData.benchmarkSeries);
        if (realValues.length > 0) {
          return realValues;
        }
      }
      
      // Fallback to provided benchmark series
      if (benchmarkSeries && benchmarkSeries.length >= points) {
        return benchmarkSeries.slice(-points);
      }
      
      // Fallback to synthetic data
      const series: number[] = [];
      const base = curValue * 0.98; // start close to portfolio
      const vol = 0.007;
      const drift = 0.0002;
      for (let i = 0; i < points; i++) {
        const noise = (Math.random() - 0.5) * vol;
        const v = base * (1 + drift * i + noise * (0.5 + 0.3 * Math.sin(i * 0.25)));
        series.push(Math.max(v, base * 0.9));
      }
      series[series.length - 1] = curValue * 0.995; // finish near portfolio but not identical
      return series;
    },
    [benchmarkSeries, curValue, useRealBenchmarkData, benchmarkData]
  );

  const [history, setHistory] = useState<number[]>([]);
  const [bench, setBench] = useState<number[]>([]);

  useEffect(() => {
    setIsLoading(true);
    const pts = pointsForTab(tab);
    setHistory(genPortfolioSeries(pts));
    setBench(genBenchmarkSeries(pts));
    const tid = setTimeout(() => setIsLoading(false), 200);
    return () => clearTimeout(tid);
  }, [tab, genPortfolioSeries, genBenchmarkSeries]);

  // live updates push to tail (portfolio only here)
  useEffect(() => {
    wsRef.current.setCallbacks({
      onPortfolioUpdate: (p: PortfolioUpdate) => {
        setLiveTotalValue(p.totalValue);
        setLiveTotalReturn(p.totalReturn);
        setLiveTotalReturnPercent(p.totalReturnPercent);
        setIsLiveData(true);
        setHistory(prev => {
          const cap = pointsForTab(tab);
          const next = [...prev, p.totalValue];
          return next.length > cap ? next.slice(-cap) : next;
        });
      },
    });
    wsRef.current.connect();
    setTimeout(() => wsRef.current?.subscribeToPortfolio(), 600);
  }, [tab]);

  const minAll = useMemo(() => Math.min(...[(history.length ? Math.min(...history) : curValue), (showBenchmark && bench.length ? Math.min(...bench) : curValue)]), [history, bench, curValue, showBenchmark]);
  const maxAll = useMemo(() => Math.max(...[(history.length ? Math.max(...history) : curValue), (showBenchmark && bench.length ? Math.max(...bench) : curValue)]), [history, bench, curValue, showBenchmark]);

  // ---- Crosshair / Tooltip state ----
  const [pointer, setPointer] = useState<{ index: number; x: number; y: number; value: number } | null>(null);

  const chartWidth = width - 48;
  const chartHeight = 200;
  const pointCount = Math.max(1, history.length || 1);
  const stepX = pointCount > 1 ? chartWidth / (pointCount - 1) : 0;

  const clamp = (n: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, n));
  const indexForX = (x: number) => clamp(Math.round(x / stepX), 0, pointCount - 1);

  const panResponder = useMemo(
    () => PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt: GestureResponderEvent) => {
        const i = indexForX(evt.nativeEvent.locationX);
        const v = history[i] ?? curValue;
        setPointer({ index: i, x: i * stepX, y: 0, value: v });
      },
      onPanResponderMove: (evt: GestureResponderEvent, _gs: PanResponderGestureState) => {
        const i = indexForX(evt.nativeEvent.locationX);
        const v = history[i] ?? curValue;
        setPointer({ index: i, x: i * stepX, y: 0, value: v });
      },
      onPanResponderRelease: () => {},
      onPanResponderTerminate: () => {},
    }),
    [history, curValue, stepX, pointCount]
  );

  // period returns - use real benchmark data if available
  const pStart = history[0] ?? curValue;
  const pEnd = history[history.length - 1] ?? curValue;
  const pRetPct = ((pEnd - pStart) / pStart) * 100;
  
  // Use real benchmark performance if available
  const benchmarkSummary = useRealBenchmarkData && benchmarkData?.benchmarkSeries 
    ? getBenchmarkSummary(benchmarkData.benchmarkSeries)
    : null;
  
  const bStart = benchmarkSummary?.startValue ?? (bench[0] ?? pStart);
  const bEnd = benchmarkSummary?.endValue ?? (bench[bench.length - 1] ?? pEnd);
  const bRetPct = benchmarkSummary?.totalReturnPercent ?? (((bEnd - bStart) / bStart) * 100);
  const vsBenchmark = calculateAlpha(pRetPct, bRetPct); // + means outperformance

  // Datasets (portfolio + optional benchmark)
  const chartData = useMemo(
    () => ({
      labels: new Array(6).fill(''),
      datasets: [
        // Portfolio (accent)
        {
          data: history.length ? history : [curValue],
          color: () => accent,
          strokeWidth: 2.6,
        } as any,
        // Benchmark (faint)
        ...(showBenchmark
          ? [{
              data: bench.length ? bench : [curValue],
              color: (opacity = 1) => `${palette.bench}${Math.round(opacity * 200).toString(16).padStart(2, '0')}`,
              strokeWidth: 2,
            } as any]
          : []),
      ],
    }),
    [history, bench, curValue, accent, palette.bench, showBenchmark]
  );

  const chartConfig = useMemo(
    () => ({
      backgroundColor: palette.bg,
      backgroundGradientFrom: palette.bg,
      backgroundGradientTo: palette.bg,
      decimalPlaces: 0,
      color: () => accent,
      labelColor: () => palette.sub,
      style: { borderRadius: 12 },
      propsForDots: { r: '0' },
      propsForBackgroundLines: {
        strokeDasharray: '4 8',
        stroke: palette.grid,
        strokeWidth: 1,
      },
      // keep subtle fill so the main series stands out; benchmark inherits but line is faint
      fillShadowGradientFrom: accent,
      fillShadowGradientTo: accent,
      fillShadowGradientFromOpacity: 0.12,
      fillShadowGradientToOpacity: 0.02,
    }),
    [accent, palette]
  );

  const handleExplain = (what: string) => {
    setClickedElement(what);
    setShowEducationModal(true);
  };

  // Tooltip overlay (shows both series at pointer)
  const Decorator = () => {
    if (!pointer || pointCount < 2) return null;

    const x = pointer.x;
    const pVal = history[pointer.index] ?? curValue;
    const bVal = bench[pointer.index] ?? null;

    const range = maxAll - minAll || 1;
    const tP = clamp((pVal - minAll) / range, 0, 1);
    const yP = (1 - tP) * (chartHeight - 16) + 8;

    const tooltipW = 160;
    const tooltipH = showBenchmark ? 52 : 34;
    const tipX = clamp(x - tooltipW / 2, 6, chartWidth - tooltipW - 6);
    const tipY = clamp(yP - tooltipH - 10, 6, chartHeight - tooltipH - 6);

    const pctAt = (v: number, first: number) => ((v - first) / first) * 100;

    const pPctAt = pctAt(pVal, pStart);
    const bPctAt = bVal ? pctAt(bVal, bStart) : null;

    return (
      <Svg>
        {/* crosshair */}
        <SvgLine x1={x} y1={0} x2={x} y2={chartHeight} stroke={accent} strokeWidth={1.5} opacity={0.5} />
        <SvgCircle cx={x} cy={yP} r={3.5} fill={accent} />

        {/* tooltip box */}
        <SvgRect
          x={tipX}
          y={tipY}
          rx={8}
          ry={8}
          width={tooltipW}
          height={tooltipH}
          fill={palette.tooltipBg}
          stroke={palette.tooltipBorder}
          strokeWidth={1}
          opacity={0.98}
        />
        <SvgText x={tipX + 10} y={tipY + 18} fill={palette.tooltipText} fontSize="12" fontWeight="600">
          {`Portfolio: ${fmtUsd(pVal)} (${fmtPct(pPctAt)})`}
        </SvgText>
        {showBenchmark && bVal != null && (
          <SvgText x={tipX + 10} y={tipY + 36} fill={palette.tooltipText} fontSize="12">
            {`${useRealBenchmarkData ? formatBenchmarkSymbol(selectedBenchmarkSymbol) : selectedBenchmarkSymbol}: ${fmtUsd(bVal)} (${fmtPct(bPctAt!)})`}
          </SvgText>
        )}
      </Svg>
    );
  };

  return (
    <>
      <View style={[styles.card, { backgroundColor: palette.bg, borderColor: palette.border }]}>
        {/* Header */}
        <View style={styles.headerRow}>
          <View style={styles.titleWrap}>
            <Icon name="pie-chart" size={18} color={palette.accent} />
            <Text style={[styles.title, { color: palette.text }]}>Portfolio Performance</Text>
          </View>

          <View style={styles.tabsWrap}>
            {TABS.map(t => {
              const active = t === tab;
              return (
                <TouchableOpacity
                  key={t}
                  onPress={() => { setTab(t); setPointer(null); }}
                  accessibilityRole="button"
                  accessibilityLabel={`Timeframe ${t}`}
                  style={[
                    styles.chip,
                    {
                      backgroundColor: active ? palette.chipActiveBg : palette.chipBg,
                      borderColor: active ? palette.chipActiveBg : palette.border,
                    },
                  ]}
                >
                  <Text style={{ color: active ? palette.chipActiveText : palette.text, fontSize: 12, fontWeight: '600' }}>
                    {t}
                  </Text>
                </TouchableOpacity>
              );
            })}
            
            {/* Benchmark controls on the same line */}
            {useRealBenchmarkData && (
              <BenchmarkSelector
                selectedSymbol={selectedBenchmarkSymbol}
                onSymbolChange={setSelectedBenchmarkSymbol}
              />
            )}
            
            {/* Benchmark toggle */}
            <TouchableOpacity
              onPress={() => setShowBenchmark(v => !v)}
              accessibilityRole="button"
              accessibilityLabel={`Toggle ${selectedBenchmarkSymbol} benchmark`}
              style={[
                styles.benchToggle,
                { borderColor: palette.border, backgroundColor: showBenchmark ? `${palette.bench}22` : palette.chipBg },
              ]}
            >
              <View style={{ width: 10, height: 2, backgroundColor: palette.bench, marginRight: 6 }} />
              <Text style={{ color: palette.text, fontSize: 12, fontWeight: '600' }}>{selectedBenchmarkSymbol}</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* KPI Row */}
        <View style={styles.kpiRow}>
          {/* Total value */}
          <EducationalTooltip term="Total Value" explanation={getTermExplanation('Total Value')} position="top">
            <TouchableOpacity
              activeOpacity={0.8}
              onLongPress={() => Alert.alert('Total Value', fmtUsd(curValue))}
              onPress={() => { setClickedElement('totalValue'); setShowEducationModal(true); }}
            >
              <Text style={[styles.value, { color: palette.text }]}>{fmtCompactUsd(curValue)}</Text>
              <Text style={[styles.kpiLabel, { color: palette.sub }]}>Total Value</Text>
            </TouchableOpacity>
          </EducationalTooltip>

          {/* Return pill */}
          <EducationalTooltip term="Total Return" explanation={getTermExplanation('Total Return')} position="top">
            <View>
              <TouchableOpacity activeOpacity={0.8} onPress={() => { setClickedElement('return'); setShowEducationModal(true); }}>
                <View style={[styles.deltaPill, { backgroundColor: `${accent}1A`, borderColor: `${accent}33` }]}>
                  <Icon name={trendIcon} size={14} color={accent} />
                  <Text style={[styles.deltaText, { color: accent }]}>
                    {`${fmtUsd(Math.abs(curReturn))} (${fmtPct(curReturnPct)})`}
                  </Text>
                </View>
              </TouchableOpacity>

              {/* vs benchmark pill */}
              {showBenchmark && (
                <View style={[styles.vsPill, { borderColor: palette.border }]}>
                  <Text style={{ fontSize: 11, color: palette.sub, marginRight: 6 }}>
                    vs {useRealBenchmarkData ? formatBenchmarkSymbol(selectedBenchmarkSymbol) : selectedBenchmarkSymbol}
                  </Text>
                  <Text style={{ fontSize: 12, fontWeight: '700', color: vsBenchmark >= 0 ? palette.green : palette.red }}>
                    {fmtPct(vsBenchmark)}
                  </Text>
                </View>
              )}
            </View>
          </EducationalTooltip>
        </View>

        {/* Chart + Crosshair */}
        <View style={styles.chartShell} {...panResponder.panHandlers}>
          <LineChart
            data={chartData}
            width={chartWidth}
            height={200}
            chartConfig={chartConfig}
            bezier
            withDots={false}
            withShadow
            withInnerLines
            withOuterLines={false}
            withVerticalLines={false}
            withHorizontalLines
            style={styles.chart}
            fromZero={false}
            segments={4}
            onDataPointClick={(dp) => {
              setPointer({ index: dp.index, x: dp.x, y: dp.y, value: dp.value as number });
            }}
            decorator={Decorator}
          />
          <View style={StyleSheet.absoluteFillObject} pointerEvents="none" />
        </View>

        {/* NEW: Legend */}
        <View style={styles.legendRow}>
          <View style={styles.legendItem}>
            <View style={[styles.legendSwatch, { backgroundColor: accent }]} />
            <Text style={styles.legendText}>Portfolio</Text>
          </View>
          {showBenchmark && (
            <View style={styles.legendItem}>
              <View style={[styles.legendSwatch, { backgroundColor: palette.bench }]} />
              <Text style={styles.legendText}>
                {useRealBenchmarkData ? formatBenchmarkSymbol(selectedBenchmarkSymbol) : selectedBenchmarkSymbol}
              </Text>
            </View>
          )}
        </View>

        {/* Footer */}
        <View style={[styles.footer, { borderTopColor: palette.border }]}>
          <Text style={[styles.footerText, { color: palette.sub }]}>
            {isLoading ? 'Loading data…' : isLiveData ? 'Live data' : 'Recent data'} • Tap or drag to inspect
          </Text>
        </View>
      </View>

      <PortfolioEducationModal
        visible={showEducationModal}
        onClose={() => setShowEducationModal(false)}
        isPositive={curReturn >= 0 && curReturnPct >= 0}
        totalValue={curValue}
        totalReturn={curReturn}
        totalReturnPercent={curReturnPct}
        clickedElement={clickedElement}
      />
    </>
  );
}

const styles = StyleSheet.create({
  card: { marginHorizontal: 0, marginVertical: 8, borderRadius: 0, padding: 16, borderWidth: 0, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 4 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12, flexWrap: 'wrap' },
  titleWrap: { flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1, minWidth: 0 },
  title: { fontSize: 18, fontWeight: '700' },
  tabsWrap: { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap' },
  chip: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12, borderWidth: 1, minWidth: 36, alignItems: 'center' },
  benchToggle: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, borderWidth: 1, maxWidth: 120 },
  kpiRow: { marginTop: 4, marginBottom: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end' },
  value: { fontSize: 24, fontWeight: '700' },
  kpiLabel: { fontSize: 12, marginTop: 2, opacity: 0.7 },
  deltaPill: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, borderWidth: 1, alignSelf: 'flex-start' },
  vsPill: { marginTop: 4, alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 999, borderWidth: 1 },
  deltaText: { fontSize: 14, fontWeight: '700' },
  chartShell: { alignItems: 'center', marginTop: 4, marginBottom: 12 },
  chart: { borderRadius: 16 },
  // NEW: Legend styles
  legendRow: { flexDirection: 'row', gap: 16, justifyContent: 'center', alignItems: 'center', marginTop: 8, marginBottom: 4 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  legendSwatch: { width: 14, height: 4, borderRadius: 2 },
  legendText: { fontSize: 13, fontWeight: '500', opacity: 0.8 },
  footer: { marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: 'rgba(0,0,0,0.05)' },
  footerText: { fontSize: 13, textAlign: 'center', opacity: 0.6 },
});