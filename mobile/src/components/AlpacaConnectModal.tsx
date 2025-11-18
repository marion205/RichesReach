/**
 * AlpacaConnectModal - Pre-connect modal for Alpaca OAuth
 * Handles users with/without existing Alpaca accounts
 */
import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Linking,
  Alert,
} from 'react-native';
import { alpacaAnalytics } from '../services/alpacaAnalyticsService';

interface AlpacaConnectModalProps {
  visible: boolean;
  onClose: () => void;
  onConnect: () => void; // Callback when user confirms they have account
}

export const AlpacaConnectModal: React.FC<AlpacaConnectModalProps> = ({
  visible,
  onClose,
  onConnect,
}) => {
  const [hasAccount, setHasAccount] = useState<boolean | null>(null);

  // Track when modal is shown
  React.useEffect(() => {
    if (visible) {
      alpacaAnalytics.track('connect_modal_shown', { action: 'opened' });
    } else {
      // Reset state when modal closes
      setHasAccount(null);
    }
  }, [visible]);

  const handleCreateAccount = () => {
    // Track signup redirect
    alpacaAnalytics.track('connect_signup_redirected', { signupSource: 'modal' });
    
    // Store timestamp to detect when user returns
    try {
      // Use AsyncStorage to track signup start time
      const { AsyncStorage } = require('@react-native-async-storage/async-storage');
      AsyncStorage.setItem('alpaca_signup_started', Date.now().toString()).catch(() => {
        // Silently fail if AsyncStorage not available
      });
    } catch (e) {
      // AsyncStorage not available, continue anyway
    }
    
    // Open Alpaca signup page
    Linking.openURL('https://alpaca.markets/signup')
      .then(() => {
        Alert.alert(
          'Account Creation Started',
          'We\'ve opened Alpaca\'s signup page.\n\n' +
          '📝 Next Steps:\n' +
          '1. Complete your Alpaca account signup\n' +
          '2. Finish identity verification\n' +
          '3. Return to RichesReach and tap "Connect with Alpaca"\n\n' +
          '💡 Tip: Keep this app open or bookmark it to easily return after signup.',
          [
            {
              text: 'Got it',
              onPress: onClose,
            },
          ]
        );
      })
      .catch((err) => {
        console.error('Failed to open Alpaca signup:', err);
        alpacaAnalytics.track('connect_oauth_error', { error: 'signup_link_failed', errorCode: 'LINKING_ERROR' });
        Alert.alert('Error', 'Could not open Alpaca signup page. Please visit alpaca.markets/signup manually.');
      });
  };

  const handleHasAccount = () => {
    alpacaAnalytics.track('connect_has_account_yes');
    setHasAccount(true);
    onConnect(); // Start OAuth flow
    onClose(); // Close modal
  };

  const handleNoAccount = () => {
    alpacaAnalytics.track('connect_has_account_no');
    setHasAccount(false);
  };

  const handleBack = () => {
    setHasAccount(null);
  };

  // Don't render anything if not visible (React Native Modal best practice)
  if (!visible) {
    return null;
  }

  // Initial screen: Ask if user has account
  if (hasAccount === null) {
    return (
      <Modal
        visible={true}
        transparent={true}
        animationType="fade"
        onRequestClose={onClose}
        onShow={() => {
          // Modal is now visible on screen
        }}
        onDismiss={() => {
          // Modal was dismissed
        }}
        statusBarTranslucent={true}
        presentationStyle="overFullScreen"
      >
        <View style={styles.overlay}>
          <View style={styles.modal}>
            <Text style={styles.title}>Connect Your Alpaca Account</Text>
            <Text style={styles.subtitle}>
              To trade with RichesReach, you'll need an Alpaca brokerage account.
            </Text>
            <Text style={styles.question}>
              Do you already have an Alpaca account?
            </Text>

            <TouchableOpacity
              style={[styles.button, styles.primaryButton]}
              onPress={handleHasAccount}
            >
              <Text style={styles.buttonText}>Yes, I have an account</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              onPress={handleNoAccount}
            >
              <Text style={styles.buttonText}>No, I need to create one</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.cancelButton}
              onPress={onClose}
            >
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    );
  }

  // User doesn't have account - show signup instructions
  if (hasAccount === false) {
    return (
      <Modal
        visible={true}
        transparent
        animationType="fade"
        onRequestClose={onClose}
        presentationStyle="overFullScreen"
      >
        <View style={styles.overlay}>
          <View style={styles.modal}>
            <Text style={styles.title}>Create Alpaca Account</Text>
            <Text style={styles.description}>
              You'll need an Alpaca account to trade with RichesReach. 
              Alpaca is a commission-free brokerage that powers RichesReach.
            </Text>

            <View style={styles.stepsContainer}>
              <Text style={styles.stepsTitle}>Steps:</Text>
              <Text style={styles.step}>1. Create your Alpaca account (free, ~5 minutes)</Text>
              <Text style={styles.step}>2. Complete identity verification</Text>
              <Text style={styles.step}>3. Return to RichesReach and connect</Text>
              <Text style={styles.note}>
                ⚠️ Note: After signup, you'll need to manually return to this app to complete the connection.
              </Text>
            </View>

            <TouchableOpacity
              style={[styles.button, styles.primaryButton]}
              onPress={handleCreateAccount}
            >
              <Text style={styles.buttonText}>Create Account at Alpaca</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.backButton}
              onPress={handleBack}
            >
              <Text style={styles.backText}>← Back</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.cancelButton}
              onPress={onClose}
            >
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    );
  }

  return null;
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
    elevation: 9999,
  },
  modal: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxWidth: 400,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 10,
    zIndex: 10000,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
    textAlign: 'center',
    lineHeight: 22,
  },
  question: {
    fontSize: 18,
    color: '#333',
    marginBottom: 24,
    textAlign: 'center',
    fontWeight: '600',
  },
  description: {
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
    textAlign: 'center',
    lineHeight: 22,
  },
  stepsContainer: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 16,
    marginBottom: 24,
  },
  stepsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  step: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    lineHeight: 20,
  },
  note: {
    fontSize: 12,
    color: '#F59E0B',
    marginTop: 12,
    fontStyle: 'italic',
    lineHeight: 18,
  },
  button: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    marginBottom: 12,
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: '#f0f0f0',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  secondaryButtonText: {
    color: '#333',
  },
  backButton: {
    paddingVertical: 12,
    alignItems: 'center',
    marginBottom: 8,
  },
  backText: {
    fontSize: 16,
    color: '#007AFF',
  },
  cancelButton: {
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  cancelText: {
    fontSize: 16,
    color: '#999',
  },
});

export default AlpacaConnectModal;

