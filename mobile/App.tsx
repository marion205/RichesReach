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
import NewsScreen from './screens/NewsScreen';
import OnboardingScreen, { UserProfile } from './screens/OnboardingScreen';

// Components
import BottomTabBar from './components/BottomTabBar';
import PersonalizedDashboard from './components/PersonalizedDashboard';

// Services
import UserProfileService from './services/UserProfileService';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('home');
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
              console.log('📱 Push notifications initialized successfully');
              
              // Set up notification listeners
              const { notificationListener, responseListener } = pushNotificationService.setupNotificationListeners();

              // Cleanup listeners on unmount
              return () => {
                pushNotificationService.removeNotificationListeners(notificationListener, responseListener);
              };
            }
          } catch (notificationError) {
            console.warn('⚠️ Push notifications not available (likely Expo Go):', notificationError instanceof Error ? notificationError.message : 'Unknown error');
          }
        } else {
          console.log('📱 Push notification service not available in Expo Go');
        }

        // Initialize price alert service
        if (priceAlertService) {
          try {
            await priceAlertService.initialize();
            console.log('📊 Price alert service initialized successfully');
          } catch (priceAlertError) {
            console.warn('⚠️ Price alert service initialization failed:', priceAlertError instanceof Error ? priceAlertError.message : 'Unknown error');
          }
        } else {
          console.log('📊 Price alert service not available in Expo Go');
        }
      } catch (error) {
        console.error('Error initializing services:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeServices();
  }, []);

  const navigateTo = (screen: string) => {
    setCurrentScreen(screen);
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
          return <LoginScreen onLogin={handleLogin} onNavigateToSignUp={() => setCurrentScreen('signup')} />;
        case 'signup':
          return <SignUpScreen navigateTo={navigateTo} onSignUp={handleSignUp} onNavigateToLogin={() => setCurrentScreen('login')} />;
        default:
          return <LoginScreen onLogin={handleLogin} onNavigateToSignUp={() => setCurrentScreen('signup')} />;
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
        return <SocialScreen />;
      case 'learning-paths':
        return <LearningPathsScreen />;
      case 'news':
        return <NewsScreen />;
      default:
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