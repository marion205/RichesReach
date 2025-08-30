// ApolloProvider.tsx
import React from 'react';
import { ApolloClient, InMemoryCache, ApolloProvider as Provider } from '@apollo/client';

const client = new ApolloClient({
  uri: 'http://localhost:8000/graphql/', // 🔁 change to your backend URL
  cache: new InMemoryCache(),
});

export default function ApolloWrapper({ children }: { children: React.ReactNode }) {
  return <Provider client={client}>{children}</Provider>;
}