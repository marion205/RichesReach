import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');
const CHART_WIDTH = width - 40;
const CHART_HEIGHT = 200;

// GraphQL Query
const GET_STOCK_CHART_DATA = gql`
  query GetStockChartData($symbol: String!, $timeframe: String!) {
    stockChartData(symbol: $symbol, timeframe: $timeframe) {
      symbol
      timeframe
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
    }
  }
`;

interface StockChartProps {
  symbol: string;
  timeframe?: string;
  onTimeframeChange?: (timeframe: string) => void;
}

const StockChart: React.FC<StockChartProps> = ({ 
  symbol, 
  timeframe = '1D',
  onTimeframeChange 
}) => {
  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);

  const { data, loading, error, refetch } = useQuery(GET_STOCK_CHART_DATA, {
    variables: { symbol, timeframe: selectedTimeframe },
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: true,
  });

  const timeframes = [
    { key: '1H', label: '1H' },
    { key: '1D', label: '1D' },
    { key: '1W', label: '1W' },
    { key: '1M', label: '1M' },
  ];

  const handleTimeframeChange = (newTimeframe: string) => {
    setSelectedTimeframe(newTimeframe);
    onTimeframeChange?.(newTimeframe);
  };

  const renderChart = () => {
    if (loading) {
      return (
        <View style={styles.chartContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading chart data...</Text>
        </View>
      );
    }

    if (error || !data?.stockChartData?.data?.length) {
      return (
        <View style={styles.chartContainer}>
          <Icon name="bar-chart-2" size={48} color="#C7C7CC" />
          <Text style={styles.errorText}>Unable to load chart data</Text>
          <TouchableOpacity onPress={() => refetch()} style={styles.retryButton}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      );
    }

    const chartData = data.stockChartData.data;
    const prices = chartData.map(d => d.close);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice;

    // Simple line chart rendering
    const points = chartData.map((point, index) => {
      const x = (index / (chartData.length - 1)) * CHART_WIDTH;
      const y = CHART_HEIGHT - ((point.close - minPrice) / priceRange) * CHART_HEIGHT;
      return `${x},${y}`;
    }).join(' ');

    return (
      <View style={styles.chartContainer}>
        <View style={styles.chartHeader}>
          <Text style={styles.symbolText}>{symbol}</Text>
          <View style={styles.priceInfo}>
            <Text style={styles.currentPrice}>
              ${data.stockChartData.currentPrice?.toFixed(2) || '0.00'}
            </Text>
            <Text style={[
              styles.changeText,
              { color: (data.stockChartData.change || 0) >= 0 ? '#34C759' : '#FF3B30' }
            ]}>
              {data.stockChartData.change >= 0 ? '+' : ''}{data.stockChartData.change?.toFixed(2) || '0.00'} 
              ({data.stockChartData.changePercent?.toFixed(2) || '0.00'}%)
            </Text>
          </View>
        </View>

        <View style={styles.chartWrapper}>
          <View style={styles.chart}>
            {/* Simple line representation */}
            <View style={styles.chartLine}>
              {chartData.map((point, index) => {
                if (index === 0) return null;
                const prevPoint = chartData[index - 1];
                const x1 = ((index - 1) / (chartData.length - 1)) * CHART_WIDTH;
                const y1 = CHART_HEIGHT - ((prevPoint.close - minPrice) / priceRange) * CHART_HEIGHT;
                const x2 = (index / (chartData.length - 1)) * CHART_WIDTH;
                const y2 = CHART_HEIGHT - ((point.close - minPrice) / priceRange) * CHART_HEIGHT;
                
                const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
                const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
                
                return (
                  <View
                    key={index}
                    style={[
                      styles.chartSegment,
                      {
                        left: x1,
                        top: y1,
                        width: length,
                        transform: [{ rotate: `${angle}deg` }],
                      }
                    ]}
                  />
                );
              })}
            </View>

            {/* Price labels */}
            <View style={styles.priceLabels}>
              <Text style={styles.priceLabel}>${maxPrice.toFixed(2)}</Text>
              <Text style={styles.priceLabel}>${minPrice.toFixed(2)}</Text>
            </View>
          </View>
        </View>

        <View style={styles.chartFooter}>
          <Text style={styles.timeframeText}>
            {selectedTimeframe} • {chartData.length} data points
          </Text>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Timeframe Selector */}
      <View style={styles.timeframeSelector}>
        {timeframes.map((tf) => (
          <TouchableOpacity
            key={tf.key}
            style={[
              styles.timeframeButton,
              selectedTimeframe === tf.key && styles.selectedTimeframeButton
            ]}
            onPress={() => handleTimeframeChange(tf.key)}
          >
            <Text style={[
              styles.timeframeText,
              selectedTimeframe === tf.key && styles.selectedTimeframeText
            ]}>
              {tf.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Chart */}
      {renderChart()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    margin: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  timeframeSelector: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingTop: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  timeframeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  selectedTimeframeButton: {
    backgroundColor: '#007AFF',
  },
  timeframeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  selectedTimeframeText: {
    color: '#FFFFFF',
  },
  chartContainer: {
    height: CHART_HEIGHT + 60,
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    marginBottom: 16,
  },
  symbolText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#000000',
  },
  priceInfo: {
    alignItems: 'flex-end',
  },
  currentPrice: {
    fontSize: 18,
    fontWeight: '700',
    color: '#000000',
  },
  changeText: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 2,
  },
  chartWrapper: {
    width: CHART_WIDTH,
    height: CHART_HEIGHT,
    position: 'relative',
  },
  chart: {
    width: CHART_WIDTH,
    height: CHART_HEIGHT,
    position: 'relative',
  },
  chartLine: {
    position: 'absolute',
    width: CHART_WIDTH,
    height: CHART_HEIGHT,
  },
  chartSegment: {
    position: 'absolute',
    height: 2,
    backgroundColor: '#007AFF',
  },
  priceLabels: {
    position: 'absolute',
    right: -40,
    top: 0,
    height: CHART_HEIGHT,
    justifyContent: 'space-between',
  },
  priceLabel: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '500',
  },
  chartFooter: {
    alignItems: 'center',
    marginTop: 12,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 12,
  },
  errorText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 12,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 12,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

export default StockChart;