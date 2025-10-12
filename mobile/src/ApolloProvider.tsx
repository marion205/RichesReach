// ApolloProvider.tsx
import React, { useMemo } from 'react';
import { ApolloProvider as Provider } from '@apollo/client';
import { makeApolloClient, getApiBase } from './lib/apolloFactory';
import JWTAuthService from './features/auth/services/JWTAuthService';

// Quick health check probe
(async () => {
  try {
    const baseUrl = getApiBase();
    const response = await fetch(`${baseUrl}/health`, { 
      method: 'GET',
      timeout: 5000 
    });
    console.log('[health] Status:', response.status, 'Text:', await response.text());
  } catch (e: any) {
    console.log('[health:error]', e?.message || 'Unknown error');
  }
})();

export default function ApolloProvider({ children }: { children: React.ReactNode }) {
  const client = useMemo(() => {
    const apolloClient = makeApolloClient();
    // Initialize the JWT service with the Apollo client
    JWTAuthService.getInstance().setApolloClient(apolloClient);
    return apolloClient;
  }, [getApiBase()]);

  console.log('[API_BASE]', getApiBase(), 'graphql ->', `${getApiBase()}/graphql`);

  return <Provider client={client}>{children}</Provider>;
}