/**
 * TYPED VERSION: useRAHASignals hook with generated GraphQL types
 *
 * Example showing how to type RAHA signals queries
 */

import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import type {
  ExtendedQueryRahaSignalsQuery,
  ExtendedQueryRahaSignalsQueryVariables,
  ExtendedMutationGenerateRahaSignalsMutation,
  ExtendedMutationGenerateRahaSignalsMutationVariables,
  RahaSignalType,
} from '../../../generated/graphql';

// ✅ Using generated type instead of manual interface
export type RAHASignal = RahaSignalType;

const GET_RAHA_SIGNALS = gql`
  query GetRahaSignals($symbol: String!, $timeframe: String, $limit: Int) {
    rahaSignals(symbol: $symbol, timeframe: $timeframe, limit: $limit) {
      id
      symbol
      timestamp
      timeframe
      signalType
      price
      stopLoss
      takeProfit
      confidenceScore
      meta
      regimeMultiplier
      regimeNarration
      globalRegime
      localContext
      strategyVersion {
        id
        strategy {
          id
          name
          slug
        }
      }
    }
  }
`;

const GENERATE_RAHA_SIGNALS = gql`
  mutation GenerateRahaSignals($symbol: String!, $timeframe: String!) {
    generateRahaSignals(symbol: $symbol, timeframe: $timeframe) {
      id
      symbol
      timestamp
      signalType
      price
      confidenceScore
    }
  }
`;

/**
 * Hook to fetch RAHA signals for a symbol
 *
 * @param symbol - Stock symbol (e.g., 'AAPL')
 * @param timeframe - Timeframe (default: '5m')
 * @param limit - Maximum number of signals to return
 * @returns Typed signals array with loading/error states
 */
export const useRAHASignals = (symbol: string, timeframe: string = '5m', limit?: number) => {
  const { data, loading, error, refetch } = useQuery<
    ExtendedQueryRahaSignalsQuery,
    ExtendedQueryRahaSignalsQueryVariables
  >(GET_RAHA_SIGNALS, {
    variables: { symbol, timeframe, limit },
    skip: !symbol,
    fetchPolicy: 'cache-and-network',
    pollInterval: 30000, // Poll every 30 seconds for new signals
  });

  return {
    // ✅ Fully typed signals - TypeScript knows all fields
    signals: (data?.rahaSignals || []) as RahaSignalType[],
    loading,
    error,
    refetch,
  };
};

/**
 * Hook to generate new RAHA signals
 *
 * @returns Mutation function to generate signals
 */
export const useGenerateRAHASignals = () => {
  const [generateSignals, { loading, error }] = useMutation<
    ExtendedMutationGenerateRahaSignalsMutation,
    ExtendedMutationGenerateRahaSignalsMutationVariables
  >(GENERATE_RAHA_SIGNALS);

  return {
    generateSignals: async (symbol: string, timeframe: string) => {
      return generateSignals({
        variables: { symbol, timeframe },
      });
    },
    loading,
    error,
  };
};

/**
 * Example: Typed helper function using RAHA signals
 */
export function getTopConfidenceSignal(signals: RahaSignalType[]): RahaSignalType | null {
  if (!signals.length) {
    return null;
  }

  // ✅ TypeScript knows confidenceScore exists and is a number
  return [...signals].sort((a, b) => (b.confidenceScore ?? 0) - (a.confidenceScore ?? 0))[0];
}

/**
 * Example: Format signal for display
 */
export function formatSignalSummary(signal: RahaSignalType): string {
  // ✅ All fields are typed - no more guessing!
  return `${signal.signalType} ${signal.symbol} @ $${signal.price} (confidence: ${signal.confidenceScore}%)`;
}
