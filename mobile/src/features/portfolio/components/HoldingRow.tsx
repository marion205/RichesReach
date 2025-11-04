/**
 * HoldingRow - Swipeable row with Buy/Sell actions
 * Phase 2: Swipe actions with haptics, better UX
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Swipeable } from 'react-native-gesture-handler';
import * as Haptics from 'expo-haptics';
import Icon from 'react-native-vector-icons/Feather';
import { useHoldingInsight } from '../hooks/useHoldingInsight';

interface Holding {
  symbol: string;
  quantity: number;
  currentPrice: number;
  totalValue: number;
  change: number;
  changePercent: number;
  name?: string;
}

interface HoldingRowProps {
  holding: Holding;
  allocationPercent: number;
  onPress: (holding: Holding) => void;
  onBuy?: (holding: Holding) => void;
  onSell?: (holding: Holding) => void;
  isLast: boolean;
}

const RightActions = ({ 
  onBuy, 
  onSell,
  holding 
}: { 
  onBuy: () => void; 
  onSell: () => void;
  holding: Holding;
}) => (
  <View style={styles.swipeActionsContainer}>
    <TouchableOpacity
      style={[styles.swipeAction, styles.buyAction]}
      onPress={() => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        onBuy();
      }}
      activeOpacity={0.8}
    >
      <Icon name="plus-circle" size={20} color="#FFFFFF" />
      <Text style={styles.swipeActionText}>Buy</Text>
    </TouchableOpacity>
    <TouchableOpacity
      style={[styles.swipeAction, styles.sellAction]}
      onPress={() => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        onSell();
      }}
      activeOpacity={0.8}
    >
      <Icon name="minus-circle" size={20} color="#FFFFFF" />
      <Text style={styles.swipeActionText}>Sell</Text>
    </TouchableOpacity>
  </View>
);

export const HoldingRow: React.FC<HoldingRowProps> = ({
  holding,
  allocationPercent,
  onPress,
  onBuy,
  onSell,
  isLast,
}) => {
  const isPositive = (holding.change || 0) >= 0;
  const changeColor = isPositive ? '#34C759' : '#FF3B30';
  
  // Phase 3: AI insights (optional, graceful fallback)
  const { data: insight, isLoading: insightLoading } = useHoldingInsight(
    holding.symbol,
    true // Enable by default
  );
  
  const handlePress = () => {
    Haptics.selectionAsync();
    onPress(holding);
  };

  const renderRightActions = (progress: any, dragX: any) => {
    if (!onBuy && !onSell) return null;
    return <RightActions onBuy={() => onBuy?.(holding)} onSell={() => onSell?.(holding)} holding={holding} />;
  };

  const accessibilityLabel = `${holding.symbol}, ${holding.quantity} ${holding.quantity === 1 ? 'share' : 'shares'}, $${(holding.totalValue || 0).toFixed(2)} value, ${isPositive ? 'up' : 'down'} ${Math.abs(holding.changePercent || 0).toFixed(1)} percent today`;

  const content = (
    <TouchableOpacity
      style={[styles.holdingCard, isLast && styles.lastCard]}
      onPress={handlePress}
      activeOpacity={0.7}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint="Double tap to view details. Swipe left for actions."
    >
      <View style={styles.holdingContent}>
        {/* Left: Symbol and details */}
        <View style={styles.holdingLeft}>
          <View style={styles.symbolRow}>
            <Text style={styles.symbol}>{holding.symbol}</Text>
            {allocationPercent > 0 && (
              <View style={styles.allocationBadge}>
                <Text style={styles.allocationText}>{allocationPercent.toFixed(0)}%</Text>
              </View>
            )}
          </View>
          {holding.name && (
            <Text style={styles.companyName} numberOfLines={1}>
              {holding.name}
            </Text>
          )}
          <Text style={styles.quantity}>
            {holding.quantity} {holding.quantity === 1 ? 'share' : 'shares'}
          </Text>
        </View>

        {/* Right: Value and performance */}
        <View style={styles.holdingRight}>
          <Text style={styles.holdingValue}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }).format(holding.totalValue || 0)}
          </Text>
          
          {/* Performance indicator */}
          <View style={styles.performanceRow}>
            <View style={[styles.performanceBadge, { backgroundColor: `${changeColor}15` }]}>
              <Icon 
                name={isPositive ? 'trending-up' : 'trending-down'} 
                size={12} 
                color={changeColor} 
              />
              <Text style={[styles.performanceText, { color: changeColor }]}>
                {isPositive ? '+' : ''}{holding.changePercent?.toFixed(2) || '0.00'}%
              </Text>
            </View>
          </View>

          {/* Gain/Loss amount */}
          <Text style={[styles.changeAmount, { color: changeColor }]}>
            {isPositive ? '+' : ''}{new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }).format(holding.change || 0)}
          </Text>
        </View>
      </View>

      {/* Phase 3: AI Insight */}
      {insight?.headline && !insightLoading && (
        <View style={styles.insightContainer}>
          <Icon name="lightbulb" size={12} color="#007AFF" />
          <Text style={styles.insightText} numberOfLines={1}>
            {insight.headline}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );

  // If no swipe actions, return plain content
  if (!onBuy && !onSell) {
    return content;
  }

  // Wrap in Swipeable
  return (
    <Swipeable
      renderRightActions={renderRightActions}
      rightThreshold={40}
      overshootRight={false}
    >
      {content}
    </Swipeable>
  );
};

const styles = StyleSheet.create({
  holdingCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    minHeight: 44, // Accessibility: minimum touch target
  },
  lastCard: {
    marginBottom: 0,
  },
  holdingContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  holdingLeft: {
    flex: 1,
    marginRight: 12,
  },
  symbolRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  symbol: {
    fontSize: 22,
    fontWeight: '700',
    color: '#000',
    marginRight: 8,
  },
  allocationBadge: {
    backgroundColor: '#E5E5EA',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  allocationText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#8E8E93',
  },
  companyName: {
    fontSize: 15,
    color: '#8E8E93',
    marginBottom: 6,
  },
  quantity: {
    fontSize: 14,
    color: '#8E8E93',
  },
  holdingRight: {
    alignItems: 'flex-end',
  },
  holdingValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
    marginBottom: 6,
  },
  performanceRow: {
    marginBottom: 4,
  },
  performanceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    gap: 4,
  },
  performanceText: {
    fontSize: 13,
    fontWeight: '600',
  },
  changeAmount: {
    fontSize: 15,
    fontWeight: '600',
  },
  insightContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E5E5EA',
    gap: 6,
  },
  insightText: {
    fontSize: 13,
    color: '#007AFF',
    flex: 1,
    fontStyle: 'italic',
  },
  swipeActionsContainer: {
    flexDirection: 'row',
    height: '100%',
    alignItems: 'center',
  },
  swipeAction: {
    width: 84,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 16,
  },
  buyAction: {
    backgroundColor: '#34C759',
  },
  sellAction: {
    backgroundColor: '#FF3B30',
  },
  swipeActionText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    marginTop: 4,
  },
});

