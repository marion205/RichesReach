/**
 * Advanced Portfolio Analytics
 * Comprehensive portfolio analysis and risk management
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { PieChart, LineChart, BarChart } from 'react-native-chart-kit';
import { useQuery, gql } from '@apollo/client';
import { Ionicons } from '@expo/vector-icons';

const { width: screenWidth } = Dimensions.get('window');

// GraphQL Queries
const GET_PORTFOLIO_OVERVIEW = gql`
  query GetPortfolioOverview {
    portfolioOverview {
      totalValue
      totalCost
      totalReturn
      totalReturnPercent
      dayChange
      dayChangePercent
      positions {
        symbol
        quantity
        currentPrice
        costBasis
        marketValue
        unrealizedPnL
        unrealizedPnLPercent
        allocation
      }
    }
  }
`;

const GET_PORTFOLIO_PERFORMANCE = gql`
  query GetPortfolioPerformance($period: String!) {
    portfolioPerformance(period: $period) {
      dailyReturns
      cumulativeReturns
      benchmarkReturns
      volatility
      sharpeRatio
      maxDrawdown
      beta
      alpha
      correlation
    }
  }
`;

const GET_RISK_METRICS = gql`
  query GetRiskMetrics {
    riskMetrics {
      var95
      var99
      expectedShortfall
      maxDrawdown
      volatility
      beta
      correlationMatrix
      sectorExposure
      concentrationRisk
    }
  }
`;

interface Position {
  symbol: string;
  quantity: number;
  currentPrice: number;
  costBasis: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  allocation: number;
}

interface PortfolioOverview {
  totalValue: number;
  totalCost: number;
  totalReturn: number;
  totalReturnPercent: number;
  dayChange: number;
  dayChangePercent: number;
  positions: Position[];
}

interface PerformanceMetrics {
  dailyReturns: number[];
  cumulativeReturns: number[];
  benchmarkReturns: number[];
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
  beta: number;
  alpha: number;
  correlation: number;
}

interface RiskMetrics {
  var95: number;
  var99: number;
  expectedShortfall: number;
  maxDrawdown: number;
  volatility: number;
  beta: number;
  correlationMatrix: any;
  sectorExposure: any;
  concentrationRisk: number;
}

interface PortfolioAnalyticsProps {
  userId: string;
  onPositionSelect?: (position: Position) => void;
  onRiskAlert?: (alert: string) => void;
}

export const PortfolioAnalytics: React.FC<PortfolioAnalyticsProps> = ({
  userId,
  onPositionSelect,
  onRiskAlert,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'risk' | 'allocation'>('overview');
  const [selectedPeriod, setSelectedPeriod] = useState('1Y');
  const [isLoading, setIsLoading] = useState(true);

  const { data: overviewData, loading: overviewLoading } = useQuery(GET_PORTFOLIO_OVERVIEW);
  const { data: performanceData, loading: performanceLoading } = useQuery(
    GET_PORTFOLIO_PERFORMANCE,
    { variables: { period: selectedPeriod } }
  );
  const { data: riskData, loading: riskLoading } = useQuery(GET_RISK_METRICS);

  useEffect(() => {
    setIsLoading(overviewLoading || performanceLoading || riskLoading);
  }, [overviewLoading, performanceLoading, riskLoading]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getReturnColor = (value: number) => {
    if (value > 0) return '#00ff88';
    if (value < 0) return '#ff4444';
    return '#888';
  };

  const formatAllocationData = (positions: Position[]) => {
    const colors = ['#00ff88', '#ff4444', '#ffbb00', '#007bff', '#ff8800', '#8800ff'];
    
    return {
      labels: positions.map(p => p.symbol),
      data: positions.map(p => p.allocation),
      colors: colors.slice(0, positions.length),
    };
  };

  const formatPerformanceData = (performance: PerformanceMetrics) => {
    const labels = Array.from({ length: performance.dailyReturns.length }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (performance.dailyReturns.length - i - 1));
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    return {
      labels: labels.slice(-30), // Last 30 days
      datasets: [
        {
          data: performance.dailyReturns.slice(-30),
          color: (opacity = 1) => `rgba(0, 255, 0, ${opacity})`,
          strokeWidth: 2,
        },
        {
          data: performance.benchmarkReturns.slice(-30),
          color: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
          strokeWidth: 1,
        },
      ],
    };
  };

  const formatRiskData = (risk: RiskMetrics) => {
    return {
      labels: ['VaR 95%', 'VaR 99%', 'Expected Shortfall', 'Max Drawdown'],
      data: [
        Math.abs(risk.var95),
        Math.abs(risk.var99),
        Math.abs(risk.expectedShortfall),
        Math.abs(risk.maxDrawdown),
      ],
    };
  };

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
  };

  const renderOverviewTab = () => {
    if (!overviewData?.portfolioOverview) return null;

    const portfolio = overviewData.portfolioOverview;
    const allocationData = formatAllocationData(portfolio.positions);

    return (
      <ScrollView style={styles.tabContent}>
        {/* Portfolio Summary */}
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Portfolio Summary</Text>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Total Value</Text>
            <Text style={styles.summaryValue}>{formatCurrency(portfolio.totalValue)}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Total Return</Text>
            <Text style={[
              styles.summaryValue,
              { color: getReturnColor(portfolio.totalReturn) }
            ]}>
              {formatCurrency(portfolio.totalReturn)} ({formatPercent(portfolio.totalReturnPercent)})
            </Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Day Change</Text>
            <Text style={[
              styles.summaryValue,
              { color: getReturnColor(portfolio.dayChange) }
            ]}>
              {formatCurrency(portfolio.dayChange)} ({formatPercent(portfolio.dayChangePercent)})
            </Text>
          </View>
        </View>

        {/* Allocation Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.chartTitle}>Portfolio Allocation</Text>
          <PieChart
            data={allocationData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            accessor="data"
            backgroundColor="transparent"
            paddingLeft="15"
            center={[10, 0]}
            absolute
          />
        </View>

        {/* Top Positions */}
        <View style={styles.positionsCard}>
          <Text style={styles.positionsTitle}>Top Positions</Text>
          {portfolio.positions.slice(0, 5).map((position, index) => (
            <TouchableOpacity
              key={position.symbol}
              style={styles.positionRow}
              onPress={() => onPositionSelect?.(position)}
            >
              <View style={styles.positionInfo}>
                <Text style={styles.positionSymbol}>{position.symbol}</Text>
                <Text style={styles.positionQuantity}>{position.quantity} shares</Text>
              </View>
              <View style={styles.positionValues}>
                <Text style={styles.positionValue}>{formatCurrency(position.marketValue)}</Text>
                <Text style={[
                  styles.positionPnL,
                  { color: getReturnColor(position.unrealizedPnL) }
                ]}>
                  {formatCurrency(position.unrealizedPnL)} ({formatPercent(position.unrealizedPnLPercent)})
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    );
  };

  const renderPerformanceTab = () => {
    if (!performanceData?.portfolioPerformance) return null;

    const performance = performanceData.portfolioPerformance;
    const performanceChartData = formatPerformanceData(performance);

    return (
      <ScrollView style={styles.tabContent}>
        {/* Performance Metrics */}
        <View style={styles.metricsCard}>
          <Text style={styles.metricsTitle}>Performance Metrics</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Volatility</Text>
              <Text style={styles.metricValue}>{performance.volatility.toFixed(2)}%</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Sharpe Ratio</Text>
              <Text style={styles.metricValue}>{performance.sharpeRatio.toFixed(2)}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Max Drawdown</Text>
              <Text style={[styles.metricValue, { color: '#ff4444' }]}>
                {performance.maxDrawdown.toFixed(2)}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Beta</Text>
              <Text style={styles.metricValue}>{performance.beta.toFixed(2)}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Alpha</Text>
              <Text style={[
                styles.metricValue,
                { color: getReturnColor(performance.alpha) }
              ]}>
                {performance.alpha.toFixed(2)}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Correlation</Text>
              <Text style={styles.metricValue}>{performance.correlation.toFixed(2)}</Text>
            </View>
          </View>
        </View>

        {/* Performance Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.chartTitle}>Daily Returns vs Benchmark</Text>
          <LineChart
            data={performanceChartData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
          />
        </View>

        {/* Period Selector */}
        <View style={styles.periodSelector}>
          {['1M', '3M', '6M', '1Y', '2Y', '5Y'].map((period) => (
            <TouchableOpacity
              key={period}
              style={[
                styles.periodButton,
                selectedPeriod === period && styles.activePeriodButton,
              ]}
              onPress={() => setSelectedPeriod(period)}
            >
              <Text style={[
                styles.periodButtonText,
                selectedPeriod === period && styles.activePeriodButtonText,
              ]}>
                {period}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    );
  };

  const renderRiskTab = () => {
    if (!riskData?.riskMetrics) return null;

    const risk = riskData.riskMetrics;
    const riskChartData = formatRiskData(risk);

    return (
      <ScrollView style={styles.tabContent}>
        {/* Risk Metrics */}
        <View style={styles.metricsCard}>
          <Text style={styles.metricsTitle}>Risk Metrics</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>VaR 95%</Text>
              <Text style={[styles.metricValue, { color: '#ff4444' }]}>
                {formatCurrency(risk.var95)}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>VaR 99%</Text>
              <Text style={[styles.metricValue, { color: '#ff4444' }]}>
                {formatCurrency(risk.var99)}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Expected Shortfall</Text>
              <Text style={[styles.metricValue, { color: '#ff4444' }]}>
                {formatCurrency(risk.expectedShortfall)}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Max Drawdown</Text>
              <Text style={[styles.metricValue, { color: '#ff4444' }]}>
                {risk.maxDrawdown.toFixed(2)}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Volatility</Text>
              <Text style={styles.metricValue}>{risk.volatility.toFixed(2)}%</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Concentration Risk</Text>
              <Text style={[
                styles.metricValue,
                { color: risk.concentrationRisk > 0.3 ? '#ff4444' : '#00ff88' }
              ]}>
                {risk.concentrationRisk.toFixed(2)}
              </Text>
            </View>
          </View>
        </View>

        {/* Risk Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.chartTitle}>Risk Exposure</Text>
          <BarChart
            data={riskChartData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            style={styles.chart}
            showValuesOnTopOfBars={true}
          />
        </View>

        {/* Risk Alerts */}
        <View style={styles.alertsCard}>
          <Text style={styles.alertsTitle}>Risk Alerts</Text>
          {risk.concentrationRisk > 0.3 && (
            <View style={styles.alertItem}>
              <Ionicons name="warning" size={20} color="#ff4444" />
              <Text style={styles.alertText}>
                High concentration risk detected. Consider diversifying your portfolio.
              </Text>
            </View>
          )}
          {risk.maxDrawdown > 0.2 && (
            <View style={styles.alertItem}>
              <Ionicons name="warning" size={20} color="#ff4444" />
              <Text style={styles.alertText}>
                Maximum drawdown exceeds 20%. Review your risk management strategy.
              </Text>
            </View>
          )}
          {risk.volatility > 0.3 && (
            <View style={styles.alertItem}>
              <Ionicons name="warning" size={20} color="#ffbb00" />
              <Text style={styles.alertText}>
                High volatility detected. Consider reducing position sizes.
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    );
  };

  const renderAllocationTab = () => {
    if (!overviewData?.portfolioOverview) return null;

    const portfolio = overviewData.portfolioOverview;
    const allocationData = formatAllocationData(portfolio.positions);

    return (
      <ScrollView style={styles.tabContent}>
        {/* Allocation Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.chartTitle}>Portfolio Allocation</Text>
          <PieChart
            data={allocationData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            accessor="data"
            backgroundColor="transparent"
            paddingLeft="15"
            center={[10, 0]}
            absolute
          />
        </View>

        {/* Detailed Allocation */}
        <View style={styles.allocationCard}>
          <Text style={styles.allocationTitle}>Detailed Allocation</Text>
          {portfolio.positions.map((position, index) => (
            <View key={position.symbol} style={styles.allocationRow}>
              <View style={styles.allocationInfo}>
                <Text style={styles.allocationSymbol}>{position.symbol}</Text>
                <Text style={styles.allocationQuantity}>{position.quantity} shares</Text>
              </View>
              <View style={styles.allocationValues}>
                <Text style={styles.allocationPercent}>{position.allocation.toFixed(1)}%</Text>
                <Text style={styles.allocationValue}>{formatCurrency(position.marketValue)}</Text>
              </View>
              <View style={[
                styles.allocationBar,
                { width: `${position.allocation}%` }
              ]} />
            </View>
          ))}
        </View>
      </ScrollView>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab();
      case 'performance':
        return renderPerformanceTab();
      case 'risk':
        return renderRiskTab();
      case 'allocation':
        return renderAllocationTab();
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0F0" />
        <Text style={styles.loadingText}>Loading portfolio analytics...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Portfolio Analytics</Text>
        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="settings-outline" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        {[
          { key: 'overview', label: 'Overview', icon: 'home-outline' },
          { key: 'performance', label: 'Performance', icon: 'trending-up-outline' },
          { key: 'risk', label: 'Risk', icon: 'shield-outline' },
          { key: 'allocation', label: 'Allocation', icon: 'pie-chart-outline' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[
              styles.tabButton,
              activeTab === tab.key && styles.activeTabButton,
            ]}
            onPress={() => setActiveTab(tab.key as any)}
          >
            <Ionicons
              name={tab.icon as any}
              size={20}
              color={activeTab === tab.key ? '#0F0' : '#888'}
            />
            <Text style={[
              styles.tabText,
              activeTab === tab.key && styles.activeTabText,
            ]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Tab Content */}
      <View style={styles.content}>
        {renderTabContent()}
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerButton: {
    padding: 5,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 20,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    marginHorizontal: 5,
  },
  activeTabButton: {
    borderBottomWidth: 2,
    borderBottomColor: '#0F0',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#888',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#0F0',
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
  },
  summaryCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  summaryLabel: {
    fontSize: 16,
    color: '#ccc',
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  chartCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  chart: {
    borderRadius: 16,
  },
  positionsCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  positionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  positionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  positionInfo: {
    flex: 1,
  },
  positionSymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  positionQuantity: {
    fontSize: 14,
    color: '#888',
  },
  positionValues: {
    alignItems: 'flex-end',
  },
  positionValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  positionPnL: {
    fontSize: 14,
    fontWeight: '500',
  },
  metricsCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  metricsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricItem: {
    width: '48%',
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 5,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  periodSelector: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  periodButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
    borderRadius: 20,
    backgroundColor: '#333',
  },
  activePeriodButton: {
    backgroundColor: '#007bff',
  },
  periodButtonText: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '500',
  },
  activePeriodButtonText: {
    fontWeight: 'bold',
  },
  alertsCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  alertsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  alertItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  alertText: {
    flex: 1,
    marginLeft: 10,
    fontSize: 14,
    color: '#fff',
  },
  allocationCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  allocationTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  allocationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
    position: 'relative',
  },
  allocationInfo: {
    flex: 1,
  },
  allocationSymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  allocationQuantity: {
    fontSize: 14,
    color: '#888',
  },
  allocationValues: {
    alignItems: 'flex-end',
  },
  allocationPercent: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0F0',
  },
  allocationValue: {
    fontSize: 14,
    color: '#ccc',
  },
  allocationBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    height: 2,
    backgroundColor: '#0F0',
  },
});

export default PortfolioAnalytics;
