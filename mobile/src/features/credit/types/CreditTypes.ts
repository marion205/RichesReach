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
  // New: Velocity tracking
  spendingVelocity?: number; // % of limit spent per day in current cycle
  historicalAverageVelocity?: number; // 6-month average
  projectedUtilizationAtStatement?: number; // Predicted utilization at statement date
  statementDate?: string; // ISO date
}

// Credit Velocity & Behavioral Tracking
export interface SpendingVelocity {
  currentCycleSpend: number;
  daysIntoCycle: number;
  projectedCycleEndSpend: number;
  projectedUtilization: number; // Predicted utilization at statement date
  velocityMultiplier: number; // Current velocity / historical average
  statementDate: string;
  daysUntilStatement: number;
}

export interface BehavioralShadowScore {
  paymentEfficiency: number; // Days between statement and payment (lower = better)
  paymentTrend: 'improving' | 'stable' | 'declining';
  behavioralAlpha: number; // Composite score of financial habits
  efficiencyMilestones: Array<{
    id: string;
    name: string;
    date: string;
    improvement: number;
  }>;
  lastPaymentEfficiency: number; // Days to pay last statement
  averagePaymentEfficiency: number; // 6-month average
}

// Macro-Economic Sentiment
export interface MacroEconomicData {
  fedRate: number;
  rateTrend: 'rising' | 'stable' | 'falling';
  inflationRate: number;
  lastUpdated: string;
  recommendationShift: 'liquidity' | 'revolving' | 'neutral';
}

// Crystal Ball Simulation
export interface FinancialAction {
  type: 'LARGE_PURCHASE' | 'NEW_CREDIT_LINE' | 'DEBT_CONSOLIDATION' | 'PAYMENT' | 'BALANCE_TRANSFER';
  amount: number;
  merchant?: string;
  description?: string;
  targetCardId?: string;
}

export interface SimulationResult {
  projectedScore: number;
  scoreDelta: number;
  projectedUtilization: number;
  monthlyInterestLeak: number;
  recoveryMonths: number;
  futureState: Partial<CreditSnapshot>;
  insight: string;
  zeroGravityOption?: {
    merchant: string;
    option: string;
    benefit: string;
    interestLeak: number; // Should be 0
  };
  opportunityCost?: {
    guaranteedReturn: number; // % return by avoiding interest
    totalInterestSaved: number;
  };
}

// Merchant Intelligence
export interface MerchantDeal {
  name: string;
  option: string;
  benefit: string;
  impact: string;
  apr: number; // 0 for 0% offers
  termMonths: number;
  eligibility?: string;
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
  // New: Enhanced tracking
  spendingVelocity?: SpendingVelocity;
  behavioralShadow?: BehavioralShadowScore;
  macroEconomic?: MacroEconomicData;
  recentInquiries?: number;
  accountAges?: Array<{
    cardId: string;
    ageMonths: number;
    isOldest: boolean;
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
  source: 'crowdsourced' | 'ai' | 'market_data' | 'real_time' | 'ai_behavioral_model' | 'velocity_tracker';
  location?: string; // city/region
  affectedFactors: string[];
  recommendation: string;
  priority?: number; // 1-10, higher = more critical (for sorting/filtering)
  // New: Predictive fields
  prediction?: string; // e.g., "Predicted Score Change: -15pts"
  urgency?: 'critical' | 'high' | 'medium' | 'low';
  interestLeak?: number; // Monthly interest cost
  recoveryTime?: string; // e.g., "4 months"
  behavioralAlpha?: number; // Shadow score metric
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

