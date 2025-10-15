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

interface GuardRequest {
  symbol: string;
  unrealized_pnl: number;
  shares_to_sell: number;
  recent_buys_30d: Record<string, number>;
  recent_sells_30d: Record<string, number>;
  portfolio_positions: Record<string, number>;
}

interface GuardResponse {
  allowed: boolean;
  reason: string;
  suggested_substitutes: Array<{
    symbol: string;
    correlation_score: number;
    current_position: number;
    recommendation: string;
    reason: string;
    wash_sale_safe: boolean;
  }>;
  wash_sale_impact: {
    loss_amount: number;
    shares_affected: number;
    estimated_tax_benefit_lost: number;
    days_to_wait: number;
    recent_buys: number;
    recent_sells: number;
    wash_sale_triggered: boolean;
  };
  alternative_strategies: Array<{
    strategy: string;
    title: string;
    description: string;
    pros: string[];
    cons: string[];
    estimated_impact: string;
  }>;
  explanation: {
    type: string;
    summary: string;
    factors: Array<{
      name: string;
      weight: number;
      detail: string;
      impact: string;
    }>;
    risk_level: string;
    recommendation: string;
  };
}

const WashGuardScreen: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [symbol, setSymbol] = useState('');
  const [unrealizedPnl, setUnrealizedPnl] = useState('');
  const [sharesToSell, setSharesToSell] = useState('');
  const [guardResult, setGuardResult] = useState<GuardResponse | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com';

  const getAuthToken = async (): Promise<string> => {
    // Mock token - replace with actual auth logic
    return 'mock-auth-token';
  };

  const onCheckWashSale = async () => {
    if (!symbol || !unrealizedPnl || !sharesToSell) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const payload: GuardRequest = {
        symbol: symbol.toUpperCase(),
        unrealized_pnl: parseFloat(unrealizedPnl),
        shares_to_sell: parseFloat(sharesToSell),
        recent_buys_30d: {
          [symbol.toUpperCase()]: 50, // Mock data - in production, get from API
        },
        recent_sells_30d: {},
        portfolio_positions: {
          [symbol.toUpperCase()]: 100, // Mock data
          'IVV': 0,
          'SPY': 0,
        }
      };

      const response = await fetch(`${API_BASE_URL}/api/tax/wash-sale-guard`, {
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
      setGuardResult(data.result);
    } catch (error) {
      console.error('Error checking wash sale:', error);
      Alert.alert('Error', 'Failed to check wash sale. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    // Reset form
    setSymbol('');
    setUnrealizedPnl('');
    setSharesToSell('');
    setGuardResult(null);
    setRefreshing(false);
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'HIGH': return '#F44336';
      case 'MEDIUM': return '#FF9800';
      case 'LOW': return '#4CAF50';
      default: return '#666666';
    }
  };

  const renderGuardResult = () => {
    if (!guardResult) return null;

    return (
      <View style={styles.resultContainer}>
        <View style={styles.resultHeader}>
          <View style={[styles.statusBadge, { backgroundColor: guardResult.allowed ? '#4CAF50' : '#F44336' }]}>
            <Text style={styles.statusText}>
              {guardResult.allowed ? 'ALLOWED' : 'BLOCKED'}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.explanationButton}
            onPress={() => setShowExplanation(!showExplanation)}
          >
            <Ionicons name="information-circle-outline" size={20} color="#007AFF" />
            <Text style={styles.explanationButtonText}>Explanation</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.reasonText}>{guardResult.reason}</Text>

        {showExplanation && (
          <View style={styles.explanationCard}>
            <Text style={styles.explanationTitle}>Wash-Sale Analysis</Text>
            <Text style={styles.explanationSummary}>{guardResult.explanation.summary}</Text>
            
            <View style={styles.riskLevelContainer}>
              <Text style={styles.riskLevelLabel}>Risk Level:</Text>
              <View style={[styles.riskLevelBadge, { backgroundColor: getRiskColor(guardResult.explanation.risk_level) }]}>
                <Text style={styles.riskLevelText}>{guardResult.explanation.risk_level}</Text>
              </View>
            </View>

            <Text style={styles.factorsTitle}>Key Factors:</Text>
            {guardResult.explanation.factors.map((factor, index) => (
              <View key={index} style={styles.factorItem}>
                <View style={styles.factorHeader}>
                  <Text style={styles.factorName}>{factor.name.replace(/_/g, ' ')}</Text>
                  <View style={styles.factorWeightContainer}>
                    <Text style={styles.factorWeight}>{(factor.weight * 100).toFixed(0)}%</Text>
                    <View style={[styles.impactBadge, { backgroundColor: getRiskColor(factor.impact) }]}>
                      <Text style={styles.impactText}>{factor.impact}</Text>
                    </View>
                  </View>
                </View>
                <Text style={styles.factorDetail}>{factor.detail}</Text>
              </View>
            ))}
          </View>
        )}

        {guardResult.wash_sale_impact.wash_sale_triggered && (
          <View style={styles.impactCard}>
            <Text style={styles.impactTitle}>Wash-Sale Impact</Text>
            <View style={styles.impactRow}>
              <Text style={styles.impactLabel}>Loss Amount:</Text>
              <Text style={styles.impactValue}>${guardResult.wash_sale_impact.loss_amount.toLocaleString()}</Text>
            </View>
            <View style={styles.impactRow}>
              <Text style={styles.impactLabel}>Tax Benefit Lost:</Text>
              <Text style={styles.impactValue}>${guardResult.wash_sale_impact.estimated_tax_benefit_lost.toLocaleString()}</Text>
            </View>
            <View style={styles.impactRow}>
              <Text style={styles.impactLabel}>Days to Wait:</Text>
              <Text style={styles.impactValue}>{guardResult.wash_sale_impact.days_to_wait}</Text>
            </View>
          </View>
        )}

        {guardResult.suggested_substitutes.length > 0 && (
          <View style={styles.substitutesCard}>
            <Text style={styles.substitutesTitle}>Suggested Substitutes</Text>
            {guardResult.suggested_substitutes.map((sub, index) => (
              <TouchableOpacity key={index} style={styles.substituteItem}>
                <View style={styles.substituteHeader}>
                  <Text style={styles.substituteSymbol}>{sub.symbol}</Text>
                  <View style={styles.substituteBadges}>
                    <View style={[styles.correlationBadge, { backgroundColor: sub.correlation_score > 0.95 ? '#4CAF50' : '#FF9800' }]}>
                      <Text style={styles.correlationText}>{(sub.correlation_score * 100).toFixed(0)}%</Text>
                    </View>
                    <View style={[styles.recommendationBadge, { backgroundColor: sub.recommendation === 'BUY' ? '#007AFF' : '#666666' }]}>
                      <Text style={styles.recommendationText}>{sub.recommendation}</Text>
                    </View>
                  </View>
                </View>
                <Text style={styles.substituteReason}>{sub.reason}</Text>
                {sub.current_position > 0 && (
                  <Text style={styles.currentPositionText}>
                    Current Position: {sub.current_position} shares
                  </Text>
                )}
              </TouchableOpacity>
            ))}
          </View>
        )}

        {guardResult.alternative_strategies.length > 0 && (
          <View style={styles.strategiesCard}>
            <Text style={styles.strategiesTitle}>Alternative Strategies</Text>
            {guardResult.alternative_strategies.map((strategy, index) => (
              <View key={index} style={styles.strategyItem}>
                <Text style={styles.strategyTitle}>{strategy.title}</Text>
                <Text style={styles.strategyDescription}>{strategy.description}</Text>
                <Text style={styles.strategyImpact}>{strategy.estimated_impact}</Text>
                
                <View style={styles.prosConsContainer}>
                  <View style={styles.prosContainer}>
                    <Text style={styles.prosTitle}>Pros:</Text>
                    {strategy.pros.map((pro, proIndex) => (
                      <Text key={proIndex} style={styles.prosText}>• {pro}</Text>
                    ))}
                  </View>
                  <View style={styles.consContainer}>
                    <Text style={styles.consTitle}>Cons:</Text>
                    {strategy.cons.map((con, conIndex) => (
                      <Text key={conIndex} style={styles.consText}>• {con}</Text>
                    ))}
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}

        {!guardResult.allowed && (
          <TouchableOpacity style={styles.substituteButton}>
            <Text style={styles.substituteButtonText}>Use Substitute</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#007AFF', '#0056CC']}
        style={styles.header}
      >
        <Text style={styles.headerTitle}>Wash-Sale Guard</Text>
        <Text style={styles.headerSubtitle}>Real-time Wash-Sale Protection</Text>
      </LinearGradient>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.inputSection}>
          <Text style={styles.inputLabel}>Symbol</Text>
          <TextInput
            style={styles.input}
            value={symbol}
            onChangeText={setSymbol}
            placeholder="e.g., AAPL, VOO"
            placeholderTextColor="#999"
            autoCapitalize="characters"
          />
        </View>

        <View style={styles.inputSection}>
          <Text style={styles.inputLabel}>Unrealized P&L</Text>
          <TextInput
            style={styles.input}
            value={unrealizedPnl}
            onChangeText={setUnrealizedPnl}
            placeholder="Enter unrealized gain/loss"
            keyboardType="numeric"
            placeholderTextColor="#999"
          />
        </View>

        <View style={styles.inputSection}>
          <Text style={styles.inputLabel}>Shares to Sell</Text>
          <TextInput
            style={styles.input}
            value={sharesToSell}
            onChangeText={setSharesToSell}
            placeholder="Enter number of shares"
            keyboardType="numeric"
            placeholderTextColor="#999"
          />
        </View>

        <TouchableOpacity
          style={[styles.checkButton, loading && styles.checkButtonDisabled]}
          onPress={onCheckWashSale}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <>
              <Ionicons name="shield-checkmark-outline" size={20} color="#FFFFFF" />
              <Text style={styles.checkButtonText}>Check Wash-Sale Risk</Text>
            </>
          )}
        </TouchableOpacity>

        {renderGuardResult()}
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
  checkButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  checkButtonDisabled: {
    backgroundColor: '#CCCCCC',
  },
  checkButtonText: {
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
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  statusText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
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
  reasonText: {
    fontSize: 16,
    color: '#666666',
    marginBottom: 16,
    lineHeight: 22,
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
  riskLevelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  riskLevelLabel: {
    fontSize: 14,
    color: '#666666',
    marginRight: 8,
  },
  riskLevelBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  riskLevelText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
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
  factorWeightContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  factorWeight: {
    fontSize: 12,
    color: '#007AFF',
    marginRight: 8,
  },
  impactBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  impactText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '600',
  },
  factorDetail: {
    fontSize: 12,
    color: '#666666',
    marginTop: 2,
  },
  impactCard: {
    backgroundColor: '#FFF3E0',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  impactTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#E65100',
    marginBottom: 12,
  },
  impactRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  impactLabel: {
    fontSize: 14,
    color: '#E65100',
  },
  impactValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#E65100',
  },
  substitutesCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  substitutesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 12,
  },
  substituteItem: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  substituteHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  substituteSymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A1A',
  },
  substituteBadges: {
    flexDirection: 'row',
  },
  correlationBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  correlationText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  recommendationBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  recommendationText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  substituteReason: {
    fontSize: 12,
    color: '#666666',
    marginBottom: 4,
  },
  currentPositionText: {
    fontSize: 12,
    color: '#007AFF',
  },
  strategiesCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  strategiesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 12,
  },
  strategyItem: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  strategyTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  strategyDescription: {
    fontSize: 12,
    color: '#666666',
    marginBottom: 4,
  },
  strategyImpact: {
    fontSize: 12,
    color: '#007AFF',
    marginBottom: 8,
  },
  prosConsContainer: {
    flexDirection: 'row',
  },
  prosContainer: {
    flex: 1,
    marginRight: 8,
  },
  prosTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4CAF50',
    marginBottom: 4,
  },
  prosText: {
    fontSize: 10,
    color: '#4CAF50',
    marginBottom: 2,
  },
  consContainer: {
    flex: 1,
    marginLeft: 8,
  },
  consTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#F44336',
    marginBottom: 4,
  },
  consText: {
    fontSize: 10,
    color: '#F44336',
    marginBottom: 2,
  },
  substituteButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  substituteButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default WashGuardScreen;
