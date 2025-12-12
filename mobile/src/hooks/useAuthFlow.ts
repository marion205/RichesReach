/**
 * useAuthFlow Hook
 * Handles authentication state management, onboarding checks, and auth-related navigation
 * Extracted from App.tsx to improve testability and separation of concerns
 */

import { useState, useEffect, useCallback } from 'react';
import logger from '../utils/logger';
import UserProfileService from '../features/user/services/UserProfileService';
import JWTAuthService from '../features/auth/services/JWTAuthService';
import type { ScreenName } from '../navigation/types';
import type { UserProfile } from '../features/auth/screens/OnboardingScreen';

interface UseAuthFlowProps {
  isAuthenticated: boolean;
  user: { id?: string } | null;
  currentScreen: ScreenName;
  setCurrentScreen: (screen: ScreenName) => void;
  authLogout: () => Promise<void>;
}

interface UseAuthFlowResult {
  hasCompletedOnboarding: boolean | null; // null = not checked yet
  setHasCompletedOnboarding: (completed: boolean) => void;
  handleLogin: (token?: string) => Promise<void>;
  handleSignUp: () => void;
  handleOnboardingComplete: (profile: UserProfile) => Promise<void>;
  handleLogout: () => Promise<void>;
  checkOnboardingStatus: () => Promise<void>;
}

/**
 * Hook to manage authentication flow, onboarding status, and related navigation
 */
export function useAuthFlow({
  isAuthenticated,
  user,
  currentScreen,
  setCurrentScreen,
  authLogout,
}: UseAuthFlowProps): UseAuthFlowResult {
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState<boolean | null>(null); // null = not checked yet

  // Handle authentication state changes
  useEffect(() => {
    logger.log('🔐 Auth state changed:', {
      isAuthenticated,
      currentScreen,
      user,
    });
    if (isAuthenticated && currentScreen === 'login') {
      logger.log('🔐 User is authenticated, navigating to home');
      setCurrentScreen('home');
    } else if (!isAuthenticated) {
      // Always navigate to login if not authenticated, regardless of current screen
      // EXCEPTION: Allow certain screens to be navigated to even if auth check is pending
      // (e.g., when navigating from authenticated screens like bank-accounts)
      const authBypassScreens: ScreenName[] = [
        'SBLOCBankSelection',
        'SBLOCApplication',
        'bank-accounts',
      ];
      const isAuthBypassScreen = authBypassScreens.includes(currentScreen);

      if (
        currentScreen !== 'login' &&
        currentScreen !== 'forgot-password' &&
        currentScreen !== 'signup' &&
        !isAuthBypassScreen
      ) {
        logger.log('🔐 User is not authenticated, navigating to login');
        setCurrentScreen('login');
        setHasCompletedOnboarding(false);
      } else if (isAuthBypassScreen) {
        logger.log('🔐 Auth bypass screen detected, allowing navigation:', currentScreen);
      }
    }
  }, [isAuthenticated, currentScreen, user, setCurrentScreen]);

  // Check onboarding status when user is authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const checkOnboarding = async () => {
        try {
          const onboardingCompleted =
            await UserProfileService.getInstance().isOnboardingCompleted();
          logger.log('✅ Onboarding check result:', onboardingCompleted);
          setHasCompletedOnboarding(onboardingCompleted);
        } catch (error) {
          logger.error('Error checking onboarding status:', error);
          setHasCompletedOnboarding(false); // Default to false on error
        }
      };
      checkOnboarding();
    } else {
      // Reset onboarding status when logged out
      setHasCompletedOnboarding(null);
    }
  }, [isAuthenticated]);

  const checkOnboardingStatus = useCallback(async () => {
    try {
      const userProfileService = UserProfileService.getInstance();
      const onboardingCompleted = await userProfileService.isOnboardingCompleted();
      setHasCompletedOnboarding(onboardingCompleted);
      if (!onboardingCompleted) {
        setCurrentScreen('onboarding');
      }
    } catch (error) {
      logger.error('Error checking onboarding status:', error);
      setCurrentScreen('onboarding');
    }
  }, [setCurrentScreen]);

  const handleLogin = useCallback(
    async (token?: string) => {
      logger.log('🎉 App handleLogin called with token:', token);
      // Check onboarding status first before navigating
      await checkOnboardingStatus();
      // Navigation will be handled by the onboarding check or by the auth state effect
    },
    [checkOnboardingStatus]
  );

  const handleSignUp = useCallback(() => {
    // New users always need onboarding
    setHasCompletedOnboarding(false);
    setCurrentScreen('onboarding');
  }, [setCurrentScreen]);

  const handleOnboardingComplete = useCallback(
    async (profile: UserProfile) => {
      try {
        const userProfileService = UserProfileService.getInstance();
        await userProfileService.saveProfile(profile);
        await userProfileService.markOnboardingCompleted();
        setHasCompletedOnboarding(true);
        setCurrentScreen('home');
      } catch (error) {
        logger.error('Error saving user profile:', error);
      }
    },
    [setCurrentScreen]
  );

  const handleLogout = useCallback(async () => {
    try {
      logger.log('🔄 Starting logout process...');

      // CRITICAL: Set screen to login FIRST, before any async operations
      // This ensures renderScreen() will return LoginScreen immediately
      setCurrentScreen('login');
      setHasCompletedOnboarding(false);
      logger.log('✅ Local state cleared, navigating to login (IMMEDIATE)');

      // Clear JWT service
      const jwtService = JWTAuthService.getInstance();
      await jwtService.logout();
      logger.log('✅ JWT service cleared');

      // Clear AuthContext state (this will trigger isAuthenticated to become false)
      await authLogout();
      logger.log('✅ AuthContext cleared');

      // Force navigation to login screen again after auth clears
      setCurrentScreen('login');
      setHasCompletedOnboarding(false);
      logger.log('✅ Forced navigation to login screen (after auth clear)');
    } catch (error) {
      logger.error('❌ Logout error:', error);
      setCurrentScreen('login');
      setHasCompletedOnboarding(false);
    }
  }, [setCurrentScreen, authLogout]);

  return {
    hasCompletedOnboarding,
    setHasCompletedOnboarding,
    handleLogin,
    handleSignUp,
    handleOnboardingComplete,
    handleLogout,
    checkOnboardingStatus,
  };
}
