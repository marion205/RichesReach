import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';
import taxOptimizationService, { TaxOptimizationRequest } from '../services/taxOptimizationService';

const SmartLotsScreen: React.FC = () => {
  const { token } = useAuth();
  const [targetCash, setTargetCash] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleOptimize = async () => {
    if (!token) {
      Alert.alert('Authentication Required', 'Please log in to use this feature.');
      return;
    }

    if (!targetCash || isNaN(Number(targetCash))) {
      Alert.alert('Invalid Input', 'Please enter a valid target cash amount.');
      return;
    }

    setLoading(true);
    try {
      // Sample lot data - in a real app, this would come from the user's portfolio
      const sampleLots = [
        {
          lot_id: 'lot_1',
          symbol: 'AAPL',
          shares: 100,
          cost_basis: 150.00,
          price: 175.00,
          acquire_date: '2023-01-15',
        },
        {
          lot_id: 'lot_2',
          symbol: 'AAPL',
          shares: 50,
          cost_basis: 160.00,
          price: 175.00,
          acquire_date: '2023-06-10',
        },
        {
          lot_id: 'lot_3',
          symbol: 'MSFT',
          shares: 75,
          cost_basis: 300.00,
          price: 320.00,
          acquire_date: '2022-12-01',
        },
        {
          lot_id: 'lot_4',
          symbol: 'GOOGL',
          shares: 25,
          cost_basis: 2500.00,
          price: 2400.00,
          acquire_date: '2023-03-20',
        },
      ];

      const request: TaxOptimizationRequest = {
        target_cash: Number(targetCash),
        lots: sampleLots,
        long_term_days: 365,
        fed_st_rate: 0.24,
        fed_lt_rate: 0.15,
        forbid_wash_sale: true,
        recent_buys_30d: {},
      };

      const response = await taxOptimizationService.optimizeLots(request, token);
      setResult(response);
    } catch (error) {
      console.error('Error optimizing lots:', error);
      Alert.alert('Error', 'Failed to optimize lots. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderResult = () => {
    if (!result) return null;

    return (
      <View style={styles.resultContainer}>
        <Text style={styles.resultTitle}>Optimization Results</Text>
        
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Summary</Text>
          <Text style={styles.summaryText}>
            Cash Raised: ${result.cash_raised?.toFixed(2) || 'N/A'}
          </Text>
          <Text style={styles.summaryText}>
            Estimated Tax Cost: ${result.est_tax_cost?.toFixed(2) || 'N/A'}
          </Text>
          <Text style={styles.summaryText}>
            Objective Value: {result.objective?.toFixed(2) || 'N/A'}
          </Text>
        </View>

        {result.sells && result.sells.length > 0 && (
          <View style={styles.sellsContainer}>
            <Text style={styles.sellsTitle}>Recommended Sales</Text>
            {result.sells.map((sell: any, index: number) => (
              <View key={index} style={styles.sellItem}>
                <Text style={styles.sellSymbol}>{sell.symbol}</Text>
                <Text style={styles.sellDetails}>
                  {sell.shares} shares @ ${sell.price?.toFixed(2)}
                </Text>
                <Text style={styles.sellTax}>
                  Tax Cost: ${sell.tax_cost?.toFixed(2)}
                </Text>
                <Text style={styles.sellReason}>{sell.reason}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Smart Lot Optimizer</Text>
      <Text style={styles.subtitle}>
        Optimize which lots to sell to minimize tax impact
      </Text>

      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Target Cash Amount ($)</Text>
        <TextInput
          style={styles.input}
          value={targetCash}
          onChangeText={setTargetCash}
          placeholder="Enter target cash amount"
          keyboardType="numeric"
          placeholderTextColor="#999"
        />
      </View>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleOptimize}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Optimize Lots</Text>
        )}
      </TouchableOpacity>

      {renderResult()}

      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>How it works:</Text>
        <Text style={styles.infoText}>
          • Analyzes all your lots to find the optimal combination
        </Text>
        <Text style={styles.infoText}>
          • Minimizes tax impact while hitting your target cash amount
        </Text>
        <Text style={styles.infoText}>
          • Considers wash-sale rules and tax brackets
        </Text>
        <Text style={styles.infoText}>
          • Uses advanced optimization algorithms
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
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
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#333',
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 24,
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultContainer: {
    marginBottom: 24,
  },
  resultTitle: {
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
  summaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  summaryText: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
  sellsContainer: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sellsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  sellItem: {
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    paddingVertical: 12,
  },
  sellSymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  sellDetails: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  sellTax: {
    fontSize: 14,
    color: '#e74c3c',
    marginTop: 4,
  },
  sellReason: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
    fontStyle: 'italic',
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
});

export default SmartLotsScreen;