/**
 * Optimized Polling Hook for Battery and Data Efficiency
 * Implements intelligent polling with exponential backoff and smart intervals
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useNetworkOptimization } from './useNetworkOptimization';
import logger from '../utils/logger';

interface PollingConfig {
  enabled: boolean;
  maxRetries: number;
  backoffMultiplier: number;
  maxBackoffInterval: number;
  enableSmartPolling: boolean;
}

const DEFAULT_POLLING_CONFIG: PollingConfig = {
  enabled: true,
  maxRetries: 3,
  backoffMultiplier: 1.5,
  maxBackoffInterval: 300000, // 5 minutes
  enableSmartPolling: true,
};

interface PollingState {
  isPolling: boolean;
  retryCount: number;
  lastSuccessTime: number | null;
  lastErrorTime: number | null;
  currentInterval: number;
  isBackingOff: boolean;
}

export const useOptimizedPolling = (
  pollFunction: () => Promise<any>,
  config: Partial<PollingConfig> = {}
) => {
  const finalConfig = { ...DEFAULT_POLLING_CONFIG, ...config };
  const networkOptimization = useNetworkOptimization();
  
  const [state, setState] = useState<PollingState>({
    isPolling: false,
    retryCount: 0,
    lastSuccessTime: null,
    lastErrorTime: null,
    currentInterval: networkOptimization.currentPollingInterval,
    isBackingOff: false,
  });
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Calculate smart polling interval based on success/failure patterns
  const calculateSmartInterval = useCallback(() => {
    if (!finalConfig.enableSmartPolling) {
      return networkOptimization.currentPollingInterval;
    }
    
    const now = Date.now();
    const { lastSuccessTime, lastErrorTime, retryCount } = state;
    
    // If we have recent errors, use exponential backoff
    if (lastErrorTime && (now - lastErrorTime) < 60000) { // Within last minute
      const backoffInterval = Math.min(
        networkOptimization.currentPollingInterval * Math.pow(finalConfig.backoffMultiplier, retryCount),
        finalConfig.maxBackoffInterval
      );
      return backoffInterval;
    }
    
    // If we have recent success, we can poll more frequently
    if (lastSuccessTime && (now - lastSuccessTime) < 30000) { // Within last 30 seconds
      return Math.max(networkOptimization.currentPollingInterval * 0.5, 5000); // At least 5 seconds
    }
    
    // Default to network-optimized interval
    return networkOptimization.currentPollingInterval;
  }, [state, networkOptimization.currentPollingInterval, finalConfig]);
  
  // Execute polling with error handling
  const executePoll = useCallback(async () => {
    if (!networkOptimization.shouldMakeRequest()) {
      // Skipping poll due to network optimization
      return;
    }
    
    try {
      setState(prev => ({ ...prev, isPolling: true }));
      
      const startTime = Date.now();
      const result = await pollFunction();
      const endTime = Date.now();
      
      // Track data usage (estimate based on response size)
      const estimatedBytes = JSON.stringify(result).length;
      networkOptimization.trackDataUsage(estimatedBytes);
      
      setState(prev => ({
        ...prev,
        isPolling: false,
        retryCount: 0,
        lastSuccessTime: Date.now(),
        isBackingOff: false,
      }));
      
      return result;
    } catch (error) {
      logger.error('Polling error:', error);
      
      setState(prev => ({
        ...prev,
        isPolling: false,
        retryCount: prev.retryCount + 1,
        lastErrorTime: Date.now(),
        isBackingOff: true,
      }));
      
      throw error;
    }
  }, [pollFunction, networkOptimization]);
  
  // Start polling
  const startPolling = useCallback(() => {
    if (!finalConfig.enabled || intervalRef.current) return;
    
    const poll = async () => {
      try {
        await executePoll();
      } catch (error) {
        // Error handling is done in executePoll
      }
    };
    
    // Execute immediately
    poll();
    
    // Set up interval
    const scheduleNext = () => {
      const interval = calculateSmartInterval();
      setState(prev => ({ ...prev, currentInterval: interval }));
      
      timeoutRef.current = setTimeout(() => {
        poll();
        scheduleNext();
      }, interval);
    };
    
    scheduleNext();
    
    // Cleanup on unmount or when disabled
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [finalConfig.enabled, executePoll, calculateSmartInterval]);
  
  // Stop polling
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    
    setState(prev => ({ ...prev, isPolling: false }));
  }, []);
  
  // Restart polling with new interval
  const restartPolling = useCallback(() => {
    stopPolling();
    startPolling();
  }, [stopPolling, startPolling]);
  
  // Update interval when network conditions change
  useEffect(() => {
    if (intervalRef.current) {
      restartPolling();
    }
  }, [networkOptimization.currentPollingInterval, restartPolling]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);
  
  return {
    ...state,
    startPolling,
    stopPolling,
    restartPolling,
    executePoll,
    networkOptimization,
  };
};
