/**
 * ShellScreenRenderer
 * Handles rendering of shell screens (auth flows, SBLOC, onboarding)
 * These screens are rendered outside of AppNavigator
 */

import React, { Suspense } from 'react';
import logger from '../../utils/logger';
import type { ScreenName, NavigateParams, WindowNavigationGlobals } from '../types';
import type { UserProfile } from '../../features/auth/screens/OnboardingScreen';

// Shell screen imports
import LoginScreen from '../../features/auth/screens/LoginScreen';
import ForgotPasswordScreen from '../../features/auth/screens/ForgotPasswordScreen';
import SignUpScreen from '../../features/auth/screens/SignUpScreen';
import OnboardingScreen from '../../features/auth/screens/OnboardingScreen';
import ZeroFrictionOnboarding from '../../features/onboarding/ZeroFrictionOnboarding';
import BankAccountScreen from '../../features/user/screens/BankAccountScreen';
import SBLOCBankSelectionScreen from '../../features/sbloc/screens/SBLOCBankSelectionScreen';
import SBLOCApplicationScreen from '../../features/sbloc/screens/SBLOCApplicationScreen';

interface ShellScreenRendererProps {
  currentScreen: ScreenName;
  isLoggedIn: boolean;
  navigateTo: (screen: ScreenName, params?: NavigateParams) => void;
  setCurrentScreen: (screen: ScreenName) => void;
  handleLogin: (token?: string) => Promise<void>;
  handleOnboardingComplete: (profile: UserProfile) => Promise<void>;
  setHasCompletedOnboarding: (completed: boolean) => void;
}

export function ShellScreenRenderer({
  currentScreen,
  isLoggedIn,
  navigateTo,
  setCurrentScreen,
  handleLogin,
  handleOnboardingComplete,
  setHasCompletedOnboarding,
}: ShellScreenRendererProps): React.ReactElement | null {
  logger.log('🔍 Rendering shell screen:', currentScreen);

  const windowWithNav =
    typeof window !== 'undefined' ? (window as Window & WindowNavigationGlobals) : null;

  switch (currentScreen) {
    case 'login':
      return (
        <LoginScreen
          onLogin={handleLogin}
          onNavigateToSignUp={() => navigateTo('signup')}
          onNavigateToForgotPassword={() => navigateTo('forgot-password')}
        />
      );

    case 'signup':
      return (
        <ZeroFrictionOnboarding
          onComplete={profile => {
            logger.log('✅ Onboarding completed with profile:', profile);
            setHasCompletedOnboarding(true);
            setCurrentScreen('home');
          }}
          onSkip={() => {
            setCurrentScreen('login');
          }}
        />
      );

    case 'forgot-password':
      return (
        <ForgotPasswordScreen
          onNavigateToLogin={() => setCurrentScreen('login')}
          onNavigateToResetPassword={email => setCurrentScreen('login')}
        />
      );

    case 'onboarding':
      return <OnboardingScreen onComplete={handleOnboardingComplete} />;

    case 'bank-accounts':
      // Ensure navigateTo is available (should always be defined, but double-check)
      if (!navigateTo) {
        logger.error('❌ navigateTo is undefined when rendering BankAccountScreen!');
      }
      // Check for window-based navigation request (fallback if navigateTo prop fails)
      if (windowWithNav?.__forceNavigateTo) {
        const targetScreen = windowWithNav.__forceNavigateTo;
        const params = windowWithNav.__sblocParams || {};
        delete windowWithNav.__forceNavigateTo;
        logger.log(
          '🔍 Window-based navigation requested to:',
          targetScreen,
          'with params:',
          params
        );
        // Navigate immediately using the function directly
        if (navigateTo) {
          navigateTo(targetScreen as ScreenName, params);
        } else if (windowWithNav.__navigateToGlobal) {
          windowWithNav.__navigateToGlobal(targetScreen, params);
        }
      }
      return (
        <BankAccountScreen
          navigateTo={navigateTo || windowWithNav?.__navigateToGlobal}
          navigation={{
            navigate: navigateTo || windowWithNav?.__navigateToGlobal,
            goBack: () => setCurrentScreen('home'),
          }}
        />
      );

    case 'SBLOCBankSelection':
      const sblocParams = windowWithNav?.__sblocParams || {
        amountUsd: 25000,
      };
      logger.log('🔍 Rendering SBLOCBankSelectionScreen with params:', sblocParams);
      logger.log('🔍 currentScreen is:', currentScreen);
      return (
        <SBLOCBankSelectionScreen
          navigation={{
            navigate:
              navigateTo ||
              ((screen: string, params?: NavigateParams) => setCurrentScreen(screen as ScreenName)),
            goBack: () => setCurrentScreen('bank-accounts'),
          }}
          route={{ params: sblocParams }}
        />
      );

    case 'SBLOCApplication':
      return (
        <SBLOCApplicationScreen
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('SBLOCBankSelection'),
          }}
          route={{
            params: {
              sessionUrl: '',
              referral: {
                id: '',
                bank: {
                  id: '',
                  name: '',
                  minLtv: 0,
                  maxLtv: 0,
                  minLineUsd: 0,
                  maxLineUsd: 0,
                  typicalAprMin: 0,
                  typicalAprMax: 0,
                  isActive: true,
                  priority: 0,
                },
              },
            },
          }}
        />
      );

    case 'SblocStatus':
      return (
        <SBLOCApplicationScreen
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('SBLOCBankSelection'),
          }}
          route={{ params: { sessionId: '' } }}
        />
      );

    default:
      // If not logged in and not on a shell screen, show login
      if (!isLoggedIn) {
        logger.log('🔍 User not logged in, showing login screen');
        return (
          <LoginScreen
            onLogin={handleLogin}
            onNavigateToSignUp={() => setCurrentScreen('signup')}
            onNavigateToForgotPassword={() => setCurrentScreen('forgot-password')}
          />
        );
      }
      // If logged in but on a shell screen that's not handled above, return null to fall through
      return null;
  }
}
