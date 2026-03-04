/**
 * AlpacaConnectModal - Pre-connect modal for Alpaca OAuth
 * Handles users with/without existing Alpaca accounts.
 * Includes required Alpaca OAuth partner authorization disclosure before redirect.
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
  ScrollView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { alpacaAnalytics } from '../services/alpacaAnalyticsService';
import logger from '../utils/logger';

/** Partner name shown in Alpaca-required authorization disclosure */
const PARTNER_NAME = 'RichesReach';

/** Alpaca-required authorization disclosure text (compliance) */
const AUTHORIZATION_DISCLOSURE = `By allowing ${PARTNER_NAME} to access your Alpaca account, you are granting ${PARTNER_NAME} access to your account information and authorization to place transactions at your direction.\n\nAlpaca does not warrant or guarantee that ${PARTNER_NAME} will work as advertised or expected. Before authorizing, learn more about ${PARTNER_NAME}.`;

interface AlpacaConnectModalProps {
  visible: boolean;
  onClose: () => void;
  onConnect: () => void; // Callback when user accepts disclosure and starts OAuth
}

export const AlpacaConnectModal: React.FC<AlpacaConnectModalProps> = ({
  visible,
  onClose,
  onConnect,
}) => {
  const [hasAccount, setHasAccount] = useState<boolean | null>(null);
  const [showAuthorizationDisclosure, setShowAuthorizationDisclosure] = useState(false);

  // Track when modal is shown; reset state when modal closes
  React.useEffect(() => {
    if (visible) {
      alpacaAnalytics.track('connect_modal_shown', { action: 'opened' });
    } else {
      setHasAccount(null);
      setShowAuthorizationDisclosure(false);
    }
  }, [visible]);

  const handleCreateAccount = () => {
    // Track signup redirect
    alpacaAnalytics.track('connect_signup_redirected', { signupSource: 'modal' });
    
    // Store timestamp to detect when user returns
    AsyncStorage.setItem('alpaca_signup_started', Date.now().toString()).catch((error) => {
      logger.error('Failed to store signup timestamp:', error);
      // Continue anyway - this is not critical
    });
    
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
        logger.error('Failed to open Alpaca signup:', err);
        alpacaAnalytics.track('connect_oauth_error', { error: 'signup_link_failed', errorCode: 'LINKING_ERROR' });
        Alert.alert('Error', 'Could not open Alpaca signup page. Please visit alpaca.markets/signup manually.');
      });
  };

  const handleHasAccount = () => {
    alpacaAnalytics.track('connect_has_account_yes');
    setHasAccount(true);
    setShowAuthorizationDisclosure(true);
    // Do not call onConnect() yet — show authorization disclosure first (Alpaca compliance)
  };

  const handleDisclosureAccept = () => {
    alpacaAnalytics.track('connect_authorization_disclosure_accepted');
    setShowAuthorizationDisclosure(false);
    onConnect();
    onClose();
  };

  const handleDisclosureDeny = () => {
    alpacaAnalytics.track('connect_authorization_disclosure_denied');
    setShowAuthorizationDisclosure(false);
    setHasAccount(null);
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

  // Alpaca-required authorization disclosure (before OAuth redirect)
  if (hasAccount === true && showAuthorizationDisclosure) {
    return (
      <Modal
        visible={true}
        transparent
        animationType="fade"
        onRequestClose={handleDisclosureDeny}
        presentationStyle="overFullScreen"
      >
        <View style={styles.overlay}>
          <View style={[styles.modal, styles.disclosureModal]}>
            <Text style={styles.disclosureTitle}>Authorize {PARTNER_NAME}</Text>
            <ScrollView
              style={styles.disclosureScroll}
              contentContainerStyle={styles.disclosureScrollContent}
              showsVerticalScrollIndicator={true}
            >
              <Text style={styles.disclosureBody}>{AUTHORIZATION_DISCLOSURE}</Text>
            </ScrollView>
            <View style={styles.disclosureButtons}>
              <TouchableOpacity
                style={[styles.button, styles.denyButton]}
                onPress={handleDisclosureDeny}
              >
                <Text style={styles.denyButtonText}>DENY</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.button, styles.acceptButton]}
                onPress={handleDisclosureAccept}
              >
                <Text style={styles.buttonText}>ACCEPT</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    );
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
  // Authorization disclosure (Alpaca OAuth partner compliance)
  disclosureModal: {
    maxHeight: '85%',
  },
  disclosureTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 16,
    textAlign: 'center',
  },
  disclosureScroll: {
    maxHeight: 220,
  },
  disclosureScrollContent: {
    paddingVertical: 8,
  },
  disclosureBody: {
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
    textAlign: 'center',
  },
  disclosureButtons: {
    flexDirection: 'row',
    marginTop: 20,
    gap: 12,
  },
  denyButton: {
    flex: 1,
    backgroundColor: '#f0f0f0',
    borderWidth: 1,
    borderColor: '#ccc',
  },
  denyButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  acceptButton: {
    flex: 1,
    backgroundColor: '#007AFF',
  },
});

export default AlpacaConnectModal;

