/**
 * Formatting utilities for currency, percentages, and numbers
 */

export const fmtUsd = (n: number): string => {
  return new Intl.NumberFormat('en-US', { 
    style: 'currency', 
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(n);
};

export const fmtPercent = (n: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 0,
    maximumFractionDigits: 1
  }).format(n / 100);
};

export const fmtNumber = (n: number, decimals: number = 2): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals
  }).format(n);
};

export const fmtCompact = (n: number): string => {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(n);
};

export const fmtCrypto = (n: number, symbol: string = 'BTC', decimals: number = 8): string => {
  return `${new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals
  }).format(n)} ${symbol}`;
};