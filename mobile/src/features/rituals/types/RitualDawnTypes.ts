/**
 * Ritual Dawn Types
 * TypeScript interfaces matching the backend RitualDawnResponse
 */

export interface PortfolioHoldingSnapshot {
  symbol: string;
  name: string;
  shares: number;
  current_price: number;
  previous_close: number;
  change_dollars: number;
  change_percent: number;
}

export interface PortfolioSnapshot {
  total_value: number;
  previous_total_value: number;
  change_dollars: number;
  change_percent: number;
  top_holdings: PortfolioHoldingSnapshot[];
  holdings_count: number;
  has_portfolio: boolean;
}

export interface MarketContext {
  sp500_change_percent: number;
  sp500_direction: 'up' | 'down' | 'flat';
  market_sentiment: 'bullish' | 'bearish' | 'neutral';
  notable_indices: Array<{ name: string; symbol: string; change_percent: number }>;
  headline: string;
  volatility_level: 'low' | 'moderate' | 'elevated';
  is_weekend?: boolean;
}

export interface ActionSuggestion {
  action_type: 'rebalance' | 'risk_flag' | 'opportunity' | 'review' | 'no_action';
  headline: string;
  detail: string;
  action_label: string;
  target_screen?: string | null;
  urgency: 'low' | 'medium' | 'high';
}

export type RitualPhase = 'sunrise' | 'portfolio' | 'market' | 'action' | 'commitment';

export interface RitualDawnResult {
  greeting: string;
  tagline: string;
  greeting_key?: string | null;
  portfolio: PortfolioSnapshot;
  market: MarketContext;
  action: ActionSuggestion;
  streak: number;
  timestamp: string;
  // Legacy compat
  transactionsSynced: number;
  haiku: string;
}
