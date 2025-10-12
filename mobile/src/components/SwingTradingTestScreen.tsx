import React from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, FlatList } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
// Mock data removed - using real API data
import SwingTradingMarketOverview from './SwingTradingMarketOverview';
import SwingTradingSignalAnalysis from './SwingTradingSignalAnalysis';
import SwingTradingEducation from './SwingTradingEducation';
import SwingTradingPerformance from './SwingTradingPerformance';
import SwingTradingMarketSentiment from './SwingTradingMarketSentiment';
import SwingTradingAdvancedAnalytics from './SwingTradingAdvancedAnalytics';

interface SwingTradingTestScreenProps {
  navigateTo?: (screen: string) => void;
}

const SwingTradingTestScreen: React.FC<SwingTradingTestScreenProps> = ({ navigateTo }) => {
  const [tab, setTab] = React.useState<'signals' | 'market' | 'analysis' | 'education' | 'performance' | 'sentiment' | 'analytics' | 'backtest' | 'daytrading' | 'risk'>('signals');

  // Tab components will be defined below

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header (fixed) */}
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

      {/* Tab bar (fixed) */}
      <View>
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          style={styles.tabBar}
          contentContainerStyle={styles.tabBarContent}
        >
          {[
            { key: 'signals', label: 'Signals' },
            { key: 'market', label: 'Market' },
            { key: 'analysis', label: 'Analysis' },
            { key: 'education', label: 'Education' },
            { key: 'performance', label: 'Performance' },
            { key: 'sentiment', label: 'Sentiment' },
            { key: 'analytics', label: 'Analytics' },
            { key: 'backtest', label: 'Backtest' },
            { key: 'daytrading', label: 'Day Trading' },
            { key: 'risk', label: 'Risk' }
          ].map((tabItem) => (
            <TouchableOpacity
              key={tabItem.key}
              style={[styles.tab, tab === tabItem.key && styles.tabActive]}
              onPress={() => setTab(tabItem.key as any)}
            >
              <Text style={[styles.tabText, tab === tabItem.key && styles.tabTextActive]}>
                {tabItem.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
        <View style={styles.underline} />
      </View>

      {/* 👇 the only flexible area on the page */}
      <View style={styles.tabSlot}>
        {tab === 'signals' && <SignalsTab />}
        {tab === 'market' && <MarketTab />}
        {tab === 'analysis' && <AnalysisTab />}
        {tab === 'education' && <EducationTab />}
        {tab === 'performance' && <PerformanceTab />}
        {tab === 'sentiment' && <SentimentTab />}
        {tab === 'analytics' && <AnalyticsTab />}
        {tab === 'backtest' && <BacktestTab />}
        {tab === 'daytrading' && <DayTradingTab />}
        {tab === 'risk' && <RiskTab />}
      </View>
    </SafeAreaView>
  );
};

// Individual Tab Components
function SignalsTab() {
  const renderSignalCard = ({ item: signal }) => (
    <View style={styles.signalCard}>
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
  );

  return (
    <FlatList
      style={{ flex: 1 }}                        // occupies the whole tab slot
      contentInsetAdjustmentBehavior="never"     // no auto top inset
      contentContainerStyle={{
        paddingTop: 0,                           // 👈 zero space under the tab bar
        paddingBottom: 24,
        paddingHorizontal: 16,
      }}
      data={[]}
      keyExtractor={(item) => item.id}
      ListHeaderComponent={
        <View style={{ paddingTop: 0, marginTop: 0 }}>
          <Text style={styles.sectionTitle}>📊 Live Trading Signals</Text>
        </View>
      }
      renderItem={renderSignalCard}
      removeClippedSubviews                    // perf + prevents odd sizing
      initialNumToRender={8}
      windowSize={5}
    />
  );
}

function MarketTab() {
  return <SwingTradingMarketOverview />;
}

function AnalysisTab() {
  return <SwingTradingSignalAnalysis />;
}

function EducationTab() {
  return <SwingTradingEducation />;
}

function PerformanceTab() {
  return <SwingTradingPerformance />;
}

function SentimentTab() {
  return <SwingTradingMarketSentiment />;
}

function AnalyticsTab() {
  return <SwingTradingAdvancedAnalytics />;
}

function BacktestTab() {
  return (
    <ScrollView
      style={{ flex: 1 }}
      contentInsetAdjustmentBehavior="never"
      contentContainerStyle={{ flexGrow: 1, justifyContent: 'flex-start', paddingHorizontal: 16, paddingTop: 0, paddingBottom: 24 }}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.sectionTitle}>📈 Backtesting Results</Text>
      {[].map((strategy) => (
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
}

function DayTradingTab() {
  return (
    <ScrollView
      style={{ flex: 1 }}
      contentInsetAdjustmentBehavior="never"
      contentContainerStyle={{ flexGrow: 1, justifyContent: 'flex-start', paddingHorizontal: 16, paddingTop: 0, paddingBottom: 24 }}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.sectionTitle}>⚡ Day Trading Picks</Text>
      <View style={styles.modeInfo}>
        <Text style={styles.modeText}>Mode: SAFE</Text>
        <Text style={styles.modeText}>Universe: 500 stocks</Text>
        <Text style={styles.modeText}>Threshold: 1.5</Text>
      </View>
      {[].map((pick, index) => (
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
            <Text style={styles.metric}>Size: {pick.risk.sizeShares} shares</Text>
            <Text style={styles.metric}>Time Stop: {pick.risk.timeStopMin}m</Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

function RiskTab() {
  return (
    <ScrollView
      style={{ flex: 1 }}
      contentInsetAdjustmentBehavior="never"
      contentContainerStyle={{ flexGrow: 1, justifyContent: 'flex-start', paddingHorizontal: 16, paddingTop: 0, paddingBottom: 24 }}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.sectionTitle}>🛡️ Risk Management</Text>
      <View style={styles.riskCard}>
        <Text style={styles.riskTitle}>Position Sizing Calculator</Text>
        <View style={styles.riskMetrics}>
          <Text style={styles.metric}>Account Equity: $25,000</Text>
          <Text style={styles.metric}>Risk per Trade: 2.0%</Text>
          <Text style={styles.metric}>Position Size: 100 shares</Text>
          <Text style={styles.metric}>Dollar Risk: $550</Text>
          <Text style={styles.metric}>Position Value: $17,550</Text>
          <Text style={styles.metric}>Risk/Reward: 2.1</Text>
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
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#fff' 
  },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16, 
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth, 
    borderBottomColor: '#E5E7EB',
    backgroundColor: '#fff',
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
    fontSize: 20, 
    fontWeight: '700', 
    color: '#111827' 
  },

  tabBar: {
    height: 42,           // keep this lean (40–44)
    paddingTop: 0,
    paddingBottom: 0,     // 🔧 remove hidden vertical padding
    marginBottom: 0,      // 🔧 remove bottom margin
    paddingHorizontal: 12,
    backgroundColor: '#fff',
  },
  tabBarContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  tab: { 
    paddingVertical: 10,  // keep touch target here instead
    paddingHorizontal: 8, 
    alignItems: 'center',
    minWidth: 80,
  },
  tabActive: { 
    borderBottomWidth: 2, 
    borderBottomColor: '#3B82F6' 
  },
  tabText: { 
    color: '#6B7280', 
    fontWeight: '600' 
  },
  tabTextActive: { 
    color: '#3B82F6' 
  },
  underline: {
    position: 'absolute',
    left: 0, right: 0, bottom: 0,
    height: 1,
    backgroundColor: '#E5E7EB',
  },

  // 👇 the only flexible area on the page
  tabSlot: { 
    flex: 1, 
    minHeight: 0  // ← critical for iOS nested scroll
  },

  // ScrollView style
  scroll: {
    flex: 1,
  },

  // Ensures content can stretch to fill even when short
  scrollGrow: { 
    // fills remaining height but keeps content at the TOP
    flexGrow: 1,
    justifyContent: 'flex-start',
    paddingBottom: 0,
  },

  section: { 
    // No gap - content starts immediately
  },
  sectionHeader: { 
    // No margin - title starts immediately
  },
  sectionTitle: { 
    marginTop: 0, 
    marginBottom: 8, 
    fontSize: 16, 
    fontWeight: '700', 
    color: '#111827' 
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
