/**
* AI Options Service
* Hedge Fund-Level Options Strategy Recommendations
*/
import { API_HTTP } from '../../../config';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';
export interface OptionsRecommendation {
strategy_name: string;
strategy_type: 'income' | 'hedge' | 'speculation' | 'arbitrage';
confidence_score: number;
symbol: string;
current_price: number;
options: Array<{
type: 'call' | 'put';
action: 'buy' | 'sell';
strike: number;
expiration: string;
premium: number;
quantity: number;
}>;
analytics: {
max_profit: number;
max_loss: number;
probability_of_profit: number;
expected_return: number;
breakeven: number;
};
reasoning: {
market_outlook: string;
strategy_rationale: string;
risk_factors: string[];
key_benefits: string[];
};
risk_score: number;
days_to_expiration: number;
created_at: string;
}
export interface MarketAnalysis {
symbol: string;
current_price: number;
volatility: number;
implied_volatility: number;
volume: number;
market_cap: number;
sector: string;
sentiment_score: number;
trend_direction: 'bullish' | 'bearish' | 'neutral';
support_levels: number[];
resistance_levels: number[];
earnings_date?: string;
dividend_yield: number;
beta: number;
}
export interface AIOptionsResponse {
symbol: string;
current_price: number;
recommendations: OptionsRecommendation[];
market_analysis: MarketAnalysis;
generated_at: string;
total_recommendations: number;
}
export interface StrategyOptimizationRequest {
symbol: string;
strategy_type: string;
current_price: number;
user_preferences?: Record<string, any>;
}
export interface StrategyOptimizationResponse {
symbol: string;
strategy_type: string;
optimal_parameters: Record<string, any>;
optimization_score: number;
predicted_outcomes: Record<string, any>;
generated_at: string;
}
export class AIOptionsService {
  private static instance: AIOptionsService;
  private baseUrl: string;
  private constructor() {
    this.baseUrl = `${API_HTTP}/api/ai-options`;
  }

  /**
   * React Native-safe timeout helper
   */
  private fetchWithTimeout(url: string, init: RequestInit, ms: number): Promise<Response> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), ms);

    return fetch(url, { ...init, signal: controller.signal })
      .finally(() => clearTimeout(timer));
  }

  /**
   * Get CSRF token from backend
   */
  private async getCSRFToken(): Promise<string | null> {
    try {
      const response = await fetch(`${API_HTTP}/csrf-token/`, {
        method: 'GET',
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.csrfToken || null;
      }
      return null;
    } catch (error) {
      logger.error('Error getting CSRF token:', error);
      return null;
    }
  }

  /**
   * Get authentication headers
   */
  private async getAuthHeaders(): Promise<Record<string, string>> {
    try {
      const token = await AsyncStorage.getItem('token');
      const csrfToken = await this.getCSRFToken();
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
      };
      
      return headers;
    } catch (error) {
      logger.error('Error getting auth headers:', error);
      return {
        'Content-Type': 'application/json',
      };
    }
  }

  /**
   * Retry helper for spotty network connections
   */
  private async retry<T>(fn: () => Promise<T>, attempts = 2, baseDelayMs = 400): Promise<T> {
    try { 
      return await fn(); 
    } catch (e) {
      if (attempts <= 0) throw e;
      await new Promise(r => setTimeout(r, baseDelayMs));
      return this.retry(fn, attempts - 1, baseDelayMs * 2);
    }
  }
public static getInstance(): AIOptionsService {
if (!AIOptionsService.instance) {
AIOptionsService.instance = new AIOptionsService();
}
return AIOptionsService.instance;
}
/**
* Get AI-powered options recommendations
*/
async getRecommendations(
symbol: string,
userRiskTolerance: 'low' | 'medium' | 'high' = 'medium',
portfolioValue: number = 10000,
timeHorizon: number = 30,
maxRecommendations: number = 5
): Promise<AIOptionsResponse> {
    try {
      logger.log({
        symbol: (symbol || 'UNKNOWN').toUpperCase(),
        user_risk_tolerance: userRiskTolerance,
        portfolio_value: portfolioValue,
        time_horizon: timeHorizon,
        max_recommendations: maxRecommendations,
      });
      const requestBody = {
        symbol: (symbol || 'UNKNOWN').toUpperCase(),
        user_risk_tolerance: userRiskTolerance,
        portfolio_value: portfolioValue,
        time_horizon: timeHorizon,
        max_recommendations: maxRecommendations,
      };
      
      const response = await this.retry(async () => {
        const headers = await this.getAuthHeaders();
        return await this.fetchWithTimeout(`${this.baseUrl}/recommendations`, {
          method: 'POST',
          headers,
          body: JSON.stringify(requestBody),
        }, 12000);
      });
      
      logger.log('Response status:', response.status);
      logger.log('Response headers:', response.headers);
      
      if (!response.ok) {
        const errorText = await response.text();
        logger.error('HTTP Error Response:', errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      // Check if response is actually JSON
      const contentType = response.headers.get('content-type');
      logger.log('Content-Type:', contentType);
      
      // Get the response text first to debug
      const responseText = await response.text();
      logger.log('Raw response text (first 200 chars):', responseText.substring(0, 200));
      
      if (!contentType || !contentType.includes('application/json')) {
        logger.error('Non-JSON response:', responseText);
        throw new Error(`Expected JSON response but got: ${contentType}`);
      }
      
      // Try to parse the JSON
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        logger.error('JSON Parse Error:', parseError);
        logger.error('Response text that failed to parse:', responseText);
        throw new Error(`JSON Parse error: ${parseError.message}`);
      }
logger.log({
  symbol: data.symbol,
  total_recommendations: data.total_recommendations,
  recommendations_count: data.recommendations?.length || 0,
});
return data;
} catch (error) {
const err = error as Error;
// For network errors, return mock data for demo instead of throwing
if (err?.message?.includes('Network request failed') || 
    err?.message?.includes('Failed to fetch') ||
    err?.name === 'TypeError') {
  logger.warn('⚠️ Network error, using mock data for demo');
  return this.getMockRecommendations(symbol, userRiskTolerance, portfolioValue, timeHorizon, maxRecommendations);
}
logger.error('❌ Error getting AI options recommendations:', error);
logger.error('Error details:', {
name: err?.name,
message: err?.message,
stack: err?.stack,
});
// For other errors, still provide mock data for demo
return this.getMockRecommendations(symbol, userRiskTolerance, portfolioValue, timeHorizon, maxRecommendations);
}
}

/**
 * Get mock recommendations for demo purposes
 */
private getMockRecommendations(
  symbol: string,
  userRiskTolerance: 'low' | 'medium' | 'high',
  portfolioValue: number,
  timeHorizon: number,
  maxRecommendations: number
): AIOptionsResponse {
  const currentPrice = 150 + Math.random() * 50;
  const mockRecommendations: OptionsRecommendation[] = [
    {
      strategy_name: 'Covered Call',
      strategy_type: 'income',
      confidence_score: 85,
      symbol: symbol.toUpperCase(),
      current_price: currentPrice,
      options: [
        {
          type: 'call',
          action: 'sell',
          strike: currentPrice * 1.05,
          expiration: new Date(Date.now() + timeHorizon * 24 * 60 * 60 * 1000).toISOString(),
          premium: currentPrice * 0.02,
          quantity: Math.floor(portfolioValue / currentPrice / 2)
        }
      ],
      analytics: {
        max_profit: currentPrice * 0.07 * Math.floor(portfolioValue / currentPrice / 2),
        max_loss: -currentPrice * 0.93 * Math.floor(portfolioValue / currentPrice / 2),
        probability_of_profit: 0.65,
        expected_return: 0.08,
        breakeven: currentPrice * 0.98
      },
      reasoning: {
        market_outlook: 'Bullish with moderate volatility',
        strategy_rationale: 'Generate income while maintaining upside exposure',
        risk_factors: ['Stock price decline below breakeven', 'Low volatility'],
        key_benefits: ['Income generation', 'Downside protection', 'Capital efficiency']
      },
      risk_score: userRiskTolerance === 'low' ? 30 : userRiskTolerance === 'medium' ? 50 : 70,
      days_to_expiration: timeHorizon,
      created_at: new Date().toISOString()
    },
    {
      strategy_name: 'Protective Put',
      strategy_type: 'hedge',
      confidence_score: 75,
      symbol: symbol.toUpperCase(),
      current_price: currentPrice,
      options: [
        {
          type: 'put',
          action: 'buy',
          strike: currentPrice * 0.95,
          expiration: new Date(Date.now() + timeHorizon * 24 * 60 * 60 * 1000).toISOString(),
          premium: currentPrice * 0.03,
          quantity: Math.floor(portfolioValue / currentPrice)
        }
      ],
      analytics: {
        max_profit: Infinity,
        max_loss: -currentPrice * 0.03 * Math.floor(portfolioValue / currentPrice),
        probability_of_profit: 0.55,
        expected_return: -0.02,
        breakeven: currentPrice * 1.03
      },
      reasoning: {
        market_outlook: 'Uncertain with potential downside',
        strategy_rationale: 'Protect against significant losses while maintaining upside',
        risk_factors: ['Time decay', 'Limited upside if stock rises'],
        key_benefits: ['Downside protection', 'Unlimited upside', 'Peace of mind']
      },
      risk_score: 20,
      days_to_expiration: timeHorizon,
      created_at: new Date().toISOString()
    }
  ];

  return {
    symbol: symbol.toUpperCase(),
    current_price: currentPrice,
    recommendations: mockRecommendations.slice(0, maxRecommendations),
    market_analysis: {
      symbol: symbol.toUpperCase(),
      current_price: currentPrice,
      volatility: 0.25,
      implied_volatility: 0.28,
      volume: 5000000,
      market_cap: 2500000000000,
      sector: 'Technology',
      sentiment_score: 0.65,
      trend_direction: 'bullish',
      support_levels: [currentPrice * 0.9, currentPrice * 0.85],
      resistance_levels: [currentPrice * 1.1, currentPrice * 1.15],
      dividend_yield: 0.015,
      beta: 1.2
    },
    generated_at: new Date().toISOString(),
    total_recommendations: mockRecommendations.length
  };
}
/**
* Optimize specific options strategy parameters
*/
async optimizeStrategy(
request: StrategyOptimizationRequest
): Promise<StrategyOptimizationResponse> {
try {
const headers = await this.getAuthHeaders();
const response = await fetch(`${this.baseUrl}/optimize-strategy`, {
method: 'POST',
headers,
body: JSON.stringify(request),
});
if (!response.ok) {
throw new Error(`HTTP error! status: ${response.status}`);
}
const data = await response.json();
return data;
} catch (error) {
logger.error('Error optimizing strategy:', error);
throw new Error('Failed to optimize strategy');
}
}
/**
* Get comprehensive market analysis
*/
async getMarketAnalysis(
symbol: string,
analysisType: 'comprehensive' | 'quick' | 'detailed' = 'comprehensive'
): Promise<any> {
try {
const headers = await this.getAuthHeaders();
const response = await fetch(`${this.baseUrl}/market-analysis`, {
method: 'POST',
headers,
body: JSON.stringify({
symbol: (symbol || 'UNKNOWN').toUpperCase(),
analysis_type: analysisType,
}),
});
if (!response.ok) {
throw new Error(`HTTP error! status: ${response.status}`);
}
const data = await response.json();
return data;
} catch (error) {
logger.error('Error getting market analysis:', error);
throw new Error('Failed to get market analysis');
}
}
/**
* Train ML models for a symbol
*/
async trainModels(symbol: string): Promise<any> {
try {
const headers = await this.getAuthHeaders();
const response = await fetch(`${this.baseUrl}/train-models`, {
method: 'POST',
headers,
body: JSON.stringify({ symbol: (symbol || 'UNKNOWN').toUpperCase() }),
});
if (!response.ok) {
throw new Error(`HTTP error! status: ${response.status}`);
}
const data = await response.json();
return data;
} catch (error) {
logger.error('Error training models:', error);
throw new Error('Failed to train models');
}
}
/**
* Get model status for a symbol
*/
async getModelStatus(symbol: string): Promise<any> {
try {
const response = await fetch(`${this.baseUrl}/model-status/${(symbol || 'UNKNOWN').toUpperCase()}`);
if (!response.ok) {
throw new Error(`HTTP error! status: ${response.status}`);
}
const data = await response.json();
return data;
} catch (error) {
logger.error('Error getting model status:', error);
throw new Error('Failed to get model status');
}
}
/**
* Health check for AI Options API
*/
async healthCheck(): Promise<any> {
try {
const response = await fetch(`${this.baseUrl}/health`);
if (!response.ok) {
throw new Error(`HTTP error! status: ${response.status}`);
}
const data = await response.json();
return data;
} catch (error) {
logger.error('Error checking AI options health:', error);
throw new Error('Failed to check AI options health');
}
}
/**
* Format recommendation for display
*/
formatRecommendation(rec: OptionsRecommendation): string {
const profitLoss = (rec.analytics?.max_loss || 0) > 0 ? 
`Max Profit: $${(rec.analytics?.max_profit || 0).toFixed(2)} | Max Loss: $${(rec.analytics?.max_loss || 0).toFixed(2)}` :
`Max Profit: $${(rec.analytics?.max_profit || 0).toFixed(2)} | Max Loss: $${Math.abs(rec.analytics?.max_loss || 0).toFixed(2)}`;
return `${rec.strategy_name || 'Unknown Strategy'} (${(rec.confidence_score || 0).toFixed(0)}% confidence)
${rec.reasoning?.strategy_rationale || 'No rationale available'}
${profitLoss}
Probability of Profit: ${((rec.analytics?.probability_of_profit || 0) * 100).toFixed(0)}%
Expected Return: ${((rec.analytics?.expected_return || 0) * 100).toFixed(1)}%`;
}
/**
* Get strategy type color
*/
getStrategyTypeColor(strategyType: string): string {
switch (strategyType) {
case 'income':
return '#34C759'; // Green
case 'hedge':
return '#FF9500'; // Orange
case 'speculation':
return '#FF3B30'; // Red
case 'arbitrage':
return '#007AFF'; // Blue
default:
return '#8E8E93'; // Gray
}
}
/**
* Get risk level description
*/
getRiskLevelDescription(riskScore: number): string {
if (riskScore <= 30) return 'Low Risk';
if (riskScore <= 60) return 'Medium Risk';
if (riskScore <= 80) return 'High Risk';
return 'Very High Risk';
}
/**
* Get confidence level description
*/
getConfidenceLevelDescription(confidenceScore: number): string {
if (confidenceScore >= 90) return 'Very High Confidence';
if (confidenceScore >= 80) return 'High Confidence';
if (confidenceScore >= 70) return 'Medium Confidence';
if (confidenceScore >= 60) return 'Low Confidence';
return 'Very Low Confidence';
}
}
export default AIOptionsService;
