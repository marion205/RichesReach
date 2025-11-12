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

// Export API base URL getter for compatibility
export function getApiBase(): string {
  return GRAPHQL_URL.replace('/graphql/', '');
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
    }).catch((error) => {
      // Production: Log all errors properly - don't suppress
      console.error('❌ Apollo Error Link caught error:', {
        operation: operation.operationName,
        errorName: error?.name,
        errorMessage: error?.message,
        errorStack: error?.stack?.substring(0, 500),
        isAbortError: error?.name === 'AbortError',
        isNetworkError: error?.message?.includes('network') || error?.message?.includes('fetch'),
        fullError: JSON.stringify(error, Object.getOwnPropertyNames(error)).substring(0, 1000),
      });
      
      // For GetAIRecommendations, log extra details
      if (operation.operationName === 'GetAIRecommendations') {
        console.error('❌ GetAIRecommendations failed:', {
          uri: GRAPHQL_URL,
          variables: operation.variables,
          errorType: error?.constructor?.name,
        });
      }
      
      console.error('❌ Apollo Error:', {
        operation: operation.operationName,
        error: error?.message,
        networkError: error?.networkError,
        graphQLErrors: error?.graphQLErrors,
      });
      // Re-throw to let error handling components handle it
      throw error;
    });
  });

  // Production: Only suppress Apollo cache warnings (expected with partial results)
  // All other errors should be logged properly
  const originalConsoleError = console.error;
  console.error = (...args: any[]) => {
    const message = args[0]?.toString() || '';
    // Only suppress "Missing field" cache write warnings - these are expected with partial GraphQL responses
    if (message.includes('Missing field') && message.includes('while writing result')) {
      // This is expected - partial results are handled by our cache typePolicies
      return;
    }
    // Log all other errors properly in production
    originalConsoleError.apply(console, args);
  };

  const httpLink = createHttpLink({ 
    uri: GRAPHQL_URL, 
    fetch: (uri: RequestInfo | URL, options?: RequestInit) => {
      // Add timeout to fetch requests for better performance
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, 10000); // 10 second timeout
      
      // Chain existing signal if present
      if (options?.signal) {
        options.signal.addEventListener('abort', () => {
          controller.abort();
          clearTimeout(timeoutId);
        });
      }
      
      return fetch(uri, {
        ...options,
        signal: controller.signal,
      })
      .then((response) => {
        // Log response details for debugging
        if (uri.toString().includes('GetAIRecommendations') || options?.body?.toString().includes('GetAIRecommendations')) {
          console.log('📡 Fetch response for GetAIRecommendations:', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok,
            headers: Object.fromEntries(response.headers.entries()),
          });
        }
        return response;
      })
      .catch((error) => {
        // Log fetch errors
        if (error?.name === 'AbortError') {
          console.error('⏱️ Fetch timeout for:', uri.toString().substring(0, 100));
        } else {
          console.error('🌐 Fetch error:', {
            uri: uri.toString().substring(0, 100),
            error: error?.message,
            name: error?.name,
          });
        }
        throw error;
      })
      .finally(() => {
        clearTimeout(timeoutId);
      });
    },
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
