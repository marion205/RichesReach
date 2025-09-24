import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { mockSignals, mockBacktestStrategies, mockBacktestResults, mockDayTradingPicks, mockRiskCalculation } from '../mockData/swingTradingMockData';

interface SwingTradingTestScreenProps {
  navigateTo?: (screen: string) => void;
}

const SwingTradingTestScreen: React.FC<SwingTradingTestScreenProps> = ({ navigateTo }) => {
  const [activeTab, setActiveTab] = useState<'signals' | 'backtest' | 'daytrading' | 'risk'>('signals');

  const renderSignals = () => (
    <ScrollView style={styles.tabContent}>
      <Text style={styles.sectionTitle}>📊 Live Trading Signals</Text>
      {mockSignals.map((signal) => (
        <View key={signal.id} style={styles.signalCard}>
          <View style={styles.signalHeader}>
            <Text style={styles.symbol}>{signal.symbol}</Text>
            <Text style={[styles.score, { color: signal.mlScore > 0.7 ? '#22C55E' : '#F59E0B' }]}>
              {(signal.mlScore * 100).toFixed(0)}%
            </Text>
          </View>
          <Text style={styles.signalType}>{signal.signalType.replace(/_/g, ' ').toUpperCase()}</Text>
          <Text style={styles.thesis}>{signal.thesis}</Text>
          <View style={styles.signalMetrics}>
            <Text style={styles.metric}>Entry: ${signal.entryPrice}</Text>
            <Text style={styles.metric}>Stop: ${signal.stopPrice}</Text>
            <Text style={styles.metric}>Target: ${signal.targetPrice}</Text>
            <Text style={styles.metric}>R:R: {signal.riskRewardRatio}</Text>
          </View>
          <View style={styles.signalFooter}>
            <Text style={styles.author}>by {signal.createdBy.name}</Text>
            <Text style={styles.likes}>❤️ {signal.userLikeCount}</Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );

  const renderBacktest = () => (
    <ScrollView style={styles.tabContent}>
      <Text style={styles.sectionTitle}>📈 Backtesting Results</Text>
      {mockBacktestStrategies.map((strategy) => (
        <View key={strategy.id} style={styles.strategyCard}>
          <Text style={styles.strategyName}>{strategy.name}</Text>
          <Text style={styles.strategyDescription}>{strategy.description}</Text>
          <View style={styles.strategyMetrics}>
            <Text style={styles.metric}>Return: {(strategy.totalReturn * 100).toFixed(1)}%</Text>
            <Text style={styles.metric}>Win Rate: {(strategy.winRate * 100).toFixed(1)}%</Text>
            <Text style={styles.metric}>Sharpe: {strategy.sharpeRatio.toFixed(2)}</Text>
            <Text style={styles.metric}>Trades: {strategy.totalTrades}</Text>
          </View>
          <View style={styles.strategyFooter}>
            <Text style={styles.author}>by {strategy.user.name}</Text>
            <Text style={styles.likes}>❤️ {strategy.likesCount}</Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );

  const renderDayTrading = () => (
    <ScrollView style={styles.tabContent}>
      <Text style={styles.sectionTitle}>⚡ Day Trading Picks</Text>
      <View style={styles.modeInfo}>
        <Text style={styles.modeText}>Mode: {mockDayTradingPicks.mode}</Text>
        <Text style={styles.modeText}>Universe: {mockDayTradingPicks.universe_size} stocks</Text>
        <Text style={styles.modeText}>Threshold: {mockDayTradingPicks.quality_threshold}</Text>
      </View>
      {mockDayTradingPicks.picks.map((pick, index) => (
        <View key={index} style={styles.pickCard}>
          <View style={styles.pickHeader}>
            <Text style={styles.symbol}>{pick.symbol}</Text>
            <Text style={[styles.side, { color: pick.side === 'LONG' ? '#22C55E' : '#EF4444' }]}>
              {pick.side}
            </Text>
            <Text style={styles.score}>Score: {pick.score.toFixed(1)}</Text>
          </View>
          <Text style={styles.notes}>{pick.notes}</Text>
          <View style={styles.pickMetrics}>
            <Text style={styles.metric}>Stop: ${pick.risk.stop}</Text>
            <Text style={styles.metric}>Target: ${pick.risk.targets[0]}</Text>
            <Text style={styles.metric}>Size: {pick.risk.size_shares} shares</Text>
            <Text style={styles.metric}>Time Stop: {pick.risk.time_stop_min}m</Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );

  const renderRisk = () => (
    <ScrollView style={styles.tabContent}>
      <Text style={styles.sectionTitle}>🛡️ Risk Management</Text>
      <View style={styles.riskCard}>
        <Text style={styles.riskTitle}>Position Sizing Calculator</Text>
        <View style={styles.riskMetrics}>
          <Text style={styles.metric}>Account Equity: ${mockRiskCalculation.accountEquity.toLocaleString()}</Text>
          <Text style={styles.metric}>Risk per Trade: {(mockRiskCalculation.riskPerTrade * 100).toFixed(1)}%</Text>
          <Text style={styles.metric}>Position Size: {mockRiskCalculation.positionSize} shares</Text>
          <Text style={styles.metric}>Dollar Risk: ${mockRiskCalculation.dollarRisk}</Text>
          <Text style={styles.metric}>Position Value: ${mockRiskCalculation.positionValue.toLocaleString()}</Text>
          <Text style={styles.metric}>Risk/Reward: {mockRiskCalculation.riskRewardRatio}</Text>
        </View>
        <TouchableOpacity 
          style={styles.calculateButton}
          onPress={() => Alert.alert('Risk Calculated', 'Position sizing complete!')}
        >
          <Text style={styles.buttonText}>Calculate Position Size</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigateTo?.('home')}
        >
          <Icon name="arrow-left" size={24} color="#6B7280" />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={styles.title}>Swing Trading Test</Text>
        </View>
        <View style={styles.headerSpacer} />
      </View>
      
      <View style={styles.tabBar}>
        {[
          { key: 'signals', label: 'Signals' },
          { key: 'backtest', label: 'Backtest' },
          { key: 'daytrading', label: 'Day Trading' },
          { key: 'risk', label: 'Risk' }
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.activeTab]}
            onPress={() => setActiveTab(tab.key as any)}
          >
            <Text style={[styles.tabText, activeTab === tab.key && styles.activeTabText]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {activeTab === 'signals' && renderSignals()}
      {activeTab === 'backtest' && renderBacktest()}
      {activeTab === 'daytrading' && renderDayTrading()}
      {activeTab === 'risk' && renderRisk()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  headerTitleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  headerSpacer: {
    width: 40, // Same width as back button to center the title
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#3B82F6',
  },
  tabText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#3B82F6',
    fontWeight: '600',
  },
  tabContent: {
    flex: 1,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
  },
  signalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  symbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  score: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  signalType: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  thesis: {
    fontSize: 14,
    color: '#374151',
    marginBottom: 12,
    lineHeight: 20,
  },
  signalMetrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  metric: {
    fontSize: 12,
    color: '#6B7280',
    marginRight: 16,
    marginBottom: 4,
  },
  signalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  author: {
    fontSize: 12,
    color: '#6B7280',
  },
  likes: {
    fontSize: 12,
    color: '#6B7280',
  },
  strategyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  strategyName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  strategyDescription: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 12,
    lineHeight: 20,
  },
  strategyMetrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  strategyFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modeInfo: {
    backgroundColor: '#EFF6FF',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  modeText: {
    fontSize: 14,
    color: '#1E40AF',
    marginBottom: 4,
  },
  pickCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  pickHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  side: {
    fontSize: 12,
    fontWeight: 'bold',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    backgroundColor: '#F3F4F6',
  },
  notes: {
    fontSize: 14,
    color: '#374151',
    marginBottom: 12,
    lineHeight: 20,
  },
  pickMetrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  riskCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  riskTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
  },
  riskMetrics: {
    marginBottom: 16,
  },
  calculateButton: {
    backgroundColor: '#3B82F6',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default SwingTradingTestScreen;
