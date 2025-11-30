import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator, Modal, TextInput } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useMutation } from '@apollo/client';
import { CLOSE_OPTIONS_POSITION, TAKE_OPTIONS_PROFITS } from '../../graphql/optionsMutations';

interface OptionsPosition {
  symbol: string; // Contract symbol (e.g., "AAPL240119C00150000")
  qty: number;
  side: 'long' | 'short';
  avg_entry_price: number;
  current_price?: number;
  market_value: number;
  cost_basis: number;
  unrealized_pl: number;
  unrealized_plpc: number;
  // Parsed from contract symbol
  underlyingSymbol?: string;
  strike?: number;
  expiration?: string;
  optionType?: 'call' | 'put';
  daysToExp?: number;
}

interface OptionsPositionCardProps {
  position: OptionsPosition;
  onTakeProfits?: () => void;
  onClosePosition?: () => void;
  onHold?: () => void;
  onPositionUpdated?: () => void;
}

export default function OptionsPositionCard({
  position,
  onTakeProfits,
  onClosePosition,
  onHold,
  onPositionUpdated,
}: OptionsPositionCardProps) {
  const [showTakeProfitModal, setShowTakeProfitModal] = useState(false);
  const [takeProfitPrice, setTakeProfitPrice] = useState('');
  const [closingPosition, setClosingPosition] = useState(false);
  const [takingProfits, setTakingProfits] = useState(false);
  
  const [closePosition] = useMutation(CLOSE_OPTIONS_POSITION);
  const [takeProfits] = useMutation(TAKE_OPTIONS_PROFITS);
  // Parse contract symbol to extract underlying, strike, expiration, type
  const parsed = useMemo(() => {
    // OCC format: SYMBOL + YYMMDD + C/P + STRIKE (8 digits)
    // Example: AAPL240119C00150000
    const contractSymbol = position.symbol;
    
    // Try to extract underlying symbol (first part before date)
    let underlyingSymbol = position.underlyingSymbol || 'UNKNOWN';
    let strike = position.strike || 0;
    let expiration = position.expiration || '';
    let optionType: 'call' | 'put' = position.optionType || 'call';
    let daysToExp = position.daysToExp || 0;
    
    // If we have the parsed data, use it
    if (position.underlyingSymbol) {
      underlyingSymbol = position.underlyingSymbol;
      strike = position.strike || 0;
      expiration = position.expiration || '';
      optionType = position.optionType || 'call';
      daysToExp = position.daysToExp || 0;
    } else {
      // Try to parse from contract symbol
      const match = contractSymbol.match(/^([A-Z]+)(\d{6})([CP])(\d{8})$/);
      if (match) {
        underlyingSymbol = match[1];
        const dateStr = match[2];
        optionType = match[3] === 'C' ? 'call' : 'put';
        strike = parseInt(match[4]) / 1000;
        
        // Parse date: YYMMDD
        const year = 2000 + parseInt(dateStr.substring(0, 2));
        const month = parseInt(dateStr.substring(2, 4)) - 1;
        const day = parseInt(dateStr.substring(4, 6));
        const expDate = new Date(year, month, day);
        expiration = expDate.toISOString().split('T')[0];
        
        // Calculate days to expiration
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        expDate.setHours(0, 0, 0, 0);
        daysToExp = Math.ceil((expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      }
    }
    
    return { underlyingSymbol, strike, expiration, optionType, daysToExp };
  }, [position]);

  // Calculate P&L percentage
  const pnlPercent = position.unrealized_plpc * 100;
  const isProfit = position.unrealized_pl >= 0;
  const isLoss = position.unrealized_pl < 0;

  // Generate AI recommendation
  const recommendation = useMemo(() => {
    const bullets: string[] = [];
    
    // Profit-taking recommendation
    if (pnlPercent > 30) {
      bullets.push(`Up ${pnlPercent.toFixed(0)}% since entry`);
      bullets.push(`AI suggests: Consider taking partial profits if > 30%`);
    } else if (pnlPercent > 0) {
      bullets.push(`Up ${pnlPercent.toFixed(0)}% since entry`);
    } else if (pnlPercent < -20) {
      bullets.push(`Down ${Math.abs(pnlPercent).toFixed(0)}% - consider cutting losses`);
    } else {
      bullets.push(`Down ${Math.abs(pnlPercent).toFixed(0)}% since entry`);
    }
    
    // Time decay warning
    if (parsed.daysToExp <= 3) {
      bullets.push(`Time decay is accelerating - ${parsed.daysToExp} days left`);
    } else if (parsed.daysToExp <= 7) {
      bullets.push(`Time decay is starting to accelerate`);
    }
    
    // Strike analysis
    if (position.current_price) {
      const currentUnderlying = position.current_price; // This would need to come from market data
      if (parsed.optionType === 'call') {
        if (currentUnderlying > parsed.strike * 1.05) {
          bullets.push(`Well in-the-money - strong profit potential`);
        } else if (currentUnderlying < parsed.strike * 0.95) {
          bullets.push(`Out-of-the-money - consider exit strategy`);
        }
      } else {
        if (currentUnderlying < parsed.strike * 0.95) {
          bullets.push(`Well in-the-money - strong profit potential`);
        } else if (currentUnderlying > parsed.strike * 1.05) {
          bullets.push(`Out-of-the-money - consider exit strategy`);
        }
      }
    }
    
    return bullets;
  }, [pnlPercent, parsed.daysToExp, parsed.optionType, parsed.strike, position.current_price]);

  // Format expiration date
  const formatExpiration = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.symbolText}>
            {parsed.underlyingSymbol} ${parsed.strike.toFixed(2)} {parsed.optionType === 'call' ? 'Call' : 'Put'}
          </Text>
          <Text style={styles.expirationText}>
            {parsed.daysToExp} days left • Expires {formatExpiration(parsed.expiration)}
          </Text>
        </View>
        <View style={[styles.statusBadge, isProfit ? styles.statusProfit : styles.statusLoss]}>
          <Text style={[styles.statusText, isProfit ? styles.statusTextProfit : styles.statusTextLoss]}>
            {isProfit ? '↑' : '↓'} {Math.abs(pnlPercent).toFixed(1)}%
          </Text>
        </View>
      </View>

      {/* P&L Display */}
      <View style={styles.pnlSection}>
        <View style={styles.pnlRow}>
          <Text style={styles.pnlLabel}>Unrealized P&L:</Text>
          <Text style={[styles.pnlValue, isProfit ? styles.pnlValueProfit : styles.pnlValueLoss]}>
            {isProfit ? '+' : ''}${position.unrealized_pl.toFixed(2)}
          </Text>
        </View>
        <View style={styles.pnlRow}>
          <Text style={styles.pnlLabel}>Position Size:</Text>
          <Text style={styles.pnlValue}>{position.qty} contracts</Text>
        </View>
      </View>

      {/* AI Recommendations */}
      <View style={styles.recommendationsSection}>
        {recommendation.map((bullet, index) => (
          <View key={index} style={styles.bulletRow}>
            <Icon 
              name={index === 0 && pnlPercent > 30 ? "trending-up" : "info"} 
              size={14} 
              color={index === 0 && pnlPercent > 30 ? "#059669" : "#6B7280"} 
              style={styles.bulletIcon} 
            />
            <Text style={styles.bulletText}>{bullet}</Text>
          </View>
        ))}
      </View>

      {/* Action Buttons */}
      <View style={styles.actionsRow}>
        <TouchableOpacity style={styles.actionButton} onPress={onHold || (() => {})}>
          <Text style={styles.actionButtonText}>Hold</Text>
        </TouchableOpacity>
        {pnlPercent > 20 && (
          <TouchableOpacity
            style={[styles.actionButton, styles.actionButtonPrimary]}
            onPress={() => setShowTakeProfitModal(true)}
            disabled={takingProfits}
          >
            {takingProfits ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={[styles.actionButtonText, styles.actionButtonTextPrimary]}>Take Profits</Text>
            )}
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[styles.actionButton, styles.actionButtonDanger]}
          onPress={handleClosePosition}
          disabled={closingPosition}
        >
          {closingPosition ? (
            <ActivityIndicator size="small" color="#DC2626" />
          ) : (
            <Text style={[styles.actionButtonText, styles.actionButtonTextDanger]}>Close Position</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Take Profit Modal */}
      <Modal
        visible={showTakeProfitModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowTakeProfitModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Take Profits</Text>
            <Text style={styles.modalSubtitle}>
              Set a limit price to lock in profits for {parsed.underlyingSymbol} ${parsed.strike.toFixed(2)} {parsed.optionType}
            </Text>
            
            <View style={styles.modalInputGroup}>
              <Text style={styles.modalLabel}>Target Price (per contract)</Text>
              <TextInput
                style={styles.modalInput}
                value={takeProfitPrice}
                onChangeText={setTakeProfitPrice}
                keyboardType="numeric"
                placeholder={`Current: $${(position.current_price || position.avg_entry_price).toFixed(2)}`}
              />
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalCancelButton}
                onPress={() => setShowTakeProfitModal(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalConfirmButton}
                onPress={handleTakeProfits}
                disabled={!takeProfitPrice || takingProfits}
              >
                {takingProfits ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <Text style={styles.modalConfirmText}>Place Order</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );

  const handleClosePosition = async () => {
    setClosingPosition(true);
    try {
      const result = await closePosition({
        variables: {
          symbol: position.symbol,
          quantity: position.qty,
        },
      });

      const response = result.data?.closeOptionsPosition;
      if (response?.success) {
        Alert.alert('Position Closed', `Order ID: ${response.orderId}`);
        onPositionUpdated?.();
      } else {
        Alert.alert('Error', response?.error || 'Failed to close position');
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to close position');
    } finally {
      setClosingPosition(false);
    }
  };

  const handleTakeProfits = async () => {
    if (!takeProfitPrice) {
      Alert.alert('Error', 'Please enter a target price');
      return;
    }

    setTakingProfits(true);
    try {
      const result = await takeProfits({
        variables: {
          symbol: position.symbol,
          quantity: position.qty,
          limitPrice: parseFloat(takeProfitPrice),
        },
      });

      const response = result.data?.takeOptionsProfits;
      if (response?.success) {
        Alert.alert('Take Profit Order Placed', `Order ID: ${response.orderId}`);
        setShowTakeProfitModal(false);
        setTakeProfitPrice('');
        onPositionUpdated?.();
      } else {
        Alert.alert('Error', response?.error || 'Failed to place order');
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to place order');
    } finally {
      setTakingProfits(false);
    }
  };
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  headerLeft: {
    flex: 1,
  },
  symbolText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  expirationText: {
    fontSize: 13,
    color: '#6B7280',
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusProfit: {
    backgroundColor: '#D1FAE5',
  },
  statusLoss: {
    backgroundColor: '#FEE2E2',
  },
  statusText: {
    fontSize: 13,
    fontWeight: '700',
  },
  statusTextProfit: {
    color: '#059669',
  },
  statusTextLoss: {
    color: '#DC2626',
  },
  pnlSection: {
    paddingVertical: 12,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#F3F4F6',
    marginBottom: 12,
  },
  pnlRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  pnlLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  pnlValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  pnlValueProfit: {
    color: '#059669',
  },
  pnlValueLoss: {
    color: '#DC2626',
  },
  recommendationsSection: {
    marginBottom: 16,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  bulletIcon: {
    marginRight: 8,
    marginTop: 2,
  },
  bulletText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  actionButtonPrimary: {
    backgroundColor: '#059669',
    borderColor: '#059669',
  },
  actionButtonDanger: {
    borderColor: '#DC2626',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  actionButtonTextPrimary: {
    color: '#FFFFFF',
  },
  actionButtonTextDanger: {
    color: '#DC2626',
  },
});

