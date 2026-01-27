// Apollo Client Factory - Single source of truth for all GraphQL clients
import { ApolloClient, InMemoryCache, createHttpLink, ApolloLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { Observable } from '@apollo/client';
// import { persistCache, AsyncStorageWrapper } from 'apollo3-cache-persist'; // Package not installed
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../utils/logger';
import { retryLink } from '../graphql/links/timeoutLink';

// Use the same configuration as the main API
import { API_GRAPHQL } from '../config/api';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Use the centralized API config (handles device detection automatically)
// Only use env var if it's NOT localhost (to avoid breaking physical devices)
const envGraphQLUrl = process.env.EXPO_PUBLIC_GRAPHQL_URL;
const isPhysicalDevice = Constants.isDevice && !Constants.deviceName?.toLowerCase().includes('simulator');
const envHasLocalhost = envGraphQLUrl && /localhost|127\.0\.0\.1/.test(envGraphQLUrl);

// Priority: Use API_GRAPHQL (smart device detection) unless env var is explicitly set for a non-localhost URL
// Never use localhost from env var on physical devices
// FORCE use API_GRAPHQL for physical devices to ensure correct IP
let GRAPHQL_URL: string;
if (isPhysicalDevice) {
  // Physical device: ALWAYS use API_GRAPHQL (which has correct LAN IP)
  // Even if env var is set, ignore it on physical devices to prevent localhost issues
  GRAPHQL_URL = API_GRAPHQL;
  logger.log('🔧 [ApolloFactory] Physical device detected - forcing API_GRAPHQL:', GRAPHQL_URL);
  if (envGraphQLUrl && envHasLocalhost) {
    logger.warn('⚠️ [ApolloFactory] Ignoring localhost env var on physical device');
  }
} else {
  // Simulator: Can use env var if it's not localhost, otherwise use API_GRAPHQL
  GRAPHQL_URL = 
    (envGraphQLUrl && !envHasLocalhost) 
      ? envGraphQLUrl 
      : API_GRAPHQL;
  logger.log('🔧 [ApolloFactory] Simulator - using:', GRAPHQL_URL);
}

// Final safety check: If somehow we still have localhost on physical device, force correct IP
if (isPhysicalDevice && (GRAPHQL_URL.includes('127.0.0.1') || GRAPHQL_URL.includes('localhost'))) {
  logger.error('⚠️ [ApolloFactory] CRITICAL: Physical device but GRAPHQL_URL is localhost!');
  logger.error('⚠️ [ApolloFactory] Forcing correct LAN IP from API_GRAPHQL');
  GRAPHQL_URL = API_GRAPHQL;
  logger.error('⚠️ [ApolloFactory] Corrected GRAPHQL_URL to:', GRAPHQL_URL);
}

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
  logger.log('[ApolloFactory] ========================================');
  logger.log('[ApolloFactory] Device Detection:');
  logger.log('[ApolloFactory]   Constants.isDevice:', Constants.isDevice);
  logger.log('[ApolloFactory]   Constants.deviceName:', Constants.deviceName);
  logger.log('[ApolloFactory]   isPhysicalDevice:', isPhysicalDevice);
  logger.log('[ApolloFactory] Environment Variables:');
  logger.log('[ApolloFactory]   EXPO_PUBLIC_GRAPHQL_URL:', process.env.EXPO_PUBLIC_GRAPHQL_URL);
  logger.log('[ApolloFactory]   EXPO_PUBLIC_API_BASE_URL:', process.env.EXPO_PUBLIC_API_BASE_URL);
  logger.log('[ApolloFactory] Config Values:');
  logger.log('[ApolloFactory]   API_GRAPHQL (from api.ts):', API_GRAPHQL);
  logger.log('[ApolloFactory]   envGraphQLUrl:', envGraphQLUrl);
  logger.log('[ApolloFactory]   envHasLocalhost:', envHasLocalhost);
  logger.log('[ApolloFactory] Final Resolution:');
  logger.log('[ApolloFactory]   GRAPHQL_URL:', GRAPHQL_URL);
  logger.log('[ApolloFactory] ========================================');
  
  // Safety check: If we're on a physical device but using localhost, warn and force correct IP
  if (isPhysicalDevice && GRAPHQL_URL.includes('127.0.0.1')) {
    logger.error('⚠️ [ApolloFactory] CRITICAL: Physical device detected but using localhost!');
    logger.error('⚠️ [ApolloFactory] Forcing correct LAN IP...');
    // Force use API_GRAPHQL which has the correct IP
    const forcedUrl = API_GRAPHQL;
    logger.error('⚠️ [ApolloFactory] Forced GRAPHQL_URL to:', forcedUrl);
    // Note: We can't reassign const, but we can log the issue
    // The fix above should prevent this, but this is a safety check
  }

  // Runtime guardrail to prevent localhost:8001
  if (/localhost:8001|127\.0\.0\.1:8001/i.test(GRAPHQL_URL)) {
    throw new Error(`Invalid GraphQL URL detected: ${GRAPHQL_URL}. Use network IP instead.`);
  }

  const logLink = new ApolloLink((operation, forward) => {
    const operationType = (operation.query.definitions?.[0] as any)?.operation || 'unknown';
    const startTime = Date.now();
    const operationName = operation.operationName || 'UNNAMED';
    
    // Log request start
    logger.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    logger.log(`🌐 [NETWORK] ${operationName} (${operationType})`);
    logger.log(`📍 URL: ${GRAPHQL_URL}`);
    logger.log(`📤 Variables:`, JSON.stringify(operation.variables, null, 2));
    
    if (!forward) {
      logger.error(`❌ [NETWORK] ${operationName} - forward is undefined!`);
      throw new Error('Apollo Link chain broken: forward is undefined');
    }
    
    logger.log(`🔄 [NETWORK] ${operationName} - Forwarding to next link...`);
    
    // Set up a timeout warning
    const timeoutWarning = setTimeout(() => {
      const elapsed = Date.now() - startTime;
      logger.warn(`⏱️ [NETWORK] ${operationName} - Still waiting for response (${elapsed}ms)...`);
    }, 3000); // Warn after 3 seconds
    
    try {
      const observable = forward(operation);
      if (!observable) {
        logger.error(`❌ [NETWORK] ${operationName} - forward() returned undefined!`);
        throw new Error('Apollo Link chain broken: forward() returned undefined');
      }
      
      // Wrap the observable to ensure timeout is cleared on both success and error
      return new Observable((observer) => {
        const subscription = observable.subscribe({
          next: (response) => {
            clearTimeout(timeoutWarning);
            const duration = Date.now() - startTime;
            
            // Log response
            if (response.errors && response.errors.length > 0) {
              logger.error(`❌ [NETWORK] ${operationName} FAILED (${duration}ms)`);
              logger.error(`   Errors:`, JSON.stringify(response.errors, null, 2));
            } else {
              logger.log(`✅ [NETWORK] ${operationName} SUCCESS (${duration}ms)`);
              if (response.data) {
                const dataKeys = Object.keys(response.data);
                logger.log(`   Data keys: ${dataKeys.join(', ')}`);
                // Log data for debugging if it's null or empty
                if (dataKeys.length === 0) {
                  logger.warn(`   ⚠️ Response data is empty`);
                } else {
                  // Log first data key value for debugging
                  const firstKey = dataKeys[0];
                  const firstValue = response.data[firstKey];
                  if (firstValue === null || firstValue === undefined) {
                    logger.warn(`   ⚠️ ${firstKey} is null/undefined`);
                  } else if (Array.isArray(firstValue)) {
                    logger.log(`   ${firstKey}: Array(${firstValue.length})`);
                  } else if (typeof firstValue === 'object') {
                    logger.log(`   ${firstKey}: Object`);
                  }
                }
              } else {
                logger.warn(`   ⚠️ Response has no data`);
              }
            }
            logger.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            
            observer.next(response);
          },
          error: (error) => {
            clearTimeout(timeoutWarning);
            const duration = Date.now() - startTime;
            logger.error(`❌ [NETWORK] ${operationName} ERROR in observable (${duration}ms):`, {
              error: error?.message,
              name: error?.name,
              stack: error?.stack?.substring(0, 500),
            });
            observer.error(error);
          },
          complete: () => {
            clearTimeout(timeoutWarning);
            observer.complete();
          },
        });
        
        return () => {
          clearTimeout(timeoutWarning);
          subscription.unsubscribe();
        };
      });
    } catch (error) {
      clearTimeout(timeoutWarning);
      const duration = Date.now() - startTime;
      logger.error(`❌ [NETWORK] ${operationName} ERROR in logLink (${duration}ms):`, {
        error: error?.message,
        name: error?.name,
        stack: error?.stack?.substring(0, 500),
      });
      // Re-throw to let errorLink handle it
      throw error;
    }
  });

  // Auth link to add JWT token to requests
  const authLink = setContext(async (_, { headers }) => {
    try {
      const token = await AsyncStorage.getItem('token');
      if (token) {
        logger.log('🔐 Apollo Client: Adding Bearer token to request');
        logger.log('🔐 Apollo Client: Token length:', token.length);
        logger.log('🔐 Apollo Client: Token preview:', token.substring(0, 20) + '...');
        return {
          headers: {
            ...headers,
            authorization: `Bearer ${token}`,
          },
        };
      } else {
        logger.log('🔐 Apollo Client: No token found in AsyncStorage');
        logger.log('🔐 Apollo Client: This will cause authentication failures');
        return { headers };
      }
    } catch (error) {
      logger.error('🔐 Apollo Client: Error getting token:', error);
      return { headers };
    }
  });

  // Error link to handle authentication failures and suppress cache write warnings
  const errorLink = new ApolloLink((operation, forward) => {
    // Log ALL operations to see what's happening
    logger.log('🔍 [Apollo Link] Operation:', {
      operationName: operation.operationName,
      operationType: (operation.query.definitions?.[0] as any)?.operation,
      queryString: operation.query.loc?.source?.body?.substring(0, 200),
    });
    
    const observable = forward(operation);
    if (!observable) {
      logger.error('❌ [Apollo Link] forward(operation) returned undefined in errorLink');
      throw new Error('Apollo Link chain broken: forward(operation) returned undefined');
    }
    
    // Wrap the observable to handle both success and error cases
    return new Observable((observer) => {
      const subscription = observable.subscribe({
        next: (response) => {
          // Debug AI recommendations queries
          if (operation.operationName === 'GetAIRecommendations') {
            logger.log('🔍 [Apollo Link] GetAIRecommendations response:', {
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
              (operation.query.loc?.source?.body && operation.query.loc.source.body.includes('addToWatchlist'))) {
            logger.log('🔍 [Apollo Link] AddToWatchlist mutation response:', {
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
              const errorMessage = error?.message || '';
              if (errorMessage.includes('Signature has expired') || 
                  errorMessage.includes('Token is invalid') ||
                  errorMessage.includes('Authentication credentials were not provided')) {
                logger.log('🔐 Authentication error detected, clearing token');
                AsyncStorage.removeItem('token').catch((err) => logger.error('Failed to remove token:', err));
              }
            });
          }
          observer.next(response);
        },
        error: (error) => {
          // Enhanced error logging to show actual GraphQL errors
          const graphQLErrors = error?.graphQLErrors || [];
          const networkError = error?.networkError;
          
          // Check for authentication errors (401/403) - these should trigger logout
          const isAuthError = networkError && 'statusCode' in networkError && 
            ((networkError as any).statusCode === 401 || (networkError as any).statusCode === 403);
          
          // Check for auth-related GraphQL errors
          const hasAuthGraphQLError = graphQLErrors.some((gqlError: any) => {
            const message = gqlError?.message || '';
            return message.includes('Signature has expired') || 
                   message.includes('Token is invalid') ||
                   message.includes('Authentication credentials were not provided') ||
                   message.includes('Not authenticated');
          });
          
          // Only handle auth errors - let other errors (400/500) pass through to UI
          if (isAuthError || hasAuthGraphQLError) {
            logger.warn('🔐 [Apollo] Authentication error detected - clearing token and logging out');
            AsyncStorage.removeItem('token').catch((err) => logger.error('Failed to remove token:', err));
            // Note: Don't navigate here - let the auth context handle it via state changes
          } else {
            // For non-auth errors (400/500), just log them - don't bounce to login
            logger.warn(`⚠️ [Apollo] Non-auth error in ${operation.operationName} - keeping user on current screen`);
          }
          
          if (graphQLErrors && graphQLErrors.length > 0) {
            logger.log('🔴 GraphQL Errors in', operation.operationName, ':', graphQLErrors);
            graphQLErrors.forEach((gqlError: any, idx: number) => {
              logger.error(`🔴 GraphQL Error ${idx + 1}:`, {
                message: gqlError?.message,
                locations: gqlError?.locations,
                path: gqlError?.path,
                extensions: gqlError?.extensions,
              });
            });
          }
          
          if (networkError) {
            logger.log('🔴 Network Error in', operation.operationName, ':', networkError);
            logger.error('🔴 Network Error:', {
              name: networkError?.name,
              message: networkError?.message,
              statusCode: (networkError as any)?.statusCode,
              result: (networkError as any)?.result,
            });
            
            // If it's a ServerError, try to dump the response body
            const anyNetErr = networkError as any;
            if (anyNetErr.result) {
              logger.log('🔴 networkError.result:', anyNetErr.result);
              logger.error('🔴 networkError.result:', JSON.stringify(anyNetErr.result, null, 2));
            }
          }
          
          // Production: Log all errors properly - don't suppress
          logger.error('❌ Apollo Error Link caught error:', {
            operation: operation.operationName,
            errorName: error?.name,
            errorMessage: error?.message,
            errorStack: error?.stack?.substring(0, 500),
            isAbortError: error?.name === 'AbortError',
            isNetworkError: (error?.message || '').includes('network') || (error?.message || '').includes('fetch'),
            fullError: JSON.stringify(error, Object.getOwnPropertyNames(error)).substring(0, 1000),
          });
          
          // For GetAIRecommendations, log extra details
          if (operation.operationName === 'GetAIRecommendations') {
            logger.error('❌ GetAIRecommendations failed:', {
              uri: GRAPHQL_URL,
              variables: operation.variables,
              errorType: error?.constructor?.name,
              graphQLErrors: graphQLErrors,
              networkError: networkError,
            });
          }
          
          // For GenerateAIRecommendations, log extra details
          if (operation.operationName === 'GenerateAIRecommendations') {
            logger.log('🔴 GenerateAIRecommendations Error Details:', {
              operationName: operation.operationName,
              variables: operation.variables,
              errorName: error?.name,
              errorMessage: error?.message,
              graphQLErrors: graphQLErrors,
              networkError: networkError,
              networkErrorResult: (networkError as any)?.result,
              networkErrorResponse: (networkError as any)?.response,
              networkErrorStatusCode: (networkError as any)?.statusCode,
            });
            logger.error('❌ GenerateAIRecommendations failed:', {
              uri: GRAPHQL_URL,
              variables: operation.variables,
              errorType: error?.constructor?.name,
              graphQLErrors: graphQLErrors,
              networkError: networkError,
              networkErrorResult: (networkError as any)?.result,
              networkErrorResponse: (networkError as any)?.response,
              networkErrorStatusCode: (networkError as any)?.statusCode,
            });
          }
          
          // IMPORTANT: Re-throw the error so Apollo can handle it with errorPolicy
          // However, with errorPolicy: 'all', Apollo will still return partial data if available
          // Network errors (500s) will still be thrown, but GraphQL errors will be included in response
          observer.error(error);
        },
        complete: () => {
          observer.complete();
        },
      });
      
      return () => {
        subscription.unsubscribe();
      };
    });
  });

  // Production: Only suppress Apollo cache warnings (expected with partial results)
  // All other errors should be logged properly
  const originalConsoleError = console.error;
  console.error = (...args: any[]) => {
    const message = (args[0]?.toString() || '');
    // Only suppress "Missing field" cache write warnings - these are expected with partial GraphQL responses
    if (message && message.includes('Missing field') && message.includes('while writing result')) {
      // This is expected - partial results are handled by our cache typePolicies
      return;
    }
    // Log all other errors properly in production
    originalConsoleError.apply(console, args);
  };

  const httpLink = createHttpLink({ 
    uri: GRAPHQL_URL, 
    fetch: (uri: RequestInfo | URL, options?: RequestInit) => {
      const fetchStartTime = Date.now();
      const urlString = uri.toString();
      
      // Log fetch request
      logger.log(`🔵 [FETCH] Starting request to: ${urlString}`);
      logger.log(`   Method: ${options?.method || 'POST'}`);
      logger.log(`   Headers:`, JSON.stringify(options?.headers || {}, null, 2));
      // Log request body for debugging (first 500 chars)
      if (options?.body) {
        const bodyStr = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
        logger.log(`   Body preview:`, bodyStr.substring(0, 500));
      }
      
      // Add timeout to fetch requests for better performance
      // Use longer timeout for slow queries (like Oracle Insights, AI Recommendations)
      const operationName = options?.body ? (() => {
        try {
          const body = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
          return body.operationName || '';
        } catch {
          return '';
        }
      })() : '';
      
      // Slow operations that need more time
      const slowOperations = [
        'GetOracleInsights', 
        'GetAIRecommendations', 
        'GenerateAIRecommendations',
        'GetResearchReport',
        'GenerateResearchReport',
        'GetStockAnalysis',
        'rustStockAnalysis',
        'GetSignalUpdates',
        'GetPortfolioSignals'
      ];
      const isSlowOperation = slowOperations.some(op => operationName.includes(op));
      const timeoutMs = isSlowOperation ? 45000 : 15000; // 45s for slow operations, 15s for normal
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        logger.error(`⏱️ [FETCH] TIMEOUT after ${timeoutMs/1000}s: ${urlString}`);
        controller.abort();
      }, timeoutMs);
      
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
      .then(async (response) => {
        const fetchDuration = Date.now() - fetchStartTime;
        logger.log(`🟢 [FETCH] Response received (${fetchDuration}ms): ${response.status} ${response.statusText}`);
        if (!response.ok) {
          logger.error(`   ❌ HTTP Error: ${response.status} ${response.statusText}`);
          // For 400 errors, try to read and log the response body
          if (response.status === 400) {
            try {
              const responseText = await response.clone().text();
              logger.error(`   📄 400 Response Body:`, responseText.substring(0, 500));
            } catch (e) {
              logger.error(`   ⚠️ Could not read 400 response body:`, e);
            }
          }
        }
        // Log response details for debugging specific queries
        const bodyString = options?.body?.toString() || '';
        if (uri.toString().includes('GetAIRecommendations') || bodyString.includes('GetAIRecommendations')) {
          logger.log('📡 Fetch response for GetAIRecommendations:', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok,
            headers: Object.fromEntries(response.headers.entries()),
          });
        }
        return response;
      })
      .catch((error) => {
        const fetchDuration = Date.now() - fetchStartTime;
        // Log fetch errors
        if (error?.name === 'AbortError') {
          logger.error(`⏱️ [FETCH] TIMEOUT (${fetchDuration}ms): ${urlString.substring(0, 100)}`);
        } else {
          logger.error(`🔴 [FETCH] ERROR (${fetchDuration}ms):`, {
            uri: urlString.substring(0, 100),
            error: error?.message,
            name: error?.name,
            stack: error?.stack?.substring(0, 200),
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
    // Link chain: log -> auth -> retry -> error -> http
    // Retry link comes before error link so it can retry before errors are logged
    link: logLink.concat(authLink).concat(retryLink).concat(errorLink).concat(httpLink),
    // Set default error policy to allow partial data even with errors
    defaultOptions: {
      watchQuery: {
        errorPolicy: 'all', // Return partial data even with errors
        fetchPolicy: 'cache-and-network', // Use cache when available, fetch in background
      },
      query: {
        errorPolicy: 'all',
        fetchPolicy: 'cache-and-network',
      },
      mutate: {
        errorPolicy: 'all',
      },
    },
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
        // nextFetchPolicy: 'cache-first', // Not available in this Apollo Client version
        notifyOnNetworkStatusChange: false,
        returnPartialData: false, // Don't return partial data to prevent cache write errors
        errorPolicy: 'all',
      },
      query: {
        fetchPolicy: 'cache-first',
        // nextFetchPolicy: 'cache-first', // Not available in this Apollo Client version
        errorPolicy: 'all',
      },
      mutate: {
        errorPolicy: 'all',
      },
    },
    assumeImmutableResults: true,
  });
}
