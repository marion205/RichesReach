/**
 * Custom Batch Link for Apollo Client
 * 
 * Batches multiple GraphQL queries into a single HTTP request.
 * This reduces network overhead and improves performance.
 */

import { ApolloLink, Operation, FetchResult, Observable } from '@apollo/client';
import { print } from 'graphql';
import logger from '../utils/logger';

interface BatchRequest {
  operations: Operation[];
  resolve: (results: FetchResult[]) => void;
  reject: (error: Error) => void;
}

export class BatchHttpLink extends ApolloLink {
  private batchInterval: number;
  private batchMax: number;
  private uri: string;
  private fetch: typeof fetch;
  private credentials?: RequestCredentials;
  private batchQueue: BatchRequest[] = [];
  private batchTimer: NodeJS.Timeout | null = null;
  private batchEnabled: boolean = true; // Can be disabled if batching fails
  private consecutiveFailures: number = 0;
  private maxFailures: number = 3; // Disable batching after 3 consecutive failures
  private adaptiveInterval: number; // Adaptive batch interval based on network conditions

  constructor(options: {
    uri: string;
    batchInterval?: number;
    batchMax?: number;
    fetch?: typeof fetch;
    credentials?: RequestCredentials;
    batchEnabled?: boolean;
  }) {
    super();
    this.uri = options.uri;
    this.batchInterval = options.batchInterval || 10;
    this.adaptiveInterval = this.batchInterval;
    this.batchMax = options.batchMax || 10;
    this.fetch = options.fetch || fetch;
    this.credentials = options.credentials;
    this.batchEnabled = options.batchEnabled !== false;
  }

  request(operation: Operation): Observable<FetchResult> {
    return new Observable((observer) => {
      // Don't batch mutations - they should execute immediately
      const isQuery = operation.query.definitions.some(
        (def: any) => def.operation === 'query'
      );

      if (!isQuery || !this.batchEnabled) {
        // Execute mutations immediately or if batching is disabled
        this.executeSingle(operation).then(
          (result) => {
            observer.next(result);
            observer.complete();
          },
          (error) => {
            observer.error(error);
          }
        );
        return;
      }

      // Add query to batch queue
      const batchRequest: BatchRequest = {
        operations: [operation],
        resolve: (results) => {
          observer.next(results[0]);
          observer.complete();
        },
        reject: (error) => {
          observer.error(error);
        },
      };

      this.batchQueue.push(batchRequest);

      // If batch is full, execute immediately
      if (this.batchQueue.length >= this.batchMax) {
        this.executeBatch();
        return;
      }

      // Otherwise, set timer to execute batch after interval
      if (this.batchTimer) {
        clearTimeout(this.batchTimer);
      }

      // Use adaptive interval (increases if batching is slow, decreases if fast)
      this.batchTimer = setTimeout(() => {
        this.executeBatch();
      }, this.adaptiveInterval);
    });
  }

  private async executeBatch(): Promise<void> {
    if (this.batchQueue.length === 0) {
      return;
    }

    const batch = this.batchQueue.splice(0, this.batchMax);
    this.batchTimer = null;

    // If batching is disabled, execute individually
    if (!this.batchEnabled) {
      batch.forEach((req) => {
        this.executeSingle(req.operations[0])
          .then((result) => req.resolve([result]))
          .catch((error) => req.reject(error));
      });
      return;
    }

    try {
      // Prepare batch request - GraphQL batching format (array of operations)
      const batchBody = batch.map((req) => ({
        query: print(req.operations[0].query),
        variables: req.operations[0].variables || {},
        operationName: req.operations[0].operationName || null,
      }));

      // Get auth headers from first operation if available
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      // Try to get auth token from AsyncStorage (if available in context)
      try {
        const AsyncStorage = require('@react-native-async-storage/async-storage').default;
        const token = await AsyncStorage.getItem('token');
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      } catch (e) {
        // Ignore if AsyncStorage not available
      }

      // Execute batch request
      const response = await this.fetch(this.uri, {
        method: 'POST',
        headers,
        body: JSON.stringify(batchBody),
        credentials: this.credentials,
      });

      if (!response.ok) {
        // If batch request fails, fall back to individual requests
        if (response.status === 400 || response.status === 415) {
          // Server doesn't support batching - disable it and retry individually
          logger.warn('[BatchLink] Server doesn\'t support batching, falling back to individual requests');
          this.batchEnabled = false;
          this.consecutiveFailures = 0;
          
          // Execute each request individually
          batch.forEach((req) => {
            this.executeSingle(req.operations[0])
              .then((result) => req.resolve([result]))
              .catch((error) => req.reject(error));
          });
          return;
        }
        throw new Error(`Batch request failed: ${response.status} ${response.statusText}`);
      }

      const results: FetchResult[] = await response.json();

      // Handle both single result and array of results
      const resultArray = Array.isArray(results) ? results : [results];

      // Validate that we got the right number of results
      if (resultArray.length !== batch.length) {
        throw new Error(`Batch response length mismatch: expected ${batch.length}, got ${resultArray.length}`);
      }

      // Reset failure counter on success
      this.consecutiveFailures = 0;
      
      // Adaptive batching: Adjust interval based on batch size
      // Larger batches = slightly longer wait time to collect more
      // Smaller batches = shorter wait time for faster response
      if (batch.length >= this.batchMax * 0.8) {
        // Large batch - slightly increase interval to collect more
        this.adaptiveInterval = Math.min(this.batchInterval * 1.5, 50);
      } else if (batch.length <= 2) {
        // Small batch - decrease interval for faster response
        this.adaptiveInterval = Math.max(this.batchInterval * 0.5, 5);
      } else {
        // Medium batch - use default interval
        this.adaptiveInterval = this.batchInterval;
      }

      // Resolve each request with its corresponding result
      batch.forEach((req, index) => {
        const result = resultArray[index];
        if (result) {
          // Check for errors in the result
          if (result.errors && result.errors.length > 0) {
            // Still resolve with errors (Apollo handles this)
            req.resolve([result]);
          } else {
            req.resolve([result]);
          }
        } else {
          req.reject(new Error('Missing result in batch response'));
        }
      });
    } catch (error) {
      // Increment failure counter
      this.consecutiveFailures++;
      
      // If too many failures, disable batching and fall back to individual requests
      if (this.consecutiveFailures >= this.maxFailures) {
        logger.warn(`[BatchLink] Too many batch failures (${this.consecutiveFailures}), disabling batching`);
        this.batchEnabled = false;
        this.consecutiveFailures = 0;
        
        // Execute each request individually as fallback
        batch.forEach((req) => {
          this.executeSingle(req.operations[0])
            .then((result) => req.resolve([result]))
            .catch((err) => req.reject(err));
        });
        return;
      }

      // Reject all requests in batch (will retry on next attempt)
      batch.forEach((req) => {
        req.reject(error as Error);
      });
    }
  }

  private async executeSingle(operation: Operation): Promise<FetchResult> {
    // Get auth headers
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Try to get auth token from AsyncStorage
    try {
      const AsyncStorage = require('@react-native-async-storage/async-storage').default;
      const token = await AsyncStorage.getItem('token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    } catch (e) {
      // Ignore if AsyncStorage not available
    }

    const response = await this.fetch(this.uri, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        query: print(operation.query),
        variables: operation.variables || {},
        operationName: operation.operationName || null,
      }),
      credentials: this.credentials,
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}

