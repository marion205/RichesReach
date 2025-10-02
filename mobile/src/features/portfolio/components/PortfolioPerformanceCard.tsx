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
import Icon from 'react-native-vector-icons/Feather';
import EducationalTooltip from '../../../components/common/EducationalTooltip';
import PortfolioEducationModal from './PortfolioEducationModal';
import { getTermExplanation } from '../../../shared/financialTerms';
import webSocketService, { PortfolioUpdate } from '../../../services/WebSocketService';

const { width } = Dimensions.get('window');

type Props = {
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  onPress?: () => void;
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
}: Props) {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  const palette = {
    bg: isDark ? '#111214' : '#FFFFFF',
    text: isDark ? '#F5F6F8' : '#1C1C1E',
    sub: isDark ? '#A1A7AF' : '#6B7280',
    border: isDark ? '#23262B' : '#E5E7EB',
    grid: isDark ? '#2A2E34' : '#EDF0F2',
    green: '#22C55E',
    red: '#EF4444',
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

  const generateSeries = useCallback(
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

  const pointsForTab = (t: Timeframe) => {
    switch (t) {
      case '1D': return 24;
      case '1W': return 7;
      case '1M': return 30;
      case '3M': return 13;
      case '1Y': return 12;
      case 'All': return 60;
    }
  };

  const [history, setHistory] = useState<number[]>([]);
  useEffect(() => {
    setIsLoading(true);
    setHistory(generateSeries(pointsForTab(tab)));
    const tid = setTimeout(() => setIsLoading(false), 200);
    return () => clearTimeout(tid);
  }, [tab, generateSeries]);

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

  const min = useMemo(() => Math.min(...(history.length ? history : [curValue])), [history, curValue]);
  const max = useMemo(() => Math.max(...(history.length ? history : [curValue])), [history, curValue]);

  // ---- Crosshair / Tooltip state ----
  const [pointer, setPointer] = useState<{
    index: number;
    x: number;
    y: number;
    value: number;
  } | null>(null);

  // map finger x → nearest data index
  const chartWidth = width - 48;
  const chartHeight = 200;
  const horizontalPadding = 0; // chart-kit internal padding is small; we keep 0 to keep math simple
  const pointCount = Math.max(1, history.length || 1);
  const stepX = pointCount > 1 ? (chartWidth - horizontalPadding) / (pointCount - 1) : 0;

  const clamp = (n: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, n));
  const indexForX = (x: number) => clamp(Math.round((x - horizontalPadding) / stepX), 0, pointCount - 1);

  // PanResponder to allow drag over the chart to move crosshair
  const panResponder = useMemo(
    () => PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt: GestureResponderEvent) => {
        const gx = evt.nativeEvent.locationX;
        const i = indexForX(gx);
        const v = history[i] ?? curValue;
        // y isn't strictly required, chart-kit computes it—approximate for tooltip anchoring:
        setPointer({ index: i, x: i * stepX, y: 0, value: v });
      },
      onPanResponderMove: (evt: GestureResponderEvent, _gs: PanResponderGestureState) => {
        const gx = evt.nativeEvent.locationX;
        const i = indexForX(gx);
        const v = history[i] ?? curValue;
        setPointer({ index: i, x: i * stepX, y: 0, value: v });
      },
      onPanResponderRelease: () => {},
      onPanResponderTerminate: () => {},
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [history, curValue, stepX, pointCount]
  );

  const chartData = useMemo(
    () => ({
      labels: new Array(6).fill(''),
      datasets: [
        {
          data: history.length ? history : [curValue],
          color: () => accent,
          strokeWidth: 2.5,
        } as any,
      ],
    }),
    [history, curValue, accent]
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
      fillShadowGradientFrom: accent,
      fillShadowGradientTo: accent,
      fillShadowGradientFromOpacity: 0.15,
      fillShadowGradientToOpacity: 0.02,
    }),
    [accent, palette]
  );

  const handleExplain = (what: string) => {
    setClickedElement(what);
    setShowEducationModal(true);
  };

  // Tooltip rendering in the chart overlay
  const Decorator = () => {
    if (!pointer || pointCount < 2) return null;

    const x = pointer.x;
    // approximate y position relative to min/max for tooltip anchoring:
    const v = pointer.value;
    const range = max - min || 1;
    const t = clamp((v - min) / range, 0, 1);
    const y = (1 - t) * (chartHeight - 16) + 8; // some padding

    const tooltipW = 120;
    const tooltipH = 34;
    const tipX = clamp(x - tooltipW / 2, 6, chartWidth - tooltipW - 6);
    const tipY = clamp(y - tooltipH - 10, 6, chartHeight - tooltipH - 6);

    return (
      <Svg>
        {/* vertical crosshair */}
        <SvgLine x1={x} y1={0} x2={x} y2={chartHeight} stroke={accent} strokeWidth={1.5} opacity={0.5} />
        {/* focus dot */}
        <SvgCircle cx={x} cy={y} r={3.5} fill={accent} />
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
          y={tipY + 20}
          fill={palette.tooltipText}
          fontSize="12"
          fontWeight="600"
        >
          {`${fmtUsd(v)}  (${fmtPct(((v - history[0]) / history[0]) * 100 || 0)})`}
        </SvgText>
      </Svg>
    );
  };

  return (
    <>
      <View style={[styles.card, { backgroundColor: palette.bg, borderColor: palette.border }]}>
        {/* Header */}
        <View style={styles.headerRow}>
          <View style={styles.titleWrap}>
            <Icon name="pie-chart" size={18} color={accent} />
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
          </View>
        </View>

        {/* KPI Row */}
        <View style={styles.kpiRow}>
          <EducationalTooltip term="Total Value" explanation={getTermExplanation('Total Value')} position="top">
            <TouchableOpacity
              activeOpacity={0.8}
              onLongPress={() => Alert.alert('Total Value', fmtUsd(curValue))}
              onPress={() => handleExplain('totalValue')}
            >
              <Text style={[styles.value, { color: palette.text }]}>{fmtCompactUsd(curValue)}</Text>
              <Text style={[styles.kpiLabel, { color: palette.sub }]}>Total Value</Text>
            </TouchableOpacity>
          </EducationalTooltip>

          <EducationalTooltip term="Total Return" explanation={getTermExplanation('Total Return')} position="top">
            <TouchableOpacity activeOpacity={0.8} onPress={() => handleExplain('return')}>
              <View style={[styles.deltaPill, { backgroundColor: `${accent}1A`, borderColor: `${accent}33` }]}>
                <Icon name={trendIcon} size={14} color={accent} />
                <Text style={[styles.deltaText, { color: accent }]}>
                  {`${fmtUsd(Math.abs(curReturn))} (${fmtPct(curReturnPct)})`}
                </Text>
              </View>
              <Text style={[styles.kpiLabel, { color: palette.sub, marginTop: 6 }]}>Since period start</Text>
            </TouchableOpacity>
          </EducationalTooltip>
        </View>

        {/* Chart + Crosshair */}
        <View
          style={styles.chartShell}
          // PanResponder overlay to support drag/hover
          {...panResponder.panHandlers}
        >
          <LineChart
            data={chartData}
            width={chartWidth}
            height={chartHeight}
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
            // tap to snap
            onDataPointClick={(dp) => {
              setPointer({ index: dp.index, x: dp.x, y: dp.y, value: dp.value as number });
            }}
            // draw our overlay
            decorator={Decorator}
          />
          <View style={StyleSheet.absoluteFillObject} pointerEvents="none" />
        </View>

        {/* Range hint */}
        <View style={styles.rangeRow}>
          <Text style={[styles.rangeText, { color: palette.sub }]}>Low {fmtCompactUsd(min)}</Text>
          <Text style={[styles.rangeText, { color: palette.sub }]}>High {fmtCompactUsd(max)}</Text>
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
        isPositive={positive}
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
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  titleWrap: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  title: { fontSize: 16, fontWeight: '700' },
  tabsWrap: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  chip: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12, borderWidth: 1 },
  kpiRow: { marginTop: 4, marginBottom: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end' },
  value: { fontSize: 28, fontWeight: '800' },
  kpiLabel: { fontSize: 12, marginTop: 2 },
  deltaPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  deltaText: { fontSize: 14, fontWeight: '700' },
  chartShell: { alignItems: 'center', marginTop: 4 },
  chart: { borderRadius: 12 },
  rangeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '92%',
    alignSelf: 'center',
    marginTop: 6,
  },
  rangeText: {
    fontSize: 11,
  },
  footer: { marginTop: 10, paddingTop: 10, borderTopWidth: 1 },
  footerText: { fontSize: 12, textAlign: 'center' },
});
