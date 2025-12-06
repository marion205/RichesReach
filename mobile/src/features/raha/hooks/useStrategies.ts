import { useQuery, useMutation } from '@apollo/client';
import {
  GET_STRATEGIES,
  GET_STRATEGY,
  GET_USER_STRATEGY_SETTINGS,
  ENABLE_STRATEGY,
  DISABLE_STRATEGY,
} from '../../../graphql/raha';
import { useState } from 'react';

export interface Strategy {
  id: string;
  slug: string;
  name: string;
  category: string;
  description: string;
  marketType: string;
  timeframeSupported: string[];
  influencerRef?: string;
  enabled: boolean;
  defaultVersion?: {
    id: string;
    version: number;
    configSchema: any;
    logicRef: string;
  };
}

export interface UserStrategySettings {
  id: string;
  strategyVersion: {
    id: string;
    version: number;
    strategy: Strategy;
  };
  parameters: Record<string, any>;
  enabled: boolean;
  autoTradeEnabled: boolean;
  maxDailyLossPercent?: number;
  maxConcurrentPositions: number;
}

export const useStrategies = (marketType?: string, category?: string) => {
  const { data, loading, error, refetch } = useQuery(GET_STRATEGIES, {
    variables: { marketType, category },
    fetchPolicy: 'cache-and-network',
  });

  return {
    strategies: (data?.strategies || []) as Strategy[],
    loading,
    error,
    refetch,
  };
};

export const useStrategy = (id: string) => {
  const { data, loading, error, refetch } = useQuery(GET_STRATEGY, {
    variables: { id },
    skip: !id,
    fetchPolicy: 'cache-and-network',
  });

  return {
    strategy: data?.strategy as Strategy | undefined,
    loading,
    error,
    refetch,
  };
};

export const useUserStrategySettings = () => {
  const { data, loading, error, refetch } = useQuery(GET_USER_STRATEGY_SETTINGS, {
    fetchPolicy: 'cache-and-network',
  });

  return {
    settings: (data?.userStrategySettings || []) as UserStrategySettings[],
    loading,
    error,
    refetch,
  };
};

export const useEnableStrategy = () => {
  const [enableStrategy, { loading, error }] = useMutation(ENABLE_STRATEGY, {
    refetchQueries: [GET_USER_STRATEGY_SETTINGS, GET_STRATEGIES],
  });

  return {
    enableStrategy: async (strategyVersionId: string, parameters: Record<string, any>) => {
      try {
        const result = await enableStrategy({
          variables: {
            strategyVersionId,
            parameters: JSON.stringify(parameters),
          },
        });
        return {
          success: result.data?.enableStrategy?.success || false,
          message: result.data?.enableStrategy?.message || '',
          settings: result.data?.enableStrategy?.userStrategySettings,
        };
      } catch (err: any) {
        return {
          success: false,
          message: err.message || 'Failed to enable strategy',
          settings: null,
        };
      }
    },
    loading,
    error,
  };
};

export const useDisableStrategy = () => {
  const [disableStrategy, { loading, error }] = useMutation(DISABLE_STRATEGY, {
    refetchQueries: [GET_USER_STRATEGY_SETTINGS, GET_STRATEGIES],
  });

  return {
    disableStrategy: async (strategyVersionId: string) => {
      try {
        const result = await disableStrategy({
          variables: { strategyVersionId },
        });
        return {
          success: result.data?.disableStrategy?.success || false,
          message: result.data?.disableStrategy?.message || '',
        };
      } catch (err: any) {
        return {
          success: false,
          message: err.message || 'Failed to disable strategy',
        };
      }
    },
    loading,
    error,
  };
};

