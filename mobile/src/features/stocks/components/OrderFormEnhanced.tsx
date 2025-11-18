/**
 * Enhanced OrderForm with Real-Time Validation
 * 
 * Provides:
 * - Real-time field validation with clear error messages
 * - Visual feedback (error states, success indicators)
 * - Context-aware validation (price vs market price, etc.)
 * - Accessibility improvements
 */

import React, { useState, useEffect, useMemo } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useOrderForm, OrderType, OrderSide } from '../hooks/useOrderForm';
import { useQuery } from '@apollo/client';
import { GET_TRADING_QUOTE } from '../../../graphql/tradingQueries';
import {
  validateSymbol,
  validateQuantity,
  validatePrice,
  validateLimitPrice,
  validateStopPrice,
  validateOrderTotal,
  ValidationResult,
} from '../../../utils/validation';

const C = {
  bg: '#F5F6FA',
  card: '#FFFFFF',
  line: '#E9EAF0',
  text: '#111827',
  sub: '#6B7280',
  primary: '#007AFF',
  green: '#22C55E',
  red: '#EF4444',
  amber: '#F59E0B',
  blueSoft: '#E8F1FF',
  successSoft: '#EAFBF1',
  dangerSoft: '#FEECEC',
  shadow: 'rgba(16,24,40,0.08)',
};

interface OrderFormProps {
  form: ReturnType<typeof useOrderForm>;
  quoteData?: any;
  quoteLoading?: boolean;
  onSBLOCPress?: () => void;
}

interface FieldValidationState {
  isValid: boolean;
  error?: string;
  touched: boolean;
}

export const OrderFormEnhanced: React.FC<OrderFormProps> = ({
  form,
  quoteData,
  quoteLoading = false,
  onSBLOCPress,
}) => {
  const {
    orderType,
    orderSide,
    symbol,
    quantity,
    price,
    stopPrice,
    notes,
    setOrderType,
    setOrderSide,
    setSymbol,
    setQuantity,
    setPrice,
    setStopPrice,
    setNotes,
  } = form;

  // Validation state for each field
  const [validations, setValidations] = useState<Record<string, FieldValidationState>>({
    symbol: { isValid: true, touched: false },
    quantity: { isValid: true, touched: false },
    price: { isValid: true, touched: false },
    stopPrice: { isValid: true, touched: false },
  });

  // Real-time validation
  useEffect(() => {
    const newValidations: Record<string, FieldValidationState> = { ...validations };

    // Validate symbol
    if (symbol) {
      const symbolResult = validateSymbol(symbol);
      newValidations.symbol = {
        isValid: symbolResult.isValid,
        error: symbolResult.error,
        touched: true,
      };
    } else {
      newValidations.symbol = { isValid: true, touched: false };
    }

    // Validate quantity
    if (quantity) {
      const qtyResult = validateQuantity(quantity);
      newValidations.quantity = {
        isValid: qtyResult.isValid,
        error: qtyResult.error,
        touched: true,
      };
    } else {
      newValidations.quantity = { isValid: true, touched: false };
    }

    // Validate price (for limit orders)
    if (orderType === 'limit' && price) {
      const currentPrice = quoteData?.tradingQuote
        ? (orderSide === 'buy' ? quoteData.tradingQuote.ask : quoteData.tradingQuote.bid)
        : undefined;
      
      const priceResult = validateLimitPrice(price, currentPrice, orderSide);
      newValidations.price = {
        isValid: priceResult.isValid,
        error: priceResult.error,
        touched: true,
      };
    } else if (orderType === 'limit') {
      newValidations.price = { isValid: false, error: 'Price is required for limit orders', touched: true };
    } else {
      newValidations.price = { isValid: true, touched: false };
    }

    // Validate stop price (for stop loss orders)
    if (orderType === 'stop_loss' && stopPrice) {
      const currentPrice = quoteData?.tradingQuote
        ? (orderSide === 'buy' ? quoteData.tradingQuote.ask : quoteData.tradingQuote.bid)
        : undefined;
      
      const stopResult = validateStopPrice(stopPrice, currentPrice, orderSide);
      newValidations.stopPrice = {
        isValid: stopResult.isValid,
        error: stopResult.error,
        touched: true,
      };
    } else if (orderType === 'stop_loss') {
      newValidations.stopPrice = { isValid: false, error: 'Stop price is required for stop loss orders', touched: true };
    } else {
      newValidations.stopPrice = { isValid: true, touched: false };
    }

    setValidations(newValidations);
  }, [symbol, quantity, price, stopPrice, orderType, orderSide, quoteData]);

  // Calculate order total with validation
  const orderTotal = useMemo(() => {
    const qty = parseFloat(quantity) || 0;
    let pricePerShare = 0;
    let total = 0;
    let isValid = true;
    let error: string | undefined;

    if (orderType === 'market') {
      const marketPrice = quoteData?.tradingQuote
        ? (orderSide === 'buy' ? quoteData.tradingQuote.ask : quoteData.tradingQuote.bid)
        : 0;
      pricePerShare = marketPrice || 150; // Fallback
      total = qty * pricePerShare;
    } else if (orderType === 'limit') {
      pricePerShare = parseFloat(price) || 0;
      total = qty * pricePerShare;
      if (pricePerShare <= 0) {
        isValid = false;
        error = 'Enter a valid limit price';
      }
    } else if (orderType === 'stop_loss') {
      pricePerShare = parseFloat(stopPrice) || 0;
      total = qty * pricePerShare;
      if (pricePerShare <= 0) {
        isValid = false;
        error = 'Enter a valid stop price';
      }
    }

    // Validate total
    if (qty > 0 && pricePerShare > 0) {
      const totalValidation = validateOrderTotal(quantity, pricePerShare.toString());
      if (!totalValidation.isValid) {
        isValid = false;
        error = totalValidation.error;
      }
    }

    return {
      pricePerShare,
      total,
      isValid,
      error,
    };
  }, [quantity, price, stopPrice, orderType, orderSide, quoteData]);

  // Check if form is valid
  const isFormValid = useMemo(() => {
    return (
      validations.symbol.isValid &&
      validations.quantity.isValid &&
      (orderType === 'market' || validations.price.isValid) &&
      (orderType !== 'stop_loss' || validations.stopPrice.isValid) &&
      orderTotal.isValid
    );
  }, [validations, orderType, orderTotal]);

  // Helper to get input style based on validation
  const getInputStyle = (field: string) => {
    const validation = validations[field];
    if (!validation.touched) {
      return styles.input;
    }
    if (validation.isValid) {
      return [styles.input, styles.inputValid];
    }
    return [styles.input, styles.inputError];
  };

  return (
    <View style={styles.container}>
      {/* Order Type Selection */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Order Type</Text>
        <View style={styles.segmentedControl}>
          {(['market', 'limit', 'stop_loss'] as OrderType[]).map((type) => (
            <TouchableOpacity
              key={type}
              style={[
                styles.segment,
                orderType === type && styles.segmentActive,
              ]}
              onPress={() => setOrderType(type)}
            >
              <Text
                style={[
                  styles.segmentText,
                  orderType === type && styles.segmentTextActive,
                ]}
              >
                {type === 'market' ? 'Market' : type === 'limit' ? 'Limit' : 'Stop Loss'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Order Side Selection */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Side</Text>
        <View style={styles.segmentedControl}>
          {(['buy', 'sell'] as OrderSide[]).map((side) => (
            <TouchableOpacity
              key={side}
              style={[
                styles.segment,
                orderSide === side && styles.segmentActive,
              ]}
              onPress={() => setOrderSide(side)}
            >
              <Text
                style={[
                  styles.segmentText,
                  orderSide === side && styles.segmentTextActive,
                ]}
              >
                {side === 'buy' ? 'Buy' : 'Sell'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Symbol Input */}
      <View style={styles.section}>
        <View style={styles.labelRow}>
          <Text style={styles.label}>Symbol</Text>
          {validations.symbol.touched && (
            validations.symbol.isValid ? (
              <Icon name="check-circle" size={16} color={C.green} />
            ) : (
              <Icon name="alert-circle" size={16} color={C.red} />
            )
          )}
        </View>
        <TextInput
          style={getInputStyle('symbol')}
          value={symbol}
          onChangeText={setSymbol}
          placeholder="e.g., AAPL"
          autoCapitalize="characters"
          autoCorrect={false}
          placeholderTextColor={C.sub}
        />
        {validations.symbol.touched && !validations.symbol.isValid && (
          <Text style={styles.errorText}>{validations.symbol.error}</Text>
        )}
      </View>

      {/* Quantity Input */}
      <View style={styles.section}>
        <View style={styles.labelRow}>
          <Text style={styles.label}>Quantity</Text>
          {validations.quantity.touched && (
            validations.quantity.isValid ? (
              <Icon name="check-circle" size={16} color={C.green} />
            ) : (
              <Icon name="alert-circle" size={16} color={C.red} />
            )
          )}
        </View>
        <TextInput
          style={getInputStyle('quantity')}
          value={quantity}
          onChangeText={setQuantity}
          placeholder="Enter quantity"
          keyboardType="numeric"
          placeholderTextColor={C.sub}
        />
        {validations.quantity.touched && !validations.quantity.isValid && (
          <Text style={styles.errorText}>{validations.quantity.error}</Text>
        )}
      </View>

      {/* Price Input (for limit orders) */}
      {orderType === 'limit' && (
        <View style={styles.section}>
          <View style={styles.labelRow}>
            <Text style={styles.label}>Limit Price</Text>
            {validations.price.touched && (
              validations.price.isValid ? (
                <Icon name="check-circle" size={16} color={C.green} />
              ) : (
                <Icon name="alert-circle" size={16} color={C.red} />
              )
            )}
          </View>
          <TextInput
            style={getInputStyle('price')}
            value={price}
            onChangeText={setPrice}
            placeholder="Enter limit price"
            keyboardType="decimal-pad"
            placeholderTextColor={C.sub}
          />
          {validations.price.touched && !validations.price.isValid && (
            <Text style={styles.errorText}>{validations.price.error}</Text>
          )}
          {quoteData?.tradingQuote && (
            <Text style={styles.hintText}>
              Current {orderSide === 'buy' ? 'ask' : 'bid'}: ${orderSide === 'buy' ? quoteData.tradingQuote.ask : quoteData.tradingQuote.bid}
            </Text>
          )}
        </View>
      )}

      {/* Stop Price Input (for stop loss orders) */}
      {orderType === 'stop_loss' && (
        <View style={styles.section}>
          <View style={styles.labelRow}>
            <Text style={styles.label}>Stop Price</Text>
            {validations.stopPrice.touched && (
              validations.stopPrice.isValid ? (
                <Icon name="check-circle" size={16} color={C.green} />
              ) : (
                <Icon name="alert-circle" size={16} color={C.red} />
              )
            )}
          </View>
          <TextInput
            style={getInputStyle('stopPrice')}
            value={stopPrice}
            onChangeText={setStopPrice}
            placeholder="Enter stop price"
            keyboardType="decimal-pad"
            placeholderTextColor={C.sub}
          />
          {validations.stopPrice.touched && !validations.stopPrice.isValid && (
            <Text style={styles.errorText}>{validations.stopPrice.error}</Text>
          )}
          {quoteData?.tradingQuote && (
            <Text style={styles.hintText}>
              Current {orderSide === 'buy' ? 'ask' : 'bid'}: ${orderSide === 'buy' ? quoteData.tradingQuote.ask : quoteData.tradingQuote.bid}
            </Text>
          )}
        </View>
      )}

      {/* Order Total */}
      {quantity && (orderType === 'market' || price || stopPrice) && (
        <View style={styles.section}>
          <View style={styles.totalContainer}>
            <Text style={styles.totalLabel}>Estimated Total</Text>
            <View style={styles.totalAmountContainer}>
              <Text style={styles.totalAmount}>
                ${orderTotal.total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
              {orderTotal.isValid ? (
                <Icon name="check-circle" size={20} color={C.green} style={{ marginLeft: 8 }} />
              ) : (
                <Icon name="alert-circle" size={20} color={C.red} style={{ marginLeft: 8 }} />
              )}
            </View>
          </View>
          {orderTotal.error && (
            <Text style={styles.errorText}>{orderTotal.error}</Text>
          )}
          <Text style={styles.totalHint}>
            {orderType === 'market' ? 'Market' : orderType === 'limit' ? 'Limit' : 'Stop'} order • {orderTotal.total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} shares × ${orderTotal.pricePerShare.toFixed(2)}
          </Text>
        </View>
      )}

      {/* Form Validation Summary */}
      {!isFormValid && (
        <View style={styles.validationSummary}>
          <Icon name="alert-triangle" size={16} color={C.amber} />
          <Text style={styles.validationSummaryText}>
            Please fix the errors above before submitting
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: C.text,
    marginBottom: 8,
  },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: C.bg,
    borderRadius: 8,
    padding: 4,
  },
  segment: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  segmentActive: {
    backgroundColor: C.card,
    shadowColor: C.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 1,
    shadowRadius: 2,
    elevation: 2,
  },
  segmentText: {
    fontSize: 14,
    fontWeight: '500',
    color: C.sub,
  },
  segmentTextActive: {
    color: C.primary,
    fontWeight: '600',
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: C.text,
  },
  input: {
    backgroundColor: C.card,
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 16,
    color: C.text,
  },
  inputValid: {
    borderColor: C.green,
    backgroundColor: C.successSoft,
  },
  inputError: {
    borderColor: C.red,
    backgroundColor: C.dangerSoft,
  },
  errorText: {
    fontSize: 12,
    color: C.red,
    marginTop: 4,
    marginLeft: 4,
  },
  hintText: {
    fontSize: 12,
    color: C.sub,
    marginTop: 4,
    marginLeft: 4,
  },
  totalContainer: {
    backgroundColor: C.blueSoft,
    borderRadius: 8,
    padding: 16,
  },
  totalLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: C.sub,
    marginBottom: 4,
  },
  totalAmountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  totalAmount: {
    fontSize: 24,
    fontWeight: '700',
    color: C.text,
  },
  totalHint: {
    fontSize: 12,
    color: C.sub,
    marginTop: 8,
  },
  validationSummary: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: C.dangerSoft,
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  validationSummaryText: {
    fontSize: 12,
    color: C.red,
    marginLeft: 8,
    flex: 1,
  },
});

