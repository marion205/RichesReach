/**
 * API Response Types
 * TypeScript interfaces for API responses to improve type safety
 */

// Common API Response Wrapper
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// User Profile Types
export interface UserProfile {
  id: string;
  name: string;
  email: string;
  profilePic?: string;
  followersCount?: number;
  followingCount?: number;
  isFollowingUser?: boolean;
  isFollowedByUser?: boolean;
}

export interface UserProfileResponse extends ApiResponse<UserProfile> {
  data?: UserProfile;
}

// Portfolio Types
export interface Portfolio {
  id: string;
  name: string;
  totalValue: number;
  totalCost: number;
  totalReturn: number;
  totalReturnPercent: number;
  holdings: PortfolioHolding[];
  createdAt: string;
  updatedAt: string;
}

export interface PortfolioHolding {
  symbol: string;
  quantity: number;
  averageCost: number;
  currentPrice: number;
  currentValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
}

export interface PortfolioResponse extends ApiResponse<Portfolio> {
  data?: Portfolio;
}

export interface PortfoliosResponse extends ApiResponse<Portfolio[]> {
  data?: Portfolio[];
}

// Stock Quote Types
export interface StockQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  previousClose: number;
  timestamp: string;
  marketStatus: 'open' | 'closed' | 'pre-market' | 'after-hours';
}

export interface StockQuoteResponse extends ApiResponse<StockQuote> {
  data?: StockQuote;
}

// Daily Brief Types
export interface DailyBrief {
  id: string;
  date: string;
  title: string;
  summary: string;
  sections: DailyBriefSection[];
  is_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface DailyBriefSection {
  id: string;
  type: 'text' | 'action' | 'insight' | 'warning';
  title?: string;
  content: string;
  actionLabel?: string;
  actionUrl?: string;
}

export interface DailyBriefResponse extends ApiResponse<DailyBrief> {
  data?: DailyBrief;
}

// Crypto Types
export interface CryptoPortfolio {
  total_value_usd: number;
  total_cost_basis: number;
  total_pnl: number;
  total_pnl_percentage: number;
  total_pnl_1d: number;
  total_pnl_pct_1d: number;
  total_pnl_1w: number;
  total_pnl_pct_1w: number;
  total_pnl_1m: number;
  total_pnl_pct_1m: number;
  holdings: CryptoHolding[];
}

export interface CryptoHolding {
  cryptocurrency: {
    symbol: string;
    name: string;
  };
  quantity: number;
  current_value: number;
  unrealized_pnl_percentage: number;
}

export interface CryptoPortfolioResponse extends ApiResponse<CryptoPortfolio> {
  data?: CryptoPortfolio;
}

// Error Types
export interface ApiError {
  message: string;
  code?: string;
  statusCode?: number;
  details?: Record<string, unknown>;
}

export interface ErrorResponse extends ApiResponse<never> {
  error: string;
  details?: ApiError;
}

// GraphQL Error Types
export interface GraphQLError {
  message: string;
  locations?: Array<{ line: number; column: number }>;
  path?: Array<string | number>;
  extensions?: Record<string, unknown>;
}

export interface GraphQLResponse<T> {
  data?: T;
  errors?: GraphQLError[];
}

