/**
 * Crystal Ball Simulator Service
 * Predicts the impact of future financial actions on credit score
 */

import { 
  CreditSnapshot, 
  FinancialAction, 
  SimulationResult,
  CreditUtilization,
} from '../types/CreditTypes';
import { getMerchantIntelligence } from './MerchantIntelligenceService';

// Simulation Constants
const SCORE_GRAVITY = {
  UTILIZATION_BUMP: 0.5, // Points lost per % increase over 30%
  INTEREST_RATE: 0.22, // Average APR for simulation (22%)
  RECOVERY_SPEED: 1.2, // Months to recover per point lost
  INQUIRY_HIT: -10, // Points lost per hard inquiry
  NEW_ACCOUNT_AGE_PENALTY: -5, // Points lost for decreasing average age
  DEBT_CONSOLIDATION_BOOST: 35, // Points gained from consolidating CC debt
};

/**
 * Simulate the impact of a financial action
 */
export const simulateFinancialAction = (
  currentData: CreditSnapshot,
  action: FinancialAction
): SimulationResult => {
  // Clone data to avoid mutating real state
  const futureState: Partial<CreditSnapshot> = JSON.parse(JSON.stringify(currentData));
  
  let scoreDelta = 0;
  let projectedUtilization = currentData.utilization.currentUtilization;
  let monthlyInterestLeak = 0;
  let recoveryMonths = 0;
  let insight = '';
  let zeroGravityOption;
  let opportunityCost;
  
  const currentScore = currentData.score.score;
  const currentBalance = currentData.utilization.totalBalance;
  const creditLimit = currentData.utilization.totalLimit;
  
  switch (action.type) {
    case 'LARGE_PURCHASE': {
      const projectedBalance = currentBalance + action.amount;
      projectedUtilization = projectedBalance / creditLimit;
      
      // Check for merchant intelligence (0% APR option)
      if (action.merchant) {
        const merchantDeal = getMerchantIntelligence(action.merchant);
        if (merchantDeal && merchantDeal.apr === 0) {
          zeroGravityOption = {
            merchant: merchantDeal.name,
            option: merchantDeal.option,
            benefit: merchantDeal.benefit,
            interestLeak: 0,
          };
          // With 0% APR, no interest leak, but utilization still impacts score
          monthlyInterestLeak = 0;
        } else {
          // Standard card APR applies
          monthlyInterestLeak = (action.amount * SCORE_GRAVITY.INTEREST_RATE) / 12;
        }
      } else {
        // No merchant specified, assume standard APR
        monthlyInterestLeak = (action.amount * SCORE_GRAVITY.INTEREST_RATE) / 12;
      }
      
      // Calculate score impact based on utilization brackets
      if (projectedUtilization > 0.5) {
        scoreDelta = -45;
      } else if (projectedUtilization > 0.3) {
        scoreDelta = -20;
      } else if (projectedUtilization > 0.1) {
        scoreDelta = -5;
      }
      
      // Calculate opportunity cost (guaranteed return by avoiding interest)
      if (monthlyInterestLeak > 0) {
        const annualInterest = monthlyInterestLeak * 12;
        const guaranteedReturn = (annualInterest / action.amount) * 100;
        opportunityCost = {
          guaranteedReturn: Math.min(100, guaranteedReturn), // Cap at 100%
          totalInterestSaved: annualInterest,
        };
      }
      
      insight = `This purchase puts you at ${(projectedUtilization * 100).toFixed(0)}% utilization.`;
      
      if (zeroGravityOption) {
        insight += ` However, using ${zeroGravityOption.option} eliminates interest costs entirely.`;
      }
      
      break;
    }
    
    case 'NEW_CREDIT_LINE': {
      scoreDelta = SCORE_GRAVITY.INQUIRY_HIT;
      
      // Decrease average account age (simplified calculation)
      if (currentData.accountAges && currentData.accountAges.length > 0) {
        const currentAvgAge = currentData.accountAges.reduce((sum, a) => sum + a.ageMonths, 0) / currentData.accountAges.length;
        const newAvgAge = (currentAvgAge * currentData.accountAges.length) / (currentData.accountAges.length + 1);
        if (newAvgAge < currentAvgAge * 0.9) {
          scoreDelta += SCORE_GRAVITY.NEW_ACCOUNT_AGE_PENALTY;
        }
      } else {
        scoreDelta += SCORE_GRAVITY.NEW_ACCOUNT_AGE_PENALTY;
      }
      
      insight = 'New inquiries cause a temporary dip, but your total limit will increase, improving utilization long-term.';
      recoveryMonths = Math.ceil(Math.abs(scoreDelta) / SCORE_GRAVITY.RECOVERY_SPEED);
      break;
    }
    
    case 'DEBT_CONSOLIDATION': {
      // Moving CC debt to installment loan
      scoreDelta = SCORE_GRAVITY.DEBT_CONSOLIDATION_BOOST;
      
      // Recalculate utilization (debt moves off revolving credit)
      const newBalance = Math.max(0, currentBalance - action.amount);
      projectedUtilization = newBalance / creditLimit;
      
      // Calculate interest savings
      const oldMonthlyInterest = (currentBalance * SCORE_GRAVITY.INTEREST_RATE) / 12;
      const newMonthlyInterest = (action.amount * 0.10) / 12; // Assume 10% personal loan APR
      const monthlySavings = oldMonthlyInterest - newMonthlyInterest;
      
      monthlyInterestLeak = -monthlySavings; // Negative = savings
      
      opportunityCost = {
        guaranteedReturn: (monthlySavings * 12 / action.amount) * 100,
        totalInterestSaved: monthlySavings * 12,
      };
      
      insight = 'Converting CC debt to a loan lowers utilization instantly and saves on interest.';
      break;
    }
    
    case 'PAYMENT': {
      const newBalance = Math.max(0, currentBalance - action.amount);
      projectedUtilization = newBalance / creditLimit;
      
      // Score improvement from lower utilization
      if (currentData.utilization.currentUtilization > 0.3 && projectedUtilization <= 0.3) {
        scoreDelta = 20; // Moving from high to optimal utilization
      } else if (currentData.utilization.currentUtilization > 0.5 && projectedUtilization <= 0.5) {
        scoreDelta = 15;
      } else if (projectedUtilization < currentData.utilization.currentUtilization) {
        scoreDelta = Math.round((currentData.utilization.currentUtilization - projectedUtilization) * 100 * 0.5);
      }
      
      // Calculate interest savings
      const interestSaved = (action.amount * SCORE_GRAVITY.INTEREST_RATE) / 12;
      monthlyInterestLeak = -interestSaved;
      
      opportunityCost = {
        guaranteedReturn: (interestSaved * 12 / action.amount) * 100,
        totalInterestSaved: interestSaved * 12,
      };
      
      insight = `Paying $${action.amount.toFixed(0)} reduces utilization to ${(projectedUtilization * 100).toFixed(0)}% and saves $${interestSaved.toFixed(2)}/month in interest.`;
      break;
    }
    
    case 'BALANCE_TRANSFER': {
      // Moving balance to 0% APR card
      projectedUtilization = currentData.utilization.currentUtilization; // Utilization stays same
      
      // Interest savings
      const oldMonthlyInterest = (action.amount * SCORE_GRAVITY.INTEREST_RATE) / 12;
      monthlyInterestLeak = -oldMonthlyInterest; // Negative = savings
      
      opportunityCost = {
        guaranteedReturn: (oldMonthlyInterest * 12 / action.amount) * 100,
        totalInterestSaved: oldMonthlyInterest * 12,
      };
      
      insight = `Transferring to a 0% APR card saves $${oldMonthlyInterest.toFixed(2)}/month in interest.`;
      break;
    }
  }
  
  // Calculate recovery time
  if (scoreDelta < 0) {
    recoveryMonths = Math.ceil(Math.abs(scoreDelta) / SCORE_GRAVITY.RECOVERY_SPEED);
  }
  
  // Update future state
  if (futureState.utilization) {
    futureState.utilization.currentUtilization = projectedUtilization;
    futureState.utilization.totalBalance = currentBalance + (action.type === 'LARGE_PURCHASE' ? action.amount : 
                                                             action.type === 'PAYMENT' ? -action.amount : 0);
  }
  
  return {
    projectedScore: Math.max(300, Math.min(850, currentScore + scoreDelta)),
    scoreDelta,
    projectedUtilization,
    monthlyInterestLeak,
    recoveryMonths,
    futureState,
    insight,
    zeroGravityOption,
    opportunityCost,
  };
};

/**
 * Calculate spending velocity and predict statement utilization
 */
export const calculateSpendingVelocity = (
  currentBalance: number,
  cycleStartBalance: number,
  daysIntoCycle: number,
  daysUntilStatement: number,
  creditLimit: number
): {
  velocity: number;
  projectedUtilization: number;
  projectedBalance: number;
  velocityMultiplier: number;
} => {
  const cycleSpend = currentBalance - cycleStartBalance;
  const dailySpendRate = cycleSpend / Math.max(1, daysIntoCycle);
  const velocity = (dailySpendRate / creditLimit) * 100; // % of limit per day
  
  // Project to statement date
  const projectedSpend = dailySpendRate * daysUntilStatement;
  const projectedBalance = currentBalance + projectedSpend;
  const projectedUtilization = projectedBalance / creditLimit;
  
  // Compare to historical average (simplified - in production, use 6-month average)
  const historicalAverageVelocity = 0.5; // 0.5% of limit per day
  const velocityMultiplier = velocity / historicalAverageVelocity;
  
  return {
    velocity,
    projectedUtilization,
    projectedBalance,
    velocityMultiplier,
  };
};

