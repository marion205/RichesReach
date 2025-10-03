// Import Reanimated first (required for worklets)
import 'react-native-reanimated';

// Import URL polyfill first to fix React Native URL.protocol issues
import 'react-native-url-polyfill/auto';

// Suppress React Native warnings in development
import { LogBox } from 'react-native';
LogBox.ignoreLogs([
  'SafeAreaView has been deprecated',
  'NetInfo not available',
  'Store reset while query was in flight',
  'Network request failed',
  'Network request timed out'
]);

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ApolloProvider } from '@apollo/client';
import { client } from './ApolloProvider';
import AsyncStorage from '@react-native-async-storage/async-storage';
import JWTAuthService from './features/auth/services/JWTAuthService';
import Toast from 'react-native-toast-message';
// Use only Expo Go compatible services to avoid "Exception in HostFunction" errors
import expoGoCompatibleNotificationService from './features/notifications/services/ExpoGoCompatibleNotificationService';
import expoGoCompatiblePriceAlertService from './features/stocks/services/ExpoGoCompatiblePriceAlertService';
// Always use Expo Go compatible services to prevent crashes
const pushNotificationService = expoGoCompatibleNotificationService;
const priceAlertService = expoGoCompatiblePriceAlertService;
// Screens
import HomeScreen from './navigation/HomeScreen';
import LoginScreen from './features/auth/screens/LoginScreen';
import EnhancedLoginScreen from './features/auth/screens/EnhancedLoginScreen';
import ForgotPasswordScreen from './features/auth/screens/ForgotPasswordScreen';
import SignUpScreen from './features/auth/screens/SignUpScreen';
import ProfileScreen from './features/user/screens/ProfileScreen';
import StockScreen from './features/stocks/screens/StockScreen';
import SocialScreen from './features/social/screens/SocialScreen';
import AIPortfolioScreen from './features/portfolio/screens/AIPortfolioScreen';
import PortfolioScreen from './features/portfolio/screens/PortfolioScreen';
import PortfolioManagementScreen from './features/portfolio/screens/PortfolioManagementScreen';
import PremiumAnalyticsScreen from './navigation/PremiumAnalyticsScreen';
import SubscriptionScreen from './features/user/screens/SubscriptionScreen';
import LearningPathsScreen from './features/learning/screens/LearningPathsScreen';
import OnboardingScreen, { UserProfile } from './features/auth/screens/OnboardingScreen';
import DiscoverUsersScreen from './features/social/screens/DiscoverUsersScreen';
import UserProfileScreen from './features/user/screens/UserProfileScreen';
import UserPortfoliosScreen from './features/portfolio/screens/UserPortfoliosScreen';
import UserActivityScreen from './features/social/screens/UserActivityScreen';
import MessageScreen from './features/social/screens/MessageScreen';
import TradingScreen from './features/stocks/screens/TradingScreen';
import DayTradingScreen from './features/trading/screens/DayTradingScreen';
import MLSystemScreen from './features/ml/screens/MLSystemScreen';
import RiskManagementScreen from './features/risk/screens/RiskManagementScreen';
// Swing Trading Screens
import { SignalsScreen, RiskCoachScreen, BacktestingScreen } from './features/swingTrading';
import LeaderboardScreen from './features/swingTrading/screens/LeaderboardScreen';
import SwingTradingTestScreen from './components/SwingTradingTestScreen';
import AIOptionsScreen from './features/options/screens/AIOptionsScreen';
import BankAccountScreen from './features/user/screens/BankAccountScreen';
import NotificationsScreen from './features/notifications/screens/NotificationsScreen';
import CryptoScreen from './navigation/CryptoScreen';
import OptionsLearningScreen from './features/options/screens/OptionsLearningScreen';
import SBLOCLearningScreen from './features/learning/screens/SBLOCLearningScreen';
import SBLOCBankSelectionScreen from './features/sbloc/screens/SBLOCBankSelectionScreen';
import SBLOCApplicationScreen from './features/sbloc/screens/SBLOCApplicationScreen';
import SBLOCStatusScreen from './features/sbloc/screens/SBLOCStatusScreen';
import NewsPreferencesScreen from './features/news/screens/NewsPreferencesScreen';
import PortfolioLearningScreen from './features/learning/screens/PortfolioLearningScreen';
// Components
import { BottomTabBar, TopHeader, PersonalizedDashboard } from './components';
// Services
import UserProfileService from './features/user/services/UserProfileService';
export default function App() {
const [currentScreen, setCurrentScreen] = useState('home');
// Track currentScreen changes for analytics (production)
useEffect(() => {
// Track screen changes for analytics in production
if (!__DEV__) {
// Analytics tracking would go here
}
}, [currentScreen]);
const [isLoggedIn, setIsLoggedIn] = useState(false);
const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
const [isLoading, setIsLoading] = useState(true);
// Initialize services and check onboarding status
useEffect(() => {
  const initializeServices = async () => {
    try {
      // Check if user is already logged in using JWT service
      const jwtService = JWTAuthService.getInstance();
      
      // Set up token refresh failure callback
      jwtService.setTokenRefreshFailureCallback(() => {
        console.log('Token refresh failed, logging out user');
        setIsLoggedIn(false);
        setCurrentScreen('login');
      });
      
      const isAuthenticated = await jwtService.isAuthenticated();
      
      if (isAuthenticated) {
        setIsLoggedIn(true);
        // Set initial screen to home if logged in
        setCurrentScreen('home');
      }
      
      // Check if user has completed onboarding
      const userProfileService = UserProfileService.getInstance();
      const onboardingCompleted = await userProfileService.isOnboardingCompleted();
      setHasCompletedOnboarding(onboardingCompleted);
// Initialize push notifications with error handling
if (pushNotificationService) {
try {
const notificationsEnabled = await pushNotificationService.initialize();
if (notificationsEnabled) {
// Set up notification listeners
const { notificationListener, responseListener } = pushNotificationService.setupNotificationListeners();
// Cleanup listeners on unmount
return () => {
pushNotificationService.removeNotificationListeners(notificationListener, responseListener);
};
}
} catch (notificationError) {
// Push notifications not available (likely Expo Go)
if (__DEV__) {
console.warn(' Push notifications not available:', notificationError instanceof Error ? notificationError.message : 'Unknown error');
}
}
}
// Initialize price alert service
if (priceAlertService) {
try {
await priceAlertService.initialize();
} catch (priceAlertError) {
console.warn(' Price alert service initialization failed:', priceAlertError instanceof Error ? priceAlertError.message : 'Unknown error');
}
} else {
}
} catch (error) {
console.error('Error initializing services:', error);
} finally {
setIsLoading(false);
}
};
initializeServices();
}, []);
const navigateTo = (screen: string, params?: any) => {
  if (screen === 'user-profile' && params?.userId) {
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
const handleLogin = (token?: string) => {
console.log('🎉 App handleLogin called with token:', token);
setIsLoggedIn(true);
// Check if user needs onboarding after login
checkOnboardingStatus();
};
const handleSignUp = () => {
setIsLoggedIn(true);
// New users always need onboarding
setHasCompletedOnboarding(false);
setCurrentScreen('onboarding');
};
const checkOnboardingStatus = async () => {
try {
const userProfileService = UserProfileService.getInstance();
const onboardingCompleted = await userProfileService.isOnboardingCompleted();
setHasCompletedOnboarding(onboardingCompleted);
if (onboardingCompleted) {
setCurrentScreen('home');
} else {
setCurrentScreen('onboarding');
}
} catch (error) {
console.error('Error checking onboarding status:', error);
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
console.error('Error saving user profile:', error);
}
};
const handleLogout = async () => {
try {
const jwtService = JWTAuthService.getInstance();
await jwtService.logout();
} catch (error) {
console.error('Logout error:', error);
} finally {
setIsLoggedIn(false);
setCurrentScreen('login');
}
};
const renderScreen = () => {
// Show loading screen while initializing
if (isLoading) {
return (
<View style={styles.loadingContainer}>
<Text style={styles.loadingText}>Loading...</Text>
</View>
);
}
if (!isLoggedIn) {
switch (currentScreen) {
case 'login':
return <LoginScreen 
onLogin={handleLogin} 
onNavigateToSignUp={() => setCurrentScreen('signup')} 
onNavigateToForgotPassword={() => setCurrentScreen('forgot-password')} 
/>;
case 'forgot-password':
return <ForgotPasswordScreen 
onNavigateToLogin={() => setCurrentScreen('login')} 
onNavigateToResetPassword={(email) => setCurrentScreen('reset-password')} 
/>;
case 'signup':
return <SignUpScreen navigateTo={navigateTo} onSignUp={handleSignUp} onNavigateToLogin={() => setCurrentScreen('login')} />;
default:
return <LoginScreen 
onLogin={handleLogin} 
onNavigateToSignUp={() => setCurrentScreen('signup')} 
onNavigateToForgotPassword={() => setCurrentScreen('forgot-password')} 
/>;
}
}
// Show onboarding if user is logged in but hasn't completed onboarding
if (isLoggedIn && !hasCompletedOnboarding) {
return <OnboardingScreen onComplete={handleOnboardingComplete} />;
}
switch (currentScreen) {
case 'home':
return <HomeScreen navigateTo={navigateTo} />;
case 'onboarding':
return <OnboardingScreen onComplete={handleOnboardingComplete} />;
case 'profile':
return <ProfileScreen navigateTo={navigateTo} onLogout={handleLogout} />;
case 'stock':
return <StockScreen navigateTo={navigateTo} />;
case 'crypto':
return <CryptoScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'ai-portfolio':
return <AIPortfolioScreen navigateTo={navigateTo} />;
case 'portfolio':
return <PortfolioScreen navigateTo={navigateTo} />;
case 'portfolio-management':
return <PortfolioManagementScreen navigateTo={navigateTo} />;
case 'premium-analytics':
return <PremiumAnalyticsScreen navigateTo={navigateTo} />;
case 'subscription':
return <SubscriptionScreen navigateTo={navigateTo} />;
case 'portfolio-analytics':
return <PremiumAnalyticsScreen navigateTo={navigateTo} />;
case 'stock-screening':
return <StockScreen navigateTo={navigateTo} />;
case 'ai-recommendations':
return <AIPortfolioScreen navigateTo={navigateTo} />;
case 'social':
return <SocialScreen onNavigate={navigateTo} />;
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
return <AIOptionsScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'trading':
return <TradingScreen navigateTo={navigateTo} />;
case 'day-trading':
return <DayTradingScreen navigateTo={navigateTo} />;
        case 'ml-system':
          return <MLSystemScreen navigateTo={navigateTo} />;
        case 'risk-management':
          return <RiskManagementScreen navigateTo={navigateTo} />;
        case 'swing-trading-test':
          return <SwingTradingTestScreen navigateTo={navigateTo} />;
        case 'swing-signals':
          return <SignalsScreen navigateTo={navigateTo} />;
        case 'swing-risk-coach':
          return <RiskCoachScreen navigateTo={navigateTo} />;
        case 'swing-backtesting':
          return <BacktestingScreen navigateTo={navigateTo} />;
        case 'swing-leaderboard':
          return <LeaderboardScreen navigateTo={navigateTo} />;
        case 'bank-accounts':
return <BankAccountScreen navigateTo={navigateTo} navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'notifications':
return <NotificationsScreen navigateTo={navigateTo} />;
case 'options-learning':
return <OptionsLearningScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'sbloc-learning':
return <SBLOCLearningScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'portfolio-learning':
return <PortfolioLearningScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'SBLOCBankSelection':
return <SBLOCBankSelectionScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('bank-accounts') }} route={{ params: { amountUsd: 25000 } }} />;
case 'SBLOCApplication':
return <SBLOCApplicationScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('SBLOCBankSelection') }} route={{ params: { sessionUrl: '', referral: { id: '', bank: { id: '', name: '', minLtv: 0, maxLtv: 0, minLineUsd: 0, maxLineUsd: 0, typicalAprMin: 0, typicalAprMax: 0, isActive: true, priority: 0 } } } }} />;
case 'SblocStatus':
return <SBLOCStatusScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('SBLOCBankSelection') }} route={{ params: { sessionId: '' } }} />;
case 'news-preferences':
return <NewsPreferencesScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('profile') }} />;
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
<ApolloProvider client={client}>
<View style={styles.container}>
{isLoggedIn && currentScreen !== 'login' && currentScreen !== 'signup' && currentScreen !== 'onboarding' && (
<TopHeader currentScreen={currentScreen} onNavigate={navigateTo} />
)}
{renderScreen()}
{isLoggedIn && currentScreen !== 'login' && currentScreen !== 'signup' && (
<BottomTabBar currentScreen={currentScreen} onNavigate={navigateTo} />
)}
</View>
<Toast />
</ApolloProvider>
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