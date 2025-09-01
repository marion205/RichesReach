// ApolloProvider.tsx
import React from 'react';
import { ApolloClient, InMemoryCache, ApolloProvider as Provider, createHttpLink, from } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// Create HTTP link
const httpLink = createHttpLink({
  uri: Platform.OS === 'android' 
    ? 'http://10.0.2.2:8000/graphql/' // Android emulator
    : 'http://localhost:8000/graphql/', // iOS simulator or web - use localhost
});

// Auth link to add JWT token to headers
const authLink = setContext(async (_, { headers }) => {
  try {
    const token = await AsyncStorage.getItem('token');
            // Token retrieved from storage
    
    const newHeaders = {
      ...headers,
      authorization: token ? `JWT ${token}` : '',
    };
    
            // Headers updated with token
    return { headers: newHeaders };
  } catch (error) {
            // Error getting token from storage
    return {
      headers: {
        ...headers,
      }
    };
  }
});

// Error handling link
const errorLink = onError(({ graphQLErrors, networkError, operation, forward }) => {
          // GraphQL operation details
  
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, locations, path }) => {
      console.error(
        `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
      );
    });
  }
  if (networkError) {
    console.error(`[Network error]: ${networkError}`);
    console.error(`[Network error details]:`, networkError);
  }
});

const client = new ApolloClient({
  link: from([errorLink, authLink, httpLink]),
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          wallPosts: {
            merge: false,
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
    },
    query: {
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
});

export default function ApolloWrapper({ children }: { children: React.ReactNode }) {
  return <Provider client={client}>{children}</Provider>;
}