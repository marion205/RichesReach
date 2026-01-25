import React, { useRef, useEffect } from 'react';
import { View, TouchableOpacity, Text, StyleSheet, StatusBar, DeviceEventEmitter } from 'react-native';
import Feather from 'react-native-vector-icons/Feather';
import { globalNavigate } from '../../navigation/NavigationService';
import logger from '../../utils/logger';

interface TopHeaderProps {
  currentScreen: string;
  onNavigate: (screen: string) => void;
  title?: string;
  navigateTo?: (screen: string, params?: any) => void; // Custom navigation function for shell screens
  showBackButton?: boolean; // Show back button instead of default buttons
  onBack?: () => void; // Back button handler
  hideMicButton?: boolean; // Hide mic button
  hideProfileButton?: boolean; // Hide profile button
}

const TopHeader: React.FC<TopHeaderProps> = ({ 
  currentScreen, 
  onNavigate, 
  title, 
  navigateTo,
  showBackButton = false,
  onBack,
  hideMicButton = false,
  hideProfileButton = false,
}) => {
  const navigationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (navigationTimeoutRef.current) {
        clearTimeout(navigationTimeoutRef.current);
        navigationTimeoutRef.current = null;
      }
    };
  }, []);
  
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
        {showBackButton && onBack ? (
          <TouchableOpacity
            style={styles.backButton}
            onPress={onBack}
            accessibilityLabel="Back"
          >
            <Feather name="arrow-left" size={24} color="#1C1C1E" />
          </TouchableOpacity>
        ) : null}
        <Text style={[styles.title, showBackButton && styles.titleWithBack]}>{getScreenTitle()}</Text>
        <View style={styles.rightSection}>
          {!hideMicButton && (
            <TouchableOpacity
              style={styles.micButton}
              onPress={() => {
                logger.log('🎤 [TopHeader] Microphone button pressed');
                
                // Always emit the event - don't wait for navigation
                // The event listener in HomeScreen will handle it regardless of current screen
                logger.log('🎤 [TopHeader] Emitting calm_goal_mic event immediately');
                DeviceEventEmitter.emit('calm_goal_mic');
                
                // Try to navigate to home (but don't block on it)
                // Use a small delay to ensure event is emitted first
                if (navigationTimeoutRef.current) {
                  clearTimeout(navigationTimeoutRef.current);
                }
                navigationTimeoutRef.current = setTimeout(() => {
                  try {
                    // Try custom navigateTo first (for shell screens), then globalNavigate, then onNavigate
                    if (navigateTo) {
                      logger.log('🎤 [TopHeader] Using navigateTo to go to home');
                      navigateTo('home');
                    } else {
                      try { 
                        logger.log('🎤 [TopHeader] Using globalNavigate to go to Home');
                        globalNavigate('Home'); 
                      } catch (navError) {
                        logger.warn('🎤 [TopHeader] globalNavigate failed, trying onNavigate:', navError);
                        try {
                          onNavigate('home');
                        } catch (onNavError) {
                          logger.warn('🎤 [TopHeader] onNavigate also failed:', onNavError);
                          // Navigation failed, but event was already emitted, so it's okay
                        }
                      }
                    }
                  } catch (error) {
                    logger.warn('🎤 [TopHeader] Navigation error (non-critical):', error);
                    // Navigation failed, but event was already emitted, so it's okay
                  }
                  navigationTimeoutRef.current = null;
                }, 100);
              }}
              accessibilityLabel="Voice"
            >
              <Feather name="mic" size={20} color="#1C1C1E" />
            </TouchableOpacity>
          )}
          {!hideProfileButton && (
            <TouchableOpacity
              style={styles.profileButton}
              onPress={() => {
                // Try custom navigateTo first (for shell screens), then globalNavigate, then onNavigate
                if (navigateTo) {
                  // For shell screens, navigate directly to profile
                  navigateTo('profile');
                } else {
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
                }
              }}
            >
              <Feather
                name="user"
                size={24}
                color={currentScreen === 'profile' ? '#007AFF' : '#8E8E93'}
              />
            </TouchableOpacity>
          )}
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
  backButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#F2F2F7',
    marginRight: 12,
  },
  titleWithBack: {
    marginLeft: 0,
  },
});

export default TopHeader;
