import React, { useState } from 'react';
import ApolloWrapper from './ApolloProvider';
import LoginScreen from './screens/LoginScreen';
import SignUpScreen from './screens/SignUpScreen';
import HomeScreen from './screens/HomeScreen';
import ProfileScreen from './screens/ProfileScreen';
import DiscoverUsersScreen from './screens/DiscoverUsersScreen';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('Login');
  const [navigationData, setNavigationData] = useState({});
  const [navigationHistory, setNavigationHistory] = useState<string[]>([]);

  const navigateTo = (screen: string, data: any = {}) => {
    if (screen === 'Back') {
      // Handle back navigation
      if (navigationHistory.length > 0) {
        const previousScreen = navigationHistory[navigationHistory.length - 1];
        const newHistory = navigationHistory.slice(0, -1);
        setNavigationHistory(newHistory);
        setCurrentScreen(previousScreen);
        setNavigationData({});
        return;
      }
      return;
    }
    
    // Add current screen to history before navigating
    if (currentScreen !== 'Login') {
      setNavigationHistory([...navigationHistory, currentScreen]);
    }
    
    setCurrentScreen(screen);
    setNavigationData(data);
  };

  const renderScreen = () => {
    switch (currentScreen) {
      case 'Login':
        return <LoginScreen navigateTo={navigateTo} />;
      case 'SignUp':
        return <SignUpScreen navigateTo={navigateTo} />;
      case 'Home':
        return <HomeScreen navigateTo={navigateTo} data={navigationData} />;
      case 'Profile':
        return <ProfileScreen navigateTo={navigateTo} data={navigationData} />;
      case 'DiscoverUsers':
        return <DiscoverUsersScreen navigateTo={navigateTo} data={navigationData} />;
      default:
        return <LoginScreen navigateTo={navigateTo} />;
    }
  };

  return (
    <ApolloWrapper>
      {renderScreen()}
    </ApolloWrapper>
  );
}