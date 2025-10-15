// Enhanced Apollo Client for Crypto with Relay Pagination & Error Handling
import { makeApolloClient } from './lib/apolloFactory';

// Create crypto client using the same factory
export const cryptoClient = makeApolloClient();

// Create repay client using the same factory
export const repayClient = makeApolloClient();

// Optimistic update helpers
export const optimisticTradeUpdate = {
  executeCryptoTrade: (cache: any, { data }: any) => {
    if (data?.executeCryptoTrade?.success) {
      // Add new trade to cache
      const newTrade = data.executeCryptoTrade.trade;
      cache.modify({
        fields: {
          cryptoTrades: (existing: any, { readField }: any) => {
            // Add to beginning of trades list
            return {
              ...existing,
              edges: [
                {
                  node: newTrade,
                  cursor: newTrade.id,
                  __typename: 'TradeEdge',
                },
                ...(existing?.edges || []),
              ],
            };
          },
        },
      });
    }
  },
};

// Cache update helpers
export const updatePortfolioCache = (cache: any, newData: any) => {
  cache.modify({
    fields: {
      cryptoPortfolio: () => newData,
    },
  });
};

export const updateSblocLoansCache = (cache: any, newData: any) => {
  cache.modify({
    fields: {
      cryptoSblocLoans: () => newData,
    },
  });
};

// Error handling utilities
export const handleGraphQLError = (error: any) => {
  if (error.graphQLErrors) {
    return error.graphQLErrors.map((err: any) => err.message).join(', ');
  }
  if (error.networkError) {
    return 'Network error - please check your connection';
  }
  return 'An unexpected error occurred';
};

// Retry logic for failed mutations
export const retryMutation = async (mutation: any, variables: any, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await mutation({ variables });
      if (result.data) {
        return result;
      }
    } catch (error) {
      if (i === maxRetries - 1) {
        throw error;
      }
      // Wait before retry (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }
  throw new Error('Max retries exceeded');
};
