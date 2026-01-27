/**
 * Debt Burn-Down Service
 * Calculates month-by-month score recovery trajectory
 */

import { CreditSnapshot } from '../types/CreditTypes';

export interface BurnDownMonth {
  month: number;
  monthLabel: string;
  balance: number;
  score: number;
  scoreChange: number;
  utilization: number;
  milestone?: {
    type: 'elite' | 'healthy' | 'behavioral_alpha' | 'halfway' | 'debt_free';
    message: string;
    scoreBoost: number;
  };
  interestSaved: number;
  cumulativeInterestSaved: number;
}

export interface BurnDownSchedule {
  months: BurnDownMonth[];
  totalMonths: number;
  finalScore: number;
  totalInterestSaved: number;
  targetDate: string; // ISO date
  monthlyPayment: number;
  strategy: 'aggressive' | 'moderate' | 'conservative';
}

/**
 * Calculate burn-down schedule with FICO 10 logic
 */
export const calculateBurnDownSchedule = (
  snapshot: CreditSnapshot,
  monthlyPayment: number,
  strategy: 'aggressive' | 'moderate' | 'conservative' = 'moderate'
): BurnDownSchedule => {
  const currentBalance = snapshot.utilization.totalBalance;
  const totalLimit = snapshot.utilization.totalLimit;
  const currentScore = snapshot.score.score;
  
  let remainingBalance = currentBalance;
  let projectedScore = currentScore;
  const months: BurnDownMonth[] = [];
  let cumulativeInterestSaved = 0;
  
  // Calculate monthly interest saved (assuming 24% APR)
  const monthlyInterestRate = 0.24 / 12;
  const monthlyInterestSaved = remainingBalance * monthlyInterestRate;
  
  let monthsElapsed = 0;
  const maxMonths = 24; // 2-year projection
  
  // Initial dip from transfer (inquiry + fee impact)
  if (monthsElapsed === 0) {
    projectedScore -= 10; // Inquiry hit
    monthsElapsed++;
    months.push({
      month: monthsElapsed,
      monthLabel: `Month ${monthsElapsed}`,
      balance: remainingBalance,
      score: Math.max(300, Math.min(850, Math.floor(projectedScore))),
      scoreChange: -10,
      utilization: (remainingBalance / totalLimit) * 100,
      milestone: {
        type: 'behavioral_alpha',
        message: 'Migration initiated. Temporary score dip from inquiry.',
        scoreBoost: -10,
      },
      interestSaved: 0,
      cumulativeInterestSaved: 0,
    });
  }
  
  while (remainingBalance > 0 && monthsElapsed < maxMonths) {
    monthsElapsed++;
    
    // Apply payment
    remainingBalance = Math.max(0, remainingBalance - monthlyPayment);
    const utilization = (remainingBalance / totalLimit) * 100;
    
    // Calculate interest saved this month
    const interestThisMonth = remainingBalance * monthlyInterestRate;
    cumulativeInterestSaved += interestThisMonth;
    
    // Score recovery logic (FICO 10 model)
    let scoreBoost = 0;
    let milestone;
    
    // Utilization milestone boosts
    if (utilization < 10 && monthsElapsed > 1) {
      scoreBoost += 5; // "Elite" boost
      milestone = {
        type: 'elite' as const,
        message: 'Elite Utilization: Below 10% threshold',
        scoreBoost: 5,
      };
    } else if (utilization < 30 && monthsElapsed > 1) {
      scoreBoost += 3; // "Healthy" boost
      milestone = {
        type: 'healthy' as const,
        message: 'Healthy Utilization: Below 30% threshold',
        scoreBoost: 3,
      };
    }
    
    // Behavioral Alpha boost (consistent payments)
    if (monthsElapsed >= 3 && monthsElapsed % 3 === 0) {
      scoreBoost += 2; // Consistency bonus
      if (!milestone) {
        milestone = {
          type: 'behavioral_alpha' as const,
          message: 'Behavioral Alpha: 3-month on-time payment streak',
          scoreBoost: 2,
        };
      }
    }
    
    // Halfway milestone
    if (remainingBalance <= currentBalance / 2 && !months.some(m => m.milestone?.type === 'halfway')) {
      scoreBoost += 5;
      milestone = {
        type: 'halfway' as const,
        message: 'Halfway Milestone: 50% of debt paid off',
        scoreBoost: 5,
      };
    }
    
    // Debt-free milestone
    if (remainingBalance <= 0) {
      scoreBoost += 10;
      milestone = {
        type: 'debt_free' as const,
        message: '🎉 DEBT FREE! Zero balance achieved',
        scoreBoost: 10,
      };
    }
    
    // Monthly consistency boost
    scoreBoost += 1.5;
    
    projectedScore += scoreBoost;
    const scoreChange = monthsElapsed === 1 ? -10 : scoreBoost;
    
    months.push({
      month: monthsElapsed,
      monthLabel: `Month ${monthsElapsed}`,
      balance: Math.max(0, remainingBalance),
      score: Math.max(300, Math.min(850, Math.floor(projectedScore))),
      scoreChange,
      utilization,
      milestone,
      interestSaved: interestThisMonth,
      cumulativeInterestSaved,
    });
    
    if (remainingBalance <= 0) break;
  }
  
  // Calculate target date
  const targetDate = new Date();
  targetDate.setMonth(targetDate.getMonth() + monthsElapsed);
  
  return {
    months,
    totalMonths: monthsElapsed,
    finalScore: months[months.length - 1]?.score || currentScore,
    totalInterestSaved: cumulativeInterestSaved,
    targetDate: targetDate.toISOString(),
    monthlyPayment,
    strategy,
  };
};

/**
 * Calculate optimal monthly payment
 */
export const calculateOptimalPayment = (
  balance: number,
  promoMonths: number,
  strategy: 'aggressive' | 'moderate' | 'conservative'
): number => {
  // Aggressive: Pay off 2 months before promo ends
  // Moderate: Pay off 1 month before promo ends
  // Conservative: Pay off by promo end
  const bufferMonths = strategy === 'aggressive' ? 2 : strategy === 'moderate' ? 1 : 0;
  const targetMonths = promoMonths - bufferMonths;
  
  return Math.ceil(balance / targetMonths);
};

