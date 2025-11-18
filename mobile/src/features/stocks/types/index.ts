/**
 * TypeScript interfaces for Trading/Stocks features
 * Replaces 'any' types with proper type definitions
 */

// Alpaca Account Types
export interface AlpacaAccount {
  id: string;
  accountNumber?: string;
  buyingPower?: number;
  cash?: number;
  portfolioValue?: number;
  equity?: number;
  dayTradeCount?: number;
  patternDayTrader?: boolean;
  tradingBlocked?: boolean;
  dayTradingBuyingPower?: number;
  isDayTradingEnabled?: boolean;
  accountStatus?: string;
  approvedAt?: string | null;
  createdAt?: string;
}

// Position Types
export interface AlpacaPosition {
  symbol: string;
  qty: number;
  marketValue: number;
  avgEntryPrice: number;
  currentPrice: number;
  unrealizedPl?: number;
  unrealizedpl?: number;
  unrealizedPL?: number;
  unrealizedPct?: number;
  side: 'long' | 'short';
  assetClass?: string;
  exchange?: string;
}

// Order Types
export interface AlpacaOrder {
  id: string;
  symbol: string;
  qty: number;
  filledQty?: number;
  side: 'buy' | 'sell';
  orderType: 'market' | 'limit' | 'stop' | 'stop_limit';
  timeInForce: 'day' | 'gtc' | 'opg' | 'cls' | 'ioc' | 'fok';
  limitPrice?: number;
  stopPrice?: number;
  status: 'new' | 'partially_filled' | 'filled' | 'done_for_day' | 'canceled' | 'expired' | 'replaced' | 'pending_cancel' | 'pending_replace' | 'accepted' | 'pending_new' | 'accepted_for_bidding' | 'stopped' | 'rejected' | 'suspended' | 'calculated';
  submittedAt: string;
  filledAt?: string;
  canceledAt?: string;
  clientOrderId?: string;
}

// Trading Quote Types
export interface TradingQuote {
  symbol: string;
  bid: number;
  ask: number;
  bidSize?: number;
  askSize?: number;
  timestamp: number;
  lastPrice?: number;
  volume?: number;
}

// Order Variables Types
export interface OrderVariables {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  orderType: 'MARKET' | 'LIMIT' | 'STOP';
  timeInForce: 'DAY' | 'GTC' | 'IOC' | 'FOK' | 'OPG' | 'CLS';
  limitPrice?: number;
  stopPrice?: number;
}

// Place Order Response Types
export interface PlaceOrderResponse {
  success: boolean;
  message?: string;
  orderId?: string;
  error?: string;
}

// Cancel Order Response Types
export interface CancelOrderResponse {
  success: boolean;
  message?: string;
  error?: string;
}

// Refetch Query Function Type
export type RefetchQueryFunction = () => Promise<any>;

// Navigation Types
export interface NavigationType {
  navigate: (screen: string, params?: any) => void;
}

// Order Form Types
export type OrderType = 'market' | 'limit' | 'stop_loss';
export type OrderSide = 'buy' | 'sell';

// Cached Data Types
export interface CachedData<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

// Cache Stats Types
export interface CacheStats {
  account: { size: number; age: number; valid: boolean };
  positions: { size: number; age: number; valid: boolean };
  orders: { size: number; age: number; valid: boolean };
  quotes: { size: number; age: number; valid: boolean };
  lastSync: number;
}

// Local Cost State Type
export interface LocalCostState {
  pricePerShare: number;
  total: number;
  source: string;
  isLive: boolean;
}

// Order Total Calculation Type
export interface OrderTotalCalculation {
  pricePerShare: number;
  total: number;
  isValid: boolean;
  error?: string;
}

