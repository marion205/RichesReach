/**
 * Alpaca Connect Flow Test Scenarios
 * Tests both "has account" and "needs account" scenarios
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import AlpacaConnectModal from '../../../components/AlpacaConnectModal';
import { alpacaAnalytics } from '../../../services/alpacaAnalyticsService';

// Mock Linking
jest.mock('react-native/Libraries/Linking/Linking', () => ({
  openURL: jest.fn(() => Promise.resolve(true)),
}));

// Mock Alert
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Alert: {
      alert: jest.fn(),
    },
  };
});

describe('AlpacaConnectModal - Test Scenarios', () => {
  beforeEach(() => {
    alpacaAnalytics.clear();
    jest.clearAllMocks();
  });

  describe('Scenario 1: User Has Alpaca Account', () => {
    it('should show initial modal asking if user has account', () => {
      const onConnect = jest.fn();
      const onClose = jest.fn();
      
      const { getByText } = render(
        <AlpacaConnectModal
          visible={true}
          onClose={onClose}
          onConnect={onConnect}
        />
      );

      expect(getByText('Connect Your Alpaca Account')).toBeTruthy();
      expect(getByText('Do you already have an Alpaca account?')).toBeTruthy();
    });

    it('should trigger OAuth flow when user selects "Yes, I have an account"', () => {
      const onConnect = jest.fn();
      const onClose = jest.fn();
      
      const { getByText } = render(
        <AlpacaConnectModal
          visible={true}
          onClose={onClose}
          onConnect={onConnect}
        />
      );

      const yesButton = getByText('Yes, I have an account');
      fireEvent.press(yesButton);

      expect(onConnect).toHaveBeenCalled();
      expect(alpacaAnalytics.getEvents().some(e => e.event === 'connect_has_account_yes')).toBe(true);
    });

    it('should track analytics events for has-account flow', () => {
      const onConnect = jest.fn();
      const onClose = jest.fn();
      
      const { getByText } = render(
        <AlpacaConnectModal
          visible={true}
          onClose={onClose}
          onConnect={onConnect}
        />
      );

      const yesButton = getByText('Yes, I have an account');
      fireEvent.press(yesButton);

      const events = alpacaAnalytics.getEvents();
      expect(events.some(e => e.event === 'connect_has_account_yes')).toBe(true);
    });
  });

  describe('Scenario 2: User Needs to Create Account', () => {
    it('should show signup instructions when user selects "No, I need to create one"', () => {
      const onConnect = jest.fn();
      const onClose = jest.fn();
      
      const { getByText, queryByText } = render(
        <AlpacaConnectModal
          visible={true}
          onClose={onClose}
          onConnect={onConnect}
        />
      );

      const noButton = getByText('No, I need to create one');
      fireEvent.press(noButton);

      // Should show signup screen
      expect(getByText('Create Alpaca Account')).toBeTruthy();
      expect(getByText('Steps:')).toBeTruthy();
      expect(queryByText('Do you already have an Alpaca account?')).toBeNull();
    });

    it('should open Alpaca signup page when user taps "Create Account at Alpaca"', async () => {
      const Linking = require('react-native/Libraries/Linking/Linking');
      const onConnect = jest.fn();
      const onClose = jest.fn();
      
      const { getByText } = render(
        <AlpacaConnectModal
          visible={true}
          onClose={onClose}
          onConnect={onConnect}
        />
      );

      // Navigate to signup screen
      const noButton = getByText('No, I need to create one');
      fireEvent.press(noButton);

      // Tap create account button
      const createButton = getByText('Create Account at Alpaca');
      fireEvent.press(createButton);

      await waitFor(() => {
        expect(Linking.openURL).toHaveBeenCalledWith('https://alpaca.markets/signup');
      });
    });

    it('should track analytics for no-account flow', () => {
      const onConnect = jest.fn();
      const onClose = jest.fn();
      
      const { getByText } = render(
        <AlpacaConnectModal
          visible={true}
          onClose={onClose}
          onConnect={onConnect}
        />
      );

      const noButton = getByText('No, I need to create one');
      fireEvent.press(noButton);

      const events = alpacaAnalytics.getEvents();
      expect(events.some(e => e.event === 'connect_has_account_no')).toBe(true);
    });

    it('should allow user to go back from signup screen', () => {
      const onConnect = jest.fn();
      const onClose = jest.fn();
      
      const { getByText } = render(
        <AlpacaConnectModal
          visible={true}
          onClose={onClose}
          onConnect={onConnect}
        />
      );

      // Navigate to signup
      const noButton = getByText('No, I need to create one');
      fireEvent.press(noButton);

      // Go back
      const backButton = getByText('← Back');
      fireEvent.press(backButton);

      // Should be back at initial screen
      expect(getByText('Do you already have an Alpaca account?')).toBeTruthy();
    });
  });

  describe('Analytics Tracking', () => {
    it('should track connect_initiated event', () => {
      alpacaAnalytics.track('connect_initiated', { source: 'order_placement' });
      
      const events = alpacaAnalytics.getEvents();
      expect(events.length).toBe(1);
      expect(events[0].event).toBe('connect_initiated');
      expect(events[0].metadata?.source).toBe('order_placement');
    });

    it('should calculate success rate correctly', () => {
      alpacaAnalytics.track('connect_initiated');
      alpacaAnalytics.track('connect_oauth_started');
      alpacaAnalytics.track('connect_oauth_success');
      
      const successRate = alpacaAnalytics.getSuccessRate();
      expect(successRate).toBe(1); // 1 success / 1 initiated = 100%
    });

    it('should provide analytics summary', () => {
      alpacaAnalytics.track('connect_initiated');
      alpacaAnalytics.track('connect_has_account_yes');
      alpacaAnalytics.track('connect_has_account_no');
      alpacaAnalytics.track('connect_oauth_started');
      alpacaAnalytics.track('connect_oauth_success');
      
      const summary = alpacaAnalytics.getSummary();
      
      expect(summary.totalAttempts).toBe(1);
      expect(summary.hasAccountCount).toBe(1);
      expect(summary.noAccountCount).toBe(1);
      expect(summary.oauthStarted).toBe(1);
      expect(summary.oauthSuccess).toBe(1);
      expect(summary.successRate).toBe(1);
    });
  });

  describe('Error Scenarios', () => {
    it('should handle OAuth errors gracefully', () => {
      alpacaAnalytics.track('connect_oauth_error', {
        error: 'access_denied',
        errorCode: 'OAUTH_DENIED',
      });
      
      const events = alpacaAnalytics.getEvents();
      const errorEvent = events.find(e => e.event === 'connect_oauth_error');
      
      expect(errorEvent).toBeTruthy();
      expect(errorEvent?.metadata?.error).toBe('access_denied');
      expect(errorEvent?.metadata?.errorCode).toBe('OAUTH_DENIED');
    });

    it('should track failed connections', () => {
      alpacaAnalytics.track('connect_initiated');
      alpacaAnalytics.track('connect_failed', { reason: 'network_error' });
      
      const summary = alpacaAnalytics.getSummary();
      expect(summary.successRate).toBe(0); // 0 success / 1 initiated
    });
  });
});

/**
 * Manual Test Scenarios (for QA/testing)
 * 
 * These should be tested manually in the app:
 * 
 * 1. Happy Path - Has Account:
 *    - Open TradingScreen
 *    - Try to place order without account
 *    - Modal appears
 *    - Select "Yes, I have an account"
 *    - OAuth flow starts
 *    - Complete OAuth
 *    - Account linked successfully
 * 
 * 2. Happy Path - Needs Account:
 *    - Open TradingScreen
 *    - Try to place order without account
 *    - Modal appears
 *    - Select "No, I need to create one"
 *    - Signup instructions shown
 *    - Tap "Create Account at Alpaca"
 *    - Browser opens to Alpaca signup
 *    - User creates account
 *    - User returns to app
 *    - User taps "Connect with Alpaca" again
 *    - OAuth flow starts
 *    - Account linked successfully
 * 
 * 3. Error - OAuth Denied:
 *    - Start OAuth flow
 *    - User denies access
 *    - Error message shown
 *    - Analytics tracks error
 * 
 * 4. Error - No Callback:
 *    - User creates account mid-OAuth
 *    - Callback doesn't fire
 *    - Error handling shows message
 *    - User can retry
 * 
 * 5. Analytics Verification:
 *    - Complete full flow
 *    - Check analytics summary
 *    - Verify all events tracked
 *    - Check success rate calculation
 */

