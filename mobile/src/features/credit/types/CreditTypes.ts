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

