import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';
import taxOptimizationService from '../services/taxOptimizationService';

interface TaxOptimizationData {
  summary?: any;
  lossHarvesting?: any;
  capitalGains?: any;
  rebalancing?: any;
  bracketAnalysis?: any;
}

const TaxOptimizationScreen: React.FC = () => {
  const { user, token } = useAuth();
  const [data, setData] = useState<TaxOptimizationData>({});
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');

  const loadData = async () => {
    if (!token) {
      Alert.alert('Authentication Required', 'Please log in to access tax optimization features.');
      return;
    }

    setLoading(true);
    try {
      const [summary, lossHarvesting, capitalGains, rebalancing, bracketAnalysis] = await Promise.allSettled([
        taxOptimizationService.getOptimizationSummary(token),
        taxOptimizationService.getTaxLossHarvesting(token),
        taxOptimizationService.getCapitalGainsOptimization(token),
        taxOptimizationService.getTaxEfficientRebalancing(token),
        taxOptimizationService.getTaxBracketAnalysis(token),
      ]);

      setData({
        summary: summary.status === 'fulfilled' ? summary.value : null,
        lossHarvesting: lossHarvesting.status === 'fulfilled' ? lossHarvesting.value : null,
        capitalGains: capitalGains.status === 'fulfilled' ? capitalGains.value : null,
        rebalancing: rebalancing.status === 'fulfilled' ? rebalancing.value : null,
        bracketAnalysis: bracketAnalysis.status === 'fulfilled' ? bracketAnalysis.value : null,
      });
    } catch (error) {
      console.error('Error loading tax optimization data:', error);
      Alert.alert('Error', 'Failed to load tax optimization data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const renderSummaryTab = () => (
    <View style={styles.tabContent}>
      <Text style={styles.sectionTitle}>Tax Optimization Summary</Text>
      {data.summary ? (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryText}>
            {JSON.stringify(data.summary, null, 2)}
          </Text>
        </View>
      ) : (
        <Text style={styles.noDataText}>No summary data available</Text>
      )}
    </View>
  );

  const renderLossHarvestingTab = () => (
    <View style={styles.tabContent}>
      <Text style={styles.sectionTitle}>Tax Loss Harvesting</Text>
      {data.lossHarvesting ? (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryText}>
            {JSON.stringify(data.lossHarvesting, null, 2)}
          </Text>
        </View>
      ) : (
        <Text style={styles.noDataText}>No loss harvesting data available</Text>
      )}
    </View>
  );

  const renderCapitalGainsTab = () => (
    <View style={styles.tabContent}>
      <Text style={styles.sectionTitle}>Capital Gains Optimization</Text>
      {data.capitalGains ? (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryText}>
            {JSON.stringify(data.capitalGains, null, 2)}
          </Text>
        </View>
      ) : (
        <Text style={styles.noDataText}>No capital gains data available</Text>
      )}
    </View>
  );

  const renderRebalancingTab = () => (
    <View style={styles.tabContent}>
      <Text style={styles.sectionTitle}>Tax Efficient Rebalancing</Text>
      {data.rebalancing ? (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryText}>
            {JSON.stringify(data.rebalancing, null, 2)}
          </Text>
        </View>
      ) : (
        <Text style={styles.noDataText}>No rebalancing data available</Text>
      )}
    </View>
  );

  const renderBracketAnalysisTab = () => (
    <View style={styles.tabContent}>
      <Text style={styles.sectionTitle}>Tax Bracket Analysis</Text>
      {data.bracketAnalysis ? (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryText}>
            {JSON.stringify(data.bracketAnalysis, null, 2)}
          </Text>
        </View>
      ) : (
        <Text style={styles.noDataText}>No bracket analysis data available</Text>
      )}
    </View>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'summary':
        return renderSummaryTab();
      case 'loss-harvesting':
        return renderLossHarvestingTab();
      case 'capital-gains':
        return renderCapitalGainsTab();
      case 'rebalancing':
        return renderRebalancingTab();
      case 'bracket-analysis':
        return renderBracketAnalysisTab();
      default:
        return renderSummaryTab();
    }
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading tax optimization data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Tax Optimization</Text>
      <Text style={styles.subtitle}>Premium Features</Text>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.tabContainer}
        contentContainerStyle={styles.tabContentContainer}
      >
        {[
          { key: 'summary', label: 'Summary' },
          { key: 'loss-harvesting', label: 'Loss Harvesting' },
          { key: 'capital-gains', label: 'Capital Gains' },
          { key: 'rebalancing', label: 'Rebalancing' },
          { key: 'bracket-analysis', label: 'Bracket Analysis' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[
              styles.tab,
              activeTab === tab.key && styles.activeTab,
            ]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === tab.key && styles.activeTabText,
              ]}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {renderTabContent()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  tabContainer: {
    marginBottom: 20,
  },
  tabContentContainer: {
    paddingHorizontal: 16,
  },
  tab: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    marginRight: 12,
    borderRadius: 20,
    backgroundColor: '#e0e0e0',
  },
  activeTab: {
    backgroundColor: '#007AFF',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  activeTabText: {
    color: '#fff',
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
  },
  tabContent: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  summaryCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  summaryText: {
    fontSize: 14,
    color: '#333',
    fontFamily: 'monospace',
  },
  noDataText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 40,
  },
});

export default TaxOptimizationScreen;