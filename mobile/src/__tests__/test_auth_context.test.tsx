/**
 * Unit Tests for Authentication and Context Components
 * Tests AuthContext, LoginScreen, and authentication flow
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';

// Mock the authentication components
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import LoginScreen from '../features/auth/screens/LoginScreen';

// Mock dependencies
jest.mock('react-native-vector-icons/Feather', () => 'Icon');
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn();

// Mock Alert
jest.spyOn(Alert, 'alert').mockImplementation(() => {});

// Test component that uses auth context
const TestComponent = () => {
  const { user, isAuthenticated, login, logout } = useAuth();
  
  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'authenticated' : 'not-authenticated'}
      </div>
      <div data-testid="user-info">
        {user ? user.email : 'no-user'}
      </div>
      <button
        data-testid="login-btn"
        onPress={() => login('test@example.com', 'password')}
      >
        Login
      </button>
      <button
        data-testid="logout-btn"
        onPress={logout}
      >
        Logout
      </button>
    </div>
  );
};

describe('Authentication and Context - Unit Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockClear();
  });

  describe('AuthContext', () => {
    it('provides initial state correctly', () => {
      const { getByTestId } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
      
      expect(getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(getByTestId('user-info')).toHaveTextContent('no-user');
    });

    it('handles successful login', async () => {
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({
          success: true,
          token: 'mock-token',
          user: {
            id: '1',
            email: 'test@example.com',
            name: 'Test User',
            username: 'testuser',
            hasPremiumAccess: false,
          },
        }),
      };
      
      (fetch as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const { getByTestId } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
      
      const loginButton = getByTestId('login-btn');
      fireEvent.press(loginButton);
      
      await waitFor(() => {
        expect(getByTestId('auth-status')).toHaveTextContent('authenticated');
        expect(getByTestId('user-info')).toHaveTextContent('test@example.com');
      });
    });

    it('handles login failure', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        json: () => Promise.resolve({
          success: false,
          error: 'Invalid credentials',
        }),
      };
      
      (fetch as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const { getByTestId } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
      
      const loginButton = getByTestId('login-btn');
      fireEvent.press(loginButton);
      
      await waitFor(() => {
        expect(getByTestId('auth-status')).toHaveTextContent('not-authenticated');
        expect(getByTestId('user-info')).toHaveTextContent('no-user');
      });
    });

    it('handles logout correctly', async () => {
      // First login
      const mockLoginResponse = {
        ok: true,
        json: () => Promise.resolve({
          success: true,
          token: 'mock-token',
          user: {
            id: '1',
            email: 'test@example.com',
            name: 'Test User',
            username: 'testuser',
            hasPremiumAccess: false,
          },
        }),
      };
      
      (fetch as jest.Mock).mockResolvedValueOnce(mockLoginResponse);
      
      const { getByTestId } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
      
      // Login first
      const loginButton = getByTestId('login-btn');
      fireEvent.press(loginButton);
      
      await waitFor(() => {
        expect(getByTestId('auth-status')).toHaveTextContent('authenticated');
      });
      
      // Then logout
      const logoutButton = getByTestId('logout-btn');
      fireEvent.press(logoutButton);
      
      await waitFor(() => {
        expect(getByTestId('auth-status')).toHaveTextContent('not-authenticated');
        expect(getByTestId('user-info')).toHaveTextContent('no-user');
      });
    });
  });

  describe('LoginScreen', () => {
    it('renders without crashing', () => {
      const mockOnLogin = jest.fn();
      const mockOnNavigateToSignUp = jest.fn();
      const mockOnNavigateToForgotPassword = jest.fn();
      
      const { getByText } = render(
        <LoginScreen
          onLogin={mockOnLogin}
          onNavigateToSignUp={mockOnNavigateToForgotPassword}
          onNavigateToForgotPassword={mockOnNavigateToForgotPassword}
        />
      );
      
      expect(getByText('Welcome Back')).toBeTruthy();
    });

    it('has pre-filled demo credentials', () => {
      const mockOnLogin = jest.fn();
      const mockOnNavigateToSignUp = jest.fn();
      const mockOnNavigateToForgotPassword = jest.fn();
      
      const { getByDisplayValue } = render(
        <LoginScreen
          onLogin={mockOnLogin}
          onNavigateToSignUp={mockOnNavigateToSignUp}
          onNavigateToForgotPassword={mockOnNavigateToForgotPassword}
        />
      );
      
      expect(getByDisplayValue('demo@example.com')).toBeTruthy();
      expect(getByDisplayValue('demo123')).toBeTruthy();
    });

    it('handles login button press', () => {
      const mockOnLogin = jest.fn();
      const mockOnNavigateToSignUp = jest.fn();
      const mockOnNavigateToForgotPassword = jest.fn();
      
      const { getByText } = render(
        <LoginScreen
          onLogin={mockOnLogin}
          onNavigateToSignUp={mockOnNavigateToSignUp}
          onNavigateToForgotPassword={mockOnNavigateToForgotPassword}
        />
      );
      
      const loginButton = getByText('Sign In');
      fireEvent.press(loginButton);
      
      // Should attempt login with demo credentials
      expect(mockOnLogin).toHaveBeenCalled();
    });

    it('handles sign up navigation', () => {
      const mockOnLogin = jest.fn();
      const mockOnNavigateToSignUp = jest.fn();
      const mockOnNavigateToForgotPassword = jest.fn();
      
      const { getByText } = render(
        <LoginScreen
          onLogin={mockOnLogin}
          onNavigateToSignUp={mockOnNavigateToSignUp}
          onNavigateToForgotPassword={mockOnNavigateToForgotPassword}
        />
      );
      
      const signUpLink = getByText('Sign up here');
      fireEvent.press(signUpLink);
      
      expect(mockOnNavigateToSignUp).toHaveBeenCalled();
    });

    it('handles forgot password navigation', () => {
      const mockOnLogin = jest.fn();
      const mockOnNavigateToSignUp = jest.fn();
      const mockOnNavigateToForgotPassword = jest.fn();
      
      const { getByText } = render(
        <LoginScreen
          onLogin={mockOnLogin}
          onNavigateToSignUp={mockOnNavigateToSignUp}
          onNavigateToForgotPassword={mockOnNavigateToForgotPassword}
        />
      );
      
      const forgotPasswordLink = getByText('Forgot Password?');
      fireEvent.press(forgotPasswordLink);
      
      expect(mockOnNavigateToForgotPassword).toHaveBeenCalled();
    });
  });

  describe('Authentication Flow Integration', () => {
    it('complete login flow works end-to-end', async () => {
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({
          success: true,
          token: 'mock-jwt-token',
          user: {
            id: '1',
            email: 'demo@example.com',
            name: 'demo',
            username: 'demo',
            hasPremiumAccess: false,
          },
        }),
      };
      
      (fetch as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const mockOnLogin = jest.fn();
      const mockOnNavigateToSignUp = jest.fn();
      const mockOnNavigateToForgotPassword = jest.fn();
      
      const { getByText } = render(
        <LoginScreen
          onLogin={mockOnLogin}
          onNavigateToSignUp={mockOnNavigateToSignUp}
          onNavigateToForgotPassword={mockOnNavigateToForgotPassword}
        />
      );
      
      const loginButton = getByText('Sign In');
      fireEvent.press(loginButton);
      
      await waitFor(() => {
        expect(mockOnLogin).toHaveBeenCalled();
      });
    });

    it('handles network errors gracefully', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
      
      const { getByTestId } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
      
      const loginButton = getByTestId('login-btn');
      fireEvent.press(loginButton);
      
      await waitFor(() => {
        expect(getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      });
    });

    it('handles invalid token responses', async () => {
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({
          success: true,
          // Missing token
          user: {
            id: '1',
            email: 'test@example.com',
          },
        }),
      };
      
      (fetch as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const { getByTestId } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
      
      const loginButton = getByTestId('login-btn');
      fireEvent.press(loginButton);
      
      await waitFor(() => {
        expect(getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      });
    });
  });

  describe('Error Handling', () => {
    it('handles malformed JSON responses', async () => {
      const mockResponse = {
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON')),
      };
      
      (fetch as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const { getByTestId } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
      
      const loginButton = getByTestId('login-btn');
      fireEvent.press(loginButton);
      
      await waitFor(() => {
        expect(getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      });
    });

    it('handles missing user data gracefully', async () => {
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({
          success: true,
          token: 'mock-token',
          // Missing user data
        }),
      };
      
      (fetch as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const { getByTestId } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
      
      const loginButton = getByTestId('login-btn');
      fireEvent.press(loginButton);
      
      await waitFor(() => {
        expect(getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      });
    });
  });
});
