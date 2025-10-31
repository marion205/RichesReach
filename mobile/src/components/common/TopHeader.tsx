import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet, StatusBar, DeviceEventEmitter } from 'react-native';
import Feather from 'react-native-vector-icons/Feather';
import { globalNavigate } from '../../navigation/NavigationService';

interface TopHeaderProps {
  currentScreen: string;
  onNavigate: (screen: string) => void;
  title?: string;
}

const TopHeader: React.FC<TopHeaderProps> = ({ currentScreen, onNavigate, title }) => {
  const getScreenTitle = () => {
    if (title) return title;
    
    switch (currentScreen) {
      case 'home': return 'RichesReach';
      case 'stock': return 'Stocks';
      case 'crypto': return 'Crypto';
      case 'ai-portfolio': return 'AI Portfolio';
      case 'trading': return 'Trading';
      case 'portfolio': return 'Portfolio';
      case 'social': return 'Community';
      case 'tutor': return 'Learn';
      case 'ai-options': return 'AI Options';
      case 'options-copilot': return 'Advanced';
      case 'scan-playbook': return 'Scan Details';
      default: return 'RichesReach';
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <View style={styles.content}>
        <Text style={styles.title}>{getScreenTitle()}</Text>
        <View style={styles.rightSection}>
          <TouchableOpacity
            style={styles.micButton}
            onPress={() => {
              try { globalNavigate('Home'); } catch {}
              setTimeout(() => DeviceEventEmitter.emit('calm_goal_mic'), 150);
            }}
            accessibilityLabel="Voice"
          >
            <Feather name="mic" size={20} color="#1C1C1E" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.profileButton}
            onPress={() => {
              try {
                // Profile is in HomeStack, use nested navigation
                globalNavigate('Home', { screen: 'Profile' });
              } catch {
                try {
                  globalNavigate('Profile');
                } catch {
                  onNavigate('profile');
                }
              }
            }}
          >
            <Feather
              name="user"
              size={24}
              color={currentScreen === 'profile' ? '#007AFF' : '#8E8E93'}
            />
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    paddingTop: 44, // Status bar height
    paddingBottom: 12,
    paddingHorizontal: 16,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000000',
    flex: 1,
  },
  rightSection: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  micButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#F2F2F7',
    marginRight: 8,
  },
  profileButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#F2F2F7',
  },
});

export default TopHeader;
