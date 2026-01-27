/**
 * Crystal Ball Simulator Component
 * "What-If" financial scenario simulator with real-time predictions
 */

import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from 'react-native-vector-icons/Feather';
import { CreditSnapshot, FinancialAction, SimulationResult } from '../types/CreditTypes';
import { simulateFinancialAction } from '../services/CrystalBallSimulatorService';
import { getMerchantIntelligence } from '../services/MerchantIntelligenceService';

interface CrystalBallSimulatorProps {
  currentData: CreditSnapshot;
  onClose?: () => void;
}

export const CrystalBallSimulator: React.FC<CrystalBallSimulatorProps> = ({
  currentData,
  onClose,
}) => {
  const insets = useSafeAreaInsets();
  const [actionType, setActionType] = useState<FinancialAction['type']>('LARGE_PURCHASE');
  const [amount, setAmount] = useState<string>('0');
  const [merchant, setMerchant] = useState<string>('');
  const [showMerchantInput, setShowMerchantInput] = useState(false);

  const currentScore = currentData.score.score;
  const currentBalance = currentData.utilization.totalBalance;
  const creditLimit = currentData.utilization.totalLimit;
  const availableCredit = creditLimit - currentBalance;

  // Run simulation
  const simulation: SimulationResult | null = useMemo(() => {
    const amountNum = parseFloat(amount) || 0;
    if (amountNum <= 0) return null;

    const action: FinancialAction = {
      type: actionType,
      amount: amountNum,
      merchant: merchant || undefined,
    };

    try {
      return simulateFinancialAction(currentData, action);
    } catch (error) {
      console.error('[CrystalBall] Simulation error:', error);
      return null;
    }
  }, [actionType, amount, merchant, currentData]);

  // Check for merchant intelligence
  const merchantDeal = merchant ? getMerchantIntelligence(merchant) : null;

  const getActionIcon = (type: FinancialAction['type']) => {
    switch (type) {
      case 'LARGE_PURCHASE': return 'shopping-bag';
      case 'NEW_CREDIT_LINE': return 'credit-card';
      case 'DEBT_CONSOLIDATION': return 'refresh-cw';
      case 'PAYMENT': return 'dollar-sign';
      case 'BALANCE_TRANSFER': return 'arrow-right';
      default: return 'help-circle';
    }
  };

  const getActionColor = (type: FinancialAction['type']) => {
    switch (type) {
      case 'LARGE_PURCHASE': return '#FF9500';
      case 'NEW_CREDIT_LINE': return '#007AFF';
      case 'DEBT_CONSOLIDATION': return '#34C759';
      case 'PAYMENT': return '#34C759';
      case 'BALANCE_TRANSFER': return '#5AC8FA';
      default: return '#8E8E93';
    }
  };

  return (
    <Modal
      visible={true}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={onClose}
    >
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <LinearGradient
          colors={['#1a1a2e', '#16213e', '#0f3460']}
          style={StyleSheet.absoluteFill}
        />
        
        {/* Header */}
        <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>🔮 Crystal Ball</Text>
          <Text style={styles.headerSubtitle}>Financial Time Machine</Text>
        </View>
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#FFFFFF" />
          </TouchableOpacity>
        )}
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Action Type Selector */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What would you like to simulate?</Text>
          <View style={styles.actionTypeGrid}>
            {(['LARGE_PURCHASE', 'PAYMENT', 'DEBT_CONSOLIDATION', 'BALANCE_TRANSFER'] as const).map((type) => (
              <TouchableOpacity
                key={type}
                style={[
                  styles.actionTypeButton,
                  actionType === type && { 
                    borderColor: getActionColor(type),
                    borderWidth: 2,
                  },
                ]}
                onPress={() => {
                  setActionType(type);
                  setShowMerchantInput(type === 'LARGE_PURCHASE');
                }}
                activeOpacity={0.7}
              >
                <Icon 
                  name={getActionIcon(type)} 
                  size={24} 
                  color={actionType === type ? getActionColor(type) : '#8E8E93'} 
                />
                <Text style={[
                  styles.actionTypeText,
                  actionType === type && { color: getActionColor(type) },
                ]}>
                  {type.replace(/_/g, ' ')}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Amount Input */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {actionType === 'LARGE_PURCHASE' ? 'Purchase Amount' :
             actionType === 'PAYMENT' ? 'Payment Amount' :
             actionType === 'DEBT_CONSOLIDATION' ? 'Debt to Consolidate' :
             'Transfer Amount'}
          </Text>
          <View style={styles.amountContainer}>
            <Text style={styles.currencySymbol}>$</Text>
            <TextInput
              style={styles.amountInput}
              value={amount}
              onChangeText={(text) => {
                const num = text.replace(/[^0-9.]/g, '');
                setAmount(num);
              }}
              placeholder="0"
              placeholderTextColor="#8E8E93"
              keyboardType="numeric"
            />
          </View>
          {actionType === 'LARGE_PURCHASE' && (
            <Text style={styles.availableCredit}>
              Available Credit: ${availableCredit.toLocaleString()}
            </Text>
          )}
        </View>

        {/* Merchant Input (for purchases) */}
        {showMerchantInput && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Where are you shopping? (Optional)</Text>
            <TextInput
              style={styles.merchantInput}
              value={merchant}
              onChangeText={setMerchant}
              placeholder="e.g., Apple Store, Amazon, Best Buy"
              placeholderTextColor="#8E8E93"
            />
            {merchantDeal && (
              <View style={styles.merchantDealCard}>
                <LinearGradient
                  colors={['#34C759', '#2E9E4B']}
                  style={styles.merchantDealGradient}
                >
                  <Icon name="zap" size={20} color="#FFFFFF" />
                  <View style={styles.merchantDealContent}>
                    <Text style={styles.merchantDealTitle}>Zero-Gravity Path Found!</Text>
                    <Text style={styles.merchantDealText}>
                      {merchantDeal.option}: {merchantDeal.benefit}
                    </Text>
                    <Text style={styles.merchantDealImpact}>
                      Interest Leak: $0.00/month
                    </Text>
                  </View>
                </LinearGradient>
              </View>
            )}
          </View>
        )}

        {/* Simulation Results */}
        {simulation && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Projected Impact</Text>
            
            {/* Score Projection */}
            <View style={styles.resultCard}>
              <LinearGradient
                colors={simulation.scoreDelta < -20 ? ['#FF3B30', '#D63028'] :
                        simulation.scoreDelta < 0 ? ['#FF9500', '#D87A00'] :
                        ['#34C759', '#2E9E4B']}
                style={styles.resultGradient}
              >
                <View style={styles.resultHeader}>
                  <Text style={styles.resultLabel}>Projected Score</Text>
                  <Icon 
                    name={simulation.scoreDelta < 0 ? "trending-down" : "trending-up"} 
                    size={24} 
                    color="#FFFFFF" 
                  />
                </View>
                <Text style={styles.resultValue}>{simulation.projectedScore}</Text>
                <Text style={styles.resultDelta}>
                  {simulation.scoreDelta >= 0 ? '+' : ''}{simulation.scoreDelta} points
                </Text>
              </LinearGradient>
            </View>

            {/* Utilization */}
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Projected Utilization</Text>
              <Text style={styles.statValue}>
                {(simulation.projectedUtilization * 100).toFixed(1)}%
              </Text>
            </View>

            {/* Interest Leak / Savings */}
            {simulation.monthlyInterestLeak !== 0 && (
              <View style={styles.statCard}>
                <Text style={styles.statLabel}>
                  {simulation.monthlyInterestLeak > 0 ? 'Monthly Interest Leak' : 'Monthly Interest Savings'}
                </Text>
                <Text style={[
                  styles.statValue,
                  { color: simulation.monthlyInterestLeak > 0 ? '#FF3B30' : '#34C759' },
                ]}>
                  ${Math.abs(simulation.monthlyInterestLeak).toFixed(2)}/month
                </Text>
                {simulation.monthlyInterestLeak > 0 && (
                  <Text style={styles.statSubtext}>
                    At 22% APR if not paid immediately
                  </Text>
                )}
              </View>
            )}

            {/* Opportunity Cost */}
            {simulation.opportunityCost && (
              <View style={styles.opportunityCard}>
                <LinearGradient
                  colors={['#FFF8E1', '#FFEFD5']}
                  style={styles.opportunityGradient}
                >
                  <Icon name="trending-up" size={20} color="#FFB800" />
                  <View style={styles.opportunityContent}>
                    <Text style={styles.opportunityTitle}>Opportunity Cost</Text>
                    <Text style={styles.opportunityText}>
                      {actionType === 'PAYMENT' ? 'Paying now' : 'Avoiding this'} is equivalent to earning a{' '}
                      <Text style={styles.opportunityHighlight}>
                        {simulation.opportunityCost.guaranteedReturn.toFixed(1)}% guaranteed return
                      </Text>
                      {' '}by avoiding interest.
                    </Text>
                    <Text style={styles.opportunitySavings}>
                      Total Interest Saved: ${simulation.opportunityCost.totalInterestSaved.toFixed(2)}/year
                    </Text>
                  </View>
                </LinearGradient>
              </View>
            )}

            {/* Recovery Time */}
            {simulation.recoveryMonths > 0 && (
              <View style={styles.recoveryCard}>
                <Icon name="clock" size={20} color="#FF9500" />
                <View style={styles.recoveryContent}>
                  <Text style={styles.recoveryTitle}>Time to Recovery</Text>
                  <Text style={styles.recoveryText}>
                    Your score will likely recover in approximately{' '}
                    <Text style={styles.recoveryHighlight}>
                      {simulation.recoveryMonths} month{simulation.recoveryMonths > 1 ? 's' : ''}
                    </Text>
                    {' '}based on your typical payment patterns.
                  </Text>
                </View>
              </View>
            )}

            {/* Oracle Insight */}
            <View style={styles.insightCard}>
              <Icon name="eye" size={20} color="#667eea" />
              <Text style={styles.insightText}>{simulation.insight}</Text>
            </View>
          </View>
        )}

        {/* Zero Gravity Option */}
        {simulation?.zeroGravityOption && (
          <View style={styles.zeroGravityCard}>
            <LinearGradient
              colors={['#667eea', '#764ba2']}
              style={styles.zeroGravityGradient}
            >
              <Icon name="zap" size={24} color="#FFFFFF" />
              <View style={styles.zeroGravityContent}>
                <Text style={styles.zeroGravityTitle}>🚀 Zero-Gravity Alternative</Text>
                <Text style={styles.zeroGravityText}>
                  Using {simulation.zeroGravityOption.option} at {simulation.zeroGravityOption.merchant} eliminates interest costs entirely.
                </Text>
                <Text style={styles.zeroGravityBenefit}>
                  {simulation.zeroGravityOption.benefit}
                </Text>
              </View>
            </LinearGradient>
          </View>
        )}

        {/* Bottom Padding */}
        <View style={{ height: 40 }} />
      </ScrollView>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  headerLeft: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
  },
  closeButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  actionTypeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  actionTypeButton: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  actionTypeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  amountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  currencySymbol: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginRight: 8,
  },
  amountInput: {
    flex: 1,
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  availableCredit: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    marginTop: 8,
  },
  merchantInput: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  merchantDealCard: {
    marginTop: 12,
    borderRadius: 12,
    overflow: 'hidden',
  },
  merchantDealGradient: {
    flexDirection: 'row',
    padding: 16,
    alignItems: 'center',
    gap: 12,
  },
  merchantDealContent: {
    flex: 1,
  },
  merchantDealTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  merchantDealText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    marginBottom: 4,
  },
  merchantDealImpact: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '600',
  },
  resultCard: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 16,
  },
  resultGradient: {
    padding: 20,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  resultLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.9)',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  resultValue: {
    fontSize: 48,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  resultDelta: {
    fontSize: 16,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.9)',
  },
  statCard: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  statSubtext: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    marginTop: 4,
  },
  opportunityCard: {
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 12,
  },
  opportunityGradient: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  opportunityContent: {
    flex: 1,
  },
  opportunityTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 8,
  },
  opportunityText: {
    fontSize: 14,
    color: '#1A1A1A',
    lineHeight: 20,
    marginBottom: 8,
  },
  opportunityHighlight: {
    fontWeight: '700',
    color: '#FFB800',
  },
  opportunitySavings: {
    fontSize: 14,
    fontWeight: '600',
    color: '#34C759',
  },
  recoveryCard: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,149,0,0.2)',
    borderRadius: 12,
    padding: 16,
    gap: 12,
    marginBottom: 12,
  },
  recoveryContent: {
    flex: 1,
  },
  recoveryTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  recoveryText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    lineHeight: 20,
  },
  recoveryHighlight: {
    fontWeight: '700',
    color: '#FF9500',
  },
  insightCard: {
    flexDirection: 'row',
    backgroundColor: 'rgba(102,126,234,0.2)',
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  insightText: {
    flex: 1,
    fontSize: 14,
    color: '#FFFFFF',
    lineHeight: 20,
  },
  zeroGravityCard: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 24,
  },
  zeroGravityGradient: {
    flexDirection: 'row',
    padding: 20,
    gap: 16,
  },
  zeroGravityContent: {
    flex: 1,
  },
  zeroGravityTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  zeroGravityText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    lineHeight: 20,
    marginBottom: 8,
  },
  zeroGravityBenefit: {
    fontSize: 14,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.9)',
  },
});

