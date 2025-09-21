// Enhanced formatting utilities with precision & accessibility
import { Decimal } from 'decimal.js';

// Currency formatting with proper precision
export const fmtUsd = (n: number | string | Decimal, options?: {
  showSign?: boolean;
  precision?: number;
  masked?: boolean;
}): string => {
  const { showSign = false, precision = 2, masked = false } = options || {};
  
  if (masked) return '•••••';
  
  const value = typeof n === 'string' ? parseFloat(n) : typeof n === 'number' ? n : n.toNumber();
  
  if (!Number.isFinite(value)) return '$0.00';
  
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
    signDisplay: showSign ? 'always' : 'auto',
  }).format(value);
  
  return formatted;
};

// Percentage formatting
export const fmtPercent = (n: number | string, options?: {
  showSign?: boolean;
  precision?: number;
  masked?: boolean;
}): string => {
  const { showSign = true, precision = 2, masked = false } = options || {};
  
  if (masked) return '•••••';
  
  const value = typeof n === 'string' ? parseFloat(n) : n;
  
  if (!Number.isFinite(value)) return '0.00%';
  
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
    signDisplay: showSign ? 'always' : 'auto',
  }).format(value / 100);
  
  return formatted;
};

// Number formatting with proper precision
export const fmtNumber = (n: number | string | Decimal, options?: {
  precision?: number;
  masked?: boolean;
  compact?: boolean;
}): string => {
  const { precision = 2, masked = false, compact = false } = options || {};
  
  if (masked) return '•••••';
  
  const value = typeof n === 'string' ? parseFloat(n) : typeof n === 'number' ? n : n.toNumber();
  
  if (!Number.isFinite(value)) return '0';
  
  if (compact && Math.abs(value) >= 1000) {
    return new Intl.NumberFormat('en-US', {
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value);
  }
  
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
  }).format(value);
};

// Crypto quantity formatting with proper precision
export const fmtCryptoQty = (qty: number | string | Decimal, symbol: string, options?: {
  masked?: boolean;
  maxDecimals?: number;
}): string => {
  const { masked = false, maxDecimals = 8 } = options || {};
  
  if (masked) return '•••••';
  
  const value = typeof qty === 'string' ? parseFloat(qty) : typeof qty === 'number' ? qty : qty.toNumber();
  
  if (!Number.isFinite(value)) return '0';
  
  // Determine precision based on symbol
  const precision = getCryptoPrecision(symbol, maxDecimals);
  
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: precision,
  }).format(value);
};

// Get appropriate precision for crypto symbol
const getCryptoPrecision = (symbol: string, maxDecimals: number): number => {
  const precisionMap: Record<string, number> = {
    'BTC': 8,
    'ETH': 6,
    'SOL': 4,
    'ADA': 2,
    'DOT': 4,
    'MATIC': 2,
    'AVAX': 4,
    'LINK': 4,
    'UNI': 4,
    'AAVE': 4,
  };
  
  return Math.min(precisionMap[symbol] || 2, maxDecimals);
};

// Mask sensitive data
export const maskIf = (value: string, masked: boolean): string => {
  return masked ? '•••••' : value;
};

// Format large numbers with K, M, B suffixes
export const fmtCompact = (n: number | string | Decimal): string => {
  const value = typeof n === 'string' ? parseFloat(n) : typeof n === 'number' ? n : n.toNumber();
  
  if (!Number.isFinite(value)) return '0';
  
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
};

// Format time ago
export const fmtTimeAgo = (date: Date | string | number): string => {
  const now = new Date();
  const past = new Date(date);
  const diffMs = now.getTime() - past.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSeconds < 60) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return past.toLocaleDateString();
};

// Format duration
export const fmtDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
};

// Color utilities for PnL
export const getPnLColor = (value: number): string => {
  if (value > 0) return '#10B981'; // Green
  if (value < 0) return '#EF4444'; // Red
  return '#6B7280'; // Gray
};

// Color utilities for risk tiers
export const getRiskColor = (tier: string): string => {
  const colors: Record<string, string> = {
    'SAFE': '#10B981',
    'WARN': '#F59E0B',
    'TOP_UP': '#EF4444',
    'AT_RISK': '#DC2626',
    'LIQUIDATE': '#7C2D12',
  };
  return colors[tier] || '#6B7280';
};

// Accessibility helpers
export const getAccessibilityLabel = (type: string, data: any): string => {
  switch (type) {
    case 'portfolio_value':
      return `Portfolio value: ${fmtUsd(data.value, { masked: data.masked })}`;
    case 'pnl':
      return `Profit and loss: ${fmtPercent(data.value, { masked: data.masked })}`;
    case 'holding':
      return `${data.symbol}: ${fmtCryptoQty(data.quantity, data.symbol, { masked: data.masked })} coins, ${fmtUsd(data.value, { masked: data.masked })} value`;
    case 'trade_button':
      return `${data.side} ${data.symbol} at ${fmtUsd(data.price)}`;
    case 'loan_status':
      return `Loan ${data.id}: ${fmtUsd(data.amount)} at ${fmtPercent(data.rate * 100)} interest`;
    default:
      return '';
  }
};

// Validation helpers
export const isValidAmount = (value: string | number): boolean => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return Number.isFinite(num) && num > 0;
};

export const isValidPrice = (value: string | number): boolean => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return Number.isFinite(num) && num > 0 && num < 1000000;
};

export const isValidQuantity = (value: string | number, symbol: string): boolean => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (!Number.isFinite(num) || num <= 0) return false;
  
  // Check precision
  const precision = getCryptoPrecision(symbol, 8);
  const decimalPlaces = (num.toString().split('.')[1] || '').length;
  return decimalPlaces <= precision;
};
