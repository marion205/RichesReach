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
 * Intelligently retries queries but not mutations (unless idempotent)
 */
export const retryLink = new ApolloLink((operation, forward) => {
  // Check if this is a mutation
  const isMutation = operation.query.definitions.some(
    (def: any) => def.kind === 'OperationDefinition' && def.operation === 'mutation'
  );
  
  // Check if operation has retry disabled in context
  const retryDisabled = operation.getContext().skipRetry === true;
  
  // Don't retry mutations by default (unless explicitly enabled)
  if (isMutation && !operation.getContext().retryMutation) {
    return forward(operation);
  }
  
  // Don't retry if explicitly disabled
  if (retryDisabled) {
    return forward(operation);
  }
  
  return new Observable(observer => {
    let retryCount = 0;
    const maxRetries = operation.getContext().maxRetries || 2;
    
    const attempt = () => {
      const subscription = forward(operation).subscribe({
        next: (value) => {
          // Reset retry count on success
          retryCount = 0;
          observer.next(value);
        },
        error: (error) => {
          if (retryCount < maxRetries && shouldRetry(error, operation)) {
            retryCount++;
            const delay = calculateRetryDelay(retryCount);
            
            logger.log(`🔄 Retrying GraphQL operation ${operation.operationName} (attempt ${retryCount}/${maxRetries}) after ${delay}ms`);
            
            setTimeout(() => {
              attempt();
            }, delay);
          } else {
            if (retryCount >= maxRetries) {
              logger.warn(`❌ Max retries (${maxRetries}) reached for ${operation.operationName}`);
            }
            observer.error(error);
          }
        },
        complete: () => observer.complete(),
      });
      
      return subscription;
    };
    
    return attempt();
  });
});

/**
 * Calculate exponential backoff delay with jitter
 */
function calculateRetryDelay(attempt: number, baseDelay: number = 300): number {
  // Exponential backoff: 300ms, 600ms, 1200ms, etc.
  const exponentialDelay = baseDelay * Math.pow(2, attempt - 1);
  
  // Add jitter (±20%) to prevent thundering herd
  const jitter = exponentialDelay * 0.2 * (Math.random() * 2 - 1);
  
  // Cap at 5 seconds
  return Math.min(exponentialDelay + jitter, 5000);
}

/**
 * Determine if an error should trigger a retry
 */
function shouldRetry(error: any, operation: Operation): boolean {
  // Don't retry auth errors (401/403) - these need user action
  const networkError = error?.networkError;
  if (networkError && 'statusCode' in networkError) {
    const statusCode = (networkError as any).statusCode;
    if (statusCode === 401 || statusCode === 403) {
      return false;
    }
  }
  
  // Don't retry client errors (4xx except 429)
  if (networkError && 'statusCode' in networkError) {
    const statusCode = (networkError as any).statusCode;
    if (statusCode >= 400 && statusCode < 500 && statusCode !== 429) {
      return false;
    }
  }
  
  // Retry on server errors (5xx)
  if (networkError?.statusCode >= 500) {
    return true;
  }
  
  // Retry on rate limits (429)
  if (networkError?.statusCode === 429) {
    return true;
  }
  
  // Retry on network failures
  if (error?.message?.includes('timeout')) return true;
  if (error?.message?.includes('Network request failed')) return true;
  if (error?.message?.includes('Failed to fetch')) return true;
  if (error?.name === 'NetworkError') return true;
  
  // Don't retry GraphQL errors (these are usually business logic errors)
  if (error?.graphQLErrors && error.graphQLErrors.length > 0) {
    return false;
  }
  
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
