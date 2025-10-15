import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

interface Trade {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  entryDate: string;
  exitDate: string;
  pnl: number;
  pnlPercent: number;
  status: 'open' | 'closed' | 'stopped';
  strategy: string;
  notes: string;
}

interface PerformanceMetrics {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  totalReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  avgHoldingPeriod: number;
}

interface PortfolioAnalytics {
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  dayChange: number;
  dayChangePercent: number;
  unrealizedPnL: number;
  realizedPnL: number;
  cashBalance: number;
  marginUsed: number;
  buyingPower: number;
}

const SwingTradingPerformance: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('30d');

  // Mock data - in real app, this would come from API
  const portfolioAnalytics: PortfolioAnalytics = {
    totalValue: 125430.50,
    totalReturn: 15430.50,
    totalReturnPercent: 14.03,
    dayChange: 1250.75,
    dayChangePercent: 1.01,
    unrealizedPnL: 3250.25,
    realizedPnL: 12180.25,
    cashBalance: 25000.00,
    marginUsed: 15000.00,
    buyingPower: 10000.00
  };

  const performanceMetrics: PerformanceMetrics = {
    totalTrades: 47,
    winningTrades: 32,
    losingTrades: 15,
    winRate: 68.09,
    avgWin: 485.32,
    avgLoss: -287.45,
    profitFactor: 1.69,
    totalReturn: 15430.50,
    maxDrawdown: -8.5,
    sharpeRatio: 1.42,
    avgHoldingPeriod: 5.2
  };

  const recentTrades: Trade[] = [
    {
      id: '1',
      symbol: 'AAPL',
      side: 'long',
      entryPrice: 175.50,
      exitPrice: 182.30,
      quantity: 100,
      entryDate: '2024-01-15',
      exitDate: '2024-01-18',
      pnl: 680.00,
      pnlPercent: 3.88,
      status: 'closed',
      strategy: 'RSI Rebound',
      notes: 'Strong volume confirmation'
    },
    {
      id: '2',
      symbol: 'TSLA',
      side: 'long',
      entryPrice: 245.30,
      exitPrice: 238.00,
      quantity: 50,
      entryDate: '2024-01-16',
      exitDate: '2024-01-17',
      pnl: -365.00,
      pnlPercent: -2.98,
      status: 'stopped',
      strategy: 'Breakout',
      notes: 'Stop loss hit'
    },
    {
      id: '3',
      symbol: 'NVDA',
      side: 'long',
      entryPrice: 420.75,
      exitPrice: 445.50,
      quantity: 25,
      entryDate: '2024-01-12',
      exitDate: '2024-01-19',
      pnl: 618.75,
      pnlPercent: 5.88,
      status: 'closed',
      strategy: 'EMA Crossover',
      notes: 'Target reached'
    },
    {
      id: '4',
      symbol: 'MSFT',
      side: 'long',
      entryPrice: 385.20,
      exitPrice: 0,
      quantity: 30,
      entryDate: '2024-01-20',
      exitDate: '',
      pnl: 0,
      pnlPercent: 0,
      status: 'open',
      strategy: 'Bollinger Squeeze',
      notes: 'Currently holding'
    }
  ];

  const periods = ['7d', '30d', '90d', '1y', 'all'];

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return '#10B981';
    if (pnl < 0) return '#EF4444';
    return '#6B7280';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'closed': return '#10B981';
      case 'stopped': return '#EF4444';
      case 'open': return '#3B82F6';
      default: return '#6B7280';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'closed': return 'check-circle';
      case 'stopped': return 'x-circle';
      case 'open': return 'clock';
      default: return 'circle';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Period Selector */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="calendar" size={20} color="#3B82F6" />
          <Text style={styles.sectionTitle}>Performance Period</Text>
        </View>
        
        <View style={styles.periodSelector}>
          {periods.map((period) => (
            <TouchableOpacity
              key={period}
              style={[
                styles.periodButton,
                selectedPeriod === period && styles.periodButtonActive
              ]}
              onPress={() => setSelectedPeriod(period)}
            >
              <Text style={[
                styles.periodText,
                selectedPeriod === period && styles.periodTextActive
              ]}>
                {period.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Portfolio Overview */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="pie-chart" size={20} color="#10B981" />
          <Text style={styles.sectionTitle}>Portfolio Overview</Text>
          <Text style={styles.sectionSubtitle}>Current Status</Text>
        </View>
        
        <View style={styles.portfolioGrid}>
          <View style={styles.portfolioCard}>
            <Text style={styles.portfolioLabel}>Total Value</Text>
            <Text style={styles.portfolioValue}>{formatCurrency(portfolioAnalytics.totalValue)}</Text>
            <Text style={[styles.portfolioChange, { color: getPnLColor(portfolioAnalytics.dayChange) }]}>
              {formatCurrency(portfolioAnalytics.dayChange)} ({formatPercentage(portfolioAnalytics.dayChangePercent)})
            </Text>
          </View>

          <View style={styles.portfolioCard}>
            <Text style={styles.portfolioLabel}>Total Return</Text>
            <Text style={[styles.portfolioValue, { color: getPnLColor(portfolioAnalytics.totalReturn) }]}>
              {formatCurrency(portfolioAnalytics.totalReturn)}
            </Text>
            <Text style={[styles.portfolioChange, { color: getPnLColor(portfolioAnalytics.totalReturn) }]}>
              {formatPercentage(portfolioAnalytics.totalReturnPercent)}
            </Text>
          </View>

          <View style={styles.portfolioCard}>
            <Text style={styles.portfolioLabel}>Unrealized P&L</Text>
            <Text style={[styles.portfolioValue, { color: getPnLColor(portfolioAnalytics.unrealizedPnL) }]}>
              {formatCurrency(portfolioAnalytics.unrealizedPnL)}
            </Text>
            <Text style={styles.portfolioChange}>Open Positions</Text>
          </View>

          <View style={styles.portfolioCard}>
            <Text style={styles.portfolioLabel}>Realized P&L</Text>
            <Text style={[styles.portfolioValue, { color: getPnLColor(portfolioAnalytics.realizedPnL) }]}>
              {formatCurrency(portfolioAnalytics.realizedPnL)}
            </Text>
            <Text style={styles.portfolioChange}>Closed Trades</Text>
          </View>
        </View>

        <View style={styles.cashInfo}>
          <View style={styles.cashItem}>
            <Text style={styles.cashLabel}>Cash Balance</Text>
            <Text style={styles.cashValue}>{formatCurrency(portfolioAnalytics.cashBalance)}</Text>
          </View>
          <View style={styles.cashItem}>
            <Text style={styles.cashLabel}>Buying Power</Text>
            <Text style={styles.cashValue}>{formatCurrency(portfolioAnalytics.buyingPower)}</Text>
          </View>
          <View style={styles.cashItem}>
            <Text style={styles.cashLabel}>Margin Used</Text>
            <Text style={styles.cashValue}>{formatCurrency(portfolioAnalytics.marginUsed)}</Text>
          </View>
        </View>
      </View>

      {/* Performance Metrics */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="bar-chart-2" size={20} color="#F59E0B" />
          <Text style={styles.sectionTitle}>Performance Metrics</Text>
          <Text style={styles.sectionSubtitle}>Trading Statistics</Text>
        </View>
        
        <View style={styles.metricsGrid}>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Win Rate</Text>
            <Text style={[styles.metricValue, { color: '#10B981' }]}>
              {performanceMetrics.winRate.toFixed(1)}%
            </Text>
            <Text style={styles.metricSubtext}>
              {performanceMetrics.winningTrades}/{performanceMetrics.totalTrades} trades
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Profit Factor</Text>
            <Text style={[styles.metricValue, { color: performanceMetrics.profitFactor > 1 ? '#10B981' : '#EF4444' }]}>
              {performanceMetrics.profitFactor.toFixed(2)}
            </Text>
            <Text style={styles.metricSubtext}>
              Avg Win: {formatCurrency(performanceMetrics.avgWin)}
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Sharpe Ratio</Text>
            <Text style={[styles.metricValue, { color: performanceMetrics.sharpeRatio > 1 ? '#10B981' : '#EF4444' }]}>
              {performanceMetrics.sharpeRatio.toFixed(2)}
            </Text>
            <Text style={styles.metricSubtext}>Risk-Adjusted Return</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Max Drawdown</Text>
            <Text style={[styles.metricValue, { color: '#EF4444' }]}>
              {performanceMetrics.maxDrawdown.toFixed(1)}%
            </Text>
            <Text style={styles.metricSubtext}>Worst Period</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Avg Holding</Text>
            <Text style={styles.metricValue}>
              {performanceMetrics.avgHoldingPeriod.toFixed(1)} days
            </Text>
            <Text style={styles.metricSubtext}>Swing Duration</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Avg Loss</Text>
            <Text style={[styles.metricValue, { color: '#EF4444' }]}>
              {formatCurrency(performanceMetrics.avgLoss)}
            </Text>
            <Text style={styles.metricSubtext}>Per Losing Trade</Text>
          </View>
        </View>
      </View>

      {/* Recent Trades */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="list" size={20} color="#8B5CF6" />
          <Text style={styles.sectionTitle}>Recent Trades</Text>
          <Text style={styles.sectionSubtitle}>Trade History</Text>
        </View>
        
        <View style={styles.tradesList}>
          {recentTrades.map((trade) => (
            <View key={trade.id} style={styles.tradeCard}>
              <View style={styles.tradeHeader}>
                <View style={styles.tradeInfo}>
                  <Text style={styles.tradeSymbol}>{trade.symbol}</Text>
                  <Text style={styles.tradeStrategy}>{trade.strategy}</Text>
                </View>
                <View style={styles.tradeStatus}>
                  <Icon 
                    name={getStatusIcon(trade.status)} 
                    size={16} 
                    color={getStatusColor(trade.status)} 
                  />
                  <Text style={[styles.statusText, { color: getStatusColor(trade.status) }]}>
                    {trade.status.toUpperCase()}
                  </Text>
                </View>
              </View>

              <View style={styles.tradeDetails}>
                <View style={styles.tradeSide}>
                  <Text style={[styles.sideText, { color: trade.side === 'long' ? '#10B981' : '#EF4444' }]}>
                    {trade.side.toUpperCase()}
                  </Text>
                  <Text style={styles.quantityText}>{trade.quantity} shares</Text>
                </View>
                
                <View style={styles.tradePrices}>
                  <Text style={styles.priceText}>
                    Entry: {formatCurrency(trade.entryPrice)}
                  </Text>
                  {trade.exitPrice > 0 && (
                    <Text style={styles.priceText}>
                      Exit: {formatCurrency(trade.exitPrice)}
                    </Text>
                  )}
                </View>
              </View>

              <View style={styles.tradePnL}>
                <Text style={[styles.pnlText, { color: getPnLColor(trade.pnl) }]}>
                  {formatCurrency(trade.pnl)} ({formatPercentage(trade.pnlPercent)})
                </Text>
                <Text style={styles.dateText}>
                  {trade.entryDate} - {trade.exitDate || 'Open'}
                </Text>
              </View>

              {trade.notes && (
                <Text style={styles.tradeNotes}>{trade.notes}</Text>
              )}
            </View>
          ))}
        </View>
      </View>

      {/* Performance Chart Placeholder */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="trending-up" size={20} color="#EC4899" />
          <Text style={styles.sectionTitle}>Equity Curve</Text>
          <Text style={styles.sectionSubtitle}>Portfolio Growth</Text>
        </View>
        
        <View style={styles.chartPlaceholder}>
          <Icon name="bar-chart" size={48} color="#D1D5DB" />
          <Text style={styles.chartPlaceholderText}>Equity Curve Chart</Text>
          <Text style={styles.chartPlaceholderSubtext}>
            Interactive chart showing portfolio value over time
          </Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  section: {
    marginBottom: 24,
    paddingHorizontal: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginLeft: 8,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 'auto',
  },
  periodSelector: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  periodButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  periodButtonActive: {
    backgroundColor: '#3B82F6',
  },
  periodText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
  periodTextActive: {
    color: '#FFFFFF',
  },
  portfolioGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  portfolioCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    width: (width - 48) / 2,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  portfolioLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  portfolioValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  portfolioChange: {
    fontSize: 12,
    fontWeight: '600',
  },
  cashInfo: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  cashItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  cashLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  cashValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    width: (width - 48) / 2,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  metricSubtext: {
    fontSize: 11,
    color: '#6B7280',
  },
  tradesList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  tradeCard: {
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  tradeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  tradeInfo: {
    flex: 1,
  },
  tradeSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  tradeStrategy: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  tradeStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '700',
    marginLeft: 4,
  },
  tradeDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  tradeSide: {
    alignItems: 'flex-start',
  },
  sideText: {
    fontSize: 14,
    fontWeight: '700',
  },
  quantityText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  tradePrices: {
    alignItems: 'flex-end',
  },
  priceText: {
    fontSize: 12,
    color: '#6B7280',
  },
  tradePnL: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  pnlText: {
    fontSize: 16,
    fontWeight: '700',
  },
  dateText: {
    fontSize: 12,
    color: '#6B7280',
  },
  tradeNotes: {
    fontSize: 12,
    color: '#6B7280',
    fontStyle: 'italic',
  },
  chartPlaceholder: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  chartPlaceholderText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginTop: 12,
    marginBottom: 4,
  },
  chartPlaceholderSubtext: {
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
  },
});

export default SwingTradingPerformance;
