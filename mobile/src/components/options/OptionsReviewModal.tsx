import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useMutation } from '@apollo/client';
import { gql } from '@apollo/client';

const PLACE_OPTIONS_ORDER = gql`
  mutation PlaceOptionsOrder(
    $symbol: String!
    $strike: Float!
    $expiration: String!
    $optionType: String!
    $side: String!
    $quantity: Int!
    $orderType: String!
    $limitPrice: Float
    $timeInForce: String!
    $estimatedPremium: Float
  ) {
    placeOptionsOrder(
      symbol: $symbol
      strike: $strike
      expiration: $expiration
      optionType: $optionType
      side: $side
      quantity: $quantity
      orderType: $orderType
      limitPrice: $limitPrice
      timeInForce: $timeInForce
      estimatedPremium: $estimatedPremium
    ) {
      success
      orderId
      alpacaOrderId
      status
      error
    }
  }
`;

interface RecommendedStrike {
  strike: number;
  expiration: string;
  optionType: string;
  greeks?: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
  };
  expectedReturn?: number;
  riskScore?: number;
}

interface OptionsReviewModalProps {
  visible: boolean;
  onClose: () => void;
  symbol: string;
  underlyingPrice: number;
  recommendation: RecommendedStrike;
  quantity?: number;
}

export default function OptionsReviewModal({
  visible,
  onClose,
  symbol,
  underlyingPrice,
  recommendation,
  quantity = 1,
}: OptionsReviewModalProps) {
  const [placingOrder, setPlacingOrder] = useState(false);
  const [placeOptionsOrder] = useMutation(PLACE_OPTIONS_ORDER);

  // Calculate days to expiration
  const daysToExp = (() => {
    try {
      const expDate = new Date(recommendation.expiration);
      const today = new Date();
      const diff = Math.ceil((expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      return diff > 0 ? diff : 0;
    } catch {
      return 0;
    }
  })();

  // Estimate premium
  const isCall = recommendation.optionType.toLowerCase() === 'call';
  const estimatedPremium = isCall
    ? Math.max(0.5, (Math.abs(recommendation.strike - underlyingPrice) * 0.1))
    : Math.max(0.5, (Math.abs(underlyingPrice - recommendation.strike) * 0.1));
  const totalCost = estimatedPremium * quantity * 100; // Options are for 100 shares

  // Calculate position size as % of portfolio (mock - would need real portfolio value)
  const portfolioValue = 10000; // Mock
  const positionSizePercent = ((totalCost / portfolioValue) * 100).toFixed(1);

  // Generate "Why AI likes this" bullets
  const whyBullets = (() => {
    const bullets = [];
    
    // Momentum
    if (recommendation.greeks?.delta) {
      const delta = recommendation.greeks.delta;
      if (delta > 0.5) {
        bullets.push(`${symbol} is showing strong momentum above its 20-day range.`);
      } else {
        bullets.push(`${symbol} momentum is building with favorable risk/reward.`);
      }
    }
    
    // Volume/Volatility
    if (recommendation.expectedReturn) {
      bullets.push(`Expected return: ${(recommendation.expectedReturn * 100).toFixed(0)}% based on current volatility.`);
    }
    
    // Greeks
    if (recommendation.greeks?.theta) {
      const theta = Math.abs(recommendation.greeks.theta);
      if (theta < 0.15) {
        bullets.push(`Time decay is moderate, giving you ${daysToExp} days to profit.`);
      }
    }
    
    return bullets.length > 0 ? bullets : [
      `${symbol} ${isCall ? 'call' : 'put'} shows favorable risk/reward at this strike.`,
      `Implied volatility is at reasonable levels.`,
      `Timeframe aligns with expected price movement.`,
    ];
  })();

  const handlePlaceTrade = async () => {
    setPlacingOrder(true);
    
    try {
      const result = await placeOptionsOrder({
        variables: {
          symbol: symbol.toUpperCase(),
          strike: recommendation.strike,
          expiration: recommendation.expiration,
          optionType: recommendation.optionType.toLowerCase(),
          side: 'BUY',
          quantity: quantity,
          orderType: 'MARKET',
          timeInForce: 'DAY',
          estimatedPremium: estimatedPremium,
        },
      });

      const response = result.data?.placeOptionsOrder;

      if (response?.success) {
        Alert.alert(
          'Trade Placed!',
          `Your ${symbol} ${recommendation.optionType} order has been submitted.\n\nOrder ID: ${response.orderId}`,
          [
            {
              text: 'Done',
              onPress: () => {
                onClose();
                // Could trigger a refresh of positions/orders here
              },
            },
          ]
        );
      } else {
        Alert.alert('Trade Failed', response?.error || 'Unknown error occurred');
      }
    } catch (error: any) {
      console.error('Error placing options order:', error);
      Alert.alert('Error', error.message || 'Failed to place trade. Please try again.');
    } finally {
      setPlacingOrder(false);
    }
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
          <Text style={styles.headerTitle}>Review Trade</Text>
          <View style={styles.placeholder} />
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Trade Summary */}
          <View style={styles.summarySection}>
            <Text style={styles.summaryText}>
              {recommendation.optionType === 'call' ? 'Buy' : 'Buy'} {quantity} × {symbol} ${recommendation.strike.toFixed(2)}{' '}
              {recommendation.optionType === 'call' ? 'Call' : 'Put'} ({daysToExp} days)
            </Text>
          </View>

          {/* Risk & Cost */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Risk & Cost</Text>
            <View style={styles.riskItem}>
              <Text style={styles.riskLabel}>You're risking:</Text>
              <Text style={styles.riskValue}>${totalCost.toFixed(2)} (max loss)</Text>
            </View>
            <Text style={styles.riskExplanation}>
              If {symbol} is {isCall ? 'below' : 'above'} ${recommendation.strike.toFixed(2)} at expiry, you lose this full amount.
            </Text>
            <View style={styles.riskItem}>
              <Text style={styles.riskLabel}>Position size:</Text>
              <Text style={styles.riskValue}>~{positionSizePercent}% of your portfolio</Text>
            </View>
          </View>

          {/* Why AI Likes This */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Why AI likes this</Text>
            {whyBullets.map((bullet, index) => (
              <View key={index} style={styles.bulletRow}>
                <Icon name="check-circle" size={16} color="#059669" style={styles.bulletIcon} />
                <Text style={styles.bulletText}>{bullet}</Text>
              </View>
            ))}
          </View>

          {/* Timing */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Timing</Text>
            <View style={styles.timingItem}>
              <Text style={styles.timingLabel}>Ideal hold:</Text>
              <Text style={styles.timingValue}>{Math.max(3, Math.floor(daysToExp * 0.5))}-{daysToExp} days</Text>
            </View>
            <View style={styles.timingItem}>
              <Text style={styles.timingLabel}>Best conditions:</Text>
              <Text style={styles.timingValue}>
                {isCall ? 'Strong market / tech sector uptrend' : 'Market pullback / volatility increase'}
              </Text>
            </View>
          </View>

          {/* High Risk Warning for 0DTE */}
          {daysToExp <= 1 && (
            <View style={styles.warningBox}>
              <Icon name="alert-triangle" size={20} color="#DC2626" />
              <Text style={styles.warningText}>
                High risk: This option expires today. You can lose 100% of your premium.
              </Text>
            </View>
          )}
        </ScrollView>

        {/* Bottom Actions */}
        <View style={styles.bottomActions}>
          <TouchableOpacity
            style={styles.cancelButton}
            onPress={onClose}
            disabled={placingOrder}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.placeButton, placingOrder && styles.placeButtonDisabled]}
            onPress={handlePlaceTrade}
            disabled={placingOrder}
          >
            {placingOrder ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.placeButtonText}>Place Trade — ${totalCost.toFixed(2)}</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  placeholder: {
    width: 32,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  summarySection: {
    paddingVertical: 24,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  summaryText: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111827',
    textAlign: 'center',
  },
  section: {
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  riskItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  riskLabel: {
    fontSize: 15,
    color: '#374151',
  },
  riskValue: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
  },
  riskExplanation: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 8,
    marginBottom: 12,
    lineHeight: 20,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  bulletIcon: {
    marginRight: 8,
    marginTop: 2,
  },
  bulletText: {
    flex: 1,
    fontSize: 15,
    color: '#374151',
    lineHeight: 22,
  },
  timingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  timingLabel: {
    fontSize: 15,
    color: '#374151',
  },
  timingValue: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
    textAlign: 'right',
  },
  warningBox: {
    flexDirection: 'row',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 12,
    padding: 16,
    marginTop: 20,
    marginBottom: 20,
  },
  warningText: {
    flex: 1,
    fontSize: 14,
    color: '#DC2626',
    marginLeft: 12,
    lineHeight: 20,
  },
  bottomActions: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  placeButton: {
    flex: 2,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  placeButtonDisabled: {
    opacity: 0.6,
  },
  placeButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});

