import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { PLACE_STOCK_ORDER } from '../../graphql/queries_actual_schema';

interface StockTradingModalProps {
  visible: boolean;
  onClose: () => void;
  symbol: string;
  currentPrice: number;
  companyName: string;
}

const StockTradingModal: React.FC<StockTradingModalProps> = ({
  visible,
  onClose,
  symbol,
  currentPrice,
  companyName,
}) => {
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [quantity, setQuantity] = useState('');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [limitPrice, setLimitPrice] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [placeOrder] = useMutation(PLACE_STOCK_ORDER);

  const handleSubmit = async () => {
    if (!quantity || parseInt(quantity) <= 0) {
      Alert.alert('Invalid Quantity', 'Please enter a valid quantity.');
      return;
    }

    if (orderType === 'LIMIT' && (!limitPrice || parseFloat(limitPrice) <= 0)) {
      Alert.alert('Invalid Limit Price', 'Please enter a valid limit price.');
      return;
    }

    setIsSubmitting(true);

    try {
      const { data } = await placeOrder({
        variables: {
          symbol,
          side,
          quantity: parseInt(quantity),
          orderType,
          limitPrice: orderType === 'LIMIT' ? parseFloat(limitPrice) : null,
          timeInForce: 'DAY',
        },
      });

      if (data?.placeStockOrder?.success) {
        Alert.alert(
          'Order Placed Successfully',
          data.placeStockOrder.message,
          [{ text: 'OK', onPress: onClose }]
        );
        // Reset form
        setQuantity('');
        setLimitPrice('');
        setSide('BUY');
        setOrderType('MARKET');
      } else {
        Alert.alert('Order Failed', data?.placeStockOrder?.message || 'Unknown error');
      }
    } catch (error) {
      console.error('Order placement error:', error);
      Alert.alert('Error', 'Failed to place order. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalValue = quantity && currentPrice 
    ? (parseInt(quantity) * (currentPrice || 0)).toFixed(2)
    : '0.00';

  return (
    <Modal visible={visible} animationType="slide" transparent={true}>
      <TouchableOpacity style={styles.overlay} activeOpacity={1} onPress={onClose}>
        <TouchableOpacity style={styles.container} activeOpacity={1} onPress={(e) => e.stopPropagation()}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#374151" />
          </TouchableOpacity>
          <Text style={styles.title}>Trade {symbol}</Text>
          <View style={styles.placeholder} />
        </View>

        {/* Stock Info */}
        <View style={styles.stockInfo}>
          <Text style={styles.companyName}>{companyName}</Text>
          <Text style={styles.symbol}>{symbol}</Text>
          <Text style={styles.currentPrice}>${(currentPrice || 0).toFixed(2)}</Text>
        </View>

        {/* Side Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Order Type</Text>
          <View style={styles.sideButtons}>
            <TouchableOpacity
              style={[styles.sideButton, side === 'BUY' && styles.sideButtonActive]}
              onPress={() => setSide('BUY')}
            >
              <Text style={[styles.sideButtonText, side === 'BUY' && styles.sideButtonTextActive]}>
                BUY
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.sideButton, side === 'SELL' && styles.sideButtonActive]}
              onPress={() => setSide('SELL')}
            >
              <Text style={[styles.sideButtonText, side === 'SELL' && styles.sideButtonTextActive]}>
                SELL
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Order Type */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Order Type</Text>
          <View style={styles.orderTypeButtons}>
            <TouchableOpacity
              style={[styles.orderTypeButton, orderType === 'MARKET' && styles.orderTypeButtonActive]}
              onPress={() => setOrderType('MARKET')}
            >
              <Text style={[styles.orderTypeButtonText, orderType === 'MARKET' && styles.orderTypeButtonTextActive]}>
                Market
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.orderTypeButton, orderType === 'LIMIT' && styles.orderTypeButtonActive]}
              onPress={() => setOrderType('LIMIT')}
            >
              <Text style={[styles.orderTypeButtonText, orderType === 'LIMIT' && styles.orderTypeButtonTextActive]}>
                Limit
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Quantity */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quantity</Text>
          <TextInput
            style={styles.input}
            value={quantity}
            onChangeText={setQuantity}
            placeholder="Enter number of shares"
            keyboardType="numeric"
            autoCapitalize="none"
          />
        </View>

        {/* Limit Price (only for LIMIT orders) */}
        {orderType === 'LIMIT' && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Limit Price</Text>
            <TextInput
              style={styles.input}
              value={limitPrice}
              onChangeText={setLimitPrice}
              placeholder="Enter limit price"
              keyboardType="numeric"
              autoCapitalize="none"
            />
          </View>
        )}

        {/* Order Summary */}
        <View style={styles.summary}>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Total Value:</Text>
            <Text style={styles.summaryValue}>${totalValue}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Order Type:</Text>
            <Text style={styles.summaryValue}>{side} {orderType}</Text>
          </View>
        </View>

        {/* Submit Button */}
        <TouchableOpacity
          style={[styles.submitButton, side === 'BUY' ? styles.buyButton : styles.sellButton]}
          onPress={handleSubmit}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.submitButtonText}>
              {side} {quantity || '0'} {symbol}
            </Text>
          )}
        </TouchableOpacity>
        </TouchableOpacity>
      </TouchableOpacity>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#F9FAFB',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    maxHeight: '80%',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  closeButton: {
    padding: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  placeholder: {
    width: 40,
  },
  stockInfo: {
    alignItems: 'center',
    paddingVertical: 20,
    backgroundColor: 'white',
    marginHorizontal: 20,
    marginTop: 20,
    borderRadius: 12,
  },
  companyName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 4,
  },
  symbol: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  currentPrice: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  section: {
    marginHorizontal: 20,
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  sideButtons: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 4,
  },
  sideButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 6,
  },
  sideButtonActive: {
    backgroundColor: 'white',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  sideButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  sideButtonTextActive: {
    color: '#111827',
  },
  orderTypeButtons: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 4,
  },
  orderTypeButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 6,
  },
  orderTypeButtonActive: {
    backgroundColor: 'white',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  orderTypeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  orderTypeButtonTextActive: {
    color: '#111827',
  },
  input: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#111827',
  },
  summary: {
    backgroundColor: 'white',
    marginHorizontal: 20,
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
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
  submitButton: {
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 40,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  buyButton: {
    backgroundColor: '#10B981',
  },
  sellButton: {
    backgroundColor: '#EF4444',
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
});

export default StockTradingModal;
