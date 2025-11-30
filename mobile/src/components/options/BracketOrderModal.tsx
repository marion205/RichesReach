import React, { useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, TextInput, Alert } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface BracketOrderModalProps {
  visible: boolean;
  onClose: () => void;
  symbol: string;
  optionType: string;
  strike: number;
  expiration: string;
  currentPrice: number;
  onPlaceOrder: (order: {
    takeProfit: number;
    stopLoss: number;
    quantity: number;
  }) => void;
}

export default function BracketOrderModal({
  visible,
  onClose,
  symbol,
  optionType,
  strike,
  expiration,
  currentPrice,
  onPlaceOrder,
}: BracketOrderModalProps) {
  const [quantity, setQuantity] = useState('1');
  const [takeProfit, setTakeProfit] = useState('');
  const [stopLoss, setStopLoss] = useState('');

  // Jobs-style: Smart defaults
  const suggestedTakeProfit = currentPrice * 1.5; // 50% profit target
  const suggestedStopLoss = currentPrice * 0.7; // 30% loss limit

  const handlePlaceOrder = () => {
    const tp = parseFloat(takeProfit) || suggestedTakeProfit;
    const sl = parseFloat(stopLoss) || suggestedStopLoss;
    const qty = parseInt(quantity) || 1;

    if (tp <= currentPrice) {
      Alert.alert('Invalid Take Profit', 'Take profit must be above current price');
      return;
    }

    if (sl >= currentPrice) {
      Alert.alert('Invalid Stop Loss', 'Stop loss must be below current price');
      return;
    }

    onPlaceOrder({ takeProfit: tp, stopLoss: sl, quantity: qty });
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.title}>Bracket Order</Text>
          <View style={styles.placeholder} />
        </View>

        {/* Trade Info - Simple, Clean */}
        <View style={styles.tradeInfo}>
          <Text style={styles.tradeSymbol}>
            {symbol} ${strike} {optionType}
          </Text>
          <Text style={styles.tradeExpiration}>{expiration}</Text>
          <Text style={styles.currentPrice}>Current: ${currentPrice.toFixed(2)}</Text>
        </View>

        {/* Input Section - Jobs Style: One thing at a time */}
        <View style={styles.inputSection}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Quantity</Text>
            <TextInput
              style={styles.input}
              value={quantity}
              onChangeText={setQuantity}
              keyboardType="numeric"
              placeholder="1"
            />
          </View>

          <View style={styles.inputGroup}>
            <View style={styles.labelRow}>
              <Text style={styles.label}>Take Profit</Text>
              <TouchableOpacity
                onPress={() => setTakeProfit(suggestedTakeProfit.toFixed(2))}
                style={styles.suggestionButton}
              >
                <Text style={styles.suggestionText}>Use ${suggestedTakeProfit.toFixed(2)}</Text>
              </TouchableOpacity>
            </View>
            <TextInput
              style={styles.input}
              value={takeProfit}
              onChangeText={setTakeProfit}
              keyboardType="numeric"
              placeholder={suggestedTakeProfit.toFixed(2)}
            />
            <Text style={styles.hint}>
              Sell automatically when price reaches this level
            </Text>
          </View>

          <View style={styles.inputGroup}>
            <View style={styles.labelRow}>
              <Text style={styles.label}>Stop Loss</Text>
              <TouchableOpacity
                onPress={() => setStopLoss(suggestedStopLoss.toFixed(2))}
                style={styles.suggestionButton}
              >
                <Text style={styles.suggestionText}>Use ${suggestedStopLoss.toFixed(2)}</Text>
              </TouchableOpacity>
            </View>
            <TextInput
              style={styles.input}
              value={stopLoss}
              onChangeText={setStopLoss}
              keyboardType="numeric"
              placeholder={suggestedStopLoss.toFixed(2)}
            />
            <Text style={styles.hint}>
              Sell automatically to limit losses
            </Text>
          </View>
        </View>

        {/* Summary - Simple, Clear */}
        <View style={styles.summary}>
          <Text style={styles.summaryTitle}>Order Summary</Text>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Buy:</Text>
            <Text style={styles.summaryValue}>
              {quantity} contract{parseInt(quantity) !== 1 ? 's' : ''} @ ${currentPrice.toFixed(2)}
            </Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Sell at profit:</Text>
            <Text style={[styles.summaryValue, styles.profit]}>
              ${(parseFloat(takeProfit) || suggestedTakeProfit).toFixed(2)}
            </Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Sell at loss:</Text>
            <Text style={[styles.summaryValue, styles.loss]}>
              ${(parseFloat(stopLoss) || suggestedStopLoss).toFixed(2)}
            </Text>
          </View>
        </View>

        {/* Place Order Button - Big, Beautiful */}
        <TouchableOpacity style={styles.placeButton} onPress={handlePlaceOrder}>
          <Text style={styles.placeButtonText}>Place Bracket Order</Text>
        </TouchableOpacity>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  closeButton: {
    padding: 8,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  placeholder: {
    width: 40,
  },
  tradeInfo: {
    alignItems: 'center',
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    marginBottom: 24,
  },
  tradeSymbol: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  tradeExpiration: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  currentPrice: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  inputSection: {
    marginBottom: 24,
  },
  inputGroup: {
    marginBottom: 24,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  suggestionButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#F0F7FF',
    borderRadius: 8,
  },
  suggestionText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#007AFF',
  },
  input: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    padding: 16,
    fontSize: 18,
    color: '#111827',
    backgroundColor: '#FFFFFF',
  },
  hint: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 8,
  },
  summary: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  profit: {
    color: '#059669',
  },
  loss: {
    color: '#DC2626',
  },
  placeButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 18,
    borderRadius: 12,
    alignItems: 'center',
  },
  placeButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});


