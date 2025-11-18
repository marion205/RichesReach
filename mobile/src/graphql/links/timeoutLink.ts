/**
 * Apollo Timeout Link
 * Adds timeout functionality to GraphQL operations
 */

import { ApolloLink, Observable, Operation, NextLink } from '@apollo/client';
import { GRAPHQL_TIMEOUT_MS } from '../../config/flags';
import logger from '../../utils/logger';

export const timeoutLink = (ms: number = GRAPHQL_TIMEOUT_MS) =>
  new ApolloLink((operation: Operation, forward: NextLink) =>
    new Observable(observer => {
      const timer = setTimeout(() => {
        observer.error(new Error(`GraphQL operation timed out after ${ms}ms`));
      }, ms);
      
      const subscription = forward(operation).subscribe({
        next: (value) => {
          clearTimeout(timer);
          observer.next(value);
        },
        error: (error) => {
          clearTimeout(timer);
          observer.error(error);
        },
        complete: () => {
          clearTimeout(timer);
          observer.complete();
        },
      });
      
      return () => {
        clearTimeout(timer);
        subscription.unsubscribe();
      };
    })
  );

/**
 * Retry link for failed operations
 */
export const retryLink = new ApolloLink((operation, forward) =>
  new Observable(observer => {
    let retryCount = 0;
    const maxRetries = 2;
    
    const attempt = () => {
      const subscription = forward(operation).subscribe({
        next: (value) => observer.next(value),
        error: (error) => {
          if (retryCount < maxRetries && shouldRetry(error)) {
            retryCount++;
            logger.log(`Retrying GraphQL operation (attempt ${retryCount}/${maxRetries})`);
            setTimeout(attempt, 1000 * retryCount); // Exponential backoff
          } else {
            observer.error(error);
          }
        },
        complete: () => observer.complete(),
      });
      
      return subscription;
    };
    
    return attempt();
  })
);

/**
 * Determine if an error should trigger a retry
 */
function shouldRetry(error: any): boolean {
  // Retry on network errors, timeouts, and 5xx server errors
  if (error.message?.includes('timeout')) return true;
  if (error.message?.includes('Network request failed')) return true;
  if (error.networkError?.statusCode >= 500) return true;
  if (error.networkError?.statusCode === 429) return true; // Rate limit
  
  return false;
}

/**
 * Error handling link
 */
export const errorHandlingLink = new ApolloLink((operation, forward) =>
  new Observable(observer => {
    const subscription = forward(operation).subscribe({
      next: (value) => observer.next(value),
      error: (error) => {
        // Log errors
        logger.error('GraphQL Error:', {
          operation: operation.operationName,
          variables: operation.variables,
          error: error.message,
        });
        
        // Handle specific error types
        if (error.message?.includes('timeout')) {
          logger.warn('GraphQL operation timed out, using cached data if available');
        }
        
        observer.error(error);
      },
      complete: () => observer.complete(),
    });
    
    return subscription;
  })
);
