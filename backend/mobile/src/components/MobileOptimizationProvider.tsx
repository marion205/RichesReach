/**
 * Mobile Optimization Provider
 * Provides optimization context and utilities throughout the app
 */
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { useNetworkOptimization } from '../hooks/useNetworkOptimization';
import { useOptimizedDataService } from '../services/OptimizedDataService';
import { getMobileOptimizationConfig, MobileOptimizationConfig } from '../config/mobileOptimization';

interface MobileOptimizationContextType {
  config: MobileOptimizationConfig;
  networkOptimization: any;
  dataService: any;
  isAppActive: boolean;
  isOnline: boolean;
  isDataSaverEnabled: boolean;
  isLowBattery: boolean;
  currentPollingInterval: number;
  dataUsageThisHour: number;
  cacheStats: any;
}

const MobileOptimizationContext = createContext<MobileOptimizationContextType | null>(null);

interface MobileOptimizationProviderProps {
  children: ReactNode;
  customConfig?: Partial<MobileOptimizationConfig>;
}

export const MobileOptimizationProvider: React.FC<MobileOptimizationProviderProps> = ({
  children,
  customConfig = {},
}) => {
  const [isAppActive, setIsAppActive] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [isLowBattery, setIsLowBattery] = useState(false);
  
  // Get configuration
  const baseConfig = getMobileOptimizationConfig();
  const config = { ...baseConfig, ...customConfig };
  
  // Initialize optimization hooks
  const networkOptimization = useNetworkOptimization({
    fastPolling: config.network.fastPolling,
    normalPolling: config.network.normalPolling,
    slowPolling: config.network.slowPolling,
    offlinePolling: config.network.offlinePolling,
    maxDataUsagePerHour: config.network.maxDataUsagePerHour,
    enableDataSaver: config.network.enableDataSaver,
    enableBatteryOptimization: config.battery.enableBatteryOptimization,
    lowBatteryThreshold: config.battery.lowBatteryThreshold,
  });
  
  const { service: dataService } = useOptimizedDataService();
  
  // Monitor app state
  useEffect(() => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      setIsAppActive(nextAppState === 'active');
    };
    
    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  }, []);
  
  // Monitor network connectivity
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((netInfo: NetInfoState) => {
      setIsOnline(netInfo.isConnected ?? false);
    });
    
    return unsubscribe;
  }, []);
  
  // Monitor battery level (simulated for now)
  useEffect(() => {
    if (!config.battery.enableBatteryOptimization) return;
    
    const checkBatteryLevel = () => {
      // Simulate battery level check
      const simulatedBatteryLevel = Math.random() * 100;
      setIsLowBattery(simulatedBatteryLevel < config.battery.lowBatteryThreshold);
    };
    
    const batteryInterval = setInterval(checkBatteryLevel, 60000); // Check every minute
    return () => clearInterval(batteryInterval);
  }, [config.battery.enableBatteryOptimization, config.battery.lowBatteryThreshold]);
  
  // Get cache stats
  const cacheStats = dataService.getCacheStats();
  
  const contextValue: MobileOptimizationContextType = {
    config,
    networkOptimization,
    dataService,
    isAppActive,
    isOnline,
    isDataSaverEnabled: networkOptimization.isDataSaverEnabled,
    isLowBattery,
    currentPollingInterval: networkOptimization.currentPollingInterval,
    dataUsageThisHour: networkOptimization.dataUsageThisHour,
    cacheStats,
  };
  
  return (
    <MobileOptimizationContext.Provider value={contextValue}>
      {children}
    </MobileOptimizationContext.Provider>
  );
};

// Hook to use mobile optimization context
export const useMobileOptimization = (): MobileOptimizationContextType => {
  const context = useContext(MobileOptimizationContext);
  if (!context) {
    throw new Error('useMobileOptimization must be used within a MobileOptimizationProvider');
  }
  return context;
};

// HOC for components that need optimization
export const withMobileOptimization = <P extends object>(
  Component: React.ComponentType<P>
) => {
  return (props: P) => {
    const optimization = useMobileOptimization();
    return <Component {...props} optimization={optimization} />;
  };
};
