/**
 * Crypto Agreement Screen
 * Displays Alpaca's crypto trading agreement and handles signing flow
 * Required before users can trade cryptocurrency via Alpaca Crypto
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { useMutation, useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../../contexts/AuthContext';

// GraphQL Queries and Mutations
const GET_CRYPTO_AGREEMENT_STATUS = gql`
  query GetCryptoAgreementStatus($userId: Int!) {
    cryptoAgreementStatus(userId: $userId) {
      isSigned
      signedAt
      agreementVersion
      regionSupported
      restrictedReason
    }
  }
`;

const VALIDATE_CRYPTO_REGION = gql`
  query ValidateCryptoRegion($state: String!) {
    validateCryptoRegion(state: $state) {
      isSupported
      reason
    }
  }
`;

const SIGN_CRYPTO_AGREEMENT = gql`
  mutation SignCryptoAgreement($userId: Int!) {
    signCryptoAgreement(userId: $userId) {
      success
      error
      signedAt
    }
  }
`;

interface CryptoAgreementScreenProps {
  navigation?: any;
  onAgreementSigned?: () => void;
  onClose?: () => void;
}

const CryptoAgreementScreen: React.FC<CryptoAgreementScreenProps> = ({
  navigation,
  onAgreementSigned,
  onClose,
}) => {
  const { user } = useAuth();
  const userId = parseInt(user?.id ?? '0', 10);
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false);
  const [isSigning, setIsSigning] = useState(false);
  const [userState, setUserState] = useState<string>(''); // Should come from user profile

  // Get agreement status
  const { data: agreementData, loading: agreementLoading, refetch: refetchAgreement } = useQuery(
    GET_CRYPTO_AGREEMENT_STATUS,
    {
      variables: { userId },
      skip: userId <= 0,
      errorPolicy: 'all',
    }
  );

  // Validate region
  const { data: regionData, loading: regionLoading } = useQuery(VALIDATE_CRYPTO_REGION, {
    variables: { state: userState },
    skip: !userState,
    errorPolicy: 'all',
  });

  const [signAgreement] = useMutation(SIGN_CRYPTO_AGREEMENT);

  const agreementStatus = agreementData?.cryptoAgreementStatus;
  const regionValidation = regionData?.validateCryptoRegion;
  const isRegionSupported = regionValidation?.isSupported ?? true; // Default to true if not checked
  const isAgreementSigned = agreementStatus?.isSigned ?? false;

  // Handle scroll to bottom (required to enable sign button)
  const handleScroll = (event: any) => {
    const { layoutMeasurement, contentOffset, contentSize } = event.nativeEvent;
    const paddingToBottom = 20;
    const isAtBottom =
      layoutMeasurement.height + contentOffset.y >= contentSize.height - paddingToBottom;
    if (isAtBottom) {
      setHasScrolledToBottom(true);
    }
  };

  // Handle agreement signing
  const handleSignAgreement = async () => {
    if (!isRegionSupported) {
      Alert.alert(
        'Trading Not Available',
        regionValidation?.reason ||
          'Cryptocurrency trading is not available in your state. Please check back later or contact support for more information.',
        [{ text: 'OK' }]
      );
      return;
    }

    Alert.alert(
      'Sign Crypto Trading Agreement',
      'By signing this agreement, you acknowledge that:\n\n' +
        '• Cryptocurrency trading involves substantial risk\n' +
        '• Crypto assets are not protected by SIPC\n' +
        '• You understand the risks and agree to Alpaca Crypto\'s terms\n\n' +
        'Do you want to proceed?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Agreement',
          onPress: async () => {
            setIsSigning(true);
            try {
              const result = await signAgreement({
                variables: { userId },
              });

              if (result.data?.signCryptoAgreement?.success) {
                Alert.alert(
                  'Agreement Signed',
                  'You can now trade cryptocurrency. Please review the risks and trade responsibly.',
                  [
                    {
                      text: 'OK',
                      onPress: () => {
                        refetchAgreement();
                        onAgreementSigned?.();
                        onClose?.();
                      },
                    },
                  ]
                );
              } else {
                Alert.alert(
                  'Error',
                  result.data?.signCryptoAgreement?.error ||
                    'Failed to sign agreement. Please try again or contact support.'
                );
              }
            } catch (error: any) {
              Alert.alert('Error', error.message || 'Failed to sign agreement. Please try again.');
            } finally {
              setIsSigning(false);
            }
          },
        },
      ]
    );
  };

  // If already signed, show success message
  if (isAgreementSigned) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.successContainer}>
          <Ionicons name="checkmark-circle" size={64} color="#22C55E" />
          <Text style={styles.successTitle}>Crypto Trading Agreement Signed</Text>
          <Text style={styles.successText}>
            You can now trade cryptocurrency through Alpaca Crypto. Please review the risks and
            trade responsibly.
          </Text>
          <TouchableOpacity style={styles.primaryButton} onPress={onClose}>
            <Text style={styles.primaryButtonText}>Continue</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // If region not supported
  if (!isRegionSupported && userState) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.restrictedContainer}>
          <Ionicons name="alert-circle" size={64} color="#F59E0B" />
          <Text style={styles.restrictedTitle}>Trading Not Available in Your State</Text>
          <Text style={styles.restrictedText}>
            {regionValidation?.reason ||
              'Cryptocurrency trading is currently not available in your state due to regulatory restrictions.'}
          </Text>
          <Text style={styles.restrictedSubtext}>
            We're working to expand availability. Please check back later or contact support for
            updates.
          </Text>
          <TouchableOpacity style={styles.secondaryButton} onPress={onClose}>
            <Text style={styles.secondaryButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Cryptocurrency Trading Agreement</Text>
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color="#333" />
          </TouchableOpacity>
        )}
      </View>

      {/* Loading State */}
      {(agreementLoading || regionLoading) && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading agreement...</Text>
        </View>
      )}

      {/* Agreement Content */}
      {!agreementLoading && (
        <ScrollView
          style={styles.scrollView}
          onScroll={handleScroll}
          scrollEventThrottle={16}
          showsVerticalScrollIndicator={true}
        >
          {/* Important Notice */}
          <View style={styles.noticeBox}>
            <Ionicons name="information-circle" size={24} color="#007AFF" />
            <Text style={styles.noticeText}>
              Please read this agreement carefully. You must scroll to the bottom and sign to enable
              cryptocurrency trading.
            </Text>
          </View>

          {/* Agreement Sections */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>1. Cryptocurrency Trading Services</Text>
            <Text style={styles.sectionText}>
              Cryptocurrency trading services are provided through Alpaca Crypto LLC, a
              FinCEN-registered money services business. Alpaca Crypto is a separate entity from
              Alpaca Securities LLC.
            </Text>
            <Text style={styles.sectionText}>
              By signing this agreement, you agree to trade cryptocurrency through Alpaca Crypto
              and acknowledge that RichesReach is not a broker-dealer for cryptocurrency.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>2. High Risk Warning</Text>
            <Text style={styles.sectionTextBold}>
              Cryptocurrency trading involves substantial risk of loss. You may lose more than your
              initial investment.
            </Text>
            <Text style={styles.sectionText}>
              • Cryptocurrency prices are highly volatile{'\n'}
              • Market conditions can change rapidly{'\n'}
              • Past performance does not guarantee future results{'\n'}
              • Only invest money you can afford to lose
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>3. No SIPC Protection</Text>
            <Text style={styles.sectionTextBold}>
              Cryptocurrency assets are NOT protected by the Securities Investor Protection
              Corporation (SIPC).
            </Text>
            <Text style={styles.sectionText}>
              Unlike stocks, cryptocurrency holdings are not covered by SIPC insurance. While
              Alpaca Crypto uses secure custody (Fireblocks MPC), there is no federal insurance
              protection for crypto assets.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>4. Fees</Text>
            <Text style={styles.sectionText}>
              Cryptocurrency trading incurs fees based on a volume-tiered maker/taker model:
            </Text>
            <Text style={styles.sectionText}>
              • Maker fees: Lower fees for providing liquidity{'\n'}
              • Taker fees: Higher fees for taking liquidity{'\n'}
              • Fees vary by trading volume
            </Text>
            <Text style={styles.sectionText}>
              Unlike stock trading (which is commission-free), cryptocurrency trading has fees.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>5. Trading Hours</Text>
            <Text style={styles.sectionText}>
              Cryptocurrency markets operate 24/7, unlike stock markets which have specific trading
              hours. This means prices can change at any time, including weekends and holidays.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>6. Regulatory Compliance</Text>
            <Text style={styles.sectionText}>
              Cryptocurrency trading may not be available in all states or jurisdictions. If you
              move to a restricted state, your ability to trade may be limited or suspended.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>7. Acknowledgment</Text>
            <Text style={styles.sectionText}>
              By signing this agreement, you acknowledge that:
            </Text>
            <Text style={styles.sectionText}>
              • You have read and understand this agreement{'\n'}
              • You understand the risks of cryptocurrency trading{'\n'}
              • You agree to Alpaca Crypto's terms and conditions{'\n'}
              • You are responsible for your trading decisions{'\n'}
              • You will only trade with money you can afford to lose
            </Text>
          </View>

          {/* Scroll Indicator */}
          {!hasScrolledToBottom && (
            <View style={styles.scrollIndicator}>
              <Icon name="chevron-down" size={20} color="#666" />
              <Text style={styles.scrollIndicatorText}>Scroll to bottom to continue</Text>
            </View>
          )}
        </ScrollView>
      )}

      {/* Footer with Sign Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[
            styles.signButton,
            (!hasScrolledToBottom || isSigning || agreementLoading) && styles.signButtonDisabled,
          ]}
          onPress={handleSignAgreement}
          disabled={!hasScrolledToBottom || isSigning || agreementLoading}
        >
          {isSigning ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Icon name="edit-3" size={20} color="#fff" />
              <Text style={styles.signButtonText}>Sign Agreement</Text>
            </>
          )}
        </TouchableOpacity>
        {!hasScrolledToBottom && (
          <Text style={styles.footerHint}>
            Please scroll to the bottom of the agreement to continue
          </Text>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
    flex: 1,
  },
  closeButton: {
    padding: 4,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
  },
  scrollView: {
    flex: 1,
  },
  noticeBox: {
    flexDirection: 'row',
    backgroundColor: '#EFF6FF',
    padding: 16,
    margin: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  noticeText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#1E40AF',
    lineHeight: 20,
  },
  section: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
  },
  sectionText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 22,
    marginBottom: 12,
  },
  sectionTextBold: {
    fontSize: 14,
    fontWeight: '600',
    color: '#DC2626',
    lineHeight: 22,
    marginBottom: 12,
  },
  scrollIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    gap: 8,
  },
  scrollIndicatorText: {
    fontSize: 12,
    color: '#666',
  },
  footer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    backgroundColor: '#fff',
  },
  signButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 8,
  },
  signButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  signButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  footerHint: {
    marginTop: 8,
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  successContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  successTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 24,
    marginBottom: 12,
    textAlign: 'center',
  },
  successText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  restrictedContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  restrictedTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 24,
    marginBottom: 12,
    textAlign: 'center',
  },
  restrictedText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 12,
  },
  restrictedSubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 32,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#F3F4F6',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  secondaryButtonText: {
    color: '#111827',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CryptoAgreementScreen;

