/**
 * Futures Types - Simple, clean interfaces
 */

export interface FuturesRecommendation {
  symbol: string; // e.g., 'MESZ5' (Micro E-mini S&P 500, Dec 2025)
  name: string; // e.g., 'Micro E-mini S&P 500'
  why_now: string; // One sentence explanation
  max_loss: number; // Dollar amount
  max_gain: number; // Dollar amount
  probability: number; // Percentage (0-100)
  action: 'Buy' | 'Sell'; // Simple action
  // Real-time price data (added for Phase 1)
  current_price?: number;
  price_change?: number; // Dollar change
  price_change_percent?: number; // Percentage change
  price_history?: number[]; // For sparklines (24h or since midnight)
  last_updated?: string; // ISO timestamp
  // Volume data (added for Phase 2)
  current_volume?: number;
  average_volume?: number;
  volume_ratio?: number; // current_volume / average_volume (unusual if > 1.5)
}

export interface FuturesOrderRequest {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number; // Number of contracts
  order_type?: 'MARKET' | 'LIMIT';
  limit_price?: number;
}

export interface FuturesPosition {
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
}

