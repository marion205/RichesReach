/**
* AI Options Service
* Hedge Fund-Level Options Strategy Recommendations
*/
import { PRODUCTION_CONFIG } from '../../../config/production';
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
this.baseUrl = `${PRODUCTION_CONFIG.API_BASE_URL}/api/ai-options`;
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
console.log({
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
const response = await fetch(`${this.baseUrl}/recommendations`, {
method: 'POST',
headers: {
'Content-Type': 'application/json',
},
body: JSON.stringify(requestBody),
});
if (!response.ok) {
const errorText = await response.text();
console.error(' HTTP Error Response:', errorText);
throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
}
const data = await response.json();
console.log({
  symbol: data.symbol,
  total_recommendations: data.total_recommendations,
  recommendations_count: data.recommendations?.length || 0,
});
return data;
} catch (error) {
console.error(' Error getting AI options recommendations:', error);
const err = error as Error;
console.error('Error details:', {
name: err?.name,
message: err?.message,
stack: err?.stack,
});
throw new Error(`Failed to get AI options recommendations: ${err?.message || 'Unknown error'}`);
}
}
/**
* Optimize specific options strategy parameters
*/
async optimizeStrategy(
request: StrategyOptimizationRequest
): Promise<StrategyOptimizationResponse> {
try {
const response = await fetch(`${this.baseUrl}/optimize-strategy`, {
method: 'POST',
headers: {
'Content-Type': 'application/json',
},
body: JSON.stringify(request),
});
if (!response.ok) {
throw new Error(`HTTP error! status: ${response.status}`);
}
const data = await response.json();
return data;
} catch (error) {
console.error('Error optimizing strategy:', error);
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
const response = await fetch(`${this.baseUrl}/market-analysis`, {
method: 'POST',
headers: {
'Content-Type': 'application/json',
},
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
console.error('Error getting market analysis:', error);
throw new Error('Failed to get market analysis');
}
}
/**
* Train ML models for a symbol
*/
async trainModels(symbol: string): Promise<any> {
try {
const response = await fetch(`${this.baseUrl}/train-models`, {
method: 'POST',
headers: {
'Content-Type': 'application/json',
},
body: JSON.stringify({ symbol: (symbol || 'UNKNOWN').toUpperCase() }),
});
if (!response.ok) {
throw new Error(`HTTP error! status: ${response.status}`);
}
const data = await response.json();
return data;
} catch (error) {
console.error('Error training models:', error);
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
console.error('Error getting model status:', error);
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
console.error('Error checking AI options health:', error);
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
