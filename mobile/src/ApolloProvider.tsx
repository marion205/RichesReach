// ApolloProvider.tsx - Production-ready Apollo Client with timeout, retry, and error handling
import React from 'react';
import { ApolloProvider as Provider } from '@apollo/client';
import { apollo } from './lib/apollo';

// Initialize the JWT service with the Apollo client
import JWTAuthService from './features/auth/services/JWTAuthService';
JWTAuthService.getInstance().setApolloClient(apollo);

// Safe cache clearing utility to prevent "Store reset while query was in flight" errors
export const safeClearCache = async () => {
  try {
    // Wait for any pending queries to complete
    await apollo.clearStore();
  } catch (error) {
    console.warn('Cache clear failed, using fallback method:', error);
    // Fallback: just clear the cache without resetting the store
    apollo.cache.reset();
  }
};

export { apollo as client };
export default function ApolloWrapper({ children }: { children: React.ReactNode }) {
  return <Provider client={apollo}>{children}</Provider>;
}