/**
 * Zero-Gravity Migration Component
 * Active Arbitrage Desk for Debt Migration Strategy
 */

import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from 'react-native-vector-icons/Feather';
import { CreditSnapshot } from '../types/CreditTypes';
import {
  findBestMigrationCard,
  calculateMigrationValue,
  generateMigrationChecklist,
  shouldConsiderMigration,
  ZeroGravityCard,
} from '../services/DebtMigrationService';
import {
  calculateBurnDownSchedule,
  calculateOptimalPayment,
  BurnDownSchedule,
} from '../services/BurnDownService';

interface ZeroGravityMigrationProps {
  snapshot: CreditSnapshot;
  onClose?: () => void;
}

export const ZeroGravityMigration: React.FC<ZeroGravityMigrationProps> = ({
  snapshot,
  onClose,
}) => {
  const [selectedStrategy, setSelectedStrategy] = useState<'max_time' | 'debt_payoff' | 'purchases' | 'fee_averse' | 'best_roi'>('best_roi');
  const [checklistItems, setChecklistItems] = useState<Array<{ id: string; completed: boolean }>>([]);
  const [showBurnDown, setShowBurnDown] = useState(false);
  
  // Check if migration makes sense
  const migrationCheck = useMemo(() => shouldConsiderMigration(snapshot), [snapshot]);
  
  // Find best card
  const bestCard = useMemo(() => {
    if (!migrationCheck.shouldMigrate) return null;
    const currentAPR = 0.24; // In production, get from actual card data
    return findBestMigrationCard(snapshot.utilization.totalBalance, currentAPR, selectedStrategy);
  }, [snapshot, selectedStrategy, migrationCheck]);
  
  // Calculate burn-down schedule
  const burnDownSchedule = useMemo<BurnDownSchedule | null>(() => {
    if (!bestCard) return null;
    
    const balance = snapshot.utilization.totalBalance;
    const optimalPayment = calculateOptimalPayment(balance, bestCard.card.promoMonths, 'moderate');
    
    return calculateBurnDownSchedule(snapshot, optimalPayment, 'moderate');
  }, [bestCard, snapshot]);
  
  // Generate checklist
  const checklist = useMemo(() => {
    if (!bestCard) return [];
    const sourceCardId = snapshot.cards[0]?.id || '';
    return generateMigrationChecklist(sourceCardId, bestCard.card, snapshot);
  }, [bestCard, snapshot]);
  
  // Initialize checklist state
  React.useEffect(() => {
    if (checklist.length > 0 && checklistItems.length === 0) {
      setChecklistItems(checklist.map(item => ({ id: item.id, completed: item.completed })));
    }
  }, [checklist]);
  
  const toggleChecklistItem = (id: string) => {
    setChecklistItems(prev =>
      prev.map(item =>
        item.id === id ? { ...item, completed: !item.completed } : item
      )
    );
  };
  
  const allCriticalItemsCompleted = checklist
    .filter(item => item.critical)
    .every(item => checklistItems.find(ci => ci.id === item.id)?.completed);
  
  if (!migrationCheck.shouldMigrate) {
    return (
      <View style={styles.container}>
        <LinearGradient
          colors={['rgba(102,126,234,0.1)', 'rgba(118,75,162,0.1)']}
          style={styles.infoCard}
        >
          <Icon name="info" size={24} color="#667eea" />
          <Text style={styles.infoText}>
            {migrationCheck.reason || 'Your current interest costs are below the migration threshold.'}
          </Text>
          <Text style={styles.infoSubtext}>
            Monthly Interest: ${migrationCheck.monthlyInterestLeak.toFixed(2)}/month
          </Text>
        </LinearGradient>
      </View>
    );
  }
  
  if (!bestCard) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>No suitable migration cards found for your balance.</Text>
      </View>
    );
  }
  
  const migrationValue = bestCard.value;
  const completedCount = checklistItems.filter(item => item.completed).length;
  const totalItems = checklist.length;
  
  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Strategy Selection */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Choose Your Strategy</Text>
        <View style={styles.strategyGrid}>
          {(['best_roi', 'max_time', 'debt_payoff', 'fee_averse'] as const).map((strategy) => (
            <TouchableOpacity
              key={strategy}
              style={[
                styles.strategyButton,
                selectedStrategy === strategy && styles.strategyButtonActive,
              ]}
              onPress={() => setSelectedStrategy(strategy)}
            >
              <Text style={[
                styles.strategyText,
                selectedStrategy === strategy && styles.strategyTextActive,
              ]}>
                {strategy === 'best_roi' ? 'Best ROI' :
                 strategy === 'max_time' ? 'Max Time' :
                 strategy === 'debt_payoff' ? 'Payoff' :
                 'Fee-Averse'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
      
      {/* Oracle's Choice Card */}
      <View style={styles.section}>
        <LinearGradient
          colors={['#667eea', '#764ba2']}
          style={styles.oracleCard}
        >
          <View style={styles.oracleHeader}>
            <Icon name="zap" size={24} color="#FFFFFF" />
            <Text style={styles.oracleTitle}>Oracle's Choice</Text>
          </View>
          <Text style={styles.cardName}>{bestCard.card.name}</Text>
          <Text style={styles.cardIssuer}>{bestCard.card.issuer}</Text>
          
          <View style={styles.cardStats}>
            <View style={styles.statBox}>
              <Text style={styles.statLabel}>0% APR Period</Text>
              <Text style={styles.statValue}>{bestCard.card.promoMonths} months</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statLabel}>Transfer Fee</Text>
              <Text style={styles.statValue}>{(bestCard.card.transferFee * 100).toFixed(0)}%</Text>
            </View>
          </View>
          
          {bestCard.card.cashback && (
            <View style={styles.cashbackBadge}>
              <Icon name="gift" size={16} color="#FFD700" />
              <Text style={styles.cashbackText}>
                {(bestCard.card.cashback * 100).toFixed(1)}% Cashback
              </Text>
            </View>
          )}
        </LinearGradient>
      </View>
      
      {/* Net Savings Calculation */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Strategic Migration Value</Text>
        <View style={styles.savingsCard}>
          <View style={styles.savingsRow}>
            <Text style={styles.savingsLabel}>Monthly Interest Leak</Text>
            <Text style={styles.savingsValue}>
              ${migrationCheck.monthlyInterestLeak.toFixed(2)}/mo
            </Text>
          </View>
          <View style={styles.savingsRow}>
            <Text style={styles.savingsLabel}>Interest Avoided ({bestCard.card.promoMonths} mo)</Text>
            <Text style={styles.savingsValue}>
              ${migrationValue.totalInterestAvoided.toFixed(2)}
            </Text>
          </View>
          <View style={styles.savingsRow}>
            <Text style={styles.savingsLabel}>Transfer Fee</Text>
            <Text style={[styles.savingsValue, styles.savingsNegative]}>
              -${migrationValue.transferFee.toFixed(2)}
            </Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.savingsRow}>
            <Text style={styles.savingsLabelBold}>Net Savings</Text>
            <Text style={styles.savingsValueBold}>
              ${migrationValue.netSavings.toFixed(2)}
            </Text>
          </View>
          <View style={styles.roiBadge}>
            <Icon name="trending-up" size={20} color="#34C759" />
            <Text style={styles.roiText}>
              {migrationValue.roiPercent.toFixed(0)}% Guaranteed Return
            </Text>
          </View>
        </View>
      </View>
      
      {/* Zero-Gravity Guardrails Checklist */}
      <View style={styles.section}>
        <View style={styles.checklistHeader}>
          <Icon name="shield" size={20} color="#FF9500" />
          <Text style={styles.sectionTitle}>Zero-Gravity Guardrails</Text>
        </View>
        <Text style={styles.checklistSubtitle}>
          Complete these steps to protect your 0% APR deal
        </Text>
        
        <View style={styles.checklistProgress}>
          <Text style={styles.progressText}>
            {completedCount} of {totalItems} completed
          </Text>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${(completedCount / totalItems) * 100}%` },
              ]}
            />
          </View>
        </View>
        
        {checklist.map((item) => {
          const checklistItem = checklistItems.find(ci => ci.id === item.id);
          const isCompleted = checklistItem?.completed || false;
          
          return (
            <TouchableOpacity
              key={item.id}
              style={[
                styles.checklistItem,
                item.critical && styles.checklistItemCritical,
                isCompleted && styles.checklistItemCompleted,
              ]}
              onPress={() => toggleChecklistItem(item.id)}
            >
              <View style={styles.checklistIcon}>
                {isCompleted ? (
                  <Icon name="check-circle" size={24} color="#34C759" />
                ) : (
                  <Icon name="circle" size={24} color={item.critical ? "#FF3B30" : "#8E8E93"} />
                )}
              </View>
              <View style={styles.checklistContent}>
                <View style={styles.checklistTitleRow}>
                  <Text style={[
                    styles.checklistTitle,
                    isCompleted && styles.checklistTitleCompleted,
                  ]}>
                    {item.title}
                  </Text>
                  {item.critical && (
                    <View style={styles.criticalBadge}>
                      <Text style={styles.criticalText}>CRITICAL</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.checklistDescription}>
                  {item.description}
                </Text>
              </View>
            </TouchableOpacity>
          );
        })}
        
        {allCriticalItemsCompleted && (
          <View style={styles.successCard}>
            <LinearGradient
              colors={['#34C759', '#2E9E4B']}
              style={styles.successGradient}
            >
              <Icon name="check-circle" size={24} color="#FFFFFF" />
              <Text style={styles.successText}>
                All critical guardrails activated! You're protected.
              </Text>
            </LinearGradient>
          </View>
        )}
      </View>
      
      {/* Burn-Down Schedule */}
      {burnDownSchedule && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recovery Roadmap</Text>
            <TouchableOpacity
              onPress={() => setShowBurnDown(!showBurnDown)}
              style={styles.toggleButton}
            >
              <Text style={styles.toggleText}>
                {showBurnDown ? 'Hide' : 'Show'} Timeline
              </Text>
              <Icon
                name={showBurnDown ? "chevron-up" : "chevron-down"}
                size={16}
                color="#007AFF"
              />
            </TouchableOpacity>
          </View>
          
          {showBurnDown && (
            <View style={styles.burnDownContainer}>
              {/* Summary Stats */}
              <View style={styles.summaryCard}>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Target Date</Text>
                  <Text style={styles.summaryValue}>
                    {new Date(burnDownSchedule.targetDate).toLocaleDateString('en-US', {
                      month: 'short',
                      year: 'numeric',
                    })}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Final Score</Text>
                  <Text style={styles.summaryValue}>{burnDownSchedule.finalScore}</Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Total Interest Saved</Text>
                  <Text style={styles.summaryValue}>
                    ${burnDownSchedule.totalInterestSaved.toFixed(2)}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Monthly Payment</Text>
                  <Text style={styles.summaryValue}>
                    ${burnDownSchedule.monthlyPayment.toFixed(0)}/mo
                  </Text>
                </View>
              </View>
              
              {/* Month-by-Month Timeline */}
              {burnDownSchedule.months.map((month, index) => (
                <View key={month.month} style={styles.monthCard}>
                  <View style={styles.monthHeader}>
                    <View style={styles.monthNumber}>
                      <Text style={styles.monthNumberText}>{month.month}</Text>
                    </View>
                    <View style={styles.monthInfo}>
                      <Text style={styles.monthLabel}>{month.monthLabel}</Text>
                      <View style={styles.monthStats}>
                        <Text style={styles.monthBalance}>
                          Balance: ${month.balance.toFixed(0)}
                        </Text>
                        <Text style={[
                          styles.monthScore,
                          month.scoreChange >= 0 ? styles.scorePositive : styles.scoreNegative,
                        ]}>
                          Score: {month.score} ({month.scoreChange >= 0 ? '+' : ''}{month.scoreChange})
                        </Text>
                      </View>
                    </View>
                  </View>
                  
                  {month.milestone && (
                    <View style={[
                      styles.milestoneCard,
                      month.milestone.type === 'debt_free' && styles.milestoneCardVictory,
                    ]}>
                      <Icon
                        name={
                          month.milestone.type === 'debt_free' ? "award" :
                          month.milestone.type === 'elite' ? "star" :
                          month.milestone.type === 'halfway' ? "target" :
                          "trending-up"
                        }
                        size={20}
                        color={
                          month.milestone.type === 'debt_free' ? "#FFD700" :
                          month.milestone.type === 'elite' ? "#5AC8FA" :
                          "#34C759"
                        }
                      />
                      <View style={styles.milestoneContent}>
                        <Text style={styles.milestoneTitle}>
                          {month.milestone.type === 'debt_free' ? '🎉 VICTORY!' :
                           month.milestone.type === 'elite' ? '⭐ Elite Status' :
                           month.milestone.type === 'halfway' ? '🎯 Halfway Milestone' :
                           '📈 Behavioral Alpha'}
                        </Text>
                        <Text style={styles.milestoneMessage}>
                          {month.milestone.message}
                        </Text>
                        <Text style={styles.milestoneBoost}>
                          Score Boost: +{month.milestone.scoreBoost} points
                        </Text>
                      </View>
                    </View>
                  )}
                  
                  <View style={styles.monthFooter}>
                    <Text style={styles.monthUtilization}>
                      Utilization: {month.utilization.toFixed(1)}%
                    </Text>
                    <Text style={styles.monthInterest}>
                      Interest Saved: ${month.cumulativeInterestSaved.toFixed(2)}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>
      )}
      
      {/* Strategy Summary */}
      {burnDownSchedule && (
        <View style={styles.section}>
          <LinearGradient
            colors={['#1a1a2e', '#16213e']}
            style={styles.strategySummaryCard}
          >
            <Text style={styles.strategySummaryTitle}>Oracle Mission Summary</Text>
            <Text style={styles.strategySummarySubtitle}>Project Phoenix</Text>
            
            <View style={styles.missionStats}>
              <View style={styles.missionStat}>
                <Text style={styles.missionLabel}>Target Date</Text>
                <Text style={styles.missionValue}>
                  {new Date(burnDownSchedule.targetDate).toLocaleDateString('en-US', {
                    month: 'long',
                    year: 'numeric',
                  })}
                </Text>
              </View>
              <View style={styles.missionStat}>
                <Text style={styles.missionLabel}>Total Interest Erased</Text>
                <Text style={styles.missionValue}>
                  ${burnDownSchedule.totalInterestSaved.toFixed(2)}
                </Text>
              </View>
              <View style={styles.missionStat}>
                <Text style={styles.missionLabel}>Credit Tier Jump</Text>
                <Text style={styles.missionValue}>
                  {snapshot.score.scoreRange} → {getScoreRange(burnDownSchedule.finalScore)}
                </Text>
              </View>
              {burnDownSchedule.totalMonths >= 14 && (
                <View style={styles.missionStat}>
                  <Text style={styles.missionLabel}>Next Opportunity</Text>
                  <Text style={styles.missionValue}>
                    Prime Mortgage Rate eligible by Month 14
                  </Text>
                </View>
              )}
            </View>
          </LinearGradient>
        </View>
      )}
      
      <View style={{ height: 40 }} />
    </ScrollView>
  );
};

const getScoreRange = (score: number): string => {
  if (score >= 800) return 'Excellent';
  if (score >= 740) return 'Very Good';
  if (score >= 670) return 'Good';
  if (score >= 580) return 'Fair';
  return 'Poor';
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  section: {
    padding: 20,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 12,
    margin: 20,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#1C1C1E',
    lineHeight: 20,
  },
  infoSubtext: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4,
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
    textAlign: 'center',
    padding: 20,
  },
  strategyGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  strategyButton: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  strategyButtonActive: {
    borderColor: '#667eea',
    borderWidth: 2,
    backgroundColor: '#F0F4FF',
  },
  strategyText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  strategyTextActive: {
    color: '#667eea',
  },
  oracleCard: {
    borderRadius: 16,
    padding: 20,
  },
  oracleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  oracleTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  cardName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  cardIssuer: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 16,
  },
  cardStats: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 12,
  },
  statBox: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 8,
    padding: 12,
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  cashbackBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255,215,0,0.3)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    gap: 6,
  },
  cashbackText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  savingsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  savingsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  savingsLabel: {
    fontSize: 14,
    color: '#636366',
  },
  savingsValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  savingsNegative: {
    color: '#FF3B30',
  },
  savingsLabelBold: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  savingsValueBold: {
    fontSize: 24,
    fontWeight: '700',
    color: '#34C759',
  },
  divider: {
    height: 1,
    backgroundColor: '#E5E5EA',
    marginVertical: 12,
  },
  roiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderRadius: 12,
    marginTop: 12,
    gap: 8,
  },
  roiText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#34C759',
  },
  checklistHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  checklistSubtitle: {
    fontSize: 14,
    color: '#636366',
    marginBottom: 16,
  },
  checklistProgress: {
    marginBottom: 16,
  },
  progressText: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 8,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#34C759',
    borderRadius: 4,
  },
  checklistItem: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  checklistItemCritical: {
    borderColor: '#FF9500',
    borderWidth: 2,
  },
  checklistItemCompleted: {
    opacity: 0.7,
    backgroundColor: '#F8F9FA',
  },
  checklistIcon: {
    marginRight: 12,
  },
  checklistContent: {
    flex: 1,
  },
  checklistTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
    gap: 8,
  },
  checklistTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    flex: 1,
  },
  checklistTitleCompleted: {
    textDecorationLine: 'line-through',
  },
  checklistDescription: {
    fontSize: 14,
    color: '#636366',
    lineHeight: 20,
  },
  criticalBadge: {
    backgroundColor: '#FF9500',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  criticalText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  successCard: {
    borderRadius: 12,
    overflow: 'hidden',
    marginTop: 16,
  },
  successGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  successText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  toggleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#F0F0F0',
  },
  toggleText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  burnDownContainer: {
    marginTop: 16,
  },
  summaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#636366',
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  monthCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#667eea',
  },
  monthHeader: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  monthNumber: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#667eea',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  monthNumberText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  monthInfo: {
    flex: 1,
  },
  monthLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  monthStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  monthBalance: {
    fontSize: 14,
    color: '#636366',
  },
  monthScore: {
    fontSize: 14,
    fontWeight: '600',
  },
  scorePositive: {
    color: '#34C759',
  },
  scoreNegative: {
    color: '#FF3B30',
  },
  milestoneCard: {
    flexDirection: 'row',
    backgroundColor: '#F0F4FF',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    gap: 12,
  },
  milestoneCardVictory: {
    backgroundColor: '#FFF8E1',
  },
  milestoneContent: {
    flex: 1,
  },
  milestoneTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  milestoneMessage: {
    fontSize: 14,
    color: '#636366',
    marginBottom: 4,
  },
  milestoneBoost: {
    fontSize: 12,
    fontWeight: '600',
    color: '#667eea',
  },
  monthFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  monthUtilization: {
    fontSize: 12,
    color: '#8E8E93',
  },
  monthInterest: {
    fontSize: 12,
    fontWeight: '600',
    color: '#34C759',
  },
  strategySummaryCard: {
    borderRadius: 16,
    padding: 24,
  },
  strategySummaryTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  strategySummarySubtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 20,
  },
  missionStats: {
    gap: 16,
  },
  missionStat: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.2)',
  },
  missionLabel: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
  },
  missionValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});

