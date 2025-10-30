// Apollo Client Factory - Single source of truth for all GraphQL clients
import { ApolloClient, InMemoryCache, createHttpLink, ApolloLink } from '@apollo/client';
import { persistCache, AsyncStorageWrapper } from 'apollo3-cache-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Use the same configuration as the main API
import { API_GRAPHQL } from '../config/api';
const GRAPHQL_URL = API_GRAPHQL;

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
  console.log('[GQL URL]', `${GRAPHQL_URL}`);

  // Runtime guardrail to prevent localhost:8001
  if (/localhost:8001|127\.0\.0\.1:8001/i.test(GRAPHQL_URL)) {
    throw new Error(`Invalid GraphQL URL detected: ${GRAPHQL_URL}. Use network IP instead.`);
  }

  const logLink = new ApolloLink((operation, forward) => {
    const operationType = operation.query.definitions?.[0]?.operation || 'unknown';
    console.log('[GQL]', operation.operationName || 'UNNAMED', `(${operationType})`, '->', GRAPHQL_URL);
    if (operation.operationName === 'AddToWatchlist' || operation.query.loc?.source?.body?.includes('addToWatchlist')) {
      console.log('[GQL] AddToWatchlist mutation detected! Variables:', JSON.stringify(operation.variables, null, 2));
    }
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

  // Error link to handle authentication failures and suppress cache write warnings
  const errorLink = new ApolloLink((operation, forward) => {
    // Log ALL operations to see what's happening
    console.log('🔍 [Apollo Link] Operation:', {
      operationName: operation.operationName,
      operationType: operation.query.definitions?.[0]?.operation,
      queryString: operation.query.loc?.source?.body?.substring(0, 200),
    });
    
    return forward(operation).map((response) => {
      // Debug AI recommendations queries
      if (operation.operationName === 'GetAIRecommendations') {
        console.log('🔍 [Apollo Link] GetAIRecommendations response:', {
          hasData: !!response.data,
          hasAiRecommendations: !!response.data?.aiRecommendations,
          aiRecommendationsKeys: response.data?.aiRecommendations ? Object.keys(response.data.aiRecommendations) : [],
          buyRecsCount: response.data?.aiRecommendations?.buyRecommendations?.length ?? 0,
          portfolioValue: response.data?.aiRecommendations?.portfolioAnalysis?.totalValue,
          rawResponse: JSON.stringify(response.data).substring(0, 800),
        });
      }
      
      // Debug: Log mutation responses to see what we're getting
      if (operation.operationName === 'AddToWatchlist' || 
          (operation.query.loc?.source?.body?.includes('addToWatchlist'))) {
        console.log('🔍 [Apollo Link] AddToWatchlist mutation response:', {
          operationName: operation.operationName,
          responseData: response.data,
          responseErrors: response.errors,
          dataKeys: response.data ? Object.keys(response.data) : [],
          fullResponse: JSON.stringify(response, null, 2).substring(0, 500),
        });
      }
      
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

  // Suppress Apollo cache write warnings for missing fields
  // This happens when GraphQL queries return partial results
  const originalConsoleError = console.error;
  console.error = (...args: any[]) => {
    const message = args[0]?.toString() || '';
    // Suppress "Missing field" cache write warnings - these are expected with partial GraphQL responses
    if (message.includes('Missing field') && message.includes('while writing result')) {
      // Silently ignore - partial results are handled by our cache typePolicies
      return;
    }
    originalConsoleError.apply(console, args);
  };

  const httpLink = createHttpLink({ 
    uri: GRAPHQL_URL, 
    fetch,
    credentials: "omit"
  });

  return new ApolloClient({
    link: logLink.concat(authLink).concat(errorLink).concat(httpLink),
    cache: new InMemoryCache({
      // Prevent Apollo from complaining about missing fields in partial results
      possibleTypes: {},
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
            // Handle benchmark queries - allow null/empty to prevent cache write errors
            benchmarkSeries: {
              merge(existing, incoming) {
                // Only write if incoming is not null/undefined
                if (incoming !== null && incoming !== undefined) {
                  return incoming;
                }
                return existing ?? null;
              },
              // Allow reading undefined to prevent cache write errors
              read(existing) {
                return existing ?? undefined;
              }
            },
            availableBenchmarks: {
              merge(existing, incoming) {
                // Return incoming if it's valid, otherwise keep existing or default
                if (Array.isArray(incoming) && incoming.length > 0) return incoming;
                if (Array.isArray(existing) && existing.length > 0) return existing;
                return undefined; // Return undefined instead of default to prevent cache write
              },
              read(existing) {
                return existing ?? undefined;
              }
            },
            cryptoPortfolio: {
              merge(existing, incoming) {
                if (incoming !== null && incoming !== undefined) {
                  return incoming;
                }
                return existing ?? undefined;
              },
              read(existing) {
                return existing ?? undefined;
              }
            },
            cryptoAnalytics: {
              merge(existing, incoming) {
                if (incoming !== null && incoming !== undefined) {
                  return incoming;
                }
                return existing ?? undefined;
              },
              read(existing) {
                return existing ?? undefined;
              }
            },
            cryptoPrice: {
              merge(existing, incoming) {
                if (incoming !== null && incoming !== undefined) {
                  return incoming;
                }
                return existing ?? undefined;
              },
              read(existing) {
                return existing ?? undefined;
              }
            },
            aiRecommendations: {
              merge(existing, incoming) {
                // Always use incoming data for AI recommendations
                if (incoming !== null && incoming !== undefined) {
                  return incoming;
                }
                return existing ?? undefined;
              },
              read(existing) {
                return existing ?? undefined;
              }
            },
            supportedCurrencies: {
              keyArgs: false,
              merge(existing = [], incoming: any[]) {
                return Array.isArray(incoming) && incoming.length > 0 ? incoming : existing;
              },
              read(existing) {
                return existing ?? undefined;
              }
            },
            cryptoMlSignal: {
              merge(existing, incoming) {
                if (incoming !== null && incoming !== undefined) {
                  return incoming;
                }
                return existing ?? undefined;
              },
              read(existing) {
                return existing ?? undefined;
              }
            },
            topYields: {
              keyArgs: false,
              merge(existing = [], incoming: any[]) { 
                return Array.isArray(incoming) && incoming.length > 0 ? incoming : existing; 
              },
              read(existing) {
                return existing ?? undefined;
              }
            },
            aiYieldOptimizer: {
              merge(existing, incoming) {
                if (incoming !== null && incoming !== undefined) {
                  return incoming;
                }
                return existing ?? undefined;
              },
              read(existing) {
                return existing ?? undefined;
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
        returnPartialData: false, // Don't return partial data to prevent cache write errors
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
