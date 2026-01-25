/**
 * Custom navigation hook
 * Extracts navigation logic from App.tsx into a reusable hook
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import logger from '../utils/logger';
import type { ScreenName, NavigateParams, WindowNavigationGlobals } from './types';

interface UseNavigationReturn {
  currentScreen: ScreenName;
  currentScreenParams: NavigateParams;
  setCurrentScreen: (screen: ScreenName) => void;
  navigateTo: (screen: ScreenName, params?: NavigateParams) => void;
  screenKey: number;
  setScreenKey: React.Dispatch<React.SetStateAction<number>>;
}

export function useNavigation(): UseNavigationReturn {
  const [currentScreen, setCurrentScreen] = useState<ScreenName>('login');
  const [currentScreenParams, setCurrentScreenParams] = useState<NavigateParams>({});
  const [screenKey, setScreenKey] = useState(0); // Force re-render key

  // Store setCurrentScreen in a ref to ensure it's always available
  const setCurrentScreenRef = useRef(setCurrentScreen);
  useEffect(() => {
    setCurrentScreenRef.current = setCurrentScreen;
  }, [setCurrentScreen]);

  // Make setCurrentScreen available globally for direct navigation
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const windowWithNav = window as Window & WindowNavigationGlobals;
    windowWithNav.__setCurrentScreen = (screen: ScreenName) => {
      logger.log('🔵 __setCurrentScreen called with:', screen);
      logger.log('🔵 Current screen before:', currentScreen);
      logger.log('🔵 setCurrentScreenRef.current type:', typeof setCurrentScreenRef.current);

      if (setCurrentScreenRef.current && typeof setCurrentScreenRef.current === 'function') {
        logger.log('🔵 Calling setCurrentScreenRef.current');
        setCurrentScreenRef.current(screen as ScreenName);
        logger.log('🔵 setCurrentScreen called via ref, new screen should be:', screen);

        setTimeout(() => {
          logger.log('🔵 After 100ms - checking if screen updated');
          logger.log('🔵 If still not updated, there may be an auth gate blocking it');
        }, 100);
      } else {
        logger.error(
          '❌ setCurrentScreenRef.current is not a function!',
          setCurrentScreenRef.current,
        );
        if (typeof setCurrentScreen === 'function') {
          logger.log('🔵 Trying direct setCurrentScreen');
          setCurrentScreen(screen as ScreenName);
        } else {
          logger.error('❌ setCurrentScreen is also not a function!');
        }
      }
    };
    logger.log('✅ Exposed setCurrentScreen globally');

    return () => {
      if (typeof window !== 'undefined') {
        const windowWithNav = window as Window & WindowNavigationGlobals;
        delete windowWithNav.__setCurrentScreen;
      }
    };
  }, [currentScreen, setCurrentScreen]);

  // Listen for force navigation requests (fallback when navigateTo prop fails)
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const windowWithNav = window as Window & WindowNavigationGlobals;
    const pollInterval = setInterval(() => {
      const forceNav = windowWithNav.__forceNavigateTo;
      const timestamp = windowWithNav.__forceNavigateTimestamp;

      if (forceNav) {
        const params = windowWithNav.__sblocParams || {};
        logger.log('🔍 Poll detected navigation request to:', forceNav, 'timestamp:', timestamp);
        logger.log('🔍 Available methods:', {
          hasNavigateToGlobal: !!windowWithNav.__navigateToGlobal,
          hasSetCurrentScreen: !!windowWithNav.__setCurrentScreen,
          setCurrentScreenType: typeof windowWithNav.__setCurrentScreen,
        });

        // Try global function first
        if (windowWithNav.__navigateToGlobal) {
          logger.log('🔍 Using global navigateTo function');
          delete windowWithNav.__forceNavigateTo;
          delete windowWithNav.__forceNavigateTimestamp;
          try {
            windowWithNav.__navigateToGlobal(forceNav, params);
            logger.log('✅ Global navigateTo called');
          } catch (error) {
            logger.error('❌ Error calling global navigateTo:', error);
          }
        } else if (windowWithNav.__setCurrentScreen) {
          logger.log('🔍 Using direct setCurrentScreen, calling with:', forceNav);
          delete windowWithNav.__forceNavigateTo;
          delete windowWithNav.__forceNavigateTimestamp;
          try {
            const setScreenFn = windowWithNav.__setCurrentScreen;
            if (typeof setScreenFn === 'function') {
              setScreenFn(forceNav);
              logger.log('✅ setCurrentScreen called with:', forceNav);
            } else {
              logger.error('❌ setScreenFn is not a function!');
            }
          } catch (error) {
            logger.error('❌ Error calling setCurrentScreen:', error);
          }
        } else {
          logger.error('❌ No navigation method available!');
          logger.error('❌ Available:', {
            navigateToGlobal: !!windowWithNav.__navigateToGlobal,
            setCurrentScreen: !!windowWithNav.__setCurrentScreen,
          });
        }
      }
    }, 50); // Check every 50ms for faster response

    return () => {
      clearInterval(pollInterval);
    };
  }, []);

  const navigateTo = useCallback(
    (screen: ScreenName, params?: NavigateParams) => {
      logger.log('🔍 navigateTo called:', { screen, params });

      // Store globally for fallback access
      if (typeof window !== 'undefined') {
        const windowWithNav = window as Window & WindowNavigationGlobals;
        windowWithNav.__navigateToGlobal = navigateTo;
        windowWithNav.__setCurrentScreen = setCurrentScreen as any; // Dispatch type
        windowWithNav.__currentScreenParams = params || {};
      }

      // Store params for the screen
      if (params) {
        setCurrentScreenParams(params);
        if (typeof window !== 'undefined') {
          const windowWithNav = window as Window & WindowNavigationGlobals;
          windowWithNav.__currentScreenParams = params;
        }
      }

      // Handle special screen cases first
      if (screen === 'StockDetail') {
        logger.log('🔍 Navigating to StockDetail with params:', params);
        setScreenKey(prev => prev + 1);
        setCurrentScreen('StockDetail');
        if (typeof window !== 'undefined') {
          const windowWithNav = window as Window & WindowNavigationGlobals;
          windowWithNav.__stockDetailParams = params || {};
        }
        return;
      } else if (screen === 'SBLOCBankSelection') {
        logger.log('🔍 Navigating to SBLOCBankSelection with params:', params);
        setScreenKey(prev => prev + 1);
        setCurrentScreen('SBLOCBankSelection');
        if (typeof window !== 'undefined') {
          const windowWithNav = window as Window & WindowNavigationGlobals;
          windowWithNav.__sblocParams = params || { amountUsd: 25000 };
        }
        return;
      } else if (screen === 'user-profile' && params?.userId) {
        const newScreen = `user-profile-${params.userId}` as ScreenName;
        setScreenKey(prev => prev + 1);
        setCurrentScreen(newScreen);
        return;
      } else if (screen === 'user-portfolios' && params?.userId) {
        const newScreen = `user-portfolios-${params.userId}` as ScreenName;
        setScreenKey(prev => prev + 1);
        setCurrentScreen(newScreen);
        return;
      } else if (screen === 'user-activity' && params?.userId) {
        const newScreen = `user-activity-${params.userId}` as ScreenName;
        setScreenKey(prev => prev + 1);
        setCurrentScreen(newScreen);
        return;
      } else if (screen === 'message-user' && params?.userId) {
        const newScreen = `message-user-${params.userId}` as ScreenName;
        setScreenKey(prev => prev + 1);
        setCurrentScreen(newScreen);
        return;
      } else {
        logger.log('🔍 Setting current screen to:', screen);
        logger.log('🔍 Current screen before change:', currentScreen);
        logger.log('🔍 setCurrentScreen function type:', typeof setCurrentScreen);

        // Force state update - always call setCurrentScreen to ensure React re-renders
        setScreenKey(prev => {
          const newKey = prev + 1;
          logger.log('🔍 Screen key incremented:', prev, '->', newKey);
          return newKey;
        });

        // Update window FIRST, before React state
        if (typeof window !== 'undefined') {
          const windowWithNav = window as Window & WindowNavigationGlobals;
          windowWithNav.__currentScreen = screen;
          logger.log('🔍 window.__currentScreen set to:', screen);
        }

        // Then update React state
        setCurrentScreen(screen);

        logger.log('🔍 setCurrentScreen called with:', screen, '(was:', currentScreen, ')');

        // Store params if provided
        if (params) {
          setCurrentScreenParams(params);
          if (typeof window !== 'undefined') {
            const windowWithNav = window as Window & WindowNavigationGlobals;
            windowWithNav.__currentScreenParams = params;
          }
        } else {
          setCurrentScreenParams({});
          if (typeof window !== 'undefined') {
            const windowWithNav = window as Window & WindowNavigationGlobals;
            windowWithNav.__currentScreenParams = {};
          }
        }

        setTimeout(() => {
          logger.log('🔍 Screen state after navigation:', currentScreen);
        }, 100);
      }
    },
    [currentScreen, setCurrentScreen]
  );

  return {
    currentScreen,
    currentScreenParams,
    setCurrentScreen,
    navigateTo,
    screenKey,
    setScreenKey,
  };
}
