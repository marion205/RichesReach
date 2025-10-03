// Enhanced Apollo Client for Crypto with Relay Pagination & Error Handling
import { ApolloClient, InMemoryCache, createHttpLink, from } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';
import { relayStylePagination } from '@apollo/client/utilities';

// HTTP Link for crypto API
const cryptoHttpLink = createHttpLink({
  uri: 'https://54.226.87.216/graphql',
});

// HTTP Link for repay API
const repayHttpLink = createHttpLink({
  uri: 'https://54.226.87.216/graphql',
});

// Auth context
const authLink = setContext((_, { headers }) => {
  // Get auth token from storage
  const token = localStorage.getItem('authToken');
  
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    }
  };
});

// Error handling
const errorLink = onError(({ graphQLErrors, networkError, operation, forward }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, locations, path, extensions }) => {
      console.error(
        `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
      );
      
      // Handle specific error codes
      if (extensions?.code === 'UNAUTHENTICATED') {
        // Redirect to login
        window.location.href = '/login';
      } else if (extensions?.code === 'FORBIDDEN') {
        // Show permission error
        console.error('Insufficient permissions');
      } else if (extensions?.code === 'VALIDATION') {
        // Show validation error
        console.error('Validation error:', message);
      }
    });
  }

  if (networkError) {
    console.error(`[Network error]: ${networkError}`);
    
    // Handle network errors
    if ((networkError as any).statusCode === 401) {
      // Unauthorized - redirect to login
      window.location.href = '/login';
    } else if ((networkError as any).statusCode >= 500) {
      // Server error - show retry option
      console.error('Server error - please try again');
    }
  }
});

// Cache configuration with Relay pagination
const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        // Relay-style pagination for trades
        cryptoTrades: relayStylePagination(['symbol']),
        
        // Cache policies for other queries
        cryptoPortfolio: {
          merge: true, // Merge partial updates
        },
        cryptoSblocLoans: {
          merge: true,
        },
        cryptoPrice: {
          merge: true,
        },
        cryptoMlSignal: {
          merge: true,
        },
      },
    },
    // Entity policies
    CryptoTrade: {
      keyFields: ['id'],
    },
    SblocLoan: {
      keyFields: ['id'],
    },
    Cryptocurrency: {
      keyFields: ['symbol'],
    },
    CryptoHolding: {
      keyFields: ['id'],
    },
  },
});

// Create crypto client
export const cryptoClient = new ApolloClient({
  link: from([errorLink, authLink, cryptoHttpLink]),
  cache,
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    },
    query: {
      fetchPolicy: 'cache-first',
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
});

// Create repay client
export const repayClient = new ApolloClient({
  link: from([errorLink, authLink, repayHttpLink]),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    },
    query: {
      fetchPolicy: 'cache-first',
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
});

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
