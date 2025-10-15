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
        timeout: 5000 
      });
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
    try {
      console.log('[ApolloProvider] Creating Apollo client...');
      const apolloClient = makeApolloClient();
      // Initialize the JWT service with the Apollo client
      JWTAuthService.getInstance().setApolloClient(apolloClient);
      console.log('[ApolloProvider] Apollo client created successfully');
      return apolloClient;
    } catch (error) {
      console.error('[ApolloProvider] Failed to create Apollo client:', error);
      // Return a minimal client to prevent the app from crashing
      const { ApolloClient, InMemoryCache, HttpLink } = require('@apollo/client');
      return new ApolloClient({
        link: new HttpLink({ uri: 'https://grounds-firewall-thereafter-bracelets.trycloudflare.com/graphql' }),
        cache: new InMemoryCache(),
      });
    }
  }, []);

  try {
    const baseUrl = getApiBase();
    console.log('[API_BASE]', baseUrl, 'graphql ->', `${baseUrl}/graphql/`);
  } catch (error) {
    console.log('[API_BASE] Error getting base URL:', error);
  }

  return <Provider client={client}>{children}</Provider>;
}