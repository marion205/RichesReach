import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { ApolloProvider } from '@apollo/client';
import { client } from './src/ApolloProvider';

// Screens
import HomeScreen from './screens/HomeScreen';
import LoginScreen from './screens/LoginScreen';
import SignUpScreen from './screens/SignUpScreen';
import ProfileScreen from './screens/ProfileScreen';
import StockScreen from './screens/StockScreen';
import SocialScreen from './screens/SocialScreen';
import AIPortfolioScreen from './screens/AIPortfolioScreen';

// Components
import BottomTabBar from './components/BottomTabBar';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('home');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

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