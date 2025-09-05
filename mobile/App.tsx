import React, { useState, useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { ApolloProvider } from '@apollo/client';
import { client } from './src/ApolloProvider';
import pushNotificationService from './services/PushNotificationService';
import priceAlertService from './services/PriceAlertService';

// Screens
import HomeScreen from './screens/HomeScreen';
import LoginScreen from './screens/LoginScreen';
import SignUpScreen from './screens/SignUpScreen';
import ProfileScreen from './screens/ProfileScreen';
import StockScreen from './screens/StockScreen';
import SocialScreen from './screens/SocialScreen';
import AIPortfolioScreen from './screens/AIPortfolioScreen';
import PortfolioScreen from './screens/PortfolioScreen';

// Components
import BottomTabBar from './components/BottomTabBar';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('home');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Initialize push notifications and price alerts
  useEffect(() => {
    const initializeServices = async () => {
      try {
        // Initialize push notifications
        const notificationsEnabled = await pushNotificationService.initialize();
        if (notificationsEnabled) {
          console.log('📱 Push notifications initialized successfully');
        }

        // Initialize price alert service
        await priceAlertService.initialize();
        console.log('📊 Price alert service initialized successfully');

        // Set up notification listeners
        const { notificationListener, responseListener } = pushNotificationService.setupNotificationListeners();

        // Cleanup listeners on unmount
        return () => {
          pushNotificationService.removeNotificationListeners(notificationListener, responseListener);
        };
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