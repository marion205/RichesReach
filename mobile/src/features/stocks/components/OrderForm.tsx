import React, { useState, useEffect, useMemo } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useOrderForm, OrderType, OrderSide } from '../hooks/useOrderForm';
import { useQuery } from '@apollo/client';
import { GET_TRADING_QUOTE } from '../../../graphql/tradingQueries';
import { TradingQuote, LocalCostState, OrderTotalCalculation } from '../types';
import logger from '../../../utils/logger';
import {
  validateSymbol,
  validateQuantity,
  validateLimitPrice,
  validateStopPrice,
} from '../../../utils/validation';
import { getMockPrice } from '../constants/mockPrices';
import EducationalTooltip from '../../../components/common/EducationalTooltip';
import { RiskRewardDiagram } from '../../../components/common/RiskRewardDiagram';

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
  quoteData?: { tradingQuote?: TradingQuote };
  quoteLoading?: boolean;
  onSBLOCPress?: () => void;
}

export const OrderForm: React.FC<OrderFormProps> = ({
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

  // Local state for immediate cost display (bypasses Apollo loading gate)
  const [localCost, setLocalCost] = useState<LocalCostState | null>(null);

  // Validation state for real-time feedback
  const [validations, setValidations] = useState<Record<string, { isValid: boolean; error?: string; touched: boolean }>>({
    symbol: { isValid: true, touched: false },
    quantity: { isValid: true, touched: false },
    price: { isValid: true, touched: false },
    stopPrice: { isValid: true, touched: false },
  });

  // Mock prices imported from constants

  // Real-time validation
  useEffect(() => {
    const newValidations: Record<string, { isValid: boolean; error?: string; touched: boolean }> = {};

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
  }, [symbol, quantity, price, stopPrice, orderType, orderSide, quoteData]); // Removed 'validations' from deps to prevent infinite loops

  // Immediate mock fallback + background real data update
  useEffect(() => {
    const qty = parseFloat(quantity) || 0;
    if (!symbol || qty <= 0) {
      setLocalCost(null);
      return;
    }

    // ALWAYS show mock estimate immediately (no waiting for GraphQL)
    const mockPrice = getMockPrice(symbol);
    const estimatedTotal = qty * mockPrice;
    
    // Set mock immediately
    setLocalCost({
      pricePerShare: mockPrice,
      total: estimatedTotal,
      source: 'Est. Market Price',
      isLive: false,
    });

    // If we have real quote data, upgrade to live price (non-blocking)
    if (quoteData?.tradingQuote) {
      const marketPrice = orderSide === 'buy'
        ? (quoteData.tradingQuote.ask || 0)
        : (quoteData.tradingQuote.bid || 0);
      
      if (marketPrice > 0) {
        // Update to live price seamlessly
        setLocalCost({
          pricePerShare: marketPrice,
          total: qty * marketPrice,
          source: orderSide === 'buy' ? 'Ask' : 'Bid',
          isLive: true,
        });
      }
    }
  }, [symbol, quantity, orderSide, quoteData?.tradingQuote]);

  // Safety net: ensure localCost is set even if first useEffect didn't run
  useEffect(() => {
    const qty = parseFloat(quantity) || 0;
    if (symbol && qty > 0 && !localCost) {
      const mockPrice = getMockPrice(symbol);
      setLocalCost({
        pricePerShare: mockPrice,
        total: qty * mockPrice,
        source: 'Est. Market Price',
        isLive: false,
      });
    }
  }, [symbol, quantity, localCost]);

  // Calculate order total estimate (now uses localCost as primary source)
  const orderTotal = React.useMemo(() => {
    const qty = parseFloat(quantity) || 0;
    let pricePerShare = 0;
    let priceSource = '';
    let isLoading = false;
    let isEstimated = false;

    // Debug logging
    if (symbol) {
      logger.log('💰 OrderTotal calculation:', {
        symbol,
        qty,
        hasQuoteData: !!quoteData?.tradingQuote,
        quoteData: quoteData?.tradingQuote,
        quoteLoading,
        orderType,
        orderSide,
      });
    }

    const marketPrice = quoteData?.tradingQuote
      ? (orderSide === 'buy'
          ? (quoteData.tradingQuote.ask || 0)
          : (quoteData.tradingQuote.bid || 0))
      : 0;

    // Show loading only if we're actively fetching and don't have cached data
    if (quoteLoading && !quoteData?.tradingQuote) {
      isLoading = true;
    }
    
    // If we have a symbol and quantity but no quote after loading completes, use estimated price
    // This prevents infinite loading states
    const hasSymbolAndQty = symbol && qty > 0;
    if (hasSymbolAndQty && !quoteData?.tradingQuote && !quoteLoading) {
      // Use a reasonable default estimate based on symbol
      // This is better than showing nothing
      const defaultPrice = getMockPrice(symbol);
      
      if (orderType === 'market' && marketPrice === 0) {
        pricePerShare = defaultPrice;
        priceSource = 'Est. Market Price';
        isEstimated = true;
      }
    }

    if (orderType === 'limit') {
      if (price) {
        // User entered limit price - use it directly
        pricePerShare = parseFloat(price) || 0;
        priceSource = 'Limit Price';
        isLoading = false;
      } else if (localCost) {
        // Show estimate from localCost while user types
        pricePerShare = localCost.pricePerShare;
        priceSource = orderSide === 'buy' ? 'Ask (Est.)' : 'Bid (Est.)';
        isEstimated = true;
        isLoading = false;
      } else if (marketPrice > 0) {
        // Fallback to quoteData if available
        pricePerShare = marketPrice;
        priceSource = orderSide === 'buy' ? 'Ask (Est.)' : 'Bid (Est.)';
        isEstimated = true;
        isLoading = false;
      } else {
        // Only show loading if we truly have nothing
        isLoading = quoteLoading && !localCost;
      }
    } else if (orderType === 'stop_loss') {
      if (stopPrice) {
        // User entered stop price - use it directly
        pricePerShare = parseFloat(stopPrice) || 0;
        priceSource = 'Stop Price';
        isLoading = false;
      } else if (localCost) {
        // Show estimate from localCost while user types
        pricePerShare = localCost.pricePerShare;
        priceSource = orderSide === 'buy' ? 'Ask (Est.)' : 'Bid (Est.)';
        isEstimated = true;
        isLoading = false;
      } else if (marketPrice > 0) {
        // Fallback to quoteData if available
        pricePerShare = marketPrice;
        priceSource = orderSide === 'buy' ? 'Ask (Est.)' : 'Bid (Est.)';
        isEstimated = true;
        isLoading = false;
      } else {
        // Only show loading if we truly have nothing
        isLoading = quoteLoading && !localCost;
      }
    } else if (orderType === 'market') {
      // ALWAYS use localCost first (instant display, bypasses Apollo loading)
      if (localCost) {
        pricePerShare = localCost.pricePerShare;
        priceSource = localCost.source;
        isEstimated = !localCost.isLive;
        // Never show loading if we have localCost
        isLoading = false;
      } else if (quoteData?.tradingQuote) {
        // Fallback to quoteData if localCost somehow isn't set
        pricePerShare = marketPrice;
        priceSource = orderSide === 'buy' ? 'Ask' : 'Bid';
        isLoading = false;
      } else {
        // Only show loading if we truly have nothing (shouldn't happen with localCost)
        isLoading = quoteLoading && !localCost;
      }
    }

    const hasValidEstimate = qty > 0 && pricePerShare > 0 && symbol;
    const shouldShow = hasValidEstimate || (isLoading && qty > 0 && symbol);

    // Determine if we're using mock/estimated data
    const isMock = isEstimated || (localCost && !localCost.isLive) || (!quoteData?.tradingQuote && !quoteLoading && pricePerShare > 0);

    return {
      shouldShow,
      qty,
      pricePerShare,
      priceSource,
      isLoading,
      isEstimated,
      isMock,
      total: qty * pricePerShare,
    };
  }, [quantity, price, stopPrice, orderType, orderSide, symbol, quoteData, quoteLoading, localCost]);

  return (
    <>
      {/* Order Type */}
      <Text style={styles.inputLabel}>Order Type</Text>
      <View style={styles.pillRow}>
        {(['market', 'limit', 'stop_loss'] as OrderType[]).map((t) => (
          <TouchableOpacity
            key={t}
            onPress={() => setOrderType(t)}
            style={[styles.pill, orderType === t && styles.pillActive]}
          >
            <Text style={[styles.pillText, orderType === t && styles.pillTextActive]}>
              {t.replace('_', ' ').toUpperCase()}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Side */}
      <Text style={[styles.inputLabel, { marginTop: 16 }]}>Side</Text>
      <View style={styles.pillRow}>
        {(['buy', 'sell'] as OrderSide[]).map((s) => (
          <TouchableOpacity
            key={s}
            onPress={() => setOrderSide(s)}
            style={[
              styles.pill,
              orderSide === s && (s === 'buy' ? styles.pillBuy : styles.pillSell),
            ]}
          >
            <Text style={[styles.pillText, orderSide === s && styles.pillTextActive]}>
              {s.toUpperCase()}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* SBLOC Alternative for Sell Orders */}
      {orderSide === 'sell' && onSBLOCPress && (
        <View style={styles.sblocAlternative}>
          <View style={styles.sblocAlternativeHeader}>
            <Icon name="lightbulb" size={16} color="#F59E0B" />
            <Text style={styles.sblocAlternativeTitle}>Consider SBLOC Instead?</Text>
          </View>
          <Text style={styles.sblocAlternativeText}>
            Instead of selling your shares, you could borrow against your portfolio to access
            liquidity while keeping your investments growing.
          </Text>
          <TouchableOpacity style={styles.sblocAlternativeBtn} onPress={onSBLOCPress}>
            <Icon name="trending-up" size={16} color="#F59E0B" />
            <Text style={styles.sblocAlternativeBtnText}>Learn About SBLOC</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Inputs */}
      <View style={{ marginTop: 16 }}>
        <View style={styles.labelRow}>
          <Text style={styles.inputLabel}>Symbol</Text>
          {validations.symbol.touched && (
            validations.symbol.isValid ? (
              <Icon name="check-circle" size={16} color={C.green} />
            ) : (
              <Icon name="alert-circle" size={16} color={C.red} />
            )
          )}
        </View>
        <TextInput
          style={[
            styles.input,
            validations.symbol.touched && (validations.symbol.isValid ? styles.inputValid : styles.inputError),
          ]}
          value={symbol}
          onChangeText={setSymbol}
          placeholder="e.g., AAPL"
          autoCapitalize="characters"
          autoCorrect={false}
          accessibilityLabel="Stock symbol input"
          accessibilityHint="Enter the stock symbol you want to trade, for example AAPL for Apple"
          accessibilityRole="textbox"
        />
        {validations.symbol.touched && !validations.symbol.isValid && (
          <Text style={styles.errorText}>{validations.symbol.error}</Text>
        )}
      </View>

      <View style={{ marginTop: 12 }}>
        <View style={styles.labelRow}>
          <Text style={styles.inputLabel}>Quantity</Text>
          {validations.quantity.touched && (
            validations.quantity.isValid ? (
              <Icon name="check-circle" size={16} color={C.green} />
            ) : (
              <Icon name="alert-circle" size={16} color={C.red} />
            )
          )}
        </View>
        <TextInput
          style={[
            styles.input,
            validations.quantity.touched && (validations.quantity.isValid ? styles.inputValid : styles.inputError),
          ]}
          value={quantity}
          onChangeText={setQuantity}
          placeholder="Number of shares"
          keyboardType="numeric"
          accessibilityLabel="Quantity input"
          accessibilityHint="Enter the number of shares you want to buy or sell"
          accessibilityRole="textbox"
        />
        {validations.quantity.touched && !validations.quantity.isValid && (
          <Text style={styles.errorText}>{validations.quantity.error}</Text>
        )}
      </View>

      {orderType === 'limit' && (
        <View style={{ marginTop: 12 }}>
          <View style={styles.labelRow}>
            <Text style={styles.inputLabel}>Limit Price</Text>
            {validations.price.touched && (
              validations.price.isValid ? (
                <Icon name="check-circle" size={16} color={C.green} />
              ) : (
                <Icon name="alert-circle" size={16} color={C.red} />
              )
            )}
          </View>
          <TextInput
            style={[
              styles.input,
              validations.price.touched && (validations.price.isValid ? styles.inputValid : styles.inputError),
            ]}
            value={price}
            onChangeText={setPrice}
            placeholder="Price per share"
            keyboardType="numeric"
            accessibilityLabel="Limit price input"
            accessibilityHint="Enter the maximum price you're willing to pay per share for a buy order, or minimum price for a sell order"
            accessibilityRole="textbox"
          />
          {validations.price.touched && !validations.price.isValid && (
            <Text style={styles.errorText}>{validations.price.error}</Text>
          )}
          {quoteData?.tradingQuote && (
            <Text style={styles.hintText}>
              Current {orderSide === 'buy' ? 'ask' : 'bid'}: ${orderSide === 'buy' ? quoteData.tradingQuote.ask?.toFixed(2) : quoteData.tradingQuote.bid?.toFixed(2)}
            </Text>
          )}
        </View>
      )}

      {orderType === 'stop_loss' && (
        <View style={{ marginTop: 12 }}>
          <View style={styles.labelRow}>
            <EducationalTooltip
              term="Stop Loss"
              explanation="A stop loss automatically sells your position if the price reaches this level, limiting your maximum loss. For example, if you buy at $100 and set a stop at $95, your maximum loss is $5 per share. Use ATR (Average True Range) to determine stop distance: 1.5-2x ATR for day trading, 2-3x ATR for swing trading."
              position="top"
            >
              <Text style={styles.inputLabel}>Stop Price</Text>
            </EducationalTooltip>
            {validations.stopPrice.touched && (
              validations.stopPrice.isValid ? (
                <Icon name="check-circle" size={16} color={C.green} />
              ) : (
                <Icon name="alert-circle" size={16} color={C.red} />
              )
            )}
          </View>
          <TextInput
            style={[
              styles.input,
              validations.stopPrice.touched && (validations.stopPrice.isValid ? styles.inputValid : styles.inputError),
            ]}
            value={stopPrice}
            onChangeText={setStopPrice}
            placeholder="Stop price"
            keyboardType="numeric"
            accessibilityLabel="Stop price input"
            accessibilityHint="Enter the stop price that will trigger this order"
            accessibilityRole="textbox"
          />
          {validations.stopPrice.touched && !validations.stopPrice.isValid && (
            <Text style={styles.errorText}>{validations.stopPrice.error}</Text>
          )}
          {quoteData?.tradingQuote && (
            <Text style={styles.hintText}>
              Current {orderSide === 'buy' ? 'ask' : 'bid'}: ${orderSide === 'buy' ? quoteData.tradingQuote.ask?.toFixed(2) : quoteData.tradingQuote.bid?.toFixed(2)}
            </Text>
          )}
          {/* Risk Preview for Stop Loss */}
          {stopPrice && quantity && quoteData?.tradingQuote && (
            <>
              <View style={styles.riskPreviewCard}>
                <View style={styles.riskPreviewHeader}>
                  <Icon name="shield" size={16} color={C.primary} />
                  <Text style={styles.riskPreviewTitle}>Risk Preview</Text>
                </View>
                {(() => {
                  const currentPrice = orderSide === 'buy' ? quoteData.tradingQuote.ask : quoteData.tradingQuote.bid;
                  const stopPriceNum = parseFloat(stopPrice) || 0;
                  const qtyNum = parseFloat(quantity) || 0;
                  const riskPerShare = Math.abs(currentPrice - stopPriceNum);
                  const totalRisk = riskPerShare * qtyNum;
                  return (
                    <>
                      <View style={styles.riskPreviewRow}>
                        <Text style={styles.riskPreviewLabel}>Risk per share:</Text>
                        <Text style={styles.riskPreviewValue}>${riskPerShare.toFixed(2)}</Text>
                      </View>
                      <View style={styles.riskPreviewRow}>
                        <Text style={styles.riskPreviewLabel}>Total risk:</Text>
                        <Text style={[styles.riskPreviewValue, { color: C.red }]}>${totalRisk.toFixed(2)}</Text>
                      </View>
                    </>
                  );
                })()}
              </View>
              {/* Risk/Reward Diagram */}
              {(() => {
                const currentPrice = orderSide === 'buy' ? quoteData.tradingQuote.ask : quoteData.tradingQuote.bid;
                const stopPriceNum = parseFloat(stopPrice) || 0;
                const risk = Math.abs(currentPrice - stopPriceNum);
                // Calculate target based on 2:1 risk/reward ratio
                const targetPrice = orderSide === 'buy' 
                  ? currentPrice + (risk * 2)
                  : currentPrice - (risk * 2);
                return (
                  <View style={{ marginTop: 12 }}>
                    <RiskRewardDiagram
                      entryPrice={currentPrice}
                      stopPrice={stopPriceNum}
                      targetPrice={targetPrice}
                      side={orderSide.toUpperCase() as 'BUY' | 'SELL'}
                      showLabels={true}
                      height={180}
                    />
                  </View>
                );
              })()}
            </>
          )}
        </View>
      )}

      <View style={{ marginTop: 12, marginBottom: 16 }}>
        <Text style={styles.inputLabel}>Notes (Optional)</Text>
        <TextInput
          style={[styles.input, { height: 84, textAlignVertical: 'top' }]}
          value={notes}
          onChangeText={setNotes}
          multiline
          placeholder="Add a note about this order"
          accessibilityLabel="Order notes input"
          accessibilityHint="Optional: Add a note or reminder about this order"
          accessibilityRole="textbox"
        />
      </View>

      {/* Quote */}
      {symbol && quoteData?.tradingQuote && (
        <View style={styles.quoteBox}>
          <View style={styles.quoteHeader}>
            <Text style={styles.quoteTitle}>Quote • {symbol.toUpperCase()}</Text>
            <View style={styles.quoteHeaderRight}>
              <View style={styles.liveBadge}>
                <View style={styles.liveDot} />
                <Text style={styles.liveText}>Live</Text>
              </View>
            </View>
          </View>
          <View style={styles.rowBetween}>
            <Text style={styles.sub}>Bid</Text>
            <Text style={styles.value}>
              ${quoteData.tradingQuote.bid?.toFixed(2)}
            </Text>
          </View>
          <View style={styles.rowBetween}>
            <Text style={styles.sub}>Ask</Text>
            <Text style={styles.value}>
              ${quoteData.tradingQuote.ask?.toFixed(2)}
            </Text>
          </View>
        </View>
      )}

      {/* Order Total Estimate */}
      {orderTotal.shouldShow && (
        <View style={styles.orderTotalBox}>
          <View style={styles.orderTotalHeader}>
            <Text style={styles.orderTotalLabel}>
              {orderTotal.isEstimated ? 'Estimated ' : ''}
              {orderSide === 'buy' ? 'Cost' : 'Proceeds'}
              {orderTotal.isEstimated && ' (at market)'}
            </Text>
            {orderTotal.isLoading ? (
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <ActivityIndicator size="small" color={C.primary} />
                <Text style={[styles.orderTotalDetail, { fontSize: 12 }]}>Loading...</Text>
              </View>
            ) : (
              <Text
                style={[
                  styles.orderTotalAmount,
                  orderTotal.isMock && styles.orderTotalAmountMock,
                ]}
              >
                ${orderTotal.total.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            )}
          </View>
          {!orderTotal.isLoading && orderTotal.pricePerShare > 0 && (
            <View style={styles.orderTotalBreakdown}>
              <View style={styles.orderTotalRow}>
                <Text style={styles.orderTotalDetail}>
                  {orderTotal.qty} {orderTotal.qty === 1 ? 'share' : 'shares'} × $
                  {orderTotal.pricePerShare.toFixed(2)} ({orderTotal.priceSource})
                </Text>
                {orderTotal.isMock && (
                  <View style={styles.mockBadge}>
                    <Text style={styles.mockBadgeText}>Estimated</Text>
                  </View>
                )}
              </View>
              {orderTotal.isMock ? (
                <Text style={[styles.orderTotalDetail, { marginTop: 4, fontSize: 12, color: C.sub }]}>
                  Updating live price...
                </Text>
              ) : (
                <View style={styles.livePriceIndicator}>
                  <View style={styles.liveDotSmall} />
                  <Text style={[styles.orderTotalDetail, { marginTop: 4, fontSize: 12, color: C.green }]}>
                    Live price
                  </Text>
                </View>
              )}
              {orderTotal.isEstimated && !orderTotal.isMock && (
                <Text style={[styles.orderTotalDetail, { marginTop: 4, fontSize: 12 }]}>
                  Enter {orderType === 'limit' ? 'limit' : 'stop'} price above to see exact
                  total
                </Text>
              )}
            </View>
          )}
          {orderTotal.isLoading && (
            <View style={styles.orderTotalBreakdown}>
              <Text style={styles.orderTotalDetail}>Fetching current market price...</Text>
            </View>
          )}
        </View>
      )}
    </>
  );
};

const styles = StyleSheet.create({
  inputLabel: {
    fontWeight: '700',
    color: C.text,
    marginBottom: 6,
  },
  input: {
    backgroundColor: C.card,
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
  },
  pillRow: {
    flexDirection: 'row',
    gap: 8,
  },
  pill: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 999,
    alignItems: 'center',
    backgroundColor: '#EEF2F7',
  },
  pillActive: {
    backgroundColor: C.primary,
  },
  pillBuy: {
    backgroundColor: C.green,
  },
  pillSell: {
    backgroundColor: C.red,
  },
  pillText: {
    fontWeight: '700',
    color: '#5B6473',
  },
  pillTextActive: {
    color: '#fff',
  },
  benchmarkContainer: {
    marginTop: 12,
    marginBottom: 8,
    alignItems: 'flex-end',
  },
  quoteBox: {
    backgroundColor: C.blueSoft,
    borderRadius: 12,
    padding: 12,
    marginTop: 8,
    gap: 6,
  },
  quoteHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  quoteHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  quoteTitle: {
    fontWeight: '800',
    color: C.text,
  },
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: C.successSoft,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: C.green,
  },
  liveText: {
    fontSize: 11,
    fontWeight: '700',
    color: C.green,
  },
  livePriceIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  liveDotSmall: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: C.green,
  },
  rowBetween: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  sub: {
    fontSize: 13,
    color: C.sub,
  },
  value: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  orderTotalBox: {
    backgroundColor: '#F0F9FF',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  orderTotalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  orderTotalLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: C.sub,
  },
  orderTotalAmount: {
    fontSize: 24,
    fontWeight: '800',
    color: C.text,
  },
  orderTotalAmountMock: {
    opacity: 0.7,
  },
  orderTotalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 8,
  },
  mockBadge: {
    backgroundColor: '#FFF7ED',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  mockBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#92400E',
  },
  orderTotalBreakdown: {
    marginTop: 4,
  },
  orderTotalDetail: {
    fontSize: 13,
    color: C.sub,
    fontStyle: 'italic',
  },
  sblocAlternative: {
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  sblocAlternativeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  sblocAlternativeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#92400E',
    marginLeft: 8,
  },
  sblocAlternativeText: {
    fontSize: 14,
    color: '#92400E',
    lineHeight: 20,
    marginBottom: 12,
  },
  sblocAlternativeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F59E0B',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  sblocAlternativeBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginLeft: 6,
  },
  riskPreviewCard: {
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 12,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  riskPreviewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  riskPreviewTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#92400E',
    marginLeft: 6,
  },
  riskPreviewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  riskPreviewLabel: {
    fontSize: 13,
    color: '#92400E',
  },
  riskPreviewValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#92400E',
  },
});

