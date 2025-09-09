// ApolloProvider.tsx
import React from 'react';
import { ApolloClient, InMemoryCache, ApolloProvider as Provider, createHttpLink, split } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getMainDefinition } from '@apollo/client/utilities';
// If you’ll add subscriptions later:
// import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
// import { createClient } from 'graphql-ws';

const HTTP_URL = 'http://localhost:8001/graphql/'; 
// Local development → use localhost
// iOS Simulator → use localhost (should work with Expo Go)
// Android Emulator → use http://10.0.2.2:8001/graphql/

const httpLink = createHttpLink({ uri: HTTP_URL });

const authLink = setContext(async (_, { headers }) => {
  try {
    const token = await AsyncStorage.getItem('token');
    // Only log in development mode to reduce overhead
    if (__DEV__) {
      console.log('🔐 Auth Debug - Token from storage:', token ? `${token.substring(0, 20)}...` : 'No token');
    }
    return {
      headers: {
        ...headers,
        ...(token ? { Authorization: `JWT ${token}` } : {}),
      },
    };
  } catch (error) {
    console.error('Error getting token from storage:', error);
    return { headers };
  }
});

// (optional) subscriptions—leave commented out if not using yet
// const wsLink = new GraphQLWsLink(createClient({
//   url: HTTP_URL.replace('http', 'ws'),
//   connectionParams: async () => {
//     const token = await AsyncStorage.getItem('token');
//     return token ? { headers: { Authorization: `Bearer ${token}` } } : {};
//   },
// }));

// const link = split(
//   ({ query }) => {
//     const def = getMainDefinition(query);
//    return def.kind === 'OperationDefinition' && def.operation === 'subscription';
//   },
//   wsLink,
//   authLink.concat(httpLink)
// );

const client = new ApolloClient({
  link: authLink.concat(httpLink), // swap for `link` if you enable ws
  cache: new InMemoryCache({
    // Optimize cache for better performance
    typePolicies: {
      Query: {
        fields: {
          // Cache user queries for better performance
          me: {
            merge: true,
          },
        },
      },
    },
  }),
  // Add default options for better performance
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
      fetchPolicy: 'cache-and-network',
    },
    query: {
      errorPolicy: 'all',
      fetchPolicy: 'cache-first',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
});

export { client };

export default function ApolloWrapper({ children }: { children: React.ReactNode }) {
  return <Provider client={client}>{children}</Provider>;
}