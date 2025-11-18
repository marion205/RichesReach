/**
 * Retry utility for network requests
 * Provides exponential backoff and configurable retry logic
 */

export interface RetryOptions {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  retryableErrors?: (error: any) => boolean;
}

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxRetries: 3,
  initialDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffMultiplier: 2,
  retryableErrors: (error: any) => {
    // Retry on network errors, timeouts, and 5xx server errors
    if (error?.message?.includes('timeout')) return true;
    if (error?.message?.includes('Network request failed')) return true;
    if (error?.message?.includes('Failed to fetch')) return true;
    if (error?.networkError?.statusCode >= 500) return true;
    if (error?.networkError?.statusCode === 429) return true; // Rate limit
    if (error?.response?.status >= 500) return true;
    if (error?.response?.status === 429) return true;
    return false;
  },
};

/**
 * Calculate delay for retry attempt with exponential backoff
 */
function calculateDelay(attempt: number, options: Required<RetryOptions>): number {
  const delay = options.initialDelay * Math.pow(options.backoffMultiplier, attempt);
  return Math.min(delay, options.maxDelay);
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry a function with exponential backoff
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let lastError: any;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;

      // Don't retry if it's the last attempt or error is not retryable
      if (attempt === opts.maxRetries || !opts.retryableErrors(error)) {
        throw error;
      }

      // Calculate delay with exponential backoff
      const delay = calculateDelay(attempt, opts);
      
      // Special handling for rate limits (429)
      if (error?.networkError?.statusCode === 429 || error?.response?.status === 429) {
        const retryAfter = error?.response?.headers?.['retry-after'] 
          ? parseInt(error.response.headers['retry-after'], 10) * 1000
          : delay;
        await sleep(Math.min(retryAfter, opts.maxDelay));
      } else {
        await sleep(delay);
      }
    }
  }

  throw lastError;
}

/**
 * Retry a GraphQL query/mutation
 */
export async function retryGraphQLOperation<T>(
  operation: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  return withRetry(operation, {
    ...options,
    retryableErrors: (error: any) => {
      // GraphQL-specific retry logic
      if (error?.networkError) {
        const statusCode = error.networkError.statusCode;
        // Retry on 5xx errors and rate limits
        if (statusCode >= 500 || statusCode === 429) return true;
      }
      // Retry on network failures
      if (error?.message?.includes('Network request failed')) return true;
      if (error?.message?.includes('timeout')) return true;
      return false;
    },
  });
}

