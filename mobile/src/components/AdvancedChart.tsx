/**
 * Advanced Charting and Visualization
 * Professional-grade charts with technical indicators
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { PanGestureHandler, State } from 'react-native-gesture-handler';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';
import { useQuery, gql } from '@apollo/client';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  runOnJS,
} from 'react-native-reanimated';
import EducationalTooltip from './common/EducationalTooltip';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// GraphQL Queries
const GET_MARKET_DATA = gql`
  query GetMarketData($symbol: String!, $timeframe: String!) {
    marketData(symbol: $symbol, timeframe: $timeframe) {
      timestamp
      open
      high
      low
      close
      volume
    }
  }
`;

const GET_TECHNICAL_INDICATORS = gql`
  query GetTechnicalIndicators($symbol: String!) {
    technicalIndicators(symbol: $symbol) {
      rsi
      macd
      bollingerBands {
        upper
        middle
        lower
      }
      movingAverages {
        sma20
        sma50
        sma200
      }
    }
  }
`;

interface ChartData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TechnicalIndicators {
  rsi: number;
  macd: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollingerBands: {
    upper: number;
    middle: number;
    lower: number;
  };
  movingAverages: {
    sma20: number;
    sma50: number;
    sma200: number;
  };
}

interface AdvancedChartProps {
  symbol: string;
  initialTimeframe?: string;
  showIndicators?: boolean;
  onDataPointPress?: (data: any) => void;
}

export const AdvancedChart: React.FC<AdvancedChartProps> = ({
  symbol,
  initialTimeframe = '1D',
  showIndicators = true,
  onDataPointPress,
}) => {
  const [timeframe, setTimeframe] = useState(initialTimeframe);
  const [chartType, setChartType] = useState<'line' | 'candlestick' | 'volume'>('line');
  const [selectedIndicator, setSelectedIndicator] = useState<string>('rsi');
  const [isLoading, setIsLoading] = useState(true);
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [technicalData, setTechnicalData] = useState<TechnicalIndicators | null>(null);
  
  const translateX = useSharedValue(0);
  const scale = useSharedValue(1);

  const { data: marketData, loading: marketLoading, error: marketError } = useQuery(
    GET_MARKET_DATA,
    {
      variables: { symbol, timeframe },
      pollInterval: 30000, // Update every 30 seconds
    }
  );

  const { data: indicatorsData, loading: indicatorsLoading } = useQuery(
    GET_TECHNICAL_INDICATORS,
    {
      variables: { symbol },
      skip: !showIndicators,
    }
  );

  useEffect(() => {
    if (marketData?.marketData) {
      setChartData(marketData.marketData);
      setIsLoading(false);
    }
  }, [marketData]);

  useEffect(() => {
    if (indicatorsData?.technicalIndicators) {
      setTechnicalData(indicatorsData.technicalIndicators);
    }
  }, [indicatorsData]);

  const timeframes = [
    { label: '1M', value: '1M' },
    { label: '5M', value: '5M' },
    { label: '15M', value: '15M' },
    { label: '1H', value: '1H' },
    { label: '4H', value: '4H' },
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' },
  ];

  const chartTypes = [
    { label: 'Line', value: 'line' },
    { label: 'Candlestick', value: 'candlestick' },
    { label: 'Volume', value: 'volume' },
  ];

  const indicators = [
    { label: 'RSI', value: 'rsi' },
    { label: 'MACD', value: 'macd' },
    { label: 'Bollinger', value: 'bollinger' },
    { label: 'MA', value: 'moving_averages' },
  ];

  const formatChartData = () => {
    if (!chartData.length) return null;

    const labels = chartData.map(item => {
      const date = new Date(item.timestamp);
      switch (timeframe) {
        case '1M':
        case '5M':
        case '15M':
          return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
        case '1H':
        case '4H':
          return `${date.getHours()}:00`;
        case '1D':
          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        case '1W':
          return date.toLocaleDateString('en-US', { month: 'short' });
        default:
          return date.toLocaleDateString();
      }
    });

    const prices = chartData.map(item => item.close);
    const volumes = chartData.map(item => item.volume);

    return {
      labels: labels.slice(-20), // Show last 20 data points
      datasets: [
        {
          data: prices.slice(-20),
          color: (opacity = 1) => `rgba(0, 255, 0, ${opacity})`,
          strokeWidth: 2,
        },
        ...(chartType === 'volume' ? [{
          data: volumes.slice(-20),
          color: (opacity = 1) => `rgba(0, 150, 255, ${opacity})`,
          strokeWidth: 1,
        }] : []),
      ],
    };
  };

  const formatVolumeData = () => {
    if (!chartData.length) return null;

    const labels = chartData.map(item => {
      const date = new Date(item.timestamp);
      return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
    });

    const volumes = chartData.map(item => item.volume);

    return {
      labels: labels.slice(-20),
      datasets: [
        {
          data: volumes.slice(-20),
        },
      ],
    };
  };

  const getRSIColor = (rsi: number) => {
    if (rsi > 70) return '#ff4444'; // Overbought
    if (rsi < 30) return '#44ff44'; // Oversold
    return '#ffbb00'; // Neutral
  };

  const getMACDColor = (macd: number, signal: number) => {
    return macd > signal ? '#44ff44' : '#ff4444';
  };

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { translateX: translateX.value },
        { scale: scale.value },
      ],
    } as any;
  });

  const handleGestureEvent = (event: any) => {
    translateX.value = event.nativeEvent.translationX;
  };

  const handleGestureStateChange = (event: any) => {
    if (event.nativeEvent.state === State.END) {
      translateX.value = withSpring(0);
    }
  };

  if (isLoading || marketLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0F0" />
        <Text style={styles.loadingText}>Loading chart data...</Text>
      </View>
    );
  }

  if (marketError) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Error loading chart: {marketError.message}</Text>
      </View>
    );
  }

  const chartConfig = {
    backgroundColor: '#000',
    backgroundGradientFrom: '#1a1a1a',
    backgroundGradientTo: '#333',
    decimalPlaces: 2,
    color: (opacity = 1) => `rgba(0, 255, 0, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: '#0F0',
    },
    propsForBackgroundLines: {
      strokeDasharray: '5,5',
      stroke: '#333',
    },
  };

  const volumeConfig = {
    ...chartConfig,
    color: (opacity = 1) => `rgba(0, 150, 255, ${opacity})`,
    fillShadowGradient: '#0096ff',
    fillShadowGradientOpacity: 0.3,
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.symbol}>{symbol}</Text>
        <Text style={styles.price}>
          ${chartData[chartData.length - 1]?.close?.toFixed(2) || '0.00'}
        </Text>
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        {/* Timeframe Selector */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.timeframeContainer}>
            {timeframes.map((tf) => (
              <TouchableOpacity
                key={tf.value}
                style={[
                  styles.timeframeButton,
                  timeframe === tf.value && styles.activeTimeframe,
                ]}
                onPress={() => setTimeframe(tf.value)}
              >
                <Text
                  style={[
                    styles.timeframeText,
                    timeframe === tf.value && styles.activeTimeframeText,
                  ]}
                >
                  {tf.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>

        {/* Chart Type Selector */}
        <View style={styles.chartTypeContainer}>
          {chartTypes.map((type) => (
            <TouchableOpacity
              key={type.value}
              style={[
                styles.chartTypeButton,
                chartType === type.value && styles.activeChartType,
              ]}
              onPress={() => setChartType(type.value as any)}
            >
              <Text
                style={[
                  styles.chartTypeText,
                  chartType === type.value && styles.activeChartTypeText,
                ]}
              >
                {type.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Main Chart */}
      <PanGestureHandler
        onGestureEvent={handleGestureEvent}
        onHandlerStateChange={handleGestureStateChange}
      >
        <Animated.View style={[styles.chartContainer, animatedStyle]}>
          {chartType === 'line' && formatChartData() && (
            <LineChart
              data={formatChartData()!}
              width={screenWidth - 40}
              height={220}
              chartConfig={chartConfig}
              bezier
              style={styles.chart}
              onDataPointClick={(data) => onDataPointPress?.(data)}
            />
          )}

          {chartType === 'volume' && formatVolumeData() && (
            <BarChart
              data={formatVolumeData()!}
              width={screenWidth - 40}
              height={220}
              chartConfig={volumeConfig}
              style={styles.chart}
              showValuesOnTopOfBars={false}
              yAxisLabel=""
              yAxisSuffix=""
            />
          )}

          {chartType === 'candlestick' && (
            <View style={styles.candlestickPlaceholder}>
              <Text style={styles.placeholderText}>
                Candlestick Chart (Implementation needed)
              </Text>
            </View>
          )}
        </Animated.View>
      </PanGestureHandler>

      {/* Technical Indicators */}
      {showIndicators && technicalData && (
        <View style={styles.indicatorsContainer}>
          <Text style={styles.indicatorsTitle}>Technical Indicators</Text>
          
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.indicatorCards}>
              {/* RSI */}
              <EducationalTooltip
                term="RSI (Relative Strength Index)"
                explanation="RSI measures momentum on a scale of 0-100. Values above 70 indicate overbought conditions (potential sell signal), while values below 30 indicate oversold conditions (potential buy signal). RSI helps identify when a stock may reverse direction. Use with price action confirmation for stronger signals."
                position="top"
              >
                <View style={styles.indicatorCard}>
                  <Text style={styles.indicatorLabel}>RSI</Text>
                  <Text style={[
                    styles.indicatorValue,
                    { color: getRSIColor(technicalData.rsi) }
                  ]}>
                    {technicalData.rsi.toFixed(1)}
                  </Text>
                  <Text style={styles.indicatorStatus}>
                    {technicalData.rsi > 70 ? 'Overbought' : 
                     technicalData.rsi < 30 ? 'Oversold' : 'Neutral'}
                  </Text>
                </View>
              </EducationalTooltip>

              {/* MACD */}
              <EducationalTooltip
                term="MACD (Moving Average Convergence Divergence)"
                explanation="MACD shows momentum and trend changes. When the MACD line crosses above the signal line, it's a bullish signal (buy). When it crosses below, it's bearish (sell). The histogram shows momentum strength. Use MACD with price action confirmation - stronger signals occur when MACD crosses in the direction of the overall trend."
                position="top"
              >
                <View style={styles.indicatorCard}>
                  <Text style={styles.indicatorLabel}>MACD</Text>
                  <Text style={[
                    styles.indicatorValue,
                    { color: getMACDColor(technicalData.macd.macd, technicalData.macd.signal) }
                  ]}>
                    {technicalData.macd.macd.toFixed(3)}
                  </Text>
                  <Text style={styles.indicatorStatus}>
                    Signal: {technicalData.macd.signal.toFixed(3)}
                  </Text>
                </View>
              </EducationalTooltip>

              {/* Bollinger Bands */}
              <EducationalTooltip
                term="Bollinger Bands"
                explanation="Bollinger Bands show price volatility. The middle line is a moving average, with upper and lower bands representing standard deviations. When price touches the upper band, the stock may be overbought (potential sell). When price touches the lower band, it may be oversold (potential buy). Wider bands indicate higher volatility."
                position="top"
              >
                <View style={styles.indicatorCard}>
                  <Text style={styles.indicatorLabel}>Bollinger</Text>
                  <Text style={styles.indicatorValue}>
                    {technicalData.bollingerBands.middle.toFixed(2)}
                  </Text>
                  <Text style={styles.indicatorStatus}>
                    ±{((technicalData.bollingerBands.upper - technicalData.bollingerBands.lower) / 2).toFixed(2)}
                  </Text>
                </View>
              </EducationalTooltip>

              {/* Moving Averages */}
              <EducationalTooltip
                term="Moving Averages (MA)"
                explanation="Moving averages smooth out price data to show trends. When price is above the MA, it indicates an uptrend (buy signal). When price is below, it's a downtrend (sell signal). MA 20 shows short-term trends, MA 50 shows medium-term, and MA 200 shows long-term trends. Golden cross (MA 20 crosses above MA 50) is bullish."
                position="top"
              >
                <View style={styles.indicatorCard}>
                  <Text style={styles.indicatorLabel}>MA 20/50/200</Text>
                  <Text style={styles.indicatorValue}>
                    {technicalData.movingAverages.sma20.toFixed(2)}
                  </Text>
                  <Text style={styles.indicatorStatus}>
                    {technicalData.movingAverages.sma50.toFixed(2)} / {technicalData.movingAverages.sma200.toFixed(2)}
                  </Text>
                </View>
              </EducationalTooltip>
            </View>
          </ScrollView>
        </View>
      )}

      {/* Chart Actions */}
      <View style={styles.chartActions}>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>📊</Text>
          <Text style={styles.actionButtonLabel}>Full Screen</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>📈</Text>
          <Text style={styles.actionButtonLabel}>Analysis</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>⚙️</Text>
          <Text style={styles.actionButtonLabel}>Settings</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>💾</Text>
          <Text style={styles.actionButtonLabel}>Save</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  loadingText: {
    color: '#0F0',
    marginTop: 10,
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
    padding: 20,
  },
  errorText: {
    color: '#ff4444',
    fontSize: 16,
    textAlign: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  symbol: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  price: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0F0',
  },
  controls: {
    backgroundColor: '#1a1a1a',
    paddingVertical: 10,
  },
  timeframeContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
  },
  timeframeButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
    borderRadius: 20,
    backgroundColor: '#333',
  },
  activeTimeframe: {
    backgroundColor: '#007bff',
  },
  timeframeText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  activeTimeframeText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  chartTypeContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginTop: 10,
  },
  chartTypeButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
    borderRadius: 20,
    backgroundColor: '#333',
  },
  activeChartType: {
    backgroundColor: '#0F0',
  },
  chartTypeText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  activeChartTypeText: {
    color: '#000',
    fontWeight: 'bold',
  },
  chartContainer: {
    margin: 20,
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 10,
  },
  chart: {
    borderRadius: 16,
  },
  candlestickPlaceholder: {
    height: 220,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#333',
    borderRadius: 16,
  },
  placeholderText: {
    color: '#888',
    fontSize: 16,
    fontStyle: 'italic',
  },
  indicatorsContainer: {
    backgroundColor: '#1a1a1a',
    paddingVertical: 15,
  },
  indicatorsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    paddingHorizontal: 20,
    marginBottom: 10,
  },
  indicatorCards: {
    flexDirection: 'row',
    paddingHorizontal: 20,
  },
  indicatorCard: {
    backgroundColor: '#333',
    borderRadius: 12,
    padding: 15,
    marginRight: 15,
    minWidth: 120,
    alignItems: 'center',
  },
  indicatorLabel: {
    fontSize: 14,
    color: '#888',
    marginBottom: 5,
  },
  indicatorValue: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  indicatorStatus: {
    fontSize: 12,
    color: '#ccc',
    textAlign: 'center',
  },
  chartActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 20,
    backgroundColor: '#1a1a1a',
  },
  actionButton: {
    alignItems: 'center',
    paddingVertical: 10,
  },
  actionButtonText: {
    fontSize: 24,
    marginBottom: 5,
  },
  actionButtonLabel: {
    fontSize: 12,
    color: '#888',
  },
});

export default AdvancedChart;
