// ApolloProvider.tsx
import React from 'react';
import { ApolloClient, InMemoryCache, ApolloProvider as Provider, createHttpLink, split } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getMainDefinition } from '@apollo/client/utilities';
import JWTAuthService from '../services/JWTAuthService';
// If you’ll add subscriptions later:
// import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
// import { createClient } from 'graphql-ws';
// Determine the correct URL based on the environment
const getGraphQLURL = () => {
  if (__DEV__) {
    // In development, try to detect if we're on a physical device
    // For now, use localhost - if this doesn't work, the user can manually change it
    return 'http://localhost:8000/graphql/';
  }
  // In production, use the production URL
  return 'https://your-production-url.com/graphql/';
};

const HTTP_URL = getGraphQLURL();


const httpLink = createHttpLink({ uri: HTTP_URL });

const authLink = setContext(async (_, { headers }) => {
try {
const jwtService = JWTAuthService.getInstance();
const token = await jwtService.getValidToken();
return {
headers: {
...headers,
...(token ? { Authorization: `JWT ${token}` } : {}),
},
};
} catch (error) {
console.error('Error getting token for request:', error);
return { headers };
}
});

// Error link to handle token expiration
const errorLink = onError(({ graphQLErrors, networkError, operation, forward }) => {
if (graphQLErrors) {
graphQLErrors.forEach(({ message, locations, path }) => {
console.error(`GraphQL error: Message: ${message}, Location: ${locations}, Path: ${path}`);
if (message.includes('Signature has expired') || message.includes('Token is invalid')) {
console.log('Token expired, attempting refresh...');
// Try to refresh the token
JWTAuthService.getInstance().refreshToken().then((newToken) => {
if (newToken) {
console.log('Token refreshed successfully');
// Retry the operation
return forward(operation);
} else {
console.log('Token refresh failed, user needs to login again');
// Clear the token and redirect to login
JWTAuthService.getInstance().logout();
}
});
}
});
}

if (networkError) {
console.error(`Network error: ${networkError}`);
}
});
// (optional) subscriptions—leave commented out if not using yet
// const wsLink = new GraphQLWsLink(createClient({
// url: HTTP_URL.replace('http', 'ws'),
// connectionParams: async () => {
// const token = await AsyncStorage.getItem('token');
// return token ? { headers: { Authorization: `Bearer ${token}` } } : {};
// },
// }));
// const link = split(
// ({ query }) => {
// const def = getMainDefinition(query);
// return def.kind === 'OperationDefinition' && def.operation === 'subscription';
// },
// wsLink,
// authLink.concat(httpLink)
// );
const client = new ApolloClient({
link: errorLink.concat(authLink).concat(httpLink), // Add error handling
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
fetchPolicy: 'network-only',
},
    query: {
      errorPolicy: 'all',
      fetchPolicy: 'network-only',
    },
mutate: {
errorPolicy: 'all',
},
},
});

// Initialize the JWT service with the Apollo client
JWTAuthService.getInstance().setApolloClient(client);

export { client };
export default function ApolloWrapper({ children }: { children: React.ReactNode }) {
return <Provider client={client}>{children}</Provider>;
}