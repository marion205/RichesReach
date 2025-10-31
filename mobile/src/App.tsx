// Import Reanimated first (required for worklets)
import 'react-native-reanimated';

// Import gesture handler (required for react-native-tab-view)
import 'react-native-gesture-handler';

// Import URL polyfill first to fix React Native URL.protocol issues
import 'react-native-url-polyfill/auto';

// Suppress React Native warnings in development
import { LogBox } from 'react-native';
LogBox.ignoreLogs([
  'SafeAreaView has been deprecated',
  'NetInfo not available',
  'Store reset while query was in flight',
  'Network request failed',
  'Network request timed out',
  'Text strings must be rendered within a <Text> component',
  'Console Error'
]);
LogBox.ignoreAllLogs(true);

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
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
import OfflineInsightsService from './services/OfflineInsightsService';
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
import StockDetailScreen from './features/stocks/screens/StockDetailScreen';
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
import AIOptionsScreen from './features/options/screens/AIOptionsScreen';
import OptionsCopilotScreen from './features/options/screens/OptionsCopilotScreen';
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
function AppContent() {
const { user, isAuthenticated, loading, logout: authLogout } = useAuth();
const [currentScreen, setCurrentScreen] = useState('login');
// Version 2 State
const [showARPreview, setShowARPreview] = useState(false);
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
  console.log('🔐 Auth state changed:', { isAuthenticated, currentScreen, user });
  if (isAuthenticated && currentScreen === 'login') {
    console.log('🔐 User is authenticated, navigating to home');
    setCurrentScreen('home');
  } else if (!isAuthenticated && currentScreen !== 'login' && currentScreen !== 'forgot-password' && currentScreen !== 'signup') {
    console.log('🔐 User is not authenticated, navigating to login');
    setCurrentScreen('login');
  }
}, [isAuthenticated, currentScreen, user]);

const isLoggedIn = isAuthenticated;
const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
const [isLoading, setIsLoading] = useState(true);
// Initialize services and check onboarding status
useEffect(() => {
  const initializeServices = async () => {
    try {
      // Authentication state is now handled by AuthContext
      // No need to check JWT service here
      
      // Check if user has completed onboarding
      const userProfileService = UserProfileService.getInstance();
      const onboardingCompleted = await userProfileService.isOnboardingCompleted();
      setHasCompletedOnboarding(onboardingCompleted);
      
      // Initialize Version 2 services
      const offlineService = OfflineInsightsService;
      const status = offlineService.getOfflineStatus();
      setOfflineStatus(status);
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
  console.log('🔍 navigateTo called:', { screen, params });
  
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
    console.log('🔍 Navigating to StockDetail with params:', params);
    // Store params for StockDetail screen
    setCurrentScreen('StockDetail');
    // Store params in a way that the screen can access them
    (window as any).__stockDetailParams = params || {};
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
const handleLogin = (token?: string) => {
console.log('🎉 App handleLogin called with token:', token);
// Navigate to home screen after successful login
setCurrentScreen('home');
// Check if user needs onboarding after login
checkOnboardingStatus();
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
    console.log('🔄 Starting logout process...');
    
    // Clear JWT service
    const jwtService = JWTAuthService.getInstance();
    await jwtService.logout();
    console.log('✅ JWT service cleared');
    
    // Clear AuthContext state
    await authLogout();
    console.log('✅ AuthContext cleared');
    
    // Clear local state
    setCurrentScreen('login');
    setHasCompletedOnboarding(false);
    console.log('✅ Local state cleared, navigating to login');
} catch (error) {
    console.error('❌ Logout error:', error);
    // Still navigate to login even if there's an error
    setCurrentScreen('login');
}
};
const renderScreen = () => {
console.log('🔍 renderScreen called:', { currentScreen, isLoggedIn, isLoading });
// Show loading screen while initializing
if (isLoading) {
return (
<View style={styles.loadingContainer}>
<Text style={styles.loadingText}>Loading...</Text>
</View>
);
}
if (!isLoggedIn) {
console.log('🔍 User not logged in, showing login screen');
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
onNavigateToResetPassword={(email) => setCurrentScreen('login')} 
/>;
case 'signup':
return (
<ZeroFrictionOnboarding
onComplete={(profile) => {
setHasCompletedOnboarding(true);
handleSignUp(profile);
}}
onSkip={() => {
setCurrentScreen('login');
}}
/>
);
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
return (
<ZeroFrictionOnboarding
onComplete={(profile) => {
setHasCompletedOnboarding(true);
handleSignUp(profile);
}}
onSkip={() => {
setHasCompletedOnboarding(true);
setCurrentScreen('home');
}}
/>
);
}
// If logged in and onboarding complete, use new tab/stack navigator
if (isLoggedIn && hasCompletedOnboarding) {
  return <AppNavigator />;
}
console.log('🔍 Main switch statement, currentScreen:', currentScreen);
switch (currentScreen) {
case 'home':
console.log('🔍 Rendering HomeScreen');
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
          console.log('🔍 Rendering StockDetailScreen');
          const stockDetailParams = (window as any).__stockDetailParams || {};
          console.log('🔍 StockDetail params:', stockDetailParams);
          return <StockDetailScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('stock'), setParams: (params: any) => {} }} route={{ params: stockDetailParams }} />;
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
return <SocialTrading userId={user?.id || 'me'} onNavigate={navigateTo} initialTab='news' />;
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
case 'options-copilot':
return <OptionsCopilotScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('ai-options') }} />;
case 'tutor':
return <TutorScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('home') }} />;
case 'scan-playbook':
return <ScanPlaybookScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('ai-scans') }} route={{ params: { scan: {} } }} />;
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
          return <SBLOCApplicationScreen navigation={{ navigate: navigateTo, goBack: () => setCurrentScreen('SBLOCBankSelection') }} route={{ params: { sessionId: '' } }} />;
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
            onCreateCircle={() => console.log('Create circle')}
            onJoinCircle={(circleId) => console.log('Join circle:', circleId)}
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
    console.log('Oracle insight pressed:', insight);
    // Navigate to insight detail or handle the insight
  }}
  onGenerateInsight={() => {
    console.log('Generate insight requested');
    // Handle insight generation
  }}
/>;
            case 'voice-ai':
            return <VoiceAIAssistant 
              onClose={() => navigateTo('home')} 
              onInsightGenerated={(insight) => {
                console.log('Insight generated:', insight);
                // You can add logic here to handle insights
              }} 
            />;
            case 'blockchain-integration':
            return <BlockchainIntegration 
              onPortfolioTokenize={(portfolio) => {
                console.log('Portfolio tokenized:', portfolio);
                // You can add logic here to handle tokenization
              }}
              onDeFiPositionCreate={(position) => {
                console.log('DeFi position created:', position);
                // You can add logic here to handle DeFi positions
              }}
              onGovernanceVote={(proposalId, vote) => {
                console.log('Governance vote:', proposalId, vote);
                // You can add logic here to handle governance votes
              }}
            />;
            case 'theme-settings':
            return <ThemeSettingsScreen onClose={() => navigateTo('home')} />;
            case 'connectivity-test':
            return <ConnectivityTestScreen onClose={() => navigateTo('home')} />;
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
      console.log('AR Trade Action:', action);
      setShowARPreview(false);
    }}
  />
)}

{showWellnessDashboard && portfolioData && (
  <WellnessScoreDashboard
    portfolio={portfolioData}
    onActionPress={(action) => {
      console.log('Wellness Action:', action);
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