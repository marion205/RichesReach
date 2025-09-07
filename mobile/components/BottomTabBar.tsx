import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';
import Feather from 'react-native-vector-icons/Feather';

interface BottomTabBarProps {
  currentScreen: string;
  onNavigate: (screen: string) => void;
}

const BottomTabBar: React.FC<BottomTabBarProps> = ({ currentScreen, onNavigate }) => {
  const tabs = [
    { id: 'home', label: 'Home', icon: 'home' },
    { id: 'stock', label: 'Stocks', icon: 'trending-up' },
    { id: 'ai-portfolio', label: 'AI Portfolio', icon: 'cpu' },
    { id: 'portfolio', label: 'Portfolio', icon: 'bar-chart-2' },
    { id: 'news', label: 'News', icon: 'globe' },
    { id: 'social', label: 'Discuss', icon: 'users' },
    { id: 'profile', label: 'Profile', icon: 'user' },
  ];

  return (
    <View style={styles.container}>
      {tabs.map((tab) => (
        <TouchableOpacity
          key={tab.id}
          style={styles.tab}
          onPress={() => onNavigate(tab.id)}
        >
          <Feather
            name={tab.icon as any}
            size={24}
            color={currentScreen === tab.id ? '#007AFF' : '#8E8E93'}
          />
          <Text style={[
            styles.tabLabel,
            currentScreen === tab.id && styles.activeTabLabel
          ]}>
            {tab.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    paddingVertical: 8,
    paddingBottom: 20, // Extra padding for home indicator
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 2,
  },
  tabLabel: {
    fontSize: 11,
    color: '#8E8E93',
    marginTop: 4,
    fontWeight: '500',
    textAlign: 'center',
    lineHeight: 14,
  },
  activeTabLabel: {
    color: '#007AFF',
    fontWeight: '600',
  },
});

export default BottomTabBar;
