/**
 * Utilities for converting AAVE account data to AAVEPosition format
 * and calculating position metrics
 */

import type { AAVEPosition } from '../../components/crypto/PositionManagementModal';

export interface AAVEAccountData {
  supplies: Array<{
    symbol: string;
    quantity: number;
    useAsCollateral: boolean;
    reserve: {
      ltv: number;
      liquidationThreshold: number;
      variableBorrowApy?: number;
      stableBorrowApy?: number;
    };
  }>;
  borrows: Array<{
    symbol: string;
    amount: number;
    rateMode: 'VARIABLE' | 'STABLE';
    apyAtOpen?: number;
    reserve: {
      ltv: number;
      liquidationThreshold: number;
      variableBorrowApy?: number;
      stableBorrowApy?: number;
    };
  }>;
  pricesUsd: Record<string, number>;
  healthFactor: number;
  collateralUsd: number;
  debtUsd: number;
  ltvWeighted: number;
  liqThresholdWeighted: number;
}

export interface WalletBalances {
  [symbol: string]: {
    walletUsd: number;
    aTokenUsd: number;
  };
}

/**
 * Convert AAVE account data to AAVEPosition array
 * Groups by reserve symbol and calculates position metrics
 */
export function convertToAAVEPositions(
  accountData: AAVEAccountData,
  walletBalances?: WalletBalances
): AAVEPosition[] {
  const positions: AAVEPosition[] = [];
  const reserveMap = new Map<string, AAVEPosition>();

  // Process supplies (collateral)
  accountData.supplies.forEach(supply => {
    const symbol = supply.symbol;
    const price = accountData.pricesUsd[symbol] || 0;
    const collateralUsd = supply.quantity * price;

    if (!reserveMap.has(symbol)) {
      reserveMap.set(symbol, {
        id: `supply-${symbol}`,
        reserveSymbol: symbol,
        debtUsd: 0,
        collateralAmount: 0,
        collateralUsd: 0,
        ltv: supply.reserve.ltv,
        liqThreshold: supply.reserve.liquidationThreshold,
        healthFactor: Infinity,
        variableApr: supply.reserve.variableBorrowApy,
        stableApr: supply.reserve.stableBorrowApy,
        walletBalanceUsd: walletBalances?.[symbol]?.walletUsd,
        aTokenBalanceUsd: walletBalances?.[symbol]?.aTokenUsd,
      });
    }

    const position = reserveMap.get(symbol)!;
    position.collateralAmount += supply.quantity;
    position.collateralUsd += collateralUsd;
  });

  // Process borrows (debt)
  accountData.borrows.forEach(borrow => {
    const symbol = borrow.symbol;
    const price = accountData.pricesUsd[symbol] || 0;
    const debtUsd = borrow.amount * price;

    if (!reserveMap.has(symbol)) {
      reserveMap.set(symbol, {
        id: `borrow-${symbol}`,
        reserveSymbol: symbol,
        debtUsd: 0,
        collateralAmount: 0,
        collateralUsd: 0,
        ltv: borrow.reserve.ltv,
        liqThreshold: borrow.reserve.liquidationThreshold,
        healthFactor: Infinity,
        variableApr: borrow.reserve.variableBorrowApy,
        stableApr: borrow.reserve.stableBorrowApy,
        walletBalanceUsd: walletBalances?.[symbol]?.walletUsd,
        aTokenBalanceUsd: walletBalances?.[symbol]?.aTokenUsd,
      });
    }

    const position = reserveMap.get(symbol)!;
    position.debtUsd += debtUsd;
    position.debtMode = borrow.rateMode.toLowerCase() as 'variable' | 'stable';
  });

  // Calculate health factors for each position
  reserveMap.forEach(position => {
    if (position.debtUsd > 0) {
      position.healthFactor = (position.collateralUsd * position.liqThreshold) / position.debtUsd;
    } else {
      position.healthFactor = Infinity;
    }
  });

  return Array.from(reserveMap.values());
}

/**
 * Calculate estimated health factor after repay
 */
export function calculateHealthFactorAfterRepay(
  collateralUsd: number,
  currentDebtUsd: number,
  repayAmountUsd: number,
  liquidationThreshold: number
): number {
  const newDebtUsd = Math.max(0, currentDebtUsd - repayAmountUsd);
  
  if (newDebtUsd <= 0) {
    return Infinity;
  }
  
  return (collateralUsd * liquidationThreshold) / newDebtUsd;
}

/**
 * Calculate estimated LTV after repay
 */
export function calculateLTVAfterRepay(
  collateralUsd: number,
  currentDebtUsd: number,
  repayAmountUsd: number
): number {
  const newDebtUsd = Math.max(0, currentDebtUsd - repayAmountUsd);
  
  if (collateralUsd <= 0) {
    return 0;
  }
  
  return (newDebtUsd / collateralUsd) * 100;
}

/**
 * Calculate available borrow capacity after repay
 */
export function calculateBorrowCapacityAfterRepay(
  collateralUsd: number,
  currentDebtUsd: number,
  repayAmountUsd: number,
  ltv: number
): number {
  const newDebtUsd = Math.max(0, currentDebtUsd - repayAmountUsd);
  const borrowCap = collateralUsd * ltv;
  
  return Math.max(0, borrowCap - newDebtUsd);
}

/**
 * Validate repay amount
 */
export function validateRepayAmount(
  amount: number,
  maxDebt: number,
  walletBalance?: number,
  aTokenBalance?: number,
  source: 'wallet' | 'aTokens' = 'wallet'
): { isValid: boolean; error?: string } {
  if (!isFinite(amount) || amount <= 0) {
    return { isValid: false, error: 'Enter a valid amount' };
  }
  
  if (amount < 10) {
    return { isValid: false, error: 'Minimum repayment is $10' };
  }
  
  if (amount > maxDebt) {
    return { isValid: false, error: 'Amount exceeds outstanding debt' };
  }
  
  if (source === 'wallet' && walletBalance != null && amount > walletBalance) {
    return { isValid: false, error: 'Insufficient wallet balance' };
  }
  
  if (source === 'aTokens' && aTokenBalance != null && amount > aTokenBalance) {
    return { isValid: false, error: 'Insufficient aToken balance' };
  }
  
  return { isValid: true };
}

/**
 * Get risk tier from health factor
 */
export function getRiskTier(healthFactor: number): 'SAFE' | 'WARN' | 'AT_RISK' | 'LIQUIDATE' {
  if (!isFinite(healthFactor) || healthFactor > 1.5) return 'SAFE';
  if (healthFactor > 1.2) return 'WARN';
  if (healthFactor > 1.0) return 'AT_RISK';
  return 'LIQUIDATE';
}

/**
 * Get risk tier color
 */
export function getRiskTierColor(tier: 'SAFE' | 'WARN' | 'AT_RISK' | 'LIQUIDATE'): string {
  const colors = {
    SAFE: '#10B981',
    WARN: '#F59E0B',
    AT_RISK: '#DC2626',
    LIQUIDATE: '#7C2D12'
  };
  return colors[tier] || '#6B7280';
}

/**
 * Format health factor for display
 */
export function formatHealthFactor(hf: number): string {
  if (!isFinite(hf)) return '∞';
  return hf.toFixed(2);
}

/**
 * Format percentage for display
 */
export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(0)}%`;
}

/**
 * Format USD for display
 */
export function formatUSD(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2
  }).format(Math.max(0, amount || 0));
}
