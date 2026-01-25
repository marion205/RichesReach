/**
 * TYPED VERSION: useStrategies hook with generated GraphQL types
 *
 * This is the "after" version showing how to use generated types.
 * Compare with useStrategies.ts to see the improvement.
 */

import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import type {
  StrategyType,
  UserStrategySettingsType,
} from '../../../generated/graphql';

// GraphQL Queries - Now with proper operation names for codegen
const GET_STRATEGIES = gql`
  query GetStrategies($marketType: String, $category: String) {
    strategies(marketType: $marketType, category: $category) {
      id
      slug
      name
      category
      description
      marketType
      timeframeSupported
      influencerRef
      enabled
      defaultVersion {
        id
        version
        configSchema
        logicRef
      }
    }
  }
`;

const GET_STRATEGY = gql`
  query GetStrategy($id: ID!) {
    strategy(id: $id) {
      id
      slug
      name
      category
      description
      marketType
      timeframeSupported
      influencerRef
      enabled
      defaultVersion {
        id
        version
        configSchema
        logicRef
      }
    }
  }
`;

const GET_USER_STRATEGY_SETTINGS = gql`
  query GetUserStrategySettings {
    userStrategySettings {
      id
      strategyVersion {
        id
        strategy {
          id
          name
          slug
        }
      }
      enabled
      customConfig
    }
  }
`;

const ENABLE_STRATEGY = gql`
  mutation EnableStrategy($strategyVersionId: ID!, $customConfig: JSONString) {
    enableStrategy(strategyVersionId: $strategyVersionId, customConfig: $customConfig) {
      id
      enabled
    }
  }
`;

const DISABLE_STRATEGY = gql`
  mutation DisableStrategy($strategyVersionId: ID!) {
    disableStrategy(strategyVersionId: $strategyVersionId) {
      id
      enabled
    }
  }
`;

// ✅ Now using generated types instead of manual interfaces
export type Strategy = StrategyType;
export type UserStrategySettings = UserStrategySettingsType;

/**
 * Hook to fetch strategies with filtering
 *
 * @param marketType - Optional market type filter (STOCKS, FUTURES, FOREX, CRYPTO)
 * @param category - Optional category filter (MOMENTUM, REVERSAL, etc.)
 * @returns Typed strategies array with loading/error states
 */
export const useStrategies = (marketType?: string, category?: string) => {
  const { data, loading, error, refetch } = useQuery(GET_STRATEGIES, {
    variables: { marketType, category },
    fetchPolicy: 'cache-first',
    nextFetchPolicy: 'cache-first',
    notifyOnNetworkStatusChange: false,
    errorPolicy: 'all',
  });

  return {
    // ✅ Fully typed - TypeScript knows the exact shape
    strategies: (data?.strategies || []) as StrategyType[],
    loading,
    error,
    refetch,
  };
};

/**
 * Hook to fetch a single strategy by ID
 *
 * @param id - Strategy ID
 * @returns Typed strategy with loading/error states
 */
export const useStrategy = (id: string) => {
  const { data, loading, error, refetch } = useQuery(GET_STRATEGY, {
    variables: { id },
    fetchPolicy: 'cache-first',
    skip: !id,
  });

  return {
    // ✅ Fully typed strategy
    strategy: data?.strategy as StrategyType | undefined,
    loading,
    error,
    refetch,
  };
};

/**
 * Hook to fetch user's strategy settings
 *
 * @returns Typed user strategy settings
 */
export const useUserStrategySettings = () => {
  const { data, loading, error, refetch } = useQuery(GET_USER_STRATEGY_SETTINGS,
    {
      fetchPolicy: 'cache-first',
    },
  );

  return {
    // ✅ Fully typed settings array
    settings: (data?.userStrategySettings || []) as UserStrategySettingsType[],
    loading,
    error,
    refetch,
  };
};

/**
 * Hook to enable a strategy
 *
 * @returns Mutation function with typed parameters
 */
export const useEnableStrategy = () => {
  const [enableStrategy, { loading, error }] = useMutation(ENABLE_STRATEGY);

  return {
    enableStrategy: async (strategyVersionId: string, customConfig?: Record<string, unknown>) => {
      return enableStrategy({
        variables: {
          strategyVersionId,
          customConfig: customConfig as any, // JSONString type
        },
      });
    },
    loading,
    error,
  };
};

/**
 * Hook to disable a strategy
 *
 * @returns Mutation function with typed parameters
 */
export const useDisableStrategy = () => {
  const [disableStrategy, { loading, error }] = useMutation(DISABLE_STRATEGY);

  return {
    disableStrategy: async (strategyVersionId: string) => {
      return disableStrategy({
        variables: { strategyVersionId },
      });
    },
    loading,
    error,
  };
};
