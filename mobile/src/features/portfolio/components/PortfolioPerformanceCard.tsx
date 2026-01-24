import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  Modal,
  Alert,
  StatusBar,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { LineChart } from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';
import UI from '../../../shared/constants';
import logger from '../../../utils/logger';

const { width: screenWidth } = Dimensions.get('window');

const TABS = ['1D', '1W', '1M', '3M', '1Y', 'All'];
const BENCHMARKS = ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI'];

interface PortfolioPerformanceCardProps {
  totalValue?: number;
  totalReturn?: number;
  totalReturnPercent?: number;
  benchmarkReturn?: number;
  navigateTo?: (screen: string, params?: any) => void;
}

interface InfoModalContent {
  title: string;
  content: string;
  formula?: string;
  percentage?: string;
  example?: string;
  interpretation?: string;
}

export default function PortfolioPerformanceCard({
  totalValue: initialTotalValue = 125430.50,
  totalReturn: initialTotalReturn = 8430.50,
  totalReturnPercent: initialTotalReturnPercent,
  benchmarkReturn = 5.45,
  navigateTo,
}: PortfolioPerformanceCardProps = {}) {
  const navigation = useNavigation<any>();
  const [tab, setTab] = useState('1M');
  const [showBenchmark, setShowBenchmark] = useState(true);
  const [useAdvancedChart, setUseAdvancedChart] = useState(false);
  const [selectedBenchmark, setSelectedBenchmark] = useState('SPY');
  const [showBenchmarkSelector, setShowBenchmarkSelector] = useState(false);
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [infoModalContent, setInfoModalContent] = useState<InfoModalContent | null>(null);
  const [chartData, setChartData] = useState<{ portfolio: number[]; benchmark: number[]; labels: string[] }>({
    portfolio: [],
    benchmark: [],
    labels: [],
  });

  // Dynamic values that can change
  const [totalValue, setTotalValue] = useState(initialTotalValue);
  const [totalReturn, setTotalReturn] = useState(initialTotalReturn);

  // Calculate totalReturnPercent if not provided
  const totalReturnPercent = useMemo(() => {
    if (initialTotalReturnPercent !== undefined) {
      return initialTotalReturnPercent;
    }
    const base = totalValue - totalReturn;
    return base > 0 ? (totalReturn / base) * 100 : 0;
  }, [initialTotalReturnPercent, totalValue, totalReturn]);

  const alpha = totalReturnPercent - benchmarkReturn;
  const positive = totalReturn >= 0;

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Educational content for info buttons
  const getInfoContent = (type: string): InfoModalContent | null => {
    const base = totalValue - totalReturn;
    switch (type) {
      case 'totalValue':
        return {
          title: 'Total Portfolio Value',
          content:
            'The total current market value of all your investments combined. This includes stocks, bonds, ETFs, and other securities in your portfolio.',
          formula: 'Total Value = Sum of (Shares × Current Price) for all holdings',
          example:
            'If you own 10 shares of Stock A at $100 and 5 shares of Stock B at $200, your total value is $2,000.',
        };
      case 'totalReturn':
        return {
          title: 'Total Return',
          content:
            'The total profit or loss on your investments, shown both in dollar amount and percentage. This reflects how much your portfolio has grown or declined since your initial investment.',
          formula: 'Total Return = Current Value - Initial Investment',
          percentage: 'Return % = (Total Return / Initial Investment) × 100',
          example: `If you invested ${formatCurrency(base)} and your portfolio is now worth ${formatCurrency(totalValue)}, your return is ${formatCurrency(Math.abs(totalReturn))} or ${formatPercent(totalReturnPercent)}.`,
        };
      case 'alpha':
        return {
          title: 'Alpha (Outperformance)',
          content:
            'Alpha measures how much your portfolio outperformed (or underperformed) the benchmark index. Positive alpha means you are beating the market!',
          formula: 'Alpha = Your Return % - Benchmark Return %',
          example: `Your portfolio returned ${totalReturnPercent.toFixed(2)}% while ${selectedBenchmark} returned ${benchmarkReturn}%, giving you an alpha of ${alpha.toFixed(2)}%.`,
          interpretation: alpha > 0 ? "You're outperforming the market! 🎉" : "Your portfolio is underperforming the benchmark.",
        };
      default:
        return null;
    }
  };

  const openInfoModal = (type: string) => {
    const content = getInfoContent(type);
    if (content) {
      setInfoModalContent(content);
      setShowInfoModal(true);
    }
  };

  // Generate dynamic data based on timeframe
  const generateData = (points: number) => {
    const data: number[] = [];
    const benchData: number[] = [];
    const labels: string[] = [];
    const base = totalValue - totalReturn;
    const timeNow = Date.now();

    const timeStep =
      tab === '1D'
        ? 3600000 // 1 hour
        : tab === '1W'
          ? 86400000 // 1 day
          : tab === '1M'
            ? 86400000 // 1 day
            : tab === '3M'
              ? 86400000 // 1 day
              : tab === '1Y'
                ? 86400000 // 1 day
                : 86400000 * 7; // 1 week for 'All'

    for (let i = 0; i < points; i++) {
      const progress = i / (points - 1);
      const noise = (Math.random() - 0.5) * 0.015;
      const trendNoise = Math.sin(i * 0.3) * 0.01;

      const portfolioValue = base + totalReturn * progress + base * (noise + trendNoise);
      const benchValue = base + totalReturn * 0.76 * progress + base * (noise * 0.8 + trendNoise * 0.7);

      const timestamp = timeNow - (points - i - 1) * timeStep;

      data.push(Math.max(portfolioValue, base * 0.85));
      benchData.push(Math.max(benchValue, base * 0.85));

      // Generate labels based on timeframe
      if (tab === '1D') {
        const date = new Date(timestamp);
        labels.push(`${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`);
      } else if (tab === '1W') {
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const date = new Date(timestamp);
        labels.push(days[date.getDay()] || '');
      } else {
        labels.push('');
      }
    }

    // Ensure last point matches current value
    if (data.length > 0) {
      data[data.length - 1] = totalValue;
    }

    return { portfolio: data, benchmark: benchData, labels };
  };

  // Update data when timeframe changes
  useEffect(() => {
    const points =
      tab === '1D' ? 24 : tab === '1W' ? 7 : tab === '1M' ? 30 : tab === '3M' ? 90 : tab === '1Y' ? 365 : 500;
    const newData = generateData(points);
    setChartData(newData);
  }, [tab, totalValue, totalReturn]);

  // Simulate live updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate small price changes
      const change = (Math.random() - 0.5) * 500;
      setTotalValue((prev) => Math.max(prev + change, 100000));
      setTotalReturn((prev) => prev + change);

      // Update last point in chart
      setChartData((prev) => {
        const newPortfolio = [...prev.portfolio];
        const newBenchmark = [...prev.benchmark];

        if (newPortfolio.length > 0) {
          newPortfolio[newPortfolio.length - 1] = totalValue + change;
          newBenchmark[newBenchmark.length - 1] += change * 0.76;
        }

        return { ...prev, portfolio: newPortfolio, benchmark: newBenchmark };
      });
    }, 5000);

    return () => clearInterval(interval);
  }, [totalValue]);

  const chartDataForDisplay = useMemo(() => {
    const datasets = [
      {
        data: chartData.portfolio,
        color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`, // Blue
        strokeWidth: 3,
      },
    ];

    if (showBenchmark && chartData.benchmark.length > 0) {
      datasets.push({
        data: chartData.benchmark,
        color: (opacity = 1) => `rgba(168, 85, 247, ${opacity * 0.4})`, // Purple with opacity
        strokeWidth: 2,
      });
    }

    return {
      labels: chartData.labels.length > 0 ? chartData.labels : chartData.portfolio.map(() => ''),
      datasets,
    };
  }, [chartData, showBenchmark]);

  const handleViewAnalytics = () => {
    try {
      // Try navigateTo first if provided
      if (navigateTo) {
        navigateTo('portfolio');
        return;
      }
      
      // Fallback to React Navigation
      if (navigation && navigation.navigate) {
        // Try navigating to Invest stack, then portfolio screen
        try {
          navigation.navigate('Invest' as never, {
            screen: 'Portfolio' as never,
          } as never);
          return;
        } catch (investError) {
          // If that fails, try direct navigation
          try {
            navigation.navigate('Portfolio' as never);
            return;
          } catch (directError) {
            // If all navigation fails, show alert
            logger.error('Navigation failed:', { investError, directError });
          }
        }
      }
    } catch (error) {
      logger.error('Error in handleViewAnalytics:', error);
    }
    
    // Final fallback: show alert
    Alert.alert(
      'Detailed Analytics',
      'Opening portfolio screen...\n\nThis would show:\n• Performance breakdown by holding\n• Risk metrics\n• Tax implications\n• Rebalancing suggestions',
      [{ text: 'OK' }],
    );
  };

  const chartConfig = {
    backgroundColor: '#FFFFFF',
    backgroundGradientFrom: '#FFFFFF',
    backgroundGradientTo: '#FFFFFF',
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(100, 116, 139, ${opacity})`,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: positive ? '#10B981' : '#EF4444',
    },
    propsForBackgroundLines: {
      strokeDasharray: '4 4',
      stroke: '#E2E8F0',
      strokeWidth: 1,
    },
  };

  return (
    <View style={styles.container}>
      {/* Info Modal */}
      <Modal
        visible={showInfoModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowInfoModal(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowInfoModal(false)}
        >
          <View style={styles.infoModalContent}>
            <View style={styles.infoModalHeader}>
              <Text style={styles.infoModalTitle}>
                {infoModalContent?.title || 'Information'}
              </Text>
              <TouchableOpacity onPress={() => setShowInfoModal(false)}>
                <Icon name="x" size={20} color="#64748B" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.infoModalBody} showsVerticalScrollIndicator={false}>
              <Text style={styles.infoModalText}>{infoModalContent?.content}</Text>

              {infoModalContent?.formula && (
                <View style={styles.formulaBox}>
                  <Text style={styles.formulaText}>{infoModalContent.formula}</Text>
                  {infoModalContent.percentage && (
                    <Text style={[styles.formulaText, { marginTop: 8 }]}>
                      {infoModalContent.percentage}
                    </Text>
                  )}
                </View>
              )}

              {infoModalContent?.example && (
                <View style={styles.exampleBox}>
                  <Text style={styles.exampleLabel}>Example:</Text>
                  <Text style={styles.exampleText}>{infoModalContent.example}</Text>
                </View>
              )}

              {infoModalContent?.interpretation && (
                <View
                  style={[
                    styles.interpretationBox,
                    alpha > 0 ? styles.interpretationPositive : styles.interpretationNegative,
                  ]}
                >
                  <Text
                    style={[
                      styles.interpretationText,
                      alpha > 0 ? styles.positiveValue : styles.negativeValue,
                    ]}
                  >
                    {infoModalContent.interpretation}
                  </Text>
                </View>
              )}
            </ScrollView>

            <View style={styles.infoModalFooter}>
              <TouchableOpacity
                style={styles.infoModalButton}
                onPress={() => setShowInfoModal(false)}
              >
                <Text style={styles.infoModalButtonText}>Got it!</Text>
              </TouchableOpacity>
            </View>
          </View>
        </TouchableOpacity>
      </Modal>

      <View style={styles.card}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerTop}>
            <View style={styles.titleContainer}>
              <View style={styles.iconContainer}>
                <Icon name="trending-up" size={20} color={UI.colors.primary} />
              </View>
              <View>
                <Text style={styles.title}>Portfolio Performance</Text>
                <Text style={styles.subtitle}>Real-time tracking & analysis</Text>
              </View>
            </View>

            {/* Controls Row */}
            <View style={styles.controlsRow}>
              {/* Timeframe Tabs */}
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.tabsContainer}
              >
                {TABS.map((t) => (
                  <TouchableOpacity
                    key={t}
                    onPress={() => setTab(t)}
                    style={[styles.tab, tab === t && styles.tabActive]}
                  >
                    <Text style={[styles.tabText, tab === t && styles.tabTextActive]}>{t}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>

              {/* Benchmark Selector */}
              <View style={styles.controlGroup}>
                <TouchableOpacity
                  onPress={() => setShowBenchmarkSelector(!showBenchmarkSelector)}
                  style={[
                    styles.benchmarkButton,
                    showBenchmark && styles.benchmarkButtonActive,
                  ]}
                >
                  <View
                    style={[
                      styles.benchmarkIndicator,
                      showBenchmark && styles.benchmarkIndicatorActive,
                    ]}
                  />
                  <Text
                    style={[
                      styles.benchmarkButtonText,
                      showBenchmark && styles.benchmarkButtonTextActive,
                    ]}
                  >
                    {selectedBenchmark}
                  </Text>
                  <Icon name="chevron-down" size={14} color={showBenchmark ? '#A855F7' : '#64748B'} />
                </TouchableOpacity>

                {showBenchmarkSelector && (
                  <Modal
                    visible={showBenchmarkSelector}
                    transparent
                    animationType="fade"
                    onRequestClose={() => setShowBenchmarkSelector(false)}
                  >
                    <TouchableOpacity
                      style={styles.modalOverlay}
                      activeOpacity={1}
                      onPress={() => setShowBenchmarkSelector(false)}
                    >
                      <View style={styles.benchmarkDropdown}>
                        {BENCHMARKS.map((bench) => (
                          <TouchableOpacity
                            key={bench}
                            onPress={() => {
                              setSelectedBenchmark(bench);
                              setShowBenchmarkSelector(false);
                            }}
                            style={[
                              styles.benchmarkOption,
                              selectedBenchmark === bench && styles.benchmarkOptionActive,
                            ]}
                          >
                            <Text
                              style={[
                                styles.benchmarkOptionText,
                                selectedBenchmark === bench && styles.benchmarkOptionTextActive,
                              ]}
                            >
                              {bench}
                            </Text>
                          </TouchableOpacity>
                        ))}
                      </View>
                    </TouchableOpacity>
                  </Modal>
                )}
              </View>

              {/* Benchmark Toggle */}
              <TouchableOpacity
                onPress={() => setShowBenchmark(!showBenchmark)}
                style={[
                  styles.toggleButton,
                  showBenchmark && styles.toggleButtonActive,
                ]}
              >
                <Text
                  style={[
                    styles.toggleButtonText,
                    showBenchmark && styles.toggleButtonTextActive,
                  ]}
                >
                  {showBenchmark ? 'Hide' : 'Show'} Benchmark
                </Text>
              </TouchableOpacity>

              {/* Advanced Chart Toggle */}
              <TouchableOpacity
                onPress={() => setUseAdvancedChart(!useAdvancedChart)}
                style={[
                  styles.toggleButton,
                  useAdvancedChart && styles.toggleButtonActive,
                ]}
              >
                <Icon name="zap" size={14} color={useAdvancedChart ? '#F59E0B' : '#64748B'} />
                <Text
                  style={[
                    styles.toggleButtonText,
                    useAdvancedChart && styles.toggleButtonTextActive,
                  ]}
                >
                  {useAdvancedChart ? 'AR' : 'Chart'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* KPI Section */}
        <View style={styles.kpiSection}>
          <View style={styles.kpiGrid}>
            {/* Total Value */}
            <View style={styles.kpiCard}>
              <View style={styles.kpiHeader}>
                <Icon name="dollar-sign" size={16} color="#64748B" />
                <Text style={styles.kpiLabel}>Total Value</Text>
                <TouchableOpacity onPress={() => openInfoModal('totalValue')}>
                  <View style={styles.infoButton}>
                    <Icon name="info" size={12} color={UI.colors.primary} />
                  </View>
                </TouchableOpacity>
              </View>
              <Text style={styles.kpiValue}>{formatCurrency(totalValue)}</Text>
            </View>

            {/* Total Return */}
            <View style={styles.kpiCard}>
              <View style={styles.kpiHeader}>
                {positive ? (
                  <Icon name="trending-up" size={16} color="#10B981" />
                ) : (
                  <Icon name="trending-down" size={16} color="#EF4444" />
                )}
                <Text style={styles.kpiLabel}>Total Return</Text>
                <TouchableOpacity onPress={() => openInfoModal('totalReturn')}>
                  <View style={styles.infoButton}>
                    <Icon name="info" size={12} color={UI.colors.primary} />
                  </View>
                </TouchableOpacity>
              </View>
              <View style={styles.returnRow}>
                <Text
                  style={[
                    styles.kpiValue,
                    positive ? styles.positiveValue : styles.negativeValue,
                  ]}
                >
                  {formatCurrency(Math.abs(totalReturn))}
                </Text>
                <Text
                  style={[
                    styles.returnPercent,
                    positive ? styles.positiveValue : styles.negativeValue,
                  ]}
                >
                  {formatPercent(totalReturnPercent)}
                </Text>
              </View>
            </View>

            {/* Alpha vs Benchmark */}
            {showBenchmark && (
              <View style={styles.kpiCard}>
                <View style={styles.kpiHeader}>
                  <Icon name="activity" size={16} color="#A855F7" />
                  <Text style={styles.kpiLabel}>Alpha vs {selectedBenchmark}</Text>
                  <TouchableOpacity onPress={() => openInfoModal('alpha')}>
                    <View style={styles.infoButton}>
                      <Icon name="info" size={12} color={UI.colors.primary} />
                    </View>
                  </TouchableOpacity>
                </View>
                <View style={styles.alphaRow}>
                  <View
                    style={[
                      styles.alphaBadge,
                      alpha >= 0 ? styles.alphaBadgePositive : styles.alphaBadgeNegative,
                    ]}
                  >
                    <Text
                      style={[
                        styles.alphaValue,
                        alpha >= 0 ? styles.positiveValue : styles.negativeValue,
                      ]}
                    >
                      {formatPercent(alpha)}
                    </Text>
                  </View>
                  <Text style={styles.benchmarkReturnText}>
                    Benchmark: {formatPercent(benchmarkReturn)}
                  </Text>
                </View>
              </View>
            )}
          </View>
        </View>

        {/* Chart Section */}
        <View style={styles.chartSection}>
          {useAdvancedChart ? (
            <ARChartView
              portfolioData={chartData.portfolio}
              benchmarkData={chartData.benchmark}
              showBenchmark={showBenchmark}
              totalValue={totalValue}
              totalReturn={totalReturn}
              positive={positive}
              onClose={() => setUseAdvancedChart(false)}
            />
          ) : (
            <View style={styles.chartContainer}>
              {chartData.portfolio.length > 0 ? (
                <LineChart
                  data={chartDataForDisplay}
                  width={screenWidth - 64}
                  height={256}
                  chartConfig={chartConfig}
                  bezier
                  style={styles.chart}
                  withDots={false}
                  withShadow={false}
                  withInnerLines={true}
                  withOuterLines={false}
                  withVerticalLines={false}
                  withHorizontalLines={true}
                />
              ) : (
                <View style={styles.chartPlaceholder}>
                  <Text style={styles.chartPlaceholderText}>Loading chart data...</Text>
                </View>
              )}
            </View>
          )}

          {/* Legend - Only show when not in AR mode */}
          {!useAdvancedChart && (
            <View style={styles.legend}>
              <View style={styles.legendItem}>
                <View style={styles.legendLinePortfolio} />
                <Text style={styles.legendText}>Portfolio</Text>
              </View>
              {showBenchmark && (
                <View style={styles.legendItem}>
                  <View style={styles.legendLineBenchmark} />
                  <Text style={styles.legendText}>{selectedBenchmark}</Text>
                </View>
              )}
            </View>
          )}
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <View style={styles.footerRow}>
            <View style={styles.statusIndicator}>
              <View style={styles.statusDot} />
              <Text style={styles.statusText}>Live data • Updated just now</Text>
            </View>
            <TouchableOpacity onPress={handleViewAnalytics}>
              <View style={styles.footerLinkContainer}>
                <Icon name="bar-chart-2" size={16} color={UI.colors.primary} />
                <Text style={styles.footerLink}>View detailed analytics →</Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </View>
  );
}

// AR Chart View Component
function ARChartView({
  portfolioData,
  benchmarkData,
  showBenchmark,
  totalValue,
  totalReturn,
  positive,
  onClose,
}: {
  portfolioData: number[];
  benchmarkData: number[];
  showBenchmark: boolean;
  totalValue: number;
  totalReturn: number;
  positive: boolean;
  onClose: () => void;
}) {
  const [rotation, setRotation] = useState(0);
  const [scale, setScale] = useState(1);
  const insets = useSafeAreaInsets();

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
  };

  // Calculate 3D positions for the chart
  const chartPoints = useMemo(() => {
    if (portfolioData.length === 0) return [];
    const min = Math.min(...portfolioData);
    const max = Math.max(...portfolioData);
    const range = max - min || 1;
    const chartHeight = 300; // Fixed height for visualization

    return portfolioData.map((value, i) => {
      const x = (i / (portfolioData.length - 1)) * (screenWidth - 80); // X position in pixels
      const normalizedY = (value - min) / range; // 0 to 1
      const y = chartHeight - normalizedY * chartHeight; // Y position from bottom
      return { x, y, value, normalizedY };
    });
  }, [portfolioData]);

  return (
    <Modal visible={true} animationType="slide" presentationStyle="fullScreen" onRequestClose={onClose}>
      <SafeAreaView style={styles.arContainer} edges={['top', 'bottom']}>
        <StatusBar barStyle="dark-content" />
        {/* AR Header */}
        <View style={[styles.arHeader, { paddingTop: Math.max(insets.top + 8, 24) }]}>
          <View style={styles.arHeaderLeft}>
            <Icon name="zap" size={24} color="#F59E0B" />
            <View>
              <Text style={styles.arTitle}>AR Portfolio Walk</Text>
              <Text style={styles.arSubtitle}>3D visualization of your portfolio journey</Text>
            </View>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.arCloseButton}>
            <Icon name="x" size={24} color="#1E293B" />
          </TouchableOpacity>
        </View>

        {/* AR Visualization Area */}
        <View style={styles.arVisualizationArea}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.arScrollContent}
          >
            <View style={styles.arCanvas}>
              {/* Grid Background */}
              <View style={styles.arGrid}>
                {[0, 1, 2, 3, 4].map((i) => (
                  <View key={i} style={[styles.arGridLine, { top: `${i * 25}%` }]} />
                ))}
              </View>

              {/* 3D Chart Line */}
              <View style={styles.arChart3D}>
                {chartPoints.map((point, i) => {
                  const nextPoint = chartPoints[i + 1];
                  if (!nextPoint) return null;

                  const dx = nextPoint.x - point.x;
                  const dy = nextPoint.y - point.y;
                  const distance = Math.sqrt(dx * dx + dy * dy);
                  const angle = (Math.atan2(dy, dx) * 180) / Math.PI;

                  return (
                    <View
                      key={i}
                      style={[
                        styles.arChartSegment,
                        {
                          left: point.x,
                          top: point.y,
                          width: distance,
                          transform: [{ rotate: `${angle}deg` }, { scale }],
                        },
                      ]}
                    >
                      <LinearGradient
                        colors={
                          positive
                            ? ['#10B981', '#34D399', '#6EE7B7']
                            : ['#EF4444', '#F87171', '#FCA5A5']
                        }
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 0 }}
                        style={styles.arChartSegmentGradient}
                      />
                    </View>
                  );
                })}

                {/* Data Points */}
                {chartPoints.map((point, i) => (
                  <TouchableOpacity
                    key={`point-${i}`}
                    style={[
                      styles.arDataPoint,
                      {
                        left: point.x - 6,
                        top: point.y - 6,
                        backgroundColor: positive ? '#10B981' : '#EF4444',
                      },
                    ]}
                    onPress={() => {
                      Alert.alert('Portfolio Value', formatCurrency(point.value));
                    }}
                  >
                    <View style={styles.arDataPointGlow} />
                  </TouchableOpacity>
                ))}

                {/* Current Value Indicator */}
                {chartPoints.length > 0 && (
                  <View
                    style={[
                      styles.arCurrentPoint,
                      {
                        left: chartPoints[chartPoints.length - 1].x - 12,
                        top: chartPoints[chartPoints.length - 1].y - 12,
                        backgroundColor: positive ? '#10B981' : '#EF4444',
                      },
                    ]}
                  >
                    <View style={styles.arCurrentPointGlow} />
                    <Icon
                      name={positive ? 'trending-up' : 'trending-down'}
                      size={16}
                      color="#FFFFFF"
                    />
                  </View>
                )}
              </View>

              {/* Y-Axis Labels */}
              <View style={styles.arYAxis}>
                {chartPoints.length > 0 && (() => {
                  const min = Math.min(...portfolioData);
                  const max = Math.max(...portfolioData);
                  const range = max - min || 1;
                  return [0, 1, 2, 3, 4].map((i) => {
                    const value = min + (range * i) / 4;
                    return (
                      <Text key={i} style={[styles.arYAxisLabel, { top: `${i * 25}%` }]}>
                        {formatCurrency(value)}
                      </Text>
                    );
                  });
                })()}
              </View>
            </View>
          </ScrollView>

          {/* Instructions Overlay */}
          <View style={styles.arInstructions}>
            <Text style={styles.arInstructionsText}>
              Swipe to explore • Pinch to zoom • Tap points for details
            </Text>
          </View>

          {/* AR Stats Panel */}
          <View style={styles.arStatsPanel}>
            <View style={styles.arStatCard}>
              <Text style={styles.arStatLabel}>Current Value</Text>
              <Text style={styles.arStatValue}>{formatCurrency(totalValue)}</Text>
            </View>
            <View style={styles.arStatCard}>
              <Text style={styles.arStatLabel}>Total Return</Text>
              <Text style={[styles.arStatValue, positive ? styles.positiveValue : styles.negativeValue]}>
                {formatCurrency(Math.abs(totalReturn))}
              </Text>
            </View>
            <View style={styles.arStatCard}>
              <Text style={styles.arStatLabel}>Performance</Text>
              <Text style={[styles.arStatValue, positive ? styles.positiveValue : styles.negativeValue]}>
                {positive ? '📈 Up' : '📉 Down'}
              </Text>
            </View>
          </View>

          {/* AR Controls */}
          <View style={styles.arControls}>
            <TouchableOpacity
              style={styles.arControlButton}
              onPress={() => setScale(Math.max(0.5, scale - 0.1))}
            >
              <Icon name="zoom-out" size={20} color="#1E293B" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.arControlButton}
              onPress={() => setScale(Math.min(2, scale + 0.1))}
            >
              <Icon name="zoom-in" size={20} color="#1E293B" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.arControlButton}
              onPress={() => setRotation((prev) => prev + 15)}
            >
              <Icon name="rotate-cw" size={20} color="#1E293B" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.arControlButton} onPress={() => setRotation(0)}>
              <Icon name="refresh-cw" size={20} color="#1E293B" />
            </TouchableOpacity>
          </View>
        </View>

        {/* AR Footer */}
        <View style={styles.arFooter}>
          <View style={styles.arFooterInfo}>
            <View style={styles.arFooterDot} />
            <Text style={styles.arFooterText}>AR Preview Mode</Text>
          </View>
          <Text style={styles.arFooterNote}>
            Full ARKit/ARCore integration coming soon
          </Text>
        </View>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    padding: UI.spacing.md,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
    overflow: 'hidden',
  },
  header: {
    padding: UI.spacing.md,
    paddingBottom: UI.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  headerTop: {
    gap: UI.spacing.md,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconContainer: {
    padding: 10,
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    borderRadius: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1E293B',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    marginTop: 2,
  },
  controlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  tabsContainer: {
    gap: 8,
  },
  tab: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
  },
  tabActive: {
    backgroundColor: UI.colors.primary,
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  tabTextActive: {
    color: '#FFFFFF',
  },
  controlGroup: {
    position: 'relative',
  },
  benchmarkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  benchmarkButtonActive: {
    backgroundColor: 'rgba(168, 85, 247, 0.1)',
    borderColor: 'rgba(168, 85, 247, 0.3)',
  },
  benchmarkIndicator: {
    width: 8,
    height: 2,
    backgroundColor: '#94A3B8',
  },
  benchmarkIndicatorActive: {
    backgroundColor: '#A855F7',
  },
  benchmarkButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  benchmarkButtonTextActive: {
    color: '#A855F7',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  benchmarkDropdown: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    overflow: 'hidden',
    minWidth: 120,
  },
  benchmarkOption: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
  },
  benchmarkOptionActive: {
    backgroundColor: '#F3F4F6',
  },
  benchmarkOptionText: {
    fontSize: 14,
    color: '#1E293B',
  },
  benchmarkOptionTextActive: {
    color: '#A855F7',
    fontWeight: '600',
  },
  toggleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  toggleButtonActive: {
    backgroundColor: 'rgba(168, 85, 247, 0.1)',
    borderColor: 'rgba(168, 85, 247, 0.3)',
  },
  toggleButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  toggleButtonTextActive: {
    color: '#A855F7',
  },
  kpiSection: {
    padding: UI.spacing.md,
    paddingBottom: UI.spacing.sm,
  },
  kpiGrid: {
    gap: UI.spacing.md,
  },
  kpiCard: {
    gap: 8,
  },
  kpiHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  kpiLabel: {
    fontSize: 12,
    color: '#64748B',
    flex: 1,
  },
  kpiValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1E293B',
  },
  returnRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 12,
  },
  returnPercent: {
    fontSize: 18,
    fontWeight: '600',
  },
  positiveValue: {
    color: '#10B981',
  },
  negativeValue: {
    color: '#EF4444',
  },
  alphaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  alphaBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
  },
  alphaBadgePositive: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  alphaBadgeNegative: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  alphaValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  benchmarkReturnText: {
    fontSize: 12,
    color: '#94A3B8',
  },
  chartSection: {
    padding: UI.spacing.md,
    paddingBottom: UI.spacing.sm,
  },
  chartContainer: {
    backgroundColor: '#F8FAFC',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 16,
    overflow: 'hidden',
  },
  chart: {
    borderRadius: 16,
  },
  legend: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 24,
    marginTop: UI.spacing.md,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  legendLinePortfolio: {
    width: 32,
    height: 4,
    borderRadius: 2,
    backgroundColor: UI.colors.primary,
  },
  legendLineBenchmark: {
    width: 32,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#A855F7',
    opacity: 0.4,
  },
  legendText: {
    fontSize: 12,
    color: '#64748B',
  },
  footer: {
    padding: UI.spacing.md,
    paddingTop: UI.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    backgroundColor: '#F8FAFC',
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981',
  },
  statusText: {
    fontSize: 12,
    color: '#64748B',
  },
  footerLinkContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  footerLink: {
    fontSize: 12,
    color: UI.colors.primary,
    fontWeight: '500',
  },
  infoButton: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.4)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoModalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    maxWidth: '90%',
    maxHeight: '80%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  infoModalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: UI.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  infoModalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1E293B',
  },
  infoModalBody: {
    padding: UI.spacing.md,
    maxHeight: 400,
  },
  infoModalText: {
    fontSize: 14,
    color: '#475569',
    lineHeight: 22,
    marginBottom: UI.spacing.md,
  },
  formulaBox: {
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    padding: UI.spacing.md,
    marginBottom: UI.spacing.md,
  },
  formulaText: {
    fontSize: 12,
    fontFamily: 'monospace',
    color: UI.colors.primary,
  },
  exampleBox: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.3)',
    borderRadius: 12,
    padding: UI.spacing.md,
    marginBottom: UI.spacing.md,
  },
  exampleLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: UI.colors.primary,
    marginBottom: 4,
  },
  exampleText: {
    fontSize: 12,
    color: '#475569',
    lineHeight: 18,
  },
  interpretationBox: {
    borderWidth: 1,
    borderRadius: 12,
    padding: UI.spacing.md,
  },
  interpretationPositive: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  interpretationNegative: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  interpretationText: {
    fontSize: 12,
    fontWeight: '600',
  },
  infoModalFooter: {
    padding: UI.spacing.md,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  infoModalButton: {
    backgroundColor: UI.colors.primary,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
  infoModalButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  chartPlaceholder: {
    height: 256,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chartPlaceholderText: {
    fontSize: 14,
    color: '#64748B',
  },
  // AR Chart Styles
  arContainer: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  arHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: UI.spacing.md,
    paddingBottom: UI.spacing.md,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  arHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  arTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1E293B',
  },
  arSubtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  arCloseButton: {
    padding: 8,
  },
  arVisualizationArea: {
    flex: 1,
    backgroundColor: '#0F172A',
    position: 'relative',
  },
  arScrollContent: {
    paddingHorizontal: 20,
  },
  arCanvas: {
    width: Math.max(screenWidth - 40, 600),
    height: 300,
    position: 'relative',
    marginVertical: 20,
  },
  arChart3D: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  arChartSegment: {
    position: 'absolute',
    height: 4,
    borderRadius: 2,
  },
  arChartSegmentGradient: {
    flex: 1,
    borderRadius: 2,
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 8,
    elevation: 4,
  },
  arDataPoint: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.5,
    shadowRadius: 4,
    elevation: 4,
  },
  arDataPointGlow: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(16, 185, 129, 0.3)',
    top: -6,
    left: -6,
  },
  arCurrentPoint: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 3,
    borderColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 12,
    elevation: 8,
  },
  arCurrentPointGlow: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(16, 185, 129, 0.4)',
    top: -8,
    left: -8,
  },
  arGrid: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  arGridLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  arYAxis: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 60,
  },
  arYAxisLabel: {
    position: 'absolute',
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.6)',
    fontWeight: '500',
    transform: [{ translateY: -8 }],
  },
  arInstructions: {
    position: 'absolute',
    bottom: 100,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  arInstructionsText: {
    fontSize: 12,
    color: '#FFFFFF',
    textAlign: 'center',
    fontWeight: '500',
  },
  arStatsPanel: {
    flexDirection: 'row',
    padding: UI.spacing.md,
    backgroundColor: '#1E293B',
    gap: UI.spacing.sm,
  },
  arStatCard: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: UI.spacing.sm,
    alignItems: 'center',
  },
  arStatLabel: {
    fontSize: 10,
    color: '#94A3B8',
    marginBottom: 4,
  },
  arStatValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  arControls: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: UI.spacing.sm,
    padding: UI.spacing.md,
    backgroundColor: '#1E293B',
  },
  arControlButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  arFooter: {
    padding: UI.spacing.md,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    alignItems: 'center',
  },
  arFooterInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  arFooterDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981',
  },
  arFooterText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '600',
  },
  arFooterNote: {
    fontSize: 10,
    color: '#94A3B8',
    marginTop: 4,
  },
});
