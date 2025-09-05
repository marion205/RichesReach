// ApolloProvider.tsx
import React from 'react';
import { ApolloClient, InMemoryCache, ApolloProvider as Provider, createHttpLink, split } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getMainDefinition } from '@apollo/client/utilities';
// If you’ll add subscriptions later:
// import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
// import { createClient } from 'graphql-ws';

const HTTP_URL = 'http://192.168.1.151:8000/graphql/'; 
// Local development → use localhost
// iOS Simulator → use actual network IP (e.g., http://192.168.1.151:8000/graphql/)
// Android Emulator → use http://10.0.2.2:8000/graphql/

const httpLink = createHttpLink({ uri: HTTP_URL });

const authLink = setContext(async (_, { headers }) => {
  const token = await AsyncStorage.getItem('token');
  console.log('🔐 Auth Debug - Token from storage:', token ? `${token.substring(0, 20)}...` : 'No token');
  return {
    headers: {
      ...headers,
      ...(token ? { Authorization: `JWT ${token}` } : {}),
    },
  };
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
  cache: new InMemoryCache(),
});

export { client };

export default function ApolloWrapper({ children }: { children: React.ReactNode }) {
  return <Provider client={client}>{children}</Provider>;
}