import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Feather from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

interface AnalyticsScreenProps {
  navigateTo: (screen: string) => void;
}

export default function AnalyticsScreen({ navigateTo }: AnalyticsScreenProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('1M');

  // Mock analytics data
  const mockAnalytics = {
    portfolioPerformance: {
      totalReturn: 12.5,
      totalReturnPercent: 8.2,
      sharpeRatio: 1.4,
      maxDrawdown: -5.2,
      volatility: 15.8,
    },
    sectorAllocation: [
      { sector: 'Technology', percentage: 35, value: 12500, color: '#007AFF' },
      { sector: 'Healthcare', percentage: 20, value: 7143, color: '#34C759' },
      { sector: 'Financials', percentage: 15, value: 5357, color: '#FF9500' },
      { sector: 'Consumer', percentage: 12, value: 4286, color: '#FF3B30' },
      { sector: 'Energy', percentage: 10, value: 3571, color: '#FFCC00' },
      { sector: 'Other', percentage: 8, value: 2857, color: '#8E8E93' },
    ],
    topPerformers: [
      { symbol: 'AAPL', name: 'Apple Inc.', return: 15.2, value: 5000 },
      { symbol: 'MSFT', name: 'Microsoft Corp.', return: 12.8, value: 3500 },
      { symbol: 'GOOGL', name: 'Alphabet Inc.', return: 8.5, value: 2800 },
      { symbol: 'TSLA', name: 'Tesla Inc.', return: 6.2, value: 2200 },
    ],
    riskMetrics: {
      beta: 1.1,
      alpha: 2.3,
      rSquared: 0.85,
      trackingError: 3.2,
    },
    monthlyReturns: [
      { month: 'Jan', return: 2.1 },
      { month: 'Feb', return: -1.5 },
      { month: 'Mar', return: 4.2 },
      { month: 'Apr', return: 3.8 },
      { month: 'May', return: -0.8 },
      { month: 'Jun', return: 5.1 },
    ],
  };

  const onRefresh = () => {
    setRefreshing(true);
    // Simulate API call
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  };

  const periods = ['1W', '1M', '3M', '6M', '1Y', 'ALL'];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Portfolio Analytics</Text>
          <Text style={styles.subtitle}>Detailed performance insights</Text>
        </View>

        {/* Period Selector */}
        <View style={styles.periodSelector}>
          {periods.map((period) => (
            <TouchableOpacity
              key={period}
              style={[
                styles.periodButton,
                selectedPeriod === period && styles.activePeriodButton,
              ]}
              onPress={() => setSelectedPeriod(period)}
            >
              <Text
                style={[
                  styles.periodText,
                  selectedPeriod === period && styles.activePeriodText,
                ]}
              >
                {period}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Performance Overview */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Performance Overview</Text>
          <View style={styles.performanceGrid}>
            <View style={styles.performanceCard}>
              <Text style={styles.performanceLabel}>Total Return</Text>
              <Text style={styles.performanceValue}>
                ${mockAnalytics.portfolioPerformance.totalReturn.toFixed(1)}K
              </Text>
              <Text style={styles.performancePercent}>
                +{mockAnalytics.portfolioPerformance.totalReturnPercent}%
              </Text>
            </View>
            <View style={styles.performanceCard}>
              <Text style={styles.performanceLabel}>Sharpe Ratio</Text>
              <Text style={styles.performanceValue}>
                {mockAnalytics.portfolioPerformance.sharpeRatio}
              </Text>
              <Text style={styles.performanceSubtext}>Risk-adjusted return</Text>
            </View>
            <View style={styles.performanceCard}>
              <Text style={styles.performanceLabel}>Max Drawdown</Text>
              <Text style={styles.performanceValue}>
                {mockAnalytics.portfolioPerformance.maxDrawdown}%
              </Text>
              <Text style={styles.performanceSubtext}>Worst decline</Text>
            </View>
            <View style={styles.performanceCard}>
              <Text style={styles.performanceLabel}>Volatility</Text>
              <Text style={styles.performanceValue}>
                {mockAnalytics.portfolioPerformance.volatility}%
              </Text>
              <Text style={styles.performanceSubtext}>Annualized</Text>
            </View>
          </View>
        </View>

        {/* Sector Allocation */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Sector Allocation</Text>
          <View style={styles.sectorContainer}>
            {mockAnalytics.sectorAllocation.map((sector, index) => (
              <View key={index} style={styles.sectorItem}>
                <View style={styles.sectorHeader}>
                  <View
                    style={[styles.sectorColor, { backgroundColor: sector.color }]}
                  />
                  <Text style={styles.sectorName}>{sector.sector}</Text>
                  <Text style={styles.sectorPercentage}>{sector.percentage}%</Text>
                </View>
                <View style={styles.sectorBar}>
                  <View
                    style={[
                      styles.sectorBarFill,
                      {
                        width: `${sector.percentage}%`,
                        backgroundColor: sector.color,
                      },
                    ]}
                  />
                </View>
                <Text style={styles.sectorValue}>${sector.value.toLocaleString()}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Top Performers */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Top Performers</Text>
          {mockAnalytics.topPerformers.map((stock, index) => (
            <View key={index} style={styles.performerItem}>
              <View style={styles.performerInfo}>
                <Text style={styles.performerSymbol}>{stock.symbol}</Text>
                <Text style={styles.performerName}>{stock.name}</Text>
              </View>
              <View style={styles.performerStats}>
                <Text style={styles.performerReturn}>+{stock.return}%</Text>
                <Text style={styles.performerValue}>${stock.value.toLocaleString()}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Risk Metrics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Risk Metrics</Text>
          <View style={styles.riskGrid}>
            <View style={styles.riskCard}>
              <Text style={styles.riskLabel}>Beta</Text>
              <Text style={styles.riskValue}>{mockAnalytics.riskMetrics.beta}</Text>
            </View>
            <View style={styles.riskCard}>
              <Text style={styles.riskLabel}>Alpha</Text>
              <Text style={styles.riskValue}>{mockAnalytics.riskMetrics.alpha}%</Text>
            </View>
            <View style={styles.riskCard}>
              <Text style={styles.riskLabel}>R²</Text>
              <Text style={styles.riskValue}>{mockAnalytics.riskMetrics.rSquared}</Text>
            </View>
            <View style={styles.riskCard}>
              <Text style={styles.riskLabel}>Tracking Error</Text>
              <Text style={styles.riskValue}>{mockAnalytics.riskMetrics.trackingError}%</Text>
            </View>
          </View>
        </View>

        {/* Monthly Returns */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Monthly Returns</Text>
          <View style={styles.monthlyContainer}>
            {mockAnalytics.monthlyReturns.map((month, index) => (
              <View key={index} style={styles.monthlyItem}>
                <Text style={styles.monthlyLabel}>{month.month}</Text>
                <Text
                  style={[
                    styles.monthlyReturn,
                    { color: month.return >= 0 ? '#34C759' : '#FF3B30' },
                  ]}
                >
                  {month.return >= 0 ? '+' : ''}{month.return}%
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionSection}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigateTo('portfolio')}
          >
            <Feather name="bar-chart-2" size={20} color="#007AFF" />
            <Text style={styles.actionButtonText}>View Portfolio</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigateTo('trading')}
          >
            <Feather name="trending-up" size={20} color="#007AFF" />
            <Text style={styles.actionButtonText}>Trading Insights</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 20,
    paddingBottom: 10,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E93',
  },
  periodSelector: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  periodButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 20,
    backgroundColor: '#E5E5EA',
  },
  activePeriodButton: {
    backgroundColor: '#007AFF',
  },
  periodText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#8E8E93',
  },
  activePeriodText: {
    color: '#FFFFFF',
  },
  section: {
    marginBottom: 24,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  performanceGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  performanceCard: {
    width: (width - 60) / 2,
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  performanceLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  performanceValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  performancePercent: {
    fontSize: 14,
    color: '#34C759',
    fontWeight: '500',
  },
  performanceSubtext: {
    fontSize: 12,
    color: '#8E8E93',
  },
  sectorContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectorItem: {
    marginBottom: 16,
  },
  sectorHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  sectorColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  sectorName: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
    color: '#1C1C1E',
  },
  sectorPercentage: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  sectorBar: {
    height: 6,
    backgroundColor: '#E5E5EA',
    borderRadius: 3,
    marginBottom: 4,
  },
  sectorBarFill: {
    height: 6,
    borderRadius: 3,
  },
  sectorValue: {
    fontSize: 14,
    color: '#8E8E93',
  },
  performerItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  performerInfo: {
    flex: 1,
  },
  performerSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  performerName: {
    fontSize: 14,
    color: '#8E8E93',
  },
  performerStats: {
    alignItems: 'flex-end',
  },
  performerReturn: {
    fontSize: 16,
    fontWeight: '600',
    color: '#34C759',
    marginBottom: 2,
  },
  performerValue: {
    fontSize: 14,
    color: '#8E8E93',
  },
  riskGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  riskCard: {
    width: (width - 60) / 2,
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  riskLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 8,
  },
  riskValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1C1C1E',
  },
  monthlyContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  monthlyItem: {
    alignItems: 'center',
  },
  monthlyLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  monthlyReturn: {
    fontSize: 14,
    fontWeight: '600',
  },
  actionSection: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingBottom: 20,
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#007AFF',
    marginLeft: 8,
  },
});
