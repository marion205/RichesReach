import { useEffect } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import {
  GET_RAHA_SIGNALS,
  GENERATE_RAHA_SIGNALS,
} from '../../../graphql/raha';

export interface RAHASignal {
  id: string;
  symbol: string;
  timestamp: string;
  timeframe: string;
  signalType: string;
  price: number;
  stopLoss?: number;
  takeProfit?: number;
  confidenceScore: number;
  meta: Record<string, any>;
  regimeMultiplier?: number;
  regimeNarration?: string;
  globalRegime?: string;
  localContext?: string;
  strategyVersion?: {
    id: string;
    strategy: {
      id: string;
      name: string;
      slug: string;
    };
  };
}

export const useRAHASignals = (symbol: string, timeframe: string = '5m', limit?: number) => {
  const { data, loading, error, refetch } = useQuery(GET_RAHA_SIGNALS, {
    variables: { symbol, timeframe, limit },
    skip: !symbol,
    fetchPolicy: 'cache-and-network',
    pollInterval: 30000, // Poll every 30 seconds for live signals
  });

  // Log regime data for debugging
  useEffect(() => {
    if (data?.rahaSignals && data.rahaSignals.length > 0) {
      const firstSignal = data.rahaSignals[0];
      console.log('[RAHA] Regime payload:', {
        symbol,
        globalRegime: firstSignal.globalRegime,
        localContext: firstSignal.localContext,
        regimeMultiplier: firstSignal.regimeMultiplier,
        regimeNarration: firstSignal.regimeNarration,
        signalType: firstSignal.signalType,
      });
    }
  }, [data, symbol]);

  return {
    signals: (data?.rahaSignals || []) as RAHASignal[],
    loading,
    error,
    refetch,
  };
};

export const useGenerateRAHASignals = () => {
  const [generateSignals, { loading, error }] = useMutation(GENERATE_RAHA_SIGNALS);

  return {
    generateSignals: async (
      strategyVersionId: string,
      symbol: string,
      timeframe: string = '5m',
      lookbackCandles?: number,
      parameters?: Record<string, any>
    ) => {
      try {
        const result = await generateSignals({
          variables: {
            strategyVersionId,
            symbol,
            timeframe,
            lookbackCandles,
            parameters: parameters ? JSON.stringify(parameters) : undefined,
          },
        });
        return {
          success: result.data?.generateRAHASignals?.success || false,
          message: result.data?.generateRAHASignals?.message || '',
          signals: (result.data?.generateRAHASignals?.signals || []) as RAHASignal[],
        };
      } catch (err: any) {
        return {
          success: false,
          message: err.message || 'Failed to generate signals',
          signals: [],
        };
      }
    },
    loading,
    error,
  };
};

