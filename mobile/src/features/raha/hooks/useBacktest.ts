import { useQuery, useMutation } from '@apollo/client';
import {
  GET_BACKTEST_RUN,
  GET_USER_BACKTESTS,
  RUN_BACKTEST,
} from '../../../graphql/raha';

export interface BacktestRun {
  id: string;
  symbol: string;
  timeframe: string;
  startDate: string;
  endDate: string;
  status: string;
  parameters: Record<string, any>;
  metrics?: {
    winRate?: number;
    sharpeRatio?: number;
    maxDrawdown?: number;
    expectancy?: number;
    totalTrades?: number;
    winningTrades?: number;
    losingTrades?: number;
    avgWin?: number;
    avgLoss?: number;
    profitFactor?: number;
  };
  equityCurve?: Array<{
    timestamp: string;
    equity: number;
  }>;
  tradeLog?: any[];
  createdAt: string;
  completedAt?: string;
  strategyVersion?: {
    id: string;
    strategy: {
      id: string;
      name: string;
    };
  };
}

export const useBacktestRun = (id: string) => {
  const { data, loading, error, refetch } = useQuery(GET_BACKTEST_RUN, {
    variables: { id },
    skip: !id,
    fetchPolicy: 'cache-and-network',
    pollInterval: (data?.backtestRun?.status === 'RUNNING') ? 5000 : 0, // Poll if running
  });

  return {
    backtest: data?.backtestRun as BacktestRun | undefined,
    loading,
    error,
    refetch,
  };
};

export const useUserBacktests = (limit?: number) => {
  const { data, loading, error, refetch } = useQuery(GET_USER_BACKTESTS, {
    variables: { limit },
    fetchPolicy: 'cache-and-network',
  });

  return {
    backtests: (data?.userBacktests || []) as BacktestRun[],
    loading,
    error,
    refetch,
  };
};

export const useRunBacktest = () => {
  const [runBacktest, { loading, error }] = useMutation(RUN_BACKTEST, {
    refetchQueries: [GET_USER_BACKTESTS],
  });

  return {
    runBacktest: async (
      strategyVersionId: string,
      symbol: string,
      timeframe: string,
      startDate: string,
      endDate: string,
      parameters?: Record<string, any>
    ) => {
      try {
        const result = await runBacktest({
          variables: {
            strategyVersionId,
            symbol,
            timeframe,
            startDate,
            endDate,
            parameters: parameters ? JSON.stringify(parameters) : undefined,
          },
        });
        return {
          success: result.data?.runBacktest?.success || false,
          message: result.data?.runBacktest?.message || '',
          backtestRun: result.data?.runBacktest?.backtestRun,
        };
      } catch (err: any) {
        return {
          success: false,
          message: err.message || 'Failed to run backtest',
          backtestRun: null,
        };
      }
    },
    loading,
    error,
  };
};

