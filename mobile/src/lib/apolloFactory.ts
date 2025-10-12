// Apollo Client Factory - Single source of truth for all GraphQL clients
import { ApolloClient, InMemoryCache, HttpLink, ApolloLink } from '@apollo/client';

export const getApiBase = () => {
  const base = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (!base) {
    throw new Error('EXPO_PUBLIC_API_BASE_URL is required in Expo Go');
  }
  return base.replace(/\/+$/, ''); // Remove trailing slashes
};

export function makeApolloClient() {
  const base = getApiBase();
  const httpUri = `${base}/graphql`;

  console.log('[ApolloFactory] Creating client with base:', base);
  console.log('[ApolloFactory] GraphQL URI:', httpUri);

  const logLink = new ApolloLink((operation, forward) => {
    console.log('[GQL]', operation.operationName, '->', httpUri);
    return forward!(operation);
  });

  const httpLink = new HttpLink({ 
    uri: httpUri, 
    fetch,
    credentials: "omit"
  });

  return new ApolloClient({
    link: logLink.concat(httpLink),
    cache: new InMemoryCache({
      typePolicies: {
        Query: {
          fields: {
            me: {
              merge: true,
            },
          },
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
        errorPolicy: 'all',
        fetchPolicy: 'cache-and-network',
      },
      query: {
        errorPolicy: 'all',
        fetchPolicy: 'network-only',
      },
      mutate: {
        errorPolicy: 'all',
      },
    },
    assumeImmutableResults: true,
  });
}
