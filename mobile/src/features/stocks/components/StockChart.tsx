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
import Svg, { Line, Polyline, Path, Text as SvgText, G, Defs, LinearGradient, Stop } from 'react-native-svg';
import PNLRibbonOverlay from '../../raha/components/PNLRibbonOverlay';

const { width: screenWidth } = Dimensions.get('window');

// GraphQL Query
const GET_STOCK_CHART_DATA = gql`
  query GetStockChartData($symbol: String!, $timeframe: String!) {
    stockChartData(symbol: $symbol, timeframe: $timeframe) {
      symbol
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
  embedded?: boolean; // New prop to indicate if it's embedded in another container
  width?: number; // Allow external width control
  height?: number; // Allow external height control
  minimal?: boolean; // Minimal style for The Whisper screen (no header, no timeframe selector)
  pnlOverlay?: {
    entryPrice: number;
    takeProfit: number;
    stopLoss: number;
    isLong: boolean;
    riskAmount: number;
    visible: boolean;
  }; // P&L ribbon overlay data
}

const StockChart: React.FC<StockChartProps> = ({ 
  symbol, 
  timeframe = '1D',
  onTimeframeChange,
  embedded = false,
  width: propWidth,
  height: propHeight = 220,
  minimal = false,
  pnlOverlay
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
    const chartWidth = Math.max(0, Math.floor(propWidth ?? screenWidth - 80));
    const chartHeight = propHeight;

    if (loading) {
      return (
        <View style={[styles.chartContainer, { height: chartHeight + 10 }]}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading chart data...</Text>
        </View>
      );
    }

    if (error || !data?.stockChartData?.data?.length) {
      return (
        <View style={[styles.chartContainer, { height: chartHeight + 10 }]}>
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
      const x = (index / (chartData.length - 1)) * chartWidth;
      const y = chartHeight - ((point.close - minPrice) / priceRange) * chartHeight;
      return `${x},${y}`;
    }).join(' ');

    // Determine if price is going up (green) or down (red)
    const firstPrice = chartData[0].close;
    const lastPrice = chartData[chartData.length - 1].close;
    const isPositive = lastPrice >= firstPrice;
    const lineColor = minimal ? (isPositive ? '#10B981' : '#EF4444') : '#007AFF';
    const gradientColor = minimal ? (isPositive ? '#10B981' : '#EF4444') : '#007AFF';
    
    // Create smooth path for area fill
    const pathData = chartData.map((point, index) => {
      const x = (index / (chartData.length - 1)) * chartWidth;
      const y = chartHeight - ((point.close - minPrice) / priceRange) * chartHeight;
      return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
    }).join(' ');
    
    // Close path for gradient fill
    const areaPath = `${pathData} L ${chartWidth} ${chartHeight} L 0 ${chartHeight} Z`;

    return (
      <View style={[styles.chartContainer, { height: chartHeight + (minimal ? 0 : 10) }]}>
        <View style={[styles.chartWrapper, { width: chartWidth, height: chartHeight }]}>
          {/* P&L Ribbon Overlay - rendered first so price chart is on top */}
          {minimal && pnlOverlay && pnlOverlay.visible && (
            <PNLRibbonOverlay
              entryPrice={pnlOverlay.entryPrice}
              takeProfit={pnlOverlay.takeProfit}
              stopLoss={pnlOverlay.stopLoss}
              isLong={pnlOverlay.isLong}
              currentPrice={chartData[chartData.length - 1]?.close || 0}
              priceData={chartData}
              chartWidth={chartWidth}
              chartHeight={chartHeight}
              minPrice={minPrice}
              maxPrice={maxPrice}
              riskAmount={pnlOverlay.riskAmount}
              visible={pnlOverlay.visible}
            />
          )}
          
          <Svg width={chartWidth} height={chartHeight} style={styles.chart}>
            {!minimal && (
              <>
                {/* Grid lines - only show in non-minimal mode */}
                <Line x1={0} y1={0} x2={chartWidth} y2={0} stroke="#f0f0f0" strokeWidth={1} />
                <Line x1={0} y1={chartHeight/2} x2={chartWidth} y2={chartHeight/2} stroke="#f0f0f0" strokeWidth={1} />
                <Line x1={0} y1={chartHeight} x2={chartWidth} y2={chartHeight} stroke="#f0f0f0" strokeWidth={1} />
                <Line x1={0} y1={0} x2={0} y2={chartHeight} stroke="#f0f0f0" strokeWidth={1} />
                <Line x1={chartWidth/2} y1={0} x2={chartWidth/2} y2={chartHeight} stroke="#f0f0f0" strokeWidth={1} />
                <Line x1={chartWidth} y1={0} x2={chartWidth} y2={chartHeight} stroke="#f0f0f0" strokeWidth={1} />
              </>
            )}
            
            {/* Gradient area fill - only in minimal mode */}
            {minimal && (
              <>
                <Defs>
                  <LinearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <Stop offset="0%" stopColor={gradientColor} stopOpacity="0.2" />
                    <Stop offset="100%" stopColor={gradientColor} stopOpacity="0.0" />
                  </LinearGradient>
                </Defs>
                <Path
                  d={areaPath}
                  fill="url(#chartGradient)"
                  stroke="none"
                />
              </>
            )}
            
            {/* Price line - smoother and thicker in minimal mode */}
            <Polyline
              points={chartData.map((point, index) => {
                const x = (index / (chartData.length - 1)) * chartWidth;
                const y = chartHeight - ((point.close - minPrice) / priceRange) * chartHeight;
                return `${x},${y}`;
              }).join(' ')}
              fill="none"
              stroke={lineColor}
              strokeWidth={minimal ? 2.5 : 2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            
            {!minimal && (
              <>
                {/* Price labels on Y-axis */}
                <SvgText x={5} y={15} fontSize="12" fill="#666">
                  ${maxPrice.toFixed(2)}
                </SvgText>
                <SvgText x={5} y={chartHeight/2 + 5} fontSize="12" fill="#666">
                  ${((maxPrice + minPrice) / 2).toFixed(2)}
                </SvgText>
                <SvgText x={5} y={chartHeight - 5} fontSize="12" fill="#666">
                  ${minPrice.toFixed(2)}
                </SvgText>
                
                {/* Time labels on X-axis */}
                <SvgText x={10} y={chartHeight - 5} fontSize="10" fill="#999">
                  {new Date(chartData[0].timestamp).toLocaleDateString()}
                </SvgText>
                <SvgText x={chartWidth/2 - 20} y={chartHeight - 5} fontSize="10" fill="#999">
                  {selectedTimeframe}
                </SvgText>
                <SvgText x={chartWidth - 50} y={chartHeight - 5} fontSize="10" fill="#999">
                  {new Date(chartData[chartData.length - 1].timestamp).toLocaleDateString()}
                </SvgText>
              </>
            )}
          </Svg>
        </View>

        {!minimal && (
          <View style={styles.chartFooter}>
            <View style={styles.chartLegend}>
              <View style={styles.legendItem}>
                <View style={styles.legendLine} />
                <Text style={styles.legendText}>Price Movement</Text>
              </View>
            </View>
            <Text style={styles.timeframeText}>
              {selectedTimeframe} • {chartData.length} data points
            </Text>
          </View>
        )}
      </View>
    );
  };

  const content = (
    <>
      {!minimal && (
        <>
          {/* Chart Header */}
          <View style={styles.chartHeader}>
            <Text style={styles.symbolText}>{symbol}</Text>
            <View style={styles.priceInfo}>
              {(() => {
                // Compute currentPrice from last close price if available
                const chartData = data?.stockChartData?.data;
                const lastClose = chartData && chartData.length > 0 ? chartData[chartData.length - 1]?.close : null;
                const currentPrice = lastClose || 0;
                
                // Compute change from first and last close prices
                const firstClose = chartData && chartData.length > 0 ? chartData[0]?.close : null;
                const change = firstClose && lastClose ? lastClose - firstClose : 0;
                const changePercent = firstClose && firstClose !== 0 ? (change / firstClose) * 100 : 0;
                
                return (
                  <>
                    <Text style={styles.currentPrice}>
                      ${currentPrice.toFixed(2)}
                    </Text>
                    <Text style={[
                      styles.changeText,
                      { color: change >= 0 ? '#34C759' : '#FF3B30' }
                    ]}>
                      {change >= 0 ? '+' : ''}{change.toFixed(2)} 
                      ({changePercent.toFixed(2)}%)
                    </Text>
                  </>
                );
              })()}
            </View>
          </View>

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
        </>
      )}

      {/* Chart */}
      {renderChart()}
    </>
  );

  return embedded ? content : (
    <View style={styles.container}>
      {content}
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
    paddingTop: 8,
    paddingBottom: 16,
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
    padding: 4, // Minimal padding to maximize chart space
    paddingTop: 30, // Add more space between timeframe selector and chart
    alignItems: 'center',
    justifyContent: 'center',
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5ea',
  },
  symbolText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#000000',
    flex: 1,
    marginRight: 16,
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
    position: 'relative',
  },
  chart: {
    position: 'relative',
  },
  chartLine: {
    position: 'absolute',
  },
  chartSegment: {
    position: 'absolute',
    height: 2,
    backgroundColor: '#007AFF',
  },
  priceLabels: {
    position: 'absolute',
    right: 8,
    top: 0,
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
  chartLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 8,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendLine: {
    width: 20,
    height: 2,
    backgroundColor: '#007AFF',
    marginRight: 8,
  },
  legendText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
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