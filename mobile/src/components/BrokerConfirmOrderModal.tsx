/**
 * Broker Confirm Order Modal
 * Shows order details, guardrails, and compliance disclosures before placing order
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface BrokerConfirmOrderModalProps {
  visible: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  orderDetails: {
    symbol: string;
    side: 'BUY' | 'SELL';
    orderType: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
    quantity: number;
    limitPrice?: number;
    stopPrice?: number;
    estimatedPrice: number;
    notional: number;
  };
  accountInfo?: {
    buyingPower: number;
    cash: number;
    dailyNotionalUsed: number;
    dailyNotionalRemaining: number;
    kycStatus: string;
    tradingBlocked: boolean;
    patternDayTrader: boolean;
  };
  guardrailWarnings?: string[];
}

export default function BrokerConfirmOrderModal({
  visible,
  onClose,
  onConfirm,
  orderDetails,
  accountInfo,
  guardrailWarnings = [],
}: BrokerConfirmOrderModalProps) {
  const [confirming, setConfirming] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const handleConfirm = async () => {
    if (!agreedToTerms) {
      Alert.alert('Agreement Required', 'Please read and agree to the terms to place an order.');
      return;
    }

    setConfirming(true);
    try {
      await onConfirm();
      onClose();
    } catch (error: any) {
      Alert.alert('Order Failed', error.message || 'Failed to place order. Please try again.');
    } finally {
      setConfirming(false);
    }
  };

  const canPlaceOrder = accountInfo?.kycStatus === 'APPROVED' && !accountInfo?.tradingBlocked;
  const hasEnoughBuyingPower = accountInfo
    ? orderDetails.side === 'BUY' && orderDetails.notional <= accountInfo.buyingPower
    : true;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          <View style={styles.header}>
            <Text style={styles.title}>Confirm Order</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color="#333" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Order Details */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Order Details</Text>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Symbol:</Text>
                <Text style={styles.detailValue}>{orderDetails.symbol}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Side:</Text>
                <Text
                  style={[
                    styles.detailValue,
                    orderDetails.side === 'BUY' ? styles.buyText : styles.sellText,
                  ]}
                >
                  {orderDetails.side}
                </Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Type:</Text>
                <Text style={styles.detailValue}>{orderDetails.orderType}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Quantity:</Text>
                <Text style={styles.detailValue}>{orderDetails.quantity} shares</Text>
              </View>
              {orderDetails.limitPrice && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Limit Price:</Text>
                  <Text style={styles.detailValue}>${orderDetails.limitPrice.toFixed(2)}</Text>
                </View>
              )}
              {orderDetails.stopPrice && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Stop Price:</Text>
                  <Text style={styles.detailValue}>${orderDetails.stopPrice.toFixed(2)}</Text>
                </View>
              )}
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Estimated Value:</Text>
                <Text style={styles.detailValue}>${orderDetails.notional.toFixed(2)}</Text>
              </View>
            </View>

            {/* Account Info */}
            {accountInfo && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Account Status</Text>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Buying Power:</Text>
                  <Text style={styles.detailValue}>${accountInfo.buyingPower.toFixed(2)}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Cash:</Text>
                  <Text style={styles.detailValue}>${accountInfo.cash.toFixed(2)}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Daily Limit Used:</Text>
                  <Text style={styles.detailValue}>
                    ${accountInfo.dailyNotionalUsed.toFixed(2)} / $50,000
                  </Text>
                </View>
                {accountInfo.patternDayTrader && (
                  <View style={styles.warningBox}>
                    <Ionicons name="warning" size={16} color="#FF9500" />
                    <Text style={styles.warningText}>
                      Pattern Day Trader: You have {3 - (accountInfo.dailyNotionalUsed > 0 ? 1 : 0)} day trades remaining
                    </Text>
                  </View>
                )}
              </View>
            )}

            {/* Guardrail Warnings */}
            {guardrailWarnings.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Warnings</Text>
                {guardrailWarnings.map((warning, index) => (
                  <View key={index} style={styles.warningBox}>
                    <Ionicons name="alert-circle" size={16} color="#FF9500" />
                    <Text style={styles.warningText}>{warning}</Text>
                  </View>
                ))}
              </View>
            )}

            {/* Compliance Disclosures */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Important Disclosures</Text>
              
              {/* Brokerage Services Disclosure */}
              <View style={styles.disclosureBox}>
                <Text style={styles.disclosureTextBold}>
                  Brokerage services provided by Alpaca Securities LLC, member FINRA/SIPC.
                </Text>
              </View>
              
              {/* Not Investment Advice */}
              <Text style={styles.disclosureText}>
                <Text style={styles.disclosureTextBold}>Not Investment Advice:</Text> This is not
                investment advice. All recommendations, analysis, and information provided by
                RichesReach are for educational and informational purposes only. You should consult
                with a qualified financial advisor before making investment decisions.
              </Text>
              
              {/* Risk of Loss */}
              <Text style={styles.disclosureText}>
                <Text style={styles.disclosureTextBold}>Risk of Loss:</Text> Trading involves
                substantial risk of loss. You may lose more than your initial investment. Past
                performance does not guarantee future results. Only invest money you can afford to
                lose.
              </Text>
              
              {/* Order Type Education */}
              {orderDetails.orderType === 'MARKET' && (
                <View style={styles.disclosureBox}>
                  <Text style={styles.disclosureTextBold}>Market Order:</Text>
                  <Text style={styles.disclosureText}>
                    Market orders execute immediately at the current market price, which may differ
                    from the displayed price. Market orders provide immediate execution but may
                    result in price slippage, especially for large orders or during volatile market
                    conditions.
                  </Text>
                </View>
              )}
              {orderDetails.orderType === 'LIMIT' && (
                <View style={styles.disclosureBox}>
                  <Text style={styles.disclosureTextBold}>Limit Order:</Text>
                  <Text style={styles.disclosureText}>
                    Limit orders execute only at your specified price or better. There is no
                    guarantee your order will be filled. Limit orders may partially fill or not
                    fill at all if the market price does not reach your limit.
                  </Text>
                </View>
              )}
              {orderDetails.orderType === 'STOP' && (
                <View style={styles.disclosureBox}>
                  <Text style={styles.disclosureTextBold}>Stop Order:</Text>
                  <Text style={styles.disclosureText}>
                    Stop orders become market orders when the stop price is reached. Stop orders do
                    not guarantee execution at the stop price and may execute at a less favorable
                    price, especially during market gaps or high volatility.
                  </Text>
                </View>
              )}
              
              {/* PDT Warning */}
              {accountInfo?.patternDayTrader && (
                <View style={styles.warningBox}>
                  <Ionicons name="warning" size={16} color="#FF3B30" />
                  <Text style={styles.warningTextBold}>
                    Pattern Day Trader (PDT) Warning:
                  </Text>
                  <Text style={styles.warningText}>
                    Your account is subject to Pattern Day Trader rules. You must maintain minimum
                    equity of $25,000 in your account. If your account falls below this amount, you
                    will be restricted from day trading until you meet the minimum equity
                    requirement.
                  </Text>
                </View>
              )}
              
              {/* Margin Warning (if applicable) */}
              {accountInfo && accountInfo.buyingPower > accountInfo.cash && (
                <View style={styles.warningBox}>
                  <Ionicons name="alert-circle" size={16} color="#FF9500" />
                  <Text style={styles.warningTextBold}>Margin Trading Warning:</Text>
                  <Text style={styles.warningText}>
                    You are using margin. Margin trading amplifies both gains and losses. You may
                    be required to deposit additional funds or securities to meet margin calls.
                    Failure to meet margin requirements may result in forced liquidation of
                    positions.
                  </Text>
                </View>
              )}
            </View>
            
            {/* Legal Documents Links */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Legal Documents</Text>
              <TouchableOpacity
                style={styles.linkButton}
                onPress={() => {
                  // Navigate to Terms of Service
                  // You'll need to implement navigation to a WebView or external browser
                  console.log('Open Terms of Service');
                }}
              >
                <Text style={styles.linkText}>Terms of Service</Text>
                <Ionicons name="chevron-forward" size={16} color="#007AFF" />
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.linkButton}
                onPress={() => {
                  console.log('Open Privacy Policy');
                }}
              >
                <Text style={styles.linkText}>Privacy Policy</Text>
                <Ionicons name="chevron-forward" size={16} color="#007AFF" />
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.linkButton}
                onPress={() => {
                  console.log('Open End User License Agreement (EULA)');
                }}
              >
                <Text style={styles.linkText}>End User License Agreement (EULA)</Text>
                <Ionicons name="chevron-forward" size={16} color="#007AFF" />
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.linkButton}
                onPress={() => {
                  console.log('Open Business Continuity Plan (BCP)');
                }}
              >
                <Text style={styles.linkText}>Business Continuity Plan (BCP)</Text>
                <Ionicons name="chevron-forward" size={16} color="#007AFF" />
              </TouchableOpacity>
            </View>

            {/* Agreement Checkbox */}
            <View style={styles.agreementSection}>
              <TouchableOpacity
                style={styles.checkboxContainer}
                onPress={() => setAgreedToTerms(!agreedToTerms)}
              >
                <Ionicons
                  name={agreedToTerms ? 'checkbox' : 'square-outline'}
                  size={24}
                  color={agreedToTerms ? '#007AFF' : '#8E8E93'}
                />
                <Text style={styles.agreementText}>
                  I understand the risks and agree to the terms
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>

          {/* Action Buttons */}
          <View style={styles.footer}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={onClose}
              disabled={confirming}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.button,
                styles.confirmButton,
                (!canPlaceOrder || !hasEnoughBuyingPower || !agreedToTerms) && styles.disabledButton,
              ]}
              onPress={handleConfirm}
              disabled={confirming || !canPlaceOrder || !hasEnoughBuyingPower || !agreedToTerms}
            >
              {confirming ? (
                <ActivityIndicator color="#FFF" />
              ) : (
                <Text style={styles.confirmButtonText}>Place Order</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    paddingBottom: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1C1C1E',
  },
  closeButton: {
    padding: 4,
  },
  content: {
    padding: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  buyText: {
    color: '#34C759',
  },
  sellText: {
    color: '#FF3B30',
  },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3E0',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  warningText: {
    fontSize: 13,
    color: '#FF9500',
    marginLeft: 8,
    flex: 1,
  },
  disclosureText: {
    fontSize: 12,
    color: '#8E8E93',
    lineHeight: 18,
    marginBottom: 8,
  },
  disclosureTextBold: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  disclosureBox: {
    backgroundColor: '#F9F9F9',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  warningTextBold: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FF3B30',
    marginBottom: 4,
  },
  linkButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 4,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  linkText: {
    fontSize: 14,
    color: '#007AFF',
  },
  agreementSection: {
    marginTop: 8,
    marginBottom: 20,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  agreementText: {
    fontSize: 14,
    color: '#1C1C1E',
    marginLeft: 8,
    flex: 1,
  },
  footer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  button: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButton: {
    backgroundColor: '#F2F2F7',
    marginRight: 8,
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  confirmButton: {
    backgroundColor: '#007AFF',
    marginLeft: 8,
  },
  disabledButton: {
    backgroundColor: '#C7C7CC',
  },
  confirmButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
});

