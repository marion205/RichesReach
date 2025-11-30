import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface OptionsRiskCalculatorProps {
  symbol: string;
  underlyingPrice: number;
}

export default function OptionsRiskCalculator({ symbol, underlyingPrice }: OptionsRiskCalculatorProps) {
  const [strike, setStrike] = useState(underlyingPrice.toString());
  const [premium, setPremium] = useState('2.50');
  const [expirationDays, setExpirationDays] = useState('30');
  const [optionType, setOptionType] = useState<'call' | 'put'>('call');
  const [contracts, setContracts] = useState('1');
  const [targetPrice, setTargetPrice] = useState('');
  const [stopLossPrice, setStopLossPrice] = useState('');

  // Calculate risk metrics
  const riskMetrics = useMemo(() => {
    const strikePrice = parseFloat(strike) || 0;
    const premiumPrice = parseFloat(premium) || 0;
    const days = parseInt(expirationDays) || 30;
    const numContracts = parseInt(contracts) || 1;
    const target = parseFloat(targetPrice) || 0;
    const stopLoss = parseFloat(stopLossPrice) || 0;

    const totalCost = premiumPrice * 100 * numContracts;
    const maxLoss = totalCost; // For long options, max loss is premium paid
    const maxProfit = optionType === 'call'
      ? (target > strikePrice ? (target - strikePrice - premiumPrice) * 100 * numContracts : 0)
      : (stopLoss < strikePrice ? (strikePrice - stopLoss - premiumPrice) * 100 * numContracts : 0);

    // Probability calculations (simplified Black-Scholes approximation)
    const moneyness = optionType === 'call'
      ? (underlyingPrice - strikePrice) / underlyingPrice
      : (strikePrice - underlyingPrice) / underlyingPrice;
    
    const timeValue = premiumPrice - Math.max(0, optionType === 'call' 
      ? underlyingPrice - strikePrice 
      : strikePrice - underlyingPrice);
    
    const intrinsicValue = optionType === 'call'
      ? Math.max(0, underlyingPrice - strikePrice)
      : Math.max(0, strikePrice - underlyingPrice);

    // Win probability (simplified - would use actual IV and Black-Scholes in production)
    const winProbability = optionType === 'call'
      ? Math.max(10, Math.min(90, 50 + (moneyness * 30)))
      : Math.max(10, Math.min(90, 50 - (moneyness * 30)));

    // Risk/Reward ratio
    const riskReward = target > 0 && stopLoss > 0
      ? Math.abs((target - strikePrice) / (strikePrice - stopLoss))
      : 0;

    // Position size recommendation (risk 1-2% of account)
    const recommendedAccountSize = totalCost / 0.02; // 2% risk

    return {
      totalCost,
      maxLoss,
      maxProfit,
      intrinsicValue,
      timeValue,
      winProbability,
      riskReward,
      recommendedAccountSize,
      breakEven: optionType === 'call'
        ? strikePrice + premiumPrice
        : strikePrice - premiumPrice,
    };
  }, [strike, premium, expirationDays, contracts, optionType, targetPrice, stopLossPrice, underlyingPrice]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="shield" size={18} color="#007AFF" />
        <Text style={styles.title}>Options Risk Calculator</Text>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Input Section */}
        <View style={styles.inputSection}>
          <View style={styles.inputRow}>
            <Text style={styles.label}>Option Type</Text>
            <View style={styles.segmentedControl}>
              <TouchableOpacity
                style={[styles.segment, optionType === 'call' && styles.segmentActive]}
                onPress={() => setOptionType('call')}
              >
                <Text style={[styles.segmentText, optionType === 'call' && styles.segmentTextActive]}>
                  Call
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.segment, optionType === 'put' && styles.segmentActive]}
                onPress={() => setOptionType('put')}
              >
                <Text style={[styles.segmentText, optionType === 'put' && styles.segmentTextActive]}>
                  Put
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Strike Price</Text>
            <TextInput
              style={styles.input}
              value={strike}
              onChangeText={setStrike}
              keyboardType="numeric"
              placeholder={underlyingPrice.toString()}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Premium (per contract)</Text>
            <TextInput
              style={styles.input}
              value={premium}
              onChangeText={setPremium}
              keyboardType="numeric"
              placeholder="2.50"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Days to Expiration</Text>
            <TextInput
              style={styles.input}
              value={expirationDays}
              onChangeText={setExpirationDays}
              keyboardType="numeric"
              placeholder="30"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Number of Contracts</Text>
            <TextInput
              style={styles.input}
              value={contracts}
              onChangeText={setContracts}
              keyboardType="numeric"
              placeholder="1"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Target Price (optional)</Text>
            <TextInput
              style={styles.input}
              value={targetPrice}
              onChangeText={setTargetPrice}
              keyboardType="numeric"
              placeholder="Take profit target"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Stop Loss Price (optional)</Text>
            <TextInput
              style={styles.input}
              value={stopLossPrice}
              onChangeText={setStopLossPrice}
              keyboardType="numeric"
              placeholder="Stop loss level"
            />
          </View>
        </View>

        {/* Risk Metrics */}
        <View style={styles.metricsSection}>
          <Text style={styles.sectionTitle}>Risk Analysis</Text>

          <View style={styles.metricCard}>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Total Cost</Text>
              <Text style={styles.metricValue}>${riskMetrics.totalCost.toFixed(2)}</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Max Loss</Text>
              <Text style={[styles.metricValue, styles.lossValue]}>
                ${riskMetrics.maxLoss.toFixed(2)}
              </Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Max Profit</Text>
              <Text style={[styles.metricValue, styles.profitValue]}>
                ${riskMetrics.maxProfit > 0 ? `+${riskMetrics.maxProfit.toFixed(2)}` : '$0.00'}
              </Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Break-Even Price</Text>
              <Text style={styles.metricValue}>${riskMetrics.breakEven.toFixed(2)}</Text>
            </View>
          </View>

          <View style={styles.metricCard}>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Intrinsic Value</Text>
              <Text style={styles.metricValue}>${riskMetrics.intrinsicValue.toFixed(2)}</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Time Value</Text>
              <Text style={styles.metricValue}>${riskMetrics.timeValue.toFixed(2)}</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Win Probability</Text>
              <Text style={styles.metricValue}>{riskMetrics.winProbability.toFixed(0)}%</Text>
            </View>
            {riskMetrics.riskReward > 0 && (
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Risk/Reward Ratio</Text>
                <Text style={styles.metricValue}>
                  {riskMetrics.riskReward.toFixed(2)}:1
                </Text>
              </View>
            )}
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.recommendationTitle}>Position Sizing Recommendation</Text>
            <Text style={styles.recommendationText}>
              To risk 2% of your account, you should have at least:
            </Text>
            <Text style={styles.recommendationValue}>
              ${riskMetrics.recommendedAccountSize.toFixed(2)} in your account
            </Text>
            {riskMetrics.totalCost > riskMetrics.recommendedAccountSize * 0.02 && (
              <View style={styles.warningBox}>
                <Icon name="alert-triangle" size={16} color="#DC2626" />
                <Text style={styles.warningText}>
                  This position risks more than 2% of recommended account size
                </Text>
              </View>
            )}
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    maxHeight: 600,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginLeft: 8,
  },
  inputSection: {
    marginBottom: 20,
  },
  inputRow: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 2,
  },
  segment: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  segmentActive: {
    backgroundColor: '#007AFF',
  },
  segmentText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  segmentTextActive: {
    color: '#FFFFFF',
  },
  inputGroup: {
    marginBottom: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#111827',
    backgroundColor: '#FFFFFF',
  },
  metricsSection: {
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  metricCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  metricLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  lossValue: {
    color: '#DC2626',
  },
  profitValue: {
    color: '#059669',
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  recommendationText: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  recommendationValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#007AFF',
    marginBottom: 8,
  },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
    gap: 8,
  },
  warningText: {
    fontSize: 13,
    color: '#DC2626',
    flex: 1,
  },
});

