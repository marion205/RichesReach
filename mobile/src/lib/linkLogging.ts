// Ultra-verbose logging for GraphQL requests
// Logs the exact URL, headers, and timing for debugging

import { ApolloLink } from "@apollo/client";

export const loggingLink = new ApolloLink((operation, forward) => {
  const started = Date.now();
  const operationName = operation.operationName || 'Unknown';
  const uri = operation.getContext().uri || 'No URI';
  
  console.log(`[GQL →] ${operationName} ${uri}`);
  
  return forward(operation).map((result) => {
    const duration = Date.now() - started;
    console.log(`[GQL ←] ${operationName} ${duration}ms`);
    
    if (result.errors) {
      console.log(`[GQL ERR] ${operationName}:`, result.errors);
    }
    
    return result;
  });
});
