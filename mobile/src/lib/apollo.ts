// Apollo Client with enforced timeouts, retries, and comprehensive error handling
// This replaces the old ApolloProvider with production-ready networking

import { ApolloClient, InMemoryCache, HttpLink, from } from "@apollo/client";
import { onError } from "@apollo/client/link/error";
import { RetryLink } from "@apollo/client/link/retry";
import { API_GRAPHQL } from "../config/api";
import { fetchWithTimeout } from "./fetchWithTimeout";
import { loggingLink } from "./linkLogging";

// HTTP Link with timeout
const httpLink = new HttpLink({
  uri: API_GRAPHQL,
  // Send keep-alive-ish headers to help some proxies
  headers: { 
    "Accept-Encoding": "gzip", 
    "Connection": "keep-alive",
    "Content-Type": "application/json"
  },
  fetch: (uri, options) => fetchWithTimeout(uri, options, 8000),
});

// Retry Link with exponential backoff
const retryLink = new RetryLink({
  attempts: (count, operation, error) => {
    // Retry on network errors / 5xx up to 3 times
    if (count >= 3) return false;
    const status = (error as any)?.statusCode;
    return !!(error && (!status || status >= 500));
  },
  delay: (count) => Math.min(1000 * Math.pow(2, count), 5000),
});

// Error Link for comprehensive error logging
const errorLink = onError(({ networkError, operation, graphQLErrors }) => {
  const operationName = operation.operationName || 'Unknown';
  
  if (networkError) {
    console.log(
      `[GraphQL NET ERR] ${operationName}:`,
      networkError.message ?? networkError
    );
  }
  
  if (graphQLErrors) {
    console.log(
      `[GraphQL ERR] ${operationName}:`,
      graphQLErrors
    );
  }
});

// Create Apollo Client with all links
export const apollo = new ApolloClient({
  link: from([loggingLink, errorLink, retryLink, httpLink]),
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          portfolioMetrics: {
            merge: true, // Merge partial updates
          },
          myPortfolios: {
            merge: true, // Merge partial updates
          },
        },
      },
      // Add type policy for portfolio holdings to handle currentPrice field
      PortfolioHolding: {
        keyFields: ["id"], // Use id as the key field
        fields: {
          currentPrice: {
            read(existing, { readField }) {
              // Try to get currentPrice from the holding itself first
              const directPrice = readField('currentPrice');
              if (directPrice !== undefined) {
                return directPrice;
              }
              // If not found, get it from the nested stock object
              const stock = readField('stock');
              return stock?.currentPrice;
            },
          },
        },
      },
      // Add type policy for portfolio positions (used in myPortfolios)
      PortfolioPosition: {
        keyFields: ["id"],
        fields: {
          currentPrice: {
            read(existing, { readField }) {
              // Try to get currentPrice from the position itself first
              const directPrice = readField('currentPrice');
              if (directPrice !== undefined) {
                return directPrice;
              }
              // If not found, get it from the nested stock object
              const stock = readField('stock');
              return stock?.currentPrice;
            },
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: { 
      fetchPolicy: "cache-and-network", 
      errorPolicy: "all" 
    },
    query: { 
      fetchPolicy: "network-only", 
      errorPolicy: "all" 
    },
  },
});
