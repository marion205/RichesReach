// Apollo Client Factory - Single source of truth for all GraphQL clients
import { ApolloClient, InMemoryCache, createHttpLink, ApolloLink } from '@apollo/client';
import { persistCache, AsyncStorageWrapper } from 'apollo3-cache-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Force the correct IP address for local development
const GRAPHQL_URL = "http://localhost:8000/graphql/";

if (!GRAPHQL_URL) {
  throw new Error(
    'EXPO_PUBLIC_GRAPHQL_URL is not set. Start Expo with EXPO_PUBLIC_GRAPHQL_URL=http://<LAN_IP>:8000/graphql/'
  );
}

if (__DEV__ && /elb\.amazonaws\.com/i.test(GRAPHQL_URL)) {
  throw new Error('Dev build is pointing to PROD ALB. Fix EXPO_PUBLIC_GRAPHQL_URL.');
}

export function makeApolloClient() {
  console.log('[ApolloFactory] Environment EXPO_PUBLIC_GRAPHQL_URL:', process.env.EXPO_PUBLIC_GRAPHQL_URL);
  console.log('[ApolloFactory] FORCED GRAPHQL_URL (ignoring env):', GRAPHQL_URL);
  console.log('[ApolloFactory] Creating client with GraphQL URL:', GRAPHQL_URL);

  const logLink = new ApolloLink((operation, forward) => {
    console.log('[GQL]', operation.operationName, '->', GRAPHQL_URL);
    return forward!(operation);
  });

  // Auth link to add JWT token to requests
  const authLink = new ApolloLink((operation, forward) => {
    return new Promise((resolve, reject) => {
        AsyncStorage.getItem('token').then((token) => {
        if (token) {
          console.log('🔐 Apollo Client: Adding Bearer token to request');
          console.log('🔐 Apollo Client: Token length:', token.length);
          console.log('🔐 Apollo Client: Token preview:', token.substring(0, 20) + '...');
          operation.setContext({
            headers: {
              authorization: `Bearer ${token}`,
            },
          });
        } else {
          console.log('🔐 Apollo Client: No token found in AsyncStorage');
          console.log('🔐 Apollo Client: This will cause authentication failures');
        }
        resolve(forward!(operation));
      }).catch(reject);
    });
  });

  // Error link to handle authentication failures
  const errorLink = new ApolloLink((operation, forward) => {
    return forward(operation).map((response) => {
      // Check for authentication errors
      if (response.errors) {
        response.errors.forEach((error) => {
          if (error.message.includes('Signature has expired') || 
              error.message.includes('Token is invalid') ||
              error.message.includes('Authentication credentials were not provided')) {
            console.log('🔐 Authentication error detected, clearing token');
            AsyncStorage.removeItem('token').catch(console.error);
          }
        });
      }
      return response;
    });
  });

  const httpLink = createHttpLink({ 
    uri: GRAPHQL_URL, 
    fetch,
    credentials: "omit"
  });

  return new ApolloClient({
    link: logLink.concat(authLink).concat(errorLink).concat(httpLink),
    cache: new InMemoryCache({
      typePolicies: {
        Query: {
          fields: {
            me: {
              merge: true,
            },
            // Merge lists instead of replacing to avoid reload flashes
            markets: {
              keyArgs: false,
              merge(existing = [], incoming: any[]) { 
                return incoming ?? existing; 
              }
            },
            cryptoPortfolio: {
              merge(existing, incoming) {
                return incoming ?? existing;
              }
            },
            cryptoAnalytics: {
              merge(existing, incoming) {
                return incoming ?? existing;
              }
            },
            topYields: {
              keyArgs: false,
              merge(existing = [], incoming: any[]) { 
                return incoming ?? existing; 
              }
            },
            aiYieldOptimizer: {
              merge(existing, incoming) {
                return incoming ?? existing;
              }
            },
          },
        },
        // Normalize by type/field for efficiency
        User: {
          keyFields: ['id'],
        },
        Cryptocurrency: {
          keyFields: ['symbol'],
        },
        CryptoTrade: {
          keyFields: ['id'],
        },
        OptionsRecommendation: {
          fields: {
            sentimentDescription: {
              read(existing, { readField }) {
                if (existing) return existing;
                const raw = readField<string>('sentiment');
                if (!raw) return 'Neutral outlook';
                const upperRaw = raw.toUpperCase();
                const confidence = readField<number>('confidence');
                const map: Record<string, string> = {
                  BULLISH: 'Bullish — model expects upside',
                  BEARISH: 'Bearish — model expects downside',
                  NEUTRAL: 'Neutral — limited directional edge',
                };
                const base = map[upperRaw] || 'Unknown';
                return typeof confidence === 'number'
                  ? `${base} (confidence ${Math.round(confidence * 100)}%)`
                  : base;
              }
            },
            daysToExpiration: {
              read(existing) {
                return existing ?? 30;
              }
            }
          }
        },
        Option: {
          fields: {
            timeValue: {
              read(existing) {
                return existing ?? 0.0;
              }
            },
            intrinsicValue: {
              read(existing) {
                return existing ?? 0.0;
              }
            },
            daysToExpiration: {
              read(existing) {
                return existing ?? 30;
              }
            }
          }
        },
        RecommendedStrategy: {
          fields: {
            daysToExpiration: {
              read(existing) {
                return existing ?? 30;
              }
            },
            marketOutlook: {
              read(existing) {
                if (typeof existing === 'string') {
                  return {
                    sentiment: existing.toUpperCase(),
                    sentimentDescription: `Market outlook: ${existing}`
                  };
                }
                return existing ?? { sentiment: 'NEUTRAL', sentimentDescription: 'Neutral outlook' };
              }
            }
          }
        },
      },
    }),
    defaultOptions: {
      watchQuery: {
        fetchPolicy: 'cache-first',
        nextFetchPolicy: 'cache-first',
        notifyOnNetworkStatusChange: false,
        returnPartialData: true,
        errorPolicy: 'all',
      },
      query: {
        fetchPolicy: 'cache-first',
        nextFetchPolicy: 'cache-first',
        errorPolicy: 'all',
      },
      mutate: {
        errorPolicy: 'all',
      },
    },
    assumeImmutableResults: true,
  });
}
