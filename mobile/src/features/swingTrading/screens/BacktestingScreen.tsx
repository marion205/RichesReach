import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  SafeAreaView,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery } from '@apollo/client';
import { GET_SWING_SIGNALS } from '../../../graphql/swingTrading';

const { width } = Dimensions.get('window');

interface BacktestingScreenProps {
  navigateTo?: (screen: string) => void;
}

interface BacktestResult {
  id: string;
  strategy: string;
  startDate: string;
  endDate: string;
  totalTrades: number;
  winRate: number;
  totalReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  profitFactor: number;
  avgHoldingPeriod: number;
  status: 'completed' | 'running' | 'failed';
}

const BacktestingScreen: React.FC<BacktestingScreenProps> = ({ navigateTo: navigateToProp }) => {
  const navigation = useNavigation<any>();
  
  // Use React Navigation if navigateTo prop not provided
  const navigateTo = navigateToProp || ((screen: string) => {
    try {
      navigation.navigate(screen as never);
    } catch (error) {
      console.warn('Navigation error:', error);
      // Fallback to globalNavigate if available
      try {
        if (typeof window !== 'undefined' && (window as any).__navigateToGlobal) {
          (window as any).__navigateToGlobal(screen);
        }
      } catch (fallbackError) {
        console.error('All navigation methods failed:', fallbackError);
      }
    }
  });
  
  // Ensure navigateTo is always a function
  if (typeof navigateTo !== 'function') {
    console.error('navigateTo is not a function:', typeof navigateTo, navigateTo);
  }
  const [refreshing, setRefreshing] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState('momentum');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1Y');

  // Mock backtest results - replace with actual GraphQL query
  const [backtestResults, setBacktestResults] = useState<BacktestResult[]>([
    {
      id: '1',
      strategy: 'Momentum Breakout',
      startDate: '2023-01-01',
      endDate: '2023-12-31',
      totalTrades: 45,
      winRate: 68.9,
      totalReturn: 24.5,
      maxDrawdown: -8.2,
      sharpeRatio: 1.85,
      profitFactor: 2.1,
      avgHoldingPeriod: 12.5,
      status: 'completed',
    },
    {
      id: '2',
      strategy: 'Mean Reversion',
      startDate: '2023-01-01',
      endDate: '2023-12-31',
      totalTrades: 38,
      winRate: 71.1,
      totalReturn: 18.3,
      maxDrawdown: -5.8,
      sharpeRatio: 1.62,
      profitFactor: 1.9,
      avgHoldingPeriod: 8.2,
      status: 'completed',
    },
    {
      id: '3',
      strategy: 'Trend Following',
      startDate: '2023-01-01',
      endDate: '2023-12-31',
      totalTrades: 52,
      winRate: 55.8,
      totalReturn: 31.2,
      maxDrawdown: -12.4,
      sharpeRatio: 1.45,
      profitFactor: 1.7,
      avgHoldingPeriod: 15.8,
      status: 'completed',
    },
  ]);

  const strategies = [
    { id: 'momentum', name: 'Momentum Breakout', description: 'Breakout strategies based on price momentum' },
    { id: 'mean-reversion', name: 'Mean Reversion', description: 'Strategies that capitalize on price reversals' },
    { id: 'trend-following', name: 'Trend Following', description: 'Following established market trends' },
    { id: 'volatility', name: 'Volatility Trading', description: 'Strategies based on volatility patterns' },
  ];

  const timeframes = [
    { id: '1M', name: '1 Month', description: 'Last 30 days' },
    { id: '3M', name: '3 Months', description: 'Last 90 days' },
    { id: '6M', name: '6 Months', description: 'Last 180 days' },
    { id: '1Y', name: '1 Year', description: 'Last 365 days' },
    { id: '2Y', name: '2 Years', description: 'Last 2 years' },
  ];

  const onRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  };

  const runBacktest = () => {
    Alert.alert(
      'Run Backtest',
      `Run ${strategies.find(s => s.id === selectedStrategy)?.name} strategy for ${timeframes.find(t => t.id === selectedTimeframe)?.name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Run', 
          onPress: () => {
            // Add new running backtest
            const newBacktest: BacktestResult = {
              id: Date.now().toString(),
              strategy: strategies.find(s => s.id === selectedStrategy)?.name || 'Unknown',
              startDate: new Date().toISOString().split('T')[0],
              endDate: new Date().toISOString().split('T')[0],
              totalTrades: 0,
              winRate: 0,
              totalReturn: 0,
              maxDrawdown: 0,
              sharpeRatio: 0,
              profitFactor: 0,
              avgHoldingPeriod: 0,
              status: 'running',
            };
            setBacktestResults(prev => [newBacktest, ...prev]);
            
            // Simulate completion after 3 seconds
            setTimeout(() => {
              setBacktestResults(prev => prev.map(bt => 
                bt.id === newBacktest.id 
                  ? { ...bt, status: 'completed' as const, totalTrades: 42, winRate: 65.5, totalReturn: 19.8, maxDrawdown: -7.2, sharpeRatio: 1.72, profitFactor: 1.95, avgHoldingPeriod: 11.3 }
                  : bt
              ));
            }, 3000);
          }
        }
      ]
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#22C55E';
      case 'running': return '#F59E0B';
      case 'failed': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return 'check-circle';
      case 'running': return 'clock';
      case 'failed': return 'x-circle';
      default: return 'help-circle';
    }
  };

  const formatNumber = (num: number, decimals: number = 1) => {
    return num.toFixed(decimals);
  };

  const formatPercentage = (num: number) => {
    return `${num >= 0 ? '+' : ''}${formatNumber(num)}%`;
  };

  const renderBacktestCard = (result: BacktestResult) => (
    <View key={result.id} style={styles.backtestCard}>
      <View style={styles.backtestHeader}>
        <View style={styles.backtestTitleContainer}>
          <Text style={styles.backtestTitle}>{result.strategy}</Text>
          <View style={styles.backtestDateContainer}>
            <Text style={styles.backtestDate}>{result.startDate} - {result.endDate}</Text>
          </View>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(result.status) }]}>
          <Icon name={getStatusIcon(result.status)} size={12} color="white" />
          <Text style={styles.statusText}>{result.status.toUpperCase()}</Text>
        </View>
      </View>

      {result.status === 'completed' && (
        <>
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Total Trades</Text>
              <Text style={styles.metricValue}>{result.totalTrades}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Win Rate</Text>
              <Text style={[styles.metricValue, { color: result.winRate >= 60 ? '#22C55E' : '#EF4444' }]}>
                {formatNumber(result.winRate)}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Total Return</Text>
              <Text style={[styles.metricValue, { color: result.totalReturn >= 0 ? '#22C55E' : '#EF4444' }]}>
                {formatPercentage(result.totalReturn)}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Max Drawdown</Text>
              <Text style={[styles.metricValue, { color: '#EF4444' }]}>
                {formatPercentage(result.maxDrawdown)}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Sharpe Ratio</Text>
              <Text style={[styles.metricValue, { color: result.sharpeRatio >= 1.5 ? '#22C55E' : '#F59E0B' }]}>
                {formatNumber(result.sharpeRatio, 2)}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Profit Factor</Text>
              <Text style={[styles.metricValue, { color: result.profitFactor >= 1.5 ? '#22C55E' : '#F59E0B' }]}>
                {formatNumber(result.profitFactor, 2)}
              </Text>
            </View>
          </View>

          <View style={styles.backtestActions}>
            <TouchableOpacity style={styles.actionButton}>
              <Icon name="bar-chart-2" size={16} color="#3B82F6" />
              <Text style={styles.actionButtonText}>View Details</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionButton}>
              <Icon name="download" size={16} color="#3B82F6" />
              <Text style={styles.actionButtonText}>Export</Text>
            </TouchableOpacity>
          </View>
        </>
      )}

      {result.status === 'running' && (
        <View style={styles.runningContainer}>
          <ActivityIndicator size="small" color="#F59E0B" />
          <Text style={styles.runningText}>Running backtest...</Text>
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigateTo('swing-trading-test')}
        >
          <Icon name="arrow-left" size={24} color="#6B7280" />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={styles.headerTitle}>Backtesting</Text>
          <Text style={styles.headerSubtitle}>Test strategies with historical data</Text>
        </View>
        <TouchableOpacity
          style={styles.helpButton}
          onPress={() => Alert.alert('Help', 'Backtesting allows you to test trading strategies using historical data to see how they would have performed.')}
        >
          <Icon name="help-circle" size={20} color="#6B7280" />
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Strategy Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Strategy Selection</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.strategyScroll}>
            {strategies.map((strategy) => (
              <TouchableOpacity
                key={strategy.id}
                style={[
                  styles.strategyCard,
                  selectedStrategy === strategy.id && styles.strategyCardSelected
                ]}
                onPress={() => setSelectedStrategy(strategy.id)}
              >
                <Text style={[
                  styles.strategyName,
                  selectedStrategy === strategy.id && styles.strategyNameSelected
                ]}>
                  {strategy.name}
                </Text>
                <Text style={styles.strategyDescription}>{strategy.description}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Timeframe Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Time Period</Text>
          <View style={styles.timeframeGrid}>
            {timeframes.map((timeframe) => (
              <TouchableOpacity
                key={timeframe.id}
                style={[
                  styles.timeframeCard,
                  selectedTimeframe === timeframe.id && styles.timeframeCardSelected
                ]}
                onPress={() => setSelectedTimeframe(timeframe.id)}
              >
                <Text style={[
                  styles.timeframeName,
                  selectedTimeframe === timeframe.id && styles.timeframeNameSelected
                ]}>
                  {timeframe.name}
                </Text>
                <Text style={styles.timeframeDescription}>{timeframe.description}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Run Backtest Button */}
        <TouchableOpacity style={styles.runButton} onPress={runBacktest}>
          <LinearGradient
            colors={['#3B82F6', '#1D4ED8']}
            style={styles.runButtonGradient}
          >
            <Icon name="play" size={20} color="white" />
            <Text style={styles.runButtonText}>Run Backtest</Text>
          </LinearGradient>
        </TouchableOpacity>

        {/* Results Section */}
        <View style={styles.section}>
          <View style={styles.resultsHeader}>
            <Text style={styles.sectionTitle}>Backtest Results</Text>
            <Text style={styles.resultsCount}>{backtestResults.length} results</Text>
          </View>
          
          {backtestResults.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="bar-chart-2" size={48} color="#9CA3AF" />
              <Text style={styles.emptyTitle}>No Backtests Yet</Text>
              <Text style={styles.emptyDescription}>
                Run your first backtest to see how your strategy performs with historical data.
              </Text>
            </View>
          ) : (
            backtestResults.map(renderBacktestCard)
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  headerTitleContainer: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  helpButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  section: {
    margin: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  strategyScroll: {
    marginHorizontal: -16,
    paddingHorizontal: 16,
  },
  strategyCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    width: 200,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  strategyCardSelected: {
    borderColor: '#3B82F6',
    backgroundColor: '#EBF4FF',
  },
  strategyName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  strategyNameSelected: {
    color: '#3B82F6',
  },
  strategyDescription: {
    fontSize: 12,
    color: '#6B7280',
    lineHeight: 16,
  },
  timeframeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  timeframeCard: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 12,
    minWidth: 80,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  timeframeCardSelected: {
    borderColor: '#3B82F6',
    backgroundColor: '#EBF4FF',
  },
  timeframeName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  timeframeNameSelected: {
    color: '#3B82F6',
  },
  timeframeDescription: {
    fontSize: 10,
    color: '#6B7280',
    marginTop: 2,
    textAlign: 'center',
  },
  runButton: {
    margin: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  runButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  runButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  resultsCount: {
    fontSize: 14,
    color: '#6B7280',
  },
  backtestCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  backtestHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  backtestTitleContainer: {
    flex: 1,
  },
  backtestTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  backtestDateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  backtestDate: {
    fontSize: 12,
    color: '#6B7280',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: 'white',
    fontSize: 10,
    fontWeight: '600',
    marginLeft: 4,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  metricItem: {
    flex: 1,
    minWidth: '30%',
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  backtestActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  actionButtonText: {
    fontSize: 14,
    color: '#3B82F6',
    marginLeft: 6,
    fontWeight: '500',
  },
  runningContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  runningText: {
    fontSize: 14,
    color: '#F59E0B',
    marginLeft: 8,
    fontWeight: '500',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginTop: 12,
    marginBottom: 8,
  },
  emptyDescription: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: 20,
  },
});

export default BacktestingScreen;
