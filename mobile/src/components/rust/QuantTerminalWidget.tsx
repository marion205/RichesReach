/**
 * Quant Terminal Widget
 * Phase 3: Vol surface heatmaps, edge decay curves, regime timeline, portfolio DNA
 */

import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';
import Svg, { Rect, Text as SvgText } from 'react-native-svg';
import { API_RUST_BASE } from '../../config/api';

const { width } = Dimensions.get('window');

interface VolSurfaceHeatmap {
  symbol: string;
  strikes: number[];
  expirations: string[];
  iv_matrix: number[][];
  timestamp: string;
}

interface EdgeDecayCurve {
  strategy_name: string;
  symbol: string;
  time_points: string[];
  edge_values: number[];
  confidence_values: number[];
  decay_rate: number;
  half_life_days: number;
  timestamp: string;
}

interface RegimeEvent {
  date: string;
  regime: string;
  headline: string;
  confidence: number;
  market_impact: number;
}

interface RegimeTimeline {
  start_date: string;
  end_date: string;
  events: RegimeEvent[];
  transitions: Array<{
    from: string;
    to: string;
    date: string;
    duration_days: number;
    volatility_spike: number;
  }>;
  timestamp: string;
}

interface PortfolioDNA {
  user_id: string;
  fingerprint: {
    win_rate: number;
    profit_factor: number;
    avg_holding_period_days: number;
    preferred_iv_regime: string;
    preferred_dte_range: string;
    risk_tolerance: number;
    strategy_preferences: Record<string, number>;
    sharpe_ratio: number;
    max_drawdown: number;
    total_trades: number;
    best_performing_strategy: string;
    worst_performing_strategy: string;
  };
  archetype: string;
  archetype_breakdown: Record<string, number>;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  timestamp: string;
}

interface QuantTerminalWidgetProps {
  symbol?: string;
  strategyName?: string;
  userId?: string;
}

export default function QuantTerminalWidget({
  symbol = 'AAPL',
  strategyName = 'long_call',
  userId = 'user_123',
}: QuantTerminalWidgetProps) {
  const [showVolSurface, setShowVolSurface] = useState(false);
  const [showEdgeDecay, setShowEdgeDecay] = useState(false);
  const [showRegimeTimeline, setShowRegimeTimeline] = useState(false);
  const [showPortfolioDNA, setShowPortfolioDNA] = useState(false);

  const [volSurface, setVolSurface] = useState<VolSurfaceHeatmap | null>(null);
  const [edgeDecay, setEdgeDecay] = useState<EdgeDecayCurve | null>(null);
  const [regimeTimeline, setRegimeTimeline] = useState<RegimeTimeline | null>(null);
  const [portfolioDNA, setPortfolioDNA] = useState<PortfolioDNA | null>(null);
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');

  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Prepare edge decay chart data
  const edgeDecayChartData = useMemo(() => {
    if (!edgeDecay) return null;

    return {
      labels: edgeDecay.time_points.map((tp, idx) => {
        // Show only first, middle, and last labels to avoid crowding
        if (idx === 0 || idx === Math.floor(edgeDecay.time_points.length / 2) || idx === edgeDecay.time_points.length - 1) {
          const date = new Date(tp);
          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }
        return '';
      }),
      datasets: [
        {
          data: edgeDecay.edge_values.map(v => Math.max(0, v * 100)), // Convert to percentage
          color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
          strokeWidth: 2,
        },
      ],
    };
  }, [edgeDecay]);

  // Heatmap component
  const VolSurfaceHeatmap = ({ data }: { data: VolSurfaceHeatmap }) => {
    const heatmapWidth = width - 80;
    const heatmapHeight = 200;
    const cellPadding = 2;
    const labelWidth = 50;
    const labelHeight = 20;
    const chartWidth = heatmapWidth - labelWidth;
    const chartHeight = heatmapHeight - labelHeight;

    const numStrikes = data.strikes.length;
    const numExpirations = data.expirations.length;

    const cellWidth = (chartWidth - cellPadding * (numStrikes - 1)) / numStrikes;
    const cellHeight = (chartHeight - cellPadding * (numExpirations - 1)) / numExpirations;

    // Normalize IV values for color mapping (0-1 range)
    const allIVs = data.iv_matrix.flat();
    const minIV = Math.min(...allIVs);
    const maxIV = Math.max(...allIVs);
    const ivRange = maxIV - minIV || 1;

    const getColor = (iv: number) => {
      const normalized = (iv - minIV) / ivRange;
      // Color gradient: blue (low) -> green -> yellow -> red (high)
      if (normalized < 0.33) {
        const t = normalized / 0.33;
        const r = Math.round(0 + t * 0);
        const g = Math.round(100 + t * 155);
        const b = Math.round(255 - t * 155);
        return `rgb(${r}, ${g}, ${b})`;
      } else if (normalized < 0.66) {
        const t = (normalized - 0.33) / 0.33;
        const r = Math.round(0 + t * 255);
        const g = Math.round(255 - t * 100);
        const b = Math.round(0);
        return `rgb(${r}, ${g}, ${b})`;
      } else {
        const t = (normalized - 0.66) / 0.34;
        const r = 255;
        const g = Math.round(155 - t * 155);
        const b = 0;
        return `rgb(${r}, ${g}, ${b})`;
      }
    };

    return (
      <View style={styles.heatmapContainer}>
        <Svg width={heatmapWidth} height={heatmapHeight}>
          {/* Render heatmap cells */}
          {data.iv_matrix.map((row, expIdx) =>
            row.map((iv, strikeIdx) => {
              const x = labelWidth + strikeIdx * (cellWidth + cellPadding);
              const y = labelHeight + expIdx * (cellHeight + cellPadding);
              return (
                <Rect
                  key={`cell-${expIdx}-${strikeIdx}`}
                  x={x}
                  y={y}
                  width={cellWidth}
                  height={cellHeight}
                  fill={getColor(iv)}
                  stroke="#fff"
                  strokeWidth={0.5}
                />
              );
            })
          )}

          {/* Strike labels (x-axis) */}
          {data.strikes.map((strike, idx) => {
            const x = labelWidth + idx * (cellWidth + cellPadding) + cellWidth / 2;
            return (
              <SvgText
                key={`strike-label-${idx}`}
                x={x}
                y={labelHeight - 5}
                fontSize="11"
                fill="#69707F"
                textAnchor="middle"
                fontWeight="600"
              >
                {strike.toFixed(0)}
              </SvgText>
            );
          })}

          {/* Expiration labels (y-axis) */}
          {data.expirations.map((exp, idx) => {
            const y = labelHeight + idx * (cellHeight + cellPadding) + cellHeight / 2;
            const date = new Date(exp);
            const month = date.toLocaleDateString('en-US', { month: 'short' });
            const day = date.getDate();
            return (
              <SvgText
                key={`exp-label-${idx}`}
                x={labelWidth - 5}
                y={y + 4}
                fontSize="11"
                fill="#69707F"
                textAnchor="end"
                fontWeight="600"
              >
                {`${month} ${day}`}
              </SvgText>
            );
          })}

          {/* IV value labels on cells */}
          {data.iv_matrix.map((row, expIdx) =>
            row.map((iv, strikeIdx) => {
              const x = labelWidth + strikeIdx * (cellWidth + cellPadding) + cellWidth / 2;
              const y = labelHeight + expIdx * (cellHeight + cellPadding) + cellHeight / 2;
              return (
                <SvgText
                  key={`iv-label-${expIdx}-${strikeIdx}`}
                  x={x}
                  y={y + 3}
                  fontSize="9"
                  fill={iv > (minIV + maxIV) / 2 ? "#FFFFFF" : "#1F1F1F"}
                  textAnchor="middle"
                  fontWeight="700"
                >
                  {(iv * 100).toFixed(0)}
                </SvgText>
              );
            })
          )}
        </Svg>
        {/* Color scale legend */}
        <View style={styles.legendContainer}>
          <Text style={styles.legendLabel}>Low IV</Text>
          <View style={styles.legendGradient}>
            <View style={[styles.legendColor, { backgroundColor: getColor(minIV) }]} />
            <View style={[styles.legendColor, { backgroundColor: getColor(minIV + ivRange * 0.25) }]} />
            <View style={[styles.legendColor, { backgroundColor: getColor(minIV + ivRange * 0.5) }]} />
            <View style={[styles.legendColor, { backgroundColor: getColor(minIV + ivRange * 0.75) }]} />
            <View style={[styles.legendColor, { backgroundColor: getColor(maxIV) }]} />
          </View>
          <Text style={styles.legendLabel}>High IV</Text>
        </View>
      </View>
    );
  };

  const fetchVolSurface = async () => {
    setLoading(prev => ({ ...prev, volSurface: true }));
    setErrors(prev => ({ ...prev, volSurface: '' }));
    try {
      const response = await fetch(`${API_RUST_BASE}/v1/quant/vol-surface`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setVolSurface(data);
    } catch (err: any) {
      setErrors(prev => ({ ...prev, volSurface: err.message || 'Failed to fetch vol surface' }));
    } finally {
      setLoading(prev => ({ ...prev, volSurface: false }));
    }
  };

  const fetchEdgeDecay = async () => {
    setLoading(prev => ({ ...prev, edgeDecay: true }));
    setErrors(prev => ({ ...prev, edgeDecay: '' }));
    try {
      const response = await fetch(`${API_RUST_BASE}/v1/quant/edge-decay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy_name: strategyName, symbol }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setEdgeDecay(data);
    } catch (err: any) {
      setErrors(prev => ({ ...prev, edgeDecay: err.message || 'Failed to fetch edge decay' }));
    } finally {
      setLoading(prev => ({ ...prev, edgeDecay: false }));
    }
  };

  const fetchRegimeTimeline = async () => {
    setLoading(prev => ({ ...prev, regimeTimeline: true }));
    setErrors(prev => ({ ...prev, regimeTimeline: '' }));
    try {
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 30);
      const endDate = new Date();
      const response = await fetch(`${API_RUST_BASE}/v1/quant/regime-timeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0],
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setRegimeTimeline(data);
    } catch (err: any) {
      setErrors(prev => ({ ...prev, regimeTimeline: err.message || 'Failed to fetch regime timeline' }));
    } finally {
      setLoading(prev => ({ ...prev, regimeTimeline: false }));
    }
  };

  const fetchPortfolioDNA = async () => {
    setLoading(prev => ({ ...prev, portfolioDNA: true }));
    setErrors(prev => ({ ...prev, portfolioDNA: '' }));
    try {
      const response = await fetch(`${API_RUST_BASE}/v1/quant/portfolio-dna/${userId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setPortfolioDNA(data);
    } catch (err: any) {
      setErrors(prev => ({ ...prev, portfolioDNA: err.message || 'Failed to fetch portfolio DNA' }));
    } finally {
      setLoading(prev => ({ ...prev, portfolioDNA: false }));
    }
  };

  return (
    <View style={styles.container}>
      {/* Section header — matches the widget's topHeader pattern */}
      <View style={styles.qtHeader}>
        <View style={styles.qtIconWrap}>
          <Icon name="activity" size={14} color="#6366F1" />
        </View>
        <Text style={styles.title}>Quant Terminal</Text>
      </View>

      {/* Vol Surface Heatmap */}
      <TouchableOpacity
        style={styles.section}
        activeOpacity={0.9}
        onPress={() => {
          setShowVolSurface(!showVolSurface);
          if (!showVolSurface && !volSurface) fetchVolSurface();
        }}
      >
        <View style={styles.sectionLeft}>
          <View style={styles.sectionIconWrap}>
            <Icon name="bar-chart-2" size={13} color="#6366F1" />
          </View>
          <Text style={styles.sectionTitle}>Volatility Surface</Text>
        </View>
        <Icon name={showVolSurface ? 'chevron-up' : 'chevron-down'} size={17} color="#6B7280" />
      </TouchableOpacity>
      {showVolSurface && (
        <View style={styles.content}>
          {loading.volSurface ? (
            <ActivityIndicator size="small" color="#00cc99" />
          ) : errors.volSurface ? (
            <Text style={styles.error}>{errors.volSurface}</Text>
          ) : volSurface ? (
            <View>
              <Text style={styles.label}>Symbol: {volSurface.symbol}</Text>
              <Text style={styles.label}>
                {volSurface.strikes.length} strikes × {volSurface.expirations.length} expirations
              </Text>
              <VolSurfaceHeatmap data={volSurface} />
            </View>
          ) : (
            <Text style={styles.empty}>Tap to load vol surface</Text>
          )}
        </View>
      )}

      {/* Edge Decay Curve */}
      <TouchableOpacity
        style={styles.section}
        activeOpacity={0.9}
        onPress={() => {
          setShowEdgeDecay(!showEdgeDecay);
          if (!showEdgeDecay && !edgeDecay) fetchEdgeDecay();
        }}
      >
        <View style={styles.sectionLeft}>
          <View style={styles.sectionIconWrap}>
            <Icon name="trending-down" size={13} color="#6366F1" />
          </View>
          <Text style={styles.sectionTitle}>Edge Decay</Text>
        </View>
        <Icon name={showEdgeDecay ? 'chevron-up' : 'chevron-down'} size={17} color="#6B7280" />
      </TouchableOpacity>
      {showEdgeDecay && (
        <View style={styles.content}>
          {loading.edgeDecay ? (
            <ActivityIndicator size="small" color="#00cc99" />
          ) : errors.edgeDecay ? (
            <Text style={styles.error}>{errors.edgeDecay}</Text>
          ) : edgeDecay ? (
            <View>
              <Text style={styles.label}>Strategy: {edgeDecay.strategy_name}</Text>
              <Text style={styles.label}>Decay Rate: {(edgeDecay.decay_rate * 100).toFixed(1)}% per day</Text>
              <Text style={styles.label}>Half-Life: {edgeDecay.half_life_days.toFixed(1)} days</Text>

              {/* Chart Type Selector */}
              <View style={styles.chartTypeSelector}>
                {(['line', 'bar'] as const).map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={[styles.chartTypeButton, chartType === type && styles.chartTypeButtonActive]}
                    onPress={() => setChartType(type)}
                  >
                    <Text style={[styles.chartTypeButtonText, chartType === type && styles.chartTypeButtonTextActive]}>
                      {type === 'line' ? 'Line' : 'Bar'}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {edgeDecayChartData && (
                <View style={styles.chartContainer}>
                  {chartType === 'line' ? (
                    <LineChart
                      data={edgeDecayChartData}
                      width={width - 80}
                      height={220}
                      chartConfig={{
                        backgroundColor: '#FFFFFF',
                        backgroundGradientFrom: '#FFFFFF',
                        backgroundGradientTo: '#F8F9FB',
                        decimalPlaces: 1,
                        color: () => '#6366F1',
                        labelColor: () => '#6B7280',
                        propsForBackgroundLines: { stroke: '#EBEBF0' },
                        propsForLabels: { fontWeight: '600' },
                        style: { borderRadius: 12 },
                        propsForDots: { r: '4', strokeWidth: '2', stroke: '#6366F1' },
                      }}
                      bezier
                      style={styles.chart}
                      withDots={true}
                      withShadow={false}
                      withInnerLines={true}
                      withOuterLines={true}
                      withVerticalLines={false}
                      withHorizontalLines={true}
                      yAxisLabel=""
                      yAxisSuffix="%"
                      segments={4}
                    />
                  ) : (
                    <BarChart
                      data={edgeDecayChartData}
                      width={width - 80}
                      height={220}
                      chartConfig={{
                        backgroundColor: '#FFFFFF',
                        backgroundGradientFrom: '#FFFFFF',
                        backgroundGradientTo: '#F8F9FB',
                        decimalPlaces: 1,
                        color: () => '#6366F1',
                        labelColor: () => '#6B7280',
                        propsForBackgroundLines: { stroke: '#EBEBF0' },
                        propsForLabels: { fontWeight: '600' },
                        style: { borderRadius: 12 },
                      }}
                      style={styles.chart}
                      showValuesOnTopOfBars={false}
                      yAxisLabel=""
                      yAxisSuffix="%"
                      segments={4}
                    />
                  )}
                  <Text style={styles.chartLabel}>Edge Value Over Time</Text>
                </View>
              )}
            </View>
          ) : (
            <Text style={styles.empty}>Tap to load edge decay</Text>
          )}
        </View>
      )}

      {/* Regime Timeline */}
      <TouchableOpacity
        style={styles.section}
        activeOpacity={0.9}
        onPress={() => {
          setShowRegimeTimeline(!showRegimeTimeline);
          if (!showRegimeTimeline && !regimeTimeline) fetchRegimeTimeline();
        }}
      >
        <View style={styles.sectionLeft}>
          <View style={styles.sectionIconWrap}>
            <Icon name="clock" size={13} color="#6366F1" />
          </View>
          <Text style={styles.sectionTitle}>Regime Timeline</Text>
        </View>
        <Icon name={showRegimeTimeline ? 'chevron-up' : 'chevron-down'} size={17} color="#6B7280" />
      </TouchableOpacity>
      {showRegimeTimeline && (
        <View style={styles.content}>
          {loading.regimeTimeline ? (
            <ActivityIndicator size="small" color="#00cc99" />
          ) : errors.regimeTimeline ? (
            <Text style={styles.error}>{errors.regimeTimeline}</Text>
          ) : regimeTimeline ? (
            <ScrollView style={styles.timelineContainer}>
              {regimeTimeline.events.map((event, idx) => (
                <View key={idx} style={styles.timelineEvent}>
                  <Text style={styles.eventDate}>{event.date}</Text>
                  <Text style={styles.eventRegime}>{event.regime}</Text>
                  <Text style={styles.eventHeadline}>{event.headline}</Text>
                  <Text style={styles.eventConfidence}>
                    Confidence: {(event.confidence * 100).toFixed(0)}%
                  </Text>
                </View>
              ))}
            </ScrollView>
          ) : (
            <Text style={styles.empty}>Tap to load regime timeline</Text>
          )}
        </View>
      )}

      {/* Portfolio DNA */}
      <TouchableOpacity
        style={styles.section}
        activeOpacity={0.9}
        onPress={() => {
          setShowPortfolioDNA(!showPortfolioDNA);
          if (!showPortfolioDNA && !portfolioDNA) fetchPortfolioDNA();
        }}
      >
        <View style={styles.sectionLeft}>
          <View style={styles.sectionIconWrap}>
            <Icon name="user" size={13} color="#6366F1" />
          </View>
          <Text style={styles.sectionTitle}>Portfolio DNA</Text>
        </View>
        <Icon name={showPortfolioDNA ? 'chevron-up' : 'chevron-down'} size={17} color="#6B7280" />
      </TouchableOpacity>
      {showPortfolioDNA && (
        <View style={styles.content}>
          {loading.portfolioDNA ? (
            <ActivityIndicator size="small" color="#00cc99" />
          ) : errors.portfolioDNA ? (
            <Text style={styles.error}>{errors.portfolioDNA}</Text>
          ) : portfolioDNA ? (
            <ScrollView>
              <View style={styles.dnaCard}>
                <Text style={styles.dnaArchetype}>{portfolioDNA.archetype ?? '—'}</Text>
                <Text style={styles.dnaSubtext}>
                  You are {Object.entries(portfolioDNA.archetype_breakdown ?? {})
                    .map(([k, v]) => `${(Number(v) * 100).toFixed(0)}% ${k}`)
                    .join(', ') || '—'}
                </Text>
              </View>
              {portfolioDNA.fingerprint && (
                <View style={styles.dnaSection}>
                  <Text style={styles.dnaLabel}>Fingerprint</Text>
                  <Text style={styles.dnaText}>Win Rate: {((portfolioDNA.fingerprint.win_rate ?? 0) * 100).toFixed(1)}%</Text>
                  <Text style={styles.dnaText}>Profit Factor: {(portfolioDNA.fingerprint.profit_factor ?? 0).toFixed(2)}</Text>
                  <Text style={styles.dnaText}>Sharpe Ratio: {(portfolioDNA.fingerprint.sharpe_ratio ?? 0).toFixed(2)}</Text>
                  <Text style={styles.dnaText}>Max Drawdown: {((portfolioDNA.fingerprint.max_drawdown ?? 0) * 100).toFixed(1)}%</Text>
                  <Text style={styles.dnaText}>Total Trades: {portfolioDNA.fingerprint.total_trades ?? 0}</Text>
                </View>
              )}
              {Array.isArray(portfolioDNA.strengths) && portfolioDNA.strengths.length > 0 && (
                <View style={styles.dnaSection}>
                  <Text style={styles.dnaLabel}>Strengths</Text>
                  {portfolioDNA.strengths.map((s, idx) => (
                    <Text key={idx} style={styles.dnaText}>✓ {s}</Text>
                  ))}
                </View>
              )}
              {Array.isArray(portfolioDNA.weaknesses) && portfolioDNA.weaknesses.length > 0 && (
                <View style={styles.dnaSection}>
                  <Text style={styles.dnaLabel}>Weaknesses</Text>
                  {portfolioDNA.weaknesses.map((w, idx) => (
                    <Text key={idx} style={styles.dnaText}>⚠ {w}</Text>
                  ))}
                </View>
              )}
              {Array.isArray(portfolioDNA.recommendations) && portfolioDNA.recommendations.length > 0 && (
                <View style={styles.dnaSection}>
                  <Text style={styles.dnaLabel}>Recommendations</Text>
                  {portfolioDNA.recommendations.map((r, idx) => (
                    <Text key={idx} style={styles.dnaText}>→ {r}</Text>
                  ))}
                </View>
              )}
            </ScrollView>
          ) : (
            <Text style={styles.empty}>Tap to load portfolio DNA</Text>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  // Container — sits inside the white featured card, no extra card shadow needed
  container: {
    backgroundColor: 'transparent',
    marginTop: 8,
    marginBottom: 8,
  },

  // Header row — matches topHeader in RustForexWidget
  qtHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  qtIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: '#6366F110',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0B0B0F',
    letterSpacing: 0.1,
  },

  // Section toggle — matches the `toggle` style in RustForexWidget
  section: {
    marginBottom: 8,
    backgroundColor: '#F8F9FB',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#EBEBF0',
    paddingVertical: 13,
    paddingHorizontal: 14,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  sectionIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: '#6366F110',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0B0B0F',
  },

  // Content panel — matches `panel` in RustForexWidget
  content: {
    marginBottom: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#EBEBF0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },

  label: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '600',
    marginBottom: 4,
  },

  error: {
    fontSize: 13,
    color: '#EF4444',
    fontWeight: '700',
    textAlign: 'center',
    marginVertical: 8,
  },

  empty: {
    fontSize: 13,
    color: '#AEAEB2',
    fontWeight: '600',
    fontStyle: 'italic',
    textAlign: 'center',
    marginVertical: 16,
  },

  // Vol Surface Heatmap
  heatmapContainer: {
    marginTop: 12,
    alignItems: 'center',
    backgroundColor: '#F8F9FB',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#EBEBF0',
  },

  legendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    gap: 10,
  },
  legendGradient: {
    flexDirection: 'row',
    gap: 3,
  },
  legendColor: {
    width: 24,
    height: 14,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#EBEBF0',
  },
  legendLabel: {
    fontSize: 11,
    color: '#8E8E93',
    fontWeight: '700',
    letterSpacing: 0.3,
  },

  // Edge Decay Chart
  chartContainer: {
    marginTop: 12,
    alignItems: 'center',
    backgroundColor: '#F8F9FB',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: '#EBEBF0',
  },
  chart: {
    borderRadius: 12,
  },
  chartLabel: {
    marginTop: 10,
    fontSize: 11,
    color: '#8E8E93',
    fontWeight: '700',
    textAlign: 'center',
  },

  chartTypeSelector: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginTop: 12,
  },
  chartTypeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: '#F8F9FB',
    borderWidth: 1,
    borderColor: '#EBEBF0',
  },
  chartTypeButtonActive: {
    backgroundColor: '#0B0B0F',
    borderColor: '#0B0B0F',
  },
  chartTypeButtonText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
  },
  chartTypeButtonTextActive: {
    color: '#FFFFFF',
  },

  // Regime Timeline
  timelineContainer: {
    maxHeight: 300,
  },
  timelineEvent: {
    backgroundColor: '#F8F9FB',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#EBEBF0',
  },
  eventDate: {
    fontSize: 10,
    color: '#AEAEB2',
    fontWeight: '700',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  eventRegime: {
    fontSize: 13,
    fontWeight: '800',
    color: '#6366F1',
    marginBottom: 4,
  },
  eventHeadline: {
    fontSize: 13,
    color: '#0B0B0F',
    fontWeight: '600',
    lineHeight: 20,
    marginBottom: 6,
  },
  eventConfidence: {
    fontSize: 11,
    color: '#8E8E93',
    fontWeight: '700',
  },

  // Portfolio DNA
  dnaCard: {
    backgroundColor: '#6366F108',
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#6366F120',
  },
  dnaArchetype: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0B0B0F',
    letterSpacing: -0.5,
    marginBottom: 6,
  },
  dnaSubtext: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '600',
    textAlign: 'center',
    lineHeight: 18,
  },

  dnaSection: {
    marginBottom: 16,
  },
  dnaLabel: {
    fontSize: 12,
    fontWeight: '800',
    color: '#0B0B0F',
    marginBottom: 8,
    letterSpacing: 0.1,
  },
  dnaText: {
    fontSize: 13,
    color: '#3A3A3C',
    fontWeight: '600',
    lineHeight: 20,
    marginBottom: 4,
    paddingLeft: 2,
  },
});

