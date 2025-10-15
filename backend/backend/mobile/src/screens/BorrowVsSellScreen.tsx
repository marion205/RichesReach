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

const BorrowVsSellScreen: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    if (!token) {
      Alert.alert('Authentication Required', 'Please log in to access this feature.');
      return;
    }

    setLoading(true);
    try {
      const response = await taxOptimizationService.getBorrowVsSellAdvisor(token);
      setData(response);
    } catch (error) {
      console.error('Error loading borrow vs sell data:', error);
      Alert.alert('Error', 'Failed to load borrow vs sell analysis. Please try again.');
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

  const renderAnalysis = () => {
    if (!data) return null;

    return (
      <View style={styles.analysisContainer}>
        <Text style={styles.analysisTitle}>Borrow vs Sell Analysis</Text>
        
        <View style={styles.comparisonCard}>
          <Text style={styles.comparisonTitle}>Recommendation</Text>
          <Text style={styles.recommendation}>
            {data.recommendation || 'Analysis in progress...'}
          </Text>
        </View>

        {data.sell_analysis && (
          <View style={styles.analysisCard}>
            <Text style={styles.cardTitle}>Selling Analysis</Text>
            <Text style={styles.analysisText}>
              Capital Gains Tax: ${data.sell_analysis.capital_gains_tax?.toFixed(2) || 'N/A'}
            </Text>
            <Text style={styles.analysisText}>
              Net Proceeds: ${data.sell_analysis.net_proceeds?.toFixed(2) || 'N/A'}
            </Text>
            <Text style={styles.analysisText}>
              Tax Rate: {(data.sell_analysis.tax_rate * 100)?.toFixed(1) || 'N/A'}%
            </Text>
          </View>
        )}

        {data.borrow_analysis && (
          <View style={styles.analysisCard}>
            <Text style={styles.cardTitle}>Borrowing Analysis</Text>
            <Text style={styles.analysisText}>
              Interest Rate: {(data.borrow_analysis.interest_rate * 100)?.toFixed(2) || 'N/A'}%
            </Text>
            <Text style={styles.analysisText}>
              Monthly Payment: ${data.borrow_analysis.monthly_payment?.toFixed(2) || 'N/A'}
            </Text>
            <Text style={styles.analysisText}>
              Total Interest (1 year): ${data.borrow_analysis.total_interest_1yr?.toFixed(2) || 'N/A'}
            </Text>
            <Text style={styles.analysisText}>
              LTV Ratio: {(data.borrow_analysis.ltv_ratio * 100)?.toFixed(1) || 'N/A'}%
            </Text>
          </View>
        )}

        {data.comparison && (
          <View style={styles.comparisonCard}>
            <Text style={styles.cardTitle}>Cost Comparison</Text>
            <Text style={styles.analysisText}>
              Sell Cost (1 year): ${data.comparison.sell_cost_1yr?.toFixed(2) || 'N/A'}
            </Text>
            <Text style={styles.analysisText}>
              Borrow Cost (1 year): ${data.comparison.borrow_cost_1yr?.toFixed(2) || 'N/A'}
            </Text>
            <Text style={styles.analysisText}>
              Savings: ${data.comparison.savings?.toFixed(2) || 'N/A'}
            </Text>
          </View>
        )}

        {data.factors && (
          <View style={styles.factorsCard}>
            <Text style={styles.cardTitle}>Key Factors</Text>
            {data.factors.map((factor: string, index: number) => (
              <Text key={index} style={styles.factorText}>
                • {factor}
              </Text>
            ))}
          </View>
        )}
      </View>
    );
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading borrow vs sell analysis...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <Text style={styles.title}>Borrow vs Sell Advisor</Text>
      <Text style={styles.subtitle}>
        Compare the costs of selling vs borrowing against your portfolio
      </Text>

      {renderAnalysis()}

      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>How it works:</Text>
        <Text style={styles.infoText}>
          • Analyzes your portfolio's current tax situation
        </Text>
        <Text style={styles.infoText}>
          • Compares capital gains tax vs borrowing costs
        </Text>
        <Text style={styles.infoText}>
          • Considers SBLOC and Aave borrowing options
        </Text>
        <Text style={styles.infoText}>
          • Factors in interest rates and LTV ratios
        </Text>
        <Text style={styles.infoText}>
          • Provides personalized recommendations
        </Text>
      </View>

      <TouchableOpacity style={styles.refreshButton} onPress={loadData}>
        <Text style={styles.refreshButtonText}>Refresh Analysis</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
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
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  analysisContainer: {
    marginBottom: 24,
  },
  analysisTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  comparisonCard: {
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
  comparisonTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  recommendation: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
    textAlign: 'center',
    padding: 12,
    backgroundColor: '#f0f8ff',
    borderRadius: 8,
  },
  analysisCard: {
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
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  analysisText: {
    fontSize: 14,
    color: '#333',
    marginBottom: 8,
  },
  factorsCard: {
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
  factorText: {
    fontSize: 14,
    color: '#333',
    marginBottom: 4,
  },
  infoContainer: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  refreshButton: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 24,
  },
  refreshButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default BorrowVsSellScreen;
