/**
 * Credit Building Types
 * TypeScript interfaces for credit building features
 */

export interface CreditScore {
  score: number;
  scoreRange: 'Poor' | 'Fair' | 'Good' | 'Very Good' | 'Excellent';
  lastUpdated: string;
  provider: 'experian' | 'equifax' | 'transunion' | 'self_reported' | 'credit_karma';
  factors?: {
    paymentHistory: number;
    utilization: number;
    creditAge: number;
    creditMix: number;
    inquiries: number;
  };
}

export interface CreditCard {
  id: string;
  name: string;
  limit: number;
  balance: number;
  utilization: number; // 0-1 (0% to 100%)
  yodleeAccountId?: string;
  lastSynced?: string;
  paymentDueDate?: string;
  minimumPayment?: number;
}

export interface CreditProjection {
  scoreGain6m: number;
  topAction: string;
  confidence: number;
  factors: {
    paymentHistory?: string;
    utilization?: string;
    creditAge?: string;
    creditMix?: string;
  };
}

export interface CreditCardRecommendation {
  id: string;
  name: string;
  type: 'secured' | 'unsecured';
  deposit?: number;
  annualFee: number;
  apr: number;
  description: string;
  benefits: string[];
  preQualified: boolean;
  applicationUrl?: string;
}

export interface CreditUtilization {
  totalLimit: number;
  totalBalance: number;
  currentUtilization: number; // 0-1
  optimalUtilization: number; // 0.3 (30%)
  paydownSuggestion: number;
  projectedScoreGain: number;
}

export interface CreditAction {
  id: string;
  type: 'AUTOPAY_SETUP' | 'CARD_APPLIED' | 'PAYMENT_MADE' | 'LIMIT_INCREASE' | 'UTILIZATION_REDUCED';
  title: string;
  description: string;
  completed: boolean;
  projectedScoreGain?: number;
  dueDate?: string;
}

export interface CreditEducationModule {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  duration: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  content: {
    sections: Array<{
      id: string;
      title: string;
      type: 'text' | 'quiz' | 'interactive';
      content: string;
    }>;
  };
}

export interface CreditSnapshot {
  score: CreditScore;
  cards: CreditCard[];
  utilization: CreditUtilization;
  projection?: CreditProjection;
  actions: CreditAction[];
  shield?: Array<{
    type: 'PAYMENT_DUE' | 'HIGH_UTILIZATION' | 'LATE_PAYMENT_RISK';
    inDays: number | null;
    message: string;
    suggestion: string;
  }>;
}

// Statement-Date Utilization Planner
export interface StatementDatePlan {
  cardId: string;
  cardName: string;
  currentBalance: number;
  limit: number;
  currentUtilization: number;
  statementCloseDate: string; // ISO date
  paymentDueDate: string; // ISO date
  recommendedPaydown: number;
  targetUtilization: number; // e.g., 0.09 for 9%
  daysUntilClose: number;
  projectedScoreGain: number;
}

// Score Simulator Inputs
export interface ScoreSimulatorInputs {
  utilizationPercent: number; // 0-100
  onTimeStreak: number; // months
  recentInquiries: number; // last 12 months
}

// Score Simulator Output
export interface ScoreSimulation {
  minScore: number;
  likelyScore: number;
  maxScore: number;
  timeToImpact: string; // e.g., "1-2 cycles" or "3-6 months"
  factors: {
    utilization: { impact: number; note: string };
    paymentHistory: { impact: number; note: string };
    inquiries: { impact: number; note: string };
  };
}

// Credit Shield Safety Plan
export interface CreditShieldPlan {
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  totalMinimumPayments: number;
  upcomingPayments: Array<{
    cardName: string;
    dueDate: string;
    minimumPayment: number;
    daysUntilDue: number;
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  }>;
  safetyBuffer: number; // recommended cash buffer
  recommendations: string[];
}

// Autopilot Mode
export interface AutopilotWeek {
  weekStart: string; // ISO date
  weekEnd: string; // ISO date
  selectedActions: CreditAction[]; // 1-2 actions
  completedActions: string[]; // action IDs
  progress: number; // 0-100
  summary?: string;
}

export interface AutopilotStatus {
  enabled: boolean;
  currentWeek: AutopilotWeek;
  weeklyHistory: AutopilotWeek[];
  streak: number; // consecutive weeks completed
  totalActionsCompleted: number;
}

// Credit Twin Simulator
export interface CreditTwinScenario {
  id: string;
  name: string;
  description: string;
  inputs: {
    utilizationChange?: number;
    paymentMissed?: boolean;
    newInquiry?: boolean;
    newAccount?: boolean;
    loanAmount?: number;
    loanType?: 'auto' | 'mortgage' | 'personal' | 'solar';
  };
  projectedOutcome: {
    scoreChange: number;
    timeToImpact: string;
    factors: string[];
  };
  branches?: CreditTwinScenario[]; // nested scenarios
}

export interface CreditTwinState {
  baseScore: number;
  currentScenario?: CreditTwinScenario;
  scenarioHistory: CreditTwinScenario[];
  projectedScore: number;
}

// Ecosystem Perks
export interface CreditPerk {
  id: string;
  name: string;
  description: string;
  category: 'discount' | 'access' | 'cashback' | 'event' | 'service';
  unlockRequirement: {
    type: 'utilization_target' | 'score_threshold' | 'action_completion' | 'streak';
    value: number;
  };
  partner: string;
  partnerLogo?: string;
  discount?: number; // percentage
  cashback?: number; // percentage
  validUntil?: string;
  redemptionUrl?: string;
}

export interface EcosystemIntegration {
  perks: CreditPerk[];
  unlockedPerks: string[]; // perk IDs
  availablePerks: string[]; // perk IDs
  totalSavings: number;
}

// Predictive Credit Oracle
export interface OracleInsight {
  id: string;
  type: 'trend' | 'warning' | 'opportunity' | 'local';
  title: string;
  description: string;
  confidence: number; // 0-1
  timeHorizon: string; // e.g., "Q4 2025"
  source: 'crowdsourced' | 'ai' | 'market_data';
  location?: string; // city/region
  affectedFactors: string[];
  recommendation: string;
  biasCheck?: {
    detected: boolean;
    adjusted: boolean;
    explanation: string;
  };
}

export interface CreditOracle {
  insights: OracleInsight[];
  localTrends: OracleInsight[];
  warnings: OracleInsight[];
  opportunities: OracleInsight[];
  lastUpdated: string;
}

// Sustainability Layer
export interface CreditImpact {
  treesPlanted: number;
  co2Offset: number; // kg
  actionsCompleted: number;
  milestones: Array<{
    id: string;
    name: string;
    date: string;
    impact: number; // trees or CO2
  }>;
}

export interface SustainabilityTracking {
  totalImpact: CreditImpact;
  weeklyImpact: CreditImpact;
  goals: Array<{
    id: string;
    name: string;
    target: number;
    current: number;
    unit: 'trees' | 'co2_kg';
  }>;
  partnerIntegrations: Array<{
    name: string;
    type: 'tree_planting' | 'carbon_offset' | 'renewable_energy';
    contribution: number;
  }>;
}

