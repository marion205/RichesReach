/**
 * Connectivity Test Screen
 * Tests all new endpoints to ensure UI can connect properly
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { API_BASE } from '../config/api';

interface EndpointTest {
  name: string;
  url: string;
  method: 'GET' | 'POST';
  payload?: any;
  status: 'pending' | 'success' | 'error';
  response?: any;
  error?: string;
}

const ConnectivityTestScreen: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [tests, setTests] = useState<EndpointTest[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Define all the new endpoints to test
  const endpointTests: Omit<EndpointTest, 'status' | 'response' | 'error'>[] = [
    // AI Market Insights
    { name: 'AI Market Insights', url: '/api/ai/market-insights/', method: 'GET' },
    { name: 'AI Symbol Insights (AAPL)', url: '/api/ai/symbol-insights/AAPL', method: 'GET' },
    { name: 'AI Portfolio Insights', url: '/api/ai/portfolio-insights/?symbols=AAPL,MSFT,GOOGL', method: 'GET' },
    { name: 'AI Market Regime', url: '/api/ai/market-regime/', method: 'GET' },
    { name: 'AI Sentiment Analysis', url: '/api/ai/sentiment-analysis/', method: 'GET' },
    { name: 'AI Volatility Forecast', url: '/api/ai/volatility-forecast/', method: 'GET' },
    { name: 'AI Trading Opportunities', url: '/api/ai/trading-opportunities/', method: 'GET' },
    { name: 'AI Market Alerts', url: '/api/ai/market-alerts/', method: 'GET' },
    { name: 'AI Sector Analysis', url: '/api/ai/sector-analysis/', method: 'GET' },
    { name: 'AI Risk Metrics', url: '/api/ai/risk-metrics/', method: 'GET' },

    // Advanced Order Management
    { name: 'Place Market Order', url: '/api/orders/place/', method: 'POST', payload: { symbol: 'AAPL', side: 'buy', quantity: 10, order_type: 'market' } },
    { name: 'Place Limit Order', url: '/api/orders/place/', method: 'POST', payload: { symbol: 'MSFT', side: 'buy', quantity: 5, order_type: 'limit', price: 300.0 } },
    { name: 'Place TWAP Order', url: '/api/orders/twap/', method: 'POST', payload: { symbol: 'GOOGL', side: 'buy', quantity: 20, order_type: 'twap', duration_minutes: 30 } },
    { name: 'Place VWAP Order', url: '/api/orders/vwap/', method: 'POST', payload: { symbol: 'AMZN', side: 'buy', quantity: 15, order_type: 'vwap', participation_rate: 0.15 } },
    { name: 'Place Iceberg Order', url: '/api/orders/iceberg/', method: 'POST', payload: { symbol: 'TSLA', side: 'buy', quantity: 500, order_type: 'iceberg', display_size: 100 } },
    { name: 'Place Bracket Order', url: '/api/orders/bracket/', method: 'POST', payload: { symbol: 'NVDA', side: 'buy', quantity: 2, order_type: 'bracket', price: 3300.0, take_profit_price: 3500.0, stop_loss_price: 3200.0 } },
    { name: 'Place OCO Order', url: '/api/orders/oco/', method: 'POST', payload: { symbol: 'META', side: 'buy', quantity: 10, order_type: 'oco', price: 380.0, take_profit_price: 400.0, stop_loss_price: 350.0 } },
    { name: 'Place Trailing Stop', url: '/api/orders/trailing-stop/', method: 'POST', payload: { symbol: 'NFLX', side: 'sell', quantity: 3, order_type: 'trailing_stop', trailing_percent: 0.02, price: 450.0 } },
    { name: 'Get Order Analytics', url: '/api/orders/analytics/', method: 'GET' },
    { name: 'Get Position Summary', url: '/api/orders/positions/', method: 'GET' },
    { name: 'Get Risk Checks', url: '/api/orders/risk-checks/?symbol=AAPL&quantity=10&side=buy', method: 'GET' },
    { name: 'Get Execution Plans', url: '/api/orders/execution-plans/?order_type=twap', method: 'GET' },

    // Education System
    { name: 'Education Progress', url: '/api/education/progress/', method: 'GET' },
    { name: 'Education Analytics', url: '/api/education/analytics/', method: 'GET' },
    { name: 'Education League', url: '/api/education/league/bipoc_wealth_builders', method: 'GET' },
    { name: 'Available Lessons', url: '/api/education/lessons/', method: 'GET' },
    { name: 'Daily Quest', url: '/api/education/daily-quest/', method: 'GET' },
    { name: 'Start Lesson', url: '/api/education/start-lesson/', method: 'POST', payload: { lesson_id: 'lesson_options_basics' } },
    { name: 'Submit Quiz', url: '/api/education/submit-quiz/', method: 'POST', payload: { lesson_id: 'lesson_options_basics', answers: { q1: 'A', q2: 'B' } } },
    { name: 'Start Simulation', url: '/api/education/start-simulation/', method: 'POST', payload: { simulation_type: 'options_trading' } },
    { name: 'Execute Sim Trade', url: '/api/education/execute-sim-trade/', method: 'POST', payload: { simulation_id: 'sim_001', action: 'buy', symbol: 'AAPL', quantity: 10 } },
    { name: 'Claim Streak Freeze', url: '/api/education/claim-streak-freeze/', method: 'POST', payload: { user_id: 'user_001' } },
    { name: 'Process Voice Command', url: '/api/education/process-voice-command/', method: 'POST', payload: { command: 'explain options', user_id: 'user_001' } },

    // Compliance & Analytics
    { name: 'Validate Content', url: '/api/education/compliance/validate-content/', method: 'POST', payload: { content: 'test content', content_type: 'lesson' } },
    { name: 'User Profile', url: '/api/education/compliance/user-profile/user_001', method: 'GET' },
    { name: 'Check Access', url: '/api/education/compliance/check-access/', method: 'POST', payload: { user_id: 'user_001', resource: 'lesson_options_basics' } },
    { name: 'Compliance Report', url: '/api/education/compliance/report/user_001', method: 'GET' },
    { name: 'Analytics Dashboard', url: '/api/education/analytics/dashboard/', method: 'GET' },
    { name: 'User Analytics', url: '/api/education/analytics/user-profile/user_001', method: 'GET' },
    { name: 'Content Analytics', url: '/api/education/analytics/content-analytics/lesson_options_basics', method: 'GET' },
    { name: 'Analytics Trends', url: '/api/education/analytics/trends/', method: 'GET' },

    // Real-Time Notifications
    { name: 'Subscribe Notifications', url: '/api/notifications/subscribe/', method: 'POST', payload: { user_id: 'user_001', topics: ['trading', 'education'] } },
    { name: 'Get Notification Settings', url: '/api/notifications/settings/?user_id=user_001', method: 'GET' },
    { name: 'Update Notification Settings', url: '/api/notifications/settings/', method: 'POST', payload: { user_id: 'user_001', settings: { push: true, email: false } } },
    { name: 'Register Push Token', url: '/api/notifications/push-token/', method: 'POST', payload: { user_id: 'user_001', token: 'test_token' } },
    { name: 'Send Notification', url: '/api/notifications/send/', method: 'POST', payload: { user_id: 'user_001', title: 'Test', message: 'Test notification' } },
    { name: 'Get Notification History', url: '/api/notifications/history/?user_id=user_001&limit=10', method: 'GET' },
    { name: 'Test Push Notification', url: '/api/notifications/test-push/', method: 'POST', payload: { user_id: 'user_001' } },
    { name: 'Clear All Notifications', url: '/api/notifications/clear-all/', method: 'POST', payload: { user_id: 'user_001' } },

    // Advanced Charting
    { name: 'Candlestick Chart', url: '/api/charts/candlestick/AAPL', method: 'GET' },
    { name: 'Volume Chart', url: '/api/charts/volume/AAPL', method: 'GET' },
    { name: 'Line Chart', url: '/api/charts/line/AAPL', method: 'GET' },
    { name: 'Heatmap', url: '/api/charts/heatmap', method: 'GET' },
    { name: 'Correlation Matrix', url: '/api/charts/correlation', method: 'GET' },
    { name: 'Market Depth', url: '/api/charts/market-depth/AAPL', method: 'GET' },
    { name: 'Technical Indicators', url: '/api/charts/indicators/AAPL', method: 'GET' },
    { name: 'Chart Screener', url: '/api/charts/screener', method: 'GET' },

    // Social Trading
    { name: 'Trader Profile', url: '/api/social/trader/trader_001', method: 'GET' },
    { name: 'Leaderboard', url: '/api/social/leaderboard', method: 'GET' },
    { name: 'Social Feed', url: '/api/social/feed/user_001', method: 'GET' },
    { name: 'Follow Trader', url: '/api/social/follow', method: 'POST', payload: { user_id: 'user_001', trader_id: 'trader_001' } },
    { name: 'Unfollow Trader', url: '/api/social/unfollow', method: 'POST', payload: { user_id: 'user_001', trader_id: 'trader_001' } },
    { name: 'Copy Trade', url: '/api/social/copy-trade', method: 'POST', payload: { user_id: 'user_001', trade_id: 'trade_001' } },
    { name: 'Search Traders', url: '/api/social/search-traders', method: 'GET' },
    { name: 'Trade Interactions', url: '/api/social/trade-interactions/trade_001', method: 'GET' },
    { name: 'Like Trade', url: '/api/social/like-trade', method: 'POST', payload: { user_id: 'user_001', trade_id: 'trade_001' } },
    { name: 'Comment Trade', url: '/api/social/comment-trade', method: 'POST', payload: { user_id: 'user_001', trade_id: 'trade_001', comment: 'Great trade!' } },
    { name: 'Trader Stats', url: '/api/social/trader-stats/trader_001', method: 'GET' },
    { name: 'Trending Traders', url: '/api/social/trending-traders', method: 'GET' },
    { name: 'Copy Performance', url: '/api/social/copy-performance/user_001', method: 'GET' },

    // Portfolio Analytics
    { name: 'Portfolio Overview', url: '/api/portfolio/overview/portfolio_001', method: 'GET' },
    { name: 'Portfolio Performance', url: '/api/portfolio/performance/portfolio_001', method: 'GET' },
    { name: 'Portfolio Risk', url: '/api/portfolio/risk/portfolio_001', method: 'GET' },
    { name: 'Portfolio Attribution', url: '/api/portfolio/attribution/portfolio_001', method: 'GET' },
    { name: 'Portfolio Correlation', url: '/api/portfolio/correlation/portfolio_001', method: 'GET' },
    { name: 'Tax Analysis', url: '/api/portfolio/tax-analysis/portfolio_001', method: 'GET' },
    { name: 'Rebalancing Suggestions', url: '/api/portfolio/rebalancing/portfolio_001', method: 'GET' },
    { name: 'Benchmark Comparison', url: '/api/portfolio/benchmark-comparison/portfolio_001', method: 'GET' },
    { name: 'Scenario Analysis', url: '/api/portfolio/scenario-analysis/portfolio_001', method: 'GET' },
    { name: 'Portfolio Optimization', url: '/api/portfolio/optimization/portfolio_001', method: 'GET' },

    // HFT System
    { name: 'HFT Performance', url: '/api/hft/performance/', method: 'GET' },
    { name: 'HFT Positions', url: '/api/hft/positions/', method: 'GET' },
    { name: 'HFT Strategies', url: '/api/hft/strategies/', method: 'GET' },
    { name: 'Execute HFT Strategy', url: '/api/hft/execute-strategy/', method: 'POST', payload: { strategy: 'momentum', symbol: 'AAPL' } },
    { name: 'HFT Place Order', url: '/api/hft/place-order/', method: 'POST', payload: { symbol: 'AAPL', side: 'buy', quantity: 100, order_type: 'market' } },
    { name: 'HFT Live Stream', url: '/api/hft/live-stream/', method: 'GET' },

    // Voice AI Trading
    { name: 'Process Voice Command', url: '/api/voice-trading/process-command/', method: 'POST', payload: { command: 'buy 10 shares of AAPL', user_id: 'user_001' } },
    { name: 'Voice Help Commands', url: '/api/voice-trading/help-commands/', method: 'GET' },
    { name: 'Create Voice Session', url: '/api/voice-trading/create-session/', method: 'POST', payload: { user_id: 'user_001' } },
    { name: 'Voice Session', url: '/api/voice-trading/session/session_001', method: 'GET' },
    { name: 'Parse Voice Command', url: '/api/voice-trading/parse-command/', method: 'POST', payload: { command: 'buy 10 shares of AAPL' } },
    { name: 'Available Symbols', url: '/api/voice-trading/available-symbols/', method: 'GET' },
    { name: 'Command Examples', url: '/api/voice-trading/command-examples/', method: 'GET' },

    // AI Regime Detection
    { name: 'Current Regime', url: '/api/regime-detection/current-regime/', method: 'GET' },
    { name: 'Regime History', url: '/api/regime-detection/history/', method: 'GET' },
    { name: 'Regime Predictions', url: '/api/regime-detection/predictions/', method: 'GET' },

    // Sentiment Analysis
    { name: 'Sentiment Analysis (AAPL)', url: '/api/sentiment-analysis/AAPL', method: 'GET' },
    { name: 'Sentiment Analysis (MSFT)', url: '/api/sentiment-analysis/MSFT', method: 'GET' },
    { name: 'Sentiment Analysis (GOOGL)', url: '/api/sentiment-analysis/GOOGL', method: 'GET' },

    // ML Pick Generation
    { name: 'ML Picks (SAFE)', url: '/api/ml-picks/generate/SAFE', method: 'GET' },
    { name: 'ML Picks (AGGRESSIVE)', url: '/api/ml-picks/generate/AGGRESSIVE', method: 'GET' },
    { name: 'ML Picks (CUSTOM)', url: '/api/ml-picks/generate/CUSTOM', method: 'GET' },

    // Advanced Mobile Features
    { name: 'Gesture Trade', url: '/api/mobile/gesture-trade/', method: 'POST', payload: { gesture: 'swipe_up', symbol: 'AAPL', action: 'buy' } },
    { name: 'Switch Mode', url: '/api/mobile/switch-mode/', method: 'POST', payload: { mode: 'day_trading' } },
    { name: 'Mobile Settings', url: '/api/mobile/settings/', method: 'GET' },
    { name: 'Mobile Performance', url: '/api/mobile/performance/', method: 'GET' },

    // Voice AI
    { name: 'Available Voices', url: '/api/voice-ai/voices/', method: 'GET' },
    { name: 'Synthesize Speech', url: '/api/voice-ai/synthesize/', method: 'POST', payload: { text: 'Hello, this is a test', voice: 'en-US-Standard-A' } },
    { name: 'Voice Settings', url: '/api/voice-ai/settings/', method: 'GET' },
    { name: 'Update Voice Settings', url: '/api/voice-ai/settings/', method: 'POST', payload: { voice: 'en-US-Standard-A', rate: 1.0, pitch: 1.0 } },

    // GraphQL
    { name: 'GraphQL Schema', url: '/graphql/', method: 'POST', payload: { query: '{ __schema { types { name } } }' } },
    { name: 'GraphQL Health', url: '/graphql/', method: 'POST', payload: { query: '{ health { status } }' } },
  ];

  useEffect(() => {
    initializeTests();
  }, []);

  const initializeTests = () => {
    const initialTests = endpointTests.map(test => ({
      ...test,
      status: 'pending' as const,
    }));
    setTests(initialTests);
  };

  const runTest = async (test: EndpointTest) => {
    try {
      const url = `${API_BASE}${test.url}`;
      const options: RequestInit = {
        method: test.method,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (test.method === 'POST' && test.payload) {
        options.body = JSON.stringify(test.payload);
      }

      const response = await fetch(url, options);
      const data = await response.json();

      if (response.ok) {
        return { status: 'success' as const, response: data };
      } else {
        return { status: 'error' as const, error: `HTTP ${response.status}: ${data.message || 'Unknown error'}` };
      }
    } catch (error) {
      return { status: 'error' as const, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    const updatedTests = [...tests];

    for (let i = 0; i < updatedTests.length; i++) {
      updatedTests[i].status = 'pending';
      setTests([...updatedTests]);

      const result = await runTest(updatedTests[i]);
      updatedTests[i] = { ...updatedTests[i], ...result };
      setTests([...updatedTests]);

      // Small delay between tests to avoid overwhelming the server
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    setIsRunning(false);
  };

  const runSingleTest = async (index: number) => {
    const updatedTests = [...tests];
    updatedTests[index].status = 'pending';
    setTests([...updatedTests]);

    const result = await runTest(updatedTests[index]);
    updatedTests[index] = { ...updatedTests[index], ...result };
    setTests([...updatedTests]);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    initializeTests();
    setRefreshing(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <Ionicons name="checkmark-circle" size={20} color="#4CAF50" />;
      case 'error':
        return <Ionicons name="close-circle" size={20} color="#F44336" />;
      case 'pending':
        return <Ionicons name="time" size={20} color="#FF9800" />;
      default:
        return <Ionicons name="help-circle" size={20} color="#9E9E9E" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return '#4CAF50';
      case 'error':
        return '#F44336';
      case 'pending':
        return '#FF9800';
      default:
        return '#9E9E9E';
    }
  };

  const successCount = tests.filter(t => t.status === 'success').length;
  const errorCount = tests.filter(t => t.status === 'error').length;
  const pendingCount = tests.filter(t => t.status === 'pending').length;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Connectivity Test</Text>
        <TouchableOpacity onPress={onClose} style={styles.closeButton}>
          <Ionicons name="close" size={24} color="#666" />
        </TouchableOpacity>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={[styles.statNumber, { color: '#4CAF50' }]}>{successCount}</Text>
          <Text style={styles.statLabel}>Success</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statNumber, { color: '#F44336' }]}>{errorCount}</Text>
          <Text style={styles.statLabel}>Errors</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statNumber, { color: '#FF9800' }]}>{pendingCount}</Text>
          <Text style={styles.statLabel}>Pending</Text>
        </View>
      </View>

      <View style={styles.actionsContainer}>
        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={runAllTests}
          disabled={isRunning}
        >
          {isRunning ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Run All Tests</Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={onRefresh}
          disabled={refreshing}
        >
          <Text style={styles.secondaryButtonText}>Reset</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {tests.map((test, index) => (
          <TouchableOpacity
            key={index}
            style={styles.testItem}
            onPress={() => runSingleTest(index)}
          >
            <View style={styles.testHeader}>
              {getStatusIcon(test.status)}
              <Text style={styles.testName}>{test.name}</Text>
              <Text style={[styles.testMethod, { color: getStatusColor(test.status) }]}>
                {test.method}
              </Text>
            </View>
            <Text style={styles.testUrl}>{test.url}</Text>
            {test.error && (
              <Text style={styles.errorText}>Error: {test.error}</Text>
            )}
            {test.response && (
              <Text style={styles.responseText}>
                Response: {JSON.stringify(test.response).substring(0, 100)}...
              </Text>
            )}
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  closeButton: {
    padding: 8,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  actionsContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  button: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: '#f0f0f0',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  secondaryButtonText: {
    color: '#333',
    fontWeight: 'bold',
  },
  scrollView: {
    flex: 1,
  },
  testItem: {
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  testHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  testName: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginLeft: 8,
  },
  testMethod: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  testUrl: {
    fontSize: 12,
    color: '#666',
    fontFamily: 'monospace',
  },
  errorText: {
    fontSize: 12,
    color: '#F44336',
    marginTop: 4,
  },
  responseText: {
    fontSize: 12,
    color: '#4CAF50',
    marginTop: 4,
    fontFamily: 'monospace',
  },
});

export default ConnectivityTestScreen;
