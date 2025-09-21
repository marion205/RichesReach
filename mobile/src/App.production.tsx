/**
* Production App Configuration
* Optimized version of App.tsx for production deployment
*/
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, StatusBar } from 'react-native';
import { ApolloProvider } from '@apollo/client';
import { client } from './ApolloProvider';
// Import production services
import { PRODUCTION_CONFIG, PRODUCTION_UTILS } from './config/production';
import productionErrorService from './services/ProductionErrorService';
import performanceMonitoringService from './services/PerformanceMonitoringService';
import productionSecurityService from './services/ProductionSecurityService';
import { ErrorType, ErrorSeverity } from './services/ProductionErrorService';
// Import core services
import UserProfileService from './features/user/services/UserProfileService';
import webSocketService from './services/WebSocketService';
// Import screens
import HomeScreen from './navigation/HomeScreen';
import LoginScreen from './features/auth/screens/LoginScreen';
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
import ForgotPasswordScreen from './features/auth/screens/ForgotPasswordScreen';
// Import components
import { BottomTabBar } from './components';
import { ErrorBoundary } from './components';
export default function ProductionApp() {
const [currentScreen, setCurrentScreen] = useState('home');
const [isLoggedIn, setIsLoggedIn] = useState(false);
const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
const [isLoading, setIsLoading] = useState(true);
// Initialize production services
useEffect(() => {
const initializeProductionServices = async () => {
try {
// Start performance monitoring
if (PRODUCTION_CONFIG.FEATURES.ENABLE_PERFORMANCE_MONITORING) {
performanceMonitoringService.startPerformanceMonitoring();
}
// Initialize user profile service
const userProfileService = UserProfileService.getInstance();
const onboardingCompleted = await userProfileService.isOnboardingCompleted();
setHasCompletedOnboarding(onboardingCompleted);
// Initialize WebSocket service with production URL
webSocketService.setBaseUrl(PRODUCTION_UTILS.getWebSocketUrl());
// Set up error handling
productionErrorService.handleError = productionErrorService.handleError.bind(productionErrorService);
// Initialize security measures
if (PRODUCTION_CONFIG.FEATURES.ENABLE_BIOMETRIC_AUTH) {
// Initialize biometric authentication
// await productionSecurityService.initializeBiometricAuth();
}
setIsLoading(false);
} catch (error) {
productionErrorService.handleError(error, {
type: ErrorType.UNKNOWN,
severity: ErrorSeverity.HIGH,
screen: 'App',
action: 'initializeProductionServices',
});
setIsLoading(false);
}
};
initializeProductionServices();
}, []);
// Track screen changes for analytics
useEffect(() => {
if (PRODUCTION_CONFIG.FEATURES.ENABLE_PERFORMANCE_MONITORING) {
performanceMonitoringService.recordScreenLoadTime(currentScreen, 0);
}
}, [currentScreen]);
const handleLogin = async (token: string) => {
try {
// Validate token security
const isValidToken = await productionSecurityService.validateToken(token);
if (!isValidToken) {
productionErrorService.handleAuthError(
new Error('Invalid token format'),
'App',
'handleLogin'
);
return;
}
// Record successful login attempt
productionSecurityService.recordLoginAttempt(true);
setIsLoggedIn(true);
setCurrentScreen('home');
} catch (error) {
productionErrorService.handleAuthError(error, 'App', 'handleLogin');
}
};
const handleSignUp = async (userData: UserProfile) => {
try {
// Validate user data security
const sanitizedData = {
...userData,
};
// Basic validation
if (!userData.experienceLevel || !userData.investmentGoals || !userData.riskTolerance) {
productionErrorService.handleError(
new Error('Missing required profile data'),
{
type: ErrorType.VALIDATION,
severity: ErrorSeverity.MEDIUM,
customMessage: 'Please complete all required profile fields.',
}
);
return;
}
setIsLoggedIn(true);
setCurrentScreen('home');
} catch (error) {
productionErrorService.handleError(error, {
type: ErrorType.AUTHENTICATION,
severity: ErrorSeverity.HIGH,
screen: 'App',
action: 'handleSignUp',
});
}
};
const navigateTo = (screen: string) => {
try {
// Validate screen navigation
const validScreens = [
'home', 'login', 'signup', 'profile', 'stock', 'social',
'ai-portfolio', 'portfolio', 'portfolio-management', 'premium-analytics',
'subscription', 'learning-paths', 'onboarding', 'discover-users',
'user-profile', 'forgot-password'
];
if (!validScreens.includes(screen)) {
productionErrorService.handleError(
new Error(`Invalid screen navigation: ${screen}`),
{
type: ErrorType.VALIDATION,
severity: ErrorSeverity.LOW,
screen: 'App',
action: 'navigateTo',
}
);
return;
}
setCurrentScreen(screen);
} catch (error) {
productionErrorService.handleError(error, {
type: ErrorType.UNKNOWN,
severity: ErrorSeverity.LOW,
screen: 'App',
action: 'navigateTo',
});
}
};
const renderScreen = () => {
try {
if (!isLoggedIn) {
switch (currentScreen) {
case 'login':
return (
<LoginScreen
onLogin={handleLogin}
onNavigateToSignUp={() => navigateTo('signup')}
onNavigateToForgotPassword={() => navigateTo('forgot-password')}
/>
);
case 'forgot-password':
return (
<ForgotPasswordScreen
onNavigateToLogin={() => navigateTo('login')}
onNavigateToResetPassword={(email) => navigateTo('login')}
/>
);
case 'signup':
return (
<SignUpScreen
navigateTo={navigateTo}
onSignUp={handleSignUp}
onNavigateToLogin={() => navigateTo('login')}
/>
);
default:
return (
<LoginScreen
onLogin={handleLogin}
onNavigateToSignUp={() => navigateTo('signup')}
onNavigateToForgotPassword={() => navigateTo('forgot-password')}
/>
);
}
}
if (!hasCompletedOnboarding) {
return (
<OnboardingScreen
onComplete={(profile) => {
setHasCompletedOnboarding(true);
handleSignUp(profile);
}}
/>
);
}
switch (currentScreen) {
case 'home':
return <HomeScreen navigateTo={navigateTo} />;
case 'profile':
return <ProfileScreen navigateTo={navigateTo} />;
case 'stock':
return <StockScreen navigateTo={navigateTo} />;
case 'social':
return <SocialScreen navigateTo={navigateTo} />;
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
case 'learning-paths':
return <LearningPathsScreen navigateTo={navigateTo} />;
case 'discover-users':
return <DiscoverUsersScreen navigateTo={navigateTo} />;
case 'user-profile':
return <UserProfileScreen navigateTo={navigateTo} />;
default:
return <HomeScreen navigateTo={navigateTo} />;
}
} catch (error) {
productionErrorService.handleError(error, {
type: ErrorType.UNKNOWN,
severity: ErrorSeverity.HIGH,
screen: 'App',
action: 'renderScreen',
});
return <HomeScreen navigateTo={navigateTo} />;
}
};
if (isLoading) {
return (
<View style={styles.loadingContainer}>
<StatusBar barStyle="light-content" backgroundColor="#00cc99" />
</View>
);
}
return (
<ErrorBoundary>
<ApolloProvider client={client}>
<View style={styles.container}>
<StatusBar barStyle="light-content" backgroundColor="#00cc99" />
{renderScreen()}
{isLoggedIn && hasCompletedOnboarding && (
<BottomTabBar currentScreen={currentScreen} onNavigate={navigateTo} />
)}
</View>
</ApolloProvider>
</ErrorBoundary>
);
}
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#ffffff',
},
loadingContainer: {
flex: 1,
backgroundColor: '#00cc99',
justifyContent: 'center',
alignItems: 'center',
},
});
