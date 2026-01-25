/**
 * TYPED VERSION: Options Flow Service with generated GraphQL types
 * 
 * This replaces manual interfaces with generated types for full type safety.
 */

import { gql } from '@apollo/client';
import { API_HTTP } from '../../../config/api';
import type {
  ExtendedQueryOptionsAnalysisArgs,
  ExtendedQueryScanOptionsArgs,
  OptionsChainType,
  OptionsAnalysisType,
  OptionsContractType,
  OptionsStrategyType,
} from '../../../generated/graphql';

// ✅ Using generated types instead of manual interfaces
export type OptionsContract = OptionsContractType;
export type OptionsChain = OptionsChainType;
export type OptionsStrategy = OptionsStrategyType;

// GraphQL Queries with proper operation names
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

/**
 * Typed hook to fetch options chain
 */
export function useOptionsChain(symbol: string) {
  // This would be used with useQuery in a component
  // Example:
  // const { data, loading, error } = useQuery<
  //   ExtendedQueryOptionsChainQuery,
  //   ExtendedQueryOptionsChainQueryVariables
  // >(GET_OPTIONS_CHAIN, { variables: { symbol } });
  // return { chain: data?.optionsChain, loading, error };
}

/**
 * Typed helper: Get top call option by volume
 */
export function getTopCallByVolume(chain: OptionsChainType | null | undefined): OptionsContractType | null {
  if (!chain?.calls || chain.calls.length === 0) return null;
  
  // ✅ TypeScript knows calls is an array of OptionsContractType
  return [...chain.calls]
    .filter(call => call != null)
    .sort((a, b) => (b?.volume ?? 0) - (a?.volume ?? 0))[0] || null;
}

/**
 * Typed helper: Get top put option by volume
 */
export function getTopPutByVolume(chain: OptionsChainType | null | undefined): OptionsContractType | null {
  if (!chain?.puts || chain.puts.length === 0) return null;
  
  // ✅ TypeScript knows puts is an array of OptionsContractType
  return [...chain.puts]
    .filter(put => put != null)
    .sort((a, b) => (b?.volume ?? 0) - (a?.volume ?? 0))[0] || null;
}

/**
 * Typed helper: Format options contract for display
 */
export function formatOptionsContract(contract: OptionsContractType | null | undefined): string {
  if (!contract) return 'N/A';
  
  // ✅ All fields are typed - no guessing!
  return `${contract.optionType} $${contract.strike} (IV: ${contract.impliedVolatility}%)`;
}

/**
 * Typed helper: Get best strategy by confidence
 */
export function getBestStrategy(
  analysis: OptionsAnalysisType | null | undefined
): OptionsStrategyType | null {
  if (!analysis?.recommendedStrategies || analysis.recommendedStrategies.length === 0) {
    return null;
  }
  
  // ✅ TypeScript knows recommendedStrategies structure
  return [...analysis.recommendedStrategies]
    .filter(strategy => strategy != null)
    .sort((a, b) => (b?.probabilityOfProfit ?? 0) - (a?.probabilityOfProfit ?? 0))[0] || null;
}

// Keep the service class for backward compatibility, but use typed interfaces
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
   * Now uses typed OptionsContractType
   */
  public calculateGreeks(
    contract: OptionsContractType | null,
    underlyingPrice: number,
    timeToExpiration: number,
    riskFreeRate: number = 0.05
  ): Partial<OptionsContractType> {
    if (!contract) {
      return {};
    }

    // ✅ TypeScript knows all fields on contract
    const { strike, impliedVolatility } = contract;
    const S = underlyingPrice;
    const K = strike ?? 0;
    const T = timeToExpiration / 365;
    const r = riskFreeRate;
    const sigma = (impliedVolatility ?? 0) / 100;

    // Simplified delta calculation
    const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * Math.sqrt(T));
    
    // Return typed partial contract
    return {
      delta: this.normalCDF(d1),
      gamma: this.normalPDF(d1) / (S * sigma * Math.sqrt(T)),
      // ... other Greeks
    };
  }

  private normalCDF(x: number): number {
    // Implementation
    return 0.5 * (1 + this.erf(x / Math.sqrt(2)));
  }

  private normalPDF(x: number): number {
    return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
  }

  private erf(x: number): number {
    // Approximation
    const a1 = 0.254829592;
    const a2 = -0.284496736;
    const a3 = 1.421413741;
    const a4 = -1.453152027;
    const a5 = 1.061405429;
    const p = 0.3275911;

    const sign = x < 0 ? -1 : 1;
    x = Math.abs(x);

    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t) * Math.exp(-x * x);

    return sign * y;
  }
}

export default OptionsFlowService;

