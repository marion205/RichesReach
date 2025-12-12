/**
 * TYPED VERSION: Portfolio hooks with generated GraphQL types
 *
 * This replaces manual interfaces with generated types for full type safety.
 */

import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import type {
  ExtendedQueryMyPortfoliosQuery,
  ExtendedQueryMyPortfoliosQueryVariables,
  ExtendedMutationCreatePortfolioMutation,
  ExtendedMutationCreatePortfolioMutationVariables,
  ExtendedMutationCreatePortfolioHoldingMutation,
  ExtendedMutationCreatePortfolioHoldingMutationVariables,
  PortfolioType,
  PortfolioHoldingType,
} from '../../../generated/graphql';

// ✅ Using generated types
export type Portfolio = PortfolioType;
export type PortfolioHolding = PortfolioHoldingType;

const GET_MY_PORTFOLIOS = gql`
  query GetMyPortfolios {
    myPortfolios {
      portfolios {
        id
        name
        totalValue
        holdingsCount
        holdings {
          id
          symbol
          shares
          averagePrice
          currentPrice
          totalValue
          unrealizedGain
          unrealizedGainPercent
        }
      }
      totalValue
      totalPortfolios
    }
  }
`;

const CREATE_PORTFOLIO = gql`
  mutation CreatePortfolio($name: String!) {
    createPortfolio(name: $name) {
      success
      message
      portfolio {
        id
        name
        totalValue
        holdingsCount
      }
    }
  }
`;

const CREATE_PORTFOLIO_HOLDING = gql`
  mutation CreatePortfolioHolding(
    $portfolioId: ID!
    $symbol: String!
    $shares: Float!
    $averagePrice: Float!
  ) {
    createPortfolioHolding(
      portfolioId: $portfolioId
      symbol: $symbol
      shares: $shares
      averagePrice: $averagePrice
    ) {
      success
      message
      holding {
        id
        symbol
        shares
        averagePrice
        currentPrice
        totalValue
      }
    }
  }
`;

/**
 * Hook to fetch user's portfolios
 *
 * @returns Typed portfolios with loading/error states
 */
export const useMyPortfolios = () => {
  const { data, loading, error, refetch } = useQuery<
    ExtendedQueryMyPortfoliosQuery,
    ExtendedQueryMyPortfoliosQueryVariables
  >(GET_MY_PORTFOLIOS, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  return {
    // ✅ Fully typed portfolios
    portfolios: (data?.myPortfolios?.portfolios || []) as PortfolioType[],
    totalValue: data?.myPortfolios?.totalValue ?? 0,
    totalPortfolios: data?.myPortfolios?.totalPortfolios ?? 0,
    loading,
    error,
    refetch,
  };
};

/**
 * Hook to create a new portfolio
 *
 * @returns Mutation function with typed parameters
 */
export const useCreatePortfolio = () => {
  const [createPortfolio, { loading, error }] = useMutation<
    ExtendedMutationCreatePortfolioMutation,
    ExtendedMutationCreatePortfolioMutationVariables
  >(CREATE_PORTFOLIO, {
    refetchQueries: [GET_MY_PORTFOLIOS],
  });

  return {
    createPortfolio: async (name: string) => {
      return createPortfolio({
        variables: { name },
      });
    },
    loading,
    error,
  };
};

/**
 * Hook to add a holding to a portfolio
 *
 * @returns Mutation function with typed parameters
 */
export const useCreatePortfolioHolding = () => {
  const [createHolding, { loading, error }] = useMutation<
    ExtendedMutationCreatePortfolioHoldingMutation,
    ExtendedMutationCreatePortfolioHoldingMutationVariables
  >(CREATE_PORTFOLIO_HOLDING, {
    refetchQueries: [GET_MY_PORTFOLIOS],
  });

  return {
    createHolding: async (
      portfolioId: string,
      symbol: string,
      shares: number,
      averagePrice: number
    ) => {
      return createHolding({
        variables: {
          portfolioId,
          symbol,
          shares,
          averagePrice,
        },
      });
    },
    loading,
    error,
  };
};

/**
 * Typed helper: Calculate total portfolio value
 */
export function calculateTotalPortfolioValue(portfolios: PortfolioType[]): number {
  // ✅ TypeScript knows totalValue exists and is nullable
  return portfolios.reduce((sum, portfolio) => sum + (portfolio.totalValue ?? 0), 0);
}

/**
 * Typed helper: Get portfolio by ID
 */
export function getPortfolioById(portfolios: PortfolioType[], id: string): PortfolioType | null {
  // ✅ TypeScript knows id field exists
  return portfolios.find(p => p.id === id) || null;
}

/**
 * Typed helper: Calculate portfolio performance
 */
export function calculatePortfolioPerformance(portfolio: PortfolioType): {
  totalValue: number;
  totalGain: number;
  totalGainPercent: number;
} {
  const totalValue = portfolio.totalValue ?? 0;
  const holdings = portfolio.holdings || [];

  // ✅ TypeScript knows holdings structure
  const totalGain = holdings.reduce((sum, holding) => sum + (holding?.unrealizedGain ?? 0), 0);

  const costBasis = holdings.reduce(
    (sum, holding) => sum + (holding?.averagePrice ?? 0) * (holding?.shares ?? 0),
    0
  );

  const totalGainPercent = costBasis > 0 ? (totalGain / costBasis) * 100 : 0;

  return {
    totalValue,
    totalGain,
    totalGainPercent,
  };
}
