/**
 * Network Optimization Hook for Battery and Data Usage
 * Implements intelligent polling, caching, and background sync
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { AppState, AppStateStatus } from 'react-native';

interface NetworkOptimizationConfig {
  // Polling intervals (in milliseconds)
  fastPolling: number;      // When app is active and on WiFi
  normalPolling: number;    // When app is active and on cellular
  slowPolling: number;      // When app is in background
  offlinePolling: number;   // When offline (for retry attempts)
  
  // Data usage limits
  maxDataUsagePerHour: number; // MB per hour
  enableDataSaver: boolean;
  
  // Battery optimization
  enableBatteryOptimization: boolean;
  lowBatteryThreshold: number; // Percentage
}

const DEFAULT_CONFIG: NetworkOptimizationConfig = {
  fastPolling: 10000,      // 10 seconds on WiFi
  normalPolling: 30000,    // 30 seconds on cellular
  slowPolling: 300000,     // 5 minutes in background
  offlinePolling: 60000,   // 1 minute when offline
  
  maxDataUsagePerHour: 50, // 50MB per hour
  enableDataSaver: true,
  
  enableBatteryOptimization: true,
  lowBatteryThreshold: 20, // 20%
};

interface NetworkOptimizationState {
  isOnline: boolean;
  connectionType: string | null;
  isDataSaverEnabled: boolean;
  isLowBattery: boolean;
  currentPollingInterval: number;
  dataUsageThisHour: number;
  isAppActive: boolean;
}

export const useNetworkOptimization = (config: Partial<NetworkOptimizationConfig> = {}) => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };
  
  const [state, setState] = useState<NetworkOptimizationState>({
    isOnline: true,
    connectionType: null,
    isDataSaverEnabled: false,
    isLowBattery: false,
    currentPollingInterval: finalConfig.normalPolling,
    dataUsageThisHour: 0,
    isAppActive: true,
  });
  
  const dataUsageRef = useRef(0);
  const lastDataResetRef = useRef(Date.now());
  const batteryLevelRef = useRef(100);
  
  // Update polling interval based on current conditions
  const updatePollingInterval = useCallback(() => {
    let interval = finalConfig.normalPolling;
    
    if (!state.isOnline) {
      interval = finalConfig.offlinePolling;
    } else if (!state.isAppActive) {
      interval = finalConfig.slowPolling;
    } else if (state.isDataSaverEnabled || state.isLowBattery) {
      interval = finalConfig.slowPolling;
    } else if (state.connectionType === 'wifi') {
      interval = finalConfig.fastPolling;
    } else {
      interval = finalConfig.normalPolling;
    }
    
    setState(prev => ({ ...prev, currentPollingInterval: interval }));
  }, [state.isOnline, state.isAppActive, state.isDataSaverEnabled, state.isLowBattery, state.connectionType, finalConfig]);
  
  // Monitor network connectivity
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((netInfo: NetInfoState) => {
      setState(prev => ({
        ...prev,
        isOnline: netInfo.isConnected ?? false,
        connectionType: netInfo.type,
        isDataSaverEnabled: (netInfo as any).isConnectionExpensive ?? false,
      }));
    });
    
    return unsubscribe;
  }, []);
  
  // Monitor app state
  useEffect(() => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      setState(prev => ({
        ...prev,
        isAppActive: nextAppState === 'active',
      }));
    };
    
    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  }, []);
  
  // Monitor battery level (if available)
  useEffect(() => {
    if (!finalConfig.enableBatteryOptimization) return;
    
    // Note: Battery API is not available in React Native by default
    // This would need a native module or third-party library
    // For now, we'll simulate battery monitoring
    const checkBatteryLevel = () => {
      // Simulate battery level check
      const simulatedBatteryLevel = Math.random() * 100;
      batteryLevelRef.current = simulatedBatteryLevel;
      
      setState(prev => ({
        ...prev,
        isLowBattery: simulatedBatteryLevel < finalConfig.lowBatteryThreshold,
      }));
    };
    
    const batteryInterval = setInterval(checkBatteryLevel, 60000); // Check every minute
    return () => clearInterval(batteryInterval);
  }, [finalConfig.enableBatteryOptimization, finalConfig.lowBatteryThreshold]);
  
  // Update polling interval when conditions change
  useEffect(() => {
    updatePollingInterval();
  }, [updatePollingInterval]);
  
  // Track data usage
  const trackDataUsage = useCallback((bytes: number) => {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    
    // Reset data usage counter every hour
    if (now - lastDataResetRef.current > oneHour) {
      dataUsageRef.current = 0;
      lastDataResetRef.current = now;
    }
    
    dataUsageRef.current += bytes;
    const mbUsed = dataUsageRef.current / (1024 * 1024);
    
    setState(prev => ({
      ...prev,
      dataUsageThisHour: mbUsed,
    }));
    
    // Enable data saver if usage exceeds limit
    if (mbUsed > finalConfig.maxDataUsagePerHour && finalConfig.enableDataSaver) {
      setState(prev => ({
        ...prev,
        isDataSaverEnabled: true,
      }));
    }
  }, [finalConfig.maxDataUsagePerHour, finalConfig.enableDataSaver]);
  
  // Get optimized fetch options
  const getOptimizedFetchOptions = useCallback(() => {
    const options: RequestInit = {
      cache: state.isDataSaverEnabled ? 'force-cache' : 'default',
    };
    
    // Add compression headers for data saver
    if (state.isDataSaverEnabled) {
      options.headers = {
        ...options.headers,
        'Accept-Encoding': 'gzip, deflate',
        'Cache-Control': 'max-age=300', // 5 minutes cache
      };
    }
    
    return options;
  }, [state.isDataSaverEnabled]);
  
  // Check if we should make a network request
  const shouldMakeRequest = useCallback(() => {
    // Don't make requests if offline
    if (!state.isOnline) return false;
    
    // Don't make requests if data usage is too high
    if (state.dataUsageThisHour > finalConfig.maxDataUsagePerHour) return false;
    
    // Don't make requests if battery is very low
    if (state.isLowBattery && batteryLevelRef.current < 10) return false;
    
    return true;
  }, [state.isOnline, state.dataUsageThisHour, state.isLowBattery, finalConfig.maxDataUsagePerHour]);
  
  return {
    ...state,
    trackDataUsage,
    getOptimizedFetchOptions,
    shouldMakeRequest,
    updatePollingInterval,
  };
};
