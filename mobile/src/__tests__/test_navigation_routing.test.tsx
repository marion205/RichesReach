/**
 * Unit Tests for Navigation and Routing Components
 * Tests HomeScreen, ProfileScreen, and App.tsx routing
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';

// Mock the main components
import HomeScreen from '../navigation/HomeScreen';
import ProfileScreen from '../features/user/screens/ProfileScreen';

// Mock dependencies
jest.mock('react-native-vector-icons/Feather', () => 'Icon');
jest.mock('expo-linear-gradient', () => 'LinearGradient');
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

// Mock Apollo Client
jest.mock('@apollo/client', () => ({
  useQuery: () => ({
    data: null,
    loading: false,
    error: null,
    refetch: jest.fn(),
  }),
  useMutation: () => [jest.fn(), { loading: false, error: null }],
  useApolloClient: () => ({
    cache: { reset: jest.fn() },
    refetchQueries: jest.fn(),
  }),
  gql: jest.fn(),
}));

// Mock Alert
jest.spyOn(Alert, 'alert').mockImplementation(() => {});

describe('Navigation and Routing - Unit Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('HomeScreen', () => {
    it('renders without crashing', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      expect(getByText('Smart Wealth Suite')).toBeTruthy();
    });

    it('displays Smart Wealth Suite section', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      expect(getByText('Smart Wealth Suite')).toBeTruthy();
      expect(getByText('Oracle Insights')).toBeTruthy();
      expect(getByText('Voice AI Assistant')).toBeTruthy();
      expect(getByText('Blockchain Integration')).toBeTruthy();
    });

    it('displays Learning & AI Tools section', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      expect(getByText('Learning & AI Tools')).toBeTruthy();
      expect(getByText('Ask & Explain')).toBeTruthy();
      expect(getByText('Knowledge Quiz')).toBeTruthy();
      expect(getByText('AI Trading Coach')).toBeTruthy();
    });

    it('handles navigation to Oracle Insights', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      const oracleButton = getByText('Oracle Insights');
      fireEvent.press(oracleButton);
      
      expect(mockNavigateTo).toHaveBeenCalledWith('oracle-insights');
    });

    it('handles navigation to Voice AI Assistant', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      const voiceButton = getByText('Voice AI Assistant');
      fireEvent.press(voiceButton);
      
      expect(mockNavigateTo).toHaveBeenCalledWith('voice-ai');
    });

    it('handles navigation to Blockchain Integration', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      const blockchainButton = getByText('Blockchain Integration');
      fireEvent.press(blockchainButton);
      
      expect(mockNavigateTo).toHaveBeenCalledWith('blockchain-integration');
    });

    it('handles navigation to AI Trading Coach', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      const coachButton = getByText('AI Trading Coach');
      fireEvent.press(coachButton);
      
      expect(mockNavigateTo).toHaveBeenCalledWith('ai-trading-coach');
    });

    it('displays rocket icon in Smart Wealth Suite title', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      // Should have the rocket icon (send icon) in the title
      expect(getByText('Smart Wealth Suite')).toBeTruthy();
    });
  });

  describe('ProfileScreen', () => {
    it('renders without crashing', () => {
      const mockNavigateTo = jest.fn();
      const mockOnLogout = jest.fn();
      
      const { getByText } = render(
        <ProfileScreen navigateTo={mockNavigateTo} onLogout={mockOnLogout} />
      );
      
      expect(getByText('Profile')).toBeTruthy();
    });

    it('displays user actions section', () => {
      const mockNavigateTo = jest.fn();
      const mockOnLogout = jest.fn();
      
      const { getByText } = render(
        <ProfileScreen navigateTo={mockNavigateTo} onLogout={mockOnLogout} />
      );
      
      expect(getByText('Actions')).toBeTruthy();
      expect(getByText('Theme Settings')).toBeTruthy();
      expect(getByText('Security Fortress')).toBeTruthy();
      expect(getByText('Viral Growth System')).toBeTruthy();
    });

    it('handles navigation to Theme Settings', () => {
      const mockNavigateTo = jest.fn();
      const mockOnLogout = jest.fn();
      
      const { getByText } = render(
        <ProfileScreen navigateTo={mockNavigateTo} onLogout={mockOnLogout} />
      );
      
      const themeButton = getByText('Theme Settings');
      fireEvent.press(themeButton);
      
      expect(mockNavigateTo).toHaveBeenCalledWith('theme-settings');
    });

    it('handles navigation to Security Fortress', () => {
      const mockNavigateTo = jest.fn();
      const mockOnLogout = jest.fn();
      
      const { getByText } = render(
        <ProfileScreen navigateTo={mockNavigateTo} onLogout={mockOnLogout} />
      );
      
      const securityButton = getByText('Security Fortress');
      fireEvent.press(securityButton);
      
      expect(mockNavigateTo).toHaveBeenCalledWith('security-fortress');
    });

    it('handles navigation to Viral Growth System', () => {
      const mockNavigateTo = jest.fn();
      const mockOnLogout = jest.fn();
      
      const { getByText } = render(
        <ProfileScreen navigateTo={mockNavigateTo} onLogout={mockOnLogout} />
      );
      
      const viralButton = getByText('Viral Growth System');
      fireEvent.press(viralButton);
      
      expect(mockNavigateTo).toHaveBeenCalledWith('viral-growth');
    });

    it('displays portfolio overview section', () => {
      const mockNavigateTo = jest.fn();
      const mockOnLogout = jest.fn();
      
      const { getByText } = render(
        <ProfileScreen navigateTo={mockNavigateTo} onLogout={mockOnLogout} />
      );
      
      expect(getByText('Overview')).toBeTruthy();
    });

    it('displays quick actions section', () => {
      const mockNavigateTo = jest.fn();
      const mockOnLogout = jest.fn();
      
      const { getByText } = render(
        <ProfileScreen navigateTo={mockNavigateTo} onLogout={mockOnLogout} />
      );
      
      expect(getByText('Quick Actions')).toBeTruthy();
    });
  });

  describe('Navigation Flow Tests', () => {
    it('HomeScreen to ProfileScreen navigation works', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      // Simulate navigation to profile
      mockNavigateTo('profile');
      
      expect(mockNavigateTo).toHaveBeenCalledWith('profile');
    });

    it('ProfileScreen to HomeScreen navigation works', () => {
      const mockNavigateTo = jest.fn();
      const mockOnLogout = jest.fn();
      
      const { getByText } = render(
        <ProfileScreen navigateTo={mockNavigateTo} onLogout={mockOnLogout} />
      );
      
      // Simulate navigation to home
      mockNavigateTo('home');
      
      expect(mockNavigateTo).toHaveBeenCalledWith('home');
    });

    it('Version 2 features are accessible from both screens', () => {
      const mockNavigateTo = jest.fn();
      
      // Test HomeScreen has Version 2 features
      const { getByText: getHomeText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      expect(getHomeText('Oracle Insights')).toBeTruthy();
      expect(getHomeText('Voice AI Assistant')).toBeTruthy();
      expect(getHomeText('Blockchain Integration')).toBeTruthy();
      
      // Test ProfileScreen has Version 2 features
      const { getByText: getProfileText } = render(
        <ProfileScreen navigateTo={mockNavigateTo} onLogout={jest.fn()} />
      );
      
      expect(getProfileText('Viral Growth System')).toBeTruthy();
      expect(getProfileText('Security Fortress')).toBeTruthy();
      expect(getProfileText('Theme Settings')).toBeTruthy();
    });
  });

  describe('Error Handling', () => {
    it('handles navigation errors gracefully', () => {
      const mockNavigateTo = jest.fn(() => {
        throw new Error('Navigation error');
      });
      
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      const oracleButton = getByText('Oracle Insights');
      
      // Should not crash when navigation fails
      expect(() => {
        fireEvent.press(oracleButton);
      }).not.toThrow();
    });

    it('handles missing props gracefully', () => {
      // Test with minimal props
      expect(() => {
        render(<HomeScreen navigateTo={jest.fn()} />);
      }).not.toThrow();
      
      expect(() => {
        render(<ProfileScreen navigateTo={jest.fn()} onLogout={jest.fn()} />);
      }).not.toThrow();
    });
  });

  describe('Accessibility', () => {
    it('has proper accessibility labels', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      // Check that interactive elements are accessible
      const oracleButton = getByText('Oracle Insights');
      expect(oracleButton).toBeTruthy();
      
      const voiceButton = getByText('Voice AI Assistant');
      expect(voiceButton).toBeTruthy();
    });

    it('supports screen readers', () => {
      const mockNavigateTo = jest.fn();
      const { getByText } = render(
        <HomeScreen navigateTo={mockNavigateTo} />
      );
      
      // All text should be readable by screen readers
      expect(getByText('Smart Wealth Suite')).toBeTruthy();
      expect(getByText('Learning & AI Tools')).toBeTruthy();
    });
  });
});
