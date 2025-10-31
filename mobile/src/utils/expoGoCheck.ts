/**
 * Check if running in Expo Go (vs development build)
 */
import Constants from 'expo-constants';

export const isExpoGo = (): boolean => {
  // Expo Go has executionEnvironment === 'storeClient'
  // Development build has executionEnvironment === 'standalone' or 'bare'
  const env = Constants.executionEnvironment;
  
  // Explicitly check for Expo Go
  if (env === 'storeClient') {
    return true; // Definitely Expo Go - no native modules
  }
  
  // If standalone or bare, it's a development/production build (not Expo Go)
  // Native modules are available
  if (env === 'standalone' || env === 'bare') {
    return false; // Development build - native modules available
  }
  
  // If undefined (can happen in some dev builds), default to allowing native modules
  // This is safer - if we're configured for dev-client, native modules should work
  // Only explicitly block if we know we're in Expo Go (storeClient)
  return false; // Default: assume dev build (native modules available)
};

export const requiresDevBuild = (moduleName: string): boolean => {
  // These modules require a development build, not Expo Go
  const devBuildOnlyModules = [
    'react-native-webrtc',
    'react-native-arkit',
    '@picovoice/porcupine-react-native',
    'react-native-agora',
  ];
  
  return devBuildOnlyModules.some(m => moduleName.includes(m));
};

