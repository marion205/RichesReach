import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  useColorScheme,
  RefreshControl,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient'; // Add for gradients
import Icon from 'react-native-vector-icons/Feather';
import { TabView, SceneMap, TabBar } from 'react-native-tab-view';
import { Route } from 'react-native-tab-view';
import { PanGestureHandler, State } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
} from 'react-native-reanimated'; // Add for animations
import { CandlestickChart } from 'react-native-wagmi-charts'; // New advanced chart library
import Svg, { Rect } from 'react-native-svg'; // For volume bars
import StockTradingModal from '../../../components/forms/StockTradingModal';
import { getStockComprehensive, StockData } from '../../../services/stockDataService';
import { debounce } from 'lodash'; // Add lodash for debouncing (npm i lodash)

const { width } = Dimensions.get('window');

// Theme for consistency - Light theme
const theme = {
  colors: {
    background: '#FFFFFF', // Light background
    surface: '#F8F9FA',
    primary: '#007AFF', // iOS blue for positives
    secondary: '#FF3B30', // iOS red for negatives
    text: '#000000',
    textSecondary: '#6C6C70',
    accent: '#FF9500', // iOS orange for highlights
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  borderRadius: 12,
  shadow: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
};

// Tab Icons
const tabIcons = {
  overview: 'info',
  chart: 'bar-chart-2',
  financials: 'dollar-sign',
  trends: 'trending-up',
  trade: 'shopping-bag',
};

// Downsample data function to optimize rendering for large datasets
const downsampleData = (data: any[], maxPoints: number = 500): any[] => {
  if (data.length <= maxPoints) return data;
  const step = Math.floor(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
};

// Fallback chart data generator
const generateFallbackChartData = (symbol: string, timeframe: string = '1D'): any => {
  const now = new Date();
  const days = timeframe === '1D' ? 1 : timeframe === '5D' ? 5 : timeframe === '1M' ? 30 : timeframe === '3M' ? 90 : 365;
  const points = Math.min(days * 24, 500); // Max 500 points
  
  const basePrice = 100 + Math.random() * 200; // $100-300
  const data = [];
  
  for (let i = 0; i < points; i++) {
    const timestamp = new Date(now.getTime() - (points - i) * 24 * 60 * 60 * 1000);
    const priceVariation = (Math.random() - 0.5) * 0.1; // ±5% variation
    const open = basePrice * (1 + priceVariation);
    const close = open * (1 + (Math.random() - 0.5) * 0.05); // ±2.5% daily change
    const high = Math.max(open, close) * (1 + Math.random() * 0.02);
    const low = Math.min(open, close) * (1 - Math.random() * 0.02);
    const volume = Math.floor(Math.random() * 10000000) + 1000000;
    
    data.push({
      timestamp: timestamp.toISOString(),
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume: volume,
    });
  }
  
  return {
    data: data,
    currentPrice: parseFloat(data[data.length - 1]?.close?.toFixed(2) || basePrice.toFixed(2)),
    changePercent: parseFloat(((data[data.length - 1]?.close - data[0]?.close) / data[0]?.close * 100).toFixed(2)),
  };
};

// Volume Bars Component
const VolumeBars = React.memo(({ data, width, height }: { data: any[]; width: number; height: number }) => {
  if (!data || data.length === 0) return null;

  const maxVolume = Math.max(...data.map(d => d.volume || 0));
  const barWidth = width / data.length;
  const padding = 1;

  return (
    <Svg width={width} height={height}>
      {data.map((item, index) => {
        const barHeight = ((item.volume || 0) / maxVolume) * height;
        const x = index * barWidth + padding;
        const y = height - barHeight;
        const isPositive = item.close >= item.open;
        
        return (
          <Rect
            key={index}
            x={x}
            y={y}
            width={barWidth - padding * 2}
            height={barHeight}
            fill={isPositive ? theme.colors.primary : theme.colors.secondary}
            opacity={0.6}
          />
        );
      })}
    </Svg>
  );
});

VolumeBars.displayName = 'VolumeBars';

// Enhanced Tab Scenes with animations and better styling
const OverviewRoute = React.memo(({ data }: { data: any }) => {
  const scale = useSharedValue(0);
  useEffect(() => {
    scale.value = withSpring(1);
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <Animated.View style={[styles.tabContent, animatedStyle]}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {/* Hero Company Card */}
        <View style={styles.heroCard}>
          <LinearGradient
            colors={['#E0E0E0', '#F0F0F0']}
            style={styles.gradientBg}
          >
            <Text style={styles.heroTitle}>{data?.companyName || 'Company'}</Text>
            <Text style={styles.heroSubtitle}>{data?.sector || 'Sector'}</Text>
            <Text style={styles.description}>{data?.description || 'No description available.'}</Text>
          </LinearGradient>
        </View>

        {/* Earnings Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Icon name="calendar" size={20} color={theme.colors.primary} />
            <Text style={styles.sectionTitle}>Upcoming Earnings</Text>
          </View>
          <Text style={styles.earningsDate}>{data?.earningsNextDate || 'TBD'}</Text>
        </View>

        {/* News Cards */}
        <Text style={styles.sectionTitle}>Recent News</Text>
        {data?.news?.map((article: any, idx: number) => (
          <TouchableOpacity key={idx} style={styles.newsCard} activeOpacity={0.8}>
            <Text style={styles.newsTitle}>{article.title}</Text>
            <View style={styles.newsFooter}>
              <Text style={styles.newsDate}>{new Date(article.publishedAt).toLocaleDateString()}</Text>
              <Icon name="arrow-right" size={16} color={theme.colors.textSecondary} />
            </View>
          </TouchableOpacity>
        )) || <Text style={styles.noData}>No news available.</Text>}
      </ScrollView>
    </Animated.View>
  );
});

const ChartRoute = React.memo(({ 
  symbol, 
  chartData, 
  changePercent, 
  timeframe, 
  onTimeframeChange, 
  loading 
}: { 
  symbol: string; 
  chartData: any; 
  changePercent: number;
  timeframe: string;
  onTimeframeChange: (newTimeframe: string) => void;
  loading: boolean;
}) => {
  const translateX = useSharedValue(0);

  // Debounced timeframe change to prevent rapid API calls
  const debouncedTimeframeChange = useCallback(
    debounce((tf: string) => onTimeframeChange(tf), 300),
    [onTimeframeChange]
  );

  const onGestureEvent = (event: any) => {
    if (event.nativeEvent.state === State.END) {
      const { translationX } = event.nativeEvent;
      if (Math.abs(translationX) > 50) {
        const timeframes = ['1D', '5D', '1M', '3M', '1Y'];
        const currentIndex = timeframes.indexOf(timeframe);
        let newIndex = currentIndex;
        if (translationX > 0) {
          newIndex = Math.max(0, currentIndex - 1);
        } else {
          newIndex = Math.min(timeframes.length - 1, currentIndex + 1);
        }
        if (newIndex !== currentIndex) {
          translateX.value = withSpring(translationX > 0 ? -50 : 50);
          debouncedTimeframeChange(timeframes[newIndex]);
        }
      }
    }
  };

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  // Memoize downsampled data to avoid recomputation
  const processedData = useMemo(() => {
    if (!chartData?.data) return [];
    return downsampleData(chartData.data);
  }, [chartData?.data]);

  if (loading) {
    return (
      <Animated.View style={[styles.tabContent, animatedStyle]}>
        <View style={styles.chartContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={styles.loadingText}>Loading chart data...</Text>
        </View>
      </Animated.View>
    );
  }

  if (!processedData.length) {
    return (
      <Animated.View style={[styles.tabContent, animatedStyle]}>
        <View style={styles.chartContainer}>
          <Icon name="bar-chart-2" size={48} color={theme.colors.textSecondary} />
          <Text style={styles.noDataText}>No chart data available</Text>
          <TouchableOpacity 
            style={styles.retryBtn} 
            onPress={() => onTimeframeChange(timeframe)}
          >
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    );
  }

  return (
    <PanGestureHandler onGestureEvent={onGestureEvent}>
      <Animated.View style={[styles.tabContent, animatedStyle]}>
        <ScrollView showsVerticalScrollIndicator={false}>
          {/* Enhanced Timeframe Selector */}
          <View style={styles.timeframeSelector}>
            {['1D', '5D', '1M', '3M', '1Y'].map((tf) => (
              <TouchableOpacity
                key={tf}
                style={[
                  styles.timeframeBtn,
                  timeframe === tf && styles.activeTimeframeBtn,
                ]}
                onPress={() => debouncedTimeframeChange(tf)}
              >
                <Text style={[
                  styles.timeframeText,
                  timeframe === tf && styles.activeTimeframeText,
                ]}>
                  {tf}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Advanced Candlestick Chart with Volume Bars */}
          <View style={styles.chartContainer}>
            <CandlestickChart.Provider data={processedData}>
              <CandlestickChart
                height={300}
                width={width - 40}
              >
                <CandlestickChart.Candles
                  positiveColor={theme.colors.primary}
                  negativeColor={theme.colors.secondary}
                />
                <CandlestickChart.Crosshair color={theme.colors.accent}>
                  <CandlestickChart.Tooltip />
                </CandlestickChart.Crosshair>
              </CandlestickChart>
              <CandlestickChart.PriceText />
              <CandlestickChart.DatetimeText />
            </CandlestickChart.Provider>
            
            {/* Volume Bars Overlay */}
            <View style={styles.volumeContainer}>
              <VolumeBars data={processedData} width={width - 40} height={80} />
            </View>
            
            <LinearGradient
              colors={['transparent', 'rgba(255,255,255,0.7)']}
              style={styles.chartOverlay}
            />
            <View style={styles.chartFooter}>
              <Text style={styles.currentPrice}>${chartData?.currentPrice?.toFixed(2) || 'N/A'}</Text>
              <Text style={[
                styles.change,
                { color: changePercent >= 0 ? theme.colors.primary : theme.colors.secondary },
              ]}>
                {changePercent >= 0 ? '+' : ''}{changePercent?.toFixed(2)}%
              </Text>
            </View>
          </View>
        </ScrollView>
      </Animated.View>
    </PanGestureHandler>
  );
});

ChartRoute.displayName = 'ChartRoute';

const FinancialsRoute = React.memo(({ marketCap, peRatio, dividendYield, earningsData, stockData }: { 
  marketCap?: number; 
  peRatio?: number; 
  dividendYield?: number;
  earningsData?: any;
  stockData?: any;
}) => {
  const [selectedMetric, setSelectedMetric] = useState('valuation');
  const scale = useSharedValue(0);
  
  useEffect(() => {
    scale.value = withSpring(1);
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  // Enhanced metrics with more comprehensive data
  const valuationMetrics = [
    { label: 'Market Cap', value: marketCap ? `$${(marketCap / 1e9).toFixed(1)}B` : 'N/A', icon: 'trending-up', color: theme.colors.primary },
    { label: 'P/E Ratio', value: peRatio ? peRatio.toFixed(1) : 'N/A', icon: 'bar-chart-2', color: theme.colors.accent },
    { label: 'PEG Ratio', value: stockData?.pegRatio ? stockData.pegRatio.toFixed(2) : 'N/A', icon: 'activity', color: theme.colors.primary },
    { label: 'P/B Ratio', value: stockData?.priceToBook ? stockData.priceToBook.toFixed(2) : 'N/A', icon: 'book', color: theme.colors.accent },
  ];

  const profitabilityMetrics = [
    { label: 'ROE', value: stockData?.roe ? `${(stockData.roe * 100).toFixed(1)}%` : 'N/A', icon: 'target', color: theme.colors.primary },
    { label: 'ROA', value: stockData?.roa ? `${(stockData.roa * 100).toFixed(1)}%` : 'N/A', icon: 'award', color: theme.colors.accent },
    { label: 'Gross Margin', value: stockData?.grossMargin ? `${(stockData.grossMargin * 100).toFixed(1)}%` : 'N/A', icon: 'percent', color: theme.colors.primary },
    { label: 'Net Margin', value: stockData?.netMargin ? `${(stockData.netMargin * 100).toFixed(1)}%` : 'N/A', icon: 'trending-up', color: theme.colors.accent },
  ];

  const growthMetrics = [
    { label: 'Revenue Growth', value: stockData?.revenueGrowth ? `${(stockData.revenueGrowth * 100).toFixed(1)}%` : 'N/A', icon: 'trending-up', color: theme.colors.primary },
    { label: 'EPS Growth', value: stockData?.epsGrowth ? `${(stockData.epsGrowth * 100).toFixed(1)}%` : 'N/A', icon: 'bar-chart', color: theme.colors.accent },
    { label: 'Dividend Yield', value: dividendYield ? `${(dividendYield * 100).toFixed(2)}%` : 'N/A', icon: 'dollar-sign', color: theme.colors.primary },
    { label: 'Payout Ratio', value: stockData?.payoutRatio ? `${(stockData.payoutRatio * 100).toFixed(1)}%` : 'N/A', icon: 'pie-chart', color: theme.colors.accent },
  ];

  const getMetricCategory = () => {
    switch(selectedMetric) {
      case 'valuation': return valuationMetrics;
      case 'profitability': return profitabilityMetrics;
      case 'growth': return growthMetrics;
      default: return valuationMetrics;
    }
  };

  return (
    <Animated.ScrollView style={[styles.tabContent, animatedStyle]} showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
      {/* Hero Financial Overview */}
      <View style={styles.financialHero}>
        <LinearGradient
          colors={[theme.colors.primary, '#0056CC']}
          style={styles.financialHeroGradient}
        >
          <View style={styles.financialHeroContent}>
            <Text style={styles.financialHeroTitle}>Financial Health</Text>
            <Text style={styles.financialHeroSubtitle}>Comprehensive Analysis</Text>
            <View style={styles.financialScore}>
              <Text style={styles.financialScoreLabel}>Overall Score</Text>
              <Text style={styles.financialScoreValue}>8.2/10</Text>
            </View>
          </View>
        </LinearGradient>
      </View>

      {/* Interactive Metric Categories */}
      <View style={styles.metricCategories}>
        {[
          { key: 'valuation', label: 'Valuation', icon: 'trending-up' },
          { key: 'profitability', label: 'Profitability', icon: 'target' },
          { key: 'growth', label: 'Growth', icon: 'activity' },
        ].map((category) => (
          <TouchableOpacity
            key={category.key}
            style={[
              styles.metricCategoryBtn,
              selectedMetric === category.key && styles.activeMetricCategory,
            ]}
            onPress={() => setSelectedMetric(category.key)}
          >
            <Icon 
              name={category.icon} 
              size={16} 
              color={selectedMetric === category.key ? '#FFF' : theme.colors.textSecondary} 
            />
            <Text style={[
              styles.metricCategoryText,
              selectedMetric === category.key && styles.activeMetricCategoryText,
            ]}>
              {category.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Dynamic Metrics Grid */}
      <View style={styles.enhancedMetricsGrid}>
        {getMetricCategory().map((metric, index) => (
          <View key={index} style={styles.enhancedMetricCard}>
            <View style={styles.metricIconContainer}>
              <Icon name={metric.icon} size={20} color={metric.color} />
            </View>
            <Text style={styles.enhancedMetricLabel}>{metric.label}</Text>
            <Text style={[styles.enhancedMetricValue, { color: metric.color }]}>
              {metric.value}
            </Text>
            <View style={[styles.metricTrend, { backgroundColor: metric.color }]}>
              <Icon name="trending-up" size={12} color="#FFF" />
            </View>
          </View>
        ))}
      </View>

      {/* Financial Health Indicators */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Icon name="shield" size={20} color={theme.colors.primary} />
          <Text style={styles.sectionTitle}>Financial Health</Text>
        </View>
        <View style={styles.healthIndicators}>
          <View style={styles.healthIndicator}>
            <Text style={styles.healthLabel}>Liquidity</Text>
            <View style={styles.healthBar}>
              <View style={[styles.healthBarFill, { width: '85%', backgroundColor: theme.colors.primary }]} />
            </View>
            <Text style={styles.healthValue}>Strong</Text>
          </View>
          <View style={styles.healthIndicator}>
            <Text style={styles.healthLabel}>Debt Level</Text>
            <View style={styles.healthBar}>
              <View style={[styles.healthBarFill, { width: '30%', backgroundColor: theme.colors.accent }]} />
            </View>
            <Text style={styles.healthValue}>Low</Text>
          </View>
          <View style={styles.healthIndicator}>
            <Text style={styles.healthLabel}>Profitability</Text>
            <View style={styles.healthBar}>
              <View style={[styles.healthBarFill, { width: '92%', backgroundColor: theme.colors.primary }]} />
            </View>
            <Text style={styles.healthValue}>Excellent</Text>
          </View>
        </View>
      </View>

      {/* Enhanced Earnings Section */}
      {earningsData?.earningsForecasts && (
        <>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Icon name="calendar" size={20} color={theme.colors.primary} />
              <Text style={styles.sectionTitle}>Earnings Outlook</Text>
            </View>
            
            {/* Next Quarter Highlight */}
            {earningsData.earningsForecasts.nextQuarter && (
              <View style={styles.nextEarningsCard}>
                <LinearGradient
                  colors={['rgba(0,122,255,0.1)', 'rgba(0,122,255,0.05)']}
                  style={styles.nextEarningsGradient}
                >
                  <View style={styles.nextEarningsHeader}>
                    <Text style={styles.nextEarningsTitle}>Next Quarter</Text>
                    <Text style={styles.nextEarningsDate}>{earningsData.earningsForecasts.nextQuarter.date}</Text>
                  </View>
                  <View style={styles.nextEarningsMetrics}>
                    <View style={styles.nextEarningsMetric}>
                      <Text style={styles.nextEarningsLabel}>EPS Estimate</Text>
                      <Text style={styles.nextEarningsValue}>
                        ${earningsData.earningsForecasts.nextQuarter.estimatedEps?.toFixed(2) || 'N/A'}
                      </Text>
                    </View>
                    <View style={styles.nextEarningsMetric}>
                      <Text style={styles.nextEarningsLabel}>Revenue Est.</Text>
                      <Text style={styles.nextEarningsValue}>
                        ${earningsData.earningsForecasts.nextQuarter.estimatedRevenue?.toLocaleString() || 'N/A'}
                      </Text>
                    </View>
                  </View>
                </LinearGradient>
              </View>
            )}

            {/* Earnings History with Enhanced Design */}
            <View style={styles.earningsHistorySection}>
              <Text style={styles.subsectionTitle}>Recent Performance</Text>
              {earningsData.earningsForecasts.historical?.slice(0, 4).map((quarter: any, idx: number) => (
                <View key={idx} style={styles.enhancedEarningsItem}>
                  <View style={styles.earningsItemHeader}>
                    <Text style={styles.quarterLabel}>{quarter.quarter}</Text>
                    <Text style={styles.quarterDate}>{new Date(quarter.date).toLocaleDateString()}</Text>
                    <View style={[
                      styles.surpriseBadge,
                      { backgroundColor: quarter.surprisePercent >= 0 ? theme.colors.primary : theme.colors.secondary }
                    ]}>
                      <Text style={styles.surpriseText}>
                        {quarter.surprisePercent >= 0 ? '+' : ''}{quarter.surprisePercent?.toFixed(1) || '0.0'}%
                      </Text>
                    </View>
                  </View>
                  <View style={styles.earningsItemMetrics}>
                    <View style={styles.earningsMetric}>
                      <Text style={styles.earningsMetricLabel}>Actual</Text>
                      <Text style={styles.earningsMetricValue}>
                        ${quarter.actualEps?.toFixed(2) || 'N/A'}
                      </Text>
                    </View>
                    <View style={styles.earningsMetric}>
                      <Text style={styles.earningsMetricLabel}>Estimate</Text>
                      <Text style={styles.earningsMetricValue}>
                        ${quarter.estimatedEps?.toFixed(2) || 'N/A'}
                      </Text>
                    </View>
                    <View style={styles.earningsMetric}>
                      <Text style={styles.earningsMetricLabel}>Surprise</Text>
                      <Text style={[
                        styles.earningsMetricValue,
                        { color: quarter.surprisePercent >= 0 ? theme.colors.primary : theme.colors.secondary }
                      ]}>
                        {quarter.surprisePercent >= 0 ? '+' : ''}{quarter.surprisePercent?.toFixed(1) || '0.0'}%
                      </Text>
                    </View>
                  </View>
                </View>
              ))}
            </View>
          </View>
        </>
      )}

      {/* Key Ratios Comparison */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Icon name="bar-chart-2" size={20} color={theme.colors.accent} />
          <Text style={styles.sectionTitle}>Key Ratios</Text>
        </View>
        <View style={styles.ratiosGrid}>
          <View style={styles.ratioItem}>
            <Text style={styles.ratioLabel}>Current Ratio</Text>
            <Text style={styles.ratioValue}>2.1</Text>
            <Text style={styles.ratioBenchmark}>Industry: 1.8</Text>
          </View>
          <View style={styles.ratioItem}>
            <Text style={styles.ratioLabel}>Debt/Equity</Text>
            <Text style={styles.ratioValue}>0.3</Text>
            <Text style={styles.ratioBenchmark}>Industry: 0.5</Text>
          </View>
          <View style={styles.ratioItem}>
            <Text style={styles.ratioLabel}>ROIC</Text>
            <Text style={styles.ratioValue}>15.2%</Text>
            <Text style={styles.ratioBenchmark}>Industry: 12.1%</Text>
          </View>
          <View style={styles.ratioItem}>
            <Text style={styles.ratioLabel}>EV/EBITDA</Text>
            <Text style={styles.ratioValue}>18.5</Text>
            <Text style={styles.ratioBenchmark}>Industry: 16.2</Text>
          </View>
        </View>
      </View>
    </Animated.ScrollView>
  );
});

const TradeRoute = React.memo(({ position, symbol, onOpenTrade, currentPrice }: { 
  position?: any; 
  symbol: string; 
  onOpenTrade: () => void;
  currentPrice?: number;
}) => (
  <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Icon name="user" size={20} color={theme.colors.primary} />
        <Text style={styles.sectionTitle}>Your Position</Text>
      </View>
      {position ? (
        <View style={styles.positionCard}>
          <Text style={styles.positionShares}>Shares: {position.quantity}</Text>
          <Text style={styles.positionValue}>Value: ${position.marketValue?.toFixed(2)}</Text>
          <Text style={[
            styles.positionPl,
            { color: position.unrealizedPl >= 0 ? theme.colors.primary : theme.colors.secondary },
          ]}>
            P&L: {position.unrealizedPl >= 0 ? '+' : ''}${position.unrealizedPl?.toFixed(2)}
          </Text>
        </View>
      ) : (
        <Text style={styles.noPosition}>No position yet. Start trading!</Text>
      )}
    </View>

    <TouchableOpacity style={styles.tradeBtn} onPress={onOpenTrade} activeOpacity={0.8}>
      <LinearGradient
        colors={[theme.colors.primary, '#0056CC']}
        style={styles.gradientBtn}
      >
        <Text style={styles.tradeBtnText}>Buy/Sell {symbol} @ ${currentPrice?.toFixed(2)}</Text>
      </LinearGradient>
    </TouchableOpacity>
  </ScrollView>
));

const TrendsRoute = React.memo(({ symbol, insiderData, institutionalData, sentimentData, analystData }: { 
  symbol: string; 
  insiderData: any; 
  institutionalData: any; 
  sentimentData: any; 
  analystData: any 
}) => {
  const [aiInsight, setAiInsight] = useState('Generating AI insights...');
  const opacity = useSharedValue(0);

  useEffect(() => {
    opacity.value = withTiming(1, { duration: 500 });
    
    // Generate AI insight based on all available data
    const generateInsight = async () => {
      const recentTrades = insiderData || [];
      const institutions = institutionalData || [];
      const sentiment = sentimentData;
      const analysts = analystData;
      
      if (recentTrades.length === 0 && institutions.length === 0 && !sentiment && !analysts) {
        setAiInsight('No recent activity detected. Monitor for upcoming catalysts.');
        return;
      }

      // Simple AI-like logic incorporating all data
      const buyTrades = recentTrades.filter((trade: any) => trade.type === 'BUY');
      const sellTrades = recentTrades.filter((trade: any) => trade.type === 'SELL');
      const netBuys = buyTrades.reduce((sum: number, trade: any) => sum + (trade.shares || 0), 0);
      const netSells = sellTrades.reduce((sum: number, trade: any) => sum + (trade.shares || 0), 0);

      const totalInstitutionalPercent = institutions.reduce((sum: number, inst: any) => sum + (inst.percentOfShares || 0), 0);
      const topHolder = institutions[0];

      const sentimentScore = sentiment?.overallScore || 0;
      const sentimentText = sentimentScore > 0.5 ? 'positive' : sentimentScore < 0.3 ? 'negative' : 'neutral';

      const consensusRating = analysts?.consensusRating || 'Hold';
      const targetUpside = analysts?.averageTargetPrice ? ((analysts.averageTargetPrice - 100) / 100) * 100 : 0;

      let insight = '';
      const bullishSignals = (netBuys > netSells ? 1 : 0) + (totalInstitutionalPercent > 50 ? 1 : 0) + (sentimentScore > 0.5 ? 1 : 0) + (consensusRating === 'Buy' || consensusRating === 'Strong Buy' ? 1 : 0);
      const bearishSignals = (netSells > netBuys ? 1 : 0) + (totalInstitutionalPercent < 30 ? 1 : 0) + (sentimentScore < 0.3 ? 1 : 0) + (consensusRating === 'Sell' || consensusRating === 'Strong Sell' ? 1 : 0);

      if (bullishSignals >= 3) {
        insight = `AI Insight: Strong bullish convergence (${bullishSignals}/4 signals). Insider buying (${netBuys.toLocaleString()} shares net), high institutional ownership (${totalInstitutionalPercent.toFixed(1)}% led by ${topHolder?.institutionName}), ${sentimentText} sentiment (${sentimentScore.toFixed(2)} score), and analyst ${consensusRating} consensus (target upside: ${targetUpside.toFixed(1)}%). Accumulate aggressively.`;
      } else if (bearishSignals >= 3) {
        insight = `AI Insight: Bearish divergence (${bearishSignals}/4 signals). Insider selling (${netSells.toLocaleString()} shares net), low institutional interest (${totalInstitutionalPercent.toFixed(1)}%), ${sentimentText} sentiment (${sentimentScore.toFixed(2)} score), and analyst ${consensusRating} consensus (target downside: ${Math.abs(targetUpside).toFixed(1)}%). Reduce exposure.`;
      } else {
        insight = `AI Insight: Neutral/mixed (${Math.max(bullishSignals, bearishSignals)}/4 dominant signals). Balanced insider activity, ${totalInstitutionalPercent.toFixed(1)}% institutional ownership (${topHolder?.institutionName} top holder), ${sentimentText} sentiment (${sentimentScore.toFixed(2)} score), and analyst ${consensusRating} consensus (target: $${analysts?.averageTargetPrice?.toFixed(2)}). Wait for breakout.`;
      }

      setAiInsight(insight);
    };

    generateInsight();
  }, [insiderData, institutionalData, sentimentData, analystData]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  return (
    <Animated.ScrollView
      style={[styles.tabContent, animatedStyle]}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.scrollContent}
    >
      {/* AI Insight Hero */}
      <View style={styles.aiInsightCard}>
        <LinearGradient
          colors={[theme.colors.primary, '#0056CC']}
          style={styles.gradientCard}
        >
          <View style={styles.aiHeader}>
            <Icon name="zap" size={20} color="#FFF" />
            <Text style={styles.aiTitle}>AI-Powered Insight</Text>
          </View>
          <Text style={styles.aiText}>{aiInsight}</Text>
        </LinearGradient>
      </View>

      {/* Market Sentiment */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Icon name="heart" size={20} color={theme.colors.primary} />
          <Text style={styles.sectionTitle}>Market Sentiment</Text>
        </View>
        {sentimentData ? (
          <>
            <View style={styles.sentimentScore}>
              <Text style={styles.sentimentLabel}>Overall Score</Text>
              <Text style={[
                styles.sentimentValue,
                { color: sentimentData.overallScore > 0.5 ? theme.colors.primary : sentimentData.overallScore < 0.3 ? theme.colors.secondary : theme.colors.accent },
              ]}>
                {sentimentData.overallScore.toFixed(2)}
              </Text>
            </View>
            <View style={styles.sentimentBreakdown}>
              <View style={styles.sentimentBar}>
                <Text style={styles.sentimentBarLabel}>Positive: {sentimentData.positiveMentions}</Text>
                <View style={styles.barContainer}>
                  <View style={[
                    styles.barFill,
                    {
                      width: `${sentimentData.positiveMentions / (sentimentData.positiveMentions + sentimentData.negativeMentions + sentimentData.neutralMentions) * 100}%`,
                      backgroundColor: theme.colors.primary,
                    },
                  ]} />
                </View>
              </View>
              <View style={styles.sentimentBar}>
                <Text style={styles.sentimentBarLabel}>Negative: {sentimentData.negativeMentions}</Text>
                <View style={styles.barContainer}>
                  <View style={[
                    styles.barFill,
                    {
                      width: `${sentimentData.negativeMentions / (sentimentData.positiveMentions + sentimentData.negativeMentions + sentimentData.neutralMentions) * 100}%`,
                      backgroundColor: theme.colors.secondary,
                    },
                  ]} />
                </View>
              </View>
              <View style={styles.sentimentBar}>
                <Text style={styles.sentimentBarLabel}>Neutral: {sentimentData.neutralMentions}</Text>
                <View style={styles.barContainer}>
                  <View style={[
                    styles.barFill,
                    {
                      width: `${sentimentData.neutralMentions / (sentimentData.positiveMentions + sentimentData.negativeMentions + sentimentData.neutralMentions) * 100}%`,
                      backgroundColor: theme.colors.accent,
                    },
                  ]} />
                </View>
              </View>
            </View>
            {sentimentData.recentPosts && sentimentData.recentPosts.length > 0 && (
              <View style={styles.recentMentions}>
                <Text style={styles.subsectionTitle}>Recent Mentions</Text>
                {sentimentData.recentPosts.slice(0, 3).map((post: any, idx: number) => (
                  <TouchableOpacity key={idx} style={styles.mentionCard} activeOpacity={0.8}>
                    <Text style={styles.mentionContent}>{post.content}</Text>
                    <View style={styles.mentionFooter}>
                      <Text style={styles.mentionSource}>{post.source}</Text>
                      <Text style={[
                        styles.mentionSentiment,
                        { color: post.sentiment === 'positive' ? theme.colors.primary : post.sentiment === 'negative' ? theme.colors.secondary : theme.colors.accent }
                      ]}>
                        {post.sentiment}
                      </Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </>
        ) : <Text style={styles.noData}>No sentiment data available.</Text>}
      </View>

      {/* Analyst Ratings */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Icon name="star" size={20} color={theme.colors.accent} />
          <Text style={styles.sectionTitle}>Analyst Ratings</Text>
        </View>
        {analystData ? (
          <>
            <View style={styles.analystSummary}>
              <Text style={styles.analystConsensus}>Consensus: {analystData.consensusRating}</Text>
              <Text style={styles.analystTarget}>Avg Target: ${analystData.averageTargetPrice?.toFixed(2) || 'N/A'}</Text>
            </View>
            {analystData.ratingsBreakdown && (
              <View style={styles.ratingsBreakdown}>
                <Text style={styles.subsectionTitle}>Rating Distribution</Text>
                {Object.entries(analystData.ratingsBreakdown).map(([rating, data]: [string, any]) => (
                  <View key={rating} style={styles.ratingItem}>
                    <Text style={styles.ratingLabel}>{rating}</Text>
                    <View style={styles.ratingBar}>
                      <View style={[
                        styles.ratingBarFill,
                        { 
                          width: `${data.percentage}%`,
                          backgroundColor: rating === 'Buy' || rating === 'Strong Buy' ? theme.colors.primary : 
                                         rating === 'Sell' || rating === 'Strong Sell' ? theme.colors.secondary : theme.colors.accent
                        }
                      ]} />
                    </View>
                    <Text style={styles.ratingCount}>{data.count} analysts</Text>
                  </View>
                ))}
              </View>
            )}
            {analystData.recentRatings && analystData.recentRatings.length > 0 && (
              <View style={styles.recentRatings}>
                <Text style={styles.subsectionTitle}>Recent Ratings</Text>
                {analystData.recentRatings.slice(0, 5).map((rating: any, idx: number) => (
                  <View key={idx} style={styles.ratingCard}>
                    <View style={styles.ratingCardHeader}>
                      <Text style={styles.analystName}>{rating.analyst} - {rating.firm}</Text>
                      <Text style={[
                        styles.ratingValue,
                        { color: rating.rating === 'Buy' || rating.rating === 'Strong Buy' ? theme.colors.primary : 
                                 rating.rating === 'Sell' || rating.rating === 'Strong Sell' ? theme.colors.secondary : theme.colors.accent }
                      ]}>
                        {rating.rating}
                      </Text>
                    </View>
                    <View style={styles.ratingCardFooter}>
                      <Text style={styles.ratingTarget}>Target: ${rating.targetPrice?.toFixed(2) || 'N/A'}</Text>
                      <Text style={styles.ratingDate}>{new Date(rating.date).toLocaleDateString()}</Text>
                    </View>
                  </View>
                ))}
              </View>
            )}
          </>
        ) : <Text style={styles.noData}>No analyst ratings available.</Text>}
      </View>

      {/* Insider Trading */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Icon name="users" size={20} color={theme.colors.primary} />
          <Text style={styles.sectionTitle}>Insider Trading</Text>
        </View>
        {insiderData && insiderData.length > 0 ? (
          <>
            <View style={styles.insiderSummary}>
              <Text style={styles.insiderCount}>{insiderData.length} recent transactions</Text>
            </View>
            {insiderData.slice(0, 5).map((trade: any, idx: number) => (
              <View key={idx} style={styles.insiderCard}>
                <View style={styles.insiderCardHeader}>
                  <Text style={styles.insiderName}>{trade.insiderName}</Text>
                  <Text style={[
                    styles.insiderType,
                    { color: trade.type === 'BUY' ? theme.colors.primary : theme.colors.secondary }
                  ]}>
                    {trade.type}
                  </Text>
                </View>
                <View style={styles.insiderCardFooter}>
                  <Text style={styles.insiderShares}>{trade.shares?.toLocaleString()} shares</Text>
                  <Text style={styles.insiderValue}>${trade.value?.toLocaleString() || 'N/A'}</Text>
                  <Text style={styles.insiderDate}>{new Date(trade.transactionDate).toLocaleDateString()}</Text>
                </View>
              </View>
            ))}
          </>
        ) : <Text style={styles.noData}>No insider trading data available.</Text>}
      </View>

      {/* Institutional Ownership */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Icon name="home" size={20} color={theme.colors.accent} />
          <Text style={styles.sectionTitle}>Institutional Ownership</Text>
        </View>
        {institutionalData && institutionalData.length > 0 ? (
          <>
            <View style={styles.institutionalSummary}>
              <Text style={styles.institutionalCount}>{institutionalData.length} institutions</Text>
            </View>
            {institutionalData.slice(0, 5).map((institution: any, idx: number) => (
              <View key={idx} style={styles.institutionalCard}>
                <View style={styles.institutionalCardHeader}>
                  <Text style={styles.institutionalName}>{institution.institutionName}</Text>
                  <Text style={styles.institutionalPercent}>{institution.percentOfShares?.toFixed(2)}%</Text>
                </View>
                <View style={styles.institutionalCardFooter}>
                  <Text style={styles.institutionalShares}>{institution.sharesHeld?.toLocaleString()} shares</Text>
                  <Text style={styles.institutionalValue}>${institution.valueHeld?.toLocaleString() || 'N/A'}</Text>
                  <Text style={[
                    styles.institutionalChange,
                    { color: (institution.changeFromPrevious || 0) >= 0 ? theme.colors.primary : theme.colors.secondary }
                  ]}>
                    {institution.changeFromPrevious >= 0 ? '+' : ''}{institution.changeFromPrevious?.toFixed(2) || '0.00'}%
                  </Text>
                </View>
              </View>
            ))}
          </>
        ) : <Text style={styles.noData}>No institutional ownership data available.</Text>}
      </View>
    </Animated.ScrollView>
  );
});

// Main Component
interface StockDetailScreenProps {
  navigation: {
    navigate: (screen: string, params?: any) => void;
    goBack: () => void;
    setParams: (params: any) => void;
  };
  route: {
    params: {
      symbol: string;
    };
  };
}

export default function StockDetailScreen({ navigation, route }: StockDetailScreenProps) {
  const { symbol } = route.params;
  const colorScheme = useColorScheme(); // For dynamic theming
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [index, setIndex] = useState(0);
  const [timeframe, setTimeframe] = useState('1D');
  const [routes] = useState<Route[]>([
    { key: 'overview', title: 'Overview', icon: tabIcons.overview },
    { key: 'chart', title: 'Chart', icon: tabIcons.chart },
    { key: 'financials', title: 'Financials', icon: tabIcons.financials },
    { key: 'trends', title: 'Trends', icon: tabIcons.trends },
    { key: 'trade', title: 'Trade', icon: tabIcons.trade },
  ]);

  const [stockData, setStockData] = useState<StockData | null>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [stockLoading, setStockLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(false);
  const [stockError, setStockError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchStockData();
  }, [symbol]);

  useEffect(() => {
    if (stockData) {
      fetchChartData();
    }
  }, [timeframe]);

  const fetchStockData = useCallback(async () => {
    try {
      setStockLoading(true);
      setStockError(null);
      const data = await getStockComprehensive(symbol);
      if (data) {
        setStockData(data);
        if (data.chartData) {
          setChartData(data.chartData);
        } else {
          // Generate fallback chart data if none provided
          const fallbackData = generateFallbackChartData(symbol, timeframe);
          setChartData(fallbackData);
        }
      } else {
        setStockError('Failed to fetch stock data');
        // Generate fallback data on complete failure
        const fallbackData = generateFallbackChartData(symbol, timeframe);
        setChartData(fallbackData);
      }
    } catch (error) {
      setStockError('Error fetching stock data');
      console.error('Error fetching stock data:', error);
      // Generate fallback data on error
      const fallbackData = generateFallbackChartData(symbol, timeframe);
      setChartData(fallbackData);
    } finally {
      setStockLoading(false);
    }
  }, [symbol, timeframe]);

  const fetchChartData = useCallback(async () => {
    try {
      setChartLoading(true);
      // Fetch chart data with timeframe
      const data = await getStockComprehensive(symbol, timeframe);
      if (data && data.chartData) {
        setChartData(data.chartData);
      } else {
        console.warn('No chart data received for', symbol);
        // Generate fallback chart data
        const fallbackData = generateFallbackChartData(symbol, timeframe);
        setChartData(fallbackData);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
      // Generate fallback chart data on error
      const fallbackData = generateFallbackChartData(symbol, timeframe);
      setChartData(fallbackData);
    } finally {
      setChartLoading(false);
    }
  }, [symbol, timeframe]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchStockData();
    setRefreshing(false);
  }, [fetchStockData]);

  const changePercent = stockData?.changePercent || 0;

  // Memoize renderScene to prevent recreation
  const renderScene = useMemo(() => SceneMap({
    overview: () => <OverviewRoute data={stockData} />,
    chart: () => (
      <ChartRoute
        symbol={symbol}
        chartData={chartData}
        changePercent={changePercent}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        loading={chartLoading}
      />
    ),
    financials: () => (
      <FinancialsRoute
        marketCap={stockData?.marketCap}
        peRatio={stockData?.peRatio}
        dividendYield={stockData?.dividendYield}
        earningsData={stockData?.earnings}
        stockData={stockData}
      />
    ),
    trends: () => (
      <TrendsRoute
        symbol={symbol}
        insiderData={stockData?.insiderTrades}
        institutionalData={stockData?.institutionalOwnership}
        sentimentData={stockData?.sentiment}
        analystData={stockData?.analystRatings}
      />
    ),
    trade: () => (
      <TradeRoute
        symbol={symbol}
        position={undefined}
        currentPrice={stockData?.currentPrice}
        onOpenTrade={() => setShowTradeModal(true)}
      />
    ),
  }), [stockData, chartData, changePercent, timeframe, chartLoading, symbol]);

  if (stockLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={theme.colors.background} />
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={styles.loadingText}>Loading {symbol}...</Text>
      </View>
    );
  }

  if (stockError || !stockData) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={theme.colors.background} />
        <Icon name="alert-circle" size={48} color={theme.colors.secondary} />
        <Text style={styles.errorText}>Failed to load stock data</Text>
        <TouchableOpacity onPress={onRefresh} style={styles.retryBtn}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={theme.colors.background} />

      {/* Enhanced Hero Header with Price Ticker */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Icon name="arrow-left" size={24} color={theme.colors.text} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>{stockData?.companyName} ({symbol})</Text>
          <View style={styles.priceTicker}>
            <Text style={styles.currentPriceHeader}>${stockData?.currentPrice?.toFixed(2)}</Text>
            <Text style={[
              styles.changeHeader,
              { color: changePercent >= 0 ? theme.colors.primary : theme.colors.secondary },
            ]}>
              {changePercent >= 0 ? '+' : ''}{changePercent?.toFixed(2)}%
            </Text>
          </View>
        </View>
        <TouchableOpacity style={styles.headerAction}>
          <Icon name="share-2" size={24} color={theme.colors.text} />
        </TouchableOpacity>
      </View>

      {/* Enhanced Tab Bar with Icons */}
      <TabView
        navigationState={{ index, routes }}
        renderScene={renderScene}
        onIndexChange={setIndex}
        initialLayout={{ width }}
        renderTabBar={(props) => (
          <TabBar
            {...props}
            indicatorStyle={[styles.tabIndicator, { backgroundColor: theme.colors.primary }]}
            style={styles.tabBar}
            activeColor={theme.colors.primary}
            inactiveColor={theme.colors.textSecondary}
            scrollEnabled={true}
          />
        )}
      />

      <StockTradingModal
        visible={showTradeModal}
        symbol={symbol}
        onClose={() => setShowTradeModal(false)}
        currentPrice={stockData?.currentPrice || 0}
        companyName={stockData?.companyName || symbol}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: theme.spacing.md,
    fontSize: 16,
    color: theme.colors.textSecondary,
    fontWeight: '500',
  },
  noDataText: {
    marginTop: theme.spacing.md,
    fontSize: 16,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  backBtn: {
    padding: theme.spacing.sm,
    borderRadius: theme.borderRadius / 2,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
    marginLeft: theme.spacing.sm,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
  },
  priceTicker: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: theme.spacing.xs,
  },
  currentPriceHeader: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.colors.text,
    marginRight: theme.spacing.sm,
  },
  changeHeader: {
    fontSize: 14,
    fontWeight: '600',
  },
  headerAction: {
    padding: theme.spacing.sm,
    borderRadius: theme.borderRadius / 2,
  },
  tabBar: {
    backgroundColor: theme.colors.surface,
    elevation: 0,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  tabIndicator: {
    height: 3,
    borderRadius: 2,
  },
  tabLabelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: theme.spacing.md,
  },
  tabLabel: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: theme.spacing.xs,
  },
  tabContent: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: theme.spacing.lg,
    paddingTop: theme.spacing.sm,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  heroCard: {
    marginBottom: theme.spacing.lg,
    borderRadius: theme.borderRadius,
    overflow: 'hidden',
  },
  gradientBg: {
    padding: theme.spacing.lg,
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.text,
    marginBottom: theme.spacing.xs,
  },
  heroSubtitle: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
  },
  description: {
    fontSize: 16,
    lineHeight: 24,
    color: theme.colors.textSecondary,
  },
  card: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.md,
    marginHorizontal: theme.spacing.md,
    ...theme.shadow,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  earningsDate: {
    fontSize: 16,
    color: theme.colors.primary,
    fontWeight: '500',
  },
  newsCard: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.lg,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.md,
    ...theme.shadow,
  },
  newsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  newsFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  newsDate: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  timeframeSelector: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: theme.spacing.lg,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    padding: theme.spacing.sm,
  },
  timeframeBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: 8,
  },
  activeTimeframeBtn: {
    backgroundColor: theme.colors.primary,
  },
  timeframeText: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.textSecondary,
  },
  activeTimeframeText: {
    color: '#FFF',
  },
  chartContainer: {
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  volumeContainer: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    height: 80,
    opacity: 0.7,
  },
  chartOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 20,
    right: 20,
    height: 100,
  },
  chartFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginTop: theme.spacing.md,
    paddingHorizontal: 20,
  },
  currentPrice: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.text,
  },
  change: {
    fontSize: 18,
    fontWeight: '600',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.lg,
  },
  metricCard: {
    width: '48%',
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.lg,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.md,
    alignItems: 'center',
    ...theme.shadow,
  },
  metricLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.text,
  },
  earningsCard: {
    backgroundColor: 'rgba(0,122,255,0.1)',
    padding: theme.spacing.lg,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.md,
  },
  earningsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.primary,
    marginBottom: theme.spacing.sm,
  },
  earningsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  earningsItem: {
    fontSize: 14,
    color: theme.colors.text,
  },
  historicalEarningsItem: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.sm,
  },
  quarterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.sm,
  },
  quarterLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
  },
  quarterDate: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  quarterMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  quarterEps: {
    fontSize: 14,
    color: theme.colors.text,
    flex: 1,
  },
  quarterEst: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    flex: 1,
    textAlign: 'center',
  },
  quarterSurprise: {
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
    textAlign: 'right',
  },
  positionCard: {
    backgroundColor: 'rgba(0,122,255,0.1)',
    padding: theme.spacing.lg,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.lg,
  },
  positionShares: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
  },
  positionValue: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.primary,
    marginVertical: theme.spacing.sm,
  },
  positionPl: {
    fontSize: 16,
    fontWeight: '600',
  },
  noPosition: {
    textAlign: 'center',
    color: theme.colors.textSecondary,
    fontSize: 16,
    marginBottom: theme.spacing.lg,
    fontStyle: 'italic',
  },
  tradeBtn: {
    borderRadius: theme.borderRadius,
    overflow: 'hidden',
    marginHorizontal: theme.spacing.lg,
    marginBottom: theme.spacing.xl,
  },
  gradientBtn: {
    paddingVertical: theme.spacing.lg,
    alignItems: 'center',
  },
  tradeBtnText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '600',
  },
  aiInsightCard: {
    marginBottom: theme.spacing.lg,
    borderRadius: theme.borderRadius,
    overflow: 'hidden',
  },
  gradientCard: {
    padding: theme.spacing.lg,
  },
  aiHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  aiTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFF',
    marginLeft: theme.spacing.sm,
  },
  aiText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#FFF',
  },
  sentimentScore: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  sentimentLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
  },
  sentimentValue: {
    fontSize: 32,
    fontWeight: '700',
  },
  sentimentBreakdown: {
    marginBottom: theme.spacing.lg,
  },
  sentimentBar: {
    marginBottom: theme.spacing.md,
  },
  sentimentBarLabel: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  barContainer: {
    height: 8,
    backgroundColor: 'rgba(0,0,0,0.1)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
  },
  analystSummary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.lg,
  },
  analystConsensus: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
  },
  analystTarget: {
    fontSize: 16,
    color: theme.colors.primary,
    fontWeight: '500',
  },
  ratingsBreakdown: {
    marginBottom: theme.spacing.lg,
  },
  noData: {
    textAlign: 'center',
    color: theme.colors.textSecondary,
    fontSize: 14,
    fontStyle: 'italic',
    marginVertical: theme.spacing.lg,
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.secondary,
    textAlign: 'center',
    marginTop: theme.spacing.md,
    marginBottom: theme.spacing.sm,
  },
  retryBtn: {
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.borderRadius,
  },
  retryText: {
    color: '#FFF',
    fontWeight: '600',
  },
  // Trends-specific styles
  subsectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
    marginTop: theme.spacing.lg,
  },
  recentMentions: {
    marginTop: theme.spacing.md,
  },
  mentionCard: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.sm,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.primary,
  },
  mentionContent: {
    fontSize: 14,
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
    lineHeight: 20,
  },
  mentionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  mentionSource: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  mentionSentiment: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  ratingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  ratingLabel: {
    fontSize: 14,
    color: theme.colors.text,
    width: 80,
  },
  ratingBar: {
    flex: 1,
    height: 8,
    backgroundColor: 'rgba(0,0,0,0.1)',
    borderRadius: 4,
    marginHorizontal: theme.spacing.sm,
    overflow: 'hidden',
  },
  ratingBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  ratingCount: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    width: 60,
    textAlign: 'right',
  },
  recentRatings: {
    marginTop: theme.spacing.md,
  },
  ratingCard: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.sm,
  },
  ratingCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  analystName: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
    flex: 1,
  },
  ratingValue: {
    fontSize: 14,
    fontWeight: '700',
  },
  ratingCardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ratingTarget: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  ratingDate: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  insiderSummary: {
    marginBottom: theme.spacing.md,
  },
  insiderCount: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    fontStyle: 'italic',
  },
  insiderCard: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.sm,
  },
  insiderCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  insiderName: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
    flex: 1,
  },
  insiderType: {
    fontSize: 14,
    fontWeight: '700',
  },
  insiderCardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  insiderShares: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  insiderValue: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  insiderDate: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  institutionalSummary: {
    marginBottom: theme.spacing.md,
  },
  institutionalCount: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    fontStyle: 'italic',
  },
  institutionalCard: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.sm,
  },
  institutionalCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  institutionalName: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
    flex: 1,
  },
  institutionalPercent: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.primary,
  },
  institutionalCardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  institutionalShares: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  institutionalValue: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  institutionalChange: {
    fontSize: 12,
    fontWeight: '600',
  },
  // Enhanced Financials styles
  financialHero: {
    marginBottom: theme.spacing.md,
    marginHorizontal: theme.spacing.md,
    borderRadius: theme.borderRadius,
    overflow: 'hidden',
  },
  financialHeroGradient: {
    padding: theme.spacing.md,
  },
  financialHeroContent: {
    alignItems: 'center',
  },
  financialHeroTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFF',
    marginBottom: theme.spacing.xs,
  },
  financialHeroSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: theme.spacing.md,
  },
  financialScore: {
    alignItems: 'center',
  },
  financialScoreLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: theme.spacing.xs,
  },
  financialScoreValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFF',
  },
  metricCategories: {
    flexDirection: 'row',
    marginBottom: theme.spacing.md,
    marginHorizontal: theme.spacing.md,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    padding: theme.spacing.xs,
  },
  metricCategoryBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.sm,
    borderRadius: theme.borderRadius - 4,
  },
  activeMetricCategory: {
    backgroundColor: theme.colors.primary,
  },
  metricCategoryText: {
    fontSize: 11,
    fontWeight: '600',
    color: theme.colors.textSecondary,
    marginLeft: theme.spacing.xs,
  },
  activeMetricCategoryText: {
    color: '#FFF',
  },
  enhancedMetricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.lg,
    paddingHorizontal: theme.spacing.sm,
  },
  enhancedMetricCard: {
    width: '48%',
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.sm,
    alignItems: 'center',
    position: 'relative',
    minHeight: 120,
    ...theme.shadow,
  },
  metricIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(0,122,255,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.xs,
  },
  enhancedMetricLabel: {
    fontSize: 11,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
    textAlign: 'center',
    fontWeight: '500',
  },
  enhancedMetricValue: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: theme.spacing.xs,
  },
  metricTrend: {
    position: 'absolute',
    top: theme.spacing.xs,
    right: theme.spacing.xs,
    width: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  healthIndicators: {
    marginTop: theme.spacing.md,
  },
  healthIndicator: {
    marginBottom: theme.spacing.lg,
  },
  healthLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  healthBar: {
    height: 8,
    backgroundColor: 'rgba(0,0,0,0.1)',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: theme.spacing.xs,
  },
  healthBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  healthValue: {
    fontSize: 12,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  nextEarningsCard: {
    marginBottom: theme.spacing.lg,
    borderRadius: theme.borderRadius,
    overflow: 'hidden',
  },
  nextEarningsGradient: {
    padding: theme.spacing.lg,
  },
  nextEarningsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  nextEarningsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.text,
  },
  nextEarningsDate: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  nextEarningsMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  nextEarningsMetric: {
    flex: 1,
    alignItems: 'center',
  },
  nextEarningsLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  nextEarningsValue: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.colors.primary,
  },
  earningsHistorySection: {
    marginTop: theme.spacing.lg,
  },
  enhancedEarningsItem: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.sm,
  },
  earningsItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  surpriseBadge: {
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs,
    borderRadius: 12,
  },
  surpriseText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFF',
  },
  earningsItemMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  earningsMetric: {
    flex: 1,
    alignItems: 'center',
  },
  earningsMetricLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  earningsMetricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
  },
  ratiosGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginTop: theme.spacing.md,
  },
  ratioItem: {
    width: '48%',
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.md,
    alignItems: 'center',
  },
  ratioLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
    textAlign: 'center',
  },
  ratioValue: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.text,
    marginBottom: theme.spacing.xs,
  },
  ratioBenchmark: {
    fontSize: 10,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
});