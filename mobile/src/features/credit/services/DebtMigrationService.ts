/**
 * Debt Migration Intelligence Service
 * 2026 Zero-Gravity Balance Transfer Strategy Engine
 */

import { CreditSnapshot, MerchantDeal } from '../types/CreditTypes';

// 2026 Zero-Gravity Strategy Cards Database
export interface ZeroGravityCard {
  id: string;
  name: string;
  issuer: string;
  promoMonths: number;
  transferFee: number; // 0-1 (e.g., 0.03 = 3%)
  purchaseAPR: number; // APR after promo ends
  minTransfer: number;
  maxTransfer: number;
  eligibility: string;
  strategy: 'max_time' | 'debt_payoff' | 'purchases' | 'fee_averse';
  cashback?: number; // % cashback if applicable
  lateFeeProtection: boolean;
  gracePeriodOnPurchases: boolean; // Critical: Can you use card for purchases during BT?
  activationWindow: number; // Days to initiate transfer
}

export const ZERO_GRAVITY_CARDS_2026: ZeroGravityCard[] = [
  {
    id: 'us-bank-shield',
    name: 'U.S. Bank Shield™ Visa®',
    issuer: 'U.S. Bank',
    promoMonths: 24,
    transferFee: 0.03, // 3%
    purchaseAPR: 0.28, // 28% after promo
    minTransfer: 500,
    maxTransfer: 15000,
    eligibility: 'Good credit (670+)',
    strategy: 'max_time',
    lateFeeProtection: true,
    gracePeriodOnPurchases: false, // ⚠️ CRITICAL: No grace period during BT
    activationWindow: 60,
  },
  {
    id: 'wells-fargo-reflect',
    name: 'Wells Fargo Reflect®',
    issuer: 'Wells Fargo',
    promoMonths: 21,
    transferFee: 0.03, // 3%
    purchaseAPR: 0.27, // 27% after promo
    minTransfer: 1000,
    maxTransfer: 20000,
    eligibility: 'Good credit (670+)',
    strategy: 'debt_payoff',
    lateFeeProtection: false,
    gracePeriodOnPurchases: false,
    activationWindow: 60,
  },
  {
    id: 'chase-freedom-unlimited',
    name: 'Chase Freedom Unlimited®',
    issuer: 'Chase',
    promoMonths: 15,
    transferFee: 0.05, // 5% (higher fee)
    purchaseAPR: 0.25, // 25% after promo
    minTransfer: 500,
    maxTransfer: 15000,
    eligibility: 'Good credit (670+)',
    strategy: 'purchases',
    cashback: 0.015, // 1.5% cashback
    lateFeeProtection: false,
    gracePeriodOnPurchases: true, // ✅ Can use for purchases
    activationWindow: 60,
  },
  {
    id: 'citi-simplicity',
    name: 'Citi Simplicity®',
    issuer: 'Citi',
    promoMonths: 21,
    transferFee: 0.03, // 3%
    purchaseAPR: 0.29, // 29% after promo
    minTransfer: 500,
    maxTransfer: 15000,
    eligibility: 'Fair credit (580+)',
    strategy: 'fee_averse',
    lateFeeProtection: true, // No late fees ever
    gracePeriodOnPurchases: false,
    activationWindow: 60,
  },
  {
    id: 'discover-it',
    name: 'Discover it® Balance Transfer',
    issuer: 'Discover',
    promoMonths: 18,
    transferFee: 0.03, // 3%
    purchaseAPR: 0.24, // 24% after promo
    minTransfer: 500,
    maxTransfer: 10000,
    eligibility: 'Good credit (670+)',
    strategy: 'debt_payoff',
    cashback: 0.01, // 1% cashback
    lateFeeProtection: false,
    gracePeriodOnPurchases: true,
    activationWindow: 60,
  },
];

/**
 * Calculate migration value and ROI
 */
export const calculateMigrationValue = (
  balance: number,
  currentAPR: number,
  targetCard: ZeroGravityCard
): {
  annualInterest: number;
  interestSavedOverPromo: number;
  transferFee: number;
  netSavings: number;
  roiPercent: number;
  monthlyCashFlowBoost: number;
  breakEvenMonths: number;
  totalInterestAvoided: number;
} => {
  const annualInterest = balance * (currentAPR / 100);
  const monthlyInterest = annualInterest / 12;
  const interestSavedOverPromo = monthlyInterest * targetCard.promoMonths;
  
  const transferFee = balance * targetCard.transferFee;
  const netSavings = interestSavedOverPromo - transferFee;
  const roiPercent = transferFee > 0 ? (netSavings / transferFee) * 100 : Infinity;
  
  // Break-even: How many months until transfer fee is paid back by interest savings
  const breakEvenMonths = transferFee / monthlyInterest;
  
  return {
    annualInterest,
    interestSavedOverPromo,
    transferFee,
    netSavings,
    roiPercent,
    monthlyCashFlowBoost: monthlyInterest,
    breakEvenMonths: Math.ceil(breakEvenMonths),
    totalInterestAvoided: interestSavedOverPromo,
  };
};

/**
 * Find best migration card based on strategy
 */
export const findBestMigrationCard = (
  balance: number,
  currentAPR: number,
  strategy: 'max_time' | 'debt_payoff' | 'purchases' | 'fee_averse' | 'best_roi'
): {
  card: ZeroGravityCard;
  value: ReturnType<typeof calculateMigrationValue>;
} | null => {
  if (balance <= 0) return null;
  
  let eligibleCards = ZERO_GRAVITY_CARDS_2026.filter(
    card => balance >= card.minTransfer && balance <= card.maxTransfer
  );
  
  if (eligibleCards.length === 0) return null;
  
  // Filter by strategy
  if (strategy !== 'best_roi') {
    eligibleCards = eligibleCards.filter(card => card.strategy === strategy);
  }
  
  if (eligibleCards.length === 0) return null;
  
  // Calculate value for each card
  const cardValues = eligibleCards.map(card => ({
    card,
    value: calculateMigrationValue(balance, currentAPR, card),
  }));
  
  // Sort by best ROI or strategy-specific metric
  if (strategy === 'best_roi' || strategy === 'debt_payoff') {
    cardValues.sort((a, b) => b.value.roiPercent - a.value.roiPercent);
  } else if (strategy === 'max_time') {
    cardValues.sort((a, b) => b.card.promoMonths - a.card.promoMonths);
  } else if (strategy === 'purchases') {
    cardValues.sort((a, b) => (b.card.cashback || 0) - (a.card.cashback || 0));
  } else if (strategy === 'fee_averse') {
    cardValues.sort((a, b) => a.value.transferFee - b.value.transferFee);
  }
  
  return cardValues[0];
};

/**
 * Check if user should consider debt migration
 */
export const shouldConsiderMigration = (
  snapshot: CreditSnapshot
): {
  shouldMigrate: boolean;
  monthlyInterestLeak: number;
  threshold: number;
  reason?: string;
} => {
  const threshold = 50; // $50/month interest leak threshold
  const currentAPR = 0.24; // Assume 24% average APR (in production, get from cards)
  const monthlyInterest = (snapshot.utilization.totalBalance * currentAPR) / 12;
  
  if (monthlyInterest < threshold) {
    return {
      shouldMigrate: false,
      monthlyInterestLeak: monthlyInterest,
      threshold,
      reason: `Your monthly interest ($${monthlyInterest.toFixed(2)}) is below the migration threshold.`,
    };
  }
  
  // Check if balance is high enough to benefit
  if (snapshot.utilization.totalBalance < 1000) {
    return {
      shouldMigrate: false,
      monthlyInterestLeak: monthlyInterest,
      threshold,
      reason: 'Balance too low for migration to be cost-effective.',
    };
  }
  
  return {
    shouldMigrate: true,
    monthlyInterestLeak: monthlyInterest,
    threshold,
  };
};

/**
 * Generate migration guardrails checklist
 */
export const generateMigrationChecklist = (
  sourceCardId: string,
  targetCard: ZeroGravityCard,
  snapshot: CreditSnapshot
): Array<{
  id: string;
  title: string;
  description: string;
  critical: boolean;
  completed: boolean;
}> => {
  const sourceCard = snapshot.cards.find(c => c.id === sourceCardId);
  const sameIssuer = sourceCard && targetCard.issuer.toLowerCase().includes(
    sourceCard.name.toLowerCase().split(' ')[0]
  );
  
  return [
    {
      id: '1',
      title: 'Stop Spending on Source Card',
      description: 'Freeze the card you\'re moving debt FROM. Interest on new purchases can get messy during transfer.',
      critical: true,
      completed: false,
    },
    {
      id: '2',
      title: 'Confirm "Same-Issuer" Rule',
      description: sameIssuer 
        ? `⚠️ WARNING: Both cards are from ${targetCard.issuer}. You cannot transfer between cards from the same bank.`
        : `✅ Verified: Source and target cards are from different issuers.`,
      critical: true,
      completed: !sameIssuer,
    },
    {
      id: '3',
      title: '14-Day Overlap Rule',
      description: 'Keep making minimum payments on your OLD card until you see $0 balance. Most interest leaks happen during the 5-14 day transfer window.',
      critical: true,
      completed: false,
    },
    {
      id: '4',
      title: 'Activate "No-Spend Zone"',
      description: targetCard.gracePeriodOnPurchases
        ? `✅ This card allows purchases during BT. You can still use it for daily spending.`
        : `⚠️ CRITICAL: Never use this card for purchases. It loses grace period during balance transfer, meaning you'll pay interest on new purchases even if paid in full.`,
      critical: !targetCard.gracePeriodOnPurchases,
      completed: false,
    },
    {
      id: '5',
      title: '60-Day Activation Window',
      description: `You must initiate the transfer within ${targetCard.activationWindow} days of account opening. Set a reminder now!`,
      critical: true,
      completed: false,
    },
    {
      id: '6',
      title: 'Set "Hard Exit" Date',
      description: `Put a calendar alert for 30 days BEFORE the promo ends (${targetCard.promoMonths} months from now). Standard APR of ${(targetCard.purchaseAPR * 100).toFixed(0)}% will apply after.`,
      critical: true,
      completed: false,
    },
    {
      id: '7',
      title: 'Set Up Autopay Immediately',
      description: 'A single late payment kills the 0% deal. Set autopay for minimum payment as soon as the card is activated.',
      critical: true,
      completed: false,
    },
  ];
};

