import React, { useState, useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
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

// Components
import BottomTabBar from './components/BottomTabBar';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('home');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Initialize services only if available
  useEffect(() => {
    const initializeServices = async () => {
      try {
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
            console.warn('⚠️ Push notifications not available (likely Expo Go):', notificationError.message);
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
            console.warn('⚠️ Price alert service initialization failed:', priceAlertError.message);
          }
        } else {
          console.log('📊 Price alert service not available in Expo Go');
        }
      } catch (error) {
        console.error('Error initializing services:', error);
      }
    };

    initializeServices();
  }, []);

  const navigateTo = (screen: string) => {
    setCurrentScreen(screen);
  };

  const handleLogin = () => {
    setIsLoggedIn(true);
    setCurrentScreen('home');
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setCurrentScreen('login');
  };

  const renderScreen = () => {
    if (!isLoggedIn) {
      switch (currentScreen) {
        case 'login':
          return <LoginScreen onLogin={handleLogin} onNavigateToSignUp={() => setCurrentScreen('signup')} />;
        case 'signup':
          return <SignUpScreen navigateTo={navigateTo} onSignUp={handleLogin} onNavigateToLogin={() => setCurrentScreen('login')} />;
        default:
          return <LoginScreen onLogin={handleLogin} onNavigateToSignUp={() => setCurrentScreen('signup')} />;
      }
    }

    switch (currentScreen) {
      case 'home':
        return <HomeScreen navigateTo={navigateTo} />;
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
});