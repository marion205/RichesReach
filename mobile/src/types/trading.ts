/**
 * Shared types for trading-related functionality
 */

export interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  orderType: 'market' | 'limit';
  quantity: number;
  price?: number;
  status: string;
  createdAt: string;
  notes?: string;
}

export interface Option {
  symbol: string;
  contractSymbol?: string;
  strike: number;
  expiration: string;
  optionType: 'call' | 'put';
  bid?: number;
  ask?: number;
  premium?: number;
  volume?: number;
  impliedVolatility?: number;
  iv?: number;
  delta?: number;
  theta?: number;
  score?: number;
  opportunity?: string;
  [key: string]: unknown;
}

export interface OptionsPosition {
  qty: number;
  currentPrice?: number;
  avgEntryPrice?: number;
  optionType?: 'call' | 'put';
  strike?: number;
  [key: string]: unknown;
}

export interface Strategy {
  id?: string;
  name?: string;
  marketOutlook?: string;
  market_outlook?: string;
  [key: string]: unknown;
}

export interface BuyRecommendation {
  symbol: string;
  companyName: string;
  recommendation: string;
  reasoning: string;
  confidence?: number;
  [key: string]: unknown;
}

export interface RebalanceSuggestion {
  action: string;
  priority: 'High' | 'Medium' | 'Low';
  [key: string]: unknown;
}
