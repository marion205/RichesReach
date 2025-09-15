import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ApolloProvider } from '@apollo/client';
import { client } from './src/ApolloProvider';
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
import AIOptionsScreen from './screens/AIOptionsScreen';
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
console.log(' Price alert service initialized successfully');
} catch (priceAlertError) {
console.warn(' Price alert service initialization failed:', priceAlertError instanceof Error ? priceAlertError.message : 'Unknown error');
}
} else {
console.log(' Price alert service not available in Expo Go');
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
console.log(' navigateTo called:', { screen, params });
console.log(' Current currentScreen before change:', currentScreen);
  if (screen === 'user-profile' && params?.userId) {
    const newScreen = `user-profile-${params.userId}`;
    console.log(' Setting currentScreen to:', newScreen);
    setCurrentScreen(newScreen);
  } else if (screen === 'user-portfolios' && params?.userId) {
    const newScreen = `user-portfolios-${params.userId}`;
    console.log(' Setting currentScreen to:', newScreen);
    setCurrentScreen(newScreen);
  } else if (screen === 'user-activity' && params?.userId) {
    const newScreen = `user-activity-${params.userId}`;
    console.log(' Setting currentScreen to:', newScreen);
    setCurrentScreen(newScreen);
  } else if (screen === 'message-user' && params?.userId) {
    const newScreen = `message-user-${params.userId}`;
    console.log(' Setting currentScreen to:', newScreen);
    setCurrentScreen(newScreen);
  } else {
console.log(' Setting currentScreen to:', screen);
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
const handleLogout = () => {
setIsLoggedIn(false);
setCurrentScreen('login');
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
console.log(' renderScreen switch - currentScreen:', currentScreen);
switch (currentScreen) {
case 'home':
return <HomeScreen navigateTo={navigateTo} />;
case 'onboarding':
return <OnboardingScreen onComplete={handleOnboardingComplete} />;
case 'profile':
return <ProfileScreen navigateTo={navigateTo} onLogout={handleLogout} />;
case 'stock':
return <StockScreen navigateTo={navigateTo} />;
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
      console.log(' user-profile case - userId:', userId);
      return <UserProfileScreen userId={userId} onNavigate={navigateTo} />;
    case 'user-portfolios':
      // Extract userId from currentScreen if it's in format 'user-portfolios-{userId}'
      const portfolioUserId = currentScreen.startsWith('user-portfolios-') 
        ? currentScreen.replace('user-portfolios-', '') 
        : 'default-user';
      console.log(' user-portfolios case - userId:', portfolioUserId);
      return <UserPortfoliosScreen userId={portfolioUserId} onNavigate={navigateTo} />;
    case 'user-activity':
      // Extract userId from currentScreen if it's in format 'user-activity-{userId}'
      const activityUserId = currentScreen.startsWith('user-activity-') 
        ? currentScreen.replace('user-activity-', '') 
        : 'default-user';
      console.log(' user-activity case - userId:', activityUserId);
      return <UserActivityScreen userId={activityUserId} onNavigate={navigateTo} />;
    case 'message-user':
      // Extract userId from currentScreen if it's in format 'message-user-{userId}'
      const messageUserId = currentScreen.startsWith('message-user-') 
        ? currentScreen.replace('message-user-', '') 
        : 'default-user';
      console.log(' message-user case - userId:', messageUserId);
      return <MessageScreen userId={messageUserId} onNavigate={navigateTo} />;
case 'social-feed':
return <SocialScreen onNavigate={navigateTo} />;
case 'ai-options':
return <AIOptionsScreen navigation={{ goBack: () => setCurrentScreen('home') }} />;
    default:
      // Handle user-profile and user-portfolios with userId pattern
      console.log(' default case - currentScreen:', currentScreen);
      if (currentScreen.startsWith('user-profile-')) {
        const userId = currentScreen.replace('user-profile-', '');
        console.log(' default case - userId:', userId);
        return <UserProfileScreen userId={userId} onNavigate={navigateTo} />;
      }
      if (currentScreen.startsWith('user-portfolios-')) {
        const userId = currentScreen.replace('user-portfolios-', '');
        console.log(' default case - portfolio userId:', userId);
        return <UserPortfoliosScreen userId={userId} onNavigate={navigateTo} />;
      }
      if (currentScreen.startsWith('user-activity-')) {
        const userId = currentScreen.replace('user-activity-', '');
        console.log(' default case - activity userId:', userId);
        return <UserActivityScreen userId={userId} onNavigate={navigateTo} />;
      }
      if (currentScreen.startsWith('message-user-')) {
        const userId = currentScreen.replace('message-user-', '');
        console.log(' default case - message userId:', userId);
        return <MessageScreen userId={userId} onNavigate={navigateTo} />;
      }
      console.log(' default case - returning HomeScreen');
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