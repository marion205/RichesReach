/**
 * Options Flow Service
 * Handles options chain data, flow analysis, and strategy execution
 */
import { gql } from '@apollo/client';
import { API_HTTP } from '../../../config/api';

export interface OptionsContract {
  strike: number;
  expiration: string;
  optionType: 'CALL' | 'PUT';
  bid: number;
  ask: number;
  volume: number;
  openInterest: number;
  impliedVolatility: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
}

export interface OptionsChain {
  expirationDates: string[];
  calls: OptionsContract[];
  puts: OptionsContract[];
}

export interface OptionsFlow {
  symbol: string;
  contractSymbol: string;
  strike: number;
  expiration: string;
  optionType: 'CALL' | 'PUT';
  bid: number;
  ask: number;
  volume: number;
  impliedVolatility: number;
  delta: number;
  theta: number;
  score: number;
  opportunity: string;
}

export interface OptionsStrategy {
  id: string;
  symbol: string;
  strategy: string;
  confidence: number;
  maxProfit: number;
  maxLoss: number;
  breakeven: number;
  expiration: string;
  reasoning: string;
  contracts: Array<{
    type: 'CALL' | 'PUT';
    strike: number;
    expiration: string;
    quantity: number;
    action: 'BUY' | 'SELL';
  }>;
}

export const GET_OPTIONS_CHAIN = gql`
  query GetOptionsChain($symbol: String!) {
    optionsChain(symbol: $symbol) {
      expirationDates
      calls {
        strike
        bid
        ask
        volume
        expirationDate
        delta
        gamma
        theta
        vega
        impliedVolatility
      }
      puts {
        strike
        bid
        ask
        volume
        expirationDate
        delta
        gamma
        theta
        vega
        impliedVolatility
      }
    }
  }
`;

export const GET_OPTIONS_ANALYSIS = gql`
  query GetOptionsAnalysis($symbol: String!) {
    optionsAnalysis(symbol: $symbol) {
      underlyingSymbol
      underlyingPrice
      optionsChain {
        expirationDates
        calls {
          strike
          bid
          ask
          volume
          expirationDate
          delta
          gamma
          theta
          vega
          impliedVolatility
        }
        puts {
          strike
          bid
          ask
          volume
          expirationDate
          delta
          gamma
          theta
          vega
          impliedVolatility
        }
      }
      unusualFlow {
        totalVolume
        callVolume
        putVolume
        putCallRatio
        largestTrade {
          symbol
          strike
          expiration
          optionType
          volume
          premium
        }
      }
      recommendedStrategies {
        id
        strategy
        confidence
        maxProfit
        maxLoss
        breakeven
        reasoning
        contracts {
          type
          strike
          expiration
          quantity
          action
        }
      }
      marketSentiment {
        putCallRatio
        impliedVolatilityRank
        skew
        sentimentScore
        sentimentDescription
      }
    }
  }
`;

export const SCAN_OPTIONS = gql`
  query ScanOptions($filters: JSONString) {
    scanOptions(filters: $filters) {
      symbol
      contractSymbol
      strike
      expiration
      optionType
      bid
      ask
      volume
      impliedVolatility
      delta
      theta
      score
      opportunity
    }
  }
`;

export const GET_OPTIONS_RECOMMENDATIONS = gql`
  query GetOptionsRecommendations($symbol: String!, $strategy: String) {
    optionsRecommendations(symbol: $symbol, strategy: $strategy) {
      id
      symbol
      strategy
      confidence
      maxProfit
      maxLoss
      breakeven
      expiration
      reasoning
      contracts {
        type
        strike
        expiration
        quantity
        action
      }
    }
  }
`;

class OptionsFlowService {
  private static instance: OptionsFlowService;
  private baseUrl: string;

  private constructor() {
    this.baseUrl = `${API_HTTP}/api/options`;
  }

  public static getInstance(): OptionsFlowService {
    if (!OptionsFlowService.instance) {
      OptionsFlowService.instance = new OptionsFlowService();
    }
    return OptionsFlowService.instance;
  }

  /**
   * Calculate option Greeks for a contract
   */
  public calculateGreeks(
    contract: OptionsContract,
    underlyingPrice: number,
    timeToExpiration: number,
    riskFreeRate: number = 0.05
  ): Partial<OptionsContract> {
    // Simplified Greeks calculation
    // In production, use Black-Scholes or more sophisticated models
    const { strike, optionType, impliedVolatility } = contract;
    const S = underlyingPrice;
    const K = strike;
    const T = timeToExpiration / 365; // Convert to years
    const r = riskFreeRate;
    const sigma = impliedVolatility / 100;

    // Simplified delta calculation
    const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * Math.sqrt(T));
    const delta = optionType === 'CALL' 
      ? this.normalCDF(d1)
      : this.normalCDF(d1) - 1;

    // Simplified gamma (same for calls and puts)
    const gamma = this.normalPDF(d1) / (S * sigma * Math.sqrt(T));

    // Simplified theta
    const theta = -(S * this.normalPDF(d1) * sigma) / (2 * Math.sqrt(T)) - 
                  r * K * Math.exp(-r * T) * (optionType === 'CALL' ? this.normalCDF(d1 - sigma * Math.sqrt(T)) : this.normalCDF(-d1 + sigma * Math.sqrt(T)));

    // Simplified vega
    const vega = S * this.normalPDF(d1) * Math.sqrt(T) / 100; // Divide by 100 for percentage

    return {
      delta: delta || contract.delta,
      gamma: gamma || contract.gamma,
      theta: theta || contract.theta,
      vega: vega || contract.vega,
    };
  }

  /**
   * Normal CDF approximation
   */
  private normalCDF(x: number): number {
    return 0.5 * (1 + this.erf(x / Math.sqrt(2)));
  }

  /**
   * Normal PDF
   */
  private normalPDF(x: number): number {
    return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
  }

  /**
   * Error function approximation
   */
  private erf(x: number): number {
    const a1 = 0.254829592;
    const a2 = -0.284496736;
    const a3 = 1.421413741;
    const a4 = -1.453152027;
    const a5 = 1.061405429;
    const p = 0.3275911;

    const sign = x < 0 ? -1 : 1;
    x = Math.abs(x);

    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);

    return sign * y;
  }

  /**
   * Analyze options flow for unusual activity
   */
  public analyzeFlow(flow: OptionsFlow[]): {
    totalVolume: number;
    callVolume: number;
    putVolume: number;
    putCallRatio: number;
    largestTrade: OptionsFlow | null;
    opportunities: OptionsFlow[];
  } {
    const totalVolume = flow.reduce((sum, f) => sum + f.volume, 0);
    const callVolume = flow.filter(f => f.optionType === 'CALL').reduce((sum, f) => sum + f.volume, 0);
    const putVolume = flow.filter(f => f.optionType === 'PUT').reduce((sum, f) => sum + f.volume, 0);
    const putCallRatio = callVolume > 0 ? putVolume / callVolume : 0;
    
    const largestTrade = flow.reduce((max, f) => 
      f.volume > (max?.volume || 0) ? f : max, 
      null as OptionsFlow | null
    );

    const opportunities = flow
      .filter(f => f.score > 7.0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);

    return {
      totalVolume,
      callVolume,
      putVolume,
      putCallRatio,
      largestTrade,
      opportunities,
    };
  }

  /**
   * Backtest an options strategy
   */
  public backtestStrategy(
    strategy: OptionsStrategy,
    historicalPrices: Array<{ date: string; price: number }>,
    currentPrice: number
  ): {
    totalReturn: number;
    maxDrawdown: number;
    winRate: number;
    sharpeRatio: number;
    trades: Array<{ date: string; price: number; pnl: number }>;
  } {
    const trades: Array<{ date: string; price: number; pnl: number }> = [];
    let totalPnL = 0;
    let maxPnL = 0;
    let minPnL = 0;
    let wins = 0;

    for (const pricePoint of historicalPrices) {
      // Calculate P&L for this price point
      let pnl = 0;
      
      for (const contract of strategy.contracts) {
        const intrinsicValue = contract.type === 'CALL'
          ? Math.max(0, pricePoint.price - contract.strike)
          : Math.max(0, contract.strike - pricePoint.price);
        
        const contractPnL = contract.action === 'BUY'
          ? (intrinsicValue - (currentPrice * 0.1)) * contract.quantity // Simplified premium
          : ((currentPrice * 0.1) - intrinsicValue) * contract.quantity;
        
        pnl += contractPnL;
      }

      totalPnL += pnl;
      maxPnL = Math.max(maxPnL, totalPnL);
      minPnL = Math.min(minPnL, totalPnL);
      
      if (pnl > 0) wins++;

      trades.push({
        date: pricePoint.date,
        price: pricePoint.price,
        pnl,
      });
    }

    const totalReturn = totalPnL;
    const maxDrawdown = maxPnL - minPnL;
    const winRate = trades.length > 0 ? wins / trades.length : 0;
    
    // Simplified Sharpe ratio
    const avgReturn = trades.length > 0 ? totalPnL / trades.length : 0;
    const variance = trades.reduce((sum, t) => sum + Math.pow(t.pnl - avgReturn, 2), 0) / trades.length;
    const stdDev = Math.sqrt(variance);
    const sharpeRatio = stdDev > 0 ? avgReturn / stdDev : 0;

    return {
      totalReturn,
      maxDrawdown,
      winRate,
      sharpeRatio,
      trades,
    };
  }
}

export default OptionsFlowService;

