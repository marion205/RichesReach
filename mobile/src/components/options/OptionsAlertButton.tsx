import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal, TextInput, Alert } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useMutation } from '@apollo/client';
import { CREATE_OPTIONS_ALERT } from '../../graphql/optionsAlertMutations';

interface OptionsAlertButtonProps {
  symbol: string;
  strike?: number;
  expiration?: string;
  optionType?: string;
  currentPrice?: number;
  currentIV?: number;
}

export default function OptionsAlertButton({
  symbol,
  strike,
  expiration,
  optionType,
  currentPrice,
  currentIV,
}: OptionsAlertButtonProps) {
  const [showModal, setShowModal] = useState(false);
  const [alertType, setAlertType] = useState<'price' | 'iv' | 'expiration'>('price');
  const [priceTarget, setPriceTarget] = useState('');
  const [ivTarget, setIvTarget] = useState('');
  
  const [createAlert, { loading: creatingAlert }] = useMutation(CREATE_OPTIONS_ALERT, {
    refetchQueries: ['GetOptionsAlerts'],
  });

  const handleCreateAlert = async () => {
    try {
      let alertTypeUpper = alertType.toUpperCase();
      let targetValue: number | null = null;
      let direction: string | null = null;
      
      switch (alertType) {
        case 'price':
          if (!priceTarget) {
            Alert.alert('Missing Target', 'Please enter a price target');
            return;
          }
          targetValue = parseFloat(priceTarget);
          direction = targetValue > (currentPrice || 0) ? 'above' : 'below';
          break;
        case 'iv':
          if (!ivTarget) {
            Alert.alert('Missing Target', 'Please enter an IV target');
            return;
          }
          targetValue = parseFloat(ivTarget) / 100; // Convert percentage to decimal
          direction = targetValue > (currentIV || 0) ? 'above' : 'below';
          break;
        case 'expiration':
          // No target value needed for expiration alerts
          break;
      }

      const { data } = await createAlert({
        variables: {
          symbol,
          strike,
          expiration,
          optionType: optionType?.toUpperCase(),
          alertType: alertTypeUpper,
          targetValue,
          direction,
        },
      });

      if (data?.createOptionsAlert?.success) {
        Alert.alert('Alert Created', `Alert set for ${symbol}`);
        setShowModal(false);
        setPriceTarget('');
        setIvTarget('');
      } else {
        Alert.alert('Error', data?.createOptionsAlert?.error || 'Failed to create alert');
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to create alert');
    }
  };

  return (
    <>
      <TouchableOpacity
        style={styles.button}
        onPress={() => setShowModal(true)}
      >
        <Icon name="bell" size={16} color="#007AFF" />
        <Text style={styles.buttonText}>Alert</Text>
      </TouchableOpacity>

      <Modal
        visible={showModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowModal(false)}>
              <Icon name="x" size={24} color="#111827" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Create Alert</Text>
            <View style={styles.placeholder} />
          </View>

          <View style={styles.alertInfo}>
            <Text style={styles.alertSymbol}>
              {symbol} {strike ? `$${strike}` : ''} {optionType || ''}
            </Text>
            {expiration && (
              <Text style={styles.alertExpiration}>Expires: {expiration}</Text>
            )}
          </View>

          {/* Simple Alert Type Selector */}
          <View style={styles.typeSelector}>
            <TouchableOpacity
              style={[styles.typeButton, alertType === 'price' && styles.typeButtonActive]}
              onPress={() => setAlertType('price')}
            >
              <Icon name="trending-up" size={18} color={alertType === 'price' ? '#FFFFFF' : '#6B7280'} />
              <Text style={[styles.typeText, alertType === 'price' && styles.typeTextActive]}>
                Price
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.typeButton, alertType === 'iv' && styles.typeButtonActive]}
              onPress={() => setAlertType('iv')}
            >
              <Icon name="activity" size={18} color={alertType === 'iv' ? '#FFFFFF' : '#6B7280'} />
              <Text style={[styles.typeText, alertType === 'iv' && styles.typeTextActive]}>
                IV
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.typeButton, alertType === 'expiration' && styles.typeButtonActive]}
              onPress={() => setAlertType('expiration')}
            >
              <Icon name="clock" size={18} color={alertType === 'expiration' ? '#FFFFFF' : '#6B7280'} />
              <Text style={[styles.typeText, alertType === 'expiration' && styles.typeTextActive]}>
                Expiration
              </Text>
            </TouchableOpacity>
          </View>

          {/* Input - Only show relevant one */}
          {alertType === 'price' && (
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Alert when price reaches</Text>
              <TextInput
                style={styles.input}
                value={priceTarget}
                onChangeText={setPriceTarget}
                keyboardType="numeric"
                placeholder={currentPrice ? `Current: $${currentPrice.toFixed(2)}` : 'Enter price'}
              />
            </View>
          )}

          {alertType === 'iv' && (
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Alert when IV reaches</Text>
              <TextInput
                style={styles.input}
                value={ivTarget}
                onChangeText={setIvTarget}
                keyboardType="numeric"
                placeholder={currentIV ? `Current: ${(currentIV * 100).toFixed(1)}%` : 'Enter IV %'}
              />
            </View>
          )}

          {alertType === 'expiration' && (
            <View style={styles.infoBox}>
              <Icon name="info" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                You'll be notified 1 day before expiration
              </Text>
            </View>
          )}

          <TouchableOpacity 
            style={[styles.createButton, creatingAlert && styles.createButtonDisabled]} 
            onPress={handleCreateAlert}
            disabled={creatingAlert}
          >
            <Text style={styles.createButtonText}>
              {creatingAlert ? 'Creating...' : 'Create Alert'}
            </Text>
          </TouchableOpacity>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F0F7FF',
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  placeholder: {
    width: 24,
  },
  alertInfo: {
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    marginBottom: 24,
  },
  alertSymbol: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  alertExpiration: {
    fontSize: 14,
    color: '#6B7280',
  },
  typeSelector: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    gap: 8,
  },
  typeButtonActive: {
    backgroundColor: '#007AFF',
  },
  typeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  typeTextActive: {
    color: '#FFFFFF',
  },
  inputGroup: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    padding: 16,
    fontSize: 18,
    color: '#111827',
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F7FF',
    borderRadius: 12,
    padding: 16,
    gap: 12,
    marginBottom: 24,
  },
  infoText: {
    fontSize: 15,
    color: '#374151',
    flex: 1,
  },
  createButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 18,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 'auto',
  },
  createButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  createButtonDisabled: {
    opacity: 0.6,
  },
});


