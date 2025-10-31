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

