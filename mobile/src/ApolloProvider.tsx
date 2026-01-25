// ApolloProvider.tsx
import React, { useMemo } from 'react';
import { ApolloProvider as Provider } from '@apollo/client';
import { makeApolloClient, getApiBase } from './lib/apolloFactory';
import JWTAuthService from './features/auth/services/JWTAuthService';
import logger from './utils/logger';

// Quick health check probe - safe version
(async () => {
  try {
    const baseUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
    if (baseUrl) {
      // Use AbortController instead of AbortSignal.timeout (not available in React Native)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      try {
        const response = await fetch(`${baseUrl}/health`, { 
          method: 'GET',
          signal: controller.signal,
        } as RequestInit);
        clearTimeout(timeoutId);
        logger.log('[health] Status:', response.status);
      } catch (fetchError) {
        clearTimeout(timeoutId);
        throw fetchError;
      }
    } else {
      logger.log('[health] Skipping - no API base URL set yet');
    }
  } catch (e: any) {
    logger.log('[health:error]', e?.message || 'Unknown error');
  }
})();

export default function ApolloProvider({ children }: { children: React.ReactNode }) {
  const client = useMemo(() => {
    logger.log('[ApolloProvider] Creating Apollo client...');
    const apolloClient = makeApolloClient();
    // Initialize the JWT service with the Apollo client
    JWTAuthService.getInstance().setApolloClient(apolloClient);
    logger.log('[ApolloProvider] Apollo client created successfully');
    return apolloClient;
  }, []);

  if (__DEV__) {
    logger.log('🔌 GRAPHQL_URL:', process.env.EXPO_PUBLIC_GRAPHQL_URL);
  }

  return <Provider client={client}>{children}</Provider>;
}

// Export client getter function for direct access (if needed)
export const getApolloClient = () => {
  return makeApolloClient();
};