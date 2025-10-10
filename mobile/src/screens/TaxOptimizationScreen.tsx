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
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

interface TaxOptimizationData {
  total_potential_savings: number;
  high_priority_actions: number;
  medium_priority_actions: number;
  low_priority_actions: number;
  next_deadline: string;
  key_opportunities: Array<{
    type: string;
    description: string;
    potential_savings: number;
    priority: string;
    deadline: string;
  }>;
  estimated_annual_savings: number;
  tax_efficiency_score: number;
}

interface TaxLossHarvestingData {
  recommendations: Array<{
    symbol: string;
    action: string;
    shares: number;
    unrealized_loss: number;
    potential_tax_savings: number;
    reason: string;
    priority: string;
  }>;
  total_potential_savings: number;
  tax_bracket: number;
  realized_gains: number;
}

const TaxOptimizationScreen: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'loss-harvesting' | 'capital-gains' | 'rebalancing' | 'bracket-analysis'>('overview');
  const [taxData, setTaxData] = useState<TaxOptimizationData | null>(null);
  const [lossHarvestingData, setLossHarvestingData] = useState<TaxLossHarvestingData | null>(null);

  const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    loadTaxOptimizationData();
  }, []);

  const loadTaxOptimizationData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/tax/optimization-summary`, {
        headers: {
          'Authorization': `Bearer ${await getAuthToken()}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setTaxData(data.summary);
      }
    } catch (error) {
      console.error('Error loading tax optimization data:', error);
      Alert.alert('Error', 'Failed to load tax optimization data');
    } finally {
      setLoading(false);
    }
  };

  const loadLossHarvestingData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/loss-harvesting`, {
        headers: {
          'Authorization': `Bearer ${await getAuthToken()}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setLossHarvestingData(data);
      }
    } catch (error) {
      console.error('Error loading loss harvesting data:', error);
    }
  };

  const getAuthToken = async (): Promise<string> => {
    // Mock token - replace with actual auth logic
    return 'mock-auth-token';
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadTaxOptimizationData();
    if (activeTab === 'loss-harvesting') {
      await loadLossHarvestingData();
    }
    setRefreshing(false);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'HIGH': return '#FF6B6B';
      case 'MEDIUM': return '#FFD93D';
      case 'LOW': return '#6BCF7F';
      default: return '#6BCF7F';
    }
  };

  const renderOverview = () => {
    if (!taxData) return null;

    return (
      <View style={styles.tabContent}>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Tax Optimization Summary</Text>
          <View style={styles.summaryStats}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>${taxData.total_potential_savings.toLocaleString()}</Text>
              <Text style={styles.statLabel}>Potential Savings</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{taxData.tax_efficiency_score}%</Text>
              <Text style={styles.statLabel}>Efficiency Score</Text>
            </View>
          </View>
        </View>

        <View style={styles.opportunitiesCard}>
          <Text style={styles.cardTitle}>Key Opportunities</Text>
          {taxData.key_opportunities.map((opportunity, index) => (
            <View key={index} style={styles.opportunityItem}>
              <View style={styles.opportunityHeader}>
                <Text style={styles.opportunityType}>{opportunity.type.replace(/_/g, ' ')}</Text>
                <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(opportunity.priority) }]}>
                  <Text style={styles.priorityText}>{opportunity.priority}</Text>
                </View>
              </View>
              <Text style={styles.opportunityDescription}>{opportunity.description}</Text>
              <View style={styles.opportunityFooter}>
                <Text style={styles.savingsText}>${opportunity.potential_savings.toLocaleString()} savings</Text>
                <Text style={styles.deadlineText}>Due: {opportunity.deadline}</Text>
              </View>
            </View>
          ))}
        </View>
      </View>
    );
  };

  const renderLossHarvesting = () => {
    if (!lossHarvestingData) {
      loadLossHarvestingData();
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading tax loss harvesting recommendations...</Text>
        </View>
      );
    }

    return (
      <View style={styles.tabContent}>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Tax Loss Harvesting</Text>
          <Text style={styles.summarySubtitle}>
            Total Potential Savings: ${lossHarvestingData.total_potential_savings.toLocaleString()}
          </Text>
          <Text style={styles.summarySubtitle}>
            Tax Bracket: {(lossHarvestingData.tax_bracket * 100).toFixed(0)}%
          </Text>
        </View>

        <View style={styles.recommendationsCard}>
          <Text style={styles.cardTitle}>Recommendations</Text>
          {lossHarvestingData.recommendations.map((rec, index) => (
            <View key={index} style={styles.recommendationItem}>
              <View style={styles.recommendationHeader}>
                <Text style={styles.symbolText}>{rec.symbol}</Text>
                <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(rec.priority) }]}>
                  <Text style={styles.priorityText}>{rec.priority}</Text>
                </View>
              </View>
              <Text style={styles.actionText}>Action: {rec.action} {rec.shares} shares</Text>
              <Text style={styles.reasonText}>{rec.reason}</Text>
              <Text style={styles.savingsText}>
                Potential Tax Savings: ${rec.potential_tax_savings.toLocaleString()}
              </Text>
            </View>
          ))}
        </View>
      </View>
    );
  };

  const renderTabButton = (tab: string, label: string, icon: string) => (
    <TouchableOpacity
      key={tab}
      style={[styles.tabButton, activeTab === tab && styles.activeTabButton]}
      onPress={() => setActiveTab(tab as any)}
    >
      <Ionicons 
        name={icon as any} 
        size={20} 
        color={activeTab === tab ? '#FFFFFF' : '#007AFF'} 
      />
      <Text style={[styles.tabButtonText, activeTab === tab && styles.activeTabButtonText]}>
        {label}
      </Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading tax optimization data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#007AFF', '#0056CC']}
        style={styles.header}
      >
        <Text style={styles.headerTitle}>Tax Optimization</Text>
        <Text style={styles.headerSubtitle}>Premium Features</Text>
      </LinearGradient>

      <View style={styles.tabContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {renderTabButton('overview', 'Overview', 'analytics-outline')}
          {renderTabButton('loss-harvesting', 'Loss Harvesting', 'trending-down-outline')}
          {renderTabButton('capital-gains', 'Capital Gains', 'trending-up-outline')}
          {renderTabButton('rebalancing', 'Rebalancing', 'swap-horizontal-outline')}
          {renderTabButton('bracket-analysis', 'Bracket Analysis', 'bar-chart-outline')}
        </ScrollView>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'loss-harvesting' && renderLossHarvesting()}
        {activeTab === 'capital-gains' && (
          <View style={styles.comingSoonContainer}>
            <Ionicons name="construct-outline" size={64} color="#007AFF" />
            <Text style={styles.comingSoonText}>Capital Gains Optimization</Text>
            <Text style={styles.comingSoonSubtext}>Coming Soon</Text>
          </View>
        )}
        {activeTab === 'rebalancing' && (
          <View style={styles.comingSoonContainer}>
            <Ionicons name="construct-outline" size={64} color="#007AFF" />
            <Text style={styles.comingSoonText}>Tax-Efficient Rebalancing</Text>
            <Text style={styles.comingSoonSubtext}>Coming Soon</Text>
          </View>
        )}
        {activeTab === 'bracket-analysis' && (
          <View style={styles.comingSoonContainer}>
            <Ionicons name="construct-outline" size={64} color="#007AFF" />
            <Text style={styles.comingSoonText}>Tax Bracket Analysis</Text>
            <Text style={styles.comingSoonSubtext}>Coming Soon</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#E3F2FD',
    marginTop: 4,
  },
  tabContainer: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E1E5E9',
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginHorizontal: 4,
    borderRadius: 20,
    backgroundColor: '#F8F9FA',
  },
  activeTabButton: {
    backgroundColor: '#007AFF',
  },
  tabButtonText: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '500',
    color: '#007AFF',
  },
  activeTabButtonText: {
    color: '#FFFFFF',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  tabContent: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
  },
  summaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 8,
  },
  summarySubtitle: {
    fontSize: 16,
    color: '#666666',
    marginBottom: 4,
  },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  statLabel: {
    fontSize: 14,
    color: '#666666',
    marginTop: 4,
  },
  opportunitiesCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 16,
  },
  opportunityItem: {
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    marginBottom: 12,
  },
  opportunityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  opportunityType: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A1A',
    textTransform: 'capitalize',
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  priorityText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  opportunityDescription: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 8,
  },
  opportunityFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  savingsText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  deadlineText: {
    fontSize: 12,
    color: '#999999',
  },
  recommendationsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  recommendationItem: {
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    marginBottom: 12,
  },
  recommendationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  symbolText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A1A',
  },
  actionText: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 4,
  },
  reasonText: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 8,
  },
  comingSoonContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  comingSoonText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginTop: 16,
    textAlign: 'center',
  },
  comingSoonSubtext: {
    fontSize: 16,
    color: '#666666',
    marginTop: 8,
    textAlign: 'center',
  },
});

export default TaxOptimizationScreen;
