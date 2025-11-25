// Initialize Sentry for error tracking (must be first)
import './config/sentry';

// Import Reanimated first (required for worklets)
// NOTE: If app crashes during startup with ReanimatedModule.mm:166 error,
// this is a known issue with Reanimated 4.1.1 + RN 0.81 + Expo SDK 54
// Solution: Update to react-native-reanimated ~3.15.0 or wait for fix
import 'react-native-reanimated';

// Import gesture handler (required for react-native-tab-view)
import 'react-native-gesture-handler';

// Import URL polyfill first to fix React Native URL.protocol issues
import 'react-native-url-polyfill/auto';

// Note: LogBox setup moved to index.js (before App import) to catch early errors

import React, { useState, useEffect, lazy, Suspense } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, LogBox } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import ApolloProvider from './ApolloProvider';
import AsyncStorage from '@react-native-async-storage/async-storage';
import JWTAuthService from './features/auth/services/JWTAuthService';
import Toast from 'react-native-toast-message';
// Version 2 Features
import { ThemeProvider } from './theme/PersonalizedThemes';
import GestureNavigation from './components/GestureNavigation';
import ZeroFrictionOnboarding from './features/onboarding/ZeroFrictionOnboarding';
import ErrorBoundary from './components/ErrorBoundary';
import WellnessScoreDashboard from './components/WellnessScoreDashboard';
import ARPortfolioPreview from './components/ARPortfolioPreview';
import SentryTestButton from './components/SentryTestButton';
import OfflineInsightsService from './services/OfflineInsightsService';
import logger from './utils/logger';
// Use only Expo Go compatible services to avoid "Exception in HostFunction" errors
import expoGoCompatibleNotificationService from './features/notifications/services/ExpoGoCompatibleNotificationService';
import expoGoCompatiblePriceAlertService from './features/stocks/services/ExpoGoCompatiblePriceAlertService';
// Always use Expo Go compatible services to prevent crashes
const pushNotificationService = expoGoCompatibleNotificationService;
const priceAlertService = expoGoCompatiblePriceAlertService;
// Screens
import HomeScreen from './navigation/HomeScreen';
import AppNavigator from './navigation/AppNavigator';
import LoginScreen from './features/auth/screens/LoginScreen';
import ForgotPasswordScreen from './features/auth/screens/ForgotPasswordScreen';
import SignUpScreen from './features/auth/screens/SignUpScreen';
import ProfileScreen from './features/user/screens/ProfileScreen';
import AccountManagementScreen from './features/user/screens/AccountManagementScreen';
import StockScreen from './features/stocks/screens/StockScreen';
import PriceChartScreen from './features/stocks/screens/PriceChartScreen';
// ✅ Code splitting: Heavy screens lazy-loaded (reduces initial bundle size)
// StockDetailScreen, AIPortfolioScreen, PortfolioManagementScreen moved to lazy imports below
import SocialScreen from './features/social/screens/SocialScreen';
import PortfolioScreen from './features/portfolio/screens/PortfolioScreen';
import PremiumAnalyticsScreen from './navigation/PremiumAnalyticsScreen';
import SubscriptionScreen from './features/user/screens/SubscriptionScreen';
import LearningPathsScreen from './features/learning/screens/LearningPathsScreen';
import OnboardingScreen, { UserProfile } from './features/auth/screens/OnboardingScreen';
import DiscoverUsersScreen from './features/social/screens/DiscoverUsersScreen';
import UserProfileScreen from './features/user/screens/UserProfileScreen';
import UserPortfoliosScreen from './features/portfolio/screens/UserPortfoliosScreen';
import SimpleCircleDetailScreen from './features/community/screens/SimpleCircleDetailScreen';
import UserActivityScreen from './features/social/screens/UserActivityScreen';
import MessageScreen from './features/social/screens/MessageScreen';
import TradingScreen from './features/stocks/screens/TradingScreen';
import DayTradingScreen from './features/trading/screens/DayTradingScreen';
import MLSystemScreen from './features/ml/screens/MLSystemScreen';
import RiskManagementScreen from './features/risk/screens/RiskManagementScreen';
// Swing Trading Screens
import { SignalsScreen, RiskCoachScreen, SwingTradingDashboard } from './features/swingTrading';
import LeaderboardScreen from './features/swingTrading/screens/LeaderboardScreen';
import BacktestingScreen from './features/swingTrading/screens/BacktestingScreen';
// ✅ Code splitting: AIOptionsScreen and OptionsCopilotScreen moved to lazy imports below
import AIScansScreen from './features/aiScans/screens/AIScansScreen';
import ScanPlaybookScreen from './features/aiScans/screens/ScanPlaybookScreen';
import BankAccountScreen from './features/user/screens/BankAccountScreen';
import NotificationsScreen from './features/notifications/screens/NotificationsScreen';
import CryptoScreen from './navigation/CryptoScreen';
import OptionsLearningScreen from './features/options/screens/OptionsLearningScreen';
import SBLOCLearningScreen from './features/learning/screens/SBLOCLearningScreen';
import SBLOCBankSelectionScreen from './features/sbloc/screens/SBLOCBankSelectionScreen';
import SBLOCApplicationScreen from './features/sbloc/screens/SBLOCApplicationScreen';
import NewsPreferencesScreen from './features/news/screens/NewsPreferencesScreen';
import PortfolioLearningScreen from './features/learning/screens/PortfolioLearningScreen';
// Tax Optimization Screens
import TaxOptimizationScreen from './screens/TaxOptimizationScreen';
import SmartLotsScreen from './screens/SmartLotsScreen';
import BorrowVsSellScreen from './screens/BorrowVsSellScreen';
import WashGuardScreen from './screens/WashGuardScreen';
import TutorScreen from './features/education/screens/TutorScreen';
import TutorAskExplainScreen from './features/learning/screens/TutorAskExplainScreen';
import TutorQuizScreen from './features/learning/screens/TutorQuizScreen';
import TutorModuleScreen from './features/learning/screens/TutorModuleScreen';
import MarketCommentaryScreen from './features/news/screens/MarketCommentaryScreen';
import DailyVoiceDigestScreen from './features/learning/screens/DailyVoiceDigestScreen';
import NotificationCenterScreen from './features/notifications/screens/NotificationCenterScreen';
import WealthCirclesScreen from './features/community/screens/WealthCirclesScreen';
import WealthCircles2 from './components/WealthCircles2';
import SocialTrading from './components/SocialTrading';
import ViralGrowthSystem from './components/ViralGrowthSystem';
import SecurityFortress from './components/SecurityFortress';
import ScalabilityEngine from './components/ScalabilityEngine';
import MarketingRocket from './components/MarketingRocket';
import OracleInsights from './components/OracleInsights';
import VoiceAIAssistant from './components/VoiceAIAssistant';
import BlockchainIntegration from './components/BlockchainIntegration';
import ConnectivityTestScreen from './components/ConnectivityTestScreen';
import ThemeSettingsScreen from './components/ThemeSettingsScreen';
import PeerProgressScreen from './features/community/screens/PeerProgressScreen';
import TradeChallengesScreen from './features/community/screens/TradeChallengesScreen';
import PersonalizationDashboardScreen from './features/personalization/screens/PersonalizationDashboardScreen';
import BehavioralAnalyticsScreen from './features/personalization/screens/BehavioralAnalyticsScreen';
import DynamicContentScreen from './features/personalization/screens/DynamicContentScreen';
import TradingCoachScreen from './features/coach/screens/TradingCoachScreen';
import AITradingCoachScreen from './features/coach/screens/AITradingCoachScreen';
// Components
import { TopHeader, PersonalizedDashboard } from './components';
// Services
import UserProfileService from './features/user/services/UserProfileService';
// Contexts
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { VoiceProvider } from './contexts/VoiceContext';

// ✅ Lazy load heavy screens for code splitting (reduces initial bundle size)
const AIPortfolioScreen = lazy(() => import('./features/portfolio/screens/AIPortfolioScreen'));
const PortfolioManagementScreen = lazy(() => import('./features/portfolio/screens/PortfolioManagementScreen'));
const StockDetailScreen = lazy(() => import('./features/stocks/screens/StockDetailScreen'));
const AIOptionsScreen = lazy(() => import('./features/options/screens/AIOptionsScreen'));
const OptionsCopilotScreen = lazy(() => import('./features/options/screens/OptionsCopilotScreen'));

// Loading fallback component for lazy-loaded screens
const ScreenLoader = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' }}>
    <ActivityIndicator size="large" color="#1D4ED8" />
  </View>
);

function AppContent() {
const { user, isAuthenticated, loading, logout: authLogout } = useAuth();
const [currentScreen, setCurrentScreen] = useState('login');
// Version 2 State
const [showARPreview, setShowARPreview] = useState(false);

// Store setCurrentScreen in a ref to ensure it's always available
const setCurrentScreenRef = React.useRef(setCurrentScreen);
React.useEffect(() => {
  setCurrentScreenRef.current = setCurrentScreen;
}, [setCurrentScreen]);

// Make setCurrentScreen available globally for direct navigation
// Update the global function whenever setCurrentScreenRef changes
React.useEffect(() => {
  if (typeof window !== 'undefined') {
    (window as any).__setCurrentScreen = (screen: string) => {
      logger.log('🔵 __setCurrentScreen called with:', screen);
      logger.log('🔵 Current screen before:', currentScreen);
      logger.log('🔵 isAuthenticated:', isAuthenticated);
      logger.log('🔵 setCurrentScreenRef.current type:', typeof setCurrentScreenRef.current);
      
      // Use React's startTransition to ensure state update is processed
      if (setCurrentScreenRef.current && typeof setCurrentScreenRef.current === 'function') {
        logger.log('🔵 Calling setCurrentScreenRef.current');
        // Force synchronous state update
        setCurrentScreenRef.current(screen);
        logger.log('🔵 setCurrentScreen called via ref, new screen should be:', screen);
        
        // Force a re-render check
        setTimeout(() => {
          logger.log('🔵 After 100ms - checking if screen updated');
          logger.log('🔵 If still not updated, there may be an auth gate blocking it');
        }, 100);
      } else {
        logger.error('❌ setCurrentScreenRef.current is not a function!', setCurrentScreenRef.current);
        // Try direct setCurrentScreen as last resort
        if (typeof setCurrentScreen === 'function') {
          logger.log('🔵 Trying direct setCurrentScreen');
          setCurrentScreen(screen);
        } else {
          logger.error('❌ setCurrentScreen is also not a function!');
        }
      }
    };
    logger.log('✅ Exposed setCurrentScreen globally');
  }
  return () => {
    if (typeof window !== 'undefined') {
      delete (window as any).__setCurrentScreen;
    }
  };
}, [setCurrentScreenRef]); // Update when ref changes

// Listen for force navigation requests (fallback when navigateTo prop fails)
// Use polling instead of window events (React Native doesn't support addEventListener)
React.useEffect(() => {
  if (typeof window === 'undefined') return;
  
  const pollInterval = setInterval(() => {
    const forceNav = (window as any).__forceNavigateTo;
    const timestamp = (window as any).__forceNavigateTimestamp;
    
    if (forceNav) {
      const params = (window as any).__sblocParams || {};
      logger.log('🔍 Poll detected navigation request to:', forceNav, 'timestamp:', timestamp);
      logger.log('🔍 Available methods:', {
        hasNavigateToGlobal: !!(window as any).__navigateToGlobal,
        hasSetCurrentScreen: !!(window as any).__setCurrentScreen,
        setCurrentScreenType: typeof (window as any).__setCurrentScreen
      });
      
      // Try global function first
      if ((window as any).__navigateToGlobal) {
        logger.log('🔍 Using global navigateTo function');
        delete (window as any).__forceNavigateTo;
        delete (window as any).__forceNavigateTimestamp;
        try {
          (window as any).__navigateToGlobal(forceNav, params);
          logger.log('✅ Global navigateTo called');
        } catch (error) {
          logger.error('❌ Error calling global navigateTo:', error);
        }
      } else if ((window as any).__setCurrentScreen) {
        // Fallback to direct setCurrentScreen
        logger.log('🔍 Using direct setCurrentScreen, calling with:', forceNav);
        delete (window as any).__forceNavigateTo;
        delete (window as any).__forceNavigateTimestamp;
        try {
          const setScreenFn = (window as any).__setCurrentScreen;
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
          navigateToGlobal: !!(window as any).__navigateToGlobal,
          setCurrentScreen: !!(window as any).__setCurrentScreen
        });
      }
    }
  }, 50); // Check every 50ms for faster response
  
  return () => {
    clearInterval(pollInterval);
  };
}, []);
const [showWellnessDashboard, setShowWellnessDashboard] = useState(false);
const [portfolioData, setPortfolioData] = useState({
  totalValue: 125000,
  totalReturn: 25000,
  totalReturnPercent: 25,
  holdings: [
    { symbol: 'AAPL', shares: 50, value: 8750, change: 1250, changePercent: 16.7 },
    { symbol: 'MSFT', shares: 30, value: 12000, change: 1800, changePercent: 17.6 },
    { symbol: 'TSLA', shares: 20, value: 4500, change: -500, changePercent: -10.0 },
  ],
  performance: {
    dayChange: 1250,
    weekChange: 3200,
    monthChange: 8500,
    yearChange: 25000,
  }
});
const [offlineStatus, setOfflineStatus] = useState(null);

// Track currentScreen changes for analytics (production)
useEffect(() => {
// Track screen changes for analytics in production
if (!__DEV__) {
// Analytics tracking would go here
}
}, [currentScreen]);

// Handle authentication state changes
useEffect(() => {
  logger.log('🔐 Auth state changed:', { isAuthenticated, currentScreen, user });
  if (isAuthenticated && currentScreen === 'login') {
    logger.log('🔐 User is authenticated, navigating to home');
    setCurrentScreen('home');
  } else if (!isAuthenticated) {
    // Always navigate to login if not authenticated, regardless of current screen
    // EXCEPTION: Allow certain screens to be navigated to even if auth check is pending
    // (e.g., when navigating from authenticated screens like bank-accounts)
    const authBypassScreens = ['SBLOCBankSelection', 'SBLOCApplication', 'bank-accounts'];
    const isAuthBypassScreen = authBypassScreens.includes(currentScreen);
    
    if (currentScreen !== 'login' && currentScreen !== 'forgot-password' && currentScreen !== 'signup' && !isAuthBypassScreen) {
      logger.log('🔐 User is not authenticated, navigating to login');
      setCurrentScreen('login');
      setHasCompletedOnboarding(false);
    } else if (isAuthBypassScreen) {
      logger.log('🔐 Auth bypass screen detected, allowing navigation:', currentScreen);
    }
  }
}, [isAuthenticated, currentScreen, user]);

const isLoggedIn = isAuthenticated;
const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState<boolean | null>(null); // null = not checked yet
const [isLoading, setIsLoading] = useState(false); // Start with false for instant load

// Check onboarding status when user is authenticated
useEffect(() => {
  if (isAuthenticated) {
    const checkOnboarding = async () => {
      try {
        const onboardingCompleted = await UserProfileService.getInstance().isOnboardingCompleted();
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

// Initialize services and check onboarding status (non-blocking for demo)
useEffect(() => {
  const initializeServices = async () => {
    // Skip blocking initialization for demo
    setIsLoading(false);
    try {
      // Authentication state is now handled by AuthContext
      // No need to check JWT service here
      
      // Initialize Version 2 services in background
      const offlineService = OfflineInsightsService;
      const status = offlineService.getOfflineStatus();
      setOfflineStatus(status);
      
      // Initialize push notifications in background (non-blocking)
if (pushNotificationService) {
        pushNotificationService.initialize().catch(() => {});
      }
      
      // Initialize price alert service in background (non-blocking)
if (priceAlertService) {
        priceAlertService.initialize().catch(() => {});
      }
      
      // Initialize Dawn Ritual scheduler
      const { dawnRitualScheduler } = await import('./features/rituals/services/DawnRitualScheduler');
      const preferences = await dawnRitualScheduler.getPreferences();
      if (preferences.enabled) {
        await dawnRitualScheduler.scheduleDailyRitual(preferences);
      }
} catch (error) {
logger.error('Error initializing services:', error);
} finally {
setIsLoading(false);
}
};
initializeServices();
}, []);

// Suppress React Navigation warnings - this app uses custom navigation system
LogBox.ignoreLogs([
  "The action 'NAVIGATE' with payload",
  "was not handled by any navigator",
]);

// Global navigateTo function - will be set below and available via window
let globalNavigateToFunction: ((screen: string, params?: any) => void) | null = null;

const navigateTo = (screen: string, params?: any) => {
  logger.log('🔍 navigateTo called:', { screen, params });
  
  // Store globally for fallback access
  globalNavigateToFunction = navigateTo;
  if (typeof window !== 'undefined') {
    (window as any).__navigateToGlobal = navigateTo;
  }
  
  // Handle Version 2 special screens
  if (screen === 'ar-preview') {
    setShowARPreview(true);
    return;
  }
  
  if (screen === 'wellness-dashboard') {
    setShowWellnessDashboard(true);
    return;
  }
  
  if (screen === 'StockDetail') {
    logger.log('🔍 Navigating to StockDetail with params:', params);
    // Store params for StockDetail screen
    setCurrentScreen('StockDetail');
    // Store params in a way that the screen can access them
    (window as any).__stockDetailParams = params || {};
  } else if (screen === 'SBLOCBankSelection') {
    logger.log('🔍 Navigating to SBLOCBankSelection with params:', params);
    // Store params for SBLOCBankSelection screen
    setCurrentScreen('SBLOCBankSelection');
    // Store params in a way that the screen can access them
    (window as any).__sblocParams = params || { amountUsd: 25000 };
  } else if (screen === 'user-profile' && params?.userId) {
    const newScreen = `user-profile-${params.userId}`;
    setCurrentScreen(newScreen);
  } else if (screen === 'user-portfolios' && params?.userId) {
    const newScreen = `user-portfolios-${params.userId}`;
    setCurrentScreen(newScreen);
  } else if (screen === 'user-activity' && params?.userId) {
    const newScreen = `user-activity-${params.userId}`;
    setCurrentScreen(newScreen);
  } else if (screen === 'message-user' && params?.userId) {
    const newScreen = `message-user-${params.userId}`;
    setCurrentScreen(newScreen);
  } else {
setCurrentScreen(screen);
}
};
const handleLogin = async (token?: string) => {
logger.log('🎉 App handleLogin called with token:', token);
// Check onboarding status first before navigating
await checkOnboardingStatus();
// Navigation will be handled by the onboarding check or by the auth state effect
};
const handleSignUp = () => {
// New users always need onboarding
setHasCompletedOnboarding(false);
setCurrentScreen('onboarding');
};
const checkOnboardingStatus = async () => {
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
};
const handleOnboardingComplete = async (profile: UserProfile) => {
try {
const userProfileService = UserProfileService.getInstance();
await userProfileService.saveProfile(profile);
await userProfileService.markOnboardingCompleted();
setHasCompletedOnboarding(true);
setCurrentScreen('home');
} catch (error) {
logger.error('Error saving user profile:', error);
}
};
const handleLogout = async () => {
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
    // Still navigate to login even if there's an error
    setCurrentScreen('login');
    setHasCompletedOnboarding(false);
}
};
// renderScreen is a regular function (not memoized) so it always sees the latest currentScreen
// This is correct - we want it to re-render whenever currentScreen changes
const renderScreen = () => {
logger.log('🔍 renderScreen called:', { currentScreen, isLoggedIn, isLoading, isAuthenticated, hasCompletedOnboarding });
  
  // Check for pending navigation requests
  if (typeof window !== 'undefined' && (window as any).__forceNavigateTo) {
    const targetScreen = (window as any).__forceNavigateTo;
    logger.log('🔍 renderScreen detected pending navigation to:', targetScreen);
    logger.log('🔍 But currentScreen is still:', currentScreen);
    // Don't delete here - let polling handle it to avoid race conditions
  }

  // ============================================================================
  // SHELL SCREENS PATTERN: Define screens that should be rendered directly
  // (not through AppNavigator). These include auth flows, SBLOC flows, etc.
  // ============================================================================
  const SHELL_SCREENS = new Set([
    'login',
    'signup',
    'forgot-password',
    'onboarding',
    'SBLOCBankSelection',
    'SBLOCApplication',
    'SblocStatus',
    'bank-accounts',
  ] as const);
  
  const isShellScreen = SHELL_SCREENS.has(currentScreen);
  
  // ============================================================================
  // 1) AUTH & ONBOARDING GATES
  // ============================================================================
  
  // Show loading while checking onboarding status
  if (isLoggedIn && hasCompletedOnboarding === null) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#667eea" />
        <Text style={{ marginTop: 16, color: '#666' }}>Loading...</Text>
      </View>
    );
  }
  
  // Show onboarding if user is logged in but hasn't completed onboarding
  if (isLoggedIn && hasCompletedOnboarding === false) {
    return (
      <ZeroFrictionOnboarding
        onComplete={async (profile) => {
          logger.log('✅ Onboarding completed with profile:', profile);
          try {
            const userProfileService = UserProfileService.getInstance();
            await userProfileService.saveProfile(profile);
            await userProfileService.markOnboardingCompleted();
          } catch (error) {
            logger.error('Error saving profile:', error);
          }
          setHasCompletedOnboarding(true);
          setCurrentScreen('home');
        }}
        onSkip={async () => {
          try {
            const userProfileService = UserProfileService.getInstance();
            await userProfileService.markOnboardingCompleted();
          } catch (error) {
            logger.error('Error marking onboarding as completed:', error);
          }
          setHasCompletedOnboarding(true);
          setCurrentScreen('home');
        }}
      />
    );
  }
  
  // Show loading screen while initializing (but not if we're explicitly on login)
  if (isLoading && currentScreen !== 'login') {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }
  
  // ============================================================================
  // 2) SHELL SCREENS: Render directly (auth flows, SBLOC, etc.)
  // ============================================================================
  // These screens are rendered outside of AppNavigator, either because:
  // - They're part of auth/onboarding flows
  // - They need custom navigation handling
  // - They're accessed before full app initialization
  if (!isLoggedIn || isShellScreen) {
    logger.log('🔍 Rendering shell screen:', currentScreen);
    
    switch (currentScreen) {
      case 'login':
        return <LoginScreen 
          onLogin={handleLogin} 
          onNavigateToSignUp={() => setCurrentScreen('signup')} 
          onNavigateToForgotPassword={() => setCurrentScreen('forgot-password')} 
        />;
      case 'signup':
        return (
          <ZeroFrictionOnboarding
            onComplete={(profile) => {
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
        return <ForgotPasswordScreen 
          onNavigateToLogin={() => setCurrentScreen('login')} 
          onNavigateToResetPassword={(email) => setCurrentScreen('login')} 
        />;
      case 'onboarding':
        return <OnboardingScreen onComplete={handleOnboardingComplete} />;
      case 'bank-accounts':
        // Ensure navigateTo is available (should always be defined, but double-check)
        if (!navigateTo) {
          logger.error('❌ navigateTo is undefined when rendering BankAccountScreen!');
        }
        // Check for window-based navigation request (fallback if navigateTo prop fails)
        if (typeof window !== 'undefined' && (window as any).__forceNavigateTo) {
          const targetScreen = (window as any).__forceNavigateTo;
          const params = (window as any).__sblocParams || {};
          delete (window as any).__forceNavigateTo;
          logger.log('🔍 Window-based navigation requested to:', targetScreen, 'with params:', params);
          // Navigate immediately using the function directly
          if (navigateTo) {
            navigateTo(targetScreen, params);
          } else if ((window as any).__navigateToGlobal) {
            (window as any).__navigateToGlobal(targetScreen, params);
          }
        }
        return <BankAccountScreen navigateTo={navigateTo || ((window as any)?.__navigateToGlobal)} navigation={{ navigate: navigateTo || ((window as any)?.__navigateToGlobal), goBack: () => setCurrentScreen('home') }} />;
      case 'SBLOCBankSelection':
        const sblocParams = (window as any).__sblocParams || { amountUsd: 25000 };
        logger.log('🔍 Rendering SBLOCBankSelectionScreen with params:', sblocParams);
        logger.log('🔍 currentScreen is:', currentScreen);
        return <SBLOCBankSelectionScreen 
          navigation={{ 
            navigate: navigateTo || ((screen: string, params?: any) => setCurrentScreen(screen)), 
            goBack: () => setCurrentScreen('bank-accounts') 
          }} 
          route={{ params: sblocParams }} 
        />;
      case 'SBLOCApplication':
        return <SBLOCApplicationScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('SBLOCBankSelection') }} route={{ params: { sessionUrl: '', referral: { id: '', bank: { id: '', name: '', minLtv: 0, maxLtv: 0, minLineUsd: 0, maxLineUsd: 0, typicalAprMin: 0, typicalAprMax: 0, isActive: true, priority: 0 } } } }} />;
      case 'SblocStatus':
        return <SBLOCApplicationScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('SBLOCBankSelection') }} route={{ params: { sessionId: '' } }} />;
      default:
        // If not logged in and not on a shell screen, show login
        if (!isLoggedIn) {
          logger.log('🔍 User not logged in, showing login screen');
          return <LoginScreen 
            onLogin={handleLogin} 
            onNavigateToSignUp={() => setCurrentScreen('signup')} 
            onNavigateToForgotPassword={() => setCurrentScreen('forgot-password')} 
          />;
        }
        // If logged in but on a shell screen that's not handled above, fall through to main switch
        break;
    }
  }
  
  // ============================================================================
  // 3) FULL APP NAVIGATOR: Render AppNavigator for all in-app screens
  // ============================================================================
  // Once authenticated and onboarded, and not on a shell screen, render the full app
  if (isLoggedIn && hasCompletedOnboarding && !isShellScreen) {
    logger.log('🔍 Rendering AppNavigator (user is logged in and not on shell screen)');
    return <AppNavigator key={`app-nav-${isAuthenticated}`} />;
  }
  
  // ============================================================================
  // 4) MAIN SWITCH: Handle remaining screens that aren't shell screens
  // ============================================================================
  // This handles screens that are part of the main app but need direct rendering
  // (e.g., screens that need custom params or navigation handling)
  logger.log('🔍 Main switch statement, currentScreen:', currentScreen);
  switch (currentScreen) {
case 'home':
logger.log('🔍 Rendering HomeScreen');
return <HomeScreen navigateTo={navigateTo} />;
case 'onboarding':
return <OnboardingScreen onComplete={handleOnboardingComplete} />;
case 'profile':
return <ProfileScreen navigateTo={navigateTo} onLogout={handleLogout} />;
case 'account-management':
return <AccountManagementScreen navigateTo={navigateTo} />;
        case 'stock':
          return <StockScreen navigateTo={navigateTo} />;
        case 'StockDetail':
          logger.log('🔍 Rendering StockDetailScreen');
          const stockDetailParams = (window as any).__stockDetailParams || {};
          logger.log('🔍 StockDetail params:', stockDetailParams);
          return (
            <Suspense fallback={<ScreenLoader />}>
              <StockDetailScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('stock'), setParams: (params: any) => {} }} route={{ params: stockDetailParams }} />
            </Suspense>
          );
        case 'crypto':
return <CryptoScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'ai-portfolio':
return (
  <Suspense fallback={<ScreenLoader />}>
    <AIPortfolioScreen navigateTo={navigateTo} />
  </Suspense>
);
case 'portfolio':
return <PortfolioScreen navigateTo={navigateTo} />;
case 'portfolio-management':
return (
  <Suspense fallback={<ScreenLoader />}>
    <PortfolioManagementScreen navigateTo={navigateTo} />
  </Suspense>
);
case 'premium-analytics':
return <PremiumAnalyticsScreen navigateTo={navigateTo} />;
case 'subscription':
return <SubscriptionScreen navigateTo={navigateTo} />;
case 'portfolio-analytics':
return <PremiumAnalyticsScreen navigateTo={navigateTo} />;
case 'stock-screening':
return <StockScreen navigateTo={navigateTo} />;
case 'ai-recommendations':
return (
  <Suspense fallback={<ScreenLoader />}>
    <AIPortfolioScreen navigateTo={navigateTo} />
  </Suspense>
);
case 'social':
return <SocialTrading userId={user?.id || 'me'} />;
case 'learning-paths':
return <LearningPathsScreen />;
case 'discover-users':
return <DiscoverUsersScreen onNavigate={navigateTo} />;
    case 'user-profile':
      // Extract userId from currentScreen if it's in format 'user-profile-{userId}'
      const userId = currentScreen.startsWith('user-profile-') 
        ? currentScreen.replace('user-profile-', '') 
        : 'default-user';
      return <UserProfileScreen userId={userId} onNavigate={navigateTo} />;
    case 'user-portfolios':
      // Extract userId from currentScreen if it's in format 'user-portfolios-{userId}'
      const portfolioUserId = currentScreen.startsWith('user-portfolios-') 
        ? currentScreen.replace('user-portfolios-', '') 
        : 'default-user';
      return <UserPortfoliosScreen userId={portfolioUserId} onNavigate={navigateTo} />;
    case 'user-activity':
      // Extract userId from currentScreen if it's in format 'user-activity-{userId}'
      const activityUserId = currentScreen.startsWith('user-activity-') 
        ? currentScreen.replace('user-activity-', '') 
        : 'default-user';
      return <UserActivityScreen userId={activityUserId} onNavigate={navigateTo} />;
    case 'message-user':
      // Extract userId from currentScreen if it's in format 'message-user-{userId}'
      const messageUserId = currentScreen.startsWith('message-user-') 
        ? currentScreen.replace('message-user-', '') 
        : 'default-user';
      return <MessageScreen userId={messageUserId} onNavigate={navigateTo} />;
case 'social-feed':
return <SocialScreen onNavigate={navigateTo} />;
case 'ai-options':
return (
  <Suspense fallback={<ScreenLoader />}>
    <AIOptionsScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />
  </Suspense>
);
case 'options-copilot':
return (
  <Suspense fallback={<ScreenLoader />}>
    <OptionsCopilotScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('ai-options') }} />
  </Suspense>
);
case 'tutor':
return <TutorScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'scan-playbook':
return <ScanPlaybookScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('ai-scans') }} route={{ params: { scan: { id: '', name: '', description: '', category: '', icon: '', tags: [], isActive: true } } }} />;
case 'trading':
return <TradingScreen navigateTo={navigateTo} />;
case 'day-trading':
return <DayTradingScreen navigateTo={navigateTo} />;
        case 'ml-system':
          return <MLSystemScreen navigateTo={navigateTo} />;
        case 'risk-management':
          return <RiskManagementScreen navigateTo={navigateTo} />;
        case 'swing-trading-test':
          return <SwingTradingDashboard navigateTo={navigateTo} />;
        case 'swing-signals':
          return <SignalsScreen navigateTo={navigateTo} />;
        case 'swing-risk-coach':
          return <RiskCoachScreen navigateTo={navigateTo} />;
        case 'swing-backtesting':
          return <BacktestingScreen navigateTo={navigateTo} />;
        case 'swing-leaderboard':
          return <LeaderboardScreen navigateTo={navigateTo} />;
        case 'notifications':
return <NotificationsScreen navigateTo={navigateTo} />;
case 'options-learning':
return <OptionsLearningScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'sbloc-learning':
return <SBLOCLearningScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'portfolio-learning':
return <PortfolioLearningScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'news-preferences':
return <NewsPreferencesScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('profile') }} />;
case 'tax-optimization':
return <TaxOptimizationScreen />;
case 'smart-lots':
return <SmartLotsScreen />;
case 'borrow-vs-sell':
return <BorrowVsSellScreen />;
case 'wash-guard':
return <WashGuardScreen />;
case 'tutor-ask-explain':
return <TutorAskExplainScreen />;
case 'tutor-quiz':
return <TutorQuizScreen />;
case 'tutor-module':
return <TutorModuleScreen />;
case 'market-commentary':
return <MarketCommentaryScreen />;
        case 'daily-voice-digest':
          return <DailyVoiceDigestScreen />;
case 'notification-center':
return <NotificationCenterScreen />;
        case 'wealth-circles':
          return <WealthCircles2 
            onCirclePress={(circle) => setCurrentScreen('circle-detail')}
            onCreateCircle={() => logger.log('Create circle')}
            onJoinCircle={(circleId) => logger.log('Join circle:', circleId)}
          />;
        case 'circle-detail':
          return <SimpleCircleDetailScreen 
            route={{ params: { circle: { id: '1', name: 'BIPOC Wealth Builders', description: 'Building generational wealth through smart investing and community support', memberCount: 1247, category: 'investment' } } }}
            navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('wealth-circles') }}
          />;
        case 'peer-progress':
          return <PeerProgressScreen />;
        case 'trade-challenges':
          return <TradeChallengesScreen />;
case 'personalization-dashboard':
return <PersonalizationDashboardScreen />;
        case 'behavioral-analytics':
          return <BehavioralAnalyticsScreen />;
        case 'dynamic-content':
          return <DynamicContentScreen />;
case 'trading-coach':
return <TradingCoachScreen />;
case 'ai-trading-coach':
return <AITradingCoachScreen onNavigate={navigateTo} />;
case 'subscription':
return <SubscriptionScreen />;
// Version 2 New Routes
case 'viral-growth':
return <ViralGrowthSystem onNavigate={navigateTo} />;
case 'security-fortress':
return <SecurityFortress onNavigate={navigateTo} />;
case 'scalability-engine':
return <ScalabilityEngine onNavigate={navigateTo} />;
case 'marketing-rocket':
return <MarketingRocket onNavigate={navigateTo} />;
case 'oracle-insights':
return <OracleInsights 
  onInsightPress={(insight) => {
    logger.log('Oracle insight pressed:', insight);
    // Navigate to insight detail or handle the insight
  }}
  onGenerateInsight={() => {
    logger.log('Generate insight requested');
    // Handle insight generation
  }}
/>;
            case 'voice-ai':
            return <VoiceAIAssistant 
              onClose={() => navigateTo('home')} 
              onInsightGenerated={(insight) => {
                logger.log('Insight generated:', insight);
                // You can add logic here to handle insights
              }} 
            />;
            case 'blockchain-integration':
            return <BlockchainIntegration 
              onPortfolioTokenize={(portfolio) => {
                logger.log('Portfolio tokenized:', portfolio);
                // You can add logic here to handle tokenization
              }}
              onDeFiPositionCreate={(position) => {
                logger.log('DeFi position created:', position);
                // You can add logic here to handle DeFi positions
              }}
              onGovernanceVote={(proposalId, vote) => {
                logger.log('Governance vote:', proposalId, vote);
                // You can add logic here to handle governance votes
              }}
            />;
            case 'theme-settings':
            return <ThemeSettingsScreen onClose={() => navigateTo('home')} />;
            case 'connectivity-test':
            return <ConnectivityTestScreen onClose={() => navigateTo('home')} />;
            case 'sentry-test':
            return (
              <View style={{ flex: 1, padding: 20, backgroundColor: '#fff' }}>
                <TouchableOpacity 
                  onPress={() => navigateTo('home')}
                  style={{ marginBottom: 20, padding: 10, backgroundColor: '#007AFF', borderRadius: 6 }}
                >
                  <Text style={{ color: '#fff', textAlign: 'center' }}>← Back</Text>
                </TouchableOpacity>
                <SentryTestButton />
              </View>
            );
    default:
      // Handle user-profile and user-portfolios with userId pattern
      if (currentScreen.startsWith('user-profile-')) {
        const userId = currentScreen.replace('user-profile-', '');
        return <UserProfileScreen userId={userId} onNavigate={navigateTo} />;
      }
      if (currentScreen.startsWith('user-portfolios-')) {
        const userId = currentScreen.replace('user-portfolios-', '');
        return <UserPortfoliosScreen userId={userId} onNavigate={navigateTo} />;
      }
      if (currentScreen.startsWith('user-activity-')) {
        const userId = currentScreen.replace('user-activity-', '');
        return <UserActivityScreen userId={userId} onNavigate={navigateTo} />;
      }
      if (currentScreen.startsWith('message-user-')) {
        const userId = currentScreen.replace('message-user-', '');
        return <MessageScreen userId={userId} onNavigate={navigateTo} />;
      }
      return <HomeScreen navigateTo={navigateTo} />;
}
};
return (
<ThemeProvider>
<GestureHandlerRootView style={styles.container}>
<GestureNavigation 
  onNavigate={navigateTo} 
  currentScreen={currentScreen}
>
  {isLoggedIn && currentScreen !== 'login' && currentScreen !== 'signup' && currentScreen !== 'onboarding' && (
    <TopHeader currentScreen={currentScreen} onNavigate={navigateTo} />
  )}
  {renderScreen()}
  {null}
</GestureNavigation>

{/* Version 2 Features */}
{showARPreview && portfolioData && (
  <ARPortfolioPreview
    portfolio={portfolioData}
    onClose={() => setShowARPreview(false)}
    onTrade={(action) => {
      logger.log('AR Trade Action:', action);
      setShowARPreview(false);
    }}
  />
)}

{showWellnessDashboard && portfolioData && (
  <WellnessScoreDashboard
    portfolio={portfolioData}
    onActionPress={(action) => {
      logger.log('Wellness Action:', action);
      setShowWellnessDashboard(false);
    }}
    onClose={() => setShowWellnessDashboard(false)}
  />
)}

<Toast />
</GestureHandlerRootView>
</ThemeProvider>
);
}

export default function App() {
  return (
    <ErrorBoundary>
      <SafeAreaProvider>
        <ApolloProvider>
          <AuthProvider>
            <VoiceProvider>
              <AppContent />
            </VoiceProvider>
          </AuthProvider>
        </ApolloProvider>
      </SafeAreaProvider>
    </ErrorBoundary>
  );
}
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#F2F2F7',
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
backgroundColor: '#F2F2F7',
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
},
});