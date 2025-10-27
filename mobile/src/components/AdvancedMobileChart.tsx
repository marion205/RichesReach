/**
 * Advanced Mobile Charting Component
 * Real-time charts with gesture support and voice integration
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  PanGestureHandler,
  State,
  Animated,
  ScrollView,
} from 'react-native';
import { LineChart, BarChart, CandlestickChart } from 'react-native-chart-kit';
import { useVoice } from '../contexts/VoiceContext';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface ChartData {
  labels: string[];
  datasets: {
    data: number[];
    color?: (opacity: number) => string;
    strokeWidth?: number;
  }[];
}

interface AdvancedChartProps {
  symbol: string;
  timeframe: string;
  chartType: 'line' | 'candlestick' | 'volume';
  onTimeframeChange?: (timeframe: string) => void;
  onChartTypeChange?: (type: string) => void;
}

export const AdvancedMobileChart: React.FC<AdvancedChartProps> = ({
  symbol,
  timeframe,
  chartType,
  onTimeframeChange,
  onChartTypeChange,
}) => {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [price, setPrice] = useState(0);
  const [change, setChange] = useState(0);
  const [changePercent, setChangePercent] = useState(0);
  const [volume, setVolume] = useState(0);
  const [showIndicators, setShowIndicators] = useState(false);
  
  const { speak } = useVoice();
  const panRef = useRef();
  const translateX = useRef(new Animated.Value(0)).current;

  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];
  const chartTypes = [
    { key: 'line', label: 'Line', icon: '📈' },
    { key: 'candlestick', label: 'Candles', icon: '🕯️' },
    { key: 'volume', label: 'Volume', icon: '📊' },
  ];

  useEffect(() => {
    loadChartData();
  }, [symbol, timeframe, chartType]);

  const loadChartData = async () => {
    setIsLoading(true);
    try {
      // Mock data - replace with real API call
      const mockData = generateMockData(timeframe);
      setChartData(mockData);
      
      // Mock price data
      setPrice(150.25);
      setChange(2.15);
      setChangePercent(1.45);
      setVolume(1250000);
      
      setIsLoading(false);
    } catch (error) {
      console.error('Error loading chart data:', error);
      setIsLoading(false);
    }
  };

  const generateMockData = (tf: string): ChartData => {
    const points = tf === '1m' ? 60 : tf === '5m' ? 48 : tf === '15m' ? 32 : tf === '1h' ? 24 : tf === '4h' ? 30 : 30;
    const data = [];
    const labels = [];
    
    let basePrice = 150;
    for (let i = 0; i < points; i++) {
      basePrice += (Math.random() - 0.5) * 2;
      data.push(Math.max(0, basePrice));
      
      if (tf === '1d') {
        labels.push(`${i + 1}d`);
      } else if (tf === '4h') {
        labels.push(`${i * 4}h`);
      } else if (tf === '1h') {
        labels.push(`${i}h`);
      } else {
        labels.push(`${i * (tf === '1m' ? 1 : tf === '5m' ? 5 : 15)}m`);
      }
    }

    return {
      labels: labels.slice(-10), // Show last 10 points
      datasets: [{
        data: data.slice(-10),
        color: (opacity = 1) => `rgba(0, 255, 136, ${opacity})`,
        strokeWidth: 2,
      }],
    };
  };

  const handlePanGesture = (event: any) => {
    const { translationX } = event.nativeEvent;
    translateX.setValue(translationX);
  };

  const handlePanStateChange = (event: any) => {
    if (event.nativeEvent.state === State.END) {
      const { translationX, velocityX } = event.nativeEvent;
      
      if (Math.abs(translationX) > 50 || Math.abs(velocityX) > 500) {
        if (translationX > 0) {
          // Swipe right - previous timeframe
          const currentIndex = timeframes.indexOf(timeframe);
          if (currentIndex > 0) {
            onTimeframeChange?.(timeframes[currentIndex - 1]);
          }
        } else {
          // Swipe left - next timeframe
          const currentIndex = timeframes.indexOf(timeframe);
          if (currentIndex < timeframes.length - 1) {
            onTimeframeChange?.(timeframes[currentIndex + 1]);
          }
        }
      }
      
      Animated.spring(translateX, {
        toValue: 0,
        useNativeDriver: true,
      }).start();
    }
  };

  const speakPrice = () => {
    const changeText = change >= 0 ? 'up' : 'down';
    speak(`${symbol} is at $${price.toFixed(2)}, ${changeText} ${Math.abs(changePercent).toFixed(2)} percent`, {
      voice: 'Nova'
    });
  };

  const renderChart = () => {
    if (!chartData) return null;

    const chartConfig = {
      backgroundColor: '#000',
      backgroundGradientFrom: '#000',
      backgroundGradientTo: '#000',
      decimalPlaces: 2,
      color: (opacity = 1) => `rgba(0, 255, 136, ${opacity})`,
      labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
      style: {
        borderRadius: 16,
      },
      propsForDots: {
        r: '4',
        strokeWidth: '2',
        stroke: '#00ff88',
      },
    };

    switch (chartType) {
      case 'line':
        return (
          <LineChart
            data={chartData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
            withDots={false}
            withShadow={false}
            withInnerLines={true}
            withOuterLines={true}
            withVerticalLines={true}
            withHorizontalLines={true}
          />
        );
      case 'volume':
        return (
          <BarChart
            data={{
              labels: chartData.labels,
              datasets: [{
                data: chartData.datasets[0].data.map(() => Math.random() * 1000000),
              }],
            }}
            width={screenWidth - 40}
            height={220}
            chartConfig={{
              ...chartConfig,
              color: (opacity = 1) => `rgba(0, 123, 255, ${opacity})`,
            }}
            style={styles.chart}
            showValuesOnTopOfBars={false}
          />
        );
      default:
        return (
          <LineChart
            data={chartData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
            withDots={false}
            withShadow={false}
            withInnerLines={true}
            withOuterLines={true}
            withVerticalLines={true}
            withHorizontalLines={true}
          />
        );
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.symbolInfo}>
          <Text style={styles.symbol}>{symbol}</Text>
          <Text style={styles.price}>${price.toFixed(2)}</Text>
          <Text style={[
            styles.change,
            { color: change >= 0 ? '#00ff88' : '#ff4444' }
          ]}>
            {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
          </Text>
        </View>
        <TouchableOpacity style={styles.voiceButton} onPress={speakPrice}>
          <Text style={styles.voiceIcon}>🎤</Text>
        </TouchableOpacity>
      </View>

      {/* Chart Type Selector */}
      <View style={styles.chartTypeSelector}>
        {chartTypes.map((type) => (
          <TouchableOpacity
            key={type.key}
            style={[
              styles.chartTypeButton,
              chartType === type.key && styles.activeChartType
            ]}
            onPress={() => onChartTypeChange?.(type.key)}
          >
            <Text style={styles.chartTypeIcon}>{type.icon}</Text>
            <Text style={[
              styles.chartTypeLabel,
              chartType === type.key && styles.activeChartTypeLabel
            ]}>
              {type.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Chart Container */}
      <PanGestureHandler
        ref={panRef}
        onGestureEvent={handlePanGesture}
        onHandlerStateChange={handlePanStateChange}
      >
        <Animated.View
          style={[
            styles.chartContainer,
            { transform: [{ translateX }] }
          ]}
        >
          {isLoading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Loading chart...</Text>
            </View>
          ) : (
            renderChart()
          )}
        </Animated.View>
      </PanGestureHandler>

      {/* Timeframe Selector */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.timeframeSelector}
        contentContainerStyle={styles.timeframeContent}
      >
        {timeframes.map((tf) => (
          <TouchableOpacity
            key={tf}
            style={[
              styles.timeframeButton,
              timeframe === tf && styles.activeTimeframe
            ]}
            onPress={() => onTimeframeChange?.(tf)}
          >
            <Text style={[
              styles.timeframeText,
              timeframe === tf && styles.activeTimeframeText
            ]}>
              {tf}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Indicators Toggle */}
      <TouchableOpacity
        style={styles.indicatorsButton}
        onPress={() => setShowIndicators(!showIndicators)}
      >
        <Text style={styles.indicatorsButtonText}>
          {showIndicators ? 'Hide' : 'Show'} Indicators
        </Text>
      </TouchableOpacity>

      {/* Technical Indicators */}
      {showIndicators && (
        <View style={styles.indicatorsContainer}>
          <View style={styles.indicatorRow}>
            <Text style={styles.indicatorLabel}>RSI (14)</Text>
            <Text style={styles.indicatorValue}>65.4</Text>
          </View>
          <View style={styles.indicatorRow}>
            <Text style={styles.indicatorLabel}>MACD</Text>
            <Text style={styles.indicatorValue}>2.15</Text>
          </View>
          <View style={styles.indicatorRow}>
            <Text style={styles.indicatorLabel}>Bollinger</Text>
            <Text style={styles.indicatorValue}>Upper: 152.1</Text>
          </View>
          <View style={styles.indicatorRow}>
            <Text style={styles.indicatorLabel}>Volume</Text>
            <Text style={styles.indicatorValue}>{volume.toLocaleString()}</Text>
          </View>
        </View>
      )}

      {/* Chart Controls */}
      <View style={styles.chartControls}>
        <TouchableOpacity style={styles.controlButton}>
          <Text style={styles.controlButtonText}>📊</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.controlButton}>
          <Text style={styles.controlButtonText}>📈</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.controlButton}>
          <Text style={styles.controlButtonText}>📉</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.controlButton}>
          <Text style={styles.controlButtonText}>🎯</Text>
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
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  symbolInfo: {
    flex: 1,
  },
  symbol: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  price: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 5,
  },
  change: {
    fontSize: 16,
    fontWeight: '500',
    marginTop: 2,
  },
  voiceButton: {
    backgroundColor: '#007bff',
    borderRadius: 25,
    width: 50,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceIcon: {
    fontSize: 20,
  },
  chartTypeSelector: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 5,
  },
  chartTypeButton: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    borderRadius: 8,
  },
  activeChartType: {
    backgroundColor: '#007bff',
  },
  chartTypeIcon: {
    fontSize: 20,
    marginBottom: 5,
  },
  chartTypeLabel: {
    fontSize: 12,
    color: '#888',
    fontWeight: '500',
  },
  activeChartTypeLabel: {
    color: '#fff',
  },
  chartContainer: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 10,
    marginBottom: 20,
  },
  chart: {
    borderRadius: 16,
  },
  loadingContainer: {
    height: 220,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#888',
  },
  timeframeSelector: {
    marginBottom: 20,
  },
  timeframeContent: {
    paddingHorizontal: 10,
  },
  timeframeButton: {
    backgroundColor: '#1a1a1a',
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 10,
    marginHorizontal: 5,
  },
  activeTimeframe: {
    backgroundColor: '#007bff',
  },
  timeframeText: {
    fontSize: 14,
    color: '#888',
    fontWeight: '500',
  },
  activeTimeframeText: {
    color: '#fff',
  },
  indicatorsButton: {
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    marginBottom: 20,
  },
  indicatorsButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '500',
  },
  indicatorsContainer: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  indicatorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  indicatorLabel: {
    fontSize: 14,
    color: '#888',
  },
  indicatorValue: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '500',
  },
  chartControls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 10,
  },
  controlButton: {
    backgroundColor: '#333',
    borderRadius: 8,
    width: 50,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlButtonText: {
    fontSize: 20,
  },
});

export default AdvancedMobileChart;
