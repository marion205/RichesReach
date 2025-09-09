import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/Feather';
import EducationalTooltip from './EducationalTooltip';
import { getTermExplanation } from '../data/financialTerms';

const { width } = Dimensions.get('window');

interface PortfolioComparisonProps {
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  portfolioHistory: Array<{ date: string; value: number }>;
}

interface Benchmark {
  id: string;
  name: string;
  symbol: string;
  returnPercent: number;
  color: string;
  icon: string;
  description: string;
}

const PortfolioComparison: React.FC<PortfolioComparisonProps> = ({
  totalValue,
  totalReturn,
  totalReturnPercent,
  portfolioHistory,
}) => {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1M' | '3M' | '6M' | '1Y'>('1M');
  const [showChart, setShowChart] = useState(false);

  // Mock benchmark data - in a real app, this would come from an API
  const benchmarks: Benchmark[] = [
    {
      id: 'sp500',
      name: 'S&P 500',
      symbol: 'SPY',
      returnPercent: 12.3,
      color: '#007AFF',
      icon: 'trending-up',
      description: 'The 500 largest US companies'
    },
    {
      id: 'nasdaq',
      name: 'NASDAQ',
      symbol: 'QQQ',
      returnPercent: 18.7,
      color: '#34C759',
      icon: 'activity',
      description: 'Technology-heavy index'
    },
    {
      id: 'dow',
      name: 'Dow Jones',
      symbol: 'DIA',
      returnPercent: 8.9,
      color: '#FF9500',
      icon: 'bar-chart',
      description: '30 large US companies'
    },
    {
      id: 'total-market',
      name: 'Total Market',
      symbol: 'VTI',
      returnPercent: 11.2,
      color: '#AF52DE',
      icon: 'pie-chart',
      description: 'Entire US stock market'
    }
  ];

  // Filter portfolio history based on selected timeframe
  const getFilteredPortfolioHistory = () => {
    const totalPoints = portfolioHistory.length;
    
    // Calculate how many data points to take based on timeframe
    let pointsToTake: number;
    
    switch (selectedTimeframe) {
      case '1M':
        pointsToTake = Math.min(4, totalPoints); // Last 4 points (1 month)
        break;
      case '3M':
        pointsToTake = Math.min(8, totalPoints); // Last 8 points (3 months)
        break;
      case '6M':
        pointsToTake = Math.min(12, totalPoints); // Last 12 points (6 months)
        break;
      case '1Y':
        pointsToTake = totalPoints; // All points (1 year)
        break;
      default:
        pointsToTake = Math.min(4, totalPoints);
    }
    
    // Always return at least 2 points for comparison
    const actualPoints = Math.max(2, pointsToTake);
    return portfolioHistory.slice(-actualPoints);
  };

  // Calculate performance metrics for the selected timeframe
  const getTimeframePerformance = () => {
    const filteredHistory = getFilteredPortfolioHistory();
    
    // Always ensure we have at least 2 data points
    if (filteredHistory.length < 2) {
      return {
        totalReturn: totalReturn,
        totalReturnPercent: totalReturnPercent,
        startValue: totalValue - totalReturn,
        endValue: totalValue
      };
    }
    
    const startValue = filteredHistory[0].value;
    const endValue = filteredHistory[filteredHistory.length - 1].value;
    const timeframeReturn = endValue - startValue;
    const timeframeReturnPercent = startValue > 0 ? (timeframeReturn / startValue) * 100 : 0;
    
    // Debug logging
    console.log(`Timeframe: ${selectedTimeframe}, Points: ${filteredHistory.length}, Start: ${startValue}, End: ${endValue}, Return: ${timeframeReturn}, Percent: ${timeframeReturnPercent}`);
    
    return {
      totalReturn: timeframeReturn,
      totalReturnPercent: timeframeReturnPercent,
      startValue,
      endValue
    };
  };

  // Generate mock chart data for comparison based on filtered timeframe
  const generateChartData = () => {
    const filteredHistory = getFilteredPortfolioHistory();
    const timeframePerformance = getTimeframePerformance();
    
    if (filteredHistory.length === 0) {
      return {
        labels: [],
        datasets: []
      };
    }
    
    const baseValue = timeframePerformance.startValue;
    const portfolioData = filteredHistory.map((point, index) => {
      const growth = (timeframePerformance.totalReturnPercent / 100) * (index / filteredHistory.length);
      return baseValue * (1 + growth);
    });

    // Adjust benchmark returns based on timeframe
    const getBenchmarkReturn = (annualReturn: number) => {
      switch (selectedTimeframe) {
        case '1M': return annualReturn / 12;
        case '3M': return annualReturn / 4;
        case '6M': return annualReturn / 2;
        case '1Y': return annualReturn;
        default: return annualReturn / 12;
      }
    };

    const sp500Data = filteredHistory.map((_, index) => {
      const growth = (getBenchmarkReturn(12.3) / 100) * (index / filteredHistory.length);
      return baseValue * (1 + growth);
    });

    const nasdaqData = filteredHistory.map((_, index) => {
      const growth = (getBenchmarkReturn(18.7) / 100) * (index / filteredHistory.length);
      return baseValue * (1 + growth);
    });

    return {
      labels: filteredHistory.map(point => {
        const date = new Date(point.date);
        return `${date.getMonth() + 1}/${date.getDate()}`;
      }),
      datasets: [
        {
          data: portfolioData,
          color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
          strokeWidth: 3,
        },
        {
          data: sp500Data,
          color: (opacity = 1) => `rgba(52, 199, 89, ${opacity})`,
          strokeWidth: 2,
        },
        {
          data: nasdaqData,
          color: (opacity = 1) => `rgba(255, 149, 0, ${opacity})`,
          strokeWidth: 2,
        },
      ],
    };
  };

  const chartData = generateChartData();

  const getPerformanceColor = (returnPercent: number) => {
    if (returnPercent > 0) return '#34C759';
    if (returnPercent < 0) return '#FF3B30';
    return '#8E8E93';
  };

  const getPerformanceIcon = (returnPercent: number) => {
    if (returnPercent > 0) return 'trending-up';
    if (returnPercent < 0) return 'trending-down';
    return 'minus';
  };

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const renderBenchmarkCard = (benchmark: Benchmark) => {
    const timeframePerformance = getTimeframePerformance();
    
    // Adjust benchmark return based on timeframe
    const getBenchmarkReturn = (annualReturn: number) => {
      switch (selectedTimeframe) {
        case '1M': return annualReturn / 12;
        case '3M': return annualReturn / 4;
        case '6M': return annualReturn / 2;
        case '1Y': return annualReturn;
        default: return annualReturn / 12;
      }
    };
    
    const adjustedBenchmarkReturn = getBenchmarkReturn(benchmark.returnPercent);
    const isOutperforming = timeframePerformance.totalReturnPercent > adjustedBenchmarkReturn;
    const difference = timeframePerformance.totalReturnPercent - adjustedBenchmarkReturn;
    
    return (
      <View key={benchmark.id} style={styles.benchmarkCard}>
        <View style={styles.benchmarkHeader}>
          <View style={styles.benchmarkInfo}>
            <View style={[styles.benchmarkIcon, { backgroundColor: benchmark.color }]}>
              <Icon name={benchmark.icon} size={16} color="#FFFFFF" />
            </View>
            <View style={styles.benchmarkDetails}>
              <Text style={styles.benchmarkName}>{benchmark.name}</Text>
              <Text style={styles.benchmarkSymbol}>{benchmark.symbol}</Text>
            </View>
          </View>
          <View style={styles.benchmarkPerformance}>
            <Text style={[
              styles.benchmarkReturn,
              { color: getPerformanceColor(adjustedBenchmarkReturn) }
            ]}>
              {formatPercent(adjustedBenchmarkReturn)}
            </Text>
            <Icon 
              name={getPerformanceIcon(adjustedBenchmarkReturn)} 
              size={14} 
              color={getPerformanceColor(adjustedBenchmarkReturn)} 
            />
          </View>
        </View>
        
        <View style={styles.comparisonRow}>
          <View style={styles.comparisonItem}>
            <Text style={styles.comparisonLabel}>Your Portfolio</Text>
            <Text style={[
              styles.comparisonValue,
              { color: getPerformanceColor(timeframePerformance.totalReturnPercent) }
            ]}>
              {formatPercent(timeframePerformance.totalReturnPercent)}
            </Text>
          </View>
          <View style={styles.comparisonItem}>
            <Text style={styles.comparisonLabel}>Difference</Text>
            <Text style={[
              styles.comparisonValue,
              { color: getPerformanceColor(difference) }
            ]}>
              {formatPercent(difference)}
            </Text>
          </View>
        </View>
        
        <View style={styles.benchmarkDescription}>
          <Text style={styles.descriptionText}>{benchmark.description}</Text>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Icon name="bar-chart-2" size={20} color="#007AFF" />
          <Text style={styles.title}>Portfolio Comparison</Text>
        </View>
        <EducationalTooltip
          term="Portfolio Comparison"
          explanation="Compare your portfolio performance against market benchmarks like the S&P 500 to see how well you're doing."
          position="top"
        >
          <Icon name="info" size={16} color="#8E8E93" />
        </EducationalTooltip>
      </View>

      {/* Performance Summary */}
      <View style={styles.summaryCard}>
        <View style={styles.summaryHeader}>
          <Text style={styles.summaryTitle}>Your Performance</Text>
          <View style={styles.timeframeSelector}>
            {(['1M', '3M', '6M', '1Y'] as const).map((timeframe) => (
              <TouchableOpacity
                key={timeframe}
                style={[
                  styles.timeframeButton,
                  selectedTimeframe === timeframe && styles.timeframeButtonSelected
                ]}
                onPress={() => setSelectedTimeframe(timeframe)}
              >
                <Text style={[
                  styles.timeframeText,
                  selectedTimeframe === timeframe && styles.timeframeTextSelected
                ]}>
                  {timeframe}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        
        <View style={styles.summaryContent}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Total Return</Text>
            <Text style={[
              styles.summaryValue,
              { color: getPerformanceColor(getTimeframePerformance().totalReturnPercent) }
            ]}>
              {formatPercent(getTimeframePerformance().totalReturnPercent)}
            </Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Return Amount</Text>
            <Text style={[
              styles.summaryValue,
              { color: getPerformanceColor(getTimeframePerformance().totalReturn) }
            ]}>
              {formatCurrency(getTimeframePerformance().totalReturn)}
            </Text>
          </View>
        </View>
      </View>

      {/* Chart Toggle */}
      <TouchableOpacity
        style={styles.chartToggle}
        onPress={() => setShowChart(!showChart)}
      >
        <View style={styles.chartToggleContent}>
          <Icon name="trending-up" size={16} color="#007AFF" />
          <Text style={styles.chartToggleText}>
            {showChart ? 'Hide' : 'Show'} Performance Chart
          </Text>
        </View>
        <Icon 
          name={showChart ? 'chevron-up' : 'chevron-down'} 
          size={16} 
          color="#8E8E93" 
        />
      </TouchableOpacity>

      {/* Chart */}
      {showChart && (
        <View style={styles.chartContainer}>
          <Text style={styles.chartTitle}>Portfolio vs Benchmarks</Text>
          <LineChart
            data={chartData}
            width={width - 40}
            height={220}
            chartConfig={{
              backgroundColor: '#FFFFFF',
              backgroundGradientFrom: '#FFFFFF',
              backgroundGradientTo: '#FFFFFF',
              decimalPlaces: 0,
              color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              style: {
                borderRadius: 16,
              },
              propsForDots: {
                r: '4',
                strokeWidth: '2',
                stroke: '#007AFF',
              },
            }}
            bezier
            style={styles.chart}
          />
          <View style={styles.chartLegend}>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#007AFF' }]} />
              <Text style={styles.legendText}>Your Portfolio</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#34C759' }]} />
              <Text style={styles.legendText}>S&P 500</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#FF9500' }]} />
              <Text style={styles.legendText}>NASDAQ</Text>
            </View>
          </View>
        </View>
      )}

      {/* Benchmarks */}
      <View style={styles.benchmarksContainer}>
        <Text style={styles.benchmarksTitle}>Market Benchmarks</Text>
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.benchmarksScroll}
        >
          {benchmarks.map(renderBenchmarkCard)}
        </ScrollView>
      </View>

      {/* Insights */}
      <View style={styles.insightsCard}>
        <View style={styles.insightsHeader}>
          <Text style={styles.insightsTitle}>Performance Insights</Text>
        </View>
        <View style={styles.insightsContent}>
          {totalReturnPercent > 12.3 ? (
            <Text style={styles.insightText}>
              🎉 <Text style={styles.insightHighlight}>Outperforming S&P 500!</Text> Your portfolio is beating the market average. Great job!
            </Text>
          ) : (
            <Text style={styles.insightText}>
              📈 <Text style={styles.insightHighlight}>Consider diversification</Text> to potentially improve returns and reduce risk.
            </Text>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  summaryCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  timeframeSelector: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 2,
  },
  timeframeButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  timeframeButtonSelected: {
    backgroundColor: '#007AFF',
  },
  timeframeText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#8E8E93',
  },
  timeframeTextSelected: {
    color: '#FFFFFF',
  },
  summaryContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  summaryItem: {
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  chartToggle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  chartToggleContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  chartToggleText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#007AFF',
  },
  chartContainer: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
    textAlign: 'center',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  chartLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginTop: 12,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  benchmarksContainer: {
    marginBottom: 16,
  },
  benchmarksTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  benchmarksScroll: {
    paddingRight: 16,
  },
  benchmarkCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    minWidth: 200,
  },
  benchmarkHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  benchmarkInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  benchmarkIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  benchmarkDetails: {
    flex: 1,
  },
  benchmarkName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  benchmarkSymbol: {
    fontSize: 12,
    color: '#8E8E93',
  },
  benchmarkPerformance: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  benchmarkReturn: {
    fontSize: 16,
    fontWeight: '700',
  },
  comparisonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  comparisonItem: {
    alignItems: 'center',
  },
  comparisonLabel: {
    fontSize: 11,
    color: '#8E8E93',
    marginBottom: 2,
  },
  comparisonValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  benchmarkDescription: {
    marginTop: 8,
  },
  descriptionText: {
    fontSize: 12,
    color: '#8E8E93',
    lineHeight: 16,
  },
  insightsCard: {
    backgroundColor: '#FFF8E1',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#FFD60A',
  },
  insightsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  insightsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  insightsContent: {
    marginLeft: 24,
  },
  insightText: {
    fontSize: 13,
    color: '#1C1C1E',
    lineHeight: 18,
  },
  insightHighlight: {
    fontWeight: '600',
  },
});

export default PortfolioComparison;
