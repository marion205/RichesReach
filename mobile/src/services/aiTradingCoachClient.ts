/**
 * AI Trading Coach Client - Mobile API Integration
 * ================================================
 * 
 * Client for the AI Trading Coach service providing:
 * - Personalized strategy recommendations
 * - Real-time trading guidance
 * - Trade analysis and insights
 * - Confidence building explanations
 * 
 * Features:
 * - Strongly-typed API responses
 * - Request timeout handling
 * - X-Request-ID headers for tracing
 * - Error handling with custom ApiError class
 * - Fallback responses for reliability
 */

import { API_BASE } from '../config/api';

const BASE_URL = API_BASE;
const DEFAULT_TIMEOUT_MS = 30_000; // Increased to 30s for AI-powered guidance generation

export class ApiError extends Error {
  status: number;
  detail?: unknown;
  requestId?: string;
  constructor(message: string, status: number, detail?: unknown, requestId?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
    this.requestId = requestId;
  }
}

// =============================================================================
// Type Definitions
// =============================================================================

export interface StrategyRecommendation {
  strategy_name: string;
  description: string;
  risk_level: 'low' | 'medium' | 'high';
  expected_return?: number;
  suitable_for: string[];
  steps: string[];
  market_conditions: Record<string, any>;
  confidence_score: number;
  generated_at: string;
}

export interface TradingGuidance {
  current_step: number;
  total_steps: number;
  action: string;
  rationale: string;
  risk_check: string;
  next_decision_point: string;
  session_id: string;
  updated_at: string;
}

export interface TradeAnalysis {
  trade_id: string;
  entry: Record<string, any>;
  exit: Record<string, any>;
  pnl: number;
  strengths: string[];
  mistakes: string[];
  lessons_learned: string[];
  improved_strategy: string;
  confidence_boost: string;
  analyzed_at: string;
}

export interface ConfidenceExplanation {
  context: string;
  explanation: string;
  rationale: string;
  tips: string[];
  motivation: string;
  generated_at: string;
}

export interface SessionSummary {
  session_id: string;
  total_steps: number;
  final_confidence: number;
  history_length: number;
  ended_at: string;
}

// =============================================================================
// Utility Functions
// =============================================================================

function withTimeout<T>(p: Promise<T>, ms: number, abort: AbortController): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const id = setTimeout(() => {
      abort.abort();
      reject(new ApiError('Request timeout', 408));
    }, ms);
    p.then(
      (v) => {
        clearTimeout(id);
        resolve(v);
      },
      (e) => {
        clearTimeout(id);
        reject(e);
      }
    );
  });
}

async function postJSON<T>(
  path: string,
  body: unknown,
  opts?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  const controller = new AbortController();
  const url = `${BASE_URL}${path}`;
  const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  
  // Debug logging
  console.log(`🌐 [Coach Client] Making request to: ${url}`);
  console.log(`🌐 [Coach Client] BASE_URL: ${BASE_URL}`);
  console.log(`🌐 [Coach Client] Timeout: ${opts?.timeoutMs ?? DEFAULT_TIMEOUT_MS}ms`);
  
  const resPromise = fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId,
      ...(opts?.headers || {}),
    },
    body: JSON.stringify(body ?? {}),
    signal: controller.signal,
    ...opts,
  });

  const res = await withTimeout(resPromise, opts?.timeoutMs ?? DEFAULT_TIMEOUT_MS, controller);
  const text = await res.text();
  let data: any = {};
  
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      throw new ApiError(
        `Invalid JSON from ${path}`,
        res.status || 500,
        text,
        res.headers.get('X-Request-ID') || requestId
      );
    }
  }
  
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || res.statusText || 'Request failed';
    throw new ApiError(
      typeof detail === 'string' ? detail : JSON.stringify(detail),
      res.status,
      data,
      res.headers.get('X-Request-ID') || requestId
    );
  }
  
  return data as T;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get personalized trading strategy recommendation
 */
export function recommendStrategy(req: {
  user_id: string;
  asset: string;
  risk_tolerance?: 'conservative' | 'moderate' | 'aggressive';
  goals?: string[];
  market_data?: Record<string, any>;
}): Promise<StrategyRecommendation> {
  return postJSON<StrategyRecommendation>('/coach/recommend-strategy', {
    user_id: req.user_id,
    asset: req.asset,
    risk_tolerance: req.risk_tolerance || 'moderate',
    goals: req.goals || [],
    market_data: req.market_data || {},
  });
}

/**
 * Start a new AI-guided trading session
 */
export function startTradingSession(req: {
  user_id: string;
  asset: string;
  strategy: string;
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  goals: string[];
}): Promise<{ session_id: string; message: string }> {
  // Use longer timeout for session start (market data fetch can take time)
  return postJSON<{ session_id: string; message: string }>('/coach/start-session', req, { timeoutMs: 30_000 }); // 30 seconds
}

/**
 * Get next step in active trading session
 */
export function getTradingGuidance(req: {
  session_id: string;
  market_update?: Record<string, any>;
}): Promise<TradingGuidance> {
  // Use longer timeout for AI-powered guidance generation
  return postJSON<TradingGuidance>('/coach/guidance', {
    session_id: req.session_id,
    market_update: req.market_update || {},
  }, { timeoutMs: 30_000 }); // 30 seconds for AI generation
}

/**
 * End trading session and get summary
 */
export function endTradingSession(req: {
  session_id: string;
}): Promise<SessionSummary> {
  return postJSON<SessionSummary>('/coach/end-session', req);
}

/**
 * Analyze completed trade for insights
 */
export function analyzeTrade(req: {
  user_id: string;
  trade_data: {
    trade_id?: string;
    entry: Record<string, any>;
    exit: Record<string, any>;
    pnl?: number;
    notes?: string;
  };
}): Promise<TradeAnalysis> {
  return postJSON<TradeAnalysis>('/coach/analyze-trade', req);
}

/**
 * Get confidence-building explanation
 */
export function buildConfidence(req: {
  user_id: string;
  context: string;
  trade_simulation?: Record<string, any>;
}): Promise<ConfidenceExplanation> {
  return postJSON<ConfidenceExplanation>('/coach/build-confidence', {
    user_id: req.user_id,
    context: req.context,
    trade_simulation: req.trade_simulation || {},
  });
}

// =============================================================================
// Fallback Data for Offline/Error Scenarios
// =============================================================================

export const FALLBACK_STRATEGY: StrategyRecommendation = {
  strategy_name: "Covered Call Strategy",
  description: "Sell call options against owned stock to generate income while maintaining upside potential",
  risk_level: "medium",
  expected_return: 0.08,
  suitable_for: ["intermediate traders", "income-focused investors"],
  steps: [
    "Own 100 shares of the underlying stock",
    "Sell 1 call option contract (strike above current price)",
    "Collect premium income immediately",
    "Monitor position and manage if stock moves significantly",
    "Close or roll position before expiration"
  ],
  market_conditions: {
    volatility: "moderate",
    trend: "neutral"
  },
  confidence_score: 0.75,
  generated_at: new Date().toISOString(),
};

export const FALLBACK_GUIDANCE: TradingGuidance = {
  current_step: 1,
  total_steps: 5,
  action: "Research the underlying asset and current market conditions",
  rationale: "Understanding the asset fundamentals and market sentiment is crucial before entering any options position",
  risk_check: "Ensure you understand the maximum loss potential and have sufficient capital",
  next_decision_point: "Proceed to step 2 once you've completed your research",
  session_id: "fallback-session",
  updated_at: new Date().toISOString(),
};

export const FALLBACK_ANALYSIS: TradeAnalysis = {
  trade_id: "fallback-analysis",
  entry: { price: 100, time: "2024-01-01T10:00:00Z" },
  exit: { price: 105, time: "2024-01-15T15:30:00Z" },
  pnl: 5.0,
  strengths: [
    "Good entry timing based on technical analysis",
    "Proper position sizing relative to portfolio"
  ],
  mistakes: [
    "Could have set a trailing stop for better risk management"
  ],
  lessons_learned: [
    "Always have an exit strategy before entering",
    "Consider market volatility when setting targets"
  ],
  improved_strategy: "Add trailing stop-loss at 3% below entry price",
  confidence_boost: "Great job on your first trade! You're learning valuable lessons that will make you a better trader.",
  analyzed_at: new Date().toISOString(),
};

export const FALLBACK_CONFIDENCE: ConfidenceExplanation = {
  context: "Why should I buy this call option?",
  explanation: "This call option aligns with your risk profile and current market conditions. The underlying asset shows strong fundamentals and technical indicators suggest upward momentum.",
  rationale: "Based on historical data, similar setups have a 65% success rate in the current market environment. The risk-reward ratio is favorable at 1:2.",
  tips: [
    "Start with a small position size to test your strategy",
    "Set a clear exit plan before entering the trade"
  ],
  motivation: "You've done your research and this trade makes sense for your goals. Trust your analysis and remember that every trade is a learning opportunity!",
  generated_at: new Date().toISOString(),
};
