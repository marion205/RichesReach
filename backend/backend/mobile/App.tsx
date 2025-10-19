import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ApolloProvider } from '@apollo/client';
import { client } from './src/ApolloProvider';
import AsyncStorage from '@react-native-async-storage/async-storage';
import JWTAuthService from './services/JWTAuthService';
// Use only Expo Go compatible services to avoid "Exception in HostFunction" errors
import expoGoCompatibleNotificationService from './services/ExpoGoCompatibleNotificationService';
import expoGoCompatiblePriceAlertService from './services/ExpoGoCompatiblePriceAlertService';
// Always use Expo Go compatible services to prevent crashes
const pushNotificationService = expoGoCompatibleNotificationService;
const priceAlertService = expoGoCompatiblePriceAlertService;
// Screens
import HomeScreen from './screens/HomeScreen';
import LoginScreen from './screens/LoginScreen';
import EnhancedLoginScreen from './screens/EnhancedLoginScreen';
import ForgotPasswordScreen from './screens/ForgotPasswordScreen';
import SignUpScreen from './screens/SignUpScreen';
import ProfileScreen from './screens/ProfileScreen';
import StockScreen from './screens/StockScreen';
import SocialScreen from './screens/SocialScreen';
import AIPortfolioScreen from './screens/AIPortfolioScreen';
import PortfolioScreen from './screens/PortfolioScreen';
import PortfolioManagementScreen from './screens/PortfolioManagementScreen';
import PremiumAnalyticsScreen from './screens/PremiumAnalyticsScreen';
import SubscriptionScreen from './screens/SubscriptionScreen';
import LearningPathsScreen from './screens/LearningPathsScreen';
import OnboardingScreen, { UserProfile } from './screens/OnboardingScreen';
import DiscoverUsersScreen from './screens/DiscoverUsersScreen';
import UserProfileScreen from './screens/UserProfileScreen';
import UserPortfoliosScreen from './screens/UserPortfoliosScreen';
import UserActivityScreen from './screens/UserActivityScreen';
import MessageScreen from './screens/MessageScreen';
import TradingScreen from './screens/TradingScreen';
import AIOptionsScreen from './screens/AIOptionsScreen';
import BankAccountScreen from './screens/BankAccountScreen';
import NotificationsScreen from './screens/NotificationsScreen';
import CryptoScreen from './screens/CryptoScreen';
// Components
import BottomTabBar from './components/BottomTabBar';
import PersonalizedDashboard from './components/PersonalizedDashboard';
// Services
import UserProfileService from './services/UserProfileService';
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
const handleLogin = () => {
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
return <CryptoScreen navigation={{ navigate: navigateTo }} />;
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
return <AIOptionsScreen navigation={{ goBack: () => setCurrentScreen('home') }} />;
case 'trading':
return <TradingScreen navigateTo={navigateTo} />;
case 'bank-accounts':
return <BankAccountScreen navigateTo={navigateTo} />;
case 'notifications':
return <NotificationsScreen navigateTo={navigateTo} />;
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
{renderScreen()}
{isLoggedIn && currentScreen !== 'login' && currentScreen !== 'signup' && (
<BottomTabBar currentScreen={currentScreen} onNavigate={navigateTo} />
)}
</View>
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