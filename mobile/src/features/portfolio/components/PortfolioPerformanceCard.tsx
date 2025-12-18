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
import Svg, {
  Line as SvgLine,
  Circle as SvgCircle,
  Rect as SvgRect,
  Text as SvgText,
} from 'react-native-svg';
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
  getBenchmarkColor,
} from '../../../graphql/benchmarkQueries';
import type {
  BenchmarkSeriesType,
  ExtendedQueryBenchmarkSeriesQuery,
  ExtendedQueryBenchmarkSeriesQueryVariables,
  ExtendedQueryAvailableBenchmarksQuery,
} from '../../../generated/graphql';
import BenchmarkSelector from './BenchmarkSelector';
import { computeYDomain, getPeriodReturnLabel } from '../utils/chartUtils';
import logger from '../../../utils/logger';
// Conditionally import Skia chart - only available in development builds, not Expo Go
let InnovativeChart: any = null;
let isSkiaAvailable = false;
try {
  InnovativeChart = require('../../../components/charts/InnovativeChartSkia').default;
  // Check if Skia library is actually available (same check as in InnovativeChartSkia.tsx)
  try {
    const SkiaComponents = require('@shopify/react-native-skia');
    // Check for the actual Skia components (Canvas, Path, Skia) like the component does
    const { Canvas, Path, Skia } = SkiaComponents || {};
    isSkiaAvailable = !!(SkiaComponents && Canvas && Path && Skia);
    if (!isSkiaAvailable) {
      logger.warn('Skia components not fully available - Canvas, Path, or Skia missing');
    }
  } catch (e) {
    // Skia library not available
    isSkiaAvailable = false;
    logger.warn(
      '@shopify/react-native-skia not installed. Install with: npm install @shopify/react-native-skia'
    );
  }
} catch (e) {
  // Skia not available - will use fallback chart
  logger.warn('Skia chart component not available, using fallback chart');
  isSkiaAvailable = false;
}

const { width } = Dimensions.get('window');
const PREF_SHOW_BENCH = 'rr.pref.show_benchmark'; // NEW

type Props = {
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  benchmarkSymbol?: string; // e.g., 'SPY'
  benchmarkSeries?: number[]; // optional: pass real benchmark series (same length as current timeframe)
  useRealBenchmarkData?: boolean; // whether to fetch real benchmark data from GraphQL
};

const TABS = ['1D', '1W', '1M', '3M', '1Y', 'All'] as const;
type Timeframe = (typeof TABS)[number];

const fmtCompactUsd = (n: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(n || 0);

const fmtUsd = (n: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(n || 0);

const fmtPct = (p: number) => `${(p || 0) >= 0 ? '+' : ''}${(p || 0).toFixed(2)}%`;

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
    bench: getBenchmarkColor(selectedBenchmarkSymbol, isDark), // benchmark color based on selected symbol
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
  // Only enable advanced chart if Skia is available
  const [useAdvancedChart, setUseAdvancedChart] = useState<boolean>(false); // Start with regular chart, can switch to advanced

  // GraphQL queries for benchmark data with error handling
  // ✅ Now using typed queries
  const {
    data: benchmarkData,
    loading: benchmarkLoading,
    error: benchmarkError,
  } = useQuery<ExtendedQueryBenchmarkSeriesQuery, ExtendedQueryBenchmarkSeriesQueryVariables>(
    GET_BENCHMARK_SERIES,
    {
      variables: { symbol: selectedBenchmarkSymbol || '', timeframe: tab },
      skip: !useRealBenchmarkData || !showBenchmark,
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all', // Continue rendering even if query has errors
      onError: error => {
        logger.warn('Benchmark series query error:', error);
      },
    }
  );

  const { data: availableBenchmarksData, error: availableBenchmarksError } = useQuery<
    ExtendedQueryAvailableBenchmarksQuery
  >(GET_AVAILABLE_BENCHMARKS, {
    skip: !useRealBenchmarkData,
    errorPolicy: 'all', // Continue rendering even if query has errors
    onError: error => {
      logger.warn('Available benchmarks query error:', error);
    },
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
        if (raw != null) {
          setShowBenchmark(raw === '1');
        }
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
      case '1D':
        return 24; // hourly-ish
      case '1W':
        return 7;
      case '1M':
        return 30;
      case '3M':
        return 13; // weekly points
      case '1Y':
        return 12; // monthly points
      case 'All':
        return 60; // arbitrary
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
    const newHistory = genPortfolioSeries(pts);
    const newBench = genBenchmarkSeries(pts);
    setHistory(newHistory);
    setBench(newBench);
    logger.log('📈 Generated portfolio history:', newHistory.length, 'points');
    const tid = setTimeout(() => setIsLoading(false), 200);
    return () => clearTimeout(tid);
  }, [tab, genPortfolioSeries, genBenchmarkSeries]);

  // Debug AR chart state - moved after innovativeChartSeries definition

  // Transform data for InnovativeChartSkia (advanced AR chart)
  const innovativeChartSeries = useMemo(() => {
    if (!history.length) {
      return [];
    }
    const now = Date.now();
    const pointsPerDay = Math.max(1, Math.floor(history.length / 30)); // Approximate days
    return history.map((price, idx) => ({
      t: now - (history.length - idx - 1) * ((24 * 60 * 60 * 1000) / pointsPerDay),
      price,
    }));
  }, [history]);

  // Debug AR chart state
  useEffect(() => {
    if (useAdvancedChart) {
      logger.log('🎯 AR Chart Mode Active');
      logger.log('  - History points:', history.length);
      logger.log('  - InnovativeChartSeries points:', innovativeChartSeries.length);
      logger.log('  - InnovativeChart available:', !!InnovativeChart);
      logger.log('  - Skia available:', isSkiaAvailable);
      if (innovativeChartSeries.length > 0) {
        logger.log('  - Sample series data:', innovativeChartSeries.slice(0, 3));
      }
    }
  }, [useAdvancedChart, history.length, innovativeChartSeries.length]);

  const innovativeChartBenchmark = useMemo(() => {
    if (!showBenchmark || !bench.length) {
      return [];
    }
    const now = Date.now();
    const pointsPerDay = Math.max(1, Math.floor(bench.length / 30));
    return bench.map((price, idx) => ({
      t: now - (bench.length - idx - 1) * ((24 * 60 * 60 * 1000) / pointsPerDay),
      price,
    }));
  }, [bench, showBenchmark]);

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

  // Use chartUtils to compute proper y-domain (prevents -100% issues)
  const chartPoints = useMemo(() => {
    const allPoints: { t: number; v: number }[] = [];
    // Portfolio points
    history.forEach((val, idx) => {
      allPoints.push({ t: idx, v: val });
    });
    // Benchmark points
    if (showBenchmark && bench.length) {
      bench.forEach((val, idx) => {
        allPoints.push({ t: idx, v: val });
      });
    }
    // If no history, use current value
    if (!allPoints.length) {
      allPoints.push({ t: 0, v: curValue });
    }
    return allPoints;
  }, [history, bench, curValue, showBenchmark]);

  const [yMin, yMax] = useMemo(() => {
    return computeYDomain(chartPoints, false); // false = dollar values, not percentages
  }, [chartPoints]);

  const minAll = yMin;
  const maxAll = yMax;

  // ---- Crosshair / Tooltip state ----
  const [pointer, setPointer] = useState<{
    index: number;
    x: number;
    y: number;
    value: number;
  } | null>(null);

  const chartWidth = width;
  const chartHeight = 200;
  const pointCount = Math.max(1, history.length || 1);
  const stepX = pointCount > 1 ? chartWidth / (pointCount - 1) : 0;

  const clamp = (n: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, n));
  const indexForX = (x: number) => clamp(Math.round(x / stepX), 0, pointCount - 1);

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: () => true,
        onPanResponderGrant: () => {
          // Tooltips disabled
        },
        onPanResponderMove: () => {
          // Tooltips disabled
        },
        onPanResponderRelease: () => {
          setPointer(null);
        },
        onPanResponderTerminate: () => {
          setPointer(null);
        },
      }),
    [history, curValue, stepX, pointCount]
  );

  // period returns - use real benchmark data if available
  // Prevent -100% issues when start value is 0 or very small
  const pStart = history[0] ?? curValue;
  const pEnd = history[history.length - 1] ?? curValue;
  const pRetPct = pStart && pStart > 0 ? ((pEnd - pStart) / pStart) * 100 : 0;

  // Use real benchmark performance if available
  const benchmarkSummary =
    useRealBenchmarkData && benchmarkData?.benchmarkSeries
      ? getBenchmarkSummary(benchmarkData.benchmarkSeries)
      : null;

  const bStart = benchmarkSummary?.startValue ?? bench[0] ?? pStart;
  const bEnd = benchmarkSummary?.endValue ?? bench[bench.length - 1] ?? pEnd;
  // Prevent division by zero in benchmark return calculation
  const bRetPct =
    benchmarkSummary?.totalReturnPercent ??
    (bStart && bStart > 0 ? ((bEnd - bStart) / bStart) * 100 : 0);
  const vsBenchmark = calculateAlpha(pRetPct, bRetPct); // + means outperformance

  // Datasets (portfolio + optional benchmark)
  const chartData = useMemo(() => {
    // Ensure we always have at least 2 data points for the chart to render
    const portfolioData = history.length >= 2 
      ? history 
      : history.length === 1 
        ? [history[0] * 0.99, history[0]] // Create a second point slightly lower
        : [curValue * 0.99, curValue]; // Fallback: create 2 points from current value
    
    const benchmarkData = bench.length >= 2
      ? bench
      : bench.length === 1
        ? [bench[0] * 0.99, bench[0]]
        : [curValue * 0.98, curValue * 0.99];
    
    const pointCount = Math.max(portfolioData.length, 6);
    
    return {
      labels: new Array(pointCount).fill(''),
      datasets: [
        // Portfolio (accent)
        {
          data: portfolioData,
          color: () => accent,
          strokeWidth: 2.6,
        } as any,
        // Benchmark (faint)
        ...(showBenchmark
          ? [
              {
                data: benchmarkData,
                color: (opacity = 1) =>
                  `${palette.bench}${Math.round(opacity * 200)
                    .toString(16)
                    .padStart(2, '0')}`,
                strokeWidth: 2,
              } as any,
            ]
          : []),
      ],
    };
  }, [history, bench, curValue, accent, palette.bench, showBenchmark]);

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
      // Format y-axis labels to prevent confusing scales
      formatYLabel: (value: string) => {
        const numValue = Number(value);
        if (isNaN(numValue)) {
          return value;
        }
        // Handle very small values
        if (Math.abs(numValue) < 0.01) {
          return '$0';
        }
        if (numValue >= 1000000) {
          return `$${(numValue / 1000000).toFixed(1)}M`;
        }
        if (numValue >= 1000) {
          return `$${(numValue / 1000).toFixed(1)}K`;
        }
        return `$${numValue.toFixed(0)}`;
      },
    }),
    [accent, palette]
  );

  const handleExplain = (what: string) => {
    setClickedElement(what);
    setShowEducationModal(true);
  };

  // Tooltip overlay (shows both series at pointer) - DISABLED
  const Decorator = () => {
    // Tooltips disabled - always return null
    return null;
    if (!pointer || pointCount < 2) {
      return null;
    }

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
        <SvgLine
          x1={x}
          y1={0}
          x2={x}
          y2={chartHeight}
          stroke={accent}
          strokeWidth={1.5}
          opacity={0.5}
        />
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
        <SvgText
          x={tipX + 10}
          y={tipY + 18}
          fill={palette.tooltipText}
          fontSize="12"
          fontWeight="600"
        >
          {`Portfolio: ${fmtUsd(pVal)} (${fmtPct(pPctAt)})`}
        </SvgText>
        {showBenchmark && bVal != null && (
          <SvgText x={tipX + 10} y={tipY + 36} fill={palette.tooltipText} fontSize="12">
            {`${
              useRealBenchmarkData
                ? formatBenchmarkSymbol(selectedBenchmarkSymbol)
                : selectedBenchmarkSymbol
            }: ${fmtUsd(bVal)} (${fmtPct(bPctAt!)})`}
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
            <Text style={[styles.title, { color: palette.text }]} numberOfLines={1}>
              Portfolio Performance
            </Text>
          </View>

          <View style={styles.tabsWrap}>
            {TABS.map(t => {
              const active = t === tab;
              return (
                <TouchableOpacity
                  key={t}
                  onPress={() => {
                    setTab(t);
                    setPointer(null);
                  }}
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
                  <Text
                    style={{
                      color: active ? palette.chipActiveText : palette.text,
                      fontSize: 12,
                      fontWeight: '600',
                    }}
                  >
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
                {
                  borderColor: palette.border,
                  backgroundColor: showBenchmark ? `${palette.bench}22` : palette.chipBg,
                },
              ]}
            >
              <View
                style={{
                  width: 10,
                  height: 2,
                  backgroundColor: palette.bench,
                  marginRight: 6,
                }}
              />
              <Text style={{ color: palette.text, fontSize: 12, fontWeight: '600' }}>
                {selectedBenchmarkSymbol}
              </Text>
            </TouchableOpacity>

            {/* Chart Type Toggle - Switch between Regular and Advanced AR Chart */}
            <TouchableOpacity
              onPress={() => {
                if (!isSkiaAvailable && !useAdvancedChart) {
                  Alert.alert(
                    'AR Chart Requires Rebuild',
                    'The AR chart requires @shopify/react-native-skia which needs a rebuild to work. Please rebuild your development build using: npm run build:dev:ios or npm run build:dev:android',
                    [{ text: 'OK' }]
                  );
                  return;
                }
                logger.log('🔄 Toggling AR chart, current state:', useAdvancedChart);
                logger.log('📊 History length:', history.length);
                logger.log('📊 InnovativeChartSeries length:', innovativeChartSeries.length);
                logger.log('📊 InnovativeChart available:', !!InnovativeChart);
                logger.log('📊 Skia available:', isSkiaAvailable);
                setUseAdvancedChart(v => !v);
              }}
              accessibilityRole="button"
              accessibilityLabel={
                useAdvancedChart ? 'Switch to regular chart' : 'Switch to advanced AR chart'
              }
              style={[
                styles.chartTypeToggle,
                {
                  borderColor: palette.border,
                  backgroundColor: useAdvancedChart ? `${palette.accent}22` : palette.chipBg,
                  marginLeft: 8,
                  opacity: isSkiaAvailable ? 1 : 0.6,
                },
              ]}
            >
              <Icon
                name={useAdvancedChart ? 'zap' : 'bar-chart-2'}
                size={14}
                color={useAdvancedChart ? palette.accent : palette.text}
                style={{ marginRight: 4 }}
              />
              <Text
                style={{
                  color: useAdvancedChart ? palette.accent : palette.text,
                  fontSize: 12,
                  fontWeight: '600',
                }}
              >
                {useAdvancedChart ? 'AR' : 'Chart'}
              </Text>
              {!isSkiaAvailable && (
                <View
                  style={{
                    position: 'absolute',
                    top: -2,
                    right: -2,
                    width: 6,
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: '#EF4444',
                  }}
                />
              )}
            </TouchableOpacity>
          </View>
        </View>

        {/* KPI Row */}
        <View style={styles.kpiRow}>
          {/* Total value */}
          <View style={styles.kpiLeft}>
            <EducationalTooltip
              term="Total Value"
              explanation={getTermExplanation('Total Value')}
              position="top"
              hideExternalIcon={true}
            >
              <TouchableOpacity
                activeOpacity={0.8}
                onLongPress={() => Alert.alert('Total Value', fmtUsd(curValue))}
                onPress={() => {
                  setClickedElement('totalValue');
                  setShowEducationModal(true);
                }}
              >
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Text
                    style={[styles.value, { color: palette.text }]}
                    numberOfLines={1}
                    adjustsFontSizeToFit={true}
                    minimumFontScale={0.8}
                  >
                    {fmtCompactUsd(curValue)}
                  </Text>
                  <TouchableOpacity
                    onPress={() => {
                      setClickedElement('totalValue');
                      setShowEducationModal(true);
                    }}
                    activeOpacity={0.7}
                    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                  >
                    <View style={{
                      width: 16,
                      height: 16,
                      borderRadius: 8,
                      backgroundColor: '#007AFF',
                      justifyContent: 'center',
                      alignItems: 'center',
                    }}>
                      <Icon name="info" size={10} color="#FFFFFF" />
                    </View>
                  </TouchableOpacity>
                </View>
                <Text style={[styles.kpiLabel, { color: palette.sub }]}>Total Value</Text>
              </TouchableOpacity>
            </EducationalTooltip>
          </View>

          {/* Return pill */}
          <View style={styles.kpiRight}>
            <EducationalTooltip
              term="Total Return"
              explanation={getTermExplanation('Total Return')}
              position="top"
            >
              <View>
                <TouchableOpacity
                  activeOpacity={0.8}
                  onPress={() => {
                    setClickedElement('return');
                    setShowEducationModal(true);
                  }}
                >
                  <View
                    style={[
                      styles.deltaPill,
                      {
                        backgroundColor: `${accent}1A`,
                        borderColor: `${accent}33`,
                      },
                    ]}
                  >
                    <Icon name={trendIcon} size={12} color={accent} />
                    <Text style={[styles.deltaText, { color: accent }]} numberOfLines={1}>
                      {`${fmtUsd(Math.abs(curReturn))} (${fmtPct(curReturnPct)})`}
                    </Text>
                  </View>
                </TouchableOpacity>

                {/* vs benchmark pill */}
                {showBenchmark && (
                  <View style={[styles.vsPill, { borderColor: palette.border }]}>
                    <Text
                      style={{
                        fontSize: 10,
                        color: palette.sub,
                        marginRight: 4,
                      }}
                    >
                      vs{' '}
                      {useRealBenchmarkData
                        ? formatBenchmarkSymbol(selectedBenchmarkSymbol)
                        : selectedBenchmarkSymbol}
                    </Text>
                    <Text
                      style={{
                        fontSize: 11,
                        fontWeight: '700',
                        color: vsBenchmark >= 0 ? palette.green : palette.red,
                      }}
                    >
                      {fmtPct(vsBenchmark)}
                    </Text>
                  </View>
                )}
              </View>
            </EducationalTooltip>
          </View>
        </View>

        {/* Chart + Crosshair - Advanced AR Chart or Regular Chart */}
        <View style={styles.chartShell}>
          {useAdvancedChart ? (
            innovativeChartSeries.length > 0 && InnovativeChart && isSkiaAvailable ? (
              <InnovativeChart
                series={innovativeChartSeries}
                benchmarkData={innovativeChartBenchmark}
                costBasis={curValue - curReturn}
                palette={{
                  bg: palette.bg,
                  grid: palette.grid,
                  price: accent,
                  text: palette.text,
                  card: palette.bg,
                  moneyGreen: palette.green,
                  moneyRed: palette.red,
                }}
                height={chartHeight}
                margin={16}
              />
            ) : (
              <View
                style={{
                  flex: 1,
                  justifyContent: 'center',
                  alignItems: 'center',
                  padding: 20,
                  minHeight: chartHeight,
                }}
              >
                <Text
                  style={{
                    color: palette.sub,
                    fontSize: 14,
                    textAlign: 'center',
                    marginBottom: 8,
                  }}
                >
                  {!isSkiaAvailable
                    ? 'AR Chart requires React Native Skia'
                    : innovativeChartSeries.length === 0
                    ? 'Loading chart data...'
                    : 'Chart unavailable'}
                </Text>
                {!isSkiaAvailable && (
                  <>
                    <Text
                      style={{
                        color: palette.sub,
                        fontSize: 12,
                        textAlign: 'center',
                        marginTop: 8,
                      }}
                    >
                      The advanced AR chart requires @shopify/react-native-skia library.
                    </Text>
                    <Text
                      style={{
                        color: palette.sub,
                        fontSize: 12,
                        textAlign: 'center',
                        marginTop: 4,
                      }}
                    >
                      This is not available in Expo Go. Use a development build instead.
                    </Text>
                  </>
                )}
                {innovativeChartSeries.length === 0 && (
                  <Text
                    style={{
                      color: palette.sub,
                      fontSize: 12,
                      textAlign: 'center',
                      marginTop: 8,
                    }}
                  >
                    History data: {history.length} points
                  </Text>
                )}
              </View>
            )
          ) : (
            <View {...panResponder.panHandlers}>
              <LineChart
                data={chartData}
                width={chartWidth}
                height={200}
                chartConfig={chartConfig}
                bezier
                withDots={false}
                withShadow={false}
                withInnerLines
                withOuterLines={false}
                withVerticalLines={false}
                withHorizontalLines
                style={styles.chart}
                fromZero={false}
                segments={4}
                yAxisInterval={1}
                onDataPointClick={dp => {
                  setPointer({
                    index: dp.index,
                    x: dp.x,
                    y: dp.y,
                    value: dp.value as number,
                  });
                }}
              />
              <TouchableOpacity
                style={StyleSheet.absoluteFillObject}
                activeOpacity={1}
                onPress={() => setPointer(null)}
                onPressIn={() => setPointer(null)}
                pointerEvents="box-none"
              />
            </View>
          )}
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
                {useRealBenchmarkData
                  ? formatBenchmarkSymbol(selectedBenchmarkSymbol)
                  : selectedBenchmarkSymbol}
              </Text>
            </View>
          )}
        </View>

        {/* Footer */}
        <View style={[styles.footer, { borderTopColor: palette.border }]}>
          <Text style={[styles.footerText, { color: palette.sub }]}>
            {isLoading ? 'Loading data…' : isLiveData ? 'Live data' : 'Recent data'} • Tap or drag
            to inspect
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
  card: {
    marginHorizontal: 0,
    marginVertical: 8,
    borderRadius: 0,
    padding: 16,
    paddingHorizontal: 16,
    borderWidth: 0,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
    flexWrap: 'wrap',
  },
  titleWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexShrink: 1,
    marginRight: 8,
  },
  title: { fontSize: 18, fontWeight: '700', flexShrink: 1 },
  tabsWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flexWrap: 'wrap',
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
    minWidth: 36,
    alignItems: 'center',
  },
  benchToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    maxWidth: 120,
  },
  chartTypeToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
  },
  kpiRow: {
    marginTop: 4,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    paddingHorizontal: 0,
    gap: 16, // Increased gap to prevent overlap
  },
  kpiLeft: {
    flex: 1,
    minWidth: 0,
    maxWidth: '55%', // Limit width to prevent wrapping
    marginRight: 12,
    paddingRight: 20, // Extra padding to account for EducationalTooltip info icon (right: -16)
    flexShrink: 1,
  },
  kpiRight: {
    flexShrink: 0,
    alignItems: 'flex-end',
    marginLeft: 12,
    paddingLeft: 4, // Small padding for the return pill
  },
  value: {
    fontSize: 20,
    fontWeight: '700',
    flexShrink: 0, // Prevent wrapping
  },
  kpiLabel: {
    fontSize: 12,
    marginTop: 2,
    opacity: 0.7,
  },
  deltaPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
    borderWidth: 1,
    alignSelf: 'flex-end',
    flexShrink: 0,
  },
  vsPill: {
    marginTop: 3,
    alignSelf: 'flex-end',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 999,
    borderWidth: 1,
    flexShrink: 0,
  },
  deltaText: { fontSize: 12, fontWeight: '700' },
  chartShell: { alignItems: 'center', marginTop: 4, marginBottom: 12, minHeight: 200, marginHorizontal: -16 },
  chart: { borderRadius: 0, marginVertical: 8 },
  // NEW: Legend styles
  legendRow: {
    flexDirection: 'row',
    gap: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 4,
  },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  legendSwatch: { width: 14, height: 4, borderRadius: 2 },
  legendText: { fontSize: 13, fontWeight: '500', opacity: 0.8 },
  footer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.05)',
  },
  footerText: { fontSize: 13, textAlign: 'center', opacity: 0.6 },
});
