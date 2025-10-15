import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  Linking,
} from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import Icon from 'react-native-vector-icons/Feather';
import { SBLOCReferral } from '../../../types/sbloc';

interface Props {
  navigation: any;
  route: {
    params: {
      sessionUrl: string;
      referral: SBLOCReferral;
    };
  };
}

const SBLOCApplicationScreen: React.FC<Props> = ({ navigation, route }) => {
  const { sessionUrl, referral } = route.params;
  const [isOpeningBrowser, setIsOpeningBrowser] = useState(false);
  const [browserOpened, setBrowserOpened] = useState(false);

  useEffect(() => {
    // Auto-open the browser when screen loads
    handleOpenApplication();
  }, []);

  const handleOpenApplication = async () => {
    if (browserOpened) return;

    setIsOpeningBrowser(true);
    try {
      // Open the aggregator's hosted application flow
      const result = await WebBrowser.openBrowserAsync(sessionUrl, {
        presentationStyle: WebBrowser.WebBrowserPresentationStyle.FULL_SCREEN,
        controlsColor: '#007AFF',
        showTitle: true,
        enableBarCollapsing: false,
        showInRecents: true,
      });

      setBrowserOpened(true);

      if (result.type === 'dismiss') {
        // User closed the browser, navigate back
        navigation.goBack();
      } else if (result.type === 'cancel') {
        // User cancelled, show confirmation
        Alert.alert(
          'Application Cancelled',
          'Your SBLOC application was not completed. Would you like to try again?',
          [
            { text: 'Go Back', style: 'cancel', onPress: () => navigation.goBack() },
            { text: 'Try Again', onPress: handleOpenApplication },
          ]
        );
      }
    } catch (error) {
      console.error('Error opening SBLOC application:', error);
      Alert.alert(
        'Error',
        'Failed to open the application. Please try again.',
        [
          { text: 'Go Back', onPress: () => navigation.goBack() },
          { text: 'Retry', onPress: handleOpenApplication },
        ]
      );
    } finally {
      setIsOpeningBrowser(false);
    }
  };

  const handleCheckStatus = () => {
    // Navigate to referral status screen
    navigation.navigate('SBLOCStatus', { referralId: referral.id });
  };

  const handleGoBack = () => {
    Alert.alert(
      'Leave Application',
      'Are you sure you want to leave the SBLOC application? Your progress will be saved.',
      [
        { text: 'Stay', style: 'cancel' },
        { text: 'Leave', onPress: () => navigation.goBack() },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={handleGoBack}
        >
          <Icon name="arrow-left" size={24} color="#374151" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>SBLOC Application</Text>
        <View style={styles.placeholder} />
      </View>

      <View style={styles.content}>
        <View style={styles.infoCard}>
          <View style={styles.infoHeader}>
            <Icon name="info" size={24} color="#3B82F6" />
            <Text style={styles.infoTitle}>Application Instructions</Text>
          </View>
          
          <Text style={styles.infoText}>
            You're being redirected to {referral.bank.name}'s secure application portal.
          </Text>
          
          <Text style={styles.infoText}>
            Complete the application process in the browser window. Your progress will be automatically saved.
          </Text>
        </View>

        <View style={styles.referralCard}>
          <Text style={styles.referralTitle}>Application Details</Text>
          <View style={styles.referralRow}>
            <Text style={styles.referralLabel}>Bank:</Text>
            <Text style={styles.referralValue}>{referral.bank.name}</Text>
          </View>
          <View style={styles.referralRow}>
            <Text style={styles.referralLabel}>Amount:</Text>
            <Text style={styles.referralValue}>${referral.requestedAmountUsd.toLocaleString()}</Text>
          </View>
          <View style={styles.referralRow}>
            <Text style={styles.referralLabel}>Status:</Text>
            <Text style={[styles.referralValue, styles.statusText]}>{referral.status}</Text>
          </View>
        </View>

        {isOpeningBrowser && (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text style={styles.loadingText}>Opening application...</Text>
          </View>
        )}
      </View>

      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={handleOpenApplication}
          disabled={isOpeningBrowser}
        >
          <Icon name="external-link" size={20} color="#007AFF" />
          <Text style={styles.actionButtonText}>
            {browserOpened ? 'Reopen Application' : 'Open Application'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.secondaryButton]}
          onPress={handleCheckStatus}
        >
          <Icon name="eye" size={20} color="#6B7280" />
          <Text style={[styles.actionButtonText, styles.secondaryButtonText]}>
            Check Status
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  placeholder: {
    width: 40,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  infoCard: {
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  infoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E40AF',
    marginLeft: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#1E40AF',
    lineHeight: 20,
    marginBottom: 8,
  },
  referralCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  referralTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  referralRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  referralLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  referralValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  statusText: {
    textTransform: 'capitalize',
    color: '#059669',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  footer: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingVertical: 16,
    borderWidth: 1,
    borderColor: '#007AFF',
    gap: 8,
  },
  secondaryButton: {
    backgroundColor: '#F9FAFB',
    borderColor: '#D1D5DB',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  secondaryButtonText: {
    color: '#6B7280',
  },
});

export default SBLOCApplicationScreen;
