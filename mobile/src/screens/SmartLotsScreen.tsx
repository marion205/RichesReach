import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

interface Lot {
  lot_id: string;
  symbol: string;
  shares: number;
  cost_basis: number;
  price: number;
  acquire_date: string;
  unrealized_gain: number;
}

interface OptimizeResponse {
  sells: Array<{
    lot_id: string;
    symbol: string;
    sell_shares: number;
    est_tax: number;
    cash_raised: number;
    holding: string;
    gain_per_share: number;
    tax_rate: number;
    days_held: number;
  }>;
  cash_raised: number;
  est_tax_cost: number;
  objective: number;
  explanation: {
    type: string;
    summary: string;
    factors: Array<{
      name: string;
      weight: number;
      detail: string;
    }>;
    metrics: {
      total_shares_sold: number;
      effective_tax_rate: number;
      long_term_tax_savings: number;
      wash_sales_avoided: number;
    };
  };
  wash_sale_warnings: string[];
  portfolio_drift_impact: Record<string, number>;
}

const SmartLotsScreen: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [targetCash, setTargetCash] = useState('');
  const [lots, setLots] = useState<Lot[]>([]);
  const [optimizationResult, setOptimizationResult] = useState<OptimizeResponse | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    loadSampleLots();
  }, []);

  const loadSampleLots = () => {
    // Sample lots data - in production, this would come from the API
    const sampleLots: Lot[] = [
      {
        lot_id: 'lot_001',
        symbol: 'AAPL',
        shares: 100,
        cost_basis: 150.00,
        price: 140.00,
        acquire_date: '2023-01-15',
        unrealized_gain: -1000.00
      },
      {
        lot_id: 'lot_002',
        symbol: 'TSLA',
        shares: 50,
        cost_basis: 200.00,
        price: 180.00,
        acquire_date: '2023-06-20',
        unrealized_gain: -1000.00
      },
      {
        lot_id: 'lot_003',
        symbol: 'MSFT',
        shares: 75,
        cost_basis: 300.00,
        price: 320.00,
        acquire_date: '2022-03-10',
        unrealized_gain: 1500.00
      },
      {
        lot_id: 'lot_004',
        symbol: 'GOOGL',
        shares: 25,
        cost_basis: 2000.00,
        price: 2500.00,
        acquire_date: '2021-11-05',
        unrealized_gain: 12500.00
      }
    ];
    setLots(sampleLots);
  };

  const getAuthToken = async (): Promise<string> => {
    // Mock token - replace with actual auth logic
    return 'mock-auth-token';
  };

  const onOptimize = async () => {
    if (!targetCash || parseFloat(targetCash) <= 0) {
      Alert.alert('Error', 'Please enter a valid target cash amount');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        lots: lots,
        target_cash: parseFloat(targetCash),
        long_term_days: 365,
        fed_st_rate: 0.24,
        fed_lt_rate: 0.15,
        state_st_rate: 0.0,
        forbid_wash_sale: true,
        recent_buys_30d: {},
        max_portfolio_drift: 0.05
      };

      const response = await fetch(`${API_BASE_URL}/api/tax/smart-lot-optimizer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await getAuthToken()}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setOptimizationResult(data.result);
    } catch (error) {
      console.error('Error optimizing lots:', error);
      Alert.alert('Error', 'Failed to optimize lots. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    loadSampleLots();
    setRefreshing(false);
  };

  const getHoldingColor = (holding: string) => {
    return holding === 'LT' ? '#4CAF50' : '#FF9800';
  };

  const renderLotItem = (lot: Lot) => (
    <View key={lot.lot_id} style={styles.lotItem}>
      <View style={styles.lotHeader}>
        <Text style={styles.symbolText}>{lot.symbol}</Text>
        <Text style={styles.sharesText}>{lot.shares} shares</Text>
      </View>
      <View style={styles.lotDetails}>
        <Text style={styles.detailText}>Cost Basis: ${lot.cost_basis.toFixed(2)}</Text>
        <Text style={styles.detailText}>Current Price: ${lot.price.toFixed(2)}</Text>
        <Text style={[styles.detailText, { color: lot.unrealized_gain >= 0 ? '#4CAF50' : '#F44336' }]}>
          Unrealized: ${lot.unrealized_gain.toFixed(2)}
        </Text>
      </View>
    </View>
  );

  const renderOptimizationResult = () => {
    if (!optimizationResult) return null;

    return (
      <View style={styles.resultContainer}>
        <View style={styles.resultHeader}>
          <Text style={styles.resultTitle}>Optimization Results</Text>
          <TouchableOpacity
            style={styles.explanationButton}
            onPress={() => setShowExplanation(!showExplanation)}
          >
            <Ionicons name="information-circle-outline" size={20} color="#007AFF" />
            <Text style={styles.explanationButtonText}>Explanation</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.summaryCard}>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Cash Raised:</Text>
            <Text style={styles.summaryValue}>${optimizationResult.cash_raised.toLocaleString()}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Tax Cost:</Text>
            <Text style={styles.summaryValue}>${optimizationResult.est_tax_cost.toLocaleString()}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Effective Rate:</Text>
            <Text style={styles.summaryValue}>
              {((optimizationResult.est_tax_cost / optimizationResult.cash_raised) * 100).toFixed(1)}%
            </Text>
          </View>
        </View>

        {showExplanation && (
          <View style={styles.explanationCard}>
            <Text style={styles.explanationTitle}>Why This Optimization?</Text>
            <Text style={styles.explanationSummary}>{optimizationResult.explanation.summary}</Text>
            
            <Text style={styles.factorsTitle}>Key Factors:</Text>
            {optimizationResult.explanation.factors.map((factor, index) => (
              <View key={index} style={styles.factorItem}>
                <View style={styles.factorHeader}>
                  <Text style={styles.factorName}>{factor.name.replace(/_/g, ' ')}</Text>
                  <Text style={styles.factorWeight}>{(factor.weight * 100).toFixed(0)}%</Text>
                </View>
                <Text style={styles.factorDetail}>{factor.detail}</Text>
              </View>
            ))}
          </View>
        )}

        <Text style={styles.sellsTitle}>Recommended Sales:</Text>
        {optimizationResult.sells.map((sell, index) => (
          <View key={index} style={styles.sellItem}>
            <View style={styles.sellHeader}>
              <Text style={styles.sellSymbol}>{sell.symbol}</Text>
              <View style={[styles.holdingBadge, { backgroundColor: getHoldingColor(sell.holding) }]}>
                <Text style={styles.holdingText}>{sell.holding}</Text>
              </View>
            </View>
            <View style={styles.sellDetails}>
              <Text style={styles.sellDetail}>Sell: {sell.sell_shares.toFixed(2)} shares</Text>
              <Text style={styles.sellDetail}>Cash: ${sell.cash_raised.toLocaleString()}</Text>
              <Text style={styles.sellDetail}>Tax: ${sell.est_tax.toLocaleString()}</Text>
              <Text style={styles.sellDetail}>Rate: {sell.tax_rate.toFixed(1)}%</Text>
            </View>
          </View>
        ))}

        {optimizationResult.wash_sale_warnings.length > 0 && (
          <View style={styles.warningsCard}>
            <Text style={styles.warningsTitle}>Wash-Sale Warnings:</Text>
            {optimizationResult.wash_sale_warnings.map((warning, index) => (
              <Text key={index} style={styles.warningText}>• {warning}</Text>
            ))}
          </View>
        )}

        <TouchableOpacity style={styles.createOrderButton}>
          <Text style={styles.createOrderButtonText}>Create Order</Text>
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#007AFF', '#0056CC']}
        style={styles.header}
      >
        <Text style={styles.headerTitle}>Smart Lot Optimizer</Text>
        <Text style={styles.headerSubtitle}>AI-Powered Tax Optimization</Text>
      </LinearGradient>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.inputSection}>
          <Text style={styles.inputLabel}>Target Cash Amount</Text>
          <TextInput
            style={styles.input}
            value={targetCash}
            onChangeText={setTargetCash}
            placeholder="Enter amount to raise"
            keyboardType="numeric"
            placeholderTextColor="#999"
          />
        </View>

        <View style={styles.lotsSection}>
          <Text style={styles.sectionTitle}>Available Lots</Text>
          {lots.map(renderLotItem)}
        </View>

        <TouchableOpacity
          style={[styles.optimizeButton, loading && styles.optimizeButtonDisabled]}
          onPress={onOptimize}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <>
              <Ionicons name="analytics-outline" size={20} color="#FFFFFF" />
              <Text style={styles.optimizeButtonText}>Optimize Lots</Text>
            </>
          )}
        </TouchableOpacity>

        {renderOptimizationResult()}
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
  content: {
    flex: 1,
    padding: 16,
  },
  inputSection: {
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
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A1A',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E1E5E9',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1A1A1A',
  },
  lotsSection: {
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
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 16,
  },
  lotItem: {
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    marginBottom: 12,
  },
  lotHeader: {
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
  sharesText: {
    fontSize: 14,
    color: '#666666',
  },
  lotDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailText: {
    fontSize: 12,
    color: '#666666',
  },
  optimizeButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  optimizeButtonDisabled: {
    backgroundColor: '#CCCCCC',
  },
  optimizeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  resultContainer: {
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
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1A1A1A',
  },
  explanationButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  explanationButtonText: {
    color: '#007AFF',
    fontSize: 14,
    marginLeft: 4,
  },
  summaryCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666666',
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  explanationCard: {
    backgroundColor: '#E3F2FD',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  explanationTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 8,
  },
  explanationSummary: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 12,
    lineHeight: 20,
  },
  factorsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
    marginBottom: 8,
  },
  factorItem: {
    marginBottom: 8,
  },
  factorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  factorName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1A1A1A',
    textTransform: 'capitalize',
  },
  factorWeight: {
    fontSize: 12,
    color: '#007AFF',
  },
  factorDetail: {
    fontSize: 12,
    color: '#666666',
    marginTop: 2,
  },
  sellsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 12,
  },
  sellItem: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  sellHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sellSymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A1A',
  },
  holdingBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  holdingText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  sellDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
  },
  sellDetail: {
    fontSize: 12,
    color: '#666666',
    marginBottom: 4,
  },
  warningsCard: {
    backgroundColor: '#FFF3E0',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  warningsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#E65100',
    marginBottom: 8,
  },
  warningText: {
    fontSize: 12,
    color: '#E65100',
    marginBottom: 4,
  },
  createOrderButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  createOrderButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default SmartLotsScreen;
