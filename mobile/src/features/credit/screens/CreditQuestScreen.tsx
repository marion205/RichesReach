/**
 * Credit Quest Screen - "Freedom Canvas"
 * Single-screen experience for credit building (Jobs-level simplicity)
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import { CreditScoreOrb } from '../components/CreditScoreOrb';
import { CreditUtilizationGauge } from '../components/CreditUtilizationGauge';
import { CreditScoreTrendChart } from '../components/CreditScoreTrendChart';
import { StatementDatePlanner } from '../components/StatementDatePlanner';
import ScoreSimulator from '../components/ScoreSimulator';
import { CreditShield } from '../components/CreditShield';
import { AutopilotMode } from '../components/AutopilotMode';
import { CreditTwinSimulator } from '../components/CreditTwinSimulator';
import { EcosystemPerks } from '../components/EcosystemPerks';
import { CreditOracle } from '../components/CreditOracle';
import { SustainabilityLayer } from '../components/SustainabilityLayer';
import { creditScoreService } from '../services/CreditScoreService';
import { creditUtilizationService } from '../services/CreditUtilizationService';
import { creditNotificationService } from '../services/CreditNotificationService';
import { scoreSimulatorService } from '../services/ScoreSimulatorService';
import { 
  CreditSnapshot, 
  CreditAction, 
  CreditScore, 
  StatementDatePlan, 
  CreditShieldPlan,
  AutopilotStatus,
  CreditTwinState,
  CreditTwinScenario,
  EcosystemIntegration,
  CreditOracle as CreditOracleType,
  SustainabilityTracking,
} from '../types/CreditTypes';

interface CreditQuestScreenProps {
  visible: boolean;
  onClose: () => void;
}

export const CreditQuestScreen: React.FC<CreditQuestScreenProps> = ({
  visible,
  onClose,
}) => {
  const insets = useSafeAreaInsets();
  const [loading, setLoading] = useState(true);
  const [snapshot, setSnapshot] = useState<CreditSnapshot | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [scoreHistory, setScoreHistory] = useState<CreditScore[]>([]);
  const [showTrends, setShowTrends] = useState(false);
  const [statementPlans, setStatementPlans] = useState<StatementDatePlan[]>([]);
  const [shieldPlan, setShieldPlan] = useState<CreditShieldPlan | null>(null);
  const [autopilotStatus, setAutopilotStatus] = useState<AutopilotStatus>({
    enabled: false,
    currentWeek: {
      weekStart: new Date().toISOString(),
      weekEnd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      selectedActions: [],
      completedActions: [],
      progress: 0,
    },
    weeklyHistory: [],
    streak: 0,
    totalActionsCompleted: 0,
  });
  const [creditTwinState, setCreditTwinState] = useState<CreditTwinState>({
    baseScore: 580,
    scenarioHistory: [],
    projectedScore: 580,
  });
  const [ecosystemIntegration, setEcosystemIntegration] = useState<EcosystemIntegration>({
    perks: [],
    unlockedPerks: [],
    availablePerks: [],
    totalSavings: 0,
  });
  const [creditOracle, setCreditOracle] = useState<CreditOracleType>({
    insights: [],
    localTrends: [],
    warnings: [],
    opportunities: [],
    lastUpdated: new Date().toISOString(),
  });
  const [sustainabilityTracking, setSustainabilityTracking] = useState<SustainabilityTracking>({
    totalImpact: {
      treesPlanted: 0,
      co2Offset: 0,
      actionsCompleted: 0,
      milestones: [],
    },
    weeklyImpact: {
      treesPlanted: 0,
      co2Offset: 0,
      actionsCompleted: 0,
      milestones: [],
    },
    goals: [],
    partnerIntegrations: [],
  });

  useEffect(() => {
    if (visible) {
      loadSnapshot();
    }
  }, [visible]);

  const loadSnapshot = async () => {
    try {
      setLoading(true);
      // getSnapshot() now returns fallback data on error, so it won't throw
      const data = await creditScoreService.getSnapshot();
      setSnapshot(data);
      
      // Initialize Credit Twin with current score
      setCreditTwinState({
        baseScore: data.score?.score || 580,
        scenarioHistory: [],
        projectedScore: data.score?.score || 580,
      });
      
      // Initialize mock ecosystem perks
      setEcosystemIntegration({
        perks: [
          {
            id: '1',
            name: 'Eco-Friendly Discount',
            description: '10% off sustainable products',
            category: 'discount',
            unlockRequirement: { type: 'utilization_target', value: 30 },
            partner: 'Amazon',
            discount: 10,
          },
          {
            id: '2',
            name: 'Premium Event Access',
            description: 'Priority access to financial wellness events',
            category: 'access',
            unlockRequirement: { type: 'score_threshold', value: 700 },
            partner: 'RichesReach',
          },
        ],
        unlockedPerks: [],
        availablePerks: ['1'],
        totalSavings: 0,
      });
      
      // Initialize mock oracle insights
      setCreditOracle({
        insights: [
          {
            id: '1',
            type: 'trend',
            title: 'Q4 Score Drops Expected',
            description: 'Historical data shows 15% of users see score drops in Q4 due to holiday spending',
            confidence: 0.75,
            timeHorizon: 'Q4 2025',
            source: 'crowdsourced',
            recommendation: 'Plan ahead: reduce utilization before November',
          },
        ],
        localTrends: [],
        warnings: [],
        opportunities: [],
        lastUpdated: new Date().toISOString(),
      });
      
      // Initialize sustainability tracking
      setSustainabilityTracking({
        totalImpact: {
          treesPlanted: 12,
          co2Offset: 2.4,
          actionsCompleted: 8,
          milestones: [
            { id: '1', name: 'First Tree Planted', date: new Date().toISOString(), impact: 1 },
          ],
        },
        weeklyImpact: {
          treesPlanted: 2,
          co2Offset: 0.4,
          actionsCompleted: 1,
          milestones: [],
        },
        goals: [
          { id: '1', name: 'Plant 50 Trees', target: 50, current: 12, unit: 'trees' },
          { id: '2', name: 'Offset 10kg CO₂', target: 10, current: 2.4, unit: 'co2_kg' },
        ],
        partnerIntegrations: [
          { name: 'Tree-Nation', type: 'tree_planting', contribution: 10 },
          { name: 'Carbon Offset Co', type: 'carbon_offset', contribution: 2.4 },
        ],
      });
      
      // Generate statement-date plans from cards
      if (data.cards && data.cards.length > 0) {
        const plans: StatementDatePlan[] = data.cards.map((card, index) => {
          const statementCloseDate = new Date();
          statementCloseDate.setDate(statementCloseDate.getDate() + (7 + index * 3)); // Stagger dates
          const paymentDueDate = new Date(statementCloseDate);
          paymentDueDate.setDate(paymentDueDate.getDate() + 21); // 21 days after statement
          
          const daysUntilClose = Math.ceil((statementCloseDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
          const targetUtilization = 0.09; // 9% optimal
          const currentBalance = card.balance;
          const targetBalance = card.limit * targetUtilization;
          const recommendedPaydown = Math.max(0, currentBalance - targetBalance);
          
          return {
            cardId: card.id,
            cardName: card.name,
            currentBalance,
            limit: card.limit,
            currentUtilization: card.utilization,
            statementCloseDate: statementCloseDate.toISOString(),
            paymentDueDate: paymentDueDate.toISOString(),
            recommendedPaydown,
            targetUtilization,
            daysUntilClose,
            projectedScoreGain: recommendedPaydown > 0 ? Math.round(recommendedPaydown / 100) : 0,
          };
        });
        setStatementPlans(plans);
      }
      
      // Generate shield plan
      if (data.cards && data.cards.length > 0) {
        const upcomingPayments = data.cards
          .filter(card => card.paymentDueDate)
          .map(card => {
            const dueDate = new Date(card.paymentDueDate!);
            const daysUntilDue = Math.ceil((dueDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
            let riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' = 'LOW';
            if (daysUntilDue <= 3) riskLevel = 'HIGH';
            else if (daysUntilDue <= 7) riskLevel = 'MEDIUM';
            
            return {
              cardName: card.name,
              dueDate: card.paymentDueDate!,
              minimumPayment: card.minimumPayment || card.balance * 0.02,
              daysUntilDue,
              riskLevel,
            };
          });
        
        const totalMinimum = upcomingPayments.reduce((sum, p) => sum + p.minimumPayment, 0);
        const overallRisk = upcomingPayments.some(p => p.riskLevel === 'HIGH') ? 'HIGH' :
                           upcomingPayments.some(p => p.riskLevel === 'MEDIUM') ? 'MEDIUM' : 'LOW';
        
        const recommendations: string[] = [];
        if (overallRisk === 'HIGH') {
          recommendations.push('Set up autopay immediately to avoid late fees');
        }
        if (totalMinimum > 0) {
          recommendations.push(`Ensure $${totalMinimum.toFixed(0)} is available for minimum payments`);
        }
        if (upcomingPayments.length > 0) {
          recommendations.push('Review payment due dates and set reminders');
        }
        
        setShieldPlan({
          riskLevel: overallRisk,
          totalMinimumPayments: totalMinimum,
          upcomingPayments,
          safetyBuffer: totalMinimum * 1.5, // 1.5x buffer
          recommendations,
        });
      }
      
      // Load score history for trends
      try {
        // In production, fetch historical scores from API
        // For now, create mock history from current score
        const currentScore = data.score;
        if (currentScore && typeof currentScore.score === 'number') {
          const history: CreditScore[] = [];
          for (let i = 5; i >= 0; i--) {
            const date = new Date();
            date.setMonth(date.getMonth() - i);
            history.push({
              score: currentScore.score - (i * 5), // Mock progression
              scoreRange: currentScore.scoreRange || 'Fair',
              lastUpdated: date.toISOString(),
              provider: currentScore.provider || 'self_reported',
              factors: currentScore.factors,
            });
          }
          setScoreHistory(history);
        } else {
          // Fallback: create mock history with default values
          const history: CreditScore[] = [];
          for (let i = 5; i >= 0; i--) {
            const date = new Date();
            date.setMonth(date.getMonth() - i);
            history.push({
              score: 580 - (i * 5),
              scoreRange: 'Fair',
              lastUpdated: date.toISOString(),
              provider: 'self_reported',
            });
          }
          setScoreHistory(history);
        }
      } catch (error) {
        console.warn('[CreditQuest] Failed to load score history:', error);
        // Set empty history on error
        setScoreHistory([]);
      }
      
      // Schedule payment reminders
      if (data.cards && data.cards.length > 0) {
        for (const card of data.cards) {
          if (card.paymentDueDate) {
            const dueDate = new Date(card.paymentDueDate);
            await creditNotificationService.schedulePaymentReminder(
              card.name,
              dueDate,
              3
            );
          }
          
          // Schedule utilization alerts if high
          if (card.utilization > 0.5) {
            await creditNotificationService.scheduleUtilizationAlert(
              card.name,
              card.utilization
            );
          }
        }
      }
    } catch (error) {
      console.error('[CreditQuest] Failed to load snapshot:', error);
      // Don't show error alert - the service now provides fallback data
      // The snapshot will be set with fallback data from the service
      // Only show alert if snapshot is still null after fallback
      if (!snapshot) {
        Alert.alert(
          'Notice',
          'Using demo credit data. Connect to backend for real-time updates.',
          [{ text: 'OK' }]
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadSnapshot();
    setRefreshing(false);
  };

  const handlePrimaryAction = () => {
    if (!snapshot) return;
    
    const topAction = snapshot.actions.find(a => !a.completed);
    if (topAction) {
      Alert.alert(
        topAction.title,
        topAction.description,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Complete', 
            onPress: () => {
              // In production, mark action as completed via API
              Alert.alert('Success', 'Action completed! Your credit score may improve.');
              loadSnapshot();
            }
          }
        ]
      );
    } else {
      Alert.alert(
        'Great Job!',
        'You\'re on track with your credit building journey.',
        [{ text: 'OK' }]
      );
    }
  };

  if (!visible) return null;

  // Ensure snapshot has valid score before rendering
  if (!snapshot || !snapshot.score) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Credit Quest</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading credit data...</Text>
        </View>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Credit Quest</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading your credit journey...</Text>
        </View>
      </View>
    );
  }

  if (!snapshot) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Credit Quest</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
        <View style={styles.emptyContainer}>
          <Icon name="credit-card" size={64} color="#8E8E93" />
          <Text style={styles.emptyTitle}>Start Your Credit Journey</Text>
          <Text style={styles.emptySubtitle}>
            Link a credit card to begin building your credit score
          </Text>
          <TouchableOpacity 
            style={styles.primaryButton}
            onPress={handlePrimaryAction}
          >
            <Text style={styles.primaryButtonText}>Get Started</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const topAction = snapshot.actions.find(a => !a.completed);
  const utilization = snapshot.utilization;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Credit Quest</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={handleRefresh} style={styles.refreshButton}>
            <Icon 
              name="refresh-cw" 
              size={20} 
              color={refreshing ? "#007AFF" : "#8E8E93"} 
            />
          </TouchableOpacity>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Credit Score Orb */}
        <View style={styles.orbSection}>
          <CreditScoreOrb 
            score={snapshot?.score || undefined}
            projection={snapshot?.projection}
          />
        </View>

        {/* This Month Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>This Month</Text>
          <CreditUtilizationGauge utilization={utilization} />
          
          {/* Score Simulator Trigger */}
          {snapshot.score && (
            <View style={styles.simulatorContainer}>
              <ScoreSimulator
                currentScore={snapshot.score.score || 580}
                onSimulate={(inputs) => scoreSimulatorService.simulateScore(
                  snapshot.score?.score || 580,
                  inputs
                )}
              />
            </View>
          )}
        </View>

        {/* Credit Shield */}
        {shieldPlan && (
          <View style={styles.section}>
            <CreditShield plan={shieldPlan} />
          </View>
        )}

        {/* Statement-Date Planner */}
        {statementPlans.length > 0 && (
          <View style={styles.section}>
            <StatementDatePlanner plans={statementPlans} />
          </View>
        )}

        {/* Top Action - Enhanced with Beginner-Friendly Coaching */}
        {topAction && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Your #1 Move This Month</Text>
            <View style={styles.coachingBox}>
              <Text style={styles.coachingText}>
                {topAction.description}
              </Text>
              <Text style={styles.coachingImpact}>
                Expected impact: {topAction.projectedScoreGain ? `+${topAction.projectedScoreGain} points` : 'Small to medium'} within 1-2 cycles
              </Text>
            </View>
            <TouchableOpacity 
              style={styles.primaryButton}
              onPress={handlePrimaryAction}
            >
              <Icon name="check-circle" size={20} color="#FFFFFF" />
              <Text style={styles.primaryButtonText}>{topAction.title}</Text>
            </TouchableOpacity>
            {topAction.projectedScoreGain && (
              <Text style={styles.actionProjection}>
                → +{topAction.projectedScoreGain} points in 3 months
              </Text>
            )}
          </View>
        )}

        {/* Shield Alerts */}
        {snapshot.shield && snapshot.shield.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Alerts</Text>
            {snapshot.shield.map((alert, index) => (
              <View key={index} style={styles.shieldAlert}>
                <Icon 
                  name="shield" 
                  size={20} 
                  color={alert.type === 'PAYMENT_DUE' ? '#FF9500' : '#FF3B30'} 
                />
                <View style={styles.shieldContent}>
                  <Text style={styles.shieldMessage}>{alert.message}</Text>
                  <Text style={styles.shieldSuggestion}>{alert.suggestion}</Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Actions List */}
        {snapshot.actions.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Your Actions</Text>
            {snapshot.actions.map((action) => (
              <View 
                key={action.id} 
                style={[
                  styles.actionCard,
                  action.completed && styles.actionCardCompleted
                ]}
              >
                <Icon 
                  name={action.completed ? "check-circle" : "circle"} 
                  size={20} 
                  color={action.completed ? "#34C759" : "#8E8E93"} 
                />
                <View style={styles.actionContent}>
                  <Text style={styles.actionTitle}>{action.title}</Text>
                  <Text style={styles.actionDescription}>{action.description}</Text>
                  {action.projectedScoreGain && (
                    <Text style={styles.actionGain}>
                      +{action.projectedScoreGain} points
                    </Text>
                  )}
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Autopilot Mode */}
        <View style={styles.section}>
          <AutopilotMode
            status={autopilotStatus}
            availableActions={snapshot.actions}
            onToggle={(enabled) => {
              setAutopilotStatus(prev => ({ ...prev, enabled }));
            }}
            onCompleteAction={(actionId) => {
              setAutopilotStatus(prev => {
                const newCompleted = [...prev.currentWeek.completedActions, actionId];
                const progress = (newCompleted.length / prev.currentWeek.selectedActions.length) * 100;
                return {
                  ...prev,
                  currentWeek: {
                    ...prev.currentWeek,
                    completedActions: newCompleted,
                    progress,
                  },
                  totalActionsCompleted: prev.totalActionsCompleted + 1,
                };
              });
            }}
            onSelectActions={(actions) => {
              setAutopilotStatus(prev => ({
                ...prev,
                currentWeek: {
                  ...prev.currentWeek,
                  selectedActions: actions,
                },
              }));
            }}
          />
        </View>

        {/* Credit Twin Simulator */}
        <View style={styles.section}>
          <CreditTwinSimulator
            initialState={creditTwinState}
            scenarios={[
              {
                id: '1',
                name: 'Miss a Payment',
                description: 'What happens if you miss a credit card payment?',
                inputs: { paymentMissed: true },
                projectedOutcome: {
                  scoreChange: -50,
                  timeToImpact: '1-2 cycles',
                  factors: ['Payment history drops significantly'],
                },
              },
              {
                id: '2',
                name: 'Take a Solar Loan',
                description: 'How does a $20k solar panel loan affect your score?',
                inputs: { loanAmount: 20000, loanType: 'solar' },
                projectedOutcome: {
                  scoreChange: -15,
                  timeToImpact: '3-6 months',
                  factors: ['New account inquiry', 'Credit mix improvement'],
                },
              },
              {
                id: '3',
                name: 'Reduce Utilization to 9%',
                description: 'Pay down all cards to optimal utilization',
                inputs: { utilizationChange: -30 },
                projectedOutcome: {
                  scoreChange: 25,
                  timeToImpact: '1-2 cycles',
                  factors: ['Utilization optimization'],
                },
              },
            ]}
            onScenarioSelect={(scenario) => {
              setCreditTwinState(prev => ({
                ...prev,
                currentScenario: scenario,
                scenarioHistory: [...prev.scenarioHistory, scenario],
                projectedScore: Math.max(300, Math.min(850, prev.projectedScore + scenario.projectedOutcome.scoreChange)),
              }));
            }}
            onReset={() => {
              setCreditTwinState({
                baseScore: snapshot.score?.score || 580,
                scenarioHistory: [],
                projectedScore: snapshot.score?.score || 580,
              });
            }}
          />
        </View>

        {/* Ecosystem Perks */}
        {ecosystemIntegration.perks.length > 0 && (
          <View style={styles.section}>
            <EcosystemPerks
              integration={ecosystemIntegration}
              onRedeemPerk={(perkId) => {
                Alert.alert('Redeem Perk', `Redirecting to redeem ${perkId}...`);
              }}
            />
          </View>
        )}

        {/* Credit Oracle */}
        {creditOracle.insights.length > 0 && (
          <View style={styles.section}>
            <CreditOracle
              oracle={creditOracle}
              onInsightPress={(insight) => {
                Alert.alert(insight.title, insight.recommendation);
              }}
            />
          </View>
        )}

        {/* Sustainability Layer */}
        <View style={styles.section}>
          <SustainabilityLayer
            tracking={sustainabilityTracking}
            onViewDetails={() => {
              Alert.alert('Impact Report', 'Full sustainability impact report coming soon!');
            }}
          />
        </View>
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  headerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  refreshButton: {
    padding: 4,
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 16,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 24,
  },
  orbSection: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 8,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  actionProjection: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginTop: 8,
  },
  shieldAlert: {
    flexDirection: 'row',
    backgroundColor: '#FFF8E1',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 12,
  },
  shieldContent: {
    flex: 1,
  },
  shieldMessage: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  shieldSuggestion: {
    fontSize: 12,
    color: '#8E8E93',
  },
  actionCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionCardCompleted: {
    opacity: 0.6,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  actionDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  actionGain: {
    fontSize: 12,
    color: '#34C759',
    fontWeight: '600',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  trendToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    padding: 8,
  },
  trendToggleText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  trendSection: {
    marginTop: 16,
  },
  simulatorContainer: {
    marginTop: 16,
  },
  coachingBox: {
    backgroundColor: '#F0F8FF',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#007AFF',
  },
  coachingText: {
    fontSize: 15,
    color: '#1C1C1E',
    lineHeight: 22,
    marginBottom: 8,
  },
  coachingImpact: {
    fontSize: 13,
    color: '#007AFF',
    fontWeight: '600',
  },
});

