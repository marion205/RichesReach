/**
 * Credit Quest Screen - "Freedom Canvas"
 * Single-screen experience for credit building (Jobs-level simplicity)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Animated,
  RefreshControl,
  Dimensions,
  Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
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
import { CrystalBallSimulator } from '../components/CrystalBallSimulator';
import { ZeroGravityMigration } from '../components/ZeroGravityMigration';
import { calculateSpendingVelocity } from '../services/CrystalBallSimulatorService';
import { shouldConsiderMigration } from '../services/DebtMigrationService';
import { creditScoreService } from '../services/CreditScoreService';
import { creditUtilizationService } from '../services/CreditUtilizationService';
import { creditNotificationService } from '../services/CreditNotificationService';
import { scoreSimulatorService } from '../services/ScoreSimulatorService';
import logger from '../../../utils/logger';
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
  OracleInsight,
  SustainabilityTracking,
} from '../types/CreditTypes';

const { width } = Dimensions.get('window');

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
  const [showCrystalBall, setShowCrystalBall] = useState(false);
  const [showZeroGravity, setShowZeroGravity] = useState(false);

  // Animation values
  const fadeAnim = useState(new Animated.Value(0))[0];
  const slideAnim = useState(new Animated.Value(50))[0];

  useEffect(() => {
    if (visible) {
      loadSnapshot();
      // Entrance animation
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.spring(slideAnim, {
          toValue: 0,
          friction: 8,
          tension: 40,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      // Reset animations when closing
      fadeAnim.setValue(0);
      slideAnim.setValue(50);
    }
  }, [visible]);

  const loadSnapshot = useCallback(async () => {
    try {
      setLoading(true);
      // getSnapshot() now returns fallback data on error, so it won't throw
      const data = await creditScoreService.getSnapshot();
      setSnapshot(data);
      
      // Initialize Credit Twin with current score
      const currentScore = data.score?.score || 580;
      setCreditTwinState({
        baseScore: currentScore,
        scenarioHistory: [],
        projectedScore: currentScore,
      });
      
      // Initialize enhanced tracking data (velocity, behavioral, macro-economic)
      // In production, fetch from API; for now, calculate from available data
      
      // Calculate spending velocity if we have cycle data
      if (data.cards && data.cards.length > 0 && data.utilization) {
        // Mock: assume cycle started 10 days ago, statement in 20 days
        // In production, use actual statement dates
        const daysIntoCycle = 10;
        const daysUntilStatement = 20;
        const cycleStartBalance = data.utilization.totalBalance * 0.7; // Assume 70% was starting balance
        
        const velocityData = calculateSpendingVelocity(
          data.utilization.totalBalance,
          cycleStartBalance,
          daysIntoCycle,
          daysUntilStatement,
          data.utilization.totalLimit
        );
        
        // Store in snapshot for Oracle to use
        data.spendingVelocity = {
          currentCycleSpend: data.utilization.totalBalance - cycleStartBalance,
          daysIntoCycle,
          projectedCycleEndSpend: velocityData.projectedBalance,
          projectedUtilization: velocityData.projectedUtilization,
          velocityMultiplier: velocityData.velocityMultiplier,
          statementDate: new Date(Date.now() + daysUntilStatement * 24 * 60 * 60 * 1000).toISOString(),
          daysUntilStatement,
        };
      }
      
      // Initialize behavioral shadow score
      // In production, calculate from payment history API
      // Mock: assume improving payment efficiency
      data.behavioralShadow = {
        paymentEfficiency: 5, // Days between statement and payment
        paymentTrend: 'improving',
        behavioralAlpha: 0.85, // Composite score (0-1)
        efficiencyMilestones: [
          {
            id: '1',
            name: 'Faster Payments',
            date: new Date().toISOString(),
            improvement: 2, // 2 days faster
          },
        ],
        lastPaymentEfficiency: 4, // Last payment was 4 days after statement
        averagePaymentEfficiency: 6, // 6-month average
      };
      
      // Initialize macro-economic data
      // In production, fetch from Fed API or market data service
      // Mock: assume stable rates for now
      data.macroEconomic = {
        fedRate: 5.25, // Current Fed rate (2026 estimate)
        rateTrend: 'stable', // 'rising' | 'stable' | 'falling'
        inflationRate: 2.5,
        lastUpdated: new Date().toISOString(),
        recommendationShift: 'neutral', // 'liquidity' | 'revolving' | 'neutral'
      };
      
      // Initialize account ages (simplified)
      if (data.cards && data.cards.length > 0) {
        data.accountAges = data.cards.map((card, index) => ({
          cardId: card.id,
          ageMonths: 12 + (index * 6), // Mock ages
          isOldest: index === 0,
        }));
      }
      
      // Initialize recent inquiries (placeholder)
      data.recentInquiries = 0; // In production: fetch from credit report API
      
      // Initialize ecosystem perks with better structure
      const perks = [
        {
          id: '1',
          name: 'Eco-Friendly Discount',
          description: '10% off sustainable products at partner stores',
          category: 'discount' as const,
          unlockRequirement: { type: 'utilization_target' as const, value: 30 },
          partner: 'Amazon',
          discount: 10,
        },
        {
          id: '2',
          name: 'Premium Event Access',
          description: 'Priority access to financial wellness events',
          category: 'access' as const,
          unlockRequirement: { type: 'score_threshold' as const, value: 700 },
          partner: 'RichesReach',
        },
        {
          id: '3',
          name: 'Fee Waiver',
          description: 'Annual fee waived on premium cards',
          category: 'discount' as const,
          unlockRequirement: { type: 'score_threshold' as const, value: 750 },
          partner: 'Various Banks',
          discount: 95,
        },
      ];
      
      const unlockedPerks = perks
        .filter(perk => {
          if (perk.unlockRequirement.type === 'score_threshold') {
            return currentScore >= perk.unlockRequirement.value;
          } else if (perk.unlockRequirement.type === 'utilization_target') {
            const utilizationPercent = data.utilization ? data.utilization.currentUtilization * 100 : 100;
            return utilizationPercent <= perk.unlockRequirement.value;
          }
          return false;
        })
        .map(p => p.id);
      
      const availablePerks = perks
        .filter(perk => !unlockedPerks.includes(perk.id))
        .map(p => p.id);
      
      const totalSavings = perks
        .filter(perk => unlockedPerks.includes(perk.id) && perk.discount)
        .reduce((sum, perk) => sum + (perk.discount || 0), 0);
      
      setEcosystemIntegration({
        perks,
        unlockedPerks,
        availablePerks,
        totalSavings,
      });
      
      // Generate oracle insights based on actual data
      // Enhanced with priority weighting to avoid insight fatigue
      const insights: Array<OracleInsight & { priority: number }> = [];
      
      // Helper function to calculate priority score (1-10)
      const calculatePriority = (
        type: 'warning' | 'opportunity' | 'trend' | 'local',
        confidence: number,
        urgency: 'critical' | 'high' | 'medium' | 'low' = 'medium'
      ): number => {
        let basePriority = confidence * 5; // 0-5 based on confidence
        
        // Type multipliers
        if (type === 'warning') basePriority += 3; // Warnings are more urgent
        else if (type === 'opportunity') basePriority += 2;
        else if (type === 'trend') basePriority += 1;
        
        // Urgency multipliers
        if (urgency === 'critical') basePriority += 2;
        else if (urgency === 'high') basePriority += 1;
        
        return Math.min(10, Math.max(1, Math.round(basePriority)));
      };
      
      // 1. HIGH UTILIZATION WARNING (High Priority)
      if (data.utilization && data.utilization.currentUtilization > 0.3) {
        const utilizationPercent = data.utilization.currentUtilization * 100;
        const urgency = utilizationPercent > 50 ? 'critical' : utilizationPercent > 40 ? 'high' : 'medium';
        insights.push({
          id: '1',
          type: 'warning',
          title: 'High Utilization Detected',
          description: `Your ${utilizationPercent.toFixed(0)}% utilization is above the recommended 30% threshold`,
          confidence: 0.95,
          timeHorizon: 'Current',
          source: 'real_time',
          recommendation: `Pay down $${data.utilization.paydownSuggestion.toFixed(0)} to reach optimal utilization`,
          affectedFactors: ['utilization'],
          priority: calculatePriority('warning', 0.95, urgency),
        });
      }
      
      // 2. PAYMENT HISTORY ANALYSIS (High Priority)
      if (data.cards && data.cards.length > 0) {
        // Check for payment due dates approaching
        const upcomingPayments = data.cards.filter(card => {
          if (!card.paymentDueDate) return false;
          const dueDate = new Date(card.paymentDueDate);
          const daysUntil = Math.ceil((dueDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
          return daysUntil > 0 && daysUntil <= 7 && card.balance > 0;
        });
        
        if (upcomingPayments.length > 0) {
          const urgentPayments = upcomingPayments.filter(card => {
            const dueDate = new Date(card.paymentDueDate!);
            const daysUntil = Math.ceil((dueDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
            return daysUntil <= 3;
          });
          
          if (urgentPayments.length > 0) {
            insights.push({
              id: '2',
              type: 'warning',
              title: 'Payment Due Soon',
              description: `${urgentPayments.length} payment${urgentPayments.length > 1 ? 's' : ''} due in 3 days or less. Missing payments can drop your score by 50-100 points.`,
              confidence: 0.98,
              timeHorizon: 'Immediate',
              source: 'real_time',
              recommendation: `Set up autopay or schedule payment now to avoid late fees and score damage`,
              affectedFactors: ['payment_history'],
              priority: calculatePriority('warning', 0.98, 'critical'),
            });
          } else {
            insights.push({
              id: '2',
              type: 'opportunity',
              title: 'Upcoming Payments',
              description: `You have ${upcomingPayments.length} payment${upcomingPayments.length > 1 ? 's' : ''} due this week. Paying on time maintains your perfect payment history.`,
              confidence: 0.90,
              timeHorizon: 'This week',
              source: 'real_time',
              recommendation: 'Schedule payments now to ensure on-time payment and protect your score',
              affectedFactors: ['payment_history'],
              priority: calculatePriority('opportunity', 0.90, 'high'),
            });
          }
        }
        
        // Check for perfect payment streak (positive reinforcement)
        const allCardsHaveGoodHistory = data.cards.every(card => {
          // In production, check actual payment history from API
          // For now, assume good if no shield alerts about late payments
          return !data.shield?.some(alert => alert.type === 'LATE_PAYMENT_RISK');
        });
        
        if (allCardsHaveGoodHistory && data.cards.length > 0) {
          insights.push({
            id: '3',
            type: 'opportunity',
            title: 'Perfect Payment History',
            description: 'You\'re maintaining excellent payment history! This is the #1 factor in your credit score (35% weight).',
            confidence: 0.85,
            timeHorizon: 'Ongoing',
            source: 'real_time',
            recommendation: 'Keep up the great work! Continue paying on time to maintain this positive factor',
            affectedFactors: ['payment_history'],
            priority: calculatePriority('opportunity', 0.85, 'low'),
          });
        }
      }
      
      // 3. CREDIT AGE INSIGHTS (Medium Priority)
      if (data.cards && data.cards.length > 0) {
        // Calculate average account age (simplified - in production, use actual account open dates)
        const accountAges = data.cards.map((card, index) => {
          // Mock: assume cards have been open for varying periods
          // In production, fetch from account data
          return 12 + (index * 6); // months
        });
        const avgAge = accountAges.reduce((sum, age) => sum + age, 0) / accountAges.length;
        const oldestAge = Math.max(...accountAges);
        
        if (avgAge < 24) {
          insights.push({
            id: '4',
            type: 'warning',
            title: 'Young Credit Profile',
            description: `Your average account age is ${Math.round(avgAge)} months. Credit age accounts for 15% of your score.`,
            confidence: 0.80,
            timeHorizon: 'Long-term',
            source: 'real_time',
            recommendation: 'Keep your oldest accounts open. Closing them will reduce your average age and hurt your score.',
            affectedFactors: ['credit_age'],
            priority: calculatePriority('warning', 0.80, 'medium'),
          });
        }
        
        if (oldestAge >= 60 && data.cards.length > 1) {
          insights.push({
            id: '5',
            type: 'opportunity',
            title: 'Protect Your Credit History',
            description: `Your oldest account is ${Math.round(oldestAge / 12)} years old. This is valuable for your score!`,
            confidence: 0.85,
            timeHorizon: 'Long-term',
            source: 'real_time',
            recommendation: 'Never close your oldest account. It anchors your credit age calculation.',
            affectedFactors: ['credit_age'],
            priority: calculatePriority('opportunity', 0.85, 'medium'),
          });
        }
      }
      
      // 4. CREDIT MIX OPTIMIZATION (Medium Priority)
      if (data.cards && data.cards.length > 0) {
        // Check if user only has revolving credit (cards)
        // In production, check for installment loans (auto, mortgage, personal)
        const hasOnlyRevolving = true; // Simplified - in production, check actual account types
        
        if (hasOnlyRevolving && data.cards.length >= 2) {
          insights.push({
            id: '6',
            type: 'opportunity',
            title: 'Credit Mix Opportunity',
            description: 'You only have revolving credit (credit cards). Adding installment credit (like a credit-builder loan) can improve your credit mix (10% of score).',
            confidence: 0.75,
            timeHorizon: '6-12 months',
            source: 'real_time',
            recommendation: 'Consider a small credit-builder loan or secured loan to diversify your credit mix. Only if you can afford it!',
            affectedFactors: ['credit_mix'],
            priority: calculatePriority('opportunity', 0.75, 'low'),
          });
        }
      }
      
      // 5. HARD INQUIRY IMPACT (High Priority)
      // In production, fetch from credit report API
      // For now, simulate based on recent activity
      const recentInquiries = 0; // Placeholder - in production: data.inquiries?.recentCount || 0
      
      if (recentInquiries > 2) {
        insights.push({
          id: '7',
          type: 'warning',
          title: 'Recent Credit Seeking',
          description: `You have ${recentInquiries} hard inquiries in the last 6 months. Each inquiry can temporarily drop your score by 5-10 points.`,
          confidence: 0.90,
          timeHorizon: 'Short-term',
          source: 'real_time',
          recommendation: 'Avoid new credit applications for 3-6 months to let your score recover. Inquiries stay on your report for 2 years but only impact score for 12 months.',
          affectedFactors: ['inquiries'],
          priority: calculatePriority('warning', 0.90, recentInquiries > 4 ? 'critical' : 'high'),
        });
      } else if (recentInquiries === 0 && currentScore < 750) {
        insights.push({
          id: '7',
          type: 'opportunity',
          title: 'Clean Inquiry History',
          description: 'You have no recent hard inquiries. Your credit report looks clean!',
          confidence: 0.85,
          timeHorizon: 'Current',
          source: 'real_time',
          recommendation: 'This is good! Hard inquiries stay on your report for 2 years, so be selective about new applications.',
          affectedFactors: ['inquiries'],
          priority: calculatePriority('opportunity', 0.85, 'low'),
        });
      }
      
      // 6. STATEMENT DATE OPTIMIZATION (Medium Priority)
      if (data.cards && data.cards.length > 0) {
        insights.push({
          id: '8',
          type: 'opportunity',
          title: 'Statement Date Optimization',
          description: 'You can improve your score by timing payments before statement dates',
          confidence: 0.85,
          timeHorizon: 'This month',
          source: 'real_time',
          recommendation: 'Pay down balances 2-3 days before each statement date to show lower utilization on your credit report',
          affectedFactors: ['utilization'],
          priority: calculatePriority('opportunity', 0.85, 'medium'),
        });
      }
      
      // 7. SEASONAL TREND (Low Priority - Informational)
      const month = new Date().getMonth();
      if (month >= 10 || month === 0) { // November, December, January
        insights.push({
          id: '9',
          type: 'trend',
          title: 'Holiday Spending Season',
          description: 'Credit scores typically drop 5-15 points during holiday season due to increased spending',
          confidence: 0.75,
          timeHorizon: 'Q4 2025',
          source: 'crowdsourced',
          recommendation: 'Plan ahead: keep utilization below 10% through January to minimize score impact',
          affectedFactors: ['utilization', 'payment_history'],
          priority: calculatePriority('trend', 0.75, 'low'),
        });
      }
      
      // 8. SCORE PROJECTION OPPORTUNITY (If projection data available)
      if (data.projection && data.projection.scoreGain6m > 0) {
        insights.push({
          id: '10',
          type: 'opportunity',
          title: 'Score Growth Potential',
          description: `Based on your current actions, you could see a ${data.projection.scoreGain6m}+ point increase in the next 6 months.`,
          confidence: 0.80,
          timeHorizon: '6 months',
          source: 'ai',
          recommendation: data.projection.topAction || 'Continue following your action plan to maximize score growth',
          affectedFactors: data.projection.factors ? Object.keys(data.projection.factors) : [],
          priority: calculatePriority('opportunity', 0.80, 'medium'),
        });
      }
      
      // 9. CREDIT VELOCITY PREDICTOR (Cutting-Edge: Predictive)
      if (data.spendingVelocity && data.utilization) {
        const { velocityMultiplier, projectedUtilization, daysUntilStatement } = data.spendingVelocity;
        
        if (velocityMultiplier > 1.5) {
          // High burn rate detected
          const projectedUtilPercent = projectedUtilization * 100;
          const scoreDrop = projectedUtilPercent > 50 ? 45 : projectedUtilPercent > 30 ? 20 : 5;
          
          insights.push({
            id: '11',
            type: 'warning',
            title: 'High Burn Rate Detected',
            description: `At your current spending pace (${(velocityMultiplier * 100).toFixed(0)}% faster than average), you're on track to hit ${projectedUtilPercent.toFixed(0)}% utilization by your statement date.`,
            confidence: 0.92,
            timeHorizon: `${daysUntilStatement} days`,
            source: 'velocity_tracker',
            prediction: `Predicted Score Change: -${scoreDrop}pts`,
            urgency: projectedUtilPercent > 50 ? 'critical' : 'high',
            recommendation: `Slow down spending for ${Math.ceil(daysUntilStatement / 2)} days to reset your trajectory. Consider using 0% APR financing for large purchases.`,
            affectedFactors: ['utilization'],
            priority: calculatePriority('warning', 0.92, projectedUtilPercent > 50 ? 'critical' : 'high'),
          });
        }
      }
      
      // 10. BEHAVIORAL SHADOW SCORE TRACKING (Cutting-Edge: Behavioral)
      if (data.behavioralShadow) {
        const { paymentEfficiency, paymentTrend, behavioralAlpha, lastPaymentEfficiency, averagePaymentEfficiency } = data.behavioralShadow;
        
        // Efficiency milestone
        if (paymentTrend === 'improving' && lastPaymentEfficiency < averagePaymentEfficiency) {
          const improvement = averagePaymentEfficiency - lastPaymentEfficiency;
          insights.push({
            id: '12',
            type: 'opportunity',
            title: 'Efficiency Milestone',
            description: `You're paying bills ${improvement.toFixed(0)} days faster than your 6-month average. This "Behavioral Alpha" indicates strong financial habits.`,
            confidence: 0.88,
            timeHorizon: 'Current',
            source: 'ai_behavioral_model',
            behavioralAlpha: behavioralAlpha,
            recommendation: `This behavioral pattern suggests a high likelihood of a credit limit increase request being approved in 60 days. Keep up the excellent payment efficiency!`,
            affectedFactors: ['payment_history', 'credit_age'],
            priority: calculatePriority('opportunity', 0.88, 'medium'),
          });
        }
        
        // Warning if efficiency declining
        if (paymentTrend === 'declining' && lastPaymentEfficiency > averagePaymentEfficiency + 3) {
          insights.push({
            id: '13',
            type: 'warning',
            title: 'Payment Efficiency Declining',
            description: `You're taking ${lastPaymentEfficiency.toFixed(0)} days to pay bills, which is ${(lastPaymentEfficiency - averagePaymentEfficiency).toFixed(0)} days slower than your average.`,
            confidence: 0.85,
            timeHorizon: 'Current',
            source: 'ai_behavioral_model',
            recommendation: 'Set up autopay or payment reminders to improve your payment efficiency and protect your credit score.',
            affectedFactors: ['payment_history'],
            priority: calculatePriority('warning', 0.85, 'medium'),
          });
        }
      }
      
      // 11. MACRO-ECONOMIC SENTIMENT OVERLAY (Cutting-Edge: Market Integration)
      if (data.macroEconomic) {
        const { fedRate, rateTrend, recommendationShift } = data.macroEconomic;
        
        if (rateTrend === 'rising' && recommendationShift === 'liquidity') {
          // Calculate potential interest savings
          const avgBalance = data.utilization.totalBalance;
          const projectedRateIncrease = 0.02; // 2% increase
          const monthlyInterestIncrease = (avgBalance * projectedRateIncrease) / 12;
          const annualSavings = monthlyInterestIncrease * 12;
          
          insights.push({
            id: '14',
            type: 'opportunity',
            title: 'Market Shift: Interest Rates Rising',
            description: `The Fed is raising rates. Your variable-rate cards will see higher APRs next month.`,
            confidence: 0.90,
            timeHorizon: 'Next month',
            source: 'market_data',
            interestLeak: monthlyInterestIncrease,
            recommendation: `Moving $${Math.min(avgBalance * 0.3, 2000).toFixed(0)} of CC debt to a fixed-rate personal loan now will save you $${annualSavings.toFixed(0)} in interest over 12 months.`,
            affectedFactors: ['utilization', 'credit_mix'],
            priority: calculatePriority('opportunity', 0.90, 'high'),
          });
        }
        
        if (rateTrend === 'falling' && recommendationShift === 'revolving') {
          insights.push({
            id: '15',
            type: 'opportunity',
            title: 'Market Opportunity: Rates Falling',
            description: 'Interest rates are declining. This is a good time to consolidate high-interest debt.',
            confidence: 0.85,
            timeHorizon: 'Next 3 months',
            source: 'market_data',
            recommendation: 'Consider a balance transfer to a 0% APR card or refinance existing debt while rates are low.',
            affectedFactors: ['utilization'],
            priority: calculatePriority('opportunity', 0.85, 'medium'),
          });
        }
      }
      
      // Sort insights by priority (highest first) and limit to top 5 to avoid fatigue
      const sortedInsights = insights
        .sort((a, b) => b.priority - a.priority)
        .slice(0, 5); // Top 5 most critical insights
      
      setCreditOracle({
        insights: sortedInsights,
        localTrends: [],
        warnings: sortedInsights.filter(i => i.type === 'warning'),
        opportunities: sortedInsights.filter(i => i.type === 'opportunity'),
        lastUpdated: new Date().toISOString(),
      });
      
      // Initialize sustainability with actual progress
      const actionsCompleted = data.actions.filter(a => a.completed).length;
      const treesPlanted = Math.floor(actionsCompleted * 1.5);
      const co2Offset = treesPlanted * 0.2;
      
      setSustainabilityTracking({
        totalImpact: {
          treesPlanted,
          co2Offset,
          actionsCompleted,
          milestones: treesPlanted >= 10 ? [
            { id: '1', name: 'First 10 Trees', date: new Date().toISOString(), impact: 10 },
          ] : [],
        },
        weeklyImpact: {
          treesPlanted: Math.min(2, treesPlanted),
          co2Offset: Math.min(0.4, co2Offset),
          actionsCompleted: Math.min(1, actionsCompleted),
          milestones: [],
        },
        goals: [
          { id: '1', name: 'Plant 50 Trees', target: 50, current: treesPlanted, unit: 'trees' },
          { id: '2', name: 'Offset 10kg CO₂', target: 10, current: co2Offset, unit: 'co2_kg' },
        ],
        partnerIntegrations: [
          { name: 'Tree-Nation', type: 'tree_planting', contribution: treesPlanted },
          { name: 'Carbon Offset Co', type: 'carbon_offset', contribution: co2Offset },
        ],
      });
      
      // Generate statement-date plans with better logic
      if (data.cards && data.cards.length > 0) {
        const plans: StatementDatePlan[] = data.cards
          .filter(card => card.limit > 0) // Only include cards with limits
          .map((card, index) => {
            // Generate statement date (cards don't have statementDate property)
            const date = new Date();
            date.setDate(date.getDate() + (7 + index * 3));
            const statementCloseDate = date;
            
            const paymentDueDate = new Date(statementCloseDate);
            paymentDueDate.setDate(paymentDueDate.getDate() + 21);
            
            const daysUntilClose = Math.ceil((statementCloseDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
            const targetUtilization = 0.09; // 9% optimal
            const currentBalance = card.balance;
            const targetBalance = card.limit * targetUtilization;
            const recommendedPaydown = Math.max(0, currentBalance - targetBalance);
            
            // More accurate score gain projection
            const utilizationDrop = card.utilization - targetUtilization;
            const projectedScoreGain = utilizationDrop > 0 
              ? Math.round(Math.min(30, utilizationDrop * 100 * 0.5)) // Up to 30 points
              : 0;
            
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
              projectedScoreGain,
            };
          })
          .sort((a, b) => a.daysUntilClose - b.daysUntilClose); // Sort by urgency
        
        setStatementPlans(plans);
      }
      
      // Generate shield plan with better risk assessment
      if (data.cards && data.cards.length > 0) {
        const upcomingPayments = data.cards
          .filter(card => card.paymentDueDate && card.balance > 0)
          .map(card => {
            const dueDate = new Date(card.paymentDueDate!);
            const daysUntilDue = Math.ceil((dueDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
            let riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' = 'LOW';
            
            if (daysUntilDue <= 2) riskLevel = 'HIGH';
            else if (daysUntilDue <= 5) riskLevel = 'MEDIUM';
            
            const minimumPayment = card.minimumPayment || Math.max(25, card.balance * 0.02);
            
            return {
              cardName: card.name,
              dueDate: card.paymentDueDate!,
              minimumPayment,
              daysUntilDue,
              riskLevel,
            };
          })
          .sort((a, b) => a.daysUntilDue - b.daysUntilDue); // Sort by urgency
        
        if (upcomingPayments.length > 0) {
          const totalMinimum = upcomingPayments.reduce((sum, p) => sum + p.minimumPayment, 0);
          const overallRisk = upcomingPayments.some(p => p.riskLevel === 'HIGH') ? 'HIGH' :
                             upcomingPayments.some(p => p.riskLevel === 'MEDIUM') ? 'MEDIUM' : 'LOW';
          
          const recommendations: string[] = [];
          if (overallRisk === 'HIGH') {
            recommendations.push('⚠️ URGENT: Payment due in 2 days or less');
            recommendations.push('Set up autopay immediately to avoid late fees (-$40) and score damage (-100 pts)');
          } else if (overallRisk === 'MEDIUM') {
            recommendations.push('⚡ Upcoming payment in next 5 days');
            recommendations.push('Schedule payment now to stay on track');
          }
          
          recommendations.push(`💰 Reserve $${Math.ceil(totalMinimum * 1.2).toFixed(0)} in checking account (includes buffer)`);
          
          if (upcomingPayments.length > 1) {
            recommendations.push(`📅 ${upcomingPayments.length} cards have payments due this month`);
          }
          
          setShieldPlan({
            riskLevel: overallRisk,
            totalMinimumPayments: totalMinimum,
            upcomingPayments,
            safetyBuffer: totalMinimum * 1.2, // 20% buffer
            recommendations,
          });
        }
      }
      
      // Load score history with better fallback
      try {
        const currentScore = data.score;
        if (currentScore && typeof currentScore.score === 'number' && currentScore.score > 0) {
          const history: CreditScore[] = [];
          const baseScore = currentScore.score;
          
          // Generate 6-month history with realistic variation
          for (let i = 5; i >= 0; i--) {
            const date = new Date();
            date.setMonth(date.getMonth() - i);
            
            // Add some realistic variation (±5 points per month)
            const variation = Math.floor(Math.random() * 10) - 5;
            const score = Math.max(300, Math.min(850, baseScore - (i * 3) + variation));
            
            history.push({
              score,
              scoreRange: getScoreRange(score),
              lastUpdated: date.toISOString(),
              provider: currentScore.provider || 'self_reported',
              factors: currentScore.factors,
            });
          }
          setScoreHistory(history);
        } else {
          setScoreHistory([]);
        }
      } catch (error) {
        logger.warn('[CreditQuest] Failed to load score history:', error);
        setScoreHistory([]);
      }
      
      // Schedule notifications intelligently
      if (data.cards && data.cards.length > 0) {
        for (const card of data.cards) {
          // Only schedule if payment is upcoming (within 30 days)
          if (card.paymentDueDate) {
            const dueDate = new Date(card.paymentDueDate);
            const daysUntil = Math.ceil((dueDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
            
            if (daysUntil > 0 && daysUntil <= 30) {
              await creditNotificationService.schedulePaymentReminder(
                card.name,
                dueDate,
                3 // Remind 3 days before
              );
            }
          }
          
          // Only alert on high utilization (>50%)
          if (card.utilization > 0.5) {
            await creditNotificationService.scheduleUtilizationAlert(
              card.name,
              card.utilization
            );
          }
        }
      }
    } catch (error) {
      logger.error('[CreditQuest] Failed to load snapshot:', error);
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
  }, [snapshot]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadSnapshot();
    setRefreshing(false);
  }, [loadSnapshot]);

  const handlePrimaryAction = useCallback(() => {
    if (!snapshot) return;
    
    const topAction = snapshot.actions.find(a => !a.completed);
    if (topAction) {
      Alert.alert(
        topAction.title,
        `${topAction.description}\n\nThis could improve your score by ${topAction.projectedScoreGain || 5}+ points.`,
        [
          { text: 'Not Now', style: 'cancel' },
          { 
            text: 'Complete Action', 
            style: 'default',
            onPress: async () => {
              // Mark action as completed
              // In production, call API here
              Alert.alert('✅ Great Job!', 'Action completed! Your score may improve within 1-2 statement cycles.');
              
              // Refresh data
              await loadSnapshot();
            }
          }
        ]
      );
    } else {
      Alert.alert(
        '🎉 All Caught Up!',
        'You\'re doing great! Keep up the good work to maintain your credit score.',
        [{ text: 'Awesome' }]
      );
    }
  }, [snapshot, loadSnapshot]);

  // Helper function to get score range
  const getScoreRange = (score: number): 'Poor' | 'Fair' | 'Good' | 'Very Good' | 'Excellent' => {
    if (score >= 800) return 'Excellent';
    if (score >= 740) return 'Very Good';
    if (score >= 670) return 'Good';
    if (score >= 580) return 'Fair';
    return 'Poor';
  };

  // Loading state
  if (loading || !snapshot || !snapshot.score) {
    return (
      <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={onClose}
      >
        <Animated.View 
          style={[
            styles.container, 
            { paddingTop: insets.top },
            { opacity: fadeAnim }
          ]}
        >
        <LinearGradient
          colors={['#F8F9FA', '#FFFFFF']}
          style={StyleSheet.absoluteFill}
        />
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Credit Quest</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading your credit journey...</Text>
          <Text style={styles.loadingSubtext}>This may take a moment</Text>
        </View>
      </Animated.View>
      </Modal>
    );
  }

  if (!snapshot) {
    return (
      <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={onClose}
      >
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
      </Modal>
    );
  }

  const topAction = snapshot.actions.find(a => !a.completed);
  const utilization = snapshot.utilization;
  const hasAlerts = shieldPlan && shieldPlan.riskLevel !== 'LOW';

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={onClose}
    >
      <View style={[styles.container, { paddingTop: insets.top }]}>
      <LinearGradient
        colors={['#F8F9FA', '#FFFFFF']}
        style={StyleSheet.absoluteFill}
      />
      
      {/* Enhanced Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>Credit Quest</Text>
          {hasAlerts && (
            <View style={styles.alertBadge}>
              <Icon name="alert-circle" size={12} color="#FFFFFF" />
            </View>
          )}
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={handleRefresh} style={styles.iconButton}>
            <Icon 
              name="refresh-cw" 
              size={20} 
              color={refreshing ? "#007AFF" : "#8E8E93"} 
            />
          </TouchableOpacity>
          <TouchableOpacity onPress={onClose} style={styles.iconButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor="#007AFF"
          />
        }
      >
        <Animated.View
          style={{
            opacity: fadeAnim,
            transform: [{ translateY: slideAnim }],
          }}
        >
          {/* Credit Score Orb - Hero Section */}
          <View style={styles.heroSection}>
            <CreditScoreOrb 
              score={snapshot.score}
              projection={snapshot.projection}
            />
          </View>

          {/* Quick Stats Card */}
          <View style={styles.statsCard}>
            <LinearGradient
              colors={['#007AFF', '#0051D5']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.statsGradient}
            >
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Utilization</Text>
                <Text style={styles.statValue}>
                  {utilization ? `${(utilization.currentUtilization * 100).toFixed(0)}%` : 'N/A'}
                </Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Actions</Text>
                <Text style={styles.statValue}>
                  {snapshot.actions.filter(a => !a.completed).length}
                </Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Streak</Text>
                <Text style={styles.statValue}>{autopilotStatus.streak}d</Text>
              </View>
            </LinearGradient>
          </View>

          {/* Priority Action Card */}
          {topAction && (
            <View style={styles.priorityCard}>
              <View style={styles.priorityHeader}>
                <Icon name="zap" size={20} color="#FF9500" />
                <Text style={styles.priorityTitle}>Top Priority This Month</Text>
              </View>
              <Text style={styles.priorityAction}>{topAction.title}</Text>
              <Text style={styles.priorityDescription}>{topAction.description}</Text>
              
              {topAction.projectedScoreGain && topAction.projectedScoreGain > 0 && (
                <View style={styles.impactBadge}>
                  <Icon name="trending-up" size={14} color="#34C759" />
                  <Text style={styles.impactText}>
                    +{topAction.projectedScoreGain} points
                  </Text>
                </View>
              )}
              
              <TouchableOpacity 
                style={styles.actionButton}
                onPress={handlePrimaryAction}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={['#007AFF', '#0051D5']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.actionButtonGradient}
                >
                  <Icon name="check-circle" size={18} color="#FFFFFF" />
                  <Text style={styles.actionButtonText}>Complete Now</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          )}

          {/* Credit Shield - Urgent Alerts */}
          {shieldPlan && shieldPlan.riskLevel !== 'LOW' && (
            <View style={styles.section}>
              <CreditShield plan={shieldPlan} />
            </View>
          )}

          {/* This Month Section */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>This Month</Text>
              <TouchableOpacity 
                onPress={() => setShowTrends(!showTrends)}
                style={styles.trendToggle}
              >
                <Text style={styles.trendToggleText}>
                  {showTrends ? 'Hide' : 'Show'} Trends
                </Text>
                <Icon 
                  name={showTrends ? "chevron-up" : "chevron-down"} 
                  size={16} 
                  color="#007AFF" 
                />
              </TouchableOpacity>
            </View>
            
            {utilization && <CreditUtilizationGauge utilization={utilization} />}
            
            {showTrends && scoreHistory.length > 0 && (
              <View style={styles.trendSection}>
                <CreditScoreTrendChart scores={scoreHistory} />
              </View>
            )}
            
            {/* Score Simulator */}
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

          {/* Statement-Date Planner */}
          {statementPlans.length > 0 && (
            <View style={styles.section}>
              <StatementDatePlanner plans={statementPlans} />
            </View>
          )}

          {/* All Actions */}
          {snapshot.actions.length > 1 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>All Actions</Text>
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
                    size={22} 
                    color={action.completed ? "#34C759" : "#C7C7CC"} 
                  />
                  <View style={styles.actionContent}>
                    <Text style={[
                      styles.actionTitle,
                      action.completed && styles.actionTitleCompleted
                    ]}>
                      {action.title}
                    </Text>
                    <Text style={styles.actionDescription}>
                      {action.description}
                    </Text>
                    {action.projectedScoreGain && action.projectedScoreGain > 0 && (
                      <View style={styles.gainBadge}>
                        <Icon name="arrow-up" size={10} color="#34C759" />
                        <Text style={styles.gainText}>
                          +{action.projectedScoreGain} pts
                        </Text>
                      </View>
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
                  const progress = prev.currentWeek.selectedActions.length > 0
                    ? (newCompleted.length / prev.currentWeek.selectedActions.length) * 100
                    : 0;
                  return {
                    ...prev,
                    currentWeek: {
                      ...prev.currentWeek,
                      completedActions: newCompleted,
                      progress,
                    },
                    totalActionsCompleted: prev.totalActionsCompleted + 1,
                    streak: prev.streak + 1,
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
                  description: 'See the impact of missing a credit card payment',
                  inputs: { paymentMissed: true },
                  projectedOutcome: {
                    scoreChange: -50,
                    timeToImpact: '1-2 cycles',
                    factors: ['Payment history severely impacted'],
                  },
                },
                {
                  id: '2',
                  name: 'Add Solar Loan',
                  description: 'How does a $20k solar loan affect your score?',
                  inputs: { loanAmount: 20000, loanType: 'solar' },
                  projectedOutcome: {
                    scoreChange: -15,
                    timeToImpact: '3-6 months',
                    factors: ['Hard inquiry', 'Credit mix improves', 'New account age decreases'],
                  },
                },
                {
                  id: '3',
                  name: 'Optimize Utilization',
                  description: 'Pay down all cards to 9% utilization',
                  inputs: { utilizationChange: -30 },
                  projectedOutcome: {
                    scoreChange: 25,
                    timeToImpact: '1-2 cycles',
                    factors: ['Utilization drops to optimal range'],
                  },
                },
                {
                  id: '4',
                  name: 'Open New Credit Card',
                  description: 'Impact of applying for a new rewards card',
                  inputs: { newAccount: true, newInquiry: true },
                  projectedOutcome: {
                    scoreChange: -5,
                    timeToImpact: '1 month',
                    factors: ['Hard inquiry', 'Average age decreases', 'Available credit increases'],
                  },
                },
              ]}
              onScenarioSelect={(scenario) => {
                const newProjectedScore = Math.max(
                  300,
                  Math.min(850, creditTwinState.projectedScore + scenario.projectedOutcome.scoreChange)
                );
                
                setCreditTwinState(prev => ({
                  ...prev,
                  currentScenario: scenario,
                  scenarioHistory: [...prev.scenarioHistory, scenario],
                  projectedScore: newProjectedScore,
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
                  const perk = ecosystemIntegration.perks.find(p => p.id === perkId);
                  Alert.alert(
                    '🎁 Redeem Perk',
                    `Ready to use your ${perk?.name}? This will redirect you to ${perk?.partner}.`,
                    [
                      { text: 'Cancel', style: 'cancel' },
                      { text: 'Continue', onPress: () => {
                        // In production, open external link or in-app browser
                        Alert.alert('Success', `Redirecting to ${perk?.partner}...`);
                      }}
                    ]
                  );
                }}
              />
            </View>
          )}

          {/* Credit Oracle */}
          {creditOracle.insights.length > 0 && (
            <View style={styles.section}>
              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>Credit Oracle</Text>
                <TouchableOpacity
                  onPress={() => setShowCrystalBall(true)}
                  style={styles.crystalBallButton}
                >
                  <LinearGradient
                    colors={['#667eea', '#764ba2']}
                    style={styles.crystalBallGradient}
                  >
                    <Icon name="eye" size={16} color="#FFFFFF" />
                    <Text style={styles.crystalBallText}>Crystal Ball</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
              <CreditOracle
                oracle={creditOracle}
                onInsightPress={(insight) => {
                  let message = `${insight.description}\n\n💡 Recommendation: ${insight.recommendation}`;
                  
                  if (insight.prediction) {
                    message += `\n\n🔮 Prediction: ${insight.prediction}`;
                  }
                  
                  if (insight.interestLeak && insight.interestLeak > 0) {
                    message += `\n\n💰 Monthly Interest Cost: $${insight.interestLeak.toFixed(2)}`;
                  }
                  
                  if (insight.recoveryTime) {
                    message += `\n\n⏰ Recovery Time: ${insight.recoveryTime}`;
                  }
                  
                  if (insight.behavioralAlpha !== undefined) {
                    message += `\n\n📊 Behavioral Alpha: ${(insight.behavioralAlpha * 100).toFixed(0)}%`;
                  }
                  
                  Alert.alert(insight.title, message, [{ text: 'Got It' }]);
                }}
              />
            </View>
          )}
          
          {/* Zero-Gravity Migration Card */}
          {snapshot && (() => {
            const migrationCheck = shouldConsiderMigration(snapshot);
            if (!migrationCheck.shouldMigrate) return null;
            
            return (
              <View style={styles.section}>
                <TouchableOpacity
                  onPress={() => setShowZeroGravity(true)}
                  activeOpacity={0.8}
                >
                  <LinearGradient
                    colors={['#FF6B6B', '#FF8E53']}
                    style={styles.zeroGravityCard}
                  >
                    <View style={styles.zeroGravityHeader}>
                      <View style={styles.zeroGravityIconContainer}>
                        <Icon name="zap" size={24} color="#FFFFFF" />
                      </View>
                      <View style={styles.zeroGravityContent}>
                        <Text style={styles.zeroGravityTitle}>
                          Zero-Gravity Debt Migration
                        </Text>
                        <Text style={styles.zeroGravitySubtitle}>
                          You're leaking ${migrationCheck.monthlyInterestLeak.toFixed(2)}/month in interest
                        </Text>
                      </View>
                      <Icon name="chevron-right" size={24} color="#FFFFFF" />
                    </View>
                    <View style={styles.zeroGravityFooter}>
                      <View style={styles.zeroGravityBadge}>
                        <Icon name="trending-up" size={14} color="#FFFFFF" />
                        <Text style={styles.zeroGravityBadgeText}>
                          Active Arbitrage Desk
                        </Text>
                      </View>
                      <Text style={styles.zeroGravityCTA}>
                        See Your Migration Strategy →
                      </Text>
                    </View>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            );
          })()}
          
          {/* Crystal Ball Simulator Modal */}
          {showCrystalBall && snapshot && (
            <CrystalBallSimulator
              currentData={snapshot}
              onClose={() => setShowCrystalBall(false)}
            />
          )}
          
          {/* Zero-Gravity Migration Modal */}
          {showZeroGravity && snapshot && (
            <Modal
              visible={showZeroGravity}
              animationType="slide"
              presentationStyle="fullScreen"
              onRequestClose={() => setShowZeroGravity(false)}
            >
              <View style={styles.modalContainer}>
                <View style={[styles.modalHeader, { paddingTop: insets.top + 20 }]}>
                  <Text style={styles.modalTitle}>Zero-Gravity Migration</Text>
                  <TouchableOpacity
                    onPress={() => setShowZeroGravity(false)}
                    style={styles.modalCloseButton}
                  >
                    <Icon name="x" size={24} color="#1C1C1E" />
                  </TouchableOpacity>
                </View>
                <ZeroGravityMigration
                  snapshot={snapshot}
                  onClose={() => setShowZeroGravity(false)}
                />
              </View>
            </Modal>
          )}

          {/* Sustainability Layer */}
          <View style={styles.section}>
            <SustainabilityLayer
              tracking={sustainabilityTracking}
              onViewDetails={() => {
                Alert.alert(
                  '🌱 Your Impact',
                  `You've planted ${sustainabilityTracking.totalImpact.treesPlanted} trees and offset ${sustainabilityTracking.totalImpact.co2Offset}kg of CO₂ through credit building actions!`,
                  [{ text: 'Amazing!' }]
                );
              }}
            />
          </View>

          {/* Bottom Padding */}
          <View style={{ height: 40 }} />
        </Animated.View>
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
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1C1C1E',
    letterSpacing: -0.5,
  },
  alertBadge: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#FF3B30',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  iconButton: {
    padding: 6,
    borderRadius: 8,
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
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 16,
  },
  loadingSubtext: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 4,
  },
  heroSection: {
    alignItems: 'center',
    paddingVertical: 20,
    marginBottom: 16,
  },
  statsCard: {
    marginBottom: 20,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#007AFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 6,
  },
  statsGradient: {
    flexDirection: 'row',
    paddingVertical: 20,
    paddingHorizontal: 16,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.8)',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  statDivider: {
    width: 1,
    height: '100%',
    backgroundColor: 'rgba(255,255,255,0.2)',
    marginHorizontal: 8,
  },
  priorityCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderWidth: 2,
    borderColor: '#FF9500',
    shadowColor: '#FF9500',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 6,
  },
  priorityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  priorityTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FF9500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  priorityAction: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 8,
    lineHeight: 28,
  },
  priorityDescription: {
    fontSize: 15,
    color: '#636366',
    lineHeight: 22,
    marginBottom: 16,
  },
  impactBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    gap: 4,
    marginBottom: 16,
  },
  impactText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#34C759',
  },
  actionButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  actionButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  trendToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#F0F0F0',
  },
  trendToggleText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  trendSection: {
    marginTop: 16,
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
  simulatorContainer: {
    marginTop: 16,
  },
  actionCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    gap: 14,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  actionCardCompleted: {
    opacity: 0.5,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 6,
  },
  actionTitleCompleted: {
    textDecorationLine: 'line-through',
  },
  actionDescription: {
    fontSize: 14,
    color: '#636366',
    lineHeight: 20,
    marginBottom: 8,
  },
  gainBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  gainText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#34C759',
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
  crystalBallButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  crystalBallGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    gap: 6,
  },
  crystalBallText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  zeroGravityCard: {
    borderRadius: 16,
    padding: 20,
    shadowColor: '#FF6B6B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  zeroGravityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  zeroGravityIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  zeroGravityContent: {
    flex: 1,
  },
  zeroGravityTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  zeroGravitySubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
  },
  zeroGravityFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  zeroGravityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    gap: 6,
  },
  zeroGravityBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  zeroGravityCTA: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  modalCloseButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

