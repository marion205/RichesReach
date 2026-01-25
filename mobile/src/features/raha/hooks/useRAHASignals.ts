import { useRef, useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import {
  GET_RAHA_SIGNALS,
  GENERATE_RAHA_SIGNALS,
} from '../../../graphql/raha';
import logger from '../../../utils/logger';

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
  const consecutiveErrorsRef = useRef(0);
  const lastErrorRef = useRef<Error | null>(null);
  const MAX_CONSECUTIVE_ERRORS = 3;
  const pollingStoppedRef = useRef(false);
  const [isPollingStopped, setIsPollingStopped] = useState(false);

  const { data, loading, error, refetch, stopPolling, startPolling } = useQuery(GET_RAHA_SIGNALS, {
    variables: { symbol, timeframe, limit },
    skip: !symbol,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all', // Return partial data even with errors - don't block UI
    notifyOnNetworkStatusChange: false, // Don't update loading state on network changes
    pollInterval: 30000, // Poll every 30 seconds for live signals
    onError: (err) => {
      try {
        const networkError = err?.networkError as any;
        const statusCode = networkError?.statusCode;
        
        // Check if it's a 500 error (server error)
        if (statusCode === 500) {
          consecutiveErrorsRef.current += 1;
          lastErrorRef.current = err;
          
          const errorMessage = networkError?.message || err?.message || 'Unknown server error';
          const errorResult = networkError?.result;
          
          try {
            logger.warn(`⚠️ GetRAHASignals: Server error (500) - consecutive errors: ${consecutiveErrorsRef.current}/${MAX_CONSECUTIVE_ERRORS}`, {
              symbol,
              timeframe,
              errorMessage: typeof errorMessage === 'string' ? errorMessage.substring(0, 200) : String(errorMessage),
              errorResult: errorResult ? (typeof errorResult === 'string' ? errorResult.substring(0, 200) : JSON.stringify(errorResult).substring(0, 200)) : undefined,
            });
          } catch (logError) {
            // Fallback if logger fails
            console.warn(`⚠️ GetRAHASignals: Server error (500) - consecutive errors: ${consecutiveErrorsRef.current}/${MAX_CONSECUTIVE_ERRORS}`);
          }
          
          // Stop polling after too many consecutive errors to avoid spam
          if (consecutiveErrorsRef.current >= MAX_CONSECUTIVE_ERRORS && !pollingStoppedRef.current) {
            try {
              logger.warn('⚠️ GetRAHASignals: Too many consecutive server errors, stopping polling to prevent spam', {
                symbol,
                timeframe,
                totalErrors: consecutiveErrorsRef.current,
              });
            } catch (logError) {
              console.warn('⚠️ GetRAHASignals: Too many consecutive server errors, stopping polling');
            }
            pollingStoppedRef.current = true;
            setIsPollingStopped(true);
            stopPolling?.();
          }
        } else {
          // Reset counter on non-500 errors (e.g., network issues, auth errors)
          if (consecutiveErrorsRef.current > 0) {
            try {
              logger.log(`✅ GetRAHASignals: Non-500 error (${statusCode}), resetting error counter`);
            } catch (logError) {
              // Ignore logging errors
            }
          }
          consecutiveErrorsRef.current = 0;
        }
      } catch (errorHandlerError) {
        // If error handler itself fails, just log and continue
        console.error('Error in GetRAHASignals error handler:', errorHandlerError);
      }
    },
    onCompleted: () => {
      try {
        // Reset error counter on successful query
        if (consecutiveErrorsRef.current > 0) {
          try {
            logger.log('✅ GetRAHASignals: Query succeeded, resetting error counter', {
              symbol,
              timeframe,
              previousErrors: consecutiveErrorsRef.current,
            });
          } catch (logError) {
            // Ignore logging errors
          }
          consecutiveErrorsRef.current = 0;
          lastErrorRef.current = null;
          
          // Resume polling if it was stopped
          if (pollingStoppedRef.current) {
            try {
              logger.log('🔄 GetRAHASignals: Resuming polling after successful query');
            } catch (logError) {
              // Ignore logging errors
            }
            pollingStoppedRef.current = false;
            setIsPollingStopped(false);
            startPolling?.(30000);
          }
        }
      } catch (completedHandlerError) {
        // If completed handler fails, just log and continue
        console.error('Error in GetRAHASignals completed handler:', completedHandlerError);
      }
    },
  });

  // Regime data is available in the signals
  // Removed debug logging

  return {
    signals: (data?.rahaSignals || []) as RAHASignal[],
    loading,
    error,
    refetch,
    // Expose polling state and control
    isPollingStopped,
    stopPolling: () => {
      pollingStoppedRef.current = true;
      setIsPollingStopped(true);
      stopPolling?.();
      logger.log('🛑 GetRAHASignals: Polling stopped manually');
    },
    startPolling: () => {
      consecutiveErrorsRef.current = 0;
      lastErrorRef.current = null;
      pollingStoppedRef.current = false;
      setIsPollingStopped(false);
      startPolling?.(30000);
      logger.log('▶️ GetRAHASignals: Polling started/resumed manually');
    },
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

