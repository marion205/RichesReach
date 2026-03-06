// ApolloProvider.tsx
import React, { useMemo } from 'react';
import { ApolloProvider as Provider } from '@apollo/client';
import { makeApolloClient } from './lib/apolloFactory';
import { makeMockApolloClient } from './lib/mockApolloClient';
import JWTAuthService from './features/auth/services/JWTAuthService';
import logger from './utils/logger';

const IS_DEMO = process.env.EXPO_PUBLIC_DEMO_MODE === 'true';

// Quick health check probe — skipped in demo mode
if (!IS_DEMO) {
  (async () => {
    try {
      const baseUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
      if (baseUrl) {
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
}

export default function ApolloProvider({ children }: { children: React.ReactNode }) {
  const client = useMemo(() => {
    if (IS_DEMO) {
      logger.log('[ApolloProvider] 🎭 DEMO MODE — using mock Apollo client');
      return makeMockApolloClient();
    }
    logger.log('[ApolloProvider] Creating Apollo client...');
    const apolloClient = makeApolloClient();
    JWTAuthService.getInstance().setApolloClient(apolloClient);
    logger.log('[ApolloProvider] Apollo client created successfully');
    return apolloClient;
  }, []);

  if (__DEV__) {
    if (IS_DEMO) {
      logger.log('🎭 DEMO MODE ACTIVE — all network calls mocked');
    } else {
      logger.log('🔌 GRAPHQL_URL:', process.env.EXPO_PUBLIC_GRAPHQL_URL);
    }
  }

  return <Provider client={client}>{children}</Provider>;
}

export const getApolloClient = () => {
  return IS_DEMO ? makeMockApolloClient() : makeApolloClient();
};
