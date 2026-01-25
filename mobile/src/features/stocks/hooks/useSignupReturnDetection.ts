/**
 * Hook to detect when user returns from Alpaca signup
 * Checks if user recently started signup and prompts them to connect
 */
import { useEffect, useState } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import { Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { alpacaAnalytics } from '../../../services/alpacaAnalyticsService';
import logger from '../../../utils/logger';

const SIGNUP_STARTED_KEY = 'alpaca_signup_started';
const SIGNUP_PROMPTED_KEY = 'alpaca_signup_prompted';
const SIGNUP_TIMEOUT_MS = 24 * 60 * 60 * 1000; // 24 hours

interface UseSignupReturnDetectionOptions {
  hasAlpacaAccount: boolean;
  onPromptConnect: () => void;
  enabled?: boolean;
}

export const useSignupReturnDetection = ({
  hasAlpacaAccount,
  onPromptConnect,
  enabled = true,
}: UseSignupReturnDetectionOptions) => {
  const [hasChecked, setHasChecked] = useState(false);

  useEffect(() => {
    if (!enabled || hasAlpacaAccount || hasChecked) {
      return;
    }

    const checkSignupReturn = async () => {
      try {
        // Check if user started signup
        const signupStarted = await AsyncStorage.getItem(SIGNUP_STARTED_KEY);
        if (!signupStarted) {
          setHasChecked(true);
          return;
        }

        const signupTime = parseInt(signupStarted, 10);
        const now = Date.now();
        const timeSinceSignup = now - signupTime;

        // Only prompt if signup was recent (within 24 hours)
        if (timeSinceSignup > SIGNUP_TIMEOUT_MS) {
          // Clean up old signup marker
          await AsyncStorage.removeItem(SIGNUP_STARTED_KEY);
          await AsyncStorage.removeItem(SIGNUP_PROMPTED_KEY);
          setHasChecked(true);
          return;
        }

        // Check if we've already prompted
        const alreadyPrompted = await AsyncStorage.getItem(SIGNUP_PROMPTED_KEY);
        if (alreadyPrompted) {
          setHasChecked(true);
          return;
        }

        // User returned from signup - track detection
        alpacaAnalytics.track('alpaca_signup_return_detected', {
          timeSinceSignup: Math.floor(timeSinceSignup / 60000), // minutes
        } as any);

        // Show welcoming prompt
        alpacaAnalytics.track('alpaca_connect_prompt_shown', {
          source: 'signup_return',
        });

        const minutesAgo = Math.floor(timeSinceSignup / 60000);
        Alert.alert(
          'Welcome back! 🎉',
          'Looks like you just finished creating your Alpaca account. Ready to connect it now and start trading?',
          [
            {
              text: 'Not yet',
              style: 'cancel',
              onPress: async () => {
                // Track abandonment
                alpacaAnalytics.track('alpaca_signup_abandoned', {
                  timeSinceSignup: minutesAgo,
                  reason: 'not_yet',
                } as any);
                // Mark as prompted but don't remove signup marker (they might come back)
                await AsyncStorage.setItem(SIGNUP_PROMPTED_KEY, 'true');
                setHasChecked(true);
              },
            },
            {
              text: 'Yes, connect now!',
              onPress: async () => {
                // Track completion
                alpacaAnalytics.track('alpaca_connect_completed', {
                  from: 'signup_return',
                  timeSinceSignup: minutesAgo,
                } as any);
                // Clear signup markers
                await AsyncStorage.removeItem(SIGNUP_STARTED_KEY);
                await AsyncStorage.removeItem(SIGNUP_PROMPTED_KEY);
                setHasChecked(true);
                // Trigger connect flow
                onPromptConnect();
              },
            },
          ]
        );
      } catch (error) {
        logger.error('Error checking signup return:', error);
        setHasChecked(true);
      }
    };

    // Check immediately
    checkSignupReturn();

    // Also check when app comes to foreground
    const subscription = AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      if (nextAppState === 'active' && !hasAlpacaAccount) {
        checkSignupReturn();
      }
    });

    return () => {
      subscription.remove();
    };
  }, [enabled, hasAlpacaAccount, hasChecked, onPromptConnect]);
};

