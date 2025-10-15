/**
 * Options Copilot Types
 * TypeScript definitions for AI-powered options strategy recommendations
 */

export interface OptionsCopilotRequest {
  symbol: string;
  riskTolerance: 'low' | 'medium' | 'high';
  marketOutlook: 'bullish' | 'bearish' | 'neutral';
  accountValue: number;
  maxRisk: number;
}

export interface OptionsCopilotResponse {
  symbol: string;
  currentPrice: number;
  marketOutlook: string;
  recommendedStrategies: OptionsStrategy[];
  riskAssessment: RiskAssessment;
  marketAnalysis: MarketAnalysis;
}

export interface OptionsStrategy {
  id: string;
  name: string;
  type: string;
  description: string;
  expectedPayoff: ExpectedPayoff;
  greeks: Greeks;
  slippageEstimate: SlippageEstimate;
  riskExplanation: RiskExplanation;
  setup: StrategySetup;
  riskRails: RiskRails;
  confidence: number;
  reasoning: string;
}

export interface ExpectedPayoff {
  maxProfit: number;
  maxLoss: number;
  breakevenPoints: number[];
  profitProbability: number;
  expectedValue: number;
  timeDecay: number;
}

export interface Greeks {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
}

export interface SlippageEstimate {
  bidAskSpread: number;
  marketImpact: number;
  totalSlippage: number;
  liquidityScore: number;
}

export interface RiskExplanation {
  plainEnglish: string;
  riskFactors: string[];
  mitigationStrategies: string[];
  worstCaseScenario: string;
  probabilityOfLoss: number;
}

export interface StrategySetup {
  legs: StrategyLeg[];
  totalCost: number;
  marginRequirement: number;
  expirationDate: string;
  strikePrices: number[];
}

export interface StrategyLeg {
  action: 'buy' | 'sell';
  optionType: 'call' | 'put';
  quantity: number;
  strikePrice: number;
  expirationDate: string;
  premium: number;
  greeks?: Greeks;
}

export interface RiskRails {
  maxPositionSize: number;
  stopLoss: number;
  takeProfit: number;
  timeStop: number;
  volatilityStop: number;
  maxDrawdown: number;
}

export interface RiskAssessment {
  overallRisk: 'low' | 'medium' | 'high';
  riskScore: number;
  riskFactors: RiskFactor[];
  recommendations: string[];
}

export interface RiskFactor {
  factor: string;
  impact: 'low' | 'medium' | 'high';
  description: string;
  mitigation: string;
}

export interface MarketAnalysis {
  volatility: VolatilityAnalysis;
  sentiment: SentimentAnalysis;
  technical: TechnicalAnalysis;
  fundamental: FundamentalAnalysis;
}

export interface VolatilityAnalysis {
  currentIv: number;
  historicalIv: number;
  ivPercentile: number;
  ivRank: number;
  trend: string;
}

export interface SentimentAnalysis {
  overall: string;
  score: number;
  sources: SentimentSource[];
}

export interface SentimentSource {
  source: string;
  sentiment: string;
  confidence: number;
}

export interface TechnicalAnalysis {
  trend: string;
  support: number;
  resistance: number;
  keyLevels: number[];
  indicators: TechnicalIndicator[];
}

export interface TechnicalIndicator {
  name: string;
  value: number;
  signal: string;
  strength: number;
}

export interface FundamentalAnalysis {
  rating: string;
  priceTarget: number;
  upside: number;
  keyMetrics: FundamentalMetric[];
}

export interface FundamentalMetric {
  metric: string;
  value: number;
  benchmark: number;
  signal: string;
}
