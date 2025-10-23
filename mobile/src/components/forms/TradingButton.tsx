import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

// GraphQL Mutations
const PLACE_MARKET_ORDER = gql`
  mutation PlaceMarketOrder($symbol: String!, $quantity: Int!, $side: String!, $notes: String) {
    placeMarketOrder(symbol: $symbol, quantity: $quantity, side: $side, notes: $notes) {
      success
      order {
        id
        symbol
        side
        orderType
        quantity
        status
        createdAt
        notes
      }
    }
  }
`;

const PLACE_LIMIT_ORDER = gql`
  mutation PlaceLimitOrder($symbol: String!, $quantity: Int!, $side: String!, $limitPrice: Float!, $notes: String) {
    placeLimitOrder(symbol: $symbol, quantity: $quantity, side: $side, limitPrice: $limitPrice, notes: $notes) {
      success
      order {
        id
        symbol
        side
        orderType
        quantity
        price
        status
        createdAt
        notes
      }
    }
  }
`;

interface TradingButtonProps {
  symbol: string;
  currentPrice?: number;
  side?: 'buy' | 'sell';
  style?: any;
  onOrderPlaced?: (order: any) => void;
}

const TradingButton: React.FC<TradingButtonProps> = ({
  symbol,
  currentPrice,
  side = 'buy',
  style,
  onOrderPlaced
}) => {
  const [showModal, setShowModal] = useState(false);
  const [quantity, setQuantity] = useState('');
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [limitPrice, setLimitPrice] = useState('');
  const [notes, setNotes] = useState('');
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);

  const [placeMarketOrder] = useMutation(PLACE_MARKET_ORDER);
  const [placeLimitOrder] = useMutation(PLACE_LIMIT_ORDER);

  const handlePress = () => {
    setShowModal(true);
    setQuantity('');
    setLimitPrice(currentPrice?.toString() || '');
    setNotes('');
  };

  const handlePlaceOrder = async () => {
    if (!quantity) {
      Alert.alert('Error', 'Please enter quantity');
      return;
    }

    setIsPlacingOrder(true);
    try {
      let result;
      const orderNotes = notes || `Quick ${side} order for ${symbol}`;

      if (orderType === 'market') {
        result = await placeMarketOrder({
          variables: {
            symbol: symbol.toUpperCase(),
            quantity: parseInt(quantity),
            side: side,
            notes: orderNotes
          }
        });
      } else {
        if (!limitPrice) {
          Alert.alert('Error', 'Please enter limit price');
          return;
        }
        result = await placeLimitOrder({
          variables: {
            symbol: symbol.toUpperCase(),
            quantity: parseInt(quantity),
            side: side,
            limitPrice: parseFloat(limitPrice),
            notes: orderNotes
          }
        });
      }

      if (result.data) {
        const orderData = result.data[`place${orderType.charAt(0).toUpperCase() + orderType.slice(1)}Order`];
        if (orderData.success) {
          Alert.alert(
            'Order Placed',
            `Your ${orderType} order for ${quantity} shares of ${symbol.toUpperCase()} has been placed successfully.`,
            [{ text: 'OK', onPress: () => {
              setShowModal(false);
              onOrderPlaced?.(orderData.order);
            }}]
          );
        } else {
          Alert.alert('Error', 'Failed to place order');
        }
      }
    } catch (error) {
      console.error('Error placing order:', error);
      Alert.alert('Error', 'Failed to place order. Please try again.');
    } finally {
      setIsPlacingOrder(false);
    }
  };

  const resetModal = () => {
    setQuantity('');
    setLimitPrice(currentPrice?.toString() || '');
    setNotes('');
    setOrderType('market');
  };

  return (
    <>
      <TouchableOpacity
        style={[
          styles.button,
          side === 'buy' ? styles.buyButton : styles.sellButton,
          style
        ]}
        onPress={handlePress}
      >
        <Icon 
          name={side === 'buy' ? 'trending-up' : 'trending-down'} 
          size={16} 
          color="#fff" 
        />
        <Text style={styles.buttonText}>
          {side === 'buy' ? 'BUY' : 'SELL'} {symbol}
        </Text>
      </TouchableOpacity>

      <Modal
        visible={showModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {side === 'buy' ? 'Buy' : 'Sell'} {symbol.toUpperCase()}
            </Text>
            <TouchableOpacity onPress={() => setShowModal(false)}>
              <Icon name="x" size={24} color="#000" />
            </TouchableOpacity>
          </View>

          <View style={styles.modalContent}>
            {/* Current Price */}
            {currentPrice && (
              <View style={styles.priceInfo}>
                <Text style={styles.priceLabel}>Current Price:</Text>
                <Text style={styles.priceValue}>${(currentPrice || 0).toFixed(2)}</Text>
              </View>
            )}

            {/* Order Type */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Order Type</Text>
              <View style={styles.orderTypeButtons}>
                <TouchableOpacity
                  style={[
                    styles.orderTypeButton,
                    orderType === 'market' && styles.orderTypeButtonActive
                  ]}
                  onPress={() => setOrderType('market')}
                >
                  <Text style={[
                    styles.orderTypeButtonText,
                    orderType === 'market' && styles.orderTypeButtonTextActive
                  ]}>
                    Market
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.orderTypeButton,
                    orderType === 'limit' && styles.orderTypeButtonActive
                  ]}
                  onPress={() => setOrderType('limit')}
                >
                  <Text style={[
                    styles.orderTypeButtonText,
                    orderType === 'limit' && styles.orderTypeButtonTextActive
                  ]}>
                    Limit
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Quantity */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Quantity</Text>
              <TextInput
                style={styles.textInput}
                value={quantity}
                onChangeText={setQuantity}
                placeholder="Number of shares"
                keyboardType="numeric"
                autoFocus
              />
            </View>

            {/* Limit Price */}
            {orderType === 'limit' && (
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Limit Price</Text>
                <TextInput
                  style={styles.textInput}
                  value={limitPrice}
                  onChangeText={setLimitPrice}
                  placeholder="Price per share"
                  keyboardType="numeric"
                />
              </View>
            )}

            {/* Notes */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Notes (Optional)</Text>
              <TextInput
                style={[styles.textInput, styles.textArea]}
                value={notes}
                onChangeText={setNotes}
                placeholder="Add a note about this order"
                multiline
                numberOfLines={2}
              />
            </View>

            {/* Order Summary */}
            {quantity && (
              <View style={styles.summaryCard}>
                <Text style={styles.summaryTitle}>Order Summary</Text>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Action:</Text>
                  <Text style={styles.summaryValue}>
                    {side.toUpperCase()} {quantity} shares of {symbol.toUpperCase()}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Type:</Text>
                  <Text style={styles.summaryValue}>{orderType.toUpperCase()}</Text>
                </View>
                {orderType === 'limit' && limitPrice && (
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Price:</Text>
                    <Text style={styles.summaryValue}>${(parseFloat(limitPrice) || 0).toFixed(2)}</Text>
                  </View>
                )}
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Total Value:</Text>
                  <Text style={styles.summaryValue}>
                    ${orderType === 'limit' && limitPrice 
                      ? ((parseFloat(limitPrice) || 0) * parseInt(quantity)).toFixed(2)
                      : currentPrice 
                        ? ((currentPrice || 0) * parseInt(quantity)).toFixed(2)
                        : '0.00'
                    }
                  </Text>
                </View>
              </View>
            )}

            {/* Action Buttons */}
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.placeOrderButton,
                  isPlacingOrder && styles.placeOrderButtonDisabled
                ]}
                onPress={handlePlaceOrder}
                disabled={isPlacingOrder}
              >
                {isPlacingOrder ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Text style={styles.placeOrderButtonText}>
                    Place {side === 'buy' ? 'Buy' : 'Sell'} Order
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    gap: 6,
  },
  buyButton: {
    backgroundColor: '#34C759',
  },
  sellButton: {
    backgroundColor: '#FF3B30',
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  priceInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#E3F2FD',
    padding: 16,
    borderRadius: 8,
    marginBottom: 20,
  },
  priceLabel: {
    fontSize: 16,
    color: '#8E8E93',
  },
  priceValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#fff',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  textArea: {
    height: 60,
    textAlignVertical: 'top',
  },
  orderTypeButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  orderTypeButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
  },
  orderTypeButtonActive: {
    backgroundColor: '#007AFF',
  },
  orderTypeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  orderTypeButtonTextActive: {
    color: '#fff',
  },
  summaryCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 'auto',
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 8,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  placeOrderButton: {
    flex: 2,
    paddingVertical: 16,
    borderRadius: 8,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  placeOrderButtonDisabled: {
    backgroundColor: '#8E8E93',
  },
  placeOrderButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default TradingButton;
