/**
 * Example: Using Generated GraphQL Types
 * 
 * This file demonstrates how to use the auto-generated TypeScript types
 * from your GraphQL schema.
 */

import type {
  UserType,
  BrokerOrderType,  // Order-related type (OrderType might be named differently)
  PortfolioType,
  AiRecommendationType,
  Scalars,
} from '../generated/graphql';

// Example 1: Typing a user object
const exampleUser: UserType = {
  __typename: 'UserType',
  id: '1',
  name: 'Example User',
  email: 'user@example.com',
  // TypeScript will autocomplete all available fields
  // and catch any typos or missing required fields
};

// Example 2: Typing a function parameter
function processOrder(order: BrokerOrderType): void {
  // TypeScript knows all available fields on BrokerOrderType
  console.log(`Processing order ${order.id}`);
  console.log(`Status: ${order.status}`);
  // TypeScript will error if you try to access non-existent fields
}

// Example 3: Typing API response
interface GetUserResponse {
  user: UserType;
}

interface GetPortfolioResponse {
  portfolio: PortfolioType;
}

// Example 4: Using with Apollo Client queries
import { useQuery, gql } from '@apollo/client';

const GET_USER = gql`
  query GetUser($id: ID!) {
    user(id: $id) {
      id
      email
      name
      hasPremiumAccess
    }
  }
`;

// Now you can type the query result
// Note: This example uses JSX, so it should be in a .tsx file
// For .ts files, you would use React.createElement or return plain objects
function UserComponent({ userId }: { userId: string }) {
  const { data, loading, error } = useQuery<{ user: UserType }>(GET_USER, {
    variables: { id: userId },
  });

  // In a .tsx file, you could return JSX like this:
  // if (loading) return <div>Loading...</div>;
  // if (error) return <div>Error: {error.message}</div>;
  // if (!data?.user) return <div>No user found</div>;
  // return (
  //   <div>
  //     <h1>{data.user.email}</h1>
  //     {data.user.hasPremiumAccess && <p>Premium User</p>}
  //   </div>
  // );

  // For .ts files, return data structure instead:
  if (loading) return { status: 'loading' };
  if (error) return { status: 'error', message: error.message };
  if (!data?.user) return { status: 'not_found' };
  
  return {
    status: 'success',
    user: data.user,
    email: data.user.email,
    hasPremium: data.user.hasPremiumAccess,
  };
}

// Example 5: Using Scalars for custom types
function formatDateTime(dateTime: Scalars['DateTime']['output']): string {
  return new Date(dateTime).toLocaleString();
}

// Example 6: Typing AI recommendations
function displayRecommendation(rec: AiRecommendationType): string {
  return `
    Symbol: ${rec.symbol}
    Recommendation: ${rec.recommendation}
    Confidence: ${rec.confidence}%
    Target Price: $${rec.targetPrice}
  `;
}

export {
  exampleUser,
  processOrder,
  UserComponent,
  formatDateTime,
  displayRecommendation,
};

