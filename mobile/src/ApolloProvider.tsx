// ApolloProvider.tsx
import React, { useMemo } from 'react';
import { ApolloProvider as Provider } from '@apollo/client';
import { makeApolloClient, getApiBase } from './lib/apolloFactory';
import JWTAuthService from './features/auth/services/JWTAuthService';

// Quick health check probe - safe version
(async () => {
  try {
    const baseUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
    if (baseUrl) {
      const response = await fetch(`${baseUrl}/health`, { 
        method: 'GET',
        signal: AbortSignal.timeout(5000), // 5 second timeout
      } as RequestInit);
      console.log('[health] Status:', response.status, 'Text:', await response.text());
    } else {
      console.log('[health] Skipping - no API base URL set yet');
    }
  } catch (e: any) {
    console.log('[health:error]', e?.message || 'Unknown error');
  }
})();

export default function ApolloProvider({ children }: { children: React.ReactNode }) {
  const client = useMemo(() => {
    console.log('[ApolloProvider] Creating Apollo client...');
    const apolloClient = makeApolloClient();
    // Initialize the JWT service with the Apollo client
    JWTAuthService.getInstance().setApolloClient(apolloClient);
    console.log('[ApolloProvider] Apollo client created successfully');
    return apolloClient;
  }, []);

  if (__DEV__) {
    console.log('🔌 GRAPHQL_URL:', process.env.EXPO_PUBLIC_GRAPHQL_URL);
  }

  return <Provider client={client}>{children}</Provider>;
}